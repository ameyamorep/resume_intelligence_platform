"""Pydantic contracts shared across the pipeline and the API.

These models are the single source of truth for the analysis payload; the
frontend `lib/types.ts` mirrors them.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- documents


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None  # "YYYY-MM" where derivable
    end: Optional[str] = None    # None => present
    bullets: list[str] = []
    raw: str = ""


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    raw: str = ""


class ProjectItem(BaseModel):
    name: Optional[str] = None
    bullets: list[str] = []
    raw: str = ""


class ResumeDoc(BaseModel):
    """Structured resume produced by the parsing layer."""

    raw_text: str
    contact: ContactInfo = ContactInfo()
    summary: str = ""
    experience: list[ExperienceItem] = []
    education: list[EducationItem] = []
    projects: list[ProjectItem] = []
    skills: list[str] = []           # as written in the skills section
    certifications: list[str] = []
    sections_found: list[str] = []   # canonical section names detected
    bullet_lines: list[str] = []     # every bullet across the document
    word_count: int = 0
    line_count: int = 0
    page_count: int = 1


class JobDoc(BaseModel):
    raw_text: str
    title: Optional[str] = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    min_years_experience: Optional[float] = None


# ---------------------------------------------------------------- ATS


class AtsCheck(BaseModel):
    rule: str
    passed: bool
    score: float
    max_score: float
    evidence: str = ""
    explanation: str = ""


class AtsCategory(BaseModel):
    name: str
    score: float
    max_score: float
    checks: list[AtsCheck]


class AtsReport(BaseModel):
    total_score: float
    max_score: float
    categories: list[AtsCategory]

    @property
    def pct(self) -> float:
        return round(100.0 * self.total_score / self.max_score, 1) if self.max_score else 0.0


# ---------------------------------------------------------------- matching / skills


class ScoreBreakdown(BaseModel):
    overall_match: float
    semantic_match: float
    skills_match: float
    experience_match: float
    project_match: float
    education_match: float
    weights: dict[str, float]
    explanation: dict[str, str]  # per-component plain-language rationale


class SkillMatch(BaseModel):
    name: str
    importance: Literal["required", "preferred", "mentioned"] = "mentioned"


class SkillGap(BaseModel):
    matched: list[SkillMatch] = []
    missing: list[SkillMatch] = []
    resume_only: list[str] = []
    coverage_pct: float = 0.0


class RadarProfile(BaseModel):
    technical_skills: float
    project_quality: float
    experience: float
    ats_compatibility: float
    writing_quality: float
    leadership: float
    readability: float
    resume_structure: float


class TimelineEntry(BaseModel):
    title: str
    company: str
    start: Optional[str] = None
    end: Optional[str] = None


# ---------------------------------------------------------------- AI


class WeakBullet(BaseModel):
    original: str
    issue: str
    improved: str


class AiAnalysis(BaseModel):
    model: str
    summary: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    weak_bullets: list[WeakBullet] = []
    missing_quantification: list[str] = []
    grammar_issues: list[str] = []
    career_progression: str = ""
    recommendations: list[str] = []


class ActionItem(BaseModel):
    priority: Literal["high", "medium", "low"]
    title: str
    detail: str
    source: Literal["ats", "skills", "ai", "matching"]


# ---------------------------------------------------------------- top-level


class AnalysisMeta(BaseModel):
    embedding_backend: Literal["sentence-transformers", "tfidf"]
    ai_available: bool
    ai_error: Optional[str] = None
    resume_filename: str = ""


class AnalysisResult(BaseModel):
    id: str
    created_at: datetime
    resume: ResumeDoc
    job: JobDoc
    scores: ScoreBreakdown
    ats: AtsReport
    skills: SkillGap
    radar: RadarProfile
    timeline: list[TimelineEntry] = []
    ai: Optional[AiAnalysis] = None
    actions: list[ActionItem] = []
    meta: AnalysisMeta


class AnalysisSummary(BaseModel):
    """Lightweight row for the history list."""

    id: str
    created_at: datetime
    resume_filename: str
    overall_match: float
    ats_score_pct: float


class HealthStatus(BaseModel):
    status: str = "ok"
    embedding_backend: str
    claude_configured: bool  # kept for backward-compat; true when any AI provider is active
    ai_provider: str = "none"
    database: str = Field(default="ok")
