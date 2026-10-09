"""Native-shaped supplied rows only, never authenticated database evidence."""
_FIELDS = {'control_row', 'receipt_rows', 'article_rows', 'recipient_set_fingerprint', 'history_manifest'}
_CONTROL = {'_id', 'schema', 'channel', 'purpose', 'history_manifest', 'history_complete', 'revision', 'active'}
_RECEIPT = {'_id', 'schema', 'channel', 'purpose', 'ids', 'hash', 'content_digest', 'rail', 'state', 'attempt', 'resolution_reference', 'scope'}
_ARTICLE = {'_id', 'schema', 'channel', 'purpose', 'article', 'receipt', 'hash', 'state'}
_STATES = ('prepared', 'started', 'acknowledged', 'cancelled', 'operator_resolved_unsent')
_FLAGS = {'source_authenticated': False, 'history_verified': False, 'current_state_verified': False,
          'send_allowed': False, 'ready': False, 'owner_approval': False, 'ledger_wired': False}
_NOTE = ('Supplied native-shaped rows only; a coherent graph can be invented or incomplete. '
         'history_complete True is the row claim, not evidence. Acknowledged articles may reference unsupplied receipts.')


def _fail():
    raise ValueError('Native projection held') from None


def project_supplied(*, enabled=False, **args):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'note': _NOTE, **_FLAGS}
    projection = None
    try:
        if set(args) != _FIELDS or any(type(k) is not str for k in args):
            _fail()
        control, receipts, articles = args['control_row'], args['receipt_rows'], args['article_rows']
        if type(receipts) is not list or len(receipts) > 128 or type(articles) is not list or len(articles) > 10000:
            _fail()
        import hashlib
        import json
        import re
        from bson import ObjectId
        def sha(value):
            if type(value) is not str or re.fullmatch(r'[0-9a-f]{64}', value, re.ASCII) is None:
                _fail()
            return value
        def oid(value):
            if type(value) is not str or re.fullmatch(r'[0-9a-f]{24}', value, re.ASCII) is None:
                _fail()
            return value
        def token(value):
            if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_-]{20,80}', value, re.ASCII) is None:
                _fail()
        def hash_value(value):
            return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')).hexdigest()
        channel = hash_value({'kind': 'email', 'recipients': sha(args['recipient_set_fingerprint'])})
        history = sha(args['history_manifest'])
        control_id = hash_value({'channel': channel, 'purpose': 'digest'})
        def native(row, fields):
            if type(row) is not dict or set(row) != fields or any(type(k) is not str for k in row):
                _fail()
            if type(row['schema']) is not int or row['schema'] != 1 or type(row['channel']) is not str or row['channel'] != channel or type(row['purpose']) is not str or row['purpose'] != 'digest':
                _fail()
        native(control, _CONTROL)
        if sha(control['_id']) != control_id or sha(control['history_manifest']) != history or control['history_complete'] is not True or type(control['revision']) is not int or not 0 <= control['revision'] < 2**53 - 1:
            _fail()
        active = control['active']
        if active is not None:
            sha(active)
        by_receipt = {}
        for row in receipts:
            native(row, _RECEIPT)
            key = sha(row['_id'])
            if key in by_receipt:
                _fail()
            ids = row['ids']
            if type(ids) is not list or not 1 <= len(ids) <= 120 or any(type(v) is not str for v in ids):
                _fail()
            for value in ids:
                oid(value)
            if ids != sorted(set(ids)):
                _fail()
            sha(row['hash']);sha(row['content_digest'])
            if row['hash'] != hash_value({'logical_channel': channel, 'purpose': 'digest', 'ids': ids, 'content_digest': row['content_digest']}):
                _fail()
            if type(row['rail']) is not str or row['rail'] not in ('apps_script', 'smtp', 'telegram', 'whatsapp') or type(row['state']) is not str or row['state'] not in _STATES:
                _fail()
            state = row['state'];reference = row['resolution_reference']
            if state in ('started', 'acknowledged', 'operator_resolved_unsent'):
                token(row['attempt'])
            elif row['attempt'] is not None:
                _fail()
            expected = ('bridge_send_returned_not_delivery' if state == 'acknowledged' and reference is None
                        else 'operator_asserted_sent_not_delivery' if state == 'acknowledged'
                        else 'operator_asserted_unsent' if state == 'operator_resolved_unsent' else 'no_send_proof')
            if type(row['scope']) is not str or row['scope'] != expected:
                _fail()
            if reference is not None:
                sha(reference)
            if state == 'operator_resolved_unsent' and reference is None:
                _fail()
            by_receipt[key] = row
        by_article = {};keys = set()
        for row in articles:
            native(row, _ARTICLE)
            article = oid(row['article']);key = sha(row['_id'])
            if key in keys or article in by_article or key != hash_value({'channel': channel, 'purpose': 'digest', 'article': article}):
                _fail()
            keys.add(key);sha(row['receipt']);sha(row['hash'])
            if type(row['state']) is not str or row['state'] not in _STATES:
                _fail()
            receipt = by_receipt.get(row['receipt'])
            if receipt is not None and (article not in receipt['ids'] or row['hash'] != receipt['hash'] or row['state'] != receipt['state']):
                _fail()
            if row['state'] in ('prepared', 'started') and (receipt is None or row['receipt'] != active):
                _fail()
            by_article[article] = row
        if active is not None and (active not in by_receipt or by_receipt[active]['state'] not in ('prepared', 'started')):
            _fail()
        for key, row in by_receipt.items():
            if row['state'] in ('prepared', 'started') and key != active:
                _fail()
            for article in row['ids']:
                current = by_article.get(article)
                if row['state'] in ('prepared', 'started', 'acknowledged'):
                    if current is None or current['receipt'] != key or current['hash'] != row['hash'] or current['state'] != row['state']:
                        _fail()
                elif current is not None and current['receipt'] == key and (current['hash'] != row['hash'] or current['state'] != row['state']):
                    _fail()
        acknowledged = tuple(ObjectId(v) for v in sorted(article for article, row in by_article.items() if row['state'] == 'acknowledged'))
        projection = {'schema': 'mail_exclusion_projection223_v1', 'logical_channel': channel,
                      'purpose': 'digest', 'acknowledged_ids': acknowledged,
                      'active_state': None if active is None else by_receipt[active]['state']}
    except Exception:
        pass
    if projection is None:
        _fail()
    return {'state': 'supplied_native_projection_only', 'projection': projection, 'note': _NOTE, **_FLAGS}
