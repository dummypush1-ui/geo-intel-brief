"""Internally consistent in-memory candidate bytes, not external persistence."""
import copy
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta

CAP = 128 * 1024
HEX = re.compile(r'[0-9a-f]{64}', re.ASCII)
ID = re.compile(r'[0-9a-f]{24}', re.ASCII)
TOKEN = re.compile(r'[A-Za-z0-9_-]{20,80}', re.ASCII)
CANDIDATE_FIELDS = {'renderer_version', 'digest_algorithm', 'kind', 'date_field', 'asof_utc',
                    'offset_minutes', 'offset_label', 'subject', 'html', 'text', 'sections',
                    'sorted_union_ids', 'skip'}
FLAGS = {'state': 'in_memory_candidate_bytes_not_archived', 'archived': False,
         'durable': False, 'send_allowed': False, 'ready': False}


def _fail():
    raise ValueError('Candidate bytes held') from None


def _wire(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def _hash(value):
    return hashlib.sha256(_wire(value)).hexdigest()


def _sha(value):
    if type(value) is not str or HEX.fullmatch(value) is None:
        _fail()
    return value


def _plain(value, depth=0):
    if depth > 12:
        _fail()
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            _fail()
        for child in value.values():
            _plain(child, depth + 1)
    elif type(value) is list:
        if len(value) > 120:
            _fail()
        for child in value:
            _plain(child, depth + 1)
    elif type(value) is str:
        if len(value) > 81920 or any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            _fail()
    elif type(value) not in (bool, int):
        _fail()


def _candidate(c):
    _plain(c)
    if type(c) is not dict or set(c) != CANDIDATE_FIELDS:
        _fail()
    if c['renderer_version'] != 'digest_email218_v1' or c['digest_algorithm'] != 'sha256_canonical_json_ascii' or c['kind'] != 'digest' or c['date_field'] not in ('published', 'created_at') or c['skip'] is not False:
        _fail()
    for field in ('renderer_version', 'digest_algorithm', 'kind', 'date_field', 'asof_utc', 'offset_label', 'subject', 'html', 'text'):
        if type(c[field]) is not str:
            _fail()
    stamp = datetime.fromisoformat(c['asof_utc'])
    if stamp.tzinfo is not timezone.utc or stamp.isoformat(timespec='microseconds') != c['asof_utc']:
        _fail()
    offset = c['offset_minutes']
    if type(offset) is not int or not -1439 <= offset <= 1439:
        _fail()
    label = ('+' if offset >= 0 else '-') + f'{abs(offset)//60:02d}:{abs(offset)%60:02d}'
    if c['offset_label'] != label or c['subject'] != 'Geo Intel Brief - ' + c['asof_utc'] + ' UTC':
        _fail()
    if not c['html'] or not c['text'] or sum(len(c[k].encode('utf-8')) for k in ('subject', 'html', 'text')) > 81920 or len(c['html'].encode('utf-8')) > 61440:
        _fail()
    sections = c['sections'];union = c['sorted_union_ids']
    if type(sections) is not list or len(sections) != 2 or type(union) is not list or not 1 <= len(union) <= 120 or any(type(v) is not str or ID.fullmatch(v) is None for v in union) or union != sorted(set(union)):
        _fail()
    displayed = []
    for section, name, heading in zip(sections, ('last_24h', 'last_7days'), ('Last 24 hours', 'Last 7 days (includes last 24 hours)')):
        if type(section) is not dict or set(section) != {'name', 'heading', 'ids', 'eligible_count', 'omitted_count'} or section['name'] != name or section['heading'] != heading:
            _fail()
        ids = section['ids']
        if type(ids) is not list or len(ids) > 60 or len(set(ids)) != len(ids) or any(type(v) is not str or ID.fullmatch(v) is None for v in ids):
            _fail()
        if type(section['eligible_count']) is not int or not len(ids) <= section['eligible_count'] <= 1000 or type(section['omitted_count']) is not int or section['omitted_count'] != section['eligible_count'] - len(ids):
            _fail()
        displayed.extend(ids)
    if sorted(set(displayed)) != union:
        _fail()
    return c


def _proposals(candidate, fingerprint, nonce, content):
    _sha(fingerprint);_sha(content)
    if type(nonce) is not str or TOKEN.fullmatch(nonce) is None:
        _fail()
    # Exact212 compatibility formulas: no new domain on these existing hashes.
    channel = _hash({'kind': 'email', 'recipients': fingerprint})
    control = _hash({'channel': channel, 'purpose': 'digest'})
    digest = _hash({'logical_channel': channel, 'purpose': 'digest',
                    'ids': candidate['sorted_union_ids'], 'content_digest': content})
    nonce_key = _hash({'control': control, 'nonce': nonce})
    return {'recipient_set_fingerprint': fingerprint, 'nonce': nonce, 'kind': 'email',
            'purpose': 'digest', 'rail': 'apps_script', 'proposed_channel': channel,
            'proposed_control_key': control, 'proposed_binding_hash': digest,
            'proposed_nonce_key': nonce_key, 'proposed_content_digest': content,
            'proposed_ids': copy.deepcopy(candidate['sorted_union_ids'])}


def _bind(blob, candidate, fingerprint, nonce, content):
    p = _proposals(candidate, fingerprint, nonce, content)
    p['snapshot_identity'] = _hash({'domain': 'mail_candidate219.snapshot_identity.v1', 'binding': p})
    p['byte_integrity'] = _hash({'domain': 'mail_candidate219.byte_integrity.v1', 'canonical_bytes_hex': blob.hex()})
    return {**FLAGS, **p}


def freeze_candidate(*, enabled=False, candidate_result=None, recipient_set_fingerprint=None, nonce=None):
    if type(enabled) is not bool:
        _fail()
    if not enabled:
        return dict(FLAGS, state='disabled')
    result = None
    try:
        if type(candidate_result) is not dict or set(candidate_result) != {'state', 'send_allowed', 'ready', 'archive_proof', 'candidate', 'content_digest'} or candidate_result['state'] != 'supplied_email_candidate_only' or any(candidate_result[k] is not False for k in ('send_allowed', 'ready', 'archive_proof')):
            _fail()
        c = copy.deepcopy(_candidate(candidate_result['candidate']))
        content = _hash(c)
        if _sha(candidate_result['content_digest']) != content:
            _fail()
        blob = _wire({'candidate': c, 'proposed_content_digest': content})
        if len(blob) > CAP:
            _fail()
        result = (blob, _bind(blob, c, recipient_set_fingerprint, nonce, content))
    except Exception:
        pass
    if result is None:
        _fail()
    return result


def _pairs(rows):
    out = {}
    for k, v in rows:
        if k in out:
            _fail()
        out[k] = v
    return out


def _constant(value):
    _fail()


def verify_snapshot(blob, binding):
    result = None
    try:
        if type(blob) is not bytes or not 1 <= len(blob) <= CAP or type(binding) is not dict:
            _fail()
        _plain(binding)
        text = blob.decode('utf-8', 'strict')
        if text.startswith('\ufeff'):
            _fail()
        envelope = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
        if type(envelope) is not dict or set(envelope) != {'candidate', 'proposed_content_digest'} or _wire(envelope) != blob:
            _fail()
        c = _candidate(envelope['candidate']);content = _hash(c)
        if _sha(envelope['proposed_content_digest']) != content:
            _fail()
        expected = _bind(blob, c, binding['recipient_set_fingerprint'], binding['nonce'], content)
        if type(binding) is not dict or _wire(binding) != _wire(expected):
            _fail()
        result = copy.deepcopy(c)
    except Exception:
        pass
    if result is None:
        _fail()
    return result
