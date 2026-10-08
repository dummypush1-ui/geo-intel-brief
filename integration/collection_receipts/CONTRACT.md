# Item6 protocol145: INERT, not durable implementation
Base e0f6e2b. Core protocol paths integration/collection_receipts/protocol.py and
tests/collection_receipts/test_protocol.py. Nine pure tests plus two integrated inventory/import-surface tests. Originals unchanged.
No transport/storage/import client/send/delete/ref update. No activation.

Required adapter must establish trusted identity, actual durabletransaction and
owner-approved destination. Supplied dict/hash/ID is not authentication proof.
commit_collection atomically articlepreview+fullrecord+outbox, immutable uniqueURL
reconciliation, exact per-record IDs/contenthash/version. No aggregate inference.
Alreadyterminal never resend, alreadypending reads STORED fullrecord, conflict
holds rather than overwrite. Unknown holds; transaction partial state reconciled.

Fenced CAS journal persisted before effects, per-piece durable started/ack state.
Provider receipt independently verifies destination+messageID+attempt+piecehash;
unknown return/crash latchesunknown and never auto-resends. Partial continues ONLY
unstarted pieces, durable confirmed state. Expired startedlease holds unknown.
finalize terminaljournal/outbox/refpublication atomicCAS of currentversion and
immutable destination/fullrecordhash, allpieces acknowledged; refs exact-idempotent
or failclosed. No fullrecordTTL/deletion. Plan chunkJSON reassembles complete record,
UTF16<=3000units, total1MiB; receiver needs journal piece ordering to reassemble.

Python protocol functions operate supplied state, NOT an authorization or forged-
receipt defense. Adapter must validate/reload stored journal, never accept state
from untrusted caller. publishable only gives supplied-state completion, not send,
refpublication or retentionpermission. No concrete transaction schema/driver
adapter provided here. Failclosed mounting requires adapter review first.

Remaining tests adapter-owned: actualCAS leasefencing/replay/rollback, duplicate
collect reconciliation, simultaneouswriters, refs immutability, unknownsend
reconciliation, durable restart, configured transactionavailability, permissions.

Review hardening: unhashable receiptURL/nonfiniteJSON/lonesurrogate now refuse as
ReceiptRefused,9tests pass. Lateack after unknown intentionally refused: adapter
must separately reconcile under authority/fencedstoredstate, no generic retry.
journal_new doesn't authenticate planrecorddigest; adapter reloads/recomputes
fullrecorddigest and orderedpieceplan beforepersisting; hash isn't receiptproof.
