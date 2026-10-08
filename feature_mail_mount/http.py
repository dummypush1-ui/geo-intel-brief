# Copyright (c) 2026 Push. All rights reserved.
"""Header-authenticated mail-only blueprint, explicitly injected, never mounted here."""
import hmac
import json
from flask import Blueprint, request, jsonify
from .store import MailUnavailable


def blueprint(store, *, secret, clock):
    if type(secret) is not str or not 48 <= len(secret) <= 256 or any(not 33 <= ord(c) <= 126 for c in secret) or not callable(clock):
        raise ValueError('Reviewed header secret and clock required')
    bp = Blueprint('mail_mount_v1', __name__)
    def auth():
        return hmac.compare_digest(request.headers.get('Authorization', '').encode(), ('Bearer ' + secret).encode()) and not request.query_string
    def body():
        if request.mimetype != 'application/json' or request.content_length is None or request.content_length > 4096: raise ValueError()
        def pairs(rows):
            out = {}
            for k, v in rows:
                if k in out: raise ValueError()
                out[k] = v
            return out
        return json.loads(request.get_data(cache=False), object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    @bp.post('/internal/mail/v1/<action>')
    def action(action):
        if not auth(): return jsonify(error='unauthorized'), 401
        try:
            data = body()
            if type(data) is not dict: raise ValueError()
            if action == 'prepare' and set(data) == {'kind', 'nonce'}:
                r = store.prepare(data['kind'], data['nonce'], clock())
                return jsonify(receipt=r['_id'], hash=r['hash'], state=r['state'], channel_id=r['channel_id'], payload=r['payload']), 200
            if action in ('claim', 'ack') and set(data) == {'receipt', 'hash', 'attempt'}:
                fn = store.claim if action == 'claim' else store.acknowledge
                args = [data['receipt'], data['hash'], data['attempt']] + ([clock()] if action == 'ack' else [])
                return jsonify(fn(*args)), 200
            raise ValueError()
        except MailUnavailable: return jsonify(error='mail_unavailable_or_uncertain', retry_send=False), 503
        except Exception: return jsonify(error='invalid_request'), 400
    @bp.get('/internal/mail/v1/receipts/<key>')
    def status(key):
        if not auth(): return jsonify(error='unauthorized'), 401
        try:
            r = store.status(key)
            return jsonify(receipt=r['_id'], hash=r['hash'], state=r['state'], scope=r['receipt_scope'], payload=r['payload']), 200
        except Exception: return jsonify(error='receipt_unavailable', retry_send=False), 503
    return bp
