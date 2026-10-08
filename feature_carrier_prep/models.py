# Copyright (c) 2026 Push. All rights reserved.
"""Closed bounded fixture schemas; no bindings, storage or network calls."""
from datetime import datetime, timezone
from ipaddress import ip_address
import re

ID = re.compile(r'fixture:[a-z][a-z0-9_-]{0,63}', re.ASCII)


def text(value, limit=200):
    if (type(value) is not str or not value or len(value) > limit
            or value.strip() != value
            or any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise ValueError('Bounded nonblank plain text required')
    return value


def fixture_id(value):
    if type(value) is not str or not ID.fullmatch(value):
        raise ValueError('Obvious fixture namespace required')
    return value


def closed(row, fields):
    if type(row) is not dict or set(row) != set(fields):
        raise ValueError('Closed plain record required')
    return row


def bounded(rows, cap):
    if type(rows) is not list or len(rows) > cap:
        raise ValueError('Bounded plain list required')
    return rows


def ids(values, cap=20):
    bounded(values, cap)
    out = [fixture_id(v) for v in values]
    if not out or len(set(out)) != len(out):
        raise ValueError('Nonempty unique fixture references required')
    return out


def timestamp(value):
    text(value, 40)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value, re.ASCII):
        raise ValueError('Explicit offset timestamp required')
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        # Exercise UTC conversion to reject overflowing boundary timestamps.
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError('Valid offset timestamp required') from None


def loopback_host(host):
    """Future preview guard only; this increment does not bind a server."""
    if type(host) is not str:
        raise ValueError('Literal loopback IP required')
    try:
        addr = ip_address(host)
    except ValueError:
        raise ValueError('Literal loopback IP required') from None
    if not addr.is_loopback or '%' in host:
        raise ValueError('Literal loopback IP required')
    return host


def references(values, evidence):
    out = ids(values)
    if any(v not in evidence for v in out):
        raise ValueError('Missing evidence reference')
    return out
