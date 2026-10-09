# 197c: durable source coverage and default-OFF production composition

Version-2 checkpoints atomically store original candidates/categories/threshold
and full pinned 25-source status coverage/catalog fingerprint. Typed input hash
is unchanged; coverage has an independent domain-separated typed hash bound to
job and fence. Capture is bounded before copy/hash. Immutable upsert/readback,
BSON roundtrip and adapter re-instantiation retain exact coverage. Version 1 is
unchanged and still separate. Same existing checkpoint collection, no new
collection/index/provisioning. Unknown/partial writes remain locked; replay
reads durable coverage, never fetches/writes. Missing/corrupt coverage refuses.

Production entry mounts only /api/collect and /api/collect/status/ through WSGI
dispatch so the public read app's GET-only authorization is not broadened.
Public GET, health, home and read credential remain unchanged. Owner Bearer,
no-Origin/query, exact nonce/timestamp JSON checks remain. OFF delegates the
original environment unchanged; no collector client/provider is invoked.

TRUE requires a real injected RuntimeEvidence provider BEFORE any client.
create_app has no provider by default, so TRUE fails closed. No boolean env
shortcut, default-ready or provider implementation. Record validates pinned
catalog, bounded host/activation source references, observed/expiry window at
most one hour, PID namespace and nested parser bwrap proofs, capacity proof,
WSGI timeout strictly over 120 seconds and conservative 1536 MiB available
memory. Record/interface validates structure, NOT owner authority or real host
claims. The actual host provider and source-grounded activation evidence are
197d. No live Render/Atlas probes or writes were performed in this unit.

Authorized requests re-fetch/revalidate provider evidence before ledger access;
expired/missing proof refuses without collection. Public reads still work.
If real Render capacity cannot meet this contract, reduce worker/parser caps
only under a separately reviewed proposal and proof. Never quietly lower caps.

No live configuration, collector start, old collector stop, mail, Telegram,
index/TTL creation, workflow or other repository changes. Source remains OFF.
