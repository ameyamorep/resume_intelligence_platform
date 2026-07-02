"use client";

import type { AtsReport } from "@/lib/types";

/** ATS score + per-category progress bars with direct value labels. */
export default function AtsScoreCard({ ats }: { ats: AtsReport }) {
  const pct = ats.max_score ? (100 * ats.total_score) / ats.max_score : 0;

  return (
    <div className="card p-6">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-ink-2">ATS Score</h3>
        <span className="tabular text-2xl font-semibold">
          {pct.toFixed(0)}
          <span className="text-sm font-normal text-muted">/100</span>
        </span>
      </div>
      <ul className="mt-4 space-y-2.5">
        {ats.categories.map((c) => {
          const p = c.max_score ? (100 * c.score) / c.max_score : 0;
          return (
            <li key={c.name}>
              <div className="mb-1 flex justify-between text-xs">
                <span className="text-ink-2">{c.name}</span>
                <span className="tabular text-muted">
                  {c.score.toFixed(0)}/{c.max_score.toFixed(0)}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-grid">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${p}%`, background: "var(--series-1)" }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
