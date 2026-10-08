# Copyright (c) 2026 Push. All rights reserved.
"""Injected Mongo snapshot transactions, bounded durable HTML receipt archive.

No client creation, indexes, provisioning, environment or activation. A reviewed
pre-provisioned control row serializes all mail operations. Archive has a hard
128-record cap: no automatic deletion. Receipt acknowledgement is a trusted
bridge assertion, not independently verified Gmail identity or delivery.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from copy import deepcopy
from bson import ObjectId
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from .reports import build, POLICIES

KINDS = ('digest', 'critical', 'weekly')
REVIEW = {'mapping', 'transaction_supported', 'source_schema_verified', 'write_permission', 'control_provisioned', 'iso_article_dates_verified'}


class MailUnavailable(ValueError):
    pass


def _token(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{20,80}', value):
        raise ValueError('Opaque nonce/attempt required')
    return value


def _digest(value):
    wire = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode()
    if len(wire) > 8 * 1024 * 1024: raise ValueError('Archived payload byte cap')
    return sha256(wire).hexdigest()


def _sha(value):
    if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('SHA256 required')
    return value


class MongoMailStore:
    def __init__(self, client, *, review, channel_id, marking_policy):
        if (type(review) is not dict or set(review) != REVIEW or review['mapping'] != ('geo_intel', 'articles', 'events', 'mail_control', 'mail_receipts')
                or any(review[k] is not True for k in REVIEW - {'mapping'})):
            raise MailUnavailable('Exact reviewed transactional source required')
        if marking_policy not in POLICIES or type(marking_policy) is not str:
            raise MailUnavailable('Explicit marking policy required')
        self.client = client
        self.channel = _sha(channel_id) # reviewed sender/recipient/scope fingerprint, never an auth credential
        self.policy = marking_policy

    def _run(self, operation):
        session = None
        committed = False
        try:
            session = self.client.start_session(causal_consistency=False)
            session.start_transaction(read_concern=ReadConcern('snapshot'), write_concern=WriteConcern('majority'), max_commit_time_ms=2000)
            db = self.client['geo_intel']
            control = db['mail_control'].find_one({'_id': 'mail-v1'}, session=session, max_time_ms=2000)
            if (type(control) is not dict or set(control) != {'_id', 'schema', 'revision', 'channel_id', 'policy', 'active'}
                    or control['_id'] != 'mail-v1' or type(control['schema']) is not int or control['schema'] != 1
                    or type(control['revision']) is not int or not 0 <= control['revision'] < 2**53
                    or control['channel_id'] != self.channel or control['policy'] != self.policy
                    or type(control['active']) is not dict or set(control['active']) - set(KINDS)):
                raise ValueError('Control unavailable')
            for k in control['active'].values():
                _sha(k)
            before = control['revision']
            result = operation(db, session, control)
            control['revision'] += 1
            r = db['mail_control'].replace_one({'_id': 'mail-v1', 'revision': before}, control, session=session)
            if r.acknowledged is not True or type(r.matched_count) is not int or r.matched_count != 1:
                raise ValueError('Control contention')
            session.commit_transaction()
            committed = True
            return deepcopy(result)
        except Exception:
            raise MailUnavailable('Mail transaction unavailable or uncertain; do not resend') from None
        finally:
            if session is not None:
                if not committed:
                    try: session.abort_transaction()
                    except Exception: pass
                try: session.end_session()
                except Exception: pass

    def _receipt(self, db, session, key):
        r = db['mail_receipts'].find_one({'_id': key}, session=session, max_time_ms=2000)
        if r is None:
            return None
        fields = {'_id', 'schema', 'channel_id', 'payload', 'hash', 'state', 'attempt', 'created_at', 'accepted_at', 'receipt_scope'}
        if (type(r) is not dict or set(r) != fields or r['_id'] != key or type(r['schema']) is not int or r['schema'] != 1
                or r['channel_id'] != self.channel or r['state'] not in ('prepared', 'started', 'acknowledged', 'skipped')
                or type(r['payload']) is not dict or _digest(r['payload']) != r['hash']
                or r['payload'].get('policy') != self.policy or r['payload'].get('kind') not in KINDS):
            raise ValueError('Archive invalid')
        p = r['payload']
        if set(p) != {'kind', 'subject', 'html', 'fetched_ids', 'displayed_ids', 'mark_ids', 'critical_count', 'skip', 'policy', 'source_scope', 'clock_scope', 'events_scope'}:
            raise ValueError('Closed archived payload required')
        for field in ('fetched_ids', 'displayed_ids', 'mark_ids'):
            ids = p[field]
            if type(ids) is not list or len(ids) > 200 or any(type(x) is not str or not re.fullmatch(r'[0-9a-f]{24}', x) for x in ids) or len(set(ids)) != len(ids):
                raise ValueError('Archived IDs invalid')
        if not set(p['displayed_ids']) <= set(p['fetched_ids']): raise ValueError('Displayed binding invalid')
        expected = [] if p['kind'] == 'weekly' or p['skip'] else p['fetched_ids'] if self.policy == 'fetched' else p['displayed_ids']
        if p['mark_ids'] != expected: raise ValueError('Mark policy binding invalid')
        if type(p['skip']) is not bool or type(p['critical_count']) is not int or not 0 <= p['critical_count'] <= 200:
            raise ValueError('Archive counts invalid')
        if type(p['subject']) is not str or len(p['subject']) > 200 or any(ord(c) < 32 for c in p['subject']) or type(p['html']) is not str or len(p['html'].encode()) > 1024 * 1024:
            raise ValueError('Archive content invalid')
        if p['source_scope'] != 'transaction_snapshot' or p['clock_scope'] != 'UTC' or p['events_scope'] != ('queried_90day' if p['kind'] == 'digest' else 'not_in_original_report'):
            raise ValueError('Archive scope invalid')
        if (r['state'] == 'skipped') != p['skip']: raise ValueError('Skip binding invalid')
        _sha(r['hash'])
        if r['state'] in ('started', 'acknowledged'): _token(r['attempt'])
        elif r['attempt'] is not None: raise ValueError('Unexpected attempt')
        if type(r['created_at']) is not str or r['receipt_scope'] != ('bridge_send_returned_not_delivery' if r['state'] == 'acknowledged' else 'no_send_proof'):
            raise ValueError('Invalid receipt scope')
        return r

    def prepare(self, kind, nonce, now):
        if type(kind) is not str or kind not in KINDS or type(now) is not datetime or type(now.tzinfo) is not timezone:
            raise MailUnavailable('Exact kind and UTC-aware clock required')
        key = _digest({'kind': kind, 'nonce': _token(nonce), 'channel': self.channel})
        def op(db, session, control):
            old = self._receipt(db, session, key)
            if old is not None: return old
            if kind in control['active']: raise ValueError('Unresolved receipt holds this mail kind')
            count = db['mail_receipts'].count_documents({}, session=session, limit=128, maxTimeMS=2000)
            if type(count) is not int or not 0 <= count < 128: raise ValueError('Archive full')
            payload = build({'articles': db['articles'], 'events': db['events']}, session, kind, now, self.policy)
            r = {'_id': key, 'schema': 1, 'channel_id': self.channel, 'payload': payload, 'hash': _digest(payload),
                 'state': 'skipped' if payload['skip'] else 'prepared', 'attempt': None,
                 'created_at': now.astimezone(timezone.utc).isoformat(), 'accepted_at': None, 'receipt_scope': 'no_send_proof'}
            result = db['mail_receipts'].insert_one(r, session=session)
            if result.acknowledged is not True: raise ValueError('Archive uncertain')
            if r['state'] == 'prepared': control['active'][kind] = key
            return r
        return self._run(op)

    def claim(self, key, digest, attempt):
        _sha(key); _sha(digest); _token(attempt)
        def op(db, session, control):
            r = self._receipt(db, session, key)
            if r is None or r['hash'] != digest: raise ValueError('Receipt binding refused')
            if r['state'] != 'prepared': return {'permit': False, 'state': r['state'], 'receipt': key}
            if control['active'].get(r['payload']['kind']) != key: raise ValueError('Active binding refused')
            r.update(state='started', attempt=attempt)
            result = db['mail_receipts'].replace_one({'_id': key, 'state': 'prepared'}, r, session=session)
            if result.acknowledged is not True or result.matched_count != 1: raise ValueError('Claim refused')
            return {'permit': True, 'state': 'started', 'receipt': key}
        return self._run(op)

    def acknowledge(self, key, digest, attempt, now):
        _sha(key); _sha(digest); _token(attempt)
        if type(now) is not datetime or type(now.tzinfo) is not timezone: raise ValueError('Fixed aware clock required')
        def op(db, session, control):
            r = self._receipt(db, session, key)
            if r is None or r['hash'] != digest or r['attempt'] != attempt or r['state'] not in ('started', 'acknowledged'):
                raise ValueError('Started receipt binding required')
            if r['state'] == 'acknowledged': return {'receipt': key, 'state': 'acknowledged', 'scope': r['receipt_scope']}
            payload = r['payload']; kind = payload['kind']
            if control['active'].get(kind) != key: raise ValueError('Active binding refused')
            ids = payload['mark_ids']
            if type(ids) is not list or len(ids) > 200 or len(set(ids)) != len(ids) or any(type(x) is not str or not re.fullmatch(r'[0-9a-f]{24}', x) for x in ids):
                raise ValueError('Exact archived ObjectIds required')
            if ids:
                flag = 'emailed' if kind == 'digest' else 'mail_critical_sent' if kind == 'critical' else None
                if flag is None: raise ValueError('Weekly must not mark')
                result = db['articles'].update_many({'_id': {'$in': [ObjectId(x) for x in ids]}}, {'$set': {flag: True}}, session=session)
                if result.acknowledged is not True or result.matched_count != len(ids): raise ValueError('Mark outcome incomplete')
            r.update(state='acknowledged', accepted_at=now.astimezone(timezone.utc).isoformat(), receipt_scope='bridge_send_returned_not_delivery')
            result = db['mail_receipts'].replace_one({'_id': key, 'state': 'started'}, r, session=session)
            if result.acknowledged is not True or result.matched_count != 1: raise ValueError('Receipt write incomplete')
            del control['active'][kind]
            return {'receipt': key, 'state': 'acknowledged', 'scope': r['receipt_scope']}
        return self._run(op)

    def status(self, key):
        _sha(key)
        def op(db, session, control):
            r = self._receipt(db, session, key)
            if r is None: raise ValueError('Unknown receipt')
            return r
        return self._run(op)
