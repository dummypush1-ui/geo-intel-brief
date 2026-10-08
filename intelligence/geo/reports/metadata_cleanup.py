"""Legacy cleanup is deliberately disabled.

Telegram URLs, flags, caller-supplied hashes and acknowledgements do not prove
an authenticated complete recoverable backup or an owner retention grant.
No storage reads or deletes run here, even when cleanup is enabled. Future
retention requires a separately reviewed implementation, not a boolean bypass.
Pending full-record outbox records must never inherit article TTL/deletion.
"""


def cleanup(days=None):
    return {"deleted": 0, "held": True,
            "reason": "retention_policy_not_implemented"}
