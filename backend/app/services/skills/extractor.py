"""Skill extraction and resume-vs-JD gap analysis."""
from __future__ import annotations

import re

from app.models.schemas import JobDoc, ResumeDoc, SkillGap, SkillMatch
from app.services.skills.taxonomy import find_skills

REQUIRED_CUE_RE = re.compile(
    r"(required|must[- ]have|must have|essential|minimum qualifications|"
    r"you (?:have|bring)|proficien|strong (?:knowledge|experience) (?:of|in|with))", re.I)
PREFERRED_CUE_RE = re.compile(
    r"(preferred|nice[- ]to[- ]have|bonus|desirable|a plus|advantageous|ideally)", re.I)


def extract_job_skills(job: JobDoc) -> tuple[list[str], list[str]]:
    """Classify JD skills as required vs preferred by the cue words in the
    line each skill appears on. Skills with no cue default to required —
    if a JD names a technology, treat it as expected."""
    required: set[str] = set()
    preferred: set[str] = set()
    mode = "required"  # section headers like "Nice to have:" set the mode for lines below
    for line in job.raw_text.splitlines():
        skills_in_line = find_skills(line)
        if not skills_in_line:
            if PREFERRED_CUE_RE.search(line):
                mode = "preferred"
            elif REQUIRED_CUE_RE.search(line) or not line.strip():
                mode = "required"
            continue
        if PREFERRED_CUE_RE.search(line) or mode == "preferred":
            preferred |= skills_in_line
        else:
            required |= skills_in_line
    preferred -= required
    return sorted(required), sorted(preferred)


def analyze_skill_gap(resume: ResumeDoc, job: JobDoc) -> tuple[SkillGap, JobDoc]:
    required, preferred = extract_job_skills(job)
    job.required_skills = required
    job.preferred_skills = preferred

    resume_skills = find_skills(resume.raw_text)

    matched: list[SkillMatch] = []
    missing: list[SkillMatch] = []
    for name in required:
        (matched if name in resume_skills else missing).append(
            SkillMatch(name=name, importance="required"))
    for name in preferred:
        (matched if name in resume_skills else missing).append(
            SkillMatch(name=name, importance="preferred"))

    jd_all = set(required) | set(preferred)
    resume_only = sorted(resume_skills - jd_all)

    # Weighted coverage: required skills count double.
    total_w = 2 * len(required) + len(preferred)
    got_w = sum(2 if m.importance == "required" else 1 for m in matched)
    coverage = round(100.0 * got_w / total_w, 1) if total_w else 100.0

    gap = SkillGap(matched=matched, missing=missing,
                   resume_only=resume_only, coverage_pct=coverage)
    return gap, job
