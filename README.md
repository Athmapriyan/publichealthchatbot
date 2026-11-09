# Odisha Public Health Chatbot — Prototype

AI-driven public-health awareness, risk screening, and misinformation-checking chatbot,
built per the Government of Odisha E&IT Dept MedTech/HealthTech project brief.

## 🚨 Security note
This project previously had real API keys committed to `.env.example` and `.env` in git history
and pushed to a public GitHub repo. If you're reading this after that happened: **revoke and
regenerate every exposed key immediately**, and re-initialize git history before pushing again
(see `.gitignore` in this repo — `.env` is now excluded). Never put real secrets in `.env.example`;
it's a template meant to be committed. Only your local `.env` (gitignored) should hold real keys.

## ⚠️ Honest status of this codebase

This is a **working MVP covering Phases 1–4 of the spec**, built so it actually runs,
not a mock of 30 modules. Please read this before presenting it as "complete":

| Spec area | Status |
|---|---|
| Phase 1 — Chatbot + LLM API + disclaimer | ✅ Implemented |
| Phase 2 — RAG (embeddings + vector DB + retrieval) | ✅ Implemented (ChromaDB + sentence-transformers) |
| Phase 3 — Disease knowledge base | ✅ Implemented, 13 seed documents across 12 diseases/topics (expand freely — see `knowledge_base/diseases.json`) |
| Safety layer + emergency detection | ✅ Implemented (regex-pattern baseline — see note below) |
| Phase 4 — Risk assessment | ✅ Implemented as an **explainable rule-based scorer**, not yet a trained ML model. The interface is ready for a drop-in sklearn/XGBoost model (see comment block at bottom of `backend/risk/risk_model.py`) once you have a labeled dataset |
| Phase 5 — Misinformation detection | 🟡 Partial: the RAG-based verification arm works end-to-end. The TF-IDF/transformer baseline comparison from spec §12 is **not built** — needs a labeled misinformation dataset first |
| Phase 6 — Multilingual (en/hi/or) | ✅ Implemented via **Sarvam AI** (`backend/multilingual/`). Query is translated to English → RAG/LLM run in English → response translated back. Requires `SARVAM_API_KEY` in `.env`; degrades gracefully (English passthrough + notice) if Sarvam is unreachable |
| Phase 7 — Voice (STT/TTS) | 🔲 Not implemented. `/speech-to-text` and `/text-to-speech` endpoints from spec §25 are not yet built |
| Frontend | ✅ `frontend-web/` — full React + TanStack Start + Tailwind app (chat, risk assessment, misinformation checker, disease directory). Plus `frontend/chat.html` (zero-install dev tester) and `backend/telegram_bot.py` (Telegram client) |
| Evaluation notebooks/scripts | 🔲 Not built |
| Research documentation (abstract, lit survey, etc.) | 🔲 Not built — ask separately, this is a writing task not a coding task |

**Why phased honesty matters here:** claiming a finished Odia-voice-enabled misinformation
classifier that was never run would actively hurt you in a project demo or viva. Build on
this foundation incrementally and test each phase before moving to the next.

### Important caveats on what IS built
- **Emergency detection is a regex/keyword baseline**, intentionally simple and transparent
  for a first pass. It is **not clinically validated** and should never be the sole safety
  net in a real deployment — treat it as a first-pass filter, not a triage system. Expand
  `EMERGENCY_PATTERNS` and ideally replace with a validated classifier before any real use.
- **Risk assessment is rule-based, not ML**, so section 10's model comparison (Logistic
  Regression vs Random Forest vs XGBoost, evaluated by recall) hasn't happened yet — you
  need a labeled symptom-outcome dataset to do that honestly.
- The knowledge base has **13 seed documents** I wrote by hand, each attributed to a real
  publisher (WHO, NCDC, MoHFW) in the style of their public guidance — but these are my
  paraphrased summaries, not scraped/verified live documents. Before any real deployment,
  replace these with actual ingested WHO/MoHFW/ICMR documents and re-verify every medical
  claim against the live source.

---

## Architecture

```
User (text)
    │
    ▼
Safety Screening — emergency keyword detection (short-circuits to urgent warning)
    │
    ▼
Intent Classification — keyword-rule baseline (disease/prevention/misinformation/etc.)
    │
    ▼
RAG Retrieval — ChromaDB vector search over trusted knowledge_base/diseases.json
    │  (refuses / returns "insufficient evidence" if nothing scores above threshold)
    ▼
LLM Provider Router — tries Groq → Gemini → OpenRouter in order, auto-falls back on
    │                   timeout / 429 rate-limit / invalid key / 5xx
    ▼
Response Validation — regex guard blocks disallowed patterns (diagnosis claims, dosages)
    │
    ▼
Response + cited sources + standard disclaimer
```

