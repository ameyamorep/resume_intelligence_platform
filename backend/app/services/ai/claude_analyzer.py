"""Claude 5 (Fable) resume analysis with structured JSON output.

- Model: claude-fable-5 (thinking always on — no `thinking` param sent).
- Server-side refusal fallback to claude-opus-4-8 so a safety-classifier
  false positive doesn't fail the analysis (beta: server-side-fallback-2026-06-01).
- Output constrained with output_config.format (JSON schema) and validated
  into the AiAnalysis Pydantic model — no free-text scraping.
- If the API key is missing or the whole chain refuses, returns (None, reason)
  and the deterministic pipeline result stands on its own.
"""
from __future__ import annotations

import json
import logging

from app.core.config import get_settings
from app.models.schemas import AiAnalysis, AtsReport, JobDoc, ResumeDoc, SkillGap

logger = logging.getLogger(__name__)

_AI_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "weak_bullets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "issue": {"type": "string"},
                    "improved": {"type": "string"},
                },
                "required": ["original", "issue", "improved"],
                "additionalProperties": False,
            },
        },
        "missing_quantification": {"type": "array", "items": {"type": "string"}},
        "grammar_issues": {"type": "array", "items": {"type": "string"}},
        "career_progression": {"type": "string"},
        "recommendations": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary", "strengths", "weaknesses", "weak_bullets",
        "missing_quantification", "grammar_issues", "career_progression",
        "recommendations",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a senior technical recruiter and resume coach.
You are given a candidate's structured resume, the target job description, and
the deterministic analysis already computed (ATS rule results, skill gap,
similarity scores). Critique the resume against this specific job.

Ground every observation in actual resume text — quote bullets verbatim in
weak_bullets.original. Do not restate the deterministic findings; add judgment
on top of them: writing quality, credibility of claims, career progression,
positioning against the JD, and concrete rewrites. Improved bullets must stay
truthful to the original (no invented metrics — use bracketed placeholders like
[X%] where the candidate should insert a real number). Keep recommendations
specific and actionable, 5-8 items, most impactful first."""


def run_claude_analysis(
    resume: ResumeDoc, job: JobDoc, ats: AtsReport, gap: SkillGap,
    semantic_match: float,
) -> tuple[AiAnalysis | None, str | None]:
    """Returns (analysis, error). Exactly one of the two is None."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None, "ANTHROPIC_API_KEY not configured — AI analysis skipped."

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        context = {
            "resume": resume.model_dump(exclude={"raw_text"}),
            "resume_text": resume.raw_text[:15000],
            "job_description": job.raw_text[:8000],
            "deterministic_findings": {
                "ats_score": f"{ats.total_score}/{ats.max_score}",
                "failed_checks": [
                    {"category": c.name, "rule": ch.rule, "evidence": ch.evidence}
                    for c in ats.categories for ch in c.checks if not ch.passed
                ],
                "missing_skills": [m.model_dump() for m in gap.missing],
                "matched_skills": [m.name for m in gap.matched],
                "semantic_match_score": semantic_match,
            },
        }

        response = client.beta.messages.create(
            model=settings.claude_model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            betas=["server-side-fallback-2026-06-01"],
            fallbacks=[{"model": settings.claude_fallback_model}],
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": _AI_SCHEMA},
            },
            messages=[{
                "role": "user",
                "content": "Analyze this candidate:\n\n" + json.dumps(context, default=str),
            }],
        )

        if response.stop_reason == "refusal":
            return None, "The analysis request was declined by the model's safety system."

        text = next(b.text for b in response.content if b.type == "text")
        data = json.loads(text)
        return AiAnalysis(model=response.model, **data), None

    except Exception as exc:
        logger.exception("Claude analysis failed")
        return None, f"AI analysis failed: {exc}"
