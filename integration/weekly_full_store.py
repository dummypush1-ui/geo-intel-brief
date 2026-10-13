"""Each download scans the existing public Geo store, not a date-index query.
Read-only mutable scan, never a snapshot. No client construction or writes.
Budgets bound retained UTF8/rows, not Python overhead or live deployment capacity.
"""
import json
import time
from datetime import datetime, timezone
from integration.public_news import READ_STORE_FIELDS
from integration.public_weekly_pdf import _bounded_rows
from integration.weekly_report.report import _parse_dt

FLAG = 'PUBLIC_WEEKLY_FULL_STORE_ENABLED'
MAX_SCAN = 25000
MAX_ROWS = 2000
MAX_BYTES = 8 * 1024 * 1024
MAX_SECONDS = 10
SORT = [('_id', 1)]

class PeriodUnavailable(ValueError):
    pass

class StoreTooLarge(PeriodUnavailable):
    pass

class PeriodTooLarge(PeriodUnavailable):
    pass


def enabled(env):
    value = env.get(FLAG, 'false')
    if value not in ('true', 'false'):
        raise ValueError('Exact whole-store PDF flag required')
    if value == 'true' and any(env.get(k) != 'true' for k in (
            'PUBLIC_WEEKLY_PDF_ENABLED', 'PUBLIC_NEWS_READ_ENABLED',
            'PUBLIC_NEWS_FULL_PAGES_ENABLED')):
        raise ValueError('Whole-store PDF requires reviewed public whole-store reads')
    return value == 'true'


class PeriodReader:
    def __init__(self, store, *, clock=time.monotonic):
        if not callable(clock):
            raise ValueError('Clock required')
        self.store = store
        self.clock = clock

    def __call__(self, start, end):
        if any(type(d) is not datetime or d.tzinfo is None for d in (start, end)) or not start < end:
            raise PeriodUnavailable('Zoned period required')
        born = self.clock()
        cursor = None
        rows = []
        size = scanned = undated = duplicates = 0
        seen = set()
        def deadline():
            elapsed = self.clock() - born
            if not 0 <= elapsed <= MAX_SECONDS:
                raise PeriodUnavailable('Period source time budget')
        try:
            cursor = self.store.find({}, {k: 1 for k in READ_STORE_FIELDS})
            cursor.sort(list(SORT))
            cursor.batch_size(100)
            cursor.max_time_ms(2000)
            while True:
                deadline()
                try:
                    raw = next(cursor)
                except StopIteration:
                    break
                scanned += 1
                if scanned > MAX_SCAN:
                    raise StoreTooLarge('Store too large for this report')
                public = _bounded_rows({'geo': [raw]})
                if len(public) != 1:
                    raise PeriodUnavailable('Period source row unavailable')
                row = public[0]
                stamp = _parse_dt(row.get('published_at'))
                # A missing publication date is valid but cannot be placed in
                # the requested period. Invalid provided dates fail upstream.
                if stamp is None:
                    undated += 1
                    continue
                if not start <= stamp < end:
                    continue
                key = row['article_key']
                if key in seen:
                    duplicates += 1
                    continue
                if len(rows) >= MAX_ROWS:
                    raise PeriodTooLarge('Period too large for this report')
                size += len(json.dumps(row, ensure_ascii=False, allow_nan=False,
                                       separators=(',', ':')).encode('utf-8'))
                if size > MAX_BYTES:
                    raise PeriodTooLarge('Period text too large for this report')
                seen.add(key)
                rows.append(row)
            deadline()
            return rows, dict(scanned=scanned,undated=undated,duplicates=duplicates,
                              scanned_at=datetime.now(timezone.utc).isoformat())
        except (StoreTooLarge, PeriodTooLarge, PeriodUnavailable):
            raise
        except Exception:
            raise PeriodUnavailable('Period source unavailable') from None
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
