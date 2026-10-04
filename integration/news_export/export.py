# Copyright (c) 2026 Push
"""CSV export of supplied public-news rows. Pure Python: no database client, no
network, no file or config reads, no threads. Callers supply rows or a pager.

Two entry points
  snapshot_export(rows, args, ...)  rows already in memory (the bounded staging view,
                                    default max 2000). Result headers are exact.
  stream_export(pager, args, ...)   incremental export over a caller-supplied pager
                                    with hard per-project caps (defaults mirror the
                                    original apps: geo 1,000,000, brics 5,000).
                                    The live pager is NOT part of this module.

Columns and cell rules match integration.loaded_news (FIELDS, csv_cell, CRLF, UTF-8
without BOM by default). Only the closed FIELDS list is ever read from a row, so
private or unknown keys cannot reach the file."""
import csv
import io
import re
import time
import unicodedata

FIELDS = ('project', 'title', 'source', 'original_country', 'category', 'published_at', 'collected_at',
          'risk_level', 'credibility', 'score', 'corroboration_count', 'url', 'summary')
CELL_LIMIT = 8000
SNAPSHOT_MAX_ROWS = 2000
DEFAULT_CAPS = {'geo': 1000000, 'brics': 5000}
PROJECTS = ('geo', 'brics')
PAGE_SIZE = 500
MAX_PAGE_SIZE = 1000
MAX_BYTES = 256 * 1024 * 1024
MAX_SECONDS = 120.0
BATCH_ROWS = 100
ALLOWED_ARGS = ('project', 'category')
_CATEGORY_RE = re.compile(r'^[A-Za-z0-9 _-]{1,60}$')


class ExportRequestError(ValueError):
    """Bad request arguments (caller answers 400)."""


class ExportUnavailable(Exception):
    """The source could not supply the first page (caller answers 503)."""


def csv_cell(value):
    """Same behaviour as loaded_news.csv_cell: bounded text, NUL removed, lone surrogates
    replaced, and a leading apostrophe when the first visible character is = + - @ or the
    cell starts with tab/CR/LF, including operators hidden behind whitespace or format
    characters. Numbers are plain text here too, so a negative score becomes '-3 as in
    the existing sample export."""
    if value is None:
        return ''
    text = str(value)[:CELL_LIMIT].replace('\x00', '')
    text = ''.join('\ufffd' if unicodedata.category(c) == 'Cs' else c for c in text)
    probe = text.lstrip()
    while probe and unicodedata.category(probe[0])[0] in ('Z', 'C'):
        probe = probe[1:]
    if text.startswith(('\t', '\r', '\n')) or probe.startswith(('=', '+', '-', '@')):
        text = "'" + text
    return text


def parse_args(args):
    """Exact allow-listed arguments only; unknown names, repeats and bad values raise."""
    if args is None:
        args = {}
    if not isinstance(args, dict):
        raise ExportRequestError('bad args')
    if any(k not in ALLOWED_ARGS for k in args):
        raise ExportRequestError('unknown argument')
    out = {}
    for k in ALLOWED_ARGS:
        v = args.get(k, '')
        if isinstance(v, (list, tuple, dict, set)):
            raise ExportRequestError('repeated or structured argument')
        if v in ('', None):
            out[k] = None
            continue
        if not isinstance(v, str):
            raise ExportRequestError('bad value')
        if k == 'project' and v not in PROJECTS:
            raise ExportRequestError('unknown project')
        if k == 'category' and not _CATEGORY_RE.fullmatch(v):
            raise ExportRequestError('bad category')
        out[k] = v
    return out


def filename(project=None, category=None, kind='export'):
    """Fixed server-built name from validated values only; never a caller path."""
    parts = ['geo-intel-news', kind]
    if project:
        parts.append(project)
    if category:
        slug = re.sub(r'[^A-Za-z0-9_-]+', '-', category).strip('-').lower()[:40]
        if slug:
            parts.append(slug)
    return '-'.join(parts) + '.csv'


