"""Supplied source-check observations only. No requests or source probes.

Errors are enum codes, not raw provider messages that might contain secrets.
A recorded successful check never asserts that the source is healthy now.
"""
from copy import deepcopy
from datetime import datetime, timezone
from integration.dashboard_model import date_view


class SourceHealthSnapshot:
    __slots__ = ('_data',)

    def __init__(self, data):
        if type(data) is not dict or any(type(k) is not str for k in data) or set(data) != {'observed_at', 'items'}:
            raise ValueError('Exact supplied observation required')
        stamp = date_view(data['observed_at']) if type(data['observed_at']) is str else None
        if not stamp or type(data['items']) is not list or len(data['items']) > 1000:
            raise ValueError('Zoned bounded source observation required')
        normalized = []
        for row in data['items']:
            if type(row) is not dict or any(type(k) is not str for k in row) or any(type(row.get(k)) is not str or not row[k].strip()
                                           or len(row[k]) > 200 for k in ('name', 'project')):
                raise ValueError('Source name/project required')
            if row['project'] not in ('geo', 'brics'):
                raise ValueError('Known project required')
            status = row.get('status')
            if type(status) is not str or status not in ('ok', 'warning', 'error', 'disabled', 'unknown'):
                raise ValueError('Exact source status required')
            count = row.get('count')
            if count is not None and (type(count) is not int or not 0 <= count <= 1000000):
                raise ValueError('Bounded fetched count required')
            checked = row.get('checked_at')
            if checked is not None and (type(checked) is not str or not date_view(checked)):
                raise ValueError('Zoned check time required')
            code = row.get('error_code')
            if code is not None and (type(code) is not str or code not in
                    ('timeout', 'http_error', 'parse_error', 'network_error', 'config_error', 'unknown_error')):
                raise ValueError('Safe error enum required')
            if status == 'ok' and code is not None:
                raise ValueError('Successful check cannot contain an error code')
            normalized.append({'name': row['name'], 'project': row['project'], 'status': status,
                               'count': count, 'checked_at': date_view(checked) if checked else None,
                               'error_code': code})
        self._data = {'observed_at': stamp, 'items': normalized}

    def view(self, now):
        if type(now) is not datetime or now.tzinfo is None:
            raise ValueError('Explicit zoned clock required')
        data = deepcopy(self._data)
        age = (now.astimezone(timezone.utc) - datetime.fromisoformat(data['observed_at'])).total_seconds()
        if age < 0:
            raise ValueError('Future source observation rejected')
        for row in data['items']:
            if row['checked_at'] and row['checked_at'] > data['observed_at']:
                raise ValueError('Check time exceeds observation')
        data['items'].sort(key=lambda row: (row['project'], row['name'].casefold(), row['checked_at'] or ''))
        data.update(state='supplied_snapshot', not_live_status=True, age_seconds=int(age),
                    total_supplied=len(data['items']), truncated=len(data['items']) > 100,
                    scope='supplied_source_checks', network=False)
        data['items'] = data['items'][:100]
        return data
