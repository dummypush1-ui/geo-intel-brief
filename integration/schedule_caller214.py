"""Pure Geo 205 ARM/TICK/acknowledge preparation, never job dispatch or timers."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json

_SCOPE = 'supplied_schedule_state_not_durable_or_execution_authority'
_FLAGS = {'send_allowed': False, 'dispatch_allowed': False, 'activation': False,
          'scope': _SCOPE}


class CallerRefused(ValueError):
    def __init__(self, reason='invalid'):
        self.reason = reason
        super().__init__('Schedule caller held: ' + reason)


def _fail(reason='invalid'):
    raise CallerRefused(reason) from None


def _clock(value):
    if type(value) is not datetime or value.tzinfo is not timezone.utc:
        _fail()
    return value.isoformat(timespec='microseconds')


def _stamp(value):
    if type(value) is not str:
        _fail('state')
    failed = False
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is not timezone.utc or result.isoformat(timespec='microseconds') != value:
            failed = True
    except (ValueError, OverflowError):
        failed = True
    if failed:
        _fail('state')
    return result


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def _settings(value):
    if type(value) is not dict or set(value) != {'GEO_SCHEDULER_TIMEZONE', 'GEO_WEEKLY_REPORT_DAY', 'GEO_DAILY_RUN_TIME'} or any(type(k) is not str or type(v) is not str for k, v in value.items()):
        _fail()
    failed = False
    try:
        from integration.scheduler_policy import profile_plan
        profile_plan('geo', value)
    except Exception:
        failed = True
    if failed:
        _fail()
    return dict(value)


def _cadences(value):
    if type(value) is not list or not 1 <= len(value) <= 2 or any(type(v) is not str or v not in ('daily', 'weekly') for v in value) or len(set(value)) != len(value):
        _fail()
    return sorted(value)


def _policies(ambiguous, nonexistent):
    if type(ambiguous) is not str or ambiguous not in ('first', 'second', 'refuse') or type(nonexistent) is not str or nonexistent not in ('skip', 'refuse'):
        _fail()


def _occurrence(settings, anchor, cadence, ambiguous, nonexistent):
    failed = False
    try:
        from integration.schedule_occurrence205 import next_occurrence
        evidence = next_occurrence(settings, anchor=_stamp(anchor), cadence=cadence,
                                   ambiguous=ambiguous, nonexistent=nonexistent)
    except Exception:
        failed = True
    if failed:
        _fail('calculation')
    # Hash canonical JSON, including skipped gaps, exact tzdata source/versions,
    # local offset/fold and both policies. No delimiter ambiguity or authority.
    identity = {'profile': 'geo', 'cadence': cadence, 'settings_hash': _hash(settings),
                'anchor': anchor, 'evidence': evidence, 'ambiguous': ambiguous,
                'nonexistent': nonexistent}
    return {'id': _hash(identity), 'cadence': cadence, 'evidence': evidence, **_FLAGS}


def arm(settings=None, *, anchor=None, cadences=None, ambiguous=None,
        nonexistent=None, enabled=False):
    """One next pending occurrence per cadence; OFF is argument/import inert."""
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return {'state': 'disabled', **_FLAGS}
    stamp = _clock(anchor)
    settings = _settings(settings)
    cadences = _cadences(cadences)
    _policies(ambiguous, nonexistent)
    return {'schema': 1, 'profile': 'geo', 'settings': settings,
            'settings_hash': _hash(settings), 'cadences': cadences,
            'ambiguous': ambiguous, 'nonexistent': nonexistent, 'last_seen': stamp,
            'anchors': {c: stamp for c in cadences},
            'occurrences': {c: _occurrence(settings, stamp, c, ambiguous, nonexistent) for c in cadences},
            **_FLAGS}


def _plain(value, depth=0, budget=None):
    if budget is None:
        budget = [0]
    budget[0] += 1
    if depth > 12 or budget[0] > 250:
        _fail('state')
    if type(value) in (str, int, bool) or value is None:
        if type(value) is int and not -2**53 <= value <= 2**53:
            _fail('state')
        if type(value) is str and len(value) > 500:
            _fail('state')
        return
    if type(value) is list:
        if len(value) > 2:
            _fail('state')
        for v in value:
            _plain(v, depth + 1, budget)
    elif type(value) is dict:
        if len(value) > 30 or any(type(k) is not str or len(k) > 100 for k in value):
            _fail('state')
        for v in value.values():
            _plain(v, depth + 1, budget)
    else:
        _fail('state')


def _validated(state):
    _plain(state)
    fields = {'schema', 'profile', 'settings', 'settings_hash', 'cadences',
              'ambiguous', 'nonexistent', 'last_seen', 'anchors', 'occurrences'} | set(_FLAGS)
    if type(state) is not dict or set(state) != fields or type(state['schema']) is not int or state['schema'] != 1 or type(state['profile']) is not str or state['profile'] != 'geo':
        _fail('state')
    if any(type(state[k]) is not type(v) or state[k] != v for k, v in _FLAGS.items()):
        _fail('state')
    settings = _settings(state['settings'])
    cadences = _cadences(state['cadences'])
    if cadences != state['cadences'] or type(state['settings_hash']) is not str or _hash(settings) != state['settings_hash']:
        _fail('changed')
    _policies(state['ambiguous'], state['nonexistent'])
    seen = _stamp(state['last_seen'])
    if type(state['anchors']) is not dict or set(state['anchors']) != set(cadences) or type(state['occurrences']) is not dict or set(state['occurrences']) != set(cadences):
        _fail('state')
    for cadence in cadences:
        _stamp(state['anchors'][cadence])
        # A late acknowledgement may advance a pending anchor beyond last_seen.
        # last_seen is still the last polled clock, never silently changed here.
        recomputed = _occurrence(settings, state['anchors'][cadence], cadence,
                                 state['ambiguous'], state['nonexistent'])
        # JSON equality distinguishes bool/int and verifies EVERY stored field,
        # including unknown keys, policies, skipped gaps, provenance and flags.
        if json.dumps(state['occurrences'][cadence], sort_keys=True, separators=(',', ':')) != json.dumps(recomputed, sort_keys=True, separators=(',', ':')):
            _fail('changed')
    return deepcopy(state), seen


def tick(state, *, now, max_lateness_seconds):
    """Return waiting/due/missed_held preparation, NEVER a dispatch permit."""
    stamp = _clock(now)
    if type(max_lateness_seconds) is not int or not 0 <= max_lateness_seconds <= 3600:
        _fail()
    copied, seen = _validated(state)
    if now < seen:
        _fail('clock_rollback')
    copied['last_seen'] = stamp
    results = []
    for cadence in copied['cadences']:
        occurrence = copied['occurrences'][cadence]
        evidence = occurrence['evidence']
        if evidence['state'] == 'none_in_window':
            status = 'held_no_occurrence'
        else:
            due = datetime.fromisoformat(evidence['utc'])
            seconds = (now - due).total_seconds()
            status = 'waiting' if seconds < 0 else 'due' if seconds <= max_lateness_seconds else 'missed_held'
        results.append({**deepcopy(occurrence), 'state': status, **_FLAGS})
    stamps = [r['evidence']['utc'] for r in results if r['evidence']['utc'] is not None]
    coincident = len(stamps) > 1 and len(set(stamps)) < len(stamps)
    return {'state': copied, 'occurrences': results, 'coincident': coincident,
            'note': 'dispatch_not_allowed', **_FLAGS}


def acknowledge_occurrence(state, occurrence_id):
    """Pure observation acknowledgement, NOT durable job/send acknowledgement.
    Future trusted caller owns provenance/authority and persistence. No callbacks.
    """
    if type(occurrence_id) is not str:
        _fail()
    copied, _ = _validated(state)
    matches = [c for c in copied['cadences'] if copied['occurrences'][c]['id'] == occurrence_id]
    if len(matches) != 1:
        _fail('unknown_occurrence')
    cadence = matches[0]
    evidence = copied['occurrences'][cadence]['evidence']
    if evidence['state'] != 'next' or evidence['utc'] is None:
        _fail('no_occurrence')
    # Anchor = observed occurrence UTC, NEVER current time. Late polls cannot
    # silently skip occurrences or cause a backfill flood.
    anchor = _clock(datetime.fromisoformat(evidence['utc']))
    copied['anchors'][cadence] = anchor
    copied['occurrences'][cadence] = _occurrence(copied['settings'], anchor, cadence,
                                               copied['ambiguous'], copied['nonexistent'])
    return copied
