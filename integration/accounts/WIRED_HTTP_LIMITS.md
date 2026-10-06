# Explicit account/session/settings HTTP wiring, not activation

create_wired_http is additive, unselected, no env/client/provision/index/startup
calls. Construction validates exact AccountService, Hasher default scrypt/
PBKDF2 params, Limiter sharing same store/secret/clock and default limits,
SettingsPolicy with exact validators/compulsory Republic, MemoryStore or
MongoAccountStore. Trusted in-process collaborators must not be monkeypatched.
One service/Limiter per store/process is an operational invariant, not globally
enforced; existing multiworker compensation defect remains unsupported.
Mongo constructor's existing review dict is a code gate, not proof of owner
permission/capabilities. A later caller serving this factory with a real store
could issue real state writes. Only disposable Memory/fakeMongo used here.

Route inventory is emitted as factory.route_contract and constants. Public GET
only /account/preauth, which returns protocol CSRF and cookie (not diagnostics).
POST account/login/signup/logout/save-settings/export/change-password/delete
use exact existing JSON schemas/Origin+CSRF protocol; signup closed. GET
account/whoami/settings private. No account preview/assets/UI promoted, no
new login UI; existing fixture/UI unchanged, therefore no changed pixels.

All enumerated selected news GET routes and workspace static rules private,
including previews/export/PDF/dashboard/APIs/Finder/assets/branding/manifest.
Two news POST read-only queries (related-news/finder-context) additionally
require existing session-derived X-CSRF-Token. No new CSRF cookie/protocol.
Legacy mark-emailed, POSTcritical/weekly and stream edit/delete denied. No
second exposed health/static/account catchall. Unknown paths denied, downstream
static filenames still use original owning validation. Factory does NOT take
a full-export pager/events adapter; original unavailable states remain.

Exact lowercase HTTPS DNS hostname, no explicit port (HTTPS443 implicit),
userinfo/path/query/fragment/wildcards/null refused. Direct WSGI host_url must
match; no forwarded-host/proto/IP trust. GET may omit Origin, all POST require
exact Origin (same-origin browser request omitting it refused). Proxy resolution
is future explicit deploy work. Resolver injected trusted callable, bounded
ASCII output via existing service; no JSON/IP override. Its implementation is
trusted code, not authenticated by callable/type alone.

Session/preauth cookies original __Host-gib_session/__Host-gib_pre, Path=/,
HttpOnly/Secure/SameSiteStrict, Max-Age30days/2hours; server session idle7days,
absolute30days. Each successful login mints a new token; existing preauth token
is bucket-valid/reusable until expiry (no new one-time claim). Logout removes
session/clears cookie; password change preserves caller, revokes other sessions.
Every protected news request calls whoami BEFORE reader and fails closed on
store errors, malformed config or revoked/expired session. No signed-in user
settings caches/global principal. Settings use session UID+CAS version, exact
schema and mandatory Republic. Hashes/passwords/session tokens never returned
in JSON; CSRF only original login/preauth/whoami protocol, never error/export
or URL. Account logging disabled to avoid exception traces; no audit-log claim.

7 focused tests exercise route denials, cookie/KDF persistence, two-user settings
CAS/export, Host/forwarded boundary, missing/hostile CSRF, news logout/expiry/
password fences, disposable Mongo flow/store outage, zero construction client
calls, collaborator/origin checks and legacy mutation refusal. No actual Atlas,
proxy/host serving, production auth/writes, shared multiworker limit or readiness
proof. Launcher/environment/original gates untouched.
