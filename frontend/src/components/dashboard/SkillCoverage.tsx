"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ScoreBreakdown } from "@/lib/types";

const ROWS: { key: keyof ScoreBreakdown; label: string }[] = [
  { key: "skills_match", label: "Skills" },
  { key: "semantic_match", label: "Semantic" },
  { key: "experience_match", label: "Experience" },
  { key: "project_match", label: "Projects" },
  { key: "education_match", label: "Education" },
];

/** Component scores behind the overall match, one hue (magnitude), direct labels. */
export default function SkillCoverage({ scores }: { scores: ScoreBreakdown }) {
  const data = ROWS.map((r) => ({
    label: r.label,
    value: scores[r.key] as number,
    weight: scores.weights[r.key === "skills_match" ? "skills" : r.key.replace("_match", "")] ?? 0,
  }));

  return (
    <div className="card p-6">
      <h3 className="text-sm font-medium text-ink-2">Match Components</h3>
      <p className="mt-0.5 text-xs text-muted">
        The weighted inputs behind the overall score
      </p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 40 }}>
            <CartesianGrid horizontal={false} stroke="var(--gridline)" />
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis
              type="category"
              dataKey="label"
              width={80}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--text-secondary)", fontSize: 12 }}
            />
            <Tooltip
              cursor={{ fill: "var(--gridline)", opacity: 0.4 }}
              formatter={(v: number, _n, item) => [
                `${Number(v).toFixed(0)} / 100 (weight ${((item?.payload?.weight ?? 0) * 100).toFixed(0)}%)`,
                "Score",
              ]}
              contentStyle={{
                background: "var(--surface-1)",
                border: "1px solid var(--border-hairline)",
                borderRadius: 8,
                color: "var(--text-primary)",
                fontSize: 12,
              }}
            />
            <Bar
              dataKey="value"
              fill="var(--series-1)"
              radius={[0, 4, 4, 0]}
              barSize={14}
              label={{
                position: "right",
                fill: "var(--text-secondary)",
                fontSize: 11,
                formatter: (v: number) => Number(v).toFixed(0),
              }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