def _header_line(bom):
    buf = io.StringIO(newline='')
    csv.writer(buf, lineterminator='\r\n').writerow(FIELDS)
    return (('\ufeff' if bom else '') + buf.getvalue()).encode('utf-8')


def _rows_to_bytes(rows):
    buf = io.StringIO(newline='')
    w = csv.writer(buf, lineterminator='\r\n')
    for r in rows:
        w.writerow([csv_cell(r.get(k)) for k in FIELDS])
    return buf.getvalue().encode('utf-8')


def _wanted(row, args):
    if type(row) is not dict:
        return False
    if args['project'] and row.get('project') != args['project']:
        return False
    if args['category']:
        cat = row.get('category') if isinstance(row.get('category'), str) and row.get('category') else 'GENERAL'
        if cat != args['category']:
            return False
    return True


def _newest_key(r):
    c = r.get('collected_at')
    return (c if isinstance(c, str) else '')


def snapshot_export(rows, args=None, max_rows=SNAPSHOT_MAX_ROWS, bom=False):
    """(body_bytes, headers, meta) for rows already in memory. Same ordering as the
    loaded view default (newest collected first, ties by title then key). Headers are exact
    because the total is known."""
    a = parse_args(args)
    if not isinstance(rows, (list, tuple)):
        raise ValueError('rows must be a list')
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or not 1 <= max_rows <= 10000:
        raise ValueError('bad max_rows')
    window = rows[:max_rows * 2 + 1000]
    seen, kept, skipped, dupes = set(), [], 0, 0
    for r in window:
        if type(r) is not dict:
            skipped += 1
            continue
        if not _wanted(r, a):
            continue
        ident = (r.get('project'), r.get('article_key'))
        if r.get('article_key') is not None:
            if ident in seen:
                dupes += 1
                continue
            seen.add(ident)
        kept.append(r)
    kept.sort(key=lambda r: (str(r.get('title') or '').casefold(), str(r.get('article_key') or '')))
    kept.sort(key=_newest_key, reverse=True)
    truncated = len(kept) > max_rows or len(rows) > len(window)
    kept = kept[:max_rows]
    body = _header_line(bom) + _rows_to_bytes(kept)
    name = filename(a['project'], a['category'], 'snapshot')
    headers = {'Content-Type': 'text/csv; charset=utf-8',
               'Content-Disposition': 'attachment; filename="%s"' % name,
               'X-Export-Scope': 'loaded_read_view_not_full_database',
               'X-Export-Limit': str(max_rows), 'X-Export-Rows': str(len(kept)),
               'X-Export-Truncated': 'true' if truncated else 'false'}
    meta = {'rows': len(kept), 'truncated': truncated, 'duplicates_omitted': dupes,
            'non_object_rows_skipped': skipped, 'filename': name}
    return body, headers, meta


def _check_caps(caps):
    caps = dict(DEFAULT_CAPS if caps is None else caps)
    if set(caps) - set(PROJECTS) or not caps:
        raise ValueError('caps must be keyed by geo/brics')
    for v in caps.values():
        if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 5000000:
            raise ValueError('bad cap')
    return caps


