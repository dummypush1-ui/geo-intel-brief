# Geo Intel Brief

Copyright (c) 2026 Push. All rights reserved.

Geo Intel Brief brings geopolitical news, trade-code lookup and BRICS source features into one codebase. The Flask workspace connects stored news with country views, story groups, trade context, exports and report tools. The original Finder, Geo and BRICS code remains in the repository.

**The merge is in progress.** A public read-only news preview is implemented, but collectors, mail, account login and the full Finder provider connection are not mounted into that public launcher. Prepared code and passing local tests do not mean a feature is live.

## Start here

- [Architecture and code map](docs/ARCHITECTURE.md)
- [Configuration guide](docs/CONFIGURATION.md)
- [Sanctions operator policy](updater_runtime/SANCTIONS-POLICY.md) - manual reviewedHashes, no approval endpoint
- [GST grounding](updater_runtime/GST-GROUNDING.md) - operator_reviewed required
- [Monitor health](updater_runtime/MONITOR-HEALTH.md) - pending_issues and uncertain outcomes
- [Folder cleanup proposal](docs/FOLDER-PLAN.md) - a plan, not a file move
- [Feature history and limits](integration/FEATURE_STATUS.md) - historical checkpoints; check the newer module-specific notes too
- [Security notes](SECURITY.md)
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

`requirements-staging.txt` installs the basic Flask/Mongo preview dependencies. It is not the full offline test closure, a hash-locked installation or proof of the deployed environment. Package installation accesses the configured package index. This path pins Gunicorn 22.0.0, as do the frozen locks. The security candidate lock pins Gunicorn 23.0.0 for the reviewed CVE fixes. A deployment should use that candidate only after its install is verified in the intended environment; do not infer deployment safety from this basic preview install.

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

For an empty public preview or private password preview, use the exact mode-specific settings in [Configuration](docs/CONFIGURATION.md). Public modes require a canonical HTTPS origin; changing the origin check to make HTTP work would weaken the boundary.

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

See [the dependency build notes](integration/dependency_build/README.md), [the current PDF profile](integration/pypdf_remediation105/README.md) and [the future deployment contract](integration/security_maintenance94/DEPLOY-CONTRACT.md). Some historical checks need their recorded artifact cache. Missing artifacts are unverified, not passed. Do not treat old test counts in documents as a current full-suite result.

The historical offline candidate lock still records its missing wheel/hash. The newer `integration/security_candidate/requirements-security-candidate.txt` has verified package hashes and a hashed `sgmllib3k` source archive; its install and `pip check` were tested separately. Its legacy source-build bootstrap is not a fully hash-locked build chain. The frozen future-deploy lock remains separate and requires verified wheel artifacts, including a locally built `sgmllib3k` wheel. Neither source tests nor a candidate install prove the deployed environment.

The current source gate is 1469 root cases plus 285 collector cases, 10 checks cases and 26 world cases outside root discovery. The staging manifest `tests` field records only 1469. See [exact gate commands](docs/TEST-GATES.md).

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
