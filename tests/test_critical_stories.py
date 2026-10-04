import unittest
from datetime import datetime, timezone
from integration.critical_stories import critical_stories
from integration.news_api import create_app

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)


def row(stamp, risk='CRITICAL', project='geo'):
    return {'project': project, 'risk_level': risk, 'collected_at': stamp,
            'title': 'Fixture story', 'url': 'https://example.com/story',
            'mongo_id': 'private', 'emailed': True}


class CriticalStoryTests(unittest.TestCase):
    def test_inclusive_cutoff_future_missing_and_policy(self):
        rows = [row('2026-10-03T12:00:00+00:00'), row('2026-10-04T12:00:00+00:00'),
                row('2026-10-03T11:59:59+00:00'), row('2026-10-04T12:00:01+00:00'),
                row(None), row('2026-10-04T12:00:00'),
                row('2026-10-04T12:00:00+00:00', 'HIGH'),
                row('2026-10-04T12:00:00+00:00', project='brics')]
        result = critical_stories(rows, NOW)
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['missing_time_count'], 2)
        self.assertEqual(result['future_time_count'], 1)
        self.assertEqual(result['outside_window_count'], 1)
        self.assertEqual(result['other_project_policy_unavailable_count'], 1)
        self.assertNotIn('mongo_id', result['items'][0])
        self.assertNotIn('emailed', result['items'][0])
        self.assertFalse(result['delivery'])

    def test_zones_cap_and_newest(self):
        rows = [row('2026-10-04T17:30:00+05:30') for _ in range(101)]
        result = critical_stories(rows, NOW)
        self.assertEqual(result['count'], 101)
        self.assertEqual(len(result['items']), 100)
        self.assertTrue(result['truncated'])

    def test_private_route_and_unavailable_reader(self):
        self.assertEqual(create_app().test_client().get('/api/critical-stories').status_code, 403)
        def unavailable():
            raise RuntimeError('fixture unavailable')
        response = create_app(reader=unavailable, authorize=lambda req: True).test_client().get('/api/critical-stories')
        self.assertEqual(response.status_code, 503)

    def test_endpoint_empty_is_loaded_not_total(self):
        response = create_app(authorize=lambda req: True).test_client().get('/api/critical-stories')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['not_total_database'])
        self.assertEqual(response.json['items'], [])

    def test_explicit_clock(self):
        with self.assertRaises(ValueError):
            critical_stories([], datetime(2026, 10, 4))
