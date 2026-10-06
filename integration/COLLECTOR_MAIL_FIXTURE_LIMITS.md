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
