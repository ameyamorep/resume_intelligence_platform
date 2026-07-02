# Resume Intelligence Platform

AI-powered resume analysis against any job description: document parsing, deterministic
ATS scoring, semantic embedding similarity, skill-gap analysis, and Claude 5 (Fable)
coaching — presented in an interactive analytics dashboard.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design, API contract,
scoring model, and roadmap.

## Quick start

### Backend (FastAPI, Python 3.11+)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env      # add a free GEMINI_API_KEY (or GROQ key / Ollama / Anthropic)
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Optional (better semantic matching — pulls PyTorch, ~2 GB):

```powershell
.\.venv\Scripts\pip install sentence-transformers
```

Without it the platform automatically uses a TF-IDF cosine fallback and reports
`embedding_backend: "tfidf"` in results. Without an `ANTHROPIC_API_KEY`, everything
except the Claude coaching panel still works.

Verify the pipeline without a server:

```powershell
.\.venv\Scripts\python smoke_test.py
```

### Frontend (Next.js)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — the dev server proxies `/api/*` to the backend on
port 8000 (override with `BACKEND_URL`).

## What you get

- **Upload** a resume (PDF/DOCX/TXT) + paste or attach a JD
- **Overall match gauge** — weighted blend of skills, semantic, experience, projects, education
- **ATS score card** — 13 deterministic rule groups, every check carries evidence + explanation
- **Radar profile** — 8 axes (technical skills, projects, experience, ATS, writing, leadership, readability, structure)
- **Keyword chips** — JD skills present vs missing (required flagged), plus resume-only skills
- **Experience timeline** — parsed roles with dates
- **AI analysis** — strengths/weaknesses, weak-bullet rewrites, career progression, recommendations.
  Provider-pluggable: **Google Gemini (free tier)**, **Groq (free tier)**, **local Ollama (fully free)**,
  or Anthropic Claude (`claude-fable-5` with server-side fallback to Opus 4.8). Set `AI_PROVIDER`
  in `backend/.env` or just add one key — `auto` picks whatever is configured.
- **Priority actions** — High/Medium/Low, merged from ATS rules, skill gaps, similarity, and AI
- **Explain My Score** — the exact weights, component scores, and every ATS check that fired

## Notes

- Analyses persist to SQLite (`backend/resume_intel.db`); set `DATABASE_URL` for PostgreSQL.
- `claude-fable-5` requires 30-day data retention on your Anthropic org; set
  `CLAUDE_MODEL=claude-opus-4-8` in `.env` if yours is ZDR.
- History endpoints: `GET /api/analyses`, `GET /api/analyses/{id}`.
