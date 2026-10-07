# Copyright (c) 2026 Push. All rights reserved.
import copy
import unittest
from feature_related_prep.hybrid import plan


class HybridTests(unittest.TestCase):
    def setUp(self):
        self.context = {'code': '090121', 'system': 'HS', 'edition': '2022',
                        'country': 'IN', 'product_terms': ['coffee']}
        self.row = {'article_key': 'sample-1', 'title': 'Coffee exports', 'summary': ''}

    def decision(self, row=None, context=None, reviews=None):
        return plan(context or self.context, [row or self.row], reviews)['decisions'][0]

    def review(self, **updates):
        item = self.decision()
        r = {'article_hash': item['article_hash'], 'context_hash': item['context_hash'],
             'provider': 'groq', 'related': True, 'confidence': 0.9, 'reason': 'Fixture only'}
        r.update(updates)
        return r

    def test_product_country_accept(self):
        row = dict(self.row, summary='India exports coffee')
        item = self.decision(row)
        self.assertEqual(item['decision'], 'accept')
        self.assertFalse(item['duty_change_verified'])
        self.assertFalse(item['provider_verified'])

    def test_code_country_accept(self):
        self.assertEqual(self.decision(dict(self.row, title='India HS code 090121'))['decision'], 'accept')

    def test_country_alone_reject(self):
        self.assertEqual(self.decision(dict(self.row, title='India elections'))['decision'], 'reject')

    def test_accidental_number_reject(self):
        self.assertEqual(self.decision(dict(self.row, title='India invoice 090121'))['decision'], 'reject')

    def test_uncertain_held(self):
        self.assertEqual(self.decision()['decision'], 'held')
        self.assertTrue(self.decision()['ai_required'])

    def test_missing_country_held(self):
        c = dict(self.context, country='')
        self.assertEqual(self.decision(context=c)['decision'], 'held')

    def test_review_accept_unverified(self):
        item = self.decision(reviews=[self.review()])
        self.assertEqual(item['decision'], 'accept')
        self.assertEqual(item['basis'], 'supplied_unverified_ai')
        self.assertFalse(item['provider_verified'])

    def test_review_reject(self):
        self.assertEqual(self.decision(reviews=[self.review(related=False)])['decision'], 'reject')

    def test_low_confidence_held(self):
        self.assertEqual(self.decision(reviews=[self.review(confidence=0.79)])['decision'], 'held')

    def test_stale_binding_rejected(self):
        for key in ('context_hash', 'article_hash'):
            with self.assertRaises(ValueError):
                self.decision(reviews=[self.review(**{key: '0' * 64})])

    def test_duplicate_review_rejected(self):
        r = self.review()
        with self.assertRaises(ValueError):
            self.decision(reviews=[r, r])

    def test_schema_provider_and_confidence_closed(self):
        for changes in ({'confidence': True}, {'confidence': float('nan')}, {'confidence': 1.1},
                        {'related': 1}, {'provider': 'nvidia'}, {'reason': ''}, {'extra': 'private'}):
            with self.assertRaises(ValueError):
                self.decision(reviews=[self.review(**changes)])

    def test_nonheld_review_rejected(self):
        with self.assertRaises(ValueError):
            self.decision(dict(self.row, summary='India coffee'), reviews=[self.review()])

    def test_private_fields_refused(self):
        with self.assertRaises(ValueError):
            self.decision(dict(self.row, api_key='DO_NOT_COPY'))

    def test_input_caps_and_duplicates(self):
        for rows in ([self.row] * 101, [self.row, self.row], [dict(self.row, summary='x' * 16001)]):
            with self.assertRaises(ValueError):
                plan(self.context, rows)
        with self.assertRaises(ValueError):
            plan(self.context, [dict(self.row, article_key=str(i), summary='x' * 15000) for i in range(20)])

    def test_context_closed(self):
        for changes in ({'code': '１２３４５６'}, {'country': 'not-a-country'}, {'product_terms': 'coffee'},
                        {'code': '', 'product_terms': []}, {'extra': 'private'}):
            with self.assertRaises(ValueError):
                self.decision(context=dict(self.context, **changes))

    def test_pure_repeatable(self):
        original = copy.deepcopy([self.context, self.row])
        a = plan(self.context, [self.row]); b = plan(self.context, [self.row])
        self.assertEqual(a, b)
        self.assertEqual(original, [self.context, self.row])
        self.assertEqual(a['provider_calls'], 0)
        self.assertFalse(a['mounted'])
