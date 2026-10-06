# Current private merge status

As of reviewed increment 71, after full offline parity check 68.
This is code/test status, not deployment or a live source certificate.
All 537 saved manifest files were restored from backup 67 and SHA-256 checked,
including original Finder assets. No synthetic original files were substituted.
Configured author command: PYTHONPATH=tests /tmp/phase1-venv/bin/python -m unittest discover.
944 tests ran in 95.9 seconds after increment 71: OK, 1 skip and 1 expected failure. The expected
failure pins unsupported multiple account Limiter instances per store. Earlier
workspace-recovery failures are not the current result. The backup workflow
checks file hashes; it does not independently run the full test suite.
No live collector, mail, DB mutation, polling, Render change or cutover occurred.
Current external service state is not verified by this table.

Works means the stated local/supplied-data scope has code and exercised tests.
Blocked means preparation exists but a live dependency, policy or effect gate
is unresolved. Missing means no equivalent complete implementation. Dropped
means intentionally excluded from the selected composition, not deleted source.

| Feature | Local works | Blocked / missing / dropped | Evidence |
|---|---|---|---|
| Original Geo/BRICS source | Preserved modules/config/templates, pinned hashes and processing AST parity | Not imported as a merged live engine; copied source is not serving parity | preservation-manifest.json; tests/test_preservation.py |
| Private preview | Optional password/CSRF/secure-session gate, deny by default | Single-worker preview only; operator secrets/origin/proxy configuration and hosted validation needed; not accounts | preview_access.py; tests/test_preview_access.py |
| Launcher | Explicit default-off Geo-only switch, read-off creates no client | private_router has a reviewed lazy narrow Geo read factory; reads remain off by default. Legacy branch still exists, not selected by missing BRICS config | preview_launcher.py; PREVIEW_LAUNCHER_LIMITS.md |
| Selected stored news | Geo-only composition targets geo_intel/articles with read/mapping/private gates and explicit factory | Live credential, ownership/schema/index/deadlines and activation unverified. BRICS newsbot excluded here, no migration/deletion | geo_only_runtime.py; GEO_ONLY_LIMITS.md |
| Finder | Private served copy, search/detail/local lists/export and exact-index news context | Network default off; original provider features tested with intercepted fixtures only. Manual AIS refresh, no timer | FINDER_NETWORK_LIMITS.md; tests/test_cross_routes.py |
| Device offline Finder | Explicit public-only snapshot install, narrow worker scope | Browser quota/hosted HTTPS/iOS unverified; offline notes/lists session-only, no protected news cache | FINDER_OFFLINE_LIMITS.md |
| News UI | Loaded-row filtering, manual refresh, independent theme, critical panel, loaded charts | Bounded newest 100/collection read view, not full history or total counts; no automatic refresh | NEWS_PANEL_LIMITS.md; news_api.py |
| Live news/My channels | Seeded embeds, browser-local controls, separate from stored news | Current availability/autoplay not verified. Opening embeds contacts YouTube; not a network-free UI | LIVE_NEWS_LIMITS.md; COMPULSORY_CHANNEL_LIMITS.md |
| Country signals | Private API/UI with exact Geo labels and observed-history counts | No country risk index/baseline;28-day span is not coverage; bounded read view | COUNTRY_SIGNALS_LIMITS.md; tests/test_country_signals_routes.py |
| Country page/watch | Exact labels, local watchlist, manual newly-seen comparison | Code watch rules/background alerts/account sync missing; no delivery | COUNTRY_PAGE_LIMITS.md; WATCH_UPDATES_LIMITS.md |
| Reference map | Private page/API, manually loaded labelled chokepoints | Ports absent; no live ships/news geocoding/tiles in standard route; not live AIS map | tests/geospatial/test_map_route.py; ui/map.js |
| Weekly PDF | Private manual PDF download, supplied rows, concurrency 2/app | Bounded history, not complete weekly collection; mail/storage absent; multi-worker work limit missing | WEEKLY_REPORT_LIMITS.md; tests/test_weekly_routes.py |
| Original dashboards/reports | Supplied snapshots and hash-pinned original renderer functions | Separately gated exact Geo events read composition feeds original digest; real event schema/role/host list unverified. Critical/weekly remain supplied article samples; SMTP original behavior preserved but not selected merged mail | dashboard_snapshots.py; EXPORT_DIGEST_LIMITS.md |
| CSV | Loaded sample export; original-order planner/pager/stream and separate dev HTTP fixture | Injected Geo same-snapshot/schema-scan original CSV adapter exists offline; production route/client/index/capability review and activation missing. Local gated-reset serving proof is not natural slow-reader/Render proof | news_export/*LIMITS.md; tests/news_export/test_fixture_serving.py |
| Original unsent queue | Supplied Geo cap-before-score/all-fetched-ID renderer | Current unsent state unverified; fetched-vs-displayed marking policy OPEN; no mark writes | GEO_QUEUE_LIMITS.md |
| BRICS stream management | Separate captured-config/RAM edit fixture; supplied-byte revision transform | Reviewed local-file revision CAS exists, not selected by runtime; durable Render volume or Atlas config store still unverified/missing. No live config loader. RAM edits do not change captured players | BRICS_STREAM_LIMITS.md; STREAM_REVISION_LIMITS.md |
| Page-watch snapshots | Canonical UTC/URL, strict integrity/bounds, parser input/event caps and bounded diff | No actual fetching/source authorization/persisted baseline; fixed Nilgiried labels, strict-reject compatibility limits, no CPU deadline | PAGE_WATCH_LIMITS.md; tests/test_page_watch_contract.py |
| Sources/tariff evidence | Supplied observation/evidence panels distinguish unavailable/empty | No live health probe or verified current tariff/legal-effect feed | SOURCE_HEALTH_LIMITS.md; TARIFF_EVIDENCE_LIMITS.md |
| Collection | Hash-pinned original post-fetch docs, fixture store and separate injected bulk article writer | Live fetching/full-text/source policy/write role/index/outcome recovery/scheduler/cutover unconnected; no second collector | COLLECTION_PREPARE_LIMITS.md; OFFLINE_CYCLE_LIMITS.md |
| Apps Script mail | Preserved source and fake-service compatibility audit; offline mail contract | Authenticated delivery/claim/receipt ledger and cutover missing. Audit VM not isolation; duplicates/mark failure source risks | apps_script_audit/README.md; mail_bridge.py |
| Accounts | Memory service/HTTP/UI fixture plus injected bounded Mongo transaction store; fences/session/settings and reservation tests | NOT merged login. Exactly one AccountService/Limiter per store. Real transaction/role/schema provisioning unverified; multiworker limiter/recovery/invite expiry missing; pinned two-instance defect | accounts/CONFORMANCE_LIMITS.md; accounts/HTTP_FIXTURE_LIMITS.md |
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

## Final offline visual scope (author observations)

Weekly PDF form and reference map inspected at 390px; PDF pages inspected from
fixture download. No horizontal overflow in these two UI pages. Original digest
renderer retains a 700px minimum layout at a 390px viewport: not phone-responsive.
Original weekly HTML also retains 680px layout; critical HTML fits 390px but
its alert icon glyph is missing. Finder core code details and country page pixels inspected at390px; readable
core hierarchy, no horizontaloverflow in fixture tests;
passed DOM tests or preserved bytes are not a complete visual certificate.
Independent reviewer verified hashes/tests/docs, not pixels. The visual notes
above are author observations. No UI rewrites or live source checks performed.

## Next decision menu, not an approval

1. Database check: exact Geo schemas, read-only role, sort/index/explain, snapshot
   and transaction support on actual Atlas tier. No index creation bundled.
2. Collection: source policy and verified feeds/full-text, write role, partial
   receipt recovery, fetched-versus-displayed and lossless retention policy.
3. Accounts and config: state provisioning, shared limiter/recovery/invite expiry,
   production HTTP wiring, and durable stream storage (local CAS alone is not
   free Render persistence).
4. Mail: Apps Script authentication, receipt/claim/retry ledger and marking policy.
5. Hosting: private origin/proxy/TLS/secrets, real serving deadlines/slow-client
   cleanup, staging deploy, rollback and eventual cutover.

These are remaining work, not checked-off activation steps. Live database checks,
writes, mail, polling, deploy and stopping original collectors require Push's
explicit permission. Offline build/test/private backup can continue.

## Increment 69: narrow mobile private preview

Digest and weekly private JSON previews now frame the sanitized original HTML
with fixed trusted CSS and a viewport. Original direct renderer and mail-builder
output remain unchanged and hash-pinned. Critical preview remains unchanged.
The preview keeps sanitized body style and wraps long words on a phone.
Reviewer approved this narrow scope after four wrapper tests and actual 390px
and 1280px screenshots. Reviewer route tests were not run (Flask unavailable);
author configured dependencies run the route tests as well.

The routes return JSON. Their CSP style-src 'self' is not proof that an eventual
iframe/srcdoc consumer can render this HTML. Test that exact consumer before
claiming hosted UI readiness. Desktop private preview is capped at 700px, not
identical to the original email. The weekly category subtable remains narrow
from the pre-existing sanitizer. Phone pixels do not establish email-client
responsiveness. No deployment, DB query or sending was added by this increment.

## Increment 70: separate injected Geo sample probe

Offline find-only20rowprobe, noenv/HTTP/startupactivation oroldgatebypass.
Exactgeo_intel/articles projectedcreated_at/published/score, noIDs/valuesreturned.
Aggregatecompatibilitycounts; sample/empty/unavailable distinct. Honestlabel:
read operations under a write-capable credential, not verified read-only access.
Fixedquery/io/connection/cleanup failure categories, never sourceerror text.
probe_issues_no_writes=true says what this probe issues, not credential powers.
Noindex/explain/role/snapshot/fullschema proof.9authornativefocusedPASS, reviewer
7of8initialtestsPASS (existinggatetest notrun, fullrepo missing); requested
doc/timeout/flagfixes applied.922fullsuitePASS1skip1expectedfailure.
Hostedprivatewrapper/auth/rate/deadline/logreview remains futurework.
Render screens held; no DBconnected/deployed/provisioned, URIcollected, writes
or real sends. DedicatedreadonlyDBuser is preferredlater access option.

## Increment 71: private manual check wrapper, no activation

Separate explicitfactory/POST wrapper andexecchild runner around70, no standard
launcher/gates/DBenvironmentactivation. AuthCSRF/exactorigin/noquery/busy10min
cooldown; fixedredactedJSON/4096bytechildoutput/10s sampledchildbudget/killwait.
ReviewV1/V2foundauthissues, fixed: atomichashreservation+singlehashslot, origin
login/logout, UTF8CSRFcomparison, import-light access, bounded128servernonces
revokedlogout, browserlogoutform, canonicalorigin. ReviewerV3SAFEprivate single
worker manualscope,21of23HTTP testsPASS;2neededUIassetsmissingfromzip. Author42
focused+944fullsuitePASS1skip1expectedfailure. Actual390pxformpixels inspected.

NoactualDB/Rendercheck/deploy/URIcollection. NohardHTTPdeadline orparentworker
forcedkillchildcleanup guarantee; clientdisconnect/logouting-flightprobe not
cancelled. Externalratecontrol, processlifecycle/hostproxy/cost/runtimechecks
required beforehostactivation. Sessions/cooldownperprocess, wallclockexpiry,
capselflockout/globalunauthbudgetburn/near1024urlencoded413 residualsdocumented.
Render screens held. DedicatedreadonlyDBuser preferred later, noindex/writes/
collectorstop/cutover/realsends inferred from manualcheckpreparation.

## Increment 72: reviewed offline scope

Closed memory account/workspace fixture; session checks, original gates unchanged. 390/1280 login/workspace/nav/logout pixels checked. Production accounts, shared limiter/recovery/invite expiry and settings sync remain blocked.
Author full configured suite: 958 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment 73: reviewed offline scope

Pure copied-memory country alerts, explicit rebaseline, bounded dedupe/inbox/history. No polling/delivery/durable state or authenticated source claim. URL queries stripped; path/text secrets not detected.
Author full configured suite: 970 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment 74: reviewed offline scope

Pure supplied WGS84 map layers with layer-local refusal and global envelope budget, freshness labels. No live sources, map UI, tiles or geocoding.
Author full configured suite: 980 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment 75: reviewed offline scope

Private supplied synthetic supported-schema archive. Original summary only 300 chars, not full-body recovery. Exact closed producer field types; incremental budget and consistency digest. No Atlas proof, durable backup or secret detection inside accepted strings.
Author full configured suite: 990 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment 76: reviewed offline scope

Separate offline collector-document and original Geo digest preview composition, independent supplied inputs and pinned dependencies. Whole-input bounds, visible scope notice. No fetch, send, write, mark or runtime wiring; no pixel/readiness claim.
Author full configured suite: 1001 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment 77: reviewed offline scope

Timed invite contract with atomic account claim validation. Expiry evaluated at explicit post-hash admission time, not commit time. Legacy integer snapshots non-expiring. No real provisioning, account activation or writes. No-burn only claim refusal; later signup failures remain. Full discovered1011 tests run in505/506 partitions OK,1skip/1expected.
Author full configured suite: 1011 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment 78: reviewed offline scope

Separate shared same-process memory admission ledger, collision-safe retained generations, exact opaque ticket ownership, bounded atomic admission and terminal transitions. Old Limiter/AccountService unchanged; production multi-instance limitation still open. Full discovered1026 tests passed513/513 partitions,1skip/1expected. No durable/cross-process/service activation claim.
Author full configured suite: 1026 tests OK, 1 skip/1 expected failure.
This milestone is offline code/test status, not live activation.

## Increment79: reviewed offline scope

Separate closed synthetic service-control-flow handles on one same-process78 memory ledger.13author+13independent focused tests PASS/SAFE. Original service/limiter/store/Mongo/78 source pins unchanged. Session-before-settlement gap and finally first-error masking explicitly tested and retained. No production limiter/account/HTTP activation or real credentials. Full configured1039 suite passed519+520 partitions,1expected/1skip.

## Increment80: supplied-fulltext offline source-semantic preparation

Separate private supplied download/extract outcome fixture preserves reviewed original<200 enrichment/strip/truncate/ellipsis and composes original lightweight docs. No real fetch/parser/import/threads/Telegram/durable backup; returned enriched text supplied, not verified/lossless.11author+11independent focused PASS/SAFE after category prevalidation refinement. Full configured1050 PASS525+262+263 partitions,1expected/1skip.

## Increment81: supplied parsed-entry RSS source-semantic selection

Separate supplied entry fixture preserving original slice/filter/field precedence/stripHTML and reviewed date parsing with explicit fixed-UTC default deviation. No live HTTP/XML/source health.10author+10independent focused PASS/SAFE; full configured1060 PASS530+265+265 partitions,1expected/1skip. No composition to80 or provider activation.

## Increment82: supplied feed/fulltext/original-doc pipeline

Separate composition81->80->64 preserving stage restrictions and deterministic date deviation.8author+8independent focused PASS/SAFE after rawURL refinement; configured1068 PASS534+267+267 partitions,1expected/1skip. No real RSS/XML/fulltext/mail/Telegram/store or health/fullarticle proof.

## Increment83: ordered supplied multi-feed global preparation

Separate0..4suppliedfeeds total100entries, original-orderflatten then80/64globallyonce. Mixedfailedsource labels+coverage_verifiedfalse, no healthy/completeclaim.7author+7independentfocusedPASS/SAFE; configured1075 PASS537+269+269partitions,1expected/1skip. Originalduplicatecorroboration countsrecords, notverifiedindependentsources. No liveeffects.

## Increment84: private synthetic Telegram formatter/batch audit

Source-native3500packingdiagnostic only, original record/batchtext+Python/UTF8/UTF16metrics, estimateunder-countgap and unsplitoversizedsingleflag. Caller syntheticassertionnotproof; NOTFORDELIVERY, no providerlimit/readiness/fullcontent/durabilityclaim.8author+8independentfocusedPASS/SAFE; configured1083 PASS541+271+271partitions,1expected/1skip. No liveeffects.

## Increment85: fixed public-synthetic real feedparser experiment

SeveninternalhashpinnedRSS/Atom/bozocases, realfeedparser6.0.11/SDKpins+Expat2.4.7guardedLinuxchild; separateoriginalASToracle agrees. No callerXML/URL/path, no liveHTTP/sourcehealth or85composition80. PythonnetworkguardsnotOSisolation/noI/Oproof.7author+7independentfocusedPASS/SAFE; configured1090 PASS545+272+273partitions,1expected/1skip.

## Increment86: fixed-seven-case parser/supplied-enrichment/document pipeline

Wrapperonly existing85enums, runtimeonechild then80/64once. Suppliedsyntheticoutcomes/private, fixeddateoffsetspreserved, bozometadatanothealth/error.6author+6independentfocusedPASS/SAFE (plus11existing80); configured1096 PASS548+274+274partitions,1expected/1skip. No newXML/livecollector/DB/mail/Telegramactivation.

## Increment87: offline dependency candidate audit

25metadata-derivedclosure,24cachedcompatiblewheelhashes, missing sgmllib3k1.0.0wheel (sdistnotbuilt). Candidate NOTINSTALLABLE/freshinstall-smoke-SDK-freshsuiteNOTATTEMPTED. Currentconfiguredregressiondifferentfromreproduction; no originalrequirements/venvchange/networkfetch.7authorfocusedPASS; independent v3 SAFE as blocked candidate, review cache absent and 119/263 baseline files unavailable to reviewer. Full configured1103 PASS551+276+276 partitions,1expected/1optionalPDFskip; not fresh reproduction.

## Increment88: isolated offline build/install audit

Independent SAFE scoped audit. Cached sgmllib sdist safely inspected/built with
pinned local tools inside bubblewrap namespaces; produced wheel source/tags/
metadata/hash verified and24cachedwheels rehashed. Separate25dependency hashed
wheel-only freshvenv install, pip-check/closure/pureSDK/85physicalpins/backend
verified. Fresh fullsuite BLOCKED: isolated loopback cannot be brought up
(Operation not permitted), no hostnetwork fallback. Configured1112 tests run,
suite OK with1expectedfailure/1skip, not fresh-environment proof. Original87
candidate immutable; source/cache/buildtool evidence author-local; single
build no deterministicbyteclaim; lock not a delivered artifactbundle. No
production/Render/Atlas/delivery/readiness claim.

## Increment89: additive unselected account/session/settings HTTP composition

7author+7independentfocused tests OK, SAFE scopedcomposition. Exact injected
service/KDF/limiter/store/policy, private news/static/export/session guards,
strictOrigin/CSRF/cookies, per-user settingsCAS/compulsoryRepublic tested with
Memory/fakeMongo only. Collaborators trustedcode, not authenticated by types;
one service/limiter perstore/process required, multiworkerdefect unfixed.
Serving with realMongo could write, not done/authorized. Selectednews reader
shared, not personalized; no synced browserUI/accountpage/pixelchange delivered.
No productionlogin/proxy/activation readiness; configured1119tests run, suiteOK559+280+280partitions,1expectedfailure/1skip; not freshsuiteproof.
