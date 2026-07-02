"""Merge deterministic findings and AI insights into a prioritized action list."""
from __future__ import annotations

from app.models.schemas import ActionItem, AiAnalysis, AtsReport, ScoreBreakdown, SkillGap


def build_actions(
    ats: AtsReport, gap: SkillGap, scores: ScoreBreakdown, ai: AiAnalysis | None,
) -> list[ActionItem]:
    actions: list[ActionItem] = []

    # --- skills gaps: missing required skills are the highest-leverage fix
    required_missing = [m.name for m in gap.missing if m.importance == "required"]
    preferred_missing = [m.name for m in gap.missing if m.importance == "preferred"]
    if required_missing:
        actions.append(ActionItem(
            priority="high", source="skills",
            title=f"Address {len(required_missing)} missing required skill(s)",
            detail="The JD requires: " + ", ".join(required_missing[:8]) +
                   ". If you have genuine exposure, surface it in your skills section and "
                   "bullets; if not, these are the gaps to close (or address in a cover letter).",
        ))
    if preferred_missing:
        actions.append(ActionItem(
            priority="medium", source="skills",
            title="Add preferred skills where truthful",
            detail="Nice-to-haves in the JD not found on your resume: " +
                   ", ".join(preferred_missing[:8]) + ".",
        ))

    # --- ATS categories: rank failed categories by points lost
    losses = sorted(
        ((c, c.max_score - c.score) for c in ats.categories),
        key=lambda t: t[1], reverse=True,
    )
    for cat, lost in losses:
        if lost <= 0:
            continue
        failed = [ch for ch in cat.checks if not ch.passed]
        if not failed:
            continue
        pct_lost = lost / ats.max_score
        priority = "high" if pct_lost >= 0.05 else "medium" if pct_lost >= 0.02 else "low"
        actions.append(ActionItem(
            priority=priority, source="ats",
            title=f"Improve {cat.name} ({cat.score:g}/{cat.max_score:g})",
            detail=" ".join(f"{ch.rule}: {ch.explanation}" for ch in failed[:2]),
        ))

    # --- semantic alignment
    if scores.semantic_match < 50:
        actions.append(ActionItem(
            priority="high", source="matching",
            title="Tailor your resume language to this job description",
            detail="Semantic similarity between your resume and the JD is low "
                   f"({scores.semantic_match:.0f}/100). Mirror the JD's terminology in your "
                   "summary and most recent role — same domain vocabulary, not copied sentences.",
        ))

    # --- AI recommendations
    if ai:
        for i, rec in enumerate(ai.recommendations[:6]):
            actions.append(ActionItem(
                priority="high" if i < 2 else "medium" if i < 4 else "low",
                source="ai", title=rec.split(".")[0][:90], detail=rec,
            ))

    order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: order[a.priority])
    return actions[:14]
