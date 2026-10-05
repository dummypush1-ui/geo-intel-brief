# Copyright (c) 2026 Push
"""Account service: signup (invite), login, logout, sessions, CSRF, settings, export, delete.
Pure logic over an injected store, clock and secret. No I/O, no config reads, no network.
Results are dicts with ok/error codes; error codes are deliberately coarse."""
import datetime, hashlib, secrets

from . import csrf as _csrf
from .limiter import Limiter, make_key
from .passwords import Busy, Hasher, check_policy, normalize_username, printable_ascii
from .settings import SettingsPolicy

SESSION_IDLE = 7 * 86400
SESSION_ABS = 30 * 86400
MAX_SESSIONS = 10
PREAUTH_TTL = 7200
COOKIE_NAME = "__Host-gib_session"
PREAUTH_NAME = "__Host-gib_pre"
MIN_SECRET = 32
MODES = ("invite", "closed", "open")


def _sha(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _cookie(name, value, max_age):
    return "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=Strict" % (name, value, max_age)


def cookie_header(token, max_age=SESSION_ABS, name=COOKIE_NAME):
    return _cookie(name, token, max_age)


def clear_cookie_header(name=COOKIE_NAME):
    return _cookie(name, "", 0)


def hash_invite(secret, code):
    return make_key(secret, "invite", code)


class AccountService:
    def __init__(self, store, secret, clock, hasher=None, policy=None, signup_mode="invite",
                 allowed_origins=(), max_users=50, require_origin=True, max_sessions=MAX_SESSIONS):
        if not isinstance(secret, (bytes, bytearray)) or len(secret) < MIN_SECRET:
            raise ValueError("secret must be at least 32 bytes")
        if signup_mode not in MODES:
            raise ValueError("signup_mode")
        self.store, self.secret, self.clock = store, bytes(secret), clock
        self.hasher = hasher or Hasher()
        self.policy = policy or SettingsPolicy()
        self.mode, self.origins, self.max_users = signup_mode, frozenset(allowed_origins), max_users
        self.require_origin, self.max_sessions = require_origin, max_sessions
        self.limiter = Limiter(store, self.secret, clock)
        self._dummy = self.hasher.hash("dummy-password-for-timing")   # precomputed with the CURRENT params

    # ---- helpers
    @staticmethod
    def _client_ok(client):
        return printable_ascii(client, 1, 200)

    def _dummy_hash(self):
        if self.hasher.needs_rehash(self._dummy):          # only after the hasher's parameters were changed
            self._dummy = self.hasher.hash("dummy-password-for-timing")
        return self._dummy

    def _origin(self, origin):
        return _csrf.origin_ok(origin, self.origins, self.require_origin)

    def purge(self):
        """Call on a schedule: removes expired sessions and limiter records."""
        self.store.purge(self.clock())

    def issue_preauth(self):
        """For the login/signup page: returns the nonce (set it as a pre-auth cookie) and the form token."""
        nonce = secrets.token_hex(16)
        return {"nonce": nonce, "csrf": _csrf.login_token(self.secret, self.clock(), nonce),
                "set_cookie": _cookie(PREAUTH_NAME, nonce, PREAUTH_TTL)}

    def _pre_ok(self, csrf_token, nonce, origin):
        return self._origin(origin) and _csrf.verify_login_token(self.secret, csrf_token, self.clock(), nonce)

    def _open_session(self, rec):
        now = self.clock()
        token = secrets.token_urlsafe(32)
        h = _sha(token)
        s = {"uid": rec["uid"], "username": rec["username"], "created": now,
             "expires": now + SESSION_ABS, "idle_expires": now + SESSION_IDLE}
        if not self.store.create_session(h, s, rec["uid"], rec["pwv"], self.max_sessions):
            return None
        return {"ok": True, "session_token": token, "csrf": _csrf.session_token(self.secret, h),
                "set_cookie": cookie_header(token)}

    def _session(self, token):
        if not isinstance(token, str) or not 20 <= len(token) <= 100 or not token.isascii():
            return None, None
        h = _sha(token)
        s = self.store.touch_session(h, self.clock(), SESSION_IDLE)
        return (s, h) if s else (None, None)

    def _authed(self, token, csrf_token, origin):
        if not self._origin(origin):
            return None, None, "forbidden"
        s, h = self._session(token)
        if not s:
            return None, None, "unauthenticated"
        if not _csrf.verify_session_token(self.secret, h, csrf_token):
            return None, None, "forbidden"
        return s, h, None

    # ---- signup / login / logout
    def signup(self, username, password, invite_code, csrf_token, nonce, client, origin=None):
        """Every refusal (bad invite, taken name, closed, cap) returns the same coarse error."""
        generic = {"ok": False, "error": "signup_failed"}
        if not self._client_ok(client):
            return {"ok": False, "error": "invalid_request"}
        if not self._pre_ok(csrf_token, nonce, origin):
            return {"ok": False, "error": "forbidden"}
        if self.mode == "closed":                          # nothing is reserved or counted
            return generic
        u = normalize_username(username)
        tok, wait = self.limiter.begin("signup", u or "invalid", client)
        if wait:
            return {"ok": False, "error": "too_many_attempts", "retry_after": wait}
        try:
            if not u:
                self.limiter.fail(tok)
                return generic
            problems = check_policy(password, u)
            if problems:
                self.limiter.refund(tok)
                return {"ok": False, "error": "weak_password", "problems": problems}
            ih = None
            if self.mode == "invite":
                if not printable_ascii(invite_code, 8, 128):
                    self.limiter.fail(tok)
                    return generic
                ih = hash_invite(self.secret, invite_code)
            try:
                pw_hash = self.hasher.hash(password)
            except Busy:
                self.limiter.refund(tok)
                return {"ok": False, "error": "busy"}
            rec = {"uid": secrets.token_hex(16), "password": pw_hash, "created": self.clock(), "pwv": 0}
            if self.store.create_account(u, rec, ih, self.max_users) != "ok":
                self.limiter.fail(tok)
                return generic
            rec["username"] = u
            out = self._open_session(rec)
            if not out:
                self.limiter.fail(tok)
                return generic
            self.limiter.success(tok)
            return out
        finally:
            # Consume unhandled/exceptional reservations without refunding counts.
            # Already-settled tokens are a no-op; fail performs no store callbacks.
            self.limiter.fail(tok)

    def login(self, username, password, csrf_token, nonce, client, origin=None):
        bad = {"ok": False, "error": "invalid_credentials"}
        if not self._client_ok(client):
            return {"ok": False, "error": "invalid_request"}
        if not self._pre_ok(csrf_token, nonce, origin):
            return {"ok": False, "error": "forbidden"}
        u = normalize_username(username)
        tok, wait = self.limiter.begin("login", u or "invalid", client)
        if wait:
            return {"ok": False, "error": "too_many_attempts", "retry_after": wait}
        try:
            rec = self.store.get_user(u) if u else None
            try:
                ok = self.hasher.verify(password, rec["password"] if rec else self._dummy_hash())
            except Busy:
                self.limiter.refund(tok)
                return {"ok": False, "error": "busy"}
            if not (rec and ok):
                self.limiter.fail(tok)
                return bad
            if self.hasher.needs_rehash(rec["password"]):
                try:
                    self.store.rehash_password(rec["uid"], rec["pwv"], self.hasher.hash(password))
                except Busy:
                    pass
            out = self._open_session(rec)
            if not out:
                self.limiter.fail(tok)
                return bad       # account deleted or password changed mid-login
            self.limiter.success(tok)
            return out
        finally:
            # Consume unhandled/exceptional reservations without refunding counts.
            # Already-settled tokens are a no-op; fail performs no store callbacks.
            self.limiter.fail(tok)

    def logout(self, token, csrf_token, origin=None):
        s, h, err = self._authed(token, csrf_token, origin)
        if err:
            return {"ok": False, "error": err}
        self.store.delete_session(h)
        return {"ok": True, "set_cookie": clear_cookie_header()}

    def whoami(self, token):
        s, h = self._session(token)
        if not s:
            return {"ok": False, "error": "unauthenticated"}
        return {"ok": True, "username": s["username"], "csrf": _csrf.session_token(self.secret, h)}

    def _reauth(self, s, password, client):
        """Password re-entry under the login limiter. Returns (error|None, user record verified)."""
        if not self._client_ok(client):
            return "invalid_request", None
        tok, wait = self.limiter.begin("login", s["username"], client)
        if wait:
            return "too_many_attempts", None
        try:
            rec = self.store.get_user(s["username"])
            if not rec or rec["uid"] != s["uid"]:
                self.limiter.refund(tok)
                return "unauthenticated", None
            try:
                ok = self.hasher.verify(password, rec["password"])
            except Busy:
                self.limiter.refund(tok)
                return "busy", None
            if not ok:
                self.limiter.fail(tok)
                return "invalid_credentials", None
            self.limiter.success(tok)
            return None, rec
        finally:
            # Consume unhandled/exceptional reservations without refunding counts.
            # Already-settled tokens are a no-op; fail performs no store callbacks.
            self.limiter.fail(tok)

    def change_password(self, token, csrf_token, old, new, client, origin=None):
        s, h, err = self._authed(token, csrf_token, origin)
        if err:
            return {"ok": False, "error": err}
        problems = check_policy(new, s["username"])
        if problems:
            return {"ok": False, "error": "weak_password", "problems": problems}
        err, rec = self._reauth(s, old, client)
        if err:
            return {"ok": False, "error": err}
        try:
            new_hash = self.hasher.hash(new)
        except Busy:
            return {"ok": False, "error": "busy"}
        # fenced commit: live session h, uid, and the pwv observed at re-authentication
        if not self.store.replace_password(s["uid"], rec["pwv"], new_hash, h, self.clock()):
            return {"ok": False, "error": "unauthenticated"}
        return {"ok": True}

    # ---- settings
    def get_settings(self, token):
        s, h = self._session(token)
        if not s:
            return {"ok": False, "error": "unauthenticated"}
        return {"ok": True, "settings": self.policy.view(self.store.get_settings(s["uid"]))}

    def save_settings(self, token, csrf_token, channels, watchlist, expected_version, origin=None):
        s, h, err = self._authed(token, csrf_token, origin)
        if err:
            return {"ok": False, "error": err}
        if type(expected_version) is not int or not 0 <= expected_version < 2 ** 31:
            return {"ok": False, "error": "invalid_request"}
        try:
            c, w = self.policy.clean(channels, watchlist)
        except ValueError:
            return {"ok": False, "error": "invalid_settings"}
        doc = {"version": expected_version + 1, "channels": c, "watchlist": w, "updated": self.clock()}
        if not self.store.put_settings(s["uid"], doc, expected_version, h, self.clock()):
            return {"ok": False, "error": "version_conflict"}
        return {"ok": True, "settings": self.policy.view(doc)}

    # ---- export / delete
    def export(self, token, csrf_token, origin=None):
        s, h, err = self._authed(token, csrf_token, origin)
        if err:
            return {"ok": False, "error": err}
        rec = self.store.get_user(s["username"])
        if not rec or rec["uid"] != s["uid"]:
            return {"ok": False, "error": "unauthenticated"}
        doc = self.store.get_settings(s["uid"]) or {"version": 0, "channels": [], "watchlist": []}
        iso = datetime.datetime.fromtimestamp(rec["created"], datetime.timezone.utc).isoformat()
        return {"ok": True, "data": {"username": s["username"], "created_at": iso,
                                     "settings": {"version": doc["version"], "channels": doc["channels"],
                                                  "watchlist": doc["watchlist"]}}}

    def delete_account(self, token, csrf_token, password, client, origin=None):
        s, h, err = self._authed(token, csrf_token, origin)
        if err:
            return {"ok": False, "error": err}
        err, rec = self._reauth(s, password, client)
        if err:
            return {"ok": False, "error": err}
        if not self.store.delete_account(s["username"], s["uid"], rec["pwv"], h, self.clock()):
            return {"ok": False, "error": "unauthenticated"}
        for op in ("login", "signup"):
            self.store.delete_attempts(self.limiter.user_key(op, s["username"]))
        return {"ok": True, "set_cookie": clear_cookie_header()}
