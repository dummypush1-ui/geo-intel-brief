"""Manual USITC release metadata capture. No duty or legal-effect inference.

No import/startup network. Call capture_latest() explicitly outside HTTP paths,
then supply its exact TariffEvidenceSnapshot to a reviewed public builder.
"""
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit
import re
import time
from integration.tariff_evidence import TariffEvidenceSnapshot

ARCHIVE = 'https://www.usitc.gov/harmonized_tariff_information/modifications_to_hts'
LIMIT = 1_000_000
TITLE = re.compile(r'([0-9]{4}) HTS (Basic Edition|Revision ([1-9][0-9]{0,2}))')
PATH = re.compile(r'/([0-9]{4})_hts_(basic_edition|revision_([1-9][0-9]{0,2}))')
CONDITIONS = ('USITC release-page metadata only; release publication date is not an '
              'instrument publication or effective date. No affected codes, duty rates, '
              'complete history or legal effect verified. No conclusion for India or EU.')

class SourceUnavailable(ValueError):
    pass

class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main = 0
        self.ignore = 0
        self.links = []
        self.words = []
        self.headings = []
        self.heading = None
    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.main += 1
        if not self.main:
            return
        if tag in ('script', 'style'):
            self.ignore += 1
        if self.ignore:
            return
        if tag == 'a':
            attrs = dict(attrs)
            if 'href' in attrs:
                self.links.append(attrs['href'])
        if tag == 'h1':
            self.heading = []
    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.ignore:
            self.ignore -= 1
        if tag == 'h1' and self.heading is not None:
            self.headings.append(' '.join(self.heading))
            self.heading = None
        if tag == 'main' and self.main:
            self.main -= 1
    def handle_data(self, data):
        if self.main and not self.ignore:
            word = ' '.join(data.split())
            if word:
                self.words.append(word)
                if self.heading is not None:
                    self.heading.append(word)

def _page(raw):
    if type(raw) is not bytes or not 1 <= len(raw) <= LIMIT:
        raise SourceUnavailable('Bounded official HTML required')
    p = _Page()
    try:
        p.feed(raw.decode('utf-8', errors='strict'))
        p.close()
    except (ValueError, UnicodeError):
        raise SourceUnavailable('Official HTML unavailable') from None
    if not p.headings:
        raise SourceUnavailable('Official page structure changed')
    return p

def discover_release(raw):
    p = _page(raw)
    if p.headings != ['Modifications to the Harmonized Tariff Schedule (HTS)']:
        raise SourceUnavailable('Official archive identity changed')
    paths = list(dict.fromkeys(h for h in p.links if PATH.fullmatch(h)))
    if not paths:
        raise SourceUnavailable('No release found; no tariff conclusion')
    # Preserve publisher ordering; never invent a higher revision from a date.
    return 'https://www.usitc.gov' + paths[0]

def parse_release(raw, url, observed_at):
    u = urlsplit(url)
    m = PATH.fullmatch(u.path)
    if u.scheme != 'https' or u.netloc != 'www.usitc.gov' or u.query or u.fragment or not m:
        raise SourceUnavailable('Exact USITC release URL required')
    p = _page(raw)
    if len(p.headings) != 1 or not TITLE.fullmatch(p.headings[0]):
        raise SourceUnavailable('Official release identity changed')
    title = p.headings[0]
    expected = m[1] + ' HTS ' + ('Basic Edition' if m[2] == 'basic_edition' else 'Revision ' + m[3])
    if title != expected:
        raise SourceUnavailable('Release URL/title mismatch')
    # The visible Release Date field wins. The download URL releaseDate can differ.
    try:
        i = p.words.index('Release Date')
        value = p.words[i + 1]
        if not re.fullmatch(r'[A-Za-z]+ [0-9]{1,2}, [0-9]{4}', value):
            raise ValueError()
        published = datetime.strptime(value, '%B %d, %Y').date()
        stamp = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
        if stamp.tzinfo is None or published > stamp.astimezone(timezone.utc).date():
            raise ValueError()
    except (ValueError, IndexError, TypeError, AttributeError):
        raise SourceUnavailable('Release date unavailable or future') from None
    row = dict(id='usitc-' + m[0][1:], jurisdiction='US', nomenclature='HTSUS',
               edition=title, codes=[], document_id=title, source_url=url,
               published_date=published.isoformat(), effective_dates=[],
               excerpt='USITC published the release listed on this source page. '
                       'This capture does not parse tariff schedules or legal instruments.',
               conditions=CONDITIONS, review_state='candidate', reviewed_at=None)
    return TariffEvidenceSnapshot(observed_at, [row])

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class _Transport:
    def __init__(self):
        self.opener = build_opener(_NoRedirect())
        self.last_start = None
    def get(self, url):
        # Fixed archive or exact derived publisher release, no cookies/credentials.
        u = urlsplit(url)
        if url != ARCHIVE and (u.scheme != 'https' or u.netloc != 'www.usitc.gov' or
                              u.query or u.fragment or not PATH.fullmatch(u.path)):
            raise SourceUnavailable('Unapproved source URL')
        if self.last_start is not None:
            time.sleep(max(0, 10 - (time.monotonic() - self.last_start)))
        self.last_start = time.monotonic()
        req = Request(url, headers={'User-Agent': 'GeoIntelBrief-ManualSourceReview/1.0',
                                    'Accept': 'text/html', 'Accept-Encoding': 'identity'})
        try:
            with self.opener.open(req, timeout=8) as r:
                if r.status != 200 or r.url != url or r.headers.get_content_type() != 'text/html':
                    raise SourceUnavailable('Official source response unavailable')
                if r.headers.get('Content-Encoding', 'identity') != 'identity':
                    raise SourceUnavailable('Encoded source refused')
                length = r.headers.get('Content-Length')
                if length and (not length.isdigit() or int(length) > LIMIT):
                    raise SourceUnavailable('Official source too large')
                # Streaming bytes and elapsed checks, not a claim to interrupt a blocked socket.
                chunks = []; size = 0
                while True:
                    if time.monotonic() - self.last_start > 15:
                        raise SourceUnavailable('Official source read deadline')
                    chunk = r.read(min(16384, LIMIT + 1 - size))
                    if not chunk:
                        break
                    chunks.append(chunk); size += len(chunk)
                    if size > LIMIT:
                        raise SourceUnavailable('Official source too large')
                return b''.join(chunks)
        except Exception:
            raise SourceUnavailable('Official source unavailable; no tariff conclusion') from None

def capture_latest():
    """Explicit manual two-page capture. Never called by a builder or HTTP handler.

    No retries, polling, private account, paid API, persistence or legal inference.
    USITC robots.txt requested ten seconds between starts when inspected 2026-10-15.
    """
    t = _Transport()
    url = discover_release(t.get(ARCHIVE))
    raw = t.get(url)
    return parse_release(raw, url, datetime.now(timezone.utc).isoformat())
