# Copyright (c) 2026 Push
"""Store interface (injected) and an in-memory reference implementation.
No real database client is created anywhere in this package.

ATOMICITY CONTRACT. Every method below must be atomic with respect to every other (a real adapter
uses transactions or conditional/compare-and-set updates). The service relies on it for:
- create_account: username, user cap and invite are claimed together or not at all.
- create_session / touch_session: a session can only be created or refreshed while its account
  (matched by immutable uid, plus password version pwv at creation) is live. No unconditional upsert.
- FENCE: delete_account, replace_password and put_settings commit only if, in the same atomic step, the
  account uid is live, the calling session (hash) is live, unexpired and belongs to that uid, and (for
  delete/replace_password) the password version equals the pwv observed when the password was verified.
  A request whose session was revoked or whose password changed meanwhile fails, whatever it paused on.
- delete_account / replace_password also remove or revoke the account's sessions in the same operation.
- put_settings: compare-and-set on version as well.
- update_attempts: read-modify-write of one limiter record (CAS retry loop in a real adapter)."""
import copy, threading, math

def epoch(value):
    if type(value) not in (int,float) or not 0<=value<=4133980799.999999 or not math.isfinite(value): raise ValueError("Invalid epoch")
    return value

def invite_value(value):
    if type(value) is int and 0<=value<=1000:return value
    if type(value) is dict and len(value)==2 and all(type(k) is str for k in value) and set(value)=={"uses","expires_at"} and type(value["uses"]) is int and 0<=value["uses"]<=1000:
        return {"uses":value["uses"],"expires_at":epoch(value["expires_at"])}
    raise ValueError("Invalid invite state")

def account_record(record):
    if type(record) is not dict or len(record)>5 or any(type(k) is not str for k in record) or not {"uid","password","pwv"}<=set(record) or set(record)-{"uid","password","pwv","created","username"}:raise ValueError("Invalid account")
    if any(type(record[k]) is not str or not 1<=len(record[k])<=512 for k in ("uid","password")) or type(record["pwv"]) is not int or not 0<=record["pwv"]<2**53:raise ValueError("Invalid account")
    if "created" in record:epoch(record["created"])
    if "username" in record and (type(record["username"]) is not str or len(record["username"])>128):raise ValueError("Invalid account")
    return dict(record)


class AccountStore:
    def create_account(self, username, record, invite_hash, max_users, now=None): raise NotImplementedError   # -> ok|taken|invite|cap
    def get_user(self, username): raise NotImplementedError
    def delete_account(self, username, uid, pwv, session_hash, now): raise NotImplementedError      # -> bool (fenced)
    def replace_password(self, uid, pwv, new_hash, session_hash, now): raise NotImplementedError    # -> bool (fenced)
    def rehash_password(self, uid, pwv, new_hash): raise NotImplementedError                          # -> bool
    def create_session(self, token_hash, record, uid, pwv, max_sessions): raise NotImplementedError  # -> bool
    def touch_session(self, token_hash, now, idle_ttl): raise NotImplementedError                     # -> record|None
    def delete_session(self, token_hash): raise NotImplementedError
    def update_attempts(self, key, fn): raise NotImplementedError
    def get_attempts(self, key): raise NotImplementedError
    def delete_attempts(self, key): raise NotImplementedError
    def add_invite(self, code_hash, uses=1, expires_at=None): raise NotImplementedError
    def get_settings(self, uid): raise NotImplementedError
    def put_settings(self, uid, doc, expected_version, session_hash, now): raise NotImplementedError  # -> bool (fenced)
    def purge(self, now): raise NotImplementedError


