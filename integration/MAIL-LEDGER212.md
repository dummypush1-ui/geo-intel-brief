# 212: unselected per-logical-channel exclusion ledger

Source-only adapter, not mail wiring completion. No current sender enforces these
keys. No client is constructed, no route, timer, sender, environment, article
flag, provisioning, index write, migration, retention purge or live effect is
added. Existing feature_mail_mount store/bridge and its 128-receipt cap remain
unchanged. FixtureLedger remains a fixture. Native200/201 engine is untouched.

## Logical identity, history and prerequisites

Proposed mapping: geo_intel/mail_control212, mail_receipts212, mail_articles212.
These are candidate names, not proof of existing collections or owner permission
to create them. Constructor requires explicit enabled=True, exact review fields,
transaction/write/control evidence and an exact history-manifest SHA256 with
history_complete=True. Such supplied flags/hashes are caller assertions, not
independent proof or authority. They never authorize activation. No absent row is
created, no genesis/zero-history assumption or migration is made.

Before real use: recover source-grounded owner authority, preserve-state policy,
actual role/validator/collection/index/transaction diagnostics, history import and
completeness, sender/recipient/scope evidence, and caller authentication. No TTL
index on any ledger collection is allowed; ordinary _id uniqueness is required.
No secondary unique index is needed. Constructor does bounded read-only index
inspection, not provisioning. OFF inspects no client attribute and creates no
handle/session, even when a hostile object is passed; repr has no client fields.

Logical channel is SHA256 of canonical kind + reviewed recipient-set fingerprint.
Transport is NOT in the key. Purpose digest/critical is bound separately in both
control and article key. Changing recipients makes a NEW logical channel and
exclusions are NOT carried over: that is an explicit owner decision, never a
silent recipient edit. Recipient fingerprint is not an address or permission.
The channel helper does not build, normalize or approve recipient sets.

Email digest and critical are supported state scopes. Critical does not suppress
normal digest, preserving the owner's separate-purpose choice. Telegram/WhatsApp
are validated selector names only, no transport is connected. Weekly is refused
and deferred to occurrence-bound scheduling work. No sender, recipient or time
is chosen. Rail is a recorded receipt attribute, never exclusion identity; rail
cannot change on a replayed receipt. A new receipt on another rail still sees
acknowledged article exclusions for the same logical channel/purpose.

Existing emailed/mail_critical_sent flags and this ledger are two distinct sources
of truth. This unit does not reconcile them or mutate them. For the future
selector, ledger keys govern recorded per-channel exclusion; legacy flags cannot
prove per-channel coverage and cannot override a recorded key. Disagreement,
unknown history or missing import must hold activation until a reviewed policy
resolves it. No current sender obeys this precedence yet.

## Transactions and state

All mutations use snapshot read concern, primary reads and majority+journaled
write concern with 5s bound. Each logical channel+purpose has its own provisioned
control: _id derived from canonical channel+purpose, schema1, channel, purpose,
history_manifest, history_complete, revision and active receipt or null. Every
write CAS replaces the exact prior revision, incrementing once. Digest/critical
and different channels do not share a control row. A competing write/duplicate
_id insertion aborts the whole transaction. No application-level body/commit
retry, with_transaction helper or automatic retry/resend exists.

prepare binds nonce-derived receipt, sorted unique exact ObjectIds (1..120),
logical channel, purpose and content/renderer digest. Payload hash covers ONLY
logical channel, purpose, sorted unique IDs and content digest. Input order does
not change it. Stored receipt contains hashes, IDs and state/rail/audit metadata,
never email body or recipient addresses. It is NOT a full HTML archive, email
renderer or independently verified send identity. Content digest must bind the
future caller's separately retained immutable body. This unit cannot establish
that fact. Empty selections refuse without creating a send claim.

Article _id = hash(channel,purpose,ObjectId). New keys, receipt and control CAS
are in the same transaction. Existing prepared/started overlap holds the entire
unit, never silently skips a subset. Acknowledged overlap refuses prepare;
exclusions(candidate_ids) returns acknowledged IDs, for the selector to exclude
BEFORE preparing. It looks up only candidate keys via _id $in, never scans
retained history; unresolved overlap holds, not silently suppressed forever.
Blockage is CHANNEL-WIDE: the active control blocks EVERY later prepare for the
same logical channel+purpose, even disjoint IDs. A crash after start halts that
digest channel until future authenticated operator resolve; a prepared-never-
started hold needs authenticated cancel. Nothing silently releases the hold.
Same nonce/hash/IDs/rail returns stored state; conflicting hash/rail holds.
Released keys are reused only through exact receipt/hash/state CAS, never deleted.

start persists started once and gives permit=True ONLY after confirmed commit AND
readback in a fresh snapshot transaction showing started/same attempt/hash.
Repeated start returns held/permit=False, never a renewed permit. Started means
POSSIBLY SENT. No elapsed time, restart or expiry releases it. Permit is source
protocol state, not user send authority. Caller must check status on held result.

