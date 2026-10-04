# Copyright (c) 2026 Push
import base64, threading, unittest
from integration.accounts import AccountService, MemoryStore, Hasher, hash_invite
from integration.accounts.limiter import make_key
from integration.accounts.passwords import check_policy, normalize_password
from integration.accounts import validators as V

SECRET = b"s" * 48
ORIGIN = "https://example.invalid"
PW = "correct horse battery"


class Clock:
    def __init__(self): self.t = 1_800_000_000.0
    def __call__(self): return self.t


class CountingHasher(Hasher):
    def __init__(self, **k):
        super().__init__(**k); self.derivations = 0; self._c = threading.Lock()
    def _derive(self, *a):
        with self._c: self.derivations += 1
        return super()._derive(*a)


def make(**kw):
    clock, store = Clock(), MemoryStore()
    h = kw.pop("hasher", None) or CountingHasher(n=2 ** 10, max_concurrent=64)
    svc = AccountService(store, SECRET, clock, hasher=h, allowed_origins=[ORIGIN], **kw)
    return svc, store, clock, h


def pre(svc):
    p = svc.issue_preauth(); return p["csrf"], p["nonce"]


def signup(svc, name="alice", code="invite-code-1", client="c1", pw=PW):
    t, n = pre(svc); return svc.signup(name, pw, code, t, n, client, ORIGIN)


def login(svc, name="alice", pw=PW, client="c1"):
    t, n = pre(svc); return svc.login(name, pw, t, n, client, ORIGIN)


def run_threads(fns):
    out, barrier = [None] * len(fns), threading.Barrier(len(fns))
    def w(i):
        barrier.wait(); out[i] = fns[i]()
    ts = [threading.Thread(target=w, args=(i,)) for i in range(len(fns))]
    [t.start() for t in ts]; [t.join() for t in ts]
    return out


class TestAccountIdentity(unittest.TestCase):
    def setUp(self):
        self.svc, self.store, self.clock, self.h = make()
        self.store.add_invite(hash_invite(SECRET, "invite-code-1"), 10)

    def test_old_token_never_works_for_reregistered_name(self):
        a = signup(self.svc)
        uid1 = self.store.users["alice"]["uid"]
        self.assertTrue(self.svc.delete_account(a["session_token"], a["csrf"], PW, "c1", ORIGIN)["ok"])
        b = signup(self.svc, client="c2")
        self.assertNotEqual(uid1, self.store.users["alice"]["uid"])
        self.assertFalse(self.svc.whoami(a["session_token"])["ok"])
        self.assertTrue(self.svc.whoami(b["session_token"])["ok"])

    def test_session_cannot_be_created_or_touched_after_delete(self):
        a = signup(self.svc); u = self.store.users["alice"]
        uid, pwv = u["uid"], u["pwv"]
        sess = next(iter(self.store.sessions)); now = self.clock()
        self.assertTrue(self.store.delete_account("alice", uid, pwv, sess, now))
        rec = {"uid": uid, "username": "alice", "created": 1, "expires": 9e12, "idle_expires": 9e12}
        self.assertFalse(self.store.create_session("h" * 64, rec, uid, pwv, 10))
        self.assertEqual(self.store.sessions, {})
        self.assertFalse(self.store.put_settings(uid, {"version": 1, "channels": [], "watchlist": []}, 0, sess, now))
        self.assertEqual(self.store.settings, {})

    def test_stale_login_cannot_open_session_after_password_change(self):
        a = signup(self.svc); stale = self.store.get_user("alice")
        self.assertTrue(self.svc.change_password(a["session_token"], a["csrf"], PW, "a-brand-new-passphrase", "c1", ORIGIN)["ok"])
        self.assertIsNone(self.svc._open_session(stale))        # pwv changed since the login read the user
        self.assertEqual(len(self.store.sessions), 1)

    def test_concurrent_delete_and_use_leaves_no_session(self):
        for round_ in range(15):
            svc, store, clock, h = make()
            store.add_invite(hash_invite(SECRET, "invite-code-1"), 5)
            a = signup(svc); uid = store.users["alice"]["uid"]
            fns = [lambda: svc.delete_account(a["session_token"], a["csrf"], PW, "c%d" % round_, ORIGIN)]
            fns += [lambda: svc.whoami(a["session_token"]) for _ in range(6)]
            fns += [lambda: svc.save_settings(a["session_token"], a["csrf"], [], ["x"], 0, ORIGIN) for _ in range(3)]
            run_threads(fns)
            self.assertEqual([s for s in store.sessions.values() if s["uid"] == uid], [])
            self.assertNotIn(uid, store.settings)
            self.assertFalse(svc.whoami(a["session_token"])["ok"])

    def test_concurrent_password_change_revokes(self):
        a = signup(self.svc); b = login(self.svc)
        run_threads([lambda: self.svc.change_password(a["session_token"], a["csrf"], PW, "a-brand-new-passphrase", "c1", ORIGIN)]
                    + [lambda: self.svc.whoami(b["session_token"]) for _ in range(4)])
        self.assertFalse(self.svc.whoami(b["session_token"])["ok"])

    def test_session_cap_evicts_oldest(self):
        svc, store, clock, h = make(max_sessions=3)
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1)
        first = signup(svc)
        toks = [first]
        for _ in range(4):
            clock.t += 1; toks.append(login(svc))
        self.assertEqual(len(store.sessions), 3)
        self.assertFalse(svc.whoami(first["session_token"])["ok"])
        self.assertTrue(svc.whoami(toks[-1]["session_token"])["ok"])


