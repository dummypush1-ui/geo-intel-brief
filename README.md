# Geo Intel Brief

Copyright (c) 2026 Push. All rights reserved.

Geo Intel Brief brings geopolitical news, trade-code lookup and BRICS source features into one codebase. The Flask workspace connects stored news with country views, story groups, trade context, exports and report tools. The original Finder, Geo and BRICS code remains in the repository.

**The merge is in progress.** A public read-only news preview is implemented, but collectors, mail, account login and the full Finder provider connection are not mounted into that public launcher. Prepared code and passing local tests do not mean a feature is live. The current production entry factory is `production_entry:create_app()`, delegating to the same guarded public builder with collection and mail default OFF.

## Start here

- [Architecture and code map](#doc-038)
- [Configuration guide](#doc-040)
- [Sanctions operator policy](#doc-236) - manual reviewedHashes, no approval endpoint
- [GST grounding](#doc-233) - operator_reviewed required
- [Monitor health](#doc-234) - pending_issues and uncertain outcomes
- [Folder cleanup proposal](#doc-041) - a plan, not a file move
- [Feature history and limits](#doc-075) - historical checkpoints; check the newer module-specific notes too
- [Security notes](#doc-001)
- [License](LICENSE)

## Entry points

| Entry point | Purpose | Important limit |
|---|---|---|
| `integration.private_router:app` | Deny-by-default private preview | Default settings do not grant workspace access or enable reads. Password preview is not account login. |
| `public_preview106:app` | Explicit public empty-sample preview | No stored-news client. All public-mode gates must match. |
| `public_live107:app` | Explicit public Geo stored-news preview | Read-only `geo_intel/articles`, latest up to 100 documents, bounded cache and public field filtering. Requires separately verified disclosure and database role. |
| `server.js` | Preserved Finder updater service | Starts a refresh timer. **Not** the merged web app. |
| `proxy.js` | Preserved Finder AI/AIS proxy | Separate provider/network service, not mounted by the public Flask launcher. |
| `intelligence/geo/`, `intelligence/brics/` | Preserved original engines | Can connect, schedule, send or clean up. Do not launch them as a shortcut to starting the merge. |

There is no single "enable everything" switch. Do not use `npm start` for the Flask workspace: it starts the updater.

## Run a safe local check

Use Python 3.10 or a separately reviewed compatible version. Node 22 or newer is needed for the Finder's Node tests and built-in WebSocket support. Run from the repository root.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-staging.txt
```

`requirements-staging.txt` installs the basic Flask/Mongo preview dependencies. It is not the full offline test closure, a hash-locked installation or proof of the deployed environment. Package installation accesses the configured package index. The current active requirements and reviewed runtime candidate pin Gunicorn 26.2.0 (upgrade commit736de534). Older archived notes and receipts describe22.0.0 or23.0.0; those are historical, not current install instructions. A local install does not prove the deployed environment.

With a clean local environment, start the no-read, deny-by-default launcher:

```bash
PREVIEW_GEO_ONLY_ENABLED=true \
PREVIEW_ACCESS_ENABLED=false \
NEWS_READ_ENABLED=false \
NEWS_EVENTS_READ_ENABLED=false \
FINDER_NETWORK_PREVIEW_ENABLED=false \
gunicorn integration.private_router:app \
  --bind 127.0.0.1:8000 --workers 1 --threads 2 --timeout 30
```

This is a startup check, not an unlocked demo. `/workspace` returning 403 is expected. Keep database URIs and provider keys out of this local check. Unset inherited operational variables before using a development shell.

For an empty public preview or private password preview, use the exact mode-specific settings in [Configuration](#doc-040). Public modes require a canonical HTTPS origin; changing the origin check to make HTTP work would weaken the boundary.

## Tests

A small offline integrity check uses only the standard library:

```bash
PYTHONPATH=tests python3 -m unittest \
  test_preservation test_package_manifest test_collector122_inventory
```

The full configured suite uses additional dependencies, verified parser artifacts and Node:

```bash
PYTHONPATH=.:collector108_prep python -m unittest discover -s tests
```

See [the dependency build notes](#doc-182), [the current PDF profile](#doc-205) and [the future deployment contract](#doc-212). Some historical checks need their recorded artifact cache. Missing artifacts are unverified, not passed. Do not treat old test counts in documents as a current full-suite result.

The historical offline candidate lock still records its missing wheel/hash. The newer `integration/security_candidate/requirements-security-candidate.txt` has verified package hashes and a hashed `sgmllib3k` source archive; its install and `pip check` were tested separately. Its legacy source-build bootstrap is not a fully hash-locked build chain. The frozen future-deploy lock remains separate and requires verified wheel artifacts, including a locally built `sgmllib3k` wheel. Neither source tests nor a candidate install prove the deployed environment.

Historical gate notes record1469 root cases plus285 collector cases,10 checks cases and26 world cases. Those counts are not a claim about the current source suite; the staging manifest is an integrity inventory, not a fresh execution receipt. See [exact gate commands](#doc-042).

## Configuration and safety

Use environment variables, not committed credentials. `.env.example` lists the historical and private settings; the configuration guide also explains newer public-mode gates absent from that example. The Flask launchers read the process environment directly; copying `.env.example` to `.env` does not load it automatically.

- A read facade does not make a privileged MongoDB credential read-only. Verify the actual Atlas role.
- Public news is a bounded stored-news view, not full-database search, whole-history totals or source fact-checking.
- Apps Script is the selected merged mail path. SMTP remains preserved legacy code, not an automatic fallback.
- Collector preparation packages and mail/account/provider fixtures need separate mounting, source review and activation.
- Keep source-policy restrictions, credential rotation and cutover decisions separate from code cleanup.
- Stop old collectors only after a reviewed migration and explicit cutover decision. Two writers can create duplicates.

This README describes source behavior, not the current Render settings, database state or provider-account permissions. No production changes are needed for this documentation cleanup.

## Separate anonymous Node proxy

The preserved `proxy.js` service now uses socket-peer identity by default, with 20 requests/peer per 10 minutes and 60 shared request/upstream-attempt budgets per process. Until actual Render proxy peer IPs and verified single appended XFF topology configure `PROXY_TRUSTED_PEERS`, all users behind one proxy share one 20/10min bucket per instance. This conservative availability regression replaces spoofable XFF buckets; a flood of distinct peers can still drain the shared cap. APP_SECRET is public client material, not login. The public Flask E1 guard is a different boundary. No live proxy configuration or provider call was made.

`PROXY_PER_PEER_LIMIT`/`PROXY_SHARED_LIMIT` default to20/60, bounded1-1000 and per-peer <=shared. After verified trust config, individual client buckets apply. Shared traffic caps are not a billing guarantee; provider free-tier/zero-spend settings still need current verification.


## Accepted scheduler217 v4 source backup

This is a source backup only, not an installed or active Apps Script scheduler. Existing Apps Script files remain unchanged. The accepted source and offline fake-service tests are in `integration/scheduler217/`. The setup instructions below were folded into this README at the owner's request; no separate setup Markdown file is added.

# Scheduler 217: source preparation only

No Apps Script install, trigger creation, property change, mail, backend request or repository push was performed. Node fixtures are synthetic and do not prove Apps Script permissions, persistence, quota, event delivery, concurrency or sending. This is not live-proven.

## Deliberately OFF native timers

Every installer, remover and handler requires an exact primitive `true` argument and both `MAIL_V1_SCHEDULER_ENABLED` and `MAIL_V1_ENABLED` properties equal to the string `true`. A missing/non-true argument returns before any service access. With a true argument, only Script Properties are read until the second gate passes. No source caller enables an entry point.

Native Apps Script timers provide an event, not an explicit true argument. Consequently these entry points stay OFF when invoked directly by a native timer. A separately approved and reviewed adapter is required before this can become unattended scheduling. Do not substitute a wrapper passing true without that review. Internal calls to 216 occur only after the handler gates, ownership check and durable occurrence reservation.

## Owner-managed configuration

The owner chose a critical interval of 10 minutes and will manage the weekly schedule directly in Apps Script. He sets and edits day, time and timezone in Script Properties; set MAIL217_CRITICAL_MINUTES to 10 for that choice. No weekly day/time/timezone has been supplied, and this package does not choose it. There is still no source default. Until all required values exist and validate, installation fails closed. Properties must all exist:

- `MAIL217_WEEKLY_DAY`: full uppercase weekday, MONDAY through SUNDAY.
- `MAIL217_WEEKLY_TIME`: HH:mm, 24-hour local wall time.
- `MAIL217_CRITICAL_MINUTES`: one of 1, 5, 10, 15, 30.
- `MAIL217_TIMEZONE`: named timezone, checked by Utilities formatting before trigger mutation.

There are no defaults. Test fixtures (THURSDAY 11:23, 10 minutes, Etc/UTC) are fake, not an owner instruction. Weekly hour/minute is approximate, not guaranteed exact. Apps Script nearMinute allows plus or minus 15 minutes. A delayed timer can cross an occurrence boundary; exact schedule-window semantics remain a live-design blocker.

## Managed installation and recovery

ScriptLock covers validation, trigger enumeration, quota and state mutations. It is never held across 216, which may acquire the same lock.

`MAIL217_OWNED` holds mutually exclusive active, staged and inactive ID arrays. Installer refuses any same-handler trigger not already owned, including a first install with pre-existing same-name triggers. Adoption requires separate manual review of owner-named IDs; there is no automatic adoption tool here. Other creators' triggers may be invisible to getProjectTriggers, so project-wide ownership is not proved.

All visible triggers count toward the 20-trigger limit. Two free staging slots are required before mutation. Actual service quotas may still refuse creation; the check is not a reservation.

The installer writes/readbacks `MAIL217_OPERATION` before the first create. It creates both new triggers before deleting anything, journals each returned ID, persists/readbacks staged IDs, then flips new IDs active and old IDs inactive before retiring old owned IDs. A nonempty operation record blocks handlers and future install/remove attempts. This conservative rule also blocks sending between the active flip and final cleanup.

An exception preserves the operation record and whatever IDs are known. If creation succeeds but the call fails before returning/persisting its ID, the created trigger is unknown, inactive and requires manual reconciliation. No automatic retry, rollback or delete-by-handler is attempted. After staged persistence/readback failure or active flip/delete failure, the same hold applies. Old triggers are retained until successful retirement; deletion is not transactional and cannot recreate an old trigger with the same ID or execution history.

Removal writes/readbacks a removal operation and sets all owned IDs inactive before deletion. It deletes only those IDs, never unrelated or unowned same-name triggers. A failure keeps the hold.

Manual recovery must compare live trigger IDs/handlers against the journal and owner-approved configuration, identify unknown new triggers, inspect occurrence/backend pending records, and receive a reviewed decision before changing state. Do not clear the operation record just to unblock execution. This package intentionally supplies no recovery mutation command.

## Occurrences and sending

Handler requires a string event triggerUid in the persisted active-owned set. Missing, unknown, staged or inactive IDs refuse; any operation hold refuses too.

Before calling 216, it writes/readbacks an occurrence ledger under the shared lock. Weekly keys use the Monday-start local calendar week; critical keys use epoch interval buckets. Both handler paths use the same durable ledger and release the lock before 216. A repeated key never calls 216 again. Failure after reservation loses that occurrence pending manual action, even if 216 returned OFF or failed before sending. It is never automatically resent.

The ledger stops at 128 entries; there is no silent pruning or rollover. Unattended operation therefore remains blocked until an approved retention/archive design exists. These keys are conservative local dedup, not proof of exactly-once email delivery, cross-project dedup or backend claim correctness.

## Collection-completion gate remains downstream

A timer firing does not prove collection or DB save completed. This source does not check collector coverage, completed job ID, durable database commit, freshness or digest readiness. E/backend must prove completed committed data and coverage before digest preparation; 216/bridge claim/ack/pending reconciliation must remain intact. Backend 217 is held and no production sending authority, sender/recipient approval or collection-completion integration is established. Do not mark E/F live or Step 6 complete from these tests.

## Current reference checks

Read on October 10, 2026:

- Installable events include triggerUid: https://developers.google.com/apps-script/guides/triggers/events
- ClockTriggerBuilder creates a Trigger; Trigger.getUniqueId returns its ID: https://developers.google.com/apps-script/reference/script/clock-trigger-builder and https://developers.google.com/apps-script/reference/script/trigger
- nearMinute is plus/minus 15 minutes; everyMinutes accepts 1, 5, 10, 15, 30: https://developers.google.com/apps-script/reference/script/clock-trigger-builder
- Trigger limit is 20 per user per script, and quotas can change: https://developers.google.com/apps-script/guides/services/quotas
- Installable triggers run as their creator; one account cannot see another account's triggers: https://developers.google.com/apps-script/guides/triggers/installable

Run local checks: `node --check < scheduler217.gs` and `node test_scheduler217.cjs`. They make no service calls. Only source and fake behavior are checked.

## Known held or lost windows and later changes

A trigger firing during installation or removal is held and never automatically retried. Its intended occurrence may be lost; manual review is required rather than catch-up mail. Failure after durable reservation likewise has no auto-retry.

The 128-entry shared ledger serves both weekly and critical paths. A critical timer every 1-30 minutes fills it in roughly 2-64 hours of successful reservations (weekly entries reduce this), then blocks weekly as well. At the owner-chosen 10-minute interval, 128 critical reservations take 1,280 minutes, about 21 hours 20 minutes; weekly reservations reduce the capacity further. A later reviewed change should use separate ledgers per kind and a safe pruning/archive rule for past critical windows. Neither separation nor pruning is implemented here. Delayed/replayed events and backend pending/claim state must be accounted for before designing expiry.

The schedule cannot fire mail as written: native timers pass only an event, so enable !== true keeps every timer invocation OFF until a separately reviewed adapter exists. Creating a trigger does not change this.


## Consolidated reference archive

The following sections preserve the original documentation bytes and source hashes. They are historical source notes, not proof of current deployment or permission to activate services. Use the current entrypoint, lock files and tests for current behavior. Former paths are lookup keys, not physical files.


### Former documentation paths

- [REVIEW.md](#doc-000)
- [SECURITY.md](#doc-001)
- [collector108_prep/ASSESSMENT.md](#doc-002)
- [collector108_prep/DEPENDENCY-SECURITY-PLAN.md](#doc-003)
- [collector108_prep/FREE-TOPOLOGY.md](#doc-004)
- [collector108_prep/JOB-CONTRACT.md](#doc-005)
- [collector108_prep/README.md](#doc-006)
- [collector108_prep/RECOVERY-GATES.md](#doc-007)
- [collector108_prep/SOURCES.md](#doc-008)
- [collector109_prep/ENGINE-STAGE.md](#doc-009)
- [collector109_prep/wiring/WIRING-STAGE.md](#doc-010)
- [collector110_prep/STAGE110.md](#doc-011)
- [collector111_prep/STAGE111.md](#doc-012)
- [collector112_prep/STAGE112.md](#doc-013)
- [collector113_prep/STAGE113.md](#doc-014)
- [collector114_prep/STAGE114.md](#doc-015)
- [collector114_prep/TRANSPORT-DESIGN.md](#doc-016)
- [collector115_prep/PROFILE-DESIGN.md](#doc-017)
- [collector115_prep/STAGE115.md](#doc-018)
- [collector116_prep/NETWORK-COMPOSITION-DESIGN.md](#doc-019)
- [collector116_prep/STAGE116.md](#doc-020)
- [collector117_prep/CYCLE-DESIGN.md](#doc-021)
- [collector117_prep/STAGE117.md](#doc-022)
- [collector118_prep/FULLTEXT-DESIGN.md](#doc-023)
- [collector118_prep/STAGE118.md](#doc-024)
- [collector119_prep/STAGE119.md](#doc-025)
- [collector120_prep/GNEWS-DESIGN.md](#doc-026)
- [collector120_prep/STAGE120.md](#doc-027)
- [collector121_prep/STAGE121.md](#doc-028)
- [collector122_prep/TELEGRAM-SAFE-PACKING-DESIGN.md](#doc-029)
- [collector123_prep/SHARED-BUDGET-DESIGN.md](#doc-030)
- [collector124_prep/FRAMING-DESIGN.md](#doc-031)
- [collector125_prep/COMPOSITION.md](#doc-032)
- [collector126_prep/EXTRA-FEED-DESIGN.md](#doc-033)
- [collector127_prep/EXTRA-COMPOSITION.md](#doc-034)
- [collector128_prep/PROJECTION-DESIGN.md](#doc-035)
- [collector129_prep/SELECTION-DESIGN.md](#doc-036)
- [collector130_prep/BOUNDED-COMPOSITION.md](#doc-037)
- [docs/ARCHITECTURE.md](#doc-038)
- [docs/CLAIM-SOURCES.md](#doc-039)
- [docs/CONFIGURATION.md](#doc-040)
- [docs/FOLDER-PLAN.md](#doc-041)
- [docs/TEST-GATES.md](#doc-042)
- [feature_finder_prep/MOUNT-DESIGN.md](#doc-043)
- [feature_mail_mount/DESIGN.md](#doc-044)
- [feature_mail_mount/HANDLERS216.md](#doc-045)
- [feature_mail_mount/OPERATIONS-CONTRACT.md](#doc-046)
- [feature_related_prep/ADJUDICATION-DESIGN.md](#doc-047)
- [integration/API-V1-187.md](#doc-048)
- [integration/ARTICLE_ARCHIVE_LIMITS.md](#doc-049)
- [integration/BRICS_STREAM_LIMITS.md](#doc-050)
- [integration/BROKER211.md](#doc-051)
- [integration/COLLECTION_PREPARE_LIMITS.md](#doc-052)
- [integration/COLLECTOR197A.md](#doc-053)
- [integration/COLLECTOR197B.md](#doc-054)
- [integration/COLLECTOR197C.md](#doc-055)
- [integration/COLLECTOR197EA.md](#doc-056)
- [integration/COLLECTOR197EBA.md](#doc-057)
- [integration/COLLECTOR_MAIL_FIXTURE_LIMITS.md](#doc-058)
- [integration/COMPULSORY_CHANNEL_LIMITS.md](#doc-059)
- [integration/CONTEXT-EXCERPT208.md](#doc-060)
- [integration/COPY191.md](#doc-061)
- [integration/COPY195.md](#doc-062)
- [integration/COUNTRY_ALERTS_LIMITS.md](#doc-063)
- [integration/COUNTRY_PAGE_LIMITS.md](#doc-064)
- [integration/COUNTRY_SIGNALS_LIMITS.md](#doc-065)
- [integration/DIGEST-DATES202.md](#doc-066)
- [integration/DIGEST-EMAIL218.md](#doc-067)
- [integration/DIGEST-RENDER203.md](#doc-068)
- [integration/DIGEST-WINDOWS193.md](#doc-069)
- [integration/EVENTS210.md](#doc-070)
- [integration/EVENT_READER_LIMITS.md](#doc-071)
- [integration/EXISTING-SCHEMA215.md](#doc-072)
- [integration/EXPORT_DIGEST_LIMITS.md](#doc-073)
- [integration/FAKE_WRITER_LIMITS.md](#doc-074)
- [integration/FEATURE_STATUS.md](#doc-075)
- [integration/FINDER-BROWSER229.md](#doc-076)
- [integration/FINDER-NETWORK230.md](#doc-077)
- [integration/FINDER198A.md](#doc-078)
- [integration/FINDER198BA.md](#doc-079)
- [integration/FINDER198BB.md](#doc-080)
- [integration/FINDER198C.md](#doc-081)
- [integration/FINDER198D.md](#doc-082)
- [integration/FINDER198OPS.md](#doc-083)
- [integration/FINDER_NESTED_LIMITS.md](#doc-084)
- [integration/FINDER_NETWORK_LIMITS.md](#doc-085)
- [integration/FINDER_OFFLINE_LIMITS.md](#doc-086)
- [integration/FINDER_PARITY_PLAN.md](#doc-087)
- [integration/FINDER_SNAPSHOT_NOTES.md](#doc-088)
- [integration/FIXED_PARSER_PIPELINE_LIMITS.md](#doc-089)
- [integration/GEO_ARTICLE_WRITER_LIMITS.md](#doc-090)
- [integration/GEO_COLLECTOR_CONTRACT_LIMITS.md](#doc-091)
- [integration/GEO_EVENTS_COMPOSITION_LIMITS.md](#doc-092)
- [integration/GEO_ONLY_LIMITS.md](#doc-093)
- [integration/GEO_PROBE_HTTP_LIMITS.md](#doc-094)
- [integration/GEO_QUEUE_LIMITS.md](#doc-095)
- [integration/GEO_READ_FACTORY_LIMITS.md](#doc-096)
- [integration/GEO_SAMPLE_PROBE_LIMITS.md](#doc-097)
- [integration/HOST197DA.md](#doc-098)
- [integration/HTML-TEXT209.md](#doc-099)
- [integration/LIVE_NEWS_LIMITS.md](#doc-100)
- [integration/MAIL-CANDIDATE219.md](#doc-101)
- [integration/MAIL-EXCLUSION223.md](#doc-102)
- [integration/MAIL-LEDGER212.md](#doc-103)
- [integration/MAIL-PREFLIGHT225.md](#doc-104)
- [integration/MAIL-REDERIVE221.md](#doc-105)
- [integration/MAIL-SURFACE217.md](#doc-106)
- [integration/MAP_LAYERS_LIMITS.md](#doc-107)
- [integration/NATIVE-MAIL-PROJECTION224.md](#doc-108)
- [integration/NATIVE200A.md](#doc-109)
- [integration/NATIVE200BA.md](#doc-110)
- [integration/NATIVE200BB.md](#doc-111)
- [integration/NATIVE200BC.md](#doc-112)
- [integration/NATIVE200CA-OWNER.md](#doc-113)
- [integration/NATIVE200CB.md](#doc-114)
- [integration/NATIVE201A.md](#doc-115)
- [integration/NATIVE201B.md](#doc-116)
- [integration/NATIVE201GUARD.md](#doc-117)
- [integration/NEWS-PAGES185.md](#doc-118)
- [integration/NEWS_PANEL_LIMITS.md](#doc-119)
- [integration/OFFLINE232.md](#doc-120)
- [integration/OFFLINE_CYCLE_LIMITS.md](#doc-121)
- [integration/PAGEWATCH_REPORT_LIMITS.md](#doc-122)
- [integration/PAGE_WATCH_LIMITS.md](#doc-123)
- [integration/POST-JSON207.md](#doc-124)
- [integration/PREVIEW_LAUNCHER_LIMITS.md](#doc-125)
- [integration/PRIVATE_NEWS_FIELDS_LIMITS.md](#doc-126)
- [integration/READINESS233.md](#doc-127)
- [integration/RECIPIENT-SCOPE220.md](#doc-128)
- [integration/REPLAY199A.md](#doc-129)
- [integration/REPLAY199B.md](#doc-130)
- [integration/REPLAY199CA.md](#doc-131)
- [integration/REPLAY199CB.md](#doc-132)
- [integration/REPLAY199CC.md](#doc-133)
- [integration/REPORT227.md](#doc-134)
- [integration/REPORT228.md](#doc-135)
- [integration/REPORT_PREVIEW_FRAME_LIMITS.md](#doc-136)
- [integration/REPORT_STYLE_LIMITS.md](#doc-137)
- [integration/REQUESTED_FEATURES.md](#doc-138)
- [integration/RETENTION_AUDIT_LIMITS.md](#doc-139)
- [integration/RUNNER199LOCK.md](#doc-140)
- [integration/SCHEDULE-CALLER214.md](#doc-141)
- [integration/SCHEDULE-OCCURRENCE205.md](#doc-142)
- [integration/SCHEDULER-CIVIL-ZONES206.md](#doc-143)
- [integration/SCROLL186.md](#doc-144)
- [integration/SENDER-SCOPE222.md](#doc-145)
- [integration/SHIPS226.md](#doc-146)
- [integration/SINGLE_DB_PLAN_LIMITS.md](#doc-147)
- [integration/SMTP-CALLER213.md](#doc-148)
- [integration/SMTP-CONFIG204.md](#doc-149)
- [integration/SOURCE_HEALTH_LIMITS.md](#doc-150)
- [integration/STREAM_DISK_LIMITS.md](#doc-151)
- [integration/STREAM_REVISION_LIMITS.md](#doc-152)
- [integration/SUPPLIED_FEED_FIXTURE_LIMITS.md](#doc-153)
- [integration/SUPPLIED_FULLTEXT_FIXTURE_LIMITS.md](#doc-154)
- [integration/SUPPLIED_MULTI_FEED_LIMITS.md](#doc-155)
- [integration/SUPPLIED_PIPELINE_LIMITS.md](#doc-156)
- [integration/TARIFF_EVIDENCE_LIMITS.md](#doc-157)
- [integration/TELEGRAM_FORMAT_AUDIT_LIMITS.md](#doc-158)
- [integration/TOKEN-REMOVAL196.md](#doc-159)
- [integration/VALIDATION188.md](#doc-160)
- [integration/WATCH_UPDATES_LIMITS.md](#doc-161)
- [integration/WEATHER231.md](#doc-162)
- [integration/WEEKLY_REPORT_LIMITS.md](#doc-163)
- [integration/accounts/CONFORMANCE_LIMITS.md](#doc-164)
- [integration/accounts/HTTP_FIXTURE_LIMITS.md](#doc-165)
- [integration/accounts/INVITE_EXPIRY_LIMITS.md](#doc-166)
- [integration/accounts/MERGED_FIXTURE_LIMITS.md](#doc-167)
- [integration/accounts/MONGO_STORE_LIMITS.md](#doc-168)
- [integration/accounts/README.md](#doc-169)
- [integration/accounts/SHARED_LEDGER_FIXTURE_LIMITS.md](#doc-170)
- [integration/accounts/SHARED_SERVICE_FIXTURE_LIMITS.md](#doc-171)
- [integration/accounts/WIRED_HTTP_LIMITS.md](#doc-172)
- [integration/apps_script_audit/README.md](#doc-173)
- [integration/bcrypt189/README.md](#doc-174)
- [integration/bounded_rss/CONTRACT.md](#doc-175)
- [integration/build_provenance/CONTRACT.md](#doc-176)
- [integration/collection_receipts/CONTRACT.md](#doc-177)
- [integration/db_contract/CONTRACT.md](#doc-178)
- [integration/db_contract/QUERY-REVIEW.md](#doc-179)
- [integration/dependabot_security173/README.md](#doc-180)
- [integration/dependency_audit/README.md](#doc-181)
- [integration/dependency_build/README.md](#doc-182)
- [integration/feedparser_audit/LIMITS.md](#doc-183)
- [integration/fulltext_policy/README.md](#doc-184)
- [integration/geonews_digest/README.md](#doc-185)
- [integration/geospatial/README.md](#doc-186)
- [integration/geospatial/data/DATA_SOURCES.md](#doc-187)
- [integration/india_open_data/README.md](#doc-188)
- [integration/india_open_data/SOURCES.md](#doc-189)
- [integration/manage_fixture95/LIMITS.md](#doc-190)
- [integration/news_export/FIXTURE_HTTP_LIMITS.md](#doc-191)
- [integration/news_export/GEO_SNAPSHOT_LIMITS.md](#doc-192)
- [integration/news_export/KEYSET_LIMITS.md](#doc-193)
- [integration/news_export/LOCAL_SERVING_LIMITS.md](#doc-194)
- [integration/news_export/ORIGINAL_CONTRACT_LIMITS.md](#doc-195)
- [integration/news_export/ORIGINAL_STREAM_LIMITS.md](#doc-196)
- [integration/news_export/RAW_PAGER_LIMITS.md](#doc-197)
- [integration/nilgiri_transport_research93/CONTRACT.md](#doc-198)
- [integration/nilgiri_transport_research93/README.md](#doc-199)
- [integration/nilgiri_transport_research93/RESULTS.md](#doc-200)
- [integration/nilgiri_watch_fixture/LIMITS.md](#doc-201)
- [integration/public_live107/README.md](#doc-202)
- [integration/public_preview106/README.md](#doc-203)
- [integration/publication_dates/CONTRACT.md](#doc-204)
- [integration/pypdf_remediation105/README.md](#doc-205)
- [integration/rss_catalog/README.md](#doc-206)
- [integration/security_candidate/README.md](#doc-207)
- [integration/security_candidate/bump158/README.md](#doc-208)
- [integration/security_candidate91/README.md](#doc-209)
- [integration/security_candidate91/planning-notes.md](#doc-210)
- [integration/security_candidate91/sources.md](#doc-211)
- [integration/security_maintenance94/DEPLOY-CONTRACT.md](#doc-212)
- [integration/security_maintenance94/README.md](#doc-213)
- [integration/weekly_report/README.md](#doc-214)
- [intelligence/brics/README.md](#doc-215)
- [intelligence/geo/BACKUP-HELD184.md](#doc-216)
- [intelligence/geo/BROWSE-INDEXES192.md](#doc-217)
- [intelligence/geo/DATE-EVENTS182.md](#doc-218)
- [intelligence/geo/LEGACY-SANCTIONS183.md](#doc-219)
- [intelligence/geo/QUERY-INDEXES181.md](#doc-220)
- [intelligence/geo/README.md](#doc-221)
- [intelligence/geo/collectors/EXTRA-FEEDS-ATTRIBUTION-PLAN.md](#doc-222)
- [legacy-config/finder-README.md](#doc-223)
- [portable_validation28/SPEC.md](#doc-224)
- [portable_validation28b/SPEC.md](#doc-225)
- [proxy_runtime/CORS190.md](#doc-226)
- [proxy_runtime/IDENTITY-POLICY.md](#doc-227)
- [runtime_build/CONTRACT27b.md](#doc-228)
- [runtime_build/GUNICORN26-SUPERSESSION.md](#doc-229)
- [runtime_build/README.md](#doc-230)
- [runtime_executor27c/SPEC.md](#doc-231)
- [updater_runtime/COMTRADE-PUBLICATION.md](#doc-232)
- [updater_runtime/GST-GROUNDING.md](#doc-233)
- [updater_runtime/MONITOR-HEALTH.md](#doc-234)
- [updater_runtime/REFRESH-BUNDLE.md](#doc-235)
- [updater_runtime/SANCTIONS-POLICY.md](#doc-236)
- [updater_runtime/TABLE-EDIT.md](#doc-237)
- [workflow_executor29b/SPEC.md](#doc-238)
- [workflow_package29/SPEC.md](#doc-239)


<a id="doc-000"></a>

### Reference: `REVIEW.md`

<!-- ORIGINAL-DOC {"bytes":1827,"path":"REVIEW.md","sha256":"ad2378a299e43b25eff3d0b1607e882613d6a5fc832503dc887ab65bd7384a46"} -->
# Current review boundary
Copyright (c) 2026 Push.

See [integration/FEATURE_STATUS.md](integration/FEATURE_STATUS.md) for current
works/blocked/missing/dropped scope. Earlier baseline-only status prose is
superseded, not a claim that every preserved feature now works in one app.

Original preservation: pinned source/config/template/script files in
preservation-manifest.json, namespace-only Python source changes and specific
classifier/dedupe/extraction hash checks. Original limitations remain visible.
Use current tests/test_preservation.py rather than obsolete baseline test counts.

Additive private routes now include Finder/news context, country signals,
weekly manual PDF, reference map and manual watched-country views. Preview
password access is optional single-worker configuration, not multi-user
accounts. All current readers/features retain explicit caps and supplied-data
limits. No live database/service/collector/mail/deploy proof follows.

Geo-only launcher is explicit default off. Its selected destination is
geo_intel/articles; no old BRICS newsbot/migration is needed in that composition.
Legacy isolated composition remains available, not silently replaced. Actual
mapping/credentials/source state and read factory must be reviewed at activation.

Before cutover: verify current service/config, exact storage identity/schema/
indexes and read authority, trusted proxy and host controls, worker/concurrency/
write deadlines, scheduler ownership and rollback. Separate explicit approvals
are required for live cutover, stopping old collectors, Render settings, mail,
live DB writes, polling and Telegram/WhatsApp delivery. Do not install a second
collector or run old setupTriggers. Destructive retention needs verified backup
policy and its own approval. No such effects were performed by this review.

<!-- END-ORIGINAL-DOC -->


<a id="doc-001"></a>

### Reference: `SECURITY.md`

<!-- ORIGINAL-DOC {"bytes":619,"path":"SECURITY.md","sha256":"ba9643955bfcb04524a6fe5a8c2929b54abc2e67bb3480ce806e742d506e4dc9"} -->
# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

Use this section to tell people how to report a vulnerability.

Tell them where to go, how often they can expect to get an update on a
reported vulnerability, what to expect if the vulnerability is accepted or
declined, etc.

<!-- END-ORIGINAL-DOC -->


<a id="doc-002"></a>

### Reference: `collector108_prep/ASSESSMENT.md`

<!-- ORIGINAL-DOC {"bytes":2969,"path":"collector108_prep/ASSESSMENT.md","sha256":"c988139e64018bb23bd492f6e10f56b85dfd7702fd38400f9da059d38fc5035e"} -->
# Collector108 preparation, not runtime or cutover

Confirmed current merged-main web/Code.gs/rss bytes against live native reads.
Original deployed Geo code/settings/Apps Script project/actual triggers remain
unverified; preserved source cannot prove current external deployment state.

Preserved runtime findings:
- web.py imports DB/client/init on startup; secret absent means _authorized True.
- GET or POST /collect starts daemon background thread, returns202 immediately.
- /collect-status is RAM only, process-local; restart loses running/outcome state.
- collection performs RSS, optional GNews, events; RSS optionally starts another
  daemon Telegram backup thread after Mongo save, reference update follows later.
- failure status includes str(exception), unsafe for secret-bearing diagnostics.
- Apps Script _renderUrl uses global RENDER_BASE_URL and query trigger key;
  runCollect ignores non-success HTTP (muteHttpExceptions=true, no status check).
- setupTriggers deletes every trigger then reinstalls collection, keepalive,
  digest, critical, weekly and destructive cleanup. Not collection-only cutover.
- standalone scheduler.py also sends SMTP, optional alerts/WhatsApp/Telegram;
  not the selected Apps Script sending architecture and not a safe launcher.

Gap inventory, not fixed by copying source:
1. Live fetching network allowlist, SSRF/DNS/redirect/TLS/body/encoding/time budget.
2. RSS XML parsing reviewed only fixed synthetic corpus, not arbitrary safe input.
3. Fulltext extractor/parser current dependency/source semantics and limits.
4. GNews wrappers, source catalog/extra feeds and actual enabled categories.
5. Durable cross-process single cycle/lease/status/recovery, no blind retry after
   ambiguous write. User/worker1 does not by itself serialize old/new services.
6. Exact uniqueURL index verification; oldest/newest source/date/scoring parity.
7. Telegram backup ordering/references and retention preconditions. Collector
   migration without backup is narrower than original full collection behavior.
8. Events writes remain separate (new public site events reads currently off).
9. Mail/receipt marking/claims remain separate, old service still needed.
10. Source deployment/current Apps Script trigger/settings inventory; topology
    lifetime/cost and write/secret permission are unresolved.

First code increment should be an inert job envelope/status/lease contract and
collection-only Apps Script adapter, with supplied synthetic jobs and fake stores
only. No live fetch/parser/write backend promised complete yet. Do not import
legacy web/scheduler/collectors to run their side-effect globals during prep.

Cutover invariant: only one collection schedule writes. Owner reviews exact
source list/flags, credential role/index/topology, manual test and rollback;
then separately authorizes pausing old collection trigger and enabling new one.
Service shutdown waits for mail/events/Telegram/cleanup owners to be replaced.

<!-- END-ORIGINAL-DOC -->


<a id="doc-003"></a>

### Reference: `collector108_prep/DEPENDENCY-SECURITY-PLAN.md`

<!-- ORIGINAL-DOC {"bytes":2733,"path":"collector108_prep/DEPENDENCY-SECURITY-PLAN.md","sha256":"1d808710cc26057d06bdd895fe7d7a308da0d3aabb8ccc386fefa9ae452b47c1"} -->
# Collector dependencies/security preparation

No package downloaded/installed, source fetched beyond authorized repository
reads, parser run on external RSS, or live collector executed by this plan.

Separate worker lock: do NOT expand public requirements-staging implicitly.
Core: requests, feedparser, python-dateutil, pymongo, dotenv. schedule not needed
if AppsScript/queue/Rendercron is sole scheduler; optional trafilatura/GNews and
transitive XML/network packages separately reviewed only if original enabled.
Original floating >= requirements are source description, not chosen safe pins.
Preserved old locks include vulnerable versions and are NOT security-clean.

For chosen profile: resolve supported Python/OS + exact source-compatible fixed
versions from upstream advisories, verify official wheel hashes/METADATA/tags/
active dependencies, complete hashlock and fresh offline install/pipcheck. Do
not use absent optional dependency as silent feature drop. Snapshot source and
SDK physical pins; compare original classifier/date/dedupe/schema outputs over
representative bounded fixtures. Timezone/date backend regression included.

Network/parser boundary: new arbitrary XML ingestion cannot reuse fixed corpus
runner as if general sandbox. Need compressed/decoded-size budgets, CPU/AS/wall/
output cap, kill-group/reap, redirect/DNS/privateIP/HTTPS policy, deterministic
source allowlist. Fulltext/GNews add separate attack/sourcepolicy surfaces.
Validate rows before writer; no nested stringify, fixed schema/aggregate limits.
No email/Telegram/server-side templating credentials inherited by parser child.

Job/token boundary: require auth before network/DB, header secret never query,
strict bounded request, no caller source/collection/URI/module/recipient. Nonce
replay idempotent, durable ownership/fence/lease/status in reviewed jobs store.
In-memory FixtureLedger is ONLY a contract model, cannot deploy as durability.
Failure after write start is uncertain, not retry-safe. Index and driver errors
must prove exact URLduplicate; code11000 alone insufficient. No automatic
index creation/deletion/cleanup or sent marking. Source exception messages,
stacktraces/URLs/credentials never in publicjob responses or logs.

Non-live migration decision list:
1. Topology: AppsScript+paidqueueworker / Rendercron / restartablefreeweb.
2. Full original behavior scope: RSS/GNews/fulltext/events/Telegrambackup flags.
3. Writer/read separation, exact article/index and durable jobs-store role.
4. New collection-only ScriptProperty/adapter/cadence; mailbase unchanged.
5. Actual triggers/services inventory BEFORE cutover and precise rollback.
6. Manuallivefetch/write scope then switch/oldstop separate ownerapprovals.

<!-- END-ORIGINAL-DOC -->


<a id="doc-004"></a>

### Reference: `collector108_prep/FREE-TOPOLOGY.md`

<!-- ORIGINAL-DOC {"bytes":2046,"path":"collector108_prep/FREE-TOPOLOGY.md","sha256":"5493fb0d08ba64c7c098e8a4c3e1d90cedb67f1cb4ca2bead95a2085a72c11e7"} -->
# Selected design: AppsScript + free Render web, inactive

Original keepAlive source confirmed live main unchanged October7,2026:
f23159b30f263e3a34cae29879900d73b23f6cf64fc6958f12712b7df484026a.
It hits OLD RENDER_BASE_URL/health with old querysecret. New additive ping must
hit separate collectionbase; old mail/base/triggers remain unchanged. No global
setupTriggers invocation (deletes ALL triggers). Active10min successfulHTTP
preventsordinary15minidle, but not restart/crash/monthlyworkspace750h quota.
Two continuouslyawake freeweb services exceed750h/month sharedworkspace;
check actualservices/remainingquota before asserting viable monthlycapacity.

Freeweb job lifecycle should use request-driven bounded work slices. Acceptance
HTTP202 alone doesnotspawn durable work. Add authenticated drive/status poll by
AppsScript; persist onephase at a time using majorityjournaled Mongo CAS ledger.
No RAMdaemon as sourceoftruth. Transport/budgets and fixed originalpreparation
mustfinish before adapter executes anything live. Jobstorecollection/role is a
newpermission gate, not smuggledinto existing geo_readonly client.

Current CAS ledger is injected and creates no client/index. Profile document
serializes jobs and fencing increments. Replay/history max64: failsclosed when
full until separatelyreviewed archival mechanism. Exact fingerprint required.
Expired lease NEVERstolen: crashes beforewrites block until safeprocessdeath
and checkpoint reconciliation. Uncertainwrite profile latches. Real article
writes are not fence-aware, so leaseexpiry cannotautomatically permitoverlap.
Ledger majority+journal validation notimplemented yet. Do not call complete.

Remaining recovery design: durable checkpoints; processidentity/readback;
prewrite candidates safe restart; write-start articleURL+runreceiptreadback;
transaction or no-takeover serialization; reconcile unknownbeforeunlock.
Cannot promise every missed cycle iscovered automatically while preserving
bounded lookback/unknownpartialwrites. Separateexplicitlivecutover required.

<!-- END-ORIGINAL-DOC -->


<a id="doc-005"></a>

### Reference: `collector108_prep/JOB-CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":2814,"path":"collector108_prep/JOB-CONTRACT.md","sha256":"5a8687804c7bb9e3fbbfd29bf0d0ed932ac813a970c59b5117b4b01b47b0ea3a"} -->
# Proposed collector job contract, inactive preparation

No route/runtime/trigger installation. To review before implementation:

Request: authenticated POST with fixed collection profile/version, opaque
request nonce, created-at UTC. No caller-provided sourceURL/collection/URI/
code/module/classifier/send recipient. Header token secret never URL/log.
Canonical serviceorigin fixed; body<=4096 bytes, nonce grammar/length strict.
Reject omitted token, malformed body or flags before client/network creation.
Replay nonce returns prior job identity/status, not another collection cycle.

Durable store: exact reviewed jobs collection, unique nonce/profile key, atomic
claim with fencing token/lease/expiry, one active profile at a time across
workers/services. Time expiry alone must not enable double writes if old job is
still executing: separate renewal/stop/reconciliation. Single worker lock is
not substitute for durable ownership. Restart outcome marked interrupted or
unknown, never success. Job source/settings fingerprint immutable.

Statuses: accepted, running, fetch_complete, prepare_complete, write_started,
completed, refused, failed_before_write, uncertain_after_write, interrupted.
Count bounds captured each phase, no article content/URI/token/exception text in
public logs. Status endpoint authenticated; aggregate source/job counts only.
Write-start phase may not be blindly retried. Bulk duplicateURL receipt only
when exact unique index and driver keys prove it. Unique index is external
current-state verification, not fabricated test assumption.

Source contract: fixed reviewed original RSS list + explicit extra-feed catalog;
future GNews/events/Telegram flags scope recorded. Network client rejects
unsafe/local DNS/redirects; strict TLS, bounded decoded/compressed bytes,
wall/read/connect budgets, max concurrent tasks/output. XML parser needs actual
arbitrary-input resource boundary, not only reviewed fixed synthetic corpus.
Fulltext same bounded allowlisted networking/parsing. Preserve original
classification/date/score/country/dedupe/document semantics with differential
fixtures. Source-policy and remaining transport gaps are separate blockers.

Scheduling: AppsScript collection-only wrapper to separate collectorbaseURL,
header-token property, strict HTTPstatus+job receipt validation, no new trigger
installer until actual schedule ownership confirmed. Original mail/checkCritical/
weekly/cleanup trigger functions retained until each separately migrated.

Deployment: owner-approved Render job/worker/topology after current pricing and
lifetime constraints researched. No ephemeral daemon thread assumed durable.
Only one scheduled owner after explicitly-approved cutover. Rollback disables
newjob triggers and restores oldcollection trigger; uncertainwrites reconciled.

<!-- END-ORIGINAL-DOC -->


<a id="doc-006"></a>

### Reference: `collector108_prep/README.md`

<!-- ORIGINAL-DOC {"bytes":1241,"path":"collector108_prep/README.md","sha256":"e5dbd9852a941e361212e357b212d1793ff788b5ddd4d7861b00249414dca24f"} -->
# Collector108: partial INACTIVE preparation, not a deployed collector

Separate scratch/review contracts. No liveentrypoint imports this directory;
no trigger installer/worker/fetch/parser/actualDBclient/mail/backup/index included.
Original runtime, Code.gs and public107 remain unchanged. FixtureLedger is only
in-memory specification. DurableLedger is injectedMongoCAS shape; majority/
journal concerns, actualstore/role/mapping not verified or wired. No automatic
expiry takeovers. Unknownwrites latchprofile. Historymax64 stopsnewjobs.

Authenticatedsubmission/status factory tests use CASCollection in memory.
Health reportscollectionfalse. AcceptedHTTP202 DOESNOTstartorfinishcollection.
AppsScript file is ADDITIVE, NOTinstalled, preservesoldbasefunctions/triggers;
headersecret fromScriptProperties, separatecollectionbase, noncepersisted.
Pendingnonce nevercleared beforefutureterminalstatus/recoveryimplementation.

Localtests: Python unittest test_job_contract test_durable; node test_apps_script.js.
No deploymentinstruction/activation included. Save is backupofinertprep ONLY.
Read FREE-TOPOLOGY.md/RECOVERY-GATES.md for outstandinggates. Fullsources/network/
checkpoint/drive/transactionorreconciliation stages areunfinished.

<!-- END-ORIGINAL-DOC -->


<a id="doc-007"></a>

### Reference: `collector108_prep/RECOVERY-GATES.md`

<!-- ORIGINAL-DOC {"bytes":1616,"path":"collector108_prep/RECOVERY-GATES.md","sha256":"d6d9747534837c053ea519f83beec35df18a090fd9ffd05b8f9c93f17958608f"} -->
# Before implementing autonomous recovery or live execution

A durable ledger is necessary but NOT sufficient. A fence value stored in
Mongo cannot prevent an old process inserting articles after losing its lease.
No write-capable automatic reclaimer will be implemented by pretending a
find_one lease check is atomic with a separate insert_many.

Safe possibilities for review:
- Single Mongo transaction includes ledger claim/version assertion and exact
  article inserts; transaction timeout/row/size bound, driver-supported replica
  topology. Must validate actual capability and role before relying on it.
- Keep expired active profile latched; prove old process stopped/reap or owner
  pauses old/new entrypoints, reconcile per-run expectedURL/hash receipts,
  then separately authorize unlock. Lower availability but no doublewriter.

Request-driven recovery must use immutable bounded candidate checkpoint before
write_started, run-specific outcome record, durable terminal acknowledgement,
source/fingerprint drift refusal. Any article readback requires reviewed role;
current readOnly/public latest100 is NOT a write-reconciliation oracle.
CheckpointDB role/mapping retention/disclosure is not granted by freechoice.

Upcoming bounded composition can be tested against fixed supplied entries with
original post-fetch semantics and injected in-memory outcomes. It must carry
explicit no-network/no-livewrite labels. Arbitrary external XML/fulltext needs
resource-isolated parsers and verified packages; no import legacycollect() as
shortcut (creates stores/Telegram daemon/network environment sideeffects).

<!-- END-ORIGINAL-DOC -->


<a id="doc-008"></a>

### Reference: `collector108_prep/SOURCES.md`

<!-- ORIGINAL-DOC {"bytes":619,"path":"collector108_prep/SOURCES.md","sha256":"a03a90cfe7a820ae876ecec7afc099259a93122547030f55246b6b606bd50c73"} -->
# Sources inspected October7,2026
https://render.com/docs/background-workers - Render official, queue-polling no inboundURL model.
https://render.com/docs/cronjobs - Render official, single-active run, manual cancels active,12hmax,min$1/month, no disk.
https://render.com/docs/free - Render official, freeweb15minidle/ephemeral/restartanytime/750workspacehours, nofreeworker/cron.
https://render.com/pricing - Render official current pricing, smalleststandardcompute$7/month, cron billedactivecompute/min$1.
https://github.com/push2006/geonews - authorized livepublicmain native reads;12criticalsourcepaths reconciled.

<!-- END-ORIGINAL-DOC -->


<a id="doc-009"></a>

### Reference: `collector109_prep/ENGINE-STAGE.md`

<!-- ORIGINAL-DOC {"bytes":3050,"path":"collector109_prep/ENGINE-STAGE.md","sha256":"fea006f35f89fe53c1aba7f661109ac2a6d121fa7c2189be6cb9fb736f19e5a9"} -->
# Collector109 stage1 revision 2: INACTIVE, offline only

No live entrypoint import, network call, Mongo client, trigger install, repo save,
or cutover. Uses saved collector108 and hash-pinned original source contracts.

Changes responding to NEEDS-CHANGES:
- HIGH1: existing write_started is never replayed. Only the invocation winning
  the prepare_complete -> write_started CAS may call the writer. A second
  heartbeat checks current ownership/lease just before that call. Crash or
  uncertainty requires reconciliation; there is no automatic lease steal.
- HIGH2 (receipt): exact writer schema/state/type/bounds/accounting validation.
  Missing, malformed, unknown or explicit uncertain receipt latches uncertainty.
  If lease/store prevents terminal update, write_started stays locked and the
  result says reconciliation_required. No guessed zero counts or completion.
- HIGH3 (encoding): tagged typed canonical encoding separates literal containers
  from datetime/scalars; rejects nonfinite floats and non-string dictionary keys.
  Existing equal-hash put does not replace a checkpoint row.
- HIGH4: driver requires an immutable FULL run checkpoint: candidates, active
  categories, threshold, key and fence. Every resume must match it before prep.
  Missing/mismatched checkpoint refuses. Uses bound copies, not caller values.
- LOW: no author /tmp import paths. Root PYTHONPATH is a test-runner input only.
  Package imports are validated from a separately copied root. Preparation
  exceptions fail_before_write when ledger authority is valid; if that update
  cannot be verified, refusal instructs checking ledger status. No article write.

32 focused offline tests pass. Safety tests cover wrong/expired write_started,
two resumed drivers (zero new writer calls), crash immediately after ticket,
concurrent prepare drivers (one total writer call), clock expiry before writer,
malformed receipts, typed collisions, run settings replacement and prep failure.
BoundedFetcher is an injected transport contract, not a live RSS implementation;
its six initial URL-host errors are fixed. No content-type/parser claim is made.

Important limits:
- FixtureCheckpoints is in-memory. Process-restart recovery is NOT implemented.
- Fencing the job ledger cannot fence an external article database operation.
  Production remains OFF until transaction/reconciled article writes and durable
  checkpoint/ledger stores with majority+journal are independently verified.
- RSS parser sandbox, real network streaming/decompression budget, DNS/IP policy,
  fulltext/GNews/Telegram backup flags and actual deployed triggers are pending.
- Endpoint/Apps Script drive wiring is next, outside this stage1 review bundle.
- Live switch, DB/mail changes and stopping old collectors need explicit owner OK.

Final package runner: python -m unittest discover -s collector109_prep -t . -p 'test_*.py' -v
Independent review: SAFE for inactive fixture/preparation scope. Candidate count
1000 does not establish aggregate byte/depth/time bounds. Production stays OFF.

<!-- END-ORIGINAL-DOC -->


<a id="doc-010"></a>

### Reference: `collector109_prep/wiring/WIRING-STAGE.md`

<!-- ORIGINAL-DOC {"bytes":1651,"path":"collector109_prep/wiring/WIRING-STAGE.md","sha256":"8f480d4c8770d26bca6c743ded1ab46b181007b723d7c1d7853df9a47fadb96f"} -->
# Collector109 wiring preparation: INACTIVE fixture only

Stage1 revision2 and this wiring increment have SAFE verdicts for inactive fixture/preparation scope only. No production approval.
Not mounted in production. No repo save, network calls, triggers, live DB/mail
changes or old-service stopping. collection_only.gs is an additive 108 test companion (including the earlier
phase type check), not a replacement for old108 or Code.gs.
The new drive app does not expose 108 submission or health routes. The
keepAlive/submission-to-drive chain is not mounted as one complete service.

- FixtureService registry accepts full run inputs only through offline explicit
  server setup. HTTP caller cannot submit candidates/categories/fence/writer.
- Auth precedes parse/ledger access. POST /internal/collector109/jobs/<key>/drive
  accepts only an empty JSON object and invokes hold-only drive (no writer/store).
- GET status returns sanitized ledger job/phase/counts.
- Apps Script polling reads preserved COLLECTION_PENDING108; derives key from
  nonce; validates status binding/counts; skips terminal/write_started/uncertain
  jobs; drives only before write and validates hold + authoritative status.
- Never clears pending or generates a new nonce. No background threads and no
  automatic recovery. The process-local input registry blocks after restart.

Six Python endpoint fixture tests + Node script assertions pass.
This is wiring preparation, NOT a working production collector. The real input
fetch/parser/checkpoint registry and production article writes remain OFF.
The production integration must not reuse this registry as durable recovery.

<!-- END-ORIGINAL-DOC -->


<a id="doc-011"></a>

### Reference: `collector110_prep/STAGE110.md`

<!-- ORIGINAL-DOC {"bytes":2335,"path":"collector110_prep/STAGE110.md","sha256":"64d589ce7947e2679f3a9e789f75e4d63384feba9623d42376ba1699f682d6db"} -->
# Collector110 input-budget and checkpoint-store preparation

INACTIVE scratch only, unreviewed. No production/import/client/index/TTL/env
wiring, repo save, database access, trigger, mail or cutover effect.

input_budget.capture bounds input BEFORE expensive copying/hashing/preparation:
2MiB conservative UTF-8 content, 20000 nodes, depth8, 100 dict keys, 1000 list
items, bounded strings/signed-int64 integers, exact builtins and reviewed timezone dates.
Cycles/nonfinite/scalar subclasses/custom objects fail. Shared subtrees count
again. This is not a measured CPU deadline or BSON byte bound; it is not yet
wired into saved109, so does not improve109's current input guarantees.

DurableCheckpoints accepts an injected collection only, validates configured
write majority+journal+wtimeout and read majority concerns, creates no client or
index, and uses _id immutability with setOnInsert + readback/hash verification.
Typed JSON/BSON-compatible projection retains dates without driver normalization.
Missing/malformed/unacknowledged/mismatched writes/readbacks refuse. All tests
use an in-memory collection double; NO real Mongo/server validation occurred.
Concerns on a Python collection do not prove server capability or owner authority.

21 focused offline tests PASS, including second-adapter retention, immutable
mismatch, corruption, concern validation, uncertain receipt, readback failure,
parallel different inputs (one winner), encoded-depth/cycle/resource rejection.
Not attached to109 driver (that explicitly accepts FixtureCheckpoints only).
No claim of production recovery, live storage, lease takeover or article fencing.
Next increment after review must separately wire this boundary, validate actual
role/server topology and use resource-isolated network/parser work. Article
write_started remains latched pending reconciliation; no retry/unlock added.

Revision2: integer capture uses signed-int64 range. Wire input integers are
canonical decimal strings with strict decoding, avoiding PyMongo Int64 subclass
changes on BSON roundtrip. Stored fence is also decimal text for stable identity.
Real BSON codec roundtrips at both signed-int64 boundaries PASS; one-beyond
values refuse before collection access; malformed decimal encodings refuse.
These are local codec tests, not a live Mongo write/capability test.

<!-- END-ORIGINAL-DOC -->


<a id="doc-012"></a>

### Reference: `collector111_prep/STAGE111.md`

<!-- ORIGINAL-DOC {"bytes":1532,"path":"collector111_prep/STAGE111.md","sha256":"8e51e80592128b69b55a5f8908a63e4519962e75e8d2da069338174bc752a911"} -->
# Collector111 durable-driver integration preparation

INACTIVE scratch; no saved109/110 edits, no live mount/client/index/TTL/network,
DB/mail write, trigger or cutover. New drive_durable composes reviewed109 phase
semantics with reviewed110 capture and injected DurableCheckpoints.

- Full run inputs captured before deepcopy/hash/preparation and before ledger
  heartbeat. Status read remains before capture; rejected budget makes no ledger
  mutation. Driver uses the captured copies throughout, exact adapters only.
- Accepted job writes immutable checkpoint before running. Resume requires full
  matching checkpoint and refuses read/write acknowledgement/integrity failures.
- Local real BSON codec backed collection double retains checkpoints across
  adapter re-instantiation. This is not a real server or process restart proof.
- Existing write_started still never retries, no uncertainty unlock, no lease
  takeover. CAS/heartbeat still cannot atomically fence external article writes.
- All26 earlier109 drive/chain/safety tests plus6 durable integration tests PASS
  (32 total); full old regression and package layout not run yet for this stage.

Configured majority+journal/read concerns do not verify server capability,
role or authority. No production deployment/recovery claim. No source fetch,
stream/decompression/DNS/parser sandbox added. These remain outstanding along
with production service mounting, source flags, run reconciliation and actual
Apps Script trigger/capacity checks. Live production stays OFF.

<!-- END-ORIGINAL-DOC -->


<a id="doc-013"></a>

### Reference: `collector112_prep/STAGE112.md`

<!-- ORIGINAL-DOC {"bytes":1808,"path":"collector112_prep/STAGE112.md","sha256":"7c30bea2a768260bebcabe1e0bd137bf4e5e52f5fa6acdc88384c56396f27551"} -->
# Collector112 supplied-byte parser preparation

SAFE independent review for inactive supplied-byte parser only. Production OFF.
Real feedparser6.0.11 over bounded supplied UTF-8 RSS/Atom inside bubblewrap.
Nine tests PASS with default Python and project3.10.12 venv. Vendored pinned
feedparser sources/sgmllib included, child PYTHONPATH=/app/vendor. Local reviewer
also observed distinct network/pid/mount/user namespaces, only loopback, child
PID2, cleared six-variable env, empty home/tmp/etc; resource limits CPU3s,
AS256MiB, file size1MiB, descriptors64. Fault output>1MiB and sleep20s killed/reaped;
NUL/UTF32/1001 entries refused. No unisolated fallback. Unavailable bwrap currently
propagates OSError, not ParserRefused (still no fallback).

These are LOCAL kernel checks, not Render capability. Read-only usr/interpreter/
app mounts expose broad readable code and are NOT confidential-file/arbitrary-code
containment. Pins cover Python source files only; interpreter/stdlib/site startup
and compiled-cache control remain final deployment gates. Vendored tree excludes
compiled caches at save; runtime controls are not established. Hostile corpus and
fault coverage must expand before live ingestion. Mount only intended artifacts
in final deployment; current installation-derived interpreter mount is a prep.

No client/index/TTL, live fetch, article write, mail, trigger installation, source
activation, production service mounting or cutover. Original feed date/selection
composition, network streaming/decompression/DNS, durable full-service integration,
source flags and article reconciliation remain pending. Original files unchanged.

Package test invocation from repo root: python -m unittest discover -s
collector112_prep -t . -p 'test_*.py' -v. Local default python3 and project venv pass.

<!-- END-ORIGINAL-DOC -->


<a id="doc-014"></a>

### Reference: `collector113_prep/STAGE113.md`

<!-- ORIGINAL-DOC {"bytes":2113,"path":"collector113_prep/STAGE113.md","sha256":"1c2b75348f29b69e3162db7c7c89c4344b28c06699444e8976eb13020297bd57"} -->
# Collector113 transport policy and feed composition preparation

Inactive supplied-response tests only. Production OFF. Public repository backup,
not the finished app. No real HTTP/DNS/TLS, no DB/mail/trigger/runtime changes.

New policy checks installed exact feed URLs, public-unicast supplied DNS answers,
supplied peer membership, explicit deprecated192.88.99.0/24 deny, HTTPS443, no fragments/redirects. Keeps hostname for
future TLS SNI/certificate checking. Supplied raw wire chunks capped at 64KiB per
chunk, 4096 chunks, 1MiB compressed and 1MiB decoded. Supports identity, gzip and
zlib-wrapped deflate only; rejects excess/truncated/concatenated compressed data,
length mismatches, duplicate headers and ambiguous transfer framing. Deadlines
checked before/after each supplied chunk. Hostile gzip expands only to remaining
output budget plus one byte.

Feeds: hash-pinned original DEFAULT_FEEDS AST literal (25 sources); no original
module imports. A supplied response passes through these policy checks, then the
reviewed112 OS-isolated feedparser, then the original hash-pinned feed-selection
AST composition. Title/link, summary cleanup, cutoff, fixed-date fallback and
source/credibility behavior tested. Bozo and parser projection counts retained;
no claim that a malformed parsed source is healthy. Original112 projection is
100 entries, MAX_ITEMS selection bounded to100; full original larger settings
remain a parity gate. Originals and prior preparations unchanged.

17 offline tests pass in the project Python3.10 environment. Supplied address
checks are not live DNS resolution, connector pinning, TLS verification, or peer
inspection. This stage deliberately has no network connector. It cannot interrupt
a blocked resolver or socket reader. Real raw streaming, HTTP framing, DNS/connect/
read deadlines, connector address pinning, actual peer/TLS checks, gzip/encoding
parity, broad hostile corpus and Render bubblewrap/runtime mounts remain gates.
No confidential-file containment claim. No live source health proof.

Invocation: python -m unittest discover -s collector113_prep -t . -v

<!-- END-ORIGINAL-DOC -->


<a id="doc-015"></a>

### Reference: `collector114_prep/STAGE114.md`

<!-- ORIGINAL-DOC {"bytes":2190,"path":"collector114_prep/STAGE114.md","sha256":"76319427498bc6fb69d4e90c0083b5b804da09fb5c06100b9193d4f8923b1563"} -->
# Collector114 fixed-code HTTPS connector candidate

INACTIVE. No app imports/mount, live fetch test, DB/mail/trigger changes. Not
live-ready or source-health verified. Installed feed allowlist only. Original UA.

Trusted fixed-code worker owns bounded DNS set -> all-answer public-unicast
policy -> pinned socket -> actual peer check -> verified hostname/SNI TLS ->
stdlib HTTP framing -> capped raw compressed reads -> bounded113 decode. No
proxy/env URL/redirect. Exact chunked without CL accepted; duplicates/TE+CL/
unsupported TE refused. UTF8 parser remains separately isolated112, not invoked
by this fetch worker. Requests compressed1MiB / decoded1MiB budget. HTTP header
framing is stdlib bounded at line/count level plus32/2KiB policy after begin.
Chunk extensions/trailers are bounded by worker CPU/memory and parent wall cap,
not claimed to have an explicit per-trailer budget. Need corpus/fault expansion.

Supervisor uses cleared environment, -I, separate session, whole timeout<=30s,
input<=128KiB/output<=2MiB, kill process group and reap. Fixed child CPU5s/memory
256MiB/file2MiB/descriptors64. Hash pins worker/connector/policy Python sources.
This is fixed-code resource containment, NOT OS sandboxing or confidential-file
containment. Child has network and read access; only trusted reviewed code runs.
Interpreter/stdlib/cert-store/site startup/compiled cache pins and deployment
paths remain gates. Parent worker protocol checks sizes/keys/address/hostname.
No request-supplied child commands, paths, socket/TLS factories or environments.

Local tests use mock DNS/socket/TLS and real stdlib HTTPResponse with supplied
BytesIO framing only. Supervisor faults run real subprocesses replacing the
fixed command in tests: hung resolver analogue, huge output, stderr and malformed
protocol. Local test results prove these offline mechanics, not live DNS/TLS or
Render behavior. Real live source health and Render process/isolation support
remain final deployment checks. Original gzip/encoding/header behavior parity
still needs source-specific verification, broader corpus and100-entry cap fix.

No durable DB writer/service/Apps Script trigger or production activation.

<!-- END-ORIGINAL-DOC -->


<a id="doc-016"></a>

### Reference: `collector114_prep/TRANSPORT-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":2160,"path":"collector114_prep/TRANSPORT-DESIGN.md","sha256":"0df5681bcb1a1bf628d84c656ba072b56e80b44c345393d926b999c63fd1a3d1"} -->
# Next transport build (not installed, not saved)

Real HTTPS connector remains required. Build after113 review, preserving original
source feeds and source User-Agent. No live sources are called in offline tests.

1. Installation-owned hash-pinned source catalog, HTTPS443, exact selected URL.
2. A fixed-code child process owns DNS, socket, TLS and raw response streaming.
   Parent hard wall deadline kills/reaps child on blocked DNS/connect/read.
   Child environment cleared; memory/CPU/descriptors/output individually capped.
   Fetch child has network but never imports XML/full-text parsers or DB/mail.
3. Resolve bounded getaddrinfo set; reject the entire set if any nonpublic,
   translated, scoped, multicast, reserved or private address. Pin one validated
   address into socket.connect, check actual peer, retain original hostname as
   TLS SNI and validate chain + hostname via fixed approved trust store.
4. No proxies, no redirects, no retries within a single feed attempt. Standard
   library HTTP parser owns wire framing; reject duplicate CL, ambiguous TE/CL,
   unsupported TE, declared body over1MiB, and redirects. Read raw body in <=64KiB
   chunks, max1MiB, deadline updated per read; no response.content buffering.
5. Feed113 bounded decoder consumes those raw chunks. Both compressed and decoded
   budgets apply. Feed112 XML child stays networkless, separate from fetch child.
6. Structured bounded child output with URL + SHA256 + size, not raw exception
   strings or environment. Parent verifies all protocol values before parsing.
7. Offline fault tests: fake resolver, peer rebinding, TLS failure/SNI, redirects,
   CL/TE and chunked framing, read delays/never-return DNS, gzip bombs, output
   overflow, descriptor cleanup and parent kill/reap. No live effect tests until
   review and final cutover prep permission checks.

Deployment blockers remain independent of local success: Render process/resource
limits and bubblewrap support, interpreter/stdlib/trust-store pins, actual Mongo
roles/indexes/TTL, durable write reconciliation, service endpoint auth/idempotence,
Apps Script scheduler ownership and free-host capacity.

<!-- END-ORIGINAL-DOC -->


<a id="doc-017"></a>

### Reference: `collector115_prep/PROFILE-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1556,"path":"collector115_prep/PROFILE-DESIGN.md","sha256":"735e24136b4d4ccdc0b54d951ce75bb7a79d27be13d2ecf82271d9d37bc915bb"} -->
# Collector115 next composition outline, scratch only

Bind approved installation profile (hash-pinned original25 feeds/config defaults)
to114 fixed network worker,112 separate networkless parser, original selection
and111 durable checkpoint driver. Fetch and selection occur before write ticket.
Persist immutable candidates before any article write. No request URL/fence/source
flags/candidates/writer accepted. Source failure is explicit partial/error status,
not fictitious all-feeds health. Per-feed output/candidate limits and whole-run
budget required; deterministic source order retained. Original classification /
dedupe/categories run before writer. Default MAX_ITEMS_PER_FEED40 is inside100
parser projection, but environment values>100 must be refused as unsupported,
never silently truncated or labelled full parity. Original feed entries[:limit]
semantics remain, not limit on accepted rows.

Optional full text/GNews/Telegram backup require explicit separate adapters;
production flag true without adapter must fail closed at profile boot, not silently
turn feature off. While disabled, flags remain reported as disabled_by_config.
Original defaults: fulltext=false, gnews=false, Telegrambackup=true. Thus ordinary
production default requires a working backup adapter before full-feature cutover;
preparation cannot call itself complete merely because optional flags are off.

Production mount still OFF. Source profile validation is NOT owner permission,
actual Mongo role/index/TTL proof, runtime viability, or scheduler/cutover approval.

<!-- END-ORIGINAL-DOC -->


<a id="doc-018"></a>

### Reference: `collector115_prep/STAGE115.md`

<!-- ORIGINAL-DOC {"bytes":1749,"path":"collector115_prep/STAGE115.md","sha256":"e1be5ed44b6281e541a045c0d2ddcfd03f330bd1e6036146856a099d3f992a2f"} -->
# Collector115 installed profile and supplied catalog composition

INACTIVE. Production OFF. No real fetch call, runtime mount, DB client/write,
mail, Telegram or trigger changes. Fixed-source original config defaults loaded
through hash-pinned AST, never by importing dotenv/client config. Original25 feed
catalog, MAX_ITEMS_PER_FEED40, timeout20, lookback48, all categories, dedupe.85.
Explicit installation override shape only. Unknown/secret/URL overrides refused.
Fulltext/GNews false and Telegrambackup true defaults retained and reported.
Enabled missing adapters are pending gates, never silently turned off.

Bounded supplied body/hash/wire evidence by catalog URL -> isolated112 parser ->
original hash-pinned selection -> aggregate capture -> immutable111 checkpoint
input shape. Original catalog order preserved even if input mapping order differs.
Missing feeds are not_supplied, not healthy/empty success. Bozo, entry/projection
counts and date fallbacks retained.100 projection cap / maxitems bounded<=100;
original default40 supported, larger environment values refused as unsupported,
not silently truncated.4MiB aggregate supplied bodies,1000 candidates and110's
2MiB/nodes/depth capture caps. No actual network fetch integration in this stage.

14 tests cover defaults/flags/refusals, body hash, real isolated parser/original
selection, cutoff/default clock/unknown timezone, firstN vs firstNvalid, order,
then111 durable fixture checkpoint+GeoFixtureStore drive. Last is a fixture write,
not real DB proof. Profile's pending_gates and live_write_ready=False are retained.
Existing adapters have their inherited limits; the full-source failure/cycle,
fulltext/GNews/Telegram, real writer/service and live deployment gates remain.

<!-- END-ORIGINAL-DOC -->


<a id="doc-019"></a>

### Reference: `collector116_prep/NETWORK-COMPOSITION-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":770,"path":"collector116_prep/NETWORK-COMPOSITION-DESIGN.md","sha256":"d3d0a0900fe5a7719e24cec34c00bc0865dbbda87f7ecc5307ea0a8572e7643b"} -->
# Next network/parser composition candidate, inactive

One source per explicit server-owned work slice.114 subprocess HTTPS connector
returns bounded decoded bytes ->112 distinct networkless XML parser -> pinned
original per-feed selection -> captured checkpoint source outcome. No article
writer and no client-supplied source/config/clock. Runtime mount remains OFF.
Network<=20s default + XML<=10s can exceed30s public worker endpoint; combined
hard deadline and host timeout are explicit blockers before service mounting.
Missing enabled fulltext/GNews/Telegrambackup adapters remain full-feature gates.
Fetch/parse/bozo/empty source outcomes must remain distinct, no health fiction.
Strict header availability, EOF identity integrity and wider pins remain114 gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-020"></a>

### Reference: `collector116_prep/STAGE116.md`

<!-- ORIGINAL-DOC {"bytes":1369,"path":"collector116_prep/STAGE116.md","sha256":"222f3e3c54546cf846afe1dd46166f80a750e5c704c4e0a5704f7b5a4aec1fe0"} -->
# Collector116 fixed fetch/parser/original-selection composition

Inactive candidate; production OFF. No app mount, clients, article writer, mail,
Telegram or triggers. Installation-owned profile settings and exact original
catalog URL. Calls fixed114 worker ->112 separate networkless parser -> pinned
original selection ->110 captured candidates. No request-injected stage factories.
Fetch failure and parser refusal are different source outcomes; bozo is unverified,
not healthy. Unsupported URL/hash/count shape fails before downstream processing.
Missing enabled adapters and inherited runtime/write/service gates travel in the
result with live_write_ready=False. No claim a selected source is live-healthy.

Six local tests patch fixed run_fetch to supplied protocol, run actual isolated112
parser, inspect original selection and failure paths. No real fetch called. This
is integration candidate mechanics, not DNS/TLS/source health or Render proof.
Network worker budget20s default + parser10s maximum can exceed30s endpoint timeout;
hard combined request deadline/sliced endpoint execution remains explicit blocker.
Strict-header availability, unframed identity integrity, runtime/transitive pins,
encoding/corpus and source-limit parity inherited114 remain unclosed. No local
success waives them. Optional fulltext/GNews/backup still not wired in this stage.

<!-- END-ORIGINAL-DOC -->


<a id="doc-021"></a>

### Reference: `collector117_prep/CYCLE-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1387,"path":"collector117_prep/CYCLE-DESIGN.md","sha256":"e940ebf21e3f1d192d0107924e4b9a26b80f2fd708da234efc924d71c707a729"} -->
# Next117 offline failure-tolerant catalog cycle

Per-source independent supplied evidence parse/select. Catch parser/refusal only
at the source boundary. Record refused vs missing vs bozo vs selected_empty;
continue other catalog sources. Malformed whole input/config/clock fails before
cycle. Aggregate raw4MiB, candidate1000,110 capture2MiB/nodes/depth cap remains a
whole-run refusal, not catch-and-continue that silently exceeds limits. Failed
source entries contribute no candidates, diagnostics coarse only. Source-derived
errors do not become command/instruction authority. No article writer.

Default25-feed original order and firstN selection preserved. Unknown source URLs
refused before parsing. EXTRA_RSS_FEEDS currently unsupported must be named in
pending_gates; later support installation-owned reviewed exact URLs. Optional
fulltext/GNews/Telegram backup gates remain. Complete source_count does not imply
healthy. Every result production/live_write_ready False, no live effects.

Then process distinct worker_integrity failure codes before network116 per-source
loop: source pin drift/missing files cannot look like ordinary DNS/server outage.
Original114 API protocol/errors are reviewed bytes; add new adapter/review rather
than casually rewriting saved code. Worker build immutability, stdlib/trust-store
pins and deployment validation still separate runtime gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-022"></a>

### Reference: `collector117_prep/STAGE117.md`

<!-- ORIGINAL-DOC {"bytes":1659,"path":"collector117_prep/STAGE117.md","sha256":"1511183970de78945ccba2588c62b3e8c08470722613d940b9aef0b1fb32bddb"} -->
# Collector117 failure-tolerant supplied catalog cycle

Inactive. Production OFF. No real HTTP/client/article writes/mail/trigger effects.
Pinned installation-source preflight and isolation-binary presence check precede
parsing. Missing files/source drift or launch OSError are loud whole-run failures,
not claimed as a bad feed. Remaining ParserRefused is source_or_parser_refused:
parser112 does not yet distinguish data errors from all sandbox/protocol failures,
so this stage explicitly does NOT call it just a source outage. Runtime-refusal
classification remains a live gate. Preflight is hash-before-use, not filesystem
locking/TOCTOU proof or complete interpreter/stdlib/startup/cache containment.

All supplied input hashes/shapes and4MiB aggregate size checked before any parser.
Each supplied source uses115 original selection/catalog order. ParserRefused
records refusal and continues next source; bozo is separately unverified. Missing
source not_supplied. Aggregate candidate1000/capture2MiB budget is whole-run
refusal, not catch-and-continue or silent truncation. Original source/config drift
remains loud. EXTRA_RSS_FEEDS omission is now explicitly pending, never implied
supported. Production/network/writes/delivery/healthy_verified all False.

10 local tests: malformed XML source continued while next source selected,
preflight aggregate/hash, missing sources, dependency drift, missing binary,
launch OSError, bozo and omission gate. Original files/earlier candidates unchanged.
Real network cycle/checkpoint/service, flags/adapters, runtime, pins/locking,
classification, encoding/corpus/cap and deployment/reconciliation remain gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-023"></a>

### Reference: `collector118_prep/FULLTEXT-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1123,"path":"collector118_prep/FULLTEXT-DESIGN.md","sha256":"c434fb3ed213177992df42e1682d9c2ff332f4f026b038cc801bc27589f2cce5"} -->
# Next118 optional fulltext adapter composition, supplied text only

Compose117 failure-tolerant supplied feed cycle -> existing hash-pinned original
fulltext enrichment AST with supplied download/extract outcomes -> final original
classify/dedupe/category/doc preparation once across all enriched candidates.
Chunk enrichment<=100 because existing adapter bound. Its incidental per-chunk
docs are discarded; only enriched candidates flow into final whole-run dedupe,
preserving cross-feed/cross-chunk dedupe and classifier-before-dedupe contract.
Fulltext flag default false. maxchars700 default read from original config AST.
Unavailable provider leaves RSS unchanged like original. No real trafilatura/network
or backup/write. Enabled adapter gaps/Telegram remain explicit. Never call supplied
article text full verified/lossless article. Maxchars per original +ellipsis.

GNews separate supplied SDK-result parity adapter still needed; actual trafilatura
network parser isolation, installed package pins, source URL allowlist/SSRF and
runtime limits remain gates. No claim enabling a flag means its live port complete.

<!-- END-ORIGINAL-DOC -->


<a id="doc-024"></a>

### Reference: `collector118_prep/STAGE118.md`

<!-- ORIGINAL-DOC {"bytes":1104,"path":"collector118_prep/STAGE118.md","sha256":"e0fe25a0a1a53cb9faac2acf4483d418f58c0b1e68d33f7991ab88134a32f6b8"} -->
# Collector118 original optional fulltext cycle composition

INACTIVE. Supplied text outcomes only; no real trafilatura/network/parser, clients,
DB/mail/Telegram or scheduler effects.117 failure-tolerant supplied cycle ->
existing pinned original fulltext enrichment AST,<=100 chunk -> final original
classification/dedupe/category/doc once across whole run. Per-chunk incidental
docs discarded, not used as final output; enriched candidates carry forward.
Original default fulltext false, default maxchars700 AST loaded, truncation+
ellipsis and failure/unavailable fallback preserved. Source health/full article
not verified. Enabled missing adapters/live fulltext isolation remain gates.

6 tests default disabled, enabled truncation, unavailable provider, provider error,
missing outcome refusal, cross-source whole-run dedupe. Aggregate110 capture2MiB,
existing bounded original-adapter resource/100-candidate limits remain inherited.
Supplied text is neither lossless full article nor live extraction proof. Original
GNews/Telegram adapters and real fulltext source URL policy/pins/runtime remain.

<!-- END-ORIGINAL-DOC -->


<a id="doc-025"></a>

### Reference: `collector119_prep/STAGE119.md`

<!-- ORIGINAL-DOC {"bytes":1070,"path":"collector119_prep/STAGE119.md","sha256":"06b0cf7dc8a9298d27b6a97373eb40ca03f77838a3eb050599652620ad23e191"} -->
# Collector119 supplied-fulltext outcome snapshot correction

Inactive, production OFF. Prior118 unchanged.110 capture accepts dictionary<=100
keys, so118 enabled fulltext>100 unique eligible URLs refused.119 captures the
full outcomes mapping as list-of-{url,outcome} records together with candidates,
then reconstructs a plain bounded mapping from captured records before any
per-chunk enrichment AST. No resource cap increase:2MiB,20000 nodes,depth8,
list1000,string10000 unchanged. Exact URL keys<=2000. Resource budgets can still
refuse large1000-item runs, explicitly, not falsely claim unlimited parity.

9 local tests: all prior6 enrichment cases,120 eligible candidates cross100-chunk
boundary successfully;240x10000-text input refused by same aggregate budget;
custom outcome object refused before adapter AST. Production/network/write/
article_verified False. Other real extraction/URL/isolation/backup/GNews/runtime
and source health/deployment gates unchanged. This fixes supplied-output plumbing,
not live trafilatura extraction or full-feature readiness.

<!-- END-ORIGINAL-DOC -->


<a id="doc-026"></a>

### Reference: `collector120_prep/GNEWS-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":695,"path":"collector120_prep/GNEWS-DESIGN.md","sha256":"cd808783d98529871e7a59960b6fda5edbf42435685a7b009f20d43d9e92c0a5"} -->
# Next120 original GNews supplied-SDK-result parity

Hash-pinned original collect/_build_queries AST in inert scope. Fake GNews yields
bounded supplied results per original OR query. Original classifier/dedupe,
seen-title dedupe, active category filter, source publisher title, MEDIUM, clock,
summary300 and docs shape preserved. Fake save captures only; no real DB.
Backup stage must explicitly hold as unwired if enabled; no simulate sent refs.
No real SDK network call or optional package guarantee. ENABLE_GNEWS false default
returns disabled, with no provider calls. Enabled missing SDK preserves original
skipped outcome. Real GNews feed URL transport/isolation/sdk pins and backup gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-027"></a>

### Reference: `collector120_prep/STAGE120.md`

<!-- ORIGINAL-DOC {"bytes":1431,"path":"collector120_prep/STAGE120.md","sha256":"f8b156a143dfc872d6a4db6617a6491c17dff9f0a59c49f03f2581c35600f711"} -->
# Collector120 original GNews supplied-SDK-result contract

Inactive production OFF. Original hash-pinned collect/_build_queries AST over
inert GNews provider, original classifier/dedupe source pins. No real SDK network,
DB/client/scheduler/import of original collector.3 OR queries from pinned original
config. Defaults languageen/countryUS/period1d/maxresults15 match original; these
are fixed only in this prep, environment override parity is still pending.

Original ENABLE_GNEWS false -> disabled, available false -> original skip. Supplied
per-query errors continue. Title dedupe, classifier/category/dedupe, source publisher,
MEDIUM credibility, clock and300-character document preview preserved. Fake save
captures docs only. Original ENABLE_TELEGRAM_BACKUP true invokes hold exception,
not fake send/refs: documents stay empty, held candidates explicit. No backup
claims. Body outcomes snapshot as list records because query length>100 cannot
be a110 dictionary key; original budgets remain. Supplied SDK results bounded100
per query/3 queries, closed strings/publisher fields and aggregate capture.

6 local tests disabled/enabled hold/queries/title dedupe/docs/source error/SDK
unavailable/missing outcomes. Original files unchanged. Real SDK/feed transport,
URL policy/isolation/package pins, config override parity, backup and runtime/
source health/deployment remain gates. Scoped inactive contract, not live parity.

<!-- END-ORIGINAL-DOC -->


<a id="doc-028"></a>

### Reference: `collector121_prep/STAGE121.md`

<!-- ORIGINAL-DOC {"bytes":1270,"path":"collector121_prep/STAGE121.md","sha256":"b0547fabe625cca9ab574ba94dd751e342d1f44fecea4d6a264346693083a3c8"} -->
# Collector121 original Telegram synthetic-response contract

Inactive synthetic only, NOT FOR DELIVERY. No real credentials/network/send,
client/DB/reference write/mail/trigger effects. Original hash-pinned five functions
AST over inert requests provider and fixture token/chat choices only. Original
full-record formatter/batching, public/numeric/unrecognized permalink behavior,
per-batch mapping and HTTP/transport/JSON failure continuation preserved. Supplied
responses explicitly synthetic; returned refs NEVER mean real send or delivery.

7 tests success mapping, links, failure fallback, missing configuration, explicit
synthetic flag, missing outcome, inherited unsplit oversize bug. Original3500
packing limit and separator accounting can overflow; synthetic metrics expose
UTF16 units>4096. Actual current provider limit/policy not verified by fixture.
This is contract parity prep, not production Telegram backup adapter. Before real
backup: owner scope/destination identity, actual provider-limit checks, fixed
secret-safe client, rate/size policy, durable send receipts/reconciliation and
article-reference write authority/state remain gates. Sending must not be replayed
blindly after unknown receipt. Source code unchanged; fixtures cannot authorize it.

<!-- END-ORIGINAL-DOC -->


<a id="doc-029"></a>

### Reference: `collector122_prep/TELEGRAM-SAFE-PACKING-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1751,"path":"collector122_prep/TELEGRAM-SAFE-PACKING-DESIGN.md","sha256":"33c819405ec9cda57b8bb5bf67c87b3d1e28f1f8b313630b0b8acbc01970def7"} -->
# Next122 reversible backup packing and receipt state prep

Original formatter kept. Fix3500/codepoint/separator bug using actual UTF16 budget
including separators. Oversized full-record split into ordered continuation pieces,
never truncate full content. Keep URL/title/context manifest mapping each article
to ALL required piece indices, not a single pointer that loses continuation.
No real send. Returned text synthetic labelled NOT FOR DELIVERY.

Send state needs planned -> sending -> acknowledged/failed/unknown per message.
Durable receipt includes source article URL/content digest/batch-piece digest,
chat identity and provider message id. Unknown send latched, no retry until reviewed
provider reconciliation. Multiple refs per article changes original schema and
backward-compatible single head permalink requires explicit contract decision,
not assume one ref means complete. Partial backup visible; full content retained
in immutable bounded checkpoint until all required refs acknowledged. Don't drop
fulltext after keeping only300-char Mongo preview. Telegram limits current-source
verification and owner send/audience scope remain gates. No credential/client.

Reviewer122: SAFE as inactive synthetic structural scratch, not provider receipts,
authenticated durable state, or production proof. Renamed importable package for
staging, receipt uses relative packing import and inventory tests check inclusion.
Loaded state can be hand-edited to fabricate progress: validation is structural
only. Durable implementation must authenticate append-only transitions. Known
failure terminal is deliberate conservatism, not a reviewed retry policy. Provider
limits, rate controls, destination scope, multi-ref schema and runtime remain gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-030"></a>

### Reference: `collector123_prep/SHARED-BUDGET-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1305,"path":"collector123_prep/SHARED-BUDGET-DESIGN.md","sha256":"d541fa7569c2336abc122a193ce99a3e2da56061bedbf8640185c3210243e9be"} -->
# Inactive shared budget composition candidate

Original114 fetch supervisor plus original112 isolated parser runner, modified
parser to accept bounded remaining timeout and kill/reap process group on failure.
116 composition starts25s monotonic budget before profile, forwards remaining
budget to fetch and parser, refuses parser start after expiry, discards selected
result if completion check is expired. No real fetch/network/send/store.

This is not hard whole-request supervision. Trusted in-process profile, hash,
selection/capture, JSON parsing and cleanup can pass25s before the next boundary
check. Thread/request timeout cannot kill those phases. Hard request supervision,
original configuration parity, real runtime bubblewrap capability/deployment,
transport unframed truncation/header behavior/pins, per-cycle budgets remain gates.
Scratch parser code reads the fixed local original installation directory solely
to exercise current isolation; installation path must be package-relative+reviewed
if staged. No caller-selected path. Earlier source files unchanged.

Staging: parser BASE now package-relative fixed collector112_prep sibling path;
network_selection imports its own relative parser; tests use package imports.
Not mounted into app. No original112/114/116 files or pins changed.

<!-- END-ORIGINAL-DOC -->


<a id="doc-031"></a>

### Reference: `collector124_prep/FRAMING-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1275,"path":"collector124_prep/FRAMING-DESIGN.md","sha256":"5a5539be5f6cb082344c871ff54c5de211856f46a2f02fead44d87469bee9edf"} -->
# Inactive114 framing fix candidate

Add malformed stdlib HTTP header parse defects refusal. Add explicit observed
wire byte count equality to declared Content-Length (stdlib read(size) accepts
short EOF unless checked). Refuse close-delimited identity bodies even if they
look like valid RSS: no framing can distinguish complete data from truncation.
Keep close-delimited gzip/deflate only when existing bounded decoder proves
compression completion. Chunked parser requires zero-sized last chunk; stdlib may accept EOF before final blank line.

9 real stdlib wire parser tests, supplied BytesIO, all network/TLS mocked.
No live fetch or production wiring. Stricter refusal can exclude legitimate
close-delimited identity feeds: source-by-source availability/parity must be
verified before activation. Existing114 code unchanged; this is an inactive staged candidate.
A real combined worker/supervisor needs updated reviewed source pins, plus fixed
process isolation/deployment gates. Current source/header rules still conservative.

Worker byte-identical114. Runner changes only connector pin; package-relative
BASE chooses this fixed124 worker/connector. Test patches/imports use124 package.
Extra bytes beyond Content-Length ignored with single Connection:close request.

<!-- END-ORIGINAL-DOC -->


<a id="doc-032"></a>

### Reference: `collector125_prep/COMPOSITION.md`

<!-- ORIGINAL-DOC {"bytes":503,"path":"collector125_prep/COMPOSITION.md","sha256":"d4b8d3d46ddbeaf7cf440a715fba2fba2db53bedb626791fcfa5c4a26a7dfd55"} -->
# Inactive strict-fetch shared-budget composition

Copy123 composition, two import changes only:124 fixed/pinned fetch runner,
123 fixed isolated parser. Shared25s remaining-budget checks identical. Five
existing tests adapted only module patch target, actual parser/mock fetch smoke.
No live network/runtime app import. Strict framing policy means healthy source
availability/parity remains unresolved. Runtime stdlib/cert/bwrap/deployment,
hard request wall/configuration/full migration remain gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-033"></a>

### Reference: `collector126_prep/EXTRA-FEED-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":858,"path":"collector126_prep/EXTRA-FEED-DESIGN.md","sha256":"6dc8acfa80bf09db5c3ef94bfc53a0b80b5b97d8a2e15a3b001919bf6085e835"} -->
# Inactive original EXTRA_RSS_FEEDS parity candidate

Grounded original config split/trim/drop-empty -> scheduler/web/app pass list ->
rss.collect adds ('Custom',URL,'MEDIUM').115 profile omitted that path. Preserve
same naming/order/credibility for safe distinct extras in fixed installation
allowlist. Validate all manifest URLs even unused. Unapproved/duplicates/default
collisions/HTTP/local/credential/fragment/port violations refuse, never silently
filter. Manifest assertion alone is not authority: owner review gate stays false.

Only profile preparation, not125 rewiring. No env/network/provider/client reads.
MAX_ITEMS>100 still refused explicitly rather than silently truncate; projection
expansion remains distinct unresolved resource/parity decision. Configured extras
may hit fixed64 feed cap. Larger/custom values aren't original full parity.

<!-- END-ORIGINAL-DOC -->


<a id="doc-034"></a>

### Reference: `collector127_prep/EXTRA-COMPOSITION.md`

<!-- ORIGINAL-DOC {"bytes":446,"path":"collector127_prep/EXTRA-COMPOSITION.md","sha256":"079420abc117f8e2fad733aef031a814cca947feaac078008dd833ea9d01c45b"} -->
# Inactive installed extra feeds composition

Copy125 selection, substitute126 profile and explicit reviewed_extra_urls keyword
passed only to profile. Original default and installed extras selection share25s
budget and124 pinned fetch/123 parser. Tuple assertion doesn't grant authority:
owner allowlist review gate preserved, live write false. Mock network only.
No app wiring/env reads, no source availability/runtime/deploy/full cycle proof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-035"></a>

### Reference: `collector128_prep/PROJECTION-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1171,"path":"collector128_prep/PROJECTION-DESIGN.md","sha256":"a33cd04e997fd7883380e55fbb2e3b113f2d315da93fa15b5ccf7f9da5430de6"} -->
# Inactive isolated parser configurable projection

Copy original112 child and123 bounded-time runner. Add installation integer
projection_limit1..200 (default100); runner fixed numeric argv to child, child
uses it for entry projection, protocol equality uses min(limit,entry_count).
No input paths/commands from caller. Same input1MiB, parsed<=1000, aggregate text
512KiB, output1MiB, per text10000, OS resource/namespaces/pinned SDK constraints.
Pin child hash updated. Vendor/pins byte-identical112. Real supplied byte parser
checks, no network. Not yet larger MAX_ITEMS profile or selection fixture wiring.

200 is a bounded candidate ceiling, not full unrestricted original config parity.
Profile/selection currently100 and generic Budget5000nodes may refuse dense rows;
need separate reviewed resource policy before composition. Default100 unchanged.
No deployment/isolation capability proof beyond this installed local smoke.

Staging chooses vendored copy to keep fixed BASE self-contained. Copy is
byte-identical112, sdk-pins unchanged; no dependency update. Test package imports
and patch targets only. No wiring to123/profile/selection. Existing files intact.

<!-- END-ORIGINAL-DOC -->


<a id="doc-036"></a>

### Reference: `collector129_prep/SELECTION-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":1130,"path":"collector129_prep/SELECTION-DESIGN.md","sha256":"01ad52842ad924c0d2fa37d37f2a1fcecda07b96e053062b391b3b017d55491d"} -->
# Inactive bounded200 original feed selection

Copy original-AST supplied_feed_fixture: entries/max_items cap100->200. Replace
old5000-node fixture Budget with existing110 capture budgets (20000nodes/2MiB,
string10000/container1000/depth8/cycle/custom rejection). Inputs captured as
whole rows once (not O(n squared) per entry); output+trace captured together.
Original AST source hashes/allowlists/dateutil/date policies unchanged.

Input and output are separate budgets; not proof of combined resident memory or
hard process wall. This is trusted in-process selection prep, no network/parser/
writer.200 ceiling not unrestricted original config parity. Profile/parser128/
composition wiring not done. Scratch ROOT fixed original installation path;
staging needs reviewed package-relative original-root path.

StagingROOT resolves repository relative. Missing original files raise loud
FileNotFoundError, wrong original pins FeedRefused; tests do not skip. Inventory
binds exact supplied_feed.py/design/init hashes, test excluded by exact name to
avoid self-hash. No wildcard exclusion or prior historical AST inventory changes.

<!-- END-ORIGINAL-DOC -->


<a id="doc-037"></a>

### Reference: `collector130_prep/BOUNDED-COMPOSITION.md`

<!-- ORIGINAL-DOC {"bytes":931,"path":"collector130_prep/BOUNDED-COMPOSITION.md","sha256":"8bfad21858b2157ff42e5a8e560a97a5547bf40723db84f209625b7ebcb7ec63"} -->
# Inactive bounded200 installation/parser/selection agreement

115 profile copy only cap100->200;126 extras copy imports copied base profile
and updates above200 pending policy label;127 selection copy imports128parser,
copied extras profile and129selection, passes configured max_items as parser
projection_limit. This keeps parser projection and original AST slice agreeing.
Defaults unchanged40, limit1..200, shared25s budget, pinned124fetch, no runtime.

6 tests mock fetch with realisolatedparser/ASTselection,150/200default40/custom150,
201refusal beforefetch and25sremaining/projectionargument. No realnetwork.
200ceiling not unrestrictedparity; denseinput512KiB parser cap remains,selection
separateinput/outputbudget not combinedmemory/hardwall, runtime/deploy stillgates.
Scratch profile ROOT fixed local original sources; staging needs repo-relative
ROOT+package imports and test fail loudly if sourcesmissing, no skip.

<!-- END-ORIGINAL-DOC -->


<a id="doc-038"></a>

### Reference: `docs/ARCHITECTURE.md`

<!-- ORIGINAL-DOC {"bytes":5453,"path":"docs/ARCHITECTURE.md","sha256":"36a339a39ba91738c5154bb5971b7f87feee769c5049d7714a462f55abaae332"} -->
# Architecture and code map

Copyright (c) 2026 Push. All rights reserved.

## Request flow

```text
Flask entry point
  production_entry.create_app / public_live107 / public_preview106 / integration.private_router
    -> shared public_live_builder / public_preview_builder (no import-time app)
    -> explicit mode and access gates
    -> integration.news_api.create_app
       -> bounded reader and public field normalization
       -> news, country, story, map, export and report adapters
       -> integration/ui and approved Finder/branding assets
```

The public live entry point injects a find-only reader for `geo_intel/articles`. It selects up to 100 documents by `created_at`, normalizes the approved public fields and caches successful reads for 60 seconds per process. Malformed rows can reduce the displayed count. A database failure latches the reader unavailable until process restart after repair; it is not shown as a successful empty collection.

The public entry point allows a narrower GET/HEAD route set than the private app. It serves a self-contained offline Finder snapshot, not the original provider-connected shell. Weekly PDF, private POST actions, event reads and account/mail operations are outside that public route set.

`integration.preview_launcher` selects the explicit Geo-only branch or the retained isolated legacy branch. `integration.geo_only_runtime` composes private access with optional reviewed article/event reads. These launchers do not import the original collector applications as a complete live merge.

The production factory and public live wrapper both call the shared guarded builder, with one Flask app/client and one headers hook per factory invocation. `integration.news_api:app` stays available through lazy compatibility access, while importing its factory creates no fixture app. The public live wrapper adds default-on E2 response headers and an optional, default-off E1 edge guard. See [Configuration](CONFIGURATION.md).

## Existing folders

| Location | Responsibility | State |
|---|---|---|
| `integration/` | Shared Flask API, adapters, access gates, readers, cross-project models and review records | Mixed runtime, test support and historical evidence; read each feature's limits |
| `integration/ui/` | Workspace, country, map, report and Finder offline UI | Assets served through explicit allowlists |
| `integration/branding/` | Workspace logos, icons and metadata | Served branding |
| `src/`, root HTML/JS/CSS assets, `vendor/` | Original Finder data, build input and static output | Retained; paths are referenced by builds, readers and tests |
| `proxy_runtime/`, `updater_runtime/` | Finder proxy safety and refresh/update helpers | Separate from public Flask mounting |
| `intelligence/geo/` | Original Geo collectors, processing, storage, reports and web app | Retained engine; importing operational modules can have effects |
| `intelligence/brics/` | Original BRICS engine, source config, reports and web app | Retained engine, not public Geo stored-news source |
| `collector108_prep/` through `collector130_prep/` | Successive collector preparation stages, receipts, parsers and bounded composition | Preparations, not automatically active collectors |
| `feature_mail_prep/`, `feature_mail_mount/` | Mail contracts, Mongo receipt/control store, blueprint and Apps Script bridge | Mount implementation exists; existing public/private launchers do not import it |
| `feature_finder_prep/` | Provider mount policy and served-copy preparation | Not a live authenticated provider connector |
| `feature_world_views/` | Supplied world detail/filter/export views | Source module and fixtures, not live world retrieval or automatic mounting |
| `checks/` | Collector facade, production wrapper and source drift checks | Ten separate cases outside root discovery |
| `feature_related_prep/` | Related-news preparation | Separate from automatic production activation |
| `tests/` | Python and Node-related regression contracts | Includes historical artifact and fixture checks |
| `scripts/` | Integrity metadata, connection audit and provenance helpers | Maintenance tools, not a deploy command |
| `state/`, `legacy-config/` | Finder updater state and retained workflow/config sources | Keep out of new deployment assumptions |

## Cross-project connections

The integration layer contains news-to-Finder context, country signals/pages, related-story groups, stored-news exports, original report adapters, source/tariff evidence and map data. `integration/cross-connections.json` records the earlier connection design. These connections are bounded by the selected launcher and reader; source retention alone does not expose every original feature.

## Boundaries to preserve

- Keep the original source and evidence intact while improving navigation.
- Do not move hash-pinned files without a reviewed manifest migration.
- Preserve the public field allowlist and private route/access separation.
- Do not reuse the public read-only client for mail acknowledgements or collection writes.
- Mount collectors, durable account login, provider calls and mail separately with reviewed credentials, limits and permissions.
- Node updater/proxy services and legacy Geo/BRICS launchers are distinct operational processes, not alternative ways to run the same app.

For proposed folder changes, see [FOLDER-PLAN.md](FOLDER-PLAN.md). No files have been moved by this documentation patch.

<!-- END-ORIGINAL-DOC -->


<a id="doc-039"></a>

### Reference: `docs/CLAIM-SOURCES.md`

<!-- ORIGINAL-DOC {"bytes":5699,"path":"docs/CLAIM-SOURCES.md","sha256":"0d92048d182b648ee8f7cca178bb987e4ee687b997493dfcc32d4cc5ed0716ba"} -->
# Documentation claim checks

Inspected source base: 20649f625838f74a429b61702c9d9a8e2fdaca84. These are source contracts, not deployed-state checks.

| Documentation claim | Source evidence |
|---|---|
| Process environment snapshot, no automatic root dotenv | `integration/private_router.py:2-10`; `integration/public_live_builder.py:143` and `integration/public_preview_builder.py:73` (final `app=build_...(dict(os.environ))` statements; use symbol search if line numbers shift) |
| `PREVIEW_GEO_ONLY_ENABLED=true` selects Geo-only; default false | `integration/preview_launcher.py:13-25` |
| Private `PREVIEW_ACCESS_ENABLED`, `PREVIEW_ORIGIN`, `PREVIEW_PASSWORD_HASH`, `PREVIEW_SESSION_KEY` | `integration/preview_access.py:92-96` |
| HTTPS canonical origin | `integration/preview_access.py:18-22`; `integration/public_preview_builder.py:34-38`; `integration/public_live_builder.py:70-74` |
| scrypt/PBKDF2 password hash accepted | `integration/preview_access.py:23-24` validation; `:12` imports `check_password_hash` |
| Session secret at least 48 characters | `integration/preview_access.py:85-86` |
| `PREVIEW_TRUST_ONE_PROXY=false` default, optional explicit true | `integration/preview_access.py:97-100`; `.env.example:147` (locate variable if lines change) |
| Empty public mode exact flags: `PREVIEW_PUBLIC_SAMPLE_ENABLED=true`, `PREVIEW_GEO_ONLY_ENABLED=true`, `PREVIEW_ACCESS_ENABLED=false`, `NEWS_READ_ENABLED=false`, `NEWS_EVENTS_READ_ENABLED=false`, `FINDER_NETWORK_PREVIEW_ENABLED=false` | `integration/public_preview_builder.py:26-33` |
| No injected client in public sample | `integration/public_preview_builder.py:29,46` |
| `PUBLIC_NEWS_READ_ENABLED` false fallback / exact true enable | `integration/public_live_builder.py:58-60` |
| Public live mode requires all public sample flags plus `NEWS_STORE_MAPPING_VERIFIED=true`, `PUBLIC_NEWS_DISCLOSURE_VERIFIED=true`, `GEO_READONLY_CREDENTIAL_VERIFIED=true` | `integration/public_live_builder.py:61-66` |
| Exact `GEO_DATABASE=geo_intel`, `GEO_ARTICLES_COLLECTION=articles`; `GEO_MONGODB_URI` required | `integration/public_live_builder.py:67-69,87`; credential role is operator assertion, not introspected |
| Private article reads require access, mapping review, URI; events separately gated | `integration/geo_only_runtime.py:23-46` |
| `GEO_MONGODB_DB_NAME` versus `GEO_DATABASE` conflict refused | `integration/preview_launcher.py:18-20` |
| Separate Geo/BRICS URI names and legacy fallback | `integration/storage_settings.py:20-30` |
| Public latest up to 100 rows; malformed rows may reduce count | `integration/public_live_builder.py:18,26-27,87,101`; `integration/storage_reader.py:23` sorts by `created_at` |
| Per-process successful read cache 60 seconds | `integration/public_live_builder.py:92-103` |
| Database read failure clears cache, closes client and latches until restart after repair | `integration/public_live_builder.py:96,104-108`; no reset branch exists in the closure |
| Public protected route authorization is GET/HEAD-only allowlist | `integration/public_live_builder.py:76-81`; `integration/public_preview_builder.py:40-45`; public framework health/error/automatic OPTIONS responses are not a write capability |
| Single-worker run guidance | `integration/public_live107/README.md:45-46`; `integration/public_preview106/README.md:16-18`; private limiter/session state in `integration/preview_access.py:26-35`. The code does not enforce Gunicorn worker count. |
| `MERGED_MAIL_PATH=apps_script`, `MERGED_MAIL_ENABLED=false` default, no SMTP fallback | `integration/mail_bridge.py:10-17`; `.env.example:127-131` |
| Mail mount not imported by existing launchers | `feature_mail_mount/DESIGN.md:5-9`; no `feature_mail_mount` imports in `public_live107.py`, `public_preview106.py`, `integration/private_router.py`, `integration/preview_launcher.py` or `integration/news_api.py` |

## Audit hash scope

`integration/dependency_audit/audit.json:583` contains `source_manifest_sha256`. It hashes the canonical JSON list in `integration/dependency_audit/import-inventory.json` -> `source_baseline.files`, not the root `staging-manifest.json`.

The test `Tests.test_source_manifest_and_ast_inventory_consistency` in `tests/test_dependency_audit.py` recomputes the list hash, checks source bytes/AST and compares the scoped inventory. The current source hash is `9ae095da1cf17bf6537ee007075d8665070406ba029fbca6eb4745c256098d5f`, recomputed from the refreshed scoped inventory. Older dependency receipts remain historical records, not current install evidence.

## Current additions

- `public_live107.guarded_public_app` installs E2 security headers by default, before optional E1. `integration/security_headers.py` defines HSTS 604800 on secure requests or a final HTTPS forwarded-proto value, plus XFO, Permissions-Policy, COOP and XPCDP. Existing response header values are preserved.
- `integration/edge_guard.py` is off unless `EDGE_GUARD_ENABLED=true`. Enabling requires a separate Render single appended XFF-hop topology check. This document does not confirm that topology.
- Root discovery includes 25 E1/E2 tests. Collector 285, checks 10 and world 26 are separately discovered. Commands and expected counts are in `TEST-GATES.md`; source tests are not deployment approval.

Factory176source correction: public_live107/public_preview106 are thin compatibility WSGI entries. Shared public_live_builder/public_preview_builder/news_api create no app/client at import. news_api:app is lazy on WSGI access, preserving factory module patch targets. production_entry uses guarded_public_app (one security headers hook, optional edge stays defaultOFF). Runtime read failure latch/restart contract unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-040"></a>

### Reference: `docs/CONFIGURATION.md`

<!-- ORIGINAL-DOC {"bytes":5705,"path":"docs/CONFIGURATION.md","sha256":"fe5094a65d09a06aaabdeb702de2781fd4a8138e64ef80e6539f54352b4887cd"} -->
# Configuration guide

Copyright (c) 2026 Push. All rights reserved.

## How settings are loaded

The merged Flask entry points use a snapshot of the process environment. They do not automatically load a root `.env` file. Set values in the local process or the hosting service's environment. Never commit filled-in examples, MongoDB URIs, session keys, passwords or provider tokens.

`.env.example` is an inventory of historical/private settings, not a complete current public-mode recipe. Original Geo and BRICS configs call `load_dotenv`; that does not mean the merged Flask launcher does. Avoid loading legacy defaults into the merged app.

## Safe local deny mode

Set `PREVIEW_GEO_ONLY_ENABLED=true`, `PREVIEW_ACCESS_ENABLED=false`, `NEWS_READ_ENABLED=false`, `NEWS_EVENTS_READ_ENABLED=false` and `FINDER_NETWORK_PREVIEW_ENABLED=false`. Use `integration.private_router:app` and bind only to loopback. No credentials are needed. Workspace access is denied by design.

## Private password preview

Use `integration.private_router:app`. The Geo-only composition needs:

| Variable | Value or purpose |
|---|---|
| `PREVIEW_GEO_ONLY_ENABLED` | `true` |
| `PREVIEW_ACCESS_ENABLED` | `true` |
| `PREVIEW_ORIGIN` | Exact canonical HTTPS origin |
| `PREVIEW_PASSWORD_HASH` | Reviewed scrypt/PBKDF2 password hash, supplied securely |
| `PREVIEW_SESSION_KEY` | Random secret of at least 48 characters, supplied securely |
| `NEWS_READ_ENABLED` | Keep `false` for a no-database preview |
| `NEWS_EVENTS_READ_ENABLED` | Keep `false` unless separately reviewed |
| `FINDER_NETWORK_PREVIEW_ENABLED` | Keep `false` unless separately reviewed |
| `PREVIEW_TRUST_ONE_PROXY` | Default `false`; only enable after verifying the exact proxy topology |

Use one worker. This is a single-worker preview password gate, not durable multi-user account login. The private Geo reader additionally requires a separately verified mapping, actual read-only role, explicit URI and `NEWS_STORE_MAPPING_VERIFIED=true`.

## Public empty-sample mode

Use `public_preview106:app` only for an explicitly selected public preview. Required values:

```text
PREVIEW_PUBLIC_SAMPLE_ENABLED=true
PREVIEW_GEO_ONLY_ENABLED=true
PREVIEW_ACCESS_ENABLED=false
NEWS_READ_ENABLED=false
NEWS_EVENTS_READ_ENABLED=false
FINDER_NETWORK_PREVIEW_ENABLED=false
PREVIEW_ORIGIN=<exact canonical HTTPS origin>
```

No injected client is allowed. No stored news is read. Public passwords are not required in this mode; do not mistake public access for account authentication.

## Public stored-news mode

Use `public_live107:app`. All empty-sample settings above are still required, plus:

| Variable | Required value or purpose |
|---|---|
| `PUBLIC_NEWS_READ_ENABLED` | `true` |
| `NEWS_STORE_MAPPING_VERIFIED` | `true`, only after the exact mapping is checked |
| `PUBLIC_NEWS_DISCLOSURE_VERIFIED` | `true`, only after the displayed fields/audience are approved |
| `GEO_READONLY_CREDENTIAL_VERIFIED` | `true`, only after the actual Atlas role is checked |
| `GEO_DATABASE` | `geo_intel` |
| `GEO_ARTICLES_COLLECTION` | `articles` |
| `GEO_MONGODB_URI` | Dedicated read-only credential supplied securely |

Environment assertions are gates, not evidence that a credential is read-only or disclosure is authorized. Keep `NEWS_READ_ENABLED=false`: that private-mode flag is not the public reader switch.

The source's single-worker command is:

```bash
gunicorn public_live107:app --bind 0.0.0.0:$PORT \
  --workers 1 --threads 2 --timeout 30
```

This is a reference command, not an instruction to change a running service. See the [public reader notes](../integration/public_live107/README.md) for timeouts, cache, row limits and rollback. Actual hosting settings are not verified by this guide.

## Public response protections

`public_live107:app` installs E2 security headers by default. Once deployed, with no environment change, responses add X-Frame-Options, Permissions-Policy, Cross-Origin-Opener-Policy and X-Permitted-Cross-Domain-Policies. HTTPS responses (or a final `X-Forwarded-Proto` value of `https`) also add HSTS for 604800 seconds (7 days), without includeSubDomains or preload. Existing header values are not overwritten. `SECURITY_HEADERS_ENABLED=false` stops adding them, but cannot undo HSTS already cached by browsers.

E1 edge guard is different: it is off by default. `EDGE_GUARD_ENABLED=true` requires a separately confirmed Render single appended X-Forwarded-For hop. Its counters are per worker. Do not enable it from these documentation examples.

## Inactive operational settings

- `GEO_MONGODB_URI` and `BRICS_MONGODB_URI` isolate credentials for the retained projects. A shared legacy `MONGODB_URI` is not a safe merged default.
- `MERGED_MAIL_PATH=apps_script` and `MERGED_MAIL_ENABLED=false` describe the selected delivery direction. They do not mount the mail blueprint or create an Apps Script trigger. The bridge has its own `MAIL_V1_*` script properties; see [mail mount design](../feature_mail_mount/DESIGN.md).
- Finder provider pools, `AISSTREAM_KEY`, `APP_SECRET`, updater GitHub tokens and Comtrade keys belong to separate preserved services. Their presence does not enable them in public Flask.
- Legacy `ENABLE_*` settings can activate sends, scraping or cleanup in the original engines. Leave them off in development and do not launch those engines casually.
- Optional `trafilatura`/`gnews` dependencies are outside the reviewed 25-package closure. Installing the original Geo requirements adds these packages even when feature flags are off.

Do not enable collection, mail, provider calls, account persistence or cleanup as part of README/folder cleanup. Each needs its own reviewed integration and cutover.

<!-- END-ORIGINAL-DOC -->


<a id="doc-041"></a>

### Reference: `docs/FOLDER-PLAN.md`

<!-- ORIGINAL-DOC {"bytes":3111,"path":"docs/FOLDER-PLAN.md","sha256":"08be5c1db2b1890d0283328fcf8aa1e005e99591ab9238f2496c7e16407513b1"} -->
# Folder arrangement proposal

Copyright (c) 2026 Push. All rights reserved.

This is a proposal only. No source, feature, asset, evidence, configuration or workflow file is moved or deleted by the documentation patch.

## First: make the existing tree understandable

1. Keep runtime and original-code paths unchanged.
2. Add the root README and `docs/` navigation guides.
3. Link each preparation package's design note from an inventory rather than renaming packages during active development.
4. Label historical dependency receipts and current installation profiles clearly. Do not erase evidence to reduce alert counts.

This gives a clearer repository without breaking imports, relative file reads, public asset allowlists, generated Finder output or preservation hashes.

## Later: proposed target layout

```text
apps/
  workspace/          # selected Flask entry points
  finder/             # Finder static input/output and separate Node services
engines/
  geo/                # original Geo engine
  brics/              # original BRICS engine
integration/          # shared adapters, readers and contracts
preparation/
  collectors/         # collector stage packages, preserved by identity
  mail/
  finder/
  related/
docs/
  architecture/
  configuration/
  evidence/           # dated, immutable receipts with source-path mappings
tests/
scripts/
```

The target layout is not ready to apply wholesale. `integration/` contains both serving modules and evidence; separating them needs an explicit import/data-path map. Root Finder filenames are loaded by builds and readers, and `intelligence/*` files are hash-pinned.

## Migration gates, one slice at a time

- Inventory every Python import, dynamic import, Node path, HTML asset reference, source-file read, manifest path and test fixture before moving a slice.
- Preserve feature behavior and add temporary compatibility entry points only where reviewed.
- Record old-to-new paths and update preservation/integrity metadata without rewriting historical evidence.
- Verify generated Finder branding/data, private/public route allowlists and forbidden-path tests.
- Run targeted tests and the configured full suite; inspect the served UI and PDFs for visual regressions.
- Have the runtime owner review build/start paths and rollback separately. Do not change hosting or trigger a deployment merely to tidy folders.
- Leave `.github/workflows/` untouched in this work. Any eventual workflow path migration is an owner-managed follow-up.

## Do not consolidate collector stages blindly

The numbered collector packages hold different parser, fetch, selection, receipt and composition contracts. A later stage imports earlier reviewed stages; the folders are not proven redundant copies. Before choosing a single production collector, document the dependency graph, preserve its audit history and prove behavioral parity. Retain every working feature and fail-closed limit.

The immediate recommendation is documentation-only navigation. Defer physical rearrangement until the active merge and runtime mounting have a stable, reviewed boundary.

<!-- END-ORIGINAL-DOC -->


<a id="doc-042"></a>

### Reference: `docs/TEST-GATES.md`

<!-- ORIGINAL-DOC {"bytes":2565,"path":"docs/TEST-GATES.md","sha256":"390a4f958a911f95652ee9f9146f583656094d4b6daf8b1fb10c5f49093f28ab"} -->
# Source test gates

Run from a clean checkout in the reviewed configured Python environment, with Node and required parser artifacts available. No network collection or deployment is part of these commands. Missing prerequisites are unverified, not passed.

The gate at source base 20649f625838f74a429b61702c9d9a8e2fdaca84 passed 1469 root + 285 collectors + 10 checks + 26 world cases, with 2 skips and 1 expected failure. The staging manifest records only the root count. Counts are measured, not permanent targets.

```bash
PYTHONPATH=.:collector108_prep python -m unittest discover -s tests
PYTHONPATH=.:collector108_prep python -m unittest collector108_prep.test_durable \
  collector108_prep.test_job_contract collector109_prep.test_drive collector109_prep.test_engine_chain \
  collector109_prep.test_fetch_stage collector109_prep.test_safety collector109_prep.wiring.test_endpoint_drive \
  collector110_prep.test_durable_checkpoint collector110_prep.test_input_budget collector111_prep.test_drive \
  collector111_prep.test_drive_durable collector111_prep.test_engine_chain collector111_prep.test_safety \
  collector112_prep.test_parser collector113_prep.test_composition collector113_prep.test_transport \
  collector114_prep.test_connector collector114_prep.test_runner collector115_prep.test_composition \
  collector115_prep.test_profile collector116_prep.test_network_selection collector117_prep.test_supplied_cycle \
  collector118_prep.test_fulltext_composition collector119_prep.test_fulltext_composition collector120_prep.test_gnews_supplied \
  collector121_prep.test_telegram_supplied collector123_prep.test_budget collector124_prep.test_framing \
  collector124_prep.test_runner collector125_prep.test_budget collector126_prep.test_profile \
  collector127_prep.test_budget collector127_prep.test_extras collector128_prep.test_projection \
  collector129_prep.test_selection collector130_prep.test_composition
PYTHONPATH=.:collector108_prep python -m unittest discover -s checks
PYTHONPATH=.:collector108_prep python -m unittest feature_world_views.test_detail \
  feature_world_views.test_export feature_world_views.test_filters feature_world_views.test_inventory \
  feature_world_views.test_world
```

For named case discovery, use the same unittest loader and print each case's `id()` before execution. Root `discover -s tests` does not include the collector, checks or world blocks above. Keep their results separate. A full source gate is not a certificate of production settings, credentials, topology, current data or live readiness.

<!-- END-ORIGINAL-DOC -->


<a id="doc-043"></a>

### Reference: `feature_finder_prep/MOUNT-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":5004,"path":"feature_finder_prep/MOUNT-DESIGN.md","sha256":"29e0f1dfc5599b2a66dfa84460af1c9fa9b4957ca3fec7357fca8c49c627b096"} -->
# Finder mount decision preparation

Copyright (c) 2026 Push. All rights reserved.

Source-only policy evaluator, not a proxy, provider connector, mounted Finder,
or authorization grant. Existing shell/source/index unchanged. public107 still
serves offline Finder. No requests, keys, environment or runtime changes here.

mount_policy.prepare accepts explicit reviewed-input records for Groq, Gemini,
Mistral only, exact official HTTPS endpoint, bounded model name, caller review
within24h, disclosure/free-only assertions, report/day/request/token/time/bytes
caps. These assertions are unverified caller data: output says account/owner
permission unverified, mountedFalse, transportFalse. It rejects shared legacy
proxy, arbitrary host/path/query/userinfo, unsupported saved-provider widening,
paid fallback and budgets multiplied beyond aggregate12requests/24000tokens.
Caps are design guardrails, not provider quota availability or execution proof.
Per-report wall <=120seconds and per-attempt <=15seconds are proposed caps;
existing shell only bounds each request, so it does NOT enforce this overall
wall. Mount requires a separate reviewed implementation to enforce all budgets
across report sections, failovers and grounded retry. No silent PDF truncation:
static original report fallback when exhausted, labeled non-live facts.

## Sources inspected October8,2026

Official docs only. Account state, actual quotas and key permissions unverified.
No model from docs or original stale arrays is selected by this increment.

- https://console.groq.com/docs/api-reference
  Documents POST https://api.groq.com/openai/v1/chat/completions.
- https://console.groq.com/docs/your-data
  Inference data not retained by default; system reliability/abuse logs may be
  retained up to30days unless legally required longer. ZDR is configurable,
  not assumed active. Never call all free providers zero-retention.
- https://ai.google.dev/gemini-api/docs/pricing
  Free tier has limited model access and content used to improve products;
  exceptions/terms need account+region review. Some models lack free tier.
  Paid search/grounding must not be an automatic fallback.
- https://ai.google.dev/gemini-api/docs/rate-limits
  Limits apply per project, not per API key; rotating keys cannot create a
  valid new quota. No numeric account quota is asserted here.
- https://ai.google.dev/gemini-api/docs/generate-content/get-started
  Documents generativelanguage.googleapis.com/v1beta/models/{model}:generateContent.
  The guide calls this legacy and recommends Interactions for new projects.
  Preserving the old Finder API shape is a reviewed compatibility choice, not
  a claim that it is the newest Google API.
- https://docs.mistral.ai/api/endpoint/chat
  Documents POST https://api.mistral.ai/v1/chat/completions.
- https://docs.mistral.ai/admin/billing-usage/usage-limits
  Free mode offers included usage within account limits. Pay-as-you-go may
  extend usage beyond included usage. Verify it is off before free-only use.
- https://docs.mistral.ai/admin/monitor-comply/privacy-data-controls
  API data is not used for model training. This is NOT proof of zero retention.
- https://docs.mistral.ai/admin/monitor-comply/zero-data-retention
  ZDR available on paid plans for supported stateless calls. Do not promise
  free-tier ZDR based on the older2024release announcement.

## Before actual mounting

Owner approves exact providers and prompt fields (product/code/country and
approved report data), account/key scope, audience and free-only budget.
Confirm current model free eligibility and retention terms for that account.
A private server proxy needs authenticated user/CSRF, durable quota ledger,
per-user and shared account budgets, bounded concurrency1-2 on512MB, fixed
provider allowlist, no redirects, no request-driven URLs/tools/grounding or
external retrieval, strict provider response parsing and output escaping.
No third-party shared proxy inherits permission to see prompts or keys.
Never put keys into client HTML/logs or expose one user's prompts to another.
Preserve unsupported-key refusal and failover without moving a saved key to a
different provider. Check existing original proxy/BYOK behavior before deciding
whether to preserve or migrate it; this evaluator does not silently replace it.

Factual labels must distinguish AI model knowledge, dated snapshot data and
verified current sources. Existing full-report UI says official/exact/live-ready
elsewhere; reviewed served-copy corrections required before real exposure.
Test actual PDF pages/first-last sections with enforced budget and static
fallback, browser errors, errors during JSON body, malformed JSON,429,deadline,
quota concurrency/restart and no-private-data leakage. Test real provider smoke
only within source-grounded disclosure permission; this unit performs none.

Mounting/secrets/quotas are later decisions. This source-only unit completes a
design checkpoint, not the requested live feature or full parity.

<!-- END-ORIGINAL-DOC -->


<a id="doc-044"></a>

### Reference: `feature_mail_mount/DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":3883,"path":"feature_mail_mount/DESIGN.md","sha256":"887b7551d3fe662f389d4bf9ab0110f047a1877d4c089c4e59262ff3aeb11a2c"} -->
# Mail mount implementation, not activation

Copyright (c) 2026 Push. All rights reserved.

Explicit MongoMailStore + blueprint + manual Apps Script bridge. Nothing is
imported by existing launchers. Runtime owner attaches the blueprint separately;
public107 read-only facade cannot be reused. No client, index, trigger or secret
is created here. No SMTP route or heavy dependency added.

Required source review: exact geo_intel articles/events/mail_control/mail_receipts
mapping, snapshot transactions, write permission, provisioned control schema,
canonical UTC datetime.isoformat article date fields. Mixed BSON/string dates are refused,
not silently treated as a complete weekly archive. No live source checked here.

Provisioning (runtime owner, not performed here): one mail_control row with _id
mail-v1, schema 1, revision 0, channel_id, policy, active {}. Channel is SHA256 of
UTF8 JSON with key order sender,recipients; sender is the lowercase Apps Script
effective-user email, recipients sorted lowercase unique addresses. Policy must
be supplied explicitly: fetched or displayed. No default. A config fingerprint
is a binding, not permission or authentication. Header secret is separate.

Snapshot query reads original top60 unsent articles then applies score4 display.
Weekly top20 plus DB category/country aggregates represent the entire queried
7day snapshot, not counters over only top20. Critical6h is bounded200 and uses
a separate mail_critical_sent flag (behavior change: suppresses repeat alerts).
Events are original digest-only90day entries, bounded200. All-low-score digest
skips unless critical/events exist, avoiding marking unseen articles in an empty
email. Stable ObjectId tie-break adds determinism absent from the old renderer.
Both behavior changes require approval before activation.

Receipt HTML and exact selected IDs are archived before send. Transactions
serialize all operations by replacing the control revision; no driver retries.
Claim gives a send permit once; another claim never gives permission to resend.
Acknowledgement atomically marks archived IDs, stores bridge acceptance and
clears active kind. Repeated ack is idempotent and never sends. Weekly never
marks; critical marks a separate flag. Arbitrary client article_ids are refused.

GmailApp return is only bridge_send_returned_not_delivery, not independent
provider verification or proof that the recipient got the email. Header holder
is a trusted bridge able to assert this receipt. It is not a public/untrusted
client endpoint. Secret rotation, sender/recipient authority and schedule are
runtime-owner decisions. No scheduling/triggers in this increment.

Apps Script persists nonce before prepare, claiming before claim, sending before
Gmail, and send_returned before ack. Lost claim response, send exception/crash or
failed persistence after send holds for manual reconciliation. No lease expiry
or automatic retry can resend an ambiguous send. Failed ack retries ack only.
Holding may miss mail; safety over silent duplication. Manual recovery is not
implemented. Parallel script copies are fenced by Mongo claim as well as local
script lock. An active kind prevents overlap even if a fresh nonce is submitted.

Archive retains full HTML without automatic deletion. Hard capacity128 fails
closed and requires reviewed export/retention work. This is not unlimited
weekly history, article backup, Telegram recovery proof or cleanup permission.
Mongo durable transactions need external review and real smoke test; local
mock tests do not prove an actual deployment. Bounded render may still fail on
schema drift, unsafe URLs, missing articles during ack or large events; failures
hold, never mark or send. Source URL constraints inherit save131 conservative
public-HTTPS/no-query validation. That restriction must be considered before
real mounting on existing article data.

<!-- END-ORIGINAL-DOC -->


<a id="doc-045"></a>

### Reference: `feature_mail_mount/HANDLERS216.md`

<!-- ORIGINAL-DOC {"bytes":2838,"path":"feature_mail_mount/HANDLERS216.md","sha256":"a606cf344630479174bdb4c43d4e427c976500662aa6e549eca905f838f53cec"} -->
# 216: OFF-by-default manual Apps Script dispatch

mailV1Digest216, mailV1Critical216 and mailV1Weekly216 map respectively to
runMailV1('digest'), runMailV1('critical') and runMailV1('weekly'). Each passes
one literal argument only. These names do not replace the declared HANDLERS
mailV1Digest/mailV1Critical/mailV1Weekly; those remain without wrappers.
The existing companion, bridge, HANDLERS table and routes are unchanged.

Editor Run passes no arguments, so it always returns OFF. A trigger event object
is refused. Exact primitive true is reachable only from another function or a
scripts.run API caller. Do NOT deploy this project as an API executable with
these functions. The file contains no true caller, installer or automatic call.
Wrappers must not be called in any real run under this source-only unit.

False/undefined returns a frozen off/no_send_attempt object before any bridge or
Apps Script service lookup. Extra arguments are ignored without access. Other
values refuse with fixed mail216_refused. ON calls the existing bridge, which
still separately requires MAIL_V1_ENABLED exactly 'true'. 216 reads/writes no
properties, creates no triggers, deploys nothing and changes no collector path.

Wrapper ON IS A REAL SEND CAPABILITY through the existing GmailApp bridge.
Source/default-OFF is not a permission barrier. No real send until the owner's
final recipient and words are confirmed and all other mail gates are satisfied.
All tests use spies or mocked Gmail, never real Gmail or Google services.

Only off/skipped/acknowledged are accepted bridge states. Output is frozen static
state/scope data; no recipient, subject, receipt ID, count or arbitrary text is
passed through. Malformed/unknown return uses fixed mail216_unknown; errors from
the bridge use fixed mail216_possibly_sent, even if a failure occurred before a
send. No raw message/stack/name or Logger output is retained. Neither error nor
acknowledged proves delivery or non-delivery. Off/skipped means this invocation
made no send attempt, not proof about older pending attempts or delivery.

claimLost, Gmail failure and persistAfterSend hold the existing pending phase;
216 never clears it, invents a nonce, retries a send or falls back to SMTP.
An ack-only bridge retry remains ack-only. 216 does not implement reconciliation.

Current mailv1 has old 128-cap receipts and does not enforce 212 exclusion keys.
History, marking, sender/recipient scope, DB timing, weekly identity, mounting and
reconciliation remain open. Mailer activation is separate from collector cutover.
Apps Script stays the selected rail; SMTP fallback stays held. No trigger rebuild,
activation, live sends, live DB access or collector cutover occurs here.

mail216_unknown after a bridge call must be treated like possibly_sent, never
"not sent"; do not retry on unknown.

<!-- END-ORIGINAL-DOC -->


<a id="doc-046"></a>

### Reference: `feature_mail_mount/OPERATIONS-CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":5593,"path":"feature_mail_mount/OPERATIONS-CONTRACT.md","sha256":"a475af4daac1a365a7f7e8537cff24def03e19542fb6bb5c6f28db54c93cd064"} -->
# Mail operations and original-feature parity audit

Copyright (c) 2026 Push. All rights reserved.

Source-only contract. No triggers installed, properties written, routes mounted,
receipt acknowledged, state deleted, DB/role/index/TTL changed, or mail sent.
operations.py only evaluates supplied configuration/snapshot proposals. Its
outputs explicitly deny send/ack/clear/new-nonce authority. Current evidence and
owner permissions must be checked separately at execution time.

## Original source inspected

intelligence/geo/apps_script/Code.gs is preserved. Original companion:
- keepAlive hits /health with query key, default10minutes.
- runCollect POST /collect, default30minutes.
- sendDigest GET /digest-data, UTF8 JSON, skip no fetchedIDs+no critical,
  Gmail send then POST /mark-emailed with arbitrary article_ids.
- critical/weekly POST /critical,/weekly, defaults30minutes and Monday09:00.
- cleanupOld POST /cleanup-old monthly, defaultday1at03:00, assumes permanent
  Telegram backup, which is not adequate recovery proof for deletion.
- digest chooses configured fixed times(default10:00,22:00) or supported hourly
  interval. setupTriggers deletes ALL project triggers, including unrelated ones.
- doGet proxies dashboard with query secret, frame optionsALLOWALL.

## New bridge parity and deliberate gaps

Save135 adds header-auth prepare/claim/ack + persistent bridge phases, not a
replacement for old script deployment. Digest/critical/weekly use original
hash-pinned renderers. Digest60 fetch/score4display; critical6hbounded200;
weekly7day DB aggregates/top20/countrytop8; events90daybounded200. Exact archived
IDs only, send-start claim once, atomic acknowledgement/mark. Receipt says
bridge_send_returned_not_delivery. No Gmail message ID is available from
GmailApp.sendEmail; no recipient-delivery proof or independent provider proof.

New bridge has no installed schedule, keepalive, collection, cleanup or dashboard
proxy. These are NOT dropped or falsely called migrated: collector timing is
runtime-track owned; cleanup staysheld pending backup proof+deletion approval;
public dashboard is existing read-only preview. Old script/props/triggers remain
untouched. Header route mounting is a future explicit source unit, stilloff.

Activation decisions remain: marking fetched vs displayed (required input, no
default); repeated-critical suppression; empty low-score digest skip/events-only
send; stabletie-break; sender/recipient/scope/interval; actual transaction/schema
and canonicalISOdate/URL checks. Source dates/URL restrictions may refuse real
records. Save135 archive128cap failsclosed, not unlimited archive migration.

## Scheduling proposal contract

schedule_plan requires explicit allfields, valid timezone, times OR supported
hourly interval, critical minutes or0off, weeklyday/time orbothemptyoff. No live
schedule inferred from original defaults or old memory. Proposed handler names
mailV1Digest/mailV1Critical/mailV1Weekly are namespace design only; wrappers and
installer not implemented. Apps Script walltimes are approximate, not exact.
Plan cannot enable mail or collection. A later installer must inspect current
project triggers/quota/timezone, only replace its exact managed handlers, and
never call original setupTriggers. Preserve every other trigger. Do not install
parallel old/new mail schedules without explicit cutover/duplicate prevention.

## Receipt recovery proposals

- Serveracknowledged + same receipt/hash/attempt: propose pendingclear only after
  current readback. A failed ack response must not resend. Clearing execution
  requires checked bridge/serverstate, not this supplied snapshot alone.
- Serverstarted + bridgesend_returned + samebinding: propose ackonly, never send.
- Serverprepared + bridgepending/bound + samehash: propose resume SAME nonce
  through normal one-shot claim. A newnonce is never automatically allowed.
- Bridgeclaiming/sending without authoritative completedack: holdmanual. Even
  serverprepared does not prove the send never happened across unknown commit/
  response outcomes. No leaseexpiry, missingrow or elapsedtime frees the hold.
- Bindingconflict: hold. Delivered/provider-verified claims are rejected.

Actual manual reconciliation implementation is still absent. Never erase a
pending record or unlock activekind to improve uptime without checked send
outcome. Future operator recovery needs authenticated explicit intent, current
fencing and append-only audit evidence, scoped to exact receipt+attempt, not an
arbitrary markIDs endpoint. Retention must never TTL-delete unresolved receipt
or activecontrol. Roles/index/TTL execution remains a separate reviewed unit.

## Test scope

12pure tests cover schedule grammar, exact snapshotbindings, ackonly/clear/resume
proposals, unknown holds and no execution authority. They do not prove Apps
Script quota/clock/service behavior, realMongo state or successful live delivery.


## Source-only companion 180
Code.gs now validates the entire schedule before changes, stages replacements
within the 20/user/script quota, and removes only known managed handler names.
Unrelated handlers stay. Staging or deletion failure needs manual inspection;
there is no transactional rollback guarantee. nearMinute delivery is approximate.
Held HTTP 403 and other non-200 responses are fixed-label errors, not success.
No retry is added. A failed acknowledgement after send has unknown receipt state,
not permission to send again. The companion remains uninstalled here; legacy
mail routes stay held and no real Google triggers/properties are changed.

<!-- END-ORIGINAL-DOC -->


<a id="doc-047"></a>

### Reference: `feature_related_prep/ADJUDICATION-DESIGN.md`

<!-- ORIGINAL-DOC {"bytes":2907,"path":"feature_related_prep/ADJUDICATION-DESIGN.md","sha256":"ba9d85e6fdc5d4fe3adcb432b1a20611ff3e720cc8c9a1b1c3d1e9b4e05366e9"} -->
# Hybrid live adjudication decision preparation

Copyright (c) 2026 Push. All rights reserved.

Source-only design and fixture evaluator, not a connector or mounted feature.
Existing hybrid.plan stays unchanged: keyword product/code+country accept,
no-product reject, uncertain held; supplied AI threshold0.8 remains uncalibrated.

calibration.evaluate accepts explicit threshold candidates and closed hash-bound
caller-labeled examples. It reports confusion counts, decided coverage, held
positives/negatives, precision, overall-positive recall (held positives count as
not retrieved), decided-only accuracy, and positives rejected by the keyword
stage. Missing denominator yields null, not invented zero/100% accuracy. It
never picks a threshold or changes config. Labels and model scores are supplied,
unverified data. Synthetic tests prove calculation behavior, not real accuracy.

Before a live path:
- Have the owner confirm exact provider(s), permitted prompt fields, sender of
  provider requests, audience/disclosure boundaries, saved key scope and limits.
- Check current official model endpoints, free quota, rate limits and retention
  terms. Groq/Gemini/Mistral are allowed choices, not already-approved live
  disclosure. No API/model/free-tier claims are made by this design.
- Build a reviewed transport with no paid fallback, fixed request/output size,
  wall-clock and quota caps, strict JSON schema, no tools/link retrieval. Timeout,
 429, malformed response or quota exhaustion keep item held with explicit reason.
- Treat article/title/summary as untrusted data, never execution instructions.
  Review returned JSON as data. Never allow a result to pick tools, recipients,
  destinations, schedules or expose user/private context.
- Bind results to context and article hashes, provider/model/config version and
  actual transport outcome. Preserve provider_verified=false meaning no factual
  correctness/recipient delivery guarantee. Separate transport attribution from
  model correctness. AI-related is a suggestion, not tariff/legal verification.
- Use owner-reviewed labeled examples representative of actual products,
  countries, dates and sources, including keyword rejects and negatives. A
  confidence value is self-reported, not a probability calibrated by these tests.
  Record sample size, selection bias and false-positive/recall tradeoff before
  recommending a threshold. Keep a held state; never force a binary choice.
- Decide whether to widen recall: country-only/no-product now skips AI, so a
  threshold change cannot recover those missed positives. Synonyms/full-text
  matching is a separate source/privacy/budget decision. No automatic expansion.

Mounting belongs to an explicit later reviewed seam with disclosure and quota
permission; this increment adds no provider call, prompt export, routing, DB,
client, callback, environment, stored keys or activation.

<!-- END-ORIGINAL-DOC -->


<a id="doc-048"></a>

### Reference: `integration/API-V1-187.md`

<!-- ORIGINAL-DOC {"bytes":1203,"path":"integration/API-V1-187.md","sha256":"09d8476aa78eb79521c46998aa644a1eb53b31680bec1c12cfe6db05a57902a0"} -->
# Read API v1 compatibility aliases

Explicit GET/HEAD aliases: news,news-page,news-stats,dashboard-signals,
dashboard-snapshots,sample-volume,critical-stories,source-health,country-page,
country-signals,map-data,story-groups,news-export.csv under/api/v1/.
Same handler/auth/payload/security headers as unversioned paths. No redirects,
query rewriting or migration. Existing URLs/frontend stay unchanged. This is a
versioned entrypoint contract, not a schema change or a claim of full controller
architecture. Route policies are still applied to actual request path.

Only corresponding already-approved public reads enter public allowlist. No
private tariff/export/workspace/health/login/digest/send/write aliases. POSTs
not added. Multiuser/merged account outer policies still deny new aliases until
separately reviewed; no new account disclosure grant. V1 news-page503while185
adapterOFF, same validation409/429/503 semantics when wired, no liveactivation.
No count/snapshot/efficiency promise added. StatsCSV still sample100, scroll gates
unchanged. Full mutable-reader tokens remain query-bound not route-bound, allowing
same authorized continuation through either spelling without new privileges.

<!-- END-ORIGINAL-DOC -->


<a id="doc-049"></a>

### Reference: `integration/ARTICLE_ARCHIVE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3432,"path":"integration/ARTICLE_ARCHIVE_LIMITS.md","sha256":"f449ed2efdcbbca2a76ec5e3aa920edb538486b7e5c86f6dba460dd1d9cc9994"} -->
# Private supplied supported-schema archive, not durable backup

This module only packs, unpacks and retrieves supplied records in memory. It
has no source reads, files, routes, writes, uploads, delivery, deletes or marks.
The original RSS and GNews save paths store summary[:300], not full body/raw
text. MongoDB adds _id and created_at ISO text; later updates add Telegram
references and emailed bool. No full-history or actual Atlas-schema claim.
BRICS has a different SQLite contract and is not supported here.

The schema is synthetic_supported_geo_storage_fields_v1. Source excerpts with
line numbers and full-file SHA256 are in the review evidence. They support
field/type selection, not a verified live collection or source completeness.
Unknown fields and any nested containers under producer fields are refused.
Text fields must be exact str (up to 1M characters before aggregate bounds),
score finite exact int/float within +/-2^53, corroboration exact int in the
same range, emailed exact bool, telegram_message_id int64 or None, and _id
ObjectId or nonempty string up to 100 characters. These are bounded supplied
fixture types, not a claim that every value follows the original producers'
semantic ranges. Text can contain private content. This rejects unknown
private fields, not secrets typed into a supported text field.

The independent tagged-array codec supports builtin bool/int64/finite float,
str/bytes/ObjectId/null/dict/list/BSON-like UTC millisecond datetime. That
broader codec is NOT the producer-field exclusion boundary. Codec depth 8,
20k nodes, dict 30/list 100/string or bytes 1M; no subclasses or hooks. BSON
fixed-offset datetime normalizes to UTC, naive assumes UTC; original offset
and naive flags not preserved. ISO producer text remains exact. Non-ms
microseconds refused. Missing fields and explicit supported null preserved.

100 records and 2MiB final encoded archive. Capture checks a conservative
aggregate budget during each field and each character BEFORE tagged copies.
It adds 192 + key length per field and at least six bytes per character,
reserving 4096 bytes for the envelope. This covers UTF-8, JSON escaping, tags,
identity manifest and scalar overhead without a large UTF-8 temporary. It
stops on first overrun and shares a 20k encoding node cap across records.
It may refuse archives below the final byte cap. Final bytes also checked.
No base64/bytes values enter producer capture. Decoder checks bytes before
JSON parsing, then validates all records and manifest before returning any.
The JSON parser can allocate within the 2MiB input limit before typed checks;
there is no hard parser CPU/allocation guarantee.

Order and typed identity preserved. Exact duplicate rows kept; conflicting
same identity refused; duplicate identity retrieval is ambiguous and refused.
Closed version/schema/scope/count/manifest/ordered records and UTC creation
stamp covered by SHA256. Hash is integrity, not authentication or source
proof. Only supplied_subset or supplied_truncated_subset; neither means full
history. Private IDs/URLs/content remain private archive bytes. No public
news/CSV/mail/preview wiring. Pack is not durable storage or cleanup approval.

V3: 10 focused tests pass, including nested private fields, multibyte and
many large records, stop-before-tag-copy, typed int64 Telegram ID, separate
codec roundtrips, duplicates, aliasing and corruption. No live DB operation.

<!-- END-ORIGINAL-DOC -->


<a id="doc-050"></a>

### Reference: `integration/BRICS_STREAM_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":6961,"path":"integration/BRICS_STREAM_LIMITS.md","sha256":"61cebc64f4326d9d21772104280b8656a4ac2fd8b340601fe4297a099efc7ac9"} -->
# Original BRICS stream contract preview

Original source video.py supports YAML-backed load/add/remove, case-insensitive duplicate-name detection and removal, country fallback Custom, channel/video enrichment. Its6+ loose ID grammar accepts arbitrary strings; preview uses exact11-character video and UC+22 channel IDs. Input watch/short/live/embed formats retained (HTTPS only, no tracking or fragments). Labels bounded80/control characters rejected; max20 fixture rows. No automatic availability claim.

Preview keeps core add/remove behavior with the differences below on /api/brics/streams (namespaced to avoid collision with My channels). New fixture-only in-memory store replaces original disk writes, process lock retained, no YAML/DB mutation. Default store absent yields503, not a silently empty configured list. Add/delete private access+same-origin guard; state fixture_only/persistencefalse. Country preserved. Original BRICS configured YAML remains preserved, not yet supplied to preview. No claim of cross-user or cross-device persistence.

My channels remains separate browser-local settings with Republic compulsory. BRICS management page has no auto-created embeds and no effect on its players. Dormant news_refresh controller carries original60s cadence, injected fake timer tests only; default off, no caller/production timer wired. Production polling approval and durable source/persistence design remain open. Manual news refresh already affects news only.

Contract differences: GET is a state/persistence envelope rather than original bare list; POST accepts JSON only (original also form); strict HTTPS and exact11/UC+22 identifiers; youtube-nocookie embeds instead of youtube.com; max20 vs original no bound; fixture-only RAM replaces YAML persistence. DELETE collection with JSON name replaces original path-name endpoint so slash/percent/query/hash/unicode/dot-segment names round-trip safely. One casefold key used for duplicate/load/removal. Canonical allowed_origin is required for supplied store and is not inferred from Host; production host filtering/private authorization and trusted reverse-proxy configuration remain operator requirements (do not trust arbitrary forwarded headers). Fixture loopback origin is test-only. Labels/country validated scalars; None/empty/whitespace country maps to Custom; irrelevant channel_id dropped from video rows.

Request boundary: exact application/json,0/missing/>4096 Content-Length rejected413 before parse, explicit read4097 max, observed/declared mismatch400; duplicate JSON keys rejected400. Does not make arbitrary reverse-proxy framing trustworthy; production proxy must reject ambiguous transfer framing.

Supplied original configuration parser increment: stream_config.configured_streams accepts explicit UTF-8 bytes/aware observation time only, no file path/discovery/config imports or writes. Original preserved YAML currently holds five video rows, all pass existing strict identifier grammar; test verifies RepublicID only as configured source, not availability. RAM editing on a copy never changes parsed configuration/source bytes. DashboardSnapshots still applies exact reviewed YouTube host/link/display gate.

YAML input16KB,1000tokens, depth4,20rows, scalar200chars; aliases/anchors/explicit tags/directives/non-string keys/duplicates/multiple documents/unknown fields fail closed. SafeLoader subclass with strict map construction only. Empty streams list verified empty; malformed/missing data unavailable/error, not silent defaults. Captured hash identifies supplied bytes, observed_at identifies capture, not actual stream status. PyYAML required in configured environment. No default loader wired to HTTP or production readers, no disk persistence; original file remains intact. Real repository source freshness and configured path/identity still require explicit source-grounded composition, no assumption from copied YAML.

V2 YAML depth counts parser collection events (mapping/sequence starts including indentless block sequences), before object construction, with1000event cap. The supplied original five rows are a fidelity test fixture, not an exact-five whitelist: accepted config may contain0..20 valid rows. Extreme fixed-offset UTC conversion overflow becomes coarse StreamConfigError. No broadened source/persistence/availability claim.

Residual parser bound:200character field checks run after SafeLoader object construction; total16KB input and token/event/depth caps bound that pre-validation work. This is not a200character parser-allocation ceiling. Review covers the offline parser, not approval to wire actual configured files or writes.

Explicit fixture composition create_stream_fixture accepts supplied bytes/observation, private authorization callback and canonical origin. No path reads or default production loader. Management uses a mutable RAM copy, while original dashboard panel remains immutable captured configuration with capture time. Management edits are not reflected in that captured panel or live/My channels players: deliberate separation to avoid pretending edits updated original source. UI says fixture-only, no original YAML/database changes; no auto embed or availability lookup. Startup with malformed bytes fails instead of substituting empty state. SourceSHA internal app config identifies capture; no provider tokens/paths/credentials required.

Three focused composition tests verify private gate, original five rows, RAM edits/source-file/captured panel unchanged, origin enforcement and health effects still off. Chromium390px fixture add/delete copied list passes no outbound/errors/overflow, actual pixels inspected. Increment repro commands in existing repo: python -m unittest tests.test_stream_fixture_app and python tests/browser_stream_config.py. Requires original root YAML fixture, existing news_api dependencies/asset tree and PyYAML/Flask/Playwright/Chromium. Not production wiring approval or self-contained archive.

Fixture composition auth hardening: host/scheme exact canonical-origin check and authorize must return literal True; raises/non-bool truthy fail closed403. Wrong/null/trailing-slash/casevariant Origin and spoofed Host regressions pass. Capture time may be historical (no freshness claim), but future beyond5minutes rejected. Source identity test compares app capture hash to exact passed-in byte hash, while mutations leave source file and captured panel unchanged. Parser errors identify failing row ordinal only, never supplied row values. Management uses RAM only; YAML-backed durable add/delete behavior remains missing rather than silently replaced as complete.

UI badges now consistently occupy their own grid row, links themed, add fields carry hints, status explicitly aria-live polite. Real mobile pixels inspected after change, no overflow/outbound/errors. Fixture-only edits do not sync to original YAML, source snapshot or My channels. No production persistence claim.

<!-- END-ORIGINAL-DOC -->


<a id="doc-051"></a>

### Reference: `integration/BROKER211.md`

<!-- ORIGINAL-DOC {"bytes":4380,"path":"integration/BROKER211.md","sha256":"f509f107f48c036cad0789a57dcd2610bac8fb58771a567051220d4ef15ec343"} -->
# 211: two unselected broker body parsers

This closes the body parser for finder198 + native201 only, not every
historical broker parser and not Finder-proxy-complete. No live effect.
The third copy of the old parser remains in replay199_broker, behavior unchanged:
malformed/extra-field JSON gives 409 there. It is synthetic-only/unselected;
if ever selected for use it needs its own reviewed unit first.

Both changed handlers call the same pure broker_json211.parse after existing
account, session, Origin and CSRF guards. No auth change. Direct non-POST or
unknown route returns 404 without body reads. The existing auth wrapper rejects
broker query strings with 403 and unsupported methods with 405. Standalone
parser query rejection is 400, defense in depth for direct calls only.

Raw Content-Type must be application/json (case insensitive, surrounding space
accepted) with at most one charset=utf-8 parameter (unquoted, case insensitive).
No other parameters, JSON suffix media, or declared transfer encoding accepted.
Raw Content-Length must be positive ASCII decimal digits, no leading zeros,
whitespace or signs; bounded before integer conversion. Missing/empty is 411.
Strict UTF-8 without BOM, duplicate decoded keys, non-finite values, top-level
non-objects, JSON decode/value/Unicode/recursion errors are refused with 400.
Duplicate escape-equivalent keys are also refused. No raw body is echoed.
Unexpected internal errors remain generic 503, not malformed-input errors.

Nonce is exactly the engine's 20..80 ASCII letters/digits/underscore/hyphen.
Model identifier is exactly its 1..100 ASCII letters/digits/dot/underscore/slash/
hyphen rule. Gemini-specific slash/catalog admission remains in the engine.
Only gemini/groq/mistral and fixed server-built payloads exist. The model catalog
is still empty. Ships port is a 1..100 safe string; membership stays engine-only.
Prompt is 1..8000 Python Unicode code points, not UTF-16 units; TAB/LF/CR allowed,
other C0, DEL/C1 controls and all surrogates refused. Provider payloads,
URLs, headers, messages and tools are never caller-supplied.

The raw cap stays 16384 bytes and is checked before parsing. It applies before
8000-code-point prompt admission: 8000 ASCII characters fit, but a three-byte
UTF-8 prompt reaches the cap around 5400 characters (exactly depending on the
other fields/spacing). JSON Unicode escapes use six raw bytes per BMP character.
Astral characters are one code point and four UTF-8 bytes. Engine-generated
payloads retain the separate existing MAX_REQUEST_BYTES limit and held409 path.

## Deliberate behavior changes

- Media mismatch remains 415 json_required; stricter raw parameter checks now
  reject media parameters previously discarded by req.mimetype.
- Declared/raw oversize remains 413 request_too_large.
- Missing/empty length changes 413 request_too_large to 411 length_required.
- Zero, signed, spaced, leading-zero or invalid length becomes 400 invalid_request
  (zero formerly413; Werkzeug formerly normalized some noncanonical forms).
- Short read remains 400 invalid_request. Observable terminated extra bytes
  become 400; over-cap terminated bytes become 413.
- Malformed/non-conforming/extra-field JSON changes 409 broker_request_held to
  400 invalid_request; invalid nonce/model shape also moves engine-held409 to400.
- Catalog, port admission, budget, replay and transport ValueError paths stay
  409 broker_request_held. Unexpected failures stay 503 broker_unavailable.
- Existing test expectations changed only: test_finder198c extra-url409->400;
  test_native201b extra-url409->400. test_finder198a/replay199ca/replay199cc
  behavior is unchanged. All catalog/admission/replay expectations stay409.

## Limits and verification

WSGI terminated streams permit bounded extra-byte checks. Nonterminated streams
are Content-Length limited; extra bytes and repeated wire Content-Length fields
may be unobservable. This is NOT HTTP-smuggling protection. No runtime server,
production mount, UI, env, account provisioning, secret, budget/retry/refund,
receipt, provider catalog or live transport changes. Native201c remains held.
Tests compare actual engine nonce/model vectors, both handler payloads and safe
errors, raw cap/multibyte/escape interplay, framing, hostile JSON, and auth-order
stream/get_data/get_json spies. Archive199's old extra-field409 is pinned.

<!-- END-ORIGINAL-DOC -->


<a id="doc-052"></a>

### Reference: `integration/COLLECTION_PREPARE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1362,"path":"integration/COLLECTION_PREPARE_LIMITS.md","sha256":"136661a40c3f662cca44b87fa2ccb5f2f0c94a725e01574de4271495c2d66331"} -->
# Offline collection processing seam

This seam accepts ordinary plain deserialized JSON-like candidate dictionaries.
It is not an interface for arbitrary Python objects: deep copying such objects
can run their custom code. The 1000-row bound does not bound individual string
length or fuzzy-comparison CPU/memory use. Keep fixtures reasonably sized.

Geo classification precedes dedupe and category filtering. The original stored
summary preview is limited to 300 characters. BRICS dedupe precedes category
classification/filtering and BRICS relevance filtering. BRICS processing rules
are a copied snapshot of preserved originals and can drift from future changes.

This establishes processing-order/rule parity against archived originals, not
live production parity or a full collector migration. Geo's unused dateutil
parse_date helper is not called by this adapter. For filesystem-free probes,
run with -B/PYTHONDONTWRITEBYTECODE=1 to avoid Python bytecode-cache writes.

Inputs are copied, including supplied identity/time fields. No collection time,
writer identity or stored status is invented. Fetching, store connections,
inserted-count versus inserted-item semantics, URL IDs, timestamp assignment,
duplicate/storage-error handling, alerts and Telegram backups remain outside
this seam. No API, scheduler, runtime, fetching or persistence is enabled.

<!-- END-ORIGINAL-DOC -->


<a id="doc-053"></a>

### Reference: `integration/COLLECTOR197A.md`

<!-- ORIGINAL-DOC {"bytes":1911,"path":"integration/COLLECTOR197A.md","sha256":"7ee36ad80ab3b16f5ec3772893ad756a988ed4018abfcea77db695a6e1556181"} -->
# 197a: injected durable collector orchestration

Source-only, unmounted and default OFF. No production facade or entry change.
GEO_WRITER_MONGODB_URI is a new contract name, not a deployed writer connection.
Never falls back to GEO_MONGODB_URI or MONGODB_URI. Fixed geo_intel.articles,
geo_intel.collector_jobs197 and geo_intel.collector_checkpoints197 mappings.
Actual collection identity and live role/index/TTL evidence are 197b obligations;
this unit accepts assertions, not proof. Initialization/provisioning is NOT run.

One accepted→running CAS winner enters fetch. Durable majority+journal ledger
and checkpoint handles are required. Immutable capture/checkpoint is stored at
running before prepare. Only prepare_complete→write_started CAS permits the
injected GeoArticleWriter. Partial, unknown, malformed or unacknowledged writes
remain locked for reconciliation. Replays never resume fetch/write. Expired
leases never transfer; retained 64-job history fails closed when full. No
automatic retries, takeover, article TTL, index creation, archive or recovery.

90-second whole-cycle contract is below 120-second lease. Per-feed bound is
25 seconds. Runtime guards reject overrun before/after injected fetch and
before write. They cannot kill a blocked callback and are NOT hard supervision.
197b must provide hard wall supervision/kill/reap, fixed catalog and network
header parity, real Mongo identity/role/index/no-TTL probes, bounded driver
write timing, authenticated owner POST /api/collect with durable request ID,
client lifecycle and production wiring. No live activation without owner OK.

Checkpoint capture remains at most 2 MiB/20,000 nodes/1000 candidates. Network
aggregate ≤4 MiB and its process input/output accounting belong to 197b.
No mail, Telegram, fulltext/GNews, import-time timers or old collector changes.
The currently held public read application continues unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-054"></a>

### Reference: `integration/COLLECTOR197B.md`

<!-- ORIGINAL-DOC {"bytes":3360,"path":"integration/COLLECTOR197B.md","sha256":"1595adf1efeb9677a827445a6fb3e577bc6b37a09805e4e8f2d71b3382d75291"} -->
# 197b composition candidate, not live activation

Mongo preflight executes read-only connectionStatus(showPrivileges), hello and
bounded exact collection listIndexes; it creates no clients, collections,
indexes or ledger documents. Requires one authenticated principal, writable
replica set primary, exact collection grants: articles find/listIndexes/insert,
jobs find/listIndexes/update, checkpoints find/listIndexes/update/insert. All global, database-wide and
extra grants refuse. It uses majority read and majority+journal writes.
Rejects any TTL on any of the three collections and requires a full unique
url:1 index, no partial/sparse/non-simple collation. Existing geo108 ledger
fingerprint/schema must match. These are observed capabilities, not permission.

Sources:
https://www.mongodb.com/docs/manual/reference/command/connectionStatus/
https://www.mongodb.com/docs/manual/core/index-partial/
https://www.mongodb.com/docs/manual/reference/read-concern-majority/

Parallel-four fixed 25-feed AST catalog, 90-second whole-cycle contract,
70-second fetch cutoff with explicit failed/unstarted sources. Each body read
is capped at 1 MiB before reading; JSON-line byte telemetry includes refused
feeds. Conservative 1 MiB launch reservations fit the 26 MiB cycle ceiling.
Wire accounting is response BODY bytes, not TLS/header/framing overhead.
Malformed telemetry/cap errors refuse a source; incomplete result envelopes
never yield candidates. Decoded aggregate also at most 26 MiB; candidate
capture remains 2 MiB/1000 rows. REQUEST_TIMEOUT follows original installation
profile; combined per-feed fetch/parse/selection is at most 25 seconds.

Every feed is in a bwrap PID namespace with die-with-parent and no new session;
all supervisors stay in coordinator process group. Individual timeout kills
the namespace supervisor; kernel kills descendants. Wrapper SIGTERM/grace then
SIGKILL group also kills every namespace. Actual fixture process cutoff and
forced coordinator kill tests inspect no remaining unique host process marker.
Fixed parser remains in separate network-less bwrap namespace, no fallback.
Four 256 MiB child limits are not a 512 MiB deployment capacity proof. Actual
Render kernel/bwrap and free capacity must be independently verified first.

Explicit owner-only default-OFF factory is unselected. No production facade
or live switch is changed. Enabled construction requires injected runtime
preflight, then read-only Mongo preflight; source assertions are not owner
permission or actual Render proof. Routes authenticate Bearer before ledger;
no browser Origin/query allowed, strict nonce/timestamp JSON. No import-time
work, timers, index/collection/ledger provisioning, mail or old collector stop.
Source status is response-only here. Durable coverage and production mounting
are deliberately deferred to 197c; this is NOT live-ready merged collection.

Conservative collation gate requires explicit locale:simple index metadata.
Older servers may omit that field for simple indexes; missing field refuses
rather than pretending it proves collation. Source evidence:
https://jira.mongodb.org/browse/SERVER-92900
https://github.com/mongodb/mongo-python-driver/pull/2761
No actual Atlas/server durability, role, deployment or free quota was tested.
Configured majority+journal concern is not a successful durable-write proof.


<!-- END-ORIGINAL-DOC -->


<a id="doc-055"></a>

### Reference: `integration/COLLECTOR197C.md`

<!-- ORIGINAL-DOC {"bytes":2236,"path":"integration/COLLECTOR197C.md","sha256":"defbc584191a052f11c1bd365cb04bfa24d8082d4ef3a35b691815d60d8c705e"} -->
# 197c: durable source coverage and default-OFF production composition

Version-2 checkpoints atomically store original candidates/categories/threshold
and full pinned 25-source status coverage/catalog fingerprint. Typed input hash
is unchanged; coverage has an independent domain-separated typed hash bound to
job and fence. Capture is bounded before copy/hash. Immutable upsert/readback,
BSON roundtrip and adapter re-instantiation retain exact coverage. Version 1 is
unchanged and still separate. Same existing checkpoint collection, no new
collection/index/provisioning. Unknown/partial writes remain locked; replay
reads durable coverage, never fetches/writes. Missing/corrupt coverage refuses.

Production entry mounts only /api/collect and /api/collect/status/ through WSGI
dispatch so the public read app's GET-only authorization is not broadened.
Public GET, health, home and read credential remain unchanged. Owner Bearer,
no-Origin/query, exact nonce/timestamp JSON checks remain. OFF delegates the
original environment unchanged; no collector client/provider is invoked.

TRUE requires a real injected RuntimeEvidence provider BEFORE any client.
create_app has no provider by default, so TRUE fails closed. No boolean env
shortcut, default-ready or provider implementation. Record validates pinned
catalog, bounded host/activation source references, observed/expiry window at
most one hour, PID namespace and nested parser bwrap proofs, capacity proof,
WSGI timeout strictly over 120 seconds and conservative 1536 MiB available
memory. Record/interface validates structure, NOT owner authority or real host
claims. The actual host provider and source-grounded activation evidence are
197d. No live Render/Atlas probes or writes were performed in this unit.

Authorized requests re-fetch/revalidate provider evidence before ledger access;
expired/missing proof refuses without collection. Public reads still work.
If real Render capacity cannot meet this contract, reduce worker/parser caps
only under a separately reviewed proposal and proof. Never quietly lower caps.

No live configuration, collector start, old collector stop, mail, Telegram,
index/TTL creation, workflow or other repository changes. Source remains OFF.

<!-- END-ORIGINAL-DOC -->


<a id="doc-056"></a>

### Reference: `integration/COLLECTOR197EA.md`

<!-- ORIGINAL-DOC {"bytes":5279,"path":"integration/COLLECTOR197EA.md","sha256":"008e035f533bd1c51faf145b19117d9eab71903809eeada23d950549e552c425"} -->
# 197e-a job source and owner diagnostic

Default OFF. No running scheduler, production provider, activation, account or
Atlas changes. This is a one-shot injected composition and read-only/local
runtime preflight, not an unattended collector. Web RuntimeEvidence unchanged.

Design allocation: four feed workers256MiB + four parsers256MiB =2048MiB AS;
coordinator256MiB; parent512MiB; kernel/bwrap/overhead allocation256MiB; total
3072MiB. These are design caps, not measured RSS or a proof that overhead fits.
Parent/coordinator get actual RLIMIT_AS before application imports in their
job launch paths. All children inherit parent bounds until tighter limits.
Feed/parser limits unchanged. 90s cycle,70s fetch cutoff,25s feeds, four active
sources unchanged; partial failed/unstarted coverage persists honestly.

Enabled composition requires exact injected JobRuntimeEvidence (no WSGI field),
fresh<=120s, observed available>=3072MiB, protected exclusive current cgroup-v2
memory.max3072MiB, swap.max0, oom.group1,512MiB parent and256MiB coordinator,
actual PID+nested isolation, source pins and independently verified aggregate
guard. The record's activation reference is not authority itself. A production
provider must bind it to original scoped owner approval. None exists here.
No environment READY flag bypass; direct CLI only accepts --diagnose. Unsupported
host returns supported=false; never opens Atlas from diagnostics.

Same dedicated writer URI, exact Atlas articles/jobs/checkpoints mappings,
majority/journal, pre-existing roles/indexes/ledger, durable CAS and immutable
coverage, no replay/takeover, uncertain writes locked. History64 remains a
fail-closed limit. No purge/reset/rotation in this unit. Long-term cadence needs
197e-b archival/status/coverage contract. No ten-minute delivery guarantee.

## Owner-operated diagnostic after source landing

This runs only synthetic allocations and local checks, with NO Atlas secrets,
production activation or collector fetch/write. It creates disposable fixture
cgroups on the GitHub runner, then removes them. Privileged setup is explicit;
no privileged setup was run during source preparation. Never run on Render.

Owner pastes the workflow below via GitHub UI. We never push .github files.
Replace REVIEWED_SOURCE_SHA with the independently reviewed landed source SHA,
not a moving branch. The checkout action v4 tag was resolved via git ls-remote
at source preparation to11d5960a326750d5838078e36cf38b85af677262. No other actions.
No schedule, pull_request trigger, production secret or persistent checkout creds.
Requires public dummypush1-ui/geo-intel-brief on standard Ubuntu VM (not slim).
The workflow must NOT be enabled or submitted automatically by this unit.

```yaml
name: Collector197e read-only diagnostic
on:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  diagnostic:
    if: github.repository == 'dummypush1-ui/geo-intel-brief' && github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: REVIEWED_SOURCE_SHA
          persist-credentials: false
      - name: Install bounded diagnostic dependencies
        shell: bash
        run: |
          set -euo pipefail
          sudo -n apt-get update
          sudo -n apt-get install -y bubblewrap
          python3 -m venv .collector-job-env
          .collector-job-env/bin/python -m pip install --require-hashes -r requirements-future-deploy.lock
      - name: Disposable aggregate guard diagnostics only
        shell: bash
        run: |
          set -euo pipefail
          sudo -n /bin/bash integration/collector197_job_diagnostic.sh --diagnose
```

Unpinned Ubuntu/apt host tooling is not an immutable application lock; actual
kernel/bwrap/isolation behavior must be observed. Dependency lock hashes remain
mandatory and missing wheel/hash refuses. Pinning source and action protects
reviewed code identity, not arbitrary runner/image changes. No silent fallback.
If controller delegation, cgroup events/peak, sudo, isolation or dependencies
are unavailable, diagnostic fails/returns unsupported. Send only the diagnostic
JSON and synthetic peak/events from run logs, no secrets. The diagnostic does
not supply a production runtime provider and never enables collector code.

## Validation scope

Locally proven: parent/coordinator allocation refusal, closed job record/default
OFF/no provider, real local unsupported facts, existing coordinator isolation
regressions. Mocked protected cgroup validation tests are source tests only.
Aggregate kernel OOM-group and synthetic overhead proof DEFERRED to the owner
GitHub diagnostic because current test host cgroup is shared/read-only. Even a
successful synthetic fixture is not actual workload peak/overhead evidence;
production stays blocked until real guard and adversarial/workload evidence.

Sources:
https://docs.github.com/en/actions/reference/runners/github-hosted-runners
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
``GitHub public standard Ubuntu4CPU/16GB and passwordlesssudo`` is capability,
not user approval; scheduling can delay/drop, public idle workflows disable.

<!-- END-ORIGINAL-DOC -->


<a id="doc-057"></a>

### Reference: `integration/COLLECTOR197EBA.md`

<!-- ORIGINAL-DOC {"bytes":4135,"path":"integration/COLLECTOR197EBA.md","sha256":"6b245b57c9c4eaf6a4b91e7818881aa9651baacba91a1fff6168fae2972de5ff"} -->
# 197e-b-a complete retained collector snapshot

Unselected, read-only source adapter. No client, environment, HTTP route, storage destination, schedule, pruning, reset or recovery mutation. Captures the exact ledger and every retained job's referenced checkpoint, including typed input and v2 source coverage. V1 checkpoints are supported without guessing v2 coverage. Missing checkpoints are permitted only for accepted/running/failed-before-write, explicitly recorded as absent; all later phases require the complete validated checkpoint. Full retained key/fence/counts/lease/revision identity survives. Original raw nonce is not stored by this ledger and cannot be reconstructed: its exact existing derived key survives, not an invented raw nonce.

All retained jobs is not lifetime history. Two matching reads detect visible ledger races, not a transaction or proof that external workers stopped. Owner must disable collectors, confirm no executing job/process/write, and authorize the actual read destination and scope before any real capture. Active or uncertain jobs can be snapshotted but stay held. Snapshot status classifies recorded terminal vs owner-review-held, never delivery, settlement or safe replay. It can inspect offline retained status without querying live accounts.

Pack validates source fields, exact typed checkpoint hash/coverage/fence, full job linkage, bounded plain values and 16MiB conservative aggregate budget before deep copying/serialization. It validates the actual serialized bytes by readback before returning. Missing/corrupt/unbounded records or visible revision changes fail closed, no partial success. Large histories may exceed the cap: stop and prepare a separately reviewed chunked format, never truncate. Hashes accompany full content; they do not replace it. No filesystem or upload action is built in. Archive contains article input/private context: private encrypted destination and retention/access rules require a separate scoped owner decision.

## Owner-operated runbook, not live authorization

1. Keep collector OFF. Preserve current ledger, checkpoints, article write evidence and all other outboxes/journals/backups. Confirm quiescence independently, including old collectors. Do not infer it from an expired lease or endpoint error.
2. Under a separately approved read scope, capture into a private destination, verify complete byte readback and exact snapshot validation, retain original source untouched. Record source revision/fence, intended destination, time and owner approval outside the data artifact. Do not include credentials.
3. For active accepted/running/fetch/prepare states, verify process termination and absence of any write-start transition from authoritative evidence. This snapshot does not settle them. For write_started/uncertain_after_write, compare immutable checkpoint candidates, exact prepared documents/URLs, writer acknowledgements and live article state using approved reads. Existing article presence alone does not prove which attempt inserted it; hashes alone do not prove recoverability. Keep ambiguous cases held. Never replay writes because a lease expired or acknowledgement was lost.
4. Snapshot completed and failed-before-write histories with their available full checkpoints. Preserve missing pre-write checkpoints as explicitly absent, not empty successful fetch. Completed means recorded writer acknowledgement, not all feeds healthy, downstream email delivery, or backup completion.
5. No pruning, active clear, fence reset, nonce reuse or capacity claim. The 64-entry cap remains. A later schema-aware immutable replay archive lookup and atomic rollover protocol must preserve old-key lookup before any capacity release or sustained cadence. Both submit and status must consult the archive; archived identity must not disappear. A private snapshot alone is not that protocol.
6. Any actual reconciliation transition, archive provisioning, role/schema change, old-collector stop or live switch needs its own source-grounded approval and reviewed implementation. Unknown stays held. No operator copy-paste reset script is supplied.

<!-- END-ORIGINAL-DOC -->


<a id="doc-058"></a>

### Reference: `integration/COLLECTOR_MAIL_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2429,"path":"integration/COLLECTOR_MAIL_FIXTURE_LIMITS.md","sha256":"6e2d181d296dcfde55c6e66d148a036dfc0018dee458280732435208e8206cfd"} -->
# Supplied collector and mail preparation composition

Private offline composition only. No fetch, database, routes, env activation,
callbacks, scheduler, Apps Script execution, sends or marks. Original files
are unchanged. Source-pinned RSS/classifier/dedupe and renderer/dependencies
checked before seam imports/AST execution. Configured full repository required.
Trusted pinned source, not hostile-code isolation; runtime monkeypatch or file
replacement by a malicious process is not a security boundary this can enforce.

Both supplied inputs and config are snapshotted and validated before either
seam. Exact inert closed scalar fields; candidate IDs/emailed/Telegram/extras
refused, queue IDs exact ObjectId, malformed sent rows also refused. Separate
100-row limits, shared 5000 nodes and incremental 1MiB UTF-8 text budget, text
16000 chars each, no nested containers. Fixed timezone and post-UTC date range
1970..2100. Immutable strings reused; mutable containers/ObjectIds copied.
These limits stop large copies; existing renderer/parser CPU not hard-bounded.
Original processing dependencies have imports/pure definitions/constants only;
no collector/database/config/Apps Script imports. No synthetic stored IDs or
candidate documents added to queue, no assumed insert/emailed outcome.

Mail preview includes visible inseparable scope notice before original HTML:
renderer differential, events omitted not verified zero, fixed UTC header,
separate fetched/displayed counts, no verified unsent queue/delivery/marks.
Fetched low-score CRITICAL count is not displayed critical count. IDs remain
private queue diagnostics, not embedded HTML or marking receipts. No recipients,
subject, schedule, article_ids/ids_to_mark aliases or Apps Script-ready envelope.
Original sanitizer and encoded-ID guard retained. It does not detect all secrets
inside accepted text or URL paths. Queue tie order uses ObjectId descending,
an addition not original tie-order guarantee. No source authenticity claims.

Fulltext/Telegram remain unwired, not silently treated as dropped functionality.
No ReceiptBridge or durable claims. Live queue/mark policy, claim ledger, source
writes/index verification, send reconciliation and owner approval remain open.

10 focused author tests pass in configured repo. No UI/rendered pixel inspection
in this increment yet; no visual readiness claim. Full suite and independent
code review still pending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-059"></a>

### Reference: `integration/COMPULSORY_CHANNEL_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":901,"path":"integration/COMPULSORY_CHANNEL_LIMITS.md","sha256":"3d781ed5a670b0a576e885e636b38d6b797a50e29d9be848a15b2e708bee2f3b"} -->
# Compulsory channel preview

Republic is the sole admin-defined compulsory channel. Its existing configured video ID is retained, not verified currently live. Al Jazeera English, France24 English, DW News and ANI News are removable defaults. Up to 20 additional/removable channels use local browser settings only; the fixed record is always composed from code, never localStorage. This is a preview configuration, not multi-user roles/auth or tamper-proof enforcement against someone editing the app itself.

Legacy saved full lists migrate in memory by removing any duplicate of the Republic video ID and retaining its configured admin name. A saved empty list means Republic alone. No DB writes, remote persistence, alerts or timers. Per-user saved settings wait for reviewed login/storage design. Existing URL validation, delayed player creation, muted playback and YouTube fallback are retained.

<!-- END-ORIGINAL-DOC -->


<a id="doc-060"></a>

### Reference: `integration/CONTEXT-EXCERPT208.md`

<!-- ORIGINAL-DOC {"bytes":3762,"path":"integration/CONTEXT-EXCERPT208.md","sha256":"f64b1114c4ea89a23c008b614fb3f6ac7028b0c8d9d7c435b994a0e947c12874"} -->
# 208: visible bounded Finder description context

This changes only the merged workspace. Preserved Finder detail/index bytes,
the matcher and the unit207 server cap stay unchanged. index.html lines3647-48
render esc(pretty(e[2])) as detail-desc. pretty (928-934) changes all-caps case,
not length. The workspace previously sent the whole textContent. The actual
0:010619 description is252characters and failed the existing200term cap.

Now ONE product term is the first200Unicode code points, counted with Array.from,
without splitting a UTF-16 surrogate pair.199ASCII characters plus emoji plus tail
returns200points, including the whole emoji.150emoji count150, not300UTF-16 units,
and show no notice. A prefix may cut mid-word or mid-character sequence (ZWJ or
combining sequence). No fuller matching coverage is claimed.

There is no whitespace normalization or control repair. TAB/LF/CR/NBSP remain.
DEL/C1 or a lone surrogate in the prefix still gets400. The existing frontend
catch shows "News is unavailable. Finder remains separate.", not the raw server
body. The notice and excerpt remain visible. Error resets lastContext, allowing
later DOM-triggered replay, not automatic retries.0..2point descriptions still
send an empty terms list.

The notice and keyboard-operable details summary live in the PARENT document,
not the iframe MutationObserver target. The excerpt uses textContent, not HTML.
The notice states first200characters, full Finder description preserved, and
matching may miss details outside the excerpt. It is separate from the loading,
results and error status, so replies never overwrite it. Short descriptions,
no-code and search context clear the notice and excerpt. Full original text plus
code-point length participate in local lastContext, but never go in the request.
The existing generation guard rejects a stale long-to-short reply; long replay
still works. Code, system and country stay unchanged. Server cost is not widened.

## Static module routes

The new module is allowlisted both in news_api's private asset route and in
public_preview_builder's public-sample ASSETS. The latter was missing in the
first source candidate, which broke the static workspace.js import on that path.
That candidate was rejected. A public-preview test now checks the new module200
and an unrelated asset403. No public POST or private access is enabled.
The public sample has its existing empty-source, offline-Finder scope; this unit
does not make related-news POST available publicly.

## Test and visual scope

Pure Node checks0/2/3/199/200/201/2850, the emoji200boundary and150emoji, multiline
and NBSP, unsafe plaintext and control preservation.23focused Python tests include
workspace,207 and public-preview allowlist checks. Actual merged workspace and
preserved Finder in local Chromium at390/1280 check0:010619's exact body: code
010619, systemHS, empty country, and ONE200point term. Full252detail remains;
the real local207handler accepts the prefix. Short0:090121clears the notice.

Synthetic DOM probes cover literal <script> and &lt;,200unbroken characters,
DEL/lone-surrogate400 with a visible excerpt, error replay,150emoji and stale reply
then long replay. All requests are loopback; zero external requests/page errors.
Actual-source screenshots at390/1280 were inspected directly: readable complete
notice and excerpt, no horizontal overflow. The full Finder keeps its existing
internally scrollable frame. Screenshots do not show every Finder section at once.

No live data, accounts, providers, DB writes, mail, collectors, timers, deployment
or cutover. Original index/data are unchanged. Long descriptions now submit a
visible excerpt, not the whole phrase. Other207 bounds/control refusals remain.
201c stays held.

<!-- END-ORIGINAL-DOC -->


<a id="doc-061"></a>

### Reference: `integration/COPY191.md`

<!-- ORIGINAL-DOC {"bytes":616,"path":"integration/COPY191.md","sha256":"4eeb1d7651f4ed04954f7ec899ac41a71700579f7bab11a0561a4e3a6efd46f8"} -->
# Whole-store feed vs latest100 summary wording

Copy only, conditional on injected whole-store pager. Generic sample label now
clarifies latest up to100storedarticle metrics, not full-store totals; feed loads
more below. Stat label Latest100metrics(not total), critical/category samebound,
CSV latest100view wording. OFF/empty/private fixture labels unchanged. No metric
calculation/query/cap/endpoint/flag/auth change. No buttonstyle/sort changes.
Actualdesktop/mobile390fixturepixelsinspected, same scroll/stale/browser regression
passes. Existing live125cards verified beforethisunit; notdeploymentclaimforcopy.

<!-- END-ORIGINAL-DOC -->


<a id="doc-062"></a>

### Reference: `integration/COPY195.md`

<!-- ORIGINAL-DOC {"bytes":958,"path":"integration/COPY195.md","sha256":"b76e2a0266d4a8f77fff71e45f676162b569ecdffa93fb46f00f929893741d4e"} -->
# Whole-store summary copy extension

Only whole-pager true branch: signals/status/critical24hline, dailyUTCvolume
heading/peakday/selectedsummary/window/meterlabels, criticalstorycountscope,
category/risk/credibilitycharts/meter/empty/errorcopy, ARIAsummarylabels,
CSVfilename/error/truncatednote,scrollfooter nowclarify latest100summary view,
notwhole-feed totals. BRICS dynamiccopy and OFF/privatefixturesretain original
loaded/samplelabels. Newwords do notchange counts/dates/filters/caps/endpoints.
CSV remains≤100matchedarticlesin selectedsort,notwholefeed;filenamechangesonly
inwholeGeobranch. No style/sort/liveflag/index/DB/secret changes.

ActuallocalChrome desktop+390mobile pixels inspectedforstats/critical/expanded
volume/signals/bars pluswholefeedscrollfooter/export. Allreadable/nooverflow;
autoscroll>100/window200/stale/error/refresh fixturestillpasses. Sourceonly,
notclaimnewwordsdeployed. Every changedsummarywording preserves scopes.

<!-- END-ORIGINAL-DOC -->


<a id="doc-063"></a>

### Reference: `integration/COUNTRY_ALERTS_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3507,"path":"integration/COUNTRY_ALERTS_LIMITS.md","sha256":"08429b42dd73828d442f82a9e797ae1b86d88a0d3196b2fbed0da81a3a5fb2fb"} -->
# Pure memory-only country alert contract

Separate transition noUI/env/network/timers/store/accountwrite/sends. Exactopaque
fixtureowner+ruleid; separateexplicitlabelcatalogue, noaliases/country inference.
Closedrulecountries/risks/categories/version, SHA256semanticsignature. Changed
semanticrule requires explicitrebaseline, quietfreshsnapshot; versionaloneno
replay, rollbackrefused. Firstbaseline noalerts. Allsuppliedidentities recorded
regardlessmatch sochangedtext/risk/country doesn'trepeat. Unknownrisk/category
nonmatching, emptycountry notdeletion. Newlyseen NOTnewlypublished.

All-or-none copies, explicitcommitted/refused/unavailable; failkeepsoldstatecopy,
noinputmutation. InertJSONonly, rows100/history2000/inbox200, noeviction. Read/
dismisskeephistoryreceipts. Missingstate startsnewbaseline; crossowner/ruleid
refused. Callertrustedfixturestate, notauthenticatedtoken/serverstorage; no
CAS/concurrency claim. No browser/accountwatchlist reuse. Copyoutputsaliasfree.

Sourceclosedstatus/observed_at/rows/sha256 envelope: availableemptydistinctfrom
unavailable(emptyrows/nullstamp/nullhashonly), malformedfailclosed. Hashchecks
canonicalsuppliedrows integrity, NOTsourceownership/externalverification. Clock
suppliedaware1970..2100, noautomaticclock, observedrollbackrefused. Timestamp
notpublicationproof. Exactpublicrows10fields, extra/privatefieldsrefused, bounded
scalarvalues/controlcharactersrejected. SHA256(project+'\n'+normalizedHTTPURL)
identity, identicaldupscollapsed/conflictingdupsrefused. URLnormalization follows
existingviewlowercasenetloc/pathslash/fragmentdrop. No credentials/backslash.
PublicalertURL querycredential-like keys/longvalues/JWT/Bearer/DBURI redacted.
Notguaranteeallnaturallanguage secrets detected; inputtrustedpublicfieldboundary.
NoURI means noDBconnectionURI/privateIDs/settings/session/backupTelegramlinks;
publicnewsHTTPURLs intentionallyremain. StoredredactedURLcan'trecomputesource
key; validateskeyshape/project/alertidentity/hash andsafe-redactedpublicform,
notoriginalURLbindingfrompersistedstate. State is trustedfixture, notpublicinput.

8focusedstdlibtestsPASS baseline/dedupe/reentry/dismiss/version/rulechange/
rollback/conflict/crossowner/capacity/aliasing/malformedenvelope/hooks/redaction.
No livealerts or background delivery, no UI yet. Future durable ledger/auth/
polling permission/rule-accountbinding remainunimplemented beforeliveuse.

V2ALLpersistedstate validatedbeforeanyoperation, canonicalUTCobserved/inboxclock,
1970..2100 bounds/versionbounds/uninitializedemptyinvariants/duplicateinboxID/
identityrefusal/inboxtimestamp<=observation. Exactnonemptytrimmedcountrylabels,
separatecataloguenotcurrentrow-derived; samplemissingselectedlabeldoesnotinvalidate
rule. PublicalertURLnowstripsALLqueryparameters (strongercredentialavoidance,
mayremovefunctionalnewsURLparameters); identitystilloriginalnormalizedURLhash.
11focusedtests includeinboxcapacityatomicfailure/clockrollback/rulechangedwith
unavailablemalformedsource/read-dismissreceipts/allstateinvariantnegativecases.
Notclaimwholecontracttestedorexternalstateauthorityproven.

V3sourceclockrange validatedafterUTCnormalization throughsamecanonicalstamp_utc
validator aspersistedstate. Bothboundaryoffsetcases atomicrefused (1970->1969,
2100->2101).12focusedPASS. ReviewV3SAFEpurememoryfixtureonly, notproduction/
account/storage/polling/delivery; trustedpublicinput/querystripping/checksumnot
sourceproof residualsretained. Fullsuite970next, backupsorderedafter71/72.

<!-- END-ORIGINAL-DOC -->


<a id="doc-064"></a>

### Reference: `integration/COUNTRY_PAGE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1483,"path":"integration/COUNTRY_PAGE_LIMITS.md","sha256":"3f8324bf3fd6c6a4bcaf5c6728323233fb5d43b3f1567f3bb258e0d0b10135f6"} -->
# Trade-country page and watchlist

Independently written. Reads supplied normalized Geo and BRICS rows under existing private preview authorization. No new clients, collectors, timers, writes, delivery, deployment or cutover.

Exact original country/region labels only. No headline inference or country-code aliases. Counts are loaded rows, not unique articles, full database coverage, trade flow, risk or verified tariff changes. Country views cap display at 100 and preserve collection labels. Finder matches use only the existing verified-index endpoint, on manual click, with no new guessed HSN codes.

Watchlist holds at most 20 labels in this browser's localStorage. It does not sync across devices or activate alerts. Storage failures are visible. Empty results and unavailable reads are distinct. Future/missing timestamps are displayed as supplied, not interpreted as verified event dates.

New URL: /workspace/countries. No public exposure: default authorization denies it. This is a local offline increment pending independent review and private backup, not a deployed app.

Whitespace-padded stored labels are not offered in the selector. They cannot be matched through the trimmed UI and remain uncounted there. Counts per project cover all matched supplied rows and may exceed the 100-row display cap. The supplied normalization layer converts missing/non-string country values to strings before this page reads them; direct unnormalized dicts are not accepted input.

<!-- END-ORIGINAL-DOC -->


<a id="doc-065"></a>

### Reference: `integration/COUNTRY_SIGNALS_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3641,"path":"integration/COUNTRY_SIGNALS_LIMITS.md","sha256":"448b9680453c8bcfc42a9f3bf93022060a8b8d670b0681962f525d95b7e5c449"} -->
# Country news signals (offline supplied snapshots)

This independently written module counts exact Geo country labels and existing stored risk classifications. It does not classify stories or rate countries. It does not read a database, make network requests or send anything.

28 days is a minimum observed-history threshold, not proof of complete coverage. created_at is normalized to collected_at by the existing news view. Zoned UTC collection and publication windows stay separate; invalid/missing timestamps do not fall back to each other. Future collection timestamps are excluded. Count unique article_key values in the snapshot, not distinct real-world stories. Duplicate-key rows use the first supplied row, so conflicting duplicates require upstream review.

Countries without an observation at least28 days old show insufficient_history. Older observations give observed_span_only. Neither state proves continuous collection, complete publisher/country coverage or a statistically valid baseline. Distinct active days and missing timestamps remain visible. An empty snapshot is unknown coverage, not a safe country.

Risk index and baseline stay null. A future index needs reviewed methodology, complete daily exposure/coverage metadata and country-specific baselines. A large archive or an earliest timestamp alone is not sufficient. No threat, investment, legal or official-rating claims.

Public outputs contain counts, exact country label, collection/publication window timestamps, earliest observed collection, history duration, coverage/methodology flags and unavailable-index states. They do not contain titles, URLs, database IDs or private Telegram fields. Private API/UI wiring exists (see final wiring paragraph); live source activation
and full-history coverage remain unverified.

Input is a plain list or tuple of at most10000 plain dictionaries of at most100 exact string keys each. Keys are validated before any field lookup. Larger inputs and invalid row shapes fail validation, not silent truncation. Consumed fields have length/type caps:country100, project5, article_key128, timestamp100, risk_level16 characters; exact datetime timestamps with datetime.timezone fixed offsets also accepted. Custom tzinfo and string/datetime subclasses are rejected without calling their hooks. Naive row timestamps remain missing; naive clocks reject. Unknown fields are not read or emitted. Missing fields may remain unavailable. These limits bound scan work; input parsing/transport must enforce its own byte-size limits before creating the snapshot.

The window is a closed28-day elapsed interval, including both endpoints. It can contain up to29 UTC date labels. observed_active_date_labels_in_window counts observed date labels, not0-28 calendar-day completeness. Future publication timestamps are reported separately. History display is floored to3decimal places so a sub28-day span cannot display28.0. Underflow clocks fail with ValueError.

Wired GET query labels reject400 before reading. Signal snapshot errors return503, never a fake zero. Normalized public rows are filtered to exact country and Geo before signal validation, so an unrelated country cannot invalidate that panel. The UI reports the supplied read-view row count and live-reader newest100 per collection cap; this is not28days of full history.

Operator to-do, not performed: if the Geo reader's created_at descending sort is used, inspect Atlas collection geo_intel/articles indexes and consider {created_at:-1}. The owner should be guided in Atlas one screen at a time when needed; no createIndex, DB mutation or index assertion has been made.

<!-- END-ORIGINAL-DOC -->


<a id="doc-066"></a>

### Reference: `integration/DIGEST-DATES202.md`

<!-- ORIGINAL-DOC {"bytes":2119,"path":"integration/DIGEST-DATES202.md","sha256":"f4c10c388b1048aa2e8146cfbd15cc337e80b293c5e457763a21bf5bd8a0976a"} -->
# Item11 normalized date projection (202)

Pure supplied-row adapter for landed193. Original geonews database.py stores
created_at as awareUTC isoformat strings and sorts published strings; original
email_report.py selects unsent rows then score-filters. Current merged193 instead
requires explicit published OR created_at policy and normalized chronology.
Read original live source before this unit; no original queries/send paths changed.

Accept exact zoned extended ISO timestamp strings (seconds, optional3or6fraction digits,
Z or valid fixed offset), or exact datetime with fixed datetime.timezone.
Emit UTC ISO with six microsecond digits. Naive dates, dates without time/offset,
custom timezone callbacks, unknown -00:00, invalid normalized offset components,
missing values and range overflow refuse. Real BSON callers must separately verify tz_aware=True with tzinfo=UTC.
PyMongo default naive BSON Date decoding
is NOT inferred UTC: caller must verify aware decoding independently. Both dates
required even for excluded/old/below-score rows; no created-to-published fallback.
This narrows accepted string spelling vs193's fromisoformat, deliberately held.

Closed supplied digest projection only;1000rows/2MiB/16ktext cap, no truncation,
extra-field dropping or receipt-derived corruption hiding. Byte cap enforced
while building normalized projection, then full unchanged193validation. Original
row identities/data remain unchanged; normalized output selection snapshot hashes
bind canonical dates, not raw date spelling/input kind. Input-kind counts reported
separately, no assertion that equivalent snapshot is identical raw source.

No client, URI/env access, Mongo query, migration, clock read, renderer, transport,
receipt store, sender, marker, scheduler or runtime mount. No default date policy;
owner policy still outstanding. All-time receipts remain supplied fixture facts,
not authenticated delivery/no-repeat proof. This unit does not clear193's actual
schema/index/explain/source completeness/snapshot/durable receipt/renderer gates.
Old collection/mail paths held, gate2/3/4 and201cunchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-067"></a>

### Reference: `integration/DIGEST-EMAIL218.md`

<!-- ORIGINAL-DOC {"bytes":4524,"path":"integration/DIGEST-EMAIL218.md","sha256":"6ca0a48435da89edcb02d0b3bb444dcd16b72286f99bb0ac9dfbefb0f958b998"} -->
# 218: supplied email candidate, not approved or sent

Default OFF returns disabled flags before reading arguments/importing selection.
Explicit True uses actual202 normalization and193 selection for email. Input is
original closed supplied rows, supplied exact UTC datetime, explicit published or
created_at policy, per-channel ObjectId receipt tuples, section limit1..60 and
fixed offset config. No DB URL/client/read, current-state check, send, marking,
archive, ledger, network, scheduler or live mount exists. No sender uses218.

ONE candidate contains Last 24 hours and Last 7 days (includes last 24 hours).
Both windows are inclusive: [asof-24h,asof] and [asof-7d,asof]. An overlapping
article appears in both sections. Each section selects score>=4 rows after exact
supplied email membership exclusion, ordered score descending, normalized
published descending, ObjectId descending. Receipt fixtures are caller-supplied
per-channel membership, not DB checks or authenticated complete send history.
Legacy emailed flags do not establish per-channel membership. Entire input is
validated, including excluded/old rows. IDs dedupe for212's ObjectId identity;
sorted union<=120 is binding data, not permission to prepare a ledger receipt.

Subject is fixed text plus supplied UTC timestamp, never an article title.
Body uses exact fixed-offset arithmetic, no timezone database. offset_label must
exactly equal its signed HH:MM offset_minutes, e.g.+05:30. Near midnight can shift
the calendar day while preserving the same instant. Label does not assert a zone
or DST rule. No clock is read inside.

Every display string goes through203 plain Unicode control/format neutralization
then HTML escaping (&,<,>,double/single quotes). Text uses the same neutralized
values and article order. Surrogates refuse via202/193; bidi, zero-width, NUL/C1
controls become spaces. URLs follow203's closed HTTPS/no-userinfo/no-controls/
no-whitespace/host/length/port rule: unsafe links refuse the WHOLE candidate,
including excluded rows. They are not silently dropped. href is escaped.
No images/tracking/remote fonts/style block/JS. Inline CSS and presentation tables
are a candidate layout, not proof of Gmail/Outlook or dark-mode compatibility.

Combined subject+html+text UTF8 cap80KiB; separate HTML-only cap60KiB gives extra
headroom against email-client clipping, not a measured Gmail limit. Overflow
refuses ALL with fixed Email candidate held; no truncation, reselect or dropped
identity. Multibyte boundaries at cap-1/cap/cap+1 are tested. Source fields remain
bounded under193/202, so even a legal input can hold on output size.

Empty selection returns skip=True and flags only: NO subject/html/text/digest or
candidate field from which an accidental212prepare can be assembled. Nonempty
result has candidate data and SHA256 canonical sorted-key/separator/ensure_ascii
JSON digest of every candidate field including renderer_version,
digest_algorithm,kind,date_field,asof_utc,offset_minutes/label,subject/html/text,
ordered section names/headings/IDs/counts,sortedunion andskip. It binds THIS
candidate only, not content approval or immutable archive proof. Same inputs
produce independent equal outputs. The owner has not approved wording/recipients.
send_allowed/ready/archive_proof remainFalse, not review flags a caller may toggle.

Visual evidence: local headless Chrome desktop and mobile screenshots inspected
for readable wrapping, headings, overlap and no horizontal overflow. Browser
pixels do not verify email-client rendering. Actual Outlook/Gmail tests remain
open. No real email, remote resource, DB or Google service was used.

Events, weekly/critical, historical exclusion completeness, immutable body archive,
212 enforcement/import/mapping/control preservation, marking, sender/recipient/
final words, reconciliation, mailv1 128-cap handling, deployed Host, real mount
and live workflow remain open.217staysheld,216unselected. AppsScriptselected/
SMTPfallbackheld/201cwriteheld.9am target is not readiness or live permission.

193 ignores emailed=True for this selection: only the supplied email receipt tuple
excludes an article.218 cannot verify those fixtures. Digest covers the rendered
candidate, not original input rows; distinct source snapshots rendering an equal
candidate share a digest. Text prints raw safe URLs and Article ID lines. A future
real renderer must decide whether those IDs belong in the owner-facing body.
Content remains a candidate, without owner-approved wording or recipient.

<!-- END-ORIGINAL-DOC -->


<a id="doc-068"></a>

### Reference: `integration/DIGEST-RENDER203.md`

<!-- ORIGINAL-DOC {"bytes":3297,"path":"integration/DIGEST-RENDER203.md","sha256":"0e9d69c13bd7800748180bc652eef563a8ae0d72400065998dafddf264f44e74"} -->
# 203 articles-only supplied digest preview

New pure render_preview takes ORIGINAL closed rows plus explicit193date/channel/
receiptfixture/limit and explicit fixedUTCoffset minutes+label. Invokes202itself;
no arbitrary selection dictionary accepted. Original category/card conventions
read from live push2006/geonews reports/email_report.py and landed digest render.
Category presentation follows original order; missing/empty/unknown category is
merged into GENERAL labelledOther, never dropped. Unknowns share originalOther
group deliberately; originalemoji/risk-colour styling is not reproduced. Cut occurs in193selection order before categorizing.

Two sections: Last24hours and Last7days(includeslast24hours). CountsShowingNofM
always printed from precap selection counts; distinct precap union uses193last7dayseligible_count, since24his subsetof7days
under identicaldatefield/eligibility. No duplicatedrenderereligibility logic. An overlap appears twice in section counts, once
inunion. Rendered-ID multiset equals selected-ID multiset, set equals supplied
selection-only union; counted omitted occurrences tracked. selection_only_union_ids
is NOT receipts, delivery/mark permission or an authenticated alltime ledger.

Fixed offset deterministic display; timezone label and numericoffset+asofclock
printed. No serverzone/IANA/tzdatafallback or DSTclaim. SnapshotID/datefield/channel
andPREVIEWnot-sent/datepolicyandreceipts-unverifiedbanner shown. No ObjectIds in
HTML/plaintext. Byte-deterministic outputs; input rows untouched.

Local link helper inspired by integration.news_view.safe_url; it is intentionally
new, no unreviewed original helper required. Exacthttpsonly(same landedrendererpolicy),2048charcap, no
userinfo/control/format/whitespace/backslash, validates host/port. ALLoriginal
links checked, including receipt-excluded/oldrows. Any invalid link holds the
WHOLErender, no silentitemdrop. Attributes/text HTMLescaped, linksnoopener
noreferrer. plain helper neutralizesUnicodeCc/Cf and collapseswhitespace/newlines,
includingbidi; plainpart noMarkdown/autolinking. Unknown fields/text overflow
stillheld by202/193. No remoteimages/fonts/CSS,JS or fetchedresources.

512KiB cap EACH HTML/plaintext offlinepreview; overflowholds wholeoutput, no
rowsreduced. This is NOTanemailbudget or clienttest. Futureemailunit needs lower
independentlyverifiedsizebudget,inlineCSS/tablelayoutandclienttesting. No darkmode
claim. Article-only preview explicitly says eventsnotsupplied, not zeroevents.

HeadlessChromium suppliedfixture inspected at390and1280px;nohorizontaloverflow,
zeroexternalrequests. Screenshots show completebanner/asof/metadata,twosections,
Othergroup andcap/clientcaveat. No liveapp/route/DBquery/client/env/readclock/
transport/sender/mark/archive/scheduler mounted. Ownerdatepolicy, actualsource,
authenticatedreceipts/norepeat andemaildeliveryremainheld.201cunchanged.

Secondrenderer rationale: landed geonews_digest/render.py implements legacy
unsent selection/event/layout conventions;203is an unmountedtwo-windowpreview
with202/193selection and visibleintegrity/capmetadata. Do not replace/wireeither
until a later reviewedconsolidationpreservescontracts and safepolicies. Local
helperstricterwholeinputrefusal isintentional, not sharedlegacybehaviorchange.

<!-- END-ORIGINAL-DOC -->


<a id="doc-069"></a>

### Reference: `integration/DIGEST-WINDOWS193.md`

<!-- ORIGINAL-DOC {"bytes":1964,"path":"integration/DIGEST-WINDOWS193.md","sha256":"9db747c408ad1c49cc9de87e23a285488f1bfde4769488c09db1185e8cbc048b"} -->
# Item11 pure selection preparation, ONE digest

Original owner menu11:18 on2026-10-09 offered24h/7days/all-time withoutrepeat;
owner11:19answered1 2 3. Mainclarified taskshape: one24h+7dsectiondigest with
all-time displayed receipt exclusion. No three modes or all-time article section.

Source plan only, not UI/render/query/store/send/mark/scheduler. Explicit caller
published OR created_at policy, with no default: owner has notpicked whichdate.
Pure plans leave raw_mongo_query=None because zoned stringdates sortlexically,
notalwayschronologically. No naïve$gte stringdatequery or schema migration.
Dates interpreted normalizedUTC,inclusive start/end,futureexcluded. Section7days
includes24hbydefinition; overlap reported, uniondisplayedIDs dedup internalonly.
Cap60persection AFTERscore>=4 differs fromoriginalcap-before-score-filter; only
showneligible IDs proposed for future receipttracking, no actualmarkpermission.

Exact1000row/2MB/16ktext fixturebound, uniqueObjectId, fullinputvalidationbefore
filter/exclude. SelectscoreDESC/normalizedpublishedDESC/ObjectIdDESC. All-time
per-channel injected exactObjectId tuples≤10000modeldisplayedreceiptexclusions;
notauthenticateddeliveryorcompleteledgerproof. Legacyemailed bool isnotchannel
receipt, intentionallyignored (reported). Noall-time receipt truncation: reject
oversized input, futuredurablestore lookup required. Snapshot hash bindsinput,
clock/date/channel/receiptsets/limits, notDBsnapshot/no-repeat/sendproof.

Remaining: ownerdatepolicy, overlappingdisplaydecision, renderer/windowlabels,
actualsource fullschema/normalizeddatequery,indexexplain, durablecrossworker
claim/receipt and all-timeidlookup keyedbychannel, events-onlybehavior, optional
limitdecision,timezonesandexactsendtimes, authenticatedsendack/markrecovery.
Currentlegacyholdsremain; this cannot activate mail or promise repeats prevented.
No renderer/UI/pixels changed; noevents falselycountedzero. No source read/network.

<!-- END-ORIGINAL-DOC -->


<a id="doc-070"></a>

### Reference: `integration/EVENTS210.md`

<!-- ORIGINAL-DOC {"bytes":2150,"path":"integration/EVENTS210.md","sha256":"8d09a0a63f5b4af9595742cb96fc702677e1f0ece6437fe87d0afdd1ee59591a"} -->
# Events snapshot UI promotion 210

Copyright (c) 2026 Push. All rights reserved.

Dedicated collapsed, keyboard-operable Events panel reuses the same validated
geo_events response from /api/dashboard-snapshots. No route/reader/source added.
Winning snapshotsId generation alone sets the shared eventSnapshotValue; stats
refresh reads it at render time, never fetches events again. Loading/unwired/
unavailable/verified-empty/rows states differ. Count reflects actual displayed
rows, not panel.items length, whole-store count or an upcoming-event window.
Observed timestamp and event_date YYYY-MM-DD strings displayed as supplied,
never parsed through Date. Reader's 90-day window versus old dashboard 120-day
window remains explicit and deferred. Panel makes no window claim.

Server host/label policy unchanged. Client additionally requires HTTPS, rechecks
name/category/confidence/description controls and renders literal text only.
Blanked descriptions leave the row present without a description. Newlines/TAB
remain plain text; description pre-wrap and unbroken name/text wrap anywhere.
HTML strings stay inert. Client rejected rows and server rejected/truncated
notices differ. Cap100 remains. No embeds or source requests. Source links open
only on user click with noopener/noreferrer.

Generic Geo captured-snapshot duplicate removed by hiding that section in Geo;
BRICS branch preserved unchanged. Existing BRICS browser fixture was stale:
production Geo-only UI has no BRICS button. Test restores that nav only in a
synthetic HTML/JS response to exercise the preserved branch, not production UI.
Digest preview continues consuming the same server panel; no digest code edited.
No new modules/assets. Public builders reuse existing workspace JS/CSS and
public sample has no event reader/disclosure; shows source-not-connected state.

This is UI promotion only. Event ingestion, official source stub, owner-approved
source/window contract, live reader activation, data coverage and complete
events feature remain open. No event seed, calendar action, mail, DB write,
collector/bootstrap/engine change or live effects. Stored rows unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-071"></a>

### Reference: `integration/EVENT_READER_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4003,"path":"integration/EVENT_READER_LIMITS.md","sha256":"a834549638b2a31765a5781655b041c722188e5a62e0d4c7228de881b04df2a7"} -->
# Injected events read adapter

Historical/direct-adapter scope: statements below that composition is not
attached describe this standalone reader's initial increment. Later Geo-only
composition is separately gated and connected to digest preview; see
FEATURE_STATUS.md and GEO_EVENTS_COMPOSITION_LIMITS.md. No live schema, role,
source capability or activation has been verified by that wiring.

ReadOnlyEventsReader preserves original Geo upcoming_events query: inclusive UTC date today..today+days, event_date ascending. No database client/config/index/imported legacy module, write, collector or live route. Clock and collection explicitly injected; verified flag required. Original source: intelligence/geo/database.py upcoming_events, retained unmodified.

Caller must verify the exact collection identity and read-only credential. Production composition is not attached. Cursor query has2second server-execution max_time_ms (not an end-to-end2s deadline) and reads at most limit+1 (limit at most1000). More rows fail unavailable rather than silently truncate; complete serialized UTF-8 snapshot envelope at most2MB, each scalar16k. Collection/provider must enforce network/socket deadlines and projection before allocating payloads; this adapter cannot bound a client library's incoming wire bytes. Cursor assigned immediately after find and closed on successful read, sort/limit/max_time_ms setup failure and validation/iteration errors; close errors suppressed without disclosing details.

Only six event fields leave adapter: name/event_date/source_url/category/confidence/description. _id excluded by query, unknowns never copied even if fixture ignores projection. Zoned fixed-offset clock normalizedUTC. Invalid dates/order/out-of-window/malformed rows/surrogates/budgets fail closed. Read time is observed_at, not a claim the source announced/updated the event then. Empty verified snapshot differs from unavailable.

Display must still go through existing DashboardSnapshots reviewed per-panel public-host/label/URL gate. Reader does not establish source URL trust or open links, and is not a renderer. Source event semantics retained, but stricter shape/budget/order requirements are deliberate safety differences. Digest events and real dashboard composition remain unwired pending separate review. No source events are invented or seeded.

Budget definition is compact ensure_ascii=False UTF-8 JSON with separators(',',':'); downstream serializers must match this to retain the stated2MB transport cap, or apply their own encoded-envelope budget. Pretty-printing/default ensure_ascii output can be larger. Before any production composition, independently verify collection identity, read-only credential, client/socket deadlines and the display host policy.

Private digest preview can now consume the exact injected DashboardSnapshots Geo panel. Existing verified host/URL/text gate runs before original renderer; additionally filters inclusive UTC90day preview window. No event data assumed when absent/unavailable, and response metadata preserves observed_at/rejected/truncated/shown state. Critical/weekly do not read events. Original HTML template remains unchanged, including its700px fixed-width mobile overflow. Loopback pixels verify escaped fixture event name and source link; no external resource requests or delivery occurred. This is supplied-snapshot dry-run composition, not a production event reader or mail queue.

Digest preview metadata now counts out_of_window only within the already capped display snapshot (window_count_scope=display_capped_snapshot_only). If display panel truncates, truncation_may_hide_in_window=true: it may have dropped matching events before date filtering. No whole-source count is claimed. Preview requires a fixed aware datetime clock; injected UTC now drives original renderer date facade/header, removing server-local date drift. Original template's no-scored-news line remains when events exist but no articles score above threshold.

<!-- END-ORIGINAL-DOC -->


<a id="doc-072"></a>

### Reference: `integration/EXISTING-SCHEMA215.md`

<!-- ORIGINAL-DOC {"bytes":3619,"path":"integration/EXISTING-SCHEMA215.md","sha256":"f8e57056114b2f6f4607aa24280dbf637149a7b4ac9e637c411a4f8955868e8b"} -->
# 215: optional existing-schema review data

The owner asked for DB wiring without a collection check, not schema changes.
This optional data is neither a pending step nor a gate for wiring. Nothing will
run it. Do not present it as an action to approve unless a later scoped unit
actually needs schema changes. Calling optional_schema_review authorizes nothing.

The function does not inspect collections, construct a client, read a DB URL,
read environment or files, install schemas, create collections, seed genesis,
change roles or counters, select runtime behavior, or execute DB commands.
It proves nothing about collection existence. Existing state and history remain
unverified. No automatic follow-up occurs when a DB URL appears.

validation_level is required. The reviewer explicitly chooses strict or moderate;
there is no default. Strict validates all later inserts and updates, including
updates of existing invalid documents. Moderate validates inserts and updates of
existing valid documents but skips validation of updates of existing invalid
documents. This choice changes whether existing rows can be updated. Neither
choice proves existing rows or writers compatible. Proposed validation action is
error. These are optional review values, not permission to tighten a live schema.

The eight names are the current fixed native names, sorted. Validators are
independent deep copies of the actual current VALIDATORS constants captured at
module import, not schema observations. Tests pin canonical validator hashes so
future source drift needs a fresh review. articles/events are not included.

request_data_not_executable contains descriptive fields, not collMod/create
command wrappers. No element is directly usable as a pymongo db.command request.
A future separately approved executor would need deliberate translation and a
copy step. This unit supplies no executor or execution instructions. Proposed
majority/j=True/wtimeout=5000 is data only, untested against a real server.

No create or missing-case branch, genesis template, read command, source clock,
fingerprint, reset, role request, upsert, repair, or callable is returned.
If separately authorized future work discovers missing collections, it must hold;
creation requires a separate explicit owner decision. This unit never discovers
missing collections and never initiates that future work.

Existing writers and rows might be incompatible with a proposed validator.
No backup/custom-role ask is reopened here; closed asks do not prove those gates
satisfied. Preserve articles/events and all existing native state. Any future
schema change needs exact scope and owner permission, not this review data.

AdmissionStore INSERT/drop TOCTOU remains open: inspection can precede an admin
drop and one insert can recreate a collection. This unit proves nothing about
no automatic creation. 201c write selection stays held; prior ONE-write wording
is not permission for that effect under the owner's no-auto-creation boundary.
No live DB read/write, presence check, provisioning, activation or cutover occurs.

Validation-level semantics source:
https://www.mongodb.com/docs/manual/core/schema-validation/specify-validation-level/

Transitive imports: this module's own imports are stdlib copy and static
constants, but native200_admission_preflight loads pymongo,
native200_transactions, native200_store, native200_admission_store and
native201_schemas. Importing 215 requires the pinned pymongo environment;
215 is not "no pymongo/no store import" at runtime. Those imports do not connect
or read a DB. Nothing in production imports 215.

<!-- END-ORIGINAL-DOC -->


<a id="doc-073"></a>

### Reference: `integration/EXPORT_DIGEST_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3157,"path":"integration/EXPORT_DIGEST_LIMITS.md","sha256":"95f9029499f75d2138ebe320ddb1accd7ad7690799dacaee9feb2d5b0b02bc1c"} -->
# Interim export and digest preview limits

Snapshot CSV is a loaded read view, max100 matching rows/project after project/category filtering, raw input max2000. Any cut sets X-Export-Truncated=true and X-Export-Input-Limit=100 per project. Reader itself currently fetches newest100/project, so a category query still cannot reach older database history. Existing generic full export route503 unless a generic pager is explicitly injected; actual launcher supplies none. Reviewed original-order keyset planner/injected fixturepager/originalcolumn streamconsumer now exist separately, not wired to that generic route. No production database adapter or original streaming route yet. Original Geo/BRICS full cap1m/5000 verified source, not currently wired live. Headers/order/trailer differ from original export contracts and remain parity work.

Streaming guard is one export per process. Release idempotent through generatorfinalizer and Response.call_on_close, including HEAD/no-first-yield close. Slow clients hold a process slot until connection close; sync-worker timeout can kill long exports. Production needs shared limits, pager query timeout below worker deadline, stable-sort/index review and measured throughput before enabling. No request creates indexes or writes.

Digest/critical/weekly routes use original HTML renderers over supplied public Geo sample. No original article IDs or sent-state flags leave the boundary. /mark-emailed always503 after private+Origin guard. No send, mark, collection or scheduler call. Digest eligibility is not a verified unsent queue because public rows lack emailed state. A bounded injected events adapter and exact DashboardSnapshots-gated supplied-event digest are now reviewed; actual source/runtime composition is still unwired. C's added pure selection helpers normalize fields; original renderers are preserved, not replaced by C's new HTML templates. Official values, actual mail delivery, cross-run alerted receipts and Apps Script compatibility are not proven here.

Renderer boundary now loads hash-pinned original AST function definitions/literal constants only, with exact dependency names, restricted builtins and explicit html.escape/date-text facades. No original Python modules, config, database, SMTP or archive functions are imported or copied. Unsupported global references are rejected. This is a capability-minimal scope for reviewed code, NOT a general hostile-code sandbox. Date strings are computed outside renderer scope to avoid datetime.strftime's internal __import__ requirement. Defaults match original category order (including GENERAL),90-day event window and4 min score; configurable production settings intentionally are not read by preview. HTML still has original fixed-width mobile behavior.

Separate supplied original-compat Geo queue renderer now preserves cap-before-score-filter and all-fetched-ID scope, with marking policy OPEN and unsent_queue_verified=false. It does not replace public digest preview or establish a current unsent queue. Aggregate retention fidelity audit finds original cleanup lacks backup verification; no cleanup activated, no lossless proof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-074"></a>

### Reference: `integration/FAKE_WRITER_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1272,"path":"integration/FAKE_WRITER_LIMITS.md","sha256":"c425188abfd19c098941adb8f1b62519e4b42200a20cc61040a6687de89e254d"} -->
# In-memory writer fixture

This is a contract exercise only, not a Mongo adapter. It chooses no database,
collection name, unique index or live configuration. Geo and BRICS use separate
in-memory maps. No production migration or persistence is implied.

Identity is the exact supplied URL, with no normalization. Case, slashes and
whitespace can form distinct identities. Before a real writer is connected,
verify original collector URL handling and actual collection ownership/schema.
BRICS adds sha256(exact URL) as id. Supplied UTC collection stamps intentionally
replace the old naive-UTC BRICS convention and need reader compatibility review.

Field values are checked for plain JSON-like types, not per-field semantics:
score can be a string, published is unparsed. Bounds are per container rather
than a total-memory/DoS budget; large integers and empty extra keys are accepted.
Required strings must be nonblank; provider-owned fields are omitted.

The failed outcome is a caller-supplied synthetic fixture. It is not a real
storage failure classifier. A future Mongo adapter must separately test unique
indexes, concurrent duplicate races and partial bulk failures. No collector,
alert, mail, Telegram, scheduling, migration, drop or index operation is enabled.

<!-- END-ORIGINAL-DOC -->


<a id="doc-075"></a>

### Reference: `integration/FEATURE_STATUS.md`

<!-- ORIGINAL-DOC {"bytes":24204,"path":"integration/FEATURE_STATUS.md","sha256":"05f3ffa53c77001fa4e258837d79d92b39fa353fd169087777cc0ea8b60324f2"} -->
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

## Increment90: separate security candidate research, unselected

Officialhashed25packagecandidateinstall/pipcheck succeeds, pymongo4.18.2 /
pypdf6.19.0. Qualifyingcandidate1119uniqueIDs/runOK1expected/1optionalPDFskip
in namespace with regressiononly4GiBvirtualRLIMIT_AS; best-effort50mssampled
process-groupmonitor768MiB/128processes NOT enforcedaggregateboundary and
notproofalldescendantcoverage. Default/attack1GiBunchanged. Originalconfigured
1119runOK559+280+280,1expected/1skip. Failed/interrupted/accidentalhostattempts
retainedandexcluded. ScopedindependentreviewSAFE, NOTproductionpinselection.
28highprovideralerts=12distinctadvisories(10PDF/2Mongo), duplicatehistorical
andpreservedmanifests; remaining3highssameBSONadvisory. Allseveritydirect/
transitivecheck pending. ExactBSON2GiBoverflowNOTexercised, sourcepatchonly;
no liveMongo/servertransactionproof. Productionpins/source/87/88unchanged,
alertsNOTfixedinproduction. NoPRmerge/deploy/send/DBeffects/collectorstop.
LICENSEexplicitlyapproved/committed separately; thirdpartytermsremain.

<!-- END-ORIGINAL-DOC -->


<a id="doc-076"></a>

### Reference: `integration/FINDER-BROWSER229.md`

<!-- ORIGINAL-DOC {"bytes":4675,"path":"integration/FINDER-BROWSER229.md","sha256":"d57036cce3e26a852e043e56624898347756688a96169f010d1a9b8fea7bc4e6"} -->
# Current own-key Finder browser regression (229)

Test/docs-only. Changes: browser_feature_finder.py, test_finder_browser229.py
and this document. No src, snapshot, provider configuration, policy, SW,
server route, dataset or 228 historical test/doc changes.

## Why the old test failed

The BEFORE script expects a configured shared hsn-ai-proxy chain and Mistral
fallback with no own key. Current source has AI_PROXY_URL and all built-in
key strings empty. The shared-rescue code is still present, but its config
is empty; this is not a claim that the shared-rescue code was deleted.
No-key original d-tpl opens settings and returns before window.open. The
unchanged script consequently times out waiting for a popup on the 228 tree.
Timestamped verbatim failing log and exit code are BEFORE artifacts outside
this commit. AFTER captures come only from the final corrected runs.

Current exact pins:
- src/app.js bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313
- index.html e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625
- ownProvider exact span SHA256 43bc397649b5d507858b9633f59b58815ae363f3ee7ac414ea39060b619b217e
- aiReportText exact span SHA256 95dc3562eaa83a65c957fb38f6019c9e786db3592686e4d5d288c67f9b37ee11

Span delimiters are in the unit test; any drift fails loudly. Empty shared
config and existing own-key dispatch are asserted in source and browser.
The existing prepare_shell adapter remains unchanged.

## Narrow proof

1. No-key: original button displays key prompt, opens no popup.
2. Mock success: original own-key storage seam selects Mistral; only actual
   api.mistral.ai/v1/chat/completions is handled. Synthetic narrative says
   SIMULATED TEST TEXT and is not a verified AI answer. Original button opens
   AI-assisted edition; HTML-like marker is literal text, not a b element.
3. Mock 429: separate fresh context, original provider failure opens the Data
   edition/error note and resets busy button. No shared-rescue claim.
4. Original popup opener listener invokes instrumented print counter1 and
   page-number setup completes. Actual OS print dialog not tested.
5. Three-provider UI enumeration is an enum check only. Unknown NVIDIA saved
   provider refusal yields no new request. Neither proves three-provider
   failover or any real provider's availability.
6. Retained bounded-body timeout probe patches fetch/timers only within its
   isolated test call and restores them. It is instrumented helper proof,
   not a real provider timeout or a change to product code.

Synthetic key is checked in memory against the obvious placeholder, never
saved in runtime artifacts. Prompts, headers, bodies and URL queries are not
logged/saved. Logs contain only method/host/path and fixture disposition.
Frankfurter reads are expected aborted reads, not FX accuracy evidence.
Any other external host/path aborts and fails the test. Real successful
outbound requests are zero. Mock fulfillment is local Playwright routing,
not a network call. No provider, AIS proxy or production network is enabled.

## Evidence and run

Two consecutive final runs have equal semantic results/calls; report date
2026-10-10 from frozen clock1791576000000, Math.random0.25, Asia/Kolkata.
1100x900 and390x900 popup captures are timestamped in result.json. No sleeps;
wait on source UI conditions and report document completion.
Chromium154.0.8037.57/Playwright1.63.0/Nodev22.23.3/Poppler22.02.0.

Success and429 PDFs both observed26 pages, A4 printBackground true,
14/12/20/12mm margins, preferCSSPageSize true, explicit print media.
Builder viewed final run2 pages1/13/26 for both, plus both390 screens.
Contents are readable; middle success page shows simulated text with literal
markup; final FAQ table and copyright fit. This does not establish layout
for arbitrary long real AI responses. Runtime artifacts remain outside the
commit, with SHA256/timestamp manifest. No BEFORE capture is relabelled AFTER.

Default unittest explicitly SKIPs the browser without RUN_FINDER229_BROWSER=1
or without Chromium/Playwright/PDF tools. It never implies browser PASS.
`python tests/browser_feature_finder.py` is the explicit browser command;
FINDER229_OUT chooses the artifact directory.

Rerun 228 browser, nested CSV/clipboard, static, offline,198d and ships226 PASS.
Existing browser_finder_network.py remains FAIL: it expects a shared AIS
proxy/manual-refresh result, but original AIS_PROXY_URL is empty and ships
returns proxy-unavailable before a fetch. Its current failure log is retained.
That script is a separate 230 candidate, not changed or silently skipped.
Full project and real-service/activation parity remain incomplete.

<!-- END-ORIGINAL-DOC -->


<a id="doc-077"></a>

### Reference: `integration/FINDER-NETWORK230.md`

<!-- ORIGINAL-DOC {"bytes":5660,"path":"integration/FINDER-NETWORK230.md","sha256":"abc5d1e4b13f89a0b83c4d3467a2266fb6c4bd35a4c0d767870a60783116f2ad"} -->
# Served Finder network fixture (230)

Test/docs-only on landed229. Supersedes the stale browser_finder_network.py
failure recorded in FINDER-BROWSER229.md; that document remains historical.
No src/index/offline/SW/dataset/adapter/policy/provider-config change.

## BEFORE

The original script on the229 tree failed waiting30seconds for "manual
refresh only in private preview". Its verbatim timestamped log/exit1 is in
BEFORE evidence. AIS_PROXY_URL is empty. src/app.js shipsLoad4081-4142
returns proxy-unavailable before a fetch; paintShips4143+ displays "Built-in
proxy access is unavailable". AI_PROXY_URL and all built-in keys are empty.
The shared-rescue code still exists, but its configuration is empty.
The old script expected shared AIS and shared AI and therefore never reached
its later weather/AI/FX checks. No BEFORE output is relabelled AFTER.

## Current assertions

- Ships: original tab/toggle, off/on, proxy-unavailable, no fetch, no busy,
  no data, null shipsTimer. This does not prove manual AIS refresh works or
  does not work. The existing manual_ships_shell adapter remains unchanged.
- Plain words no-key: original plainWordsRun3018-3050 calls aiPickText301+
  (exact span pinned in test). It displays the unavailable error, not the
  settings prompt. Button is enabled again, no AI request. This differs from
  the no-key report button in229, which opens settings.
- Plain words own-key: existing storage seam selects Mistral. Exact POST
  api.mistral.ai/v1/chat/completions mocked success with visibly SIMULATED
  narrative, literal <b>marker</b> rather than an element, cached only in
  disposable browser storage. Separate429 checks error/no result/busy reset.
  Original model pool retries3times in this429 fixture, not3-provider failover.
- Weather: exact GET api.open-meteo.com/v1/forecast and
  marine-api.open-meteo.com/v1/marine mocked with SIMULATED fixture numbers.
  Original port selection triggers another pair. Forecast503 shows unavailable,
  data null and busy false. Marine503 leaves forecast and no invented wave.
- FX: exact Frankfurter GET /v1/2025-09-04..2026-10-09. Fixture dates/rates
  2025-10-09:80,2026-09-09:85,2026-10-09:90. The test derives12.5%year and
  5.9%month with (90/base-1)*100, then checks the original displayed arithmetic.
  This is the test's own arithmetic check, not real FX accuracy.503 sets
  V.ccyImpact='err' and removes the card, no invented rate; there is no FX
  busy flag in this original source.

Exactmethod/host/path matches only; any other external request aborts and
fails. Real outbound successes0. Mistral synthetic bearer is compared locally,
never saved. Queries, headers, bodies, prompts and keys not persisted in
artifacts/logs. Server request logs suppressed. Synthetic placeholder exists
only in test source. Runtime records method/host/path/disposition only.
No product functions/provider config replaced. A bottom SIMULATED LOCAL TEST
label added only for screenshots, not to alter behavior or security policy.

Whole SHA pins: src/app.js bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313;
index.html e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625.
Exact news_api/shell/finder_network hashes in browser PINS. Exact shipsLoad,
aiPickText,plainWordsRun and config span hashes in test_finder_network230.py.
In-memory mutations of each proxy/built-in key and unavailable branch fail
loudly, without touching product files.

CSP origins checked in served browser response. Opt-in cases have zero
unexpected securitypolicyviolation events across navigations. Separate unit
checks defaultOFF self-only, unauthorized403 even with opt-in, and other news
pages' unchanged CSP. No CSP/sandbox relaxation. The negative CSP permission
check is separate from the local mock routing and is not a real-network test.
Playwright readiness uses function expressions, not string predicates that
would require unsafe-eval. No sleeps or60second waits; dynamic loopback port.

## Evidence / limits

Two consecutive final browser runs semantically equal excluding timestamps
and artifact hashes. Frozen1791576000000/Math.random0.25/AsiaKolkata;
1100x900 and390x900. Chromium154.0.8037.57, Playwright1.63.0,
Python3.10.12. Final AFTER run times and per-artifact hashes in result.json.
Final390success/plain/FX/ships/weather and error-case pixels inspected.
Desktop plain/FX/weather pixels inspected in preceding semantically-identical
run; final390 contact sheets inspected again. This is not arbitrary longAI
layout or native device/browser coverage.

Mobile limitation found, not fixed: weather table values are clipped at
initial horizontal scrollleft. Programmatic scroll moves it to the opposite
edge but beginnings/rowlabels then lie offleft. Opposite edges appear in
separate screenshots, not all values together. No keyboard accessibility or
whole-value readability claim. Outer page has no horizontal overflow; that
alone is not enough to claim full mobile readability. Bottom test label may
cover the bottom of a viewport capture; it is not product UI.

229/228/nested/static/offline/198d/ships226 final-source regressions PASS.
Default wrapper explicitly SKIPs unless RUN_FINDER230_BROWSER=1; missing
Chromium/Playwright explicitly SKIPs, never implies browser PASS.
Run `python tests/browser_finder_network.py`; FINDER230_OUT sets artifacts.

Not proven: real weather, real FX accuracy, real AI, provider availability,
three-provider failover, manual AIS availability. No live accounts, DB
reads/checks/writes/creation, sends, activation or wiring. Full project remains
incomplete. Historical feature-status claims are not silently rewritten.

<!-- END-ORIGINAL-DOC -->


<a id="doc-078"></a>

### Reference: `integration/FINDER198A.md`

<!-- ORIGINAL-DOC {"bytes":3298,"path":"integration/FINDER198A.md","sha256":"85e619e6ed305602bd9d5b229681e8509b02d53e3b51313b6d7af5445bcb220e"} -->
# 198a narrow account/session gate (unselected)

Default OFF injected WSGI factory only. No production mount, environment read,
client, account provisioning, login UI, proxy request or runtime provider.
OFF returns the original public callable. Enabled routes only exact account
preauthGET/loginPOST/logoutPOST/whoamiGET and /api/finder-broker/ prefix. Other
account routes denied (including signup/settings/export/change/delete). Every
other public route passes unchanged, including news/health/own-key paths.

No broad create_wired_http mount: that old factory makes all news private.
Only its exact AccountService collaborator validation and account protocol
helper are reused behind the smaller allowlist. Closed accounts, current KDF
parameters, exact store/limiter/policy types and shared secret/clock checks.
SingleWorkerEvidence independently injected, fresh<=120s, observed workers=1,
exact scoped host/activation references at startup and each protected request.
No environment WORKERS or assumed Gunicorn default shortcut. No real provider
is shipped; references/record do not grant permission or prove live settings.
One registered service per store in this factory and same bound limiter through
requests. Other service constructors remain a deployment invariant, not proven
absent. Known multiworker compensation defect remains unsupported.

Exact direct HTTPS lowercase configured origin, no forwarded host/proto trust,
no explicit port; query/encoded/dot/backslash/double-slash protected paths deny.
Login/logout original Origin+preauth/session CSRF and16KiB strict body protocol.
whoami original live session check/touch and protocol CSRF. Every brokerGET/POST
needs exact Origin AND live session AND X-CSRF-Token; even authorized broker
returns503 broker_not_wired (198b separate), never calls public or any transport.
No session/secret/password/hash JSON/URL forwarding. Account cookies preserve
original HttpOnly/Secure/SameSiteStrict/__Host/Path scope; no new CSRF protocol.
GET preauth/whoami may omit Origin as original protocol. Public passes unchanged
without account/worker evidence lookup, including when evidence expires.

Serving enabled real store can write: whoami/session checks touch_session,
login creates/re-hashes/session/attempt writes, logout deletes session. Real
Mongo role/transaction/pre-provisioned accounts_state and scoped owner approval
must be checked before mounting; constructor review fields are not permission.
Source tests only disposable MemoryStore/fixtures. No live authDB or owner
state accessed. No automatic account signup, purge, reset or recovery.

Existing login may create a session before limiter-settlement failure; this
unit does NOT claim login+limiter whole-transaction atomicity. Errors return no
success cookie; no automatic retry. Original session idle/absolute expiry,
revocation and account UID checks retained. Singleworker does not fix unrelated
service/store failure modes. No runtime parity or readiness claim.

No UI/client/source Finder changes, so no changed visual artifact. This is only
an inert server boundary; public offline Finder network remains OFF, own-key
flows unchanged. 198b will separately review fixed proxy/provider/model/port
choices and shared durable budget, without arbitrary URL/header forwarding.

<!-- END-ORIGINAL-DOC -->


<a id="doc-079"></a>

### Reference: `integration/FINDER198BA.md`

<!-- ORIGINAL-DOC {"bytes":4225,"path":"integration/FINDER198BA.md","sha256":"a08badb45a33e1936c59256da7693d462c8fb8c7eb1009d8b177f2244ab95755"} -->
# 198b-a source-only durable proxy-call budget and closed connector contract

Not a live broker. No transport implementation, client, environment selection,
production mount, schedule, model activation or provisioning. 198a still503.
Model catalog EMPTY/DISABLED; Groq/Gemini/Mistral only, NVIDIA excluded. Enabling
entries later requires owner scope, live vendor availability/free entitlement,
current deployed proxySHA, configured provider keys and live health JSON.
Client model comments and wildcard upstream acceptance are not verification.

Reviewed source decisions: fixed geo_intel.finder_budget198, single preprovisioned
_id=shared-finder-v1, majority+journal/wtimeout<=5000 +majority read, revisionCAS,
60 PROXY CALLS per600seconds, global1inflight, consumed BEFORE transport, no
refunds, no takeover/expiry release, unknown/expired held for separate explicit
reconciliation. Dedicated credential must not alias reader/account credential;
actual later client factory must validate that, this injected adapter creates
none. No upsert/create/index/TTL/purge/reset/reconciliation implementation.
Read-only inspect_budget checks exact single identity find/listIndexes/update
role only, fixed mapping/_idindex/noTTL/preprovisionedclosedstate. Constructor
review fields gate source but never prove owner permission or live role.

State: _id, revision, window_start, calls, fence, active, last_clock. Active
key/fence/started_at/deadline<=25s/phase inflight|unknown_held.4boundedCAS contention
iterations; unknownreceiptfailclosed/no network. Completion within ticketdeadline
clears active, NEVER refunds; incomplete/late remainsheld. Clockrollbackrefused.
All requests need distinct nonces; adapter is NOT durable request-id dedup after
settlement and NOT an HTTP retry mechanism. A future broker must not replay a
consumed request under a new or old nonce; no automatic retries/fallbacks here.
No claim of audit-history retention or saved result beyond currentticket/counters.
A separate reviewed receipt/idempotency layer is needed before mounting transport.

Connector CONTRACT fixes https://hsn-ai-proxy.onrender.com and exactpaths; no
arbitraryURL, callerheaderforwarding/redirect/fallback. Ships acceptsALL+42source
portcodes only. AIcatalogdisabled, no live model selectable. Requestcap16KiB,
responsecap1MiB,20secondtransportdeadline, exactlyONEproxyrequest/noautoreties.
These are plan metadata, NOT an implemented bounded network connector. Actual
future transport must enforce while reading bytes, DNS/TLS/fixedhost/noredirect,
and session+Origin+CSRF via198a before durable reservation and before network.
BackendFINDER_PROXY_BASE_URLmustexactfixedorigin;FINDER_PROXY_SECRET48..256visible
ASCII, no secret returned by config validation. No live token loaded or tested.

PROXY CALLS is the accounting unit, NEVER provider attempts. Current proxy may
rotate an unknown keypool on401/403/429/errors. A broker timeout/abort does NOT
prove the proxy/upstream stopped; unknown remains globalinflightheld with no
automaticrelease/retry. End-to-end attempt bounds and acknowledgement are a
separate proxy-hardening work item, not solved by these independent brokercaps.
Source-only success in fixtures is not deployed runtime or free entitlement.

## Current source grounding, October9

Read original proxyrepo push2006/finder-hsn-codee HEAD
9133270856bb77170956b707bafe260997690d80 via live repository source. render.yaml
nameshsn-ai-proxy/nodeproxy.js/free/node22, but actual deployedSHA unverified.
Public /health fetch503 is inconclusive(possiblecoldstart), NOT downproof.
Source has4providersinclNVIDIA/wildcardGemini/no modelallowlist; HITSMap60IP/10min,
trustsCFIP/FIRSTXFF, clearsALL>5000keys, no durable/shared budget/inflight. CORS*,
publicclientAPP_SECRET.2e6charbody,150sabortperkey, unboundedresponse/default
redirect/rotation. Do NOT inherit these policies. Repo hardening is later
separate work; no otherrepochanges/settings/providercalls in this unit.

Sources read:
https://github.com/push2006/finder-hsn-codee
https://hsn-ai-proxy.onrender.com/health

Validation only local disposableCAS/read-onlyfakeclient and closedplans.
No UI or visual change. No Atlas state/role/key/server/upstream accessed.

<!-- END-ORIGINAL-DOC -->


<a id="doc-080"></a>

### Reference: `integration/FINDER198BB.md`

<!-- ORIGINAL-DOC {"bytes":3827,"path":"integration/FINDER198BB.md","sha256":"ac54d70e1f71f4323f49a01d68af748a28fc3993e000192aa37949eb8d9764f4"} -->
# 198b-b same-document receipts and bounded transport, unselected

Default OFF. No production mount, client/env loading, account state, schema
migration, catalog entry enabling or live proxy request. AI catalog remains
EMPTY/DISABLED, NVIDIA excluded; ships require closed42codes+ALL. Tests use
local disposable CAS and mocked sockets/transports; no upstream network.

Reviewed v2 contract: SAME geo_intel.finder_budget198/shared-finder-v1 document,
schema2 with original counter/ticket fields +receipts64. Explicit owner-operated
preprovision/migration required, no automatic migration; v1 adapter unchanged.
RevisionCAS combines nonce/body/identity hashes receipt +budgetcounter+active
reservation atomically; second CAS transitions reserved->send_started BEFORE
network. Original60proxycalls/600s/global1inflight/norefund rules preserved.
Full64receipts failclosed; noTTL/drop/reset/archive. Nonce duplicate withdifferent
body/identity refuses. Same nonce returns status only, nevertransport/cacheanswer.
No prompt/response text, secret/sessiontoken stored. Receipt identity hash includes
required principal_hash plusoperation/provider/model/port. A future HTTP adapter
must derive this hash from authenticated UID on eachrequest, nevertrust caller's
principal_hash. This factory does NOT prove principal authentication itself.
Receipt hashes are private metadata, not a public status route. No mount here.

Receipts keepnoncehash/bodyhash/identityhash/fence/phase/start/deadline and only
complete response status/hash/length. State validatesclosedtypes/hashes/active
matching. UnknownCAS never retried; completed response is returned only if
receiptCAS succeeds in time. Lost CAS ack may leave complete receipt; a later
same-nonce call returns statusonly, never resends. Unknown/late/failure stays
send_started orunknown_held/globalhold pending explicit ownerreconciliation.
No takeover/expiryrelease. Manual reconciliation and futurearchive contracts
must exist beforemount; no clearing mechanism here.

Actual transport: exact fixed hsn-ai-proxy.onrender.com HTTPS443/routes, allDNS
answers checked public/nonmixed beforefirstsocket; pinnedpeer+hostnameverified
TLS, no redirects, oneconnection/no retries/fallbacks.20s parent supervised
whole deadline includes DNS/TLS/read;256MiB childAS/32FD/emptyenv/secret in stdin,
not argv/logs/errors. Fixed Host/Content-Type/x-app-token/Content-Length/Connection
headers only; no callerheaderforwarding. Request16KiB; response1MiB beforebody
reads, strictJSON content-type/identityencoding/unambiguous framing/no duplicate
headers; finite headercount/valuecaps. Late/partial/redirect/invalid/secret-echo
(includingJSONescapes)/childstderr/status/protocol anomalies held. Childkilled/
reaped on timeout. Installed childSHA checked beforelaunch. A model/path plan
is reconstructed from disabledcatalog/closedport set beforetransport.

Transport request20s <ticket25s allows receipt overhead, not a guarantee Mongo
will finish. Ledger operations timeout/concern failures remainheld. Brokerabort
DOESNOTproveproxy/providerstopped. UnitPROXYCALLS, upstreamattempt countunknown
(keyrotation). Independentbrokercaps doNOTrepairproxyCORS/XFF/quota/redirect/
rotation/server-secret exposure. Separateproxyhardening+ack remainsneeded for
end-to-endbudget. No currentdeployedSHA/key/model/freeentitlementfacts verified.

Source composition not an HTTPbroker: no loginUI/publicpasschange/198a mount.
Authenticated session+Origin+CSRF+singleworker/ownerDBgrant+liveproxyfacts are
latermountprerequisites. AI provider-specific request schema still laterwork;
AI disabledtoday so no payloadcanselecta model. No providerusage/paidcall tests.
Two clients with differentauthenticatedprincipal hashes cannotreuseonenonce.
No savedanswer/result delivery onduplicate; usermustretainoriginalresponse.

<!-- END-ORIGINAL-DOC -->


<a id="doc-081"></a>

### Reference: `integration/FINDER198C.md`

<!-- ORIGINAL-DOC {"bytes":2944,"path":"integration/FINDER198C.md","sha256":"9279c55c60256138ec86e2d6b9731cf9bc4a8a0a2a7dc42327d06891cf957992"} -->
# 198c default-OFF unselected server composition

No production mount/environment/client/provision/migration/provider/UI/live
requests. OFF returns original public callable unchanged, no collaborators.
Enabled factory requires exact injected closed AccountService, fresh1worker
evidence, v2ProxyReceiptBudget and enabledFixedProxyTransport. No construction
of these collaborators from env or guessed readiness. Publicnews/ownkey routes
pass unchanged; no whole-news auth wrapper. Existing production_entry unchanged.

Account gate now derives principal_hash from exact service._authed live session
UID returned after touch_session and Origin+CSRF checks, domain-separatedSHA256.
No caller UID/username/principal fields trusted. Storecontract guarantees live
account/revocation/expiry at touch; not an end-to-endtransactionthroughnetwork.
Accounts/helpers sourceunchanged, only narrowgateuse. Brokerhandler receives
only derivedhash, neverrawsessiontoken/UID/password. Tokens/secretsnotinreceipts.
A concurrentlogoutafterauthorization cannotrecallalreadyissuedupstreamcall;
no such guarantee implied. Singleworker/service/limiter invariants unchanged.

Exact POST /api/finder-broker/ships JSON nonce+port; POST /api/finder-broker/ai
JSON nonce+provider+model+prompt.16KiB cappedbody, duplicateJSON/unknownfields/
URL/header overridesdeny, no arbitrarypayload/tools/messages. Prompt<=8000chars;
provider-specificsingleuser payloads constructed internally,2048outputtokens/
temperature0.2. AllAIrefused by EMPTYcatalog; no enablingexistingclientaliases.
Everyrequestneeds exacthost/origin/live session/sessionCSRF beforebody/budget.
Unknownroutes/methodsdeny; allaccount routesremainpreauth/login/logout/whoami
only, signup/settings/mutations/UIdenied. No HTTPbudgetstatus enumeration.

Newread-onlyinspect_budget_v2 exactrole/mapping/noTTL/_id/schema2 checks, v1
inspect_budgetunchanged. No writepermission fromthisobservationalpreflight;
actualscopedownergrant/preprovision/credentialrole mustprecedelivefactoryuse.
Current preflightnotautomaticallycalledbyinjectedfactory; deploymentmustexecute
and bindindependentevidence beforeconstructingreviewedbudgetcollaborator.

CompletionreturnsboundedJSONbytes/statusfromtransport, no upstreamheaders/
backendtokenforwarded. Replay409onlyphase/status/length/cached_answerfalse,
neverreceipt/principalhash/fence/bodyhash/internalmetadata/cachedanswer. Errors
coarse/notrace/privatecontext. Unknowntransportwritesdurableglobalhold and
requiresmanualreconciliation, neverautoretry. Full64historyfailsclosed. Owner
archive/reconciliation/schema migration runbookmustexistbeforemount.

TestsonlydisposableMemoryStore/CAS/mockedFixedProxyTransport/fakeMongopreflight.
ActualAtlas/proxy/network/authrole/config/freecatalog/WSGIhttpsschemenotverified.
No UI/visualchange, Finderisstillasection/offlinepublic107networkOFF. Frontend
login/closedownercredentials andbuilt-inbrokerflow198d separate reviewedunit.

<!-- END-ORIGINAL-DOC -->


<a id="doc-082"></a>

### Reference: `integration/FINDER198D.md`

<!-- ORIGINAL-DOC {"bytes":2345,"path":"integration/FINDER198D.md","sha256":"8762d9da77f6c577f0d5f00597f5cf1fb2b2a1e8738d5d60cd1181e5a9336b13"} -->
# 198d source-only Finder account panel

Default OFF, unselected ES module controller and panel. No public route, launcher or existing Finder own-key path is changed. No signup/reset/settings UI, backend proxy token, persistence, polling or automatic retry. Browser cookies stay HttpOnly in the existing account service; protocol CSRF stays in controller memory. Enabled embedding requires explicit fetcher and cryptographic fresh nonce adapter, same-origin asset serving, policy review and independent live activation approval. This unit does not provide those live adapters or mount the panel.

Finder remains a section. The local mobile fixture's public news header and Finder section demonstrate composition, not the deployed dashboard. Own-key source byte hashes are unchanged. AI button and controller remain disabled while the server model catalog is empty. Ships controls now use the complete static 42-port catalog, plus ALL, pinned to the preserved proxy source by unit 226. Structured ship rows use literal text only, with bounded raw JSON retained. Response cap is 1MiB streamed before consumption; requests have a 25-second browser deadline with no retry. A timeout only means outcome unknown, not upstream cancellation.

Unknown, held and replay block further requests within the controller, including across sign-out/sign-in. Any broker 401/403 is held too because an upstream refusal is not proof no upstream request occurred. Reloading is not reconciliation: in-memory UI state is lost but server durable global holds/receipts remain authoritative and must be checked by the owner. Never use a new nonce as a recovery bypass. A successful request displays response text but is not entitlement or delivery proof. Sign-out failure clears local protocol material and explicitly says server sign-out was not confirmed.

Fixtures use synthetic credentials and intercept all operations. Mobile 320/390 screenshots and state tests are not live end-to-end proof. Real single-worker evidence, HTTPS direct WSGI origin, auth database write scope, preprovisioned schema2 budget, receipt reconciliation/archive, proxy credential acceptance and deployed upstream SHA still gate mounting. No workflow or live settings are changed.

The route_contract broker_transport label now reflects whether a handler was injected. UI remains unselected.

<!-- END-ORIGINAL-DOC -->


<a id="doc-083"></a>

### Reference: `integration/FINDER198OPS.md`

<!-- ORIGINAL-DOC {"bytes":4505,"path":"integration/FINDER198OPS.md","sha256":"5cf1d9f9748b951108959bb9992299ca56a16778b7ea7c7404e401b1d45d29b8"} -->
# 198-ops retained receipts snapshot and reconciliation classification

Unselected read-only source. Exact schema2 whole budget, window counters, revision, fence, active ticket and every retained nonce/body/identity/response hash are preserved in full. Hash-only receipts are all the broker stores: answer text, request body, raw nonce and principal UID are not recoverable from them. Do not describe this as a full answer backup. No v1 migration, client/env/HTTP route, private data upload, provisioning, active clear, history prune, quota refund, window/fence reset, replay or retry. No transition function is supplied.

128KiB output cap, exact schema validation and bounded plain-value inspection before serialization/copy; actual serialized output is re-read and validated. Corrupt linkage, missing active receipt, orphan uncompleted receipt, duplicate identity/schema/JSON fields or unreadable data fail closed. Two equal reads detect visible source changes, not a transaction, quiescence or proxy cancellation. Separate owner scope covers real database reads and a private destination/access/retention decision. Snapshot includes hashes which may still be sensitive correlation identifiers; do not publish it.

## Classification, never settlement

- Reserved: no recorded send-start, not proof unsent. A failed CAS acknowledgement may have landed; query authoritative state and confirm workers stopped before drawing conclusions.
- Send-started: upstream may have received it. Timeout, browser abort, connection loss or expired deadline do not prove no provider attempt.
- Unknown-held: keep global hold. Do not issue new nonce, switch keys/models/providers, refund a proxy call or retry because no answer arrived.
- Complete: recorded bounded proxy response metadata, not end-user answer delivery, valid AI meaning, free entitlement, provider-attempt count or proof of upstream key rotations. Snapshot has no cached answer. A 4xx/5xx complete receipt remains a consumed proxy call.

All classification results explicitly deny retry safety, refund, active clear and capacity release. A retained lookup miss is not lifetime absence. Snapshot alone does not solve the 64-receipt cap. A later immutable replay archive and schema-aware atomic rollover must keep claim/status lookup across old nonce identities before any capacity release or sustained use, with cross-UID identity and body mismatch checks retained. No archive deletion/reset shortcut.

## Owner-operated runbook, not live authorization

1. Keep built-in broker OFF, independently confirm stopped local processes and determine upstream state through approved proxy/provider evidence. Browser abort is local only. Preserve original active ticket, receipt phases and counters regardless of deadline.
2. Approve exact read account, database, source mapping and private snapshot destination separately. Capture the full retained document, read actual bytes back and validate. Record source revision/fence/time/access scope outside the artifact; do not include keys or passwords. Keep source unchanged.
3. Match original nonce hash, body hash, principal-scoped identity hash, fence and ticket to authorized proxy logs/evidence. Inspect whether send-start CAS and network attempt could have occurred, including acknowledgement loss. Missing logs are not proof no request. Cross-user receipts cannot authorize sharing private owner data.
4. Require evidence that the relevant upstream attempt ended and any provider attempts/rotations and final response are accounted for. A health endpoint, current-key presence, timeout or later success is not that evidence. If any part is unknown, keep the ticket held and report the gap; never fabricate complete response metadata.
5. Any release/settlement or reconciliation mutation needs a separately reviewed schema protocol and the owner's scoped approval of the exact ticket/evidence/transition. This unit only classifies; it never applies an operator's claim as authority. Quota remains consumed, fences monotonic, archived nonce replay identity retained. No automatic deadline takeover.
6. Before live mounting: exact auth database role/write permission, verified single worker/direct HTTPS origin, preprovisioned v2 dedicated budget role/no TTL, deployed proxy SHA/private credential acknowledgement and fixed-model/free entitlement evidence, archive/replay-capacity protocol and host proof remain separate prerequisites. AI catalog stays empty/off until verified; owner OK live remains required.

<!-- END-ORIGINAL-DOC -->


<a id="doc-084"></a>

### Reference: `integration/FINDER_NESTED_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":5934,"path":"integration/FINDER_NESTED_LIMITS.md","sha256":"fae0cd7ffdc87848c2b41df262c84ccf4b0a34c8ab8e36b723858b0bd0574f7b"} -->
# Nested Finder capability check and shortlist scroll port

Offline Chromium at actual /workspace iframe verified code090121 detail, merged-origin clipboard link, favourites/shortlist/notes persisted after reload, original shortlist CSV download with exact fields and literal note, and print button invoking window.print. Native print dialog/PDF export not verified: the invocation test replaces print with a counter in the frame DOM world. Real clipboard write/read uses browser permission for the throwaway loopback origin, not a stub; production clipboard permissions/browser support remain to test.

At outer390px/iframe360px the preserved shortlist table was390px wide and clipped Remove. Narrow served-preview transformation wraps the exact original table string in a keyboard-focusable horizontal-scroll region with scoped overflow style. Mobile iframe/root widths now360/360; right-hand Remove visible after horizontal scroll, actual pixels inspected. Original index/src/offline assets unchanged. CSP inline-script hashes recomputed by existing private-route response handler after transformation. Transform fails closed when exact table seam changes. Style goes before first real head close (original script also contains generated-document head closes).

This does not rewrite source data/codes/notes/settings/share destination. Copy handler already derives location.href so merged route works without changing original identifiers; JSON-LD original public-origin reference remains a separate metadata consideration. Downloads intentionally remain original CSV behavior (quotes/BOM); spreadsheet formula defense is not added here, so untrusted notes could be interpreted as formulas in spreadsheet software, an existing source behavior needing separate review.

Loopback no external attempts/page errors. Test command in the existing configured repo: /tmp/phase1-venv/bin/python tests/browser_finder_nested.py; focused unittest: python -m unittest tests.test_finder_nested. Browser needs installed Chromium+Playwright and current root index/data snapshot/assets. Review bundle contains these two test sources, transform, changed news_api and this limit doc; it is an increment for the full existing repo, not a standalone whole-repo runnable archive. Full-suite proof will run in real tree after review.

V2 insertion gate selects exactly one head-close/body boundary outside all script spans, refusing ambiguity. Removing the exact STYLE and reverting REPLACEMENT restores original bytes. Fake head/body strings inside scripts are never insertion targets. Tests compare every served inline script SHA to CSP header and assert counts unchanged/no script unsafe-inline. Note the exact hash set cannot equal pre-transform set: table wrapper is inside the original UI script, so exactly one UI-script hash changes deliberately; all other original script hashes stay equal. Existing offline opt-in adds its own reviewed bootstrap script before served CSP hashing.

Browser test now asserts actual geometry: region scrollWidth greater than clientWidth, Remove extends beyond region before scroll, its full bbox is within region after scrolling. Region can receive keyboard focus; native ArrowRight/keyboard scroll across every browser remains unverified. Offline.html is deliberately not transformed; its original offline shortlist may still clip at narrow widths.

V3 keyboard check: Tab from Print actually focuses region, End/ArrowRight produce nonzero scrollLeft without a programmatic scrollLeft assignment; bounding-box reachability checked after that. Single Remove lookup assumes the one-item fixture only. First review bundle finder-nested-review.zip includes changed news_api.py; v2 delta includes transform/tests/docs only. Browser CSP listener finds expected default-off Frankfurter connect-src refusals on detail load; zero script/style CSP violations, not zero all-policy events. Original FX calls remain blocked, no production network enabled.

CSV safety increment (served preview only): exact original quote-helper seam replaced. Columns/order/BOM/newline/CSV quoting unchanged; notes remain unmodified in browser storage. Download cells with first meaningful character=,+,-,@ or leading tab/CR/LF gain a literal apostrophe, including whitespace/Unicode-format hidden prefixes. NUL removed and unpaired UTF-16 surrogate replaced; valid surrogate pairs retained. Intentional text-safety difference from source CSV, not byte parity for affected values. Defense reduces common formula execution on first open; re-saving/editing/import settings in spreadsheet software can strip the apostrophe, so do not treat arbitrary CSV as permanently inert. Offline.html CSV retains original behavior and is not hardened in this increment.

Focused command now includes Node.js execution of the actual injected quote function across formula/hidden/control/negative/quote/non-BMP fixtures; genuine Chromium download contains apostrophe-prefixed formula note while UI note stays unchanged. Original code/source assets remain preserved. Increment review bundle includes finder_nested.py, news_api.py, tests and this document, requires existing real repo/Node/Playwright/Chromium/root snapshot. No production activation or real notes read.

CSV compatibility hardening: no regex lookbehind or toWellFormed dependency; a simple UTF-16 loop repairs lone surrogates and preserves pairs. Existing app browser baseline still requires modern Unicode-property-regex support used in the prefix probe; legacy-browser whole-app support is not claimed. C0/DEL/C1 controls including U+0085 also skipped when checking first meaningful character. Negative numeric cells receive apostrophe deliberately. Header and every shortlist column pass the original q helper, verified against source. Other /api CSV exports are outside this narrow seam increment and need their own consistent safety review; no claim all app exports now share this helper.

<!-- END-ORIGINAL-DOC -->


<a id="doc-085"></a>

### Reference: `integration/FINDER_NETWORK_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1509,"path":"integration/FINDER_NETWORK_LIMITS.md","sha256":"a5b3d3ecc8dfddc53374853649e1f0d4468d7a90be1a367b2ae35abe085da768"} -->
# Finder external feature preview port

Default off. FINDER_NETWORK_PREVIEW_ENABLED accepts exact true/false; no Render setting is changed here. Explicit opt-in changes only Finder HTML connect-src to seven fixed original HTTPS origins (NVIDIA excluded by owner scope). It permits original AI proxy, optional user-key providers, currency and weather requests; it never creates a forwarding proxy or accepts arbitrary destinations. Private auth and other pages' CSP stay unchanged. Network opt-in remains separate from owner approval to disclose AI prompts to providers. Original browser personal-key behavior is preserved, not a server-secret solution.

Served private Finder HTML suppresses original AIS retry/refresh timers using an exact fail-closed seam; polling remains off. Original index/source bytes remain unchanged. In this preview users can load ships manually and hide/reopen to refresh. Automatic60-second live tracking is not silently enabled by network opt-in.

Fixture browser tests intercept every external request before network. Verified original AI plain-words, INR/USD FX, AIS and weather/marine UI render against simulated responses, no browser errors at390px. These tests do not prove current provider availability, CORS, quota, account ownership or proxy operation on the real preview origin. Live activation must be separately approved; real provider/CORS/auth validation comes at that gate. Model descriptions and free-tier claims inherited from original code are not verified here.

<!-- END-ORIGINAL-DOC -->


<a id="doc-086"></a>

### Reference: `integration/FINDER_OFFLINE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2969,"path":"integration/FINDER_OFFLINE_LIMITS.md","sha256":"e8378108d5c4c7599c90054b4374357031f351c41be8e71ad5ed3c38ddd4dbbc"} -->
# Public-only device offline Finder

Original offline.html is served through a reviewed served-copy seam; original files untouched. User explicitly clicks Store public snapshot on this device before any worker registration or fetch. Worker scope exactly /workspace/finder/, caches exactly /workspace/finder/offline.html. Self-contained public tariff/trade snapshot only. Never cache/intercept protected index, /workspace, /api, accounts, news, login, session or digest routes. Cached offline snapshot intentionally works after session expiry because it contains only public data; this does not authorize any other cached route.

Offline copy removes proxy URLs/token/shared keys, replaces localStorage access with no-op session state, disables fetch with a local rejecting function, removes AIS refresh/retry timers, has connect-src none plus only hash-approved inline scripts. It includes no injected private-news/account content. All original key/settings reads and writes are disabled in this copy. Original online Finder may already have provider keys/notes/AI output in same-origin localStorage; offline does NOT read them, and clear-cache does NOT remove them. Clearing those originals requires their own settings UI/user choice. Favourites/shortlist/notes in offline copy are page-session-only, unlike original persistence, and this difference is stated in banner. Network-dependent AI/FX/weather/AIS are deliberately unavailable. Existing original section UI may still show AI settings/fallback help, but cannot fetch or retain a supplied key offline.

Offline response initially still requires private preview access to download. Default registration OFF. Install refuses non200, redirect, wrong content type or missing server public-snapshot marker. Clear button unregisters only this scope+worker URL and deletes only geo-public-finder-* caches, no other workers/data. Snapshot install failure visible. Quota/incognito restrictions may prevent20MB cache; install-time failure has no success claim. Safari/iOS install behavior and real hosted HTTPS not tested; Chromium loopback offline fixture verified. App-wide installable manifest remains separate; narrow Finder manifest starts offline snapshot. Default online/new index continues to require authorization.

Source contains public proxy access token in original app (speedbump, not permission/credential authority). Offline copy blanks it; it never supplies approval to use the network.

Final selfcheck: in-memory UTF-8 transformed response ignores Range, never returns206 raw source; meta+header use same inline-script hashes, no unsafe-inline script permission. Source token/nonempty built-in key values absent; sessionStorage/indexedDB/document.cookie patterns absent. Worker date-independent cache namespace tied to pinned offline SHA cfc66f0e2234. Same-scope old sw.js unregistered on clear, old hsn-data-* caches removed on activation/clear. Registration waits only when worker not yet activated.

<!-- END-ORIGINAL-DOC -->


<a id="doc-087"></a>

### Reference: `integration/FINDER_PARITY_PLAN.md`

<!-- ORIGINAL-DOC {"bytes":10360,"path":"integration/FINDER_PARITY_PLAN.md","sha256":"d263bfd47db901e3234158758fa2f3d8547862e7bc7cd64c982edaf6c17cbf10"} -->
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
| Finder | Share/print/export/settings | Nested Chromium code/favourites/notes/clipboard merged-link/CSV fixture; 228 popup CSP-safe pagination, intercepted print invocation and rendered PDF (dfec6589, REPORT228.md, browser_report228.py); 232 offline CSV safety and keyboard scroll fixture (c7b231d6, OFFLINE232.md, browser_offline232.py) | Native OS print dialog, real AI and all-browser proof open; offline session-only state retained; JSON-LD standalone origin remains |
| Finder | PWA | Public-only offline snapshot preview; explicit device opt-in and clear cache | Hosted HTTPS/Safari/quota tests; page-session offline settings, never protected news/cache |
| Geo | Read/filter/sort/loaded stats/CSV/signal adapters | Works in offline tested preview | Production signoff remains gated |
| Geo | Events snapshot | Injected bounded read-only adapter + gated supplied-event original digest preview reviewed | Production collection/client/socket budget identity and real composition unwired |
| Geo | Collection/classifier/scoring/credibility/corroboration/dedupe | Present but unwired | Single Geo-only collector composition, no live execution |
| Geo | Apps Script digest/sent-marking/critical/weekly/channel delivery | Original HTML dry-run previews wired; supplied original-compat queue renderer fixture reviewed, not actual unsent queue; delivery unwired | Port original delivery contracts; approved Apps Script path, no SMTP replacement |
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
| Reports | Original digest/critical/weekly dry-run HTML; supplied gated events with UTC clock | Actual unsent queue/claim, Apps Script send/receipt/mark integration and alert scheduler; supplied queue renderer and aggregate retention audit are offline only, not receipt/lossless backup proof | SMTP replacement (owner chose Apps Script) |
| Streams | Original supplied YAML fidelity, strict parsing, RAM add/delete copy; captured original panel | Persistent YAML/store edit, cross-worker locking, fresh source read, availability checks, player integration | No new separate BRICS news collection |
| Finder | Existing source/snapshot; nested code/notes/favourites/CSV/clipboard; 228 popup/PDF/intercepted-print fixture (dfec6589, REPORT228.md); 232 offline CSV/scroll fixture (c7b231d6, OFFLINE232.md); PWA public-only offline fixture | Real network/CORS/provider disclosure, native OS print dialog/real AI/all-browser proof, hosted PWA/Safari/quota, JSON-LD origin | None |

Remaining work is not a reason to activate unsafe defaults. Preserve originals and complete offline contracts/tests while production choices stay explicit. Fixture accumulation cannot satisfy live source, delivery or account readiness. No claim of full merged parity is supported yet.

<!-- END-ORIGINAL-DOC -->


<a id="doc-088"></a>

### Reference: `integration/FINDER_SNAPSHOT_NOTES.md`

<!-- ORIGINAL-DOC {"bytes":1029,"path":"integration/FINDER_SNAPSHOT_NOTES.md","sha256":"f17380d3c633e8dc55248303f209bcda6805006b5354f63a3c7fdecaa06375e4"} -->
# Finder snapshot reconciliation

Ported original snapshot from upstream asset data.17204075ad25.js, SHA25617204075ad25512b76900835aca83960c82ed8d9e8a997c4e23e954713d89330. Hash refers to JS asset bytes, not HTTP wire compression or decoded JSON.340,232 core code rows unchanged; inline application455,031 UTF8 bytes (454,994 characters) unchanged. Loader changes data filename;10 upstream branding lines copied, served private head still replaced by merged branding.

Partner context adds740400 and871120. Sanctions adds58 OFAC rows and removes1 EVER SHINING LIMITED row (75106->75163). This is a source-snapshot change, not a legal-clearance decision or independent official-source verification. Source says auto-refreshed2026-10-04; UFLPA throughAug2026 remains supplied unchanged. Prior bundle retained locally/in backup for rollback. Original upstream tradepartner/sanction source literals, service worker fingerprint and offline artifact ported together. Offline/PWA merged execution remains queued, not proven by HTTP200.

<!-- END-ORIGINAL-DOC -->


<a id="doc-089"></a>

### Reference: `integration/FIXED_PARSER_PIPELINE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2570,"path":"integration/FIXED_PARSER_PIPELINE_LIMITS.md","sha256":"ecbc3c258a54805f7ce2b9d097fb14ff9b9cf84ad141cc0876ed185f27d4a681"} -->
# Existing fixed parser -> supplied enrichment/document composition

EXACT existingseven85CASESenums, no newcorpus/bytes/URL/path/childconfigsurface.
RuntimeONE85resourcechild, thenONE80whichalreadycalls64. No secondruntimeparse/
docloop. Child10swallbound applieschildonly; boundedparentprocessingnot10spipeline
claim. No liveRSS/XML/fetch/fulltext/storage/mail/Telegram/providerhealth orready
sender. SyntheticTruecallerassertionnotprovenance/secretdetection, staysprivate.

Rawconfig/outcomes snapshot+wholeintersectionvalidation beforespawn:exactcategories
1..100,maxchars1..9997,boolflags,finite0<threshold<=1,maxitems1..100,exactclocks
fixedawareUTCyear1970..2100,closedconsistentoutcomes/whitespacekey/UTF8refusal,
shared1MiB/5000nodesincludingconfig. Sourcepins85runner/child/corpus/hashSDKmanifest,
81/80/64/originalRSS/extract/classifier/dedupe/plain/82snapshot beforechild;
SDKphysicalpinscheckedin85child,dateutil2.9.0.post0. Trustedimports beforechecks,
driftguardsnothostilesandbox/loadedmoduleauthentication. Originalsource unchanged.

ParentpublishedISOconvertedexactbuiltin datetime/timezone, samefixedoffset/instant,
UTCboundaryvalidated. Independentselectedcopyto80prevents in-placeenrichmentalias.
Missing/unusedoutcomesrefuseafterreversiblefixedparse, no partialresult. Disabled/
unavailable requireemptyoutcomesbeforechild andprepareoriginaldocsunchanged.
Bozometadata NOTsourceerror; empty/bozoempty selected_empty, nothealthy/current/
complete. PreserveSDK.getpresencealiases, notrawXMLtagproof,81datepolicyDEVIATION/
unverifiedfallback. Futurefixturedate maypasscutoff. PythonnetworkguardnotOSfirewall,
Expatbinarynotpinned,parentprotocolnotmaliciouschildauthentication.

Finalindependentselected/enriched/docs/diagnosticcontainers, entirewrapperincluding
redundantcopiestraceskeysstringsnotice countsONE1MiB/5000node outputbudget before
return. NoIDs/emailed/save/claims/mark/sendenvelope. Text suppliedsyntheticoutcome,
notfetched/verified/lossless fullarticle; docs originalpreview<=300. Telegramfull
contentpreservation/durablebackup remainopen, notsilentlydropped.

6authorfocusedPASS RSS/Atom/bozo/empty,missingunused/disabledunavailable,allsourcepins
andmalformedbeforechild,nonUTCoffset/dateboundary,outputduplicationbudget/isolation.
Independent80originalAST+64looporacleusesSECOND85childINTESTONLY forselecteddata,
shared85/81datepolicyexplicitlynotnewdateindependence. Values/order/dates/docs
compare, notflag/countonly. Existing80testscover199/200/201 independentofXMLcorpus.
NoUI/visualartifact. Fullsuite/independentreviewpending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-090"></a>

### Reference: `integration/GEO_ARTICLE_WRITER_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3239,"path":"integration/GEO_ARTICLE_WRITER_LIMITS.md","sha256":"1de66dab3c2ce5c4e0695637197d1c755810c4b3ad3ff12fde6999e82d6fdf48"} -->
# Injected Geo article writer: no activation

GeoArticleWriter maps only geo_intel/articles and accepts an injected client.
It never uses the read facade or creates a client, URI, index, route, scheduler,
mail, Telegram send or collector. Developer review requires the exact mapping,
write permission, verified unique URL index and source contract. This attestation
is self-declared, not owner permission. Real writes still need Push's approval.
The live client must be a reviewed PyMongo MongoClient with bounded connection,
socket and pool settings, suitable write concern and least-privilege credentials.
None of those live facts have been checked. This is not a hostile-client sandbox.

Input is the closed original post-fetch document contract. Caller IDs, emailed
and created_at overrides are rejected; Telegram ID must be null and URL empty.
The explicit fixed-zone clock supplies created_at in UTC. The writer takes a
bounded exact-built-in snapshot before validation: at most 1000 documents,
100000 visited nodes, depth 8, bounded fields and 2MB compact JSON. It rejects
summaries over 300 characters and scores outside [-2^53, 2^53]. The full batch
is validated before mapping or writing. Concurrent caller mutation is not an
atomic snapshot, but only the captured copy is validated and submitted.
Empty batches do nothing. insert_many(ordered=False) preserves the original
bulk path and missing emailed field. The driver gets its own list; attempted
count is captured separately so driver mutation cannot change reported totals.

Lookup and method binding failures cannot be classified as insert errors.
Only the insert invocation's BulkWriteError is classified. Receipt attributes
are read once; receipt exceptions are uncertain. Details access is redacted;
consumed receipt fields are captured as exact built-in values before parsing.
Confirmed counts require nInserted plus unique error indices to cover the whole
batch, no write concern errors, and final count coherence. URL duplicates need
code 11000 and exact integer keyPattern {'url': 1}. Other key failures are
failed, not URL duplicates. All non-URL failures still use state 'partial'.
SON document_class or double-valued keyPattern yields uncertain; pre-4.2 servers
missing keyPattern yield failed. This intentionally prefers uncertainty to a
false duplicate claim.

Network, malformed, unacknowledged or write concern outcomes are uncertain:
inserted/duplicate/failed counts are None. Writes may already have happened.
No retries, raw error text or IDs are returned. Partial/uncertain outcomes need
source reconciliation under a separate grant; recovery is not implemented.
Original BulkWriteError's loose len-minus-errors estimate is not reused.

Tests: 22 focused tests with native PyMongo 4.8.0 passed locally and from the
extracted bundle. Independent v4 review passed 20 tests with PyMongo 4.18.2;
the final two bounded-input checks were reviewed by own tests and sanity diff.
Repro: python -m unittest tests.test_geo_article_writer -v. Dependencies:
python-dateutil 2.9.0.post0, PyMongo 4.8.0, Flask 3.0.3, Werkzeug 3.0.6, PyYAML 6.0.2.
Tests use fake driver clients only, never a real database. No durable stream or
account store is wired by this increment.

<!-- END-ORIGINAL-DOC -->


<a id="doc-091"></a>

### Reference: `integration/GEO_COLLECTOR_CONTRACT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3835,"path":"integration/GEO_COLLECTOR_CONTRACT_LIMITS.md","sha256":"ec5c229454d3063dbcc805c5cfd238e63048670f40250ab3dc0e3ca5d093db6e"} -->
# Original Geo post-fetch candidate/doc/store contract, offline only

Explicit already-fetched/enriched candidates only, no provider collection or
full-textfetch. Hash-pinned originalRSS AST statements classification loop,
dedupe, activecategoryfilter, document comprehension. No collect() execution,
originalimports/config/db/scheduler/thread/Telegram/mail/indexes/route/client.
Original classifier/dedupe pure modules reused. Network/errorsourcepolicy/
providerdate parsing/actual enrichment remain separate collector work.

Preserves class-before-dedupe/scorekeeper/corroboration/300charpreview/published
isoformat/credibilitydefault/Telegramemptyplaceholders. Unlike earlier generic
FakeCollectionWriter, originalRSS path DOES NOT add emailed=False: original
bulk save only adds created_at. This absence is deliberate original parity;
original unemailed query matches missing/null emailed. CallerIDs/emailed/times/
Telegram overrides stripped. Published exactdatetime/fixed timezone required.

GeoFixtureStore exactsealed in-memory fixture, no arbitrarywritercallback. URL
insert-only/created_atUTC/explicitsyntheticfailed versusduplicate, no livewrites.
Up to1000input/retainedrows, boundedplainfields; too many accumulatedrows rejects
before mutation. Original MongoBulkWriteError's loose len-writeErrors estimate
not claimed real outcome proof. Separate futurewriter must classify failures
honestly, not label arbitrary storageerror duplicate. No eventsseed invention:
original EVENTS currently [{}], unavailable until proper authoritativeseed.

Telegrambackup remains in untouchedoriginalcode but disabled/unwired here,
never silently dropped from productfeature inventory. Shortsummary notfulltext
retention proof. Actual fetched-versus-displayed/losslessretention remains OPEN.

Repro python -m unittest tests.test_geo_collector_contract -v after install
python-dateutil==2.9.0.post0 plus existing configured deps. Bundle includes all
originalRSS/classifier/dedupe source+integrationdependencytree.7focusedtests
include differential full originalcollectAST with inert feed/thread/store oracle,
exactdocs/noemailed/corroboration/defaultplaceholders, storeclock/duplicatefailed,
hashrefusal/override stripping/invalidinput/filter/empty/no arbitrarycallback.
Not fetching or persistentstore or full originalcollector integration parity.

V2 accepts exact reviewed dateutil tzutc/tzoffset/tzlocal original-parser dates,
normalizes them to fixed datetime.timezone offset before contract execution.
Preserves instant AND original isoformat. Original parse_date makes naive input
UTC-aware. Differential GMT/+0530/naive/Z cases pass. Other custom tzinfo types
rejected. Raw naive datetime (not passed through original parser) still rejected.
Classifier/dedupe sources now hash-pinned before lazy import alongside RSS.
This is source-integrity check, not hostile-Python sandbox or protection against
in-process module monkeypatching.9focusedtests include parsing/sourcepin cases.
Retained guard excludes explicit failedURLs (won't be inserted), no artificial
capacity failure from synthetic failedcandidate. Input bounds per-field/count,
not aggregate bytes/runtime proof: fuzzydedupe quadratic, copied text batches
can be large; add aggregatebytes/time/worker budgets before widerexposure.

Freshv2reviewSAFE9/9,250own differentialbatches0diffs; timezone cases UTC/NY/
Kolkata checked. Pins cover disk bytes, not loaded-module object identity.
Far-past UTC clock conversion may raise OverflowError (store unchanged).
Summary>10000chars rejects whole batch rather than individualskip; original
fulltextmax bound must be checked before widercollectorwiring. Caller must strip
title/URL exactly like originalfetcher; this seam doesn't strip again. Same-run
URLduplicates accepted, store firstinsert then duplicate. No cleanup by user.

<!-- END-ORIGINAL-DOC -->


<a id="doc-092"></a>

### Reference: `integration/GEO_EVENTS_COMPOSITION_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3092,"path":"integration/GEO_EVENTS_COMPOSITION_LIMITS.md","sha256":"7131804831955b0a9aa1a9311dcbbd6f1bcebf31ba91f934e4e430b5737da27c"} -->
# Separately gated Geo events and original digest read composition

NEWS_EVENTS_READ_ENABLED=false default. True requires NEWS_READ_ENABLED=true,
private preview access and NEWS_EVENTS_MAPPING_VERIFIED=true before client.
Exact geo_intel/events only; no override inferred from article mapping. Explicit
GEO_EVENTS_ALLOWED_HOSTS comma-separated public hosts, no whitespace/duplicates,
max20 hosts/2048chars. Host catalog is display link safety, NOT source ownership,
credential read authority or policy approval. Dedicated read-only Atlas user
must separately cover exact events collection. No real credential verified.

Uses the SAME gated narrow Geo client, not BRICS/client2. No writes/commands/
aggregate/indexes. Existing article reader unaffected, events off maps none.
ReadOnlyEventsReader preserves inclusive UTCtoday..today+90day query, ascending
event_date, projection with _id excluded,1001row overflow guard/1000cap,2MB
snapshot/16kfields/query2s/cursorclose. DashboardSnapshots filters display
labels/links then caps100; digest additionally applies its90day window.

Only original digest includes events, matching existing report behavior.
Critical and weekly report paths don't read events; no invented new block.
Hash-pinned source renderer loads AST definitions only, no original config/DB
imports/SMTP functions. Existing reports remain bounded supplied article samples,
not current unsent queue/full-history weekly statistics. No mail/mark/scheduler.

Events failure becomes unavailable panel, not supplied_snapshot with zeroitems.
Article reads remain available if events fail. No automatic polling/retry loop;
manual request may attempt source again. Shared client lifetime remains article
failure close-once/latch; event failure cursor closes but doesn't close client.
Unavailable metadata is visible even when original HTML omits event section.
No live source read/deploy/environment change by this increment.

4 focused composition tests PASS in rebuilt configured environment. Finder
index seam mocked as synthetic context, NOT original Finder parity proof.
Pinned original renderer source restored from backed repository and hashchecks
run in test. Tests private403/gates before constructor/exact query projection
sort/limit/maxtime/close/originaleventblock/errorunavailable+articlesstill200.
Review bundle includes integration dependency tree, test helper and three
original report sources. Installed Flask/PyMongo/PyYAML required, no rootFinder
assets needed for these4tests. No hosted proxy/schema/index/permissions proof.

Real events documents not checked. BSON datetime event_date or numeric confidence
won't satisfy bounded string reader contract, may show unavailable until real
one-time source check. Both events+articles must be independently covered by
read-only Atlas role. Punycode display hosts rejected by existing public_host.
Add short bounded cache before wider exposure; current per-request opt-in path
has no cache, polling or background retries. Fresh independent review SAFE,
4/4PASS reported; no real-document validation inferred from fixtures.

<!-- END-ORIGINAL-DOC -->


<a id="doc-093"></a>

### Reference: `integration/GEO_ONLY_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2153,"path":"integration/GEO_ONLY_LIMITS.md","sha256":"c7987ba25cbb982a42c9131bd2dc902895eb37aff066b8972302430b412b64de"} -->
# Geo-only stored news composition

Geo news is the sole stored news view. geo_intel/articles is the user-identified mapping. Any nondefault GEO_DATABASE/GEO_ARTICLES_COLLECTION pair requires a separate GEO_MAPPING_OVERRIDE_VERIFIED gate after source ownership/schema review. newsbot/admin/local/events database names and events/oplog/admin/local collection names are denied case-insensitively even with that gate. No BRICS target or migration. Existing old newsbot store and original engines stay preserved but are not loaded by this separate composition. Events, admin and local are excluded. Live streams remain browser configuration independent of stored news.

compose_geo_only is now selectable through build_preview by explicit
PREVIEW_GEO_ONLY_ENABLED=true (default off). private_router uses that launcher;
legacy compose remains unchanged. No operator settings/deploy changed. Direct compose requires injected factory. private_router now selects a lazy
narrow read-only facade for explicit Geo-only/read-on flags only. Private login config + NEWS_READ_ENABLED + NEWS_STORE_MAPPING_VERIFIED + explicit URI required before client creation. Factory connect=False, bounded reads100, no indexes/update/insert/write. Finder index/local exact-HSN reader retained when access configured. Failure closes supplied client and redacts connection errors.

Default read-off creates no client and news view remains empty. Screenshot mapping/schema is evidence, not verification of live credentials, permissions, rate-limit suitability or old/new cutover. URI should be configured through secret environment by the owner, never in browser/source. No deployment or live database action performed.

Request-time find/sort/cursor failures close the sole client once and latch reads unavailable. Later requests remain503 until the composition is rebuilt after operator review; no automatic retry or second client. Guarded read uses a lock for request concurrency. Raw errors never returned to UI.

Separately gated events composition now exists; see GEO_EVENTS_COMPOSITION_LIMITS.md.
Article mapping exclusions unchanged; events mapped only via independent flags.

<!-- END-ORIGINAL-DOC -->


<a id="doc-094"></a>

### Reference: `integration/GEO_PROBE_HTTP_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4832,"path":"integration/GEO_PROBE_HTTP_LIMITS.md","sha256":"32395d1bd216b46c805f0759723090bcb3adac58779641e50ad623110be5d40d"} -->
# Separate private manual sample-check app, offline only

create_probe_app explicittrustedconfig only. No env/readstandardlauncher import,
route addition to main app, proxytrustselection/deploy/sourcegrant. Reuses single
workerPreviewAccess/login, secureHostcookie/origin/twohour authentication, csrf
forprobePOST. AuthouterWSGI beforedispatchunknownpaths/methods. POSTexactOrigin,
urlencodedonly, singlecsrf/noextras/noquery. Allstatusesprivate/no-store/noindex/
nosniff/defaultdenyCSP. FormonlyGET; responsefixedsmallJSON. Noautomaticfetch.

ModuleglobalnonblockingLock and10minattemptcooldown acrossappinstances; failures
consumecooldown, noqueue/retry/polling. Stateperprocess/resetonrestart, notdurable
or distributed. OneGunicornworkerrequired. NoDBstatus exposed withoutlogin.

FixedexecPythonmodule child, minimalGEO_MONGODB_URI+LANGenv, noURIargv/shell/fullenv.
Child loggingdisabled,stderrDEVNULL, popsURIenv beforeprobe, emits fixed result.
Secretremainschildmemory duringoperation and initiallyprocessenv; authorizedOS
inspection is not isolated. StartupPython/libraryerrors could depend on platform;
no blanketplatformloggingcertificate. Trustedrunnernotuntrustedexecutableinput.
Parentselectors reads<=4096byteUTF8strictresultschema;10secondbudget, timeout or
malformed/nonzeroresult=>fixedunavailable. Kill/wait/close onnormal/error/control.
Clientownedchild; nochildren expectedfromfixedcode. Parentkill targetschildonly,
notarbitrarydescendantprocesses. Childmustnothostuntrustedplugins/hookspawners.

10s clock/select/read/poll budget isn't finitewholeHTTP/ingressdeadline orhard
processspawnbound. kill/waitcleanup canitselfstall atOSlevel; no guaranteed10s
requestcompletion. Clientdisconnectdoesnotinterrupt synchronousWSGIexecutor;
childnormallyfinishes/timeouts, thenlockreleased. Actualnetworkslowclient/
disconnect/Renderproxy tests notyetperformed. GUNICORN timeoutmustnotbeclaimed
asrequestcancel+childcleanup proof. Parentworkerforcedkill could orphanchild;
hostactivationrequireslifecycleproof orstrongerprocessgroup/watchdogdesign.

15nativeofflineHTTP/process tests:authpathmethods/loginCSRF/origin/query/type,
fixedresponses/crossinstancecooldown/busy/controlrelease/importinert,realexec
success/malformed>4096/nonzero/stderrdiscard/immediateclocktimeout/childkillwait,
strictschema/invalidURI/childenvpop. Timedtest usesforcedclockadvance, not10real
secondnetworkhang. NoMongo/Render probe executed. Standard gates untouched.
Needindependentreview,fullsuite and visualformcheck beforebackup. Noactivation.

V2 auth hardening: PreviewAccess now import-light (news_api imported only when
build/from_env called), one nonblocking global-peraccess hashslot plus atomic
attemptreservation beforehash, including successfullogin attempts. No24thread
expensivehashfanout. ExactOrigin nowrequiredlogin/logout/probePOST, logoutcsrf
issuedatlogin. UTF8bytecomparison rejectsnonASCIIinvalidCSRF403,notTypeError500.
Existinglogin/logoutbehavior changedintentionally forsecurity; noDB/readgate
change. Logoutcallers needcsrfparameter fromsession, notbarePOST.
URIstillininitialchildprocessenv, notOSsecretisolation. killchildonly, notprocess
groupcleanup. InitialHTTPreviewUNSAFE supersededonlyafterfreshreview; noreadiness
claim. 12access+15wrapper/process nativefocused tests planned/rerun.

V3 sessionrevocation: bounded128active server-side nonces perPreviewAccess,
expiry2h, purgeonlogin/authorize, logoutremovesnonce; replayedprevioussignedcookie
refused. Restartrevokesall sessions. Singleworker/peraccess stateonly, notshared
productionaccounts. Loginreplacesoldsessionnonce. Capacityfailclosed429, noeviction.
Browserlogoutformdeliveredon/db-check and/private-session; HTTPonlytests take
hiddenCSRF and replayoldcookie, notsession_transaction backdoor.
Canonicaloriginstartupvalidation rejectsports(including443), uppercase,backslash,
credentials,path/query/fragment and malformedhost. SimplelowercaseDNSnames only.
Oversizedpassword400 beforehashreservation. Busy429 consumesnoattempt. Validform
unauthenticatedcallers canburnglobal10/300s budget; availabilitytradeoff remains,
needexternalratecontrolbeforepublicexposure. Successfulhashalso consumesbudget.

ReviewV3SAFEprivate/singleworker/manualscope. Reviewer21of23HTTP/access testsPASS;
2failedonlybecauseUIassetsabsentfromincrementzip. Author42focusedwithassetsPASS,
944fullsuitePASS1skip1expectedfailure. Residuals: unauthenticatedglobalbudgetburn
needsexternalratecontrolbeforeexposure;128activecapcanlockoutuntilsessionexpiry/
logout/restart; logoutdoesnotcancelalreadyaccepted in-flightprobe; sessionexpiry
useswallclock; clockchangescanaffectvalidity; formMAX_CONTENT_LENGTH1024 means
urlencodedpassword/CSRFnear1024charscan413beforeexplicitlengthcheck. Process-local
sessions/cooldown resetonrestart, notdurable/sharedproductionaccountstate.

<!-- END-ORIGINAL-DOC -->


<a id="doc-095"></a>

### Reference: `integration/GEO_QUEUE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4089,"path":"integration/GEO_QUEUE_LIMITS.md","sha256":"3b51b3246bfff820d49f478c2e5b3fe5d6e33422d31b1aaa796eb799ec3f0609"} -->
# Original Geo queue supplied-fixture contract

This is renderer-differential preparation, not a current digest or delivery queue. Pure Mongo plan and supplied-fixture selection only. No client, source read, mail, mark, route or scheduler.

Original query is emailed {$ne:True}, score DESC/published DESC, limit60. The original renderer applies score>=4 AFTER fetch, returns all fetched IDs, and counts CRITICAL across all fetched rows. We retain that distinction with fetched_ids/displayed_ids and critical_count/displayed_critical_count. Both ID sets are fixture selections, NOT receipts. Future marking policy is OPEN: fetched versus displayed is a separate reviewed decision; no ids_to_mark/emailed_ids field exists.

Projection, proposed max_time_ms2000 and ObjectId DESC tie-break are additions to originals, not parity claims. Tied source order was unspecified originally. Limit<60 is fixture-only. Original MIN_SCORE4 and both .get defaults (credibility MEDIUM, corroboration1) are pinned by drift/differential tests. Other fields use original required accesses. We reject explicit None text/numeric values, unlike original `or ''` fallbacks for several fields; missing score also errors. Production schema may contain such rows, so this fixture contract cannot be activated without full-schema review and a separately reviewed compatibility policy.

Entire supplied snapshot validates before selection. Scalar emailed missing/null/false included, True excluded; any array or mixed type errors whole snapshot. Mongo supports other BSON equality behavior, so sampling or type-filtering unsupported rows would not prove full coverage. Exact closed scalar/ObjectId values, <=1000 rows/2MB/16k text, finite nonnegative score/corroboration<=1m, zoned published strings. No original category normalization added. Fresh plain copy and original hash-pinned AST renderer plus sanitization retained.

HTML renders empty events and therefore contains "0 upcoming events". This means omitted fixture events, NOT verified zero events: events_scope explicitly omitted_fixture_events_not_verified_zero; html_scope renderer_differential_only_not_current_digest. Do not publish this HTML without its scope, and do not send it. Header date uses fixed aware UTC rather than original server-local time, so near midnight IST the date can differ. Actual timezone choice remains separate before delivery. No visual layout change or completion claim.

IDs are internal exact ObjectIds. HTML-only guard checks casefolded rendered output after two HTML-unescape passes and URL decoding; uppercase/entity/percent forms tested. It is not a general encoding-proof/private-data scanner, and does not sanitize arbitrary downstream artifacts. No IDs in tested HTML text/link/attributes. supplied_fixture source and unsent_queue_verifiedFalse are explicit. snapshot_id hashes validated rows plus limit, not a production database snapshot or global canonical identity; observed_at is caller's fixed UTC clock, not verified DB observation time.

Before any future send: verified immutable source snapshot ID/time, atomic claim keyed by exact ObjectId set, content-hash/send-receipt binding, marker restricted to claimed IDs, cross-worker dedup/expiry/retry policy. At-least-once delivery unless a separately proved idempotency rail establishes otherwise. Concurrent builds overlap today. None implemented. Existing three-project ReceiptBridge unchanged and not Geo-only activated. Apps Script chosen, but receipt auth/durable ledger/atomic marking/email scope still missing.

Repro in configured repo: python -m unittest tests.test_geo_queue_fixture.11 tests: pure query/projection/scope, renderer-only differential low-score CRITICAL/HTML/IDs/defaults, missing/null/false/true emailed plus array hard errors, tie deviation/cap-before-render, bounds, HTML identity forms, MIN_SCORE/default drift, limit-bound snapshot hash and None strictness/import guard. Selection is not a live Mongo differential. Bundle needs report_adapters/renderer_scope/original pinned source/sanitization helpers, not standalone full repo.

<!-- END-ORIGINAL-DOC -->


<a id="doc-096"></a>

### Reference: `integration/GEO_READ_FACTORY_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2581,"path":"integration/GEO_READ_FACTORY_LIMITS.md","sha256":"51f161c7421d970ff4fd82cbacf3a595417d0d37a69d8433e5ee39eaa5006445"} -->
# Geo lazy read factory wiring

Reads off by default. private_router selects factory ONLY when explicit
Geo-only/read-on flags true. Private login/origin/secret, exact booleans,
verified mapping, URI and denied database/collection labels still validated
before constructor. No live environment changed, credential validated, network
read/client instantiated against real account, deploy or write performed.

Facade public surface client[]/close, database[], collection.find and cursor
sort/limit/max_time_ms/iterate/close. No aggregate, command, with_options, writes,
indexes, admin APIs or arbitrary attribute forwarding. Private _client etc are
reachable to hostile Python code: NOT sandbox or credential restriction. A
separately verified dedicated read-only Atlas user remains mandatory.

Lazy PyMongo import inside factory only, connectFalse/TLStrue, certificate and
hostname validation true, serverselection/connect/socket5s, poolmax4/min0,
waitqueue2s. No ping or startup query. SRV DNS resolution/client initialization
may still perform network at read-on construction; connectFalse is NOT no-I/O.
URI not logged by our code, exception string sanitized. Dependency debug/log
configuration and startup traceback contexts are not credential isolation;
operator must avoid debug logs and supply URI securely. No URI stored in facade
public fields/output. Bad creation becomes fixed ValueError, no retry.

Geo reader projected public-store fields, created_atDESC/newest100,
max_time_ms2000 server query ceiling, cursor assigned immediately after find,
closed on success/sort/limit/max-time/iteration failure. Close errors suppressed.
Existing request failure closes client once and latches503 until reviewed rebuild.
Legacy reader gains cursor cleanup but no default new query ceiling. No index
creation/aggregate/full-history/store capability. Timeouts are per-operation,
NOT end-to-end deadline/wirebyte cap/snapshot consistency/production proof.

22 focused configured tests PASS: actual router fakeconstructor, gates before
client, reads-off trap (existing), constructor options/sanitization, facade
surface, setup/iteration cursor closure and existing launcher/read regressions.
No real account/Atlas/Render test. Source schema/index/deadlines/permissions and
live activation approval still required. Review bundle includes integration
modules/assets plus required tests and rootFinder files for indexload tests.

The same narrow read facade may map exact geo_intel/events only through separate
events composition gates; article-only default unchanged. No new facade API.

<!-- END-ORIGINAL-DOC -->


<a id="doc-097"></a>

### Reference: `integration/GEO_SAMPLE_PROBE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3102,"path":"integration/GEO_SAMPLE_PROBE_LIMITS.md","sha256":"9cde4838179cf49f6bf3bcffb6d490757d5630e50b91d9949603bfa022e0aa46"} -->
# Injected Geo sample probe, not hosted

probe_geo_sample is separate offline trusted injection. No env/route/startup
activation, scheduler/retry, original read-gate change or live query. Label:
read operations under a write-capable credential, not verified read-only access.
No privilege measurement. Intended operator env URI stays in Render, not chat,
logs, repository, response or raised ordinary exception.

Exactly geo_intel/articles, find {}, projection created_at/published/score and
_id0, created_atDESC, limit20, maxTimeMS2000. Bounded aggregate field compatibility
counts only; no values/IDs/articles/URI/host/error text returned. Empty distinct
from unavailable. Failures discard partial counts. Missing fields count missing,
unsupported inert values count incompatible. Custom objects/extra keys/oversized
strings/rows fail closed. published uses original-export zoned-string contract;
created_at uses current preview parse_dt (aware string<=40,UTCyear1970..2100).
BSON datetime created_at may be structurally inert but incompatible, never
coerced and marked compatible. score exact int/float finite +/-10^12.

Cursor/client close once on every owned path. Find failing before a cursor is
returned cannot close an unreturned cursor. Ordinary cleanup errors refuse result;
control BaseExceptions re-raised after both closes. Trusted factory externally
reviewed for bounded timeouts/TLS; probe passes serverSelection5s/connectFalse.
Existing create_geo_read_client meets defaults but Python facade is not privilege
isolation. Source malicious Python factories/provider hooks are not sandboxed.
Provider BSON allocation precedes scalar bounds; not wire-memory guarantee.
maxTimeMS/getMore/socket limits aren't one finite serving deadline.

9 native fake-driver tests pass. No real Mongo/Render check. Full schema/index,
explain/roles/snapshot/accounttransaction aren't established by samples. No
verified-source flag set. Dedicated read-only Atlas user preferred later; offer
click path only on request. Private manual hosted wrapper/auth/origin/CSRF/rate/
deadline/log review still needed before activation. No Free Render shell exists.

Any list/dict/ObjectId/Decimal128/bytes/custom value or string>100 in these three
projected fields refuses the WHOLE probe as unavailable; it is not counted as
incompatible. Supported inert wrong-format/date/null/bool/NaN values can count
incompatible. No claim every historical schema shape yields compatibilitycounts.

Fixed unavailable_reason distinguishes PyMongo ExecutionTimeout=query_timeout,
NetworkTimeout=io_timeout, ConnectionFailure(including selection timeout)=
connection_unavailable, ordinary other errors=source_unavailable, cleanup errors=
cleanup_unavailable. No source error/code/text emitted. Without PyMongo installed
classification falls back source_unavailable. created_at sorting may exceed2s
without an appropriate existing index; timeout is not connection refusal or
verified-empty. This probe never inspects/creates an index. Flag is precisely
probe_issues_no_writes=true, not a statement about credential or provider powers.

<!-- END-ORIGINAL-DOC -->


<a id="doc-098"></a>

### Reference: `integration/HOST197DA.md`

<!-- ORIGINAL-DOC {"bytes":2346,"path":"integration/HOST197DA.md","sha256":"ff93d13e078a9a25d8342f45eee1a12141d7ae30b73419b0752c211e7fbe62f3"} -->
# 197d-a read-only host probe

Default OFF. Owner-authenticated GET /api/collector-host-probe only when
COLLECTOR_HOST_PROBE_ENABLED=true and dedicated backend
COLLECTOR_HOST_PROBE_SECRET is configured. No browser Origin, no query string,
no user-supplied command/path/env. Owner enables/deploys this diagnostic only;
this does NOT enable collection or establish activation authority.

Closed facts: point-in-time cgroup allowance minus current use bounded by host
MemAvailable; /usr/bin/bwrap presence, actual PID namespace and nested bwrap
fixed /usr/bin/true probes (3 seconds each, kill/reap); kernel release; current
Gunicorn worker config timeout and count only if observable, otherwise null.
No env values, process command lines, tokens, DB facts, raw failures or files
are returned. Fixed closed response schema blocks arbitrary injected outputs.
No persistent writes, clients, indexes, provider, or collector activation.
One-at-a-time process-local probe gate; owner asks for one measurement, not
ongoing polling. Public health/home/read routes remain unchanged.

Probe's memory observation is not reserved capacity or free monthly quota.
A missing/unavailable fact is a blocker, not a successful readiness proof.
The conservative collector contract remains 1536 MiB available memory and
WSGI worker timeout >120s; actual host provider is still a separate 197d unit.
No live host query or deployment happened while preparing this source.

Render documents a 100-minute HTTP response/request ceiling, so the 90-second
collector contract is below that documented proxy ceiling. Actual Gunicorn
worker timeout and requester timeout remain separate checks. The 75-second
edge number in the runtime-errors tutorial describes keep-alive reuse, not
an established maximum response duration. No slow remote test was run.

Sources, read at preparation:
https://render.com/docs/render-vs-heroku-comparison
https://render.com/articles/deploy-streamlit-gradio-localhost-to-live
https://render.com/tutorials/when-deploys-go-wrong/runtime-errors
https://render.com/docs/free
https://render.com/docs/web-services

Free plan documentation states 0.1 CPU/512 MB RAM, single instance and no shell.
Do not assume this exact service's current plan from generic documentation;
probe actual allocation. Do not quietly lower worker/parser caps when too small.

<!-- END-ORIGINAL-DOC -->


<a id="doc-099"></a>

### Reference: `integration/HTML-TEXT209.md`

<!-- ORIGINAL-DOC {"bytes":8043,"path":"integration/HTML-TEXT209.md","sha256":"f6d8935e0959eef61e8fe8a08f4753bce54ac88e4073fcd3972a21aa7a59ea6c"} -->
# Geo summary HTML text policy 209

Copyright (c) 2026 Push. All rights reserved.

Owner report October 8, 2026 16:20:09 identified cascading &amp; before &lt;
replacement in geonews processing/classifier.py. Original numbered item 15 asks
single-pass entity decoding/tag handling and numeric/Unicode/malformed/tag tests.
This unit changes Geo summary text only. Sanctions decoder 150 is separate and
unchanged. Title normalization is deferred. Already stored summaries are NOT
rewritten. This does not prove whole item 15 or live collection complete.

## Contract

Remove actual markup by HTMLParser source-position spans, then decode references
once, then remove markup produced by that single decode. Entity parser events are
never reconstructed: raw source text preserves AT&T, &amp 5, &#65 x, &#x41, &;,
&#;, and &foo; exactly. No html.unescape, semicolonless repair, cascading replace,
or regex parsing of HTML. Semicolon-terminated html.entities.html5 keys only;
multi-codepoint values supported. Numeric references use ASCII decimal/hex digits,
x or X and leading zeros, at most 12 digits. Zero, surrogate, out-of-range,
controls except TAB/LF/CR, and Unicode noncharacters remain literal. NBSP and all
Unicode whitespace collapse to ASCII spaces. &hellip; becomes the actual Unicode
ellipsis, not the old three ASCII dots. Encoded once tags are stripped; nested
escaped text stays escaped. Existing HTML renderers must still escape plain text.

Actual/once-encoded script/style element and its content are removed. Unclosed
script/style removes remainder deliberately. Complete comments/declarations/PIs
and CDATA declarations removed; incomplete declarations/comments remain literal.
Raw declaration spans are masked before HTMLParser so unknown declarations cannot
assert. Unterminated ordinary tags remain literal: <div and a <b preserved.
Prose a < b / x <3 y preserved. Script/style always hide content regardless of attributes. Known HTML elements
strip when every valueless attribute is in the fixed broad bare-attribute set;
unknown elements with any bare attribute, or known elements with an unknown bare
attribute, stay literal. Ambiguous start tags with unknown bare attributes
are retained, so if a<b and c>d remains prose. Quoted attributes with > are handled
by HTMLParser, not regex. Tag boundaries become spaces. No version check, import
time assertion, refusal, or exception-swallowing in the helper.

Golden output vectors are independent literal expectations, not helper-derived.
AST parity tests check integration only; they share the actual helper and are not
claimed independent behavioral oracles. Golden vectors run on proven CPython
3.10.12. Other interpreters are unverified. The actual target runtime must pass
this golden suite before any activation/deploy using the helper, a blocking
acceptance prerequisite for items 27-29, not an import-time/runtime gate.

## Caller and field inventory

| Path | title/summary assignment and classifier/text calls | decoding count |
| --- | --- | --- |
| intelligence/geo/collectors/rss.py | _fetch_feed title stripped only; summary/description strip_html; optional extracted full text replaces summary; collect calls classify, truncates stored summary to 300 | feed summary once; extracted plain text zero; classify zero |
| intelligence/geo/collectors/gnews_search.py | title stripped only; description strip_html; classify then documents summary[:300] | summary once, title zero |
| collector120_prep/gnews_supplied.py | executes same pinned collect AST over supplied SDK outcomes, injects classify/strip_html; returns detached documents | same once |
| integration/supplied_feed_fixture.py | executes pinned _fetch_feed AST, wrapper calls hash-pinned helper | once |
| collector129_prep/supplied_feed.py | same supplied AST with separate captured aggregate budget; coordinated runtime decoder-binding adaptation approved | once after reviewed adaptation |
| integration/feedparser_audit/child.py | parser-sanitized fixed synthetic rows, both supplied selection and AST parity oracle call helper independently from original row, never sequentially | once per branch; upstream feedparser sanitization is separate |
| integration/supplied_collector_pipeline.py and supplied_multi_feed.py | supplied feed output to supplied enrichment, then original document preparation | no second decoder |
| integration/supplied_fulltext_fixture.py | optional supplied extraction replaces summary; geo_collector_contract classifies | no second decoder |
| integration/fixed_parser_pipeline.py | fixed parser child output to supplied fulltext preparation | no second decoder |
| integration/geo_collector_contract.py | caller supplies candidate title/summary; pinned original classification/document AST, truncated summary | zero; raw supplied HTML is not automatically decoded |
| integration/collection_prepare.py | manual/offline supplied Geo candidates classified as supplied, summary[:300] | zero; caller responsible for text provenance |
| integration/collector_mail_fixture.py | supplied candidates to document contract, stored supplied rows to escaped mail renderer | zero extra decoding |
| intelligence/geo/collectors/official.py | empty collect stub; no fields/classifier | none |
| intelligence/geo/collectors/events.py | empty event seed; no article title/summary/classifier | none |
| intelligence/geo/collectors/sanctions.py | held legacy service; no article summary/classifier | none |
| intelligence/brics/collectors/rss.py + processing/classifier.py | separate _clean + BRICS classify; does not import Geo strip_html | unchanged, outside scope |
| intelligence/brics/collectors/official.py | manual-check homepage stub title/summary; BRICS processing only | unchanged, outside scope |
| scraper/GDELT | no such collector modules in current repo; no Geo text-helper caller found | not invented |
| tests/text_matching/test_matching.py | direct classify with literal titles/summaries | zero |
| tests/test_supplied_feed_fixture.py, test_supplied_collector_pipeline.py, test_supplied_multi_feed.py | execute actual AST parity wrappers and compare from independently copied raw rows | once per branch |
| tests/test_news182.py | GNews AST with identity strip_html stub for date-only test | zero, not HTML proof |
| tests/test_html209.py | independent golden corpus, named/numeric/control/fuzz vectors, no-downstream-redecode check | explicitly tested |
| remaining tests/collector tests | call named supplied entry/fulltext/GNews/cycle seams above; mutate detached title/summary fixtures only | no new decoder |

Geo classify intentionally still receives raw titles such as AT&amp;T. Supplied
manual candidates and extracted text can reach matcher raw. No title/fulltext
normalization claim. Field storage, matcher/rules/scoring/date policy unchanged.
No DB rewrite, SMTP, collector activation, engine/bootstrap/install/deploy edits.

## Wrapper boundary

Both wrappers execute the actual hash-pinned classifier strip_html AST, whose
only names are text and strip_html_once and which has no attributes. The injected
strip_html_once is the same imported pure helper, separately byte-pinned in each
PINS mapping. No duplicated decoder, dynamic imports or startup effects. Helper
imports html.parser and html.entities only. No wrapper builtin added. Existing
Exception/print builtins remain unchanged. Old classifier source shape refused.
Runtime confirmed no active conflicting wrapper patch. 197 worker pin refresh is
metadata only, no engine edits. Historical original source inventories unchanged.

Prose/tag ambiguity cannot be resolved perfectly: known element b with bare
attribute c remains prose, while b with bare attribute hidden is stripped. Real
HTML bearing unknown bare attributes can remain literal. This is plain-text
processing, not a safe-HTML sanitizer. Bare-attribute whitelist covers tested
legacy and modern WordPress/embed tags. Script/style masking bypasses that
heuristic unconditionally, including defer/async/nomodule/unknown bare attributes.

<!-- END-ORIGINAL-DOC -->


<a id="doc-100"></a>

### Reference: `integration/LIVE_NEWS_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2611,"path":"integration/LIVE_NEWS_LIMITS.md","sha256":"678826c4012d5573c1aca79b347455f32986f87e72983d2aa2ffb178a3a7bf9c"} -->
# Live news preview UI

The old separate news tab is removed from the workspace UI only. Preserved
source, project identities and API filters remain intact. Geo news is still
the Geo read view, not a union of all stored project articles. No migration or
silent policy change is performed by removing a tab.

Five seeded fixed video IDs are copied from source configuration. Availability
or current live status is not guaranteed. Mini players and selected large
player use youtube-nocookie embeds, muted autoplay and inline playback.
Browsers may block autoplay and broadcasters may disable embeds or end a video.
External watch links remain available. Opening Live news first creates players;
loading the workspace alone does not contact YouTube. Multiple concurrent
players use data and duplicate playback of the selected video is intentional.
No live-discovery polling, YouTube API key, message listener or wildcard trust.
An ended-state overlay is not implemented; YouTube owns its player UI.

My channels stores up to20 named video IDs in browser localStorage only. It does
not change original config, DB, GitHub or Render disk. It is per-browser, not a
cross-device durable store. Clearing site data loses changes. Storage failure
is explicit and leaves page-session settings. Cross-device server persistence
requires a separate reviewed destination and owner approval. No such adapter
is wired. Accepted inputs are bare11-character IDs, exact www.youtube.com
watch links and youtu.be links without extra params. Channel/live-page links
are deliberately unsupported rather than guessed into video IDs.

Names and errors render as text; no innerHTML. CSP extends only workspace
frame-src to exact youtube-nocookie host. Existing Finder CSP stays separate.
News refresh/theme never call player rendering or change player frames. Channel
edits may recreate players; selection changes only the large player.
No auto-news timer, collectors, mail, DB writes or deployment are enabled.

Embed iframe sandbox is allow-scripts allow-same-origin allow-presentation.
Real-network playback and CSP behavior remain unverified; fallback links stay.
Add/remove while Live is hidden updates local settings/list without creating new
players; retained mini frames keep their DOM identity. Removed channels may
remove their own frame. Switching back reconciles additions/selection. Existing
dead other-project UI branches remain in workspace.js pending later cleanup;
no separate tab activates them. Oversize saved lists explicitly fall back to
defaults. Per-device localStorage is a prototype, not final server persistence.

<!-- END-ORIGINAL-DOC -->


<a id="doc-101"></a>

### Reference: `integration/MAIL-CANDIDATE219.md`

<!-- ORIGINAL-DOC {"bytes":3697,"path":"integration/MAIL-CANDIDATE219.md","sha256":"1b6b83263318bd1baa44631be8fb167280483079856816d2ccdc9287bc31c6a2"} -->
# 219: in-memory candidate bytes, not archived

freeze_candidate defaultsOFF before inspecting arguments or importing any other
integration. ON takes a supplied nonempty218-shaped result, a caller-supplied
lowercase64hex SHA256 recipient-set fingerprint and a20..80ASCII nonce of letters,
digits,underscore,hyphen. It validates closed shapes and internal consistency,
then returns (immutable bytes, independent plain binding dict). Bytes are not
written anywhere. archived/durable/send_allowed/ready stayFalse.

Recipient fingerprint will come from a future recipient unit.219 cannot verify
it refers to real addresses or owner-approved recipients. No address/name is
included in binding. Proposed fields are212input data, not permits or proof.
No call to212/218/217/216/store/DB/file/network/env/sender occurs. No production
module imports219. OFF imports no pymongo or dependent integration.

CanonicalASCII JSON bytes contain candidate and proposed_content_digest. Exact
bytes type is required; bytearray/memoryview/subclasses refuse.128KiB cap includes
the envelope. Candidate combinedbody80KiB/html60KiB and IDunion120 still apply.
verify_snapshot parses strictUTF8/noBOM/duplicates/nonfinite then requires EXACT
canonical re-serialization bytes. Whitespace, key order,escape variants,newline,
secondvalue and mutations refuse. Every candidate/binding field is checked,
contentdigest recomputed, wholebinding recomputed,then independentcopyreturned.

218digest keeps its exact canonical candidateJSON formula.212compatible channel,
control,binding andnonce hashes keep exact formulas WITHOUTnewdomains. Separation
is only by their different closed JSON key sets and212purpose field; no claim of
cryptographic non-collision is made. Only new219snapshot_identity andbyte_integrity
use separate versionedASCII domains over canonical length-safeJSON. Tests pin
hardcoded212/218vectors and compare against actual212purehelpers in tests only.

Internal consistency is NOT authentication. A changed HTML candidate with a
recomputed digest/binding is accepted; tests show this deliberate limitation.
219 does not sanitize HTML or establish that218 produced it. A future unit
holding original rows must re-derive218 output when provenance matters. Hashes
bind this candidate, not source completeness, owner wording/recipient approval,
safe rendering or persistent retention. Neither canonical bytes nor nonce grants
send/retry/newnonce/clear/ack/mark authority. Empty218skiprefuses without binding.

218desktop/mobileChrome pixels remain the only visual evidence.219changes no
visual surface and makes no Gmail/Outlook claim. Real immutable durable storage,
existing-state preservation/history/import, exclusion enforcement, marking,
recipient/words authority,reconciliation,mapping,realmount andsendworkflow remain
open.217held/216unselected/AppsScriptselected/SMTPfallbackheld/201cwriteheld.
No DB check/read/write, automatic creation, live wiring/send or cutover occurs.

Bytes commit only to candidate/content digest, not recipient fingerprint or nonce;
only binding commits to those. The same bytes can verify with a freshly frozen
binding for that candidate and another fingerprint/nonce. verify_snapshot proves
bytes and binding agree, NOT that these bytes were used for a given send. Future
ledger wiring must retain binding hash together with content digest and re-derive
218 from original rows before sending. Nothing is persisted; restart loses the
bytes. Durable body storage remains open.212_hash defaults ensure_ascii=False;
219usesTrue. Compatibility equality here relies on ALL formula values beingASCII,
including IDs/hashes/fingerprint/nonce; test matrix is deliberately ASCII-only.

<!-- END-ORIGINAL-DOC -->


<a id="doc-102"></a>

### Reference: `integration/MAIL-EXCLUSION223.md`

<!-- ORIGINAL-DOC {"bytes":3248,"path":"integration/MAIL-EXCLUSION223.md","sha256":"cbcf746c984d7f40e1a237983660dc93538f1692374cc368c4184b9f424895b8"} -->
# 223: supplied exclusion view consistency only

This projection is a caller assertion, not a ledger read. Two caller-supplied
acknowledged-ID lists agree. That does not prove either list is a ledger view.
The closed, non-native projection has these fields:
- schema: mail_exclusion_projection223_v1
- logical_channel: lowercase 64-hex string
- purpose: digest
- acknowledged_ids: exact tuple of unique ObjectIds, at most 10000
- active_state: None, prepared or started

None means "caller asserts none", not evidence of no active control. Prepared
or started refuses the whole asserted channel and purpose, even with no article
overlap. Unknown, cancelled, resolved and all other states refuse. They are
never treated as None. 223 mirrors only active prepared/started on this channel
and purpose. 212 itself owns its control rules.

The email tuple must have exact set equality to the projection IDs. There is no
deduplication. Order does not matter. All three exact email/telegram/whatsapp
tuples are checked for type, uniqueness and caps before copying or set conversion.
Other channels are not unioned or compared. A telegram-only article inside the
window is not excluded and is not an error. 221 receives displayed_receipts
unchanged; a deep comparison checks that after the call.

221 checks independent expected fingerprint and nonce, then fully re-freezes
219. Channel equality is checked after that verification; purpose is exactly
digest. The 219 candidate union strings must be disjoint from the projection
ObjectId strings. Renderer 218 already excludes email receipts. An overlap means
candidate and supplied view disagree, so the check refuses.

Omission in BOTH views passes. Stale views pass. Both views can be forged or
incomplete. This is no delivery, receipt membership, current active state,
history completeness or no-repeat proof. No authenticated native projection
producer from 212 exists. That producer, with an authenticated read under future
permissions, remains an open item. No read is performed here. None does not
permit a live workflow. Supplied rows matching 221 is not provenance or freshness.

Default OFF before arguments or imports. ON dynamically imports 221, 219 and
bson; 218 is reached through 221. There is no 212 import or constructor, driver
check, live DB client, query, write, creation, index change or store. The fixed
refusal is raised outside except without upstream message, cause or context.
The closed constant result contains a note and flags, not IDs, counts, channel,
projection or receipt_status. send_allowed, ready, owner_approval,
receipt_membership_verified, history_complete, source_complete, durable and
ledger_wired remain False. No output receipt conversion or input mutation.

No send, wiring, property or environment change, deployment, activation, trigger,
cutover, mount or selection. Apps Script remains selected, SMTP fallback held,
217 held and 201c write held. The sender blocker from 222 is prepared, not
resolved. History, exclusion authority, provenance, durable body and approval
of recipients and words remain open. The owner has not approved recipients or
words. Native 212 article prepared/started keys and its active pointer are not
validated or mapped by this unit.

<!-- END-ORIGINAL-DOC -->


<a id="doc-103"></a>

### Reference: `integration/MAIL-LEDGER212.md`

<!-- ORIGINAL-DOC {"bytes":11046,"path":"integration/MAIL-LEDGER212.md","sha256":"31a32b4f04bea64ba3c452573dde15a674b1203f3516b6258c97fbf2045ec7f3"} -->
# 212: unselected per-logical-channel exclusion ledger

Source-only adapter, not mail wiring completion. No current sender enforces these
keys. No client is constructed, no route, timer, sender, environment, article
flag, provisioning, index write, migration, retention purge or live effect is
added. Existing feature_mail_mount store/bridge and its 128-receipt cap remain
unchanged. FixtureLedger remains a fixture. Native200/201 engine is untouched.

## Logical identity, history and prerequisites

Proposed mapping: geo_intel/mail_control212, mail_receipts212, mail_articles212.
These are candidate names, not proof of existing collections or owner permission
to create them. Constructor requires explicit enabled=True, exact review fields,
transaction/write/control evidence and an exact history-manifest SHA256 with
history_complete=True. Such supplied flags/hashes are caller assertions, not
independent proof or authority. They never authorize activation. No absent row is
created, no genesis/zero-history assumption or migration is made.

Before real use: recover source-grounded owner authority, preserve-state policy,
actual role/validator/collection/index/transaction diagnostics, history import and
completeness, sender/recipient/scope evidence, and caller authentication. No TTL
index on any ledger collection is allowed; ordinary _id uniqueness is required.
No secondary unique index is needed. Constructor does bounded read-only index
inspection, not provisioning. OFF inspects no client attribute and creates no
handle/session, even when a hostile object is passed; repr has no client fields.

Logical channel is SHA256 of canonical kind + reviewed recipient-set fingerprint.
Transport is NOT in the key. Purpose digest/critical is bound separately in both
control and article key. Changing recipients makes a NEW logical channel and
exclusions are NOT carried over: that is an explicit owner decision, never a
silent recipient edit. Recipient fingerprint is not an address or permission.
The channel helper does not build, normalize or approve recipient sets.

Email digest and critical are supported state scopes. Critical does not suppress
normal digest, preserving the owner's separate-purpose choice. Telegram/WhatsApp
are validated selector names only, no transport is connected. Weekly is refused
and deferred to occurrence-bound scheduling work. No sender, recipient or time
is chosen. Rail is a recorded receipt attribute, never exclusion identity; rail
cannot change on a replayed receipt. A new receipt on another rail still sees
acknowledged article exclusions for the same logical channel/purpose.

Existing emailed/mail_critical_sent flags and this ledger are two distinct sources
of truth. This unit does not reconcile them or mutate them. For the future
selector, ledger keys govern recorded per-channel exclusion; legacy flags cannot
prove per-channel coverage and cannot override a recorded key. Disagreement,
unknown history or missing import must hold activation until a reviewed policy
resolves it. No current sender obeys this precedence yet.

## Transactions and state

All mutations use snapshot read concern, primary reads and majority+journaled
write concern with 5s bound. Each logical channel+purpose has its own provisioned
control: _id derived from canonical channel+purpose, schema1, channel, purpose,
history_manifest, history_complete, revision and active receipt or null. Every
write CAS replaces the exact prior revision, incrementing once. Digest/critical
and different channels do not share a control row. A competing write/duplicate
_id insertion aborts the whole transaction. No application-level body/commit
retry, with_transaction helper or automatic retry/resend exists.

prepare binds nonce-derived receipt, sorted unique exact ObjectIds (1..120),
logical channel, purpose and content/renderer digest. Payload hash covers ONLY
logical channel, purpose, sorted unique IDs and content digest. Input order does
not change it. Stored receipt contains hashes, IDs and state/rail/audit metadata,
never email body or recipient addresses. It is NOT a full HTML archive, email
renderer or independently verified send identity. Content digest must bind the
future caller's separately retained immutable body. This unit cannot establish
that fact. Empty selections refuse without creating a send claim.

Article _id = hash(channel,purpose,ObjectId). New keys, receipt and control CAS
are in the same transaction. Existing prepared/started overlap holds the entire
unit, never silently skips a subset. Acknowledged overlap refuses prepare;
exclusions(candidate_ids) returns acknowledged IDs, for the selector to exclude
BEFORE preparing. It looks up only candidate keys via _id $in, never scans
retained history; unresolved overlap holds, not silently suppressed forever.
Blockage is CHANNEL-WIDE: the active control blocks EVERY later prepare for the
same logical channel+purpose, even disjoint IDs. A crash after start halts that
digest channel until future authenticated operator resolve; a prepared-never-
started hold needs authenticated cancel. Nothing silently releases the hold.
Same nonce/hash/IDs/rail returns stored state; conflicting hash/rail holds.
Released keys are reused only through exact receipt/hash/state CAS, never deleted.

start persists started once and gives permit=True ONLY after confirmed commit AND
readback in a fresh snapshot transaction showing started/same attempt/hash.
Repeated start returns held/permit=False, never a renewed permit. Started means
POSSIBLY SENT. No elapsed time, restart or expiry releases it. Permit is source
protocol state, not user send authority. Caller must check status on held result.

acknowledge exact receipt/hash/attempt atomically transitions all bound article
keys, receipt and control, then fresh readback. It is an authenticated future
bridge assertion: bridge_send_returned_not_delivery, NOT recipient delivery or
independent provider proof. A repeated ack is idempotent and cannot resend.

cancel(receipt/hash) applies ONLY to prepared-never-started. It atomically changes
keys/receipt to cancelled and clears that control; keys are freed by state change,
not delete. Started cancel refuses. resolve(receipt/hash/attempt,confirmed_sent,
authority_reference) applies ONLY to started (or exact idempotent terminal replay).
Confirmed sent becomes acknowledged with operator_asserted_sent_not_delivery;
confirmed unsent becomes operator_resolved_unsent with keys released by state
change. The SHA reference is audit binding, NOT proof of operator identity or
permission. Who may invoke resolve/cancel is the future authenticated owner/
operator workflow, not a public client. This unit grants no such authority and
adds no endpoint. Existing receipt records remain immutable in binding and kept.

Fixed reasons include conflict_started, conflict_prepared, conflict_other_hash,
conflict_sent, conflict, capacity, schema, unknown_commit, unavailable, readback,
missing, history_unverified, invalid, disabled and driver. No private ID, nonce,
hash, body, address or driver error string is echoed in exceptions/held reasons.
Successful internal status includes scoped hashes/IDs for its trusted caller,
not a public disclosure API.

## Driver behavior, limits and uncertainty

Pinned installed PyMongo4.18.2 source is recorded in mail_driver212.json:
synchronous client_session, mongo_client, collection and errors. Enabled
construction/transactions verify those exact bytes/version on EVERY _run.
Activation prerequisite: deployed requirements must resolve to PyMongo4.18.2
exactly, or this pin must be deliberately updated and reviewed. Different driver
version/bytes fail closed even when other configuration is valid. Public
ClientSession.commit_transaction uses _finish_transaction_with_retry and
MongoClient._retry_internal(retryable=True): the DRIVER may retry commit once for
retryable errors. "No retry" here means no APPLICATION retry. Commit sets its
transaction state COMMITTED in finally even on unknown outcomes; end_session does
not abort a possibly committed transaction. Ordinary pre-commit failures abort
and release session. No private/native200 no-retry primitive is used or changed.

OperationFailure code112/TransientTransactionError yields conflict, without
rerunning the body. DuplicateKeyError yields conflict. UnknownTransactionCommitResult
and other commit uncertainty yield unknown_commit. start never grants permission
and ack never reports success on unknown commit or failed readback, even when the
write landed. Caller must status/reconcile; it cannot infer unsent from a failure.
The driver can retry the commit of ONE transaction, never duplicate send effects.
Readback is a fresh snapshot, not proof of actual deployment durability.

All-time means no time expiry of recorded exclusion keys, NOT authenticated
historical coverage, unlimited storage or a backup. Per-transaction IDs are capped
120 (24h+7d union), never a 10k historical scan/tuple limit. Receipt storage remains
subject to DB capacity; failures hold. Schema/index drift after construction
requires future ongoing deployment monitoring, not a claim this code prevents it.
No current HTML archive is replaced or automatically expanded/purged.

## Evidence and test limits

Current main feature_mail_mount/store.py was live-read and matches SHA256
 d425883b8f22a2530dda2e6fe9b28bed7036c88bb1e842748b2b277040f843a8.
Original push2006/geonews reports/email_report.py sendthenmark and scheduler.py
three attempts were live-read (30d7552def0e9d56f8981f25b3d81ed3475bcc354971aea304a30e6f7d583688;
dc42e6147db678d3ad93d62f3412cd521230a040296a405e60d77588b99936a0).
BRICS- reports/email_report.py SMTP+STARTTLS source
6582d81d184e2c18842f1507d7e46042514c9d0cfbfea7e1202ce8bf1218ac65.
They were read, not executed. This adapter does not preserve unsafe retry semantics.

19 offline tests: OFF hostile client, history/no-genesis gates, no TTL, ordered
hashes, overlap hold-whole-unit, no renewed start, ack atomic/idempotent, cancel,
operator resolution, distinct purposes/channels, >10000 retained keys with120
candidate lookup and121 refusal, unknown commit before/after applied write,
unknown ack and status-only recovery, failed readback, actual PyMongo exception
classes/labels, two racing snapshot writers with exactly one winner, restart,
stored corruption, pinned driver semantics/options. Fake snapshots model CAS,
WriteConflict/TransientTransactionError and unknown AFTER durable apply vs BEFORE
apply. They are not real Mongo concurrency/durability proof. No live DB/SMTP/Gmail,
article mutation, operator call, trigger, timer or deploy happened.

Remaining mail wiring: source query/completeness +193/202 selector integration,
email-ready renderer (203 is browser preview ONLY), immutable body archive,
logical-channel history migration, caller authentication, article marker decision,
Apps Script mount/cutover,204 SMTP caller (fallback still held),205 scheduler,
actual DB diagnostics/permission/activation. No mail-complete claim.

<!-- END-ORIGINAL-DOC -->


<a id="doc-104"></a>

### Reference: `integration/MAIL-PREFLIGHT225.md`

<!-- ORIGINAL-DOC {"bytes":3137,"path":"integration/MAIL-PREFLIGHT225.md","sha256":"16ccb8087004bf8e5730105f14445c455e6514be10c315c4c9722916c05fcbbc"} -->
# 225: composed supplied preflight DATA only

A pass means "these supplied rows and these supplied bytes agree". Nothing about
an authenticated read, history completeness, freshness, current inactivity,
delivery or authority. A wholly invented self-consistent graph and matching blob
passes. Omitted and stale inputs can pass. Sender scope 222 is not consumed, so
this preflight is NOT a send gate. All prior open items remain open.

OFF is static before arguments or imports. ON accepts the closed field union of
221's renderer/snapshot inputs and 224's native inputs. There is no supplied
exclusion_projection, stage result, sender scope or recipient list parameter.
Extra fields refuse. No default fingerprint, nonce, history or native rows.
Closed argument check, exact list caps (1000 rows, 128 receipts, 10000 articles)
and three exact tuple receipt caps (10000 each) precede imports, copying or sort.
Subclasses of those containers refuse. Stage owners check the remaining types.

224 runs first with the explicit native rows, fingerprint and history manifest.
Its projection object alone goes directly to 223, once. 223 owns the chain into
221 and 218/219. No separate body generation, cached stage result or override.
No 223 call if 224 refuses. No partial success result. Fingerprint/nonce/native
inputs are forwarded by identity without conversion or defaults. The displayed
receipt tuples are never altered to fit the derived projection.

224 includes EVERY acknowledged article in the supplied graph, even articles
whose old receipts are not supplied. 223 requires the email tuple to equal that
FULL set exactly. Subsets and supersets refuse. Telegram/whatsapp tuples are
validated but not unioned; their IDs remain unexcluded in an email candidate.
The supplied graph is the sole source of the email exclusion set here. This says
nothing about whether that set is real history.

Input container structure is copied recursively for a deep comparison after both
stages, retaining scalar identity to avoid unvalidated scalar deepcopy hooks.
Immutable scalar types are validated by their owning stages. No stage may mutate
any caller input, including native rows or displayed receipts. Depth is bounded.
Only ON imports are copy, 224 and 223; no 212 import or enabled ledger constructor.

One fixed error is raised outside except with no upstream text, cause or context.
The output is constant state/preflight_match/note and False flags only. No stage
result, projection, channel, IDs, counts, hashes, body or native data is returned.
Flags send_allowed, ready, owner_approval, source_authenticated, history_verified,
current_state_verified, receipt_membership_verified, source_complete, durable,
ledger_wired and production_wired remain False.

No production caller edge, DB read/check/write/create, send, ledger mutation,
store, environment/property change, deployment, trigger, activation, mount or
cutover. Apps Script selected, SMTP fallback held, 217 held and 201c write held.
Sender blocker 222, authenticated native read, history authority, provenance,
durable body and owner-approved recipients and words remain open.

<!-- END-ORIGINAL-DOC -->


<a id="doc-105"></a>

### Reference: `integration/MAIL-REDERIVE221.md`

<!-- ORIGINAL-DOC {"bytes":2420,"path":"integration/MAIL-REDERIVE221.md","sha256":"4c4eae805aac94c225cf15f1ad9f649388d054473782df9d7c2f2d9c54338d42"} -->
# 221: supplied-row rederivation only

DefaultOFF before arguments/imports. ON verifies219snapshot first, renders218
from explicitly supplied original rows and config, freezes219 with explicit
expected fingerprint/nonce, compares FULL bytes and FULL canonical binding.
No digest-only/ID-only shortcut.219bindingsmustmatchthe independent expected
fingerprint/nonce. Doesn't derive those expected inputs from binding. Same fixed
refusal outside except with no upstream message/cause/context. Closed constant
result with no echo of body/ids/count/binding/hash/nonce/rows.

"These supplied rows regenerate these bytes" is the only match claim. Rows can
be a subset or invented. Completeness is NOTproven; omitted rows outside every
Invented extra rows outside every window can also match. No later unit may
treat a match as source completeness.
window or email-excluded cannot be detected by this unit. Original refers to the
supplied renderer input, NOTsource-authenticated original database records.
Self-consistent219HTMLforgery refuses if supplied rows regenerate differentHTML;
an attacker who invents rows ANDconsistentbytes can still match. No provenance,
history, receipt membership authority, freshness, approved words or recipient
ownership proof. Replay of old inputs also matches, not freshness. No clock;
asof is the supplied now inside candidate bytes. Email-only supplied receipt
exclusions/emailedignored policy unchanged. Invalid URLs refuse even outofwindow.

All218219rules apply. Rows exactlist<=1000/exactdict/rawleaf types checked before
deepcopy. Renderer uses deepcopiedrows, verified unchanged afterwards. Empty/skipped
candidates refuse. ONimports218/219andbson so pymongo test environment is required;
OFF doesn't load them. No import/execution edge into production.

No persistence/network/DB/check/read/create/ledger/send/config/property/env,
activation/triggers/cutover/mount/selection. No212key-equation checks added beyond
what219alreadychecks. Supplied fingerprint remains an assertion;220casepolicy
requires owner acceptance. NAMEDBLOCKERsenderbinding for ledger wiring (bridge
hashes sender+recipients,212doesn't), history, exclusionauthority, provenance,
durablebody, recipients and words approval remainopen. AppsScriptselected,
SMTPfallbackheld,201cwriteheld. sourceonly; send_allowed/ready/archive_proof/
durable/source_complete/receipt_membership_verified/owner_approval remainFalse.

<!-- END-ORIGINAL-DOC -->


<a id="doc-106"></a>

### Reference: `integration/MAIL-SURFACE217.md`

<!-- ORIGINAL-DOC {"bytes":4295,"path":"integration/MAIL-SURFACE217.md","sha256":"ad9c470ae221e0a6b87e127963444b9ca92a93c86eae1c0839e3d17556a84055"} -->
# 217: held private mail mount, source only

build_mail_surface returns the public object unchanged by default, before any
config/public access. Explicit True plus closed config builds a WSGI wrapper,
not a DB-backed mailer. No production module imports it. This unit does not make
mail work; it makes the mount safe to reason about. A 9am target is not readiness.

Config has exactly origin, rail=apps_script, channel_id and header_secret.
Origin is lowercase canonical HTTPS hostname, no port (including explicit443),
path, trailing slash, query, fragment, userinfo, IP literal or localhost.
Channel is lowercase64hex, not authentication or owner permission. Secret is
ASCII48..256 without whitespace/control. Only its SHA256 credential digest is
stored in the wrapper; no plaintext secret is returned/logged/repr'd. Config is
not a grant to send, read DB state, deploy, or change properties.

PATH_INFO interception reserves the exact /internal/mail/v1 segment and children.
Normalization-lookalikes are refused uniformly, never sent to public. SCRIPT_NAME
is not prepended; mounted-app PATH_INFO semantics are preserved. Other routes go
to public with the original environ object unchanged. Public exceptions propagate.

Private auth is checked before body/method/route-key/framing access. Expected and
supplied Authorization digests compare at equal length. Only exact single-space
Bearer ASCII header is accepted; comma-joined duplicates refuse. WSGI cannot
observe a server silently discarding duplicate headers or bytes outside its
stream, so the edge server still owns HTTP framing/header normalization.
Missing/wrong/malformed auth, query string and suspicious paths get the same
401 body/headers. Origin/host mismatches refuse. No proxy headers pick origin.

After auth, POST prepare/claim/ack and GET receipts/64lowerhex are recognized;
other methods/paths refuse. POST JSON is bounded4KiB, required exact Content-Length,
read cap4097, no transfer encoding, strictUTF8/noBOM/duplicate/nonfinite/extra keys.
This observable WSGI check is not proof about raw network framing or hang-proof
transport. The WSGI server must supply bounded/terminated input and read timeouts.
No user-supplied client/default database/DB URL is consulted.

Every valid authorized operation returns503 with exactly
{state:mail_integration_held,retry_send:false}, no payload/receipt/nonce/channel
or Retry-After, fixed JSON/no-store. No successful prepare/claim/ack is possible.
No backend, DB read (including status), DB write, store, ledger, sender, capability,
role, collection/index/genesis creation, timer or environment read is used.
Metadata mounted_held explicitly denies wired/live/ready.

Existing real bridge.gs and216 wrappers are unchanged. Tests use mocked services:
503 at prepare gives zero Gmail calls and retains nonce;503 at claim retains
claiming and never permits/retries send;503 at ack means a send may have occurred,
unknown, and remains possibly_sent under216. Never infer not-sent or clear state.
Ack-only retries do not send again. No real Gmail is used in tests.

No trigger rebuild/activation, property/env/deployment/clasp changes or collector
cutover. Mailer is separate from collector. Apps Script rail stays selected;
SMTP fallback held. Owner's noDB-read/check boundary is preserved. 201c write
selection stays held, including INSERT/drop implicit-creation TOCTOU.

Later units remain open: actual data/mount contract, old128-cap receipt handling,
212key enforcement/history import, mapping/control/state preservation, renderer
selection, marking policy, sender/recipient/final words permission, reconciliation,
DBtiming/weeklyidentity and live workflow proof. This held wrapper resolves none
of these and never starts a follow-up when a future DB URL appears.

channel_id is validated but never used or bound in this surface: inert config,
not enforced channel scope. Uppercase hex in a status path is suspicious401, not
404. Normalized routes starting with /internal/mail/v1, including public-looking
/internal/mail/v10, are deliberately blocked401. Exact HTTP_HOST must equal the
origin hostname without a port; a proxy rewriting Host makes authorized calls
400. Future wiring must verify the real deployed Host; this config does not prove
the origin is the real service.

<!-- END-ORIGINAL-DOC -->


<a id="doc-107"></a>

### Reference: `integration/MAP_LAYERS_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3084,"path":"integration/MAP_LAYERS_LIMITS.md","sha256":"bd0ec31e0326b20cc83ca70f30ec46a4b73ff6d93a2f8b15448f405391b09d7a"} -->
# Pure supplied map layers, not a live map

Separatecontract no route/launcher/chokepointbehavior/sourcepoll/tiles/geocode/
DB/provider/userlocation. Perlayeravailable/empty/unavailable/invalid, closed
sourceclock/points envelope; failedlayeratomicinvalid, otherlayersretained.
100points/layer512KiBencodedoutput cap, nocaptruncation. Suppliedsourceprovenance
notownership/sourceproof. Portsrequired dataset/version/licence metadata marked
unverified_fixture orreference_metadata_supplied; source_verified alwaysfalse.

WGS84decimaldegrees lat/lon exactint/float finitebounded, zero valid; bbox
south<=north, west>east iff antimeridiantrue, inclusivepointconsistency. Crosskind
sameidallowed, withinlayeridenticaldupscollapse/conflictingdupsrefuse. Scalar
strings bounded/controlsinvisiblecharsrejected. PublicHTTPURLsno credentials/
whitespace/backslash, query/fragmentdropped, neverfetched. Exactnewskeyconsistent
existingprojectnewline-normalizedURLhash; URLqueryusedforidentity thenstripped
fromdisplay, suppliednewscoordinatesnotinferred. IMO7/MMSI9ASCIIdigitsformatonly,
no checksum orownershipverification. Privateextras refused.

Allclockssuppliedaware ->UTC ->1970..2100 rangeafterconversion. Future>5min skew
labelsfuture, neverquietlyfresh. Vessel15minfreshnessfromreported_at, notlayer
observation; missingreporttimeunknown. News24hfromlocated_at, publicationnotgeo
clock. Portdatedreference notlive. Layerobservedage24h, no wallclockfetch. Dates
are suppliednotverifiedmeasurement. Returnedcopydoesnotaliasinputs.

7focusedstdlibtestsPASSincludingempty/malformedmixedlayers/caps/dups/clockbounds/
future/stale/unknown/antimeridian/boolNaNinfhugeint/halfcoords/ASCIIIDs/URLs/
privateextras/controls/aliasing. NoUI/pixel claim, no liveAIS/portsdataavailability.
NewmapoverlayUI/sourcecatalogue remainseparatereviewedwork. Existinggeospatial
featuresfirstwins/dropbehavior andship_viewcaptured_at semanticsnotused.

V2newsdedupebindsverifiedproject+articlekey, opaqueprovidedidnottheidentity;
outputidcanonicalproject:key. Identicalsamearticlewithdifferentids collapses;
conflictingcoords/display/sourcefieldswholelayerinvalid. Vesselrepeatednonempty
IMO/MMSIacrossdifferentopaqueidrefuseswholelayer, noverifiedownershipclaim.
Boundsbeforeprocessing: exactinertcopydepth8/nodes10000/dictkeys15/string2048/
list100, no nonstringkeys/hugeints/nonfinite values. Invalidoverallinertshape
refusesenvelope, notpartiallayers. Thenperlayerclosedvalidation/atomicinvalid.
Overallinput/result1MiBUTF8budget, eachlayer512KiBoutput, nopartialtruncation.
9focusedtestsv2includingnewsidcollision/vesselIDs/inputkeynodebytecaps. Hash/
trustedinputsnotexternalidentityproof; no live map ready claim.

ReviewV2SAFEpuresuppliedcontract. Globalinertpreflight/overallinput-result1MiB
failureinvalidateswholeenvelope; point/closedschema/perlayer512KiBfailurelayer-
localinvalid, otherlayerskept. MultibyteUTF8budgetregressionsretained. No navigation
orcurrentAISclaim, clock/provenance suppliednotverified, querystrippedURLs/public
inputonlycaveatsretained.10focusedfinalPASS, fullsuite980next.

<!-- END-ORIGINAL-DOC -->


<a id="doc-108"></a>

### Reference: `integration/NATIVE-MAIL-PROJECTION224.md`

<!-- ORIGINAL-DOC {"bytes":3821,"path":"integration/NATIVE-MAIL-PROJECTION224.md","sha256":"349ccdda846c6b5ec246e142d91ae8d1f3aeb4eb5c7ef94a94d64ceabcb5219b"} -->
# 224: native-shaped supplied rows, not a database read

Pure parser to produce the 223 assertion projection. It adds no authenticated
read, historical completeness, current state, delivery or owner authority.
A complete coherent graph can be wholly invented. control.history_complete True
is that row's own claim, not evidence. An omitted whole graph can pass too.
The output flags source_authenticated, history_verified, current_state_verified,
send_allowed, ready, owner_approval and ledger_wired are all False.

OFF does not inspect arguments or import anything. ON takes exact native-shaped
control, receipt and article dictionaries, plus explicit expected recipient
fingerprint and history manifest. Kind is email, purpose digest. Caps checked
before processing: 128 receipts, 10000 articles, each receipt 1..120 sorted unique
lowercase ASCII 24-hex IDs. 128 times 120 is 15360, so a full graph can exceed the
article cap and refuse. No truncation or silent deduplication. No default history.

Reproduces 212 channel/control/article/receipt-binding hash equations with their
closed key sets. Schema and revision are exact ints, not bool; revision from 0
through 2**53-2. Rails, states, attempt, resolution reference and scope follow
212 _receipt rules. Receipt _id is only checked as 64-hex: nonce is not supplied,
so receipt _id == hash(control, nonce) CANNOT be checked. No 212 import,
constructor, driver check, client, file read, DB read/check/write or creation.

State-dependent graph rules preserve normal native history:
- Prepared/started receipts must be the single control.active receipt. Every ID
  must have an article pointing back with equal hash and state.
- Acknowledged receipts require every ID to point back with equal hash and state.
  212 cannot overwrite acknowledged articles.
- Cancelled/operator_resolved_unsent receipts need not have articles pointing
  back. 212 prepare can overwrite released article keys with a newer receipt.
  If an article still points back, hash and state must match. If it points to
  another native-shaped receipt key, that other receipt need not be supplied.
- For every article whose receipt IS supplied: ID membership, hash and state
  must match. Prepared/started articles must have a supplied active receipt.
- Acknowledged articles referencing unsupplied receipts ARE accepted. 212
  exclusions reads article state; requiring every old receipt would hit the
  receipt cap. Article key/schema/channel/purpose/receipt/hash/state still checked,
  but unsupplied receipt contents and binding are NOT verified. Released articles
  with unsupplied receipts also accept and are never exclusions.
- Active None with unresolved receipts/articles refuses. Active set without a
  supplied prepared/started receipt refuses. Duplicate receipt keys, article keys
  or article IDs refuse. Input order does not change sorted output.

Only acknowledged article IDs become projection ObjectId tuple. Cancelled and
operator_resolved_unsent do not exclude. Prepared/started yields active_state for
223 to hold the entire channel and purpose. The output necessarily echoes channel
and ObjectIds as private internal data for 223, not approval to disclose or send.
No raw receipt, attempt, resolution reference, manifest, body, sender or addresses
returned. Fixed error has no upstream message, cause or context. Inputs untouched.
No 224 call to 223, 221, 219 or a real ledger.

No send, wiring, store, environment/property change, deployment, activation,
trigger, cutover, mount or identity selection. Apps Script selected, SMTP fallback
held, 217 held, 201c write held. Sender blocker 222, authenticated native read,
history authority, provenance, durable body, and owner-approved recipients and
words remain open. Shape production is prepared, not an authorized live producer.

<!-- END-ORIGINAL-DOC -->


<a id="doc-109"></a>

### Reference: `integration/NATIVE200A.md`

<!-- ORIGINAL-DOC {"bytes":4756,"path":"integration/NATIVE200A.md","sha256":"0f209bc52f98506668455cc4ed1df1e6150b344fcf769ce2cfdfdf37e418ab54"} -->
# 200a pinned no-retry native transaction primitive

Unselected/default OFF. Only explicit existing synchronous MongoClient injection; no URI/env/client factory, production selection, 199 core integration, collection/index/journal creation, Atlas operation or activation. Source tests are not permission for a live write. ReplicaSetWithPrimary must be observed; reject standalone, mongos/sharded/load-balanced. Check actual checked-out connection too. Exact PyMongo4.18.2 and eleven source-module hashes checked against the official cp312 manylinux wheel, identical to local3.10 installed source. Refuse drift rather than silently accepting a compatible-looking driver.

Explicit lifetime lifecycle: begin original ClientSession(causal_consistency=False), start(snapshot/primary/majority+journal/wtimeout5000/max_commit_time5000), commit_once or abort_once, close. Original ClientSession passed to native collection operations. No body/commit retry wrapper or callback. Commit latch set before topology/checkout; one _conn_for_writes checkout and one explicit conn.command(...,no_reauth=True) call. The pinned equivalent of _finish_transaction spec construction adds native writeConcern, maxTimeMS, recoveryToken and lsid/txnNumber/autocommit via _apply_to. No invented/reused lsid or transaction number. Private API is intentionally pinned, not stable-public-API compatibility. Client/ambient CSOT refused so maxTimeMS semantics cannot silently change. Auto-encryption refused; retryReads/retryWrites disabled.

_commit_transaction / _finish_transaction_with_retry / with_transaction are never used. Commit/abort route never enters _retry_internal. Ordinary body native find/write APIs may enter _retry_internal with retryable=false: one attempt, zero retry; parent clarified this is acceptable. _select_server may discover/select/handshake a connection before dispatch; this is not replay of a commit. Pinned checkout path has no callback replay. Initial v2 had a hidden code391 reauth replay in decorated Connection.command reached via Database._command. Independent audit rejected it. Repaired v3 bypasses Database._command, sets no_reauth=True, and refuses MONGODB-OIDC clients. ReauthRequired now raises/holds rather than sends a second frame. command_runner._run_command sends one encoded command then reads one reply. Partial socket send/receive loops complete that frame, not another command. Need independent audit of this exact connection/pool/network path before landing; source/wire tests complement but do not replace review.

Any exception after commit latch, including checkout failure, drop, timeout, retryable/unknown label, writeConcernError, cancellation or topology mismatch, is held unknown. finally marks native session COMMITTED, mirroring driver's own lifecycle, so end_session never calls its auto-retrying abort helper after commit attempt. Empty STARTING transaction is COMMITTED_EMPTY without network. Beforecommit explicit abort_once uses one direct primitive; close of unattempted in-progress session quarantines local state/no implicit network abort. No second begin/start/commit/abort; close idempotent. No retry permission or cached external answer inferred from acknowledged commit.

Tests use real hash-pinned PyMongo TCP/OP_MSG to a disposable loopback protocol fixture, not mock send counters. Verify wire commitcount1/lsid/txnNumber/autocommit/writeConcern/maxTimeMS/admindb, no abort after lostreply or serverretryablelabels/stepdown/writeConcernError. Commit and abort code391 wire cases now verify one frame each; native _finish_transaction/Database._command no longer used. Public commit/retryhelper/_retry_internal patched to throw during commit yet correct path passes. Emptytxn, oneabort, close quarantine, checkoutloss, ambienttimeout, topologychange, realmongos/standalone/loadbalanced andretryclient refusal. This proves realdriver-to-fixture framing/oneattempt only, not servertransaction durability/snapshot isolation or realAtlas roles/topology.

200b still owes durable pre-registered journal/source guard/outcome marker plus native core integration: no reclaim/no TTL/no auto-clear; startup unresolved intent blocks writes. This local200a uncertainty flag is NOT restart durability. 200c measurement harness and separately authorized disposable realreplicaset/Atlas proof still required; no production/native capacity-ready claim. Existing199exactsyntheticprovider restrictions/oldproduction bytes unchanged.

Official artifact/source URL recorded in native200a-pins.json. Command semantics context: https://www.mongodb.com/docs/manual/reference/command/commitTransaction/ . Stable PyMongo docs currently4.18.3, not evidence for4.18.2 private behavior. No workflow/settings/otherrepo/newgrant changes.

<!-- END-ORIGINAL-DOC -->


<a id="doc-110"></a>

### Reference: `integration/NATIVE200BA.md`

<!-- ORIGINAL-DOC {"bytes":3520,"path":"integration/NATIVE200BA.md","sha256":"a5fa23ea3ae954f0fa6e4c9fbdfcdef96d7541a3d8300cbc9a6409c3178fb607"} -->
# Native 200b-a: source only, default OFF

Adds a new NativeArchiveCore and fixed raw bridge. No existing 199 types,
adapters or gates change, and existing exact type gates reject the new core.
No production selection, client construction, env reading, migration, mail,
Atlas operation, workflow file or deployment is included.

Eight exact geo_intel collection mappings are inspected with listCollections
and listIndexes before enabled core use and before writes. Collections must
already exist, journal validators must exactly match VALIDATORS (strict/error),
and every collection must have an ordinary unique _id index and no TTL.
Inspection is read-only and bounded to exhausted cursors. No getMore/provision.
Observed inspection cannot prevent an owner concurrently dropping a collection.
Gate 2 therefore additionally requires a verified restricted role without
collection-creation privilege, verified schemas/indexes, and a maintenance
boundary for owner DDL. This code does not grant or configure those permissions.

Outside-transaction finds use majority readConcern; writes use majority+journal
with a 5-second write-concern timeout. Native transactions inherit the 200a
snapshot/majority settings. Every bridge operation uses one checked-out primary
connection and command(no_reauth=True), never Collection retry wrappers.
Commands have 2-second maxTimeMS and an 8-MiB encoded command/reply cap. Finds
request at most two rows, reject duplicates and nonzero cursors. Index inspection
is capped to 16 rows. This pins the existing 4.18.2 private-driver source surface.

Guard CAS is first, then majority readback, then immutable intent insert and
readback, all before the write transaction begins. The core independently plans
under a read-only transaction, reserves the journal, and revalidates the full
bounded chain and source revision in a fresh native transaction. Source CAS and
outcome marker are in that same transaction. commit_attempt is durably recorded
before the sole commit primitive; acknowledged is recorded after its ACK.
Failure/unknown outcomes remain held. No retry, reclaim, TTL, deletion, release,
or rollback compensation is provided. Even an ACKNOWLEDGED operation retains
its guard. Restart reconciliation only reports observed facts, never permission
to retry or clear holds. A missing intent after reservation is a hold.

One guard per source limits this unit to one successful operation until a
separately reviewed closure protocol. Serial capacity is 4096 and is never reset.
The new native collector ledger/budget adapters are a separate 200b-b unit.
Continuous cadence, actual replica-set durability, real 3-GiB measurements and
live cutover are not proved or authorized by these fixtures.

Tests use the actual pinned PyMongo driver against a synthetic loopback TCP
OP_MSG server, including kind-1 document sequences. This exercises real driver
serialization/no-reauth behavior, not MongoDB isolation, validators, replication,
crash persistence or transaction durability. Synthetic crash cuts are simulated
lost/error replies after processing, not operating-system power loss.

## Superseded gate2 role claim

The earlier no-creation-role requirement above is superseded by
NATIVE201GUARD.md: INSERT itself can permit implicit collection creation.
The operational role is least-privilege, NOT creation-proof. All-eight exact
validator preflight, owner-exclusive DDL boundary and an accepted one-write
inspection/insert TOCTOU effect replace that claim. No zero-effect guarantee.

<!-- END-ORIGINAL-DOC -->


<a id="doc-111"></a>

### Reference: `integration/NATIVE200BB.md`

<!-- ORIGINAL-DOC {"bytes":2189,"path":"integration/NATIVE200BB.md","sha256":"39dd6b5749c20789f8db12170ff686d6c4f106c0a49cdf0f7b616ec04f213b5d"} -->
# Native 200b-b: additive pair only

New NativeArchivedCollectorLedger and NativeArchivedProxyReceiptBudget inherit
unchanged 199 business methods, but accept only the exact enabled NativeArchiveCore
and override its mutation path. Old 199 exact type gates are byte-unchanged and
continue to reject these new types. No broker/collector/production composition
accepts them. No transport, env/client construction, provisioning, live selection,
automatic rollover, guard release or closure is included.

A nonblocking core-local lock serializes preparation with rollover. A read-only
transaction verifies the full bounded archive chain, validates the method's
business transition, and computes the exact resulting source. A no-change replay
returns status only without a guard reservation. A mutation records an immutable
journal plan, then a fresh native transaction revalidates the complete snapshot
and identical result before source CAS/readback. The core adds the outcome marker
in that same transaction and durably records commit_attempt before its sole
commit. All 200b-a raw bridge, preflight, concerns, no-reauth, capacity, restart
hold and no-auto-release behavior remains in force.

This unit deliberately permits only one mutation per pre-existing idle source
guard. Even acknowledged writes leave it held. Multi-step workflows cannot run
continuously until 200b-c separately proves closure/admission. Tests pre-seed
independent phases to exercise each transition; they do not release guards
between transitions. Unknown/expired broker tickets keep calls charged and
active held, and archived collector jobs cannot reactivate. Nonce/body/principal
scope, fence, clock, counts, deadlines and bounded capacity use unchanged 199
business validation. Status and replay do not authorize network delivery.

Actual pinned 4.18.2 loopback OP_MSG tests exercise serialization and one-frame
391 source/commit errors. No Atlas requests or actual replica-set durability,
validator enforcement or crash persistence measurements are included. Gate 2
still requires the restricted no-creation role plus verified schema/index/DDL
boundary. Native 200b-c closure is the next separate review unit.

<!-- END-ORIGINAL-DOC -->


<a id="doc-112"></a>

### Reference: `integration/NATIVE200BC.md`

<!-- ORIGINAL-DOC {"bytes":3780,"path":"integration/NATIVE200BC.md","sha256":"1c384f23c6909238083abdc93d38924abed9e6f8251077b132c3b7db09a44830"} -->
# Native 200b-c: separately selected automated admission

Adds NEW admission store/preflight/journal/core/adapters, with old 199, 200a,
200b-a and 200b-b bytes unchanged. No production composition selects them.
Default OFF, explicit injected client, no env reading, provisioning, migration,
Atlas request, transport effect, workflow edit or live cutover.

The extended validator is a distinct reviewed schema, inspected only. Existing
outcome shapes remain accepted, plus a discriminated immutable admission record
in native_outcomes200. No ninth collection. Guards add admission_attempt.
Old preflight intentionally rejects the extension, and old exact adapter gates
reject the new core. Schema installation/maintenance is a separately authorized
gate-2 activity; this code does not install it.

Admission only from acknowledged with capacity remaining. A read-only snapshot
verifies the full chain/source and the exact prior immutable intent/outcome.
The current source hash must equal the old outcome, and the next plan's revision,
epoch and head must match. Majority+journal CAS first permanently latches
acknowledged-old -> admission_attempt, retaining old operation/serial. A fresh
native transaction re-proves the same source and exact latched guard, then
atomically CASes reserved-new, inserts the immutable successor intent, and
inserts an immutable admission record binding old/new operation IDs/serials
and the proven source hash. Readback happens inside that same transaction.

Only its same-process known commit ACK returns an executable successor intent
for the source-write transaction. Unknown/lost ACK never returns that intent.
A failure before commit leaves admission_attempt held; a committed but unknown
admission leaves reserved-new held. No idle release, retry, reclaim, compensation,
TTL, delete or restart execution exists. reserved/commit_attempt cannot admit.

Accepted consequence: a crash after acknowledged admission but before successor
execution permanently holds the source until owner review. Read-only restart
reconciliation labels this admitted_but_never_executed_owner_review_required.
The same observation also covers a landed admission whose ACK was lost: it does
not assert the ACK was received or distinguish that historical fact. Latch-only
and malformed admission records have distinct held states. None clears holds,
grants retry, or claims recovered capacity. Future restart recovery is excluded.

First idle guard reservation uses the original 200b-a ordering. All later source
writes still use its journal-before-write-begin, same-txn sourceCAS/outcome marker,
commit_attempt-before-singlecommit, and acknowledged-but-not-idle semantics.
Read-only no-change replay remains status only. The local lock is process-local;
the durable guard CAS is the cross-process stop. Concurrent external writes cause
loud refusal. Guard serial caps at4096 and is never reset.

Pinned4.18.2 synthetic loopback tests cover multi-step collector/broker workflows,
admission wire errors/lostACK, crash-before-execution, exact atomic session/txn,
missing proof and capacity. They do not prove actual MongoDB isolation, validator
enforcement, replication or crash durability. Restricted no-creation role plus
verified schemas/indexes/DDL boundary still required. Real measurement/cadence
activation needs separate gates and explicit owner live approval.

## Superseded gate2 role claim

The earlier no-creation-role requirement above is superseded by
NATIVE201GUARD.md: INSERT itself can permit implicit collection creation.
The operational role is least-privilege, NOT creation-proof. All-eight exact
validator preflight, owner-exclusive DDL boundary and an accepted one-write
inspection/insert TOCTOU effect replace that claim. No zero-effect guarantee.

<!-- END-ORIGINAL-DOC -->


<a id="doc-113"></a>

### Reference: `integration/NATIVE200CA-OWNER.md`

<!-- ORIGINAL-DOC {"bytes":12428,"path":"integration/NATIVE200CA-OWNER.md","sha256":"4660328c1b292b6d7c040b5a79c41358c85d4dd99f2bf300d465022ce3448b59"} -->
# Gate2 owner steps package: review first, no activation

The offline owner_package(fingerprint=..., clock=...) function returns request
DATA only. It opens no client, reads no URI/environment, executes no command and
writes no file. Use the exact reviewed repo snapshot and pinned4.18.2 environment.
Fingerprint must come from the reviewed collector catalog/config, not a made-up
value; clock is the owner-reviewed initial integer source clock in UNIX epoch
seconds, NOT milliseconds. ready stays false.
The package is not proof that an Atlas cluster or account is configured correctly.

## 1. Choose and inventory before any mutation

Owner confirms the intended Atlas project/cluster/account, geo_intel DB, replica-
set (not sharded/mongos/loadbalanced), current server version and maintenance
window. Preserve an owner-controlled complete snapshot/backup and document the
restore path before changing schemas. Keep the proposed native selection and any
new collectors OFF. This package does not stop any existing collector or writer.
Before any schema installation, identify EVERY process writing EACH of the eight
collections, including pre-existing 197/198 collectors, broker writers, jobs and
manual/admin tools. Record the owner-reviewed writer inventory per collection.
Proceed only if a collection is verified new/unused, or ALL its current rows AND
EVERY current writer already satisfy its exact proposed validator for every
write shape. strict/error can reject legacy writes, even when current rows pass.
If writer identity, compatibility or quiescence is unknown or incompatible, STOP.
Any stopping, migration or writer change needs a separately approved preservation
plan; this package grants none and must not disrupt a running legacy writer.
Inventory all8 collections, current validators/indexes and exact source/guard/
genesis documents. No secrets in screenshots, logs or package evidence.

Use the package's readonly_verification_commands on the selected DB, one by one.
They inspect exact names, collection options and exhausted index cursors, not
user authorization. All8 must be ordinary pre-existing collections, unique
ordinary _id, no TTL, no view/time-series mapping. Validate source and complete
archive chains with the separately reviewed read-only200c-b harness when ready.

STOP if collection identity, state, existing data, backup, fingerprint, topology
or permissions are unknown. Do not infer empty from an empty cache or a failed
query. Retained checkpoints may be v1 orv2; all hot/archive/journal data must remain.

## 2. Separate administrator and runtime identities

Configure Atlas custom roles through Atlas UI/CLI/API, not db.createRole in
mongosh: Atlas manages those roles and can roll back out-of-band role changes.
The package role JSON is a request payload, not a command sent by this code.
Assign the operational identity ONLY the reviewed custom role: exact8 FIND,
INSERT, UPDATE, LIST_INDEXES, plus DB LIST_COLLECTIONS. Inspect all additional
built-in/custom/inherited/specific user privileges; Atlas privileges combine.
No REMOVE/drop/collMod/createIndexes/createCollection/validation bypass/admin
or broad readWrite role is proposed. Use a separate owner admin for schema DDL.
The coarse role may later be narrowed per collection if separately reviewed.

IMPORTANT: this is least-privilege, NOT creation-proof. MongoDB permits non-capped
collection creation with INSERT on that collection, even without CREATE_COLLECTION.
Mongo privileges are grants, not a deny list that overrides other roles.

Owner-only exclusive DDL is an operational requirement while native selected:
no concurrent collection drops, schema/index changes or restoration. The
inspection-to-insert race can permit ONE write into a recreated bare collection.
The NEXT exact-schema inspection holds. This accepted limitation is not zero-
effect safety. Role restrictions alone do not eliminate it.

## 3. Install exact schema requests under explicit owner approval

schema_requests contains both create_if_verified_absent and
modify_if_existing_owner_reviewed. These are alternatives, never run both.
- Verified absent: owner admin may create the exact collection with its reviewed
  validator, strict validationLevel and error validationAction.
- Existing: owner reviews ALL current rows against the new schema before choosing
  collMod. strict does not retroactively prove old rows valid.
- Unknown/mismatching shape: STOP. Do not delete, replace, relax or coerce records
  merely to make validation pass. No generic migration tool is included.

### Preserve integer types before any approved command

The returned Python objects are request data, NOT copy-paste execution commands.
Each concrete command, chosen identity, target and final typed payload requires
owner review and approval. Do not paste ordinary JSON into a JavaScript shell or
Atlas editor. Large bounds include 9223372036854775807 (int64 max); a JS Number
cannot preserve it exactly. Even exactly representable numeric values must not
be stored as doubles where the reviewed schema/data expects int/long.

Use Canonical Extended JSON v2 for transport, generated offline from the reviewed
package through pinned PyMongo 4.18.2. This serialization fragment performs no DB
operation and assumes `package` is the reviewed owner_package return value:

```python
from bson.json_util import dumps, loads, CANONICAL_JSON_OPTIONS
requests_ejson = dumps(package['schema_requests'],
                      json_options=CANONICAL_JSON_OPTIONS, sort_keys=True)
genesis_ejson = dumps(package['empty_new_genesis_templates'],
                     json_options=CANONICAL_JSON_OPTIONS, sort_keys=True)
# Decode only through the pinned driver's Extended JSON decoder, not json.loads.
typed_requests = loads(requests_ejson, json_options=CANONICAL_JSON_OPTIONS)
typed_genesis = loads(genesis_ejson, json_options=CANONICAL_JSON_OPTIONS)
```

Canonically encoded signed int32 values use {"$numberInt":"5000"}; int64 bounds
and integer clocks outside signed int32 use {"$numberLong":"9223372036854775807"}
(or the exact clock's decimal string). Booleans stay booleans, not integers.
These wrappers are transport representations: decode them into BSON numeric
values before any separately approved DB command. Never install the wrappers
as literal validator subdocuments, run JSON.parse on them as a substitute for an
Extended JSON decoder, use relaxed serialization, or convert values through float.
If a chosen UI/tool cannot prove lossless typed decoding, STOP and choose a
separately reviewed typed command path. Large epoch-second clocks still use
int64; the input unit remains seconds. This is not a BSON Date/millisecond value.
Genesis ordering and idempotency remain deferred to a future approved harness.

The exact admission validator set includes five source/archive/checkpoint schemas
plus3journal schemas, with an $or outcome/admission validator. Hashes, complete
chain, fence uniqueness, phase relationships and recursive typed checkpoint
content still require app validation. DB structural schemas do not replace it.

After each separately approved install and before further setup/selection, run
the corresponding read-only verification commands through pinned PyMongo 4.18.2
on the verified geo_intel DB. Require the exact intended collection, exhausted
cursor and strict/error options; compare its returned validator against the
reviewed VALIDATORS entry. In addition to the admission preflight's object-value
comparison, require type-preserving canonical equality using the same pinned
`dumps(..., json_options=CANONICAL_JSON_OPTIONS, sort_keys=True)` on each side.
This stronger owner check distinguishes an int/long from an equal-valued double
(Python numeric equality alone does not). Any int-vs-double difference, lost
precision, int-width drift or missing/unverifiable readback means STOP, retain
the evidence and get source review. No automatic repair/coercion is authorized.
Use the same typed exact readback for any later approved genesis insertion.
Compare actual listCollections validator objects to the package EXACTLY as the
admission preflight does. Do not treat equivalent-looking normalization as PASS:
if the server returns a different $or/oneOf/schema form, STOP for source review.
Real server normalization and BSON numeric types remain unmeasured. No index
creation/drop request is emitted; resolve non-ordinary _id or TTL with a separately
approved preservation plan, not a blind dropIndexes command.

## 4. Genesis templates apply ONLY to a verified brand-new empty install

empty_new_genesis_templates contains collector/broker source, batch0 manifest and
idle serial0 guard per family. These are templates, NOT writes. Insert only after
owner confirms all dependent mappings are empty and each ID absent, and approves
the final documents, snapshot and actual collector fingerprint. Use majority+j
and exact readback if the owner later authorizes the setup. No upsert or overwrite.

Existing v1/v2 ledgers/budgets, any calls/fences/active jobs/receipts/history,
checkpoints, archive chain or journal entries invalidate new-empty templates.
STOP and commission a separate migration plan preserving every full record and
hold. Never reset calls, fences, serials or active tickets; never truncate hot64.
No converter or replay/recovery permissions are supplied.

## 5. Verify on actual separately authorized staging

Before gate2 can pass, record actual server/version/topology and role evidence,
all8exact returned schemas/indexes, valid full sources/chains, and hashes of the
reviewed request package. Read-only200c-b checks may establish observed state,
not crash durability or live-readiness. Required staging checks still unrun:
- Actual $or/oneOf/$jsonSchema acceptance/rejection for all lifecycle shapes,
  checkpoint1/2, BSON int/long bounds, schema normalization and strict/error.
- Pinned no-retry native transaction/body maxTimeMS behavior on that server.
- Owner-approved disposable drop/bare-recreation test, verifying NEXT write
  inspection refuses; preserve accepted one-write race in the report.
- Actual known/unknown commit/abort/crash persistence and3GiB workload proof.

The last items are mutating measurements: require a future separately reviewed
write harness with owner-approved disposable mappings/effects. The current fixed
geo_intel client/store cannot be repointed to an invented staging DB. Do NOT run
these tests on production or infer proof from the loopback fixture. No dormant
write tests are included in the read-only harness.

## 6. Completion is not cutover

Gate2 observed PASS alone does not turn collectors on. Owner diagnosticgate3,
reviewed production factorygate4 and explicit final ownerOKlive gate5 remain.
201c is held until gate2/3 contracts align. Old collectors are not stopped, emails
are not sent, and deployment/live switches are not touched by this package.
Do not confuse "new native selection OFF" with permission to stop existing
writers. The section 1 per-collection writer-compatibility STOP applies before
any strict validator change, independent of all later cutover gates.
DB-level LIST_COLLECTIONS exposes all collection names in geo_intel; this is
an accepted scope of the proposed role, not a collection-name privacy boundary.

## Official sources fetched for this package

- Create privileges, INSERT permits creation:
  https://www.mongodb.com/docs/manual/reference/command/create/
- Implicit creation, including transactions:
  https://www.mongodb.com/docs/manual/reference/command/insert/
- Atlas role management and combined grants:
  https://www.mongodb.com/docs/atlas/security-add-mongodb-roles/
- Atlas action names:
  https://www.mongodb.com/docs/atlas/reference/custom-role-actions/
- Collection options and verification command:
  https://www.mongodb.com/docs/manual/reference/command/listCollections/
- JSON schema and query-operator validation:
  https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema
- Transaction runtime/DDL limitations:
  https://www.mongodb.com/docs/manual/core/transactions-production-consideration/

- Canonical Extended JSON and pinned Python serialization/decoding guidance:
  https://www.mongodb.com/docs/languages/python/pymongo-driver/current/data-formats/extended-json/
- Numeric Canonical Extended JSON v2 representations:
  https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/

<!-- END-ORIGINAL-DOC -->


<a id="doc-114"></a>

### Reference: `integration/NATIVE200CB.md`

<!-- ORIGINAL-DOC {"bytes":3479,"path":"integration/NATIVE200CB.md","sha256":"dc862b267956b497d98f1ffc2eeeae24d026a8826aa3da2c11d27106b5d108bc"} -->
# 200c-b read-only measurement harness: observed evidence only

integration/native200_readonly_measurement.py is a DEFAULT-OFF observation
function. measure(client, enabled=True, fingerprint=...) requires an explicit
owner-constructed pinned PyMongo 4.18.2 synchronous client, the reviewed
collector fingerprint and a monotonic clock. It NEVER constructs or closes a
client, starts a session/transaction, reads a URI/environment, installs a
schema or runs any write command. The command allowlist is exactly: hello,
buildInfo, listCollections, listIndexes, find and majority count on the fixed
eight geo_intel collections, every one with maxTimeMS 2000, exhausted
single-batch cursors (no getMore) and the 8 MiB command/reply cap.

## What one successful run establishes

- Observed replica-set primary topology (not a URI assertion; mongos and load
  balanced service IDs refused), sanitized server version string and pinned
  driver hash verification.
- All eight collections exist as ordinary collections with exact typed
  strict/error validators matching the reviewed VALIDATORS set. Comparison is
  Canonical Extended JSON with sorted keys, so an int/long bound stored as a
  double, precision loss or width drift is a STOP, never a silent pass.
- Ordinary unique _id index, no TTL index, bounded index inventory.
- Complete bounded contents: every document, string identities unique,
  per-collection 16384-row cap, cross-checked by a majority count so a
  silently truncated singleBatch is a STOP, total observation byte cap 32 MiB.
- Complete immutable archive chains for both families revalidated offline by
  the reviewed 199 verifier: manifest linkage, record hashes, chronology,
  fence/revision consistency, no archive orphan or missing row, retained
  collector checkpoints subset of known jobs and equal to archived copies.
- Journal consistency: exactly two guards, serial/contiguity, plan shapes,
  outcome markers canonically equal, admission closure linkage to proven
  source hashes, acknowledged operations proven against current source
  revision and after_hash.
- A second full inventory after validation; ANY data/schema/index change
  between the two reads is a STOP, because this is NOT an atomic snapshot.

## What a PASS is NOT

ready stays false. A run is observed evidence at two read instants, not an
atomic snapshot, not proof of quiet writers, not crash/commit durability, not
live-readiness, not role/privilege verification, not capacity release and not
retry/recovery permission. No measurement here turns collectors on, proves a
real Atlas cluster correct or authorizes the next gate.

## What is deliberately absent

No dormant mutation tests, no drop/recreate probes, no transaction body
maxTimeMS measurement, no 3 GiB workload, no write harness hidden behind a
flag. Those exist only as future separately reviewed scopes with
owner-approved disposable mappings; the fixed geo_intel stores are never
repointed at an invented staging DB. On ANY refusal the harness stops with no
mutation, retry or repair; reauthentication (391) is consumed and re-raised,
never replayed.

## Output evidence

Sanitized hashes per collection (validator/index/data SHA-256, row counts),
chain summaries, guard phases, observed byte total, driver and sanitized
server version. No host names, credentials, URIs or document contents are
returned. Evidence is for owner/reviewer comparison against the approved
200c-a package; it grants no permission by itself.

<!-- END-ORIGINAL-DOC -->


<a id="doc-115"></a>

### Reference: `integration/NATIVE201A.md`

<!-- ORIGINAL-DOC {"bytes":2445,"path":"integration/NATIVE201A.md","sha256":"ee17e6b38cf8f49aed84d8cf2319895df76045d19b72938963d2c92e27baac9d"} -->
# Native 201a: atomic immutable checkpoint and source advance

New NativeCoverageCheckpoints exposes validated get only, no standalone put.
It accepts the exact AdmissionStore collector_checkpoints197 mapping and keeps
existing typed-budget, encoded schema, input hash and source-coverage hash
validation. checkpoint_row is pure preparation, not a database mutation.

New NativeCheckpointCollectorLedger adds checkpoint_and_advance. A read-only
complete-chain/source view verifies the exact running key/fence, lease/clock,
bounded inputs/coverage and any existing immutable checkpoint. A conflict refuses
before admission. A journal plan precedes a fresh source-write transaction. In
that ONE transaction, absent checkpoint is inserted via raw no_reauth and read
back exactly, then source is CASed running -> fetch_complete and read back. The
inherited source outcome marker is in that same transaction. Existing identical
checkpoint is verified, never rewritten. No upsert, replacement, TTL or deletion.

Admission and source commit semantics remain unchanged: latch before admission,
known same-process admission ACK only, journal before source mutation, no retry,
no idle release, and unknown outcomes held across restart. Checkpoint presence
alone never grants permission to resume a job or redo fetch/write work.

Existing 199, 200a, 200b-a/b/c bytes and exact gates unchanged. New ledger and
coverage types are unselected; no collector cycle/composition accepts them yet.
No live flag, production selection, env/client creation, workflow, provisioning,
Atlas request, timer or article write is included. Source-only/default OFF.

Pinned4.18.2 loopback fixtures exercise shared lsid/txnNumber for checkpoint,
sourceCAS and marker, real391 single-frame failures and unknown commit, immutable
scope, wrong ticket/clock/lease, replay of identical checkpoint and hash corruption.
The fixture does not prove actual Mongo isolation/validators/crash durability.
Gate2 role/schema/index/DDL boundary and gate3diagnostic evidence remain required.

## Superseded gate2 role claim

The earlier no-creation-role requirement above is superseded by
NATIVE201GUARD.md: INSERT itself can permit implicit collection creation.
The operational role is least-privilege, NOT creation-proof. All-eight exact
validator preflight, owner-exclusive DDL boundary and an accepted one-write
inspection/insert TOCTOU effect replace that claim. No zero-effect guarantee.

<!-- END-ORIGINAL-DOC -->


<a id="doc-116"></a>

### Reference: `integration/NATIVE201B.md`

<!-- ORIGINAL-DOC {"bytes":2626,"path":"integration/NATIVE201B.md","sha256":"365cb5dc3b2afdd189b3ad17b2d095bde770519f4235979dfe5fcaaa3d3d092d"} -->
# Native 201b: unselected broker, collector and composition

New native201_broker accepts only AdmissionProxyReceiptBudget and the existing
exact FixedProxyTransport. Auth/session/CSRF/principal scope and closed ships/AI
routes remain mandatory. Only known claim AND send-start ACKs allow proxy entry.
Replays return status only, not cached answers. Unknown/late transport holds the
global ticket; no refund, resend or upstream-stopped claim. Existing empty model
catalog stays closed, provider restrictions unchanged. No actual proxy call in
fixtures: transport execution is mocked.

New native201_collector accepts only NativeCheckpointCollectorLedger and
NativeCoverageCheckpoints on the same client. Existing CollectorConfig, supervised
whole-cycle fetch contract, resource evidence and exact GeoArticleWriter guards
remain. After fetch and heartbeat, checkpoint_and_advance atomically inserts the
immutable checkpoint and advances running -> fetch_complete with its marker.
No ordinary checkpoint put/upsert. All later ledger steps use native admission
and journaled source mutations. Replays never fetch or enter article writes.
Article writes happen only after known write-started ACK and heartbeat/evidence.
They are NOT claimed transactional with ledger/checkpoint operations.

New build_native_composition default OFF returns the public app unchanged.
Explicitly enabled source fixture mounts the same closed authenticated broker
routes and owner-Bearer retained collector GET-status route. Collector auth,
Origin/query/body/method/key checks precede state access. Status requires current
job evidence and exact retained checkpoint/hash coverage; generic 503 on missing
or corrupt state, never recovery permission. Responses are no-store.

Existing 199 gates/source, production_entry.py, public_live107.py, collector197_job
and orchestrator remain unchanged and reject the new types. No env/client creation,
production selection, migration, timer, workflow edit, live flag or DB provisioning.
Default-off/source-only/unselected. Production factory is a later 201c unit after
gate2/3 contracts align; owner final live approval still required.

Pinned4.18.2 loopback lifecycle tests prove serialization and local behavior,
not Mongo validation, isolation, replication or crash durability. Gate2 least-
privilege role is NOT creation-proof: INSERT can create collections. Owner-only
exclusive DDL boundary plus all8exact schema inspections and accepted ONE-write
TOCTOU effect (then next inspection holds) remain requirements. Real staging
normalization/$or/oneOf/BSON/maxTimeMS and diagnostic evidence are unverified.

<!-- END-ORIGINAL-DOC -->


<a id="doc-117"></a>

### Reference: `integration/NATIVE201GUARD.md`

<!-- ORIGINAL-DOC {"bytes":3628,"path":"integration/NATIVE201GUARD.md","sha256":"4d24dd1b5f6d425a8b428975da71d05c1edfea0202b60e553a3b26e326b759e3"} -->
# All-eight validator selection gate

The admission preflight now requires exact strict/error validators on all eight
fixed mappings. No mutation semantics change. New five validators come from:

| Mapping | Shape evidence | Validator scope |
| --- | --- | --- |
| collector_jobs197 | replay199_schema.source and durable_ledger._valid_document/_valid_job | fixed schema2 source, nullable active job, hot history64, closed counts, archive fields |
| finder_budget198 | replay199_schema.source, finder198_receipts._v2 and finder198_budget._state | fixed schema3 source, nullable active ticket, hot receipts64, archive fields |
| collector_replay199 | replay199_schema.manifest/record/validate_record and collector197_archive.pack | discriminated manifest/record; terminal collector rows, nullable retained checkpoint1/2 |
| finder_replay199 | replay199_schema.manifest/record/validate_record | discriminated manifest/record; complete broker receipt, null fingerprint/checkpoint |
| collector_checkpoints197 | DurableCheckpoints.put/get and CoverageCheckpoints.put/get, native201_coverage.checkpoint_row | closed checkpoint1/2 envelopes with bounded encoded arrays and exact hash/fence/version fields |

No fallback collection. Encoded content is genuinely variable recursively, but
its top-level projection is fixed. DB schema checks its bounded array envelope;
existing _encoded_budget/_decode/capture, hash and cross-field/source-chain checks
remain mandatory. Validators are structural envelopes, not substitutes for
hashes, key/fence uniqueness, phase relationships, budgets or archive-chain proof.
All three existing journal validators remain byte-equivalent in value.

## Explicit correction to prior native docs

Prior NATIVE200BA/BC/201A references to a restricted no-creation role are
SUPERSEDED. MongoDB INSERT permission itself permits creation of a non-capped
collection. Removing CREATE_COLLECTION does NOT make an insert-enabled role
creation-proof. The revised gate2 requires least-privilege find/insert/update on
exact mappings, listCollections/listIndexes for inspection, no extra/inherited
roles or explicit DDL grants, plus an owner-only exclusive DDL boundary while
the native path is enabled. No concurrent drops/schema changes are allowed.

The inspection-to-insert TOCTOU window remains accepted. An administrative drop
inside it can allow ONE write into a recreated unvalidated collection. The next
inspection rejects its missing exact validator, holding the source. This is
fail-closed continuation, NOT a zero-effect race guarantee. Tiny timing is only
mitigation. No claim of transaction durability or live enforcement is made.

All-eight bare recreation rejection is tested before the next write. Actual
Mongo $or/oneOf validation, listCollections normalization, BSON numeric types,
in-transaction maxTimeMS and DDL/recreation behavior must be verified on separately
authorized staging. No schema installation/Atlas operation is included.

Source-only/defaultOFF/unselected. Old199/200a/200b-a preflight and every native
journal/core/adapter unchanged. Admission preflight strictening is deliberate,
so the previous journal-only schema installation now refuses to enable. Gate2
owner package must install/verify the new full schema set before selection.

Official grounding:
https://www.mongodb.com/docs/manual/reference/command/create/
https://www.mongodb.com/docs/manual/reference/method/db.createcollection/
https://www.mongodb.com/docs/manual/reference/command/insert/
https://www.mongodb.com/docs/atlas/security-add-mongodb-roles/
https://www.mongodb.com/docs/atlas/reference/custom-role-actions/

<!-- END-ORIGINAL-DOC -->


<a id="doc-118"></a>

### Reference: `integration/NEWS-PAGES185.md`

<!-- ORIGINAL-DOC {"bytes":3287,"path":"integration/NEWS-PAGES185.md","sha256":"f1be6081bdbdea959e9f2a428a3ce70aaab1fbb0ac70ce8036fc8fcd392d854c"} -->
# Whole Geo store cursor paging (source-only, default OFF)

PUBLIC_NEWS_FULL_PAGES_ENABLED=false is the default. true requires all existing
public live read/disclosure/mapping/read-only credential gates. No new client or
write privileges. Existing /api/news and loaded CSV remain first100 contracts.
The UI is unchanged in this reader unit. Infinite-scroll UI is a separate unit.

GET /api/news-page accepts single project=geo, q (200), category/country (100),
sort=newest/title/country/score, limit1-100(default25), cursor. Invalid inputs400,
disabled/unavailable503, expired/query-bound mismatch409, busy/capacity429.
Every page still passes existing authorization and public sanitizer/projection.
Opaque random tokens reveal no raw IDs. They are continuation data, not auth.
Tokens bind exact query/limit; one immediately repeated continuation returns its
cached reply, avoiding consumption after a lost response. Older tokens expire.

An injected reviewed Mongo store .find scans the entire collection, no total
limit100 or RAM materialization. At most1000 raw rows scanned per page and100
returned. Filter-after-normalization preserves existing casefold semantics.
A sparse filter can return empty items with next_cursor; this is NOT EOF. Counts
are unknown, never asserted21k. Closed projection; sanitizer rejects oversized
and nested scalar fields. Batch100, server max_time_ms2000, existing socket and
pool bounds. No client query operators, offset/skip, aggregate or DB writes.

Sort is RAW SOURCE Mongo order: created_at DESC, title ASC, country ASC or score
DESC, plus unique _id same direction. This differs from loaded view's normalized
casefold/tie order and is labeled in the API. Missing/mixed source sort values
remain in the single cursor, avoiding unsafe type-bracketed keyset exclusions.
It is a mutable read, NOT a stable snapshot: concurrent edits/deletes/inserts can
change visibility or repeat rows. No whole-store consistency guarantee, current
count or performance claim. Refresh opens a new read. Mongo cursor lifetime,
server query budget and source failures can force restart earlier than expiry.

Worker-local state: max16 active/cached streams; nonblocking global lock permits
one page read at a time.120s idle/30min absolute expiry; background15s sweep plus
sweep on request. EOF/failure/expiry/explicit close closes cursor; worker restart
loses tokens409. Multi-worker routing needs sticky routing or a reviewed shared
continuation service before live enablement. Slow cursor.close can delay sweep;
server/socket bounds are not a hard overall wall-time guarantee. Abandoned UI
streams are reclaimed by expiry, not browser unload promises. No snapshot session.
No index is created. All raw sorts need real source/index/explain evidence before
live enablement or claiming efficient full-store browsing. _id unique tie-break
is a source Mongo property, not verified by fixture tests.

Grounding:
https://www.mongodb.com/docs/manual/reference/bson-type-comparison-order/
https://www.mongodb.com/docs/manual/reference/method/cursor.sort/
https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/cursors/
https://pymongo.readthedocs.io/en/stable/api/pymongo/cursor.html
https://www.mongodb.com/docs/v8.3/reference/read-concern-snapshot/

<!-- END-ORIGINAL-DOC -->


<a id="doc-119"></a>

### Reference: `integration/NEWS_PANEL_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1569,"path":"integration/NEWS_PANEL_LIMITS.md","sha256":"1d8c28ed84406b508a242b02f8131c14d76b3ca5ce637338381163ae22e1c387"} -->
# News panel controls

The news-only dark/light switch is session-local and does not change Finder's
independent theme. Manual refresh replaces news panels only, never player
iframes. No automatic news-refresh interval is enabled.

The critical-story panel uses supplied Geo risk_level=CRITICAL and zoned
collection timestamps in a rolling inclusive 24-hour window. Missing, naive,
future and out-of-window times are not presented as recent. It does not apply
Geo risk labels or keyword rules to other-source news. Other policy remains
unavailable. Counts are loaded-read-view counts, not full database totals.
The panel is capped at100 stories with truncation disclosed. It does not send
alerts. Reader/auth failures fail closed, not as an empty successful panel.

This increment does not yet add live video, channel management, source-health
refresh or tab removal. Those remain separate reviewed increments. All live
polling, collection, database writes, mail and deployment remain off.

Counts are rows, not distinct-story identities. The live-reader adapter loads
up to100 rows/project; the panel therefore cannot prove a whole-database24h
count. Sorting assumes API-normalized UTC timestamps. The helper is used
through views() in the API, not as a raw provider-row adapter.

This panel has no fetcher, but configured runtime.py can perform approved
database reads when explicitly enabled. Do not describe the whole project as
incapable of fetching. Full-suite counts are local author test results; focused
review-bundle tests do not reproduce that entire suite.

<!-- END-ORIGINAL-DOC -->


<a id="doc-120"></a>

### Reference: `integration/OFFLINE232.md`

<!-- ORIGINAL-DOC {"bytes":4437,"path":"integration/OFFLINE232.md","sha256":"65d3fe2162dcb5d4e1b9ab5a5be7c2510fc882e8065a60c660334075e3d980c9"} -->
# Public offline shortlist CSV and keyboard scroll (232)

Public offline shortlist exports now use the same safe CSV quoting as the
online preview. Formula-like cells get a leading apostrophe, NULs are removed
and invalid surrogate characters replaced. Valid Unicode, quotes, commas and
newlines remain. Six columns, order, code/description/duty/source values and
hsn-shortlist.csv filename stay unchanged. The shortlist table gains the
online preview's named, focusable scroll container. This supersedes the
offline CSV/shortlist caveats in FINDER_PARITY_PLAN; the original196 offline
limits document stays historical. No new persistent settings or live features.

finder_offline.shell calls the existing shortlist_scroll and shortlist_csv_safe
from finder_nested after the raw-source SHA gate and manual-ships transform,
before CSP script hash calculation. No copied sanitizer. Missing/doubled/already
applied anchors fail closed. Header and meta script hashes independently
recomputed; no unsafe-inline script permission, connect-src none unchanged.
Range returns full transformed200; no-store,403 gate and public marker unchanged.

BEFORE on clean7333a8a actual local cached offline page: formula/tab/CR/newline/
format-control notes exported unprefixed; NUL survived. Original Blob already
replaced an unpaired surrogate in downloaded bytes, so no before/after byte
change is claimed for that row. Astral/quotes/newlines survive both. Python3.10
CSV refuses NUL: probe uses a parsing-only sentinel then restores NUL in result;
raw downloaded CSV untouched. byte.decode keeps CR instead of universal newline
conversion. Initial harness parsing/desktop scroll wait/expected CSP errors
were corrected before final recorded BEFORE and AFTER, not product changes.

BEFORE outer width already fits320/390/1100 in this fixture. Missing focusable
container, not proven whole-page overflow. AFTER Tab from print reaches named
region at every width;320 ArrowRight scrolls and End exposes Remove.390/1100
fixture already fits, no forced-scroll claim. Actual final images inspected at
320/390/1100 light/dark, plus320 light/dark end-scroll: readable public banner,
code/description/note/duty/Remove; keyboard outline clear, no page overflow.
Full-page images include12rows; viewport crops used for readability inspection.

Two final consecutive browser_offline232 runs PASS, stable semantic results
excluding timestamps and animated scroll fractions normalized to nonzero bool.
The raw keyboardScroll pixel number is not stable (for example1versus2).
Real original CSV click/download from cached-local offline document, not mocked
quoting.12 synthetic in-memory notes only, no real device data. Online normal
export matches normal offline row; other non-note fields equal for all12rows.
Fresh offline reload clears notes/shortlist/key; Storage writes0 offline. Old
cache deletion, unrelated cache retained, explicit install/clear, no private
paths cached. Existing online bootstrap expected Frankfurter blocked-connect
CSP messages only; offline has no requests. No script/style CSP weakening.

Derived cache roll separate from activation:
geo-public-finder-c100d1017b7c-v1 -> geo-public-finder-f08e061a1af2-v1.
f08e061a1af2 is first12hex SHA256 of actual complete served offline response
bytes, f08e061a1af28f591b1e4b5c10377967cfbe4a0fcc6a516e346562be59c7ed10.
Test recomputes served response SHA and compares CACHE, fails if bytes change
without roll. Worker logic byte-identical except constant. Existing activate
step deletes old snapshot cache. Matters only on future explicit serving/use.
Raw offline.html/index.html/app.js/dataset/sw.js/build receipt unchanged.
Local raw provenance double rebuild inputs/outputs equal saved receipt; no raw
rebuild or receipt byte change needed. Pins/audit record this separately.

Source regressions: weather231/network230/own-key229/report228/nested/static/
offline/198d/ships226 PASS. Units offline232/offline/nested/provenance19OK1default
browserSKIP. Browser wrapper RUN_OFFLINE232_BROWSER=1 opt-in; missingChromium/
Playwright explicitSKIP. Chromium154.0.8037.57/Python3.10.12/Playwright1.63.0,
Node22.23.3, frozen1791576000000/random.25/Kolkata. No real provider/weather/
FX/AI/manualAIS/hostedHTTPS/Safari/quota/full spreadsheet-client proof.

No DB, send, mount, serving, deploy, activation or wiring. Full project remains
incomplete. Existing raw Finder source and other tables are untouched.

<!-- END-ORIGINAL-DOC -->


<a id="doc-121"></a>

### Reference: `integration/OFFLINE_CYCLE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1932,"path":"integration/OFFLINE_CYCLE_LIMITS.md","sha256":"27486fc2db38e9aea323f3b5afdfb9ba770186d783f294c5a636ea5edcc0cc80"} -->
# Offline collection cycle

`run_offline_cycle` connects supplied-candidate processing to an exact
`FakeCollectionWriter` instance. It is not a live collector or database adapter
and is not imported by the runtime. Categories, threshold, zoned clock and
synthetic failure URLs must be explicit. Reusing the same fixture writer allows
repeat-cycle duplicate tests. Separate Geo and BRICS maps stay separate.

The fixture writer uses slots, so instance method overrides are refused. The
cycle calls the class implementation directly and requires both internal maps
to be exact dictionaries containing bounded plain JSON before processing.
This is a trusted Python fixture, not a security sandbox against arbitrary
code that replaces class definitions or imported functions.

Candidates are checked as bounded plain JSON before processing. Writer batch
validation precedes fake-store changes. Processing exceptions propagate; they
are not reported as success. No transaction across projects is provided.

The limits in COLLECTION_PREPARE_LIMITS.md and FAKE_WRITER_LIMITS.md still apply:
copied processing rules may drift; URL identity is exact; field semantics are
not fully validated; nested container limits are not a total memory/CPU budget;
failures are synthetic and do not model real MongoDB errors, races or indexes.
No source-policy approval, real collection mapping, runtime wiring, scheduler,
alerts, mail, migration, live write or old-app shutdown is added by this module.

The reviewed entry point is run_offline_cycle only. Direct calls to
prepare_candidates or FakeCollectionWriter.snapshot/write have weaker type
boundaries, including subclass hooks. Keep them internal and harden them before
wiring any other caller. The cycle validates clock and synthetic failure URLs
in write(), after pure preparation; invalid values raise before fake-store
changes, but preparation can occur first. Geo extraction remains unwired.

<!-- END-ORIGINAL-DOC -->


<a id="doc-122"></a>

### Reference: `integration/PAGEWATCH_REPORT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2251,"path":"integration/PAGEWATCH_REPORT_LIMITS.md","sha256":"9fdaa5ddaed815f53b29b59af39e1d37eaa8f28c46fd740fb83e1e04c07e43d3"} -->
# Bounded supplied page-watch preview report

No source fetching/authentication, mail, marking, storage, routes or scheduler.
Function signature/return keys retained; valid small legacy HTML bytes retained
against the explicit test string by golden test (not an independently retrieved
original report). All rendered title/summary/URL escaped, no str coercion.

Exact plain dict/list/str/bool values only, depth4, dict24keys/key64chars, list1,
per-string2MBUTF8 and aggregate4MBUTF8 before semantic rendering. These bound
validation, not caller input parsing/allocation. Closed result/row keys accept
actual compare output and small legacy report input; unknown keys/non-dict rows
reject. Optional snapshot validates canonical integrity, but NOT row association,
opaque id binding, URL source ownership or actual observation truth. No metadata
or hash authenticates report contents. ids are opaque/unverified, never deletion
or sent-state authority. Baseline/unchanged must have no rows; no report sent.

Required id nonempty128chars, title200(default Page changed), summary12100chars,
URL canonical page-watch2048chars; The character caps bound UTF8 allocation; no distinct4x-character safety
claim. Unicode Cc/Cf/Zl/Zp controls and bidi formats rejected except
summary CR/LF/TAB. Other optional row fields strings256chars (summary_html80000)
or emailed exactbool. Unused fields never rendered, but malformed values reject.
No mutation or new fixed-source binding. Page-watch producer still emits fixed
Nilgiried labels for arbitrary accepted URL; caller must bind reviewed source.
No ID relation/comparison provenance proof follows from escaped HTML.

30 configured tests PASS across report/snapshot/parser,6new report tests:
compare integration, legacy golden bytes, script-title/summary escaping,
customhooks/bool/int no-coercion, malformed/bounds/closedrows/flags, no mutation.
Standalone bundle reproduces these tests. No live integration or UI claim.

Forged changed results can pass syntactic checks; IDs/URL never authorize
runtime wiring, disclosure, send or marking. Must bind provenance separately.
Snapshot diff falls back to omitted message for forbidden controls, not silent
text normalization; raw snapshot text/hash remain unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-123"></a>

### Reference: `integration/PAGE_WATCH_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":5424,"path":"integration/PAGE_WATCH_LIMITS.md","sha256":"efd7f956afaaf6eecb9e6a09377c0eb8e9d6dbd7829970db97795909c00c08ee"} -->
# Supplied page-watch snapshot contract

Pure supplied HTML/snapshot comparison. No fetch, source allowlist/authorization,
policy approval, store, mail, timer, route or source activation. Nilgiried fixed
report labels are NOT derived from URL: accepted arbitrary URLs do not establish
that source or ownership. Caller must bind source identity before sharing/use.
Observation timestamp is self-claimed, not verified capture/time truth. Hash is
integrity, not authenticity or proof a page was actually fetched.

Signatures retained. validate_snapshot now returns fresh canonical plain dict,
previously returned None. Closed keys url/observed_at/text/sha256/method, exact
plain str/dict types; old baseline shapes from snapshot re-canonicalize. Unknown
keys/missing method reject. No input mutation, silent NFC or text re-normalization.
Extraction still normalizes visible whitespace; any changed extraction rules
would appear as changed text, not semantic event verification.

URL <=2048chars, HTTP(S), scheme/host lowercase, fragment/defaultport removed,
empty path /, query unchanged. Reject userinfo, bad port, controls/whitespace,
backslash, lone surrogates and non-ASCII host. Limited equivalence only: no
percent/path/query/IDNA semantic normalization or source authorization.
Timestamp plainstr<=64, aware ISO parsed, original+UTC years1970..2100, offset
validated by datetime parser. Canonical UTC fixed microseconds, idempotent.
Compare canonical UTC strings; older instant rejects, equal stamp samehash
unchanged, equal stamp differenthash conflict. Older real observation represented
by later local-clock string now rejects. No future-clock truth check exists.

Original HTML2MB cap superseded by the parser input tightening below. Text <=2MB UTF8, min30chars, <=20000lines,
each <=100000chars checked before hash/diff. Surrogates reject cleanly.
Exact lowercase64hex SHA256 after caps. Diff allowed only when BOTH sides
<=1000lines and <=100000UTF8bytes, else changed with fixed diff-omitted summary.
This bounds difflib input, not a formal worst-case CPU deadline. Identical large
hashes return unchanged without diff. Existing small diff format retained by
golden byte-string test;80line/12000char display truncation remains. Added
result diff_omitted flag; summary labels observed change, not event verification.
No report renderer change, no persisted baseline rewrite/migration.

Earlier contract run20tests PASS (superseded by24-test parser bundle) covers old regression, offset chronology/equal
conflict, URL/time canonicalization/idempotence, shape/hash/caps, one-character
and repetitive lines fallback, unchanged large input, fresh copies, input
mutation and golden small diff. Report tests retain escaping/separate no-send
contract. Existing app is not importing a source watcher into runtime here.

HTML parser CPU is not bounded by the new line/diff caps: crafted <=2MB HTML
was observed by review to take about13.8seconds (predates this fix). This prior observation predates the new delimiter/event caps below; no
interrupting wall-clock limit implemented. This is not safe untrusted
live source ingestion without further parser work. Timestamp accepted ISO forms
depend on Python version (3.11+ is more lenient); configured tests use3.10.12.
Year bounds checked on original local year AND resulting UTC year. Naive/date-
only timestamps or missing-method old baselines now reject. An invalid retained
baseline needs an explicit reviewed re-baseline, not automatic silent repair.
Report title/source remain fixed Nilgiried strings for ANY accepted URL.

## Parser input tightening (supersedes2MB HTML acceptance)

HTML now <=128KiB UTF8 AND chars, raw '<' count<=4000, every delimiter span
between raw '<'/'>' <=4096chars before HTMLParser. This conservative preflight
rejects giant tags/attributes/comments/text runs, not a new tokenizer or exact
HTML token semantics. Nested delimiters can split a lexical token; total input
cap remains the bound. Parsed start/end/data/comment/decl/PI/unknown-decl event
budget8000 and existing depth500. Strict rejection keeps caller's previous
baseline unchanged. Smaller-page compatibility break explicit: formerly accepted
large legitimate pages can now reject. No fallback to partial/empty baseline.

24 configured tests PASS including direct event budget, UTF8/size/delimiter/
span limits, nested-unclosed '<a>'x500+'</b>'x3000, giantattribute/comment,
nearcapaccepted example and ordinary text golden. Six crafted measurements in
subprocess, timeout2s for entire harness (not runtime): observed worst~0.095s
nested-unclosed and~0.054s nested-within. Platform/version-specific observations,
not formal CPU deadline or hostile-HTML safety guarantee. Actual HTMLParser
can spend work before callback; malformed/nested cases may still be expensive.
No runtime subprocess or timeout is added, no live source activation.

Compatibility examples: inline script/JSON-LD longer than4096chars, plain
<p> text longer than4096chars, and pages over roughly3000tags may reject
(delimiter/events count structure, not a precise tag-count guarantee). These
were formerly accepted even if hidden script text was ignored. Timing numbers
above were measured on Python3.10.12 only; other versions/platforms unverified.
Existing broad-except maps parser exceptions to fixed malformed error, losing
specific diagnostics intentionally; do not treat that as a detailed fault code.

<!-- END-ORIGINAL-DOC -->


<a id="doc-124"></a>

### Reference: `integration/POST-JSON207.md`

<!-- ORIGINAL-DOC {"bytes":4754,"path":"integration/POST-JSON207.md","sha256":"effd35bc5ca6cf0fbd3806c97942d390b010e55733f99c14b1d22ea618029137"} -->
# 207: bounded read-context POST bodies

Only /api/related-news and /api/finder-context change. Auth then Origin guards
remain first (403), parser next, reader only after valid body. No v1 POST aliases,
UI/auth/CSRF/CORS changes, app-wide MAX_CONTENT_LENGTH or other route changes.
This closes188's named two-route gap, not whole-app validation.

application/json only, optional single charset=utf-8 (case-insensitive), no other
or duplicate parameters. application/*+json refused415. Raw body cap16384bytes;
JSON escapes count against it. Observable environ CONTENT_LENGTH must be canonical
positive ASCII decimal (no leading zeros/sign/whitespace/comma/duplicate values).
Missing/empty length411, invalid/zero400, declared overcap413 before read.
HTTP_TRANSFER_ENCODING present400. Short/disconnected body400. All errors have
fixed "Invalid read context" JSON, no supplied values/body echo or logging.
StrictUTF8/noBOM; object_pairs_hook refuses nested and top-level duplicate keys,
including identical values. parse_constant refuses NaN/Infinity. Exactobject,
closedkeys/noqueryparams. Decode/JSONValueError/RecursionError400. Oversize nested
arrays/hugeinteger413 before decode/parse. Under-cap recursion/5000digit integer
refused400 in tested Python3.10's integer-string-limit environment.

Nonterminated input: never read beyond declaredlength or bypass request.stream.
Duplicate Content-Length headers and bytes beyond declaredlength are unobservable
at Flask on a nonterminated server. Deployment server unreviewed; HTTP framing
relies on that server/proxy. NO request-smuggling protection claim. Explicit
wsgi.input_terminated=True permits bounded cap+1 read and excess-body detection;
actual bytes must equal declaredlength. These are Werkzeugtestclient/hand-built
environ forms with/without terminated input, not end-to-endHTTPframing proof.

Relatedoptionalkeys: code/system/edition/country/product_terms. Exactstrings,
codeempty orASCII1..12digits (leadingzeroskept),system/edition32,country100chars.
Terms exactlist<=20/exactstring<=200chars. Emptyobject/code/terms keep priornoop
semantics. Allstrings refuseC0/DEL/C1/lonesurrogates, exceptTAB/LF/CR allowed
within terms only;NBSPallowed asordinaryUnicode. No trim/normalization. Matcher
unchanged, including its narrower6..12digit explicit-code evidence behavior.
Finderexactrequiredprojectgeo|brics and lowerhex64article_key; no unknownfields.

## Browser and source bounds

206 index.html503-525 SYS.tag values22tags,max3chars,no whitespacepadding;
sysTagHtml1226 directly inserts tagtext,workspace.js111 reads untrimmedtextContent.
SYS_COUNTRY workspace.js6 longestlabel UnitedArabEmirates20characters. Caps32/100
cover currentlabels, not a promised futurecatalog. workspace.js110 stripscode
nondigits and only guards!code, so all ASCII lengths1..12 accepted here.

Actual data.d6d1b417562b.js340232rows decoded for this audit;SHA256
`d6d1b417562bad99e7b434605d63966772749d573375fb10d74ee52cb6bb82f6`.
Digits-only code lengths per systemindex snapshot:
0:0,2,4,6;1:2,4,5,6,7,8;2:4,6,8,10;3:2,4,6,8,10,12;
4:2,4,6,10;5:2,4,6,7,8,9,10;6:2,4,6,8,10;7:2,4,6,9;
8:4,5,6,7,8,10;9:2,4,5,6,7,8;10:11;11:10;12:2,4,5,6,8;
13:2,4,6,8;14:2,4,6,8,10;15:2,4,6,8,10;16:0,2,4,6,8;
17:0,2,4,6,8;18:0,2,4,6,10;19:2,4,6;20:2,4,6,8;21:2,4,6,8.
Emptycodedrows failbrowser!code guard. Laterindexcode>12 would be refused until
boundreview; this is a snapshot not a dynamicindexvalidator.

Related-news requests from code pages whose description exceeds200characters
already fail today; this unit keeps that behaviour and does not fix it.
Groundedindexmaxdescription2850chars,376rows containTAB/LF/CR,currentcap200.
Frontendexcerpt/split/truncatepolicy or measuredservercost/timebudget remains
queued separately.20x200ASCII fits16KiB;4000fourbytecharacters plus usualJSON
payload roughly16KB fits, but escaped representations can exceed and413.
No promise everymaximal-field combination fits the aggregatecap; no truncation.

Tests compare valid{},code-only,country-only against oldhandler's exactfixture
loop/output; validFinder/currentbrowser-shape preserved. Test multiline/NBSP,
200passes/201fails, closedfields/types/controlbounds, media/charset, duplicate/
nonfinite/UTF8/BOM, query, depth/integer/size, environlength/TE/terminated forms,
auth/Origin403 before read/parser and no reader on refusal.49focused regressions
run; no UI/pixelchange, DBwrite/mail/network/collector/liveeffect.201c held.

Behavior changes: fixed error text is now "Invalid read context"; wrong media
returns415 (previously400). Null fields, nonstring country and unknownkeys now
return400 where oldhandler accepted some. Declaredovercap413 precedes parsing.
These are validation changes, not currentbrowserpayload regressions.

<!-- END-ORIGINAL-DOC -->


<a id="doc-125"></a>

### Reference: `integration/PREVIEW_LAUNCHER_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4076,"path":"integration/PREVIEW_LAUNCHER_LIMITS.md","sha256":"77bb03e830afd66324ebe479f7c0354c0af4cdd99c8e60a344424e332a438870"} -->
# Geo-only preview launcher wiring boundary

private_router now calls build_preview with a plain captured environment. PREVIEW_GEO_ONLY_ENABLED accepts exactly true/false, default false. False retains original isolated legacy composition for rollback. True selects reviewed compose_geo_only with Geo-only article identity and no BRICS client, database, migration, indices or writes. This flag does not enable anything else.

Geo-only read-off makes no client. With private access enabled and supplied valid session/hash/origin settings, it serves an empty bounded-news private preview plus the preserved Finder. No production credential or database availability claim. private_router now supplies a lazy narrow Geo read factory only for explicit
Geo-only/read-on flags. Direct build_preview still requires an injected factory.
Reads remain off by default and all private/mapping/URI gates run before client. Read gates and mapping restrictions remain those in GEO_ONLY_LIMITS.md. A production factory step needs separate review of read-only credential, exact mapping, timeouts and current service before activation.

Deployment boundary: code backup is not Render deployment or setting change. Do not change Render command/environment/service, stop old collectors, activate NEWS_READ_ENABLED/Finder network/mail/accounts, or select production launcher branch under this wiring work. Before a private Render preview, explicitly review intended command (single worker integration.private_router:app), canonical HTTPS origin/trusted proxy, enabled flags, secrets delivery, read-off behavior and rollback. Keep original runtime.compose unchanged; rollback switches Geo-only flag false, but legacy read settings must still be validated, never auto-enabled.

Do not create defaults from old URI labels. Geo-only requires GEO_DATABASE; a conflicting GEO_MONGODB_DB_NAME is refused instead of ignored. Neither .env.example nor a verified flag proves live ownership/permission. Exact source mapping, preview deployment approval and current Render configuration remain outside offline tests. Source test fixtures use fake factories only; no client/package constructed on read-off launcher import.

Render preview plan (requires separate approval to execute): select PREVIEW_GEO_ONLY_ENABLED=true, NEWS_READ_ENABLED=false, FINDER_NETWORK_PREVIEW_ENABLED=false and MERGED_MAIL_ENABLED=false; no BRICS credential required or loaded in that branch. Legacy false rollback with NEWS_READ_ENABLED=true DOES create both Geo and BRICS client handles and can read the BRICS DB. It is not an acceptable Geo-only preview setting; rollback must keep reads off unless separately reviewed. This document is preparation, not permission to edit Render.

GEO_DATABASE defaults geo_intel. Legacy .env.example GEO_MONGODB_DB_NAME is ignored for mapping except conflict refusal; BRICS labels/URIs ignored in Geo-only branch. Actual Geo-only private_router now has the lazy reviewed factory; invalid
private/mapping/URI settings still fail closed at startup. Do not retry by switching to legacy mode to bypass that blocker.

Boolean policy: the new launcher selector is exact true/false; selected Geo-only branch validates all listed access/read/mapping/proxy/Finder booleans exact too, before calling older helpers. Direct older compose/helper entry points still use case-insensitive parsing in places; legacy rollback semantics are preserved, not silently changed. Operators use lowercase values throughout.

Double create_preview_from_env during injected read composition is intentional pre-client access validation then reader-bound app creation. Tests verify two distinct Flask objects, no duplicate login route/global registration and only final app returned; first app discarded. Neither creation starts background work or connects a client. Finder network helper only returns flags/strings. Finder index loader reads/hash-validates/decompresses local bounded files, not remote sources; fake-factory tests trap socket/Mongo/HTTP calls while loading. No import-time network/Mongo action is introduced.

<!-- END-ORIGINAL-DOC -->


<a id="doc-126"></a>

### Reference: `integration/PRIVATE_NEWS_FIELDS_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1682,"path":"integration/PRIVATE_NEWS_FIELDS_LIMITS.md","sha256":"abf477fd8b12df7b4c128e367a0c4e281272cbe4b706a32be0baa2f62a0578cd"} -->
# Private news field boundaries

Private Telegram fallback URLs/message IDs are not exposed by news-facing APIs or fetched by the read-only store projection. Normalized internal supplied views retain backup_url for existing internal behavior, but public-row and critical-story boundaries remove it. Country-page projection and CSV already exclude it. Existing legacy source records and report/mail engines are untouched. No live reads/writes or reported disclosure occurred in this offline preview.

Atlas-shape fixture supports empty country, zoned ISO string published/created_at, query-bearing original URLs, score/risk and emailed flag without exposing sent state or IDs. Screenshot counts are capture-time evidence, not runtime assertions. Geo mapping geo_intel/articles is identified; events/admin/local remain outside this read contract. Distinct BRICS collection/schema/ownership and activation remain unresolved.

Shared PUBLIC_NEWS_FIELDS exact allowlist now applies to every normalized news output path, critical/country views, sorted JSON/CSV rows, story profiles, relevance input, chart and dashboard-signal inputs. Only canonical field names pass; case-fold collisions omit ambiguous canonical fields rather than trusting an alternate-case key. No unknown/private key is renamed into an approved key. UI reads the canonical url field only; original_url and backup_url are not frontend dependencies and never article-key/link fallback. Article identity remains project + valid source URL, with no Telegram fallback. Content inside allowed title/summary/source is not a secret-detection boundary; preserve source text, don't claim automatic sensitive-content redaction.

<!-- END-ORIGINAL-DOC -->


<a id="doc-127"></a>

### Reference: `integration/READINESS233.md`

<!-- ORIGINAL-DOC {"bytes":10032,"path":"integration/READINESS233.md","sha256":"9c4e466289560800a811385ba876b7eaa074a7ab7ed5f2590e06c3db7b67d9c1"} -->
# Repo-only readiness ledger (233)

Checkpoint: c7b231d636922958f6c81a59a0a4aa6ec74d419f.
This is source and local test evidence, not a deployed release or live
verification. No automatic live switch follows from this ledger. Open gates
below are separate from test results; this document selects no live subset.

## Landed Finder changes and evidence

The builder and independent reviewer ran the named local probes. Reviewer
verdicts and exact runs are retained in each unit's review receipt/handoff;
committed docs describe the evidence, not proof of a live runtime. The tree
hashes below are verified from git, not inferred from a report.

### 228: report popup repair

Commit dfec65891ac509405c75c3094b7a0fb836190e9f.
Tree 1a03815b400442e8a231f9ca73a631f8fc915ce8.
Sources: src/app.js (setupTemplateReportWindow/buildTemplateReport), rebuilt
index.html/offline.html, integration/REPORT228.md; probe
tests/browser_report228.py and tests/report228_test.mjs.

Changed popup inline handlers/scripts to opener-side setup under inherited
CSP; pagination and print binding work in the local simulated report fixture.
Builder and reviewer observed intercepted print calls and rendered PDF pixels.
Not proof of a native OS print dialog, arbitrary report content, real AI output,
all browsers or hosted deployment. No real runtime observation recorded here.

### 229: own-key browser regression

Commit c0db3e69f2e33a3c3652eeb215bdcf18e1b6f8c4.
Tree 6bf46d2501cb7324506bfd60a98a44adbc260e4e.
Paths: tests/browser_feature_finder.py, tests/test_finder_browser229.py,
integration/FINDER-BROWSER229.md.

Tests-only: replaced stale shared-proxy fixture with current no-key prompt,
local mocked Mistral success and 429 fallback. Builder and reviewer ran the
probe; simulated text remains literal, print counter 1, fixture PDF 26 pages.
No real provider availability, AI quality or three-provider failover proof.
No production app change and no real runtime observation recorded here.

### 230: network browser regression

Commit 88604076805e3b658773ad4a4b091b5ca8436d7b.
Tree 2eebe6fe03b54c1e4eb8e1697d0d27a07410609e.
Paths: tests/browser_finder_network.py, tests/test_finder_network230.py,
integration/FINDER-NETWORK230.md.

Tests-only: exact local mocks for forecast/marine, FX and own-key plain words;
empty AIS proxy means unavailable without fetch. Builder and reviewer ran six
simulated cases and failures; zero real outbound successes. No real weather,
FX accuracy, AI, failover or manual AIS proof. Current network preview remains
default-off (integration/news_api.py create_app, integration/finder_network.py).
No real runtime observation recorded here. Mobile clipping found in 230 was
subsequently fixed by 231, not by this test change.

### 231: weather table phone fit

Commit 7333a8ab37027fb2d265f19af82f643ed739bd93.
Tree 50f95116564d8d6761b68c516e4b2c624787dcb0.
Paths: src/style.css, integration/WEATHER231.md,
tests/browser_weather231.py and tests/test_weather231.py.

Scoped CSS fits only the successful weather table. Builder and reviewer saw
full labels/values/date/warning at 320/390/1100 light/dark with local simulated
weather, long-number stress, keyboard/select and503 states. Global 680px table
rule untouched; app, dataset and sw.js unchanged. Not real weather correctness,
all-browser proof or live availability. No real runtime observation recorded
here. Derived raw snapshots/pins changed, not a live deployment.

### 232: public offline CSV and scroll

Commit c7b231d636922958f6c81a59a0a4aa6ec74d419f.
Tree 427e0bc06b58a21fe932cdd0eb4b379935e4bd4f.
Paths: integration/finder_offline.py, integration/ui/finder-offline-sw.js,
integration/OFFLINE232.md, tests/browser_offline232.py, tests/test_offline232.py.

Offline served copy reuses existing online CSV safety and shortlist scroll
transforms before CSP hashing. Builder and reviewer downloaded CSV from the
actual cached-local page, with synthetic session notes only. Danger cells get
an apostrophe; NUL removed; quotes/CR/LF/astral Unicode survive. Six columns,
order, normal values and filename retained; normal row matches online export.
Invalid surrogate already became U+FFFD through the original Blob, so no
before/after downloaded-byte change is claimed for that row.

Builder and reviewer viewed 320 light/dark and end-scroll: Tab reaches the
named region, ArrowRight scrolls, End shows Remove fully. Builder also viewed
390/1100 light/dark; 390 fixture fits. BEFORE outer page already fit, so no
whole-page-widening claim. Raw animated keyboardScroll numbers vary (1 versus 2);
semantic success, not the raw pixel number, was stable in two runs. Session
notes/shortlist/keys clear on fresh page; offline storage writes 0. Not hosted
HTTPS/Safari/quota/spreadsheet-client proof. No real runtime observation here.

## Derived cache history, not activation

228:2491a5a38160 -> 4f48ae1b3cd7 (REPORT228.md and git dfec6589).
231:4f48ae1b3cd7 -> c100d1017b7c (WEATHER231.md and git 7333a8ab).
232:c100d1017b7c -> f08e061a1af2 (OFFLINE232.md, git c7b231d6).
232 ID is first 12 hex SHA256 of the complete served offline response, tested
by test_offline232.py. Worker logic unchanged except CACHE; existing activate
deletes old snapshot caches. This matters only on future explicit serving/use.
Raw index/offline/app/dataset/sw.js unchanged in 232. No activation recorded.

## Last-known repository gates

At c7b231d6, builder retained receipt: root 2175 =650+200+125+60+65+200+250+625,
8 skips and 1 expected failure; collectors 285, checks 10, world 26; closure 584
with 7 skips; focused 48 with 6 skips; 97 JS syntax checks including cjs. Logs are
builder runs; reviewer checked receipt sums/hashes and reran selected units,
including explicit offline232 browser wrapper 3 OK. Reviewer did not rerun the
whole root suite. Required Finder browser regressions ran on the audited
identical sources. These numbers are not evidence for a later runtime merge.
The retained 232 receipt and root1..root8/collectors/checks/world/closure/focused/
node-all logs support these counts. No live readiness follows from them.

## Remaining gates and owners

Runtime status below is runtime's own report relayed at 06:45 IST Oct10, not an
independent builder audit of a target. Runtime has no active executable bundle,
patch/image/install or target acceptance receipt. Last direct current-main
source audit at 22:03 Oct9 found runtime_build absent; later source receipts do
not establish that a bundle appeared. Recheck source before execution.

- Runtime owns 27: complete pinned bootstrap, OS/wheel/native/app artifacts,
  exact runtime_build bytes/manifest/anchor, fresh install/import proof and
  selected-runtime environment/start parity are missing.
- Runtime owns 28: supported interpreter matrix and actual target validator,
  timezone, JSON-depth, bwrap/process identity/deadline/kill-reap acceptance,
  including combined 512 MB boundary. Fixtures and 768 MB sampled monitoring
  are not target acceptance.
- Runtime owns 29: manual build scaffold exists, but required reviewed input
  package, selected current-source closure/build receipt and target identity
  are missing. No build dispatch reported.27-29 are open, not a current build.
- Runtime owns 209 target vectors: ship integration/html_text209.py and pass
  its golden vectors on the actual selected interpreter. Only 3.10.12 proven
  (tests/test_html209.py and integration/html_text209.py).
- Cross-component held 201c: later source selection plus runtime validation
  need accepted native production composition/write selection and real Atlas
  roles/schemas/admission/transactions/durability measurement, exclusive-writer
  and DDL evidence. Current source is not permission to execute writes
  (tests/test_native201guard.py, native201 modules).
- Owner owns DB URL/Render environment stage. Owner enters the connection
  setting at wiring stage. Agent DB presence checks/reads/create are not
  permitted by the latest instruction. No check performed in this ledger.
- Cross-component held 217 mount: later source unit must provide exact
  mount/selection closure, runtime must validate the target. Source-only
  Apps Script wrappers are not mounting (integration/MAIL-SURFACE217.md).
- Sender222 consumer is open: later source unit must supply actual reviewed
  runtime caller consumption (tests/test_sender_scope222.py). Runtime then
  validates it; source helper existence is not a working send path.
- Owner owns final recipients/words review before mail effects. Apps Script
  is the selected rail; sends and SMTP fallback remain held. No recipient,
  sending words or user data is included here (feature_mail_mount docs).
- Hosted accounts, trusted proxy and configuration require later source
  closure and runtime selected-target validation. Closed memory account
  fixtures are not shared-store/login/proxy readiness (integration/accounts,
  integration/FEATURE_STATUS.md accounts limits).
- Real provider/CORS availability, AI disclosure permission, polling/collector
  activation and hosted PWA remain open. Runtime/later source units must
  establish exact configured routes and capabilities; owner must approve
  disclosures and activation. Local simulated fixtures above do not prove
  live availability (FINDER_PARITY_PLAN.md and FINDER_OFFLINE_LIMITS.md).
- Owner still chooses actual compute target and intended live subset after
  the readiness package is known. Runtime must establish selected release/
  deployed identity, current merged smoke, exact flags, one scheduler owner,
  rollback/backup proof and no duplicate writers/sends. Final specific owner
  choice plus per-step confirmation remains necessary. No automatic 09:00
  switch or blanket go/stop recommendation is made here.

Full project parity is not established. Static Finder function coverage remains
partial (tests/browser_finder_static.py covers code details/favourites/CSV,
not the whole feature inventory). The two current parity-plan rows supersede
popup/offline caveats only; other open rows are retained.

<!-- END-ORIGINAL-DOC -->


<a id="doc-128"></a>

### Reference: `integration/RECIPIENT-SCOPE220.md`

<!-- ORIGINAL-DOC {"bytes":2352,"path":"integration/RECIPIENT-SCOPE220.md","sha256":"65df32e0be16b346ba89165f620469eefd0cc3379f5b1bc651c4d8387247bc9d"} -->
# 220: supplied recipient config fingerprint

DefaultOFF static flags; explicitTrue validates supplied config only. No address
is searched, selected, inferred, autofilled, contacted or retained. Owner has not
provided or approved a recipient list. send_allowed/ready/owner_approvalFalse.

Exactlist1..20 exactASCIIstr addresses<=254,213legacyfullmatchregex. May refuse
validRFCaddresses; refusal is not a claim an address is invalid. Acceptance is not
proof of validity or deliverability (legacy regex accepts a@b..com). No trim, display
name/comment/quotedlocalpart/comma-string/Unicode/space/control support. Duplicate
case-insensitive addresses REFUSE, never silently dedupe. Input remains unchanged.

Protocol lowercases WHOLE addresses including local part, then sorts. Real
mailboxes may treat localpart as case-sensitive; owner must accept this policy
before first use. Case variants share fingerprint; permutation doesn't matter.
No aliases/Gmaildots/plustags/DNS/ownership or mailbox-equivalence rule is inferred.

Hash is canonical sorted-key/separator/ASCII JSON SHA256 of closed
{schema:email_recipient_set220_v1,kind:email,recipients:sortedloweraddresses}.
This length-safe schema value supplies domain separation, no joined delimiter.
Plain64hex is accepted by219/212 tests only. Output contains fingerprint/policy/
count/flags only, no actual address/name/sender/bridgechannel. Errors fixed with no
address/cause/context. Hash is NOTprivacy/anonymity; guesslists can test addresses.
Do not log fingerprints together with addresses.

Not bridge identity: bridge hashes sender+recipients,220onlyrecipients.220 does
not compute/return bridge MAIL_V1_CHANNEL. Sender change is invisible to220and
212logicalchannel unless a later unit binds sender: NAMED BLOCKER for ledger wiring.
Recipient change makes a new fingerprint/channel; exclusions/history do not carry
over automatically. Owner must decide changes and approve actual recipients/words.

No219212constructor/ledger/store/SMTP/bridge/production import or config/property
write. No DBURL/read/check/write/creation/files/network/send/activation/cutover.
Existingbridge216/217heldsurface/219bytes unchanged. AppsScriptselected/
SMTPfallbackheld/201cwriteheld. History/exclusion/marking/reconciliation/mount,
durablebody/recipientpolicy/words/liveworkflow remainopen. This is data only.

<!-- END-ORIGINAL-DOC -->


<a id="doc-129"></a>

### Reference: `integration/REPLAY199A.md`

<!-- ORIGINAL-DOC {"bytes":6107,"path":"integration/REPLAY199A.md","sha256":"0c38579397f8e746ecb7bee11397f029732fd3274ab7d57154ffcb049aeda675"} -->
# 199a unselected archive transaction core

New collector schema2 and broker schema3 only, no migration. Existing source factories, collectors, auth/broker service, schemas and callers stay unchanged. Runtime capacity is NOT released: new submit/claim/status adapters (199b) must use the same snapshot-transaction archive-aware view before reserving identity, then a separately reviewed composition must wire the pair. This core alone is not a 64-cap solution or cadence-ready.

Fixed source collections and dedicated insert-only collector_replay199/finder_replay199 archives in geo_intel. Genesis is preprovisioned immutable batch:0, no core initialization. New source carries archive_epoch, archived_count and chain_head, retaining source counters, windows, fences, active ticket and fingerprint. Every archive record contains full original terminal job/receipt, original source revision, epoch, exact derived key/nonce hash and full raw collector typed checkpoint when present. Missing checkpoint only for failed-before-write; completed requires full validated checkpoint. V1/v2 checkpoint encoding and hashes preserved, no invented coverage. Broker receipts are still hash-only metadata, not answers, raw nonce, request text or UID.

Each epoch's immutable manifest has exact ordered record identity/hash references, previous head and a domain-separated family/schema context through fields. Source chain_head binds committed final manifest. Before declaring an identity absent, complete bounded chain and every referenced record are validated, including key/fence uniqueness, cross-current collisions, counter/head linkage and checkpoint hash. Missing/corrupt archive evidence fails closed. No lone empty find authorizes a new request. Broker lookup requires exact body and principal-scoped identity hashes, mismatch refuses status disclosure. No archive enumeration HTTP route is exposed.

## Atomic transaction, not handoff heuristics

Explicit injected NoRetryTransactionProvider (synthetic test driver only) with snapshot reads, primary preference, majority+journal write concern, max commit 5s, 20s workload deadline. Exactly one transaction and one commit call; no with_transaction retry helper, callback retry or commit retry. Rollover validates source revision and no-active; reads oldest terminal prefix, inserts complete immutable records plus manifest, reads each full document back, CAS-replaces exact schema/revision/epoch/head source, verifies source readback, then commits. No article/checkpoint deletion, quota refund/window reset/fence reset/held-ticket settlement. A missing ACK aborts before commit if possible; any mutation uncertainty latches this core instance and further writes are denied. Commit acknowledgement loss does not abort or retry the commit. Ending a session is cleanup, not proof of rollback.

The exact proposed operation metadata is retained once prepared (family, epoch, source revisions, old/new head, selected IDs). read-only reconcile validates the whole chain plus exact operation and classifies committed archive-only, not-visible-in-this-snapshot (NOT permission to retry), or unknown. It never clears holds, retries, settles a transport outcome, releases permission, or marks capacity/cadence ready. A newly constructed core is not a way around owner review of an uncertain prior operation; caller must preserve uncertainty/operation evidence across processes before runtime use. Real Mongo transaction behavior and unknown-commit handling must be proven separately before activation.

## Locked limits and remaining gates

Max1024epochs, max64 terminal records per batch, 8MiB BSON/canonical workload and rollout batch cap, max4096 completeness records across all epochs. Oldest full-record prefix fitting cap is archived; no record or checkpoint truncation. An overlarge record or cumulative archive workload holds even below epoch/record count. Limits are bounded safety contracts, not unlimited storage or permanent throughput. Later measured indexed-proof/scaling format is separately reviewed. A full collector record may be near its own 2MiB input budget; complete history may not fit a batch, hence prefix-only. Archive insert-only credentials, no update/delete/TTL/drop privileges; source update scope remains separate.

Read-only preflight checks exact observed family role/mappings, replica-set session/wire prerequisites, majority+journal handles, existing unfiltered _id indexes/no TTL, new source schema and immutable genesis. It does NOT prove transaction execution, whole-chain completeness, immutable external backups, runtime memory/capacity, owner authority, active process termination, or correct live deployment. No provisioning or transaction in preflight. Live owner write grants, private archive retention/audience, role/schema/genesis provisioning, real transaction/host evidence and explicit OK live remain separate. Test double proves source algorithm cuts/interleavings only; no live Atlas/provider calls.

## Native provider unavailable

Grounded from installed PyMongo4.18.2 source: ClientSession.commit_transaction invokes _finish_transaction_with_retry, which calls _retry_internal(retryable=True), an internal retry even when the application calls commit once. Avoiding with_transaction alone does not meet this unit's no-auto-commit-retry contract. No contract relaxation or raw-command workaround is included. Exact explicitly injected NoRetryTransactionProvider is required by enabled core; no implicit native start_session/fallback. Holder supports synthetic session factory only and refuses PyMongo clients, test driver lives in tests. The holder validates source shape, not external driver correctness. A malicious custom non-PyMongo wrapper is not an audited native adapter and cannot be used as a runtime grant. This source proves core semantics only with the audited transaction test double. Native no-retry provider must be separately implemented, reviewed and measured before any live archive transaction or capacity use. Live 64-cap solution remains blocked until that plus 199b and composition are delivered.

<!-- END-ORIGINAL-DOC -->


<a id="doc-130"></a>

### Reference: `integration/REPLAY199B.md`

<!-- ORIGINAL-DOC {"bytes":3303,"path":"integration/REPLAY199B.md","sha256":"6f4aee82936526595c53e57b6c1c15eb681896a718e8db0d5c68eaf1f2bb7e05"} -->
# 199b unselected archive-aware adapters

New exact ArchivedCollectorLedger and ArchivedProxyReceiptBudget only. Old DurableLedger/ProxyReceiptBudget types, source schemas, runtime factories, orchestrator, transport, server and production entry are unchanged and still do not select these adapters. Enabled source core still requires synthetic-only NoRetryTransactionProvider; native no-retry provider remains unavailable. No runtime capacity/cadence claim, live client, migration, provisioning or new route.

Submit/claim validate complete archive chain in the SAME snapshot transaction as nonce check and exact source CAS/readback. Old collector derived keys and broker nonce hashes remain authoritative after rollover. Collector replays return retained terminal job; broker returns original receipt status only, body/principal-scoped identity mismatch denies without disclosure. Archived lookup is also used for status and transitions; archived/terminal ticket cannot restart writes. No automatic rollover, replay fetch/transport, counters refund, window reset outside normal new-claim timing, archived identity drop, active release or expiry takeover. Broker single global active and60proxycalls/600s remain; collector hot64history and broker hot64receipts still hold before explicit core rollover. A synthetic rollover followed by adapters proves bounded source reuse without erasing replay identity, not live Mongo behavior.

New claim returns only after transaction commit ACK. Any lost commit/CAS ACK raises and latches this core instance; no returned ticket means caller must NOT fetch or send. It may have committed reserved state, which remains held. Recreated cores are not permission to retry an unknown operation. Durable uncertainty and process restart behavior require a later native-provider/composition review and owner scope. Read-only status does not settle or clear. Exact original ticket transitions match current active row, clock monotonicity/deadline/phase required; expired complete becomes unknown-held, no refund. Source readbacks and chain chronology/revision/key/fence checks prevent unseen old nonce or stale source state from entering a mutation.

Collector transitions preserve known bounded count schema, heartbeat semantics and terminal archival rules. Broker reserve/start/finish/hold preserve v2 shape and no takeover/late settlement. All mutations use exact new schema/revision/epoch/head CAS with one explicit test-provider transaction/commit, no automatic retries. No arbitrary native wrapper is treated as audited provider. New adapters are intentionally NOT accepted by the old exact-type runtime constructors: separately reviewed composition is still required. Privacy routing of internal status remains server-owned; no HTTP archive enumeration is added. Unknown archive reads/corruption/max1024epochs/max4096records/8MiB completeness orbatch limits fail closed before nonce mutation.

Tests use synthetic explicit transaction backend only. Real session isolation/interleaving/conflict outcomes, host memory/time, no-retry native transport, scoped archive roles/genesis/new-source migration and replay-aware runtime pairing remain live activation gates. Source tests are not owner authority. No runtime adapter is available to claim the64-cap is solved live.

<!-- END-ORIGINAL-DOC -->


<a id="doc-131"></a>

### Reference: `integration/REPLAY199CA.md`

<!-- ORIGINAL-DOC {"bytes":2884,"path":"integration/REPLAY199CA.md","sha256":"461285a9a209b4fe47bae5c271938e71a599ab2307ac95092ad18e05c782d32f"} -->
# 199c-a synthetic-only archive-aware broker server

Default OFF unselected create_archive_broker_server; OFF returns public callable unchanged. Old broker server/transport factories and production_entry/public_live107/collector197_job bytes are unchanged. Enabled requires exact ArchivedProxyReceiptBudget with synthetic-only ArchiveCore provider, exact enabled FixedProxyTransport, exact account service/single-worker evidence and fixed direct HTTPS origin. No env/client/provider construction or live mount; native no-retry provider unavailable. No runtime capacity-ready claim or real network/Atlas tests.

New proxy_request_archive explicitly consumes {state,receipt}; current old v2 claim also has this shape, old v1 reserve ticket is not interchangeable. Request plan fixed HTTPS/EMPTY AI catalog and parent/child transport contract unchanged. Derived live-session UID principal hash is bound internally before any broker operation. Strict POST ships nonce+port, AI nonce+provider+model+prompt; 16KiB cap, duplicate/extras/URL/header overrides refused. Public news and own-key paths pass unchanged. No UI asset mount, account signup/reset or archive enumeration.

Replay checks complete archive/current state and returns before send-start/network. Both claim and send-start transaction ACKs must return before exactly one transport execute. Lost claim/start ACK means no upstream call from this invocation. Lost finish ACK may have settled the receipt but no answer is presented as verified; core local uncertainty latches, no resend. Browser abort/transport deadline does not prove upstream cancellation. Late completion/unknown remains held, quota consumed, no automatic key/model/provider fallback, retry, rollover or active clear. No transaction retry/implicit native provider. Corrupt archive refuses before transport.

HTTP replay exposes only phase/status/response_bytes/cached_answer false and ok/state, no fence/hash/UID/body/request/answer/archive status. Nonce/body/principal mismatch returns coarse held error, not cross-user details. 409 errors are coarse broker_request_held since archive refusal is a ValueError; not assumed validation-before-attempt proof. 503 remains other unexpected failures. Tests check held outcome rather than pretending HTTP status establishes no upstream attempt.

Synthetic tests cover full64 -> explicit rollover -> oldnonce replay/no send -> newnonce65 once; HTTP UID-scoped archived replay; auth revoked before archive/transport; lost claim/start/finish ACK; archive corruption; global unknown beyond expiry; AI empty catalog; public/OFF unchanged. Real no-retry native transaction adapter, Mongo isolation/restart-uncertainty binding, private grants/roles/genesis/schema migration, host evidence and owner OK live remain separate. 199c-b collector and 199c-c helper are later reviewed units; production wiring explicitly NOT done.

<!-- END-ORIGINAL-DOC -->


<a id="doc-132"></a>

### Reference: `integration/REPLAY199CB.md`

<!-- ORIGINAL-DOC {"bytes":2588,"path":"integration/REPLAY199CB.md","sha256":"c1b50249beb1509444cd94d78cb0aed832469b607ffb9608ba7976bc348b0d1a"} -->
# 199c-b unselected synthetic archive-aware collector cycle/status

New run_archive_cycle only, old orchestrator/job/production_entry/public_live107 unchanged. OFF returns disabled without collaborators. Enabled requires exact ArchivedCollectorLedger+CoverageCheckpoints+reviewed writer shape, explicit fetch/clocks and exact fresh injected JobRuntimeEvidence contract. No production provider, native transaction adapter, environment client, schedule, runtime guard construction, cgroup mutation or live mount. The job record's 3GiB fixed containment and real-host proof remain external activation gates, never a512MiB WSGI readiness claim.

Provider refreshed before claim, fetch and write-start. Submit/running transaction ACK required before fetch; exclusive write-start ACK and heartbeat required before writer. Fixed full input/source coverage schema, 90s cycle budget/immutable checkpoint/prepared article contract preserved. No automatic rollover/retry/takeover. Archived oldnonce returns terminal status and retained coverage without fetch/write. Missing/corrupt retained checkpoint holds, no invented healthy feeds. Newnonce after explicit synthetic terminal rollover proceeds once under monotonically preserved fence. Unknown write stays active uncertain_after_write, acknowledgement loss never authorizes replay or another writer.

Archive-aware status uses complete verified chain/current job and exact retained fence, then reads the original immutable coverage checkpoint. It is an internal callable, no archive enumeration/HTTP route. Two status snapshots are observational, not a transaction across checkpoint state; checkpoint immutability remains an independently enforced source contract and retained original checkpoints are not deleted. Status failure does not clear jobs. HTTP owner-Bearer status exposure deferred to199c-c sourcehelper boundary; not silently promoted to publicnews.

Tests use synthetic transaction provider/disposable checkpoint/article fixture and mocked writer. Full64 -> explicit rollover -> oldnonce no65thfetch/write ->newnonce65once, claim/running/write-start lost ACK no affected external I/O, corrupt archivebeforefetch, missing retained checkpoint, stale/no provider, beforewrite proofrefresh and writerunknown holds. No actual feed/provider/Atlas calls or measured workload proof. Native no-retry provider and durable uncertainty across restarts, real transaction isolation/host limits, private roles/new schema/genesis and owner OK live remain gates. Runtime capacity ready is NOT claimed. Production wiring remains explicitly NOT done.

<!-- END-ORIGINAL-DOC -->


<a id="doc-133"></a>

### Reference: `integration/REPLAY199CC.md`

<!-- ORIGINAL-DOC {"bytes":2481,"path":"integration/REPLAY199CC.md","sha256":"e53f402652ffd2939aa70a8dba3b7037d7a7baba679033145be68938814bdea9"} -->
# 199c-c explicit source composition helper

Default OFF returns the exact public callable without reading collaborators. No environment flag/client URI/provider construction, no production entry import/mount, no scheduler/job launcher or collector POST execution. Enabled helper is synthetic-only source composition of independently reviewed archive broker/auth plus owner-Bearer GET collector status. Existing production_entry/public_live107/collector197_job/old factories unchanged. Production wiring is explicitly NOT done. A future separately reviewed activation unit needs verified native no-retry provider plus owner grants/host/schema gates; this helper and synthetic provider are not that unit.

Owner status namespace /api/collect/status/<exact64hexkey> intercepted before public fallback. Exact bounded Bearer comparison before key inspection/archive access/job evidence; Origin/query/request body/transfer encoding rejected. Only GET exact key, no enumeration, no POST collection/method fallback/public exposure. Fresh exact injected JobRuntimeEvidence before archive status. Status reads full verified chain and retained checkpoint coverage. Missing/corrupt data, stale proof, local uncertainty fail generic503; none supplies retry permission. Two independent status snapshots remain observational, checkpoint immutability retained as source contract. No private token appears in responses/logs; no-store/nosniff/no-referrer/noindex headers. This read-only source gate does not authorize sharing private status or opening live databases.

Broker path still existing source198 auth/origin/CSRF/live account gates and exact199ca archive budget/transport. Replay fields remain phase/status/length/cached_answerfalse only; no UID/hash/fence/archive enumeration. Public routes pass unchanged, no health-ready claim. AI catalog empty. Collector and broker transaction providers remain injected and synthetic tests only; no live capacity-ready claim or64cap readiness. No automatic archive rollover/retry/refund/reset.

Tests compose synthetic collector/archive retained status with authenticated HTTP broker, oldnonce replay/no second network, both-family corrupt-chain denial before I/O, bearer/privacy/method/body/query/stale-proof checks, public/OFF identity. Earlier199ca/b full64->rollover->new65 and ACK loss gates retained. No actual3GiB guard/workload/provider/Atlas/roles/schema/mount/oldcollectorstop/live switch executed. Owner OK live still required separately.

<!-- END-ORIGINAL-DOC -->


<a id="doc-134"></a>

### Reference: `integration/REPORT227.md`

<!-- ORIGINAL-DOC {"bytes":7747,"path":"integration/REPORT227.md","sha256":"7cd8c35fa0f6e4a093046e24ff291d41772b2fbd55b9c2fbedfa3c92714cfb24"} -->
# Finder nested report diagnostic ledger (227)

Test/docs only. No production source, policy, sandbox, mount or activation changes.
The indexed preserved Finder source is src/app.js, SHA256
`f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91`.
The older FINDER_PARITY_PLAN.md rows 31 and 60 remain open, with this ledger
adding narrower observations rather than declaring report parity complete.

## Claim ledger

| Claim | Status and scope |
| --- | --- |
| Nested original report button opens fallback report | Verified in Chromium's nested private workspace fixture, with a synthetic placeholder own key. Existing CSP blocks the provider before a request reaches the harness. Original button opens an about:blank-written popup whose opener is the nested Finder frame, with source-parsed 21 ordered sections, original product title/code 090121, Data edition date/error note, and original busy-button reset. Not an AI narrative report. |
| No-key report button | Verified: original key prompt appears; no popup opens. No-key static report by button is NOT supported by this original gate. |
| Popup blocked | Verified with a harness-only window.open returning null: original popup-blocked message appears and original finally path resets the button. |
| Chromium page.pdf emulation | Captured, text extracted and pixels inspected. NOT clean layout parity: fixed footer overlaps the contents boundary on page 1; original pagination effects absent. Native print/PDF remains OPEN. |
| Popup print button invokes window.print | OPEN, observed blocked. Keyboard activation of original inline onclick leaves instrumented counter 0 -> 0 and logs enforced-CSP violation. Control test-only listener increments 0 -> 1 without a new violation. Earlier preliminary counter-1 result is not evidence of working original print. |
| Native OS print dialog, real AI narrative popup, Safari/Firefox, live network | OPEN; not tested, not implied. |
| Inline popup report script/pagination | OPEN, effect absent: zero .pgnum elements and zero inline-positioned .tpl-sec sections. Source load script would create both. No assumption that missing effect is explained solely by a console message. |

The provider fetch was blocked by the existing connect-src 'self' CSP before
any request reached the harness; harness recorded zero outbound requests.
No outbound request succeeded. Two runs observed 14 provider CSP console
blocks. That count is evidence, not a general service retry guarantee.
Existing Frankfurter attempts are also blocked by current CSP; no network is
turned on. Popup itself recorded no requests. No headers, request bodies or
query strings are saved; console URLs are reduced to scheme/host/path.

## Original seams and policy

- src/app.js 104: aiAvailable reads V.apiKey, proxy and built-in keys.
- 191 and 742: original hsn-gemini-api-key localStorage own-key seam.
- 2232-2510: original report generator, escaping, ordered section inventory,
  date, Data edition error note, inline print handler and load script.
- 2512-2525: original openTemplateReport and popup-blocked error.
- 3441-3451: original no-key gate, popup opening and finally reset.
- integration/ui/workspace.html line 5: actual iframe sandbox is exactly
  `allow-scripts allow-same-origin allow-downloads allow-modals allow-popups`.
- integration/news_api.py 52-60: actual enforced Content-Security-Policy,
  not Report-Only. The test compares exact workspace CSP and nested response
  CSP, including inline hash values derived from actual response bodies.
  connect-src remains 'self'; no extra sandbox flags or CSP directives.

Synthetic own key is only `SYNTHETIC-PLACEHOLDER-NOT-A-KEY`, set before load
in throwaway browser storage. No real keys, users, rows or service accounts.
No product function instrumentation, fake report HTML or provider response.
Harness-only print counter and window.open-null probe are labelled above.
The print control listener is attached only after the original probe, outside
production. Screenshots/PDF depict this diagnostic report, not live research.
The report's source claims about data accuracy and busy services are original
text, not verified current facts. In this run the actual failure is CSP.

## Determinism and artifacts

Date constructor/Date.now frozen to 1791576000000 (report shows 2026-10-10 in
Asia/Kolkata). Math.random fixed to 0.25. No timed sleeps. Nested viewport
1440x1000; popup captures 1440x1000 and 390x1000. Two stable diagnostic runs.
Chromium 154.0.8037.57; pdftotext/pdftoppm 22.02.0. Playwright version is in
the review receipt. No after/before-fix claims: there is no production fix.
Per-run probe.json labels capture times, viewport and selected PDF pages.

PDF parameters: A4, print_background true, margins top14/right12/bottom20/
left12 mm, prefer_css_page_size true. This is Chromium emulation, not an OS
print dialog. 27 pages observed; source-derived section titles all appear
in extracted text. First/middle/last sections were checked in text. First,
middle and last PDF pages inspected as pixels are 1,14,27. Page14 is Technical
uses; page27 is FAQ. Page1 contents meets the fixed footer, so vertical layout
cleanliness remains OPEN. All 27 rendered pages are 707x1000; a rightmost
25px dark-pixel check is zero across them. That right-edge check establishes
only empty right margins, not absence of vertical overlap or full parity.
The PDF shows the report as rendered without the pagination script's effects.
Artifacts remain outside the commit.

## Run

`python tests/browser_finder_report227.py` writes to REPORT227_OUT (default
/tmp/report227-review). The unittest wrapper is opt-in with
RUN_REPORT227_BROWSER=1; missing Chromium, Playwright or PDF tools produces an
explicit skip, never a popup/PDF pass. Source pin/policy tests run by default.

Existing nested CSV/clipboard/print-invocation and 198d browser results belong
in the receipt, with failures and any test-navigation correction disclosed.
The nested shortlist print counter is not proof of this popup's print handler.
No DB reads/checks/writes, mail/send, production assets/mount/wiring/activation,
217/201c, sender222 consumer, cutover, recipients or wording selected.

## Regression findings on the current 226 base

The unchanged nested shortlist browser script failed: current workspace opens
on Geo and it waited for hidden #d-fav. This was pre-existing, outside the root
suite; earlier CSV/clipboard proof was an earlier run, not today's current
verification. 227 makes only two actual Finder-navigation clicks after goto/
reload in that existing test. Assertions, fixture and final pass line remain
unchanged. Corrected nested script PASS, including CSV/clipboard persistence,
keyboard scroll, instrumented shortlist-print invocation and mobile width.
The original FAIL log and corrected PASS log are retained separately.

Additional current browser probes: 198d PASS; ships226 PASS; Finder static
PASS; Finder offline PASS. Standalone browser_feature_finder FAIL waiting for
popup with no own key, not a Geo navigation issue. browser_finder_network FAIL
waiting for manual ships refresh text, not a Geo navigation issue (direct
Finder route). Neither is changed here, neither counts as current parity
proof. These failures are retained and require separate scope if repaired.
All other browser_*.py workspace-entry scripts were scanned for this exact
Finder-hidden assumption; the nested script was the affected Finder test.
News-only/map/weekly/country/channels scripts are not report evidence and
are not claimed rerun by this unit.

2026-10-10: 228 supersedes current source/snapshot pins and popup behavior. The observations and source hashes above remain historical BEFORE evidence. See REPORT228.md.

<!-- END-ORIGINAL-DOC -->


<a id="doc-135"></a>

### Reference: `integration/REPORT228.md`

<!-- ORIGINAL-DOC {"bytes":7219,"path":"integration/REPORT228.md","sha256":"3ee86e08a87e0e33034dd7da0fb3d26d264b88aaba07d215d56e2df2629b8ef1"} -->
# Finder report popup repair (228)

## Visible changes

The report opens the same way and keeps the same product text/data/AI fallback.
Its Print button and page-number setup run from the Finder opener rather than
scripts inside the popup, so they work with the existing security policy.
Print layout no longer places the fixed footer over report text. Copyright
now appears at the document end in print, not on every page. Screen footer
stays fixed. No security rule or AI/network access is opened.

This is local code and generated snapshot preparation, not serving, mount,
deploy, live SW activation or runtime wiring. No DB/send/cutover changes.
Native OS print dialog, live AI/provider behavior and other browsers remain
unverified. Existing feature-finder and finder-network failing scripts are
not repaired here. Historical REPORT227.md and SHIPS226.md retain their old
source pins and findings with a dated supersession note.

## Mechanics and limits

buildTemplateReport returns no executable script or on*= attribute. It keeps
21 ordered sections (01,01A,02..20), titles, esc() text, product code, Data
edition/error note and copyright. Print button id tpl-print gets a listener
from the opener, calling the captured popup's w.print. A later print throw is
caught without falsely displaying a popup-blocked error. Setup failure still
uses the original report-open error path; no-key gate and finally unchanged.

setupTemplateReportWindow stores a one-shot guard on the popup document.
It waits for complete readyState or one load event, then actual doc.fonts.ready
or a 1500ms deadline (no polling). Actual report uses system fonts; the tested
report's fonts are ready before measurement. If a font is still pending at
the deadline, layout is measured then and is not remeasured later. That is a
bounded fallback, not a promise for custom late web fonts. No font requests
are added. The exact helper is tested in a synthetic realm for late ready,
load, deadline, closed-popup guards, idempotence and later print throws.
Actual Chromium tests exercise the real report and its font/layout effects.

Pagination retains original TPL_PAGE_H=994, section order, min-height and
Page X of Y screen stamps. It uses popup-owned elements. Print uses natural
flow, hides stamps/actions and overrides min-height; print footer is static.
No @page margin boxes, content duplication, removed contents or hidden text.

Popup reload/navigate loses its written document/listeners/pagination. Reload
was observed as about:blank with zero report sections. Reopen from Finder to
regenerate; this is not a durable report URL. Old inline behavior lived in the
old document and cannot be promised after a reload either, but attaching from
opener does not reinject listeners into a replacement document. This lifecycle
change is explicit, not hidden or claimed supported.

## Pins and local snapshot consequences

| Path | Current SHA256 |
| --- | --- |
| src/app.js | bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313 |
| index.html | e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625 |
| offline.html | b55d6b0cf2be2ff3ddf366c4afa23d452367265ef2e85a31b9a4fb6cd411b486 |
| data.d6d1b417562b.js | d6d1b417562bad99e7b434605d63966772749d573375fb10d74ee52cb6bb82f6 |

Dataset filename/bytes unchanged. sw.js unchanged. Local index/offline bytes
changed. Public offline served snapshot bytes changed, so its explicit-opt-in
cache id changes from geo-public-finder-2491a5a38160-v1 to
geo-public-finder-4f48ae1b3cd7-v1. Returning devices would get the revised public
snapshot once the new code is served and their offline flow is used. No live
origin's cache or SW is touched now. Privacy/no saved keys/notes behavior is
unchanged and its existing offline browser probe passes.

Own-key pins in test_finder198d/test_ships226 and served-copy SOURCE_SHA/
OFFLINE_SHA are updated with 228 notes. Build provenance is generated locally
with scripts/finder_provenance.mjs prepare(), which double-builds and confirms
inputs unchanged. Node v22.23.3. Exact portable rebuild command is shipped in
the audit artifacts, writing only index/offline/sw and receipt, refusing any
changed dataset. No refresh.mjs/automate/provider read is run.

## Evidence

BEFORE: verbatim copies of 227 final indexed-run report/PDF/PNG/probe, original
capture times exactly as saved in the copied probe: run started 2026-10-09T23:07:00.683204+00:00 and finished 2026-10-09T23:07:21.943997+00:00. Their source is the 227 tree ffe6092,
report print counter0->0/CSP violation, pagination0 effects, fixed footer
covers Contents 08/17. They are not recaptured or relabelled as new before.

AFTER: final 228 builder runs run1/run2, timestamps per probe/artifact; fixed
report date2026-10-10, random0.25, nested1440x1000, popup1440/390x1000. SHA256
and exact before/after capture times live in the outside-commit artifact
manifest. Two runs stable on semantic evidence. Chromium154.0.8037.57,
Playwright1.63.0, pdftotext/pdftoppm22.02.0. Harness uses only synthetic
SYNTHETIC-PLACEHOLDER-NOT-A-KEY. No headers/bodies/query strings recorded.

Nested: original button opens fallback from iframe; enforced CSP and sandbox
unchanged; no-key prompt and popup-blocked reset pass. ProviderCSP blocks14
observed, zero outbound/pop requests, not harness-aborted. Print Tab/Enter
calls popup print counter0->1 without an inline warning. Print throw doesn't
change opener briefError. Idempotent setup keeps 27 page stamps and 21
positioned sections, numbers ordered. Actions visible/keyboard-reachable on
screen and hidden under print media. Generator runtime purity checked.

Standalone: original generated index.html with no CSP served from separate
local static server; original button placeholder-key/failing-provider fallback
opens, paginates and prints via opener listener. Gemini/Frankfurter requests
are aborted at harness, sanitized method/host/path only, no outbound success.
Local branding/favicon404 is observed, unrelated to this report repair.

PDF uses same 227 options: A4, printBackground true, margins14/12/20/12mm,
preferCSSPageSize true, explicit print-media mode before page.pdf. Observed27
pages. All21 section titles/code/product/Dataedition/error/copyright match
227 extracted text (whitespace normalized); no print button in PDF text.
All-page word boxes lie within page bounds. Copyright is at document end.
Builder inspected final run2 page1 (Contents08/17 unobscured), page14 Technical
uses, page27 FAQ+copyright, and390 popup pixels. This is evidence for this
fixture, not clean layout for arbitrary long/AI text or native OS printing.

A preliminary harness run left media='screen' before PDF and produced50
pages, including the button; that run is rejected as PDF evidence. Final
runs set print explicitly and are the only AFTER captures used in audit.

Regressions: nestedCSV/clipboard/persistence/keyboard/mobile PASS; Finder
static PASS; offline PASS(new cache id/privacy); 198d PASS; ships226 PASS.
227 browser now explicitly skips as superseded BEFORE method; its historical
pin assertion checks REPORT227.md rather than current production source.
No claims that the older standalone feature-finder/network tests now pass.

<!-- END-ORIGINAL-DOC -->


<a id="doc-136"></a>

### Reference: `integration/REPORT_PREVIEW_FRAME_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1594,"path":"integration/REPORT_PREVIEW_FRAME_LIMITS.md","sha256":"e3a81eab0783cd0d48dc6ccb7d8d0a4763ac5972457463a7f2f75eca067cbd13"} -->
# Mobile-safe original report preview frame

Only digest_preview digest/weekly output is framed. Original hash-pinned report
sources, direct renderer output and mail builder output remain unchanged. No
new send, event query, data selection, client or runtime activation. Critical
preview remains unchanged; its missing alert glyph is a separate original issue.

Re-sanitizes HTML first, then appends fixed trusted viewport/CSS. Source script,
style, iframe and unsafe links remain blocked. Body style is retained so font,
colors and desktop appearance don't default to browser serif. Source tables
retain order/content, but private preview outer report widths can shrink to
phone width. Cell/anchor long words wrap. Not a changed email template and no
claim all mail clients are responsive. Only internal original body shape used.

11 focused wrapper+existing preview route tests pass locally with restored
original assets. Author actual pixel checks at390px digest/weekly long title and
summary fixtures: no horizontaloverflow, readable font/layout, no external
resource requests. Direct original weekly still width680, originalhashesmatch.
No actual phone/mailclient/hostedproxy check. Desktop/event/empty visual cases
need expanded check before broad UI readiness claim. Fullsuite69:913testsPASS,1skip,1expectedfailure. Reviewer independently
checked four wrapper tests and390/1280pixels, but lackedFlask forroute tests.
Repro python -m unittest tests.test_report_preview_frame tests.test_digest_preview_routes -v;
requirements-staging.txt plus python-dateutil installed, bundled originals.

<!-- END-ORIGINAL-DOC -->


<a id="doc-137"></a>

### Reference: `integration/REPORT_STYLE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1141,"path":"integration/REPORT_STYLE_LIMITS.md","sha256":"6914cc0083abbf8dcc968f26fcb72098dfe286ec8407a5c5b619ebb714475f43"} -->
# Inline report styling

The report sanitizer keeps bounded decorative inline CSS, including solid colors,
linear gradients, spacing, typography and borders. It is a resource/execution
boundary, not a guarantee of text visibility or color contrast. White text on a
white background can still be unreadable.

CSS dimensions, overflow, opacity, text alpha/RGBA colors and negative margins
are omitted. Font sizes use 8-99px/pt. Existing HTML table width attributes remain;
the preserved 700px report table overflows a 390px browser viewport and is not
claimed to be mobile-responsive.

A `background:linear-gradient(...)` declaration gets a solid color fallback.
A `background-image` gradient does not automatically get that fallback. Email
clients can omit gradients. Rendering has been checked in Chrome only, not a
matrix of email clients.

Styles are bounded to 64 declarations and 4000 output characters. No remote CSS,
URL-based CSS resources, scripting expressions, custom variables, positioning or
animation is allowed. This design support does not enable delivery or change
sender, recipient, schedule, collector or storage settings.

<!-- END-ORIGINAL-DOC -->


<a id="doc-138"></a>

### Reference: `integration/REQUESTED_FEATURES.md`

<!-- ORIGINAL-DOC {"bytes":3903,"path":"integration/REQUESTED_FEATURES.md","sha256":"461a78a8c1610c6d33b2bed9496a2b109ca3ac9e02d7a0b4be2833076250eeda"} -->
# Requested features awaiting implementation

## Story sources list

Recorded October 6, 2026, from the user's feature request and refinement relayed
by the parent. Status: requested, future increment after the current queue.
Do not build yet.

### One news page: main story and similar reports

User example: channel X reports "Tomorrow rain". That is the main full record.
Another 2-3 channels may cover the same story with different, extra or minimal
wording. Those reports must NOT become separate full news records.

On the same news page, show the main story's full data. Below it, show a
"similar" section listing each other covering channel's name, short wording
and link. Save the per-channel source/title or short wording/link/time so the
other links and mini data survive grouping. This is the user's "Full coverage"
idea, refined to one main record plus a similar-reports list, not duplicate
full pages for each channel.

Matching the same story across different wording is the hard part. Future work
needs title/content similarity, not exact-title dedupe. A related topic is not
necessarily the same event; matching accuracy and false-grouping cases need
review before implementation is treated as correct.

### Current gap

intelligence/geo/processing/dedupe.py keeps one near-duplicate article (first
seen, or the higher score when score_key is supplied), increments corroboration,
and drops the other articles' source details and links. It uses fuzzy title
similarity, not title/content story matching. The count is matching records,
not a verified count of distinct independent channels.

No grouping/schema/storage/UI code change is included in this record. Preserve
source identity and per-channel mini data; do not assume the existing count is
a sources list. Main-record selection and similarity rules remain future design
work, not an instruction to change the original collector now.

## Anti-hacker layers

Recorded October 6, 2026, from the user's request relayed by the parent.
Status: queued after current work, alongside the integrated serving/security
review package. No implementation or activation now. Free/simple only, no
paid services.

Requested scope:
- Rate limiting on endpoints.
- Input validation review.
- Honeypot: hidden form field and fake admin endpoint that auto-flags/blocks
  bot IPs.

Future design must review trusted-proxy/client-IP handling, shared rate-limit
state, validation boundaries and abuse tests. Honeypot-triggered blocking
needs false-positive, shared-IP, expiry/recovery and accessibility review;
an endpoint hit or filled hidden field alone is not proof of a hacker.
Do not treat these layers as a complete security guarantee. No real IP
blocking, endpoint addition or configuration change is included in this note.

## Login security verification

Queued with production login wiring: verify password persistence uses a salted
password KDF (bcrypt/Argon2 or equivalent), never plaintext, and verify actual
HTTPS responses set HttpOnly and Secure session cookies. Review storage write
paths, logs, exports and injected implementations, not only helper functions.

Current inspected code: accounts/passwords.py defaults to scrypt N=32768,
r=8,p=1 with random16-byte salt and32-byte derived key; PBKDF2-HMAC-SHA256
600000-iteration fallback when scrypt unavailable. accounts/service.py hashes
signup/change/rehash values before storage and emits HttpOnly/Secure/SameSite
Strict cookies. preview_access.py sets Secure/HttpOnly Flask session flags.
These are offline code findings, not verification of production persistence or
hosted cookies. Store interfaces accept caller-supplied strings, so they alone
cannot guarantee every injected caller stores a valid hash. The closed synthetic
shared-service fixture uses labelled SHA256 test hashes, not password security,
and must never be wired for real users. Production login remains unwired.

<!-- END-ORIGINAL-DOC -->


<a id="doc-139"></a>

### Reference: `integration/RETENTION_AUDIT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4334,"path":"integration/RETENTION_AUDIT_LIMITS.md","sha256":"04d2776a42d4e24c441cd53eb057538c0ed9265a3dfdf5aa665fd77886e6ae93"} -->
# Supplied Geo retention fidelity audit

Pure audit only, no source query/client/network/send/delete/write/route/scheduler. Original functions unchanged. Exact hash-pinned allowlisted pure formatter/batcher AST definitions loaded without original imports/config/requests/database. This is reviewed trusted source, not hostile-code sandbox. No identity field (_id/id) accepted; ordinary title/summary/URL strings may contain identifiers. Those values never returned/printed. Output aggregate counts only, no per-input selection or ordinal eligibility list. Output contains lengths/booleans/counts, not article values, links or identity sets.

Original metadata cleanup deletes all age-selected IDs without verifying backup refs/receipts/retrievability. Original Telegram archive is a readable summary (title120, no full summary or all fields), not lossless storage. Full-record backup includes public fields/summary but isn't exact BSON fidelity. Its estimator +2 differs from actual8-character separators, permitting batches above3500; single oversized record unsplit. Backup send failures can leave empty references while later original cleanup does not check them. Original same-local-day HTML archive overwrites; nonfatal write happens before SMTP, not Apps Script digest-data. These are source findings, not permission to run those paths.

Exact inert fixture<=1000 rows/2MB/16kstrings, no IDs/privatekeys/custom objects. Explicit None normalized to empty fixture text, documented difference from original None behavior; created_at stays unclassifiable. Fixed aware UTC clock/daywindow1..3650. Original age query is lexicographic string<$UTCcutoff, strict inequality. Audit classifies actual aware timestamp separately, reports mixed-offset discrepancies; missing/invalid/naive timestamp unclassifiable chronologically, no implicit timezone. Every originally supplied string still gets the original-style lexical comparison. Missing/null created_at never counts as Mongo$lt selected, separately counted unclassifiable_missing_or_null; empty string is a string and may be selected. Aggregate source_would_select and unclassifiable_source_would_select counts expose the risk, never eligibility. Cutoff .isoformat() formatting/clock parity with database.py remains explicitly unverified; source bundled for inspection. Exactcutoff excluded. UTC fixture archivefilename differs from original server-local date; collision finding doesn't assume current deployment timezone/path.

Internal per-input batch span accounting flags dropped/duplicated records, empty text and oversized content. Internal substring checks are structural only and tautological for the original full formatter, not preserved-value/lossless proof. Summary text characters not found are measured by substring occurrence (coincident content may match), not a semantic omission proof. Aggregate title truncation and substring nonoccurrence reported. Actual backup/summary batch lengths and overflow flags versus original estimator computed. failed/partial counts unknown (None), send_state not_executed, no real receipts. Backup URL is supplied unverified hint, never safety evidence. No issue or age selection implies deletion safety. deletion_safety/backup_losslessness always not_established.

Future retention policy OPEN: required full-content coverage/content-hash receipts/retrievability, stable source version/claim binding, exact destination/collection/IDs, authorized destructive policy, snapshot retention/expiry and partial retries need separate review and user effect approval. Defaults remain no deletion. No eligible_to_delete/deleteapproved/deleteID output. No cleanup changed.

Configured repo repro: python -m unittest tests.test_retention_audit.8 tests: original formatter value/ordinal accounting, title truncation/summary omission, separator-overflow3504 vs3500 and oversizedsingle, missing/invalid/naive/mixed-offset/exactcutoff, identity-field rejection/no outputvalues, hints/no-sendcounts, same-day collision/AppsScript omission/bounds. Bundle needs pinned original files, not standalonefullrepo. No live external provider policy/current availability proof.

Tested Python3.10.12. Pure AST structure check only, not a general capability sandbox. Aggregate noissues never permits deletion; no list of selected article ordinals/IDs returned.

<!-- END-ORIGINAL-DOC -->


<a id="doc-140"></a>

### Reference: `integration/RUNNER199LOCK.md`

<!-- ORIGINAL-DOC {"bytes":2887,"path":"integration/RUNNER199LOCK.md","sha256":"2c8d580d1e2a71780446172792d71ddb2819afbcd5243e2120d64acb1414f20c"} -->
# GitHub Ubuntu24.04 CPython3.12 lock repair

Owner's first manual diagnostic run stopped at pip hash validation, before the aggregate guard ran. Charset-normalizer3.5.2 selected cp312 manylinux wheel SHA3d31298449090ab8d47b7b1b2a555ff73cac7ed438a08b7ac160980c7ebed649; old lock pinned a different interpreter artifact. This is a hash selection mismatch verified against official release metadata and actual download bytes, not evidence of malicious modification.

All25 exact pinned versions audited via official PyPI JSON release endpoints. Complete published wheels+sdist hash sets added for each version; no version change, no hash removal, no --require-hashes weakening. Charset172, MarkupSafe151, PyMongo71 and PyYAML53 published artifacts. All other packages similarly include their full official artifact sets. Provenance ledger includes filenames, URLs, sizes, SHA256 and metadata-payload hash. Official metadata hashes are not proof arbitrary package code is safe; scope is exact existing versions/artifact compatibility. No credentials, workflows or repository settings changed.

Runner-target cross-download checks24binary wheels using CPython3.12/cp312+ABI3+none and manylinux2014/manylinux2.28x86_64 tags with --require-hashes, actualbyteshashes match official metadata. Five old entries would fail: charset-normalizer, MarkupSafe, PyMongo, PyYAML, sgmllib3k. Sgmllib has only an official sdist: old hash was a previously reviewed locally built wheel. Preserve that local wheel hash and add official tarball SHA7868fb1c8bfa764c1ac563d3cf369c381d1325d36124933a726f29fcdaa812e9, explicitly distinguished from official provenance. Downloaded tarball/setup.py/sgmllib.py matches the prior source inspection/build receipt; no new source version. Pip may build that pure Python sdist on runner; actual runner result remains to verify.

3.12 execution not performed in the source workspace (only3.10 interpreter installed). Cross-target wheel download and metadata verification is not3.12 runtime proof. Owner reruns the manual pinned diagnostic after this source landing; no secrets needed and no live collector activation. Keep existing action/source checkout policy, no schedule/PRtrigger/persistent credentials. The diagnostic may still stop on cgroup delegation/isolation/OOM checks; lock repair is not a3GiB guard/workload PASS. Do not relax those checks or change source pin without observed failure and separate review. Production/native no-retry transaction provider/roles/schema/owner OK live remain blocked separately.

Fresh isolated CPython3.10 venv installed all25 pinned packages with --require-hashes; pip check PASS. All24 cp312wheel METADATA names/versions/active Linux3.12 dependencies match the pinned25package closure. Sgmllib legacy setup install executed only after matching prior reviewed source/setup bytes. This fresh3.10 check is not3.12 runtime proof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-141"></a>

### Reference: `integration/SCHEDULE-CALLER214.md`

<!-- ORIGINAL-DOC {"bytes":6195,"path":"integration/SCHEDULE-CALLER214.md","sha256":"c0fea1454c0fcd989f677e11276833b57150b2d6afe909d41913a7ad00865ad5"} -->
# 214: pure Geo occurrence caller, not a scheduler installation

arm/tick/acknowledge_occurrence integrate actual205next-occurrence calculation
with plain supplied state. No job is dispatched. No timer, callback, sleep,
environment, processTZ, DB, ledger, SMTP, AppsScript trigger or production mount
exists. Native/runtimeengine stays unchanged. No current module imports214except
its test. AppsScript rail and legacy schedules remain untouched. Item25 staysOPEN.

## Scope

205is Geo-only: profile_plan('geo',settings), one next occurrence per call and
ONE configured wall-time per day.214accepts ONLY exactGEO_SCHEDULER_TIMEZONE,
GEO_WEEKLY_REPORT_DAY,GEO_DAILY_RUN_TIME settings. BRICS' two collector intervals
and multipleDIGEST_TIMES are NOTcovered. Geo weeklycadence is an explicit policy
choice, not legacy installation or feature parity. No invalidweekdayMonday
fallback. Missing timezone/time/day/DSTpolicies refuses, never inferreddefaults.

OFF arm returns staticdisabled/send_allowedFalse/dispatch_allowedFalse/
activationFalse/scope before touching anyargument or importing205. Enabled must
be exactbool. ON calls175validation and205separately for exactdistinctdaily/weekly
cadences(max2), strict exactUTCdatetime anchor, explicitfirst/second/refuse fold
policy andskip/refuse gap policy. It stores at most ONEpending occurrence per
cadence, no missed-run backlog.205none_in_window is held_no_occurrence, NOTwaiting.

## State and identity

State is exactplainJSON, no datetime/callable/capability. It includes schema1,
profilegeo, settings/hash, sortedcadences, bothpolicies, last_seen, per-cadence
anchors andoccurrences. Eachoccurrence includes205evidence:UTC,localoffsetwalltime,
fold,offsetseconds,weekday,skipped_nonexistent count andexacttzdataprovenance
source/systemversion/packageversion/zonefileSHA. CanonicalJSONhash binds profile,
cadence,settingshash,anchor,ALLEVIDENCE(includingskippedgaps),bothpolicies. No
ambiguous delimiterjoin. Different folds/policies/cadences have differentIDs.

Each tick recomputes205from the STOREDANCHOR, revalidates settingshash and requires
ALLEVIDENCE/identity/flags equal. ChangedUTC/local/fold/offset/tzdataversions/source/
zonehash/policies/extra fields holds with fixedreason, no settings/errorvalueecho.
Boolean-vs-int andsubclass differences refuse. Shapes/depth/nodecounts/text/int
bounds hold beforecopy/hash. No private error context/cause remains. This checks
consistency, NOTauthentication: a caller can fabricate an entirely self-consistent
state. Such supplied state cannot authorize dispatch or prove durableacknowledgment.

## Polling and observation acknowledgement

tick takes exactUTCnow andexplicitexactint max_lateness_seconds0..3600 (bool
refused). Before occurrenceUTC=waiting; exactlydue=due; due+limit inclusive=due;
one secondlater=missed_held. now earlier than storedlast_seen is clock_rollback.
Input never mutates: only RETURNEDstate advances last_seen. Repeatedpoll gives
sameID/status, NOTa renewedjob/sendpermit. No automaticcatch-up or advancing past
unresolveddue. A poll dayslate returns ONE missed_held per cadence, no backfill
flood. Daily+weeklycoincident returnsBOTH with distinctIDs, coincidentTrue andfixed
notedispatch_not_allowed, never deduplicatedsilently.

Everyreturnedoccurrence has static send_allowedFalse,dispatch_allowedFalse,
activationFalse andscope supplied_schedule_state_not_durable_or_execution_authority.
Due means only preparation for futureexplicitreviewedcaller, neverpermission.

acknowledge_occurrence is PUREOBSERVATIONacknowledgment, notdurablejob/sendreceipt.
It requires an exactpendingID and recomputes current205evidence beforeadvancing
onlythatcadence. Next205anchor is the ACKNOWLEDGEDOCCURRENCE'SUTC, strictlyafter,
NEVER now. Lateackcannot silentlyskip interveningoccurrences. It leaveslast_seen
unchanged anddoesnotcalltransport/store/operator. Caller owns anyprovenance,
persistence andauthority; functiongrantsnone. No ack ofnone_in_window. StaleID
refuses. It is not a replayjournal/exactlyonceguarantee.

IMPORTANT: acknowledge_occurrence has NO CLOCK. It accepts a still-WAITING
(not-due) pendingID and advances it, silently skipping that day if misused. A
future TRUSTED caller may only acknowledge IDs it actually observed in a due or
missed_held tick result. This unit does not enforce that evidence or authority.
Every tick re-reads205tzdata; source/package/zone changes hold(changed), never
automatically re-arm. A future explicit reviewed re-arm path is required.

Supplied-state dedup NOTexactly-once. Crashed/restartedprocess loses
acknowledgment unless futuredurablecaller persistsit; it may repeatobservation.
Nothing about duplicateIDs guarantees no duplicatecollector/mailjobs. Activation
needs durableoccurrenceclaim/checkpoint, clock/restart/missedrunpolicy,
source-groundedowner timing/cadence/DSTchoice, reviewedtimer/callback,
weeklyidentity, actualdeploymenttzdata andAppsScriptcutover. Native201c held.

## Grounding and tests

Actualcurrentmain205live-readSHA25644fd51c027e14bef4c30cf81b4fd4bf77d1faac1637b6b414fbeaa6c88f8ee52
matchedlocalbase. ActualoriginalGeo schedulerdc42e6147db678d3ad93d62f3412cd521230a040296a405e60d77588b99936a0
uses process-local schedule.every().day.at, weeklyMondayfallback and--now.
BRICSscheduler8e57b8aa7aeed25d4b9723d5235861b8f4be38c336de6be79e32bc713ba63f26
usescollectorintervals/multipleDIGEST_TIMES, no weeklyinstall. Both readlive,
neitherimported/executed. Legacyinit_db outageguard remainsseparate, notsilently
"fixed" by this caller; no legacycollectorentry is invoked.

11newtests+205/175=30focused: realdaily/weeklyIST/equality/latenessboundaries,
rollback/deepcopy, dayslateheldoneeach/ackanchoroccurrence-not-now, coincident,
NYfold0/1/gaps/skippedcount/policyIDs/LordHowe, mutateEVERYstoredoccurrenceleaf,
statefields/subclasses/boolint/extra/configmissing/naive/nonUTCnow, tzdatadrift,
none_in_windowheld, OFFhostileargs/importtrap/sysmodulesunchanged, duplicatepoll,
JSONroundtrip/staticflags andASTallowedimports/no currentactivationedge. Expected
timevalues depend onlocal205tzdata, notverifiedproductiondata. No live scheduling,
mail/DB/collector/timer/trigger/cutovereffects occurred.

<!-- END-ORIGINAL-DOC -->


<a id="doc-142"></a>

### Reference: `integration/SCHEDULE-OCCURRENCE205.md`

<!-- ORIGINAL-DOC {"bytes":6285,"path":"integration/SCHEDULE-OCCURRENCE205.md","sha256":"e6b2c33bb57360b7cbd802964dec92aeadb2758a6d54b47aeb6aeca0440377d3"} -->
# 205: next Geo report occurrence, calculation only

`next_occurrence` answers only "next after the anchor". A missed occurrence is
never reported or replayed. This is not a schedule, timer, job, claim, durable
ledger or exactly-once mechanism. No caller is wired. No collection or mail
function is imported or invoked. No environment configuration or current-clock
read is introduced, but zone data has the environment dependency described below.

Input: exact unit175 Geo namespaced settings, required explicit `cadence`
(daily/weekly), `ambiguous` (first/second/refuse) and `nonexistent` (skip/refuse).
No DST policy defaults. Anchor must be an exact datetime whose tzinfo is the
singleton timezone.utc; naive, nonzero-offset and subclass inputs are refused.
Anchor microseconds are retained in strict UTC comparison; candidate wall times
have second and microsecond zero. Equality is not "next".

Fifteen local calendar dates are searched, including the anchor's local date.
Weekly uses175's canonical weekday; daily still validates the closed settings
but does not use that weekday for selection. This bound permits a weekly skip
through New York's spring-forward Sunday02:30 to the following Sunday (14 days
when the previous Sunday occurrence equals the anchor). Result is `next`, or
`none_in_window` with null occurrence fields. No silent extension of the window.
Skipped future nonexistent times are counted. Past gaps are not missed reports.
Datetime-range overflow and unusable zone data return a static refusal.

For each wall time, fold0 and fold1 are converted to UTC and back. A candidate
exists only if both wall fields and fold round-trip. A gap is skipped or refused,
never shifted. An ambiguous future wall time is refused or selects fold0 (first)
or fold1 (second); these terms mean wall-clock repeats only, not positive/negative
DST or standard/summer time. If the selected repeat already passed, calculation
moves to a later date, not to the other repeat. Thus an anchor at first/between
repeats with policy first chooses a later date; second can select the remaining
fold1. At or after both repeats all policies skip that past wall time. This does
not catch up a missed first occurrence. Policy refusal can hold the whole result.

Result includes UTC ISO instant, local ISO instant with offset, offset seconds,
fold, local weekday, explicit policy labels, cadence, configured zone, inspected
window and source provenance. Fixed flags say no timer/activation/catch-up.

## Zone data and reproducibility

Python zoneinfo normally searches TZPATH, which can be set by PYTHONTZPATH at
process startup, and then the tzdata package. Unit175 validation inherits those
sources. This module takes its imported TZPATH snapshot, reads the selected TZif
bytes, hashes them, and uses ZoneInfo.from_file on those same bytes (not the
ZoneInfo process cache) for calculation. If no system file exists, it reads the
tzdata package resource. No zone bytes are downloaded. It performs local file
reads, so it is not a filesystem-free or literally environment-independent pure
function. Updating PYTHONTZPATH/reset_tzpath after module import does not update
this module's imported TZPATH; restart/reload is needed.

Provenance: source `system_TZPATH` or `tzdata_package`; SHA256 of actual zonefile;
system tzdata version from that root's tzdata.zi when available (else null);
installed tzdata package version when available (else null). Package metadata is
not evidence that the package supplied the selected system zone. These labels
are local-source diagnostics, not authenticated production provenance. Non-IANA host keys localtime, posixrules and Factory are explicitly refused.
Unit175 alone still accepts those keys; its independent follow-up remains open.
Unknown zone keys/read/parse failures refuse with static text, never echo supplied keys.

Author expected New York/Lord Howe/Apia/Sao Paulo/Dublin values were computed
using system IANA tzdata2025b. The installed fallback package is2026.4, not the
source used for those results. Older or different production timezone data can
differ. Tests pin observed expected instants; they are not universal timezone
policy or proof that a production server has current data.

## Legacy difference, not equivalence

Actual original snapshots were read from GitHub on2026-10-09:
- push2006/geonews scheduler.py SHA256
  `dc42e6147db678d3ad93d62f3412cd521230a040296a405e60d77588b99936a0`:
  lines111-116 use schedule.every().day.at and invalid-weekday Monday fallback.
- push2006/BRICS- scheduler.py SHA256
  `8e57b8aa7aeed25d4b9723d5235861b8f4be38c336de6be79e32bc713ba63f26`:
  lines54-57 install two collector intervals and each DIGEST_TIMES entry;
  this file installs no weekly report schedule.

Original Geo uses process-local timezone through schedule library and silently
falls back to Monday on invalid weekday. This planner uses an explicitly
configured zone and refuses invalid weekday per175. No legacy equivalence is
claimed. A UTC server's original09:00 process-local run would be09:00UTC, while
an IST-configured09:00 planner yields03:30UTC. This owner-visible timing change
requires the item25 decision before any wiring. Original code was not run.

BRICS intervals, multiple digest times and weekly-not-installed behavior remain
outside this unit. Existing legacy schedulers/configuration are unchanged.
Item25 stays open until reviewed caller/engine and profile decisions exist;
production DST policy, missed-run/restart behavior, durable claims and exact
send times remain separate gates. AppsScript selection, SMTP fallback hold,
201c and Atlas/live-effect holds are unchanged.

## Test scope

14 focused tests (11 new +3 unit175): fixed IST strict equality/microseconds,
midnight/week boundary/leapday, weekly skip across NY gap beyond seven days,
NY folds before/at/between/after repeats, Lord Howe30minute fold, Apia whole-day
skip2011-12-30, Sao Paulo nonexistent midnight2018-11-04, negative-DST Dublin,
exact UTC anchors and policies, static zone failure and provenance. Synthetic
empty-iteration test exercises none_in_window's shape (not real-zone evidence).
AST rejects effect-library imports. No original scheduler, real timer, mail,
collector, DB or production timezone source was executed or verified.

<!-- END-ORIGINAL-DOC -->


<a id="doc-143"></a>

### Reference: `integration/SCHEDULER-CIVIL-ZONES206.md`

<!-- ORIGINAL-DOC {"bytes":3321,"path":"integration/SCHEDULER-CIVIL-ZONES206.md","sha256":"3a1b352442e4ff7c2aebd17ea3281aab52e79deb271e262710eeba9e8bddf2d6"} -->
# 206: civil zone key validation for unit175

Host-dependent and leap-second variant keys are refused; real IANA aliases
are accepted subject to host availability. Zone data and the listing are
whatever the host/tzdata package provides, not verified current production data.
An older/minimal host may lack a legitimate alias and will refuse it (fail closed).

One shared helper validates the zone key in both profile_plan and local_clock.
Type must be exact str, nonempty, with no surrounding whitespace. Case-sensitive
exact keys localtime, posixrules and Factory are refused before any scan;
case-sensitive prefixes posix/, right/ and SystemV/ are also refused. right/UTC
is explicitly blocked as a leap-second variant. No normalization or broad
ban of legitimate alias trees is introduced. Remaining keys must belong to
zoneinfo.available_timezones(), minus the same explicit exclusions.

The accepted frozenset is cached per process on the first successful validation,
not at import. First use scans system timezone files and/or installed tzdata
resources through zoneinfo; subsequent use checks membership without rescanning.
No environment configuration, download or timer is added. An empty listing,
malformed listing, listing with no accepted keys or scan exception returns static
ScheduleRefused; failure is NOT cached, so the next call retries. A successful
listing remains cached even if a later requested key is not listed.
Reload/restart is needed to refresh the listing after host tzdata/TZPATH changes.
This is not a synchronized multiworker cache or a guarantee that concurrent first
calls scan only once; sequential validation uses one successful scan. The actual
ZoneInfo lookup is still required and may fail if a listed file is unusable.

Geo and BRICS settings use this same rule. local_clock now applies it even to
hand-built plan dictionaries with the expected scope; other prepared-plan fields
are still trusted as before, so this is not full forged-plan validation.
No return shape, weekday canonicalization, clock parsing, DST calculation,
profile selection, timer or caller is changed. No legacy scheduler is run.

205 source, tests and doc stay byte-unchanged. Its call into profile_plan inherits
the widened refusal. Its own three-key check remains redundant and harmless.
Its source provenance/calculation limitations still apply. Item25 remains open
until caller/engine/profile decisions and activation gates are reviewed. No
AppsScript/SMTP/collector/DB/live effect or201c change is introduced.

Tests add five methods to unit175: both profiles' exact/prefix refusals and
legitimate positives, direct local_clock refusal, cache count in both deny-first
and accept-first order, scan empty/raise then retry, and absent legitimate alias
fail-closed behavior. Tests reset/restore the per-process cache so mocks do not
depend on order. right/UTC is refused even if a mocked listing contains it.
Positives include UTC, Asia/Calcutta, Asia/Kolkata, America/New_York, US/Eastern,
GMT, Zulu, UCT, Etc/GMT+5 and EST5EDT on the tested host. Their presence is not a
claim that every host supplies them. Existing unit175 and all205 tests rerun.

The unchanged205 doc sentence "Unit175 alone still accepts those keys; its
independent follow-up remains open" is superseded by206's shared key validation.

<!-- END-ORIGINAL-DOC -->


<a id="doc-144"></a>

### Reference: `integration/SCROLL186.md`

<!-- ORIGINAL-DOC {"bytes":2161,"path":"integration/SCROLL186.md","sha256":"bb1e02d57a8df0f2b976debc3d2726041f23d11b03d965c777a5ff9ec8a590e8"} -->
# Geo feed scroll loading (source only)

The whole-store pager185 must be wired behind its default-OFF flag. Server HTML
emits a true marker only for that adapter; otherwise existing /api/news loaded100
mode stays unchanged. No UI request can turn a reader flag on. New module is same
origin and added to existing approved static asset allowlist. No new live hosts.

Scroll near the bottom requests25 more, with Load more as keyboard/manual fallback.
No refresh timer/polling. Sequential requests only; filter/sort/refresh aborts and
invalidates old replies before JSON/render. Leaving Geo cancels the old generation.
Empty filtered scan with cursor is not EOF: button can continue. EOF stops loading.
409/429/other errors pause; already visible cards remain. Manual refresh starts
again. Network abort doesn't close the backend stream immediately:185expiry reclaims
it. Repeated fast resets may hit16streams/429 until expiry; no silent retry loops.

Live DOM limited200cards with removal notice and height compensation. This is a
DISPLAY WINDOW, not a traversal cap. Earlier cards are unavailable for backscroll;
refresh begins again. No all21kRAM/DOMload. Browser position may shift for late font
changes/margin collapse; no claim of pixel-perfect virtual-list caching. No total
count fabricated. Raw-source sort/mutable-read meaning comes from185API. Existing
summary charts/exportCSV remain latest100 sample, not full database summaries.

Existing safe card rendering uses textContent/validated URLs. Controller checks
public response scope, mutable-read marker, ≤25items and43char opaque tokens;
source data still governed by185sanitizer. Public Finder actions remain suppressed
by existing serving transform. HOME Geo layout/theme/navigation stays intact.

Tests: pureJS sequential/abort/stale/EOF/empty/error/schema paths; server markers,
OFF/default/public static module routes; local Chrome fixture scroll beyond100,
200card trim,390px no overflow,409preserves cards,refresh reset,tab-switch stale.
Screenshots of desktop/mobile/expired states inspected. This is fixture evidence,
not a live Mongo/index/worker-route or production performance claim.

<!-- END-ORIGINAL-DOC -->


<a id="doc-145"></a>

### Reference: `integration/SENDER-SCOPE222.md`

<!-- ORIGINAL-DOC {"bytes":3053,"path":"integration/SENDER-SCOPE222.md","sha256":"52cb6b9d4d5b022f2bdb2c73d58bacdaf848a2c37d69054a4b5aa7d3148a9f12"} -->
# 222: supplied sender-inclusive scope DATA only

NAMED sender-binding BLOCKER is prepared, NOT resolved. No consumer checks this
value against the real sender.212/219/bridge do not consume222; sender change is
STILL invisible to212logicalchannel. ledger_wired/bridge_wiredFalse. No sender or
recipient list provided or approved by owner. No default sender/autofill/Session
or effective-user lookup. Bridge sender is ONLY Session.getEffectiveUser().getEmail()
.trim().toLowerCase();222neverclaims supplied sender matches that real identity.

DefaultOFF before argument/import access. ON accepts one exactASCIIstr sender<=254
with213legacyfullmatchgrammar, and calls real220for suppliedrecipientlist. No
recipient grammar copied here. Refusal may reject validRFCaddresses; acceptance
isn't validity/deliverability (legacy regex accepts a@b..com). No trim/aliases/DNS.
Sender equal to a recipient is allowed; separate fields, no cross-field dedupe.

220/222refuse whitespace. Realbridge trims sender and each comma-split recipient;
'a@example.invalid, B@example.invalid' works inbridge, raw secondaddresswithspace
refuses220/222.222inputs must already be normalized addresses; future wiring must
apply the same trim rule before calling220, with owner-reviewed address selection.
Wholeaddresslowercase includinglocalpart is an explicitpolicyowneracceptancebefore
use; realmailboxes may treatlocalpartcaseassensitive. Sortedrecipientpolicy220.

Sender fingerprint: canonical sorted-key/no-spaces/ASCII JSON sha256 of closed
{schema:email_sender_fingerprint222_v1,domain:email.sender222,sender_lower:loweraddress}.
Scope fingerprint: samecanonicalsha256 of closed
{schema:email_sender_recipient_scope222_v1,sender_fingerprint,recipient_set_fingerprint}.
220recipientfingerprint unchanged. Newhashes NOTlegacybridgeMAIL_V1_CHANNEL, no
replacement for212logicalchannel/219binding. Realbridgelegacyhash is JSON.stringify
{sender,recipients} in THAT insertion order (senderfirst), lower/sort/trim; no sorted
keys. Test executes realbridge in NodeVM ONLYuntil digest, no lock/send/request.
Module never computes/returnsbridgevalue. Sender changesnewscopehash, not220fp.

Closed output3hashes/policy/note/Falseflags only, no addresses/count/name/rawlists.
Hashes NOTprivacy/anonymity: candidate addresslists can guesssenderhash and test
recipientsets. Don't logfingerprintswithaddresses. Fixedrefusal no upstreammessage,
cause/context. No words/nonce/content binding, authority/provenance/effectiveidentity.
History inheritance and exclusions on sender orrecipientchange needseparateowner
decision; no automaticnewchannel/historymigration/inheritedexclusions.

No DB/check/read/create/store/send/ledger/productionedge/property/env/deployment,
activation/triggers/cutover/mount/selection. AppsScriptselected/SMTPfallbackheld,
217held/201cwriteheld. Laterledgerunitmustconsumevalue andcheckagainstrealselected
rail/effectivesenderandstoredbinding. Otherhistory/exclusionauthority/provenance/
durablebody/recipientswordsapprovalopen. Config DATA only, allflagsFalse.

<!-- END-ORIGINAL-DOC -->


<a id="doc-146"></a>

### Reference: `integration/SHIPS226.md`

<!-- ORIGINAL-DOC {"bytes":3492,"path":"integration/SHIPS226.md","sha256":"e6478272b1a49bfba58ffb6cb423ad5e6ba4773fe04a0311a6213e002cafc7fc"} -->
# 226: Finder supplied ship response presentation

Real source parity work in the unselected 198d account panel: all 42 static port
choices and a bounded vessel table, with the existing bounded raw JSON retained.
This adds no mount, asset serving or activation. Own-key original files untouched.
Pins: preserved merged src/app.js f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91;
proxy.js dc6a77bd88d294a84c012d9e6928fb24ed5e8b3504877f7dcf13950829e0869c.
Live upstream Finder was also read, but is a DIFFERENT checkout; those upstream
hashes are not the test pins. Audit includes credential-free indexed excerpts.

Options come from indexed proxy AIS_PORTS and AIS_PORTS_WORLD, never response
names. Tests require exact 42-code and name equality and connector PORTS equality.
Supplied response requires every static port exactly once with matching name and
bounded integer count. Port counts are whole-fleet per-port values regardless
of filter, not selected count. They are neither summed nor displayed as fleet.
Headline count is matching vessels before the upstream 150-row slice: show
"Showing X supplied rows; source reported Y", not a current coverage claim.

Strict closed success shape only: ok True, bool warming/stalled, canonical ISO
milliseconds timestamp ending Z, count 0..6000, exactly 42 ports and <=150 vessels.
MMSI is a 9-ASCII-digit STRING: indexed aisUpsert uses String, not a number.
Text fields may be null or strings <=120; controls, bidi overrides and invisible
ZWSP are refused. Speed finite 0..102.3 knots or null, latitude -90..90 and longitude
-180..180 are finite non-null numbers. Seen seconds exact integer 0..31536000
(one year); bool is not number. Unknown shapes or limits fall back to raw JSON.
Bounds are presentation rules, not proof the upstream enforces them. No rows are
silently dropped. ETA is literal "as reported". Timestamp is displayed literally,
not toLocaleTimeString, no calculated "ago" or local clock/freshness assertion.
Coordinates validated but not shown; no maps or links. Empty says "Supplied
response has no vessels". Warming/stalled are as reported, not freshness proof.

Dynamic text uses textContent only. Hostile HTML remains literal. Coverage text
is the exact original paintShips warning: coastal volunteer AIS, crew-entered
ETA/destination may be stale, not for navigation. Its "Free data" wording is
preserved original copy, not independently verified current entitlement.

Only a completed success-shaped body becomes a table. Errors, holds, replay,
401/403 and sign-out behavior are unchanged. The raw bounded pre remains visible.
The view triggers no request. Port selection alone never requests. A click uses
198d's existing POST account/nonce broker route, which causes upstream GET /ships.
Original proxy GET requires app token and read limits; no new path added here.
Unlike original Finder's 60-second polling, 90-second abort and automatic retry,
198d keeps single-click, 25-second deadline, no polling or retry. No credentials,
provider secrets, model catalog, backend, DB or runtime changes.

Synthetic browser fixtures only: 320/390 widths, 150 long-name rows, internal
horizontal table scrolling, keyboard dropdown, malformed fallback and client
hold states. No real accounts or external requests. All live gates remain open.

2026-10-10: 228 supersedes current source/snapshot pins and popup behavior. The observations and source hashes above remain historical BEFORE evidence. See REPORT228.md.

<!-- END-ORIGINAL-DOC -->


<a id="doc-147"></a>

### Reference: `integration/SINGLE_DB_PLAN_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2301,"path":"integration/SINGLE_DB_PLAN_LIMITS.md","sha256":"59f843ef877dd8cafc0613c1184024b21df692de01b6990d5cca6d232f080ddb"} -->
# One-database mapping preparation

Historical/direct-adapter scope: this describes SingleDatabasePlan and the
separate two-project compose_single_database seam, not the later Geo-only
private_router. Current selected Geo-only read factory and separate events
composition are described in FEATURE_STATUS.md and GEO_EVENTS_COMPOSITION_LIMITS.md.
This seam remains unwired; do not read its old wiring limits as global status.

SingleDatabasePlan is an offline caller-supplied label/map fixture. It does not
connect to MongoDB or change runtime.compose. The selected existing Geo database
will be the eventual destination, but its actual database/collection names,
ownership, schema and indexes must be verified before configuring real reads
or writes. No label is inferred from legacy defaults.

Two distinct project article maps model two separate collections in one DB.
This preserves exact-URL versus hash identity semantics. Old separate DB and
its records remain untouched. No migration, index creation, dedupe update or
alert delivery occurs. Live writer and cutover remain separate approvals.

Runtime currently supports the preserved two-project read configuration. This
new fixture does not replace it or declare it safe to point both projects at
one articles collection. Single-DB runtime wiring remains unfinished.

single_db_runtime.compose_single_database is now a separate, unwired preview
composition seam. It takes one explicit injected client factory, one URI and a
reviewed plan, retaining separate project collections and private access gates.
There is no default MongoClient or private_router wiring. It can perform reads
if deliberately wired and enabled later; current tests inject fake clients.
No claim is made that arbitrary caller factories are effect-free. The factory
is trusted composition code, not untrusted config/data. Mapping failures close
the created client. No writes/index creation/migration/delivery are added.

Factory failures are redacted without original host/URI error text. None
clients fail explicitly; ordinary mapping/cleanup errors are contained. Only
Exception is caught, not process interruption/BaseException. Real wiring must
use a read-only Atlas user for preview reads, not an existing write credential.
No live connection was made by these tests.

<!-- END-ORIGINAL-DOC -->


<a id="doc-148"></a>

### Reference: `integration/SMTP-CALLER213.md`

<!-- ORIGINAL-DOC {"bytes":6363,"path":"integration/SMTP-CALLER213.md","sha256":"80a09d9da2e3d2b7348962c65b91cfbe9bed176934c74d290c7a76873f29e4c3"} -->
# 213: unselected 204 -> 174 closure-construction caller

This is source-only preparation, not SMTP activation, mail wiring completion or
item24 closure. Apps Script stays selected; SMTP fallback stays held. Existing
174/204 modules, original legacy BRICS direct sender and mailv1/212/201 production
composition are unchanged. No route, environment, client, timer, retry, ledger,
receipt, marking, resolution, scheduling or send identity is added or chosen.

build_sender(enabled=False, **arguments) returns (None, static metadata):
selected=False, prepared_not_sent=False, state=disabled,
selected_rail=apps_script, smtp_fallback_held=True. OFF touches no settings,
credential/address/capability argument and imports neither174 nor204; extra or
missing arguments are irrelevant OFF. enabled must be an exact bool.

Enabled construction requires exactly settings/user/password/mail_from/mail_to.
settings is an exact built-in dict with exact built-in str keys and scalar
str/int values;204 owns its closed keys and profile/port/host/mode/timeout rules.
Subclass dict/list/str/scalars are refused, not passed to permissive174 checks.
Missing/extra arguments and unknown204keys refuse with fixed text. No defaults
come from environment. The adapter passes an independent settings dict and copy
of the recipient list through actual204binding_data -> actual174smtp_sender.
Geo default465/implicit_tls; BRICS default587/requiredSTARTTLS. Explicit reviewed
465/implicit_tls or587/starttls pairs accepted for either profile; mismatched
pairs refuse before closure creation. No arbitrary sender factory is accepted.

username is exact str,1..320 characters, ASCII0x21..0x7E (no spaces). Password is
exact str,1..1024 characters, ASCII0x20..0x7E (spaces preserved literally).
Non-ASCII passwords are REFUSED, never altered. This prevents smtplib.login's
ASCII encoding error from exposing a secret character/position inside send.
No normalization/stripping of credentials occurs. No credential is logged,
printed, returned in metadata, repr, exception or exception chain.

mail_from is exactASCIIstr <=254 matching the legacy address grammar with
FULLMATCH. mail_to is an exactlist of1..20 exactstr addresses with the same
fullmatch/cap; comma-joined strings/tuples refuse. Trailing newline, leading
space, embeddedTAB, Unicode and case-insensitive duplicates refuse. This is a
closed legacy grammar, not universal RFC mailbox support or proof of ownership.
Subject/body are not prevalidated/authored by213, they stay174-owned on future
call. A caller still needs approved sender/recipient/final words together.

Enabled build returns (wrapped174send_callable, static metadata):
selected=False, prepared_not_sent=True, state=prepared_capability_not_selected,
selected_rail=apps_script, smtp_fallback_held=True. The CALLABLE IS A REAL SEND
CAPABILITY once built, even though metadata says not selected. Building it makes
no socket, DNS, TLS context or send. A future selected/authorized caller could
invoke it, so OFF/source-only labels are not a capability-security barrier.
No current production/mailv1/201/ledger module imports smtp_caller213; AST import
edge tests verify this. Import itself has no network/env/context/effect.

All204/174construction and future174send exceptions are replaced by fixed
CallerRefused('SMTP caller refused') raised fromNone OUTSIDE except blocks, so
__cause__ and __context__ carry no upstream credential/settings fragments.
This intentionally replaces174DeliveryError with the caller's fixed refusal;
it is NOT a safe resend signal. Success returns the original174result (None).
Neither None nor refusal is used to acknowledge any receipt in this unit.

## Transport uncertainty, unchanged174

174 uses ssl.create_default_context with certificate/hostname verification.
465 usesSMTP_SSL;587 usesSMTP thenEHLO/STARTTLS/EHLO/login/sendmail. Missing or
refusedSTARTTLS fails BEFORE credentials and send, never plaintext fallback.
Construction verifies config only, not DNS/private-host safety, realserver
compatibility, credentials, quota or actual intended recipient. Those are
future activation decisions;213does not turn an injected hostname into authority.

174 discards sendmail's per-recipient refusal dictionary. When SOME recipients
are refused, sendmail may return that dictionary rather than raising. Therefore
174's None return does NOT prove all-recipient acceptance or delivery. When ALL
are refused SMTPRecipientsRefused normally raises. Connection context exit sends
QUIT; a QUIT error AFTER send acceptance may raise SMTPException and174maps it
toDeliveryError. Thus DeliveryError/213CallerRefused also does NOT prove unsent.
Future212-ledger caller MUST treat every error-after-start as POSSIBLY SENT,
leave started held, and never infer operator_resolved_unsent from DeliveryError.
No retry/fallback/ack/mark is added and174is deliberately unchanged. No email-sent
or independently verified delivery claim is made here.

## Grounding and tests

Actual live current integration/geonews_digest/delivery.py matched landedsource
SHA256527be6ca3a1a42d3e384195f57cfd899940f84f0f72fc25c3a1f7ea9a46985e1.
OriginalGeo reports/email_report.py SHA25630d7552def0e9d56f8981f25b3d81ed3475bcc354971aea304a30e6f7d583688
andBRICS- reports/email_report.py6582d81d184e2c18842f1507d7e46042514c9d0cfbfea7e1202ce8bf1218ac65
were read live during212grounding: GeoSSL465 vsBRICSSTARTTLS587, notexecuted.
CPython3.10.12 smtplib login/sendmail/context-exit semantics motivate ASCII
credentials and uncertainty caveats; source inspected, no realSMTPcalled.

11newoffline tests plus204/174 (25total): real204->174profiledefaults andexplicit
pairs with mockedSMTP, exacthost/port/timeout/contexttype andverifiedTLS/order,
STARTTLSnot-supported/error beforelogin, mismatchbeforefactory, credentialcaps/
ASCII/nonASCIIcanary never174, addressfullmatch/newline/TAB/duplicates/21/255cap,
exactsubtypes/keys, exceptionchain/refusal/repr, OFFhostileargs/importtrap,
moduleimport/buildsocketDNScontexttraps/noenvread, copyindependence, partial
recipient refusalNone andQUITerrorafteracceptance, ASTnocurrentimportedge.
MockSMTPcalls are tests, not realnetwork/email effects. No current sender is
wired. Remaining: realcaller/212receipt/authscope/legacyBRICSexclusion/205schedule/
AppsScriptbridge/DBhistory+activation. SMTPfallbackremainsheld,201cstillheld.

<!-- END-ORIGINAL-DOC -->


<a id="doc-149"></a>

### Reference: `integration/SMTP-CONFIG204.md`

<!-- ORIGINAL-DOC {"bytes":5509,"path":"integration/SMTP-CONFIG204.md","sha256":"5673f2f072edca5682c9118c13edf8010efa75616bd5422aaf84f40ea40f5cbd"} -->
# 204: inert legacy SMTP profile configuration adapter

This unit adds `smtp_config204.profile_plan(settings)` and
`binding_data(settings)`. Neither function constructs a sender, TLS context,
connection or capability. No caller uses this adapter yet. AppsScript remains
selected; SMTP fallback and activation remain held. No environment reads,
credential handling, timers, DB writes or sends are introduced.

## Closed input and output

Input is an exact built-in dict. Only `profile`, `host`, `port`, `mode`,
`timeout` keys are accepted. Unknown keys are refused, including credential,
address, environment, enable and TLS weakening options. Profile is exactly
`geo` or `brics`. No normalization, aliases or case folding are applied.
Missing means a missing key, not None or an empty value. Host is required.

| Port | Mode | Outcome |
| --- | --- | --- |
| absent | absent | pinned profile default |
| present | absent | refuse |
| absent | present | refuse |
| present | present | unit174 pair validation |

Values explicitly equal to defaults are accepted as an explicit pair.
Geo defaults to implicit TLS/465; BRICS defaults to required STARTTLS/587.
The two reviewed pairs are accepted for either profile when explicitly set.
Ports accept exact built-in int or canonical ASCII nonzero decimal str,
1..65535. No bool, float, whitespace, leading zero, sign or Unicode digits.
Unit174 then limits ports to the reviewed 465/587 pairs.

Host is an ASCII DNS-style hostname (single labels such as localhost allowed),
1..253 characters, labels 1..63 characters, alphanumeric edges and internal
hyphens only. No trailing dot, scheme, userinfo, port, path, whitespace,
controls or IDN Unicode. IP literals and all-numeric dotted spellings are
refused, including noncanonical IPv4. No DNS lookup is done. Timeout is an
exact int, 1..30 seconds, default 30; bool and float are refused.

"Redacted settings" here means secret-free by input exclusion, not masking:
the output contains only validated profile, hostname, TLS mode, port and
timeout, provenance and fixed policy/hold metadata. Hostnames are returned
unchanged and may be private; output is not claimed safe for public logging.
Exceptions contain only static text, never supplied keys or values. The module
prints nothing. Invalid profiles, including secret-looking values, are refused.
Only exact built-in scalar values are accepted before the input is deep-copied;
no custom deepcopy hooks are run. Results are independent plain dictionaries.
Binding returns only future scalar sender arguments. It supplies no credentials,
addresses or enabled flag, and must not be described as making legacy code safe.

## Pinned source provenance

Original files read from GitHub default branches on 2026-10-09. SHA256 values
below hash the exact UTF-8 file content returned, not a JSON response. These
are source snapshots, not a claim that originals will remain unchanged.

- push2006/geonews `config.py`, lines 50-51: host smtp.gmail.com, port465.
  SHA256 `f7fbf007954c6918fbe2e402863fa29f597fe5d5cb4d60d1001deca8896b21f3`.
- push2006/geonews `reports/email_report.py`, line170: SMTP_SSL with context.
  SHA256 `30d7552def0e9d56f8981f25b3d81ed3475bcc354971aea304a30e6f7d583688`.
- push2006/BRICS- `config.py`, lines29-30: host smtp.gmail.com, port587.
  SHA256 `2419339566c5946dd0daeae7147eba7a49dffdd379b3c34769d6d62860afc82d`.
- push2006/BRICS- `reports/email_report.py`, lines59-60: SMTP then starttls.
  SHA256 `6582d81d184e2c18842f1507d7e46042514c9d0cfbfea7e1202ce8bf1218ac65`.

The adapter does not watch originals. Later upstream default changes are
unnoticed. Tests pin both constants; no live configuration imports are used.

## TLS safety and tests

Unit174 transport_plan supplies hostname verification, no plaintext fallback,
AppsScript-not-replaced and runtime_activation=False. No weaker option exists
in this adapter. Existing reviewed delivery code creates a default verified
SSL context. STARTTLS is called before credentials; an unsupported STARTTLS
raises and prevents login/send, never falling back to plaintext. A mock-only
unit204 test exercises that refusal using returned binding data. This is a
source contract check, not a real-server compatibility or send approval.

Tests cover the complete mixed table, pinned defaults, explicit overrides,
pair refusal, strict ports/modes/hosts/timeouts, closed keys, canary-secret
non-echo, independent output and deep copy, AST import allowlist and patched
socket/getaddrinfo refusal during import and both functions. No network test
or SMTP effect is needed. Unit174 tests run alongside this unit.

## Not closed

Per the snapshot and smtplib source, legacy BRICS STARTTLS calls
server.starttls() without a context (email_report.py line60), falling back to
ssl._create_stdlib_context without certificate/hostname verification; this
weaker legacy path stays live outside this unit as a standing hazard for the
owner's BRICS decision, while landed174 uses create_default_context with
verification (the original BRICS code was not run).

BRICS direct send() remains live code outside this contract. No runtime caller
uses the adapter. Item24 stays open until a reviewed runtime caller and BRICS
exclusion decision exist. Original configurations/callers are unchanged.
No legacy path is made safe by this adapter. SMTP fallback remains unselected
and held; no environment activation, role changes, cutover or live effects.
201c remains held. Source audit and indexed LAND review are separate gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-150"></a>

### Reference: `integration/SOURCE_HEALTH_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1642,"path":"integration/SOURCE_HEALTH_LIMITS.md","sha256":"b2f2d1bcb3b0368ced209b49a84eb348e2e3926a355894c98177d01eee32c2a1"} -->
# Source-check observations

SourceHealthSnapshot accepts caller-supplied captured source checks, not a live
collector or status endpoint. No callbacks, requests, storage clients or probes
are added. The private API accepts only this exact snapshot type. Unwired,
unavailable and verified-empty states are different. No current health is
claimed from a stored successful check.

The panel shows observation age, per-source check time, recorded status, fetched
count and safe error-code enums. Raw provider error strings and URLs are not
exposed; they may contain credentials or request data. Source names are rendered
as literal text. A status is historical even when its label is "ok".

Up to100 of1000 supplied source checks are shown; truncation is disclosed.
Counts are source checks, not unique source identities. Only supplied known
project identifiers are accepted; no production source mapping is inferred.
Future observations/checks fail unavailable rather than appearing fresh.
No universal freshness threshold is invented; age is explicit. Manual refresh
rereads the supplied snapshot only. Automatic polling remains disabled.

Preview source checks will remain unwired until a reviewed observation reader
and source ownership/collection schedule are established. This is display prep,
not permission to run a source, change its policy, or write the database.

Unwired returns HTTP200 with state=source_health_unwired, not a successful
empty snapshot. UI displays unknown health, not zero sources. Error codes on
recorded ok checks are rejected as contradictory. Exact string dict keys
prevent subclass-key hooks at this boundary.

<!-- END-ORIGINAL-DOC -->


<a id="doc-151"></a>

### Reference: `integration/STREAM_DISK_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2902,"path":"integration/STREAM_DISK_LIMITS.md","sha256":"5ce37a8701a04fb68e533af1137d0dfba393a6d5a89f42c3aeb551cc1002f875"} -->
# Explicit local stream file CAS, no activation

DiskStreams needs an explicit reviewed absolute path to an existing operator-
prepared file in an owned private directory. No default/live path, mkdir,
initial config, route, environment selection, network or status polling. This
increment tests temporary directories only. Render ephemeral storage is NOT
claimed durable: a persistent volume, path ownership, backups and permissions
must be verified before activation. It never changes the user's live config.

Linux nonblocking flock on an adjacent 0600 lock file serializes cooperative
writers on one host. Lock covers load, SHA expected revision, reviewed revise
transform, same-directory 0600 temporary file, fsync, atomic replace and parent
fsync. Busy and stale requests are refused, never silently overwrite. Read
snapshot also takes lock. Existing original parser/grammar and expected-revision
transform reused. Changed YAML loses comments/format, reported in result.

Bounded 16KiB regular single-link owner-only file; O_NOFOLLOW refuses final
symlink. Constructor checks parent chain and private immediate directory. This
is not hostile shared-directory safe: parent replacement/rogue noncooperative
writers/lock deletion/path races can bypass cooperative protocol. No distributed
or multi-host filesystem guarantee. A no-op preserves raw bytes; its result says
fsync completed local only, but does not perform a new sync because no write.

Pre-replace failures leave old file untouched and remove temp. After replace,
fsync failure is uncertain: new bytes may be present but durable-on-crash not
proved, no retry. Caller must read back under separate authority if needed.
Actual power loss/filesystem crash/NFS/Render volume were not tested. Cleanup
and descriptor close best-effort, no hostile syscall sandbox.

9 tests local and extracted: read/write/restart, permission, stale revision,
replace failure/temp cleanup, directory fsync uncertainty, symlink/unsafe mode,
invalid transform, busy lock, no-op and two-process same-revision race.
Repro python -m unittest tests.test_stream_disk -v with PyYAML 6.0.2 and existing
integration tree. Stream availability remains not_checked; no UI or accounts
wiring. This is storage preparation, not the finished merged application.

Review SAFE for trusted-local-operator scope (9/9). Busy and invalid source
both return the same coarse unavailable error, intentionally indistinguishable.
The adjacent .lock file persists and may be created even if the source later
fails validation. Lock identity is not tied to data-file inode; all cooperating
writers must use the same path and leave its lock file in place. External
replacement/deletion is outside this trusted-directory scope. BaseException
inside read/update is converted after cleanup; after replace it is uncertain,
including KeyboardInterrupt.10 final local tests include that regression.

<!-- END-ORIGINAL-DOC -->


<a id="doc-152"></a>

### Reference: `integration/STREAM_REVISION_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3513,"path":"integration/STREAM_REVISION_LIMITS.md","sha256":"ac5c8731800995d24ea21e32795784ab6aae03da4d2f7890eeaf2f8490d110e4"} -->
# Supplied stream bytes expected-revision contract

Pure transform only. No filesystem writer, default config path, original module import, network, env, database or live activation. SHA256 exact supplied bytes, lowercase64hex expectedrevision, hmac constant-time comparison. This is expected-revision CHECK, not atomic compare-and-swap or durable/persisted mutation. Caller must make eventual read/check/write atomic with a separately reviewed writer.

Original video.py has process-local _STREAMS_LOCK around add/remove, but no cross-process lock/revision check/atomic fsync replace. Originals unchanged and _write_raw_streams not imported/called. Add appends to end, remove preserves survivors/order. Merged strict parser rejects duplicate casefold names (including Straße/STRASSE); remove on a colliding source harderrors, never picks one. A single Straße can be removed by STRASSE under casefold, unlike original lower(); explicit deviation. İ/i+combiningdot lower/casefold equal tested. Strict YouTube11chargrammar/canonicalURLs, labels80/rows20/bytes16KiB are existing fixture safety differences from permissive original.

Input byte size checked first, strictUTF8, BOM/NUL rejected. Existing reviewed bounded StrictLoader SafeLoader-derived parser rejects anchors/aliases/merge keys/tags/duplicates/multidoc/unknown fields, scalarstrstoredfields only. Original envelope is mapping streams:list of mappings, not a top-level bare list (source shape retained). Fixed aware observationclock validates parser only, not live observation. Expectedhash checked before parsing/noop. Noop remove returns exactbytes includingcomments/format. Effective change deterministic safe_dump sort_keysFalse/allow_unicodeTrue/blockstyle/indent2/width1000/LF/noexplicitdocmarkers, reparses semantic equality, closedstoredfields only. comments/format loss explicittrue on change; no preservation claim. Hash over emittedbytes, availabilitynotchecked/persistenceFalse.

Fixed publicerrors no inputecho, but Pythonexceptioncontext may retain originalvalidationdetails; do not introspect logs. Known RevisionErrorconflict exacttext. Future sourcepath/symlink/filepermissions/crossworkerlock/fsync/temp/dirfsync/volume/crashrecovery/undo and userlivewriteapproval unresolved. Capturedpanel/RAMapp unchanged, no route/UIchange or sourcefilewrite. Semanticroundtrip not durability or playeravailability.

Configured repo repro python3 -m unittest tests.test_stream_revision.11tests deterministicroundtrip/addappend/original5rowsfidelity/noenrichedfields, exactnoop/checkmalformedconflict, strictYAML/UTF8/BOM/NUL/size/noecho, lower-vs-casefold/İ/collisionharderror, AST nofs/net/env/originalwriterimport. Bundle requires existing stream_config/brics_streams/youtube_links/PyYAML, not standalonefullrepo. PyYAML version output bytes should be pinned before deploying any writer.

Changed output also normalizes values under existing strict parser: strips label whitespace, empty country becomes Custom, URL video_id becomes bare11char ID, stray channel_id on video row dropped. Untouched row byte/value preservation is NOT claimed after a change; normalized semantic equality only. Exact11char bare IDs accepted, other arbitrary bare strings rejected. All3module ASTguard importallowlist permits urllib.parse (pure parsing only), bans urllib.request/subprocess/os/fs/eval/exec/import original writer. Caller must not log chained traceback/__context__ because fixederrors suppressdisplaychain but originalexceptioncontext retained.

<!-- END-ORIGINAL-DOC -->


<a id="doc-153"></a>

### Reference: `integration/SUPPLIED_FEED_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3611,"path":"integration/SUPPLIED_FEED_FIXTURE_LIMITS.md","sha256":"4e3f0335e2307cb30396d1d461699fa9c075a4a3880a48b404ff9b47b21f2e79"} -->
# Supplied parsed-entry feed selection

Private isolated function research, not HTTP/XML/feedparser/provider health.
No original RSS/classifier/config module import, requests/feedparser/thread/env/
DB/Telegram/send. AST only exact pinned _fetch_feed/strip_html/parse_date, explicit
names/attributes; source literal _HEADERS/_ENTITY_MAP and regex expression read
from pinned sources. Tiny Exception/print sink builtins; sink drops raw formatted
source/exception text, returns fixed supplied_source_error code only. Pins are
reviewed-code drift controls, not hostile-code or loaded-object authentication.

One feed exact source/url/credibility tuple/list; exact supplied parsed entries
<=100, closed optional title/link/summary/description/published/updated strings,
no unknown fields or arbitrary objects/callbacks/exceptions. Strings<=10000,
feed scalar<=2000, incremental1MiB UTF8/5000nodes input; same separate output
budget. Invalid UTF8/scalar subclasses/config/date refuse before source execution.
Cutoff/fallback exact fixed-offset aware datetime with UTCyear1970..2100;
max_items exact1..100, timeout finite exact positive<=30. Timeout is only supplied
traced parameter, not a real deadline or external availability evidence.

Original slice BEFORE missing/old-entry filtering; title/link stripped; summary
absent falls back to description, present empty does not. Published absent falls
back to updated, present empty does not. Date equality cutoff accepted. Original
strip_html entities/whitespace retained. Output candidate keys/order unchanged,
no docs/IDs/emailed/save/backup references. URL text supplied, not authenticated
provider/feed identity or vetted safe destination. No source health assertion.

Dateutil version exactly2.9.0.post0. Internal parser facade supplies fixed UTCclock
as naive default for partial date/time components, a documented deterministic
DEVIATION from original real-current-date behavior. Empty date original now
fallback uses fixed clock. Malformed date/UnknownTimezoneWarning becomes fixed
fallback (unknown zone NOT verified UTC), no warning stderr; date_fallback_count
counts parser exceptions/unknown zones, not empty-string now fallback. Full
original date parser catches errors, so this is not parser authenticity proof.
Post-parse normalize only exact datetime with reviewed timezone/tzutc/tzoffset/
tzlocal concrete classes, preserve ISO/instant using fixed offset. Selected date
outside UTCrange refuses whole output. Dates filtered as old are not output and
not reported valid. Real timezone databases/ambiguous abbreviations unverified.

Declarative http_mode/parser_mode ok|error built into exact inert facades.
Opaque bytes handle maps to copied declarative entry list, not actual XML parse.
Errors return original empty candidate list with fixed coarse diagnostic; empty
ok is not healthy/completeness. Strict entry contract cannot trigger mid-loop
partial-source-error semantics, so partial-error parity is NOT claimed. Source
print suppressed; trace contains supplied URL/timeout, never credentials/config.
Caller input untouched, independent copied output rows, immutable dates reused.

10author focused PASS with independent original AST oracle and separate facades/
explicit clock policy; maxslice/filter/equality,absence/empty precedence,HTML,
naive/GMT/+0530/Z/partial/time-only/malformed/unknown-zone dates,source failures,
whole-input/hooks/UTF8/budget,selected-date bounds/drift/no new external imports.
No composition to80, real fetch/SSRF/timeout/XML-parser behavior or UI artifact.
Full configured suite and independent code review pending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-154"></a>

### Reference: `integration/SUPPLIED_FULLTEXT_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3639,"path":"integration/SUPPLIED_FULLTEXT_FIXTURE_LIMITS.md","sha256":"0921e7659ef804d821a502969ba4e021520d165e5bb5ecc917b2d11338d710d2"} -->
# Supplied-text enrichment preparation only

Separate private supplied-text fixture; no HTTP/source fetch, real extractor,
trafilatura import, thread, env/config/DB/log/Telegram/send/durable backup.
Pins RSS/extract exact bytes, inspect exact function definitions/nested process
with name/attribute allowlists; only tiny builtins len/list/Exception supplied.
No original module imports. Pinned64 document seam/dependencies run only after
complete input/output validation. Source pins/AST checks are reviewed drift
controls, NOT hostile-code sandbox or loaded-module authentication.

Original enrichment threshold strictly<200 characters. Nonempty provider result
is stripped, truncated to max_chars then'...' when longer, including replacing
with shorter text. Whitespace-only returns empty. Empty/error download skips
extract; empty/error extract retains original summary. Unavailable/disabled
zero calls. Opaque supplied download handle is URL, not downloadedHTML/parser
proof. Real requests/timeouts/SSRF/parser and live-provider semantics untested.

Declarative outcomes exact download=text|empty|error,extract=text|empty|error,
text bounded plain string. Nontext download requires empty extraction/text;
nontext extraction requires empty text. Missing requested or unused outcomes
reject before AST/provider execution. One supplied outcome per exactURL, but
repeated short-summary candidates call download/extract EACH time in order,
never cache/dedupe before enrichment. Trace is ordered calls+URL+occurrence;
no actual fetch/authenticity evidence or credential/config fields. Original64
then dedupes titles/classifies/prepares docs. Synthetic IDs, emailed/save/mark
receipts not created. Original empty Telegram placeholders retained, not sends.

Up to100 exact closed candidate records with title/url/source/summary/published/
credibility; fixed-offset exact aware datetime, UTC year1970..2100. Exact strings
<=10000,URL<=2000, title/URL already stripped. Exact category controls1..100 characters, <=20;
exact boolean enable/availability and positive exact max_chars<=9997 (output
<=10000 including ellipsis), finite threshold0<value<=1. These are narrower
than all possible original inputs, not blanket collector parity. Scalar and
container subclasses/hooks refused; no caller provider/executor/callback/store.
No caller overrides/unknown fields. UTC boundary checked before publication.

Snapshot and whole-batch validation before AST/provider/doc seam; cheap field
counts,5000nodes,1MiB aggregate UTF8 for inputs and separately combined returned
candidate/trace/doc output. Input and output each bounded, not combined1MiB.
Out-of-range/invalid UTF8/date/config/outcome or output growth refuses whole
composition, no partial published result. CPU/allocations remain bounded-input
research, not process timeouts or hostile memory isolation. Same output result
contains independent candidate/doc dictionaries; immutable date/string reused.
Returned text is private SUPPLIED data, not fetched/verified/lossless full article.
Stored original doc preview<=300; Telegram full-content preservation remains
unwired, neither silently dropped nor proved by this preparation.

11author focused tests include independent original AST oracle with separate
provider/executor mocks,199/200/201, repeats/order/isolation, disabled/unavailable,
empty/error/short/whitespace/Unicode strip/astral/exactlimit/ellipsis, aggregate
input/output growth, malformed whole batch/no hooks, drift and no newly imported
original/external modules. No HTML/mail/UI artifact, no visual readiness claim.
Full configured suite and independent code review pending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-155"></a>

### Reference: `integration/SUPPLIED_MULTI_FEED_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3109,"path":"integration/SUPPLIED_MULTI_FEED_LIMITS.md","sha256":"9c822dcf8bba27e0543efb0656dfc0b3e67efb033906515fc671630ac27f0120"} -->
# Ordered multi-supplied-feed preparation

Private supplied observations only, coverage_verified=false. No live complete
collector/HTTP/XML/threads/parser/provider/authenticity/health/fullarticle/store/
mail/Telegram/runtime proof. Original source and81/80/64 unchanged. Up to4 exact
ordered closed batch records with feed/entries/http_mode/parser_mode, <=100TOTAL
entries. Zero feeds labelledall_empty; duplicatefeeds explicitly allowed repeated
observations, never silently collapsed. Perfeed max_items slice beforefilter.
Globalflatten ->80enrichment ->original64classify/dedupe/filter/docs happens ONCE,
not82perfeed. Corroboration counts original matching records, not verified unique
independent sources; duplicated feed can increase it, retained original behavior.

Every batch/config/outcome snapshotted and validated beforefirst81call. Reuse82
private snapshot helper only, neverrunner. Exact category1..100,maxchars1..9997,
finite threshold/timeout,boolflags,datebounds,entry/outcomeshapes/UTF8 inclwhite
outcomeURLrefusal. Selectedoverlonglink>2000 remains whole80stage refusal, no
truncate/filter. Raw boundedcopies precedeaggregatecount, notzerowork guarantee.
Sharedraw1MiB/5000nodes acrossallfeeds/config/outcomes, separatefinalcombined
outputbudget beforepublication includesallselected/enriched/docs/traces/diagnostics/
wrapper. Tuplefeed converted tolist onlyforbudgetaccounting, notfeed normalization.

Trustedimports82/81/80/Budget/dateutil occur beforepinchecks, driftguards nothostile
sandbox/loadedobjectauthentication. Pin82helperfile,81/80/64/plain/originalRSS/
extract/classifier/dedupe beforestage1; versiondateutil2.9.0.post0. FixedUTCdefault
partialdateDEVIATION/unverifiedunknownzonefallback policyfrom81 retained. Future
supplieddates maypasscutoff; warninginterceptionprocess-local, notconcurrentproof.

Perfeedordinaldiagnostics only, statesdeclared_error/selected_empty/selected,
fixedcoarseerrors. Aggregatepartially_failed/all_failed/all_empty/selected, NEVER
healthy/current/complete/no relevant news. Failedfeeds contributezero, not hidden.
Globaloutcomes match ONLY selectedshortsummaryURLsenabled+available afteralllocal
selections; mixedsameURL successfulelsewherelegitimate, solelyfailedfilteredunused
refuseswhole. Disabled/unavailableexpectemptyoutcomes. Allfailed/emptywithnonempty
outcomesrefuse. No partialpublicresult, but reversibleselectionmayalreadyhaverun.
Enrichmentdisabled/unavailable/suppliedoutcomes statesdistinct; no send/markcount.
Traceperrepeatedshortcandidate, nocache; originaldocpreview<=300, noID/emailed/save/
receipt/sendenvelope. Independentcopiedselected/enriched/docs containers.

7authorfocusedPASS inclduplicateorder/corroboration/globaldedupe,zero/empty/oneall
errors/mixedsameURL,disabled/unavailable/unusedfiltered,maxslice,totalcap/malformed
laterfeedbeforefirststage,drift/config/narrowselectedlink,growth/alias. Independent
originaloracleexecutes ONLYcollectpureflatten/enrichment/classify/dedupe/doc
statements withdistinctinertmocks, neverstore/Telegrambody. Fullconfiguredand
independentcodereviewpending. NoUI/visualartifact.

<!-- END-ORIGINAL-DOC -->


<a id="doc-156"></a>

### Reference: `integration/SUPPLIED_PIPELINE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3260,"path":"integration/SUPPLIED_PIPELINE_LIMITS.md","sha256":"238ca2ecf7f44659fbdd2fb1391c24e8dccc0640186bb33054c682d6f1c761f1"} -->
# Supplied parsed entries -> supplied text -> original lightweight docs

Private isolated composition81->80->64, never live RSS/XML/request/extractor,
DB/mail/Telegram/HTTP runtime/callback/env activation. Pins81/80/Budget's file64/
RSS/extract/classifier/dedupe/plain helper before stage1, parser2.9.0.post0.
Trusted drift controls, not hostile-code sandbox or loaded-object authentication.
All source modules/seams unchanged. Original64 classifies/dedupes/filters and
stores<=300 preview only. Returned enriched text supplied, not fetched/verified/
lossless full article or durable backup. No IDs/emailed/save/claim/mark receipts.

Snapshot raw list/tuple/dict into exact inert copies before validation/stages;
closed optional entries and outcome fields, no arbitrary objects/scalar subclasses,
config normalization or callbacks. <=100entries/outcomes,20categories exact1..100,
maxchars1..9997,bool enable/availability,finite exact threshold/timeout limits,
feed/clock/maxitems requirements same81. Shared incremental1MiB/5000nodes raw
input includes wrapper/config/clocks. Aggregate counting occurs after bounded
raw container copies; this is not zero work before counting. Immutable strings/dates reused; private
Python convention not concurrent hostile-mutation or process isolation.

Malformed raw config/entry/outcome/error-with-outcomes refuses BEFORE stage1.
Outcome matching depends on selected URLs: missing/unused outcomes refuse AFTER
reversible stage1, before enrichment, with no partial result returned. Selected
record80 narrower boundary applied as whole-stage refusal (e.g.URL>2000), not
silently shortened/filtered or broad original parity. Empty selection+empty
outcomes labelled selected_empty; empty selection+nonempty outcomes refuses.
Declared source error skips80 entirely; any supplied outcomes in that case refuse.

State labels separate source declared_error/selected/selected_empty and enrichment
not_run/disabled/unavailable/supplied_outcomes_processed. Empty extraction/docs
not source healthy/current/no relevant news. Trace/counts reflect only supplied
stage semantics, not attempted real HTTP or authenticated source. Preserve81
fixedUTC partial-date/default deviation and unverified fallback policy; future
supplied dates can pass cutoff. Warning handling process-local research, not
concurrent isolation. Preserve80<200/repeated URL each call, no preenrichmentcache.
No send/mark authority from counts or successful offline result.

Final separate selected/enriched/doc dictionaries plus ordered traces, diagnostics,
count/notice wrapper counted in ONE combined output1MiB/5000node budget before
return, including independently copied redundant candidate records. No retained
whole stage result. Refusal publishes nothing; local source selection may already
have run. No real side effects. Input/output budgets separate, not combined1MiB.

8author focused PASS with independent originalAST pipeline oracle/separate mocks,
original document loop on independent copy; malformed preexecution/source drift,
sourceerrors/empty/disabled/unavailable,overlong selectedURL,missing/unused/repeats,
inputmutation/crossoutputalias/growth refusal. Full configured/code review pending.
No UI/HTML/mail artifact or visual readiness claim.

<!-- END-ORIGINAL-DOC -->


<a id="doc-157"></a>

### Reference: `integration/TARIFF_EVIDENCE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4503,"path":"integration/TARIFF_EVIDENCE_LIMITS.md","sha256":"f8ffc5f123be528079985a9eec9c05d206f5ccab7b42ca3b54ebb17c7059ce16"} -->
# Passive tariff-document evidence preview

Independently written. Injected supplied snapshot only; no fetch/clients, DB writes, timers, ingestion or delivery. Existing default-private guard applies to UI, API and asset. Default runtime has no snapshot and returns unwired, not an empty claim of complete coverage.

A strict row keeps jurisdiction, nomenclature/edition, numeric code strings, document ID, exact official HTTPS URL, publication date, multiple effective dates, short excerpt, conditions and candidate/document-reviewed state. Review timestamps cannot exceed capture. Source-host allowlist is link safety, not proof of source authorship, legal interpretation or review. No rates/current-law verification, inferred duty change or product/origin eligibility. Supplied document-review state is recorded input; it is not agent approval and never enables actions. All display text is literal textContent.

Code digits have no invented Finder scope. Existing exact HS/HSN news-to-Finder endpoint now displays its explicit mention reason in the country page. Finder existence/context still does not prove affected legal scope. No tariff record is matched to Finder automatically.

Empty lists mean no supplied records for that jurisdiction, not no tariff changes. Unwired and failed reads are separate. View cap100, input cap1000, codes100 per row. Current official-source legal-document ingestion, terms, snapshot persistence, polling and source-review workflow remain unconfigured. Supported host catalog starts with IN/US/EU, not worldwide coverage. Publication dates are not legal effective dates. No live notification rows shipped, only browser fixtures in tests.

Official route research:
https://www.cbic.gov.in/Customs-Notifications
https://www.indiabudget.gov.in/doc/cen/cus0326.pdf
https://www.usitc.gov/harmonized_tariff_information/modifications_to_hts
https://www.usitc.gov/harmonized_tariff_information/hts/archive/list
https://taxation-customs.ec.europa.eu/online-services/online-services-and-databases-customs/eu-customs-tariff-taric_en

## Strict supplied value boundary

Exact field shape and plain string/list/None values checked BEFORE copying.
Manual scalar/list copy prevents custom deepcopy hooks. No supplied objects,
subclasses or coercion. Per-scalar max2000chars prevalidation, codes100 x12chars,
effective dates20 x12chars, then existing semantic caps. Surrogates rejected
before encoding. Normalized compactUTF8 rows cumulatively <=2MB after all canonicalization,
right before appending each row. Budget is SUM OF ROW BYTES, excluding snapshot
envelope and row separators; not full response-size cap.
not a total interpreter/input-allocation bound. Input list <=1000 still applies.

Observation/review strings<=64, aware ISO, local+UTC years1970..2100. Exact
fixed datetime.timezone clock required in view; custom tzinfo/ZoneInfo rejected
before any hook. Timestamp acceptance depends on Python version. Output ISO
format remains existing format, no new legal-date or review-authority semantics.
Plain copies on returned views remain isolated. Review_state is supplied input,
not authenticated review or permission. Host catalog only safe link restriction.

Configured17tests PASS (9existing+8plain boundary). Eight new standalone tests
cover hook nonexecution, clock hooks, mutation isolation, scalar/time bounds
and aggregate bytes. Full route tests need configured merged dependencies.
No live sources/rates/credentials/client/API/store/activation/deploy changes.

List-element UTF8/surrogates checked before copying. Returned normalized rows
now use manual plain copies, not deepcopy. Internal Python state is trusted;
hostile mutation of private _items is outside this adapter contract.

Constructor uses plain_row only: exact dict and wrong field count reject
before key iteration or set allocation, including oversized wrong-schema dicts.

Residual limits: official_url does not reject every DEL/bidi/category-C codepoint
like text() does; hostname casing is accepted through parsed hostname and an
empty port may be accepted by the URL parser. Host restriction is not canonical
exact-string identity/authentication. Caller-owned lists may change between
validation/copy under hostile concurrent mutation; no snapshot lock supplied.
Private _items is reachable Python state; view plain_row revalidates its shape
but cannot authenticate tampered semantic values. Trusted in-process callers
required; no adversarial code isolation or concurrency-copy guarantee.

<!-- END-ORIGINAL-DOC -->


<a id="doc-158"></a>

### Reference: `integration/TELEGRAM_FORMAT_AUDIT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2427,"path":"integration/TELEGRAM_FORMAT_AUDIT_LIMITS.md","sha256":"6eed50f278590e0417c2301a19c9c302ef1c3a3b0dd78be11220f84ecef1217a"} -->
# Private explicitly synthetic original Telegram formatting audit

No delivery/sendready/API/bot/chatID/messageID/permalink/config/requests/import/
HTTP/store/Telegram effect. Complete originalsource pinned, extract ONLY two
formatter/batcher definitions and source literal3500; name/attributeallowlists,
tinylen/enumerate globals. Sourcepins trusteddriftguards, nothostilesandbox.
Nooriginalsendhelper/moduleimports; noUI/HTML/visualartifact.

synthetic=True required callerassertion, NOT provenanceverification/secretdetection.
Closed exact optionalformatterfields only, no privateextras/IDs/tokens/chat/session/
backupoverrides. Strings<=10000, finiteexactscore0..100,intcorroboration1..100.
Published absent/empty defaults retained, or exactawarefixedoffsetdatetime with
UTCyear1970..2100 convertedISO preservingoffset/instant. This isnarrower input
thanoriginal; no arbitrarycoercion/hooks. Rawnewline/controltext retained, nohidden
sanitize/clip/split. InvalidsurrogateUTF8 rejectedbeforeAST. Privateonly, never
feed83automaticdata or disclose callercontent. Embeddedsecretsnotdetected.

Input<=100records,1MiBUTF8/5000nodes; separatecombinedoutputbudget countsredundant
record/batchtexts/metrics/spans/notice/wrapper BEFOREpublication. Boundedcopies
precedecounting, notzeroallocations guarantee. Strings/datedata immutable; new
outputcontainers. Notice OUTSIDEoriginaltext so sourceparitymetrics remain exact.
Never callbatchready/safe/deliverable. ready_for_delivery alwaysfalse.

Metrics Pythoncodepoints,UTF8bytes,UTF16codeunits; surrogate refusalfirst.
Sourcepackingestimate=sum(len(record)+2); actualjoin=sumlen+8*(n-1).
Signedactual-estimate=6*n-8:one=-2,two=4. Source3500comparison estimates/actual
codepointsSEPARATE, notcurrentproviderpolicy/availability orverified4096rule.
Spancontiguous/nonempty/inbounds+orderedcoverexactlyallinput, text exact8char
separatorjoin. Spansformattingdiagnostics, notsent/archiveddeliverymapping.
SingleoversizedoriginalrecordflaggedUNSPLIT, noautomaticchange/truncation.

8authorfocusedPASS:defaults/empty/rawcontrol,Tamilastralmetrics,estimateequality/
oneover/multirecordcross3500,singleoversize,spans/order/repeats/isolation,published
conversion,privateextras/hooks/surrogatesbeforeAST,drift,outputgrowth; independent
originalASToracle againstseparatescope. Fullsuite+independentreviewpending.
FullcontentTelegrampreservation,eventualmessagepolicy/durablebackup remainopen.

<!-- END-ORIGINAL-DOC -->


<a id="doc-159"></a>

### Reference: `integration/TOKEN-REMOVAL196.md`

<!-- ORIGINAL-DOC {"bytes":930,"path":"integration/TOKEN-REMOVAL196.md","sha256":"23ebba422eea87f9edec350d8ad5444645e64ea9a994dd22658fde30e90ca476"} -->
# Remove public shared proxy credential, fail closed

Remove publichardcodedtokenandall4x-app-tokeninjectionpathsfromsrc/app.js,
index.html,offline.html. No publicreplacementtoken. AI_PROXY_URL/AIS_PROXY_URL
empty, low-level no-keyGemini/Groq/OpenAI provider paths refuseBEFOREfetch with
fixedBuilt-inproxyaccessisunavailable. Shipsheldbeforefetch/timers,retrybutton
notdisplayedforheldstate. Built-inproxyfallback disabled;ownproviderkeypaths
unchanged andmockedVMdirectGroqBearerflowpassed. Proxy.jsAPP_SECRET/auth/CORS
unchanged, public107networkOFF unchanged. No provider/credentialtest orrotation.
Standalonelegacybuilt-inAI/ships unavailablebydesign afterdeployment. Historical
credentialmayremaininGitandowner/runtime rotationreviewneeded;nohistoryrewrite.
Offline hashpin/served-copy token-removal seam updated, remainsno-network/keyread.
ActualmobilepixelsheldAI/shipsinspected,noproxyrequests(noexternalrequestallowed).

<!-- END-ORIGINAL-DOC -->


<a id="doc-160"></a>

### Reference: `integration/VALIDATION188.md`

<!-- ORIGINAL-DOC {"bytes":910,"path":"integration/VALIDATION188.md","sha256":"d94b05fd92b66797f448c1fd720054287a3076680ac7652d6ab0654b728cbff6"} -->
# Strict read query boundaries

Known single parameters only for13publicreadroutes and v1 aliases, private tariff
jurisdiction and weekly dates. News q200/categorycountry100/project5/sort20:
oversize inputs rejected, not silently truncated. Duplicate keys rejected even
when values match. Controls/NUL/DEL rejected. Raw query ≤2048bytes. No-parameter
routes reject any args. Existing domain/sort/limit/date validation still applies.
Auth runs first; invalid read requests400before any reader. Valid requests retain
same filters/caps/response semantics. No live flags/access/schema/query operators.
Export-full/export snapshot use their existing stricter parsers, unchanged.

POST related-news/Finder body validation gaps are NOT covered by this read-only
unit. Login/account/legacy app form shapes also remain their own contracts.
This is no claim of uniformly strict validation across the whole repository.

<!-- END-ORIGINAL-DOC -->


<a id="doc-161"></a>

### Reference: `integration/WATCH_UPDATES_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1054,"path":"integration/WATCH_UPDATES_LIMITS.md","sha256":"9bc130bfd55e72ea1490a0e0773b172617565cefb10344a151feae322576badb"} -->
# Manual watched-country update comparison

Browser-local identity baseline for an already watched exact country label and selected project. Loading the country manually compares the current first100 supplied rows. First load is a baseline, never a new-news alert. Duplicate identities counted once; same project+URL identities from the existing read view are reused. Content edits at the same identity are not detected.

UI calls these newly seen rows, not newly published news or verified trade/tariff changes. No device/browser push permission, background tab check, service worker, timers, polling, account storage, email/WhatsApp or deliveries. History caps60 label/project baselines,500 article identities each; eviction may make previously seen rows newly seen again. Truncated-view comparison has a visible coverage caveat. Failed storage stays visible and no persisted-success claim is made. Clearing data resets memory. This is a manual in-page update prototype, not activated real-time watchlist alerts. Code-based watch rules remain unbuilt.

<!-- END-ORIGINAL-DOC -->


<a id="doc-162"></a>

### Reference: `integration/WEATHER231.md`

<!-- ORIGINAL-DOC {"bytes":4031,"path":"integration/WEATHER231.md","sha256":"402d98ea12a61fbf5416829f83588863f0f8faba2f41758fa1d5516ca80a1a49"} -->
# Port-weather card wrapping (231)

On phones, weather values ran off the right edge; scrolling right hid labels
and the starts of the values. The weather card now fits two columns to the
phone and wraps long values. Labels and full values can be read together
without sideways scrolling. Values, sources, dates and requests stay the
same. Other Finder tables stay unchanged.

CSS only: src/style.css global .report-table min-width680px remains. New
#portwx-pick + .report-table-wrap .report-table selector matches only the
successful weather data table next to its original select. min-width0,
width100%, fixed layout, cell wrapping, first-column40% with label words
unbroken. No hidden content, smaller fonts, ellipsis or max-height. Wrapper
keeps its original overflow:auto fallback. src/app.js SHA bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313 unchanged.

New browser_weather231 and test_weather231 check table/cell bounds, labels,
source/date, native port control focus/Tab/ArrowDown/Enter/Escape, model503
states and original formatters with long numeric fixture values/degrees0/359.
Expected directions both round to N via the original formatter. No formatter
or text changes. All fixture numbers SIMULATED, not official weather. Caption
is outside raw card captures (result.json); no fixture label covers the card.

BEFORE230 final390 screenshots copied verbatim with their original UTC result
and hashes. Fresh230-tree probe at320/390/1100 light/dark failed geometry at
320/390, exit1. Initial harness syntax error corrected before that recorded
geometry run; no product error claim from that attempt. AFTER from two final
consecutive runs only; semantic equality excluding times. Actual final30card
pixels inspected via five contact sheets: success, stress0,stress359,marine503,
forecast503 at320/390/1100 both themes. Full values/date/warning fit; long
wave period wraps; label words intact. Not real weather/model accuracy or
all browsers/devices. Chromium154.0.8037.57/Python3.10.12/Playwright1.63.0,
Nodev22.23.3. Frozen1791576000000/random0.25/AsiaKolkata, no sleeps.

Test-only scope mutations occur after all captures: widen selector to global
.report-table and detect non-weather minWidth changed; insert a sibling after
the weather select and detect selector no longer matches/minWidth680px.
Restore both. Port statistics retains680px and horizontal scroll at320.
No CSS/DOM mutation is used to make the final card pass. Native table markup
unchanged; accessibility checks cover the control, not a full accessibility
audit. Five probe modes use exact GETforecast/marine mocks; expected FX read
aborted. Original230 six-case regression has unchanged endpoint/counts and
CSP; its geometry now checks fitting cells instead of historical clipping,
with dated231 supersession comment. FINDER-NETWORK230.md untouched, historical
clipping finding superseded by this document.

Local double rebuild commands in audit. index.html now8e1ce9c7fa5da880085afb2b8a20e6fbc3195d8b24f4ffdde4bee09c787d0967;
offline.html now0e2e85ea54f276c3c50984e8c26b9400e1deee9f4b8a035a8866e56c2455b65b.
Public offline cache ID4f48ae1b3cd7 -> c100d1017b7c is a separate derived change,
only relevant when future snapshot explicitly served/used. No live activation.
Dataset data.d6d1b417562b.js and sw.js unchanged. Source.css, snapshot hashes,
adapter hash pins, build receipt and preservation note updated; adapter logic
unchanged. 229/230 index pins updated with231 comments. 230 historicaldoc
not rewritten. Default new wrapper explicit SKIP unless RUN_WEATHER231_BROWSER=1;
missing Chromium/Playwright explicit SKIP, never browser PASS.

230/229/228/nested/static/offline/198d/ships226 regressions PASS on finalsource.
One combined120second regression call timed out after all8logscompleted; logs
read for completion before continuing, no side effect retried. No DB access,
sends, mount, serving, deployment, activation or wiring. Full project remains
incomplete. Scope is local code/snapshot review, not live operation.

<!-- END-ORIGINAL-DOC -->


<a id="doc-163"></a>

### Reference: `integration/WEEKLY_REPORT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":961,"path":"integration/WEEKLY_REPORT_LIMITS.md","sha256":"13fd36f41aa34e5d4436ef151406201ede23ff4afd34bc4b0ed327491fbf643c"} -->
# Weekly preview limits

Manual download only, no storage or delivery. Reader normalized only after an exact raw snapshot check and2000-row bound; max100 rows per collection enter the public view. Snapshot completeness is not weekly-history completeness. Period is1..31 days, India offset, earliest start1970-01-02, years through2100. Public fields only; malformed snapshots and builder failures return generic503. Duplicate dates400. Two PDF builds per Flask app/process; additional concurrent calls429. Semaphore releases after exceptions.

Single-worker private preview is REQUIRED: PreviewAccess itself documents a per-process limiter. No live deployment/worker count is verified or changed in this increment. Multiple workers multiply this PDF limit; production needs a reviewed shared concurrency/work limiter. The default single-process fixture server is verified, not the Render runtime. No production readiness claim follows from this local semaphore.

<!-- END-ORIGINAL-DOC -->


<a id="doc-164"></a>

### Reference: `integration/accounts/CONFORMANCE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":7114,"path":"integration/accounts/CONFORMANCE_LIMITS.md","sha256":"5a6351b5f5e4ceed59aa9791676a9c0a35e24a00e0add0053bd4960bcba113f1"} -->
# In-process account conformance and reservation lifecycle

Contract conformance with ONE Limiter instance per store. Multiple limiter
instances, even in one process, are unsupported. Passing proves only exercised
sequences, not production Mongo/shared-limiter atomicity. No live account
activation, client, database writes or preview access replacement.

## Exercised store sequences

Nine new tests use a fake clock, at most eight workers, barrier/event and join
timeouts, worker exception propagation, no sleeps. They exercise normalized
username, invite N claims/N winners and cap without invite burn, same-user
winner, password version race with caller retained and other sessions revoked,
settings CAS and expiry at now, delete/settings/session race without orphans,
paused stale session creation, limiter caps/generation and a deliberately
broken invite-store negative control. Existing service hardening tests cover
other fences. Invite expiry is NOT implemented (integer uses only).
replace_password doc wording remains ambiguous: implementation keeps caller,
revokes others. Tests pin behavior, not a new policy approval.

## Local limiter fix

Repeated same-window refund erased another attempt count. Reservation is now
an exact frozen/slotted sealed object carrying only random owner nonce/token.
No dict or read-key compatibility; service callers only pass it back. Copy,
deepcopy and pickle rejected. Issued token map stores authoritative instance
and key-generation pairs; owner, type and instance identity checked. Legacy
dict, constructor copy and foreign limiter rejected. Terminal check/pop and
operations are under one per-limiter RLock; repeated refund/success/fail is a
no-op. Not tamper-proof against hostile in-process Python private-state edits.

success clears user/refunds client, refund refunds both, fail consumes token
without changing counted failures. AccountService's terminal invalid username,
invite/taken/cap/session, bad/unknown login and invalid password re-entry call
fail. Weak password/Busy refund. Existing success calls unchanged. This avoids
completed invalid attempts accumulating until the global outstanding cap.
1030 distinct real service failed logins tested with zero outstanding tokens.

Map hard cap1024 is fail-closed for in-flight/abandoned operations only. No redundant key index. Issued tokens track both key-generation pairs. Clear/rollover does not drop sibling
reservations because each still-current client side must settle. Lazy prune
inspects at most4 queue tokens per pass (two reads each); begin performs one
pass, <=8 store reads independent of map size. Local index/queue maintenance can
still take O(n) CPU under the lock; bounded1024, not a network throughput proof.
Pruning occurs on begin/finish, no timer or immediate notification of another
limiter's clear. All local tables bounded by outstanding cap and pruned tokens.

Each side independently settles only its current generation. One stale user
side does not prevent a valid client refund. Lazy prune drops a token only when
BOTH sides are stale/expired. _begin compensates successfully counted keys if a later count or denial
compensation raises. Compensation uses a per-generation last rollback marker
for immediate retry after commit-then-raise, preserving original exception,
ONLY under the single-Limiter-instance-per-store contract.
Persistent store outage can still prevent compensation; this is not a durable
rollback ledger. Count callback commit-then-raise before returning generation
is also not recoverable by this local API. _finish consumes token before callbacks, so
first or second callback failure surfaces and won't retry; some counts may
remain. Cross-process store-side attempt IDs/transactions/crash-safe retry
ledger are not implemented. Store per-record atomicity remains required.

## Evidence and limits

110 focused tests (25 reservation,9 conformance,76 existing tests) run:109 PASS and1 expected failure in the
configured run. Tests include repeated refund, success/refund orders, eight
worker races, stale/clear/prune/cap, copy/forge/subclass/foreign, reentrant
callback, second-operation failure and real service terminal failures. Count
of existing tests in this bundle follows observed unittest total, not readiness.

Standalone review bundle includes all account package Python dependencies and
four test files, plus root empty package initializers. No filesystem secrets or
live integrations. Python3.10.12, stdlib only for these tests. Production shared
store/failover/load/index/credentials/TLS proxy/recovery/invite-expiry/real
serving concurrency remain untested. Report output with in-process-conformance
and exercised-sequences-only labels, not deployment readiness.

## Exception and integration boundaries

signup/login/_reauth own admitted reservation in try/finally; terminal fail
runs even on BaseException and consumes without callbacks or refunds. Original
exceptions propagate. Eleven post-begin callback injections and1025exception
recovery checked. Begin rejects callback-nested begin before prune/count with
RuntimeError, preserving capacity even with RLock re-entry. Same-token finish
re-entry remains safe. No prune runs after issuing a token inside begin.
Store attempt records are not purged by this limiter. The store integration
must provide scheduled/TTL cleanup for expires; MemoryStore retains them.
This zip is a standalone account-unit-test bundle, NOT a runnable HTTP/UI app.

Begin is prohibited during finish callbacks as well; same-token finish re-entry
still no-ops. Dead key index removed. Second-count exception repeated seven
times and denial compensation before/after commit failure are exercised.
The existing policy clears a successful user's failure count: interleaved
successful victim logins can reset an attacker's per-user brake. Client brake
is separate. client MUST be a trusted server-derived identity with admission
concurrency limits, not arbitrary caller input. Slow in-flight requests can
fill the1024cap; it is a resource bound, not production DoS prevention.
success() store exception after session creation can leave a live session even
though caller receives an exception. No transaction couples session creation
and limiter settlement. This is documented missing atomicity, not readiness.

## Pinned unsupported two-instance compensation

A second Limiter sharing the store can overwrite the last rollback marker
between another instance's committed compensation and retry. That retry can
then decrement an unrelated failure. The named expected-failure test
UNSUPPORTED_two_limiter_compensation_marker_interleaving pins this defect with
same-process instance B interleaving. Do not instantiate multiple limiters for
a store or use this limiter in multi-worker deployment. Shared instance/process
support needs per-attempt store ledger or bounded applied-marker sets with
proper retention; it is not implemented. This is an explicit contract limit,
not a passing shared-store guarantee. No production account activation.

Exactly one AccountService per store is required (it owns the sole Limiter).

<!-- END-ORIGINAL-DOC -->


<a id="doc-165"></a>

### Reference: `integration/accounts/HTTP_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2743,"path":"integration/accounts/HTTP_FIXTURE_LIMITS.md","sha256":"97c8717037cd7c0ce6d6fcc27738de4e165b5bde70814238e3b198401be833d4"} -->
# Memory-only account HTTP fixture

Factory must be explicitly constructed with AccountService, exact MemoryStore, caller's secret/clock/origin and a trusted fixture client resolver. It is not imported by the merged app and does not replace PreviewAccess. No real signup/login service, database client, network, environment read or provider key entry is enabled. Test fixture inputs only. Existing account foundation defaults invite signup; a production operator must explicitly choose closed signup before activation.

Verified HTTP boundary: exact HTTPS canonical host and exact-string Origin match (no trailing slash normalization, no alternate origins); secure HttpOnly SameSiteStrict host-prefix cookies; session tokens omitted from JSON, post-login/signup preauth cookie cleared; logout session cookie cleared even when expired/invalid; no-store and CSP; JSON404/405/500 (redacted exception body), debug off; bounded16KB strict field JSON, duplicate fields rejected before service; cookie-bound session/login CSRF; coarse status/error codes. Secure cookies require HTTPS; loopback-browser tests use HTTPS fixture context, not credential collection.

Production blockers/design choices:
- request.host_url host/scheme comparison fails closed behind unconfigured TLS termination. Require explicit trusted reverse-proxy addresses and canonical host filtering; never trust arbitrary forwarded headers.
- Trusted client identity resolver must be pinned to platform proxy policy, never raw X-Forwarded-For or a caller JSON value. Shared/atomic store/limiter still missing. MemoryStore is one process only.
- HSTS and rate limits for preauth/entire auth surface must exist at the edge. No preauth edge limiter is simulated by the fixture.
- Optional Sec-Fetch-Site same-origin/none gate for GET endpoints should be decided before production. Current GETs still require exact host and use SameSiteStrict cookies; no CORS permissions.
- save_settings and export intentionally do NOT require password re-entry: live session+CSRF+Origin are required. Change password/delete require re-entry. Reassess with owner before exposing production account/export behavior.
- Mongo adapter must meet foundation's full fenced atomicity contract and index/shared limiter design. Signup mode/reset recovery/real operator configuration and lifecycle must be reviewed, no auto scheduler/purge here.

Loopback HTTPS Chromium validated the separate fixture sign-in/settings UI at390px: login, save, reload, export and logout. Fixture signup is explicitly closed after test seeding. No real phone/device functional validation, production performance, cross-worker durability or deployment readiness is claimed. Merged routing and production accounts remain unwired.

<!-- END-ORIGINAL-DOC -->


<a id="doc-166"></a>

### Reference: `integration/accounts/INVITE_EXPIRY_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2485,"path":"integration/accounts/INVITE_EXPIRY_LIMITS.md","sha256":"15d7e55ac883f40cd8a89a7dbe273b612d4d5dd75b089c0ec91970cae34e254a"} -->
# Timed invite contract, no provisioning or activation

Expiry authorization is at the explicitly supplied post-password-hash admission
time, not store lock/transaction/commit time. MemoryStore and MongoAccountStore
both use caller now for that decision. Adapter's clock only drives existing
limiter cleanup, not invite authority. A delayed claim admitted before expiry
can commit after expiry. This is an intentional limitation, not commit-time
expiry protection. Test callers supply trusted clock; a store API is not an
untrusted HTTP boundary. No new routes, clients, env selection or real writes.

Legacy exact integer invites remain non-expiring. New provisioning uses exact
int1..1000; stored exhausted0 allowed. Timed shape is exactly uses/ expires_at;
uses0..1000 persisted, finite exact numeric epoch0..last second of2100 including
fractions. Bool/subclasses/unknown fields refused. Timed claim needs valid now
even for exhausted/taken/cap refusal. New inventory cap1000, existing hash can
be replaced at cap. Purge explicitly removes expired timed entries and validates
clock+inventory before effects; no timer. Adapter existing cleanup of exhausted
legacy entries remains: refusal means no account/cap/use consumption, not byte
identical snapshot. No uncertain transaction auto-refund or replay.

Account creation prevalidates/captures closed inert record and claim inputs
before decrement or account table changes; duplicate uid refused. Invalid
record, expired invite/taken/cap claims do not consume uses. This no-burn claim
ONLY covers account creation. Preexisting subsequent session/limiter failure
can leave a created account and consumed invite; tested and NOT solved here.
Allocator failure/hostile concurrent private table mutation is not a transactional
MemoryStore guarantee. Mongo transaction failure stays outcome unavailable,
no retry; committed-response-lost can leave the account/invite consumption.

Actual source baseline store/service/Mongo files matched live private repo before
changes. Source hashes are included review evidence. Schema1 gains optional timed
invite shape without migration; old integer snapshots retained. No real Atlas
compatibility/provisioning/schema/index/tier proof. Transaction/shared limiter,
recovery, account activation/proxy/live loader remain blocked. Tests run in full
configured repository:10 new invite tests+15 prior adapter tests PASS;132 account
tests OK with1expected limiter failure. Full suite/code review pending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-167"></a>

### Reference: `integration/accounts/MERGED_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":2909,"path":"integration/accounts/MERGED_FIXTURE_LIMITS.md","sha256":"cd79cdec80e64bb132fd0a9ddc4f19e41d3a3311c789a9d409e39fed659d9f83"} -->
# Separate merged memory-account fixture

ExactAccountService/MemoryStore/FixtureNews, seededtestusers, closedmode,
canonicalHTTPS origin, trustedexplicitclientresolver. No productionstore/reader,
env/client/Mongo/sourcegrant/standardentrypoint change. Fullwhoami authorization
EVERYprotectedrequest, existingoriginalservice owns cookie/session/expiry/fences.
No secondcookieparser, accountcookie can't bypass oldpreviewdefaultdeny path.
Accountsettings existingfixtureonly, no workspace settings sync.

Explicit route/method allowlist, defaultdeny; workspace/APIs/assets/downloads/
Finderrequireliveaccountsession. OnlyexistingaccountloginUI/assets/preauth and
merged-loginfixturepagepublic; whoami/settings originalendpoints stillvalidate
cookieandreturnunauthenticated. Rejectrawpercentaliases/dots/backslash/doubleslash,
prefixcollisions/unsupportedmethods. IfserveromitsRAW_URI normalizeddecodedpath
can'talways be distinguished fromexactpath; notdeployedproxyproof. CookieSecure/
HttpOnly/SameSiteStrict/CSRF/exactOrigin retained. No forwardedhost/IPtrust in
factory; resolver is trustedinjection, actualplatformpolicy remainsreviewgate.

Memoryonlystate resets, oneAccountService/Limiter perstore. Multiplefactories
sharingservice don'tmake distributedlimiter. Sharedlimiter/recovery/inviteexpiry,
DBstateprovisioning/transactions, actualhostproxy/rate/deadlines remainliveblockers.
9nativefocusedtestsPASS login/signupclosed/logoutreplay/expiry/passwordfence/delete/
oldgateisolation/aliases/assets/navigation/crossorigin/forgedforwarded/production
storeorreaderrefusal. NoactualDB/networkeffects. UIbrowserverificationnext.

V2reviewfixes: exactGETstreamreadroutes+POSTrelated-news/finder-context nowallowed,
POSTfullsessioncheck thenexactorigin/bounded16KBstrictJSONduplicatekey/closedfields;
noBRICSwrite routes. Offlineoptin/worker/control/manifest/rootSW routes denied in
this fixture. Existingcachedpublicsnapshotsfromotherpreviousserviceorigins are
notremotelyrevoked; usefreshdedicatedfixtureorigin/profile forbrowserQA. Finder
mayattemptSWregistrationandfail403, notofflineinstallation support. NoSWcache
logoutguarantee claimed. Loginrenderoverride changesbothwarning+headers/wrapper,
notjustwarningtext; restoreoriginalno-store/nosniff/noindex/no-referrer/base-uri.
13nativefocusedPASS withfullconfiguredassets, realvalidcounterpartcookiesboth
old/newgates, idleexpiry/invalid/revokedassets/downloadclasses, subclassrejection.

FinalfixtureHTML-onlybanner labels Storepublicsnapshot/offlineinstallation and
BRICSadd/removewrites disabled/unwired onworkspace/Finder/streams. Existing
controlsretainoriginalbytes, backenddenied; labelmakesnosavebehaviorvisible.
OriginalsourceHTMLunmodified, response-only warning +accountsettings/logoutlink.
Usefreshdedicatedfixtureorigin/profile. LogoutdoesNOTpromiseoldofflinecache
revocation.14focusednativefullassetsPASS afterwarning, fullsuite958next.

<!-- END-ORIGINAL-DOC -->


<a id="doc-168"></a>

### Reference: `integration/accounts/MONGO_STORE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":5006,"path":"integration/accounts/MONGO_STORE_LIMITS.md","sha256":"04dfe9296398e82ecc893ae629386b1e789ef835d8ebe84fec971bc8e4b78744"} -->
# Injected Mongo transaction account seam, offline only

MongoAccountStore uses one pre-provisioned geo_intel/accounts_state document
with _id account-state-v1, schema 1, version and bounded state maps. No client,
credential, default environment, runtime selection, index creation or bootstrap
insert. Exact source/write/schema/transaction developer review required; these
booleans do not establish owner permission. Real Atlas session/transaction,
free-tier support, role and source capability remain unverified until Push
allows a live check. No live Mongo operation occurred in this increment.

Single document stores at most 50 users, 500 sessions, 10000 attempt records,
1000 invites and 50 settings, at most 2MB JSON/100000 nodes/depth16. This is a
bounded small-account design, not a normalized collection migration or scalable
account database. Serialization/write contention on one document is deliberate.
Missing or malformed state fails closed; no automatic schema repair or init.
The operator must separately review provisioning and any future migration.

Every AccountStore operation starts an explicit snapshot/majority transaction,
finds state, reuses original MemoryStore operation on copied maps, validates
bounded result state, conditionally replaces matching version and commits.
Read-only operations also transact. No with_transaction automatic retry, callback
runs once; commit failure is outcome unavailable, may have committed, do not
retry. Abort/end cleanup best effort, fixed redacted error with no source context.
Nested same-thread calls refused. Client externally owned. max_commit_time2s
and find max_time2s aren't total socket/worker deadlines; injected client must
have independent finite socket/connect/pool settings.

Existing atomic semantics preserved for invite+cap+username, session password
version, live-session fences/settings CAS/delete/password replacement. Caller
session retained on password replacement as original; others revoked. One
AccountService/Limiter per store remains required. This does NOT fix existing
multi-limiter/process compensation defect, crash settlement or service session
creation versus limiter-success failure coupling. No account HTTP activation,
TTL cleanup schedule, invite expiry, secret storage or recovery UI added.

8 focused fake-transaction tests: shared backing state across adapter instances,
invite cap/no burn, password/session/settings/delete fences, callback once/nested
refusal, four-thread same-user race, bad state refusal, commit-failure rollback
and cleanup. Fake commits implement locks and rollback; they do not prove actual
Mongo transaction behavior or commit uncertainty reconciliation. Real PyMongo
4.8.0 read/write concern objects used, no fake imported driver. Full existing
account conformance suite not rerun in partial tree; passing is scoped evidence.
Repro python -m unittest tests.test_mongo_account_store -v with PyMongo4.8.0 and
integration/accounts modules. Bundle contains all dependencies, no original
Finder or connected DB needed.

Choice sources inspected:
https://www.sqlite.org/wal.html (same-host/no network filesystem WAL)
https://sqlite.org/atomiccommit.html (transaction atomic commit)
https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/
The user's single Atlas DB direction favors injected Mongo over local SQLite;
no inference about current tier transaction support from these docs.

V2 cleanup uses injected clock (default time.time); expired attempt records and
exhausted invites purged inside transaction before new mutation/bounds. Active
attempt keys still cap10000; refuses limit/invalid distinctly, no eviction of
active brakes. Invites have no expiry format yet;1000 active invite cap permanent
until consumed or separately removed. Deterministic state bound/non-JSON errors
raise MongoStoreInvalid, not an uncertain outage. Control KeyboardInterrupt/
SystemExit re-raised after abort/end cleanup.13tests include10000expiredkeys,
51stuser/nonJSON, sameinvite4thread2winner race and labelled fake OperationFailure
112 WriteConflict/TransientTransactionError plus UnknownTransactionCommitResult.
Each callback executes once; fake rollback doesn't prove real unknowncommit
outcome, recovery/source reconciliation and live support still open. No app retry.

Final review SAFE v2 (13/13 with stub concern types in reviewer environment);
author tests use installed native PyMongo4.8.0.15 final local/extracted tests.
All non-Exception BaseExceptions re-raised after cleanup, including cancellation
and generator exit. Pure get_user/get_attempts/get_settings never persist purge.
Mutating operations drop expired or missing-expires attempts like MemoryStore;
non-numeric expires remain invalid/unsupported producer state. Store clock,
not service clock, governs housekeeping: inject the same clock or account for
skew; a fast clock can expire limiter records early. end_session failure after
successful commit returns unknown/do-not-retry; committed writes may stand.

<!-- END-ORIGINAL-DOC -->


<a id="doc-169"></a>

### Reference: `integration/accounts/README.md`

<!-- ORIGINAL-DOC {"bytes":5185,"path":"integration/accounts/README.md","sha256":"e439a4604863382f28a8c3c7ba2e5fcbca3e971fca152aa747463b27a154feb3"} -->
Copyright (c) 2026 Push

# accounts (offline foundation, not wired)

Stdlib only. No network, DB client, config reads or import-time side effects. Store, clock and secret are injected.

## Modules
- passwords.py: policy (10-128 chars, raw length bounded before and after NFKC, no control/invisible chars, small common list); scrypt (N=2^15, r=8, p=1, 16-byte salt) with PBKDF2-SHA256 fallback; stored hashes are strictly parsed before any derivation (param caps, exact salt/digest length, canonical base64, pbkdf2 1000..5,000,000 iterations); constant-time compare; concurrency cap (Busy); rehash on login.
- store.py: AccountStore interface + MemoryStore. Atomicity contract below.
- limiter.py: reserve-then-refund attempt counter (HMAC keys). Operation-specific user keys: "login" (also used for password re-entry in change/delete) and "signup" are separate, so signup traffic can never lock a login. Closed-mode signup refusals reserve nothing. 5 attempts per user key / 20 per client key per 15 min; the next attempt locks 15 min, doubling to 1 h. Records carry a generation id; a refund or clear from an older window is ignored. Unknown names count identically.
  Deliberate trade-off: 6 wrong passwords against an account lock that account's logins for 15 min (anyone who knows a username can do this). The client key limiter (shared across operations) is the main brake on one source; the per-user lock is the backstop against distributed guessing.
- csrf.py: stateless HMAC tokens, bounded ASCII formats. Login/signup token is bound to a pre-auth nonce cookie; session token is bound to the session. Origin must be present and exact (require_origin=True default).
- service.py: issue_preauth, signup (invite|closed|open), login, logout, whoami, change_password, get/save settings, export, delete_account, purge.
- settings.py / validators.py: browser-rule mirrors. Channels: up to 20 extras stored; the code-defined Republic row is never stored, so users see up to 21 rows (20 extras + Republic). Watchlist up to 20.

## Store atomicity contract (real adapter must meet it)
create_account (username + user cap + invite claimed together); create_session / touch_session (only while the account uid is live; create also checks password version pwv; no upsert); FENCED commits: delete_account(username, uid, pwv, session_hash, now), replace_password(uid, pwv, new_hash, session_hash, now) and put_settings(uid, doc, expected_version, session_hash, now) succeed only if, atomically, the uid is live, the calling session is live/unexpired/owned by that uid, and (delete/replace) pwv equals the value seen when the password was verified; delete/replace also remove or revoke sessions in the same operation; put_settings is also compare-and-set on version; update_attempts atomic read-modify-write (CAS loop). Accounts have an immutable random uid, so a re-registered username never inherits old sessions or settings.

## Stored per user
uid, normalized username, password hash, created time, password version, settings. No email, name, phone or IP. Sessions: SHA-256 of token, uid, username, times. Limiter keys are HMACs with TTL (client hashes expire via purge).

## Wiring requirements (HTTP layer, not in this package)
- Trusted client identity: derive `client` from the platform's trusted proxy header (Render), never from a client-supplied value; pass a non-empty string (<=200). Empty/missing is refused.
- Pre-auth cookie: on the login page call issue_preauth(), set its cookie (__Host-gib_pre) and embed the csrf value; pass both back on POST. Authenticated POSTs send the session csrf value.
- Shared limiter across workers: use a store whose update_attempts is shared and atomic. MemoryStore is single-process only.
- DB atomicity as above; unique index on username and uid.
- Call service.purge() on a schedule (e.g. hourly).
- Request body size limits (e.g. 16 KB) and JSON depth limits before calling the service; cap total request rate at the proxy.
- Env supplied by Push in Render, never in chat: ACCOUNTS_SECRET (>=32 random bytes), signup mode, allowed origins, invite codes (store only hash_invite output).
- Input hygiene: passwords reject control, format/invisible, surrogate, private-use and unassigned characters (ordinary spaces allowed); client keys and invite codes are bounded printable ASCII; usernames are ASCII; labels reject Unicode category C. All checks run before any HMAC or KDF, and refusals are coarse error codes (no exceptions escape).
- Timing: the dummy hash used for unknown users is computed at construction with the CURRENT hash parameters (and recomputed only if the hasher's parameters change). Accounts still holding an older, different-cost hash take a measurably different time than unknown names (a reviewer measured ~12 ms vs ~3 ms for n=4096 vs 1024) until their next successful login rehashes them. Remaining signal: it reveals only that a username exists with legacy parameters; change parameters rarely and expect it to disappear as users log in.
Separate memory-only HTTP/UI fixture exists; see HTTP_FIXTURE_LIMITS.md. Not implemented: production HTTP/UI integration, Mongo adapter, password reset (owner-run only), logging.

<!-- END-ORIGINAL-DOC -->


<a id="doc-170"></a>

### Reference: `integration/accounts/SHARED_LEDGER_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3830,"path":"integration/accounts/SHARED_LEDGER_FIXTURE_LIMITS.md","sha256":"bd6275b950453abfb820ce5441f4560841a34ae79bdd4a78c5b1afec1d332979"} -->
# Same-process atomic ledger experiment

Separate Ledger/Facade only, NOT AccountService wiring or production fix.
Old one-Limiter-per-store restriction and expected two-instance defect retained.
Live source limiter matched configured bytes before work; hash recorded in proof.
No Mongo/client/routes/environment/store callbacks or new live accounts.

Closed constants: user5/client20, window900, base lock900/max3600, locks cap64.
Window rolls when now-last>900, not equality. Denial keeps newly-created lock on
limiting side only, no phantom admitted contribution on other side. Existing
locked side unchanged. Counterpart differs from old compensation bookkeeping:
no last/expiry/count update at all on denied counterpart. Differential admission
wait policy tested narrowly, not blanket parity. Capacity denial changes nothing,
even prune/clock/cursors. Both at-limit sides lock in same transition.

One Python shared lock supports two facades only in one process. Ledger-issued
exact Ticket identity+random nonce, bound to authoritative ledger identity map.
Either facade can settle. Caller copy/forge/foreign/purged/expired refuse. First
terminal wins; repeat returns already_settled, cannot change counters. Key IDs
HMAC, raw username/client not stored in results/state. Ticket grants settlement
only, not user authority. Fail retains counts; refund current generation decrements
once; success clears matching user generation and refunds client. This can reset
unrelated same-user failures and invalidate other in-flight user contributions,
matching the retained original policy; late refund never edits newer generation.

TTL4500 from admission, terminal receipts count against200 cap until expiry.
Expired pending refuses later settlement, no automatic refund. Prune may remove
expired keys only with no live lock; counters otherwise keep admission effect.
Keys cap200, no live eviction. Persistent queues rotate at most4 keys+4 receipts
per prune call, fair traversal. Full state validation/copy is boundedO(200+200),
not just8 reads: exact closed scalars and shapes before JSON<=256000 bytes.
Node count implicit bounded records/shapes/queues, no recursive values accepted.
Every operation validates finite exact numeric epoch, upper margin for TTL/lock,
no rollback; repeated terminal also advances clock. No injected RNG/callbacks:
internal random token generation4tries then refuse without publish. Source tests
may mock internals as trusted faults, never caller controls.

Transition constructs captured containers before reference publish. Fault before
publish keeps counters/receipts/clock/cursors. This is not hostile process isolation,
crash durability or durable transaction outcome proof. Private-state mutation by
hostile Python and allocation failure between assignments are outside guarantee.
Random ID reuse astronomically unlikely, not impossible; exact ticket identity
prevents replay even if nonce collision after purge. Results are fresh scalars
plus opaque ticket, no mutable records/raw key identities.11focusedauthorPASS,
no full-suite/code-review claim yet. No visual artifact/UI was introduced.

V2 generations reject collisions with ALL live keys and retained receipt pairs,
including generations from cleared keys. New generations within one transition
also enter that used set. Bounded4 retries exhaustion refuses before publication.
Ticket nonce exact64 lowercase hex checked before any hash lookup; forged object/
subclass nonce cannot run hooks.15focusedtests include forced generation replay,
rollover collision, nonce hook refusal,8-thread admission cap, every terminal
repeat and prune passing live entries. Structural shape checks are not semantic
receipt-pair uniqueness/authenticated state integrity; hostile private mutation
remains outside guarantee. Code review/full-suite pending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-171"></a>

### Reference: `integration/accounts/SHARED_SERVICE_FIXTURE_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3281,"path":"integration/accounts/SHARED_SERVICE_FIXTURE_LIMITS.md","sha256":"7067979719048f144c1263b8ba360f23ad88b85613a2197ffe4baa7ea4e12c68"} -->
# Shared-memory service control-flow fixture

Separate explicit factory, no HTTP/production constructor/wiring change. Owns a
fresh exact MemoryStore, Ledger, sealed clock/hasher, fixed synthetic secret/origin,
1..8 synthetic users with public test password. This hasher is intentionally NOT
password security. Never real users/passwords. Only handles for preauth/login,
closed signup and synthetic _reauth research. _reauth uses artificial identity,
not session authorization; change/delete/settings are not exposed by handles.
Private introspection/mutation or spoofing class module is outside isolation.
This is a conventionally isolated Python fixture, not hostile code containment.

Validate exact bounded primitive user count before constructing anything.
Hasher owns only exact fixture clock; constructor's original dummy hash calls
are counted. Bind both service instances to shared-ledger adapters before any
handle escapes. Original service/limiter/store/Mongo/78-ledger source hash pinned
in tests. Existing original two-Limiter expected defect remains. The obsolete
Limiter objects created by original constructors are never used after binding.
No production fixes or distributed/durable behavior inferred from tests.

Closed signup checks client/CSRF first, then exits before admission/hash. No
weak-signup refund claim. Login Busy refunds, failed verification consumes,
success clears user/refunds client; finally-fail repeats first terminal as no-op
only while clock and receipt remain valid. Synthetic _reauth valid/invalid/Busy
and missing-user paths exercised. No real reauthentication permission implied.

Hard capacity/input/clock admission errors raise coarse FixtureRefused, never
fake backoff or (None,0). Real lock denial uses ledger wait. Scalar subclasses
refused before original validators; handle client length <=128 vs original200.
Both exclude spaces. Seed/password/config are copied fixed primitives, no caller
clock, hasher, store, callbacks, network, environment or owner account state.
Bounded hasher controls normal/Busy/error/TTL advance/rollback are private test
fault controls. Tests may monkeypatch classes for barrier/error faults only;
these are trusted research, not runtime extension hooks. Time controls finite,
nonrecursive and restricted; no wall-clock timers or background activity.

Settlement errors also raise FixtureRefused. Original unconditional finally can
mask a first error: intentionally retained, tested, NOT first-error preservation.
No error is converted into successful settlement or old-limiter fallback.
Success login opens a session BEFORE settlement: TTL expiry/clock rollback during
verify can leave a LIVE session even though the caller receives an exception.
Finally failure AFTER success similarly retains a session. Explicit tests retain
this pre-existing larger-transaction gap. No fail-closed account-authentication
claim, automatic session rollback or durable session/limiter atomicity.

Concurrent test uses bounded barrier/events/join and surfaces worker exceptions,
inspects authoritative pending receipts and counts before release. Broad parity,
real hash load, cross-process concurrency, crash recovery, distributed clock and
live source functionality remain unproven. No UI/visual artifact introduced.

<!-- END-ORIGINAL-DOC -->


<a id="doc-172"></a>

### Reference: `integration/accounts/WIRED_HTTP_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3743,"path":"integration/accounts/WIRED_HTTP_LIMITS.md","sha256":"232203717277d1e5a42a07ba0bb0dce3e2681c238326f531b5f48f93f8d84b65"} -->
# Explicit account/session/settings HTTP wiring, not activation

create_wired_http is additive, unselected, no env/client/provision/index/startup
calls. Construction validates exact AccountService, Hasher default scrypt/
PBKDF2 params, Limiter sharing same store/secret/clock and default limits,
SettingsPolicy with exact validators/compulsory Republic, MemoryStore or
MongoAccountStore. Trusted in-process collaborators must not be monkeypatched.
One service/Limiter per store/process is an operational invariant, not globally
enforced; existing multiworker compensation defect remains unsupported.
Mongo constructor's existing review dict is a code gate, not proof of owner
permission/capabilities. A later caller serving this factory with a real store
could issue real state writes. Only disposable Memory/fakeMongo used here.

Route inventory is emitted as factory.route_contract and constants. Public GET
only /account/preauth, which returns protocol CSRF and cookie (not diagnostics).
POST account/login/signup/logout/save-settings/export/change-password/delete
use exact existing JSON schemas/Origin+CSRF protocol; signup closed. GET
account/whoami/settings private. No account preview/assets/UI promoted, no
new login UI; existing fixture/UI unchanged, therefore no changed pixels.

All enumerated selected news GET routes and workspace static rules private,
including previews/export/PDF/dashboard/APIs/Finder/assets/branding/manifest.
Two news POST read-only queries (related-news/finder-context) additionally
require existing session-derived X-CSRF-Token. No new CSRF cookie/protocol.
Legacy mark-emailed, POSTcritical/weekly and stream edit/delete denied. No
second exposed health/static/account catchall. Unknown paths denied, downstream
static filenames still use original owning validation. Factory does NOT take
a full-export pager/events adapter; original unavailable states remain.

Exact lowercase HTTPS DNS hostname, no explicit port (HTTPS443 implicit),
userinfo/path/query/fragment/wildcards/null refused. Direct WSGI host_url must
match; no forwarded-host/proto/IP trust. GET may omit Origin, all POST require
exact Origin (same-origin browser request omitting it refused). Proxy resolution
is future explicit deploy work. Resolver injected trusted callable, bounded
ASCII output via existing service; no JSON/IP override. Its implementation is
trusted code, not authenticated by callable/type alone.

Session/preauth cookies original __Host-gib_session/__Host-gib_pre, Path=/,
HttpOnly/Secure/SameSiteStrict, Max-Age30days/2hours; server session idle7days,
absolute30days. Each successful login mints a new token; existing preauth token
is bucket-valid/reusable until expiry (no new one-time claim). Logout removes
session/clears cookie; password change preserves caller, revokes other sessions.
Every protected news request calls whoami BEFORE reader and fails closed on
store errors, malformed config or revoked/expired session. No signed-in user
settings caches/global principal. Settings use session UID+CAS version, exact
schema and mandatory Republic. Hashes/passwords/session tokens never returned
in JSON; CSRF only original login/preauth/whoami protocol, never error/export
or URL. Account logging disabled to avoid exception traces; no audit-log claim.

7 focused tests exercise route denials, cookie/KDF persistence, two-user settings
CAS/export, Host/forwarded boundary, missing/hostile CSRF, news logout/expiry/
password fences, disposable Mongo flow/store outage, zero construction client
calls, collaborator/origin checks and legacy mutation refusal. No actual Atlas,
proxy/host serving, production auth/writes, shared multiworker limit or readiness
proof. Launcher/environment/original gates untouched.

<!-- END-ORIGINAL-DOC -->


<a id="doc-173"></a>

### Reference: `integration/apps_script_audit/README.md`

<!-- ORIGINAL-DOC {"bytes":6775,"path":"integration/apps_script_audit/README.md","sha256":"5948049385be05306a3cc6df2b05bfcef1fd9b52b82863c0731e985ab5ba440f"} -->
# Reviewed Apps Script 180 source-local audit

Strict schedule validation happens before trigger changes: exact HH:MM and
integer syntax, supported minutes/hours, weekly day, duplicate times and staging
capacity. Interval mode ignores unused DIGEST_TIMES. Only known managed handler
names are replaced. Unrelated handlers stay. Replacements are staged first;
create failure removes staged triggers and preserves the old schedule. Cleanup
failure and partial old-trigger deletion are reported for manual review. Google
trigger replacement is not transactional; duplicate timers can remain after a
delete failure. nearMinute delivery is approximate (+/-15 minutes), not exact.

HTTP 403 is visibly held in health/collection/digest/critical/weekly calls.
Non-200 responses and transport errors fail with fixed labels, no response body
or exception details in logs. No retry is scheduled. Digest acknowledgement
failure after a send reports unknown receipt state; this companion still has no
durable mail receipt gate, so a separately invoked later successful legacy cycle
can repeat articles. Legacy server mail routes remain held, and installing this
companion is NOT approved. Do not reopen them to use it.

25 trusted offline mock scenarios, one Python wrapper. Node VM mocks are not
isolation: host constructors expose process. Exact reviewed source is hash-pinned.
Only dummy fixtures, no real Google project, properties, triggers, network, mail
or deployment. Google quota/timezone/delivery and real Gmail receipt identity
remain unverified. Hash pins prove bytes, not production behavior.

Docs verified:
https://developers.google.com/apps-script/reference/script/clock-trigger-builder
https://developers.google.com/apps-script/guides/services/quotas

Historical canaries retained below describe superseded behavior, not current
trigger parsing/HTTP handling. The current structured audit is authoritative for
source-local scenarios; it is not production or receipt proof.

# Legacy Apps Script audit after P0 header migration

The reviewed source intentionally differs from the preserved original: fixed
HTTPS origin, header-only auth, redirects refused, cleanup request/trigger held.
The source pin in audit.js covers these exact new bytes. Historical send/mark,
trigger-rebuild and parsing defects remain explicit canaries, not fixed claims.
No Google script, properties, triggers or deployment was changed. Node VM mocks
are a trusted-code harness, not an isolation boundary. Companion auth tests are
in tests/legacy_geo/test_auth.cjs; seven route shapes use header credentials.
Real Google/Render behavior and migration of existing installations are unverified.

## Historical original-source audit (superseded auth transport/pin)

# Original Apps Script offline compatibility audit

Every result is offline, not production and not receipt proof. Original Code.gs unchanged. SourceSHA256 f23159b30f263e3a34cae29879900d73b23f6cf64fc6958f12712b7df484026a checked every childrun; source is preserved local copy, originating sourcecommit not independently verified here. Script compiles in NodeVM with only fake Google services, no direct require/process/fetch globals, but host-created mocks expose their host Function constructor and process via it. VM not a hostile-code security boundary; only hashpinned reviewed original code. Host Node process has normal filesystem/network powers and host mock constructor escape can expose them to original code. This is NOT an isolation or no-I/O guarantee. Only trusted exact-hash reviewed source may run; no unknown code or arbitrary scenario scripts. The escape self-test probes typeof process without I/O. child10s timeout, individualVM1000ms. Fake fetch throws on unmocked destinations/routes/responses, fake routes perform no actual requests, but no guarantee against host escape. Original routines may catch that failure, as source behavior; selftest proves directunmockedcall throws. No environment credentials loaded. Fixture addresses example.invalid and keyDUMMY_NON_SECRET only, never report them. Report logs content discarded; action kinds/counts only.

Run: python3 -m unittest tests.test_apps_script_audit, invoking node integration/apps_script_audit/audit.js. Python3.10.12/Node22.23.3.17 local scenario checks, one Python childwrappertest. Harness first hash/selftest then sendDigest cases then trigger/parsers then structuredscope report. No original Code.gs changes or Google project/properties/triggers/deployment.

Observed source behavior under fake services: empty skip, critical-only send/no mark, UTF8 fixture/order, non200/no send, truncated/replacement-decodedbad JSON throws, replacementcharacterHTML accepted, Gmail quota throw/no mark, markHTTP500 ignored with two-cycleduplicate sends, transportmarkfailurelogged, unbounded10000-IDmarkbody, allprojecttriggerdelete + partialfailure/no rollback, loose time/int parsing, dummydoGet. These are source-local outcomes, not Google/provider validation. NonUTF8 case is simulated already-decoded replacementtext, not a real Apps Script UTF8decode test.

GmailApp real no-messageID behavior and actual subjecttimezone/providerquotas/trigger limits are unverified external/API documentation questions, not proved by fake return or Utilities formatter. Source uses no receipt identity; original send-mark success doesn't establish receipt/claim policy. Open fetched-vs-displayed marking decision remains unchanged. At-least-once duplicate risk, durable atomicGeo-only claim/ledger/auth needed before delivery; no enabled sender here. Original doGet carries querysecret, not an approved publicsharing route. Trigger installer can delete unrelatedtimers, not allowed to install under this audit. Real mail/mark/collection/cleanup/deploy remain gated.

No live Apps Script connection or external API claim. Test fixtures and outputs contain only dummy values; audit script prints no recipients/URLs/keys/body/IDs. No runtime module imports this harness, no productionactivation path. Source fixture can include syntheticIDstrings, never actual DB identities.

Harness stdout is one labeled JSON line only, stderr empty on passing run. Unittest human output must be captured and prefixed offline_not_production_not_receipt_proof per physical line before publication; raw unittest output is not a report. Request mocks validate method/query/content-type and synthetic ID payload. Wrapper asserts exact17unique names/pass/sourcehash/top-levelscope and scans both output streams for URLs/IDs/addresses/dummykey. Partial-trigger-deletion failure tested.

Repro labeled stdout/stderr including child failure: python3 integration/apps_script_audit/labeled_run.py. Child timeout/failure wrapper suppresses exception details; this is display labeling, not sandboxing.

<!-- END-ORIGINAL-DOC -->


<a id="doc-174"></a>

### Reference: `integration/bcrypt189/README.md`

<!-- ORIGINAL-DOC {"bytes":1790,"path":"integration/bcrypt189/README.md","sha256":"93b156096a3c098fa10edb007bb8370db71d52208a71e9748e9fe0daceb466cc"} -->
# Optional bcrypt private preview verification

Stored PREVIEW_PASSWORD_HASH may be exact$2b$ cost10-14 canonical60chars, bcrypt5.0.0.
Legacy scrypt/PBKDF2 remains compatible and unchanged. Existing defaults stay OFF.
No hash migration, password changes, secret generation, account activation or
public login. Do not treat bcrypt as an upgrade over scrypt: OWASP recommends
Argon2id/scrypt first, bcrypt for compatibility. Keep config/cost review separate.

Password1-72UTF8bytes, rejectoversize insteadtruncate/prehash. Strictboundedformat
before import/hashing; canonicalterminalsalt/checksum bits, exactversion checked.
No expensive startup hash. Existingserialslot/ratequota/CSRF/cookie/logout retained.
Verifiererrorsfixed503,releaseslot,no exceptionsecretlogging. Hashes/environment
must still be set by owner securely; no exposure/rotation effect in this unit.

Publishedbinarywheel5.0.0downloadedfromPyPI,hashmatchesreleaseJSON; Apache2license
inspected, no runtime dependency; optionaltest/typecheck extras notinstalled.
Installedlocallywheel/no-sourcebuild,realcheckpwsmoke/tests;pip-auditnewdependency
only5.0.0returnedno-known-vulns. Notwholeappsecurityproof or reproduciblebuildclaim.
requirements-staging exactpin. Historical25packageofflineaudit/build records stay
unchanged; bcrypt is supplemental pinned_addition inventory with ownreceipt, not
silently added to old lock. requirements-future-deploy.lock oldlockdoes NOT install
bcrypt; don'tselectbcryptconfigonthatlockuntilseparatereviewedlockrefresh. No wheel
vendored, production/platforminstallation must use reviewed package index/artifact.

Sources:
https://pypi.org/project/bcrypt/
https://github.com/pyca/bcrypt/blob/5.0.0/README.rst
https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

<!-- END-ORIGINAL-DOC -->


<a id="doc-175"></a>

### Reference: `integration/bounded_rss/CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":1836,"path":"integration/bounded_rss/CONTRACT.md","sha256":"cd9d80e9a0104a72408b1f15290d2fd6cdbde66fd65418fbf8694f3a2aea40b7"} -->
# RSS177 bounded legacy seam (held by default)

The legacy RSS requests/feedparser names now point to one bounded driver, not
requests.content or an in-process feedparser. Import builds only a held driver,
never fetches. Explicit installation can construct an enabled driver with exact
reviewed feed tuples and projection1..200; mounting it and starting collectors
remain separate owner/runtime steps. Default catalogue unchanged25feeds. Custom
extras do not bypass installation. No unsafe fallback, no artificial dates.

Fixed124transport caps wire/decoded1MiB, streaming chunks64KiB, verifies every
DNS answer/public peer/TLS hostname, refuses redirects and bad framing, kills
and reaps its worker at deadline. Fixed128parser uses no-network bubblewrap,
pinned SDK6.0.11, memory256MiB/CPU3s,1MiB input/output and512KiB projected text.
Two phases share min25s/configuredtimeout. This is a phase budget, not a claim
of hard aggregate cycle/supervisor memory or wall containment. Dense XML,
non-UTF8, malformed/bozo, isolation absence and oversized entries are refused.

The original field/date selection is unchanged over a one-use opaque parsed
projection, never a parser URL or raw stream. Output errors are a fixed safe
source_refused label, without raw source names, URLs, query keys or exceptions.
A refusal yields zero candidates, NOT proof of a healthy source. Installation
health/status, full cycle supervisor, resource sizing, fulltext extractor and
live wiring remain held. Fulltext original still defaultOFF and unsafe to enable.

Historical117dependency-pins.json stays untouched; current supplied-cycle
preflight uses new dependency-pins177.json. Original108 inventory/reconciliation
stays source evidence; current consumer pins are explicitly refreshed only after
review of original selection/document differential tests.

<!-- END-ORIGINAL-DOC -->


<a id="doc-176"></a>

### Reference: `integration/build_provenance/CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":1399,"path":"integration/build_provenance/CONTRACT.md","sha256":"cd8f877dd314614ce4251a75f7c4da4953bfcdbb897453831e399b7c982fa155"} -->
Item18: source/build provenance alignment, not fresh data collection.
All four market-value sections matched the source, old active build, old orphan
and offline file before this change. The only active dataset difference from
current source build is the importer Baked comment: Oct4 becomes source Oct1.
No value is refreshed or inferred from that date. Source bytes remain unchanged.
Two builds with the same exact input hashes produce equal output bytes. The
receipt covers every flat src file (a conservative superset of actual reads),
build.mjs and the inflater, plus generated index/offline/SW/data hashes.
Two old root data files removed; their hashes retained in baseline receipt and
bytes remain in Git history. New data filename is its SHA256 prefix. No other
delete. Offline served-copy pin/cache test follows exact regenerated bytes;
network/key stripping still applies. Geo HOME/integration route structure unchanged.
History only includes merged bulk-import snapshot and a shallow original Oct7
snapshot. Cause/author/time of earlier comment drift cannot be established.
No deployment, network refresh, provider call, key/env/schedule/activation changes.

The baseline favicon/social head block was not in old build.mjs. It is now
kept verbatim in build source. No branding changes; source input hash records
this deliberate build change. Feature Finder index hash pin follows output.

<!-- END-ORIGINAL-DOC -->


<a id="doc-177"></a>

### Reference: `integration/collection_receipts/CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":2527,"path":"integration/collection_receipts/CONTRACT.md","sha256":"3aed8015514872a454f30c7c62dc2a717abb3a84fa8a227231d6a3d789537842"} -->
# Item6 protocol145: INERT, not durable implementation
Base e0f6e2b. Core protocol paths integration/collection_receipts/protocol.py and
tests/collection_receipts/test_protocol.py. Nine pure tests plus two integrated inventory/import-surface tests. Originals unchanged.
No transport/storage/import client/send/delete/ref update. No activation.

Required adapter must establish trusted identity, actual durabletransaction and
owner-approved destination. Supplied dict/hash/ID is not authentication proof.
commit_collection atomically articlepreview+fullrecord+outbox, immutable uniqueURL
reconciliation, exact per-record IDs/contenthash/version. No aggregate inference.
Alreadyterminal never resend, alreadypending reads STORED fullrecord, conflict
holds rather than overwrite. Unknown holds; transaction partial state reconciled.

Fenced CAS journal persisted before effects, per-piece durable started/ack state.
Provider receipt independently verifies destination+messageID+attempt+piecehash;
unknown return/crash latchesunknown and never auto-resends. Partial continues ONLY
unstarted pieces, durable confirmed state. Expired startedlease holds unknown.
finalize terminaljournal/outbox/refpublication atomicCAS of currentversion and
immutable destination/fullrecordhash, allpieces acknowledged; refs exact-idempotent
or failclosed. No fullrecordTTL/deletion. Plan chunkJSON reassembles complete record,
UTF16<=3000units, total1MiB; receiver needs journal piece ordering to reassemble.

Python protocol functions operate supplied state, NOT an authorization or forged-
receipt defense. Adapter must validate/reload stored journal, never accept state
from untrusted caller. publishable only gives supplied-state completion, not send,
refpublication or retentionpermission. No concrete transaction schema/driver
adapter provided here. Failclosed mounting requires adapter review first.

Remaining tests adapter-owned: actualCAS leasefencing/replay/rollback, duplicate
collect reconciliation, simultaneouswriters, refs immutability, unknownsend
reconciliation, durable restart, configured transactionavailability, permissions.

Review hardening: unhashable receiptURL/nonfiniteJSON/lonesurrogate now refuse as
ReceiptRefused,9tests pass. Lateack after unknown intentionally refused: adapter
must separately reconcile under authority/fencedstoredstate, no generic retry.
journal_new doesn't authenticate planrecorddigest; adapter reloads/recomputes
fullrecorddigest and orderedpieceplan beforepersisting; hash isn't receiptproof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-178"></a>

### Reference: `integration/db_contract/CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":4970,"path":"integration/db_contract/CONTRACT.md","sha256":"22dc5dc4265771e5928604c4c829baca943d2958b030288cd49f5962686d4cb5"} -->
# Database resources, indexes and retention proposal

Copyright (c) 2026 Push. All rights reserved.

No provisioning, client, DB write, delete, role, index, TTL, mount or activation.
Exact collector names must be coordinated before executable schemas. Tests use
fixture names, not approved live collection names. plan() takes explicit distinct
names for full_records, collection_outbox, collection_control and backup_journal.
Fixed existing mail/article resources stay geo_intel/articles/events/mail_control/
mail_receipts. Output is a candidate, not an authorization or persistence claim.

## Privilege boundary

Separate proposed publicreader, mailworker, collectionwriter, backupjournalworker.
Each grants explicit collection actions only (find/insert/update), no inherited
readWrite/admin role, createIndex, remove, drop, rolemanagement or cluster action.
Provisioning credential is separate and not modeled as a runtime role. Existing
read-only facade remains intact. Mongo role updates are collection-level, not
field-level: mail article update can modify more than emailed flags. Application
validation, isolated credential, transactions and actual role audit still matter.
Backupjournalworker has no article access. It records acknowledgements in its
journal/outbox; collectionwriter publishes preview Telegram references only
after authenticated complete-receipt validation. That publisher is a later
implementation, not assumed present.
These proposals are not proof that an Atlas free tier exposes custom role APIs or
that deployed accounts have only these privileges. Verify current account/tier.

## Index candidates, not executed

Unique articles.url requires existing duplicates/index/collation review first.
Unsent emailed+score+published+_id compound index, created_at, events.event_date,
mail_receipts channel_id+created_at are candidates for query explain/storage-cost
review. None is TTL. Existing implicit _id indexes support exact receipt/control
keys. Do not create duplicate/conflicting index names blindly. No guarantee that
a compound query candidate is optimal without real explain/index inspection.
Collector schemas/indexes remain interface requirements pending exact mappings.

## Runtime140handoff compatibility

handoff.prepare output is untrusted candidate data with all authority/durability
flagsfalse. Batch/record hashes bind bytes, not author, storage or recovery proof.
Retain full_record losslessly beside summary300 preview, not in the same TTL
lifetime. Commit preview+fullrecord+checkpoint/outbox transactionally with reviewed
version/lease fencing. Existing GeoArticleWriter unordered preview insert is NOT
that atomic commit and must not be reused as if it preserves fulltext/outbox.
AgentA owns the collector engine/fulltext/GNews/Telegram journal implementation.

The collection send journal must bind exact destination, record/batch/piece
payloadhash, attemptnonce+version and providerack. Record sending durably before
effect, unknown timeout/disconnect latches. Every required piece needs current
authenticated receipt before completebackup. Local MAC/hash fixtures cannot
prevent rollback/replay or prove provider acknowledgement. This proposal performs
no sends or receipt verification and cannot unlock a collector lease.

## Retention and TTL

No TTL on articles, fullrecords, pending/active mail receipts, collectionoutbox,
control or backupjournal. No automatic deletion anywhere. Terminal supplied
fullrecord+allpieceauth+export claims merely make a record eligible for owner
retentionreview; delete/TTLallowed remainfalse. Unknown/pending alwayshold.
Actual archiveexport/recovery evidence and ownerapproval required separately.
Never delete receipt keys while replay/newnonce could resend an old effect.
Save135mailarchive128cap is unchanged; operator must see failclosed and plan an
explicit reviewed retention/export solution, not enableTTL as a quick fix.
MongoTTL uses a backgroundprocess and BSONdates; ISOstring articletimestamps
are not equivalent expiry fields. No source-specific TTL or migration selected.

## Official source grounding (fetched October8,2026)

https://www.mongodb.com/docs/manual/core/security-user-defined-roles/
Customroles described with explicit privileges; actual Atlas availability unverified.
https://www.mongodb.com/docs/manual/reference/privilege-actions
find/insert/update apply to database/collection resources. Role is not field policy.
https://www.mongodb.com/docs/manual/core/index-ttl/
TTL is a special single-field automatic expiration index; background cleanup,
not a receipt-aware transaction or exact-clock retention guarantee.

## Delivery status

11puretests, proposedroles/indexes/retentiondecision only. No installed DB roles,
no schema/provisioning command, no durable writer, no completebackup claim.
Default-off routes and containment gate remain unchanged. Mail routing/credential
binding and production retention implementation remain later reviewed units.

<!-- END-ORIGINAL-DOC -->


<a id="doc-179"></a>

### Reference: `integration/db_contract/QUERY-REVIEW.md`

<!-- ORIGINAL-DOC {"bytes":2746,"path":"integration/db_contract/QUERY-REVIEW.md","sha256":"eece04ef7f7f11b92eae4c214ec122165e3c25aac5e1834b9c180c97762e429b"} -->
# Query/index and bounded export source contracts

query_plan.py lists candidate compound indexes tied to legacy score/published/title, unsent, critical/date and category/export access. No index is created by these contracts. Existing init_db behavior is retained; provisioning, explain, schema/date types, duplicates/collation and storage/write costs require actual target review and permission. Supplied explain_review counters are not authenticated live proof and never permit provisioning. emailed $ne true may scan widely; critical/date range plus score sort may still block-sort. No claim that all queries are index-covered.

Legacy list reads now cap at 2000, use driver maxTimeMS3000 and bounded batches; stable _id tie-breakers added where appropriate. Calls above the cap fail rather than materialize one million articles. Legacy export now streams newest-first descending _id keyset pages of250 with a frozen upper _id, max2000 rows,16MiB source/output budgets,8000-character cells,30sec wall checks and cursor cleanup. It is not a consistent snapshot: concurrent updates/deletes remain possible. Every field is allowlisted; CSV formula prefixes are neutralized. Export is explicitly not a complete full-record/recovery backup. Early failures return400/503; after headers, errors append an EXPORT_INCOMPLETE marker, never an ordinary successful empty export. Use a separately reviewed full-record recovery workflow for larger archives.

Nothing provisions Mongo roles/indexes, changes credentials/TTL or enables collection/mail/deletion. Before deployment review the 2000-row behavior change and endpoint consumers. Query-size and timeout tests use injected fake collections, not real Atlas explain evidence.

GENERAL preserves legacy missing/null category semantics through explicit $or branches. No duplicate _id index is proposed; MongoDB already supplies that index. The category/_id candidate must be explained with each branch on actual schema. explain_review checks counters only, never index coverage.

Call-site audit: reports/email_report uses events default2000; dashboard uses explicit120day events and24hour critical, each2000, article default now2000; WhatsApp/Telegram use recent default60 and events2000 sliced3; critical_alert uses default2000; telegram_archive uses default2000. At exactly2000 critical/archive records are returned; at2001 these complete-selection reads raise before any sender, rather than silently drop records. Archive deletion remains globally disabled; this does not make the legacy archive send/receipt protocol safe, which remains item6/10 work. Ordinary recent top-N and weekly top-N remain intentional bounded selections, not claimed full sets. Dashboard caller limit above2000 is rejected.

<!-- END-ORIGINAL-DOC -->


<a id="doc-180"></a>

### Reference: `integration/dependabot_security173/README.md`

<!-- ORIGINAL-DOC {"bytes":2196,"path":"integration/dependabot_security173/README.md","sha256":"8d946db57a55f25541cf378c5c0047dffb557e6165856771aafd6090bedfaa63"} -->
# Historical profile security supersession173

Only current offline candidate and built locks change. Frozen87/88/105receipts
and snapshots are unchanged observations, not relabelled new results. Staging,
futuredeploy, runtime/service settings and workflow files unchanged.

Flask3.1.3,Werkzeug3.1.9,PyMongo4.18.2,dotenv1.2.2inboth historical tracks.
Requests2.34.2candidate,2.33.0built: both cover patched2.33.0floor. Feedparser
remains6.0.11with original32source pins;Gunicorn22hereunchanged, candidate23
andbot26.2require separate evaluated source unit. Stagingdotenv1.2.4notdowngraded.

Candidate still explicitly misses sgmllib wheel hash and is not fully directly
installable; official changed wheels bytes/metadata verified. Built lock uses
fresh isolated sgmllib wheel from exact105source members; no deterministic wheel
hash claim. Original105artifact cache missing; rebuilt, new hash receipt recorded.
Build bubblewrap network namespace/clearenv/CPU/memory/file/wall/output caps and
killgroup/reap, fixed reviewed setuptools59.6.0wheel0.37.1system tools. Shared
hostCPython/OS/toolfiles not new reproducibility certification.

Fresh built environment hashed noindexonlybinary install andpipcheck observed.
Candidate changed package artifacts checked separately; no false candidate
fresh-install claim. Historical provenance remains frozen. Full gated tests and
actual package versions must be reported separately for configured vs built env.
No liveDB/send/collector/provision/cutover/alert dismissal follows local passes.

Authenticated owner SecurityUI at research time24openalerts: root/candidate
12+dependency_build12. Fivefamilies:PyMongo4pertrack(2high2moderate),Werkzeug4
pertrack(moderate),requests2pertrack(moderate),dotenv1pertrack(moderate),Flask1
pertrack(low). No botPRmerged. Recheck alert state after landing; never claim
resolved based on packageversionalone or expected count. BotPRcomments/closures
require explicit owner approval, not silence or sourcepush permission.

Review172followup tests: publicIP-literal host rejected by109feedURLgrammar;
trailingdot host rejected by113origin regex. Supplied fulltext policy remains
partialOFF, no realfetch/extractor proof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-181"></a>

### Reference: `integration/dependency_audit/README.md`

<!-- ORIGINAL-DOC {"bytes":4525,"path":"integration/dependency_audit/README.md","sha256":"540c63d9ede5956d14aca3000844f6de576625ea5012b8ec05e940deb757b9f8"} -->
## Historical receipt, superseded current lock

This document and its JSON receipt describe historical increment87/88, not the current lock. Current pypdf105 supersession: ../pypdf_remediation105/README.md. Original lock bytes/hashes remain in historical-locks.json and git d8f8902.

# Offline dependency audit: candidate blocked, not an installable lock

Scope CPython3.10.12/Linuxx86_64, static integration/tests/scripts AST inventory,
minimum staging+discovered unittest+original pure AST fixture support. Original
requirements-staging and Geo/BRICS requirements unchanged. Configuredvenv unchanged.
Inventory records installedmetadata import->distribution mappings and direct/
transitiveRequires-Dist with active/default-extra markers. Standard/local/unknown
imports and dynamicimport files retained, static discovery NOTcomplete runtime
proof. Intentionally excludesmanualPlaywrightbrowser scripts/binaries; noimport
of arbitrarypackages merelytoidentifyversions. Node22.23.3 separatetestprerequisite.

25distribution closure audited,24compatiblewheels inexplicit/downloads/wheels68.
Exactfilename/version/tags/SHA256 in audit.json. sgmllib3k1.0.0 hasonlysdist present,
SHA256 recorded, inspectedsetup.py importssetuptools/readsREADME; noofflinebuild
performed and no wheel hash fabricated. Noambientindex/cache, latest/no-deps/pin
loosening. requirements-offline-reviewed.candidate.txt deliberatelylabelledNOT
INSTALLABLE hashedclosure because missingwheel/hash. It is NOT environment-frozen
proof, a productionlock or freshinstallclaim. Cachefiles privateworkspace/local,
notpublisheddependencybundle or promiseduser-accessibleartifact.

Separate outcome statuses:artifactclosureBLOCKED; offlineinstall/importsmoke/
freshSDKbackendchecks/freshsuite NOTATTEMPTED. Configuredsuite regression evidence
only. Anewvenv sharesbaseCPython/Expat, not reproducesOS/interpreter. 85 requires
feedparser6.0.11plus32SDKsourcehashes, sgmllibsourcehash andExpat2.4.7; matchingwheel
versionsalone insufficient. ExistingSDKpins in integration/feedparser_audit and
resourcechild verify them locally, NOTfreshenvverified. No OSnetworkisolation.

Optional pikepdf missing ->weekly_report.test_report.Writer.test_external_validators
skip. trafilatura absent separatelypreserves unavailable-provider baseline, notPDF
skip. Neither added silently. Xfailaccounts.test_reservation_terminal.ReservationTests.
test_UNSUPPORTED_two_limiter_compensation_marker_interleaving remainsunfixed, not
passproof. ManualPlaywright1.48/greenlet3.1.1/pyee12/browsers excludedminimumlock.

INERT futureinstructions ONLY AFTERcompatiblemissingwheelclosure is suppliedand
allhashesvalidated, neveragainst configuredvenv:
1. Createanewdisposablevenv with matchingCPython/OS/Expat baseline.
2. Install completeapprovedhashedlock using pip --no-index --find-links <explicit
   verifiedartifactdirectory> --require-hashes -r <completehashedlock>.
3. Verify transitiveclosure/pipcheck, importonlyreviewedpuremodules, SDKphysicalpins
   andbackend, thenfullconfiguredtests includingNodeprerequisite.
DoNOTrun currentcandidateascomplete. Noexternalpipfetchauthorized orneededforaudit.
Eachfuture subprocesswall/outputmustbound,kill/reap; importmonkeypatchnotOSfirewall.
No productioncollector/configimport/liveRender/DB/credentials/deploy/readinessclaim.

Auditjson environment/sourceinventory is localcontext, notsecrets. Tests verify
hashes/cacheclosure/version/markers forrecordedcandidate; noactivation sideeffects.

Revision87 review correction: inventory is bound to revision86
4d7f7f342140a144f429d03f82b94a3176f341c2, with all263 scoped Python paths and
SHA256s. Scanpolicy/exclusions recorded; currentfiles checkedagainst baseline.
Eachimport is classified stdlib/local/required_distribution/optional_absent/
excluded/unresolved. Metadatafilepaths resolve flask/werkzeug/bson/pymongo/pypdf
where packages_distributions omitted them. Provenance retained; unresolved=[]
for this static scope only, not runtime completeness. Namespace/local paths
are recorded, not inferred dependency absence.
Seven focusedchecks cover activeclosure/specifiers/markers, canonicalunique
names, exactperdistributionlockhash equality, wheelbytes/tags/METADATAincluding
activeRequiresDist, completeclassifications and baselinefilehash/ASTconsistency.
Unavailablecache is an explicit UNVERIFIED unittestskip, never hashverification
success; authorcacheavailable and all24 wheelbytechecks pass. Independentreview
hasnocachebytes unless transferred. No freshinstall/importclaim added.

<!-- END-ORIGINAL-DOC -->


<a id="doc-182"></a>

### Reference: `integration/dependency_build/README.md`

<!-- ORIGINAL-DOC {"bytes":3399,"path":"integration/dependency_build/README.md","sha256":"a5677f5e86dd1dc6328f1b8b7cbca47cc35ca4752e07b54450c72ebfe9ec2fd4"} -->
## Historical receipt, superseded current lock

This document and its JSON receipt describe historical increment87/88, not the current lock. Current pypdf105 supersession: ../pypdf_remediation105/README.md. Original lock bytes/hashes remain in historical-locks.json and git d8f8902.

# Separate offline build and fresh-install experiment

Increment88, separate from immutable87 blocked audit. Receipt records source
members/hashes, build-tool Python-file metadata, interpreter and exact argv,
isolated stages, produced wheel and complete installed metadata. Orchestrator
text is the executed evidence, NOT a general-purpose installer or launcher.
It uses fixed author scratch paths and reviewed inputs; do not run it blindly.

Bubblewrap unshare-all enforces separate network/user/mount namespaces, only
/usr,/lib,/lib64 read-only plus writable scratch, /proc and /dev. No host home,
project credentials, downloads or inherited env/PYTHONPATH/user-site. Explicit
controlled HOME/TMP and resource CPU60s/AS1GiB/FSIZE64MiB, wall120s/output1MiB,
kill-process-group and reap. Probe verified missing host paths and refused
external connection before setup execution. This is a local Linux boundary,
not a certificate for arbitrary code, other hosts or production collectors.
Build script/setup/config/README/source exact bytes reviewed. Archive permits
only regular files/directories, <=32members/100000bytes, no traversal/links/
devices. Wheel equivalent limits, metadata one Name/Version, no dependencies,
compatible tags, same sgmllib source hash. Single build: deterministic wheel
bytes NOT claimed. Original87 lock/requirements/configured venv unchanged.

25 verified wheel hashes in separate requirements-offline-built.txt. Fresh
venv has no system-site-packages, explicit copied/rehashed artifact directory,
--no-index --no-cache-dir --only-binary=:all: --require-hashes; pip-check and
metadata closure verified. pip/setuptools are bootstrap, not app closure.
Base CPython/Expat/OS shared with host, not independently reproduced. Tool
Python-file hashes are recorded, not every shared-library/interpreter input.

Smoke allowlist feedparser/sgmllib/dateutil.parser/xml.parsers.expat only.
Unchanged85 guarded child verifies32feedparser Python pins, sgmllib source,
Expat backend and fixed RSS original-AST oracle. No production config imports.
No trafilatura or pikepdf silently added, no manual Playwright/browser binary
reproduction. Fresh full-suite is separate and pending until recorded.

Private wheel/artifact bytes are in author scratch, not published by this
receipt. A text lock alone is not a usable distributed artifact bundle.
No live functionality/Render/Atlas/delivery/cutover claim follows any pass.

Review correction: original executed runner had cleanup gaps and is retained
only as historical evidence. runner.py replaces capture: deadline begins just
after Popen, drains until both EOF and exit, bounded nonblocking stdin/output,
finally kills process group and reaps on every path. Fault tests cover closed
stdout-then-sleep, crash, oversized output and wall timeout. The separate
post-build Debian tool-hash fallback is preserved with command/digest/timing;
it is not represented as part of the original build entrypoint. Source copy
is writable scratch, NOT a read-only project mount. Future full suites run
from copied scratch, never production source/service credentials.

<!-- END-ORIGINAL-DOC -->


<a id="doc-183"></a>

### Reference: `integration/feedparser_audit/LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3237,"path":"integration/feedparser_audit/LIMITS.md","sha256":"755e8e7d392de3e5e2b1c26b15cafe950ce070f8221ac4463940cdaeaa5efb15"} -->
# Fixed public-synthetic RSS/Atom parser experiment

Seven closed internally generated hash-pinned corpus enums only, no caller XML,
URL/path/filebytes/module/argv/env. Synthetic corpus<=64KiB, noSYSTEM/PUBLIC
externalDTDs/entity/resource references; boundedinternalentityonly, nobombs.
This is realfeedparser6.0.11 parsing FIXED syntheticBytesIO data, notlivefeed.
BytesIO bypasses _open_resource filenameprobe beforebytesfallback. Actual SDK32py
files plus sgmllib.py hash pinned; backendExpatParser/expat_2.4.7 checked. Inspected
SDKapi.parse strictSAXexternalgeneralentitiesdisabled,replace_doctype stripsDTD/
reinsertsregexsafeentities. No currentexternalprovider/SDKbehaviorclaim beyond
inspectedlocalimplementation. Standardlib/Expatversionchecked, notbinaryhashpin.

Linuxresourcecontrolsrequired. ChildCPU3s,AS256MiB,FSIZE1MiB; parentwall10s;
combinedstdout/stderr1MiB streamingselectors cap,stdin<=16KiB; fixed executable
sys.executable/fixedchildpath/cwd,envonlyLANG/LC_ALL/TZ/PYTHONPATHcodepath. No
inheritedapplicationcredentials. Kill/reap ontimeout/overflow/childexit/protocol,
noautomaticretry/partialsuccess. Trustedtestpatchesinjectfaultchildren,notruntime
parameters. Limitshardboundsresearch, nothostilecode/OSnetworkisolation.

Socket/create_connection/urllibrequest/openerblocked BEFOREparserimport,SDKhttpget
blockedbeforeparse. Threeattemptguardselfchecks. PythonmonkeypatchnotOSfirewall:
no generalno-I/Oproof, fixedtrustedfixturesonly. Filesystemreadingcode/SDKallowed;
no arbitraryresources. Noexternalreferencecorpus or realresolverfetchtested.

FeedParserDict SDKentries projectonlyinspected scalar title/link/summary/description/
published/updated usingSDK.get exactlyoriginalalias semantics. Fieldpresence
isget-visiblepresence, notrawXMLtagpresence. Rejectunsupportedscalars/oversized
entries, no strcoercion. Bozobool+fixedlabelseparate, bozoentries selectableexactly
originalstyle, nothealthy/completeness. Missing/emptydate fixedfallback,partialdate
explicitUTCdefaultDEVIATION andunknownzoneunverifiedfallbacksame81. Fixedaware
cutoff/fallback UTCyear1970..2100,maxitems1..100. Childselectionexact81 andseparate
originalAST_fetch_feed oracle withrealparserBytesIO/inertresponse andfixeddate
policy in SAMEguarded/resourcechild. Originalmodule/config/requestsnotimported.
Originaldate/classifier functions ASTonly, sourcepinscheckedbeforeexecution.

ClosedplainJSONoutput exactversion/corpus/configecho/fields,<=100entries/candidates,
Budget1MiB/5000nodes, scalarboundedstrings/datevalidatedafterUTCnormalization.
Parentchecksprotocol/budgets/fixedcase/hash/echo; childstderrrefusesdiscardrawtext.
No rawsourcelogs/exceptions, no source health/HTTPtimeout/XMLarbitrarysecurityproof.
No composition80/fulltext/store/mail/Telegram/runtimeactivation orUIartifact.

7authorfocusedPASS sevenparsercases includingbozowith/withoutentries,Atomcontent/
Unicode/presence/datefallback/oracleagreement; invalidentityconfigbeforespawn,
fixturehashdrift,timeout/crash/protocol/outputoverflowkillreap. Noarbitraryparser
inputtests beyondfixedcorpus. ExternalguardtestcallsPythonblockedinterfacesonly.
SDKversion/drift andtrustedimports nothostilecodeauthentication. Independent
codereview/fullconfiguredsuitepending.

<!-- END-ORIGINAL-DOC -->


<a id="doc-184"></a>

### Reference: `integration/fulltext_policy/README.md`

<!-- ORIGINAL-DOC {"bytes":1621,"path":"integration/fulltext_policy/README.md","sha256":"453b5ee9cf7e46a201905bf2d82f9902dc44f54e596d0f9ae772aaeb3c1ff315"} -->
# Partial item16: inactive article endpoint and supplied-body policy

DefaultOFF. No URL is learned from feed results: installation must name exact
HTTPS article URLs, max64. Refuse credential URLs, controls, whitespace,
fragments, private/mixed DNS answers, rebinding peer changes and redirects.
Shared transport113 supplied evidence decoder caps raw/decoded bytes1MiB,
chunks64KiB, headers32/2000chars, compression/framing and deadline checks.
This adapter does not fetch or parse; bytes are untrusted and remain undecoded.

DNS/peer inputs are synthetic evidence, not actual verified network. Installed
fetch124 already pins public address/TLS peer and whole-fetch subprocess wall.
It is not invoked here. Extraction remains blocked until reviewed/pinned
trafilatura dependencies plus no-network parser containment and hard aggregate
fetch+extract supervision exist. No fallback to original fetch_url. The legacy
extract.py and supplied AST experiment are unchanged, not called secure live
fulltext. GNews remains supplied SDK results only. Neither optional provider is
claimed installed/live-ready by this seam. Do not enable collector/fulltext live.

Remaining item12 backup choice: telegram_backup.py full-record URL field is
stored raw as article evidence; it is not the clickable report URL boundary.
Changing/omitting it would alter complete source record preservation. Preserve
it pending reviewed record schema/receipt migration, never call backup metadata
sanitized/lossless/complete from this alone. The legacy archive import remains
blocked by absent config fields; purge/sends remain outside this adapter.

<!-- END-ORIGINAL-DOC -->


<a id="doc-185"></a>

### Reference: `integration/geonews_digest/README.md`

<!-- ORIGINAL-DOC {"bytes":5324,"path":"integration/geonews_digest/README.md","sha256":"734269a0cef4fd49c46ecb5f9d3a0cca8fa1c7b6fbfb4d61c5f85745e511aaf4"} -->
Copyright (c) 2026 Push

# geonews_digest (digest, critical alert, weekly summary, chat digests)

Port of the report behaviour of the public repo `push2006/geonews` (commit d0937ab66c20122cbd33e7385ec577914c506c73, 2026-09-22) as pure modules. Selection rules, ordering, limits, thresholds, section order, wording and colours follow the original; see the table below for the few deliberate differences.

Standard library only. No database, network, timers or file/env reads at import or in the build functions. Delivery code (SMTP mail, Telegram Bot API, CallMeBot WhatsApp) is present in `delivery.py` but OFF: nothing is sent unless the caller passes `enabled=True` (exactly `True`) and supplies credentials as arguments and a sender. Default calls return a dry-run `Outcome` with the subject and body and mark nothing.

## Interface
- `normalise_all(rows) -> (articles, stats)`: accepts the legacy geonews row shape and the public news shape; drops unknown keys (telegram_*, backup_url, ...); https links only; aware dates only; bounds on every value.
- `build_digest(articles, events, now, settings) -> Digest` (`.html`, `.subject`, `.critical_count`, `.refs`, `.to_digest_data()` = the `/digest-data` JSON shape), `should_send_digest(d)` (Apps Script skip rule).
- `build_alert(items, now)`, `model.critical_since(...)`, `build_weekly(articles, now)`, `build_telegram_message(...)`, `build_whatsapp_message(...)`.
- `deliver_digest / deliver_critical_alert / deliver_weekly / deliver_chat(...)`: build, and only with `enabled=True` plus a sender, send; the digest marks items sent via your `mark_sent(refs)` callback only after a confirmed send; failed sends mark nothing. Retry count and an injected `sleep` replace the original 3 x 30 s loop (no timers here).
- `parse_mark_request(payload, known_refs=None)`: validation for the `/mark-emailed` call.
- `smtp_sender / telegram_sender / whatsapp_sender(enabled=..., credentials...)` -> sender closures. Errors never contain tokens, passwords or URLs.
- `Settings`: defaults equal geonews (min score 4, 60 per digest, 90 upcoming days, 6 h critical lookback, 7 days / 20 items weekly, 8 countries, 8 and 6 chat items). `display_tz` defaults to Asia/Kolkata and every printed date states its zone.

## Deliberate differences from geonews
| Area | geonews | Here | Why |
|---|---|---|---|
| Links | any URL, only HTML-escaped | https only, default port, no credentials | `javascript:` etc. cannot reach mail |
| Dashboard link | `?key=<TRIGGER_SECRET>` in mail and Telegram | plain https URL only; secrets are refused | secret in a message is a leak |
| Telegram text | raw Markdown | `_ * ` [ \` escaped in titles/names | a title with `_` or `*` makes the API reject the message |
| Dates | server local time, no zone | caller `now`, zone shown | owner rule: dates carry the time zone |
| Data source | MongoDB queries | caller supplies rows; queries re-implemented as pure functions | no live DB in this stage |
| Empty weekly top list | prints an empty heading | adds "No items in the supplied data... does not mean nothing happened" | do not read silence as quiet |
| Weekly ties | Mongo leaves ties unordered | ties sorted by name | deterministic output |
| Recipients/subject | not validated | recipients validated, CR/LF in headers rejected | header injection |
Everything else (sections, labels, risk and credibility colours, "confirmed by N sources", critical count, event block, footers) is the same text.

## Deliberate behaviour changes (review round 2)
- Digest: items below min_score are dropped BEFORE the 60 cap, so the refs marked sent equal the items shown. (geonews capped first and marked unseen low-score items as sent.)
- Critical alert: the caller supplies `alerted_refs` and `mark_alerted(refs)`; items already alerted are skipped and refs are marked only after a confirmed send. (geonews re-alerted the same items on every check in the 6 h window.) Items without a ref are never alerted.
- If marking fails after a confirmed send the outcome is `sent` with note `mark failed` (never reported as failed, which would cause a re-send).
- Telegram: token/chat id format-checked at construction; malformed requests become `DeliveryError('invalid request')`; URLs are escaped (`_ * \` [`, `)` as `%29`); long messages are cut at a line boundary.
- Bidi/format characters (U+2066-2069, U+061C, U+180E) are stripped from text. Missing zone database falls back to fixed +05:30.

## Still as in geonews
- Chat digests take the best 60 by score, keep score >= 4, then the first 8 (Telegram) or 6 (WhatsApp).

## Not ported (out of this module's scope, see PATCH.md)
Collectors, classifier and dedupe (other merged modules), Telegram full-record backup/archive and Mongo metadata cleanup (destructive), dashboard and CSV routes, the scheduler loop and Apps Script triggers (timers), digest archiving to disk (the caller can store `Digest.html`), config check.

## Checks
`python -m unittest discover -s tests/geonews_digest -t .` (34 tests). A development-only parity script (not shipped in this bundle) ran geonews' own database and report code on an in-memory Mongo fake and compares what is selected, its order, counts, section order and the chat texts with this module: all pass for the 150-row fixture. Not checked: how the HTML looks in a mail client.

<!-- END-ORIGINAL-DOC -->


<a id="doc-186"></a>

### Reference: `integration/geospatial/README.md`

<!-- ORIGINAL-DOC {"bytes":1594,"path":"integration/geospatial/README.md","sha256":"1324fc92895bc610c1427be788bf2936334cb787fa2bd60634dde30cd5f3f8d2"} -->
Copyright (c) 2026 Push

# geospatial (offline display modules)

Python (pure, no I/O): `validate_features(items)->(features,report)`, `ship_view(observation, now, stale_after=15min)->dict`,
`map_payload(news_features, ports, chokepoints, ships, now)->dict`, `project(lat,lon)`, `bbox_rects(bbox)`.
JS (ES module): `mountMap(element, payload, options)` and `dispose(element)`; link `geo_map.css` (no inline style needed).
Ship age threshold 15 min is a proposal: AIS position reports normally arrive within seconds to minutes.
Caps: 1000 features, 1000 ships in, 500 ships shown, 200 news; truncation is flagged.
No tile, network, stream or key use. Preview/fixtures are synthetic.
CSP needs for this offline build: script-src 'self' (module), style-src 'self', img-src 'self' data:, connect-src none.

Notes: items may carry `"fixture": true`; the table then appends "(fixture)". News `risk_level` text, when supplied, passes through unchanged;
this package derives no risk, threat or congestion value. Wrong-kind feature rows are counted in `report.wrong_kind_dropped`.
Stale ship markers are dimmed. Markers at longitude +-180 are inside a padded viewBox.

URL rule (Python _safe.safe_https_url and JS safeUrl): printable ASCII only (percent-encode the rest), https scheme, no "@" in the authority,
hostname [a-z0-9.-] with alphanumeric ends and no "..", last label not all digits, port <= 65535. JS also runs new URL() and may reject a few more
(for example malformed xn-- labels), so: JS accepts implies Python accepts. Tested with fixed vectors (exact match) and a seeded fuzz (one-way).

<!-- END-ORIGINAL-DOC -->


<a id="doc-187"></a>

### Reference: `integration/geospatial/data/DATA_SOURCES.md`

<!-- ORIGINAL-DOC {"bytes":2240,"path":"integration/geospatial/data/DATA_SOURCES.md","sha256":"4b831a3711029c24fa183938e78fafcbe627274ce97cdf2bd0be8581dfff7dc2"} -->
Copyright (c) 2026 Push (wrapper/selection). Wikidata coordinates are CC0; no other third-party text is copied.

# Reference data status (retrieved 2026-10-04 20:36 UTC, 2026-10-05 02:06 IST)

## chokepoints_wikidata.json - REAL data, 12 rows
Source: Wikidata via its API (wbgetentities, props labels/descriptions/claims/info), read once, polite rate. Each row's
coordinate is the single P625 value of the item, normal rank; revision id recorded per row in field wikidata_revision. Each item page returned HTTP 200:
https://www.wikidata.org/wiki/Q79883 (Strait of Hormuz), Q48359 (Malacca), Q83318 (Bab-el-Mandeb), Q899 (Suez Canal), Q7350 (Panama Canal),
Q35958 (Bosporus), Q6514 (Dardanelles), Q36124 (Gibraltar), Q104662 (Oresund), Q159898 (Dover), Q127031 (Taiwan Strait), Q4092 (Cape of Good Hope).
Licence read at https://www.wikidata.org/wiki/Wikidata:Licensing : "All structured data ... is released into the public domain under Creative Commons Zero."
Item identity: chosen from wbsearchentities results by label and description (e.g. Q4092 is the headland, not the colony or paintings).
Limits: points are display centres only. Canals (Suez, Panama) and the Cape headland are single points. Coordinates were sanity-checked
by the builder against general geography, NOT against a second independent source. The EIA page
(https://www.eia.gov/international/analysis/special-topics/world_oil_transit_Chokepoints) returned only site navigation text when fetched, so the
name cross-check against EIA was NOT done. The list of 12 is the builder's own selection; no volume or status claims are made.

## Ports - NOT included
Natural Earth ports page https://www.naturalearthdata.com/downloads/10m-cultural-vectors/ports/ shows version 5.0.0, "derives from High Seas ... in the public domain".
Terms page https://www.naturalearthdata.com/about/terms-of-use/ says all Natural Earth vector data is in the public domain.
But the download links on that page (observed href .../http//www.naturalearthdata.com/download/10m/cultural/ne_10m_ports.zip, also ?version=4.0.0 and 2.0.0)
all returned HTTP 500 on 2026-10-04, so no port rows were created. Not guessing other download URLs.
NGA World Port Index: excluded (licence wording not verified).

<!-- END-ORIGINAL-DOC -->


<a id="doc-188"></a>

### Reference: `integration/india_open_data/README.md`

<!-- ORIGINAL-DOC {"bytes":5484,"path":"integration/india_open_data/README.md","sha256":"cdf6cac8e8952e990fedb421116ce3b78e218eb8976c3fb2fbc78b142de826a5"} -->
# NITI / India government open-data backend review candidate
Copyright (c) 2026 Push. All rights reserved (new code only).

Pinned base: 739107f95affa02d828e72005991586025278538.
New files only. No original entrypoints, features, workflows, metadata manifests,
credentials, Render service or databases changed. Police track was dropped.

## Ready for code review, not live data readiness
- Strict bounded CSV/JSON imports with exact reviewed column mappings.
- NDAP exported snapshots supported. No invented NDAP API or dataset IDs.
- Optional injected export pull and OGD resource pagination; disabled by default.
- Standard-library HTTPS transport: verified TLS, pinned public DNS address,
  no redirects/cookies/proxy-environment/retries, sanitized errors, size limits.
- Canonical observations: original metric/unit/period/geography, decimal value,
  stable identity, source date, payload hash, publisher/source/rights provenance.
  Missing values are not zero; unknown dataset dates do not become fresh now.
- Atomic supplied-map snapshot candidate and read interface. Data stays in its
  own dataset layer, never coerced into article schemas or overwriting news.
- Separate proposed storage resource contract, no client creation, Mongo
  writes, index creation, TTL, deletion or route registration.

## What remains before live use
A verified dataset export/OGD resource, real headers/units/dimensions, permitted
reuse/required attribution and provider limits. Operator must provide exact new
collection mapping, transactional store adapter, non-public server credential
handling and mount into the reviewed app. No source has been called by this
backend, and no real NDAP dataset fixture or authenticated API smoke was run.
Unknown numeric quotas and API availability are not success claims. The strict
OGD shape may reject a legitimate dataset with different response metadata;
review its actual schema rather than loosening validators blindly.

NDAP exports requiring browser login, expiring signed URLs or non-CSV/JSON
formats must be downloaded through an approved route and passed as bytes.
This transport does not automate accounts/login, use undocumented NDAP APIs,
follow cross-host redirects or parse PDF indicator tables.

Only a complete validated nonempty snapshot may stage replacement. Failed,
partial, held and disabled pulls retain the old supplied snapshot. An empty
source is held, not treated as deletion authority. A published numeric change
updates a stable observation key; a duplicate/underspecified identity holds the
whole batch. No automatic merging of changed district boundaries or LGD codes.
Caller must include additional dimensions in metric/row-id mapping where needed.

## Example offline use (fixture, not real government facts)
```python
from integration.india_open_data.core import source_spec, import_export, stage_snapshot
from integration.india_open_data.data_layer import GovernmentDataReader
spec = source_spec(
    dataset_id='niti_reviewed_export', publisher='NITI Aayog',
    source_url='https://ndap.niti.gov.in/', provider='ndap_export',
    dataset_date=None, coverage='Explicit coverage from actual dataset',
    columns={'metric':'Indicator', 'value':'Value', 'unit':'Unit',
             'state':'State', 'district':'District', 'period':'Year'},
    license_url='https://ndap.niti.gov.in/', reuse_reviewed=False)
# Actual bytes/headers and rights review still required; URLs above are portal
# placeholders only, never claimed to be verified dataset/license permalinks.
records = import_export(b'Indicator,Value,Unit,State,District,Year\nDemo,1,count,TN,Demo,2021\n', 'csv', spec)
snapshot = stage_snapshot({'state':'complete','records':records}, {},
                          'niti_reviewed_export', '2026-10-08T23:00:00+05:30')
view = GovernmentDataReader(snapshot).read('niti_reviewed_export', limit=100)
```
Rendering/display of untrusted imported text must use the existing HTML escaping
and CSV formula guards. The module returns data, not safe HTML/CSV cells.

## Review test command
From repository root:
`python3 -m unittest discover -s tests/india_open_data -v`
All tests are synthetic/offline. No visual deliverable/UI changes.
No full application regression, dependency inventory refresh or preservation
manifest changes included. Builder must perform those after integrating additions.
Socket timeout is per operation; production worker needs total-runtime cap.
Pagination cannot prove snapshot isolation if provider changes rows mid-pull;
prefer published static exports or dataset-version verification for live use.

## Accepted fail-closed limits
Control characters are a hard failure in labels and source specification text.
In particular, multiline CSV labels with embedded newlines/tabs are refused,
not silently flattened or altered. Duplicate observation identity rejects the
entire dataset, even if duplicate numeric values agree.
GovernmentDataReader's 10,000-row cap applies across ALL datasets in its supplied
snapshot map, not 10,000 rows per dataset.
DNS getaddrinfo has no timeout; socket timeouts do not bound DNS resolution or
total wall-clock duration. Every live pull must run in a bounded worker with an
external overall deadline and termination/reaping on timeout.

The additive landing delta accompanies this bundle. It describes new paths,
AST/import/hash entries only. It is not a replacement for the repository's
existing preservation/staging/import audit manifests or their landing gates.

<!-- END-ORIGINAL-DOC -->


<a id="doc-189"></a>

### Reference: `integration/india_open_data/SOURCES.md`

<!-- ORIGINAL-DOC {"bytes":3385,"path":"integration/india_open_data/SOURCES.md","sha256":"ec57c5934cdd26d41e02daded900f885f42aacae5f00537d5669f69c87bc2b68"} -->
# NITI and India government data source ledger
Checked 2026-10-08. Research supports adapter preparation, not dataset activation.

| Source | Publisher/type | Evidence and scope | Status |
| --- | --- | --- | --- |
| https://www.pib.gov.in/PressReleasePage.aspx?PRID=1825145 | PIB, primary announcement, 2022-05-13 | NDAP was launched for open public use. Datasets may be downloaded and merged freely; common schema. | Fetched; historical statement, not present API quota guarantee. |
| https://www.niti.gov.in/divisions/division/data-management-and-analysis | NITI, official program description | NDAP hosts government datasets and supports analytics/integration. | Fetched, no API contract. |
| https://ndap.niti.gov.in/ | NITI, current portal | Portal exists, fetch only exposes loading shell. | No current dataset download URL or public API verified. |
| https://niti.gov.in/whats-new/walkthrough-ndap-portal | NITI, current walkthrough page | Official walkthrough PDF link. | Fetched; PDF is image-only in local text extraction, not interpreted as API docs. |
| https://www.data.gov.in/apis/2ed5b97a-d5bc-404b-a8f3-2a08f20c0b8f | OGD, official API detail page | Generate API Key control. | Fetched; no full API response/quota contract in accessible text. ID is a research lead, not configured live dataset. |
| https://punjab.data.gov.in/Godl | OGD Punjab, official legal terms | Royalty-free use of covered data; mandatory provider/source/license attribution, no endorsement, no warranty/update guarantee, exemptions including personal/sensitive information. | Fetched; dataset-specific applicability still requires review. |
| https://data.gov.in/sites/default/files/NDSAP_OpenDataLicense.pdf | OGD, legal primary document | License document found in search and fetched. | Official terms independently read at Punjab OGD mirror above. |
| https://econabhishek.github.io/datagovindia/ | Open-source wrapper authors, technical implementation docs | OGD resource path, api-key, offset and limit conventions; account/key requirement. | Fetched; no wrapper dependency copied or installed, no example keys used. |
| https://puredevkit.com/api-guides/data-gov-in/ | Independent technical guide | Describes free key registration and dataset-specific quotas. | Fetched; site also labels service freemium. Official quota/free-tier endpoint not verified. Do not promise unlimited access or paid fallback. |

## Cost boundaries
New backend uses only Python standard library; no paid provider, packages or
billing rail. NDAP download/merge free statement is official but historical.
OGD key generation is visible officially; free registration/API conventions are
corroborated by independent technical documentation. Current numerical quotas,
paid-tier boundary and continued availability remain unverified. Any 401/403,
429, redirect/challenge or quota failure stops the call without retries, upgrade,
scraping workaround or payment. A 100-row page cap, 100-page cap, 10,000-row cap
and byte limits are OUR safety limits, not government-published quotas.

## Rights boundary
Push owns new code. Imported government data has its own terms. Do not remove
required provider/source/data-license attribution to satisfy code copyright
preferences. No real data is included. Set reuse_reviewed only after the actual
dataset's rights, attribution, non-sensitive status and intended use are checked.

<!-- END-ORIGINAL-DOC -->


<a id="doc-190"></a>

### Reference: `integration/manage_fixture95/LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":1574,"path":"integration/manage_fixture95/LIMITS.md","sha256":"3655e88ddea3f152072f07b6bd87cffe888eb91a1ca42ef04a3af4cbd6771373"} -->
# Manage95 partial backend fixture

The catalog covers four families: Nilgiri watch, Tender, Finder and stored news. It is not a complete feature inventory. Each row points to files verified at source commit 0fef9a26a15887cb02a8281222c67155c447664a. Evidence hashes are in evidence.json. Tuning defaults are authored fixture values, not live settings.

Every row starts with requested state unspecified, last-known configured state unknown, and effective state unwired_unknown. A supplied authorized caller can record an ON or OFF request, but no request is applied to a runtime. Activation is disabled. Register only adds a known inert adapter to RAM.

Authorization and the expected revision are checked under one lock before a mutation. The closed batch is validated before any changes are published. Inputs, outputs and history are copied. History holds at most eight volatile records. Undo applies a new revision only to the current edit and refuses stale revisions. This is not a durable admin audit.

No source URL, plugin, code, account or provider input is accepted. Nilgiri cadence cannot be below 3600 seconds. There is no refresh or retry bypass. This fixture cannot read or write per-user channels or watchlists, and has no runtime, file-write, fetch, database or send integration. Supplied authorization checks a fixture boundary; it does not prove production admin identity.

There is no UI or production route. Persistence, production ownership, activation and complete catalog coverage remain separate work. No visual or production readiness claim is made.

<!-- END-ORIGINAL-DOC -->


<a id="doc-191"></a>

### Reference: `integration/news_export/FIXTURE_HTTP_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":5257,"path":"integration/news_export/FIXTURE_HTTP_LIMITS.md","sha256":"ce9b9897da5e2e73f49ddab61d4c8946eb2ea915a5e9232cc48fab656a8b01ff"} -->
# Dev/test original-export HTTP fixture

Separate create_original_export_fixture_app only. No standard create_app parameter/env/launcher activation. Standard runtime modules never import this module and standard url_map route absent (tested). No UI change. Exact bounded inert source data validated/copied/frozen at construction, private concrete in-memory executor callback defined in module only. No supplied executable hook except existing trusted authorization callable. No live DB/network/credentials/polling/writes/index. Source fixture coverage differs from production schema/index/snapshot requirements, never claims to satisfy them.

Exact dict/list/bool/str/int/float/None/ObjectId type checks, no subclasses/custom scalar hooks/deepcopy. ObjectId cloned from binary. Strings32k, list100*8k, row128KiB, combined10000rows/8MiBcompactUTF8; cumulative check before retention. Immutable tuples retained, original ordering checked; no request sorting. Caller tests/dev only. Peak memory caller inputs/temporary validation/copies not globally bounded; supplied8MiB cap bounds retained encoding, not interpreter overhead. Serialization via reviewed plain values only.

Outer WSGI auth using unbound Request before Flask URL binding; malformed environment that cannot construct Request fails closed403. Auth before routing on ALLmethods and unknown/malformed paths, fixed403 when unauth. Methodoverride rejected, OPTIONS204, wrongmethod405, unsupportedproject404, absentproject503. HTTP X-Export-Fixture: supplied-offline-fixture every status/method. Private/no-store/maxage0, pragma/expires/vary/nosniff/noindex allstatuses. No conditional handling/ETag/LastModified/AcceptRanges, Range/IfRange ignored, never206/304. HEAD metadataonly, no slot/pager/fetch/ContentLength; X-Export-Readiness: metadata-only; same static validation/status/type/filename/scope/protocol as GET, excludes busy: GET may429 whileHEAD200.

CSV original columns, noBOM, CRLFrecordends, multilineunicode preserved. Normal final status firstcell exact EXPORT_COMPLETE/TRUNCATED/INCOMPLETE. Reason prefix fixture:, enum source_exhausted/requested_limit => COMPLETE, hard_cap/byte_budget/time_budget => TRUNCATED, invalid_row/source_unavailable => INCOMPLETE. Metadata outputrowcount excludesheader/footer, consumedsourcecount prefilter excludesprefetchedunconsumed, SHA256exact precedingUTF8CSVbytes, cellcutflag, remainingblanks. All data EXPORT_prefixcells escaped withapostrophe, lossyintentional. Consumers CSVparse (not line split), exact firstcell, no trimming/casefold/apostrophe removal, require exactlyone finalfooter, reject empty/headeronly/malformed/missing/duplicate/nonfinal/wrongreason-kind/count/hash. Validator supplied. Hash integrity not authentication. Missingfooter on disconnect/crash/controlflow incomplete, no deliveryguarantee. Protocol differs intentionally from originals and needs downstreamreview.

One module-level perprocess slotflag+Lock across app instances, route owns until responseconstructed, transferflag; constructionfinally cleanup fallback, bodyfinally/responseclose idempotent shutdown-before-slotrelease. NeveriteratedWSGI iterable close tested. Request-specific environ cleanup handles start_response failures after ownership transfer; regression nextGET200. static_folder=None excludes default static route. No watchdog/GC guarantee; caller/server must close responses. No external session; pagerclose is local. Stream120s sampled budget cannot interrupt slow socket write. Real deployment finiteconnection/write/worker timeouts and slowclientdisconnect tests not done. Werkzeug inprocessWSGIclose proof only, not real ingress/server proof. Render still untouched; ingress cache/header/timeout validation remains blocker before deploying. No claim finite real serving-slot lifetime.

Configured repo63focusedtests across fixtureHTTP/originalstream/rawpager/keyset: authpathmethods, hookreject/freeze/bounds/order, headers/methods/conditionalrequests, HEADbusy distinction, late/earlyclose, protocolforgery/malformedfooter/digest/multiline, standardcompositionabsence. Constructor/Response/start_response failures, HEAD no-pager instrumentation, 501-row Geo HTTP and exact128KiB/8MiB/10000row boundaries tested. Real serving socket disconnect/slowclient experiments remain needed. Validator rejects any unescaped reserved prefix in EVERY DATA cell and counts beyond fixture caps/5digits. Review bundle not fullrepo; existing Flask/PyMongo/helpers required. Tested Python3.10.12, Flask3.0.3, Werkzeug3.0.6, PyMongo4.8.0 in configured repo; pin these before reproduction, production serving version unverified.

In-memory RawPager uses fixed15-row pages derived conservatively from validated128KiB perrow bound: 15*131072 plus JSON separators/envelope remains below2MiB. Freeze uses same compactUTF8/ObjectId serialization size as RawPager, so accepted pages cannot exceed pager budget; no byte-dependent short pages or falseEOF. Regression500rows*5000source and63maximum-sizedrows prove accepted multipage fixtures complete with matching counts. Hardconsumer20MiB/time limits still deliberately truncate with status, not source omission. Both production-exclusion tests need existing modules/rootassets; the review zip is increment-scoped.

<!-- END-ORIGINAL-DOC -->


<a id="doc-192"></a>

### Reference: `integration/news_export/GEO_SNAPSHOT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4356,"path":"integration/news_export/GEO_SNAPSHOT_LIMITS.md","sha256":"71734b010f30f2fabab37e54dc8cdbaccb31ebc649bfb342c9666d7d8b1949c3"} -->
# Geo original CSV snapshot adapter (offline injection, not live wiring)

create_geo_original_stream requires injected driver client plus closed explicit
review of geo_intel/articles/read-only role/snapshot support/index name/explain.
No URI/client construction, environment/router selection, read61facade expansion,
aggregate/command/write/index creation or source probes. Callback attestations
are developer prerequisites, NOT independently established real-source proof.

Starts PyMongo snapshot=True,causal_consistency=False session. Complete ordered
projection scan validates every score/published/ObjectId with existing resume
contract before header. It rejects mixed/missing/null/unsupported keys anywhere,
not filtered typed sample. Same session/simple binary collation/exact named hint
for schema scan and all original keyset continuation pages. No count/aggregate
added. SnapshotTooOld/indexmissing/unsupportedserver errors fail redacted; no
retry or fallback to inconsistent reads. Full preflight can be expensive and
must finish inside sampled120s budget; may refuse large history, notmillionrow
throughput claim. Sort ties _idDESC added by existing reviewed keyset contract.

Query max_time_ms2000, batch100, page500 (adapter rejects>1000),2MB retainedpage
budget, bounded fields before copy. Provider BSON allocation/buffer happens
before Python checks; upstream injected client MUST have reviewed socket/connect
and pool bounds. No synthetic guarantee of interrupting blockedcalls. Current
stream20MB/1m cap/8kcell clipping and explicittrailer unchanged. Sampled remaining
stream budget is inside snapshot120s total, external slowclient timeout still
required beforeHTTP exposure. Request filters stay AFTER cap, no querypushdown.

Managed wrapper owns session end once alongside exact OriginalStream cleanup:
initialfailure, latefailure, EOF, explicitclose, neveriterated close, context.
Caller still MUSTclose disposed response; no destructor/GC/watchdog guarantee.
Preflight and page cursor closes before end_session on failure. Client externally
owned and never closed by adapter. No real DB accessed; no index/server/user
credential/schema/collation/explain attestation validated here. Geo only, no
BRICS migration. Original fixtureHTTP is untouched; no new route or UI exposure.

Repro: pip install pymongo==4.8.0 Flask==3.0.3 Werkzeug==3.0.6 PyYAML==6.0.2;
python -m unittest tests.test_geo_snapshot -v. Bundle contains integration tree
and tests; no original Finder/root assets required.10focusedfake-driver tests:
reviewbeforeeffects/snapshotflags/samesession/full501multipage/querycontinuation/
completefullschema/orderrefusal/deadline/pagebytes/earlylateerrors/closeidempotent.

Driver docs inspected for snapshot semantics:
https://pymongo.readthedocs.io/en/latest/api/pymongo/client_session.html
https://www.mongodb.com/docs/manual/reference/read-concern-snapshot
MongoDB5.0+ snapshot reads required; source operator still must verify actual
server support and independent credential/index permissions before activation.

V2 query boundary: adapter owns last continuation; complete supplied plan must
match query_plan for that typed resume/limit. Extra operators ($where included),
malformed $or or injected predicates rejected before find. Schema/page/factory
errors raised after exception scope, no __context__ source error retained.
12focused tests (v2) include query injection and context retention regression.

max_time_ms applies initial find, not a finite deadline for every getMore;
client socketTimeoutMS and serving cleanup remain required. Attestation is
self-declared, not independently measured. Full schema preflight scales with
collection size and may exceed budget. MongoDB5.0+ required, AtlasM0 snapshot
support has not been verified. No live availability implied.

V3 initial guards moved into cleanup/redaction scope: exact plain plan,
missing/None/wrong project and malformed scope close session once, no unredacted
AttributeError.14focusedtests include execute/scope malformed-entry regressions.

Reviewv3SAFE14/14. Constructor review values are trusted developer injection,
not untrusted input sandbox: an object with raising equality can expose its
exception before session. Control exceptions during adapter calls are converted
to redacted SnapshotUnavailable after cleanup (not preserved cancellation).

<!-- END-ORIGINAL-DOC -->


<a id="doc-193"></a>

### Reference: `integration/news_export/KEYSET_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4526,"path":"integration/news_export/KEYSET_LIMITS.md","sha256":"08efb761999e743637e83d1668857211fff2b5fb663ebfbc3109d1d33b2a0c32"} -->
# Original-order raw CSV keyset plan (not executed)

Pure query/projection/order/resume plan, no MongoClient/cursor/store/config/HTTP call. Original Geo score DESC,published DESC and BRICS collected_at DESC retained. Descending ObjectId _id added as deterministic tie-break where originals had no tied order guarantee. No category/country/q/critical query pushed down: original cap-before-filter remains a consumer requirement (Geo1m/BRICS default1000,max5000). Projection includes only original contract fields plus _id and BRICS summary for critical predicate; private IDs must never become CSV content.

Contract requires homogeneous numeric finite score, Geo zoned timestamp strings and exact BRICS naive UTC producer strings and ObjectId IDs. Lexicographic timestamp string order matches original Mongo source sort, not chronological normalization across offset variants. Missing/null/BSON datetime/mixed-type/NaN/non-ObjectId sort keys are rejected only when returned. Mongo comparison type bracketing can silently exclude incompatible/missing values from later $lt branches. Execution requires preflight typed-count == total-count under the same approved snapshot, for every sort field and supported value format/range; a page sample is not proof. A mismatch must stop the export, not filter legacy rows. This returned-page validation cannot prove no unsupported records elsewhere in the source: production needs full schema/coverage verification before selecting this planner. Do not add $type filters that hide legacy data and call export complete.

Internal Resume is typed/revalidated, not a public request token. A stateless public cursor would need authenticated bounded serialization and query-binding, outside this module. Strict descending page keys reject duplicates/reordering/nonadvancing continuation. Limit1..1000, max_time_ms2000 is proposed server-execution query cap, not end-to-end deadline. Without a matching index Mongo may perform a full in-memory sort for each page. No index created; require the exact compound index matching sort and a reviewed explain() proving bounded indexed traversal, plus timeout/socket/memory/performance review before wiring.

No source snapshot guarantee: concurrent inserts/score edits/deletes can change ordering and coverage across requests. Production requires an approved consistent read snapshot strategy or frozen export boundary; max_id fence alone does not solve score updates. Current original CSV serializers remain snapshot-only, generic stream route still not original contract. This plan is preparation for an injected bounded executor/stream serializer, not a million-row export or live read.

Focused repro in existing configured repo: python -m unittest tests.news_export.test_keyset_plan (PyMongo BSON dependency, existing original_contract/export helpers). Tests verify original orders/closed projections/lexicographic tie continuation/page order/schema refusals, real BRICS producer format, int/float equality and fixture raw-page-to-original-serializer exclusions. No production database adapter exists. Increment bundle requires existing package dependencies, not standalone full repo.

Mongo-only plan. Original SQLite backends need their own reviewed plan and identity contract.

BRICS producer intelligence/brics/database.py uses datetime.datetime.utcnow().isoformat(): exactly YYYY-MM-DDTHH:MM:SS with optional six fractional digits, naive but documented UTC. No timezone suffix accepted for this producer contract. Geo retains zoned strings and existing source string sort. Python datetime.fromisoformat accepted syntax differs by Python version (especially 3.11); deployed Python version must be pinned and verified. BRICS regex narrows acceptance independent of that parser, while Geo broader zoned parsing must be source-schema checked before wiring. utcnow() is deprecated on newer Python but retained here only to test exact existing producer behavior, not to change it.

Preflight string-format counts must use Mongo $regex matching the reviewed producer format (ASCII digits), not merely $type string; numeric counts must enforce finite reviewed range and ObjectId types. Confirm the collection has no default collation or explicitly apply the same reviewed binary collation to count/find/sort; Python tuple comparison assumes binary string ordering. explain() review must cover initial query and the actual lexicographic $or continuation form, not only a simple _id range, with the matching compound index and no blocking full sort.

<!-- END-ORIGINAL-DOC -->


<a id="doc-194"></a>

### Reference: `integration/news_export/LOCAL_SERVING_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3470,"path":"integration/news_export/LOCAL_SERVING_LIMITS.md","sha256":"fc79461042c82e5367c96998ab2a35603bd37f1aab3f26038e629054a5de9b1c"} -->
# Local Werkzeug fixture serving evidence

Test-only real loopback HTTP,127.0.0.1 ephemeral bound port0. No production
module or route change, DB, external source, credentials, mail, deploy or UI.
Python3.10.12 Flask3.0.3 Werkzeug3.0.6 PyMongo4.8.0 configured environment.

Four tests: complete response equals in-process expected CSV bytes, validator
parses one multiline row/footer/digest; no-store/fixture header; HEAD empty and
unauthorized403 start no export. Real TCP reset while producer awaits a known
pending data chunk and actual module slot is busy: socket SO_LINGER reset,
resume producer, closure occurs before completion and actual slot false; next
GET validates. Linux-only reset mechanics, no cross-platform reliability claim.

Slow-reader experiment is a CONTROLLED PRODUCER-GATE observation, not natural
socket backpressure or a measured timeout. Observed at least74payloadbytes received (headers separately consumed),
74producerbytes, producer unfinished, actualslot busy, socketdeadline2s,
forced reset/release cleanup. Gate is explicit and bounded4s. This does NOT
prove finite serving-slot lifetime, actual write timeout, natural slow-reader
behavior, Render ingress behavior or production deadlines. Those remain open.

Harness caps active request workers2, no daemon threads, bound server kept,
peraccepted socket timeout2s, absolute9s context budget; each event/socket wait uses minimum of local cap
and remaining deadline, bounded shutdown/joins,
server shutdown from test thread, workers joined before close, survivors fail.
Teardown release gate and close client sockets even if assertion/setup fails.
Worker exceptions collected; Werkzeug's normal disconnect handling is expected,
handle_error records every exception (including unexpected disconnect
exceptions), with fallback when exc_info is None; any recorded exception fails. Cleanup diagnostics do not mask an
original exception; they are printed alongside it. Actual module slot checked after teardown. Port is re-bound to verify release.
Real _pager and OriginalStream construction counters cover all requests;
unauthorized and HEAD assert0 before authenticated GET. HTTP/1.0 handler
pinned and close-delimited headers asserted. Client consumes the exact74byte
CSV header only, compares to expected full response prefix, and verifies
non-empty remaining expected bytes while producer held. Stalled producer is
NOT freed by client disconnect alone; releasing test gate is required.
No sleeps or header-case assertions. Server poll interval.01 is local lifecycle,
not website monitoring. These are local Werkzeug fixture evidence only.

Repeat evidence:200iterations/800test executions PASS with ResourceWarning
promoted to error. HTTP response EOF can precede request-worker completion;
harness joins completed request workers before issuing next request. Initial
repeat without this synchronization failed at113 due to cap2 overlap, corrected
and entire200 rerun. This is harness evidence only, not throughput readiness.

By-construction limits: expected CSV uses the same app implementation and thus
is not independent parity proof. Probe.remaining is set but not asserted;
actual client-prefix length and non-empty expected remainder are asserted.
Worker cap/start failure paths are implemented, not all fault-injected. Whole
fixture HTTP test suite needs full merged project/root assets for composition
exclusion tests. Extracted bundle executes serving tests only, not full app.

<!-- END-ORIGINAL-DOC -->


<a id="doc-195"></a>

### Reference: `integration/news_export/ORIGINAL_CONTRACT_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":3298,"path":"integration/news_export/ORIGINAL_CONTRACT_LIMITS.md","sha256":"abdcc9c9a6f4ec5c9870ae118175e68294d760d34baff2f426eb4b780c70d8f7"} -->
# Original CSV contract snapshot port

Pure supplied-snapshot serializer, no route or DB reader attached. Original Geo/BRICS exports' exact columns/order, filtering and cap-before-filter behavior are covered by differential tests against original export AST functions. BRICS critical predicate oracle is extracted from its original classifier with explicit default keyword fixture, never original config imports. Source SHA pins checked by tests.

Original order is a caller requirement: Geo score DESC then published DESC; BRICS collected_at DESC. Input is raw public contract fields rather than normalized public_news_row: normalization had lost corroborated_by names and Geo original timestamp values. Allowed export fields are copied explicitly; IDs, sent state and unknown keys are never exported. No original module imports, config, environment, DB calls or network in serializer.

BRICS defaults1000 input rows, maximum5000, filters AFTER cap just as original. Geo supplied snapshots maximum10000 accepted here, original live cap1m remains a separate pager requirement. This is not full-history availability. Defaults for critical keywords mirror original config, not a claim about user's live env; caller can explicitly inject reviewed keywords.

Intentional safety differences: strict scalar/allowlisted query args, nonpositive BRICS limit rejected (original forwarded it to store), formula-defense apostrophe,8k cell text cap, safe filename slug, bounded scalar/list rows. Plain benign fixtures match original CSV bytes, including CRLF/quotes/newlines and BRICS corroboration separator. Timestamp scalars must be normalized by caller; datetime/BSON/custom objects refused rather than invoking their string hooks. No broad projection or private-field passthrough.

No route, pager, live DB, index, collector or deploy added. Existing merged sample/full CSV routes unchanged. Full keyset paging still needs query/index/deadline review and explicit production source wiring. Trailer/safety differences from original full export remain documented in EXPORT_DIGEST_LIMITS.md.

V2 hardening: UTF-16 surrogate scalars/list members rejected with ExportRequestError before encoding; BRICS stamp validated before row work. A running20MB maximum encoded-output budget is checked before each append, failing without returning a partial file; injected smaller budgets are bounded128bytes..20MB. Row count/cell size remain bounded. X-Export-Truncated also reports any8k cell clipping, and metadata includes cells_truncated/encoded bytes. Additional tests cover all formula prefixes/hiddenprefix/tab/CR/LF/negative numeric scores, overlong cells with flag, surrogate/list refusal and output budget/fail-fast stamp. No silent partial export is returned on a budget/error.

Review notes: negative numeric cells intentionally receive the formula-defense apostrophe (e.g. '-3), consistent with existing merged CSV defense rather than original byte parity for negative values. Any future download UI must inspect X-Export-Truncated/metadata and show a clipping warning; no such UI is wired by this increment. The20MB output limit does not bound the upstream reader's already allocated input memory: any future real source reader needs its own input byte/row/query deadline budget before supplying snapshots.

<!-- END-ORIGINAL-DOC -->


<a id="doc-196"></a>

### Reference: `integration/news_export/ORIGINAL_STREAM_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":5201,"path":"integration/news_export/ORIGINAL_STREAM_LIMITS.md","sha256":"3506c2cd590e899065301863a3cacaa7f66933c243d9b52df4ce4a71ed58b642"} -->
# Original CSV incremental fixture consumer

No route, credentials, production database adapter, snapshot or live-source query. Exact RawPager instance required with matching project. One stream claims a pager once; it cannot be reused. Existing original_snapshot serializer reused per row retains column order, field handling, BRICS predicates, filename and formula protection. ID and BRICS summary stay out of output columns. Generic stream_export is not used.

RawPager.fetch_page accepts a smaller exact integer limit <= configured page size. Source requests never read past remaining original cap (Geo1m, BRICS1000 default/max5000). Source rows count toward cap BEFORE category/country/search/critical filtering, matching originals; output rows can therefore be fewer. Reaching BRICS requested/default limit is EXPORT_COMPLETE relative to the request, not proof source exhausted. BRICS requests above5000 and Geo1m hard clamps report EXPORT_TRUNCATED conservatively without an extra read to prove EOF.

Initial fetch before header. Initial failure closes and propagates redacted pager error, no file. Every normal terminal path after header emits exactly one fixed-cell-count final status: EXPORT_COMPLETE, EXPORT_TRUNCATED or EXPORT_INCOMPLETE; cells are kind,reason,output rows,source rows,SHA256 of preceding CSV bytes,cell truncation flag,then blanks. Any serialized DATA cell beginning EXPORT_ is apostrophe-escaped, so a source row cannot impersonate a status row. Digest is an integrity check, not cryptographic authentication. File consumers must require a final status and recompute digest; absence on disconnect/control-flow/crash means incomplete. There is no way to deliver a terminator after a network disconnect or process death. The HTTP X-Export-Trailer header describes this convention, but the file itself contains status. Intentional contract difference requires downstream parser review before wiring. Reserved-prefix data escaping is another intentional difference.

Later source/row failure emits EXPORT_INCOMPLETE. One bad row aborts export rather than skip silently. Byte/time/hardcap stop emits EXPORT_TRUNCATED.20MB hard emitted-byte budget reserves512bytes for status; in practice Geo is limited to roughly20MB long before1m normal-sized rows.120s deadline sampled before row/fetch cannot cancel blocked callback. Existing8k cell truncation is reported by final status flag/state (including successful status), not hidden. Complete preflight/index/collation/snapshot obligations remain in RAW_PAGER_LIMITS/KEYSET_LIMITS. Callback memory/time cannot be controlled here. Production route needs concurrency admission, cancellation and separately reviewed session lifecycle.

Explicit close and context manager cover disposal before iteration/midstream. Automatic completion/failure closes. Caller must close on any response disposal, including unstarted iterator; no destructor guarantee. Local shutdown clears callbacks, not an external session. No external session in fixtures. Internal class isn't subclass-sealed or hostile-caller safe. Do not log exception introspection/context/locals. Callback exceptions after header map to fixed status text; BaseException propagates and closes, so final status absent means incomplete.

Configured repo repro: python -m unittest tests.news_export.test_original_stream tests.news_export.test_raw_pager tests.news_export.test_keyset_plan.36focusedtests: originaldata prefix differential, finaldigest/status, forgedmarker escape, requested/hardcap distinction, cap-before-filter and querybounds, cellflag, ownership/contextclose, initial/latefailure, bytes/time. No million-row throughput/live consistency proof. Bundle depends on existing helpers/PyMongo BSON, not standalone full repo.

Status recognition: use a real CSV parser, never split lines (cells may contain quoted newlines). Compare first parsed cell exactly against reserved status kinds, without whitespace stripping, case folding or removing apostrophes. Apostrophe escaping is intentionally lossy: a source cell EXPORT_COMPLETE and a source cell already apostrophe-prefixed can produce indistinguishable display values. Do not remove the safety apostrophe while checking status. Recompute SHA256 over exact original bytes preceding the final parsed record, preserving newline/encoding, not CSV reserialization. read means source rows consumed by the consumer, not matched/output rows; initial fetched but not yet consumed rows are not counted.

Fresh pager required: no prior resume, verification, EOF or closed state. Constructor validation fails before claiming the pager; ownership stays with caller, who must close it. Once claimed, clock/first-fetch constructor failure closes pager. A second claim fails without closing the first stream's pager. BRICS original web.py parses min(int(limit),5000), defaults1000 on ValueError and passes nonpositive values to backend (Mongo limit(0) unlimited/negative backend semantics; SQLite differs). As already documented by original_snapshot, this consumer intentionally rejects<=0 rather than recreate that unsafe backend-dependent behavior. Nonnumeric still defaults1000. No original parity claim for nonpositive limits.

<!-- END-ORIGINAL-DOC -->


<a id="doc-197"></a>

### Reference: `integration/news_export/RAW_PAGER_LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4137,"path":"integration/news_export/RAW_PAGER_LIMITS.md","sha256":"d3418bd1e96269f32e020b8a6e798eb290d10dd8bfcf0b15e4dbf92bfe9eaf73"} -->
# Injected raw pager fixture contract

No production adapter, client factory, environment read, router, credentials, Mongo execution, index change or source query exists here. RawPager is single-pass internal state, not a browser cursor API. Tests supply plain in-memory fake callbacks only.

verify_scope(project, order) must return exactly True before first executor call. Its adapter obligation is the complete same-snapshot format-aware count, binary collation, compound index and actual continuation-$or explain checks in KEYSET_LIMITS. This callback promise is not independently proved by RawPager and is not sufficient to activate production. Reviewer/operator must validate the real adapter evidence before wiring. Snapshot creation/release is not implemented: any production adapter needs a separately reviewed snapshot-resource lifecycle. close() here clears callbacks, not an external session.

execute(plan) must materialize at most requested limit, enforce projection and query, close its own cursor on all paths and preserve the same stable read snapshot throughout. Caller-provided callback executes wherever caller runs it; no real adapter is supplied or invoked in this increment. Exceptions permanently close pager, redacted error, no retries. Scalar/schema/projection/page order/byte budget checks apply after callback return. They cannot bound memory used or elapsed time during callback execution; server max_time_ms is not an end-to-end deadline. Cancellation/timeout/socket/lifecycle need review before live wiring.

Short page is assumed EOF by executor contract. An exact-full final page needs one final empty read. Subsequent EOF calls are local and do not invoke executor. Binary Python comparison supports reviewed homogeneous sort-key types only; complete coverage check must precede use or Mongo type bracketing may omit records. Mutable source ordering remains unsafe without a verified stable snapshot.

2MB compact UTF-8 serialized raw page budget, bounded row strings/lists and closed projection; IDs internal only. Payload size validation includes _id converted to its string solely for size estimation, never CSV output. BRICS summary supports original critical predicate, excluded from original BRICS columns. Original_snapshot fixture handoff proves differential bytes and exclusions within its existing 10000-row bound. This is not the original streaming CSV consumer, million-row support or original routes. Original cap-before-filter and output/time/interrupt-safe cleanup must be implemented in that separate consumer. Generic stream_export has a different public schema and must not be wired as the original consumer.

Repro configured repo: python -m unittest tests.news_export.test_raw_pager tests.news_export.test_keyset_plan. Twenty focused tests: multipage fake continuation differential, exact-bool verification, duplicate/order/missing/overlimit/nonadvancing failures, no-retry redaction, closed fields/budget/surrogates, manual close and BRICS exclusions. Increment review bundle depends on existing PyMongo BSON plus original_contract/export helpers; not a runnable full repository.

BaseException failures close and clear both callbacks. Normal exceptions become the fixed RawPagerError with suppressed display chaining. Known exact control-flow types KeyboardInterrupt, GeneratorExit and asyncio.CancelledError are reconstructed with empty arguments. SystemExit retains an exact int/None code, other values map to 1. Unknown BaseException subclasses become a fixed BaseException-derived RawPagerControlError, never reconstructed from arbitrary constructors. Reconstruction is guarded. Failure uses the class-qualified private shutdown (not public close); subclassing is prohibited. Control flow is not swallowed; callback-supplied secret text is not carried by the replacement. Python retains the original exception in __context__, including its message/traceback. Never log exception introspection, repr(__context__), traceback locals or callback arguments; only emit the fixed public error. This is a display-redaction contract, not erasure of the interpreter's exception context.

<!-- END-ORIGINAL-DOC -->


<a id="doc-198"></a>

### Reference: `integration/nilgiri_transport_research93/CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":3451,"path":"integration/nilgiri_transport_research93/CONTRACT.md","sha256":"dd636e38230e6c7e1c95b430cf7c0565cb5055f8d284eb9fb0bb96c1d0413adb"} -->
# 93 unselected local transport proof, production routing BLOCKED

Productionnetworknamespace routing notdesigned/verified. No runtimefactory/fixtureselection/env/testCAinput permitted. Publicnilgiried requests NOTauthorized inthisincrement. Localproof onlyfixedseparateTLSserverfixture andauthoredCA, notdeployconfiguration.

One child per ENTIRE cycle robots+page, nottwochildbacked callbacks. Closedinputprotocol reviewedobservedatUTC+cadence/retainedvalidators only, no argv/path/host/CA/header selection. Fixednilgiried.com:443 resources; max2insidechild and92gate. DNSmax16answers boundwall20s; rejectanyunsupportedfamily/private/special/malformed/zoneID; IPv4mapped normalizeIPv4. PicksortedONEglobaladdress no fallback;port443pinned peercompare normalizedliteral. ProductionTLSdefaultroots CERT_REQUIRED/checkhostname nilgiried.com/SNI/exactHost no insecureoverride.

Sharedwhole20swall includesDNS/connect/TLS/bothreads/serialization. Parentkillprocessgroup+reap ensuresDNSstallterminated. CPU10s/AS1GiB notregression4GiB. Connect<=3s/TLS<=3s/read<=6s eachlimitedremainingwholedeadline, NEVERperbyte reset. No proxy/netrc/env transportlookup. Errorcoarse, stderrdiscarded, no rawHTML/header/errorlog.

Wireencodingbinaryframed: magic N93v1 then2recordsmax; record4-bytebigendianJSONmetadata length<=12288 + JSONmetadata status/headers/bodybyteslength + exactrawbodybytes<=131072 (identityonly) sourcekindclosed robots/page. Worst2*(4+12288+131072)+5=286733 bytes; parentstdoutcap286733 (nevertruncates). Input<=8192utf8JSON; parentclosedframe/schema/sourcestatus/hash/UTF8allvalidatebefore92. Failure outputcoarseclosederrorframe, no mixedpartialsuccess. Serializationdeadline+maxstdout independentlytest.

HTTP1.1 only statusline<=256bytes includingCRLF, headerline<=1152bytes,32headers,headerstotal<=8192bytes includingCRLF, capbeforeparse. Noobsfold/control/invalidnames/1xx/duplicateframing orduplicatecasefoldname, TE+CL/conflictingLength. Status100..599butinterimrefused; redirectsreturnedcoarsestatus nofollow. Identitybodyencodingonly. CLdecimal<=6digits and<=131072, exactbody. TEexactchunkedonly, chunkextensions/trailersrefuse,chunkline<=16bytes,hex<=6digits eachchunk<=131072/max256chunks+total128KiB. ConsumeCRLFexactly, unexpectedEOFreject.304mustnobody: CLabsentor0/TEabsent; unexpectedbufferedbodyreject. No-framingEOFdelimitedrefuse (simplifiesdeadline/framing), connectionclose requested. HTTP1.0 statusrefuse untilreview (not silentlysupported).

LocalactualTLSfixtureproof mustcertnameverification/SNI/Host/peer observable, testwrongcert/mixedDNS/mapped/slowdrip/headerbomb/framingchunktrailer/overflow/crashEOF-livechild/reap. No mocks pretending TLS. FakeDNS selectionunitproof distinctfromactualDNS timeoutsubprocessproof. Productionnamespace route remainsBLOCKEDevenalllocaltestsPASS.

HISTORICAL23:47proofstatus (superseded RESULTS v2):8standalonefocusedIDs pass HTTP/DNS/wire+actualTLS local. Parser nowrequires EOF afterframedbody/304 (rejectextra bytes, close-boundreadabsolute deadline); strictwiredecoder verifiesclosedmeta/duplicateJSON/count/source/status/header/bodysize/UTF8/robots404progression. TheseareNOTwholechildcycle/processnamespaceproof; productionroutingSTILLBLOCKED. Remaining: fixedonecyclechild/protocol/parentboundedcapture+killreap/crash/EOFalive/stdoutoverflow/DNSstall; namespace1GiBactualTLSlocalproof; productionCA/pinDNSlinkcontrol fixedtransportnotimplemented. Nointegration/livecycles.

<!-- END-ORIGINAL-DOC -->


<a id="doc-199"></a>

### Reference: `integration/nilgiri_transport_research93/README.md`

<!-- ORIGINAL-DOC {"bytes":886,"path":"integration/nilgiri_transport_research93/README.md","sha256":"0cd643bf54b5e1eb3ac887030933a7787d707678d1f8934d84d7a410370b1cff"} -->
# Scoped standalone local research93 - NOT production transport

9HTTP/DNS/wiretests independentlyreplayedOK;11namespacefocusedIDs authorrunincludes2realTLS, whole-cycle2TLSresponse andkill/reap authoronly (CA/orchestrationnottransferred). Allsourcearchivedtxt, unselected/unwired. ProductionglobalDNS→literalpeer/defaultrootschain, actualresolverstall, slowhandshake/writephase, namespacerouting materiallyUNVERIFIED/BLOCKED. No liveNilgiriedfetch/watch/activation/DB/render/mail. Binarydecoderverifiesnormalizedframing butcannotindependentlyproveoriginalchunkcount/extensions (childparserresponsibility). FutureclosedDNSscalars exactaddress/port/flow/scope/cname beforeoperations: currentmalformedtuplemayTypeErrornotRefused. NEWreviewedcontractrequiredbeforetransportselection.1GiBper-processAS vsbest-effort50msgroupmonitorNOTenforcedaggregate. Historical87/88/90/91/92unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-200"></a>

### Reference: `integration/nilgiri_transport_research93/RESULTS.md`

<!-- ORIGINAL-DOC {"bytes":2661,"path":"integration/nilgiri_transport_research93/RESULTS.md","sha256":"c2ce82c4fcb2b4b90e584ccf4286db87224ab26adb558e226a0a3eacda81af48"} -->
# Scoped 93 local transport research, production STILL BLOCKED

8 focused unittest IDs suite OK in unshare-all namespace under1GiBAS/CPU10s. Real localTLS authoredCA certificatehostname/SNI/Host/peer validation, wrongname refusal; HTTP/DNSselection/wirefixtures. Whole-cycle authoredlocalchild max2robots/page actualTLSresponses +closedvalidators input+binarystrictdecoder tested namespace:first200/conditional304, hostileheader/extra-host inputsrefusecoarseexit23. Parent resourcecapture tests stdoutoverflow cap286733, crash17, EOFleaderalive deadline, sleepingchildstalldeadline groupkill/reap exit-9. Sleepingchild is NOTactualDNS timeoutproof. No productionDNSresolution/link-pinnedTLS implementationyet. No prodCAoverride.

Onebinaryframeformatworst286733bytes. Bodyidentity-only128KiB, headercount32/line1152/total8192 preparse, CL/chunk bounded, no1xx/redirectfollow/extensions/trailers/obsfold/duplicates/TE+CL, EOFmustcloseexact(noextrabody),UTF8strict. Header parsing readsbytesone-at-time forbounds clarity, performanceunknown. DNSunitselectionrejectsprivate/mixed/malformed>16+mappednormalize; notactualresolverproof. Readabsolute slowdrip unit, actualTLS success+wrongname; no slowTLS/failurephase/DNSresolverdeadlinetests yet. ChildTLSsendall timeoutnotwhole-serializationclockassertafterwrite, futureactualtransportmusthandle.

Localfixturehardcodedloopback/authoredCA intentionallyseparatefromproduction. DoesNOTproveprodglobalIP pin/defaultroots/namespacerouting. Productionnetworknamespace routingBLOCKER, transportunselected/unwired, noactivation/sitefetch/periodicwatch/DB/render/mail.

Processcapture reusedresearchharnesssample50msgroupRSS/processcountbest-effortNOTenforcedaggregate,1GiBper-processRLIMIT_AS enforced. Testharnessmodesonlydirectauthoredproofscriptnotruntimeinput. No usersecrets;generatedfixtureprivatekeys areephemeralauthoredtestmaterialnotdelivered. Fullconfigured1150notrerunbecause no integratedchanges.

v2 corrections23:54: exactlinecapcheckedbeforereturn, cap/cap+1tests; normalizedwireframingCL/TE/304consistency +deepJSONRecursionErrorcoarserefusal; exactfamily/address/tuple-shape DNSrefusal. WholelocalTLSrequestwrite+read shareoneabsolute6sphase, serializationscopefinalcheck.11focusedIDs authornamespaceproof (9HTTP/DNS/wire+2TLS), reviewprior6HTTP independentlyreplayedonly. ProductionroutingSTILLBLOCKED; actualDNSstall/productionpinnedconnectdefaultrootschain/slowTLSwrite fullproof pending. PreviousCONTRACT23:47remainingparagraph historical; localwholecycle/processproof nowexists, notproductionboundaryproof. Allstdiofailureserrorcoarseexit23, no parsedpartialrows returned. Notlivecrawler readiness.

<!-- END-ORIGINAL-DOC -->


<a id="doc-201"></a>

### Reference: `integration/nilgiri_watch_fixture/LIMITS.md`

<!-- ORIGINAL-DOC {"bytes":4327,"path":"integration/nilgiri_watch_fixture/LIMITS.md","sha256":"a2bca7e07fb29b391e61e404ab4f71e85d4fef3bcdfc0ea82b013fd7906a7453"} -->
# 92 offline injected fixture, not a live crawler

Exactly https://nilgiried.com/robots.txt and https://nilgiried.com/ on HTTPS authority443. No caller URL/port/path, redirect, retries, link discovery, user headers. Trusted injected fake fetch only, response closed schema status/plainint100..599, headers plaindict<=32 unique casefold names; total UTF8<=8192bytes, each name<=64 and value<=1024, ASCIIHTTPtoken names, valuesno controls. body exactbytes<=131072, identity Content-Encoding only (gzip/br rejected; no decompressor), strictUTF8, ContentLength checked if present. Header/body bounds checked for robots too. Exactly maxone robots andonepage call per attempt.

States disabled/requested-on-not-running/eligible/paused/stopped; live wiring absent. Fixture eligibility requires explicit trustedoffline-only switch. Robots404 permits fixtureprogress; robots200 conservativepolicy pause, notdisallowclaim; everyotherstatus pauses except403/429 stop. Homepage403/429/challenge stops forownerdecision, no automatictimedrestart. Challenge rubric conservative: lowercase textcontains captcha, cloudflare, access denied, verify you are human, cf-chl-, too many requests. False positives pause safely, notproofbotwall. Unexpectedstatus/invalidheaders/body/store/parser uncertaintypaused andbaselineuntouched. OwnerONnotthirdpartysourcepermission.

Atomic trusted in-memoryfake store CAS: begin underlock reserves attempt token, advances last_attempt, rejects alreadyactive or elapsed<max3600/configuredinterval. Errorsconsumecadence. Finishescompare token+version, publisheschangedresultonlyaftercommit, conflictoffersnoalert. Storeerrorlatchesactiveuncertainty, noimmediateretry. Persistent/networkstore notimplemented. Oneactive persource; no manualrefreshbypass. Exact awareUTC datetimes, offsetzero, no clockrollback; retainedattempt/check/observed mustnotbefuture. Callertrustedclock injected, notpage timestamps. No realtime/futureproofifclockitselfbad.

Baselineclosed source/policy/revision/snapshot/validators/checked_at record. Fixedsourcebound, policy92v1, revisionpositiveint, snapshotcanonicalUTC/URL/text/hash validated existingpage_watch schema/caps. Storedvalidators onlyetag/lastmodified plainopaque <=1024nocharsCR/LF/control, no authority. Historicalsnapshotkeptunchangedonerrors. Conditionalonlybaselinecheckage<=24h, originalobservedage<=7days. Otherwiseunconditional. 304 requiresmatchingactuallysentconditionalheaders andvalidbaseline/revision/policy, emptybody; checktimeadvances separatefromobserved unchanged. Successful200checkedtime=observedtime. Firstbaseline nofabricatedchangedalert; changedcompare existingparser/diff128KiB/4000delimiters/8000events. Retainonlylatestbaseline+lastattempt/status, boundedresultsummary<=16000, no accumulatedhistory. CPU formalwall/decompression/transport limits NOT implemented byinjectedfixture.

Nexttransport mustindependently prove DNS/globalIP pin/connectpeer/TLSHostSNI/noenvproxy/netrc/connect/readdeadlines/namespace1GiB/outputwallkillreap. None claimed here. No livefetch/watch/deploy/DB/files/mail/render. Sourcepolicybasis homepagepublicrobots404nohomepagepolicyanchorsOct6; notpermission/legalguarantee.

v2 tighterwrapper: exactbuiltindatetime+exactbuiltindatetime.timezone zerooffset checkedbeforehooks on now/last/checked_at. Retainedsnapshot plainclosedshape/types,text<=128KiBUTF8/chars, otherfields<=2048 beforegenerichash/copy. Aggregate singlebaseline source/policy/revision/all snapshotvalues/validatornamesvalues/checktime<=128KiB. Pairedcomparison oldtext+newtext+validators+16KBreservedpreview<=256KiB; genericparserlimits unchanged. Offlinepreviewalert NOTsendready, legacyemailed:false grantsnothing. Conflicts/uncertainstorelatched no resumeAPI/auto-unlock; futureownerdrivenrecoveryneeded. Trustedinjectedfakes only, no productionstore/fetchproof. Stickycadenceslowdown remains deliberate.

Reviewedscope correction: 30unittestIDs =14inheritedtests executedtwice+2boundarytests,16distinctscenarios. 262144check isconservative content/validator+alert allowance NOTexactserializedwhole-statecounter. Actual128KiBtext/singlebaselineaggregate and16KiBrepralertcap. TrustedfixtureNOThostilestore sandbox. FakeCASNOTdurable/multiworkerproof. NoownerresumeAPI. Actualtransport/no-networkproofseparatefuturework. Originalpage_watchunchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-202"></a>

### Reference: `integration/public_live107/README.md`

<!-- ORIGINAL-DOC {"bytes":4593,"path":"integration/public_live107/README.md","sha256":"6bca798b7e0939d2c803749c00bb168434bdd99c21130d44d339c7d7456da1c4"} -->
# Reviewed public Geo article reads107

Additive public_live107:app entrypoint. Default PUBLIC_NEWS_READ_ENABLED=false
delegates unchanged public106/sample/private rollback. Exact true requires ALL:
PREVIEW_PUBLIC_SAMPLE_ENABLED=true, PREVIEW_GEO_ONLY_ENABLED=true,
PREVIEW_ACCESS_ENABLED=false, NEWS_READ_ENABLED=false,
NEWS_EVENTS_READ_ENABLED=false, FINDER_NETWORK_PREVIEW_ENABLED=false,
NEWS_STORE_MAPPING_VERIFIED=true, PUBLIC_NEWS_DISCLOSURE_VERIFIED=true,
GEO_READONLY_CREDENTIAL_VERIFIED=true. GEO_DATABASE=geo_intel and
GEO_ARTICLES_COLLECTION=articles only; URI required in GEO_MONGODB_URI.

These assertions do not themselves prove owner permission, mapping or Atlas role.
Operator must check source and read-only credential independently before enabling.
No URI or credential copied into evidence. Read-only role cannot be introspected
or proven by facade; a privileged URI remains privileged and must not be used.

Canonical HTTPS origin validated before client creation. Existing read facade with new timezone-aware TLS factory,
timeouts5s/pool4, find-only wrapper. Reader exact geo_intel.articles, limit100,
created_at descending, maxTimeMS2000, cursor always closed, whitelist projection.
Mongo dates read with tz_aware=True (UTC), avoiding naive datetime loss.
Additive sanitizer accepts exact bounded strings ONLY for URL/title/display fields,
nullable/time fields accept bounded strings or timezone-aware datetime; score is
finite exact numeric, not bool. Nested dict/list/objects omitted without str().
Malformed requiredURL/title rows dropped; all private raw keys discarded before
cache/normalization. Historical private normalizer unchanged.
Existing public normalization strips IDs/emailed/receipt/private keys and unsafe
URLs. All allowed output fields are public disclosure, including summary/source,
country/category/timestamps/risk/credibility/score. Original source content not
independently fact-checked; page is a bounded stored-news read view, not truth proof.
No arbitrary collection or client from request. Client factory injectable only
for reviewed tests; source env controls production, no network before gates.

Per-process60-second read cache, one fetch at a time, lock acquire2s bound.
Successful empty collection is legitimately empty. Read error clears cache,
closes client, latches unavailable until process restart after operator repair;
API503 sanitized, never replaces failed read with empty success. Latest100
stored documents selected before normalization, so invalid rows may reduce count.
Cache means manual refresh need not immediately reflect DB change. No polling.

Public GET/HEAD allowlist unchanged; write/private/events/full export/PDF/digest
routes denied. Offline Finder unchanged; no private saved keys/localStorage.
Public news label and loaded100 scope replace empty-sample label. Sample/private
fallback unchanged. No old source,105/106evidence or frozen baseline changed.

User-operated Render Start Command after reviewed save:
gunicorn public_live107:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 30

Additional live-public env values after owner/operator verification:
PUBLIC_NEWS_READ_ENABLED=true
NEWS_STORE_MAPPING_VERIFIED=true
PUBLIC_NEWS_DISCLOSURE_VERIFIED=true
GEO_READONLY_CREDENTIAL_VERIFIED=true
GEO_DATABASE=geo_intel
GEO_ARTICLES_COLLECTION=articles
GEO_MONGODB_URI=(user enters read-only URI directly in Render, never chat)

Keep106public flags/origin/Python unchanged, particularly NEWS_READ_ENABLED=false,
NEWS_EVENTS_READ_ENABLED=false and FINDER_NETWORK_PREVIEW_ENABLED=false.
Rollback PUBLIC_NEWS_READ_ENABLED=false returns sample106 with no Mongo client;
private fallback still uses original reviewed private settings. No collectors,
mail, migration/index/write/otherDB requests, no Render changes by task.

Public workspaceJS exact-code button disabled via scoped response transform;
private sourceJS unchanged. Text bounds2048 URL/title,8000summary,200otherfields,
100dates, UTF8<=4xcharacter cap; lone surrogate invalid.12focused tests pass.
V2initial test found uncached return used raw rows, now corrected to sanitized
cache on FIRST fetch and all subsequent requests; adversarial firstfetch PASS.

Final13focusedPASS including cold+expiredcache across9publicJSON/CSV endpoints
with hostile nested marker/ID absence checks. Full1166unique/runPASS with existing
1expected limiter failure and1optional pikepdfskip. Fixture390/1280browser
PASS nooverflow/errors/externalrequests, publiccodebutton absent; pixels
inspected, readable news card/loadedlimits. No liveDB or credential inspected.

<!-- END-ORIGINAL-DOC -->


<a id="doc-203"></a>

### Reference: `integration/public_preview106/README.md`

<!-- ORIGINAL-DOC {"bytes":2333,"path":"integration/public_preview106/README.md","sha256":"efc931919b43c1125f0908d737a0cf291aa65b356f1b8aae0d14aa2f46c578af"} -->
# Public empty-sample preview106

Explicit opt-in public preview. No stored news, passwords, provider keys, notes,
DB connection, collector, mail, write routes, PDF generation or live network
Finder. Default false delegates unchanged private launcher, preserving rollback.
Public true requires Geo-only true, access false, article/events reads false and
Finder network false. Injected clients rejected before construction. Canonical
HTTPS origin required; unexpected host rejected. Fixed empty reader is public
sample scope, not news DB. GET/HEAD exact allowlist; other methods denied. Health
retains existing public staging status. Root redirects to workspace. Public label
in HTML; no-store/noindex/CSP remain. Original Finder shell with saved keys is
not exposed: iframe is sanitized self-contained offline snapshot (no localStorage,
fetch or SW registration). Live video/channel controls and heavier weekly/BRICS
links removed from public home. No old source or historical audit bytes changed.

User-operated Render settings, only after reviewed save:
Start Command:
gunicorn public_preview106:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 30

PREVIEW_PUBLIC_SAMPLE_ENABLED=true
PREVIEW_GEO_ONLY_ENABLED=true
PREVIEW_ACCESS_ENABLED=false
NEWS_READ_ENABLED=false
NEWS_EVENTS_READ_ENABLED=false
FINDER_NETWORK_PREVIEW_ENABLED=false
PREVIEW_TRUST_ONE_PROXY=false
PREVIEW_ORIGIN=https://geo-intel-brief.onrender.com
PYTHON_VERSION=3.10.12

Password hash/session key ignored in public mode; can remain for rollback, never
shared in chat or repository. Secret URI not used. Do not turn live reads on in
public mode. Rollback: PREVIEW_PUBLIC_SAMPLE_ENABLED=false and original private
settings/access credentials, or restore prior private_router start command.
Public output uses empty sample/unavailable panels honestly, not fake live rows.

Executed8 public-mode focused tests PASS, including private rollback. Full1166
configured tests PASS, existing1expected limiter failure/1optional pikepdf skip.
Local390/1280browser screenshots visually inspected: readable, no overflow,
clear empty-sample labels, zero pageerrors/external requests, offlineFinder works.
Local HTTPS authority rewrite used ONLY in browser harness, never production.
Render proxy behavior requires live200 verification after user switches entrypoint.

<!-- END-ORIGINAL-DOC -->


<a id="doc-204"></a>

### Reference: `integration/publication_dates/CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":898,"path":"integration/publication_dates/CONTRACT.md","sha256":"7acef222b3c27af6e9f32eb80f63ccc629725982d1d3a5ec259e7c708e4c3ce9"} -->
Strict publication evidence, date151 integrated on 739107f.
Missing, bad, incomplete, naive, unknown-zone and future dates are held. No UTC
guess, clock skew or fake-now fallback. Explicit UTC/GMT/Z and numeric offsets
up to 14 hours are accepted. Existing old-valid lookback remains.
Process-cumulative locked counters are separate from the unchanged seven-field
write outcome. Diagnostic failure reports unavailable and cannot replace a
confirmed, partial or uncertain collection outcome. This is not durable
quarantine or retained raw-feed storage. parse_date returns datetime or None.
Exact source, seam and pin closure is required. No activation is authorized by
this document.
Feed observations cover 25 DEFAULT feeds only: 10 dated samples with no held
named zones, 3 with no date sample and 12 unavailable. Extra feeds are unknown.
These observations do not establish activation readiness.

<!-- END-ORIGINAL-DOC -->


<a id="doc-205"></a>

### Reference: `integration/pypdf_remediation105/README.md`

<!-- ORIGINAL-DOC {"bytes":4024,"path":"integration/pypdf_remediation105/README.md","sha256":"79d341bc0b0d34e3e91526cfb837ada42a94d18cfb129f9c14c178f0d1188867"} -->
# Current pypdf offline profile supersedes old locks

This change selects pypdf6.19.0 in BOTH current offline locks. It does not change
requirements-staging.txt, future-deploy lock, legacy runtime requirements,
collectors, DB, mail, Render or current UI. pypdf remains test-only in the basic
preview profile; parsing fixture PDFs is still execution, not zero risk.

Original87 audit and88 build receipt JSON remain byte-identical historical
observations. They describe old pypdf5.0.1 and the old built sgmllib wheel, NOT
these current locks. Their README headings now make that distinction explicit.
Original two lock bytes plus SHA256 are preserved in historical-locks.json and
in git parent d8f89025ae03e36a1f93c93607886535ce2e1905. Historical tests compare
against those exact snapshots. Current-profile focused checks are separate.
No old successful/blocked stage is relabelled as a new execution.

Candidate lock still explicitly lacks a sgmllib wheel hash and is NOT directly
installable. Built lock is the complete25artifact profile: new official pypdf
wheel7e5d6e730e7dae87d560a2cee218b852f6498c8be61966f3cd02ead971e48d14,
and newly built sgmllib wheel a16186785516975fd0f6f8f2a8c944cc0d832e061c9205ea904bf803ac25c0ad.
The sgmllib bytes differ from old88 because wheel builds are not deterministic;
source sdist/hash/source.py unchanged. No byte-identical build claim.

New build: safely inspected original11-member20923-byte sgmllib sdist, no
traversal/link/device members; reviewed setup imports setuptools and reads README.
Bubblewrap unshare-all/network isolated, clearenv, system trees read-only plus
scratch writable; bounded capture120s/CPU60s/AS1GiB/file64MiB/output1MiB and
kill-group/reap. Actual stage/log/argv and source hashes retained. Build-tool
wheel0.37.1/setuptools59.6.0, shared CPython3.10.12/Linuxx86_64, not new OS proof.

All25 wheel hashes inspected/copied. Fresh venv install uses --no-index,
--no-cache-dir,--only-binary=:all:,--require-hashes. This install occurred in the
local host environment, not an OS network namespace; flags are not an OS firewall.
No system-site; pip-check and active default-extra dependency edges pass.
25installed packages and641physical Python-file hashes recorded. Existing
feedparser/sgmllib SDK source pins and fixed parser tests pass. Optional extras
remain excluded. Artifact bytes are local scratch, not a published wheel bundle
or a one-command public-index deployment promise.

The other historical pinned versions are unchanged, including Flask3.0.3,
Werkzeug3.0.6,PyMongo4.8.0,requests2.32.3. This is a pypdf remediation ONLY, not a
security-clean runtime profile. No “all alerts fixed” or provider closure claim.
Future-deploy patched profile94 is separate and unchanged. Provider count/IDs
must be rechecked after the save; dismissals are not remediation evidence.

Upstream four advisory fixes: cross-reference>=6.14.0, ASCIIHex>=6.7.5,
RunLength>=6.7.4, whitespace>=6.15.0;6.19.0covers all four and requiresPython>=3.9.
https://github.com/py-pdf/pypdf/security/advisories/GHSA-55h5-xmcq-c37v
https://github.com/py-pdf/pypdf/security/advisories/GHSA-9m86-7pmv-2852
https://github.com/py-pdf/pypdf/security/advisories/GHSA-f2v5-7jq9-h8cg
https://github.com/py-pdf/pypdf/security/advisories/GHSA-fc8x-2rww-xw9m
https://pypdf.readthedocs.io/en/latest/meta/CHANGELOG.html

Fresh offline-built105 full suite:1166 unique/run successful, one existing
expected limiter failure and one optional pikepdf validator skip. Configured
staging first sweep had one manifest bookkeeping failure after adding evidence
during execution; correction and chunk rerun will be recorded explicitly.
Full build argv recovered from unchanged archived executed script.

Corrected staging chunk8 rerun100PASS after registering evidence. Combined
12chunk final accounting1166 unique/run successful, zero failures/errors,
one existing expected limiter failure and one existing optional pikepdf skip.
First failed chunk preserved in full-staging-regression.json, not erased.

<!-- END-ORIGINAL-DOC -->


<a id="doc-206"></a>

### Reference: `integration/rss_catalog/README.md`

<!-- ORIGINAL-DOC {"bytes":2478,"path":"integration/rss_catalog/README.md","sha256":"ad16bfe99118af51e0a96ccefa52740dae622e674860827cdc154ab518b9dd54"} -->
# Disabled RSS candidates

Independently researched publisher feed URLs,143 candidates:133 reachable/parseable observations and10 needs-review. Every enabled=false, terms_state=unverified. This is not143 approved/permitted feeds, not a live source registry and not wired to collectors. Original source lists untouched. Feed URLs are public publisher URLs from our own discovery; some coincide with other public lists. URL overlap does not prove code/list copying, and the inventory is not a licence clearance.

Reachability/item count/latest/robots are historical captures, not current source health or reuse permission. A publisher-country hint isn't the country covered by every article. HTTPS candidates preferred; HTTP candidates need review. Publisher terms, feed licence, attribution/reuse limits and current reachability need source-grounded approval before live ingest. Headlines/links/excerpts do not automatically avoid rights obligations. No bodies are included.

Pure validator checks closed fields, bounded lists/strings, disabled activation and unknown terms. It never upgrades status or chooses active feeds. Candidate discovery provenance retained per row; URLs aren't authority or execution instructions. Live network/polling/fetch/DB/mail remain off. Adding more candidates cannot establish100+ permitted coverage until per-publisher terms reviewed.

ASCII DNS names only, including literal ASCII punycode xn-- labels; no Unicode IDNA conversion performed. Nonpublic IP literals and userinfo/invalid ports rejected. DNS resolution and redirects are not checked by this offline validator, so this is not SSRF protection for a future fetcher. Returns mutable deep copy; every consumer must revalidate at use, never rely on an earlier validation after mutation.

DNS final label begins with a letter; hex0x labels, shorthand numeric hosts and localhost/local/internal/lan suffixes denied. IPv6::/96 and64:ff9b::/96 embedded forms denied explicitly. Credential-like query names denied. Duplicates compare lowercase hosts; no DNS equivalence/path/query canonicalization claim. Nonempty category/country/language/discovery strings and exact valid ISO latest date required.
Credential-query checks cover common credential-like names, not detection of all secrets. Default ports (such as explicit:443 vs omitted port) are not normalized into one identity for duplicate checks. Render Python version remains unknown/unverified; current tests run locally on Python3.10.

<!-- END-ORIGINAL-DOC -->


<a id="doc-207"></a>

### Reference: `integration/security_candidate/README.md`

<!-- ORIGINAL-DOC {"bytes":2300,"path":"integration/security_candidate/README.md","sha256":"f3a83bd887ce341d61cb4c5340637d408d8e22ca9c9f496af9bfdba4e322d635"} -->
# Separate PyMongo/pypdf security research candidate

Not selected by launcher/build; original requirements/configuredvenv and
87/88 historicallocks unchanged. Not complete securityfix or readiness.
Official PyPI metadata, SHA256, canonicalwheelidentity, compatiblePython3.10
and safe180/64members inspected. Complete25package hashedcandidateinstall/
pipcheck/no-systemsite verified. pymongo4.18.2 + pypdf6.19.0 candidates only.
Exact officialadvisories/provenanceURLs and receipts recorded.

Currentfullcandidate regression:1119uniqueIDs/run exactlyonce in qualifyingfinalcoverage, suiteOK1expected
and1optionalPDFskip, qualifyingnamespace partitions finishnormally. Dedicated
regression-only4GiBvirtualcap,best-effort50mssampledprocess-groupmonitor at768MiB/128processes; default/
attack1GiB provedunchanged. Initial1GiBAS threadMemoryError/CPU137/manifest
failures retained; finaltree rerun exactmanifest, no skippedassertions. Initial
hostpart1 excluded. Historical88loopbackblock not current90: bind succeeds.
Researchharness kept outsideapp; archivedastext, historicalinventory untouched.

IsolatedattacktinyURIencodedhost refused,4incompleteASCII85/ASCIIHex cases
refused, boundedBSONCbackend roundtrip. Overflow>2GiB NOT exercised, upstream
Cwidearithmeticpatch sourceonly, no smaller-test equivalence claim. CSFLE
.sockguard installedsync/async sourceverified; no productionencryption path
found. FakeMongo/API contracts do not prove liveMongo servertransaction/
cursor correctness. No liveDB/send/deploy/PRmerge/permissivefallback.

75 affectedsourcecontracts ranhostunit OK1optionalPDFskip, not fullisolated
proof. pypdf only validatestestgeneratedPDF, productionwriter unchanged:
structure/text tested, no changedPDFvisualdeliverable claimed. Otherdirect/
transitive advisorycheck pending;3remaininghighs sameBSONadvisory triaged; not blanketclean.
Historicalalerts willcontinue, no hide/rename/dismissalworkaround.

Monitor is NOT an enforcedaggregateboundary/cgroup memory.max or pids.max.
Bwrapnewsession/descendantsownsession canfalloutside, spikes/threads not
counted. Actual4GiBRLIMIT_AS per-processvirtualcap is enforced; sampled
monitor doesnotprove all descendantsstayedunder768MiB. Failed/interrupted
attempts ran some testsearlier; exactlyonce applies qualifyingfinalcoverage.

<!-- END-ORIGINAL-DOC -->


<a id="doc-208"></a>

### Reference: `integration/security_candidate/bump158/README.md`

<!-- ORIGINAL-DOC {"bytes":740,"path":"integration/security_candidate/bump158/README.md","sha256":"d1320e50a638ca7c2a825ec7f5ecfbffd74862dbce7b1e2c453f0787080fde37"} -->
Supplemental candidate-lock validation, October9

The candidate lock has four reviewed bumps plus the PyPI-published sgmllib3k
1.0.0 sdist hash. Frozen original/offline locks are unchanged. The old receipt
and regression-coverage remain historical, not coverage of this bumped lock.
Fresh isolated venv hashed install and pip check passed. pip used legacy
setup.py install for sgmllib3k because wheel was absent. Bootstrap pip and
setuptools versions are recorded but not hash-pinned. The app input hashes
were enforced; this is not a reproduced or independently attested build chain.
Full current-tree regression must pass in the bumped environment before landing.
No runtime profile or deployed environment was changed by this candidate.

<!-- END-ORIGINAL-DOC -->


<a id="doc-209"></a>

### Reference: `integration/security_candidate91/README.md`

<!-- ORIGINAL-DOC {"bytes":1025,"path":"integration/security_candidate91/README.md","sha256":"c5bba9bcd61489316147889ae2b244d45994d7e4bed0553433a813a63ff7f899"} -->
# Unselected candidate91, October6 2026

Tests run, suite OK: original configured1119 plus candidate1119uniqueIDs on eachold/upgradedbootstrapprofile, each1expectedfailure/1existingoptionalPDFskip. Not allindividualtests passed, earlierfailedattemptsretainedinreviewarchive. No productionpinselection orsecurityoutcomeclosure.

New-installer1635hash equivalence isinstallationevidence ONLY, no separatelyrerunsuite. Tinybuild_meta probe isnot sgmllib rebuild; sgmllib existingwheelreused. Windows safe_join Linuxstringbranch ONLY, crossdevdotenv/BSON>2GiB/liveMongo nottested. 39exactOSVqueries emptyisnohit scopedtotime/version/ecosystem notimmunity. Historicalalertsremainvisibleand GitHubalertbodyunverified.

1GiBattack/install and4GiBperprocess regressionlimit. Best-effort50msprocess-groupRSS/processcount monitor isNOTenforcedaggregateboundary, missesthreads/spikes/own sessions. Originalsources/historical87/88/90immutable. Manifestrefresh currentFEATURE_STATUSstalenessonly. No deploy/liveactivation/DBwrites/sends.

<!-- END-ORIGINAL-DOC -->


<a id="doc-210"></a>

### Reference: `integration/security_candidate91/planning-notes.md`

<!-- ORIGINAL-DOC {"bytes":1940,"path":"integration/security_candidate91/planning-notes.md","sha256":"7105f6af33c6a57103db2b66cf7ee6ce7c38589d0cdd3693d6c127928c1de1bc"} -->
# PRE-IMPLEMENTATION PLANNING NOTES - historical, not currentstatus

# Dependency review October6 2026

Exact25candidateapp+2bootstrapOSVquery yields8distinctapp advisories across
Flask/Werkzeug/requests/dotenv, plus11distinctbootstrap pip/setuptools.
AliasPYSEC records reconciled, no pagination. CurrentMongo/PDFplusretained
other21app packages no OSV matchingrecord, notabsenceofunknownvulnerabilities.

Proposed researchedupdates: Flask3.1.3, Werkzeug3.1.9, requests2.34.2,
python-dotenv1.2.4; exactcurrentPyPImetadata compatiblePython3.10 and retained
closuredefaultdependencies. Proposed separatebootstrap pip26.2.1/setuptools84.
No download/install/selectionyet; independentplanreviewpending. RuntimeAPI/
sourceparity and completecandidate regression stillrequired. Originalsource/
87/88/90historicalreceiptlocks untouched.

FlasksessioncacheVaryCookie: currentpreviewprivateNoStore mitigation, session
getpaths used, no blanketprotectionclaim. WerkzeugWindowsdevicepath issues
notLinuxpathproof; crossplatform .safe_join API stillneedsupstreamcontract.
Requestsnetrc+tempzip: sourcecollectors use requests.get onconfiguredfeeds,
no trust_env=False explicit; exactrelevance requires hostnetrc/tempzipconfig,
unknownratherthanabsent. Dotenvonlyload_dotenv usage found, set_key notused.
Bootstrapadvisories matterinstaller/buildinputs notsameasappHTTPexposure.
Verifiedofficialartifactintegrity+wheelonlyhashpins reducebutnoteliminate
installerissues, and are not substitutedforupdates. No credentialvaluesused.

Source ledger and exactOSV records retained separately. Beforeselection:
inspectwheelpaths/METADATA/RequiresPython/defaultclosure/hashes, independent
review, boundedsyntheticcases, fullconfiguredcandidate tests without skips,
productionpins nevereditedwithoutfinalevidence.


Currentstate: artifact/actualclosureverified and tested; independentSAFE unselectedevidencereviewOct6 22:29. See README/receipt. No pinselection.

<!-- END-ORIGINAL-DOC -->


<a id="doc-211"></a>

### Reference: `integration/security_candidate91/sources.md`

<!-- ORIGINAL-DOC {"bytes":10894,"path":"integration/security_candidate91/sources.md","sha256":"3d5d9fe66a75b5fbbf368084d0a8e0781bbbfab8a4bbd818fd4b48e081bc779b"} -->
# Sources, read October6 2026

OSV exactversionAPI via documented https://google.github.io/osv.dev/post-v1-querybatch/

http://seclists.org/fulldisclosure/2025/Jun/2
http://www.openwall.com/lists/oss-security/2025/06/03/11
http://www.openwall.com/lists/oss-security/2025/06/03/9
http://www.openwall.com/lists/oss-security/2025/06/04/1
http://www.openwall.com/lists/oss-security/2025/06/04/6
http://www.openwall.com/lists/oss-security/2026/04/20/8
http://www.openwall.com/lists/oss-security/2026/04/27/7
http://www.openwall.com/lists/oss-security/2026/06/01/5
http://www.openwall.com/lists/oss-security/2026/07/29/7
https://access.redhat.com/errata/RHSA-2026:33313
https://access.redhat.com/errata/RHSA-2026:34374
https://access.redhat.com/errata/RHSA-2026:34456
https://access.redhat.com/errata/RHSA-2026:34739
https://access.redhat.com/errata/RHSA-2026:34740
https://access.redhat.com/errata/RHSA-2026:34741
https://access.redhat.com/errata/RHSA-2026:34748
https://access.redhat.com/errata/RHSA-2026:34749
https://access.redhat.com/errata/RHSA-2026:34750
https://access.redhat.com/errata/RHSA-2026:34752
https://access.redhat.com/errata/RHSA-2026:34756
https://access.redhat.com/errata/RHSA-2026:34758
https://access.redhat.com/errata/RHSA-2026:34760
https://access.redhat.com/errata/RHSA-2026:34765
https://access.redhat.com/errata/RHSA-2026:34772
https://access.redhat.com/errata/RHSA-2026:34773
https://access.redhat.com/errata/RHSA-2026:34774
https://access.redhat.com/errata/RHSA-2026:34775
https://access.redhat.com/errata/RHSA-2026:34776
https://access.redhat.com/errata/RHSA-2026:34777
https://access.redhat.com/errata/RHSA-2026:34778
https://access.redhat.com/errata/RHSA-2026:34780
https://access.redhat.com/errata/RHSA-2026:34891
https://access.redhat.com/errata/RHSA-2026:36193
https://access.redhat.com/errata/RHSA-2026:36315
https://access.redhat.com/errata/RHSA-2026:37275
https://access.redhat.com/errata/RHSA-2026:37283
https://access.redhat.com/security/cve/CVE-2026-8643
https://bugzilla.redhat.com/show_bug.cgi?id=2460927
https://github.com/advisories/GHSA-4xh5-x5gv-qwph
https://github.com/advisories/GHSA-58qw-9mgm-455v
https://github.com/advisories/GHSA-6vgw-5pg2-w6jp
https://github.com/advisories/GHSA-87hc-h4r5-73f7
https://github.com/advisories/GHSA-9hjg-9r4m-mvj7
https://github.com/advisories/GHSA-cx63-2mw6-8hw5
https://github.com/advisories/GHSA-hgf8-39gv-g3f2
https://github.com/advisories/GHSA-jp4c-xjxw-mgf9
https://github.com/advisories/GHSA-mq26-g339-26xf
https://github.com/advisories/GHSA-qwm4-qh6w-59xr
https://github.com/advisories/GHSA-r9hx-vwmv-q579
https://github.com/advisories/GHSA-wf93-45jw-7689
https://github.com/pallets/flask/commit/089cb86dd22bff589a4eafb7ab8e42dc357623b4
https://github.com/pallets/flask/releases/tag/3.1.3
https://github.com/pallets/flask/security/advisories/GHSA-68rp-wp8r-4726
https://github.com/pallets/werkzeug/commit/4b833376a45c323a189cd11d2362bcffdb1c0c13
https://github.com/pallets/werkzeug/commit/7ae1d254e04a0c33e241ac1cca4783ce6c875ca3
https://github.com/pallets/werkzeug/commit/8d77320bcdf3a34941ec06dcf16b03c065cd21b6
https://github.com/pallets/werkzeug/commit/f407712fdc60a09c2b3f4fe7db557703e5d9338d
https://github.com/pallets/werkzeug/pull/3309
https://github.com/pallets/werkzeug/releases/tag/3.1.4
https://github.com/pallets/werkzeug/releases/tag/3.1.6
https://github.com/pallets/werkzeug/releases/tag/3.1.9
https://github.com/pallets/werkzeug/security/advisories/GHSA-29vq-49wr-vm6x
https://github.com/pallets/werkzeug/security/advisories/GHSA-87hc-h4r5-73f7
https://github.com/pallets/werkzeug/security/advisories/GHSA-g6x2-hccm-hh4m
https://github.com/pallets/werkzeug/security/advisories/GHSA-hgf8-39gv-g3f2
https://github.com/psf/requests/commit/66d21cb07bd6255b1280291c4fafb71803cdb3b7
https://github.com/psf/requests/commit/96ba401c1296ab1dda74a2365ef36d88f7d144ef
https://github.com/psf/requests/pull/6965
https://github.com/psf/requests/releases/tag/v2.33.0
https://github.com/psf/requests/security/advisories/GHSA-9hjg-9r4m-mvj7
https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2
https://github.com/pypa/advisory-database/tree/main/vulns/pip/PYSEC-2023-228.yaml
https://github.com/pypa/advisory-database/tree/main/vulns/pip/PYSEC-2026-196.yaml
https://github.com/pypa/advisory-database/tree/main/vulns/pip/PYSEC-2026-3721.yaml
https://github.com/pypa/advisory-database/tree/main/vulns/setuptools/PYSEC-2022-43012.yaml
https://github.com/pypa/advisory-database/tree/main/vulns/setuptools/PYSEC-2025-49.yaml
https://github.com/pypa/advisory-database/tree/main/vulns/setuptools/PYSEC-2026-3447.yaml
https://github.com/pypa/pip/commit/10dfb6b9005484578b386f64b9f36982e3dc6679
https://github.com/pypa/pip/commit/389cb799d0da9a840749fcd14878928467ed49b4
https://github.com/pypa/pip/commit/8e227a9be4faa9594e05d02ca05a413a2a4e7735
https://github.com/pypa/pip/commit/b369bfc96cc524e00c267e1693290e6599c36bad
https://github.com/pypa/pip/commit/f2b92314da012b9fffa36b3f3e67748a37ef464a
https://github.com/pypa/pip/issues/13867
https://github.com/pypa/pip/pull/12306
https://github.com/pypa/pip/pull/13550
https://github.com/pypa/pip/pull/13777
https://github.com/pypa/pip/pull/13870
https://github.com/pypa/pip/pull/13923
https://github.com/pypa/pip/pull/14000
https://github.com/pypa/pip/pull/14110
https://github.com/pypa/setuptools/blob/6ead555c5fb29bc57fe6105b1bffc163f56fd558/setuptools/package_index.py#L810C1-L825C88
https://github.com/pypa/setuptools/blob/fe8a98e696241487ba6ac9f91faa38ade939ec5d/setuptools/package_index.py#L200
https://github.com/pypa/setuptools/commit/250a6d17978f9f6ac3ac887091f2d32886fbbb0b
https://github.com/pypa/setuptools/commit/43a9c9bfa6aa626ec2a22540bea28d2ca77964be
https://github.com/pypa/setuptools/commit/88807c7062788254f654ea8c03427adc859321f0
https://github.com/pypa/setuptools/commit/dd9f436a36486b4cb8a4c70a2321548b0be09b8f
https://github.com/pypa/setuptools/compare/v65.5.0...v65.5.1
https://github.com/pypa/setuptools/issues/3659
https://github.com/pypa/setuptools/issues/4946
https://github.com/pypa/setuptools/pull/4332
https://github.com/pypa/setuptools/releases/tag/v83.0.0
https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf
https://github.com/pypa/setuptools/security/advisories/GHSA-h35f-9h28-mq5c
https://github.com/theskumar/python-dotenv/commit/790c5c02991100aa1bf41ee5330aca75edc51311
https://github.com/theskumar/python-dotenv/commit/790c5c02991100aa1bf41ee5330aca75edc51311.patch
https://github.com/theskumar/python-dotenv/releases/tag/v1.2.2
https://github.com/theskumar/python-dotenv/security/advisories/GHSA-mf9w-mj56-hr94
https://huntr.com/bounties/d6362117-ad57-4e83-951f-b8141c6e7ca5
https://ichard26.github.io/blog/2026/04/whats-new-in-pip-26.1/#security-fixes
https://lists.debian.org/debian-lts-announce/2024/09/msg00018.html
https://lists.debian.org/debian-lts-announce/2025/05/msg00035.html
https://lists.debian.org/debian-lts-announce/2025/10/msg00028.html
https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/ADES3NLOE5QJKBLGNZNI2RGVOSQXA37R
https://lists.fedoraproject.org/archives/list/package-announce%40lists.fedoraproject.org/message/YNA2BAH2ACBZ4TVJZKFLCR7L23BG5C3H
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/622OZXWG72ISQPLM5Y57YCVIMWHD4C3U
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/65UKKF5LBHEFDCUSPBHUN4IHYX7SRMHH
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/ADES3NLOE5QJKBLGNZNI2RGVOSQXA37R
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/FXUVMJM25PUAZRQZBF54OFVKTY3MINPW
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/KFC2SPFG5FLCZBYY2K3T5MFW2D22NG6E
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/YBSB3SUPQ3VIFYUMHPO3MEQI4BJAXKCZ
https://lists.fedoraproject.org/archives/list/package-announce@lists.fedoraproject.org/message/YNA2BAH2ACBZ4TVJZKFLCR7L23BG5C3H
https://mail.python.org/archives/list/security-announce@python.org/thread/F4PL35U6X4VVHZ5ILJU3PWUWN7H7LZXL
https://mail.python.org/archives/list/security-announce@python.org/thread/F4PL35U6X4VVHZ5ILJU3PWUWN7H7LZXL/
https://mail.python.org/archives/list/security-announce@python.org/thread/IF5A3GCJY3VH7BVHJKOWOJFKTW7VFQEN
https://mail.python.org/archives/list/security-announce@python.org/thread/L2BNQGGVQCEV7DROOORQ7WFKKFF2OOQX
https://mail.python.org/archives/list/security-announce@python.org/thread/L2BNQGGVQCEV7DROOORQ7WFKKFF2OOQX/
https://mail.python.org/archives/list/security-announce@python.org/thread/QAJ5JIVWWCAJ4EZL2FP5MOOW35JS7LRJ
https://mail.python.org/archives/list/security-announce@python.org/thread/WIEA34D4TABF2UNQJAOMXKCICSPBE2DJ
https://mail.python.org/archives/list/security-announce@python.org/thread/YV63UET5D3OOJY7O4M5XCVYO2YM4NBYJ
https://mail.python.org/archives/list/security-announce@python.org/thread/YV63UET5D3OOJY7O4M5XCVYO2YM4NBYJ/
https://nvd.nist.gov/vuln/detail/CVE-2022-40897
https://nvd.nist.gov/vuln/detail/CVE-2023-5752
https://nvd.nist.gov/vuln/detail/CVE-2024-47081
https://nvd.nist.gov/vuln/detail/CVE-2024-6345
https://nvd.nist.gov/vuln/detail/CVE-2025-47273
https://nvd.nist.gov/vuln/detail/CVE-2025-66221
https://nvd.nist.gov/vuln/detail/CVE-2025-8869
https://nvd.nist.gov/vuln/detail/CVE-2026-102598
https://nvd.nist.gov/vuln/detail/CVE-2026-13346
https://nvd.nist.gov/vuln/detail/CVE-2026-1703
https://nvd.nist.gov/vuln/detail/CVE-2026-21860
https://nvd.nist.gov/vuln/detail/CVE-2026-25645
https://nvd.nist.gov/vuln/detail/CVE-2026-27199
https://nvd.nist.gov/vuln/detail/CVE-2026-27205
https://nvd.nist.gov/vuln/detail/CVE-2026-28684
https://nvd.nist.gov/vuln/detail/CVE-2026-3219
https://nvd.nist.gov/vuln/detail/CVE-2026-59890
https://nvd.nist.gov/vuln/detail/CVE-2026-6357
https://nvd.nist.gov/vuln/detail/CVE-2026-8643
https://pip.pypa.io/en/stable/news/#v25-2
https://pyup.io/posts/pyup-discovers-redos-vulnerabilities-in-top-python-packages
https://pyup.io/posts/pyup-discovers-redos-vulnerabilities-in-top-python-packages/
https://pyup.io/vulnerabilities/CVE-2022-40897/52495
https://pyup.io/vulnerabilities/CVE-2022-40897/52495/
https://requests.readthedocs.io/en/latest/api/#requests.Session.trust_env
https://seclists.org/fulldisclosure/2025/Jun/2
https://security.access.redhat.com/data/csaf/v2/vex/2026/cve-2026-8643.json
https://security.netapp.com/advisory/ntap-20230214-0001
https://security.netapp.com/advisory/ntap-20240621-0006
https://setuptools.pypa.io/en/latest

OfficialPyPIcurrentmetadata:
https://pypi.org/pypi/Flask/json
https://pypi.org/pypi/Werkzeug/json
https://pypi.org/pypi/requests/json
https://pypi.org/pypi/python-dotenv/json
https://pypi.org/pypi/pip/json
https://pypi.org/pypi/setuptools/json
<!-- END-ORIGINAL-DOC -->


<a id="doc-212"></a>

### Reference: `integration/security_maintenance94/DEPLOY-CONTRACT.md`

<!-- ORIGINAL-DOC {"bytes":1747,"path":"integration/security_maintenance94/DEPLOY-CONTRACT.md","sha256":"be8849c197919ba09a3d61544cca8b1b2b2b334fc77a274da7fa2bb43214b724"} -->
# Future deployment contract, not deployment approval

This exact profile was tested on CPython 3.10.12, Linux x86_64. Bootstrap: pip 26.2.1 and setuptools 84.0.0 from hash-locked wheels. Application: 25 packages in requirements-future-deploy.lock. Use only verified wheel bytes with --no-index --only-binary=:all: --require-hashes, then pip check and compare installed metadata and physical package hashes. No sdist builds, automatic resolver upgrade or untested optional extras.

A future deployment must recover all 25 wheel artifacts from the verified artifact records, including locally built sgmllib3k 1.0.0. That wheel is not published by this change. Do not call this a ready one-command public-index install. Existing Geo >= constraints alone are not this tested profile. GNews and trafilatura extras remain outside this lock and must stay off until separately tested.

This change does not create a Render service, select a build command there, update an OS/base image, stop a collector, create indexes, write to a database or send messages. No deployed dependency or provider closure claim. The 130 historical candidate alerts remain open and visible at their unchanged paths. Package-level remediation for 18 operational-source alert occurrences is separate from provider reindexing and deployment.

Retained limits: Windows safe_join tested only Linux string branch, not Windows filesystem; BSON >2GiB overflow not executed; no live Mongo tests. Old-bootstrap1150 author logs not independently rerun. Freshselected1150 ID set independently verified, not an independent entire-suite execution. Bootstrap26.2.1/setuptools84 tested; sgmllib existing local wheel reused, not rebuilt with new bootstrap. No build command/service selected.

<!-- END-ORIGINAL-DOC -->


<a id="doc-213"></a>

### Reference: `integration/security_maintenance94/README.md`

<!-- ORIGINAL-DOC {"bytes":1475,"path":"integration/security_maintenance94/README.md","sha256":"948d75c742537a022ce6beb7b52430649c323c8c6bce29d58d942a7b489828a0"} -->
# Security-maintenance94 preparation, not deployed

18 operational-source alert occurrences mapped exactID/GHSA/ranges from liveprovider. 130 historical research occurrences remainVISIBLE atunchangedpaths/bytes, notfixed/dismissed/renamed. Root requirements-staging isfutureintent, notRenderdeployed. Exactfuturelock requires Python3.10.12 Linuxx86_64 and hash-locked installer offlinephysicalwheels; no claimcrossplatform. Geo>=floorsminimalconstraints, notreproducibledeploy. Preserved BRICS/geo requirements intentionalmaintenancewithbeforebytes/hashes inrevisionrecord; sourcecodeunchanged. Existingoptionalgeo ENABLE_FULL_TEXT/trafilatura+ENABLE_GNEWS/gnews notincluded25closure, mustnotenable untilseparatelock+testreview. Future25closure coversstagingandBRICSroots, notevery optionalgeo path.

No liveDB/client/collector/send/Finder/deploy. Providercount148 unchangeduntilsave/reindex, historical130remainunresolved. Freshinstall/pipcheck/metadata/physicalpins/fullcurrent1150 regression must pass andindependentreview before save.

Retained limits: Windows safe_join tested only Linux string branch, not Windows filesystem; BSON >2GiB overflow not executed; no live Mongo tests. Old-bootstrap1150 author logs not independently rerun. Freshselected1150 ID set independently verified, not an independent entire-suite execution. Bootstrap26.2.1/setuptools84 tested; sgmllib existing local wheel reused, not rebuilt with new bootstrap. No build command/service selected.

<!-- END-ORIGINAL-DOC -->


<a id="doc-214"></a>

### Reference: `integration/weekly_report/README.md`

<!-- ORIGINAL-DOC {"bytes":3853,"path":"integration/weekly_report/README.md","sha256":"ea97d6a15ee2c5d33045df008bac94d2b14036fdc9644e0b8e41205b44fea16c"} -->
Copyright (c) 2026 Push

# weekly_report (offline weekly intelligence PDF)

Pure module with its own PDF writer. No network, database, application-file or settings reads, no clock reads, no sending or scheduling, no third-party runtime dependency (Python standard library only). The only outside read is the standard library's time zone lookup (zoneinfo reads the system tz database). The caller supplies rows and timezone-aware datetimes and gets PDF bytes back. Same input gives identical bytes; environment variables do not change output (tested, including SOURCE_DATE_EPOCH).

## Interface
- `build_weekly_report(news_rows, tariff_records=None, *, period_start, period_end, generated_at, display_tz="Asia/Kolkata", title=...) -> bytes`
- `summarize_week(...) -> dict`, `render_pdf(summary) -> bytes` (the renderer re-cleans every text, number and link in the summary it is given; only https links become PDF links)
- `sanitize_news_rows(rows, period_start, period_end, generated_at) -> (rows, stats)`
- `sanitize_tariff_records(records, generated_at) -> (records, stats)`
- Datetimes (including those in a summary passed straight to `render_pdf`) must be timezone-aware and between years 1970 and 2100 (ValueError otherwise). Period is [start, end) and must be 1 to 31 days long (ValueError otherwise); the per-day table lists every day of the period, never cut.

## Closed field lists (everything else is dropped, never echoed)
News: article_key, project, url, title, summary, source, original_country, category, published_at, collected_at, risk_level, credibility, score, corroboration_count.
Tariff evidence (own list): record_id, country, product_code, measure, rate_text, effective_date, source_name, source_url, captured_at, note.

## Rules enforced
https links only (scheme normalised to lowercase; only the default port, or :443; no credentials, backslash, spaces, control/invisible chars, non-ASCII, over 500 chars); dates need an explicit offset (naive, overflowing, over-long or out-of-range rejected and counted); items after generated_at or outside the period are excluded and counted; duplicates dropped; bool/NaN/inf and numbers beyond 10^12 rejected; text is first limited to 8 times its cap, then normalised, then cut to its cap, so huge input is cheap; input capped at 2000 news rows / 300 tariff records with the cut shown in "Data checks"; 25 top items and 60 tariff rows listed.
Risk labels and scores are printed as supplied; nothing is scored or inferred. Dates always show the zone, e.g. "05 Oct 2026, 08:00 IST (UTC+05:30)".

## PDF writer (_pdf.py, _render.py, _metrics.py)
Own code. 390 x 780 pt pages (a fit-to-width view on a 390 px phone is 1:1; smallest font is 9 pt, body 11.5 pt). Base-14 Helvetica and Helvetica-Bold, WinAnsi, not embedded, so no font files and no font licence in the product. Text outside the Western European set prints as "?" (stated in the report). Line widths come from `_metrics.py`: advance widths measured offline from a metric-compatible font; plain numbers, no font data. Metadata: Creator/Producer "Copyright (c) 2026 Push", creation date = generated_at; each page footer carries the same notice.

## Port note (Python and platform)
Needs Python 3.9+ for zoneinfo. On Windows or minimal images with no system tz database, install the `tzdata` package (free) or the time zone lookup raises. No other runtime dependency, nothing to pin. Test-only: `pypdf` (tested 6.x), optional `pikepdf` (structure check); keep these out of requirements.

## Not done / for Builder A
No route, button, schedule, mail or storage; wiring and where rows come from are A's. Fixture data only in tests. Not checked on a physical phone or in every viewer: checked with pypdf (strict), pikepdf/qpdf, poppler render and a visual look at every page.
Run: `python -m unittest discover -s tests/weekly_report -t .`

<!-- END-ORIGINAL-DOC -->


<a id="doc-215"></a>

### Reference: `intelligence/brics/README.md`

<!-- ORIGINAL-DOC {"bytes":4097,"path":"intelligence/brics/README.md","sha256":"ed3d3b027e4fc1ed3c5f091b742fd166b37b0d1eb2b77155aa26ec1ab927ac00"} -->
# BRICS Live Monitor

A fresh, standalone project — one unified dashboard combining live news,
embedded live video feeds, critical alerts, and the full source list, all
on a single page, plus a matching email digest. Not built on top of the
old Geo Intel Monitor codebase.

## What you get

- **One dashboard page** (`/dashboard`) — live video embeds at the top,
  a searchable/filterable news feed, a critical-alerts panel, and a live
  source list, all "at your fingertips" on one screen.
- **Live video** — embedded YouTube live streams for WION, CGTN, RT News,
  Al Jazeera English, France 24 (edit `config/streams.yaml` to add/remove
  any public YouTube channel — official summit broadcast can be added the
  same way once you have its channel ID).
- **Email digest** — same articles, grouped by category, plus a list of
  live-stream links (email can't play video, so it links out instead).
- **24/7**, either mode:
  - **Local**: `python run_all.py` — one command runs the collector loop
    and the dashboard together on your machine.
  - **Cloud**: deploy `web.py` to Render + MongoDB Atlas, driven by an
    external scheduler hitting `/trigger-collect` and `/trigger-report`.
- Everything else (storage, delivery channels, alerts) is togglable in
  `.env`, same pattern as before — all off except email/critical-alerts
  defaults, which you fill in with your own credentials.

## Quick start — local, everything visible immediately

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py init
python run_all.py
```

Open **http://localhost:5000** — the dashboard, live feeds, and article
list are all there immediately. The collector runs on startup and then
every `COLLECT_INTERVAL_MINUTES`.

To also get emails: edit `.env`, set `ENABLE_EMAIL=true` and fill in a
Gmail **App Password** (https://myaccount.google.com/apppasswords),
`EMAIL_FROM`, `EMAIL_TO`. Restart `run_all.py`.

## Cloud 24/7 (Render + MongoDB Atlas)

1. `.env`: `DEPLOY_MODE=cloud`, `STORAGE_BACKEND=mongodb`
2. MongoDB Atlas free tier → create cluster → database user → Network
   Access allow `0.0.0.0/0` → copy connection string into `MONGODB_URI`
3. Push this folder to GitHub, then on Render: New → Web Service →
   connect repo → build `pip install -r requirements.txt` → start command
   uses `Procfile` (`gunicorn web:app`) → add every `.env` variable in the
   Environment tab, including a real `TRIGGER_SECRET` (not `changeme`)
4. Confirm `https://your-app.onrender.com/health` returns ok, then visit
   `/dashboard` — live feeds and articles render the same as local
5. Set up an external scheduler (cron-job.org is free) to POST:
   - `/trigger-collect?key=YOUR_SECRET` every 15 min
   - `/trigger-report?key=YOUR_SECRET` at your digest times

## Adding/editing live feeds

Edit `config/streams.yaml` — each entry is a YouTube channel ID (or fixed
video ID). To add the official BRICS summit broadcast once you have its
channel, just add a new `channel` entry; no code changes needed.

## Adding/editing news sources

`config/sources.yaml` — same 33-source, 3-tier, 11-country BRICS list as
before, still fully editable YAML.

## Routes

| Route | Purpose |
|---|---|
| `GET /dashboard` (or `/`) | The unified live dashboard |
| `GET /export.csv` | Download all stored articles as CSV |
| `GET /api/articles` | JSON of recent articles |
| `GET /api/sources` | JSON of the current source list |
| `GET /health` | Uptime check |
| `POST /trigger-collect?key=SECRET` | Cloud mode: run one collect cycle |
| `POST /trigger-report?key=SECRET` | Cloud mode: run one report cycle |

## Notes

- Live embeds use YouTube's `live_stream?channel=` URL, which
  auto-switches to a channel's live broadcast if one is running, or shows
  their latest video otherwise — no API key needed, but verify channel
  IDs occasionally since they can change.
- Same data-loss-safe email logic as before: an article is only marked
  "sent" after a confirmed successful send.

<!-- END-ORIGINAL-DOC -->


<a id="doc-216"></a>

### Reference: `intelligence/geo/BACKUP-HELD184.md`

<!-- ORIGINAL-DOC {"bytes":1130,"path":"intelligence/geo/BACKUP-HELD184.md","sha256":"0cec4a68c00c56ab7640596668b6af165094fe58604b93eecace0ea5ea87f4af"} -->
# Backup request is not capability

ENABLE_TELEGRAM_BACKUP defaults false. An explicitly configured true value only
records requested configuration; it does not wire a sender or prove backup.
TELEGRAM_BACKUP_CAPABILITY remains held_pending_durable_adapter regardless.
RSS/GNews have no pre-write Telegram send. Durable full-record/outbox/journal,
exact destination acknowledgements and recovery checks remain required before
activation or a backup-completion claim. No existing flags, records or destinations
were changed in a live account. No mail or Telegram messages were sent.

Metadata cleanup stays held at the database/HTTP boundaries. A flag, message
link, stored short preview or hypothetical channel retention is not complete
recovery evidence and cannot authorize deletion or TTL. Existing records remain.

Apps Script's prior backup promise was already removed in unit180. Its current
collection wrapper does not promise backup. The edge guard's ban_seconds comment
now describes explicit/honeypot bans. Flood overflow refuses requests for the
rate window; it does not add a ban. Runtime rate/ban policy is unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-217"></a>

### Reference: `intelligence/geo/BROWSE-INDEXES192.md`

<!-- ORIGINAL-DOC {"bytes":1898,"path":"intelligence/geo/BROWSE-INDEXES192.md","sha256":"75921e949a46c7b4ba626314281037a9021d4db88b30c423829b0824b966c0ce"} -->
# Whole-store browse index candidates, source only

Four proposed indexes match185 raw sorts exactly: created_at/_id descending,
title/_id ascending(existing181name reused),country/_id ascending,
score/_id descending.181score/published/_id does not provide score/_id ordering
when published is unconstrained;181created_at lacks _id tie. These plans change
no read query/order/filters, no index drop/TTL and no collection/event calls.

init_db defaults provision_browse_indexes=False, separate from181query gate.
Both gates require literal booleans before connect; default retains four legacy
calls. Both true deduplicates shared title name,9newunique candidates pluslegacy.
No production caller sets either gate. Source gate is not permission to provision.

Tests compare candidate order to185source AST, mockedcreate_index contracts,
boolean defaults/dedup and explicitly synthetic explain shapes. These are NOT
real explain output, a Mongo planner, index utilization or performance evidence.
No DB contacted/index created bytests. No guarantee efficient filtering:185uses
find({},projection),rawsort then Python filtering; filtered scans may remainlarge.
No covered-read claim: article fields requireFETCH. No snapshot/count claim.

Before any separate owner-reviewed live provision: inspect actual schema/types,
collation, existing indexnames/keys/conflicts,storagecosts and real explain
executionStats for every sort and filter,includingSORTstages/keys/docs examined.
Review deployment/routing/cursor lifetime separately. No Atlas changes here.

Current source references verified2026-10-09:
https://www.mongodb.com/docs/manual/tutorial/sort-results-with-indexes/
https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/
Sort fields must follow index order/directions(or wholeinverse);non-prefix
subsets require equality on precedingfields. Source plans aren'tlive evidence.

<!-- END-ORIGINAL-DOC -->


<a id="doc-218"></a>

### Reference: `intelligence/geo/DATE-EVENTS182.md`

<!-- ORIGINAL-DOC {"bytes":1518,"path":"intelligence/geo/DATE-EVENTS182.md","sha256":"8be541293b1cf81e91423753b199c8b0d7904bf1049577ea4165df9894cd6406"} -->
# Optional GNews and event source checks

GNews uses the provider's `published date` field through the shared strict
publication-date policy. Missing, invalid, incomplete, naive/unknown-zone and
future values produce no candidate. Observation time is only a validation bound,
never the publication date. Known dates are stored in UTC ISO form. No provider
calls or GNews activation were made. ENABLE_GNEWS remains false by default.

Field evidence read from the provider source and README:
https://github.com/ranahaani/GNews/blob/master/gnews/gnews.py
https://github.com/ranahaani/GNews/blob/master/README.md
This documents current upstream field semantics, not certification of an installed
optional SDK version. Alternate backends or missing fields fail held rather than
using a synthetic time. No durable quarantine or source-completeness claim.

EVENTS is empty, not a fabricated placeholder. save_event requires a nonblank
name (at most 512 characters) and canonical valid YYYY-MM-DD before connecting.
Additional event fields remain compatible. This is minimum write validation,
not independent verification that a real event exists. Existing events were not
edited, deleted, loaded or reseeded.

collector120's inactive supplied-data adapter tracks reviewed source bytes and
accepts the actual publication field. Its fixtures now supply real synthetic
publication evidence instead of relying on the old fake-now behavior. Historical
stage evidence remains historical; no installed SDK/transport/schedule proof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-219"></a>

### Reference: `intelligence/geo/LEGACY-SANCTIONS183.md`

<!-- ORIGINAL-DOC {"bytes":1098,"path":"intelligence/geo/LEGACY-SANCTIONS183.md","sha256":"3fa609826c70127ae071e0828954ce098e8ac37c6c9d39266ffb5168654d93f2"} -->
# Dormant legacy sanctions hold

The legacy CSV import and text screening now raise LegacySanctionsHeld rather
than returning an empty success or misleading substring match. No transport
imports or network calls remain in this module. No callers or activation added.

The former CSV selected the first column. OFAC's current data specification
identifies it as ent_num (identifier) and the second as SDN_Name. That defect is
not repaired by assuming a position without a reviewed complete schema fixture.
Substring checks also do not establish entity identity or sanctions status.

Official field evidence:
https://ofac.treasury.gov/system/files/126/dat_spec.txt
https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/tutorial-on-the-use-of-list-related-legacy-flat-files

A future parser/matcher needs schema, bounded transport, name/alias coverage and
reviewed matching before use. This change supplies no current list, last-good
cache, screening result, sanctions clearance or production-readiness claim.
The independent sanctions-refresh.mjs pipeline and its review policy are unchanged.

<!-- END-ORIGINAL-DOC -->


<a id="doc-220"></a>

### Reference: `intelligence/geo/QUERY-INDEXES181.md`

<!-- ORIGINAL-DOC {"bytes":1720,"path":"intelligence/geo/QUERY-INDEXES181.md","sha256":"4232f5e045c4514a959b60228d6ec502e7701e7aeea4ab6367e0303ae558c740"} -->
# Source query-index proposals

connect() is locked for lazy initialization. MongoClient and database are built
locally and published together. Failed database selection closes the new client
and leaves both globals unset. Clients are shared per process, not per thread.
No connection, URI, live database or indexes were inspected by this change.

init_db() retains its existing four index calls. New compound candidates require
explicit provision_query_indexes=True; no production caller sets this flag.
This source-only gate is NOT permission to create Atlas indexes. The caller must
review current schema, names, duplicate keys, collation, storage costs and explain
plans separately before provisioning. No TTL or deletion indexes are added.

Candidates match existing queries, without changing filters or result order:
- score/published/_id/emailed: dashboard score order and unsent queue sort.
  emailed $ne true also includes missing fields; it is NOT an equality prefix.
  Filtering follows sort keys; this does not promise a cheap or covered query.
- published/_id: newest order; title/_id: title order.
- created_at: latest collection, retention review and date aggregates/ranges.
- risk_level/score/created_at: critical equality, score order, date range.
- score/created_at: weekly score order and date range.

Sort-first ESR tradeoffs can scan many rows when date ranges are selective.
Live explain evidence may choose a different range-first index. Existing URL
unique, score-only and event-name/date/date indexes remain; no indexes are dropped.
Default callers remain without the six extra provisioning calls. This closes the
source init race/proposal gap, not live index provisioning or performance proof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-221"></a>

### Reference: `intelligence/geo/README.md`

<!-- ORIGINAL-DOC {"bytes":20035,"path":"intelligence/geo/README.md","sha256":"adc826e5af1937625e557e98d9d851d4882cd33f4ab98769ad090cb94162522c"} -->
# Geo Intel Monitor V2

Python + MongoDB monitor for trade activity, sanctions/circulars, and
research papers, with automated HTML email, a browser dashboard, and
24/7 cloud deployment (Render + MongoDB Atlas + Google Apps Script).

## Changelog — Sept 2026 deployment fixes (post-manual)

These three changes were made **after** the `Geo_Intel_Monitor_V2_Manual.pdf`
was written, on top of that manual's Chapter 2 audit. Nothing else in this
package changed from the manual's description — collection, scoring,
classification, and dedupe logic are untouched. Same format as the manual's
own audit table for consistency:

| # | Finding | Fix |
|---|---|---|
| 1 | `ACTIVE_CATEGORIES` defaulted to `TRADE,SANCTIONS,RESEARCH` only. Real-world RSS output skews GEOPOLITICS/CONFERENCE/RISK, so a fresh deploy with the documented default routinely showed "0 relevant items" every cycle even while collection was working correctly. | Default widened to all seven categories: `GEOPOLITICS,CONFERENCE,TRADE,SANCTIONS,RISK,RESEARCH,GENERAL` (`config.py`, `.env.example`). **This is a default only** — set `ACTIVE_CATEGORIES` explicitly in Render's environment variables to narrow it back down to whatever subset you actually want. |
| 2 | `/digest-data` and the direct-SMTP `send()` path both marked articles `emailed: true` the moment the HTML was *built* — before confirming the email actually sent. A failed Gmail/SMTP send (quota, bad address, network blip) meant those articles silently vanished from every future digest despite never reaching an inbox, with no error visible anywhere. | `reports/email_report.py` now exposes `build_digest()` (returns html + article ids, marks nothing) and `mark_sent(ids)` (marks, called only after a confirmed send). `send()` now marks only after `sendmail()` returns without raising. Added `web.py` route `POST /mark-emailed` and updated `apps_script/Code.gs`'s `sendDigest()` to call it right after `GmailApp.sendEmail()` succeeds — so a failed send just means those articles repeat in the next digest instead of disappearing. `build_html()` is kept as a backwards-compatible wrapper (same old immediate-mark behavior) for `app.py`/`scheduler.py`, which send synchronously in one call anyway. |
| 3 | Mojibake (`♦♦♦♦♦♦`) in place of emoji in subject lines and digest headers. | Root cause: a stale/previous version of `apps_script/Code.gs` was still live in the Apps Script project (not a code bug in this bundle — `getContentText('UTF-8')` plus Flask's ASCII-safe `jsonify` already handle this correctly). **Action needed on your end:** fully replace the live Apps Script project's `Code.gs` with the one in this package and redeploy — editing in place isn't enough since Apps Script doesn't diff/merge, it just keeps whatever was last saved there. |

### Updated data-loss-safe email flow (supersedes manual section 7.1's description)

```
/digest-data (GET)                    Apps Script sendDigest()
  build_digest()                         GmailApp.sendEmail(...)
  -> html, critical_count,               |
     article_ids  ----response------->   | (only if send did NOT throw)
                                          v
                                     POST /mark-emailed
                                       {article_ids: [...]}
                                          |
                                          v
                                     mark_sent(article_ids)
                                       -> only NOW flagged emailed:true
```

If `GmailApp.sendEmail()` throws, `Code.gs` never calls `/mark-emailed`, so
those same articles are simply included again in the next digest — safer
than the old behavior, at the cost of an occasional repeat instead of a
silent loss.

## Two ways to run this

| | Local (`scheduler.py`) | Cloud (Render + Apps Script) |
|---|---|---|
| Use when | Testing on your own PC | 24/7 always-on deployment |
| Storage | Still needs `MONGODB_URI` (no more SQLite) | MongoDB Atlas |
| Timing controlled by | `DAILY_RUN_TIME`/`SEND_TIMES` in `.env` | Apps Script Script Properties (see "Deploying" section) |
| Email sent via | Direct SMTP from your PC | Apps Script/GmailApp (Render blocks outbound SMTP) |
| Entry point | `python scheduler.py` | `web.py` (via `Procfile`/gunicorn) |

If you're deploying to Render, skip straight to "Deploying" below —
`scheduler.py` and its `DAILY_RUN_TIME` setting are not used there at all.

## What's new

- **Self-contained daily scheduler** (`scheduler.py`) — no cron/Task Scheduler
  required; runs continuously, retries a failed email send up to 3 times,
  and logs everything to `logs/app.log`.
- **Categorized email digest** — sections for Geopolitics, Conferences &
  Meetings, Trade Activity, Sanctions & Circulars, Risk Signals, and
  Research Papers & Documents, each sorted by relevance score, plus a
  summary bar (total items / critical count / upcoming events).
- **Date-stamped subject line** so digests are easy to find/filter in your
  inbox (`🌍 Geo Intel Daily Brief — 03 Sep 2026`).
- **Instant critical-risk alert** (`ENABLE_CRITICAL_ALERTS=true`) — a
  separate email fires as soon as a CRITICAL item is detected, instead of
  waiting for the next scheduled digest.
- **Weekly trend summary** (`ENABLE_WEEKLY_REPORT=true`) — a 7-day rollup
  (top stories, category volume, most-mentioned countries) on top of the
  daily digest, sent on `WEEKLY_REPORT_DAY`.
- **Fuzzy duplicate filtering** — the same story reported by five outlets in
  one cycle now collapses to one item instead of cluttering the digest
  five times (`DEDUPE_THRESHOLD` in `.env`).
- **Telegram delivery** (`ENABLE_TELEGRAM=true`) — an alternative to
  WhatsApp/CallMeBot that uses the official Bot API (more reliable, no
  manual re-verification).
- **Digest archiving** — every day's HTML digest is saved to `archive/YYYY-MM-DD.html`
  (`ARCHIVE_DIGESTS=true`), so you have a browsable history even without
  digging through email.
- **Startup config validation** (`config_check.py`) — if a feature is
  enabled in `.env` but missing its credentials or dependency, the app
  tells you exactly what's wrong before running, instead of crashing mid-cycle.
- **Browser dashboard** (`/dashboard?key=...` on the Render URL) — live
  view of recent articles, upcoming events, risk/credibility breakdowns,
  and a search box, reusing the exact same MongoDB data as the email.
- **Source credibility + corroboration** — each source is tagged HIGH/
  MEDIUM/LOW credibility, and when the same story is confirmed by multiple
  outlets in one cycle, the digest shows "confirmed by N sources".
- **Two digests a day, no repeats** — articles are marked as sent after
  each digest, so the 10pm email only contains what's new since 10am.
- **Long-term Telegram archive** (`ENABLE_TELEGRAM_ARCHIVE=true`) — old
  articles get posted to a Telegram channel and removed from MongoDB, so
  the free 512MB Atlas tier doesn't fill up over months of continuous
  collection.

## ⚠️ Security first

Never hardcode email passwords, API keys, or phone numbers in the `.py`
files. This project reads all secrets from a local `.env` file (git-ignored),
via `config.py`. If you ever paste code containing a real Gmail app password
or API key into a script, chat, or repo, treat it as compromised and rotate
it immediately at https://myaccount.google.com/apppasswords.

## Install — Windows

    py -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env

Edit `.env`. For Gmail use a Google App Password, not your normal password
(requires 2-Factor Authentication to be enabled on the account first).

Test:

    python app.py init
    python app.py collect
    python app.py events
    python app.py email

Or run everything in one go:

    python app.py run

## Linux/macOS

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    python app.py run

## Optional features (off by default)

All disabled unless you flip the flag in `.env`:

| Feature | Enable with | What it adds |
|---|---|---|
| Full-article text | `ENABLE_FULL_TEXT=true` | Extracts full article text instead of the short RSS summary. Slower; some sites block scraping. (`trafilatura` is already in `requirements.txt` — just flip the flag.) |
| Google News keyword search | `ENABLE_GNEWS=true` | Adds keyword-driven search (geopolitics, summits/conferences, sanctions & trade terms) on top of the fixed RSS list. Keyword groups live in `config.GNEWS_QUERY_GROUPS`, joined with `OR`. (`gnews` is already in `requirements.txt` — just flip the flag.) |
| WhatsApp digest | `ENABLE_WHATSAPP=true` | none | Sends a short digest via [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/). |
| Telegram digest | `ENABLE_TELEGRAM=true` | none | Sends a short digest via the official Telegram Bot API — more reliable than CallMeBot. |
| Instant critical alert | `ENABLE_CRITICAL_ALERTS=true` | none | Separate email fired immediately when a CRITICAL item is found. |
| Weekly trend summary | `ENABLE_WEEKLY_REPORT=true` | none | 7-day rollup of top stories, category volume, top countries. |
| Digest archiving | `ARCHIVE_DIGESTS=true` (on by default) | none | Saves each day's HTML digest under `archive/`. |

Run a single piece manually:

    python app.py gnews       # Google News keyword collector only
    python app.py whatsapp    # send WhatsApp digest only
    python app.py telegram    # send Telegram digest only
    python app.py critical    # check for + send a critical alert only
    python app.py weekly      # send the weekly summary only

## What it monitors

- Geopolitics
- Trade / tariffs / export controls
- Sanctions signals (OFAC SDN list screening via `collectors/sanctions.py`)
- Country / risk signals
- Conferences / summits
- Research papers & reports (arXiv, NBER, CEPR/VoxEU, PIIE, BIS Research)
- Official-source feeds (WTO, UN, UNCTAD, PIB India)
- Major news (BBC, Reuters, NYT, Guardian, Al Jazeera, Hindu, Indian
  Express, Mint, Foreign Policy)
- Sanctions & trade-law trackers (Baker McKenzie, Global Trade & Sanctions Law)

## Local daily scheduling (only if NOT deploying to Render)

    python scheduler.py --now      # sends one digest now, then runs daily
    python scheduler.py            # just runs daily, at DAILY_RUN_TIME in .env

Leave this running in a terminal, `screen`/`tmux` session, or as a background
service. It logs every run to `logs/app.log` and the console, and if a
source fails or the email send fails, it retries the email up to 3 times and
then logs the failure and continues to the next day — it never crashes the
whole scheduler.

**Alternative for local use: cron / Task Scheduler**, if you'd rather the OS
handle timing:

Windows Task Scheduler: run `run_daily.bat` once per day.

Linux cron example:

    0 7 * * * /path/to/geo_intel_monitor_v2/run_daily.sh

For 24/7 always-on operation with twice-daily email, skip this section
entirely and use the "Deploying: Render" section below instead.

## Important

This is a monitoring/aggregation tool, not legal, sanctions-compliance,
investment or intelligence advice. Verify important facts at primary sources.
Some RSS feed URLs occasionally change or go offline upstream — each source
fails independently (logged, not fatal) so one broken feed never stops a run.

## Deploying: Render (free) + MongoDB Atlas (free) + Telegram + Google Apps Script

This replaces local SQLite + `scheduler.py` with continuous cloud
collection, full-data storage on Telegram, and scheduled emails at
whatever times you choose — without changing any collection, scoring, or
filtering logic. Follow these steps in order.

**1. MongoDB Atlas (metadata storage) — free M0 cluster**
1. Sign up at https://www.mongodb.com/cloud/atlas, create a free M0 cluster
2. Database Access → create a username + password (save these)
3. Network Access → Add IP Address → Allow access from anywhere (`0.0.0.0/0`)
   — Render's IP isn't fixed on the free tier, so this is required
4. Connect → Drivers → Python → copy the connection string. This is your
   `MONGODB_URI` (looks like `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/`)

**2. Telegram (full data storage) — optional but recommended**
1. Message **@BotFather** on Telegram → `/newbot` → follow prompts → copy
   the bot token it gives you → this is `TELEGRAM_BACKUP_BOT_TOKEN`
   (you can reuse the same bot/token as `TELEGRAM_BOT_TOKEN` if you also
   want the separate Telegram-digest feature — they don't have to differ)
2. Create a Telegram channel (private is fine — this is your database, not
   something to share)
3. Add your bot as an **admin** of that channel, with "Post Messages"
   permission
4. Get the channel's numeric chat id: forward any message from the channel
   to **@userinfobot**, or send a test message in the channel then visit
   `https://api.telegram.org/bot<token>/getUpdates` in a browser and read
   the chat id from the JSON (it looks like `-1001234567890`) — this is
   `TELEGRAM_BACKUP_CHAT_ID`

Once this is on (`ENABLE_TELEGRAM_BACKUP=true` in step 4 below), every
article collected gets its full record (full summary, all fields) posted
to this channel — that's your permanent full-data store. MongoDB only
keeps a short preview plus a link to the matching Telegram message. The
dashboard shows both: the metadata list from MongoDB, and a "📦 Full
record on Telegram ↗" link per article that jumps straight to the
complete data.

**3. Push this code to GitHub**
Render deploys from a GitHub repo. Create one and push everything in this
zip into it (all folders and files, including `Procfile`, `runtime.txt`,
and the hidden-looking `apps_script/` folder).

**4. Render (runs the app)**
1. https://render.com → New → Web Service → connect your GitHub repo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: leave default — it reads from `Procfile` automatically
4. Instance type: Free
5. Environment tab → add every variable from `.env.example`, with your
   real values: `MONGODB_URI` from step 1, a made-up `TRIGGER_SECRET`,
   your Gmail address for `EMAIL_FROM`/`EMAIL_TO`, a Gmail **App
   Password** (not your real password) for `EMAIL_APP_PASSWORD` generated
   at https://myaccount.google.com/apppasswords, and — if using Telegram
   backup — `ENABLE_TELEGRAM_BACKUP=true` plus the two values from step 2
6. Also add `PYTHON_VERSION` = `3.11.9` (avoids a known SSL bug between
   very new Python versions and MongoDB Atlas)
7. Deploy. Once live, open `https://your-app.onrender.com/health` —
   it should show `{"status":"ok"}`. Save this URL for the next step.

**5. Google Apps Script (scheduler + mailer + optional dashboard page)**
1. https://script.google.com → New project
2. Paste `apps_script/Code.gs`'s contents in as the main file
3. Click the gear icon (Project Settings) → check "Show appsscript.json
   manifest file in editor" → open that new file → replace its contents
   with `apps_script/appsscript.json` from this zip (this pins the
   script's timezone to `Asia/Kolkata` so whatever times you set below
   mean Indian time, not whatever timezone the script defaults to —
   change this in the manifest if you're in a different timezone)
4. Still in Project Settings, scroll to **Script Properties**, add:
   - `RENDER_BASE_URL` → your Render URL from step 4 (no trailing slash)
   - `TRIGGER_SECRET` → same value as Render's `TRIGGER_SECRET`
   - `EMAIL_TO` → your Gmail address (comma-separate for multiple people)
   - **`DIGEST_TIMES`** → set this to whatever times YOU want the digest
     sent, comma-separated, any number of them — e.g. `08:00,20:00` or
     `09:00,14:00,19:00,23:00`. If you skip this property entirely, it
     defaults to `10:00,22:00`. **This is the setting you control
     yourself — just edit this property to change your schedule, no
     code changes needed.**
5. Function dropdown (top toolbar) → select `setupTriggers` → click Run →
   approve the permissions it asks for
6. Click the clock icon (Triggers) on the left — confirm one `sendDigest`
   trigger exists for each time you put in `DIGEST_TIMES`, plus
   `keepAlive`, `runCollect`, `checkCritical`, `sendWeekly`, `cleanupOld`
7. **To change your send times later**: just edit the `DIGEST_TIMES`
   Script Property, then run `setupTriggers` again — it always rebuilds
   everything from scratch, so this is safe to re-run any time.

**6. Optional: dashboard as an Apps Script web page**
If you'd rather open your dashboard at a `script.google.com` link than
remember your Render URL:
1. In the Apps Script editor: **Deploy → New deployment**
2. Select type **Web app**
3. Execute as: **Me**. Who has access: **Only myself** (or "Anyone with
   the link" if you want to share it with others)
4. Click **Deploy**, copy the Web App URL it gives you
5. Open that URL in a browser — it shows your live dashboard, fetched
   fresh from Render/MongoDB/Telegram each time you load it

**7. Test it**
- Function dropdown → `sendDigest` → Run → check your inbox
- Wait ~10 min → check MongoDB Atlas → Collections → `articles` should be
  growing
- If Telegram backup is on, check your backup channel — you should see
  batched messages with full article records appearing
- Next day, check the Triggers page — "Last run" should show real
  timestamps instead of "-"

**Notes on how the scheduling works:**
- `keepAlive` pings `/health` every 10 min just to stop Render's free tier
  from sleeping — it's cheap and doesn't run collection
- `runCollect` does the actual (heavier) collection job every 30 min —
  that's what "24/7 collecting" means here, not collecting every few
  minutes. This is also when Telegram backup posting happens.
- Each digest only includes articles not already sent in a previous
  digest, so your 2nd/3rd/4th digest of the day won't repeat what an
  earlier one already sent — this holds no matter how many times you've
  set in `DIGEST_TIMES`
- Critical alerts and the weekly report are independent of the digest —
  they can still mention an item even if it already appeared in a digest,
  since they serve a different purpose (immediate alert / weekly recap)
- `cleanupOld` (monthly) only ever deletes MongoDB metadata, never
  Telegram messages — the full data stays on Telegram permanently

## Summary of env var changes from the previous version

If you had already deployed an earlier version of this project, here's
exactly what changed:

| Old variable | New variable | Why |
|---|---|---|
| `ENABLE_TELEGRAM_ARCHIVE` | `ENABLE_METADATA_CLEANUP` | Renamed: it no longer archives-then-deletes, it just deletes (data's already been on Telegram since collection time) |
| `TELEGRAM_ARCHIVE_CHAT_ID` | *(removed)* | No longer needed — cleanup doesn't post anywhere |
| `ARCHIVE_AFTER_DAYS` | `METADATA_CLEANUP_AFTER_DAYS` | Renamed to match the new behavior |
| *(new)* | `ENABLE_TELEGRAM_BACKUP` | Turns on full-data storage to Telegram |
| *(new)* | `TELEGRAM_BACKUP_BOT_TOKEN` | Bot token for the backup channel (can reuse `TELEGRAM_BOT_TOKEN`) |
| *(new)* | `TELEGRAM_BACKUP_CHAT_ID` | Chat id of your backup channel |
| Apps Script: `DIGEST_TIME_1` / `DIGEST_TIME_2` | Apps Script: `DIGEST_TIMES` | One comma-separated property instead of two fixed slots — set any number of times yourself |
| Apps Script: `ARCHIVE_DAY_OF_MONTH` / `ARCHIVE_TIME` | Apps Script: `CLEANUP_DAY_OF_MONTH` / `CLEANUP_TIME` | Renamed to match |
| Route `/archive-old` | Route `/cleanup-old` | Renamed to match |

If you're deploying fresh, none of this matters — just follow the steps
above with the current names.

## V3 ideas

Dedicated official calendars, better event extraction, PDF/document
collection, sanctions-list versioning, full-text search, 7/30/90-day
calendar view, stronger source/deduplication scoring.

<!-- END-ORIGINAL-DOC -->


<a id="doc-222"></a>

### Reference: `intelligence/geo/collectors/EXTRA-FEEDS-ATTRIBUTION-PLAN.md`

<!-- ORIGINAL-DOC {"bytes":2470,"path":"intelligence/geo/collectors/EXTRA-FEEDS-ATTRIBUTION-PLAN.md","sha256":"34709192eb06b524c6089f9fb3f0ba7dbac2df9a34f41562160c0eee0c683e05"} -->
# Attribution plan for EXTRA_VERIFIED_FEEDS (design only, nothing wired)

Why: every one of the 8 feeds is reusable only with credit. EC is CC BY 4.0 (credit plus indicate changes). UK feeds are OGL v3 (attribution statement). Council, ECB, BIS and WTO require citing the source. WTO also asks to be informed of reuse (landing TODO below). ECB asks that modified information be stated as modified.

Data model
- Each stored article keeps `source` (the feed name, already present) plus a new `attribution` object copied at ingest from EXTRA_FEED_ATTRIBUTION: provider, licence, licence_url, terms_url, line. The existing 25 feeds get no attribution field.
- Store it with the article so CSV and old rows keep it.

Where it shows
1. Article card or list row: the `line` text as small secondary text under the headline, with the licence name linked to licence_url (EC, UK).
2. Article detail view: provider, source, licence link, and an "Original article" link to the item URL.
3. CSV export: two added columns, `attribution` (the line) and `licence`. The existing 12 columns are unchanged.
4. A "Sources and licences" section or page listing the 8 providers with terms_url and licence, linked from the footer.

Rules
- All lines start with "Source:". Lines contain only what is true of every row. If wiring ever shortens or rewrites summaries, add a modified-text note then, not before.
- Never remove or hide the attribution line, including in dark mode or print.
- Attribution is data, not code credits.
- ECB: keep headline, link and date only. The ingest rule is in EXTRA_FEED_INGEST_RULES (drops summary, body, full_text). It must be enforced at ingest in the wiring phase with a test. The feed carries named-author speeches and interviews, and the ECB terms restrict reprinting author-named documents.
- UK: the line carries the OGL sentence. Do not reuse items that state other rights holders.

Landing TODOs (before wiring)
- WTO: the terms ask that the WTO be informed of reuse. The owner has to send that notice. It has not been sent. Do not wire without noting this.
- EC: confirm the Press Corner feed items carry no item-level copyright exclusions.
- Add the ECB ingest test: ECB rows contain no summary, body or full text.
- Re-run all 8 through strict publication_date() before wiring (last run: all verified).
- Wiring changes rss.py, so the collector113 and collector130 sha pins and the manifest/AST entries move. Coordinate the landing order with main.

<!-- END-ORIGINAL-DOC -->


<a id="doc-223"></a>

### Reference: `legacy-config/finder-README.md`

<!-- ORIGINAL-DOC {"bytes":7536,"path":"legacy-config/finder-README.md","sha256":"a039168172213205bf113faa40f76c19b18aafd8119a1e545c071792beb1e2ca"} -->
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

<!-- END-ORIGINAL-DOC -->


<a id="doc-224"></a>

### Reference: `portable_validation28/SPEC.md`

<!-- ORIGINAL-DOC {"bytes":4836,"path":"portable_validation28/SPEC.md","sha256":"1be50d743da2ee9235b0dc1acb4bcfd14a52dd38749b9db63b4c5c7ea92d81ec"} -->
# 28a SPEC + local harness only

LOCAL CPython3.10.12 Linuxx86_64 only. 28 remains OPEN. No existing tests fixed, no production policy changed. No target/ABI/Render/512MB/runtime-ready claim. CP312 execution NOT RUN, cannot be substituted by declared marker fixtures. 27b ownCP312sgmlwheelanchor awaits capableexecutor, remains separate queueddependency.

Source baseline8e7f5a6f11bd7ac497de73ce13156132990af3b2. Inert portable_validation28 additions only. Root/workflow/requirements/27a/27b bytes unchanged. source-allowlist hashes all existing files read for findings; drift fails. Existing27a verifier also rechecks its exactartifactinputset/sourceallowlist before local freshvenvs. No new pins, packageinstall only existingreviewed offlinehashed27aprofileinsideisolatedscratch. Artifactbytesnotrepo.

## Findings, not fixes

- tests/geospatial/test_map_route.py:70 creates '['*2000+'0'+']'*2000 and asserts rows=[], status.ok=False, reason='unreadable'. integration/geospatial/response.py:26 calls json.loads and at29 catches OSError/ValueError/RecursionError. Thus the assertion depends on whether depth2000 raises in the chosen interpreter. Current3.10.12recursionlimitmetadata1000; observationrowrecordsactualjson.loads outcome. This is SKIP, notpass/fixed. NoassumedCP312threshold.
- tests/test_dependency_audit.py calls Requirement.marker.evaluate({'extra':''}) for active/inactive historicalauditdependencies, leaving otherkeysambient. 28a independenttable suppliesall12markerkeys. Historicalaudit/lockbytes unchanged.
- tests/weekly_report/test_report.py imports pypdf in pdf_text/page/linktests; externalvalidator at404 importsoptionalpikepdf, skipsifabsent, otherwisecalls pdf.check(). 28a pypdf6.19.0 strictreaderopens generatedharmlessblank1page+checksmetadata. NOTequivalenttopikepdf.pdf.check(). pikepdf optional absent BLOCKED, notpass. No dependency added.
- tests/test_schedule_caller214.py defaults Asia/Calcutta; canonicalAsia/Kolkata usedelsewhere. Zoneinfoequivalence tested aroundfixed18:30UTCdateboundary, nofallbackorcreatedalias.
- collector110_prep/input_budget.py production MAX_DEPTH=8 unchanged. FIXTURE_DEPTH_PROBE=64 is harness-only nestedarraylanguageprobe, NOT generalJSONvalidator or newpolicy. Iterative strings63/64/65 give accepted/accepted/refusedfixture_depth_probe. NoRecursionErrortextassertion.

## Matrix and evidence

Every rowstatus oneofPASS/FAIL/SKIP/BLOCKED/NOT RUN withreason+actualinterpreteridentity. Countskipseparately. 3.12markerrows evaluate declaredfixtures on3.10, clearly NOTPython3.12 execution. Independentliteralexpectedtablehasbothversiondirections; current3.10versusdeclared3.12 switchprovesdeclareddrivesresult.

Zoneinfo resolvesbothrealkeys +05:30/samedatesat4fixedinstants. Requiredaliasabsent->BLOCKED noUTCfallback. Metadata systemtzdata.zi version/header +zonefilehashes. Existingbwrappatterndoesnotmounthostdpkgdatabase; tzdatapackagequeryunavailableisrecordedBLOCKEDmetadata, notinventedversion. Hostoutside-sandboxobservedtzdata2025b-0ubuntu0.22.04.1/system2025b, cacheorientationonly, notproofinsidecontainer.

Bwrap unshare-all RO/usr/lib/lib64+proc/dev, scratchonly, nohome/downloads; externalconnectrefused. HarnesscreatesONLYownharmlesssleepchild, subreaper, hardchildpid2secondtimeout, killsprocessgroupandwaitsleader+descendant, checksPIDsabsent. RLIMIT1GiB addressspace/CPU/filelimits PERPROCESS, NOTcombined512MBtarget. NoOOMstress. Noappserver/collector/provider/DB/userdata/mail.

Twofreshhashedvenvssemanticreceiptsbyteidentical; timestamps/absolutehostpaths excluded. Recursionlimit onlymetadata, PID/timeexcluded. Noenvironment-wide/venv/pycreproducibilityclaim. Negativeprobesdeclaredenvs/depth/tzabsence/skipnotpass/sourcedrift. Fulloldrootgatecountsremainhistorical, not28aevidence.

Harnessinitialattempts failed: /bin/sleep notmounted (corrected/usr/bin/sleep); hostdpkgpackageDBnotmounted (now metadataunavailable); testexpected11keys buttablehas12keys corrected. Discardedattemptvenvs, fresh2completepassrunslogged. Nooriginalcodefixes/dependenciesadded.

Remaining28b actualtestfixes requireseparatecontract/editallowlist+pinreview. CP312/realcandidateimagevalidator/bwrap/deadline/reap/combined512MBacceptanceUNRUN. Gunicorn22vs23,bcrypt5,extras,nativeprivateinternals,historicalwheelopen.27/28/29open.

Re-run (sameinterpreter,bwrap and exact27aartifacts supplied separately):

    python3 portable_validation28/run_local.py /path/to/baseline-with-overlay /tmp/28a-clean /path/to/exact27a-artifacts
    python3 portable_validation28/test_harness.py

Runner requiresfreshnonexistentworkdir. Tests import onlyinactiveharness. No workflow/import by existing app.

Run the harness ONLY through run_local.py. Its sandbox-only assertions deliberately fail elsewhere. 28 remains OPEN; 28b actual fixes need a separate contract and pin review.

<!-- END-ORIGINAL-DOC -->


<a id="doc-225"></a>

### Reference: `portable_validation28b/SPEC.md`

<!-- ORIGINAL-DOC {"bytes":1200,"path":"portable_validation28b/SPEC.md","sha256":"e688f5910543e6f55baa36d5e4e6f452f4c2dbc0bc4cb7d5838625bd4160a4a6"} -->
# 28b1 actual portable test fixes

Only two tests and derived metadata change. The production loader is unchanged. Run the focused tests with `python -m unittest tests.geospatial.test_map_route tests.test_dependency_audit`. Run `python portable_validation28b/negative_tests.py` to confirm that escaped recursion, accepted unsafe shape and ambient marker evaluation fail. Mutated files are restored even on failure.

Real depth 2000 never reports ok; allowed reasons are unreadable or bad_shape. Recursion and nested-array shape have separate exact refusal checks. Audit receipt identity supplies the historical marker environment; remaining keys are fixed labelled test context. The real pypdf historical requirement is checked as true for 3.10 and false for 3.12. Ambient 3.12 is mocked during the entire closure test. CPython 3.12 execution is NOT RUN.

The old 28a allowlist, receipts and logs remain historical bytes. Its unchanged runner on this tree fails at expected source drift. Historical cache verification still skips as unverified; current interpreter tag checks are unchanged. Validators, pikepdf, TZ, 512MB and profile conflicts remain open. Item 28 is OPEN. No production activation.

<!-- END-ORIGINAL-DOC -->


<a id="doc-226"></a>

### Reference: `proxy_runtime/CORS190.md`

<!-- ORIGINAL-DOC {"bytes":1783,"path":"proxy_runtime/CORS190.md","sha256":"52948353421d769aabbffd47971d7f03ebe805cce095c42e5fcc6570e46a4d4e"} -->
# Proxy CORS (source-only)

PROXY_ALLOWED_ORIGINS defaults empty: browser cross-origin requests denied403.
Operator-reviewed comma-separated1..10 exactcanonicalHTTPSorigins, no path,
credentials,query,fragment,trailing slash,spaces,duplicate,wildcard/null. No
legacyorigin guessed or activated. index.html currentlynamesaFinderorigin; that
source string is not an owner grant for configuration. PublicmergedofflineFinder
stillhasnetworkOFF. LegacyproxydeploywithoutallowlistwillstopbrowserAI/ships:
separateowner-approvedoriginconfiguration is needed beforethatlivecutover.

SingleexactOrigin reflected with Vary: Origin; allresponse/error/providerbranches
remove wildcard. No Access-Control-Allow-Credentials. Unknown/null/duplicate
Origin403beforehandler/providerwork. OPTIONSneedsOrigin/exactGETorPOSTandonly
Content-Type/x-app-token (single,≤200headerchars,knownuniqueheadernames);204maxage600.
ServerrequestswithoutOrigincontinueexistingtoken/rateconstraints,nocorsheader.
CORSisnotauthenticationorprotectionagainstdirectservertraffic. PublicAPP_SECRET
hintstillnotuserauth. AIS/providerkeys,anonymousbudgets,trusttopologyunchanged.
No liveenvironment/settings/providers/DB/mail calls; no actualprovidercall tests.

Tests purepolicy+VMproxyfixtures: defaultemptydenies/exactreflect/null/duplicate/
canonical/preflight/methodheaderrejection; integratedbadOriginzero fetches,allowed
providerresponsepreservesexactOriginandnowildcard,nocredentials,nativehealthno
Origin; existingidentity/AISfixturesstillPASS. Realbrowser/platformproxyheader
normalization/currentoriginconfignotverified, no claimofliveCORSinstallation.

https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS
https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin

<!-- END-ORIGINAL-DOC -->


<a id="doc-227"></a>

### Reference: `proxy_runtime/IDENTITY-POLICY.md`

<!-- ORIGINAL-DOC {"bytes":3482,"path":"proxy_runtime/IDENTITY-POLICY.md","sha256":"87a2a181784c536a33940b7ca2aac9aff8f849565b8de17051b1793484ecad76"} -->
# Anonymous proxy boundary

The Finder remains public and anonymous. APP_SECRET is embedded public client material, a compatibility hint only, not private authentication. Knowing it grants no extra routes. No sign-in barrier is added.

Both AI and ships now use the socket peer by default. CF-Connecting-IP and X-Forwarded-For cannot choose identity without an explicit verified trust configuration. Behind a proxy this conservatively shares the peer bucket until its topology is confirmed.

Optional PROXY_TRUSTED_PEERS is a bounded comma-separated list of exact IPs, not CIDRs or wildcard trust. Nonempty trust requires PROXY_XFF_TOPOLOGY_VERIFIED=single_appended_hop. Only those direct peers may supply one XFF header. The last appended address is selected; malformed, duplicate or oversized chains fall back to the socket peer. These assertions are not proof of actual infrastructure. No deployment configuration was changed.

Per-peer limit is reduced to 20 requests per 10 minutes to prevent one verified client draining all 60 shared slots. A shared process-wide limit of 60 accepted AI requests per 10 minutes now limits bypass by many clients. Provider failover also counts every upstream attempt against a separate 60-attempt process-wide budget. Keys do not multiply that budget. Denials may consume a peer slot conservatively. Restart resets process memory; multiple workers/instances have separate budgets. Provider 4xx failures consume upstream attempts too. Distinct-peer flooding can still exhaust the shared budget; protecting the hard cap favors denial over availability. This is not a durable global quota, token/output budget or proof of zero billing. Before enabling network provider wiring, verify free-tier zero-spend account settings and a deployment-wide budget appropriate to the actual instance count.

No provider call, key rotation, live config change or private authentication provisioning was performed. Tests use fixture keys and fake network responses.

Until actual Render proxy peer IPs and single-appended-hop evidence support trusted configuration, ALL users behind one proxy share the same 20-per-10min peer bucket per instance (shared cap60). This is an intentional conservative availability regression from spoofable per-user XFF buckets. No peer IPs are guessed.

PROXY_PER_PEER_LIMIT and PROXY_SHARED_LIMIT are configurable positive decimal integers up to1000, defaults20/60; per-peer cannot exceed shared. Malformed config fails startup closed. Upstream-attempt budget remains60. Raising request limits does not raise this attempt cap or authorize account spending. After trusted topology is verified, individual client20/10min buckets apply, still under shared60 requests and60 attempts. Request/attempt caps bound traffic, not token cost, provider billing or a durable global spend budget.

179: /ships uses a separate 20-per-peer and 60-shared read budget per 10 minutes.
The socket/verified-proxy identity policy is unchanged. AI request budgets
(20 per peer, 60 shared) and 60 upstream attempts remain separate and unchanged.
Snapshots are cached for 30 seconds, with at most 64 known port keys. Unknown
ports return 400. Ships 429 includes Retry-After: 600. Finder stops automatic
polling and blocks manual retry until at least 10 minutes have passed.
Reading the cache causes no AI upstream attempt. Cached status and updated time
are from the snapshot, not a new AIS observation. This is not a shared
cross-process quota or cache.

<!-- END-ORIGINAL-DOC -->


<a id="doc-228"></a>

### Reference: `runtime_build/CONTRACT27b.md`

<!-- ORIGINAL-DOC {"bytes":6320,"path":"runtime_build/CONTRACT27b.md","sha256":"53fab7a41602e630db7692240367b1faff8f6d6ffe42de876f1f0b920c8a6801"} -->
# Candidate27b incomplete source draft

candidate image target chosen by runtime and reviewer for build-input closure

fetched-and-hashed CP312/deb candidate inputs, byte-compared 11 Python module sources; build not run; no install, import, ABI, closure or target-solver proof.

PathA: Ubuntu24.04 linux/amd64 aptCPython3.12. PathB not evaluated. HostworkflowUbuntu24.04 is not proof of containerOS. NoRender target claim.27/28OPEN;29advancesinputclosureonly.

Registry digests: observed from the registry's own responses and re-observed by two parties. Tag 24.04 is mutable, discovery only. Observed at 2026-10-10, not a claim of what the tag points to later.

Apt metadata: signature-valid against a keyring SUPPLIED from the workspace, not independently authenticated. Fingerprint matches a public Ubuntu-hosted mailing-list page - corroboration, not a trust bootstrap. Reviewer's gpgv run used the same supplied keyring, so it adds reproducibility but no new authentication. The Dockerfile's apt trust path (keyring package or key file) must be pinned by hash in the inputs and named as such.

noble InRelease dates 25 Apr 2024 (release pocket); updates/security 8 Oct 2026. Snapshot id 20261009T000000Z is the single pin for all three. Record that pocket dates differ. Apt behaviour with snapshot URL + these suites must be fixed in apt.sources; the apt.sources hash is what build-args.REVIEWED_APT_SOURCES_SHA256 carries.

The deb closure is a local apt_pkg metadata traversal, NOT an apt/dpkg solve against the target image. It does not prove installability or closure. Never say "closure verified".

## Refusal state

inputs/application.pending.lock deliberately excludes sgml wheel pin. inputs/application.lock is ABSENT. OwnCP3122builds/outputanchor pending capableexecutor. Existingworkflow required-filecheck MUSTfailmissingapplication.lock. Dockerfile also refusesmissingreadylock BEFOREapt/network. No guessed27a wheelhash reused. Neednewreview beforeaddingreadylock orlocalbuiltwheel fetchroute. This is not a workflowreadybundle or executablebuild plan.

Exactmanifest covers allruntime_buildfilesincludinghistorical27a additions; excludesonlyinputs-manifest.json+inputs.sha256 perworkflow. Historical27a change-manifest/README/evidence bytes untouched anddo notcover27bnewfiles. Newchange-manifest27b.jsoncoversonly27badditions excludingitselfandanchorfiles (listedseparatelyreceipt). Rootmetadata/locks/requirements/.githubuntouched.

## Apt approach

Use apt signed snapshot sources ONLY, roots explicitpkg=version. apt --simulate chooses actualbase-dependent plan, rejectsremoval/unlistedversion/downgrade; download-only apt checks signedindexhashes. Explicitdpkg-deb package/version/arch+size/SHAchecksagainstledger before apt --no-downloadinstallation. apt -y --no-download rather thanwholesaledpkg-i permitsnormal dependencyconfiguration, no networkfallback. Entirepostinstallpackage-set mustexactmatch146name/version post-install anchor including92basepackages+54Inst fromlocalapt2.4.14metadata/base-statussolve.119downloadledger is superset, NOT wholesale install. Suppliedbaseidentity is boundtodigest, notpackagebytehash. Realnobleaptmaychoosedifferently; failrequire newanchors. No solverproof or no-downgradeproof yet.

Ubuntuvenv initiallyusesUbuntuensurepip's pinnedpython3-pip-whl/setuptools-whl, then26.2.1/84.0.0hashedofflinebootstrap replacesitandmetadataassertionchecks. WheelsdownloadedbyfixedpublicURL+size/SHA beforepip --no-index --require-hashes fullresolver. CompleteappinstallcannotoccuruntilownCP312sgmlwheelhash+bytesroute reviewed. Currentfetch_verify deliberatelydoesnotfetchlocaloutput.

## Launcher and limits

Csource reviewedcandidate only. Localhostgcc syntaxcheckpassed, NOTtargetcompile/execution. LauncherfixedcandidatePython path, closesnonstdiofds, no_new_privs andseccompdenies socket/connect/bind/listen/send/recv/io_uring, rejectswrongarch+x32. Itisnot generalfilesystem/processsandbox, processdeadline/reap acceptance or512MBproof. It doesnotstartapp/server/client/provider. FinalUSER65534, no appentrypoint. RUN stages use workflowbuildnetworkdefaultforpinnedfetch; no runtime--networkinstruction. PipofflineflagsdonotproveOSnetworkisolationduringbuild. Actualseccompenforcementdependsontargetkernelandmustbetestedlater. No claims beyondsourceinspection.

Dockerpull/build/workflowdispatch separateownerpermission+capableexecutorhandoff. Neitherbuilder norreviewer hasDocker/CPython3.12. No runattempted. ONE139430byteca-certificates-bootstrap.deb is a namedauthorizedbinaryrepoexception forTLSbootstraponly; nowincludedinchange/inputmanifestsandreceipt. Noother.deb/wheel/imagebytescommitted; publicledgers,suppliedhash-pinnedkeyringandcode/docs. Baseimagebyteswerenotpulled. RootconflictsGunicorn22vs23,bcrypt5,extras,nativeprivateinternals,historicalwheelremainopen.

## Revised source gates and remaining limits

Dockerfile has not run; originalblockers1(TLSbootstrap)and2(postinstalledset)wereexpectedtofailoriginaldraft. RevisedcandidateusesbootstrapONECA.debreadonlyextraction,121sortedMozillaPEMconcatenationhash9481fcd95f41b221f02f14d896535fe500bec539bc563c4cdca1acee483a8bdd, explicitCaInfo. PeerverificationNEVERdisabled. Suppliedderivedartifact NOTsystembundleorblacklist-equivalent. AfteraptinstallsCApackage normally, postinstexecutesupdate-ca-certificates/writes/etc/ssl/certs, thenCaInfoSWITCHEStothesystembundleandapt-getupdateverifiesTLS. Bootstrap extractiondoesnotexecutepostinst; laternormalinstallDOES. Stoponbadbundle/hash/TLS.

Postledgerbase92names/versionsboundtobaselayerdigestonly.89snapshot.debhashesaresame-version.deb hashes,NOTlayerpackagefilesproof. libaudit-common/libaudit1=1:3.1.2-2.1build1.1 andlibssl3t64=3.0.13-0ubuntu3.15 haveNOindividual.debhash, versionidentityonly. Openssl3.0.13-0ubuntu3.16plannedwhilelibssl3t64 staysbase. Localaptaccepts version skew; noterrororABIproof. Realaptupgradinglibssl/audit changes146ledger->failnewanchorrequired. No guessedhashes.

Finalimagecontainsgcc/libc6-dev/bubblewraptoolchainbytes, candidateonly. No stripping/multistageclaim. Shelltestsseparatewith explicit ||exit, plan/before/afterloggedBEFOREgateandEXITtrapprintsavailablefailureevidence. Compilesource andshellsyntaxonlylocal, nottargetapt/Docker. InputsremainincompleteuntilownCP312sgmlanchor. Noexisting27a/rootedits.

<!-- END-ORIGINAL-DOC -->


<a id="doc-229"></a>

### Reference: `runtime_build/GUNICORN26-SUPERSESSION.md`

<!-- ORIGINAL-DOC {"bytes":1076,"path":"runtime_build/GUNICORN26-SUPERSESSION.md","sha256":"3237773e61323ca801ef19cc1db4fa86eaeec6f75ece0c2117d050591681cab0"} -->
# Current Gunicorn26.2 supersession, not historical proof

Active app locks/packages/artifact rows use26.2.0; prior22 artifact rows retained as historical fields. Old change-manifest.json, change-manifest27b.json, input/fetch receipts, receipt1/2/run logs and immutable source anchors remain historical and unchanged. They do NOT prove this revised profile installed, passed targetbuild or native/CP312 checks. Current exact runtime_build input manifest includes the supersession and changes; application.lock remains absent/pending. No workflow dispatch/build/deploy or activation.

Fetched Gunicorn26.2 purePythonwheel228389B from officialPyPI, SHA256bd249d0b3f7972f7432f0a6b6ff3b3ee2d129f70cd1ff6c09a9dd9e29a2b88e3. RequiresPython>=3.10, no default RequiresDist; optionalextras not selected. CP310 isolated fixture tests172 passed with current Flask/Werkzeug/PyMongo/requests versions; not CP312target or Gunicornlive-server proof. Existing historicalrunnerdownload arrays stay22 and tests use the historicalpackage row for those observations, not reinterpretoldbytesas26.

<!-- END-ORIGINAL-DOC -->


<a id="doc-230"></a>

### Reference: `runtime_build/README.md`

<!-- ORIGINAL-DOC {"bytes":5616,"path":"runtime_build/README.md","sha256":"a2d3b4d2e5ad44f5432885a5a5506f12f4fd98f1c46ba9f9c83ced9f6f86f47b"} -->
# 27a local evidence only

local CPython3.10.12 Linuxx86_64 venv build/import proof

Item27 remains OPEN. Items28/29 remain OPEN. No Docker, Render, Ubuntu24.04, CPython3.12, runtime verified, 512MB, env parity or native ABI claim. No service, DB, client, credentials, mail, provider, collector or application startup is selected by this package.

Root source anchor:695f7420b15521e73423092abd7f8bc2b7002771. Existing app, requirements, root locks, workflows and staging remain unchanged. This directory is additive and no existing installer selects it.

## Profiles and unresolved closure

- Local selected application evidence profile: future lock25versions, Gunicorn22.0.0. This is a test choice only, not production choice.
- Security candidate uses Gunicorn23.0.0. Conflict remains unresolved.
- Staging includes bcrypt5.0.0; absent from25package lock. Preview bcrypt path is not exercised. No closure claim.
- Native200 pins were audited against a CP312wheel. All11 corresponding Python source files in fetched CP310wheel byte-match. Private-internals portability and nativeABI remain unresolved; native provider stays off, no client is created.
- GNews/trafilatura extras are not selected and not closed.
- 217mount,201cwrite,sender222consumer and actualruntimeactivation remain held and separately owned. This package does not implement them.

## Historical artifact

Historical sgmllib wheel SHA d697b1ce32621812e6fbf5d3dac57818192068f47e4b6f39bc76e14a8fb4c534: not available, not reproduced, not used. Recovery remains OPEN. New candidate e9700ff7e63fc008b252e8ff564641874f4521d29fdaa9daebe7c234dad83560 has different bytes. It is not equivalent to or a replacement for historical wheel. Different recorded bootstrap/toolchain and fixed timestamps do not prove a sole cause. Officialsdist unchanged and source member bytes match historical review.

Two clean candidate builds produced equal wheel bytes. This statement covers that wheel only, not virtualenv, pyc or full environment reproducibility. A reviewed output hash anchor is required before install proof.

## Fetch and test boundaries

Network only during pinned-fetch stage, domains pypi.org/files.pythonhosted.org; source archive discovery uses api.github.com/codeload.github.com. Tests/builds use bwrap unshare-all with no hosthome/downloads, no source credentials. Offline pip --no-index --only-binary=:all: --require-hashes and full resolver. No --no-deps install and no network fallback. Import allowlist explicitly excludes servers, DB/client creation, providers and real collectors. Tests AST-execute selected original functions with supplied mock fixtures only.

Every artifact is separately recorded: fetched+checked public artifact rows; supplied repo source bytes with exact sourceallowlist; merely named historical unavailable wheel. Fetch times are provenance metadata, not part of byte-stable receipt. Interpreter existed in Ubuntu22.04 environment: binarySHA recorded, dpkg3.10.12-1~22.04.18; installation source not recovered. No officialbinary origin claim.

The verifier fails on missing/extra/nonregular artifacts, wrong hashes and source drift. Negative cases cover tamperedwheel, wronghash, missingwheel and extraunpinnedpackage. Installed distribution set must exactly equal declared application+bootstrap names/versions. Two clean run deterministicreceipt comparison excludes timestamps, paths and pyc. No venv reproducibility claim.

## Re-run

From exact baseline source233 plus additive candidate directory, with all28recorded artifacts supplied separately:

    python3 runtime_build/prepare27.py /tmp/27a-clean /path/to/source233 /path/to/exact-artifacts
    python3 runtime_build/run27.py /tmp/27a-clean

Source233 is commit695f7420b15521e73423092abd7f8bc2b7002771. Re-read/re-hash the exactsourceallowlist before copying. Paths shown are placeholders, not deploymentpaths. run27.py insists on the recorded /usr/bin/python3.10 hash and version; a different3.10.12binary is not silently equivalent. Reviewer unable to meet this must state rerun unavailable or explicitly review distinct interpreter provenance. Requires bwrap namespaces and /usr,/lib,/lib64. No512MBproof; testresource ceiling1GiB.

fetch27.py is a separate public pinnedartifactfetch stage and refuses non-files.pythonhosted.org origins/redirects. It does not fetch or invent the locally built candidate wheel. Its ledger goes to stdout with actualfetch instants. Deterministic receipt excludes fetch/build times.

Builder first-hand PyPIJSON/file-byte checks and reviewer SECONDARYcorroboration of wheel0.45.1/sdist are different evidence. Do not report reviewer as first-hand PyPI verification.

Initial test harness mistakenly requested bs4, an unselected extra. That failed; no dependency was added. Allowlist corrected; all oldvenvs discarded before two fresh successfulruns. The correction narrows claims, not selects runtimeextras.

## LAND contents

The Git index contains only runtime_build additions, not artifact-inputs or the selected-source scratch copy. No binary wheels are added to the repository. The28artifacthashes live in artifacts.json; prepare27.py needs their bytes supplied separately. Existing selected-source bytes are already in source233. Root staging-manifest.json, audit.json and import-inventory.json remain historical233, byte-identical, and do NOT cover runtime_build. With respect to rootmanifest, unmanifestedfiles are staging-manifest.json, four.githubfiles and all27runtime_buildfiles. change-manifest.json lists26newfiles and excludes only itself. Rootgate2175/closurecounts remain historical, not overlayproof.

<!-- END-ORIGINAL-DOC -->


<a id="doc-231"></a>

### Reference: `runtime_executor27c/SPEC.md`

<!-- ORIGINAL-DOC {"bytes":6676,"path":"runtime_executor27c/SPEC.md","sha256":"b5203097aa7df4b061c4541b169d51c996fbc11d1264cfbe8f3b78bbe0190953"} -->
# 27c inert executor-discovery preparation

27c executor-discovery preparation; Docker/CP312 NOT RUN; 27/28/29 OPEN

This unit does NOT implement execution, failure capture, or Stage B. A future adapter needs its own contract and review. Failure-log retention is OPEN, not satisfied. The package is local preparation only, not selected by any workflow or application.

Baseline: 4cf969029042c29b8e5ea0c604c0d1b52d4db34d. Existing runtime_build, workflows, portable_validation28 and workflow_package29 are unchanged. No new binaries are added. The existing CA deb and supplied keyring would be reused by pinned hash, not copied into this package.

## Default and refusal paths

prepare.py with no arguments returns NOT RUN without reading pins, writing files, using the network or starting subprocesses. Stage A with its technical gate off does the same. Unknown, duplicate, missing or wrong arguments return REFUSED.

Gate ON inspects source pins only and returns NOT RUN. Stage B always returns REFUSED, even if a caller supplies an anchor filename. A filename does not authenticate approval. execute_reviewed raises before any subprocess call. The execution adapter is absent. Tests mock subprocess, socket, read and write paths and confirm zero calls on the default path.

A technical opt-in is not owner permission or executor capability. Any future Docker pull, build, dispatch or package execution needs a separately reviewed adapter and the owner's separate approval for that task.

## Stage A is not implemented

plan_only.sh contains only printf and exit. It has no executable apt, dpkg, Docker, fetch or install path, including through arguments or environment variables. Dockerfile.discovery is a FROM scratch placeholder with no COPY, RUN or entrypoint. Neither file implements Stage A.

The comparison function is exercised only on labelled fixtures. Identical fixture pairs return MATCH, but install_permitted remains false. Added, changed, downgraded or removed fixture pairs return STOP. Actual target-plan acquisition, parsing and comparison are unimplemented and OPEN. Fixtures are not real apt evidence.

The base image anchor records apt 2.8.3. Target executor behaviour is unobserved. The local apt 2.4.14 metadata/base-status simulation from 27b is not reused as target execution evidence. A future Stage A must stop before installation, return its real plan for review, and compare the resulting name/version pairs with the reviewed 146-pair anchor. Any difference requires a new anchor round. Even a match does not grant installation permission.

## Fixed trust tiers

Registry digests: observed from the registry's own responses and re-observed by two parties. Tag 24.04 is mutable, discovery only. Observed at 2026-10-10, not a claim of what the tag points to later.

Apt metadata: signature-valid against a keyring SUPPLIED from the workspace, not independently authenticated. Fingerprint matches a public Ubuntu-hosted mailing-list page - corroboration, not a trust bootstrap. Reviewer's gpgv run used the same supplied keyring, so it adds reproducibility but no new authentication. The Dockerfile's apt trust path (keyring package or key file) must be pinned by hash in the inputs and named as such.

noble InRelease dates 25 Apr 2024 (release pocket); updates/security 8 Oct 2026. Snapshot id 20261009T000000Z is the single pin for all three. Record that pocket dates differ. Apt behaviour with snapshot URL + these suites must be fixed in apt.sources; the apt.sources hash is what build-args.REVIEWED_APT_SOURCES_SHA256 carries.

The CA deb is the ONE reviewed repo-binary exception: the existing runtime_build/inputs/ca-certificates-bootstrap.deb, 139,430 bytes. It is not duplicated here. The derived bootstrap bundle is the concatenation of 121 sorted Mozilla PEMs, not the system bundle and not blacklist-equivalent. Its exact hash is in the reviewed derivation ledger. Bootstrap extraction does not run postinst or disable TLS verification. Future normal package installation would be a separate action and may run postinst.

Upstream index and network availability remain unreviewed for future execution. The default path does not create an input directory or fetch anything.

## Stage B is queued, not implemented

Only after a real Stage A has an accepted anchor and a capable executor route may a separately reviewed adapter install needed packages and record the actual CP312 interpreter, binary hash and toolchain.

stage-b-input-pins.json records hashes, versions and URLs for pip 26.2.1, setuptools 84.0.0, wheel 0.45.1, packaging 26.3 and the sgmllib3k sdist. These are pinned inputs, not verified CP312 execution. The ledger includes the nine reviewed source members and fixed SOURCE_DATE_EPOCH 1704067200.

Future source execution needs two fresh venvs, full-resolver offline hashed build tools and executor-side proof that networking is disabled. Docker --network none text alone is not proof. Namespace/no-route verification output must be included, or the execution is BLOCKED. Do not assume bwrap works inside Docker.

The two output wheels must be byte-compared and the outcome stated plainly, even if they differ. The CP312 wheel hash is a Stage B output to be reviewed before any application install. It must not be inferred from the 27a wheel or historical d697b1ce wheel. The historical artifact remains unavailable and unused. No application.lock is created here.

## Failure evidence and remaining obligations

A future adapter must retain bounded failure logs, stop reasons, stage identities and timeout/kill/reap evidence under its own reviewed contract. This package implements none of those execution features. 29b owns a workflow wrapper with always(); the existing workflow's upload-on-failure gap remains unchanged.

OPEN: no application source copy, no 209 helper or goldens, Gunicorn 22 vs 23, bcrypt 5, extras, native private internals, historical wheel recovery, own CP312 sgmllib anchor, real apt/Docker discovery, 28b actual fixes and pin review, and 29b ready lock/application source/failure-evidence wrapper. No Render, ABI, 512 MB or runtime-ready claim.

Local checks cover shell syntax, 14 unit/fixture/negative tests and two byte-identical default semantic receipts. There is no image, venv or environment-wide reproducibility claim. The 29a receipt remains 82d2cd9d432ebca4851ef53957b32a5ae1bc751cc2022284cb09a16cb82d0d94 because its read paths are unchanged.

Commands for local preparation only:

    python3 runtime_executor27c/prepare.py
    python3 runtime_executor27c/prepare.py --stage A --gate on --source /path/to/baseline
    python3 runtime_executor27c/test_prepare.py /path/to/baseline

<!-- END-ORIGINAL-DOC -->


<a id="doc-232"></a>

### Reference: `updater_runtime/COMTRADE-PUBLICATION.md`

<!-- ORIGINAL-DOC {"bytes":1963,"path":"updater_runtime/COMTRADE-PUBLICATION.md","sha256":"fae945e5510f3911b5ac7f28f0f00ae60abbebebda410dcba0cc49400c924638"} -->
# Comtrade178 publication fence

RENDER_DRY=1 returns before reads, key, network, checkpoints or output writes for
all four Comtrade bakes. This intentionally no longer tests live providers in dry
mode. No provider calls are made by source tests. Runtime key selection unchanged.

Market/marketx complete relative to the returned nongroup reporter reference;
partners complete relative to source trade-value codes; mirror complete relative
to its fixed23-country scope. Partial/failure/429 retains last-good baked output
and saves an atomic resumable checkpoint with expected/completed/missing/throttled
coverage. A successful empty API table counts as requested, not proof of healthy
country reporting. Complete relative scope is NOT universal market/source truth.
Failures>=3 no longer permanently exclude a source: retry next invocation with
existing pacing/batch limits, never a tight retry loop. Empty scope and malformed
checkpoint/reference/data fail. API count exceeding rows or100k cap refuses the
table; mirror falls back to chapter chunks and refuses truncated chapter tables.

Old market/partners/mirror state lacking v2 is reset in memory then recollected;
old trend cache lacks v3 and is refreshed. Existing baked last-good files stay
until complete scope is fetched. Outputs replace via same-directory rename, not a
cross-file transaction. Trend data is a separate complete10call/5year table; its
output may update even if partner gathering remains incomplete, never partial
trend publication. State cached only after trend output rename. No externalDB,
Git publication, provider/disclosure or workflow configuration is changed here.

Automate's two Comtrade steps propagate errors/incomplete results before the
build instead of calling every failure a skip. No-key remains an explicit skip.
Other automate steps and build readiness remain separate work. Owner decides
whether to run live bakes. Public read-only Flask pilot does not import bakes.

<!-- END-ORIGINAL-DOC -->


<a id="doc-233"></a>

### Reference: `updater_runtime/GST-GROUNDING.md`

<!-- ORIGINAL-DOC {"bytes":2108,"path":"updater_runtime/GST-GROUNDING.md","sha256":"3302711e30dd93c611faa54ad3d5b9fbc80cb8fcba0f12545d65b18599d9918b"} -->
GST proposal evidence, item21

A proposal is not a rate decision. Match one table row with an explicit 4/6/8-digit code, exactly one rate, and exact description. Two-digit chapter matches,
code substrings, rates on neighboring rows, multiple matching rows/rates and
scope modifiers, exemptions or footnotes are held. Structured evidence carries
line, row, code, rate, description, nearby context, scope and review_required.
Conservative matching can hold legitimate wrapped tables; manual review is the
intended path, not a silent fallback. No claim that nearby context proves the
notification's complete legal effect.

All new proposal files have state=manual_review_required. apply-gst refuses
that state. An operator checks the full official notification, strips evidence
fields to the existing reviewed schema and sets state=operator_reviewed before local
PR preparation. There is no production approval endpoint or automatic rate
commit. Held candidates retain their reason/source in the proposal artifact.

PDF extraction requires declared Poppler pdftotext 22.02.0, checked exactly at
runtime (binary version, not an attested package hash). Missing/drifted tool,
invalid/oversized PDF, extraction error, timeout, empty or oversized text fail
before seen-state updates. Each extraction uses a private temporary directory,
spawn without a shell, and cleanup. Deployment must install/verify this pinned
input separately; these changes install nothing and activate nothing.
Bounded streamed PDF reads cap 10 MiB, output 2 MiB and extraction 20 seconds. Test
fixtures may supply arrayBuffer only; size is checked before extraction.

Pending proposal sources are merged without replacing existing source evidence.
A held-only later run cannot wipe prior changes. Completed/reviewed files must
be archived by the operator before the next proposal batch. PDF failure blocks
the batch and retains seen-state; the updater log identifies the held notice.
Poppler has time/output limits, not an OS memory limit. Deployment must add
process isolation/memory limits before treating hostile PDFs as production-safe.

<!-- END-ORIGINAL-DOC -->


<a id="doc-234"></a>

### Reference: `updater_runtime/MONITOR-HEALTH.md`

<!-- ORIGINAL-DOC {"bytes":1720,"path":"updater_runtime/MONITOR-HEALTH.md","sha256":"b91ca8d2d344f43e27ef4e292b6aec21d56d25a5cba174a6c4c155625152fd45"} -->
Monitor issue health, item22

List requests check HTTP status and validate every page. Up to 100 pages of
100 open issues are searched before creating. Malformed/truncated/pagination
cap and transport errors fail closed. PRs do not satisfy duplicate issue checks.
Creation requires HTTP201 and valid number/title/URL acknowledgement. 5xx or
transport/bad acknowledgement is uncertain, not a success or blind resend.
Each retry lists first; this prevents duplicate creation when a previous lost
acknowledgement actually created a visible open issue. Concurrent creators or
GitHub list visibility lag remain possible races; this is not exactly-once.

Per-source pending_issues is keyed by title and persists independently of the
source signature, which may already have advanced. Failed, uncertain and
disabled requests keep pending; created/existing clears only that title. Retry
runs before the next source signature check, including when source is offline.
Invalid issue configuration is failed issue health, not a source exception.
No token means disabled and pending remains until configuration is supplied.

Sanctions escalation now retries every attempt at or after seven failures,
instead of only the seventh. Each retry checks all open pages first. If an old
issue is closed, another issue may be created on a later attempt; persistent
listing failure reports failed and creates nothing. These are attempts, not
verified daily cadence. monitor/automate log structured issue health.

No issue was sent and no monitor/trigger was installed during these tests.
The source interface does not authorize communication; activation and issue
sends still need user scope. Tests use private temporary state and fake calls.

<!-- END-ORIGINAL-DOC -->


<a id="doc-235"></a>

### Reference: `updater_runtime/REFRESH-BUNDLE.md`

<!-- ORIGINAL-DOC {"bytes":2095,"path":"updater_runtime/REFRESH-BUNDLE.md","sha256":"47c4cb916dabcafe8aa24d4a9a1a56c5eec7ec83a4f22849d45048c6139f9485"} -->
Item17 source/runtime fix149. No execution or deployment in this change.
Source changes are prepared in memory. DRY does not write source chunks/maps,
generated files, temporary build files or Git; configured Comtrade and Gemini
calls can still happen when an operator later runs it with keys. DRY is not an
offline switch. Tests replace fetch and never use keys or network.
Non-DRY builds in a disposable snapshot. Source checkout remains unchanged even
if build/Git fails. Missing Git identity config prepares only, not local rebuild.
With configured Git, clean tracked checkout HEAD must equal captured remote HEAD
before reads and again before publish. One tree contains source edits,index,
offline,SW and one exact SHA256-named datafile. Only old root data.<12hex>.js
paths from the complete prior remote tree may be deleted. No other delete path.
Non-force ref update uses a commit parented on captured base. Concurrent sibling
branch move rejects rather than overwriting. Commit/ref failure is not retried;
uncertain ref response needs manual readback/reconciliation. Local snapshot can
remain stale after successful publication; next run holds until checkout matches.
Root Finder assets remain root Finder assets. Integration Geo HOME is untouched.
Actual regenerated dataset history/source matching is item18, not proven here.
No preservation hash exception, activation, provider key or trigger changes.

Operator recovery: after publication re-pull or redeploy the committed remote
HEAD into a clean Git checkout before the next publication run. Stale/dirty
checkout is intentionally held, not rebased automatically. Missing .git/HEAD
fails at preflight with a fixed explanatory message before provider requests.
A failed/timed-out PATCH may already have landed; inspect remote HEAD and the
created commit before doing anything else. No automatic resend/retry.
Static build.mjs inspection: input reads are exclusively src/ files and
vendor/pako-inflate.min.js; it reads no root templates/package/config. The
disposable copy list src/,vendor/,build.mjs covers that exact build surface.

<!-- END-ORIGINAL-DOC -->


<a id="doc-236"></a>

### Reference: `updater_runtime/SANCTIONS-POLICY.md`

<!-- ORIGINAL-DOC {"bytes":2259,"path":"updater_runtime/SANCTIONS-POLICY.md","sha256":"3a4db077b4cb3f2be56f1351986f9f8015d830fc089d8e014be1edf9a26c3f42"} -->
Sanctions refresh policy

The inclusive count envelope is 85% to 115%, calculated with integers. Empty
base bootstrap and valid outliers are held, not discarded. They are written to
state/sanctions-review.json with exact ordered rows and a SHA-256 over list+rows.
Candidates survive fetch failures. Changed candidates retain earlier unresolved
hashes in candidate_history. Applying a reviewed hash removes only that exact
hash; other pending candidates remain. An operator can review these rows and
supply reviewedHashes for the exact
candidate. A different fetch cannot inherit the approval. A zero-row or
malformed candidate cannot be approved. This source interface grants no
permission to perform a real refresh or to approve a sanctions dataset.

Old list rows and their success labels stay on refusal. Each automatic list
has health state, last_attempt, last_success (null if unknown), stale and
manual_review in SANCTIONS_META. The automate log reports this structured
state; the escalation counter measures attempts, not days. Global checked
advances only when both OFAC and EU refresh successfully. UFLPA is untouched.
Candidate rows are stored only for local operator review, not automatically
published or committed by this module. Writes use sibling temporary files and
rename; dataset and review file are not one atomic transaction.

No actual sanctions feed, dataset refresh, build or deployment was run to
validate this change. Tests use temporary files and supplied synthetic bodies.
Existing baked Finder UI is not rebuilt by this source change. New health is
visible to the updater/operator, not yet a rendered user-facing stale banner.

Intended design: there is no production approval endpoint or CLI. An operator
hand-edits the reviewedHashes argument after inspecting exact candidate rows.
A stale reviewed hash blocks even an in-range update for that list. This is
conservative by design. Health and last_attempt changes mean the sanctions
source file may differ daily even when old rows are retained.

The dependency audit hash covers canonical import-inventory source_baseline
files (path and SHA-256), not the whole preservation or staging manifest. The
new root test file is in those scopes, so its addition changes the audit hash.

<!-- END-ORIGINAL-DOC -->


<a id="doc-237"></a>

### Reference: `updater_runtime/TABLE-EDIT.md`

<!-- ORIGINAL-DOC {"bytes":1307,"path":"updater_runtime/TABLE-EDIT.md","sha256":"da4074ee5f0e54e41446df5b14ace984ee8f5b7564bfd718a53303bc959fe537"} -->
Item20 pure source edit guard, not tax grounding approval.
GST replacement uses a function, preserving $ forms literally. $1 was already
literal in the original noncapture regex; $&/$backtick/$apostrophe were not.
Exact single declarations/final terminators; loose same-code row count refuses
nonstandard indentation instead of inserting a duplicate. Insert adds missing
last-row comma. Closed change schema accepts 2/4/6/8-digit codes, finite rate
syntax <=100%, nonempty bounded/control-free descriptions and known source URL.
Proposer emits only code/rate/description/source through that same validator;
invalid row shape is counted as rejected and skipped, allowing other rows to
continue. The rejected count is included in the job result. Strict applyGst
validation still refuses a malformed stored proposal before output writes. Grounding
errors/2digit scope are still item21, not settled by syntactic validity.
Alias filter and helper share exact ^[a-z][a-z0-9 -]{1,38}$ and word-set bounds.
Failed edit validation writes nothing; counts follow verified pure result, not
an attempted replacement. Scripts are not run live here. apply-gst is local
PR preparation only; merging rates still requires review. Actual write/disk
failure is reported by the filesystem; multi-file durability is not claimed.

<!-- END-ORIGINAL-DOC -->


<a id="doc-238"></a>

### Reference: `workflow_executor29b/SPEC.md`

<!-- ORIGINAL-DOC {"bytes":13371,"path":"workflow_executor29b/SPEC.md","sha256":"0a3886086d64674cc23947e3f8f52c4beb1aed31f5123692886c894ae4491749"} -->
# 29b1 hosted manual Stage A discovery adapter

Hosted execution NOT RUN. Items 27/28/29 OPEN. This additive package prepares Stage A plan acquisition only. No package install, postinst, pip, source build, application execution, image push, Render mutation, DB/mail or cutover. Existing workflows and 27c stubs remain unchanged. The new workflow is NOT in this LAND tree. Its final bytes are reviewed separately only after this adapter commit lands, then the owner pastes and commits it in GitHub UI. Post-check must verify exactly one added workflow file and its reviewed hash. No atomic combined-commit claim.

`workflow.template.yml` is a NON-dispatchable template outside .github. It has placeholders, not predicted commit pins. The final workflow uses the landed full commit SHA, adapter and manifest content hashes before importing code. Gate OFF does not check out code or invoke Docker/network; it writes a NOT RUN receipt and publishes that tiny artifact. Technical gates never establish owner approval. The owner must review final workflow bytes and explicitly approve the particular run. Stage A install and Stage B paths are absent and refused.

The adapter has one subprocess entry and five fixed Docker commands: info, digest pull, run, fixed-name rm --force --volumes, fixed-name container inspect. No input string reaches argv. Local tests use a private fixed-fixture command seam, never exposed in env or CLI. The container name is reviewed-stage-a-29b1. Absence requires a nonzero inspect result with the exact Docker No such container diagnostic for that name and no timeout. Other errors and a surviving container fail the claim.

Online Stage A uses the reviewed Ubuntu amd64 digest, apt 2.8.3, snapshot 20261009T000000Z and exact signed InRelease hashes. The supplied keyring is hash-pinned but not independently authenticated. The bootstrap CA is the reviewed deb extracted without postinst and its 121 sorted Mozilla PEMs, not the normal system bundle or blacklist-equivalent trust. Metadata acquisition uses fixed reviewed URLs. Docker bridge is NOT domain-enforced egress isolation: redirects/registry behavior and pull rate limits remain unreviewed failure modes. TLS verification is not disabled. No Stage B offline-isolation claim.

Actual base installed identities must match 92 packages. Strict simulation parsing checks architecture and the entire proposed 146-package set, including 54 changes, against the existing anchor. Zero-byte, malformed, oversize, added, removed, changed or downgraded identities STOP. MATCH permits no installation and requires independent real-plan review. Historical local apt 2.4.14 output is only a parser fixture, never hosted evidence. Pocket dates are retained and not treated as one shared publication date.

Outputs are bounded public package/tool versions, pocket dates and stop reasons only. Raw runner env, Docker config, credentials and repository secrets are never retained. Per-process output cap 1MiB; public artifact cap 4MiB; retention one day. Oversize capture retains its bounded prefix and records truncation, never silently deletes the log. Process timeout sends TERM then KILL to its own group, waits leader and adopted descendants, checks group absence; named Docker-container removal is separately inspected. Local harmless-child tests prove the fixture mechanics only. always() cleanup/upload are semantic checks locally, not proof on a hosted runner. Cancellation, host loss and failed artifact publication can still prevent evidence delivery.

The existing 29a source pins do not cover this package and remain historical unchanged. This unit does not close application.lock, own CP312 sgml wheel, application/209 source closure, profile conflicts, pikepdf/TZ/512MB, serving or activation gates.

## Reviewed functional caveats

The container drops ALL capabilities and mounts tmpfs over /etc/apt. Apt's sandbox user drop may fail without CAP_SETUID/SETGID. A first hosted run can therefore be BLOCKED for environment reasons; that is not accepted package-plan evidence. Only stdout is parsed. Apt stderr warnings are not retained in public artifacts. These are reviewed functional gaps, not claimed target success. No capability expansion or stderr-capture behavior is added in this preparation unit.

The new template uses exact upstream checkout v4.2.2 (11bd71901bbe5b1630ceea73d27597364c9af683), deliberately different from existing workflow checkout 11d5960a... (floating v4). Release identity is verified, not full action-code security.

## 29b2 source revision: diagnostic and public input permissions

The observed prior hosted receipt was BLOCKED: Docker probe and pull exit 0, container exit 2, empty plan prefix, cleanup inspect-confirmed absent. Its stderr was not retained. The work directory's 0700 mode under a capability-free container is a leading hypothesis, NOT a proven cause. This revision explicitly chmods the public reviewed work directory to 0755 and every file to 0644 after creation, including under umask 077. The bind remains read-only. Capabilities, apt sandbox user, image, snapshot and package policy are unchanged. A later apt sandbox drop failure still needs its own contract.

STAGE start is the first script command. No marker can appear if the shell cannot open the script. Other exact whitelisted markers report that the preceding step completed, except plan-begin which reports imminent simulation. Their order never establishes plan success; the full existing 146-pair parser remains required. Unknown marker text is dropped.

The receipt retains a tail of the already bounded captured stderr on failed, timed-out, killed and successful container outcomes. It strips controls, suppresses env-looking assignments, Authorization/token/key/password lines and URLs with userinfo, then applies a 20-line/4096-byte tail cap. Counts record suppressed/truncated lines, byte truncation, upstream output-cap truncation and whether captured stderr was empty. The tail is untrusted diagnostics only; it never controls state or gates. Capture itself is a bounded prefix, so an upstream output-cap stop can exclude later stderr. Diagnostics cannot prove the root cause without another separately approved hosted run.

The old owner-committed workflow continues to pin the old adapter commit. New final workflow bytes must pin the actual new landed commit, new manifest and adapter hashes, receive separate review, then be committed by the owner and post-checked. No workflow edit is part of this source LAND and no run is performed by this unit. Receipt scope remains verbatim "29b1 Stage A discovery only; items 27/28/29 OPEN".

## 29b3 source revision: missing apt config directory and sandbox-user setting

The second hosted run reached start/inputs-ok/dpkg-ok/ca-ok, and all 92 BASE package identities matched the anchor. Its captured diagnostic was "cannot create /etc/apt/apt.conf.d/99reviewed: Directory nonexistent". The tmpfs hides the image's apt.conf.d. This revision creates only /etc/apt/apt.conf.d immediately before writing 99reviewed. conf-ok prints after that write and before apt-get update. It remains diagnostic data, not plan evidence.

The config retains the previous three lines and adds APT::Sandbox::User "root";. This deliberate sandbox weakening disables only apt download-method privilege drop inside this container. The container still has no-new-privileges, --cap-drop ALL, a pids limit and read-only root. No capabilities are added. Signature checks, Signed-By supplied keyring, exact check_release hashes and the snapshot URL remain unchanged. This is plan-only; installation and Stage B remain REFUSED. An "unsandboxed" style apt stderr warning is diagnostic only, not failure by itself.

This combines the two reviewed changes in one source cycle, not two speculative environment edits. Remaining unverified risks: dpkg lock-frontend/read-only root at plan-begin, snapshot.ubuntu.com/apt/network failure, and conservative stderr suppression of package=version or NO_PUBKEY lines. A later failure needs a separate 29b4 contract. Revised hosted execution is NOT RUN, items 27/28/29 OPEN. Receipt scope remains verbatim "29b1 Stage A discovery only; items 27/28/29 OPEN". New workflow bytes need the new actual landed commit plus discover, adapter and manifest hashes and separate review.

## 29b4 source revision: anonymous apt cache and failure disk diagnostic

The third hosted receipt was BLOCKED with exit 100 after conf-ok, before apt-update-ok. Captured stderr reported "No space left on device" and "IO Error saving source cache". It contained 92 BASE rows and no POCKET rows. This points to apt's 8MiB /var/cache/apt file-cache allocation, but no df measurement was retained in that run. No successful snapshot/Release hash check or plan acquisition follows from it.

99reviewed now has exactly the previous four lines plus Dir::Cache::pkgcache ""; and Dir::Cache::srcpkgcache "";. Apt builds caches in anonymous memory instead of these cache files. OOM under the 768MiB container limit is unmeasured. All mounts are unchanged: the 8MiB cache tmpfs stays, no longer needed for pkgcache/srcpkgcache files. No tmpfs was enlarged and adapter.py is unchanged.

The actual apt-get update failure group captures rc first, emits df -P for only /var/lib/apt/lists /var/cache/apt /tmp to stderr, then exits the original rc. apt-update-ok prints only on success. Command-shim tests execute those actual contiguous script lines and prove failure rc 100, stderr df and no success marker, plus success rc 0 with no df. If apt lists is the full mount next, df should show it; that needs separate 29b5 review.

Remaining unverified: dpkg lock/read-only root at plan-begin, snapshot reachability and exact Release hashes not reached, anonymous-memory OOM, and conservative diagnostic redaction. Revised hosted execution NOT RUN; items 27/28/29 OPEN. Installation and Stage B stay REFUSED. Next separate workflow package changes only commit, manifest and discover hashes; adapter pin remains unchanged.

## 29c anchor revision: actual apt 2.8.3 plan identity

Run 38029882882 supplied a real 92-base/55-Inst plan. The old anchor differed only at libssl3t64: the target solver upgrades 3.0.13-0ubuntu3.15 to 3.0.13-0ubuntu3.16 to match openssl, while the local apt 2.4.14 simulation had 54 changes. The 146-name post-set stays fixed. The real plan is stored byte-for-byte as a test fixture; a parser MATCH of that fixture is not a new hosted run or installation proof.

The new libssl identity, filename, architecture, size and SHA match both noble-updates and noble-security signed Packages entries. Our cached xz indexes were checked against the exact pinned InRelease hashes and their SHA256 lines, signatures checked with the supplied hash-pinned keyring, and fresh gz bytes checked against the same InRelease lines. The result matches the reviewer's independent check. Keyring trust tier is unchanged: signature-valid with a supplied keyring, not independently authenticated. The deb bytes were not verified in this check. Source URLs and complete hash evidence are in signed-index29c.json.

Only this package identity/provenance row and planned count change in the anchor; other 145 full rows remain byte-identical semantically. JSON/TSV parity is tested for all 146 pairs. Current inputs-manifest/inputs.sha256 and 29b source pins are refreshed. Historical 27b change manifest, 27c allowlist/receipts and 29a allowlist/receipts remain exact bytes and intentionally refuse the changed current sources. They are not current valid proof after 29c.

Expected new red checks, not silently repaired: 27c Tests.test_gateon_still_notexecuted (NOT RUN becomes REFUSED on anchor drift); 29a Negatives.test_baseline_blocked_not_pass (source drift in inputs-manifest); 29a preflight (same drift); 27c source-gated preflight (anchor drift). No .github workflow references those harnesses. Existing manual build-review input hash chain remains self-consistent but application.lock is still absent, so it remains blocked. The 28a runner already failed on the base at source_drift:tests/geospatial/test_map_route.py and fails at the identical point after this revision.

The historical 54-Inst parser fixture bytes are unchanged. Its MATCH assertion is intentionally strengthened to the specific STOP: entire proposed post-set differs from reviewed 146-pair anchor. Synthetic fixtures now model 54 new packages plus one existing upgrade; independent real-plan checks hard-code libssl .15 base and .16 target and refuse .15, extra/missing Inst, Remv and wrong architecture. No test is removed, skipped or loosened.

Next separately reviewed owner run may produce MATCH, meaning first accepted real Stage A package-plan identity only. Installation and Stage B stay REFUSED. No CP312 execution, runtime readiness or application.lock follows. Items 27/28/29 remain OPEN. New workflow requires actual landed commit, adapter and manifest hashes; discover.sh is unchanged.

Clarification: base_versions_not_in_pinned_indexes still describes the original base .15 identity, not the revised .16 planned row. The base layer remains .15; the planned upgrade has signed-index provenance. The real run-5 fixture SHA256 is 044b11c478c588cbc85c6966fadb31a1d6e5c33a4710b08bcf50894e86d27db6. The earlier handoff's 95dd53c4 filename prefix was not a content hash.

<!-- END-ORIGINAL-DOC -->


<a id="doc-239"></a>

### Reference: `workflow_package29/SPEC.md`

<!-- ORIGINAL-DOC {"bytes":4744,"path":"workflow_package29/SPEC.md","sha256":"fbb3a4c4e4f2ba37a0c501540e57dd280451f685a9fd1fd2df236fda9c6f1f6b"} -->
# 29a local preflight and package inventory

local workflow preflight/package inventory; Docker NOT RUN; item 29 OPEN

Inert additionsonlyworkflow_package29/. No workflow/root/runtime_build/portable_validation28 edits, no newpins, noapplication.lockcreation. Baselinef836bf1267c84274d05074f8a0c038bcc15261fa. CancloseONLYlocalpreflight/inventorysubunit, notitem29buildready. NoDockerpull/build/dispatch/network/client/server/DB/mail.

preflight independentlyreimplementsworkflowinputchecks, neverexec/evalembeddedPython. Exactwholeworkflowhash+embeddedheredocblockhash detecttrigger/permissions/steps/order/repositoryguard/arg drift. Tightregexanchorssupplementhashes forbuildARGs/expectedversionstrings, aptsourcehash,COPYcontextreferences. Everyreadexistingfileinhashallowlist(54runtime_build+workflow). Input52filesmatchanchors/perfile64MiB/total256MiBbound; inputs-manifest+anchor themselvesexcludedexactlyperworkflow. Missingapplication.lock REQUIRED ->BLOCKED reasonexact. application.pending.lockneverpromoted, old27asgmlhash/placeholderrejected. Incompletelocknotreadinesspass.

## Observed workflow, not endorsed or dispatched

workflow_dispatchonly; contents:read; concurrencygroup runtime-build-review/cancel-in-progress:false; repositoryguarddummypush1-ui/geo-intel-brief; hostubuntu24.04;45minjob;30minDockerbuildtimeout;4MiBlogcap; Dockerlinux/amd64 --pull --network default;1dayartifactretention. Checkout/uploadactionSHAs recordedobservednotendorsed. Uploadstep hasNOalways(): failedbuildstep normallyskipsevidenceupload. Receiptcontainsexactlinefinding. No workflowfixhere,29bfailure-evidenceeditneedsseparatecontract.

## Live-byte inventory and gaps

COPY inputs /reviewed-inputs plusnetwork-launcher.conly. File/commandreferencesDockerfile/shell/fetchPython extracted fromanchoredbytes; generatedCA.pem/plan/dpkgfiles separatedfromsuppliedinputs. Readyapplication.lockabsent. Application source NOTcopied; integration/html_text209.py/goldens NOT inimage. Existing27aCP310selected-sourceproof isnotCP312imageappsourceclosure. BuildfetchPythonusesfiles.pythonhosted.org; aptsnapshot.ubuntu.com; thereforebuildNOTOFFLINE despiteofflinepipinstallstage. Theseareobservedmechanicsnotpermission orclosure.

52inputfiles actualbytes/maxcomputedfromdisk,119downloaddebledger/146postidentityledger. Two small binaries: suppliedhash-pinnedkeyring7399bytes+hash-pinnedCAbootstrapdeb139430bytes; CAdeb is authorizednamedbinaryexception, no otherbinaryartifactaddedby29a.

## States and receipts

manifest_integrityPASS(onlybyte/preflightcheck), required_input_closureBLOCKED(application.lockabsent), targetapplicationartifactclosureBLOCKED, DockercapabilityNOTRUN(no probe), targetbuild/importNOTRUN, dispatchpermissionBLOCKED/HELD. No buildreadinessPASS. Summary "preflight: 1 blocked input, build not attempted" namesrequiredinputcount, otherblockedstatescountedseparately. Two freshlocalinvocationssemanticreceiptsbyteidentical, no timestamps/hostpaths/PIDs. Noenvironmentwideimage/venvreproducibilityclaim. Alloutputsscope-labelled, testslogscopeheader.

12negative/unitprobes: baselineblocked, oldsgmlhash, placeholder, workflowif/permissions, Dockerrefusalgateremoved, missing/extra/symlinkinput, tamperedanchor/cyclicmanifest, argdrift. Hashdrift refusalvalidindependentlyofsemanticchecks. Noharnesssubprocess/socket/urllib/git/gh/docker/networkcalls. Filesystemreadsonly, stdoutreceipt; testswritescratchmutatedcopiesonly.

27bcompletiondependsownCP312sgml2builds+reviewedoutputanchor/external3.12executor andrealnobleapt/Dockerdiscovery. 28bactualtestfixesseparatecontract+pinreview.29b readyapplicationlock/appsourcepackage/workflowfailure-evidenceedit separatecontract afterexecutorplan. ExistingprofileconflictsGunicorn22vs23,bcrypt5,extras/nativeprivateinternals/historicalwheel remainOPEN. NoRender/ABI/512MB/runtime-readyclaim. Mainholdsseparateper-taskownerdispatchapproval; filecreationnotauthorization.

Run:

    python3 workflow_package29/preflight.py /path/to/exact-baseline
    python3 workflow_package29/test_preflight.py /path/to/exact-baseline

RefusalprintsFAILwithreason/scope andnonzeroexit. KnownmissingreadylockreportedBLOCKED/exit0forpreflightreport, notworkflowbuildsuccess. Existingworkflowwouldfailrequiredcheck. Root2175/closure/JSgatehistoryunchanged, notrerun/overlayproof.

The current application.lock refusal is temporary: 29b must REPLACE it with newly reviewed lock/output anchors and source allowlist when the real lock arrives. Missing always() is recorded from the anchored workflow, not detected by a general semantic YAML parser; a future workflow fix requires re-reviewed workflow/block anchors. This allowlist is exact landed f836bf12/tree04926cec, not general acceptance of other trees.

<!-- END-ORIGINAL-DOC -->


---

## Collector Actions: current dormant-source status and owner steps

This source is dormant. Do not install or run the workflow yet. CP312 identity,
sgmllib build and the complete target dependency closure remain UNVERIFIED.
The workflow still needs the immutable landed SHA substituted and reviewed.

Current steps, superseding every older instruction in the history below:

1. Independent reviewer accepts the final source and manifests; builder lands
   dormant source through the reviewed token flow. No workflow is installed by
   that source landing. Replace the workflow's placeholder with that immutable
   landed commit. Verify exact HEAD and a clean checkout before running.
2. Owner creates GitHub Environment `collector-owner-approved`, configures a
   required reviewer (prevent self-review where supported), and stores
   `GEO_WRITER_MONGODB_URI` ONLY as an Environment secret. Do not create a
   repository-level writer secret. Review the matching profile fingerprint,
   Atlas least-privilege roles, collection/index/TTL/ledger setup and network
   allowlist. This launcher does not provision or repair the database.
3. Before workflow installation, finish the exact CP312 interpreter selection
   and hash-locked target install/build verification. The attached lock is a
   candidate, not proof of target execution.
4. Owner pastes the final reviewed manual-first workflow via GitHub UI. The
   owner separately approves measurement's named scope: actual approved public
   RSS fetches plus Atlas READ-ONLY privilege/index/ledger preflight using the
   writer URI. Measurement DOES consume the Environment secret for these reads,
   but does not claim jobs or write articles. Required Environment review applies.
5. The qualification producer IS implemented in the current source. It derives
   same-run cgroup peak/events and aggregate-adversary output, binds source and
   package bytes, and passes a root-owned read-only qualification descriptor.
   Its result means qualified for fixture/limit, NOT proven real write memory.
6. After target qualification review and owner approval for collection's exact
   writer destination/scope, run one manual `collect` job with the Environment
   approval click. Real write memory is first observed in that real run. Reruns
   and `status` read durable state only, without RSS or writes. Active/uncertain
   jobs hold later claims; no automatic lease steal, clear or blind retry.
7. Review terminal job, actual peak/events, duplicate outcomes and source coverage
   before offering a schedule. The current template has NO schedule. Owner
   chooses cadence only after this review; history64 requires a separate
   reviewed retention plan. Render remains read-only with collector OFF.

Budget: both measure and collect use an80s installation deadline. Coordinator
fetch reserves15s; supervisor feed cutoff reserves20s. Soft stop at82s attempts
held-state recording, outer90s TERM plus2s KILL is last resort. Forced kill or
DB failure can leave active state requiring separate reconciliation.

The following blocks preserve the earlier drafts exactly as historical records.
They are NOT current install/run instructions. In particular, their claims of
no Atlas secret, repository secret, absent producer or measure-only launcher are
superseded by the current steps above. No workflow reference string by itself
creates owner approval. Original authenticated owner scope and the reviewed
Environment policy remain required before any external run.

### HISTORICAL / SUPERSEDED: owner-step drafts v1 through v4

# Free collector route: manual-first candidate

This is source prepared for independent review, not permission to run collection.
No collector DB writes, pushes or workflow installs have been made.

1. Reviewer checks the source and tests. Builder lands reviewed non-workflow code
   with current source/import/staging manifests refreshed. Owner handles helper
   token through the usual secure route. No token in conversation or source.
2. Reviewer supplies exact landed source SHA and a hash-locked CP312 dependency
   closure. The workflow candidate currently has REVIEWED_SOURCE_COMMIT_REQUIRED
   and un-hashed additive pip installation; replace before final owner workflow.
   A file with that placeholder is NOT a ready execution workflow.
3. Owner opens repo > Add file > Create new file, name
   .github/workflows/collector-actions-qualification.yml; pastes final reviewed
   workflow and commits to main. Then Actions > Collector Actions qualification
   candidate > Run workflow. This manual diagnostic uses no Atlas secret and
   does not create triggers or write articles. Review actual bwrap/cgroup/OOM
   evidence and real workload peak/coverage/deadlines. Failure remains held.
4. Complete independent qualification producer: maximum supported input,
   checkpoint/prepare, source drift, privilege drop, all descendant cleanup,
   memory/OOM/headroom and Mongo serialization/pool overhead must be accounted
   for. Current launch.sh only permits measurement; collect/status are held.
5. Review Atlas dedicated writer privileges, indexes, TTL, preinitialized ledger
   fingerprint and checkpoint stores. No provisioning in this launcher. Owner
   enters GEO_WRITER_MONGODB_URI under Settings > Secrets and variables > Actions
   > New repository secret, not in chat. Current measurement never consumes it.
   Host allowlisting requires review, no automatic broad Atlas access change.
6. After final producer/workflow review and owner approval: manual one-shot
   collection. Deterministic repo/run_id nonce is recorded by Atlas CAS ledger
   before fetch; same run_id rerun only reads status, never reclaims/reexecutes.
   Any active or uncertain job blocks all later new claims. Read status and
   reconcile independently before repair, no lease-steal or blind retry.
7. After actual terminal receipt and duplicate/coverage checks, owner enables
   reviewed schedule on main, with chosen cadence and off-minute cron.
   Schedules may be delayed/dropped; after 60 days inactivity public schedules
   can stop. Durable ledger history has 64 terminal-job limit. Rotation/archival
   is separate reviewed work, not deleting evidence automatically.

The accepted scheduler217 v4 is mail weekly/critical scheduler, not this
collector route. Render web remains read-only, COLLECTION_ENABLED absent/false.
No paid Render instance is part of this route. GitHub public standard Ubuntu
runner currently lists 4CPU/16GB and free unlimited standard jobs, subject to
Actions policy. Actual capability is probed rather than inferred from the label.

Source docs:
https://docs.github.com/en/actions/reference/runners/github-hosted-runners
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

V2: rootproducer derives same-run measuredcgroup peak/events + actualadversarylog, opensread-onlyFD3inroot0700dir; no receiptpathfrompayload. Rootsnippets use/usr/bin/python3 -I -S, no venv interpreterasroot. Fullsource+installedbytesmanifest andfreshcheckbeforeclaim bound90swindow. Maximum1000checkpoint/prepare/GeoWriterBSONfixture + realAtlasreadonlypreflight+RSS measurement implemented, source-onlyunexecutedonActions. HashedCP312artifactcandidate attached;sgmllibsdistbuild/closure notyetproven. Workflowstillrequiresfinalreviewedcommit. Ownerinputreferenceisnotauthoritybyitself: mainmustrecoveroriginalscopebeforeanynetwork/DBrun.

V3 installation prerequisites: create GitHub Environment collector-owner-approved,
set REQUIRED REVIEWER and prevent self-review if available; place writer secret
ONLY there. Never repository-level writer secret. Both measure and collect jobs
require approval click because measurement uses same secret for Atlas read-only
preflight plus actual approved public RSS network; owner approves this exact scope.
Workflow hardpins landed SHA and checks HEAD equals it + clean checkout. Placeholder
cannot be replaced until builder lands dormant reviewed source. No schedule yet.
Budget:80s cycle total including startup; supervisor cuts fetch20s before cycle
end, reservingprepare/write/reconcile;82s soft alarm/TERMrecordsheld state where
possible;90s outerTERM+2sKILLfallback. Forcedkill/DBoutage may leaveactivejob;
allnewclaimshelduntilseparatelyreviewedreconciliation. History64stillfinite.
Receipt means qualified for fixture/limit, not proven actualwritepeak. Realcollect
reports actualmemory.peak/events; no claimbeforeobservingthatrealrun.

Final dormant-source addendum: MEASURE shares80sstart deadline; coordinator reserves15s (deadline-15), supervisor feed cutoffdeadline-20. Priorwording20sreservewascoordinator-inaccurate. Write hasnoindependentforced20stimer; remainingcyclebudget+driver8stimeoutmustbeobserved. Post-writeoverrunremainsuncertain_after_writebyexistingconservativeorchestratorpolicy, notdowngradedjustbecausereceiptarrivedafterdeadline. SIGTERM/softalarmbest-effortterminalrecordcanfail; heldactiveisintentionalratherthanblindretry. 86testsPASS(1historicalartifactcacheunverifiedskip).


### HISTORICAL / SUPERSEDED: review-checklist drafts v1 through v4

# Review candidate v1, source only

Implemented: fixed nonroot runner guard, hard95s deadline/2s kill fallback,
3GiB cgroup/swap0/oomgroup, caps cleared/no-new-privileges, parent512MiB AS before
imports, input size/schema checks, no secrets argv/logs, exact protected receipt
binding source/run/reference/age and measured headroom/clean OOM events,
JobRuntimeEvidence from actual runtime probes, deterministic run_id nonce,
rerun/read status hold, active/uncertain/history64 hold, no initializer/repair.
Existing run_job does CAS claim/checkpoint/write fencing and no automatic replay.

Not complete or approved for ON:
- Qualification producer is intentionally absent. Shell permits measure only.
  Provider cannot accept an env-ready boolean as substitute. Public workflow
  has no Atlas secret access and no collection step. No ready proof fabricated.
- Need root-owned receipt producer with independently verified adverse aggregate
  kill and maximum input/prepare/checkpoint/Mongo accounting. Current measurement
  is real RSS+prepare, no DB; it declares writer_memory_proven=false.
- Need clean CP312 hashed closure/native source-byte compatibility/target probes.
- Need race tests across different runs: read-status gate can race, but existing
  Atlas CAS prevents second claim. A concurrent same-run first-attempt launch
  must not reclaim accepted job; existing CAS advance only one wins, loser stops.
- Need correct static fingerprint of installed profile, owner authority evidence,
  Atlas least-privilege collection/index/TTL/ledger provisioning reviewed.
- Review new receipt path against symlink ancestry races/root-owned protected dir.
  Arbitrary writable scratch receipt must refuse. Module source digest coverage
  should include the entire reviewed application code and exact package lock,
  not only current worker pins and launcher subset.
- No source-metadata mutation in the live clone; manifest landing belongs builder.

Tests28PASS (11new +17existing job runtime tests), BashsyntaxPASS,
version-only dependency CP310 install and source SDK hashesPASS. Not actual
root/cgroup/runner/Atlas execution; real tests await owner manual qualification.

V2 closes first-pass source issues:rootstdlibonly, no payloadreceiptpath, inheritedreadonlyFDrootownership/hashderivedevidence,fullsource/installed-bytebinding,positive/negativeprovider tests31PASS,knownunblocked replayhold included,freshqualificationoncebeforeclaimthen90swindow,90souterdeadline,ledger.profilekeynotliteralgeo108. Qualificationproducer nowimplementedbutnotlivevalidated. Needsmaximumfixture+fetchwithin90s timingreview; fixture/DBserializationnotactualnetworkwritecapacitymeasurement. trustboundaryisreviewedpinnedworkflow/source; malicioussudo stepcanalwaysforgehoststateandisNOTdefendedbyrootreceipt. FullCP312sgmlsourcebuildandpackageclosureexecutionstillrequired.

V3 extends mutanttests:FDreadonly,independentpeakcap/consistency,rawevents/adversarylog,
allcaps/euid/NoNewPrivs,earlystatusunsupported,eachreceiptproducerbranch andpositive.
80scyclehard_deadline optionalAPI retains90sdefaultforexistingcallers; collectentry
passesabsolute80sdeadline, fetchpreserves20sreserve. GracefulSIGTERM/82salarmexception
flow throughorchestratorbest-effortstate recording, but forcedkillisnotrecovery.
Environmentrequired-reviewer+immutablecheckout/cleanchecktemplateimplemented;
landedSHAandownerapprovalexchange pending. Budget/signals requireindependentreview.


## Public Finder reference-rates candidate (not deployed)

This additive candidate is NOT full live AI/weather/ships Finder. Original Finder,
private network preview and public offline source remain unchanged. The public
wrapper embeds the offline trade-code search and adds one manual reference-rate
button. No provider request happens at boot, page render, HEAD or on a timer.

`PUBLIC_FINDER_RATES_ENABLED` defaults to `false`. To enable it, the provider,
abuse and single-worker reviews must each explicitly be `true` through
`PUBLIC_FINDER_PROVIDER_REVIEWED`, `PUBLIC_FINDER_ABUSE_REVIEWED` and
`PUBLIC_FINDER_SINGLE_WORKER_VERIFIED`. These are deployment review assertions,
not permission to spend, share credentials, change live environment or publish.
`FINDER_NETWORK_PREVIEW_ENABLED` must remain `false` in public builders.

The only upstream destination is `https://api.frankfurter.dev/v1/latest`, with
fixed `base`/`symbols` currency parameters. No arbitrary URL, redirects,
environment proxy, credentials, shared key pool or user storage is used. Allowed
currencies: USD, EUR, INR, GBP, JPY, CHF, CAD, AUD, CNY, SGD and HKD. Returned data
is limited to validated pair, positive finite rate, date and source label. This
is daily reference data, not an executable quote or real-time trading price.

Abuse plan: one upstream request at a time, 3-second socket timeout, 16KB input
cap, no automatic retry, max30 upstream attempts/minute and200/day including
failures. A cache holds32 pairs for1hour. Every request, including cache hits,
counts toward60 total requests/minute and10 per socket-peer/minute. Forwarded
identity headers are never trusted. Behind a reverse proxy, visitors may share a
peer limit deliberately. Limits and counters are per process and reset on
restart, so use exactly one worker, reviewed host-level ingress caps, bounded
restart policy, and no auto-scaling before enabling. This is not a global or
restart-proof quota. There is no paid provider rail; overload returns429 or503.

Official provider facts checked October10,2026:
- https://frankfurter.dev/ and https://frankfurter.dev/license/: API permits
  commercial use; rates carry underlying provider terms, can lag/revise and
  have no warranty. No monthly/day caps; upstream abuse limits still apply.
- https://frankfurter.dev/v1/: v1 remains available, though deprecated; uses
  `base` and `symbols`. No live endpoint call was made for this build.
- https://open-meteo.com/en/terms and https://open-meteo.com/en/pricing: free
  weather service is non-commercial only, with600/minute,5000/hour,10000/day
  limits. Commercial product use needs a reviewed licence/plan. Weather stays
  OFF. AI/AIS need a reviewed keyless or separately authorized provider route
  and cost/abuse plan; no owner keys may be exposed. Neither is implemented.

Candidate review must verify origin guards, fixed destination, sanitization,
manual-only UI, same-origin CSP, no storage and all private routes still denied.
Local screenshots validate layout only. Provider reliability and real response
compatibility were not tested against the live service. No deployment or public
exposure is authorized by this source candidate.
