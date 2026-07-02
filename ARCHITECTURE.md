# Resume Intelligence Platform — Architecture

AI-powered resume analysis against a Job Description (JD) using document parsing, NLP,
semantic embeddings, deterministic ATS scoring, and Claude 5 (Fable) — presented in a
SaaS-grade analytics dashboard. Every score is explainable: each number is traceable to
rules that fired, similarity values, or model rationale.

---

## 1. System Overview

```
Resume (PDF/DOCX) + Job Description (text/PDF)
        │
        ▼
┌───────────────────────────┐
│  Document Parsing Layer   │  PyMuPDF / pdfplumber / python-docx
└───────────┬───────────────┘
            ▼
   Structured Resume & JD JSON (sections, contact, experience, skills…)
            │
   ┌────────┼─────────────────────┐
   ▼        ▼                     ▼
ATS Rule  Embedding Engine    Skill Extraction
Engine    (sentence-           (taxonomy + NLP)
(13 rule   transformers,
 groups)   cosine similarity)
   │        │                     │
   ▼        ▼                     ▼
ATS Score  Semantic Match     Skill Gap Analysis
(explained) (overall + per-    (present / missing /
             dimension)         partial)
   └────────┼─────────────────────┘
            ▼
┌───────────────────────────┐
│   Claude 5 Analysis       │  structured JSON output, refusal fallback → Opus 4.8
└───────────┬───────────────┘
            ▼
┌───────────────────────────┐
│  Recommendation Engine    │  merges rule findings + AI insights → prioritized actions
└───────────┬───────────────┘
            ▼
   Interactive Analytics Dashboard (Next.js)
```

### Design principles

1. **Explainability first** — the ATS engine is deterministic; every rule returns
   `(score, max_score, evidence, explanation)`. Semantic scores expose the raw cosine
   values. Claude output is structured and cited against resume text.
2. **Graceful degradation** — the platform works without the heavy ML stack:
   - No `sentence-transformers` installed → TF-IDF cosine fallback (flagged in response).
   - No `ANTHROPIC_API_KEY` → deterministic analysis only, AI panels show a notice.
3. **Modular services** — each pipeline stage is an isolated service with typed
   inputs/outputs (Pydantic), composed by a single orchestrator.
4. **Stateless API + persisted analyses** — each analysis is stored (SQLite dev /
   PostgreSQL prod) and retrievable by ID.

---

## 2. Repository Layout

```
resume_intelligence_platform/
├── ARCHITECTURE.md
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py                    # FastAPI app factory, CORS, routers
│       ├── core/
│       │   ├── config.py              # pydantic-settings, env config
│       │   └── exceptions.py          # typed domain errors → HTTP errors
│       ├── api/
│       │   └── routes/
│       │       ├── health.py          # GET /api/health (component status)
│       │       └── analysis.py        # POST /api/analyze, GET /api/analyses[/id]
│       ├── models/
│       │   └── schemas.py             # All Pydantic contracts (single source of truth)
│       ├── db/
│       │   ├── database.py            # SQLAlchemy engine/session
│       │   └── models.py              # Analysis ORM model (JSON result column)
│       └── services/
│           ├── orchestrator.py        # runs the full pipeline
│           ├── parsing/
│           │   ├── document_parser.py # PDF/DOCX/TXT → raw text (+ layout stats)
│           │   └── section_extractor.py # raw text → structured ResumeDoc / JobDoc
│           ├── ats/
│           │   └── engine.py          # 13 deterministic rule groups → AtsReport
│           ├── matching/
│           │   └── embedding_engine.py # ST model (lazy) or TF-IDF fallback; cosine
│           ├── skills/
│           │   ├── taxonomy.py        # curated tech-skill taxonomy + aliases
│           │   └── extractor.py       # skill extraction + gap analysis
│           ├── ai/
│           │   └── claude_analyzer.py # Claude Fable 5, structured JSON, fallbacks
│           └── recommendations/
│               └── engine.py          # merge signals → prioritized actions
└── frontend/
    ├── package.json / tsconfig.json / tailwind.config.ts / next.config.mjs
    └── src/
        ├── app/
        │   ├── layout.tsx / globals.css
        │   └── page.tsx               # upload → analyze → dashboard
        ├── lib/
        │   ├── api.ts                 # typed API client
        │   └── types.ts               # mirrors backend schemas
        └── components/
            ├── upload/UploadPanel.tsx
            └── dashboard/
                ├── Dashboard.tsx          # layout + section composition
                ├── ScoreGauge.tsx         # overall match gauge
                ├── AtsScoreCard.tsx       # ATS score + category bars
                ├── RadarProfile.tsx       # 8-axis spider chart
                ├── SkillCoverage.tsx      # coverage bar chart
                ├── KeywordChips.tsx       # present vs missing chips
                ├── ExperienceTimeline.tsx # roles over time
                ├── PriorityActions.tsx    # High/Med/Low action panel
                └── ExplainScore.tsx       # score breakdown accordion
```

---

## 3. API Design

Base URL: `http://localhost:8000`

