"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { analyzeResume } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";
import UploadPanel from "@/components/upload/UploadPanel";
import Dashboard from "@/components/dashboard/Dashboard";

export default function Home() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze(resume: File, jd: string, jdFile: File | null) {
    setLoading(true);
    setError(null);
    try {
      setResult(await analyzeResume(resume, jd, jdFile));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className="flex h-9 w-9 items-center justify-center rounded-xl text-sm font-bold text-white"
            style={{
              background: "linear-gradient(135deg, var(--series-1), var(--series-5))",
              boxShadow: "0 4px 18px -4px rgba(57,135,229,0.55)",
            }}
          >
            RI
          </span>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Resume Intelligence
            </h1>
            <p className="text-sm text-ink-2">
              Semantic matching · ATS scoring · Claude-powered coaching
            </p>
          </div>
        </div>
        {result && (
          <button
            onClick={() => setResult(null)}
            className="rounded-lg border border-hairline bg-surface px-3 py-1.5 text-sm text-ink-2 hover:text-ink"
          >
            New analysis
          </button>
        )}
      </header>

      <AnimatePresence mode="wait">
        {!result ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <UploadPanel onAnalyze={handleAnalyze} loading={loading} error={error} />
          </motion.div>
        ) : (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <Dashboard result={result} />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