class TestLimiterConcurrency(unittest.TestCase):
    def test_parallel_guesses_bounded(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1); signup(svc)
        before = h.derivations
        res = run_threads([lambda: login(svc, "alice", "wrong-password-1", "same") for _ in range(40)])
        derived = h.derivations - before
        self.assertLessEqual(derived, 5)                    # at most MAX_USER_FAILS reach verification
        self.assertGreaterEqual(sum(1 for r in res if r["error"] == "too_many_attempts"), 35)
        self.assertEqual(login(svc)["error"], "too_many_attempts")

    def test_parallel_failures_all_counted(self):
        svc, store, clock, h = make()
        run_threads([lambda i=i: login(svc, "user%02d" % i, "wrong-password-1", "client-x") for i in range(20)])
        a = store.get_attempts(make_key(SECRET, "c", "client-x"))
        self.assertEqual(a["fails"], 20)                    # no lost updates

    def test_success_clears_user_and_refunds_client(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1); signup(svc)
        for _ in range(3): login(svc, "alice", "wrong-password-1")
        self.assertTrue(login(svc)["ok"])
        self.assertIsNone(store.get_attempts(make_key(SECRET, "u-login", "alice")))
        self.assertEqual(store.get_attempts(make_key(SECRET, "c", "c1"))["fails"], 3)

    def test_busy_refunds(self):
        svc, store, clock, h = make(hasher=Hasher(n=2 ** 10, max_concurrent=1))
        svc._dummy  # already computed
        h._sem.acquire()
        self.assertEqual(login(svc, "ghost")["error"], "busy")
        self.assertEqual(store.get_attempts(make_key(SECRET, "u-login", "ghost"))["fails"], 0)

    def test_client_key_required(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 5)
        for bad in ("", None, 5, "x" * 201):
            t, n = pre(svc)
            self.assertEqual(svc.login("alice", PW, t, n, bad, ORIGIN)["error"], "invalid_request")
            self.assertEqual(svc.signup("alice", PW, "invite-code-1", t, n, bad, ORIGIN)["error"], "invalid_request")
        a = signup(svc)
        for bad in ("", None):
            self.assertEqual(svc.delete_account(a["session_token"], a["csrf"], PW, bad, ORIGIN)["error"], "invalid_request")
            self.assertEqual(svc.change_password(a["session_token"], a["csrf"], PW, "x-long-new-pass1", bad, ORIGIN)["error"], "invalid_request")

    def test_purge_removes_expired_attempts_and_sessions(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 5); signup(svc)
        login(svc, "ghost", "wrong-password-1", "cl")
        self.assertTrue(store.attempts)
        clock.t += 31 * 86400; svc.purge()
        self.assertEqual(store.attempts, {}); self.assertEqual(store.sessions, {})


