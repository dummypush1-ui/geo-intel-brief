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
import copy, threading


class AccountStore:
    def create_account(self, username, record, invite_hash, max_users): raise NotImplementedError   # -> ok|taken|invite|cap
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
    def add_invite(self, code_hash, uses=1): raise NotImplementedError
    def get_settings(self, uid): raise NotImplementedError
    def put_settings(self, uid, doc, expected_version, session_hash, now): raise NotImplementedError  # -> bool (fenced)
    def purge(self, now): raise NotImplementedError


class MemoryStore(AccountStore):
    def __init__(self):
        self._l = threading.RLock()
        self.users, self.by_uid, self.sessions, self.attempts = {}, {}, {}, {}
        self.invites, self.settings = {}, {}

    def create_account(self, username, record, invite_hash, max_users):
        with self._l:
            if username in self.users:
                return "taken"
            if invite_hash is not None and self.invites.get(invite_hash, 0) <= 0:
                return "invite"
            if len(self.users) >= max_users:
                return "cap"
            if invite_hash is not None:
                self.invites[invite_hash] -= 1
            rec = copy.deepcopy(record)
            rec["username"] = username
            self.users[username] = rec
            self.by_uid[rec["uid"]] = username
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

    def add_invite(self, code_hash, uses=1):
        with self._l:
            self.invites[code_hash] = int(uses)

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
        with self._l:
            for h in [h for h, s in self.sessions.items() if s["expires"] <= now or s["idle_expires"] <= now]:
                del self.sessions[h]
            for k in [k for k, a in self.attempts.items() if a.get("expires", 0) <= now]:
                del self.attempts[k]
