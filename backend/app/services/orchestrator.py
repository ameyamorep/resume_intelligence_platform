"""Runs the full analysis pipeline: parse → ATS → match → skills → AI → actions."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.models.schemas import (
    AnalysisMeta,
    AnalysisResult,
    RadarProfile,
    ScoreBreakdown,
    TimelineEntry,
)
from app.services.ai.analyzer import run_ai_analysis
from app.services.ats.engine import run_ats_analysis
from app.services.matching import embedding_engine as emb
from app.services.parsing.document_parser import parse_document
from app.services.parsing.section_extractor import extract_job, extract_resume
from app.services.recommendations.engine import build_actions
from app.services.skills.extractor import analyze_skill_gap

WEIGHTS = {"skills": 0.35, "semantic": 0.25, "experience": 0.20, "projects": 0.10, "education": 0.10}


def run_analysis(resume_filename: str, resume_bytes: bytes, jd_text: str) -> AnalysisResult:
    # 1. Parse
    parsed = parse_document(resume_filename, resume_bytes)
    resume = extract_resume(parsed.text, parsed.page_count)
    job = extract_job(jd_text)

    # 2. Deterministic ATS
    ats = run_ats_analysis(resume)

    # 3. Skill gap (also fills job.required/preferred skills)
    gap, job = analyze_skill_gap(resume, job)

    # 4. Semantic matching
    semantic = emb.calibrate(emb.similarity(resume.raw_text, job.raw_text))
    exp_text = "\n".join(e.raw for e in resume.experience) or resume.raw_text
    proj_text = "\n".join(p.raw for p in resume.projects)
    edu_text = "\n".join(e.raw for e in resume.education)

    experience_match = _experience_match(resume, job, exp_text)
    project_match = emb.calibrate(emb.similarity(proj_text, job.raw_text)) if proj_text else 30.0
    education_match = _education_match(edu_text, job.raw_text)

    overall = round(
        WEIGHTS["skills"] * gap.coverage_pct
        + WEIGHTS["semantic"] * semantic
        + WEIGHTS["experience"] * experience_match
        + WEIGHTS["projects"] * project_match
        + WEIGHTS["education"] * education_match, 1)

    scores = ScoreBreakdown(
        overall_match=overall,
        semantic_match=semantic,
        skills_match=gap.coverage_pct,
        experience_match=experience_match,
        project_match=project_match,
        education_match=education_match,
        weights=WEIGHTS,
        explanation={
            "overall": "Weighted blend of the five component scores using the returned weights.",
            "skills": f"Coverage of JD skills found on the resume (required weighted 2x): "
                      f"{len(gap.matched)} matched, {len(gap.missing)} missing.",
            "semantic": f"Embedding cosine similarity between resume and JD, calibrated to 0-100 "
                        f"({emb.backend_name()} backend).",
            "experience": "Section-level similarity of your experience against the JD, adjusted "
                          "for the JD's years-of-experience requirement where stated.",
            "projects": "Similarity of your projects section to the JD (30 baseline if absent).",
            "education": "Similarity plus degree-keyword alignment with the JD.",
        },
    )

    # 5. AI analysis (optional — provider chosen by AI_PROVIDER / available keys)
    ai, ai_error = run_ai_analysis(resume, job, ats, gap, semantic)

    # 6. Recommendations
    actions = build_actions(ats, gap, scores, ai)

    return AnalysisResult(
        id=uuid.uuid4().hex[:12],
        created_at=datetime.now(timezone.utc),
        resume=resume,
        job=job,
        scores=scores,
        ats=ats,
        skills=gap,
        radar=_radar(resume, ats, gap, scores),
        timeline=_timeline(resume),
        ai=ai,
        actions=actions,
        meta=AnalysisMeta(
            embedding_backend=emb.backend_name(),
            ai_available=ai is not None,
            ai_error=ai_error,
            resume_filename=resume_filename,
        ),
    )


def _experience_match(resume, job, exp_text: str) -> float:
    base = emb.calibrate(emb.similarity(exp_text, job.raw_text))
    if job.min_years_experience:
        years = _estimate_years(resume)
        ratio = min(years / job.min_years_experience, 1.0) if job.min_years_experience else 1.0
        base = round(0.7 * base + 30.0 * ratio, 1)
    return base


def _estimate_years(resume) -> float:
    """Sum date ranges across roles (overlaps ignored — good enough for a ratio)."""
    now = datetime.now()
    total_months = 0
    for e in resume.experience:
        if not e.start:
            continue
        sy, sm = _ym(e.start)
        if e.end:
            ey, em = _ym(e.end)
        else:
            ey, em = now.year, now.month
        total_months += max(0, (ey - sy) * 12 + (em - sm))
    return round(total_months / 12, 1)


def _ym(s: str) -> tuple[int, int]:
    parts = s.split("-")
    return int(parts[0]), int(parts[1]) if len(parts) > 1 else 6


def _education_match(edu_text: str, jd_text: str) -> float:
    if not edu_text.strip():
        return 20.0
    base = emb.calibrate(emb.similarity(edu_text, jd_text))
    jd_low, edu_low = jd_text.lower(), edu_text.lower()
    degree_terms = ["bachelor", "master", "phd", "degree"]
    jd_wants = any(t in jd_low for t in degree_terms)
    has_degree = any(t in edu_low for t in degree_terms + ["b.sc", "m.sc", "btech", "b.tech", "mba"])
    if not jd_wants:
        return max(base, 70.0)  # JD doesn't gate on education
    return round(min(100.0, 0.4 * base + (60.0 if has_degree else 10.0)), 1)


def _radar(resume, ats, gap, scores) -> RadarProfile:
    def cat_pct(name: str) -> float:
        for c in ats.categories:
            if c.name == name:
                return round(100.0 * c.score / c.max_score, 1) if c.max_score else 0.0
        return 0.0

    writing = round((cat_pct("Action Verbs") + cat_pct("Grammar & Language")
                     + cat_pct("Quantified Achievements")) / 3, 1)
    structure = round((cat_pct("Resume Structure") + cat_pct("Section Completeness")
                       + cat_pct("Formatting")) / 3, 1)
    return RadarProfile(
        technical_skills=gap.coverage_pct,
        project_quality=cat_pct("Project Quality"),
        experience=scores.experience_match,
        ats_compatibility=round(100.0 * ats.total_score / ats.max_score, 1),
        writing_quality=writing,
        leadership=cat_pct("Leadership Indicators"),
        readability=cat_pct("Readability"),
        resume_structure=structure,
    )


def _timeline(resume) -> list[TimelineEntry]:
    entries = []
    for e in resume.experience:
        if e.title or e.company:
            entries.append(TimelineEntry(
                title=e.title or "Role", company=e.company or "",
                start=e.start, end=e.end))
    return entries
