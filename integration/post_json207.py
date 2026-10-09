"""Two read-only POST route bodies, after existing auth/Origin guards."""
import json
import re
from werkzeug.exceptions import ClientDisconnected

CAP = 16384


class BodyRefused(ValueError):
    def __init__(self, status):
        super().__init__('Invalid read context')
        self.status = status


def _fail(status=400):
    raise BodyRefused(status)


def _pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            _fail()
        out[key] = value
    return out


def _constant(value):
    _fail()


def _text(value, cap, *, multiline=False):
    if type(value) is not str or len(value) > cap:
        _fail()
    for char in value:
        number = ord(char)
        if number < 32 and not (multiline and char in '\t\n\r'):
            _fail()
        if 127 <= number <= 159 or 0xD800 <= number <= 0xDFFF:
            _fail()
    return value


def parse(request, kind):
    """Parse observable WSGI forms, not an HTTP framing security boundary."""
    if request.query_string:
        _fail()
    content_type = request.environ.get('CONTENT_TYPE', '')
    parts = content_type.split(';')
    if parts[0].strip().lower() != 'application/json':
        _fail(415)
    if len(parts) > 2:
        _fail(415)
    if len(parts) == 2:
        parameter = parts[1].strip().split('=')
        if len(parameter) != 2 or parameter[0].strip().lower() != 'charset' or parameter[1].strip().lower() != 'utf-8':
            _fail(415)
    if 'HTTP_TRANSFER_ENCODING' in request.environ:
        _fail()
    length = request.environ.get('CONTENT_LENGTH')
    if length is None or length == '':
        _fail(411)
    if type(length) is not str or re.fullmatch(r'[1-9][0-9]*', length, re.ASCII) is None:
        _fail()
    # Avoid parsing an arbitrarily long integer header.
    if len(length) > 5 or int(length) > CAP:
        _fail(413)
    declared = int(length)
    try:
        # Only terminated inputs may be read beyond declared length. On other
        # servers the request stream enforces CL; extra bytes are unobservable.
        terminated = request.environ.get('wsgi.input_terminated') is True
        raw = request.stream.read(CAP + 1 if terminated else declared)
    except (ClientDisconnected, OSError, ValueError):
        _fail()
    if len(raw) > CAP:
        _fail(413)
    if len(raw) != declared:
        _fail()
    try:
        text = raw.decode('utf-8', 'strict')
        if text.startswith('\ufeff'):
            _fail()
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except BodyRefused:
        raise
    except (ValueError, UnicodeError, RecursionError):
        _fail()
    if type(value) is not dict:
        _fail()
    if kind == 'related':
        if set(value) - {'code', 'system', 'edition', 'country', 'product_terms'}:
            _fail()
        for key, cap in [('code', 12), ('system', 32), ('edition', 32), ('country', 100)]:
            if key in value:
                _text(value[key], cap)
        if value.get('code', '') and re.fullmatch(r'[0-9]{1,12}', value['code'], re.ASCII) is None:
            _fail()
        if 'product_terms' in value:
            terms = value['product_terms']
            if type(terms) is not list or len(terms) > 20:
                _fail()
            for term in terms:
                _text(term, 200, multiline=True)
    elif kind == 'finder':
        if set(value) != {'project', 'article_key'}:
            _fail()
        if type(value['project']) is not str or value['project'] not in ('geo', 'brics'):
            _fail()
        if type(value['article_key']) is not str or re.fullmatch(r'[0-9a-f]{64}', value['article_key'], re.ASCII) is None:
            _fail()
    else:
        _fail()
    return value
