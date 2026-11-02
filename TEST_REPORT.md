# Unified integration verification

- **67 Python tests passed**, including the original 45 regressions.
- **6 Apps Script workflow scenarios passed** using mocked Google services:
  combined collection/delivery, acknowledgement retry without duplicate send, Gmail
  failure without marking sent, legacy pending acknowledgement migration, trigger
  installation, and invalid schedule rejection before deleting triggers.
- Ruff fatal/error checks and workspace JavaScript syntax: passed.
- HSN build and offline validation: passed; **340,232** dataset rows.
- Chromium browser smoke: passed with seeded local data, mocked AI, and blocked external
  browser requests. Checked sign-in, combined feed, country filter, saved view, selected
  story analysis/download, shared Geo session, BRICS stream writes, HSN deep link,
  mobile horizontal overflow, sign-out, and absence of JavaScript page errors.
- MongoDB stream persistence tested with mongomock; source outage and AI provider
  fallback tested with mocks. No real credentials or outbound messages used.

## New behavior

One signed administrator session works across the three tools. The homepage combines
news, heuristic HS links, shared provider/model configuration, source-numbered AI
briefs, saved browser views and port context. Stream edits persist in MongoDB (or
DATA_DIR for local SQLite mode). Apps Script collects both feeds and sends a combined
Gmail digest with idempotent acknowledgements and retry state. Placeholder empty
events are skipped. AI and AIS data are not presented as proof of cargo/compliance.

## Live verification still needed

Actual Render deployment, Atlas access, provider model/quota access, AIS data reception,
Google authorization/trigger timing and Gmail delivery require the owner's accounts.
Free Render can sleep; no uptime guarantee is made. Tests do not establish tariff or
news accuracy. The integrated AI uses saved source excerpts, not independent live
web verification. This release does not add automatic event discovery, scheduled AI
emails, or a replacement weekly/critical email workflow.

## Reproduce

```bash
pip install -r requirements-dev.txt
python -m pytest -q
ruff check . --select E9,F63,F7,F82
node tests/test_apps_script.mjs
node --check static/workspace.js
cd hsn/tools
npm run build
npm run check
```

Optional Chromium test from the project root:

```bash
pip install playwright
CHROMIUM_PATH=/usr/bin/chromium python tests/browser_smoke.py
```

---

# Earlier fixes and verification

## Results

- Python regression suite: **45 passed**.
- Ruff fatal/error checks (`E9,F63,F7,F82`): passed.
- Python compilation: passed.
- HSN `npm run build`: passed.
- HSN `npm run check`: passed; decoded **340,232** dataset rows, checked generated
  JavaScript, service worker, hosted/offline artifacts, GST and trade data checks.

## Corrected issues

1. Metadata cleanup now retains articles without confirmed Telegram backup references.
2. Missing Geo MongoDB configuration fails immediately rather than attempting localhost;
   initialization readiness reaches the hub and Geo health returns 503 when unavailable.
3. Added `/geo/` dashboard route so the hub link resolves.
4. BRICS critical windows accept naive UTC and offset timestamps, reject invalid/future dates.
5. Shared SQLite operations and singleton creation are serialized across request threads.
6. MongoDB insertion only treats duplicate-key errors as duplicates. Geo bulk writes use
   confirmed insertion counts and propagate nonduplicate and write-concern errors.
7. Related-news retrieval requests newest Geo articles instead of silently sorting by score.
8. Collection trigger respects disabled or unavailable news apps.
9. Invalid mark-emailed JSON and ID lists return 400; valid IDs still reach the database.
10. Concurrent gzip builds are serialized; gzip;q=0 is respected and cache Vary includes
    Accept-Encoding on both compressed and plain responses.
11. CORS preserves existing Vary values and handles Flask automatic preflight responses.
12. AIS capacity eviction runs after the incoming ship is populated, retaining new positions.
13. Dashboard links encode secret/filter query values; category grouping no longer overwrites
    the active category in the footer.
14. BRICS stream administration rejects the shared weak-secret placeholders.
15. CSV row limits are bounded to positive values; deprecated BRICS utcnow calls replaced.

Added requirements-dev.txt, regression tests, and an offline HSN build-check command.

## Limits

No MongoDB, AI provider, AIS, email, Telegram, or WhatsApp credentials were provided.
External integrations and live feed freshness were not verified against those services.
MongoDB failure handling was tested using mocks; SQLite was tested with concurrent writes.
No full browser automation was performed. HTML routes, static delivery, generated JavaScript
syntax, dataset decoding and build invariants were checked. No deployment or outbound
notification was performed. These checks do not guarantee every possible defect is absent.

## Run locally

Follow README.md; copy .env.example to .env and supply TRIGGER_SECRET. Supply MONGODB_URI
for Geo. To rerun checks, use the Verification commands in README.md. Run npm run build
before npm run check, since the check validates generated hosted and offline files.
