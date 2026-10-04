# Finder feature-preserving merge plan

Preserve and port existing functionality. Do not rebuild existing Finder features. File preservation is not runtime parity: private nested routes, sandbox and CSP need function-level tests.

## Source feature inventory, retained in Finder tab
- Product/code search, national systems, code hierarchy, cross-system linkage/reverse mapping, explanations.
- Duty comparison across systems, country comparison, landed cost, origin duties, GST/FTA/RoDTEP/anti-dumping/SCOMET, document and certificate/checklist context.
- Per-HS world import/export values, India partner/trend data, country profiles, supplier/competitor/demand gap, seasonal timing, tariff-drop/growth signals.
- Price watch: baked India export USD/kg unit values (not live commodity quotes).
- Country sanctions exposure, company/person name screening, vessel IMO/name screening, route risks, port cargo/traffic stats and transit/container links.
- Shortlist, client report/CSV, template report/print, copy/share links, country deep links, AI plain words/brief/classifier/document explanation/comparison/report helpers.
- Live currency rate/trend/INR impact, port weather/marine, AIS ships, optional personal-provider AI access.
- PWA/service worker, offline page/data, source-refresh pipeline and snapshot freshness.

## Gaps to port/verify before calling merge complete
1. Existing external-fetch functions are blocked by private Finder connect-src self: AI proxy/provider requests, Frankfurter currency, Open-Meteo weather/marine, AIS proxy. Port exact trusted endpoints/config or a private reviewed adapter, without opening arbitrary destinations; no live activation before owner gate.
2. Nested private iframe sandbox/cookies/permissions must preserve exports, print/popups, clipboard/share, user settings and exact-country/code navigation. Source includes old standalone share origin; adapt links to approved merged destination without changing identifiers.
3. PWA/service worker manifest/scope/asset cache needs private-mode review: do not cache protected news/account pages or expose authenticated data offline. Do not enable caching by copying standalone behavior blindly.
4. Finder data/updater/AI+AIS services are copied but not wired into merged deployment. Keep one scheduler owner; no new collector/refresh runs. Reconcile updates from original repo so preserved snapshot does not drift.
5. Geo digest mail and Telegram record backup are preserved but merged delivery remains gated and unwired; Telegram record backup is not a daily digest. No daily-brief-to-Telegram implementation was identified.

Static features above are present by preserved Finder source/bundle, not individually proven functional yet. Use a feature-by-feature browser matrix before signoff, including mobile, blocked network, privacy/auth and empty/missing-data behavior. Report any failure as a gap rather than claiming all features landed based on hashes.

## Three-project parity work order (offline only)

| Project | Feature group | Status | Remaining port |
|---|---|---|---|
| Finder | Static code search/details/duties/trade/market/sanctions/unit values | Present, source preserved; comprehensive function tests pending | Test each original feature in nested private route |
| Finder | AI/FX/weather/marine/AIS | Present but blocked by CSP | Exact trusted-origin allowlist or reviewed adapter; fixture-only tests before live access approval |
| Finder | Snapshot/data and new branding | Earlier snapshot present | Diff latest data provenance and headers, port reviewed delta |
| Finder | Share/print/export/settings | Present, nested operation unproven | Private route tests and merged-origin links |
| Finder | PWA | Missing on merged host (old-host-only registration) | Private-safe manifest/scope/cache port |
| Geo | Read/filter/sort/loaded stats/CSV/signal adapters | Works in offline tested preview | Production signoff remains gated |
| Geo | Events snapshot | Present but reader unwired | Port original read-only event data |
| Geo | Collection/classifier/scoring/credibility/corroboration/dedupe | Present but unwired | Single Geo-only collector composition, no live execution |
| Geo | Apps Script digest/sent-marking/critical/weekly/channel delivery | Present but unwired | Port original delivery contracts; approved Apps Script path, no SMTP replacement |
| Geo | HTML digest archive/Telegram record archive/cleanup | Present but unwired | Port retention and archive contracts; execution gated |
| Geo | Full-history CSV | Missing (sample CSV differs) | Original fields and category filtering, bounded streaming/incremental read design |
| BRICS | News/search/filter/critical display/loaded CSV | Backend adapters present; separate BRICS tab absent in current Geo-only UI | Port BRICS-specific capabilities onto unified Geo UI; do not dismiss removed capabilities as storage consolidation |
| BRICS | Source-status and original streams | Snapshot adapters present, readers unwired | Port source status and exact configured streams |
| BRICS | Stream add/delete | Missing | Port original validated mutation semantics, fixture store first |
| BRICS | Auto-refresh | Missing by no-polling gate | Port original UI logic, disabled until polling approval |
| BRICS | Full filtered/critical-only CSV | Missing (sample CSV differs) | Port original export contract, not sample substitute |
| BRICS | Collection/classifier/dedupe/delivery | Present but unwired | Port relevant processing/delivery capabilities to Geo-only composition |
| BRICS | Separate BRICS collection/database | Intentionally dropped | Keep historical code for rollback; no new BRICS writes/migration |

Work order: Finder blocked functions + snapshot reconciliation; Geo digest/alerts/delivery; full CSV; BRICS stream management/auto-refresh; merged-origin PWA. Each increment gets independent review. Live cutover, stopping old collectors, Render preview settings, mail sends, live DB writes, polling and Telegram/WhatsApp delivery each remain separately gated. Map and weekly work can proceed independently where files do not collide. No external network activation is implied by offline wiring.
