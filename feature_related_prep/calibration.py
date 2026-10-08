# Copyright (c) 2026 Push. All rights reserved.
"""Explicit-threshold evaluation over bounded caller-labeled fixtures only.

No provider, prompt, route, client, callback, environment, automatic selection
or live configuration update. Labels and AI scores are supplied, unverified
caller data. Metrics are fixture diagnostics, not estimates of real accuracy.
"""
from copy import deepcopy
import math
import re

FIELDS = {'article_hash', 'context_hash', 'keyword_decision', 'related_label', 'ai_related', 'ai_confidence'}


def _score(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Finite confidence in [0,1] required')
    return value


def evaluate(rows, thresholds):
    if type(rows) is not list or not 1 <= len(rows) <= 1000:
        raise ValueError('Nonempty bounded fixture list required')
    if type(thresholds) is not list or not 1 <= len(thresholds) <= 20:
        raise ValueError('Explicit bounded threshold candidates required')
    values = [_score(v) for v in thresholds]
    if len(set(values)) != len(values):
        raise ValueError('Unique threshold candidates required')
    clean, seen = [], set()
    for row in rows:
        if type(row) is not dict or set(row) != FIELDS:
            raise ValueError('Closed labeled fixture required')
        for k in ('article_hash', 'context_hash'):
            if type(row[k]) is not str or not re.fullmatch(r'[0-9a-f]{64}', row[k]):
                raise ValueError('Exact article/context hash required')
        key = (row['article_hash'], row['context_hash'])
        if key in seen:
            raise ValueError('Duplicate fixture pair refused')
        seen.add(key)
        if type(row['keyword_decision']) is not str or row['keyword_decision'] not in ('accept', 'reject', 'held') or type(row['related_label']) is not bool:
            raise ValueError('Keyword decision and boolean caller label required')
        if row['ai_related'] is None and row['ai_confidence'] is None:
            pass
        elif row['keyword_decision'] != 'held' or type(row['ai_related']) is not bool:
            raise ValueError('AI score only on a held fixture required')
        else:
            _score(row['ai_confidence'])
        if (row['ai_related'] is None) != (row['ai_confidence'] is None):
            raise ValueError('Complete AI pair required')
        clean.append(deepcopy(row))
    total = len(clean)
    positives = sum(r['related_label'] for r in clean)
    keyword_recall_misses = sum(r['related_label'] and r['keyword_decision'] == 'reject' for r in clean)
    results = []
    for threshold in values:
        counts = {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0, 'held_positive': 0, 'held_negative': 0, 'ai_used': 0}
        for row in clean:
            decision = row['keyword_decision']
            if decision == 'held' and row['ai_confidence'] is not None and row['ai_confidence'] >= threshold:
                decision = 'accept' if row['ai_related'] else 'reject'
                counts['ai_used'] += 1
            label = row['related_label']
            if decision == 'held': counts['held_positive' if label else 'held_negative'] += 1
            elif decision == 'accept': counts['tp' if label else 'fp'] += 1
            else: counts['fn' if label else 'tn'] += 1
        decided = counts['tp'] + counts['fp'] + counts['tn'] + counts['fn']
        accepted = counts['tp'] + counts['fp']
        results.append({'threshold': threshold, 'counts': counts, 'coverage': decided / total,
                        'precision': counts['tp'] / accepted if accepted else None,
                        'overall_positive_recall': counts['tp'] / positives if positives else None,
                        'decided_accuracy': (counts['tp'] + counts['tn']) / decided if decided else None})
    return {'scope': 'caller_labeled_fixture_diagnostics_not_real_accuracy',
            'labels_verified': False, 'model_scores_calibrated': False,
            'threshold_selected': None, 'config_changed': False, 'provider_calls': 0,
            'total': total, 'positive_labels': positives,
            'keyword_reject_positive_labels': keyword_recall_misses,
            'results': results}