This deliberately avoids `User → LLM → Answer`. Every medical factual answer must pass
through retrieval first; if retrieval finds nothing relevant, the system refuses rather
than letting the LLM free-associate.

## Why this LLM provider order (verified as of Oct 2026)

- **Groq (primary)**: genuinely free, no credit card, ~30 req/min and ~14,400 req/day on
  entry-level models like `llama-3.3-70b-versatile` — the most generous truly-free tier
  for a prototype demo.
- **Gemini (fallback 1)**: Google's free tier via AI Studio, lighter models like
  `gemini-2.0-flash`.
- **OpenRouter (fallback 2)**: aggregates many `:free`-suffixed open models behind one key.

Flagship/paid-tier models (GPT-5-class, Claude Opus-class, Gemini Pro-class) are
increasingly gated behind paid tiers as of 2026 — don't assume free access to those.
**Re-verify rate limits before any demo/deployment**, as free tiers change terms often.

## Tech stack & why

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI | async, auto OpenAPI docs, matches spec §18 |
| Vector DB | ChromaDB (local, file-based) | zero-infra, free, swappable for Qdrant/FAISS later |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | small, fast, runs locally/free, good enough for retrieval over a small curated KB |
| LLM | Provider-abstracted (Groq/Gemini/OpenRouter) | spec §5/§6 cost-optimization requirement |
| Risk model | Rule-based (Phase 1), ML-ready interface | explainable now, upgradeable later |

---

## Setup

