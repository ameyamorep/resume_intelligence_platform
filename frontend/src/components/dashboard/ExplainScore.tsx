"use client";

import { useState } from "react";
import { Check, ChevronDown, X } from "lucide-react";
import clsx from "clsx";
import type { AtsReport, ScoreBreakdown } from "@/lib/types";

/** Full transparency: how the overall score is computed and every ATS check. */
export default function ExplainScore({
  scores,
  ats,
}: {
  scores: ScoreBreakdown;
  ats: AtsReport;
}) {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <div className="card p-6">
      <h3 className="text-sm font-medium text-ink-2">Explain My Score</h3>

      {/* Weighted blend table */}
      <div className="mt-3 overflow-hidden rounded-lg border border-hairline">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-hairline text-left text-muted">
              <th className="px-3 py-2 font-medium">Component</th>
              <th className="px-3 py-2 font-medium">Score</th>
              <th className="px-3 py-2 font-medium">Weight</th>
              <th className="hidden px-3 py-2 font-medium sm:table-cell">Why</th>
            </tr>
          </thead>
          <tbody>
            {(
              [
                ["skills", "Skills match", scores.skills_match],
                ["semantic", "Semantic match", scores.semantic_match],
                ["experience", "Experience", scores.experience_match],
                ["projects", "Projects", scores.project_match],
                ["education", "Education", scores.education_match],
              ] as const
            ).map(([key, label, value]) => (
              <tr key={key} className="border-b border-hairline last:border-0">
                <td className="px-3 py-2">{label}</td>
                <td className="tabular px-3 py-2">{value.toFixed(0)}</td>
                <td className="tabular px-3 py-2">
                  {((scores.weights[key] ?? 0) * 100).toFixed(0)}%
                </td>
                <td className="hidden px-3 py-2 text-ink-2 sm:table-cell">
                  {scores.explanation[key]}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">{scores.explanation.overall}</p>

      {/* ATS rule accordion */}
      <p className="mb-2 mt-5 text-xs font-medium text-muted">
        ATS checks ({ats.total_score.toFixed(0)}/{ats.max_score.toFixed(0)} points)
      </p>
      <div className="space-y-1.5">
        {ats.categories.map((c) => {
          const isOpen = open === c.name;
          return (
            <div key={c.name} className="rounded-lg border border-hairline">
              <button
                onClick={() => setOpen(isOpen ? null : c.name)}
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm"
              >
                <span>{c.name}</span>
                <span className="flex items-center gap-2 text-xs text-muted">
                  <span className="tabular">
                    {c.score.toFixed(0)}/{c.max_score.toFixed(0)}
                  </span>
                  <ChevronDown
                    className={clsx("h-4 w-4 transition-transform", isOpen && "rotate-180")}
                  />
                </span>
              </button>
              {isOpen && (
                <ul className="space-y-2 border-t border-hairline px-3 py-2">
                  {c.checks.map((ch) => (
                    <li key={ch.rule} className="text-xs">
                      <p className="flex items-center gap-1.5 font-medium">
                        {ch.passed ? (
                          <Check className="h-3.5 w-3.5" style={{ color: "var(--delta-good-text)" }} />
                        ) : (
                          <X className="h-3.5 w-3.5 text-critical" />
                        )}
                        {ch.rule}
                        <span className="tabular font-normal text-muted">
                          ({ch.score}/{ch.max_score})
                        </span>
                      </p>
                      <p className="ml-5 mt-0.5 text-ink-2">{ch.explanation}</p>
                      {ch.evidence && (
                        <p className="ml-5 text-muted">Evidence: {ch.evidence}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
