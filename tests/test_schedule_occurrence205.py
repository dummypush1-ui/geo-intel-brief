import ast
import inspect
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from integration import schedule_occurrence205 as module


class Occurrences205(unittest.TestCase):
    def calculate(self, anchor, zone='Asia/Calcutta', clock='09:00', day='monday', cadence='daily', ambiguous='first', nonexistent='skip'):
        settings = {'GEO_SCHEDULER_TIMEZONE': zone, 'GEO_WEEKLY_REPORT_DAY': day, 'GEO_DAILY_RUN_TIME': clock}
        return module.next_occurrence(settings, anchor=anchor, cadence=cadence, ambiguous=ambiguous, nonexistent=nonexistent)

    def utc(self, text):
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)

    def test_fixed_zone_equality_and_microsecond(self):
        instant = self.utc('2026-10-09T03:30:00')
        self.assertEqual(self.calculate(instant - timedelta(microseconds=1))['utc'], '2026-10-09T03:30:00+00:00')
        for anchor in [instant, instant + timedelta(microseconds=1)]:
            out = self.calculate(anchor)
            self.assertEqual(out['utc'], '2026-10-10T03:30:00+00:00')
            self.assertEqual(out['offset_seconds'], 19800)
            self.assertEqual(out['fold'], 0)
            self.assertEqual(out['local_weekday'], 'saturday')
            self.assertFalse(out['catch_up'])
            self.assertFalse(out['timer_installed'])

    def test_weekly_boundary_midnight_leapday(self):
        out = self.calculate(self.utc('2026-10-11T18:29:59'), clock='00:00', cadence='weekly')
        self.assertEqual(out['local'], '2026-10-12T00:00:00+05:30')
        self.assertEqual(out['local_weekday'], 'monday')
        self.assertEqual(self.calculate(self.utc('2024-02-28T23:59:59'), zone='UTC', clock='00:00')['utc'], '2024-02-29T00:00:00+00:00')

    def test_new_york_weekly_gap_skip_past_seven_days(self):
        anchor = self.utc('2026-03-01T07:30:00')
        out = self.calculate(anchor, 'America/New_York', '02:30', 'sunday', 'weekly')
        self.assertEqual(out['utc'], '2026-03-15T06:30:00+00:00')
        self.assertEqual(out['skipped_nonexistent'], 1)
        with self.assertRaises(module.OccurrenceRefused):
            self.calculate(anchor, 'America/New_York', '02:30', 'sunday', 'weekly', nonexistent='refuse')

    def test_new_york_fold_strict_anchors(self):
        first = self.utc('2026-11-01T05:30:00')
        second = self.utc('2026-11-01T06:30:00')
        for anchor in [first, first + timedelta(minutes=30)]:
            self.assertEqual(self.calculate(anchor, 'America/New_York', '01:30', ambiguous='first')['utc'], '2026-11-02T06:30:00+00:00')
            out = self.calculate(anchor, 'America/New_York', '01:30', ambiguous='second')
            self.assertEqual(out['utc'], second.isoformat())
            self.assertEqual(out['fold'], 1)
        for policy in ['first', 'second', 'refuse']:
            self.assertEqual(self.calculate(second, 'America/New_York', '01:30', ambiguous=policy)['utc'], '2026-11-02T06:30:00+00:00')
        before = first - timedelta(microseconds=1)
        self.assertEqual(self.calculate(before, 'America/New_York', '01:30')['utc'], first.isoformat())
        with self.assertRaises(module.OccurrenceRefused):
            self.calculate(before, 'America/New_York', '01:30', ambiguous='refuse')

    def test_lord_howe_half_hour_fold(self):
        anchor = self.utc('2026-04-04T14:00:00')
        first = self.calculate(anchor, 'Australia/Lord_Howe', '01:45', ambiguous='first')
        second = self.calculate(anchor, 'Australia/Lord_Howe', '01:45', ambiguous='second')
        self.assertEqual(first['utc'], '2026-04-04T14:45:00+00:00')
        self.assertEqual(second['utc'], '2026-04-04T15:15:00+00:00')
        self.assertEqual(second['fold'], 1)

    def test_apia_skipped_whole_day(self):
        out = self.calculate(self.utc('2011-12-29T22:00:00'), 'Pacific/Apia', '12:00')
        self.assertEqual(out['local'], '2011-12-31T12:00:00+14:00')
        self.assertEqual(out['skipped_nonexistent'], 1)
        with self.assertRaises(module.OccurrenceRefused):
            self.calculate(self.utc('2011-12-29T22:00:00'), 'Pacific/Apia', '12:00', nonexistent='refuse')

    def test_sao_paulo_nonexistent_midnight(self):
        out = self.calculate(self.utc('2018-11-03T03:00:00'), 'America/Sao_Paulo', '00:00')
        self.assertEqual(out['local'], '2018-11-05T00:00:00-02:00')
        self.assertEqual(out['skipped_nonexistent'], 1)

    def test_dublin_negative_dst_fold(self):
        anchor = self.utc('2026-10-25T00:00:00')
        first = self.calculate(anchor, 'Europe/Dublin', '01:30', ambiguous='first')
        second = self.calculate(anchor, 'Europe/Dublin', '01:30', ambiguous='second')
        self.assertEqual(first['utc'], '2026-10-25T00:30:00+00:00')
        self.assertEqual(second['utc'], '2026-10-25T01:30:00+00:00')
        self.assertEqual(second['fold'], 1)

    def test_anchor_exact_utc_and_closed_policies(self):
        class Subclass(datetime):
            pass
        for anchor in [datetime(2026, 1, 1), datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1))), Subclass(2026, 1, 1, tzinfo=timezone.utc), '2026-01-01']:
            with self.assertRaises(module.OccurrenceRefused):
                self.calculate(anchor)
        for field, values in [('cadence', ['monthly', None, True]), ('ambiguous', ['FIRST', None, True]), ('nonexistent', ['shift', None, True])]:
            for value in values:
                with self.assertRaises(module.OccurrenceRefused):
                    self.calculate(self.utc('2026-01-01'), **{field: value})
        for day in ['bad', ' monday']:
            with self.assertRaises(module.OccurrenceRefused):
                self.calculate(self.utc('2026-01-01'), day=day)

    def test_zone_failure_static_and_provenance(self):
        for zone in ['Not/Exists', '../secret', '', 'localtime', 'posixrules', 'Factory']:
            with self.assertRaises(module.OccurrenceRefused) as error:
                self.calculate(self.utc('2026-01-01'), zone=zone)
            self.assertEqual(str(error.exception), 'Schedule occurrence refused')
        result = self.calculate(self.utc('2026-01-01'))
        self.assertIn(result['tzdata']['source'], ('system_TZPATH', 'tzdata_package'))
        self.assertEqual(len(result['tzdata']['zonefile_sha256']), 64)
        self.assertIn('tzdata_package_version', result['tzdata'])
        self.assertEqual(result['search_local_dates'], 15)

    def test_none_window_and_no_effect_imports(self):
        # Synthetic all-dates gap proves the bounded terminal shape.
        with patch.object(module, 'range', return_value=() , create=True):
            result = self.calculate(self.utc('2026-01-01'))
        self.assertEqual(result['state'], 'none_in_window')
        self.assertIsNone(result['utc'])
        tree = ast.parse(inspect.getsource(module))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertFalse(imports & {'os', 'socket', 'smtplib', 'schedule', 'pymongo', 'requests'})


if __name__ == '__main__':
    unittest.main()
