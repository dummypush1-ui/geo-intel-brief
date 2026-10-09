"""Supplied sender-inclusive scope data. No effective identity or wiring."""
import hashlib
import json
import re

_ADDRESS = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', re.ASCII)
_POLICY = 'email_sender_recipient_scope222_v1_ascii_whole_address_lowercase_sorted'
_NOTE = ('Sender fingerprint is a plain hash of the lowercased address and can be guessed '
         'from a candidate list. Sender binding blocker is prepared, not resolved; no consumer checks the real sender.')
_FLAGS = {'send_allowed': False, 'ready': False, 'owner_approval': False,
          'ledger_wired': False, 'bridge_wired': False}


def _fail():
    raise ValueError('Sender scope held') from None


def _hash(value):
    wire = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')
    return hashlib.sha256(wire).hexdigest()


def binding_data(*, enabled=False, sender=None, recipients=None):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'note': _NOTE, **_FLAGS}
    result = None
    try:
        if type(sender) is not str or not 1 <= len(sender) <= 254 or _ADDRESS.fullmatch(sender) is None:
            _fail()
        from integration.recipient_scope220 import fingerprint
        recipient_fp = fingerprint(enabled=True, recipients=recipients)['fingerprint']
        sender_fp = _hash({'schema': 'email_sender_fingerprint222_v1',
                           'domain': 'email.sender222', 'sender_lower': sender.lower()})
        scope_fp = _hash({'schema': 'email_sender_recipient_scope222_v1',
                          'sender_fingerprint': sender_fp, 'recipient_set_fingerprint': recipient_fp})
        result = {'sender_fingerprint': sender_fp, 'recipient_set_fingerprint': recipient_fp,
                  'sender_recipient_scope_fingerprint': scope_fp, 'policy': _POLICY,
                  'note': _NOTE, **_FLAGS}
    except Exception:
        pass
    if result is None:
        _fail()
    return result
