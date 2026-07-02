"""Per-module verification: run one stage of the pipeline in isolation.

Usage:
    python module_tests.py parser
    python module_tests.py embedding
    python module_tests.py ats
    python module_tests.py skills
    python module_tests.py claude      (needs ANTHROPIC_API_KEY in .env)
    python module_tests.py all
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SAMPLES = Path(__file__).parent / "samples"
RESUME = (SAMPLES / "sample_resume.txt").read_text(encoding="utf-8")
JD = (SAMPLES / "sample_jd.txt").read_text(encoding="utf-8")


def test_parser() -> None:
    from app.services.parsing.section_extractor import extract_resume

    r = extract_resume(RESUME)
    print("== PARSER ==")
    print("contact  :", r.contact.model_dump(exclude_none=True))
    print("sections :", r.sections_found)
    print("roles    :", [(e.title, e.company, e.start, e.end, len(e.bullets)) for e in r.experience])
    print("education:", [(e.degree, e.year) for e in r.education])
    print("projects :", [p.name for p in r.projects])
    print("skills   :", r.skills)
    assert r.contact.email and len(r.experience) == 2 and r.skills, "parser regression"
    print("PASS\n")


def test_embedding() -> None:
    from app.services.matching import embedding_engine as emb

    print("== EMBEDDING ==")
    print("backend  :", emb.backend_name())
    same = emb.similarity(RESUME, RESUME)
    related = emb.similarity(RESUME, JD)
    unrelated = emb.similarity(RESUME, "Recipe for banana bread: flour, sugar, ripe bananas, butter, bake at 180C.")
    print(f"self     : {same:.3f} (should be ~1.0)")
    print(f"resume-jd: {related:.3f} -> calibrated {emb.calibrate(related)}")
    print(f"unrelated: {unrelated:.3f} -> calibrated {emb.calibrate(unrelated)}")
    assert same > 0.99 and related > unrelated, "similarity ordering broken"
    print("PASS\n")


def test_ats() -> None:
    from app.services.ats.engine import run_ats_analysis
    from app.services.parsing.section_extractor import extract_resume

    print("== ATS ==")
    good = run_ats_analysis(extract_resume(RESUME))
    weak = run_ats_analysis(extract_resume(
        (SAMPLES / "sample_weak_resume.txt").read_text(encoding="utf-8")))
    print(f"good resume: {good.total_score}/{good.max_score}")
    print(f"weak resume: {weak.total_score}/{weak.max_score}")
    for c in good.categories:
        print(f"  {c.name:<26} {c.score:g}/{c.max_score:g}")
    assert good.total_score > weak.total_score, "ATS engine can't tell good from weak"
    print("PASS (good > weak, deterministic)\n")


def test_skills() -> None:
    from app.services.parsing.section_extractor import extract_job, extract_resume
    from app.services.skills.extractor import analyze_skill_gap

    print("== SKILLS ==")
    gap, job = analyze_skill_gap(extract_resume(RESUME), extract_job(JD))
    print("required :", job.required_skills)
    print("preferred:", job.preferred_skills)
    print("matched  :", [m.name for m in gap.matched])
    print("missing  :", [f"{m.name}({m.importance})" for m in gap.missing])
    print("coverage :", gap.coverage_pct, "%")
    assert "Kubernetes" in [m.name for m in gap.missing]
    assert "Python" in [m.name for m in gap.matched]
    print("PASS\n")


def test_claude() -> None:
    """Tests whichever AI provider is configured (gemini/groq/ollama/anthropic)."""
    from app.services.ai.analyzer import resolve_provider, run_ai_analysis
    from app.services.ats.engine import run_ats_analysis
    from app.services.parsing.section_extractor import extract_job, extract_resume
    from app.services.skills.extractor import analyze_skill_gap

    print(f"== AI ({resolve_provider()}) ==")
    resume = extract_resume(RESUME)
    job = extract_job(JD)
    ats = run_ats_analysis(resume)
    gap, job = analyze_skill_gap(resume, job)
    ai, err = run_ai_analysis(resume, job, ats, gap, semantic_match=55.0)
    if err:
        print("ERROR:", err)
        sys.exit(1)
    print("model    :", ai.model)
    print("summary  :", ai.summary[:200])
    print("strengths:", len(ai.strengths), "| weaknesses:", len(ai.weaknesses),
          "| rewrites:", len(ai.weak_bullets), "| recs:", len(ai.recommendations))
    if ai.weak_bullets:
        print("sample rewrite:")
        print(json.dumps(ai.weak_bullets[0].model_dump(), indent=2))
    assert ai.summary and ai.recommendations, "structured output incomplete"
    print("PASS\n")


TESTS = {"parser": test_parser, "embedding": test_embedding, "ats": test_ats,
         "skills": test_skills, "claude": test_claude, "ai": test_claude}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for name, fn in TESTS.items():
            if name == "ai":
                continue  # alias of "claude"
            if name == "claude":
                from app.services.ai.analyzer import resolve_provider
                if resolve_provider() == "none":
                    print("== AI ==\nSKIPPED (no AI provider configured)\n")
                    continue
            fn()
    elif which in TESTS:
        TESTS[which]()
    else:
        print(__doc__)
        sys.exit(2)
