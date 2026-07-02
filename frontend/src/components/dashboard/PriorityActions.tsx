"use client";

import { AlertTriangle, ArrowDown, Flame } from "lucide-react";
import type { ActionItem } from "@/lib/types";

const META = {
  high: { label: "High priority", icon: Flame, color: "var(--status-critical)" },
  medium: { label: "Medium priority", icon: AlertTriangle, color: "var(--status-serious)" },
  low: { label: "Low priority", icon: ArrowDown, color: "var(--text-muted)" },
} as const;

export default function PriorityActions({ actions }: { actions: ActionItem[] }) {
  const groups = (["high", "medium", "low"] as const)
    .map((p) => ({ p, items: actions.filter((a) => a.priority === p) }))
    .filter((g) => g.items.length > 0);

  return (
    <div className="card p-6">
      <h3 className="text-sm font-medium text-ink-2">Priority Actions</h3>
      <div className="mt-4 space-y-5">
        {groups.map(({ p, items }) => {
          const { label, icon: Icon, color } = META[p];
          return (
            <div key={p}>
              <p className="mb-2 flex items-center gap-1.5 text-xs font-medium" style={{ color }}>
                <Icon className="h-3.5 w-3.5" /> {label}
              </p>
              <ul className="space-y-2">
                {items.map((a, i) => (
                  <li key={i} className="rounded-lg border border-hairline p-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium">{a.title}</p>
                      <span className="shrink-0 rounded bg-grid px-1.5 py-0.5 text-[10px] uppercase text-muted">
                        {a.source}
                      </span>
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-ink-2">{a.detail}</p>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
        {groups.length === 0 && (
          <p className="text-sm text-muted">No actions — this resume is in great shape.</p>
        )}
      </div>
    </div>
  );
}
