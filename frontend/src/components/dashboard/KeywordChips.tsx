"use client";

import { Check, X } from "lucide-react";
import type { SkillGap } from "@/lib/types";

/** Present vs missing JD keywords. Status color + icon + label (never color alone). */
export default function KeywordChips({ gap }: { gap: SkillGap }) {
  return (
    <div className="card p-6">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-ink-2">Keyword Match</h3>
        <span className="tabular text-sm text-ink-2">
          {gap.coverage_pct.toFixed(0)}% coverage
        </span>
      </div>

      <p className="mb-2 mt-4 text-xs font-medium text-muted">
        Present ({gap.matched.length})
      </p>
      <div className="flex flex-wrap gap-1.5">
        {gap.matched.map((s) => (
          <span
            key={s.name}
            className="inline-flex items-center gap-1 rounded-full border border-hairline px-2.5 py-1 text-xs"
            style={{ color: "var(--delta-good-text)" }}
          >
            <Check className="h-3 w-3" /> {s.name}
          </span>
        ))}
        {gap.matched.length === 0 && (
          <span className="text-xs text-muted">No JD skills found on the resume.</span>
        )}
      </div>

      <p className="mb-2 mt-4 text-xs font-medium text-muted">
        Missing ({gap.missing.length})
      </p>
      <div className="flex flex-wrap gap-1.5">
        {gap.missing.map((s) => (
          <span
            key={s.name}
            className="inline-flex items-center gap-1 rounded-full border border-hairline px-2.5 py-1 text-xs text-critical"
            title={s.importance === "required" ? "Required by the JD" : "Preferred by the JD"}
          >
            <X className="h-3 w-3" /> {s.name}
            {s.importance === "required" && (
              <span className="ml-0.5 rounded bg-critical/10 px-1 text-[10px] uppercase">
                req
              </span>
            )}
          </span>
        ))}
        {gap.missing.length === 0 && (
          <span className="text-xs" style={{ color: "var(--delta-good-text)" }}>
            All JD skills covered.
          </span>
        )}
      </div>

      {gap.resume_only.length > 0 && (
        <>
          <p className="mb-2 mt-4 text-xs font-medium text-muted">
            On resume, not in JD ({gap.resume_only.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {gap.resume_only.map((s) => (
              <span
                key={s}
                className="rounded-full border border-hairline px-2.5 py-1 text-xs text-ink-2"
              >
                {s}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
