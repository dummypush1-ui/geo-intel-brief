# Copyright (c) 2026 Push. All rights reserved.
"""Fixture provenance only, never source-policy verification or permission."""
from .models import bounded, closed, fixture_id, text, timestamp

FIELDS = {'evidence_id', 'url', 'publisher', 'release', 'observed_at',
          'expires_at', 'rights_state', 'scope'}


def catalog(rows, *, as_of):
    now = timestamp(as_of)
    result = {}
    for row in bounded(rows, 2000):
        closed(row, FIELDS)
        key = fixture_id(row['evidence_id'])
        if key in result:
            raise ValueError('Duplicate evidence ID')
        # Deliberately not a connector URL: reserved synthetic fixture origin.
        if row['url'] != 'https://example.invalid/carrier-fixture':
            raise ValueError('Fixture-only evidence URL required')
        if row['rights_state'] != 'synthetic_fixture' or row['scope'] != 'fixture_only':
            raise ValueError('No source reuse or live-data assertions allowed')
        observed, expires = timestamp(row['observed_at']), timestamp(row['expires_at'])
        if observed > now or expires < observed:
            raise ValueError('Consistent evidence observation interval required')
        result[key] = {**row, 'publisher': text(row['publisher']), 'release': text(row['release']),
                       'state': 'stale' if now >= expires else 'fixture',
                       'verified_live': False}
    return result


def state(refs, evidence):
    return 'stale' if any(evidence[r]['state'] == 'stale' for r in refs) else 'fixture'