acknowledge exact receipt/hash/attempt atomically transitions all bound article
keys, receipt and control, then fresh readback. It is an authenticated future
bridge assertion: bridge_send_returned_not_delivery, NOT recipient delivery or
independent provider proof. A repeated ack is idempotent and cannot resend.

cancel(receipt/hash) applies ONLY to prepared-never-started. It atomically changes
keys/receipt to cancelled and clears that control; keys are freed by state change,
not delete. Started cancel refuses. resolve(receipt/hash/attempt,confirmed_sent,
authority_reference) applies ONLY to started (or exact idempotent terminal replay).
Confirmed sent becomes acknowledged with operator_asserted_sent_not_delivery;
confirmed unsent becomes operator_resolved_unsent with keys released by state
change. The SHA reference is audit binding, NOT proof of operator identity or
permission. Who may invoke resolve/cancel is the future authenticated owner/
operator workflow, not a public client. This unit grants no such authority and
adds no endpoint. Existing receipt records remain immutable in binding and kept.

Fixed reasons include conflict_started, conflict_prepared, conflict_other_hash,
conflict_sent, conflict, capacity, schema, unknown_commit, unavailable, readback,
missing, history_unverified, invalid, disabled and driver. No private ID, nonce,
hash, body, address or driver error string is echoed in exceptions/held reasons.
Successful internal status includes scoped hashes/IDs for its trusted caller,
not a public disclosure API.

## Driver behavior, limits and uncertainty

Pinned installed PyMongo4.18.2 source is recorded in mail_driver212.json:
synchronous client_session, mongo_client, collection and errors. Enabled
construction/transactions verify those exact bytes/version on EVERY _run.
Activation prerequisite: deployed requirements must resolve to PyMongo4.18.2
exactly, or this pin must be deliberately updated and reviewed. Different driver
version/bytes fail closed even when other configuration is valid. Public
ClientSession.commit_transaction uses _finish_transaction_with_retry and
MongoClient._retry_internal(retryable=True): the DRIVER may retry commit once for
retryable errors. "No retry" here means no APPLICATION retry. Commit sets its
transaction state COMMITTED in finally even on unknown outcomes; end_session does
not abort a possibly committed transaction. Ordinary pre-commit failures abort
and release session. No private/native200 no-retry primitive is used or changed.

OperationFailure code112/TransientTransactionError yields conflict, without
rerunning the body. DuplicateKeyError yields conflict. UnknownTransactionCommitResult
and other commit uncertainty yield unknown_commit. start never grants permission
and ack never reports success on unknown commit or failed readback, even when the
write landed. Caller must status/reconcile; it cannot infer unsent from a failure.
The driver can retry the commit of ONE transaction, never duplicate send effects.
Readback is a fresh snapshot, not proof of actual deployment durability.

All-time means no time expiry of recorded exclusion keys, NOT authenticated
historical coverage, unlimited storage or a backup. Per-transaction IDs are capped
120 (24h+7d union), never a 10k historical scan/tuple limit. Receipt storage remains
subject to DB capacity; failures hold. Schema/index drift after construction
requires future ongoing deployment monitoring, not a claim this code prevents it.
No current HTML archive is replaced or automatically expanded/purged.

## Evidence and test limits

Current main feature_mail_mount/store.py was live-read and matches SHA256
 d425883b8f22a2530dda2e6fe9b28bed7036c88bb1e842748b2b277040f843a8.
Original push2006/geonews reports/email_report.py sendthenmark and scheduler.py
three attempts were live-read (30d7552def0e9d56f8981f25b3d81ed3475bcc354971aea304a30e6f7d583688;
dc42e6147db678d3ad93d62f3412cd521230a040296a405e60d77588b99936a0).
BRICS- reports/email_report.py SMTP+STARTTLS source
6582d81d184e2c18842f1507d7e46042514c9d0cfbfea7e1202ce8bf1218ac65.
They were read, not executed. This adapter does not preserve unsafe retry semantics.

19 offline tests: OFF hostile client, history/no-genesis gates, no TTL, ordered
hashes, overlap hold-whole-unit, no renewed start, ack atomic/idempotent, cancel,
operator resolution, distinct purposes/channels, >10000 retained keys with120
candidate lookup and121 refusal, unknown commit before/after applied write,
unknown ack and status-only recovery, failed readback, actual PyMongo exception
classes/labels, two racing snapshot writers with exactly one winner, restart,
stored corruption, pinned driver semantics/options. Fake snapshots model CAS,
WriteConflict/TransientTransactionError and unknown AFTER durable apply vs BEFORE
apply. They are not real Mongo concurrency/durability proof. No live DB/SMTP/Gmail,
article mutation, operator call, trigger, timer or deploy happened.

Remaining mail wiring: source query/completeness +193/202 selector integration,
email-ready renderer (203 is browser preview ONLY), immutable body archive,
logical-channel history migration, caller authentication, article marker decision,
Apps Script mount/cutover,204 SMTP caller (fallback still held),205 scheduler,
actual DB diagnostics/permission/activation. No mail-complete claim.