class TestSignupAtomic(unittest.TestCase):
    def test_same_username_one_winner_one_invite_used(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 30)
        res = run_threads([lambda i=i: signup(svc, "alice", client="c%d" % i) for i in range(25)])
        self.assertEqual(sum(1 for r in res if r["ok"]), 1)
        self.assertEqual(store.invites[hash_invite(SECRET, "invite-code-1")], 29)   # losers' invites not burned

    def test_single_use_invite_one_winner(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1)
        res = run_threads([lambda i=i: signup(svc, "user%d" % i, client="c%d" % i) for i in range(20)])
        self.assertEqual(sum(1 for r in res if r["ok"]), 1)
        self.assertEqual(len(store.users), 1)

    def test_user_cap_atomic_and_invite_not_burned_when_full(self):
        svc, store, clock, h = make(max_users=3)
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 100)
        res = run_threads([lambda i=i: signup(svc, "user%d" % i, client="c%d" % i) for i in range(15)])
        self.assertEqual(sum(1 for r in res if r["ok"]), 3)
        self.assertEqual(len(store.users), 3)
        self.assertEqual(store.invites[hash_invite(SECRET, "invite-code-1")], 97)
        self.assertEqual(signup(svc, "late", client="z"), {"ok": False, "error": "signup_failed"})

    def test_weak_password_keeps_invite(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1)
        self.assertEqual(signup(svc, "bob", pw="short")["error"], "weak_password")
        self.assertEqual(store.invites[hash_invite(SECRET, "invite-code-1")], 1)


class TestHashParsing(unittest.TestCase):
    def setUp(self):
        self.h = CountingHasher(n=2 ** 10)
        self.good = self.h.hash(PW)
        self.h.derivations = 0

    def b(self, n): return base64.b64encode(b"a" * n).decode()

    def test_rejects_before_deriving(self):
        salt, dig = self.b(16), self.b(32)
        bads = [
            "scrypt$0,8,1$%s$%s" % (salt, dig), "scrypt$1024,0,1$%s$%s" % (salt, dig),
            "scrypt$1024,8,0$%s$%s" % (salt, dig), "scrypt$1000,8,1$%s$%s" % (salt, dig),   # n not power of two
            "scrypt$%d,8,1$%s$%s" % (2 ** 31, salt, dig), "scrypt$1024,8,99$%s$%s" % (salt, dig),
            "scrypt$1024,8$%s$%s" % (salt, dig), "scrypt$-1024,8,1$%s$%s" % (salt, dig),
            "scrypt$1024,8,1$%s$%s" % (self.b(15), dig), "scrypt$1024,8,1$%s$%s" % (salt, self.b(31)),
            "scrypt$1024,8,1$%s$%s" % ("!!!!", dig), "scrypt$1024,8,1$%s$%s" % (salt, dig + "="),
            "scrypt$1024,8,1$%s$%s$extra" % (salt, dig), "scrypt$1024,8,1$%s" % salt,
            "pbkdf2$10$%s$%s" % (salt, dig), "pbkdf2$99999999$%s$%s" % (salt, dig),
            "pbkdf2$1000,2$%s$%s" % (salt, dig), "md5$1$%s$%s" % (salt, dig),
            "scrypt$1024,8,1$%s$%s" % (salt, "A" * 5000), "scrypt$\u0663,8,1$%s$%s" % (salt, dig),
            "", None, 5, "$" * 4, "scrypt$1024,8,1$%s$%s\n" % (salt, dig),
        ]
        for b in bads:
            self.assertFalse(self.h.verify(PW, b), repr(b))
            self.assertTrue(self.h.needs_rehash(b), repr(b))
        self.assertEqual(self.h.derivations, 0)
        self.assertTrue(self.h.verify(PW, self.good)); self.assertEqual(self.h.derivations, 1)

    def test_pbkdf2_bounds_accept(self):
        salt, dig = self.b(16), self.b(32)
        self.assertIsNotNone(Hasher.parse("pbkdf2$1000$%s$%s" % (salt, dig)))
        self.assertIsNotNone(Hasher.parse("pbkdf2$5000000$%s$%s" % (salt, dig)))
        self.assertIsNone(Hasher.parse("pbkdf2$999$%s$%s" % (salt, dig)))
        self.assertIsNone(Hasher.parse("pbkdf2$5000001$%s$%s" % (salt, dig)))

    def test_raw_length_before_nfkc(self):
        self.assertIsNone(normalize_password("a" * 129))
        self.assertEqual(check_policy("\ufdfa" * 40, "u"), ["too_long"])      # NFKC would expand this hugely
        self.h.derivations = 0
        self.assertFalse(self.h.verify("\ufdfa" * 40, self.good)); self.assertEqual(self.h.derivations, 0)


