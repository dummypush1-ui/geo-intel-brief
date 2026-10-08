# Copyright (c) 2026 Push. All rights reserved.
import copy
import unittest
from feature_finder_prep.mount_policy import prepare

NOW=1791432000


def config(provider='groq', **changes):
    model='fixture-model-not-live'
    endpoint={'groq':'https://api.groq.com/openai/v1/chat/completions',
              'mistral':'https://api.mistral.ai/v1/chat/completions',
              'gemini':'https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent'}[provider]
    r={'provider':provider,'model':model,'endpoint':endpoint,'model_checked_at':NOW,
       'free_tier_checked_at':NOW,'disclosure_checked_at':NOW,'free_only_account':True,
       'disclosure_confirmed':True,'per_report_requests':2,'per_report_tokens':4000,
       'daily_requests':20,'request_bytes':16000,'response_bytes':64000,'attempt_seconds':15,'report_seconds':60}
    r.update(changes);return r


class Tests(unittest.TestCase):
    def test_three_provider_bounded(self):
        p=prepare([config(n) for n in ('groq','gemini','mistral')],checked_at=NOW)
        self.assertEqual(p['report_requests_cap'],6);self.assertEqual(p['report_tokens_cap'],12000)
        self.assertFalse(p['mounted']);self.assertEqual(p['provider_calls'],0)
        self.assertFalse(p['owner_permission_verified']);self.assertFalse(p['provider_account_verified'])
    def test_proxy_query_userinfo_http_refused(self):
        for value in ('https://hsn-ai-proxy.onrender.com/groq/openai/v1/chat/completions',
                      'http://api.groq.com/openai/v1/chat/completions',
                      'https://api.groq.com/openai/v1/chat/completions?key=SECRET',
                      'https://user@api.groq.com/openai/v1/chat/completions'):
            with self.assertRaises(ValueError):prepare([config(endpoint=value)],checked_at=NOW)
    def test_unsupported_duplicate_provider(self):
        for rows in ([config(provider='groq')]*2,[dict(config(),provider='nvidia')]):
            with self.assertRaises(ValueError):prepare(rows,checked_at=NOW)
    def test_model_path_injection(self):
        for m in ('x/y','x?key=secret','../model','x\n',''):
            with self.assertRaises(ValueError):prepare([config(model=m)],checked_at=NOW)
    def test_fresh_review_required(self):
        for field in ('model_checked_at','free_tier_checked_at','disclosure_checked_at'):
            for value in (NOW-86401,NOW+1,True,None):
                with self.assertRaises(ValueError):prepare([config(**{field:value})],checked_at=NOW)
    def test_permissions_are_explicit_inputs(self):
        for field in ('free_only_account','disclosure_confirmed'):
            for value in (False,1,'true'):
                with self.assertRaises(ValueError):prepare([config(**{field:value})],checked_at=NOW)
    def test_caps(self):
        for changes in ({'per_report_requests':13},{'per_report_tokens':24001},{'daily_requests':1001},
                        {'request_bytes':65537},{'response_bytes':262145},{'attempt_seconds':16},
                        {'report_seconds':121},{'daily_requests':True}):
            with self.assertRaises(ValueError):prepare([config(**changes)],checked_at=NOW)
    def test_combined_budget(self):
        with self.assertRaises(ValueError):prepare([config('groq',per_report_tokens=20000),config('mistral',per_report_tokens=10000)],checked_at=NOW)
        with self.assertRaises(ValueError):prepare([config('groq',per_report_requests=8),config('mistral',per_report_requests=8)],checked_at=NOW)
    def test_consistent_budgets(self):
        for changes in ({'report_seconds':10},{'daily_requests':1}):
            with self.assertRaises(ValueError):prepare([config(**changes)],checked_at=NOW)
    def test_closed_schema(self):
        with self.assertRaises(ValueError):prepare([config(api_key='DO_NOT_COPY')],checked_at=NOW)
    def test_empty_and_clock(self):
        for rows in ([],[config()]*4,'groq'):
            with self.assertRaises(ValueError):prepare(rows,checked_at=NOW)
        with self.assertRaises(ValueError):prepare([config()],checked_at=True)
    def test_detached_fallback(self):
        rows=[config()];original=copy.deepcopy(rows);p=prepare(rows,checked_at=NOW);p['configs'][0]['model']='changed'
        self.assertEqual(rows,original);self.assertEqual(p['on_exhaustion'],'static_report_fallback');self.assertFalse(p['paid_fallback_allowed'])
