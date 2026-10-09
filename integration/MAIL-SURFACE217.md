# 217: held private mail mount, source only

build_mail_surface returns the public object unchanged by default, before any
config/public access. Explicit True plus closed config builds a WSGI wrapper,
not a DB-backed mailer. No production module imports it. This unit does not make
mail work; it makes the mount safe to reason about. A 9am target is not readiness.

Config has exactly origin, rail=apps_script, channel_id and header_secret.
Origin is lowercase canonical HTTPS hostname, no port (including explicit443),
path, trailing slash, query, fragment, userinfo, IP literal or localhost.
Channel is lowercase64hex, not authentication or owner permission. Secret is
ASCII48..256 without whitespace/control. Only its SHA256 credential digest is
stored in the wrapper; no plaintext secret is returned/logged/repr'd. Config is
not a grant to send, read DB state, deploy, or change properties.

PATH_INFO interception reserves the exact /internal/mail/v1 segment and children.
Normalization-lookalikes are refused uniformly, never sent to public. SCRIPT_NAME
is not prepended; mounted-app PATH_INFO semantics are preserved. Other routes go
to public with the original environ object unchanged. Public exceptions propagate.

Private auth is checked before body/method/route-key/framing access. Expected and
supplied Authorization digests compare at equal length. Only exact single-space
Bearer ASCII header is accepted; comma-joined duplicates refuse. WSGI cannot
observe a server silently discarding duplicate headers or bytes outside its
stream, so the edge server still owns HTTP framing/header normalization.
Missing/wrong/malformed auth, query string and suspicious paths get the same
401 body/headers. Origin/host mismatches refuse. No proxy headers pick origin.

After auth, POST prepare/claim/ack and GET receipts/64lowerhex are recognized;
other methods/paths refuse. POST JSON is bounded4KiB, required exact Content-Length,
read cap4097, no transfer encoding, strictUTF8/noBOM/duplicate/nonfinite/extra keys.
This observable WSGI check is not proof about raw network framing or hang-proof
transport. The WSGI server must supply bounded/terminated input and read timeouts.
No user-supplied client/default database/DB URL is consulted.

Every valid authorized operation returns503 with exactly
{state:mail_integration_held,retry_send:false}, no payload/receipt/nonce/channel
or Retry-After, fixed JSON/no-store. No successful prepare/claim/ack is possible.
No backend, DB read (including status), DB write, store, ledger, sender, capability,
role, collection/index/genesis creation, timer or environment read is used.
Metadata mounted_held explicitly denies wired/live/ready.

Existing real bridge.gs and216 wrappers are unchanged. Tests use mocked services:
503 at prepare gives zero Gmail calls and retains nonce;503 at claim retains
claiming and never permits/retries send;503 at ack means a send may have occurred,
unknown, and remains possibly_sent under216. Never infer not-sent or clear state.
Ack-only retries do not send again. No real Gmail is used in tests.

No trigger rebuild/activation, property/env/deployment/clasp changes or collector
cutover. Mailer is separate from collector. Apps Script rail stays selected;
SMTP fallback held. Owner's noDB-read/check boundary is preserved. 201c write
selection stays held, including INSERT/drop implicit-creation TOCTOU.

Later units remain open: actual data/mount contract, old128-cap receipt handling,
212key enforcement/history import, mapping/control/state preservation, renderer
selection, marking policy, sender/recipient/final words permission, reconciliation,
DBtiming/weeklyidentity and live workflow proof. This held wrapper resolves none
of these and never starts a follow-up when a future DB URL appears.

channel_id is validated but never used or bound in this surface: inert config,
not enforced channel scope. Uppercase hex in a status path is suspicious401, not
404. Normalized routes starting with /internal/mail/v1, including public-looking
/internal/mail/v10, are deliberately blocked401. Exact HTTP_HOST must equal the
origin hostname without a port; a proxy rewriting Host makes authorized calls
400. Future wiring must verify the real deployed Host; this config does not prove
the origin is the real service.
