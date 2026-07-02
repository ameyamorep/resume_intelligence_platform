"use client";

import { useCallback, useRef, useState } from "react";
import { FileText, Loader2, UploadCloud } from "lucide-react";
import clsx from "clsx";

interface Props {
  onAnalyze: (resume: File, jd: string, jdFile: File | null) => void;
  loading: boolean;
  error: string | null;
}

export default function UploadPanel({ onAnalyze, loading, error }: Props) {
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) setResume(file);
  }, []);

  const canSubmit = !!resume && (jd.trim().length > 30 || !!jdFile) && !loading;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Resume dropzone */}
      <section className="card p-6">
        <h2 className="mb-1 text-sm font-medium">Resume</h2>
        <p className="mb-4 text-xs text-muted">PDF, DOCX or TXT — max 10 MB</p>
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={clsx(
            "flex h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed transition-colors",
            dragging ? "border-brand bg-brand/5" : "border-grid hover:border-brand/60",
          )}
        >
          {resume ? (
            <>
              <FileText className="h-8 w-8 text-brand" />
              <div className="text-center">
                <p className="text-sm font-medium">{resume.name}</p>
                <p className="text-xs text-muted">
                  {(resume.size / 1024).toFixed(0)} KB — click to replace
                </p>
              </div>
            </>
          ) : (
            <>
              <UploadCloud className="h-8 w-8 text-muted" />
              <p className="text-sm text-ink-2">
                Drop your resume here or <span className="text-brand">browse</span>
              </p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => setResume(e.target.files?.[0] ?? null)}
          />
        </div>
      </section>

      {/* Job description */}
      <section className="card p-6">
        <h2 className="mb-1 text-sm font-medium">Job description</h2>
        <p className="mb-4 text-xs text-muted">Paste the JD text (or attach a file)</p>
        <textarea
          value={jd}
          onChange={(e) => setJd(e.target.value)}
          placeholder="Paste the full job description here…"
          className="h-48 w-full resize-none rounded-lg border border-hairline bg-transparent p-3 text-sm outline-none placeholder:text-muted focus:border-brand"
        />
        <div className="mt-3 flex items-center justify-between text-xs text-muted">
          <label className="cursor-pointer text-brand hover:underline">
            {jdFile ? jdFile.name : "…or attach a JD file"}
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <span className="tabular">{jd.trim().length} chars</span>
        </div>
      </section>

      <div className="lg:col-span-2">
        {error && (
          <div className="mb-4 rounded-lg border border-critical/40 bg-critical/5 px-4 py-3 text-sm text-critical">
            {error}
          </div>
        )}
        <button
          disabled={!canSubmit}
          onClick={() => resume && onAnalyze(resume, jd, jdFile)}
          className={clsx(
            "flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-white transition-all",
            canSubmit ? "hover:brightness-110" : "cursor-not-allowed opacity-40",
          )}
          style={{
            background: "linear-gradient(135deg, var(--series-1), var(--series-5))",
            boxShadow: canSubmit ? "0 8px 24px -8px rgba(57,135,229,0.6)" : "none",
          }}
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Analyzing — parsing, scoring, asking Claude…" : "Analyze match"}
        </button>
      </div>
    </div>
  );
}
