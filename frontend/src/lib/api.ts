import type { AnalysisResult } from "./types";

export async function analyzeResume(
  resume: File,
  jobDescription: string,
  jdFile?: File | null,
): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("resume", resume);
  form.append("job_description", jobDescription);
  if (jdFile) form.append("jd_file", jdFile);

  const res = await fetch("/api/analyze", { method: "POST", body: form });
  if (!res.ok) {
    let detail = `Analysis failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return res.json();
}
