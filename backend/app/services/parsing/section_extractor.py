"""Raw resume/JD text → structured documents (ResumeDoc / JobDoc).

Heuristic, dependency-light section segmentation: detect canonical section
headings, bucket lines under them, then run per-section extractors.
"""
from __future__ import annotations

import re
from typing import Optional

from app.models.schemas import (
    ContactInfo,
    EducationItem,
    ExperienceItem,
    JobDoc,
    ProjectItem,
    ResumeDoc,
)

# Canonical section name -> heading aliases (matched case-insensitively on
# short lines that look like headings).
SECTION_ALIASES: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "profile", "objective", "about me", "about"],
    "experience": [
        "experience", "work experience", "professional experience", "employment",
        "employment history", "work history", "internships", "internship experience",
    ],
    "education": ["education", "academic background", "academics", "qualifications"],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "selected projects"],
    "skills": [
        "skills", "technical skills", "core skills", "skills & tools", "technologies",
        "tech stack", "core competencies", "skills and abilities",
    ],
    "certifications": ["certifications", "certificates", "licenses", "licenses & certifications"],
    "achievements": ["achievements", "awards", "honors", "accomplishments"],
    "publications": ["publications", "research"],
    "leadership": ["leadership", "leadership experience", "volunteering", "volunteer experience", "extracurricular"],
}

BULLET_RE = re.compile(r"^\s*[•▪◦‣·o\-\*–—]\s+(.+)$")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s|,)]+", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s|,)]+", re.I)
URL_RE = re.compile(r"(?:https?://)?(?:www\.)?[\w-]+\.[a-z]{2,}(?:/[^\s|,)]*)?", re.I)
DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
    r"\s*(?:-|–|—|to)\s*"
    r"(?P<end>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4}|present|current|now)",
    re.I,
)
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _heading_lookup() -> dict[str, str]:
    table = {}
    for canonical, aliases in SECTION_ALIASES.items():
        for a in aliases:
            table[a] = canonical
    return table


_HEADINGS = _heading_lookup()


def _match_heading(line: str) -> Optional[str]:
    stripped = re.sub(r"[:\s]+$", "", line.strip())
    if not stripped or len(stripped) > 40:
        return None
    return _HEADINGS.get(stripped.lower())


def _normalize_date(token: str) -> Optional[str]:
    token = token.strip().rstrip(".")
    low = token.lower()
    if low in ("present", "current", "now"):
        return None
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{4})", token)
    if m:
        month = MONTHS.get(m.group(1).lower()[:3])
        return f"{m.group(2)}-{month:02d}" if month else m.group(2)
    m = re.match(r"(\d{1,2})/(\d{4})", token)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    if re.fullmatch(r"\d{4}", token):
        return token
    return None


def split_sections(text: str) -> dict[str, list[str]]:
    """Return {canonical_section: lines}, with pre-heading lines under 'header'."""
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in text.splitlines():
        canonical = _match_heading(line)
        if canonical:
            current = canonical
            sections.setdefault(current, [])
            continue
        if line.strip():
            sections.setdefault(current, []).append(line.rstrip())
    return sections


def _extract_contact(header_lines: list[str], full_text: str) -> ContactInfo:
    header = "\n".join(header_lines[:8])
    contact = ContactInfo()
    if m := EMAIL_RE.search(full_text):
        contact.email = m.group(0)
    if m := PHONE_RE.search(header or full_text):
        digits = re.sub(r"\D", "", m.group(1))
        if 8 <= len(digits) <= 15:
            contact.phone = m.group(1).strip()
    if m := LINKEDIN_RE.search(full_text):
        contact.linkedin = m.group(0)
    if m := GITHUB_RE.search(full_text):
        contact.github = m.group(0)
    # Name: first non-empty header line that isn't contact data or a heading.
    for line in header_lines[:4]:
        s = line.strip()
        if not s or EMAIL_RE.search(s) or PHONE_RE.search(s) or URL_RE.fullmatch(s):
            continue
        if len(s.split()) <= 5 and not any(c.isdigit() for c in s):
            contact.name = s
            break
    return contact