class TestTimingAndBounds(unittest.TestCase):
    def test_dummy_precomputed_and_equal_derivations(self):
        h = CountingHasher(n=2 ** 10, max_concurrent=64)
        self.assertEqual(h.derivations, 0)
        svc, store, clock, _ = make(hasher=h)
        self.assertEqual(h.derivations, 1)                  # dummy hash done at construction
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1); signup(svc)
        base = h.derivations
        login(svc, "ghost", "wrong-password-1"); unknown = h.derivations - base
        base = h.derivations
        login(svc, "alice", "wrong-password-1"); known = h.derivations - base
        self.assertEqual((unknown, known), (1, 1))          # same work for unknown and known users

    def test_oversize_password_everywhere(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 5)
        a = signup(svc)
        big = "a" * 129
        base = h.derivations
        self.assertEqual(login(svc, "alice", big)["error"], "invalid_credentials")
        self.assertEqual(svc.delete_account(a["session_token"], a["csrf"], big, "c1", ORIGIN)["error"], "invalid_credentials")
        self.assertEqual(svc.change_password(a["session_token"], a["csrf"], big, "a-brand-new-passphrase", "c1", ORIGIN)["error"], "invalid_credentials")
        self.assertEqual(signup(svc, "bob", pw=big)["error"], "weak_password")
        self.assertEqual(h.derivations, base)               # no derivation for any oversize input
        self.assertEqual(signup(svc, "carol", pw="\ufdfa" * 40)["error"], "weak_password")

    def test_label_bounds_before_processing(self):
        for bad in ("a" * 10_000_000, " " * 5_000, "x" * 1000):
            with self.assertRaises(ValueError): V.clean_label(bad, 80)
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1); a = signup(svc)
        r = svc.save_settings(a["session_token"], a["csrf"], [], ["a" * 5_000_000], 0, ORIGIN)
        self.assertEqual(r["error"], "invalid_settings")
        r = svc.save_settings(a["session_token"], a["csrf"], [{"name": "n" * 5_000_000, "video": "abcdefghijk"}], [], 0, ORIGIN)
        self.assertEqual(r["error"], "invalid_settings")

    def test_21_displayed_channels(self):
        svc, store, clock, h = make()
        store.add_invite(hash_invite(SECRET, "invite-code-1"), 1); a = signup(svc)
        ch = [{"name": "c%d" % i, "video": "%011d" % i} for i in range(20)]
        r = svc.save_settings(a["session_token"], a["csrf"], ch, [], 0, ORIGIN)
        self.assertTrue(r["ok"]); self.assertEqual(len(r["settings"]["channels"]), 21)     # 20 extras + Republic
        r = svc.save_settings(a["session_token"], a["csrf"], ch + [{"name": "c20", "video": "%011d" % 20}], [], 1, ORIGIN)
        self.assertEqual(r["error"], "invalid_settings")


