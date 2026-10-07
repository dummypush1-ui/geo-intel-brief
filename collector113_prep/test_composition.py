import gzip
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from .feed_composition import original_catalog, select_response, CompositionRefused
from collector113_prep.transport_policy import TransportRefused
from collector112_prep.parser_runner import ParserRefused
D = datetime(2026, 1, 1, tzinfo=timezone.utc)
F = (('Fixture','https://example.com/rss','HIGH'),)
RSS = b'''<rss version="2.0"><channel><title>Fixture</title>
<item><title>Trade tariff</title><link>https://example.com/a</link><description>&lt;b&gt;Trade&lt;/b&gt;</description><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item>
<item><title>Old</title><link>https://example.com/old</link><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item>
<item><title>No link</title></item></channel></rss>'''
class Tests(unittest.TestCase):
    def select(self, blob=RSS, headers=None, **kwargs):
        return select_response(F,F[0][1],answers=('8.8.8.8',),peer='8.8.8.8',
                               status=200,headers=headers or {},chunks=[blob],
                               deadline=10,clock=lambda:1,cutoff=D,fallback_clock=D,**kwargs)
    def test_original_default_catalog_without_import_effects(self):
        feeds=original_catalog()
        self.assertEqual(len(feeds),25)
        self.assertEqual(feeds[0][0],'BBC World')
        self.assertEqual(feeds[-1][0],'Australian Institute of International Affairs')
    def test_supplied_gzip_to_isolated_parser_to_original_selection(self):
        r=self.select(gzip.compress(RSS),{'content-encoding':'gzip'})
        self.assertEqual(r['parser_entry_count'],3)
        self.assertEqual(r['selection']['selected_count'],1)
        row=r['selection']['candidates'][0]
        self.assertEqual(row['summary'],'Trade')
        self.assertEqual(row['source'],'Fixture')
        self.assertEqual(row['published'],D)
        self.assertFalse(r['writes']);self.assertFalse(r['network'])
    def test_original_limit_and_fixed_date_fallback(self):
        self.assertEqual(self.select(max_items=1)['selection']['selected_count'],1)
        blob=b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link><pubDate>bad</pubDate></item></channel></rss>'
        r=self.select(blob)['selection']
        self.assertEqual(r['date_fallback_count'],1)
        self.assertEqual(r['candidates'][0]['published'],D)
    def test_bozo_remains_visible_not_health(self):
        r=self.select(b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link></item>')
        self.assertTrue(r['parser_bozo'])
        self.assertNotIn('healthy',r)
    def test_policy_refuses_before_parser(self):
        with patch('collector113_prep.feed_composition.parse_supplied_bytes') as p:
            with self.assertRaises(TransportRefused):self.select(b'x',{'content-length':'2'})
            p.assert_not_called()
    def test_parser_refuses_before_selection(self):
        with patch('collector113_prep.feed_composition.prepare_supplied_feed') as p:
            with self.assertRaises(ParserRefused):self.select(b'<!DOCTYPE rss>'+RSS)
            p.assert_not_called()
    def test_catalog_source_drift(self):
        with patch('collector113_prep.feed_composition.PINS',{'intelligence/geo/collectors/rss.py':'0'*64}):
            with self.assertRaises(CompositionRefused):original_catalog()
if __name__ == '__main__': unittest.main()