def _extract_experience(lines: list[str]) -> list[ExperienceItem]:
    """Group lines into roles: a non-bullet line with a date range (or followed
    closely by one) starts a new role; bullets attach to the current role."""
    items: list[ExperienceItem] = []
    current: Optional[ExperienceItem] = None

    for line in lines:
        bullet = BULLET_RE.match(line)
        date_m = DATE_RANGE_RE.search(line)
        if bullet:
            if current is None:
                current = ExperienceItem(raw=line)
                items.append(current)
            current.bullets.append(bullet.group(1).strip())
            current.raw += "\n" + line
        elif date_m or current is None or not current.bullets:
            header_text = DATE_RANGE_RE.sub("", line).strip(" |,-–—")
            # A bare date line right after a role header belongs to that role.
            if (date_m and current is not None and not header_text
                    and current.start is None and not current.bullets):
                current.start = _normalize_date(date_m.group("start"))
                current.end = _normalize_date(date_m.group("end"))
                current.raw += "\n" + line
            elif date_m or current is None:
                current = ExperienceItem(raw=line)
                items.append(current)
                if date_m:
                    current.start = _normalize_date(date_m.group("start"))
                    current.end = _normalize_date(date_m.group("end"))
                _fill_title_company(current, header_text)
            else:
                # Continuation of a role header (e.g. company on next line)
                header_text = DATE_RANGE_RE.sub("", line).strip(" |,-–—")
                if current.company is None and header_text:
                    _fill_title_company(current, header_text)
                current.raw += "\n" + line
        else:
            # After bullets, a short heading-like line starts the next role.
            stripped = line.strip()
            if len(stripped) <= 70 and not stripped.endswith((".", "!", "?")):
                current = ExperienceItem(raw=line)
                items.append(current)
                _fill_title_company(current, stripped.strip(" |,-–—"))
            else:
                current.raw += "\n" + line
    return [i for i in items if i.raw.strip()]


def _fill_title_company(item: ExperienceItem, header_text: str) -> None:
    if not header_text:
        return
    parts = re.split(r"\s+[|@•]\s+|\s+-\s+|,\s+", header_text, maxsplit=1)
    if item.title is None:
        item.title = parts[0].strip() or None
        if len(parts) > 1 and item.company is None:
            item.company = parts[1].strip() or None
    elif item.company is None:
        item.company = header_text.strip() or None


def _extract_education(lines: list[str]) -> list[EducationItem]:
    items: list[EducationItem] = []
    degree_re = re.compile(
        r"(bachelor|master|b\.?sc|m\.?sc|b\.?e\b|b\.?tech|m\.?tech|mba|ph\.?d|diploma|associate)", re.I)
    current: Optional[EducationItem] = None
    for line in lines:
        year_m = re.search(r"(19|20)\d{2}", line)
        if degree_re.search(line) or current is None:
            current = EducationItem(raw=line)
            items.append(current)
            if degree_re.search(line):
                current.degree = line.strip()
            else:
                current.institution = line.strip()
        else:
            current.raw += "\n" + line
            if current.institution is None and not degree_re.search(line):
                current.institution = line.strip()
        if year_m and current and current.year is None:
            current.year = year_m.group(0)
    return items


def _extract_projects(lines: list[str]) -> list[ProjectItem]:
    items: list[ProjectItem] = []
    current: Optional[ProjectItem] = None
    for line in lines:
        bullet = BULLET_RE.match(line)
        if bullet and current is not None:
            current.bullets.append(bullet.group(1).strip())
            current.raw += "\n" + line
        else:
            name = BULLET_RE.sub(r"\1", line).strip()
            current = ProjectItem(name=name.split("|")[0].split("–")[0].strip()[:80] or None, raw=line)
            items.append(current)
    return items


def _extract_list(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        line = BULLET_RE.sub(r"\1", line)
        # split on common delimiters
        for token in re.split(r"[|,;•·]", line):
            token = re.sub(r"^[\w &/+.-]{0,25}:\s*", "", token.strip())  # drop "Languages:" prefixes
            token = token.strip(" .")
            if token and len(token) <= 40:
                out.append(token)
    seen, deduped = set(), []
    for s in out:
        if s.lower() not in seen:
            seen.add(s.lower())
            deduped.append(s)
    return deduped


def extract_resume(raw_text: str, page_count: int = 1) -> ResumeDoc:
    sections = split_sections(raw_text)
    lines = [ln for ln in raw_text.splitlines() if ln.strip()]
    bullets = [m.group(1).strip() for ln in lines if (m := BULLET_RE.match(ln))]

    return ResumeDoc(
        raw_text=raw_text,
        contact=_extract_contact(sections.get("header", []), raw_text),
        summary=" ".join(sections.get("summary", []))[:1500],
        experience=_extract_experience(sections.get("experience", [])),
        education=_extract_education(sections.get("education", [])),
        projects=_extract_projects(sections.get("projects", [])),
        skills=_extract_list(sections.get("skills", [])),
        certifications=_extract_list(sections.get("certifications", [])),
        sections_found=[k for k in sections if k != "header" and sections[k]],
        bullet_lines=bullets,
        word_count=len(raw_text.split()),
        line_count=len(lines),
        page_count=page_count,
    )


def extract_job(raw_text: str) -> JobDoc:
    """Structure a JD: title guess, years-of-experience requirement.

    Skill lists are filled in later by the taxonomy-based extractor, which is
    far more reliable than heading heuristics for JDs.
    """
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    title = lines[0][:120] if lines else None

    years = None
    m = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:relevant\s+)?experience", raw_text, re.I)
    if m:
        years = float(m.group(1))
    return JobDoc(raw_text=raw_text, title=title, min_years_experience=years)
