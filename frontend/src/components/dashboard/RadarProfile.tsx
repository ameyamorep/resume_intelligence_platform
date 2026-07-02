"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { RadarProfile as RadarData } from "@/lib/types";

const AXES: { key: keyof RadarData; label: string }[] = [
  { key: "technical_skills", label: "Technical skills" },
  { key: "project_quality", label: "Projects" },
  { key: "experience", label: "Experience" },
  { key: "ats_compatibility", label: "ATS" },
  { key: "writing_quality", label: "Writing" },
  { key: "leadership", label: "Leadership" },
  { key: "readability", label: "Readability" },
  { key: "resume_structure", label: "Structure" },
];

export default function RadarProfileChart({ radar }: { radar: RadarData }) {
  const data = AXES.map((a) => ({ axis: a.label, value: radar[a.key] }));

  return (
    <div className="card p-6">
      <h3 className="text-sm font-medium text-ink-2">Candidate Profile</h3>
      <div className="mt-2 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="72%">
            <PolarGrid stroke="var(--gridline)" />
            <PolarAngleAxis
              dataKey="axis"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            />
            <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
            <Radar
              dataKey="value"
              stroke="var(--series-1)"
              strokeWidth={2}
              fill="var(--series-1)"
              fillOpacity={0.15}
              dot={{ r: 3, fill: "var(--series-1)" }}
            />
            <Tooltip
              formatter={(v: number) => [`${Number(v).toFixed(0)} / 100`, "Score"]}
              contentStyle={{
                background: "var(--surface-1)",
                border: "1px solid var(--border-hairline)",
                borderRadius: 8,
                color: "var(--text-primary)",
                fontSize: 12,
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
