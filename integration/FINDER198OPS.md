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
