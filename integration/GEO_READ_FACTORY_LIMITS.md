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
