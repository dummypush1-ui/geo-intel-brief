# Copyright (c) 2026 Push
"""Attempt limiting with reserve-then-refund semantics.

begin() atomically counts the attempt BEFORE the password is checked, so concurrent guesses cannot
all pass a stale check: at most `limit` attempts per window reach verification.
Keys are HMACs; unknown usernames are counted exactly like known ones (no enumeration).
Per-user keys are operation-specific ("login" also covers password re-entry for change/delete;
"signup" is separate), so one operation cannot lock another. The client key is shared and is the main brake.
Each record carries a generation id; a refund or clear from an older generation is ignored.
Requires exactly ONE Limiter instance per store. Multiple instances/workers
are unsupported: compensation retry marker can erase unrelated failures.
Requires store.update_attempts(key, fn): atomic read-modify-write (adapters use compare-and-set)."""
import hashlib, hmac, secrets, threading
from dataclasses import dataclass
from collections import deque

@dataclass(frozen=True,slots=True,eq=False)
class Reservation:
    owner: str
    token: str
    def __init_subclass__(cls,**kwargs): raise TypeError("sealed reservation")
    def __copy__(self): raise TypeError("reservation cannot be copied")
    def __deepcopy__(self,memo): raise TypeError("reservation cannot be copied")
    def __reduce__(self): raise TypeError("reservation cannot be serialized")
    def __reduce_ex__(self,protocol): raise TypeError("reservation cannot be serialized")

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
        self._reservation_lock = threading.RLock()
        self._outstanding = {}
        self._prune_queue = deque()
        self._reservation_owner=secrets.token_hex(24)
        self._reservation_cap = 1024
        self._begin_active = False
        self._finish_depth = 0

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

    def _drop(self,token):
        state=self._outstanding.pop(token,None)
        if state is None:return
        try:self._prune_queue.remove(token)
        except ValueError:pass
    def _prune(self):
        now=self.clock()
        # Fixed work budget, two record reads per inspected live reservation.
        for _ in range(min(4,len(self._prune_queue))):
            token=self._prune_queue.popleft();state=self._outstanding.get(token)
            if state is None:continue
            pairs=state[1:]
            records=[self.store.get_attempts(key) for key,gen in pairs]
            if all(a is None or a.get("gen")!=gen or a.get("expires",0)<=now for a,(_,gen) in zip(records,pairs)):self._drop(token)
            else:self._prune_queue.append(token)

    def begin(self,op,username,client):
        with self._reservation_lock:
            # Reject callback-nested admission, including during prune reads.
            if self._begin_active or self._finish_depth:raise RuntimeError("nested limiter begin prohibited")
            self._begin_active=True
            try:
                self._prune()
                if len(self._outstanding)>=self._reservation_cap:return None,1
                result,wait=self._begin(op,username,client)
                return result,wait
            finally:
                self._begin_active=False

    def _begin(self, op, username, client):
        """Reserve one attempt. Returns (reservation, wait_seconds); wait > 0 means denied."""
        taken, wait = [], 0
        def compensate(pair):
            key,gen,marker=pair
            def fn(a):
                if a and a.get("gen")==gen and marker != a.get("rollback_id"):
                    a["fails"]=max(0,a["fails"]-1)
                    # Idempotent retry if store commits then raises. Kept to end
                    # of the next compensation. Admission is non-reentrant.
                    a["rollback_id"]=marker
                return a
            self.store.update_attempts(key,fn)
        try:
            for key, limit in ((self.user_key(op, username), self.max_user), (self.client_key(client), self.max_client)):
                w, gen = self._count(key, limit)
                if w:wait=max(wait,w)
                else:taken.append((key,gen,secrets.token_hex(24)))
            if wait:
                while taken:
                    compensate(taken[-1]);taken.pop()
                return None,wait
        except BaseException:
            # Best effort if the store is down; never replace original error.
            for pair in reversed(taken):
                try:compensate(pair)
                except BaseException:pass
            raise
        taken=[(key,gen) for key,gen,marker in taken]
        token=secrets.token_hex(24)
        while token in self._outstanding:token=secrets.token_hex(24)
        res=Reservation(self._reservation_owner,token);self._outstanding[token]=(res,taken[0],taken[1])
        self._prune_queue.append(token)
        return res,0

    def _finish(self,res,success):
        # In-process only. Authoritative issued-instance identity, not caller fields.
        if type(res) is not Reservation or res.owner!=self._reservation_owner:raise TypeError("issued reservation required")
        with self._reservation_lock:
            if self._begin_active:raise RuntimeError("finish during begin prohibited")
            issued=self._outstanding.get(res.token)
            if issued is None:return
            if issued[0] is not res:raise TypeError("issued reservation required")
            self._finish_depth+=1
            try:
                self._drop(res.token)
                if success is None:return
                pairs=issued[1:]
                records=[self.store.get_attempts(key) for key,gen in pairs]
                # Each side settles its own still-current generation independently.
                # Token was consumed before callbacks, so each side is at-most-once.
                user_current=records[0] is not None and records[0].get("gen")==pairs[0][1]
                client_current=records[1] is not None and records[1].get("gen")==pairs[1][1]
                if user_current:
                    if success:self._clear(*pairs[0])
                    else:self._refund(*pairs[0])
                if client_current:self._refund(*pairs[1])
                self._prune()
            finally:
                self._finish_depth-=1

    def success(self,res):
        self._finish(res,True)

    def refund(self,res):
        self._finish(res,False)

    def fail(self,res):
        """Terminal credentials failure: consume reservation, retain counts."""
        self._finish(res,None)
