"""Provider-pluggable AI analysis layer.

Free options (Gemini free tier, Groq free tier, local Ollama) plus the paid
Anthropic path. All free providers are called over plain REST with httpx
(already installed as an anthropic dependency) — no extra packages.

Every provider must return JSON matching AI_SCHEMA; responses are coerced and
validated into the AiAnalysis Pydantic model, so the rest of the pipeline and
the frontend are provider-agnostic.
"""
from __future__ import annotations

import json
import logging
import re

import httpx

from app.core.config import get_settings
from app.models.schemas import AiAnalysis, AtsReport, JobDoc, ResumeDoc, SkillGap

logger = logging.getLogger(__name__)

AI_SCHEMA = {
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
specific and actionable, 5-8 items, most impactful first.

Respond ONLY with a JSON object matching this schema (no markdown, no prose):
""" + json.dumps(AI_SCHEMA)

_DEFAULTS: dict = {
    "summary": "", "strengths": [], "weaknesses": [], "weak_bullets": [],
    "missing_quantification": [], "grammar_issues": [],
    "career_progression": "", "recommendations": [],
}


def resolve_provider() -> str:
    s = get_settings()
    p = s.ai_provider.lower().strip()
    if p != "auto":
        return p
    if s.anthropic_api_key:
        return "anthropic"
    if s.gemini_api_key:
        return "gemini"
    if s.groq_api_key:
        return "groq"
    if _ollama_reachable():
        return "ollama"
    return "none"


def _ollama_reachable() -> bool:
    try:
        httpx.get(get_settings().ollama_base_url + "/api/tags", timeout=2.0)
        return True
    except Exception:
        return False


def run_ai_analysis(
    resume: ResumeDoc, job: JobDoc, ats: AtsReport, gap: SkillGap,
    semantic_match: float,
) -> tuple[AiAnalysis | None, str | None]:
    """Returns (analysis, error). Exactly one of the two is None."""
    provider = resolve_provider()
    if provider == "none":
        return None, ("No AI provider configured. Set GEMINI_API_KEY or GROQ_API_KEY "
                      "(both free), run Ollama locally, or set ANTHROPIC_API_KEY.")

    user_prompt = "Analyze this candidate:\n\n" + json.dumps({
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
    }, default=str)

    try:
        if provider == "anthropic":
            from app.services.ai.claude_analyzer import run_claude_analysis
            return run_claude_analysis(resume, job, ats, gap, semantic_match)
        if provider == "gemini":
            raw, model = _call_gemini(user_prompt)
        elif provider == "groq":
            raw, model = _call_groq(user_prompt)
        elif provider == "ollama":
            raw, model = _call_ollama(user_prompt)
        else:
            return None, f"Unknown AI_PROVIDER '{provider}'."
        return _parse(raw, model)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:300]
        logger.error("%s API error %s: %s", provider, exc.response.status_code, detail)
        return None, f"{provider} API error {exc.response.status_code}: {detail}"
    except Exception as exc:
        logger.exception("%s analysis failed", provider)
        return None, f"AI analysis failed ({provider}): {exc}"


# ------------------------------------------------------------------ providers


def _call_gemini(user_prompt: str) -> tuple[str, str]:
    """Google Gemini — free tier. Native JSON-schema constrained output."""
    s = get_settings()
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{s.gemini_model}:generateContent")
    # Gemini's responseSchema dialect doesn't accept additionalProperties.
    resp = httpx.post(
        url,
        params={"key": s.gemini_api_key},
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": AI_SCHEMA,
                # Gemini 2.5 thinking tokens count against maxOutputTokens and can
                # truncate the JSON mid-object. Structured critique doesn't need
                # thinking here — disable it and leave generous output headroom.
                "maxOutputTokens": 16384,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        candidate = data["candidates"][0]
        text = candidate["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        reason = (data.get("candidates") or [{}])[0].get("finishReason", "unknown")
        raise RuntimeError(f"Gemini returned no text (finishReason={reason})")
    if candidate.get("finishReason") == "MAX_TOKENS":
        raise RuntimeError("Gemini output hit MAX_TOKENS and was truncated — "
                           "increase maxOutputTokens or shorten the input.")
    return text, s.gemini_model


def _call_groq(user_prompt: str) -> tuple[str, str]:
    """Groq — free tier, OpenAI-compatible endpoint, JSON mode."""
    s = get_settings()
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {s.groq_api_key}"},
        json={
            "model": s.groq_model,
            "temperature": 0.3,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"], s.groq_model


def _call_ollama(user_prompt: str) -> tuple[str, str]:
    """Local Ollama — fully free/offline. `format` enforces the JSON schema."""
    s = get_settings()
    resp = httpx.post(
        s.ollama_base_url + "/api/chat",
        json={
            "model": s.ollama_model,
            "stream": False,
            "format": AI_SCHEMA,
            "options": {"temperature": 0.3, "num_ctx": 8192},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=600.0,  # local models can be slow on CPU
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"], s.ollama_model


# ------------------------------------------------------------------ parsing


def _parse(raw: str, model: str) -> tuple[AiAnalysis | None, str | None]:
    """Tolerant parse: strip code fences, fill missing keys, validate."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)  # last resort: outermost object
        if not m:
            return None, f"{model} did not return valid JSON."
        data = json.loads(m.group(0))

    merged = {**_DEFAULTS, **{k: v for k, v in data.items() if k in _DEFAULTS}}
    merged["weak_bullets"] = [
        b for b in merged["weak_bullets"]
        if isinstance(b, dict) and {"original", "issue", "improved"} <= b.keys()
    ]
    return AiAnalysis(model=model, **merged), None
