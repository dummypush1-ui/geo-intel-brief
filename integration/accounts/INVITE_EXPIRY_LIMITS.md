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