class MemoryStore(AccountStore):
    def __init__(self):
        self._l = threading.RLock()
        self.users, self.by_uid, self.sessions, self.attempts = {}, {}, {}, {}
        self.invites, self.settings = {}, {}

    def create_account(self, username, record, invite_hash, max_users, now=None):
        # Authorization is at supplied post-hash admission time, NOT commit time.
        rec=account_record(record)
        if type(username) is not str or not 1<=len(username)<=128 or type(max_users) is not int or not 0<=max_users<=10000:raise ValueError("Invalid claim")
        if invite_hash is not None and (type(invite_hash) is not str or not 1<=len(invite_hash)<=512):raise ValueError("Invalid claim")
        with self._l:
            value=invite_value(self.invites[invite_hash]) if invite_hash in self.invites else None
            if type(value) is dict:epoch(now)
            if username in self.users:return "taken"
            if invite_hash is not None and (value is None or (value if type(value) is int else value['uses'])<=0 or type(value) is dict and value['expires_at']<=now):return "invite"
            if len(self.users)>=max_users:return "cap"
            if rec['uid'] in self.by_uid:raise ValueError("Duplicate account identity")
            rec['username']=username
            # All potentially failing caller validation/copy completed above.
            if invite_hash is not None:
                self.invites[invite_hash]=value-1 if type(value) is int else dict(value,uses=value['uses']-1)
            self.users[username]=rec
            self.by_uid[rec['uid']]=username
            return "ok"

    def get_user(self, username):
        with self._l:
            return copy.deepcopy(self.users.get(username))

    def _live(self, uid):
        n = self.by_uid.get(uid)
        return self.users.get(n) if n else None

    def _fence(self, uid, session_hash, now, pwv=None):
        u = self._live(uid)
        ss = self.sessions.get(session_hash)
        if (not u or not ss or ss["uid"] != uid or ss["expires"] <= now or ss["idle_expires"] <= now
                or (pwv is not None and u["pwv"] != pwv)):
            return None
        return u

    def delete_account(self, username, uid, pwv, session_hash, now):
        with self._l:
            u = self._fence(uid, session_hash, now, pwv)
            if not u or u["username"] != username:
                return False
            del self.users[username]
            self.by_uid.pop(uid, None)
            self.settings.pop(uid, None)
            for h in [h for h, s in self.sessions.items() if s["uid"] == uid]:
                del self.sessions[h]
            return True

    def replace_password(self, uid, pwv, new_hash, session_hash, now):
        with self._l:
            u = self._fence(uid, session_hash, now, pwv)
            if not u:
                return False
            u["password"], u["pwv"] = new_hash, u["pwv"] + 1
            for h in [h for h, s in self.sessions.items() if s["uid"] == uid and h != session_hash]:
                del self.sessions[h]
            return True

    def rehash_password(self, uid, pwv, new_hash):
        with self._l:
            u = self._live(uid)
            if not u or u["pwv"] != pwv:
                return False
            u["password"] = new_hash
            return True

    def create_session(self, token_hash, record, uid, pwv, max_sessions):
        with self._l:
            u = self._live(uid)
            if not u or u["pwv"] != pwv or record.get("uid") != uid:
                return False
            mine = sorted((s["created"], h) for h, s in self.sessions.items() if s["uid"] == uid)
            while len(mine) >= max_sessions:
                del self.sessions[mine.pop(0)[1]]
            self.sessions[token_hash] = copy.deepcopy(record)
            return True

    def touch_session(self, token_hash, now, idle_ttl):
        with self._l:
            s = self.sessions.get(token_hash)
            if not s:
                return None
            u = self._live(s["uid"])
            if not u or s["expires"] <= now or s["idle_expires"] <= now:
                del self.sessions[token_hash]
                return None
            s["idle_expires"] = min(s["expires"], now + idle_ttl)
            return copy.deepcopy(s)

    def delete_session(self, token_hash):
        with self._l:
            self.sessions.pop(token_hash, None)

    def update_attempts(self, key, fn):
        with self._l:
            new = fn(copy.deepcopy(self.attempts.get(key)))
            if new is None:
                self.attempts.pop(key, None)
            else:
                self.attempts[key] = new

    def get_attempts(self, key):
        with self._l:
            return copy.deepcopy(self.attempts.get(key))

    def delete_attempts(self, key):
        with self._l:
            self.attempts.pop(key, None)

    def add_invite(self, code_hash, uses=1, expires_at=None):
        if type(code_hash) is not str or not 1<=len(code_hash)<=512 or type(uses) is not int or not 1<=uses<=1000:raise ValueError("Invalid invite")
        value=uses if expires_at is None else {'uses':uses,'expires_at':epoch(expires_at)}
        with self._l:
            if code_hash not in self.invites and len(self.invites)>=1000:raise ValueError("Invite capacity")
            self.invites[code_hash]=value

    def get_settings(self, uid):
        with self._l:
            return copy.deepcopy(self.settings.get(uid))

    def put_settings(self, uid, doc, expected_version, session_hash, now):
        with self._l:
            if not self._fence(uid, session_hash, now):
                return False
            cur = self.settings.get(uid)
            if (cur["version"] if cur else 0) != expected_version:
                return False
            self.settings[uid] = copy.deepcopy(doc)
            return True

    def purge(self, now):
        epoch(now)
        with self._l:
            captured={k:invite_value(v) for k,v in self.invites.items()}
            for k,v in captured.items():
                if type(v) is dict and v["expires_at"]<=now:self.invites.pop(k,None)
            for h in [h for h, s in self.sessions.items() if s["expires"] <= now or s["idle_expires"] <= now]:
                del self.sessions[h]
            for k in [k for k, a in self.attempts.items() if a.get("expires", 0) <= now]:
                del self.attempts[k]
