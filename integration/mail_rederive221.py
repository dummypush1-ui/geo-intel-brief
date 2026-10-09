"""Supplied rows reproduce supplied bytes only. No external provenance proof."""
_FIELDS = {'blob', 'binding', 'rows', 'now', 'date_field', 'displayed_receipts',
           'offset_minutes', 'offset_label', 'limit', 'recipient_set_fingerprint', 'nonce'}
_FLAGS = {'send_allowed': False, 'ready': False, 'archive_proof': False,
          'durable': False, 'source_complete': False, 'receipt_membership_verified': False,
          'owner_approval': False}
_NOTE = ('These supplied rows regenerate these bytes only; rows may be a subset or invented. '
         'Completeness and freshness are not proven.')


def _fail():
    raise ValueError('Row rederivation held') from None


def verify_rederived(*, enabled=False, **args):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'row_derivation_match': False, 'note': _NOTE, **_FLAGS}
    matched = False
    try:
        if set(args) != _FIELDS or any(type(k) is not str for k in args):
            _fail()
        # ON only.219 validation must precede renderer and freeze.
        import copy
        import json
        from integration.mail_candidate219 import verify_snapshot, freeze_candidate, HEX, TOKEN
        from integration.digest_email218 import render_candidate
        blob, binding = args['blob'], args['binding']
        verify_snapshot(blob, binding)
        fp, nonce = args['recipient_set_fingerprint'], args['nonce']
        if type(fp) is not str or HEX.fullmatch(fp) is None or type(nonce) is not str or TOKEN.fullmatch(nonce) is None:
            _fail()
        if fp != binding['recipient_set_fingerprint'] or nonce != binding['nonce']:
            _fail()
        if type(args['rows']) is not list or len(args['rows']) > 1000 or any(type(row) is not dict for row in args['rows']):
            _fail()
        # Validate raw values before copying so deepcopy cannot erase subclasses.
        for row in args['rows']:
            if any(type(k) is not str for k in row):
                _fail()
            for key, value in row.items():
                if key == '_id':
                    from bson import ObjectId
                    if type(value) is not ObjectId:
                        _fail()
                elif key in ('published', 'created_at'):
                    from datetime import datetime
                    if type(value) not in (str, datetime):
                        _fail()
                elif key == 'emailed':
                    if value is not None and type(value) is not bool:
                        _fail()
                elif key in ('score', 'corroboration'):
                    if type(value) not in (int, float):
                        _fail()
                elif type(value) is not str:
                    _fail()
        rows = copy.deepcopy(args['rows'])
        rendered = render_candidate(enabled=True, rows=rows, now=args['now'],
                                    date_field=args['date_field'], displayed_receipts=args['displayed_receipts'],
                                    offset_minutes=args['offset_minutes'], offset_label=args['offset_label'],
                                    limit=args['limit'])
        if rows != args['rows']:
            _fail()
        rebuilt_blob, rebuilt_binding = freeze_candidate(enabled=True, candidate_result=rendered,
                                                         recipient_set_fingerprint=fp, nonce=nonce)
        wire = lambda v: json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
        matched = blob == rebuilt_blob and wire(binding) == wire(rebuilt_binding)
    except Exception:
        pass
    if not matched:
        _fail()
    return {'state': 'supplied_rows_rederived_match', 'row_derivation_match': True, 'note': _NOTE, **_FLAGS}
