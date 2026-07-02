"use client";

import type { AnalysisResult } from "@/lib/types";
import ScoreGauge from "./ScoreGauge";
import AtsScoreCard from "./AtsScoreCard";
import RadarProfileChart from "./RadarProfile";
import SkillCoverage from "./SkillCoverage";
import KeywordChips from "./KeywordChips";
import ExperienceTimeline from "./ExperienceTimeline";
import PriorityActions from "./PriorityActions";
import ExplainScore from "./ExplainScore";
import AiInsights from "./AiInsights";

export default function Dashboard({ result }: { result: AnalysisResult }) {
  return (
    <div className="space-y-6">
      {/* header strip */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
        <span>{result.meta.resume_filename}</span>
        <span>·</span>
        <span>{result.job.title ?? "Job description"}</span>
        <span>·</span>
        <span>similarity backend: {result.meta.embedding_backend}</span>
        {!result.meta.ai_available && (
          <>
            <span>·</span>
            <span className="text-warning">AI analysis off</span>
          </>
        )}
      </div>

      {/* top row: gauge / radar / ats */}
      <div className="grid gap-6 lg:grid-cols-3">
        <ScoreGauge score={result.scores.overall_match} />
        <RadarProfileChart radar={result.radar} />
        <AtsScoreCard ats={result.ats} />
      </div>

      {/* second row */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SkillCoverage scores={result.scores} />
        <KeywordChips gap={result.skills} />
      </div>

      {/* third row */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AiInsights ai={result.ai} aiError={result.meta.ai_error} />
        </div>
        <ExperienceTimeline timeline={result.timeline} />
      </div>

      {/* actions + explainability */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PriorityActions actions={result.actions} />
        <ExplainScore scores={result.scores} ats={result.ats} />
      </div>
    </div>
  );
}
