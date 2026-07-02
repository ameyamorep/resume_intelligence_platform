"""Deterministic, explainable ATS rule engine.

Every check returns (score, max_score, evidence, explanation) so the frontend
"Explain My Score" panel can render the exact reasons behind each point.
No ML, no randomness — the same resume always scores the same.
"""
from __future__ import annotations

import re

from app.models.schemas import AtsCategory, AtsCheck, AtsReport, ResumeDoc

ACTION_VERBS = {
    "achieved", "analyzed", "architected", "automated", "built", "collaborated",
    "created", "delivered", "designed", "developed", "drove", "engineered",
    "established", "implemented", "improved", "increased", "launched", "led",
    "managed", "mentored", "migrated", "optimized", "orchestrated", "owned",
    "reduced", "refactored", "resolved", "scaled", "shipped", "spearheaded",
    "streamlined", "tested", "trained", "transformed", "deployed", "integrated",
    "initiated", "coordinated", "researched", "presented", "founded",
}
WEAK_OPENERS = {
    "responsible", "worked", "helped", "assisted", "involved", "participated",
    "was", "were", "did", "duties", "tasked",
}
LEADERSHIP_TERMS = [
    "led", "lead", "managed", "mentored", "supervised", "coordinated", "directed",
    "founded", "president", "captain", "chair", "head of", "spearheaded", "owner",
    "organized", "team lead", "scrum master",
]
QUANT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent|x\b|k\b|m\b|users|customers|requests|ms\b|sec|hours|days|\$|aud|usd)|\$\s?\d|(?:by|to|from)\s+\d", re.I)
FILLER_PHRASES = [
    "team player", "hard working", "hardworking", "go-getter", "think outside the box",
    "results-driven", "detail-oriented", "self-starter", "synergy", "dynamic individual",
]


def _check(rule: str, passed: bool, score: float, max_score: float,
           evidence: str, explanation: str) -> AtsCheck:
    return AtsCheck(rule=rule, passed=passed, score=round(score, 1), max_score=max_score,
                    evidence=evidence, explanation=explanation)


def _cat(name: str, checks: list[AtsCheck]) -> AtsCategory:
    return AtsCategory(
        name=name,
        score=round(sum(c.score for c in checks), 1),
        max_score=sum(c.max_score for c in checks),
        checks=checks,
    )


def run_ats_analysis(resume: ResumeDoc) -> AtsReport:
    categories = [
        _contact_info(resume),
        _structure(resume),
        _section_completeness(resume),
        _bullet_consistency(resume),
        _action_verbs(resume),
        _quantified_achievements(resume),
        _readability(resume),
        _length(resume),
        _formatting(resume),
        _grammar_heuristics(resume),
        _project_quality(resume),
        _technical_skills(resume),
        _leadership(resume),
    ]
    return AtsReport(
        total_score=round(sum(c.score for c in categories), 1),
        max_score=sum(c.max_score for c in categories),
        categories=categories,
    )


# --------------------------------------------------------------- categories


def _contact_info(r: ResumeDoc) -> AtsCategory:
    c = r.contact
    checks = [
        _check("Email present", bool(c.email), 3 if c.email else 0, 3,
               c.email or "none found",
               "ATS systems key candidate records off an email address."),
        _check("Phone present", bool(c.phone), 2 if c.phone else 0, 2,
               c.phone or "none found",
               "Recruiters expect a phone number in the header."),
        _check("Name detected", bool(c.name), 2 if c.name else 0, 2,
               c.name or "not detected",
               "A clear name on the first line parses reliably."),
        _check("LinkedIn or portfolio link", bool(c.linkedin or c.github or c.website),
               2 if (c.linkedin or c.github or c.website) else 0, 2,
               c.linkedin or c.github or c.website or "none found",
               "A LinkedIn/GitHub link adds credibility and is often auto-imported."),
    ]
    return _cat("Contact Information", checks)


def _structure(r: ResumeDoc) -> AtsCategory:
    core = {"experience", "education", "skills"}
    found = core & set(r.sections_found)
    checks = [
        _check("Core sections labelled", len(found) == 3, len(found), 3,
               f"found: {', '.join(sorted(r.sections_found)) or 'none'}",
               "ATS parsers map content using standard headings "
               "(Experience, Education, Skills)."),
        _check("Summary/profile present", "summary" in r.sections_found,
               1 if "summary" in r.sections_found else 0, 1,
               (r.summary[:80] + "…") if r.summary else "no summary section",
               "A 2–3 line summary orients both parsers and recruiters."),
    ]
    return _cat("Resume Structure", checks)


