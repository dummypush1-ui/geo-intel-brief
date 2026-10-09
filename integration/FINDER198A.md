# 198a narrow account/session gate (unselected)

Default OFF injected WSGI factory only. No production mount, environment read,
client, account provisioning, login UI, proxy request or runtime provider.
OFF returns the original public callable. Enabled routes only exact account
preauthGET/loginPOST/logoutPOST/whoamiGET and /api/finder-broker/ prefix. Other
account routes denied (including signup/settings/export/change/delete). Every
other public route passes unchanged, including news/health/own-key paths.

No broad create_wired_http mount: that old factory makes all news private.
Only its exact AccountService collaborator validation and account protocol
helper are reused behind the smaller allowlist. Closed accounts, current KDF
parameters, exact store/limiter/policy types and shared secret/clock checks.
SingleWorkerEvidence independently injected, fresh<=120s, observed workers=1,
exact scoped host/activation references at startup and each protected request.
No environment WORKERS or assumed Gunicorn default shortcut. No real provider
is shipped; references/record do not grant permission or prove live settings.
One registered service per store in this factory and same bound limiter through
requests. Other service constructors remain a deployment invariant, not proven
absent. Known multiworker compensation defect remains unsupported.

Exact direct HTTPS lowercase configured origin, no forwarded host/proto trust,
no explicit port; query/encoded/dot/backslash/double-slash protected paths deny.
Login/logout original Origin+preauth/session CSRF and16KiB strict body protocol.
whoami original live session check/touch and protocol CSRF. Every brokerGET/POST
needs exact Origin AND live session AND X-CSRF-Token; even authorized broker
returns503 broker_not_wired (198b separate), never calls public or any transport.
No session/secret/password/hash JSON/URL forwarding. Account cookies preserve
original HttpOnly/Secure/SameSiteStrict/__Host/Path scope; no new CSRF protocol.
GET preauth/whoami may omit Origin as original protocol. Public passes unchanged
without account/worker evidence lookup, including when evidence expires.

Serving enabled real store can write: whoami/session checks touch_session,
login creates/re-hashes/session/attempt writes, logout deletes session. Real
Mongo role/transaction/pre-provisioned accounts_state and scoped owner approval
must be checked before mounting; constructor review fields are not permission.
Source tests only disposable MemoryStore/fixtures. No live authDB or owner
state accessed. No automatic account signup, purge, reset or recovery.

Existing login may create a session before limiter-settlement failure; this
unit does NOT claim login+limiter whole-transaction atomicity. Errors return no
success cookie; no automatic retry. Original session idle/absolute expiry,
revocation and account UID checks retained. Singleworker does not fix unrelated
service/store failure modes. No runtime parity or readiness claim.

No UI/client/source Finder changes, so no changed visual artifact. This is only
an inert server boundary; public offline Finder network remains OFF, own-key
flows unchanged. 198b will separately review fixed proxy/provider/model/port
choices and shared durable budget, without arbitrary URL/header forwarding.