class GatedHasher(Hasher):
    def __init__(self):
        super().__init__(n=1024, max_concurrent=64)
        self.enter, self.release, self.gate = threading.Event(), threading.Event(), None
    def hash(self, pw):
        if pw == self.gate:
            self.enter.set(); assert self.release.wait(10)
        return super().hash(pw)


def open_make(h=None):
    clock, store = Clock(), MemoryStore()
    h = h or GatedHasher()
    return AccountService(store, SECRET, clock, hasher=h, signup_mode="open", allowed_origins=[ORIGIN]), store, clock, h


def post(s, fn, *a, client="one"):
    p = s.issue_preauth(); return getattr(s, fn)(*a, p["csrf"], p["nonce"], client, ORIGIN)


class TestFence(unittest.TestCase):
    def test_pending_password_change_fenced_by_revoked_session(self):
        s, st, c, h = open_make()
        a = post(s, "signup", "alice", PW, None); b = post(s, "login", "alice", PW)
        late, recent = "late password overwrite", "newly secure password"
        h.gate = late; out = {}
        t = threading.Thread(target=lambda: out.update(s.change_password(a["session_token"], a["csrf"], PW, late, "one", ORIGIN)))
        t.start(); self.assertTrue(h.enter.wait(5))
        self.assertTrue(s.change_password(b["session_token"], b["csrf"], PW, recent, "two", ORIGIN)["ok"])
        h.release.set(); t.join()
        self.assertEqual(out["error"], "unauthenticated")
        self.assertTrue(h.verify(recent, st.get_user("alice")["password"]))
        self.assertFalse(h.verify(late, st.get_user("alice")["password"]))
        self.assertTrue(s.whoami(b["session_token"])["ok"])

    def test_pending_delete_fenced_after_rotation(self):
        s, st, c, h = open_make()
        a = post(s, "signup", "alice", PW, None); b = post(s, "login", "alice", PW)
        entered, release, orig, out = threading.Event(), threading.Event(), st.delete_account, {}
        def paused(*args):
            entered.set(); assert release.wait(10); return orig(*args)
        st.delete_account = paused
        t = threading.Thread(target=lambda: out.update(s.delete_account(a["session_token"], a["csrf"], PW, "one", ORIGIN)))
        t.start(); self.assertTrue(entered.wait(5))
        self.assertTrue(s.change_password(b["session_token"], b["csrf"], PW, "newly secure password", "two", ORIGIN)["ok"])
        release.set(); t.join()
        self.assertEqual(out["error"], "unauthenticated")
        self.assertIsNotNone(st.get_user("alice"))

    def test_pending_delete_fenced_by_pwv_alone(self):
        s, st, c, h = open_make()
        a = post(s, "signup", "alice", PW, None)
        u = st.get_user("alice"); sess = next(iter(st.sessions))
        self.assertTrue(st.replace_password(u["uid"], 0, "x", sess, c()))          # pwv now 1, session kept
        self.assertFalse(st.delete_account("alice", u["uid"], 0, sess, c()))        # stale pwv
        self.assertFalse(st.replace_password(u["uid"], 0, "y", sess, c()))
        self.assertFalse(st.delete_account("alice", u["uid"], 1, "nosuchsession", c()))
        self.assertFalse(st.put_settings(u["uid"], {"version": 1}, 0, "nosuchsession", c()))

    def test_settings_write_fenced_by_session(self):
        s, st, c, h = open_make()
        a = post(s, "signup", "alice", PW, None); b = post(s, "login", "alice", PW)
        u = st.get_user("alice"); sess = next(h2 for h2, x in st.sessions.items())
        s.logout(a["session_token"], a["csrf"], ORIGIN)
        self.assertFalse(st.put_settings(u["uid"], {"version": 1, "channels": [], "watchlist": []}, 0, sess, c()))
        self.assertEqual(st.settings, {})
        c.t += 40 * 86400
        self.assertFalse(st.put_settings(u["uid"], {"version": 1}, 0, next(iter(st.sessions)), c()))   # expired session


