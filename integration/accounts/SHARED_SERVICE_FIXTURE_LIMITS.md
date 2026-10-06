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
