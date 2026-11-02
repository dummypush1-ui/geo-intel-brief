"""One shared guard for every trigger / admin route (/brics/*, /geo/*)."""
import hmac
import os
import hashlib
from flask import session
from flask import request, jsonify

_WEAK = {"", "changeme", "change-me", "secret", "password"}


def _secret():
    return os.getenv("TRIGGER_SECRET", "").strip()


def is_weak_secret(value):
    return (value or "").strip().lower() in _WEAK


def secret_is_weak():
    return is_weak_secret(_secret())


def session_fingerprint():
    return hashlib.sha256(("geo-admin:" + _secret()).encode()).hexdigest()


def session_authorized():
    return not secret_is_weak() and hmac.compare_digest(
        str(session.get("admin", "")), session_fingerprint())


def authorized(req=None):
    """True when ?key= / X-Trigger-Key matches TRIGGER_SECRET.

    A missing or placeholder secret FAILS CLOSED (the originals either
    accepted any request or accepted the literal "changeme"). Local dev can
    opt out explicitly with ALLOW_INSECURE_LOCAL=true."""
    req = req or request
    if secret_is_weak():
        return os.getenv("ALLOW_INSECURE_LOCAL", "false").lower() == "true"
    if session_authorized():
        return True
    supplied = req.args.get("key") or req.headers.get("X-Trigger-Key") or ""
    return hmac.compare_digest(supplied.encode(), _secret().encode())


def deny():
    if secret_is_weak():
        return jsonify(error="TRIGGER_SECRET is not set (or is a placeholder); "
                             "set a real value in the environment."), 503
    return jsonify(error="unauthorized"), 401
