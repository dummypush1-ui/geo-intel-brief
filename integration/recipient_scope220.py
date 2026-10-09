"""Supplied config fingerprint only. No recipient choice or send authority."""
import hashlib
import json
import re

_ADDRESS = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', re.ASCII)
POLICY = 'email_recipient_set220_v1_ascii_whole_address_lowercase_sorted'


def _fail():
    raise ValueError('Recipient fingerprint refused') from None


def fingerprint(*, enabled=False, recipients=None):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'send_allowed': False, 'ready': False, 'owner_approval': False}
    if type(recipients) is not list or not 1 <= len(recipients) <= 20:
        _fail()
    for value in recipients:
        if type(value) is not str or not 1 <= len(value) <= 254 or _ADDRESS.fullmatch(value) is None:
            _fail()
    normalized = sorted(value.lower() for value in recipients)
    if len(set(normalized)) != len(normalized):
        _fail()
    wire = json.dumps({'schema': 'email_recipient_set220_v1', 'kind': 'email',
                       'recipients': normalized}, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')
    return {'fingerprint': hashlib.sha256(wire).hexdigest(), 'policy': POLICY,
            'count': len(normalized), 'send_allowed': False, 'ready': False,
            'owner_approval': False}
