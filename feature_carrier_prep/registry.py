# Copyright (c) 2026 Push. All rights reserved.
"""Exact fixture carrier/location registry. No real code list bundled."""
from .models import bounded, closed, fixture_id, references, text
from .evidence import state


def carriers(rows, evidence):
    result, aliases = {}, {}
    for row in bounded(rows, 200):
        closed(row, {'carrier_id', 'name', 'aliases', 'mode', 'evidence_ids'})
        key = fixture_id(row['carrier_id'])
        if key in result or row['mode'] != 'maritime':
            raise ValueError('Unique maritime carrier required')
        name = text(row['name'])
        supplied = [text(v) for v in bounded(row['aliases'], 10)]
        if len(set([name] + supplied)) != len([name] + supplied):
            raise ValueError('Duplicate exact carrier alias')
        for alias in [name] + supplied:
            if alias in aliases:
                raise ValueError('Ambiguous exact carrier alias')
            aliases[alias] = key
        refs = references(row['evidence_ids'], evidence)
        result[key] = {**row, 'aliases': supplied, 'evidence_ids': refs,
                       'state': state(refs, evidence)}
    return result


def locations(rows, evidence):
    result = {}
    for row in bounded(rows, 2000):
        closed(row, {'location_id', 'name', 'function', 'evidence_ids'})
        key = fixture_id(row['location_id'])
        if key in result or row['function'] != 'port':
            raise ValueError('Unique fixture port required')
        refs = references(row['evidence_ids'], evidence)
        result[key] = {**row, 'name': text(row['name']), 'evidence_ids': refs,
                       'state': state(refs, evidence)}
    return result


def lookup(carriers_by_id, name):
    text(name)
    matches = [r for r in carriers_by_id.values() if name == r['name'] or name in r['aliases']]
    return matches[0]['carrier_id'] if matches else None
