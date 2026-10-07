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
