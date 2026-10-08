# Copyright (c) 2026 Push. All rights reserved.
import copy
import json
import unittest
from integration.india_open_data.core import *


from tests.india_open_data.fixtures import spec, CSV, ROW, UUID


class CoreTests(unittest.TestCase):
    def test_import_provenance_and_dates(self):
        r = import_export(CSV, 'csv', spec())[0]
        self.assertEqual(r['value_decimal'], '72.500')
        self.assertEqual(r['freshness'], 'unknown')
        self.assertIsNone(r['dataset_date'])
        self.assertEqual(r['geography']['district'], 'Nilgiris')
        self.assertEqual(r['payload_sha256'], hashlib.sha256(CSV).hexdigest())

    def test_dated_not_fresh(self):
        r = import_export(CSV, 'csv', spec(dataset_date='2021-01-01'))[0]
        self.assertEqual(r['freshness'], 'dated_snapshot')

    def test_id_is_deterministic_not_payload_or_value(self):
        a = import_export(CSV, 'csv', spec())[0]
        b = import_export(CSV.replace(b'72.500', b'73.5'), 'csv', spec())[0]
        self.assertEqual(a['_id'], b['_id'])
        self.assertNotEqual(a['payload_sha256'], b['payload_sha256'])

    def test_json_import(self):
        r = import_export(json.dumps({'records': [ROW]}).encode(), 'json', spec())
        self.assertEqual(len(r), 1)

    def test_missing_not_zero(self):
        for value in ('', 'NA', '..', '-', 'null'):
            r = import_export(CSV.replace(b'72.500', value.encode()), 'csv', spec())[0]
            self.assertIsNone(r['value_decimal'])
            self.assertEqual(r['value_state'], 'missing')
        self.assertEqual(number('0'), '0')

    def test_numeric_no_guesses_and_precision(self):
        self.assertEqual(number('123456789012345678901234567890.123'), '123456789012345678901234567890.123')
        for bad in ('1,000', '3%', 'NaN', 'Infinity', '1e999999', '1e-999999', True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                number(bad)

    def test_spec_schema_urls(self):
        for url in ('http://ndap.niti.gov.in/', 'https://localhost/',
                    'https://niti.gov.in.evil.com/', 'https://evil.com/',
                    'https://niti.gov.in/?token=x', 'https://user@niti.gov.in/',
                    'https://niti.gov.in:444/', 'https://niti.gov.in/#x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                spec(source_url=url)
        with self.assertRaises(ValueError): spec(columns={'value':'x'})
        with self.assertRaises(ValueError): spec(dataset_date='2026-02-30')
        with self.assertRaises(ValueError): spec(reuse_reviewed=1)

    def test_malformed_exports(self):
        cases = [b'', b'\xff', b'a,a\n1,2\n', b'a,b\n1\n', b'a\n1,2\n', b'<!DOCTYPE html>']
        for body in cases:
            with self.subTest(body=body), self.assertRaises((ValueError, UnicodeError)):
                import_export(body, 'csv', spec())
        with self.assertRaises(ValueError): parse_export(b'[]', 'json')
        with self.assertRaises(ValueError): parse_export(b'x', 'pdf')
        with self.assertRaises(ValueError): parse_export(b'x' * (MAX_BYTES+1), 'csv')

    def test_duplicates_hold(self):
        with self.assertRaises(ValueError):
            import_export(CSV + CSV.splitlines(keepends=True)[1], 'csv', spec())

    def test_bounds_and_non_scalar(self):
        for rows in ([ROW] * (MAX_ROWS+1), [dict(ROW, extra={})], [dict(ROW, extra=True)]):
            with self.assertRaises(ValueError): validate_rows(rows)
        with self.assertRaises(ValueError):
            normalize([{'Indicator':'x'}], spec(), 'a'*64)

    def test_disabled_never_transport(self):
        def fail(*args): self.fail('network called')
        self.assertEqual(pull_export(spec(), 'bad', 'csv', fail)['state'], 'disabled')
        self.assertEqual(pull_ogd(spec(), 'bad', 'secret', fail)['state'], 'disabled')

    def test_reuse_gate(self):
        def fail(*args): self.fail('network called')
        self.assertEqual(pull_export(spec(), 'bad', 'csv', fail, enabled=True)['state'], 'held')

    def test_export_success_and_sanitized_failure(self):
        s = spec(reuse_reviewed=True)
        self.assertEqual(pull_export(s, s['source_url'], 'csv', lambda *args: CSV, enabled=True)['state'], 'complete')
        def fail(*args): raise RuntimeError('private secret')
        r = pull_export(s, s['source_url'], 'csv', fail, enabled=True)
        self.assertNotIn('private', str(r))
        self.assertEqual(r['state'], 'failed')
        with self.assertRaises(ValueError):
            pull_export(s, 'https://data.gov.in/', 'csv', fail, enabled=True)

    def test_ogd_pages(self):
        calls = []
        s = spec(provider='ogd', source_url='https://www.data.gov.in/', reuse_reviewed=True)
        def transport(url, params, max_bytes, timeout):
            calls.append(dict(params))
            row = dict(ROW, District='District' + str(params['offset']))
            return json.dumps({'status': 'ok', 'total': 2, 'count': 1,
                               'offset': params['offset'], 'records': [row]}).encode()
        r = pull_ogd(s, UUID, 'do-not-expose', transport, enabled=True, page_size=1)
        self.assertEqual(r['state'], 'complete')
        self.assertEqual([c['offset'] for c in calls], [0,1])
        self.assertNotIn('do-not-expose', str(r))

    def test_ogd_decimal_string_metadata(self):
        s=spec(provider='ogd',reuse_reviewed=True)
        page={'status':'ok','total':'1','count':'1','offset':'0','records':[ROW]}
        r=pull_ogd(s,UUID,'secret',lambda *args:json.dumps(page).encode(),enabled=True)
        self.assertEqual(r['state'],'complete')
        for bad in (True, 1.0, '1.0', '-1', ' 1', '01'):
            with self.assertRaises(ValueError):metadata_int(bad)

    def test_ogd_failures_no_partial_records(self):
        s = spec(provider='ogd', source_url='https://www.data.gov.in/', reuse_reviewed=True)
        base = {'status':'ok', 'total':1, 'count':1, 'offset':0, 'records':[ROW]}
        changes = [dict(status='error'), dict(total='1.0'), dict(total=0), dict(total=10001),
                   dict(count=2), dict(offset=1), dict(offset=False), dict(records=[]), dict(records='x')]
        for change in changes:
            page = dict(base, **change)
            r = pull_ogd(s, UUID, 'secret', lambda *args: json.dumps(page).encode(), enabled=True)
            self.assertEqual(r['state'], 'failed', change)
            self.assertEqual(r['records'], [])

    def test_ogd_changed_total_repeated_page_and_budget(self):
        s = spec(provider='ogd', reuse_reviewed=True)
        for mode in ('changed', 'repeated', 'limit'):
            def transport(url, params, *args):
                i = params['offset']
                row = dict(ROW, District=str(i) if mode != 'repeated' else 'same')
                return json.dumps({'status':'ok', 'total':3+i if mode=='changed' else 3,
                                   'count':1, 'offset':i, 'records':[row]}).encode()
            r = pull_ogd(s, UUID, 'secret', transport, enabled=True, page_size=1, max_pages=2)
            self.assertEqual(r['state'], 'partial' if mode=='limit' else 'failed')
            self.assertEqual(r['records'], [])

    def test_atomic_candidate_and_no_mutation(self):
        old = {'other': {'records': [1]}}
        before = copy.deepcopy(old)
        for state in ('disabled','held','partial','failed'):
            self.assertEqual(stage_snapshot({'state':state}, old, 'niti_health_test', 'bad'), old)
        result = {'state':'complete', 'records':import_export(CSV, 'csv', spec())}
        new = stage_snapshot(result, old, 'niti_health_test', '2026-10-08T23:00:00+05:30')
        self.assertEqual(old, before)
        self.assertIn('niti_health_test', new)
        new['other']['records'].append(2)
        self.assertEqual(old, before)
        with self.assertRaises(ValueError):
            stage_snapshot(result, old, 'niti_health_test', '2026-10-08T23:00:00')
        with self.assertRaises(ValueError):
            stage_snapshot(result, old, 'wrong', '2026-10-08T23:00:00+05:30')

if __name__ == '__main__': unittest.main()