def _section_completeness(r: ResumeDoc) -> AtsCategory:
    checks = [
        _check("Experience entries parsed", bool(r.experience),
               3 if r.experience else 0, 3,
               f"{len(r.experience)} role(s) detected",
               "Roles with title/company/dates must be machine-readable."),
        _check("Education entries parsed", bool(r.education),
               2 if r.education else 0, 2,
               f"{len(r.education)} entr(ies) detected",
               "Degree and institution should be identifiable."),
        _check("Skills list parsed", len(r.skills) >= 5,
               min(len(r.skills), 5) * 0.4, 2,
               f"{len(r.skills)} skills listed",
               "A dedicated skills section is the primary keyword surface for ATS."),
    ]
    return _cat("Section Completeness", checks)


def _bullet_consistency(r: ResumeDoc) -> AtsCategory:
    n = len(r.bullet_lines)
    exp_bullets = sum(len(e.bullets) for e in r.experience)
    lengths = [len(b.split()) for b in r.bullet_lines]
    good_len = sum(1 for L in lengths if 6 <= L <= 30)
    ratio = good_len / n if n else 0
    checks = [
        _check("Bullets used for experience", exp_bullets >= 2,
               2 if exp_bullets >= 2 else exp_bullets, 2,
               f"{exp_bullets} bullets across {len(r.experience)} role(s)",
               "Bullet points are parsed more reliably than paragraphs."),
        _check("Bullet length 6–30 words", ratio >= 0.7, round(3 * ratio, 1), 3,
               f"{good_len}/{n} bullets in range" if n else "no bullets found",
               "Very short bullets carry no signal; very long ones read as paragraphs."),
    ]
    return _cat("Bullet Consistency", checks)


def _action_verbs(r: ResumeDoc) -> AtsCategory:
    n = len(r.bullet_lines)
    strong = sum(1 for b in r.bullet_lines
                 if (w := re.sub(r"^\W+", "", b).split()) and w[0].lower().rstrip("ds") in ACTION_VERBS
                 or (w and w[0].lower() in ACTION_VERBS))
    weak = [b for b in r.bullet_lines
            if (w := re.sub(r"^\W+", "", b).split()) and w[0].lower() in WEAK_OPENERS]
    ratio = strong / n if n else 0
    checks = [
        _check("Bullets start with action verbs", ratio >= 0.6, round(4 * ratio, 1), 4,
               f"{strong}/{n} bullets open with a strong verb" if n else "no bullets found",
               "Opening with 'Built', 'Led', 'Reduced'… signals ownership and outcomes."),
        _check("No weak openers", not weak, 2 if not weak else max(0, 2 - len(weak) * 0.5), 2,
               ("e.g. \"" + weak[0][:70] + "…\"") if weak else "none found",
               "'Responsible for' / 'Worked on' phrasing hides your actual contribution."),
    ]
    return _cat("Action Verbs", checks)


def _quantified_achievements(r: ResumeDoc) -> AtsCategory:
    n = len(r.bullet_lines)
    quantified = [b for b in r.bullet_lines if QUANT_RE.search(b)]
    ratio = len(quantified) / n if n else 0
    checks = [
        _check("Bullets include metrics", ratio >= 0.3, round(6 * min(ratio / 0.5, 1), 1), 6,
               f"{len(quantified)}/{n} bullets quantified" if n else "no bullets found",
               "Numbers (%, $, time saved, users served) are the strongest credibility "
               "signal a resume can carry."),
    ]
    return _cat("Quantified Achievements", checks)


def _readability(r: ResumeDoc) -> AtsCategory:
    words = re.findall(r"[A-Za-z']+", r.raw_text)
    sentences = max(1, len(re.findall(r"[.!?\n]", r.raw_text)))
    avg_sentence = len(words) / sentences
    long_words = sum(1 for w in words if len(w) >= 10)
    long_ratio = long_words / len(words) if words else 0
    ok_sentence = avg_sentence <= 24
    ok_words = long_ratio <= 0.18
    checks = [
        _check("Concise line length", ok_sentence, 2 if ok_sentence else 1, 2,
               f"~{avg_sentence:.0f} words per line/sentence",
               "Recruiters skim; short lines keep the eye moving."),
        _check("Plain-language vocabulary", ok_words, 2 if ok_words else 1, 2,
               f"{long_ratio:.0%} of words are 10+ letters",
               "Overly formal vocabulary reduces skimmability."),
    ]
    return _cat("Readability", checks)


def _length(r: ResumeDoc) -> AtsCategory:
    wc, pages = r.word_count, r.page_count
    ok_pages = pages <= 2
    ok_words = 300 <= wc <= 1100
    checks = [
        _check("1–2 pages", ok_pages, 2 if ok_pages else 0, 2,
               f"{pages} page(s)",
               "Beyond two pages, content gets skipped by both ATS ranking and humans."),
        _check("300–1100 words", ok_words, 2 if ok_words else 1 if wc else 0, 2,
               f"{wc} words",
               "Too short reads as thin experience; too long buries the signal."),
    ]
    return _cat("Resume Length", checks)


