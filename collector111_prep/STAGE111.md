# Collector111 durable-driver integration preparation

INACTIVE scratch; no saved109/110 edits, no live mount/client/index/TTL/network,
DB/mail write, trigger or cutover. New drive_durable composes reviewed109 phase
semantics with reviewed110 capture and injected DurableCheckpoints.

- Full run inputs captured before deepcopy/hash/preparation and before ledger
  heartbeat. Status read remains before capture; rejected budget makes no ledger
  mutation. Driver uses the captured copies throughout, exact adapters only.
- Accepted job writes immutable checkpoint before running. Resume requires full
  matching checkpoint and refuses read/write acknowledgement/integrity failures.
- Local real BSON codec backed collection double retains checkpoints across
  adapter re-instantiation. This is not a real server or process restart proof.
- Existing write_started still never retries, no uncertainty unlock, no lease
  takeover. CAS/heartbeat still cannot atomically fence external article writes.
- All26 earlier109 drive/chain/safety tests plus6 durable integration tests PASS
  (32 total); full old regression and package layout not run yet for this stage.

Configured majority+journal/read concerns do not verify server capability,
role or authority. No production deployment/recovery claim. No source fetch,
stream/decompression/DNS/parser sandbox added. These remain outstanding along
with production service mounting, source flags, run reconciliation and actual
Apps Script trigger/capacity checks. Live production stays OFF.
