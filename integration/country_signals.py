"""Experimental supplied-country counts. No threat rating, I/O or classification.

Copyright (c) 2026 Push. Independently written.
"""
from collections import Counter
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta, timezone

MAX_ROWS = 10000
MAX_KEY = 128
MAX_TIMESTAMP = 100

LEVELS = ('CRITICAL', 'HIGH', 'MODERATE', 'LOW')

def stamp(value):
    if type(value) is str and len(value) > MAX_TIMESTAMP:
        return None
    if type(value) not in (str, datetime):
        return None
    try:
        result = value if type(value) is datetime else datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or type(result.tzinfo) is not timezone:
            return None
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None

def country_signals(rows, country, now):
    if type(country) is not str or not country or country.strip() != country or len(country) > 100 or any(ord(c) < 32 or ord(c) == 127 for c in country):
        raise ValueError('Exact country label required')
    now = stamp(now)
    if now is None:
        raise ValueError('Zoned clock required')
    try:
        cutoff = now - timedelta(days=28)
    except OverflowError:
        raise ValueError('Clock must support a 28-day lookback') from None
    if type(rows) not in (list, tuple) or len(rows) > MAX_ROWS:
        raise ValueError('Supply at most 10000 rows as a list or tuple')
    selected, seen = [], set()
    for row in rows:
        if type(row) is not dict:
            raise ValueError('Plain row dictionaries required')
        if len(row) > 100 or any(type(key) is not str for key in row):
            raise ValueError('At most 100 exact string row keys required')
        limits = {'original_country':100,'project':5,'article_key':MAX_KEY,
                  'collected_at':MAX_TIMESTAMP,'published_at':MAX_TIMESTAMP,'risk_level':16}
        for field, limit in limits.items():
            value = row.get(field)
            if value is None:
                continue
            if field in ('collected_at','published_at') and type(value) is datetime:
                if value.tzinfo is not None and type(value.tzinfo) is not timezone:
                    raise ValueError('Fixed-offset timestamp required')
                continue
            if type(value) is not str or len(value) > limit:
                raise ValueError('Invalid or oversized signal field')
        if row.get('original_country') != country or row.get('project') != 'geo':
            continue
        key = row.get('article_key')
        if not isinstance(key, str) or not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        selected.append(row)
    # Collection time measures ingestion, publication time measures the story.
    # Keep both timelines separate. Missing collection times have no fallback.
    times = [stamp(r.get('collected_at')) for r in selected]
    valid_times = [t for t in times if t is not None and t <= now]
    recent = [r for r,t in zip(selected,times) if t is not None and cutoff <= t <= now]
    published = [stamp(r.get('published_at')) for r in selected]
    earliest = min(valid_times) if valid_times else None
    span = (now-earliest).total_seconds()/86400 if earliest else None
    history = 'insufficient_history' if span is None or span < 28 else 'observed_span_only'
    risk = Counter(r.get('risk_level') for r in recent if r.get('risk_level') in LEVELS)
    return {
        'country':country, 'project':'geo', 'scope':'loaded_supplied_snapshot',
        'experimental':True, 'not_total_database':True, 'not_unique_story_count':True,
        'as_of':now.isoformat(), 'window_start':cutoff.isoformat(), 'window_days':28,
        'window_interval':'closed_28_day_elapsed_interval',
        'loaded_distinct_article_keys':len(selected), 'collected_28d_count':len(recent),
        'published_28d_count':sum(t is not None and cutoff <= t <= now for t in published),
        'missing_collection_time_count':sum(t is None for t in times),
        'future_collection_time_count':sum(t is not None and t > now for t in times),
        'missing_publication_time_count':sum(t is None for t in published),
        'future_publication_time_count':sum(t is not None and t > now for t in published),
        'stored_risk_level_counts':{k:risk[k] for k in LEVELS},
        'missing_risk_level_28d_count':sum(r.get('risk_level') not in LEVELS for r in recent),
        'observed_active_date_labels_in_window':len({t.date() for t in valid_times if t >= cutoff}),
        'earliest_observed_collection':earliest.isoformat() if earliest else None,
        'observed_history_days':float(Decimal(str(span)).quantize(Decimal('0.001'), rounding=ROUND_DOWN)) if span is not None else None,
        'history_state':history, 'coverage_verified':False,
        'risk_index':None, 'risk_index_state':history if history=='insufficient_history' else 'methodology_and_coverage_unverified',
        'baseline':None, 'baseline_state':'unavailable_without_verified_complete_daily_coverage',
        'network':False, 'delivery':False,
    }
