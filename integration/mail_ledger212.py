"""Unselected per-logical-channel exclusion ledger. No sender or article writes.
Public PyMongo transaction API: no application retry, driver commit may retry.
"""
import hashlib
import json
import re
import inspect
from pathlib import Path
import pymongo
from copy import deepcopy
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern

DB = 'geo_intel'
CONTROL = 'mail_control212'
RECEIPTS = 'mail_receipts212'
ARTICLES = 'mail_articles212'
KINDS = ('email', 'telegram', 'whatsapp')
PURPOSES = ('digest', 'critical')
STATES = ('prepared', 'started', 'acknowledged', 'cancelled', 'operator_resolved_unsent')
RELEASED = ('cancelled', 'operator_resolved_unsent')
CAP = 120
REVIEW_FIELDS = {'mapping', 'transaction_supported', 'write_permission',
                 'control_provisioned', 'history_manifest', 'history_complete'}


class LedgerRefused(ValueError):
    def __init__(self, reason='unavailable'):
        self.reason = reason
        super().__init__('Mail ledger held: ' + reason)


def _fail(reason='invalid'):
    raise LedgerRefused(reason)


def _sha(value):
    if type(value) is not str or re.fullmatch(r'[0-9a-f]{64}', value, re.ASCII) is None:
        _fail()
    return value


def _token(value):
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_-]{20,80}', value, re.ASCII) is None:
        _fail()
    return value


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')).hexdigest()


def logical_channel(kind, recipient_set_fingerprint):
    """Recipient fingerprint is reviewed input, not permission or authentication.
    Rail/transport is intentionally absent. Recipient-set change is a new channel.
    """
    if type(kind) is not str or kind not in KINDS:
        _fail()
    return _hash({'kind': kind, 'recipients': _sha(recipient_set_fingerprint)})


def _ids(values):
    if type(values) is not list or not 1 <= len(values) <= CAP or any(type(v) is not ObjectId for v in values):
        _fail('capacity' if type(values) is list and len(values) > CAP else 'invalid')
    out = sorted(str(v) for v in values)
    if len(set(out)) != len(out):
        _fail()
    return out


def _stored_ids(values):
    if type(values) is not list or not 1 <= len(values) <= CAP or any(type(v) is not str or re.fullmatch(r'[0-9a-f]{24}', v, re.ASCII) is None for v in values) or values != sorted(set(values)):
        _fail('schema')
    return values


def _rail(value):
    if type(value) is not str or value not in ('apps_script', 'smtp', 'telegram', 'whatsapp'):
        _fail()
    return value


def verify_driver():
    """Public API behavior is source-pinned; this is not deployment proof."""
    import importlib
    pins = json.loads(Path(__file__).with_name('mail_driver212.json').read_text())
    if pymongo.version != pins['version']:
        _fail('driver')
    for row in pins['modules']:
        module = importlib.import_module(row['module'])
        if hashlib.sha256(Path(inspect.getfile(module)).read_bytes()).hexdigest() != row['sha256']:
            _fail('driver')
    return pins['version']


