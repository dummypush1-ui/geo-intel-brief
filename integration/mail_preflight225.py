"""Supplied native rows and candidate bytes agree only, never a send gate."""
_FIELDS = {'blob', 'binding', 'rows', 'now', 'date_field', 'displayed_receipts',
           'offset_minutes', 'offset_label', 'limit', 'recipient_set_fingerprint', 'nonce',
           'control_row', 'receipt_rows', 'article_rows', 'history_manifest'}
_NATIVE = ('control_row', 'receipt_rows', 'article_rows', 'recipient_set_fingerprint', 'history_manifest')
_FLAGS = {'send_allowed': False, 'ready': False, 'owner_approval': False,
          'source_authenticated': False, 'history_verified': False, 'current_state_verified': False,
          'receipt_membership_verified': False, 'source_complete': False, 'durable': False,
          'ledger_wired': False, 'production_wired': False}
_NOTE = ('These supplied rows and these supplied bytes agree only. Invented, omitted or stale inputs '
         'can pass; no authenticated read, completeness, freshness, current-inactive, delivery or authority. '
         'Sender scope 222 is not consumed; not a send gate.')


def _fail():
    raise ValueError('Composed preflight held') from None


def check_supplied(*, enabled=False, **args):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'preflight_match': False, 'note': _NOTE, **_FLAGS}
    matched = False
    try:
        if set(args) != _FIELDS or any(type(k) is not str for k in args):
            _fail()
        for key, cap in (('rows', 1000), ('receipt_rows', 128), ('article_rows', 10000)):
            if type(args[key]) is not list or len(args[key]) > cap or any(type(row) is not dict for row in args[key]):
                _fail()
        if type(args['control_row']) is not dict or type(args['binding']) is not dict:
            _fail()
        receipts = args['displayed_receipts']
        if type(receipts) is not dict or set(receipts) != {'email', 'telegram', 'whatsapp'} or any(type(k) is not str for k in receipts):
            _fail()
        if any(type(values) is not tuple or len(values) > 10000 for values in receipts.values()):
            _fail()
        import copy
        from integration.native_mail_projection224 import project_supplied
        from integration.mail_exclusion223 import check_supplied as check_view
        # Snapshot container structure without calling unvalidated scalar deepcopy hooks.
        # Immutable scalar leaves are validated by the owning stage; retain identity.
        def snapshot(value, depth=0):
            if depth > 12:
                _fail()
            if type(value) is dict:
                if any(type(k) is not str for k in value):
                    _fail()
                out = copy.copy(value)
                for k, v in value.items():
                    out[k] = snapshot(v, depth + 1)
                return out
            if type(value) is list:
                if len(value) > 10000:
                    _fail()
                return [snapshot(v, depth + 1) for v in value]
            if type(value) is tuple:
                if len(value) > 10000:
                    _fail()
                return tuple(snapshot(v, depth + 1) for v in value)
            return value
        before = snapshot(args)
        native = project_supplied(enabled=True, **{k: args[k] for k in _NATIVE})
        check_view(enabled=True, **{k: args[k] for k in _FIELDS if k not in ('control_row', 'receipt_rows', 'article_rows', 'history_manifest')},
                   exclusion_projection=native['projection'])
        if args != before:
            _fail()
        matched = True
    except Exception:
        pass
    if not matched:
        _fail()
    return {'state': 'supplied_composed_preflight_match', 'preflight_match': True, 'note': _NOTE, **_FLAGS}
