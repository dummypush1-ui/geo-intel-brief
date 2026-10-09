# 224: native-shaped supplied rows, not a database read

Pure parser to produce the 223 assertion projection. It adds no authenticated
read, historical completeness, current state, delivery or owner authority.
A complete coherent graph can be wholly invented. control.history_complete True
is that row's own claim, not evidence. An omitted whole graph can pass too.
The output flags source_authenticated, history_verified, current_state_verified,
send_allowed, ready, owner_approval and ledger_wired are all False.

OFF does not inspect arguments or import anything. ON takes exact native-shaped
control, receipt and article dictionaries, plus explicit expected recipient
fingerprint and history manifest. Kind is email, purpose digest. Caps checked
before processing: 128 receipts, 10000 articles, each receipt 1..120 sorted unique
lowercase ASCII 24-hex IDs. 128 times 120 is 15360, so a full graph can exceed the
article cap and refuse. No truncation or silent deduplication. No default history.

Reproduces 212 channel/control/article/receipt-binding hash equations with their
closed key sets. Schema and revision are exact ints, not bool; revision from 0
through 2**53-2. Rails, states, attempt, resolution reference and scope follow
212 _receipt rules. Receipt _id is only checked as 64-hex: nonce is not supplied,
so receipt _id == hash(control, nonce) CANNOT be checked. No 212 import,
constructor, driver check, client, file read, DB read/check/write or creation.

State-dependent graph rules preserve normal native history:
- Prepared/started receipts must be the single control.active receipt. Every ID
  must have an article pointing back with equal hash and state.
- Acknowledged receipts require every ID to point back with equal hash and state.
  212 cannot overwrite acknowledged articles.
- Cancelled/operator_resolved_unsent receipts need not have articles pointing
  back. 212 prepare can overwrite released article keys with a newer receipt.
  If an article still points back, hash and state must match. If it points to
  another native-shaped receipt key, that other receipt need not be supplied.
- For every article whose receipt IS supplied: ID membership, hash and state
  must match. Prepared/started articles must have a supplied active receipt.
- Acknowledged articles referencing unsupplied receipts ARE accepted. 212
  exclusions reads article state; requiring every old receipt would hit the
  receipt cap. Article key/schema/channel/purpose/receipt/hash/state still checked,
  but unsupplied receipt contents and binding are NOT verified. Released articles
  with unsupplied receipts also accept and are never exclusions.
- Active None with unresolved receipts/articles refuses. Active set without a
  supplied prepared/started receipt refuses. Duplicate receipt keys, article keys
  or article IDs refuse. Input order does not change sorted output.

Only acknowledged article IDs become projection ObjectId tuple. Cancelled and
operator_resolved_unsent do not exclude. Prepared/started yields active_state for
223 to hold the entire channel and purpose. The output necessarily echoes channel
and ObjectIds as private internal data for 223, not approval to disclose or send.
No raw receipt, attempt, resolution reference, manifest, body, sender or addresses
returned. Fixed error has no upstream message, cause or context. Inputs untouched.
No 224 call to 223, 221, 219 or a real ledger.

No send, wiring, store, environment/property change, deployment, activation,
trigger, cutover, mount or identity selection. Apps Script selected, SMTP fallback
held, 217 held, 201c write held. Sender blocker 222, authenticated native read,
history authority, provenance, durable body, and owner-approved recipients and
words remain open. Shape production is prepared, not an authorized live producer.
