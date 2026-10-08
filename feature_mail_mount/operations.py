# Copyright (c) 2026 Push. All rights reserved.
"""Pure explicit mail schedule and recovery contracts; no installation/effects.

Plans do not authorize sends, acknowledgement, state deletion or new attempts.
Snapshot reconciliation must use current bridge and durable server evidence at
execution time. Unknown sends always hold; no expiry or missing row proves safe
resend. Existing non-mail/legacy triggers are never deleted by this contract.
"""
import re

HANDLERS = {'digest': 'mailV1Digest', 'critical': 'mailV1Critical', 'weekly': 'mailV1Weekly'}
FIELDS = {'digest_times', 'digest_interval_hours', 'critical_interval_minutes', 'weekly_day', 'weekly_time', 'timezone'}


def _hhmm(value):
    if type(value) is not str or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', value):
        raise ValueError('Exact 24h HH:MM required')
    return value


def schedule_plan(config):
    if type(config) is not dict or set(config) != FIELDS:
        raise ValueError('Closed explicit schedule required')
    timezone = config['timezone']
    if type(timezone) is not str or not 1 <= len(timezone) <= 100:
        raise ValueError('Explicit IANA timezone required')
    from zoneinfo import ZoneInfo
    try: ZoneInfo(timezone)
    except Exception: raise ValueError('Known IANA timezone required') from None
    times, interval = config['digest_times'], config['digest_interval_hours']
    if type(times) is not list or len(times) > 10 or type(interval) is not int:
        raise ValueError('Bounded digest schedule required')
    times = [_hhmm(t) for t in times]
    if len(set(times)) != len(times) or (bool(times) == bool(interval)) or interval not in (0, 1, 2, 4, 6, 8, 12):
        raise ValueError('Choose times OR supported interval, not both')
    critical = config['critical_interval_minutes']
    if type(critical) is not int or critical not in (0, 1, 5, 10, 15, 30):
        raise ValueError('Explicit supported critical interval or zero-off required')
    day, weekly = config['weekly_day'], config['weekly_time']
    if type(day) is not str or day not in ('', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY') or type(weekly) is not str or bool(day) != bool(weekly):
        raise ValueError('Weekly day/time together or both empty-off required')
    if weekly: _hhmm(weekly)
    triggers = []
    if interval:
        triggers.append({'handler': HANDLERS['digest'], 'style': 'hours', 'interval': interval})
    else:
        triggers.extend({'handler': HANDLERS['digest'], 'style': 'daily_approximate', 'time': t} for t in times)
    if critical:
        triggers.append({'handler': HANDLERS['critical'], 'style': 'minutes', 'interval': critical})
    if weekly:
        triggers.append({'handler': HANDLERS['weekly'], 'style': 'weekly_approximate', 'day': day, 'time': weekly})
    return {'scope': 'schedule_proposal_not_installed', 'timezone': timezone,
            'triggers': triggers, 'managed_handlers': list(HANDLERS.values()),
            'delete_other_triggers': False, 'enable_mail': False,
            'clock_precision': 'Apps_Script_approximate_not_exact',
            'installation_allowed': False, 'collection_trigger': False}


def recovery_plan(bridge, receipt):
    """A read-only proposed next step, never send permission or receipt proof."""
    bf = {'receipt', 'hash', 'attempt', 'phase'}
    rf = {'receipt', 'hash', 'attempt', 'state', 'scope'}
    if type(bridge) is not dict or set(bridge) != bf or type(receipt) is not dict or set(receipt) != rf:
        raise ValueError('Closed recovery snapshots required')
    for value in (bridge['receipt'], receipt['receipt'], bridge['hash'], receipt['hash']):
        if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise ValueError('Exact SHA bindings required')
    for value in (bridge['attempt'], receipt['attempt']):
        if value is not None and (type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{20,80}', value)):
            raise ValueError('Opaque attempt required')
    phase, state = bridge['phase'], receipt['state']
    if type(phase) is not str or phase not in ('pending', 'bound', 'claiming', 'sending', 'send_returned') or type(state) is not str or state not in ('prepared', 'started', 'acknowledged', 'skipped'):
        raise ValueError('Known bridge/server phase required')
    scope = receipt['scope']
    if scope != ('bridge_send_returned_not_delivery' if state == 'acknowledged' else 'no_send_proof'):
        raise ValueError('Honest receipt scope required')
    if state in ('started', 'acknowledged') and receipt['attempt'] is None or state in ('prepared', 'skipped') and receipt['attempt'] is not None:
        raise ValueError('Server state/attempt mismatch')
    bound = bridge['receipt'] == receipt['receipt'] and bridge['hash'] == receipt['hash']
    same_attempt = bridge['attempt'] is not None and bridge['attempt'] == receipt['attempt']
    action = 'hold_manual_reconciliation'
    if bound and same_attempt and state == 'acknowledged':
        action = 'propose_clear_pending_after_current_readback'
    elif bound and same_attempt and state == 'started' and phase == 'send_returned':
        action = 'propose_ack_only_no_send'
    elif bound and state == 'prepared' and phase in ('pending', 'bound'):
        action = 'propose_resume_existing_nonce_via_normal_claim'
    elif bound and state == 'skipped' and phase in ('pending', 'bound'):
        action = 'propose_clear_skipped_after_current_readback'
    return {'scope': 'supplied_snapshots_not_execution_authority', 'proposal': action,
            'send_allowed': False, 'clear_allowed': False, 'ack_allowed': False,
            'new_nonce_allowed': False, 'automatic_retry': False,
            'delivery_verified': False, 'current_evidence_required': True}
