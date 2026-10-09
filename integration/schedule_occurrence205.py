"""Pure next-occurrence calculation, with explicit zone data and DST policies."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib import metadata, resources
from pathlib import Path
from zoneinfo import TZPATH, ZoneInfo

from integration.scheduler_policy import DAYS, ScheduleRefused, profile_plan


class OccurrenceRefused(ValueError):
    """Static errors do not echo settings."""


def _refuse():
    raise OccurrenceRefused('Schedule occurrence refused')


def _zone(key):
    """Use the bytes we hash, without ZoneInfo's process cache."""
    try:
        package_version = metadata.version('tzdata')
    except metadata.PackageNotFoundError:
        package_version = None
    for root in TZPATH:
        path = Path(root).joinpath(*key.split('/'))
        if path.is_file():
            data = path.read_bytes()
            version_file = Path(root) / 'tzdata.zi'
            version = None
            if version_file.is_file():
                first = version_file.read_text(encoding='utf-8').splitlines()[0]
                if first.startswith('# version '):
                    version = first[len('# version '):]
            from io import BytesIO
            return ZoneInfo.from_file(BytesIO(data), key=key), {
                'source': 'system_TZPATH', 'system_tzdata_version': version,
                'tzdata_package_version': package_version,
                'zonefile_sha256': sha256(data).hexdigest(),
            }
    try:
        resource = resources.files('tzdata.zoneinfo').joinpath(*key.split('/'))
        data = resource.read_bytes()
        from io import BytesIO
        return ZoneInfo.from_file(BytesIO(data), key=key), {
            'source': 'tzdata_package', 'system_tzdata_version': None,
            'tzdata_package_version': package_version,
            'zonefile_sha256': sha256(data).hexdigest(),
        }
    except Exception:
        _refuse()


def next_occurrence(settings, *, anchor, cadence, ambiguous, nonexistent):
    """Next Geo report wall-time strictly after an exact UTC anchor.

    Fifteen local dates, including anchor's local date, are inspected. This is
    calculation only: no missed-occurrence report, catch-up, timer or job.
    """
    if type(anchor) is not datetime or anchor.tzinfo is not timezone.utc:
        _refuse()
    if type(cadence) is not str or cadence not in ('daily', 'weekly'):
        _refuse()
    if type(ambiguous) is not str or ambiguous not in ('first', 'second', 'refuse'):
        _refuse()
    if type(nonexistent) is not str or nonexistent not in ('skip', 'refuse'):
        _refuse()
    try:
        plan = profile_plan('geo', settings)
        if plan['timezone'] in ('localtime', 'posixrules', 'Factory'):
            _refuse()
        zone, provenance = _zone(plan['timezone'])
        local_anchor = anchor.astimezone(zone)
        hour, minute = map(int, plan['time'].split(':'))
        requested_weekday = DAYS.index(plan['weekday'])
        base = {
            'scope': 'next_after_anchor_calculation_only', 'profile': 'geo',
            'cadence': cadence, 'timezone': plan['timezone'],
            'ambiguous_policy': ambiguous, 'nonexistent_policy': nonexistent,
            'tzdata': provenance, 'search_local_dates': 15,
            'timer_installed': False, 'activation_allowed': False,
            'catch_up': False,
        }
        skipped = 0
        for offset in range(15):
            day = local_anchor.date() + timedelta(days=offset)
            if cadence == 'weekly' and day.weekday() != requested_weekday:
                continue
            wall = datetime(day.year, day.month, day.day, hour, minute)
            candidates = {}
            for fold in (0, 1):
                candidate = wall.replace(tzinfo=zone, fold=fold)
                utc = candidate.astimezone(timezone.utc)
                back = utc.astimezone(zone)
                if back.replace(tzinfo=None) == wall and back.fold == fold:
                    candidates[fold] = (utc, back)
            if not candidates:
                # A gap already in the local past is not a next occurrence.
                if wall <= local_anchor.replace(tzinfo=None):
                    continue
                if nonexistent == 'refuse':
                    _refuse()
                skipped += 1
                continue
            if len(candidates) == 2:
                # Never refuse an ambiguous wall time whose repeats both passed.
                if all(utc <= anchor for utc, _ in candidates.values()):
                    continue
                if ambiguous == 'refuse':
                    _refuse()
                selected = candidates[0 if ambiguous == 'first' else 1]
            else:
                selected = next(iter(candidates.values()))
            utc, local = selected
            if utc <= anchor:
                continue
            return dict(base, state='next', utc=utc.isoformat(),
                        local=local.isoformat(), offset_seconds=int(local.utcoffset().total_seconds()),
                        fold=local.fold, local_weekday=DAYS[local.weekday()],
                        skipped_nonexistent=skipped)
        return dict(base, state='none_in_window', utc=None, local=None,
                    offset_seconds=None, fold=None, local_weekday=None,
                    skipped_nonexistent=skipped)
    except OccurrenceRefused:
        raise
    except (ScheduleRefused, ValueError, TypeError, OverflowError, OSError, IndexError):
        _refuse()
