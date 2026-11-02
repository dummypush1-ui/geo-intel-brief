# Geo Intel Brief — one application, one web service

Merges three projects into a single Flask service:

| URL | What | Origin |
|---|---|---|
| `/` | Hub: links + live status of each app | new |
| `/hsn/` | Worldwide HSN Code Finder (340k codes, duties, sanctions, AI reports, live ships) | `finder-hsn-codee` |
| `/brics/` | BRICS Live Monitor: live video, news feed, critical alerts, CSV | `BRICS-` |
| `/geo/` | Geo Intel Monitor: trade / sanctions / research digest, weekly report, CSV | `geonews` |
| `/health` | Aggregate health (used by Render) | new |
| `/api/links/*` | News ↔ HS-code link (see below) | new |
| `POST /api/trigger/collect?key=…` | Runs both collectors (one cron job drives everything) | new |

**News ↔ code link.** Each BRICS and Geo article shows `HS xxxx` chips that open that heading in the finder (`/hsn/#code=0:xxxx`); each code page in the finder has a *Related news* panel listing the last 30 days of BRICS + Geo headlines mapped to that heading. Matching is keyword-based and explainable: curated phrases in `hsn/data/news_aliases.json` (edit freely) plus an IDF-weighted overlap with HS heading text (needs two distinctive words). JSON: `GET /api/links/news-for-code?code=8542`, `GET /api/links/codes-for-article?text=...`. Regenerate the lexicon after a data refresh with `node hsn/tools/export-lexicon.mjs`.

A sub-app that fails to start (missing DB, bad config) is shown as *unavailable* on the hub; the others keep running.

## Unified intelligence workspace

The homepage now combines BRICS + Geo news with filters, saved views, HS-code links,
selected-story AI trade-impact briefs, and live AIS context. Sign in once using your
TRIGGER_SECRET; the same session opens Geo and authorizes BRICS stream management.
MongoDB deployments persist stream edits across redeploys.

**Free Render users:** follow [the combined setup guide](docs/FREE_RENDER_SETUP.md)
and replace your Apps Script with [the updated Code.gs](geonews/apps_script/Code.gs).
The script now collects BOTH news feeds and sends one combined Gmail digest.
AI keys and optional model overrides are shared between the workspace and HSN finder.

## Layout
```
app.py            hub + blueprint mounting          core/   paths, shared auth, scheduler
hsn/              routes.py (static + AI proxy), ais.py (live ships), static/ (built site), tools/ (build + daily data pipeline)
brics/            BRICS package (blueprint in web.py)   geonews/   Geo News package (blueprint in web.py)
```

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # set TRIGGER_SECRET at minimum
python app.py               # http://localhost:5000  (starts the in-process scheduler)
```
Geo News needs `MONGODB_URI` (free Atlas tier works). BRICS works with SQLite out of the box. HSN finder needs nothing for search; AI and live ships need the provider keys below.

## Deploy (Render)
1. Push this folder to GitHub → Render → *New Blueprint* (uses `render.yaml`) or a Web Service with `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 300`.
2. Environment: `TRIGGER_SECRET` (long random), `MONGODB_URI`, `STORAGE_BACKEND=mongodb`, `DEPLOY_MODE=cloud`, and optionally `GROQ_KEYS` / `GEMINI_KEYS` / `MISTRAL_KEYS` / `NVIDIA_KEYS` / `AISSTREAM_KEY`.
3. Free tier sleeps: set one external cron (cron-job.org) to `POST https://<app>/api/trigger/collect?key=<TRIGGER_SECRET>` every 15 min. On an always-on host set `RUN_SCHEDULER=true` instead. Use **one gunicorn worker** (the scheduler and the AIS socket are per-process).
4. Geo's Google Apps Script mailer (`geonews/apps_script/Code.gs`) now calls `/geo/*`; re-paste the file into your Apps Script project.

## HSN data refresh
`hsn/tools/` is the original build + daily pipeline. `node build.mjs && node publish.mjs` (or `npm run build`) regenerates `hsn/static/`. `.github/workflows/hsn-refresh.yml` runs the daily job and commits the result; the service redeploys on that commit.

## What changed vs. the three originals
- **Same-origin AI/ships API** at `/hsn/api/*` (Python port of `proxy.js`: same key rotation, failover, 60 calls/10 min/IP). The shared `x-app-token` that was baked into the public JS bundle is gone; same-origin browser calls need no token. Cross-origin callers: set `HSN_ALLOWED_ORIGINS` or `APP_SECRET`.
- **Auth fails closed.** Geo used to accept every request when `TRIGGER_SECRET` was empty; BRICS accepted the literal `changeme`. Both now share `core/auth.py` and refuse to run triggers/admin routes until a real secret is set. BRICS stream add/remove no longer unlocks with the default dashboard key.
- **No more import-time side effects / CWD dependence**: files resolve under `DATA_DIR`; BRICS and Geo have separate env overrides (`BRICS_*`, `GEO_*`) for names that collided (`SMTP_PORT`, `DEDUPE_THRESHOLD`, …).
- Removed dead code: `geonews/reports/telegram_archive.py` imported config names that never existed.
- Service-worker registration and manifest are now path-relative (work under `/hsn/`), and the page no longer hard-codes the old Render hostnames.

## Known limitations
- News↔code tagging is heuristic (headline/summary keywords → 4-digit HS heading), not a classification ruling. Expect some misses and the odd wrong tag; each tag shows the words it matched. BRICS articles are tagged on title only (that's all it stores); Geo on title + summary.
- `/api/links/*` is public read-only (titles, links, sources, dates from both feeds) and rate-limited to 120 calls / 10 min / IP.
- Geo's dashboard/email/Telegram links still carry `?key=<TRIGGER_SECRET>` in the URL (original design). Treat those links as secrets, or change the key if one leaks.
- `ENABLE_TELEGRAM_BACKUP` defaults to **true** in Geo News; set `GEO_ENABLE_TELEGRAM_BACKUP=false` unless you've configured the backup channel.

## Verification

```bash
pip install -r requirements-dev.txt
python -m pytest -q
ruff check . --select E9,F63,F7,F82
node tests/test_apps_script.mjs
cd hsn/tools
npm run build
npm run check
```

Tests use temporary SQLite storage and mocks for MongoDB errors; they do not send
messages, collect external feeds, or require provider credentials. See
`TEST_REPORT.md` for fixes and verification limits. Geo requires a configured,
reachable MongoDB database; without it the hub marks Geo unavailable and its
health route returns 503. Other apps continue running. Metadata cleanup keeps
records without both a confirmed Telegram message ID and backup URL.
