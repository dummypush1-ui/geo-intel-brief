"""Strict supplied publication evidence, no clock-based fallback."""
from datetime import datetime, timezone
import re
from dateutil import parser

HOLD_STATES = ('missing', 'invalid', 'incomplete', 'naive_timezone', 'unknown_timezone', 'future')

def publication_date(value, observed_at):
    if type(observed_at) is not datetime or observed_at.tzinfo is None:
        raise ValueError('Explicit aware observation required')
    if type(value) is not str or not value.strip():
        return None, 'missing'
    if len(value) > 256:
        return None, 'invalid'
    if re.search(r'(?:UTC|GMT|Z)\s*[+-]\s*\d', value, re.IGNORECASE):
        return None, 'invalid'
    if re.search(r'(?:UTC|GMT|Z).*?[+-]\d{2}:?\d{2}', value, re.IGNORECASE):
        return None, 'invalid'
    def strict_tz(name, offset):
        # dateutil may recognize host-local abbreviations before warnings.
        if name not in (None, 'UTC', 'GMT', 'Z'):
            raise LookupError('Unverified zone name')
        if name in ('UTC', 'GMT', 'Z') and offset not in (None, 0):
            raise ValueError('Named offset is ambiguous')
        if offset is None:
            return timezone.utc if name in ('UTC', 'GMT', 'Z') else None
        if abs(offset) > 14 * 3600:
            raise OverflowError('Offset outside reviewed range')
        from datetime import timedelta
        return timezone(timedelta(seconds=offset))
    try:
        a = parser.parse(value, default=datetime(2000, 1, 1), fuzzy=False, tzinfos=strict_tz)
        b = parser.parse(value, default=datetime(2004, 12, 28), fuzzy=False, tzinfos=strict_tz)
        if (a.year, a.month, a.day) != (b.year, b.month, b.day):
            return None, 'incomplete'
        if a.tzinfo is None or a.utcoffset() is None:
            return None, 'naive_timezone'
        result = a.astimezone(timezone.utc)
        if result > observed_at.astimezone(timezone.utc):
            return None, 'future'
        return result, 'verified'
    except LookupError:
        return None, 'unknown_timezone'
    except (ValueError, TypeError, OverflowError):
        return None, 'invalid'