class TestOperationKeys(unittest.TestCase):
    def test_closed_signup_does_not_lock_login_or_reserve(self):
        s, st, c, h = open_make()
        post(s, "signup", "alice", PW, None, client="victim"); s.mode = "closed"; before = dict(st.attempts)
        for _ in range(8): self.assertEqual(post(s, "signup", "alice", PW, None, client="attacker")["error"], "signup_failed")
        self.assertEqual(st.attempts, before)                      # nothing reserved by closed-mode refusals
        self.assertTrue(post(s, "login", "alice", PW, client="victim")["ok"])

    def test_signup_failures_do_not_lock_login(self):
        s, st, c, h = open_make(); s.mode = "invite"
        post(s, "signup", "bob", PW, "invite-code-x")                # fails (no such invite, account missing)
        s.mode = "open"; post(s, "signup", "alice", PW, None, client="v")
        s.mode = "invite"
        for i in range(8): post(s, "signup", "alice", PW, "bad-invite-code", client="att%d" % i)
        self.assertTrue(post(s, "login", "alice", PW, client="v")["ok"])

    def test_login_failures_do_not_lock_signup_key_and_reauth_shares_login_key(self):
        s, st, c, h = open_make()
        a = post(s, "signup", "alice", PW, None)
        for i in range(5): s.delete_account(a["session_token"], a["csrf"], "wrong-password-1", "r%d" % i, ORIGIN)
        self.assertEqual(post(s, "login", "alice", PW, client="z")["error"], "too_many_attempts")   # shared login key (deliberate)
        self.assertEqual(s.limiter.begin("signup", "alice", "zz")[1], 0)


class TestSurrogates(unittest.TestCase):
    BAD = ["strong passphrase\ud800", "\udfff" * 12, "ok-password-\udc00-1"]

    def test_no_crash_any_entry_point(self):
        s, st, c, h = open_make(); s.mode = "invite"
        st.add_invite(hash_invite(SECRET, "invite-code-1"), 5)
        for bad in self.BAD:
            r = post(s, "signup", "alice", bad, "invite-code-1"); self.assertEqual(r["error"], "weak_password")
            self.assertEqual(r["problems"], ["bad_characters"])
            self.assertEqual(post(s, "login", "ghost", bad)["error"], "invalid_credentials")
            self.assertEqual(post(s, "signup", "alice", PW, "invite\ud800-code")["error"], "signup_failed")
            self.assertEqual(post(s, "login", "ghost", "bad password", client="\ud800")["error"], "invalid_request")
            self.assertEqual(post(s, "signup", "ghost", PW, "invite-code-1", client="\ud800")["error"], "invalid_request")
            self.assertEqual(post(s, "login", "gh\ud800st", "bad password")["error"], "invalid_credentials")
        a = post(s, "signup", "alice", PW, "invite-code-1")
        self.assertTrue(a["ok"])
        for bad in self.BAD:
            st.attempts.clear()
            self.assertEqual(s.change_password(a["session_token"], a["csrf"], PW, bad, "one", ORIGIN)["error"], "weak_password")
            self.assertEqual(s.change_password(a["session_token"], a["csrf"], bad, "a-brand-new-passphrase", "one", ORIGIN)["error"], "invalid_credentials")
            self.assertEqual(s.delete_account(a["session_token"], a["csrf"], bad, "one", ORIGIN)["error"], "invalid_credentials")
        for bad in ("\ud800", "ab\ud800" * 10, None):
            self.assertFalse(s.whoami(bad)["ok"])
        for bad_label in ("name\ud800", "\ud800"):
            self.assertEqual(s.save_settings(a["session_token"], a["csrf"], [{"name": bad_label, "video": "abcdefghijk"}], [], 0, ORIGIN)["error"], "invalid_settings")
            self.assertEqual(s.save_settings(a["session_token"], a["csrf"], [], [bad_label], 0, ORIGIN)["error"], "invalid_settings")
        self.assertEqual(s.save_settings(a["session_token"], a["csrf"], [{"name": "x", "video": "abcdefghi\ud800k"}], [], 0, ORIGIN)["error"], "invalid_settings")
        self.assertEqual(post(s, "login", "alice", PW)["ok"], True)

    def test_other_invisible_rejected(self):
        for bad in ("pass\u200bphrase-long-1", "pass\u0000phrase-long-1", "pass\u2028phrase-long-1", "pass\ue000phrase-long-1"):
            self.assertEqual(check_policy(bad, "u"), ["bad_characters"], repr(bad))
        self.assertEqual(check_policy("normal passphrase ok", "u"), [])      # ordinary space allowed

    def test_client_and_invite_charset(self):
        s, st, c, h = open_make()
        for bad in ("a b", "a\n", "\u00e9", "x" * 201, ""):
            self.assertFalse(s._client_ok(bad), repr(bad))
        self.assertTrue(s._client_ok("203.0.113.9"))


