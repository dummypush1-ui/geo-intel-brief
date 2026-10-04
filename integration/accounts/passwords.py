# Copyright (c) 2026 Push
"""Password policy and hashing (stdlib scrypt, PBKDF2 fallback)."""
import base64, hashlib, hmac, os, re, threading, unicodedata

MIN_LEN, MAX_LEN = 10, 128
USERNAME_RE = re.compile(r"^[a-z0-9_-]{3,32}$")
_PARAMS_RE = re.compile(r"^[0-9]{1,8}(,[0-9]{1,8}){0,2}$")
_BAD_CATEGORIES = frozenset(("Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"))   # control, format/invisible, surrogate, private, unassigned, line/para sep


def has_bad_chars(text):
    return any(unicodedata.category(c) in _BAD_CATEGORIES for c in text)


def printable_ascii(value, lo, hi):
    """Bounded printable-ASCII token (client keys, invite codes). Never raises."""
    return (isinstance(value, str) and lo <= len(value) <= hi and value.isascii()
            and all(0x21 <= ord(c) <= 0x7e for c in value))
_COMMON = frozenset("""password1234 passwordpassword 1234567890 12345678910 qwertyuiop
qwerty123456 iloveyou123 letmein1234 welcome1234 admin12345 changeme123 abc1234567
1q2w3e4r5t 0123456789 password123 11111111111 123456789012""".split())


class Busy(Exception):
    """Too many concurrent hash operations."""


def normalize_username(value):
    if not isinstance(value, str) or len(value) > 64:
        return None
    v = unicodedata.normalize("NFKC", value).strip().lower()
    return v if USERNAME_RE.fullmatch(v) else None


def normalize_password(value):
    """Raw length is bounded BEFORE normalisation (NFKC can expand strings)."""
    if not isinstance(value, str) or len(value) > MAX_LEN or has_bad_chars(value):
        return None                                   # also rejects lone surrogates (not UTF-8 encodable)
    v = unicodedata.normalize("NFKC", value)
    return v if len(v) <= MAX_LEN else None          # NFKC can expand: bound again afterwards


def check_policy(password, username=""):
    """Return list of problem codes (empty = acceptable)."""
    if not isinstance(password, str):
        return ["invalid"]
    if len(password) > MAX_LEN:
        return ["too_long"]
    if has_bad_chars(password):
        return ["bad_characters"]
    if len(unicodedata.normalize("NFKC", password)) > MAX_LEN:
        return ["too_long"]
    p = normalize_password(password)
    if p is None:
        return ["invalid"]
    out = []
    if len(p) < MIN_LEN:
        out.append("too_short")
    if len(p) > MAX_LEN:
        out.append("too_long")
    if has_bad_chars(p):
        out.append("bad_characters")
    low = p.lower()
    if low in _COMMON or len(set(low)) < 4:
        out.append("too_common")
    if username and username in low:
        out.append("contains_username")
    return out


class Hasher:
    """scrypt with per-user salt; params are stored in the hash string."""

    def __init__(self, n=2 ** 15, r=8, p=1, max_concurrent=4, pbkdf2_iters=600_000):
        self.n, self.r, self.p, self.iters = n, r, p, pbkdf2_iters
        self._sem = threading.BoundedSemaphore(max_concurrent)
        self._has_scrypt = hasattr(hashlib, "scrypt")

    def _derive(self, algo, params, salt, pw):
        data = pw.encode("utf-8")
        if algo == "scrypt":
            n, r, p = params
            return hashlib.scrypt(data, salt=salt, n=n, r=r, p=p,
                                  maxmem=128 * n * r * 2 + (1 << 20), dklen=32)
        if algo == "pbkdf2":
            return hashlib.pbkdf2_hmac("sha256", data, salt, params[0], 32)
        raise ValueError("algo")

    def _run(self, algo, params, salt, pw):
        if not self._sem.acquire(blocking=False):
            raise Busy()
        try:
            return self._derive(algo, params, salt, pw)
        finally:
            self._sem.release()

    def hash(self, password):
        pw = normalize_password(password)
        salt = os.urandom(16)
        if self._has_scrypt:
            algo, params = "scrypt", (self.n, self.r, self.p)
        else:
            algo, params = "pbkdf2", (self.iters,)
        dk = self._run(algo, params, salt, pw)
        b = lambda x: base64.b64encode(x).decode()
        return "$".join([algo, ",".join(map(str, params)), b(salt), b(dk)])

    @staticmethod
    def parse(stored):
        """Strictly validate a stored hash BEFORE any derivation. Returns (algo, params, salt, digest) or None."""
        if not isinstance(stored, str) or len(stored) > 200 or not stored.isascii():
            return None
        parts = stored.split("$")
        if len(parts) != 4:
            return None
        algo, ps, s, d = parts
        if not _PARAMS_RE.fullmatch(ps):
            return None
        params = tuple(int(x) for x in ps.split(","))
        try:
            salt = base64.b64decode(s, validate=True)
            dig = base64.b64decode(d, validate=True)
        except Exception:
            return None
        if len(salt) != 16 or len(dig) != 32:
            return None
        if base64.b64encode(salt).decode() != s or base64.b64encode(dig).decode() != d:
            return None                              # canonical base64 only
        if algo == "scrypt":
            if len(params) != 3:
                return None
            n, r, p = params
            if not (2 ** 10 <= n <= 2 ** 17 and n & (n - 1) == 0 and 1 <= r <= 16 and 1 <= p <= 4):
                return None
        elif algo == "pbkdf2":
            if len(params) != 1 or not 1000 <= params[0] <= 5_000_000:
                return None
        else:
            return None
        return algo, params, salt, dig

    def verify(self, password, stored):
        """Constant-time compare. Malformed stored value or oversize password -> False (no derivation)."""
        pw = normalize_password(password)
        parsed = self.parse(stored)
        if pw is None or parsed is None:
            return False
        algo, params, salt, want = parsed
        got = self._run(algo, params, salt, pw)     # Busy propagates
        return hmac.compare_digest(got, want)

    def needs_rehash(self, stored):
        parsed = self.parse(stored)
        if parsed is None:
            return True
        algo, params = parsed[0], parsed[1]
        want = ("scrypt", (self.n, self.r, self.p)) if self._has_scrypt else ("pbkdf2", (self.iters,))
        return (algo, params) != want