### 1. Prerequisites
- Python 3.11+
- A free API key from at least one of: [console.groq.com](https://console.groq.com) (recommended),
  [aistudio.google.com](https://aistudio.google.com), [openrouter.ai](https://openrouter.ai)
- For Hindi/Odia support: an API key from [dashboard.sarvam.ai](https://dashboard.sarvam.ai) (sign up, then
  Dashboard → API Keys → generate). Without this, `language: "hi"` or `"or"` requests still work but
  fall back to English-only responses.

### 2. Environment
```bash
cd public-health-chatbot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste in at least GROQ_API_KEY
```

### 3. Run the backend
```bash
uvicorn backend.main:app --reload --port 8000
```
First request will download the embedding model (~80MB) and build the Chroma vector
index from `knowledge_base/diseases.json` — this happens once, then is cached in
`./data/chroma_db`.

Visit `http://localhost:8000/docs` for interactive Swagger UI to try every endpoint.

### 4. Try it
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the symptoms of dengue?", "language": "en"}'

curl -X POST http://localhost:8000/risk-assessment \
  -H "Content-Type: application/json" \
  -d '{"age_group": "adult", "symptoms": ["high fever", "joint pain"], "duration_days": 3, "temperature_celsius": 39.0}'

curl -X POST http://localhost:8000/misinformation-check \
  -H "Content-Type: application/json" \
  -d '{"claim": "Drinking papaya leaf juice completely cures dengue with no need to see a doctor"}'
```

### 5. Test
```bash
pytest tests/ -v
```
Tests marked `skip` require a live API key configured — run those manually after setup.

### 6. Docker
```bash
docker compose -f docker/docker-compose.yml up --build
```

---

## API reference (implemented so far)

| Endpoint | Method | Status |
|---|---|---|
| `/chat` | POST | ✅ |
| `/risk-assessment` | POST | ✅ |
| `/misinformation-check` | POST | ✅ |
| `/diseases` | GET | ✅ |
| `/health-resources` | GET | ✅ (returns official links only — no fabricated hospital data, per spec §15) |
| `/sources` | GET | ✅ |
| `/detect-language` | POST | 🔲 not built (Phase 6) |
| `/speech-to-text` | POST | 🔲 not built (Phase 7) |
| `/text-to-speech` | POST | 🔲 not built (Phase 7) |

## Running the web frontend (`frontend-web/`)

A full React app (TanStack Start + Tailwind + Radix UI) with four views: chat,
risk assessment, misinformation checker, and a disease directory. Originally
built with [Lovable.dev](https://lovable.dev) — runs fine standalone outside
Lovable's platform, see notes below.

### 1. Install Node.js
Node 20+ recommended. Check with `node -v`.

### 2. Install dependencies
This project uses `bun.lock`, but `npm install` works too if you don't have Bun:
```powershell
cd frontend-web
npm install
```
(or, if you have [Bun](https://bun.sh) installed: `bun install` — faster, and matches the committed lockfile exactly)

### 3. Point it at your backend
```powershell
copy .env.example .env
```
Default `VITE_API_BASE_URL=http://127.0.0.1:8000` already matches your local backend — no edit needed
unless you deploy the backend elsewhere later.

### 4. Make sure the backend is running (separate terminal)
```powershell
cd ..
uvicorn backend.main:app --reload --port 8000
```

### 5. Run the frontend dev server
```powershell
cd frontend-web
npm run dev
```
Open the URL it prints (typically `http://localhost:3000` or similar — check the terminal output).

### Notes on this frontend
- Built via Lovable.dev — a few files (`src/lib/lovable-error-reporting.ts`, `src/lib/error-capture.ts`)
  hook into `window.__lovableEvents`, which only exists inside Lovable's own hosting/preview. Outside
  Lovable these simply no-op harmlessly — they don't block anything locally.
- `vite.config.ts` uses `@lovable.dev/vite-tanstack-config`, which defaults `npm run build`'s output
  target to Cloudflare Workers (via Nitro). This is fine for `npm run dev` locally. If you deploy
  elsewhere (Vercel, Netlify, your own VM), you may need to override the Nitro preset — ask if you hit
  this when you get to deployment.
- CORS: the backend's `main.py` currently has `allow_origins=["*"]` (open to any origin) for development
  convenience. **Tighten this to your frontend's actual deployed domain before any real deployment** —
  wide-open CORS is fine for local dev, not for production.

## Running the Telegram bot

`backend/telegram_bot.py` is a thin Telegram-shaped client that talks to your
already-running FastAPI backend over HTTP — it doesn't duplicate any logic.

### 1. Create a bot with BotFather
In Telegram, message **@BotFather** → `/newbot` → follow the prompts (choose a
name and a unique username ending in `bot`). It replies with a token like
`123456789:ABCdefGhIjKlmNoPQRstuVwxyz`.

### 2. Add the token to `.env`
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIjKlmNoPQRstuVwxyz
BACKEND_BASE_URL=http://127.0.0.1:8000
```

### 3. Install the dependency
```powershell
pip install python-telegram-bot==21.6
```

### 4. Run BOTH processes (two separate terminals)
Terminal 1 — your existing backend, unchanged:
```powershell
uvicorn backend.main:app --reload --port 8000
```
Terminal 2 — the Telegram bot:
```powershell
python -m backend.telegram_bot
```

### 5. Test it
Open Telegram, search for your bot's username, send `/start`. Try:
- A plain health question: "What are the symptoms of dengue?"
- `/language` to switch to Hindi/Odia (requires `SARVAM_API_KEY` configured for real translation)
- `/checkclaim <some health rumour>` to test the misinformation checker
- An emergency-sounding message ("I have severe chest pain") to confirm it short-circuits correctly

### Notes on this implementation
- **Polling mode**, not webhooks — simplest for local development, no public URL/HTTPS/ngrok needed.
  For production deployment (spec §30 Phase 8), switch to `run_webhook()` with a public HTTPS endpoint.
- Per-chat language preference is stored **in memory only** (`USER_LANGUAGE` dict) — resets if the bot
  restarts. Fine for a prototype; wire up a small SQLite table if you need persistence.
- The bot process must be able to reach `BACKEND_BASE_URL` — if you deploy the FastAPI backend to a
  server later, update this to that server's URL rather than `127.0.0.1`.
- **Never commit `TELEGRAM_BOT_TOKEN`** — it's gitignored via `.env` like your other keys.

## Adding a new disease to the knowledge base
Add an entry to `knowledge_base/diseases.json` following the existing schema
(`source`, `publisher`, `url`, `publication_date`, `content`, etc.), delete
`./data/chroma_db` to force re-ingestion, and restart the server. No retraining needed —
this is the point of the RAG architecture (spec §3).

## Next steps (recommended order)
1. Run and sanity-check this MVP end-to-end with a real Groq key.
2. Expand the knowledge base with verified WHO/MoHFW/NCDC/Odisha govt documents.
3. Build Phase 6 (language detection + translation layer) — needed before Odia/Hindi claims in your report are true.
4. Build Phase 7 (Whisper STT + an Indic TTS option).
5. Collect/label a small symptom-risk dataset to replace the rule-based risk scorer with a real evaluated ML model (spec §10) — this is likely your strongest "research" chapter.
6. Build the frontend (React recommended per spec §18).
7. Write evaluation scripts once there's a model/dataset to evaluate.
#   p u b l i c h e a l t h c h a t b o t  
 