class MailLedger:
    def __init__(self, client=None, *, enabled=False, kind=None, purpose=None,
                 recipient_set_fingerprint=None, review=None):
        if type(enabled) is not bool:
            _fail()
        self.enabled = enabled
        if not enabled:
            # Never inspect, repr or save a supplied client while OFF.
            return
        if type(kind) is not str or kind not in KINDS or type(purpose) is not str or purpose not in PURPOSES:
            _fail()
        if type(review) is not dict or set(review) != REVIEW_FIELDS or review['mapping'] != (DB, CONTROL, RECEIPTS, ARTICLES) or any(review[k] is not True for k in ('transaction_supported', 'write_permission', 'control_provisioned', 'history_complete')):
            _fail('history_unverified')
        verify_driver()
        self.history = _sha(review['history_manifest'])
        self.channel = logical_channel(kind, recipient_set_fingerprint)
        self.kind = kind
        self.purpose = purpose
        self.control_id = _hash({'channel': self.channel, 'purpose': purpose})
        self.client = client
        # Read-only no-TTL inspection, no creation/index mutation. Future schema,
        # privilege, history and actual transaction diagnostics are separate gates.
        try:
            db = client[DB]
            for name in (CONTROL, RECEIPTS, ARTICLES):
                cursor = db[name].list_indexes(maxTimeMS=2000)
                try:
                    rows = []
                    for row in cursor:
                        if len(rows) >= 16:
                            _fail('schema')
                        rows.append(row)
                finally:
                    cursor.close()
                if not rows or any(type(r) is not dict or 'expireAfterSeconds' in r for r in rows):
                    _fail('schema')
                if not any(r.get('name') == '_id_' and r.get('key') == {'_id': 1} and not r.get('sparse') and not r.get('partialFilterExpression') and r.get('unique', True) is True for r in rows):
                    _fail('schema')
        except LedgerRefused:
            raise
        except Exception:
            _fail('unavailable')

    def __repr__(self):
        return 'MailLedger(enabled=' + str(self.enabled) + ')'

    def _enabled(self):
        if not self.enabled:
            _fail('disabled')

    def _control(self, db, session):
        row = db[CONTROL].find_one({'_id': self.control_id}, session=session, max_time_ms=2000)
        fields = {'_id', 'schema', 'channel', 'purpose', 'history_manifest', 'history_complete', 'revision', 'active'}
        if type(row) is not dict or set(row) != fields or row['_id'] != self.control_id or type(row['schema']) is not int or row['schema'] != 1 or row['channel'] != self.channel or row['purpose'] != self.purpose or row['history_manifest'] != self.history or row['history_complete'] is not True or type(row['revision']) is not int or not 0 <= row['revision'] < 2**53 - 1:
            _fail('schema')
        if row['active'] is not None:
            _sha(row['active'])
        return row

    def _run(self, operation, *, write=True):
        self._enabled()
        verify_driver()
        session = None
        commit_attempted = False
        try:
            session = self.client.start_session(causal_consistency=False)
            session.start_transaction(read_concern=ReadConcern('snapshot'),
                write_concern=WriteConcern(w='majority', j=True, wtimeout=5000),
                read_preference=ReadPreference.PRIMARY, max_commit_time_ms=5000)
            db = self.client[DB]
            control = self._control(db, session)
            revision = control['revision']
            result = operation(db, session, control)
            if write:
                control['revision'] += 1
                changed = db[CONTROL].replace_one({'_id': self.control_id, 'revision': revision}, control, session=session)
                if changed.acknowledged is not True or type(changed.matched_count) is not int or changed.matched_count != 1:
                    _fail('conflict')
            commit_attempted = True
            # Driver retries commit once on retryable errors. Never call
            # with_transaction, loop/replay the body, or retry here.
            session.commit_transaction()
            return deepcopy(result)
        except LedgerRefused:
            raise
        except DuplicateKeyError:
            _fail('conflict')
        except OperationFailure as error:
            if error.has_error_label('UnknownTransactionCommitResult'):
                _fail('unknown_commit')
            if error.has_error_label('TransientTransactionError') or error.code == 112:
                _fail('conflict')
            _fail('unavailable')
        except Exception:
            _fail('unknown_commit' if commit_attempted else 'unavailable')
        finally:
            if session is not None:
                if not commit_attempted:
                    try:
                        session.abort_transaction()
                    except Exception:
                        pass
                # Public driver sets COMMITTED even on unknown commit. Its
                # end_session then does not abort a possibly committed write.
                try:
                    session.end_session()
                except Exception:
                    pass

    def article_key(self, article_id):
        self._enabled()
        if type(article_id) is not ObjectId:
            _fail()
        return _hash({'channel': self.channel, 'purpose': self.purpose, 'article': str(article_id)})

    def _article(self, row, key):
        fields = {'_id', 'schema', 'channel', 'purpose', 'article', 'receipt', 'hash', 'state'}
        if type(row) is not dict or set(row) != fields or row['_id'] != key or type(row['schema']) is not int or row['schema'] != 1 or row['channel'] != self.channel or row['purpose'] != self.purpose or type(row['article']) is not str or re.fullmatch(r'[0-9a-f]{24}', row['article'], re.ASCII) is None or row['state'] not in STATES or self.article_key(ObjectId(row['article'])) != key:
            _fail('schema')
        _sha(row['receipt']); _sha(row['hash'])
        return row

    def _lookup(self, db, session, ids):
        keys = [self.article_key(ObjectId(v)) for v in ids]
        cursor = db[ARTICLES].find({'_id': {'$in': keys}}, session=session, max_time_ms=2000)
        found = {}
        try:
            for row in cursor:
                if len(found) >= len(keys) or type(row) is not dict or row.get('_id') not in keys or row['_id'] in found:
                    _fail('schema')
                found[row['_id']] = self._article(row, row['_id'])
        finally:
            cursor.close()
        return found

    def exclusions(self, candidate_ids):
        self._enabled()
        ids = _ids(candidate_ids)
        def op(db, session, control):
            rows = self._lookup(db, session, ids)
            if any(r['state'] == 'started' for r in rows.values()): _fail('conflict_started')
            if any(r['state'] == 'prepared' for r in rows.values()): _fail('conflict_prepared')
            return {'excluded_ids': [r['article'] for r in rows.values() if r['state'] == 'acknowledged'],
                    'scope': 'recorded_keys_only_not_historical_completeness', 'send_allowed': False}
        return self._run(op, write=False)

    def _binding(self, ids, content_digest):
        return _hash({'logical_channel': self.channel, 'purpose': self.purpose,
                      'ids': ids, 'content_digest': _sha(content_digest)})

    def _receipt(self, db, session, key):
        row = db[RECEIPTS].find_one({'_id': key}, session=session, max_time_ms=2000)
        if row is None:
            return None
        fields = {'_id', 'schema', 'channel', 'purpose', 'ids', 'hash', 'content_digest', 'rail', 'state', 'attempt', 'resolution_reference', 'scope'}
        if type(row) is not dict or set(row) != fields or row['_id'] != key or type(row['schema']) is not int or row['schema'] != 1 or row['channel'] != self.channel or row['purpose'] != self.purpose or row['state'] not in STATES:
            _fail('schema')
        _sha(row['_id']); _stored_ids(row['ids']); _sha(row['hash']); _sha(row['content_digest']); _rail(row['rail'])
        if self._binding(row['ids'], row['content_digest']) != row['hash']:
            _fail('schema')
        if row['state'] in ('started', 'acknowledged', 'operator_resolved_unsent'):
            _token(row['attempt'])
        elif row['attempt'] is not None:
            _fail('schema')
        expected = 'bridge_send_returned_not_delivery' if row['state'] == 'acknowledged' and row['resolution_reference'] is None else 'operator_asserted_sent_not_delivery' if row['state'] == 'acknowledged' else 'operator_asserted_unsent' if row['state'] == 'operator_resolved_unsent' else 'no_send_proof'
        if row['scope'] != expected:
            _fail('schema')
        if row['resolution_reference'] is not None:
            _sha(row['resolution_reference'])
        if row['state'] == 'operator_resolved_unsent' and row['resolution_reference'] is None:
            _fail('schema')
        return row

    def prepare(self, nonce, displayed_ids, content_digest, *, rail):
        self._enabled(); _token(nonce); ids = _ids(displayed_ids); _rail(rail)
        digest = self._binding(ids, content_digest)
        key = _hash({'control': self.control_id, 'nonce': nonce})
        def op(db, session, control):
            old = self._receipt(db, session, key)
            if old is not None:
                if old['hash'] != digest or old['rail'] != rail: _fail('conflict_other_hash')
                return old
            rows = self._lookup(db, session, ids)
            if any(r['state'] == 'started' for r in rows.values()): _fail('conflict_started')
            if any(r['state'] == 'prepared' for r in rows.values()): _fail('conflict_prepared')
            if any(r['state'] == 'acknowledged' for r in rows.values()): _fail('conflict_sent')
            if control['active'] is not None:
                active = self._receipt(db, session, control['active'])
                if active is None or active['state'] not in ('prepared', 'started'): _fail('schema')
                _fail('conflict_started' if active['state'] == 'started' else 'conflict_prepared')
            receipt = {'_id': key, 'schema': 1, 'channel': self.channel, 'purpose': self.purpose,
                'ids': ids, 'hash': digest, 'content_digest': content_digest, 'rail': rail,
                'state': 'prepared', 'attempt': None, 'resolution_reference': None, 'scope': 'no_send_proof'}
            for article in ids:
                identity = self.article_key(ObjectId(article))
                row = {'_id': identity, 'schema': 1, 'channel': self.channel, 'purpose': self.purpose,
                       'article': article, 'receipt': key, 'hash': digest, 'state': 'prepared'}
                if identity in rows:
                    prior = rows[identity]
                    result = db[ARTICLES].replace_one({'_id': identity, 'receipt': prior['receipt'], 'hash': prior['hash'], 'state': prior['state']}, row, session=session)
                    if result.acknowledged is not True or result.matched_count != 1: _fail('conflict')
                else:
                    if db[ARTICLES].insert_one(row, session=session).acknowledged is not True: _fail('conflict')
            if db[RECEIPTS].insert_one(receipt, session=session).acknowledged is not True: _fail('conflict')
            control['active'] = key
            return receipt
        return self._run(op)

    def status(self, key):
        self._enabled(); _sha(key)
        def op(db, session, control):
            row = self._receipt(db, session, key)
            if row is None: _fail('missing')
            return row
        return self._run(op, write=False)

    def _transition(self, key, digest, attempt, target, *, reference=None):
        def op(db, session, control):
            row = self._receipt(db, session, key)
            if row is None or row['hash'] != digest: _fail('conflict_other_hash')
            if row['state'] == target:
                if target == 'started': _fail('conflict_started')
                if row['attempt'] != attempt or row['resolution_reference'] != reference: _fail('conflict_other_hash')
                return row
            prior = 'prepared' if target in ('started', 'cancelled') else 'started'
            if row['state'] != prior or control['active'] != key: _fail('conflict_started' if row['state'] == 'started' else 'conflict')
            if prior == 'started' and row['attempt'] != attempt: _fail('conflict_other_hash')
            articles = self._lookup(db, session, row['ids'])
            if len(articles) != len(row['ids']) or any(r['receipt'] != key or r['hash'] != digest or r['state'] != prior for r in articles.values()): _fail('schema')
            for identity, article in articles.items():
                changed = dict(article, state=target)
                result = db[ARTICLES].replace_one({'_id': identity, 'receipt': key, 'hash': digest, 'state': prior}, changed, session=session)
                if result.acknowledged is not True or result.matched_count != 1: _fail('conflict')
            scope = 'bridge_send_returned_not_delivery' if target == 'acknowledged' and reference is None else 'operator_asserted_sent_not_delivery' if target == 'acknowledged' else 'operator_asserted_unsent' if target == 'operator_resolved_unsent' else 'no_send_proof'
            row.update(state=target, attempt=attempt, resolution_reference=reference, scope=scope)
            result = db[RECEIPTS].replace_one({'_id': key, 'hash': digest, 'state': prior}, row, session=session)
            if result.acknowledged is not True or result.matched_count != 1: _fail('conflict')
            if target != 'started': control['active'] = None
            return row
        return self._run(op)

    def start(self, key, digest, attempt):
        self._enabled(); _sha(key); _sha(digest); _token(attempt)
        try:
            # The transition atomically denies replay before readback.
            self._start_fresh(key, digest, attempt)
            stored = self.status(key)  # fresh snapshot readback, no application retry
            if stored['state'] != 'started' or stored['attempt'] != attempt or stored['hash'] != digest:
                _fail('readback')
            return {'permit': True, 'state': 'started', 'scope': 'source_only_not_send_authority'}
        except LedgerRefused as error:
            return {'permit': False, 'state': 'held', 'reason': error.reason, 'status_required': True}

    def _start_fresh(self, key, digest, attempt):
        # A start operation must atomically deny existing started state. Reuse
        # transition implementation with allow_replay=False, no precheck race.
        return self._transition(key, digest, attempt, 'started')

    def acknowledge(self, key, digest, attempt):
        self._enabled(); _sha(key); _sha(digest); _token(attempt)
        return self._finish(key, digest, attempt, 'acknowledged')

    def cancel(self, key, digest):
        self._enabled(); _sha(key); _sha(digest)
        return self._finish(key, digest, None, 'cancelled')

    def resolve(self, key, digest, attempt, *, confirmed_sent, authority_reference):
        """Future caller authenticates operator intent. This function grants none.
        The reference is audit binding, never proof of that authority.
        """
        self._enabled(); _sha(key); _sha(digest); _token(attempt); _sha(authority_reference)
        if type(confirmed_sent) is not bool: _fail()
        return self._finish(key, digest, attempt,
                            'acknowledged' if confirmed_sent else 'operator_resolved_unsent',
                            reference=authority_reference)

    def _finish(self, key, digest, attempt, target, reference=None):
        try:
            self._transition(key, digest, attempt, target, reference=reference)
            stored = self.status(key)
            if stored['state'] != target or stored['hash'] != digest or stored['attempt'] != attempt or stored['resolution_reference'] != reference: _fail('readback')
            return {'state': target, 'scope': stored['scope'], 'send_allowed': False}
        except LedgerRefused as error:
            return {'state': 'held', 'reason': error.reason, 'status_required': True, 'send_allowed': False}
