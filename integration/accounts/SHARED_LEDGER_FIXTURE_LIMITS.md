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