def _formatting(r: ResumeDoc) -> AtsCategory:
    text = r.raw_text
    # Heuristics for ATS-hostile artifacts that survive text extraction.
    weird_chars = len(re.findall(r"[^\x00-\x7F•–—''""·]", text))
    weird_ratio = weird_chars / max(1, len(text))
    tabs_cols = len(re.findall(r"\t{2,}| {6,}", text))
    all_caps_lines = sum(1 for ln in text.splitlines()
                         if len(ln.strip()) > 25 and ln.strip().isupper())
    checks = [
        _check("Clean character set", weird_ratio < 0.01,
               2 if weird_ratio < 0.01 else 0, 2,
               f"{weird_chars} non-standard characters",
               "Symbols/icons from design templates often turn into garbage in ATS parsers."),
        _check("No multi-column artifacts", tabs_cols < 8,
               2 if tabs_cols < 8 else 0, 2,
               f"{tabs_cols} wide gaps / tab runs detected",
               "Multi-column layouts scramble reading order when parsed as text."),
        _check("Limited ALL-CAPS blocks", all_caps_lines <= 2,
               1 if all_caps_lines <= 2 else 0, 1,
               f"{all_caps_lines} long all-caps lines",
               "Long all-caps lines hurt readability and can break heading detection."),
    ]
    return _cat("Formatting", checks)


def _grammar_heuristics(r: ResumeDoc) -> AtsCategory:
    text = r.raw_text
    doubles = re.findall(r"\b(\w+)\s+\1\b", text, re.I)
    spacing = len(re.findall(r"\s[,.;:]", text))
    first_person = len(re.findall(r"\b(I|me|my|mine)\b", text))
    fillers = [p for p in FILLER_PHRASES if p in text.lower()]
    checks = [
        _check("No repeated words", len(doubles) <= 1,
               1 if len(doubles) <= 1 else 0, 1,
               f"e.g. '{doubles[0]} {doubles[0]}'" if doubles else "none found",
               "Duplicated words ('the the') are the most common typo class."),
        _check("Clean punctuation spacing", spacing <= 2,
               1 if spacing <= 2 else 0, 1,
               f"{spacing} occurrences of space before punctuation",
               "' ,' or ' .' patterns signal rushed editing."),
        _check("Minimal first-person pronouns", first_person <= 3,
               1 if first_person <= 3 else 0, 1,
               f"{first_person} uses of I/me/my",
               "Resume convention drops first-person pronouns."),
        _check("No filler clichés", not fillers,
               1 if not fillers else 0, 1,
               ", ".join(fillers) if fillers else "none found",
               "Clichés like 'team player' add words without evidence."),
    ]
    return _cat("Grammar & Language", checks)


def _project_quality(r: ResumeDoc) -> AtsCategory:
    n = len(r.projects)
    with_detail = sum(1 for p in r.projects if p.bullets or len(p.raw.split()) > 12)
    proj_text = " ".join(p.raw for p in r.projects)
    has_tech = bool(re.search(r"(python|react|node|sql|aws|api|docker|tensorflow|java|typescript)", proj_text, re.I))
    checks = [
        _check("Projects present", n >= 1, 2 if n else 0, 2,
               f"{n} project(s)",
               "Projects prove applied skill, especially early-career."),
        _check("Projects described in detail", with_detail >= 1 and (with_detail / n >= 0.5 if n else False),
               2 if n and with_detail / n >= 0.5 else 1 if with_detail else 0, 2,
               f"{with_detail}/{n} projects have detail" if n else "no projects",
               "A name alone says nothing — describe what was built and its impact."),
        _check("Projects name technologies", has_tech, 1 if has_tech else 0, 1,
               "technology keywords found" if has_tech else "no tech keywords in projects",
               "Naming the stack makes projects keyword-searchable."),
    ]
    return _cat("Project Quality", checks)


def _technical_skills(r: ResumeDoc) -> AtsCategory:
    n = len(r.skills)
    in_context = 0
    body = " ".join(r.bullet_lines).lower()
    for s in r.skills[:30]:
        if len(s) >= 2 and s.lower() in body:
            in_context += 1
    checks = [
        _check("Skills section populated", n >= 8, min(n, 8) * 0.25, 2,
               f"{n} skills listed",
               "8+ skills give ATS keyword matching enough surface."),
        _check("Skills evidenced in experience", in_context >= 3,
               min(in_context, 3), 3,
               f"{in_context} listed skills also appear in bullets",
               "Skills repeated inside experience bullets rank higher than a bare list."),
    ]
    return _cat("Technical Skills", checks)


def _leadership(r: ResumeDoc) -> AtsCategory:
    text = r.raw_text.lower()
    hits = [t for t in LEADERSHIP_TERMS if re.search(rf"\b{re.escape(t)}\b", text)]
    checks = [
        _check("Leadership indicators", len(hits) >= 2,
               min(len(hits), 3), 3,
               ", ".join(hits[:5]) if hits else "none found",
               "Mentoring, leading or coordinating signals seniority potential."),
    ]
    return _cat("Leadership Indicators", checks)
