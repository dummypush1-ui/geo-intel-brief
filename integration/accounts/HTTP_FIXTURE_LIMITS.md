# Memory-only account HTTP fixture

Factory must be explicitly constructed with AccountService, exact MemoryStore, caller's secret/clock/origin and a trusted fixture client resolver. It is not imported by the merged app and does not replace PreviewAccess. No real signup/login service, database client, network, environment read or provider key entry is enabled. Test fixture inputs only. Existing account foundation defaults invite signup; a production operator must explicitly choose closed signup before activation.

Verified HTTP boundary: exact HTTPS canonical host and exact-string Origin match (no trailing slash normalization, no alternate origins); secure HttpOnly SameSiteStrict host-prefix cookies; session tokens omitted from JSON, post-login/signup preauth cookie cleared; logout session cookie cleared even when expired/invalid; no-store and CSP; JSON404/405/500 (redacted exception body), debug off; bounded16KB strict field JSON, duplicate fields rejected before service; cookie-bound session/login CSRF; coarse status/error codes. Secure cookies require HTTPS; loopback-browser tests use HTTPS fixture context, not credential collection.

Production blockers/design choices:
- request.host_url host/scheme comparison fails closed behind unconfigured TLS termination. Require explicit trusted reverse-proxy addresses and canonical host filtering; never trust arbitrary forwarded headers.
- Trusted client identity resolver must be pinned to platform proxy policy, never raw X-Forwarded-For or a caller JSON value. Shared/atomic store/limiter still missing. MemoryStore is one process only.
- HSTS and rate limits for preauth/entire auth surface must exist at the edge. No preauth edge limiter is simulated by the fixture.
- Optional Sec-Fetch-Site same-origin/none gate for GET endpoints should be decided before production. Current GETs still require exact host and use SameSiteStrict cookies; no CORS permissions.
- save_settings and export intentionally do NOT require password re-entry: live session+CSRF+Origin are required. Change password/delete require re-entry. Reassess with owner before exposing production account/export behavior.
- Mongo adapter must meet foundation's full fenced atomicity contract and index/shared limiter design. Signup mode/reset recovery/real operator configuration and lifecycle must be reviewed, no auto scheduler/purge here.

Loopback HTTPS Chromium validated the separate fixture sign-in/settings UI at390px: login, save, reload, export and logout. Fixture signup is explicitly closed after test seeding. No real phone/device functional validation, production performance, cross-worker durability or deployment readiness is claimed. Merged routing and production accounts remain unwired.
