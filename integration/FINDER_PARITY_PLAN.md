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
| Finder | AI/FX/weather/marine/AIS | Offline preview port reviewed; seven exact origins behind default-off flag, original UI fixture tests pass | Real network/provider CORS availability and AI-disclosure permission still gated; AIS timers suppressed in served preview |
| Finder | Snapshot/data and new branding | Reviewed Oct4 upstream snapshot ported offline | Source-derived auto-refreshed label only; not independently verified official data |
| Finder | Share/print/export/settings | Nested Chromium code/favourites/notes/clipboard merged-link/CSV proven in private fixture; narrow scroll and CSV cell safety ported | Native print/PDF and AI report popup unverified; offline shortlist scroll/CSV safety unchanged; JSON-LD standalone origin remains |
| Finder | PWA | Public-only offline snapshot preview; explicit device opt-in and clear cache | Hosted HTTPS/Safari/quota tests; page-session offline settings, never protected news/cache |
| Geo | Read/filter/sort/loaded stats/CSV/signal adapters | Works in offline tested preview | Production signoff remains gated |
| Geo | Events snapshot | Injected bounded read-only adapter + gated supplied-event original digest preview reviewed | Production collection/client/socket budget identity and real composition unwired |
| Geo | Collection/classifier/scoring/credibility/corroboration/dedupe | Present but unwired | Single Geo-only collector composition, no live execution |
| Geo | Apps Script digest/sent-marking/critical/weekly/channel delivery | Original HTML dry-run previews wired; delivery still unwired | Port original delivery contracts; approved Apps Script path, no SMTP replacement |
| Geo | HTML digest archive/Telegram record archive/cleanup | Present but unwired | Port retention and archive contracts; execution gated |
| Geo | Full-history CSV | Bounded snapshot+fixture stream wired; original 12-column pure serializer differential-tested | Pure Mongo keyset plan, injected pager and original-column streaming fixture consumer reviewed; production schema/index/collation/snapshot/read-only adapter and original streaming route missing; effective consumer20MB cap, no 1m-throughput proof |
| BRICS | News/search/filter/critical display/loaded CSV | Backend adapters present; separate BRICS tab absent in current Geo-only UI | Port BRICS-specific capabilities onto unified Geo UI; do not dismiss removed capabilities as storage consolidation |
| BRICS | Source-status and original streams | Captured-panel adapters; bounded supplied-original YAML parser + explicit RAM fixture composition reviewed | Real source-status readers/config path and durable original writes unwired; configured availability never verified |
| BRICS | Stream add/delete | Fixture-only CRUD+management page preview | Original stream readers/durable persistence unwired |
| BRICS | Auto-refresh | Original60s logic ported dormant with fake-timer tests | Production callers/timers disabled until polling approval |
| BRICS | Full filtered/critical-only CSV | Original 8-column/category/country/search/critical/cap-before-filter pure serializer differential-tested | Original-order planner/pager/stream consumer reviewed only with supplied fixtures; production route/source adapter/full-history download missing; no separate BRICS DB activated |
| BRICS | Collection/classifier/dedupe/delivery | Present but unwired | Port relevant processing/delivery capabilities to Geo-only composition |
| BRICS | Separate BRICS collection/database | Intentionally dropped | Keep historical code for rollback; no new BRICS writes/migration |

Work order: Finder blocked functions + snapshot reconciliation; Geo digest/alerts/delivery; full CSV; BRICS stream management/auto-refresh; merged-origin PWA. Each increment gets independent review. Live cutover, stopping old collectors, Render preview settings, mail sends, live DB writes, polling and Telegram/WhatsApp delivery each remain separately gated. Map and weekly work can proceed independently where files do not collide. No external network activation is implied by offline wiring.

## Runtime boundary and closeout status (offline verification only)

Works means the named scope below, not public deployment. Current private_router now invokes build_preview. PREVIEW_GEO_ONLY_ENABLED=true selects reviewed Geo-only composition, default false retains legacy two-project rollback; actual Render setting and deployment unchanged. Geo-only reads remain off and fail closed without a separately injected reviewed factory. The owner's Geo-only storage choice is not implemented by changing labels alone. No collectors, shared accounts or mail activated; no old app stopped.

| Area | Works in current verified scope | Blocked or missing | Intentionally dropped |
|---|---|---|---|
| Accounts | Explicit MemoryStore HTTP/UI fixture, HTTPS login/settings/export/logout | Atomic Mongo/shared limiter, trusted TLS proxy/client identity, signup/recovery operator policy, actual merged login routing | None |
| Geo-only runtime | Injected read-only Geo-only composition tested, failure latch closes client | Actual Geo-only launcher setting/deployment, reviewed read factory/current mapping/read-only credential/Render config and production cutover approval | Separate BRICS stored-news DB/migration |
| CSV | Loaded sample, bounded generic stream fixture, original serializers and safety tests | Reviewed pure original-order keyset plan/injectedpager/originalstream consumer, but no production adapter/schema/consistent snapshot/index/collation/route/deadlines/throughput; UI cap warnings missing | None |
| Reports | Original digest/critical/weekly dry-run HTML; supplied gated events with UTC clock | Actual unsent queue, Apps Script send/receipt/mark integration, HTML/Telegram archive retention, alert scheduler | SMTP replacement (owner chose Apps Script) |
| Streams | Original supplied YAML fidelity, strict parsing, RAM add/delete copy; captured original panel | Persistent YAML/store edit, cross-worker locking, fresh source read, availability checks, player integration | No new separate BRICS news collection |
| Finder | Existing source/snapshot; nested code/notes/favourites/CSV/clipboard, PWA public-only offline fixture | Real network/CORS/provider disclosure, native print/AI report popup, hosted PWA/Safari/quota, offline CSV/shortlist caveats, JSON-LD origin | None |

Remaining work is not a reason to activate unsafe defaults. Preserve originals and complete offline contracts/tests while production choices stay explicit. Fixture accumulation cannot satisfy live source, delivery or account readiness. No claim of full merged parity is supported yet.
