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
