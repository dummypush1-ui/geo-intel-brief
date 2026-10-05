# Current private merge status

As of the reviewed local increments through 58. This is a code/test status,
not a deployment, live source, availability or full parity certificate.
As reported by the author's local run: 816 tests, OK with 1 skip and 1
expected failure. Command: PYTHONPATH=tests /tmp/phase1-venv/bin/python -m
unittest discover. Recorded in the backup 58 completion report and run
https://github.com/dummypush1-ui/geo-intel-brief/actions/runs/37255729398
(the backup run confirms uploaded files, not independent test execution). The
expected failure pins unsupported multiple account Limiter instances per store.
No collector, mail, DB mutation, polling, Render change or cutover was performed
by these increments. Current external service state is not verified here.

Works means the stated local/supplied-data scope has code and exercised tests.
Blocked means preparation exists but a live dependency, policy or effect gate
is unresolved. Missing means no equivalent complete implementation. Dropped
means intentionally excluded from the selected composition, not deleted source.

| Feature | Local works | Blocked / missing / dropped | Evidence |
|---|---|---|---|
| Original Geo/BRICS source | Preserved modules/config/templates, pinned hashes and processing AST parity | Not imported as a merged live engine; copied source is not serving parity | preservation-manifest.json; tests/test_preservation.py |
| Private preview | Optional password/CSRF/secure-session gate, deny by default | Single-worker preview only; operator secrets/origin/proxy configuration and hosted validation needed; not accounts | preview_access.py; tests/test_preview_access.py |
| Launcher | Explicit default-off Geo-only switch, read-off creates no client | private_router injects no Geo factory: read-on fails closed. Legacy branch still exists, not selected by missing BRICS config | preview_launcher.py; PREVIEW_LAUNCHER_LIMITS.md |
| Selected stored news | Geo-only composition targets geo_intel/articles with read/mapping/private gates and explicit factory | Live credential, ownership/schema/index/deadlines and activation unverified. BRICS newsbot excluded here, no migration/deletion | geo_only_runtime.py; GEO_ONLY_LIMITS.md |
| Finder | Private served copy, search/detail/local lists/export and exact-index news context | Network default off; original provider features tested with intercepted fixtures only. Manual AIS refresh, no timer | FINDER_NETWORK_LIMITS.md; tests/test_cross_routes.py |
| Device offline Finder | Explicit public-only snapshot install, narrow worker scope | Browser quota/hosted HTTPS/iOS unverified; offline notes/lists session-only, no protected news cache | FINDER_OFFLINE_LIMITS.md |
| News UI | Loaded-row filtering, manual refresh, independent theme, critical panel, loaded charts | Bounded newest 100/collection read view, not full history or total counts; no automatic refresh | NEWS_PANEL_LIMITS.md; news_api.py |
| Live news/My channels | Seeded embeds, browser-local controls, separate from stored news | Current availability/autoplay not verified. Opening embeds contacts YouTube; not a network-free UI | LIVE_NEWS_LIMITS.md; COMPULSORY_CHANNEL_LIMITS.md |
| Country signals | Private API/UI with exact Geo labels and observed-history counts | No country risk index/baseline;28-day span is not coverage; bounded read view | COUNTRY_SIGNALS_LIMITS.md; tests/test_country_signals_routes.py |
| Country page/watch | Exact labels, local watchlist, manual newly-seen comparison | Code watch rules/background alerts/account sync missing; no delivery | COUNTRY_PAGE_LIMITS.md; WATCH_UPDATES_LIMITS.md |
| Reference map | Private page/API, manually loaded labelled chokepoints | Ports absent; no live ships/news geocoding/tiles in standard route; not live AIS map | tests/geospatial/test_map_route.py; ui/map.js |
| Weekly PDF | Private manual PDF download, supplied rows, concurrency 2/app | Bounded history, not complete weekly collection; mail/storage absent; multi-worker work limit missing | WEEKLY_REPORT_LIMITS.md; tests/test_weekly_routes.py |
| Original dashboards/reports | Supplied snapshots and hash-pinned original renderer functions | Original query/store/events composition unwired; SMTP original behavior preserved but not selected merged mail | dashboard_snapshots.py; EXPORT_DIGEST_LIMITS.md |
| CSV | Loaded sample export; original-order planner/pager/stream and separate dev HTTP fixture | Full production original adapter/route/index/snapshot missing. Local gated-reset serving proof is not natural slow-reader/Render proof | news_export/*LIMITS.md; tests/news_export/test_fixture_serving.py |
| Original unsent queue | Supplied Geo cap-before-score/all-fetched-ID renderer | Current unsent state unverified; fetched-vs-displayed marking policy OPEN; no mark writes | GEO_QUEUE_LIMITS.md |
| BRICS stream management | Separate captured-config/RAM edit fixture; supplied-byte revision transform | Durable YAML writer/CAS/recovery missing, no production config loader. RAM edits do not change captured players | BRICS_STREAM_LIMITS.md; STREAM_REVISION_LIMITS.md |
| Page-watch snapshots | Canonical UTC/URL, strict integrity/bounds, parser input/event caps and bounded diff | No actual fetching/source authorization/persisted baseline; fixed Nilgiried labels, strict-reject compatibility limits, no CPU deadline | PAGE_WATCH_LIMITS.md; tests/test_page_watch_contract.py |
| Sources/tariff evidence | Supplied observation/evidence panels distinguish unavailable/empty | No live health probe or verified current tariff/legal-effect feed | SOURCE_HEALTH_LIMITS.md; TARIFF_EVIDENCE_LIMITS.md |
| Collection | Original processing order plus fake-writer/offline cycle fixture | Live fetching/writer/schema/identity/atomicity/scheduler/cutover unconnected; no second collector | COLLECTION_PREPARE_LIMITS.md; OFFLINE_CYCLE_LIMITS.md |
| Apps Script mail | Preserved source and fake-service compatibility audit; offline mail contract | Authenticated delivery/claim/receipt ledger and cutover missing. Audit VM not isolation; duplicates/mark failure source risks | apps_script_audit/README.md; mail_bridge.py |
| Accounts | Memory-only service/HTTP/UI fixture, fences/session/settings and reservation tests | NOT merged login. Exactly one AccountService/Limiter per store. Shared adapter/multiworker/recovery/invite expiry missing; pinned two-instance defect | accounts/CONFORMANCE_LIMITS.md; accounts/HTTP_FIXTURE_LIMITS.md |
| Retention/archive | Aggregate original-fidelity audit | Lossless backup/retrieval/receipt policy unproven; original cleanup unsafe without verification; no delete | RETENTION_AUDIT_LIMITS.md |

| Dropped: BRICS tab/ticker | Original source retained only | Not part of selected workspace composition | LIVE_NEWS_LIMITS.md; ui/workspace.js |
| Dropped: old news tab/ticker | Source retained; new Live news UI separate | Old separate tab/ticker not selected | LIVE_NEWS_LIMITS.md |
| Dropped: BRICS stored news | Legacy fixtures/source retained | Geo-only branch excludes newsbot; no migration/delete | GEO_ONLY_LIMITS.md |
| Dropped: NVIDIA | Original source preserved | Excluded from Finder network preview scope | FINDER_NETWORK_LIMITS.md |

## Open security and source-policy items

Credential rotation for BRICS's public .env is an existing operator item;
completion is not verified here. Do not copy exposed values into new runtime.
Previously recorded site reviews remain open activation blockers: Saudi SPA
scraping prohibition, nilgiried.com with no published terms/robots located,
and Agencia Gov Brazil personal/non-commercial terms. These are recorded
review context, not a current live-policy verification. All staging scraper
rules remain off. Re-check actual terms and permitted use before any source
activation; no absence of terms is permission.

## Selected exclusions versus preserved source

BRICS stored news is excluded from the Geo-only branch, not erased from legacy
modules or fixtures. NVIDIA is excluded from Finder network preview scope.
SMTP is preserved legacy code, not a merged fallback to Apps Script. Telegram/
WhatsApp delivery, destructive cleanup and old scheduler/trigger installers are
not activated. No retained source implies approval to execute those effects.

## Before live operation

Reconcile exact current service/config/identity with the operator; independently
review source mapping/credential read-only authority, indexes/stable snapshots,
TLS proxy/host filtering, request/write/worker deadlines, concurrency and rollback.
Atlas operator check: inspect geo_intel/articles for the created_at descending
reader sort and consider {created_at: -1}; no index presence or createIndex is
asserted.
Choose and authorize each live activation/cutover/send/write/polling/cleanup
separately. Never infer completion from tests, old limits wording or this table.
Per-feature limits remain authoritative for scope and known contract differences.