| Method | Path                 | Description |
|--------|----------------------|-------------|
| GET    | `/api/health`        | Service + component availability (embeddings model, Claude, DB) |
| POST   | `/api/analyze`       | Multipart: `resume` file (PDF/DOCX/TXT) + `job_description` text or `jd_file`. Runs full pipeline, persists, returns `AnalysisResult`. |
| GET    | `/api/analyses`      | List past analyses (id, filename, scores, created_at) |
| GET    | `/api/analyses/{id}` | Full stored `AnalysisResult` |

### `AnalysisResult` (response contract, abridged)

```jsonc
{
  "id": "a1b2…",
  "created_at": "…",
  "resume": { "contact": {…}, "sections": {…}, "experience": [...], "skills": [...] },
  "scores": {
    "overall_match": 78.4,          // weighted blend (weights returned too)
    "semantic_match": 71.2,
    "skills_match": 82.0,
    "experience_match": 75.0,
    "project_match": 68.0,
    "education_match": 90.0,
    "weights": { "skills": 0.35, "semantic": 0.25, ... }
  },
  "ats": {
    "total_score": 84, "max_score": 100,
    "categories": [ { "name": "Contact Information", "score": 9, "max": 10,
                      "checks": [ {"rule": "...", "passed": true, "evidence": "...",
                                   "explanation": "..."} ] } ]
  },
  "skills": {
    "matched": [ {"name": "Python", "source": "resume+jd"} ],
    "missing": [ {"name": "Kubernetes", "importance": "required"} ],
    "resume_only": [...]
  },
  "radar": { "technical_skills": 82, "project_quality": 70, "experience": 75,
             "ats_compatibility": 84, "writing_quality": 77, "leadership": 55,
             "readability": 80, "resume_structure": 88 },
  "timeline": [ {"title": "...", "company": "...", "start": "2022-07", "end": null} ],
  "ai": {                                  // null if Claude unavailable
    "model": "claude-fable-5",
    "summary": "...",
    "strengths": [...], "weaknesses": [...],
    "weak_bullets": [ {"original": "...", "issue": "...", "improved": "..."} ],
    "recommendations": [...]
  },
  "actions": [ {"priority": "high", "title": "...", "detail": "...", "source": "ats|ai|skills"} ],
  "meta": { "embedding_backend": "sentence-transformers|tfidf", "ai_available": true }
}
```

---

## 4. Scoring Model (explainable by construction)

**Overall Match** = weighted blend, weights returned in the payload:
`0.35·skills + 0.25·semantic + 0.20·experience + 0.10·projects + 0.10·education`

- **Skills match** — Jaccard-style coverage of JD skills found in resume (taxonomy-normalized),
  required skills weighted 2× preferred.
- **Semantic match** — cosine similarity of resume↔JD embeddings (whole-doc plus
  section-vs-JD for experience/projects), calibrated from raw cosine to 0–100.
- **Experience / project / education match** — section-level embedding similarity plus
  rule signals (years detected vs JD requirement, quantified projects, degree keywords).
- **ATS score** — 13 deterministic rule groups (structure, contact, sections, bullets,
  action verbs, grammar heuristics, readability, length, formatting, quantified
  achievements, project quality, technical skills, leadership). Each check contributes
  points and carries evidence + explanation → “Explain My Score” panel renders directly
  from this data.

## 5. Claude Integration

- Model: `claude-fable-5`; server-side refusal fallback to `claude-opus-4-8`
  (`betas=["server-side-fallback-2026-06-01"]`) so benign resumes never fail on a
  classifier false positive.
- Structured output enforced with `output_config.format` (JSON schema) — the response
  parses directly into the `AiAnalysis` Pydantic model; no free-text scraping.
- Thinking: omitted (always-on for Fable 5); `output_config.effort: "medium"` — resume
  critique is not a max-effort task and this keeps latency reasonable.
- The prompt receives the *structured* resume JSON + JD + deterministic findings so the
  model critiques rather than re-derives, and grounds suggestions in actual bullets.
- `stop_reason == "refusal"` after the whole chain → `ai: null`, pipeline still returns
  the deterministic result.

## 6. Data & Persistence

- Dev: SQLite (`backend/resume_intel.db`), swap to PostgreSQL via `DATABASE_URL`.
- One table `analyses`: id (uuid), filename, created_at, overall/ats score columns for
  cheap listing, full `AnalysisResult` as JSON.

## 7. Development Roadmap

| Phase | Deliverable |
|-------|-------------|
| 1 | Architecture, contracts, scaffolding (this document) |
| 2 | Parsing layer: PDF/DOCX → raw text → structured sections |
| 3 | ATS rule engine (13 groups, explainable checks) |
| 4 | Embeddings + similarity (+ TF-IDF fallback), skill taxonomy & gap analysis |
| 5 | Claude analyzer + recommendation engine + orchestrator + API + DB |
| 6 | Frontend: upload flow, dashboard (gauge, radar, chips, timeline, actions, explain) |
| 7 | Polish: loading/error states, history list, README, smoke tests |
