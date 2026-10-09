"""Pure body shape for two unselected broker handlers, after account guards.
Observable WSGI checks only, not an HTTP framing security boundary.
"""
import json
import re
from werkzeug.exceptions import ClientDisconnected

CAP = 16384
NONCE = re.compile(r'[A-Za-z0-9_-]{20,80}', re.ASCII)
MODEL = re.compile(r'[A-Za-z0-9._/-]{1,100}', re.ASCII)


class BodyRefused(ValueError):
    def __init__(self, status=400):
        super().__init__('Invalid broker request')
        self.status = status
        self.error = {415: 'json_required', 413: 'request_too_large',
                      411: 'length_required'}.get(status, 'invalid_request')


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


def _text(value, cap, multiline=False):
    if type(value) is not str or not 1 <= len(value) <= cap:
        _fail()
    for char in value:
        n = ord(char)
        if n < 32 and not (multiline and char in '\t\n\r'):
            _fail()
        if 127 <= n <= 159 or 0xD800 <= n <= 0xDFFF:
            _fail()


def parse(request, kind):
    if request.query_string:
        _fail()
    media = request.environ.get('CONTENT_TYPE', '')
    if type(media) is not str:
        _fail(415)
    parts = media.split(';')
    if parts[0].strip().lower() != 'application/json' or len(parts) > 2:
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
    if len(length) > 5 or int(length) > CAP:
        _fail(413)
    declared = int(length)
    try:
        terminated = request.environ.get('wsgi.input_terminated') is True
        raw = request.stream.read(CAP + 1 if terminated else declared)
    except (ClientDisconnected, OSError, ValueError):
        _fail()
    if type(raw) is not bytes:
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
    if kind == 'ships':
        if set(value) != {'nonce', 'port'}:
            _fail()
        _text(value['port'], 100)
    elif kind == 'ai':
        if set(value) != {'nonce', 'provider', 'model', 'prompt'}:
            _fail()
        if type(value['provider']) is not str or value['provider'] not in ('gemini', 'groq', 'mistral'):
            _fail()
        if type(value['model']) is not str or MODEL.fullmatch(value['model']) is None:
            _fail()
        _text(value['prompt'], 8000, multiline=True)
    else:
        _fail()
    if type(value['nonce']) is not str or NONCE.fullmatch(value['nonce']) is None:
        _fail()
    return value
