"""Consistency of supplied exclusion assertions only. No ledger evidence."""
_FIELDS = {'blob', 'binding', 'rows', 'now', 'date_field', 'displayed_receipts',
           'offset_minutes', 'offset_label', 'limit', 'recipient_set_fingerprint', 'nonce',
           'exclusion_projection'}
_VIEW_FIELDS = {'schema', 'logical_channel', 'purpose', 'acknowledged_ids', 'active_state'}
_FLAGS = {'send_allowed': False, 'ready': False, 'owner_approval': False,
          'receipt_membership_verified': False, 'history_complete': False,
          'source_complete': False, 'durable': False, 'ledger_wired': False}
_NOTE = ('Supplied exclusion view consistency only: two caller-supplied lists agree, not ledger reads. '
         'Omission in both views and stale views can pass; caller asserts no active control, not proof.')


def _fail():
    raise ValueError('Exclusion view held') from None


def check_supplied(*, enabled=False, **args):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', 'consistency_match': False, 'note': _NOTE, **_FLAGS}
    matched = False
    try:
        if set(args) != _FIELDS or any(type(k) is not str for k in args):
            _fail()
        view, receipts = args['exclusion_projection'], args['displayed_receipts']
        if type(view) is not dict or set(view) != _VIEW_FIELDS or any(type(k) is not str for k in view):
            _fail()
        if type(view['schema']) is not str or view['schema'] != 'mail_exclusion_projection223_v1' or type(view['purpose']) is not str or view['purpose'] != 'digest':
            _fail()
        if view['active_state'] is not None:
            # Includes prepared/started: hold the whole asserted channel+purpose.
            _fail()
        if type(receipts) is not dict or set(receipts) != {'email', 'telegram', 'whatsapp'} or any(type(k) is not str for k in receipts):
            _fail()
        tuples = [view['acknowledged_ids']] + list(receipts.values())
        if any(type(values) is not tuple or len(values) > 10000 for values in tuples):
            _fail()
        # Caps checked before uniqueness conversion, copy or renderer.
        from bson import ObjectId
        import copy
        from integration.mail_rederive221 import verify_rederived
        from integration.mail_candidate219 import verify_snapshot, HEX
        for values in tuples:
            if any(type(v) is not ObjectId for v in values) or len(set(values)) != len(values):
                _fail()
        if type(view['logical_channel']) is not str or HEX.fullmatch(view['logical_channel']) is None:
            _fail()
        if set(view['acknowledged_ids']) != set(receipts['email']):
            _fail()
        before = copy.deepcopy(receipts)
        #221 checks independent expected fp/nonce then fully re-freezes219.
        result = verify_rederived(enabled=True, **{k: v for k, v in args.items() if k != 'exclusion_projection'})
        if result['row_derivation_match'] is not True or receipts != before:
            _fail()
        candidate = verify_snapshot(args['blob'], args['binding'])
        if view['logical_channel'] != args['binding']['proposed_channel']:
            _fail()
        if set(candidate['sorted_union_ids']) & {str(v) for v in view['acknowledged_ids']}:
            _fail()
        matched = True
    except Exception:
        pass
    if not matched:
        _fail()
    return {'state': 'supplied_exclusion_consistent', 'consistency_match': True, 'note': _NOTE, **_FLAGS}
