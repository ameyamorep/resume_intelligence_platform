"use client";

import type { TimelineEntry } from "@/lib/types";

function fmt(ym?: string | null): string {
  if (!ym) return "Present";
  const [y, m] = ym.split("-");
  if (!m) return y;
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[Number(m) - 1] ?? m} ${y}`;
}

export default function ExperienceTimeline({ timeline }: { timeline: TimelineEntry[] }) {
  if (timeline.length === 0) return null;
  return (
    <div className="card p-6">
      <h3 className="text-sm font-medium text-ink-2">Experience Timeline</h3>
      <ol className="mt-4 space-y-0">
        {timeline.map((t, i) => (
          <li key={i} className="relative flex gap-4 pb-5 last:pb-0">
            {/* rail */}
            <div className="flex flex-col items-center">
              <span
                className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ background: "var(--series-1)" }}
              />
              {i < timeline.length - 1 && <span className="w-px flex-1 bg-grid" />}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{t.title}</p>
              <p className="truncate text-xs text-ink-2">{t.company}</p>
              <p className="tabular mt-0.5 text-xs text-muted">
                {fmt(t.start)} — {fmt(t.end)}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
