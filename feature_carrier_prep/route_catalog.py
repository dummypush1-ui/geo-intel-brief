# Copyright (c) 2026 Push. All rights reserved.
"""Ordered source-backed fixture legs; no geometry, rate or ETA inference."""
from .models import bounded, closed, fixture_id, references, text, timestamp
from .evidence import state


def catalog(rows, carriers, locations, evidence, *, as_of):
    now = timestamp(as_of)
    result = {}
    for row in bounded(rows, 1000):
        closed(row, {'route_id', 'carrier_id', 'service', 'valid_from', 'valid_until', 'legs', 'evidence_ids'})
        key, carrier = fixture_id(row['route_id']), fixture_id(row['carrier_id'])
        if key in result or carrier not in carriers:
            raise ValueError('Unique route and known carrier required')
        begin, end = timestamp(row['valid_from']), timestamp(row['valid_until'])
        if end < begin:
            raise ValueError('Ordered route validity required')
        legs, previous_port, previous_time = [], None, None
        for leg in bounded(row['legs'], 20):
            closed(leg, {'origin', 'destination', 'departure_at', 'arrival_at', 'classifier'})
            origin, destination = fixture_id(leg['origin']), fixture_id(leg['destination'])
            if origin not in locations or destination not in locations or origin == destination:
                raise ValueError('Two known distinct ports required')
            if previous_port is not None and previous_port != origin:
                raise ValueError('Continuous ordered route required')
            if leg['classifier'] not in ('actual', 'planned', 'estimated'):
                raise ValueError('Explicit timing classifier required')
            dep, arr = timestamp(leg['departure_at']), timestamp(leg['arrival_at'])
            if not begin <= dep <= arr <= end or previous_time is not None and dep < previous_time:
                raise ValueError('Chronological bounded route legs required')
            if leg['classifier'] == 'actual' and arr > now:
                raise ValueError('Actual route leg cannot be in the future')
            legs.append(dict(leg))
            previous_port, previous_time = destination, arr
        if not legs:
            raise ValueError('Route requires evidence-backed legs')
        refs = references(row['evidence_ids'], evidence)
        result[key] = {**row, 'service': text(row['service']), 'legs': legs,
                       'evidence_ids': refs, 'state': ('stale' if now >= end else 'not_yet_valid' if now < begin else state(refs, evidence)), 'live': False}
    return result
