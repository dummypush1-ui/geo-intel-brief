# Copyright (c) 2026 Push
import socket, threading, unittest
from integration.accounts import AccountService, MemoryStore, Hasher, SettingsPolicy, hash_invite
from integration.accounts import csrf, validators as V
from integration.accounts.passwords import check_policy, normalize_username, Busy
from integration.accounts.service import clear_cookie_header
from integration.accounts.limiter import make_key

SECRET = b"s" * 48
ORIGIN = "https://example.invalid"
PW = "correct horse battery"
FAST = dict(n=2 ** 10)


class Clock:
    def __init__(self): self.t = 1_800_000_000.0
    def __call__(self): return self.t


class Base(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.store = MemoryStore()
        self.svc = AccountService(self.store, SECRET, self.clock, hasher=Hasher(**FAST),
                                  allowed_origins=[ORIGIN])
        self.store.add_invite(hash_invite(SECRET, "invite-code-1"), 2)

    def pre(self):
        p = self.svc.issue_preauth(); return p["csrf"], p["nonce"]

    def signup(self, name="alice", pw=PW, code="invite-code-1", client="c1"):
        t, n = self.pre()
        return self.svc.signup(name, pw, code, t, n, client, ORIGIN)

    def login(self, name="alice", pw=PW, client="c1"):
        t, n = self.pre()
        return self.svc.login(name, pw, t, n, client, ORIGIN)

    def user(self):
        r = self.signup()
        self.assertTrue(r["ok"])
        return r["session_token"], r["csrf"]


class TestPasswords(unittest.TestCase):
    def test_hash_verify(self):
        h = Hasher(**FAST); s = h.hash(PW)
        self.assertTrue(h.verify(PW, s)); self.assertFalse(h.verify("wrong password!", s))
        self.assertNotEqual(s, h.hash(PW))             # per-user salt
        self.assertFalse(h.verify(PW, "garbage"))
        self.assertNotIn(PW, s)

    def test_nfkc_and_rehash(self):
        h = Hasher(**FAST)
        self.assertTrue(h.verify("\uff50assword-long-1", h.hash("password-long-1")))
        self.assertTrue(Hasher(n=2 ** 11).needs_rehash(h.hash(PW)))
        self.assertFalse(h.needs_rehash(h.hash(PW)))

    def test_pbkdf2_fallback(self):
        h = Hasher(pbkdf2_iters=1000); h._has_scrypt = False
        s = h.hash(PW); self.assertTrue(s.startswith("pbkdf2$")); self.assertTrue(h.verify(PW, s))

    def test_policy(self):
        self.assertEqual(check_policy(PW, "alice"), [])
        for bad in ["short", "x" * 129, "aaaaaaaaaaaa", "password1234", "ok-password\u200b-1", "alice-is-me-123", None, 5]:
            self.assertTrue(check_policy(bad, "alice"), bad)

    def test_usernames(self):
        self.assertEqual(normalize_username(" Alice_1 "), "alice_1")
        for bad in ["ab", "a" * 33, "bad name", "a@b.c", "x\u0430y", None, 3, "..."]:
            self.assertIsNone(normalize_username(bad), bad)

    def test_busy(self):
        h = Hasher(max_concurrent=1, **FAST); h._sem.acquire()
        with self.assertRaises(Busy): h.hash(PW)


class TestCsrf(unittest.TestCase):
    N = "ab" * 16

    def test_login_token(self):
        t = csrf.login_token(SECRET, 5000.0, self.N)
        self.assertTrue(csrf.verify_login_token(SECRET, t, 5000.0, self.N))
        self.assertTrue(csrf.verify_login_token(SECRET, t, 5000.0 + 3600, self.N))
        self.assertFalse(csrf.verify_login_token(SECRET, t, 5000.0 + 7300, self.N))
        self.assertFalse(csrf.verify_login_token(SECRET, t, 5000.0, "cd" * 16))     # other browser's nonce
        self.assertFalse(csrf.verify_login_token(b"o" * 48, t, 5000.0, self.N))
        for bad in [None, "", "1.2.3", "x.y", t[:-1] + "0", 5, "\u0663.\u0663" * 3, "\xe9" * 70,
                    "9" * 5000 + "." + "a" * 64, "1." + "A" * 64, t + "\n", " " + t, b"x"]:
            self.assertFalse(csrf.verify_login_token(SECRET, bad, 5000.0, self.N), repr(bad)[:40])
        for bad in [None, "", "zz", "\xe9" * 32, 5, "ab" * 17]:
            self.assertFalse(csrf.verify_login_token(SECRET, t, 5000.0, bad))
        with self.assertRaises(ValueError): csrf.login_token(SECRET, 5000.0, "short")

    def test_session_token_bounded(self):
        t = csrf.session_token(SECRET, "h" * 64)
        self.assertTrue(csrf.verify_session_token(SECRET, "h" * 64, t))
        for bad in [None, "", "\xe9" * 64, "\u0663" * 64, "a" * 5000, 5, t.upper(), t + "0"]:
            self.assertFalse(csrf.verify_session_token(SECRET, "h" * 64, bad))

    def test_origin(self):
        self.assertFalse(csrf.origin_ok(None, {"a"})); self.assertTrue(csrf.origin_ok(None, {"a"}, require=False))
        self.assertTrue(csrf.origin_ok("a", {"a"}))
        self.assertFalse(csrf.origin_ok("b", {"a"})); self.assertFalse(csrf.origin_ok("null", {"a"}))


class TestFlow(Base):
    def test_signup_login_logout(self):
        r = self.signup()
        self.assertTrue(r["ok"])
        for flag in ("HttpOnly", "Secure", "SameSite=Strict", "Path=/", "__Host-"):
            self.assertIn(flag, r["set_cookie"])
        self.assertNotIn("Domain", r["set_cookie"])
        self.assertTrue(self.svc.whoami(r["session_token"])["ok"])
        out = self.svc.logout(r["session_token"], r["csrf"], ORIGIN)
        self.assertTrue(out["ok"]); self.assertEqual(out["set_cookie"], clear_cookie_header())
        self.assertFalse(self.svc.whoami(r["session_token"])["ok"])
        l = self.login(); self.assertTrue(l["ok"])
        self.assertNotEqual(l["session_token"], r["session_token"])   # fresh token per login

    def test_store_holds_only_hashes_and_minimal_data(self):
        r = self.signup()
        self.assertNotIn(r["session_token"], self.store.sessions)
        self.assertEqual(set(self.store.users["alice"]), {"uid", "username", "password", "created", "pwv"})
        self.assertEqual(set(self.store.sessions[next(iter(self.store.sessions))]),
                         {"uid", "username", "created", "expires", "idle_expires"})
        blob = repr(self.store.attempts) + repr(self.store.users)
        self.assertNotIn("alice", repr(self.store.attempts)); self.assertNotIn("c1", repr(self.store.attempts))
        self.assertNotIn(PW, blob)

    def test_enumeration_resistance(self):
        self.signup()
        a = self.login("alice", "wrong-password-1"); b = self.login("nobody", "wrong-password-1")
        self.assertEqual(a, b)
        self.assertEqual(self.login("bad name!", "x"), a)
        # signup refusals identical: taken name, bad invite, missing invite
        t = self.signup("alice", PW, "invite-code-1", "c2")
        u = self.signup("newname", PW, "wrong-invite-xx", "c3")
        v = self.signup("newname2", PW, None, "c4")
        self.assertEqual(t, u); self.assertEqual(u, v)
        self.assertEqual(t, {"ok": False, "error": "signup_failed"})

    def test_timing_dummy_hash_used(self):
        calls = []
        orig = self.svc.hasher.verify
        self.svc.hasher.verify = lambda p, s: (calls.append(s), orig(p, s))[1]
        self.login("ghost", "whatever-password")
        self.assertEqual(len(calls), 1)               # unknown user still costs one verification

    def test_invite_single_use_and_failed_signup_keeps_invite(self):
        self.store.add_invite(hash_invite(SECRET, "one-shot-code"), 1)
        self.signup("weak", "short", "one-shot-code")   # weak password: invite not consumed
        self.assertTrue(self.signup("bob", PW, "one-shot-code")["ok"])
        self.assertFalse(self.signup("carol", PW, "one-shot-code", "c9")["ok"])

    @staticmethod
    def _p(svc):
        p = svc.issue_preauth(); return (p["csrf"], p["nonce"])

    def test_modes(self):
        s = AccountService(self.store, SECRET, self.clock, hasher=Hasher(**FAST), signup_mode="closed",
                           allowed_origins=[ORIGIN])
        self.assertEqual(s.signup("dave", PW, "invite-code-1", *self._p(s), "c", ORIGIN)["error"], "signup_failed")
        o = AccountService(self.store, SECRET, self.clock, hasher=Hasher(**FAST), signup_mode="open",
                           allowed_origins=[ORIGIN])
        self.assertTrue(o.signup("dave", PW, None, *self._p(o), "c", ORIGIN)["ok"])
        with self.assertRaises(ValueError): AccountService(self.store, b"short", self.clock)
        with self.assertRaises(ValueError): AccountService(self.store, SECRET, self.clock, signup_mode="x")

    def test_csrf_and_origin_enforced(self):
        self.signup()
        t, n = self.pre()
        self.assertEqual(self.svc.login("alice", PW, "bad", n, "c", ORIGIN)["error"], "forbidden")
        self.assertEqual(self.svc.login("alice", PW, t, n, "c", "https://evil.invalid")["error"], "forbidden")
        self.assertEqual(self.svc.login("alice", PW, t, n, "c", None)["error"], "forbidden")      # absent Origin refused
        self.assertEqual(self.svc.login("alice", PW, t, "cd" * 16, "c", ORIGIN)["error"], "forbidden")  # token bound to nonce
        self.assertEqual(self.svc.login("alice", PW, t, None, "c", ORIGIN)["error"], "forbidden")
        self.assertTrue(self.svc.login("alice", PW, t, n, "c", ORIGIN)["ok"])
        tok, c = self.user_login()
        self.assertEqual(self.svc.save_settings(tok, "bad", [], [], 0, ORIGIN)["error"], "forbidden")
        self.assertEqual(self.svc.save_settings(tok, c, [], [], 0, "https://evil.invalid")["error"], "forbidden")
        self.assertEqual(self.svc.logout(tok, None, ORIGIN)["error"], "forbidden")
        self.assertEqual(self.svc.logout(tok, c, None)["error"], "forbidden")
        self.assertTrue(self.svc.whoami(tok)["ok"])

    def user_login(self):
        r = self.login(); return r["session_token"], r["csrf"]

    def test_csrf_not_transferable_between_sessions(self):
        self.signup(); a = self.login(); b = self.login()
        self.assertEqual(self.svc.logout(a["session_token"], b["csrf"], ORIGIN)["error"], "forbidden")

    def test_lockout_and_recovery(self):
        self.signup()
        for _ in range(5): self.login("alice", "wrong-password-1")
        r = self.login("alice", PW)
        self.assertEqual(r["error"], "too_many_attempts"); self.assertGreater(r["retry_after"], 0)
        self.clock.t += 901
        self.assertTrue(self.login("alice", PW)["ok"])

    def test_lockout_same_for_unknown_user(self):
        for _ in range(5): self.login("ghost", "wrong-password-1")
        self.assertEqual(self.login("ghost", "wrong-password-1")["error"], "too_many_attempts")

    def test_client_limit_across_usernames(self):
        for i in range(20): self.login("user%d" % i, "wrong-password-1", client="same")
        self.assertEqual(self.login("alice", PW, client="same")["error"], "too_many_attempts")

    def test_lock_escalates(self):
        for _ in range(6): self.login("x1x", "wrong-password-1")
        self.clock.t += 901
        for _ in range(5): self.login("x1x", "wrong-password-1")
        self.assertGreater(self.login("x1x", "wrong-password-1")["retry_after"], 1000)

    def test_session_expiry(self):
        r = self.signup()
        self.clock.t += 6 * 86400; self.assertTrue(self.svc.whoami(r["session_token"])["ok"])   # idle slides
        self.clock.t += 6 * 86400; self.assertTrue(self.svc.whoami(r["session_token"])["ok"])
        self.clock.t += 8 * 86400; self.assertFalse(self.svc.whoami(r["session_token"])["ok"])
        r = self.login(); self.clock.t += 31 * 86400
        self.assertFalse(self.svc.whoami(r["session_token"])["ok"])    # absolute limit

    def test_garbage_tokens(self):
        for t in [None, "", "x", "a" * 500, 5, {}]:
            self.assertFalse(self.svc.whoami(t)["ok"])

    def test_change_password_revokes_others(self):
        self.assertEqual(self.svc.change_password('x' * 30, 'x', PW, PW, 'c', ORIGIN)['error'], 'unauthenticated')
        a = self.signup(); b = self.login()
        r = self.svc.change_password(b["session_token"], b["csrf"], PW, "another long passphrase", "c1", ORIGIN)
        self.assertTrue(r["ok"])
        self.assertFalse(self.svc.whoami(a["session_token"])["ok"]); self.assertTrue(self.svc.whoami(b["session_token"])["ok"])
        self.assertFalse(self.login("alice", PW)["ok"]); self.assertTrue(self.login("alice", "another long passphrase")["ok"])
        self.assertEqual(self.svc.change_password(b["session_token"], b["csrf"], "nope-nope-nope", "a-different-long-pass", "c1", ORIGIN)["error"], "invalid_credentials")

    def test_rehash_on_login(self):
        self.signup()
        self.svc.hasher = Hasher(n=2 ** 11)
        self.assertTrue(self.login()["ok"])
        self.assertIn("2048", self.store.users["alice"]["password"]); self.assertEqual(self.store.users["alice"]["pwv"], 0)

    def test_no_network(self):
        orig = socket.socket
        def boom(*a, **k): raise AssertionError("network")
        socket.socket = boom
        try:
            self.signup(); self.login()
        finally:
            socket.socket = orig


class TestSettings(Base):
    CH = {"name": "Chan One", "video": "abcdefghijk"}

    def test_roundtrip_and_republic(self):
        tok, c = self.user()
        g = self.svc.get_settings(tok)["settings"]
        self.assertEqual(g["version"], 0); self.assertEqual(g["channels"][0]["video"], "jndNegut8RY")
        self.assertTrue(g["channels"][0]["compulsory"])
        r = self.svc.save_settings(tok, c, [self.CH, {"name": "Rep dup", "video": "https://youtu.be/jndNegut8RY"}], ["India", "Japan"], 0, ORIGIN)
        self.assertTrue(r["ok"], r)
        self.assertEqual([x["video"] for x in r["settings"]["channels"]], ["jndNegut8RY", "abcdefghijk"])
        self.assertEqual(self.store.settings[self.uid()]["channels"], [self.CH])     # Republic never stored
        self.assertEqual(r["settings"]["version"], 1)

    def test_version_conflict(self):
        tok, c = self.user()
        self.assertTrue(self.svc.save_settings(tok, c, [], [], 0, ORIGIN)["ok"])
        self.assertEqual(self.svc.save_settings(tok, c, [], [], 0, ORIGIN)["error"], "version_conflict")
        for bad in (True, -1, "0", 1.0, None):
            self.assertEqual(self.svc.save_settings(tok, c, [], [], bad, ORIGIN)["error"], "invalid_request")

    def test_isolation_between_users(self):
        t1, c1 = self.user()
        self.svc.save_settings(t1, c1, [self.CH], ["India"], 0, ORIGIN)
        t2 = self.signup("bob", PW, "invite-code-1", "c2")
        self.assertEqual(self.svc.get_settings(t2["session_token"])["settings"]["watchlist"], [])

    def uid(self): return self.store.users["alice"]["uid"]

    def test_unauthenticated(self):
        self.assertEqual(self.svc.get_settings("x" * 40)["error"], "unauthenticated")

    def test_invalid_inputs(self):
        tok, c = self.user()
        bads = [
            ([{"name": "x", "video": "short"}], []),
            ([{"name": "x", "video": "abcdefghijk", "extra": 1}], []),
            ([{"name": "x"}], []), (["abcdefghijk"], []), ([None], []),
            ([{"name": "", "video": "abcdefghijk"}], []),
            ([{"name": "\u200b", "video": "abcdefghijk"}], []),
            ([{"name": "a\u0007b", "video": "abcdefghijk"}], []),
            ([{"name": "n" * 81, "video": "abcdefghijk"}], []),
            ([{"name": "x", "video": "https://www.youtube.com/watch?v=abcdefghijk&t=1"}], []),
            ([{"name": "x", "video": "http://youtu.be/abcdefghijk"}], []),
            ([{"name": "x", "video": "https://youtu.be/abc%64efghijk"}], []),
            ([{"name": "x", "video": "https://youtu.be\\abcdefghijk"}], []),
            ([{"name": "x", "video": "abcdefghij "}, {"name": "y", "video": "abcdefghijk"}][:0] + [{"name": "x", "video": "abcdefghi k"}], []),
            ([self.CH, {"name": "Other", "video": "https://youtu.be/abcdefghijk"}], []),   # duplicate video
            ([{"name": "\uff32epublic", "video": "abcdefghijk"}], []),                      # NFKC 'Republic'
            ([dict(self.CH, name="v%d" % i, video="%011d" % i) for i in range(21)], []),
            ([], ["a"] * 2), ([], [""]), ([], [" "]), ([], ["x" * 101]), ([], ["a\nb"]),
            ([], list("abcdefghijklmnopqrstu")), ([], [5]), ([], "India"), ("x", []),
            ([], [{"__proto__": 1}]),
        ]
        for ch, wl in bads:
            r = self.svc.save_settings(tok, c, ch, wl, 0, ORIGIN)
            self.assertEqual(r.get("error"), "invalid_settings", (ch, wl))
        self.assertEqual(self.svc.get_settings(tok)["settings"]["version"], 0)

    def test_valid_edge(self):
        tok, c = self.user()
        ok = [{"name": "  Trim me ", "video": "https://www.youtube.com/watch?v=ab_-defghij"},
              {"name": "n" * 80, "video": "abcdefghijk"}]
        r = self.svc.save_settings(tok, c, ok, ["x" * 100, "india", "India"], 0, ORIGIN)
        self.assertTrue(r["ok"], r)
        self.assertEqual(self.store.settings[self.uid()]["channels"][0], {"name": "Trim me", "video": "ab_-defghij"})

    def test_watch_allowed_list_and_no_mutation(self):
        p = SettingsPolicy(watch_allowed=["India"])
        inp = [self.CH]; p.clean(inp, ["India"]); self.assertEqual(inp, [self.CH])
        with self.assertRaises(ValueError): p.clean([], ["Japan"])

    def test_pluggable_validator(self):
        p = SettingsPolicy(compulsory_channels=(), channel_validator=lambda i: {"name": "n", "video": str(i)})
        self.assertEqual(p.clean(["a", "b"], [])[0][1]["video"], "b")


class TestExportDelete(Base):
    def test_export_minimal(self):
        tok, c = self.user()
        self.svc.save_settings(tok, c, [TestSettings.CH], ["India"], 0, ORIGIN)
        d = self.svc.export(tok, c, ORIGIN)["data"]
        self.assertEqual(set(d), {"username", "created_at", "settings"})
        self.assertEqual(d["username"], "alice"); self.assertTrue(d["created_at"].endswith("+00:00"))
        self.assertNotIn("password", repr(d))
        self.assertEqual(self.svc.export(tok, "bad", ORIGIN)["error"], "forbidden")

    def test_delete(self):
        tok, c = self.user(); other = self.login()
        self.svc.save_settings(tok, c, [], ["India"], 0, ORIGIN)
        self.assertEqual(self.svc.delete_account(tok, c, "wrong-password-1", "c1", ORIGIN)["error"], "invalid_credentials")
        self.assertEqual(self.svc.delete_account(tok, "bad", PW, "c1", ORIGIN)["error"], "forbidden")
        self.assertTrue(self.svc.delete_account(tok, c, PW, "c1", ORIGIN)["ok"])
        self.assertIsNone(self.store.get_user("alice")); self.assertEqual(self.store.settings, {}); self.assertEqual(self.store.by_uid, {})
        self.assertEqual(self.store.sessions, {})
        self.assertFalse(self.svc.whoami(other["session_token"])["ok"])
        self.assertNotIn(make_key(SECRET, "u", "alice"), self.store.attempts)     # per-user limiter record removed
        self.assertFalse(self.login()["ok"])

    def test_purge(self):
        self.user(); self.clock.t += 40 * 86400; self.store.purge(self.clock())
        self.assertEqual(self.store.sessions, {})


class TestValidatorsDirect(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(V.clean_label(" 日本 ", 100), "日本")
        self.assertEqual(V.utf16_len("😀"), 2)
        with self.assertRaises(ValueError): V.clean_label("😀" * 51, 100)   # 102 UTF-16 units
        with self.assertRaises(ValueError): V.clean_label("\u00ad", 100)


if __name__ == "__main__":
    unittest.main()
