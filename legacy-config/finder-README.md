# Worldwide HSN Code Finder

Free, offline-first tariff code finder covering 22 official systems (WCO HS 2022 + India, USA, EU, UK, Korea, Canada, Japan, Australia, Brazil, Taiwan, New Zealand, Norway, Singapore, Israel, Mexico, Hong Kong, South Africa, Peru, China, UAE and India SAC), 340,232 codes, as a fast hosted page plus a self-contained `offline.html` download.

Live: https://finder-hsn-codee.onrender.com/

## What it does

**Find the code**
- **Search anything**: product names, trader terms, typo-tolerant ("DISEL" finds diesel), code prefixes. One row per product; each row leads with the direct deepest national code (India first), never the 6-digit family parent. The `offline.html` download works fully offline - no AI needed to search.
- **Suggest best codes / search assist**: AI reads the shown matches against your words and points at the fitting rows; on zero matches it suggests better search words.
- **Reverse lookup**: have a foreign code? Crosswalk it to the India HSN line.
- **HS 2022 change correlation**: code changed in the HS 2022 revision? The detail page maps old to new (CBSA correlation tables).

**Decide with data (detail page, every feature connected to the code)**
- Duty rates, GST (India), code chain from HS root to national line.
- **Trade brief**: one-tap AI paragraph built only from the code's baked official figures (duty, trade values, markets, seasonality, incentives, sanctions), with a verify line.
- **Plain words**: one-tap plain-English explanation of what the legal code text covers.
- **Markets**: top importing countries + world total (UN Comtrade, 5,845 codes); **Competitor share**: top exporting countries, India highlighted.
- **Trade risk + market data**: sanctions status, anti-dumping measures, SCOMET/export-control flags, geopolitics and policy-impact signals, demand and supply facts.
- **Sanction gap finder**: supply-at-risk lines with alternative suppliers, sanctioned-demand lines with India's rank (mirror statistics for non-reporting countries, marked).
- **Tariff drop finder**: FTA duty cuts claimable now (India-Australia ECTA, India-UAE CEPA step-downs).
- **Price watch**: India export unit-value jumps/drops from official quantity data.
- **Currency impact**: USD-INR move vs this code's trade value, with a worked crore example.
- **Country compare**: two countries side by side for the same product - duty, documents, market size.
- **Compare verdict**: AI one-tap verdict on a shortlist, numbers only from baked data.
- **Seasonality**: India's monthly import/export pattern for the code; **Product intel**: the code's whole picture on one card.
- **Documents**: export/import document checklists per chapter, per-document AI explainer, export checklist (IEC, ICEGATE, e-Sanchit, certificates, RoDTEP incentive rate), company lookup link (US bills of lading).
- **Ports for this cargo**: chapter-mapped cargo type -> the government major ports that handle it, with 2024-25 traffic and UN/LOCODEs (official IPA port statistics).
- **PDF report**: the whole page as a clean print/PDF.

**Home tools**
- India trade in words (top imports/exports), Country profile (104 countries, what each buys and sells), Trade currencies (30 live INR pairs, ECB/Frankfurter), Payment currency rules (RBI), Port trade statistics (13 major ports, traffic + commodity, official), Port weather (live), **Sea transit time** (any two of 3,319 worldwide ports - NGA World Port Index - straight-line NM + day range), container tracking links, **Live ships near major ports worldwide** (AISStream feed through the proxy, 42 port boxes).

## Architecture (all free)
1. **Static site** (Render, this repo root): serves `index.html`, auto-deploys on every push to `main`.
2. **AI + AIS proxy** (`proxy.js`, Render web service on the same repo, start command `node proxy.js`): the browser holds no provider keys. The page calls the proxy with a public-by-design `APP_SECRET` speed bump; the proxy attaches the real key from its env and forwards, with per-request shuffled provider order (Groq / Gemini / Mistral), key rotation, failover, and a per-IP rate cap. It also keeps one AISStream websocket open and answers `/ships` with the latest vessels per port box.
   - Env: `APP_SECRET`, `GEMINI_KEYS`, `GROQ_KEYS`, `MISTRAL_KEYS` (comma-separated pools), `AISSTREAM_KEY` (optional; without it `/ships` answers 503).
3. **Daily refresh** (GitHub Actions, 03:30 UTC, `.github/workflows/refresh.yml` -> `automate.mjs`): India trade values (Comtrade), description cleanup, OFAC + EU sanctions refresh, watch of all official source pages, rebuild the hosted and offline pages, safety checks, commit only if changed. Render redeploys on the commit.
   - Repo secret needed: `COMTRADE_KEY`. Optional: `GEMINI_API_KEY` for the AI jobs below.

## AI rules
- **AI proposes, code verifies.** Nothing unverified is written to data.
- AI surfaces are one-tap and optional; the app works fully without them. AI answers are built only from baked official figures, run through output checks (prompt-echo and garbage detection with retry), and cached locally.
- Daily AI jobs (need `GEMINI_API_KEY`): search aliases (must match real tariff descriptions), GST notification drafter (opens a PR, never edits directly), description cleanup.

## Automatic vs. alerted
- Automatic: India trade values, sanctions lists, description cleanup, aliases, rebuild, deploy.
- Alerted (GitHub Issue "Source changed: ..."): national tariff systems, the India GST page, UFLPA - no stable feed. GST rates are legal data and are never auto-edited from a scraped page.

## Data sources (all official, all free)
WCO HS 2022, India CBIC/GST notifications + DGFT, USITC HTS, EU TARIC/CN, UK Trade Tariff, Korea Customs, Canada CBSA, Japan Customs, Australia Home Affairs, Brazil NCM, Taiwan Customs, NZ Customs, Norway Tolletaten, Singapore Customs, Israel Tax Authority, Mexico SNICE, Hong Kong C&ED, South Africa SARS, Peru SUNAT, China Customs, UAE FCA, India SAC; UN Comtrade (trade values/partners), OFAC + EU + UN + UK sanctions lists, DGFT SCOMET/Appendix-3, anti-dumping (DGTR/CBIC), RoDTEP notification rates, IPA port statistics, NGA World Port Index, AISStream (live AIS), Open-Meteo (port weather), Frankfurter/ECB (exchange rates).

## Repo layout
- `index.html` - hosted shell; `data.<hash>.js` - versioned data; `offline.html` - self-contained offline copy
- `src/` - dataset + app source (data chunks, GST/trade/market/sanctions/FTA/port maps, aliases, app.js, style.css)
- `build.mjs` - rebuilds both pages and the versioned data from `src/` (`node build.mjs`)
- `automate.mjs`, `refresh.mjs`, `sanctions-refresh.mjs`, `comtrade-*.mjs`, `compute-sancgap.mjs`, `gemini.mjs`, `ai-agent.mjs`, `apply-gst.mjs`, `monitor.mjs` - the daily pipeline and data jobs
- `proxy.js` - the AI + AIS proxy web service (see above)
- `render.yaml` - blueprint for the static site

## Hosted speed and offline copy

`index.html` is a small shell. It loads the versioned `data.<hash>.js` code dataset before search starts. `sw.js` caches that exact data file for repeat visits while allowing the HTML shell to refresh on each visit. For a self-contained offline copy, download `offline.html` instead; it still includes the code dataset inline. The offline copy cannot use the hosted service worker; live AI and ship feeds still need a connection. Run `node build.mjs` after editing source to regenerate both builds. The manifest and icons enable installation on supported browsers; the site still works without installation.
