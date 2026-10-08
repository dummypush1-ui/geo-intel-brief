# Copyright (c) 2026 Push. All rights reserved.
"""Fixture milestones with explicit source revisions, no customer identifiers."""
from .models import bounded, closed, fixture_id, references, timestamp
from .evidence import state

FIELDS = {'event_id', 'subject_id', 'category', 'code', 'classifier', 'event_at',
          'source_recorded_at', 'revision', 'location_id', 'cancelled', 'evidence_ids'}
CODES = {'shipment': {'confirmed', 'documented'},
         'transport': {'arrived', 'departed'},
         'equipment': {'loaded', 'discharged', 'gate_in', 'gate_out'}}


def prepare(rows, locations, evidence, *, as_of):
    now = timestamp(as_of)
    current, revisions, by_event, parsed = {}, {}, {}, {}
    for row in bounded(rows, 5000):
        closed(row, FIELDS)
        key, subject = fixture_id(row['event_id']), fixture_id(row['subject_id'])
        revision = row['revision']
        if type(revision) is not int or not 1 <= revision <= 1000000:
            raise ValueError('Bounded integer source revision required')
        if type(row['category']) is not str or row['category'] not in CODES:
            raise ValueError('Supported milestone category required')
        if type(row['code']) is not str or row['code'] not in CODES[row['category']]:
            raise ValueError('Supported category-specific milestone code required')
        if row['classifier'] not in ('actual', 'planned', 'estimated') or type(row['cancelled']) is not bool:
            raise ValueError('Explicit classifier and cancellation state required')
        event_time, recorded = timestamp(row['event_at']), timestamp(row['source_recorded_at'])
        if recorded > now or row['classifier'] == 'actual' and event_time > recorded:
            raise ValueError('Actual event cannot follow source record; no future source records')
        location = fixture_id(row['location_id'])
        if location not in locations:
            raise ValueError('Known fixture port required')
        refs = references(row['evidence_ids'], evidence)
        item = {**row, 'evidence_ids': refs, 'state': state(refs, evidence), 'live': False}
        identity = (subject, row['category'], row['code'])
        old = current.get(key)
        if old and identity != (old['subject_id'], old['category'], old['code']):
            raise ValueError('Event identity cannot change between revisions')
        revision_key = (key, revision)
        if revision_key in revisions and revisions[revision_key] != item:
            raise ValueError('Conflicting same-revision source event')
        revisions[revision_key] = item
        if key in by_event and revision not in by_event[key] and len(by_event[key]) >= 32:
            raise ValueError('Maximum 32 revisions per fixture event')
        for seen_revision, seen in by_event.get(key, {}).items():
            seen_stamp = parsed[(key, seen_revision)]
            if revision > seen_revision and recorded < seen_stamp or revision < seen_revision and recorded > seen_stamp:
                raise ValueError('Revision order conflicts with source observation order')
        parsed[(key, revision)] = recorded
        by_event.setdefault(key, {})[revision] = item
        if old is None or revision > old['revision']:
            current[key] = item
    out = sorted(current.values(), key=lambda r: (timestamp(r['event_at']), r['event_id']))
    return {'items': out, 'scope': 'fixture_only', 'live_tracking': False,
            'deduplicated_input_count': len(rows) - len(revisions),
            'superseded_revision_count': len(revisions) - len(current),
            'retains_cancelled': True}
