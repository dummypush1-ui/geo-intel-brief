# Copyright (c) 2026 Push
"""Attempt limiting with reserve-then-refund semantics.

begin() atomically counts the attempt BEFORE the password is checked, so concurrent guesses cannot
all pass a stale check: at most `limit` attempts per window reach verification.
Keys are HMACs; unknown usernames are counted exactly like known ones (no enumeration).
Per-user keys are operation-specific ("login" also covers password re-entry for change/delete;
"signup" is separate), so one operation cannot lock another. The client key is shared and is the main brake.
Each record carries a generation id; a refund or clear from an older generation is ignored.
Requires store.update_attempts(key, fn): atomic read-modify-write (adapters use compare-and-set)."""
import hashlib, hmac, secrets

WINDOW = 900
MAX_USER_FAILS = 5
MAX_CLIENT_FAILS = 20
BASE_LOCK = 900
MAX_LOCK = 3600


def make_key(secret, kind, value):
    return hmac.new(secret, ("%s:%s" % (kind, value)).encode("utf-8"), hashlib.sha256).hexdigest()


class Limiter:
    def __init__(self, store, secret, clock, max_user=MAX_USER_FAILS, max_client=MAX_CLIENT_FAILS):
        self.store, self.secret, self.clock = store, secret, clock
        self.max_user, self.max_client = max_user, max_client

    def user_key(self, op, username):
        return make_key(self.secret, "u-" + op, username)

    def client_key(self, client):
        return make_key(self.secret, "c", client)

    def _count(self, key, limit):
        now, out = self.clock(), {"wait": 0, "gen": None}

        def fn(a):
            if a is None or (a["locked_until"] <= now and now - a["last"] > WINDOW):
                a = {"fails": 0, "locks": a["locks"] if a else 0, "last": 0, "locked_until": 0,
                     "gen": secrets.token_hex(6)}            # new window = new generation
            if a["locked_until"] > now:
                out["wait"], out["gen"] = int(a["locked_until"] - now) + 1, a["gen"]
                return a
            a["fails"] += 1
            a["last"] = now
            if a["fails"] > limit:
                a["locks"] += 1
                a["locked_until"] = now + min(MAX_LOCK, BASE_LOCK * 2 ** (a["locks"] - 1))
                a["fails"] = 0
                a["gen"] = secrets.token_hex(6)
                out["wait"] = int(a["locked_until"] - now) + 1
            out["gen"] = a["gen"]
            a["expires"] = max(a["locked_until"], now + WINDOW) + MAX_LOCK
            return a
        self.store.update_attempts(key, fn)
        return out["wait"], out["gen"]

    def _refund(self, key, gen):
        def fn(a):
            if a and a.get("gen") == gen and a["fails"] > 0:
                a["fails"] -= 1
            return a
        self.store.update_attempts(key, fn)

    def _clear(self, key, gen):
        self.store.update_attempts(key, lambda a: None if a and a.get("gen") == gen else a)

    def begin(self, op, username, client):
        """Reserve one attempt. Returns (reservation, wait_seconds); wait > 0 means denied."""
        taken, wait = [], 0
        for key, limit in ((self.user_key(op, username), self.max_user), (self.client_key(client), self.max_client)):
            w, gen = self._count(key, limit)
            if w:
                wait = max(wait, w)
            else:
                taken.append((key, gen))
        if wait:
            for k, g in taken:
                self._refund(k, g)
            return None, wait
        return {"user": taken[0], "client": taken[1]}, 0

    def success(self, res):
        """Correct credentials: clear the user record (same generation only), give the client slot back."""
        self._clear(*res["user"])
        self._refund(*res["client"])

    def refund(self, res):
        """Attempt never reached a verdict (e.g. server busy): give both slots back (same generation only)."""
        self._refund(*res["user"])
        self._refund(*res["client"])
