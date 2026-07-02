// Mirrors backend/app/models/schemas.py

export interface ContactInfo {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  github?: string | null;
  website?: string | null;
  location?: string | null;
}

export interface ExperienceItem {
  title?: string | null;
  company?: string | null;
  start?: string | null;
  end?: string | null;
  bullets: string[];
  raw: string;
}

export interface ResumeDoc {
  raw_text: string;
  contact: ContactInfo;
  summary: string;
  experience: ExperienceItem[];
  education: { degree?: string | null; institution?: string | null; year?: string | null; raw: string }[];
  projects: { name?: string | null; bullets: string[]; raw: string }[];
  skills: string[];
  certifications: string[];
  sections_found: string[];
  word_count: number;
  page_count: number;
}

export interface JobDoc {
  raw_text: string;
  title?: string | null;
  required_skills: string[];
  preferred_skills: string[];
  min_years_experience?: number | null;
}

export interface AtsCheck {
  rule: string;
  passed: boolean;
  score: number;
  max_score: number;
  evidence: string;
  explanation: string;
}

export interface AtsCategory {
  name: string;
  score: number;
  max_score: number;
  checks: AtsCheck[];
}

export interface AtsReport {
  total_score: number;
  max_score: number;
  categories: AtsCategory[];
}

export interface ScoreBreakdown {
  overall_match: number;
  semantic_match: number;
  skills_match: number;
  experience_match: number;
  project_match: number;
  education_match: number;
  weights: Record<string, number>;
  explanation: Record<string, string>;
}

export type SkillImportance = "required" | "preferred" | "mentioned";

export interface SkillGap {
  matched: { name: string; importance: SkillImportance }[];
  missing: { name: string; importance: SkillImportance }[];
  resume_only: string[];
  coverage_pct: number;
}

export interface RadarProfile {
  technical_skills: number;
  project_quality: number;
  experience: number;
  ats_compatibility: number;
  writing_quality: number;
  leadership: number;
  readability: number;
  resume_structure: number;
}

export interface TimelineEntry {
  title: string;
  company: string;
  start?: string | null;
  end?: string | null;
}

export interface AiAnalysis {
  model: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  weak_bullets: { original: string; issue: string; improved: string }[];
  missing_quantification: string[];
  grammar_issues: string[];
  career_progression: string;
  recommendations: string[];
}

export interface ActionItem {
  priority: "high" | "medium" | "low";
  title: string;
  detail: string;
  source: "ats" | "skills" | "ai" | "matching";
}

export interface AnalysisResult {
  id: string;
  created_at: string;
  resume: ResumeDoc;
  job: JobDoc;
  scores: ScoreBreakdown;
  ats: AtsReport;
  skills: SkillGap;
  radar: RadarProfile;
  timeline: TimelineEntry[];
  ai: AiAnalysis | null;
  actions: ActionItem[];
  meta: {
    embedding_backend: "sentence-transformers" | "tfidf";
    ai_available: boolean;
    ai_error?: string | null;
    resume_filename: string;
  };
}
