"""Default-OFF held private mail surface. No backend or send capability."""
import hashlib
import hmac
import json
import re
from urllib.parse import unquote, urlsplit

PREFIX = '/internal/mail/v1'
CAP = 4096
HEX = re.compile(r'[0-9a-f]{64}', re.ASCII)
TOKEN = re.compile(r'[A-Za-z0-9_-]{20,80}', re.ASCII)
UNAUTHORIZED = ('401 Unauthorized', {'error': 'unauthorized'})
HELD = ('503 Service Unavailable', {'state': 'mail_integration_held', 'retry_send': False})


def _response(start, status, body):
    wire = json.dumps(body, separators=(',', ':'), ensure_ascii=True).encode('ascii')
    start(status, [('Content-Type', 'application/json'), ('Content-Length', str(len(wire))),
                  ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff')])
    return [wire]


def _config(config):
    if type(config) is not dict or set(config) != {'origin', 'rail', 'channel_id', 'header_secret'}:
        return None
    if any(type(v) is not str for v in config.values()) or config['rail'] != 'apps_script':
        return None
    if HEX.fullmatch(config['channel_id']) is None:
        return None
    secret = config['header_secret']
    if not 48 <= len(secret) <= 256 or any(not 33 <= ord(c) <= 126 for c in secret):
        return None
    origin = config['origin']
    try:
        p = urlsplit(origin)
        host = p.hostname
        if (p.scheme != 'https' or not host or p.netloc != host or p.path or p.query or p.fragment
                or origin != 'https://' + host or host == 'localhost' or '.' not in host
                or re.fullmatch(r'[0-9.]+', host) or ':' in host
                or re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', host, re.ASCII) is None):
            return None
    except Exception:
        return None
    return origin, hashlib.sha256(('Bearer ' + secret).encode('ascii')).digest()


def _classify(path):
    if type(path) is not str:
        return 'suspicious'
    if path == PREFIX or path.startswith(PREFIX + '/'):
        if path != path.lower() or any(c in path for c in ('%', '\\', '\0')) or '/.' in path or '//' in path:
            return 'suspicious'
        return 'private'
    # PATH_INFO belongs to this app; SCRIPT_NAME is never prepended or rewritten.
    decoded = path
    for _ in range(3):
        after = unquote(decoded)
        if after == decoded:
            break
        decoded = after
    normalized = decoded.replace('\\', '/').replace('\0', '').lower()
    segments = []
    for part in normalized.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            if segments:
                segments.pop()
        else:
            segments.append(part.rstrip('.'))
    normalized = '/' + '/'.join(segments)
    if normalized.startswith(PREFIX) or normalized.startswith('/internal/mail/v1'):
        return 'suspicious'
    return 'public'


def _pairs(rows):
    out = {}
    for k, v in rows:
        if k in out:
            raise ValueError()
        out[k] = v
    return out


def _constant(value):
    raise ValueError()


def _body(environ, action):
    if 'HTTP_TRANSFER_ENCODING' in environ:
        raise ValueError()
    media = environ.get('CONTENT_TYPE')
    if type(media) is not str or media.lower() not in ('application/json', 'application/json; charset=utf-8'):
        raise ValueError()
    size = environ.get('CONTENT_LENGTH')
    if type(size) is not str or re.fullmatch(r'[1-9][0-9]*', size, re.ASCII) is None:
        raise ValueError()
    if len(size) > 4 or not 1 <= int(size) <= CAP:
        raise ValueError()
    # WSGI servers own HTTP framing. A terminated stream may expose extra bytes;
    # otherwise read only declared bytes plus one bounded lie-detection byte.
    raw = environ['wsgi.input'].read(CAP + 1 if environ.get('wsgi.input_terminated') is True else int(size) + 1)
    if type(raw) is not bytes or len(raw) != int(size) or len(raw) > CAP:
        raise ValueError()
    text = raw.decode('utf-8', 'strict')
    if text.startswith('\ufeff'):
        raise ValueError()
    data = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    if type(data) is not dict:
        raise ValueError()
    if action == 'prepare':
        if set(data) != {'kind', 'nonce'} or type(data['kind']) is not str or data['kind'] not in ('digest', 'critical', 'weekly'):
            raise ValueError()
        if type(data['nonce']) is not str or TOKEN.fullmatch(data['nonce']) is None:
            raise ValueError()
    else:
        if set(data) != {'receipt', 'hash', 'attempt'}:
            raise ValueError()
        for field in ('receipt', 'hash'):
            if type(data[field]) is not str or HEX.fullmatch(data[field]) is None:
                raise ValueError()
        if type(data['attempt']) is not str or TOKEN.fullmatch(data['attempt']) is None:
            raise ValueError()


class HeldMailSurface:
    def __init__(self, public, origin, credential_digest):
        self._public = public
        self._origin = origin
        self._credential_digest = credential_digest

    def __repr__(self):
        return 'HeldMailSurface(mounted_held=True, ready=False, live=False)'

    def __call__(self, environ, start_response):
        route = _classify(environ.get('PATH_INFO', ''))
        if route == 'public':
            return self._public(environ, start_response)
        result = UNAUTHORIZED
        try:
            if route == 'suspicious':
                return _response(start_response, *UNAUTHORIZED)
            auth = environ.get('HTTP_AUTHORIZATION')
            good = type(auth) is str and re.fullmatch(r'Bearer [\x21-\x7e]{48,256}', auth, re.ASCII) is not None
            given = hashlib.sha256(auth.encode('ascii')).digest() if good else hashlib.sha256(b'').digest()
            if not hmac.compare_digest(given, self._credential_digest) or not good:
                return _response(start_response, *UNAUTHORIZED)
            if environ.get('QUERY_STRING', ''):
                return _response(start_response, *UNAUTHORIZED)
            # No proxy forwarding headers or URI path can select the origin.
            expected_host = self._origin[len('https://'):]
            if (environ.get('wsgi.url_scheme') != 'https' or environ.get('HTTP_HOST') != expected_host
                    or environ.get('HTTP_ORIGIN') is not None):
                result = ('400 Bad Request', {'error': 'invalid_request'})
            else:
                path = environ['PATH_INFO']
                action = path[len(PREFIX) + 1:]
                is_post = action in ('prepare', 'claim', 'ack')
                is_status = action.startswith('receipts/') and HEX.fullmatch(action[len('receipts/'):]) is not None
                method = environ.get('REQUEST_METHOD')
                if not is_post and not is_status:
                    result = ('404 Not Found', {'error': 'route_unavailable'})
                elif method != ('POST' if is_post else 'GET'):
                    result = ('405 Method Not Allowed', {'error': 'method_refused'})
                else:
                    result = ('400 Bad Request', {'error': 'invalid_request'})
                    if is_post:
                        _body(environ, action)
                    elif ('HTTP_TRANSFER_ENCODING' in environ or environ.get('CONTENT_LENGTH', '') not in ('', '0')):
                        raise ValueError()
                    result = HELD
        except Exception:
            # No state, raw exception or private request information is retained.
            pass
        return _response(start_response, *result)


def build_mail_surface(public, *, enabled=False, config=None):
    if type(enabled) is not bool:
        raise ValueError('Mail surface configuration refused') from None
    if not enabled:
        return public
    checked = None
    try:
        checked = _config(config)
    except Exception:
        pass
    if checked is None or not callable(public):
        raise ValueError('Mail surface configuration refused') from None
    origin, digest = checked
    return HeldMailSurface(public, origin, digest)


def metadata():
    return {'state': 'mounted_held', 'wired': False, 'live': False, 'ready': False,
            'rail': 'apps_script', 'smtp_fallback_held': True}
