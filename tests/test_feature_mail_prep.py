# Copyright (c) 2026 Push. All rights reserved.
import ast
from datetime import datetime, timezone, timedelta
import pathlib
import socket
import unittest
from unittest.mock import patch
from feature_mail_prep.reports import prepare_report, MAX_ROWS
from feature_mail_prep.cleanup import prepare_cleanup, article_hash

NOW = datetime(2026, 10, 8, 0, tzinfo=timezone.utc)
ROOT = pathlib.Path(__file__).resolve().parents[1]


def article(n=1, **kw):
    row = {'_id': 'fixture%d' % n, 'title': 'Fixture trade headline %d' % n,
           'summary': 'Fixture summary', 'url': 'https://example.com/news/%d' % n,
           'source': 'Fixture Wire', 'category': 'TRADE', 'country': 'India',
           'risk_level': 'HIGH', 'score': 20, 'credibility': 'HIGH',
           'corroboration': 1, 'published': (NOW - timedelta(hours=1)).isoformat(),
           'created_at': (NOW - timedelta(hours=1)).isoformat(), 'emailed': False}
    row.update(kw)
    return row


def event(**kw):
    row = {'name': 'Fixture meeting', 'event_date': NOW.date().isoformat(),
           'source_url': 'https://example.com/event', 'category': 'CONFERENCE',
           'confidence': 'HIGH', 'description': 'Fixture event'}
    row.update(kw)
    return row


