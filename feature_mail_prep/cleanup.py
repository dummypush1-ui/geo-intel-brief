# Copyright (c) 2026 Push. All rights reserved.
"""Metadata cleanup plan from geonews, never deletion.

The original deletes created_at < now-days, oldest first, assuming Telegram
backups persist. Here every candidate is HELD. Supplied receipt hash matches
are diagnostic only: no URL, flag or caller assertion verifies an archive.
Future live deletion needs independent backup recovery proof and owner approval.
"""
from datetime import timedelta
from hashlib import sha256
import json
import re
from .reports import _clock, _snapshot, _stamp


def article_hash(article):
    """Content binding for supplied original metadata. Not archive proof."""
    rows, _ = _snapshot([article], [])
    return sha256(json.dumps(rows[0], sort_keys=True, ensure_ascii=False,
        separators=(',', ':')).encode('utf-8')).hexdigest()


def prepare_cleanup(articles, now, *, days=30, supplied_receipt_hashes=None):
    now = _clock(now)
    if type(days) is not int or not 1 <= days <= 3650:
        raise ValueError('Cleanup window must be 1-3650 days')
    rows, _ = _snapshot(articles, [])
    receipts = {} if supplied_receipt_hashes is None else supplied_receipt_hashes
    if type(receipts) is not dict or len(receipts) > 200:
        raise ValueError('Bounded plain receipt map required')
    if any(type(k) is not str or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}', k)
           or type(v) is not str or not re.fullmatch(r'[a-f0-9]{64}', v)
           for k, v in receipts.items()):
        raise ValueError('Opaque ID and SHA256 receipt fields required')
    known = {r['_id'] for r in rows}
    if not set(receipts).issubset(known):
        raise ValueError('Receipt outside supplied snapshot')
    cutoff = now - timedelta(days=days)
    old = sorted((r for r in rows if _stamp(r['created_at']) < cutoff),
                 key=lambda r: _stamp(r['created_at']))
    candidates = []
    for row in old:
        digest = article_hash(row)
        candidates.append({'diagnostic_id': row['_id'], 'created_at': row['created_at'],
            'content_hash': digest, 'supplied_hash_matches': receipts.get(row['_id']) == digest,
            'archive_verified': False, 'state': 'held_not_deletable'})
    return {'state': 'supplied_cleanup_plan_only', 'database': 'geo_intel',
            'collection': 'articles', 'cutoff': cutoff.isoformat(), 'comparison': 'strict_lt',
            'candidates': candidates, 'candidate_count': len(candidates), 'deleted': 0,
            'deletion_ids': [], 'network': False, 'writes': False,
            'required_before_live': ['independent_archive_recovery_proof', 'owner_deletion_approval',
                                     'live_snapshot_and_receipt_binding', 'runtime_review']}
