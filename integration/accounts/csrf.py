# Copyright (c) 2026 Push
"""CSRF tokens (HMAC, no storage), pre-auth nonce binding and Origin check.
All token formats are bounded ASCII and validated before any comparison."""
import hashlib, hmac, re

LOGIN_BUCKET = 3600
_NONCE = re.compile(r"^[0-9a-f]{32}$")
_LOGIN = re.compile(r"^([0-9]{1,12})\.([0-9a-f]{64})$")
_SESSION = re.compile(r"^[0-9a-f]{64}$")


def _mac(secret, msg):
    return hmac.new(secret, msg.encode("ascii"), hashlib.sha256).hexdigest()


def nonce_ok(nonce):
    return isinstance(nonce, str) and len(nonce) == 32 and bool(_NONCE.fullmatch(nonce))


def session_token(secret, session_hash):
    return _mac(secret, "csrf-session:" + session_hash)


def login_token(secret, now, nonce):
    """Bound to a pre-auth cookie nonce so one token cannot be shared across browsers."""
    if not nonce_ok(nonce):
        raise ValueError("nonce")
    b = int(now // LOGIN_BUCKET)
    return "%d.%s" % (b, _mac(secret, "csrf-login:%d:%s" % (b, nonce)))


def verify_login_token(secret, token, now, nonce):
    if not nonce_ok(nonce) or not isinstance(token, str) or len(token) > 80 or not token.isascii():
        return False
    m = _LOGIN.fullmatch(token)
    if not m:
        return False
    cur = int(now // LOGIN_BUCKET)
    b = int(m.group(1))
    if b not in (cur, cur - 1):
        return False
    return hmac.compare_digest(m.group(2), _mac(secret, "csrf-login:%d:%s" % (b, nonce)))


def verify_session_token(secret, session_hash, token):
    if not isinstance(token, str) or len(token) != 64 or not token.isascii() or not _SESSION.fullmatch(token):
        return False
    return hmac.compare_digest(token, session_token(secret, session_hash))


def origin_ok(origin, allowed, require=True):
    """Present Origin must match exactly. Absent Origin is refused when require=True (default)."""
    if origin is None:
        return not require
    return isinstance(origin, str) and origin in allowed