def stream_export(pager, args=None, caps=None, page_size=PAGE_SIZE, max_bytes=MAX_BYTES,
                  max_seconds=MAX_SECONDS, clock=time.monotonic, bom=False):
    """Incremental export. Returns (chunks, headers, state).

    pager(project, cursor, limit) -> (rows, next_cursor): rows is a list of at most
    `limit` public-news dicts for that project in a stable order, next_cursor is an opaque
    value or None at the end. It must be read-only. The first page is fetched here, before
    anything is sent, so a source failure raises ExportUnavailable (answer 503).

    chunks is a generator of bytes. After streaming starts the HTTP status cannot change, so
    a cap, byte or time stop, or a later source error, ends the file with ONE trailer row
    whose first cell is EXPORT_TRUNCATED or EXPORT_INCOMPLETE (header X-Export-Trailer says
    so). state is a dict updated as chunks are produced (rows, pages, stopped, reason) for
    the caller's logging. Rows read is bounded by the per-project cap, so a category filter
    cannot make it scan more than the cap. Order is the pager's order per project, not
    re-sorted; no cross-page de-duplication (cursor paging does not repeat rows)."""
    a = parse_args(args)
    caps = _check_caps(caps)
    if not callable(pager):
        raise ValueError('pager must be callable')
    if not isinstance(page_size, int) or isinstance(page_size, bool) or not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError('bad page_size')
    projects = [a['project']] if a['project'] else [p for p in PROJECTS if p in caps]
    projects = [p for p in projects if p in caps]
    if not projects:
        raise ExportRequestError('project not enabled for export')
    state = {'rows': 0, 'pages': 0, 'stopped': False, 'reason': None, 'read': 0}

    def fetch(project, cursor, remaining):
        limit = min(page_size, remaining)
        try:
            res = pager(project, cursor, limit)
        except Exception as exc:
            raise ExportUnavailable(type(exc).__name__) from None
        if (type(res) is not tuple or len(res) != 2 or type(res[0]) is not list or len(res[0]) > limit):
            raise ExportUnavailable('pager_contract')
        return res[0], res[1]

    first = {projects[0]: fetch(projects[0], None, caps[projects[0]])}  # fail before any byte is sent
    name = filename(a['project'], a['category'], 'full')
    headers = {'Content-Type': 'text/csv; charset=utf-8',
               'Content-Disposition': 'attachment; filename="%s"' % name,
               'X-Export-Scope': 'paged_read_view_capped',
               'X-Export-Limit': ','.join('%s=%d' % (p, caps[p]) for p in projects),
               'X-Export-Trailer': 'EXPORT_TRUNCATED or EXPORT_INCOMPLETE row is appended when the file is cut short'}

    def trailer(kind, why):
        state.update(stopped=True, reason=why)
        buf = io.StringIO(newline='')
        csv.writer(buf, lineterminator='\r\n').writerow([kind + ': ' + why])
        return buf.getvalue().encode('utf-8')

    def chunks():
        started = clock()
        total = 0
        head = _header_line(bom)
        total += len(head)
        yield head
        for project in projects:
            cursor, remaining, seen_cursors = None, caps[project], set()
            page = first.pop(project, None)
            while remaining > 0:
                if page is None:
                    try:
                        page = fetch(project, cursor, remaining)
                    except ExportUnavailable as exc:
                        yield trailer('EXPORT_INCOMPLETE', 'source error after %d rows' % state['rows'])
                        return
                rows, nxt = page
                page = None
                state['pages'] += 1
                state['read'] += len(rows)
                remaining -= len(rows)
                good = [r for r in rows if type(r) is dict and r.get('project') in (None, project) and _wanted(dict(r, project=project), a)]
                for i in range(0, len(good), BATCH_ROWS):
                    part = _rows_to_bytes([dict(r, project=project) for r in good[i:i + BATCH_ROWS]])
                    if total + len(part) > max_bytes:
                        yield trailer('EXPORT_TRUNCATED', 'byte limit %d reached' % max_bytes)
                        return
                    total += len(part)
                    state['rows'] += len(good[i:i + BATCH_ROWS])
                    yield part
                    if clock() - started > max_seconds:
                        yield trailer('EXPORT_TRUNCATED', 'time limit %ds reached' % int(max_seconds))
                        return
                if nxt is None or not rows:
                    break
                key = repr(nxt)[:200]
                if key in seen_cursors:
                    yield trailer('EXPORT_INCOMPLETE', 'pager cursor did not advance')
                    return
                seen_cursors.add(key)
                cursor = nxt
                if remaining <= 0:
                    yield trailer('EXPORT_TRUNCATED', 'row cap %d reached for %s' % (caps[project], project))
                    return
                if clock() - started > max_seconds:
                    yield trailer('EXPORT_TRUNCATED', 'time limit %ds reached' % int(max_seconds))
                    return

    return chunks(), headers, state


def guarded(chunks, release):
    """Wrap a chunk generator so release() runs exactly once when streaming ends, fails or the
    client disconnects (use with a BoundedSemaphore slot)."""
    try:
        yield from chunks
    finally:
        release()
