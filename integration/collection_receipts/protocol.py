"""Inert collection transaction/journal protocol. No storage or transport.

Adapter output is an operational receipt only after the caller independently
establishes adapter identity, destination authority and durable transaction.
This module never upgrades supplied dictionaries into authentication proof.
"""
from copy import deepcopy
import hashlib
import json
import re

class ReceiptRefused(ValueError):
    pass

_STATES = {'newly_committed', 'already_pending', 'already_terminal', 'rejected', 'unknown'}
_IDS = {'article_id', 'full_record_id', 'outbox_id', 'version'}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def validate_commit(batch, receipt):
    """Match exact per-record transaction outcome, never aggregate insert count."""
    if type(batch) is not list or not 0 < len(batch) <= 200:
        raise ReceiptRefused('Bounded batch required')
    wanted = {}
    for r in batch:
        if type(r) is not dict or set(r) != {'url', 'record_sha256'}:
            raise ReceiptRefused('Closed record identity')
        if type(r['url']) is not str or not r['url'] or len(r['url']) > 2048:
            raise ReceiptRefused('URL identity required')
        if not isinstance(r['record_sha256'], str) or not re.fullmatch('[a-f0-9]{64}', r['record_sha256']):
            raise ReceiptRefused('Record digest required')
        if r['url'] in wanted:
            raise ReceiptRefused('Unique URL batch required')
        wanted[r['url']] = r['record_sha256']
    if type(receipt) is not list or len(receipt) != len(batch):
        raise ReceiptRefused('Exact per-record receipts required')
    seen = set()
    for row in receipt:
        if type(row) is not dict or set(row) - ({'url', 'record_sha256', 'state'} | _IDS):
            raise ReceiptRefused('Closed outcome')
        if type(row.get('url')) is not str or row.get('url') not in wanted or row['url'] in seen or row.get('record_sha256') != wanted[row['url']]:
            raise ReceiptRefused('Exact immutable content identity required')
        seen.add(row['url'])
        if row.get('state') not in _STATES:
            raise ReceiptRefused('Closed outcome state')
        if row['state'] in {'newly_committed', 'already_pending', 'already_terminal'}:
            if not _IDS <= set(row) or type(row['version']) is not int or row['version'] < 1:
                raise ReceiptRefused('Fenced persisted identity required')
            if any(type(row[k]) is not str or not 0 < len(row[k]) <= 128 for k in _IDS - {'version'}):
                raise ReceiptRefused('Exact persisted IDs required')
        elif _IDS & set(row):
            raise ReceiptRefused('Unknown/rejected cannot claim persisted identity')
    return deepcopy(receipt)


def plan_pieces(full_record, *, max_chars=3000):
    """Lossless JSON chunks, UTF16 bound for Telegram, no send/ref creation."""
    if type(max_chars) is not int or not 256 <= max_chars <= 3000:
        raise ReceiptRefused('Fixed piece budget')
    try:
        body = json.dumps(full_record, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        byte_count = len(body.encode())
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError):
        raise ReceiptRefused('Plain finite Unicode full record required') from None
    if byte_count > 1024 * 1024:
        raise ReceiptRefused('Full record byte bound')
    pieces = []; current = []; units = 0
    for char in body:
        width = 2 if ord(char) > 0xffff else 1
        if units + width > max_chars:
            pieces.append(''.join(current)); current = []; units = 0
        current.append(char); units += width
    if current: pieces.append(''.join(current))
    return {'record_sha256': digest(full_record), 'pieces': [
        {'index': i, 'text': p, 'sha256': hashlib.sha256(p.encode()).hexdigest()}
        for i, p in enumerate(pieces)]}


def journal_new(outbox_id, version, attempt_id, destination, plan):
    """To be persisted by adapter CAS before ANY send; not permission to send."""
    if any(type(v) is not str or not 0 < len(v) <= 128 for v in (outbox_id, attempt_id, destination)):
        raise ReceiptRefused('Exact fenced identifiers required')
    if type(version) is not int or version < 1:
        raise ReceiptRefused('Version required')
    if type(plan) is not dict or set(plan) != {'record_sha256', 'pieces'} or not plan['pieces']:
        raise ReceiptRefused('Fixed piece plan required')
    for i, p in enumerate(plan['pieces']):
        if set(p) != {'index', 'text', 'sha256'} or p['index'] != i or hashlib.sha256(p['text'].encode()).hexdigest() != p['sha256']:
            raise ReceiptRefused('Ordered exact pieces required')
    return {'outbox_id': outbox_id, 'version': version, 'attempt_id': attempt_id,
            'destination': destination, 'record_sha256': plan['record_sha256'],
            'piece_hashes': [p['sha256'] for p in plan['pieces']],
            'state': 'prepared', 'acknowledgements': {}, 'in_flight': None}


def start_piece(journal, index):
    """Persist started state before effect. Never resend unknown/in-flight."""
    if journal['state'] not in {'prepared', 'partial'} or journal['in_flight'] is not None:
        raise ReceiptRefused('Attempt cannot send')
    if type(index) is not int or not 0 <= index < len(journal['piece_hashes']) or str(index) in journal['acknowledgements']:
        raise ReceiptRefused('Unsent exact piece required')
    out = deepcopy(journal); out['state'] = 'started'; out['in_flight'] = index
    return out


def record_ack(journal, *, attempt_id, destination, index, piece_sha256, provider_message_id):
    if journal['state'] != 'started' or journal['in_flight'] != index or attempt_id != journal['attempt_id'] or destination != journal['destination']:
        raise ReceiptRefused('Current attempt/destination required')
    if type(index) is not int or not 0 <= index < len(journal['piece_hashes']) or piece_sha256 != journal['piece_hashes'][index]:
        raise ReceiptRefused('Exact piece hash required')
    if type(provider_message_id) is not int or provider_message_id <= 0:
        raise ReceiptRefused('Provider message identity required')
    out = deepcopy(journal); out['acknowledgements'][str(index)] = provider_message_id
    out['in_flight'] = None
    out['state'] = 'terminal' if len(out['acknowledgements']) == len(out['piece_hashes']) else 'partial'
    return out


def recover(journal):
    """Crash during started send is uncertain. Owner/provider reconciliation only."""
    out = deepcopy(journal)
    if out['state'] == 'started': out['state'] = 'unknown'
    return out


def publishable(journal):
    return (journal['state'] == 'terminal' and journal['in_flight'] is None
            and set(journal['acknowledgements']) == {str(i) for i in range(len(journal['piece_hashes']))})
