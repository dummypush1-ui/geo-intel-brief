"""Loaded Geo critical stories, explicit UTC rolling24-hour clock.

Preserves supplied risk labels; never classifies, fetches or sends an alert.
Other-project critical policy is not inferred from Geo risk or keywords.
"""
from datetime import datetime, timezone
from integration.dashboard_model import date_view


def critical_stories(rows, now):
    if type(rows) is not list or type(now) is not datetime or now.tzinfo is None:
        raise ValueError('Loaded rows and explicit zoned clock required')
    now = now.astimezone(timezone.utc)
    selected = []
    missing = future = outside = unsupported = 0
    for row in rows:
        if row.get('project') != 'geo':
            unsupported += 1
            continue
        if row.get('risk_level') != 'CRITICAL':
            continue
        stamp = date_view(row.get('collected_at'))
        if not stamp:
            missing += 1
            continue
        age = (now - datetime.fromisoformat(stamp)).total_seconds()
        if age < 0:
            future += 1
        elif age > 86400:
            outside += 1
        else:
            selected.append(row)
    selected.sort(key=lambda row: row['collected_at'], reverse=True)
    # Rows are normalized read views. Do not expose legacy IDs or sent state.
    items = [{key: value for key, value in row.items()
              if key not in ('mongo_id', 'legacy_id', 'emailed', 'original_url')}
             for row in selected[:100]]
    return {'items': items, 'scope': 'loaded_read_view', 'not_total_database': True,
            'policy': 'supplied_geo_critical_risk_only', 'as_of': now.isoformat(),
            'window_hours': 24, 'count': len(selected), 'limit': 100,
            'truncated': len(selected) > 100, 'missing_time_count': missing,
            'future_time_count': future, 'outside_window_count': outside,
            'other_project_policy_unavailable_count': unsupported,
            'delivery': False}
