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
