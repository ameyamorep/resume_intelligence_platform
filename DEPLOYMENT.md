# Deployment Guide — free stack

Target architecture (both tiers free):

```
Browser ──> Vercel (Next.js frontend, free Hobby tier)
                │   /api/* rewrite (server-side proxy — no CORS in the browser)
                ▼
            Render (FastAPI backend, free web service)
                │
                ▼
            Gemini free tier (AI analysis)
```

## 0. Prerequisites

- GitHub account (repo must be pushed there — Render and Vercel deploy from GitHub)
- Render account (render.com, free) and Vercel account (vercel.com, free)
- Your Gemini API key at hand. **Never commit it** — `backend/.env` is gitignored;
  on the hosts it goes into their environment-variable settings.

## 1. Push the repo to GitHub

```powershell
cd "c:\...\resume_intelligence_platform"
git add -A
git commit -m "Resume Intelligence Platform"
git remote add origin https://github.com/<you>/resume-intelligence-platform.git
git push -u origin main
```

Sanity check before pushing: `git status` must NOT list `backend/.env`.

## 2. Deploy the backend on Render

1. Render dashboard → **New + → Blueprint** → select your repo.
   Render reads `render.yaml` and creates the `resume-intel-api` service.
2. When prompted for `GEMINI_API_KEY`, paste your key (it's marked `sync: false`
   so it is never stored in the repo).
3. Deploy. First build takes ~3–5 min. Verify:
   `https://resume-intel-api.onrender.com/api/health`
   → `{"status":"ok", "ai_provider":"gemini", ...}`

**Free-tier realities:**
- The service **sleeps after 15 min idle**; the first request after that takes
  ~50 s to wake. Fine for a portfolio/demo; upgrade to Starter to remove.
- The filesystem is **ephemeral** — the SQLite history resets on each deploy or
  restart. Each analysis still works fully; only the saved history is transient.
  For persistence, create a free Postgres at neon.tech, add
  `psycopg2-binary` to `requirements.txt`, and set `DATABASE_URL` to the Neon URL
  (`postgresql://...`).
- 512 MB RAM → do **not** install sentence-transformers here; the TF-IDF
  fallback is automatic and the dashboard labels it.

## 3. Deploy the frontend on Vercel

1. Vercel dashboard → **Add New → Project** → import the same repo.
2. Set **Root Directory** to `frontend` (Framework preset: Next.js — auto-detected).
3. Add one environment variable:
   - `BACKEND_URL` = `https://resume-intel-api.onrender.com`
4. Deploy. Your app is live at `https://<project>.vercel.app`.

## 4. Close the loop

1. Back in Render, set `CORS_ORIGINS` to your real Vercel URL
   (e.g. `https://resume-intel.vercel.app`) and redeploy.
   (Browser traffic goes through the Vercel proxy, so CORS is belt-and-braces.)
2. Test the live app end-to-end with `backend/samples/sample_resume.txt`
   + `sample_jd.txt`.
3. Expect the first analysis after idle to be slow (Render cold start).

## 5. Post-launch checklist

- [ ] `/api/health` on the public URL shows `ai_provider: gemini`
- [ ] Full analysis works from the public frontend (upload → dashboard)
- [ ] Error path works: upload a .png → clean error banner
- [ ] Gemini free-tier quota is per-day; if analyses start failing with 429,
      the `meta.ai_error` field will say so — deterministic scores keep working
- [ ] Optional hardening before sharing widely: rate limiting (e.g. slowapi),
      an upload size/type gate at the proxy, and Neon Postgres for history
