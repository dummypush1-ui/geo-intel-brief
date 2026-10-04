Copyright (c) 2026 Push

# accounts (offline foundation, not wired)

Stdlib only. No network, DB client, config reads or import-time side effects. Store, clock and secret are injected.

## Modules
- passwords.py: policy (10-128 chars, raw length bounded before and after NFKC, no control/invisible chars, small common list); scrypt (N=2^15, r=8, p=1, 16-byte salt) with PBKDF2-SHA256 fallback; stored hashes are strictly parsed before any derivation (param caps, exact salt/digest length, canonical base64, pbkdf2 1000..5,000,000 iterations); constant-time compare; concurrency cap (Busy); rehash on login.
- store.py: AccountStore interface + MemoryStore. Atomicity contract below.
- limiter.py: reserve-then-refund attempt counter (HMAC keys). Operation-specific user keys: "login" (also used for password re-entry in change/delete) and "signup" are separate, so signup traffic can never lock a login. Closed-mode signup refusals reserve nothing. 5 attempts per user key / 20 per client key per 15 min; the next attempt locks 15 min, doubling to 1 h. Records carry a generation id; a refund or clear from an older window is ignored. Unknown names count identically.
  Deliberate trade-off: 6 wrong passwords against an account lock that account's logins for 15 min (anyone who knows a username can do this). The client key limiter (shared across operations) is the main brake on one source; the per-user lock is the backstop against distributed guessing.
- csrf.py: stateless HMAC tokens, bounded ASCII formats. Login/signup token is bound to a pre-auth nonce cookie; session token is bound to the session. Origin must be present and exact (require_origin=True default).
- service.py: issue_preauth, signup (invite|closed|open), login, logout, whoami, change_password, get/save settings, export, delete_account, purge.
- settings.py / validators.py: browser-rule mirrors. Channels: up to 20 extras stored; the code-defined Republic row is never stored, so users see up to 21 rows (20 extras + Republic). Watchlist up to 20.

## Store atomicity contract (real adapter must meet it)
create_account (username + user cap + invite claimed together); create_session / touch_session (only while the account uid is live; create also checks password version pwv; no upsert); FENCED commits: delete_account(username, uid, pwv, session_hash, now), replace_password(uid, pwv, new_hash, session_hash, now) and put_settings(uid, doc, expected_version, session_hash, now) succeed only if, atomically, the uid is live, the calling session is live/unexpired/owned by that uid, and (delete/replace) pwv equals the value seen when the password was verified; delete/replace also remove or revoke sessions in the same operation; put_settings is also compare-and-set on version; update_attempts atomic read-modify-write (CAS loop). Accounts have an immutable random uid, so a re-registered username never inherits old sessions or settings.

## Stored per user
uid, normalized username, password hash, created time, password version, settings. No email, name, phone or IP. Sessions: SHA-256 of token, uid, username, times. Limiter keys are HMACs with TTL (client hashes expire via purge).

## Wiring requirements (HTTP layer, not in this package)
- Trusted client identity: derive `client` from the platform's trusted proxy header (Render), never from a client-supplied value; pass a non-empty string (<=200). Empty/missing is refused.
- Pre-auth cookie: on the login page call issue_preauth(), set its cookie (__Host-gib_pre) and embed the csrf value; pass both back on POST. Authenticated POSTs send the session csrf value.
- Shared limiter across workers: use a store whose update_attempts is shared and atomic. MemoryStore is single-process only.
- DB atomicity as above; unique index on username and uid.
- Call service.purge() on a schedule (e.g. hourly).
- Request body size limits (e.g. 16 KB) and JSON depth limits before calling the service; cap total request rate at the proxy.
- Env supplied by Push in Render, never in chat: ACCOUNTS_SECRET (>=32 random bytes), signup mode, allowed origins, invite codes (store only hash_invite output).
- Input hygiene: passwords reject control, format/invisible, surrogate, private-use and unassigned characters (ordinary spaces allowed); client keys and invite codes are bounded printable ASCII; usernames are ASCII; labels reject Unicode category C. All checks run before any HMAC or KDF, and refusals are coarse error codes (no exceptions escape).
- Timing: the dummy hash used for unknown users is computed at construction with the CURRENT hash parameters (and recomputed only if the hasher's parameters change). Accounts still holding an older, different-cost hash take a measurably different time than unknown names (a reviewer measured ~12 ms vs ~3 ms for n=4096 vs 1024) until their next successful login rehashes them. Remaining signal: it reveals only that a username exists with legacy parameters; change parameters rarely and expect it to disappear as users log in.
Separate memory-only HTTP/UI fixture exists; see HTTP_FIXTURE_LIMITS.md. Not implemented: production HTTP/UI integration, Mongo adapter, password reset (owner-run only), logging.