class MailPreparation(unittest.TestCase):
    def test_no_network_all_paths(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('network')):
            for kind in ('digest', 'critical', 'weekly'):
                r = prepare_report(kind, [article(risk_level='CRITICAL')], [], NOW)
                self.assertFalse(r['network'] or r['writes'] or r['delivery'])
                self.assertEqual(r['delivery_path'], 'apps_script')
            self.assertEqual(prepare_cleanup([article()], NOW)['deleted'], 0)

    def test_critical_window_and_order(self):
        rows = [article(1, risk_level='CRITICAL', score=1),
                article(2, risk_level='CRITICAL', score=99),
                article(3, risk_level='CRITICAL', created_at=(NOW-timedelta(hours=7)).isoformat())]
        r = prepare_report('critical', rows, [], NOW)
        self.assertEqual(r['diagnostic_ids'], ['fixture2', 'fixture1'])
        self.assertEqual(r['critical_count'], 2)

    def test_empty_critical_skip(self):
        self.assertTrue(prepare_report('critical', [], [], NOW)['skip'])

    def test_weekly_top20_and_counts(self):
        rows = [article(i, score=i) for i in range(25)]
        r = prepare_report('weekly', rows, [], NOW)
        self.assertEqual((r['fetched_sample_count'], r['displayed_sample_count']), (25, 20))
        self.assertIn('India (25)', r['html'])
        self.assertNotIn('Fixture trade headline 0<', r['html'])
        self.assertEqual(r['diagnostic_ids'], [])

    def test_weekly_excludes_old(self):
        r = prepare_report('weekly', [article(created_at=(NOW-timedelta(days=8)).isoformat())], [], NOW)
        self.assertEqual(r['fetched_sample_count'], 0)

    def test_digest_fetch_display_difference(self):
        r = prepare_report('digest', [article(score=0)], [], NOW)
        self.assertEqual((r['fetched_sample_count'], r['displayed_sample_count']), (1, 0))
        self.assertFalse(r['skip'])
        self.assertEqual(r['marking_policy'], 'unresolved_fetched_vs_displayed')

    def test_digest_caps_and_sent(self):
        rows = [article(i) for i in range(70)] + [article(100, score=999, emailed=True)]
        r = prepare_report('digest', rows, [], NOW)
        self.assertEqual(r['fetched_sample_count'], 60)
        self.assertNotIn('fixture100', r['diagnostic_ids'])

    def test_digest_events_window(self):
        r = prepare_report('digest', [], [event(), event(name='Too far', event_date=(NOW+timedelta(days=91)).date().isoformat())], NOW)
        self.assertIn('Fixture meeting', r['html'])
        self.assertNotIn('Too far', r['html'])
        self.assertTrue(r['skip'])  # preserves Apps Script event-only skip

    def test_no_invented_events_other_reports(self):
        for kind in ('weekly', 'critical'):
            with self.assertRaises(ValueError): prepare_report(kind, [], [event()], NOW)

    def test_html_and_link_safety(self):
        r = prepare_report('critical', [article(title='<img src=x onerror=alert(1)>', risk_level='CRITICAL')], [], NOW)
        self.assertIn('&lt;img', r['html'])
        self.assertNotIn('<img', r['html'])
        for link in ('javascript:alert(1)', 'https://example.com/?key=secret', 'https://u:p@example.com/', 'https://127.0.0.1/', 'https://localhost/', 'https://127.1/x', 'https://0x7f.0.0.1/', 'https://foo.internal/', 'https://example.com./'):
            with self.assertRaises(ValueError): prepare_report('digest', [article(url=link)], [], NOW)

    def test_closed_fields_no_coercion(self):
        class Trap:
            def __str__(self): raise AssertionError('coercion')
        for row in (article(summary=Trap()), article(secret='private'), article(score=True), article(score=10**1000)):
            with self.assertRaises(ValueError): prepare_report('digest', [row], [], NOW)

    def test_identity_hidden(self):
        with self.assertRaises(ValueError):
            prepare_report('digest', [article(title='fixture1 leak')], [], NOW)
        r = prepare_report('digest', [article(_id='1')], [], NOW)
        self.assertEqual(r['diagnostic_ids'], ['1'])

    def test_caps(self):
        with self.assertRaises(ValueError): prepare_report('digest', [article(i) for i in range(MAX_ROWS+1)], [], NOW)
        with self.assertRaises(ValueError): prepare_report('digest', [article(i, summary='x'*16000) for i in range(40)], [], NOW)

    def test_duplicate_id_and_clock(self):
        with self.assertRaises(ValueError): prepare_report('digest', [article(), article()], [], NOW)
        with self.assertRaises(ValueError): prepare_report('digest', [], [], NOW.replace(tzinfo=None))

    def test_inputs_unchanged(self):
        rows = [article()]; evs = [event()]; before = repr((rows, evs))
        prepare_report('digest', rows, evs, NOW)
        self.assertEqual(repr((rows, evs)), before)

    def test_cleanup_strict_boundary(self):
        rows = [article(1, created_at=(NOW-timedelta(days=31)).isoformat()),
                article(2, created_at=(NOW-timedelta(days=30)).isoformat())]
        r = prepare_cleanup(rows, NOW)
        self.assertEqual(r['candidate_count'], 1)
        self.assertEqual(r['candidates'][0]['diagnostic_id'], 'fixture1')
        self.assertEqual(r['deletion_ids'], [])

    def test_cleanup_even_matching_receipt_is_held(self):
        a = article(created_at=(NOW-timedelta(days=31)).isoformat())
        r = prepare_cleanup([a], NOW, supplied_receipt_hashes={'fixture1': article_hash(a)})
        c = r['candidates'][0]
        self.assertTrue(c['supplied_hash_matches'])
        self.assertFalse(c['archive_verified'])
        self.assertEqual(c['state'], 'held_not_deletable')

    def test_cleanup_changed_content_mismatch(self):
        a = article(created_at=(NOW-timedelta(days=31)).isoformat())
        digest = article_hash(a); a['summary'] = 'changed'
        self.assertFalse(prepare_cleanup([a], NOW, supplied_receipt_hashes={'fixture1': digest})['candidates'][0]['supplied_hash_matches'])

    def test_cleanup_unknown_receipt_refused(self):
        with self.assertRaises(ValueError): prepare_cleanup([], NOW, supplied_receipt_hashes={'other': 'a'*64})
        for days in (0, True, -1, 9999):
            with self.assertRaises(ValueError): prepare_cleanup([], NOW, days=days)

    def test_source_renderers_still_pinned(self):
        from integration.renderer_scope import renderer
        for kind, deps in [('geo_critical', {}), ('geo_weekly', {'weekly_top_articles':lambda **kw:[], 'category_counts':lambda **kw:[], 'top_countries':lambda **kw:[]})]:
            self.assertTrue(callable(renderer(kind, deps, NOW)))

    def test_no_sender_runtime_imports(self):
        for path in (ROOT/'feature_mail_prep').glob('*.py'):
            tree = ast.parse(path.read_text())
            imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            self.assertFalse(any(x and ('delivery' in x or 'runtime' in x or 'database' in x or 'config' in x) for x in imports))

if __name__ == '__main__': unittest.main()
