"use client";

import { Sparkles } from "lucide-react";
import type { AiAnalysis } from "@/lib/types";

export default function AiInsights({
  ai,
  aiError,
}: {
  ai: AiAnalysis | null;
  aiError?: string | null;
}) {
  if (!ai) {
    return (
      <div className="card p-6">
        <h3 className="flex items-center gap-1.5 text-sm font-medium text-ink-2">
          <Sparkles className="h-4 w-4" /> AI Analysis
        </h3>
        <p className="mt-3 text-sm text-muted">
          {aiError ?? "AI analysis unavailable for this run."} The deterministic
          scores above are unaffected.
        </p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <div className="flex items-baseline justify-between">
        <h3 className="flex items-center gap-1.5 text-sm font-medium text-ink-2">
          <Sparkles className="h-4 w-4" /> AI Analysis
        </h3>
        <span className="text-[10px] uppercase text-muted">{ai.model}</span>
      </div>

      <p className="mt-3 text-sm leading-relaxed">{ai.summary}</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1.5 text-xs font-medium" style={{ color: "var(--delta-good-text)" }}>
            Strengths
          </p>
          <ul className="list-disc space-y-1 pl-4 text-xs text-ink-2">
            {ai.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1.5 text-xs font-medium text-critical">Weaknesses</p>
          <ul className="list-disc space-y-1 pl-4 text-xs text-ink-2">
            {ai.weaknesses.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      </div>

      {ai.weak_bullets.length > 0 && (
        <div className="mt-5">
          <p className="mb-2 text-xs font-medium text-muted">Bullet rewrites</p>
          <ul className="space-y-3">
            {ai.weak_bullets.map((b, i) => (
              <li key={i} className="rounded-lg border border-hairline p-3 text-xs">
                <p className="text-muted line-through decoration-critical/50">
                  {b.original}
                </p>
                <p className="mt-1 italic text-ink-2">{b.issue}</p>
                <p className="mt-1.5 font-medium">{b.improved}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {ai.career_progression && (
        <div className="mt-5">
          <p className="mb-1 text-xs font-medium text-muted">Career progression</p>
          <p className="text-xs leading-relaxed text-ink-2">{ai.career_progression}</p>
        </div>
      )}
    </div>
  );
}
