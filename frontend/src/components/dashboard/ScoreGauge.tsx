"use client";

import { motion } from "framer-motion";

/** Overall match gauge — hero number with a semicircular progress arc. */
export default function ScoreGauge({ score }: { score: number }) {
  const r = 80;
  const circumference = Math.PI * r; // semicircle
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);

  const label =
    clamped >= 75 ? "Strong match" : clamped >= 55 ? "Moderate match" : "Weak match";

  return (
    <div className="card flex flex-col items-center p-6">
      <h3 className="self-start text-sm font-medium text-ink-2">Overall Match</h3>
      <svg viewBox="0 0 200 110" className="mt-2 w-full max-w-[260px]">
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="var(--gridline)"
          strokeWidth="10"
          strokeLinecap="round"
        />
        <motion.path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="var(--series-1)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <text
          x="100"
          y="86"
          textAnchor="middle"
          className="fill-ink"
          style={{ fill: "var(--text-primary)", fontSize: "34px", fontWeight: 600 }}
        >
          {clamped.toFixed(0)}
        </text>
        <text
          x="100"
          y="104"
          textAnchor="middle"
          style={{ fill: "var(--text-muted)", fontSize: "11px" }}
        >
          / 100
        </text>
      </svg>
      <p className="mt-1 text-sm text-ink-2">{label}</p>
    </div>
  );
}
