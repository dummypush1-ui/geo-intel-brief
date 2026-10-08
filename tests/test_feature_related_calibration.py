# Copyright (c) 2026 Push. All rights reserved.
import copy
import unittest
from feature_related_prep.calibration import evaluate


def row(n=1, **changes):
    value={'article_hash':format(n,'064x'),'context_hash':'c'*64,
           'keyword_decision':'held','related_label':True,'ai_related':True,'ai_confidence':0.8}
    value.update(changes)
    return value


class Tests(unittest.TestCase):
    def test_threshold_boundary(self):
        results=evaluate([row()],[0.8,0.81])['results']
        self.assertEqual(results[0]['counts']['tp'],1)
        self.assertEqual(results[1]['counts']['held_positive'],1)
        self.assertEqual(results[1]['overall_positive_recall'],0)
    def test_keyword_reject_recall_miss(self):
        value=evaluate([row(keyword_decision='reject',ai_related=None,ai_confidence=None)],[0.8])
        self.assertEqual(value['keyword_reject_positive_labels'],1)
        self.assertEqual(value['results'][0]['counts']['fn'],1)
    def test_confusion_and_coverage(self):
        rows=[row(1),row(2,related_label=False),row(3,ai_related=False),row(4,ai_related=False,related_label=False),row(5,ai_confidence=None,ai_related=None)]
        result=evaluate(rows,[0.8])['results'][0]
        self.assertEqual(result['counts'],{'tp':1,'fp':1,'tn':1,'fn':1,'held_positive':1,'held_negative':0,'ai_used':4})
        self.assertEqual(result['coverage'],0.8);self.assertEqual(result['precision'],0.5)
        self.assertEqual(result['overall_positive_recall'],1/3)
    def test_null_denominators(self):
        result=evaluate([row(related_label=False,ai_related=None,ai_confidence=None)],[0.8])['results'][0]
        self.assertIsNone(result['precision']);self.assertIsNone(result['overall_positive_recall']);self.assertIsNone(result['decided_accuracy'])
    def test_no_automatic_selection(self):
        value=evaluate([row()],[0,0.8,1])
        self.assertIsNone(value['threshold_selected']);self.assertFalse(value['config_changed']);self.assertEqual(value['provider_calls'],0)
    def test_bad_thresholds(self):
        for values in ([],[True],[float('nan')],[-0.1],[1.1],[0.8,0.8],[0]*21,'0.8'):
            with self.assertRaises(ValueError):evaluate([row()],values)
    def test_duplicate_pair_and_caps(self):
        for rows in ([],[row(),row()],[row()]*1001):
            with self.assertRaises(ValueError):evaluate(rows,[0.8])
    def test_closed_schema(self):
        for changes in ({'private':'no'},{'article_hash':'x'},{'keyword_decision':'maybe'},{'related_label':1}):
            with self.assertRaises(ValueError):evaluate([row(**changes)],[0.8])
    def test_ai_only_for_held(self):
        with self.assertRaises(ValueError):evaluate([row(keyword_decision='accept')],[0.8])
    def test_bad_ai_pair(self):
        for changes in ({'ai_related':None},{'ai_confidence':None},{'ai_related':1},{'ai_confidence':True},{'ai_confidence':float('inf')}):
            with self.assertRaises(ValueError):evaluate([row(**changes)],[0.8])
    def test_repeatable_and_detached(self):
        rows=[row()];original=copy.deepcopy(rows)
        a=evaluate(rows,[0.8]);self.assertEqual(a,evaluate(rows,[0.8]));self.assertEqual(rows,original)
    def test_distinct_context_pairs(self):
        result=evaluate([row(),row(context_hash='d'*64)],[0.8])
        self.assertEqual(result['total'],2)