class TestGeneration(unittest.TestCase):
    def test_stale_refund_ignored_in_new_window(self):
        from integration.accounts.limiter import Limiter, WINDOW
        st, c = MemoryStore(), Clock(); lim = Limiter(st, SECRET, c)
        old, w = lim.begin("login", "alice", "one"); self.assertFalse(w)
        c.t += WINDOW + 1
        for _ in range(5):
            tok, w = lim.begin("login", "alice", "one"); self.assertFalse(w)
        lim.refund(old)                                            # stale generation: no effect
        _, w = lim.begin("login", "alice", "one")
        self.assertGreater(w, 0)                                   # 6th attempt in the fresh window is locked out
        self.assertEqual(st.get_attempts(lim.user_key("login", "alice"))["locks"], 1)

    def test_stale_success_does_not_clear_new_window(self):
        from integration.accounts.limiter import Limiter, WINDOW
        st, c = MemoryStore(), Clock(); lim = Limiter(st, SECRET, c)
        old, _ = lim.begin("login", "alice", "one"); c.t += WINDOW + 1
        for _ in range(3): lim.begin("login", "alice", "one")
        lim.success(old)
        self.assertEqual(st.get_attempts(lim.user_key("login", "alice"))["fails"], 3)

    def test_same_generation_refund_works(self):
        from integration.accounts.limiter import Limiter
        st, c = MemoryStore(), Clock(); lim = Limiter(st, SECRET, c)
        r, _ = lim.begin("login", "alice", "one"); lim.refund(r)
        self.assertEqual(st.get_attempts(lim.user_key("login", "alice"))["fails"], 0)


class TestTimingParams(unittest.TestCase):
    def test_dummy_uses_current_params_and_follows_changes(self):
        h = CountingHasher(n=2 ** 10)
        s, st, c, _ = make(hasher=h)
        self.assertFalse(h.needs_rehash(s._dummy))
        h.n = 2 ** 11                                              # parameters upgraded
        before = h.derivations
        s._dummy_hash(); self.assertEqual(h.derivations, before + 1); self.assertFalse(h.needs_rehash(s._dummy))
        s._dummy_hash(); self.assertEqual(h.derivations, before + 1)

    def test_rehash_on_login_upgrades_legacy(self):
        h = CountingHasher(n=2 ** 10); s, st, c, _ = make(hasher=h)
        st.add_invite(hash_invite(SECRET, "invite-code-1"), 1); signup(s)
        st.users["alice"]["password"] = Hasher(n=2 ** 11).hash(PW)
        self.assertTrue(h.needs_rehash(st.users["alice"]["password"]))
        self.assertTrue(login(s)["ok"]); self.assertFalse(h.needs_rehash(st.users["alice"]["password"]))


if __name__ == "__main__":
    unittest.main()
