import unittest
from copy import deepcopy
from unittest.mock import patch
from integration.offline_collection_cycle import run_offline_cycle
from integration.fake_collection_writer import FakeCollectionWriter

CATS = ['GEOPOLITICS', 'TRADE', 'SANCTIONS', 'RISK', 'CONFERENCE', 'GENERAL']
NOW = '2026-10-04T14:00:00+05:30'


def row(title, url, source='Fixture'):
    return {'title': title, 'url': url, 'source': source, 'summary': ''}


class OfflineCycleTests(unittest.TestCase):
    def test_processing_then_insert_duplicate_and_synthetic_failure(self):
        writer = FakeCollectionWriter()
        rows = [row('Trade agreement tariff notification', 'https://example.com/a'),
                row('Regional security conflict military', 'https://example.com/b')]
        before = deepcopy(rows)
        with patch('socket.socket', side_effect=AssertionError('Network forbidden')):
            first = run_offline_cycle('geo', rows, CATS, .85, NOW, writer,
                                      ['https://example.com/b'])
            second = run_offline_cycle('geo', rows[:1], CATS, .85, NOW, writer)
        self.assertEqual(first['prepared_count'], 2)
        self.assertEqual(first['writer']['inserted_count'], 1)
        self.assertEqual(first['writer']['failed_count'], 1)
        self.assertEqual(second['writer']['duplicate_count'], 1)
        self.assertEqual(rows, before)
        self.assertFalse(first['live_writes'])
        self.assertFalse(first['network'])
        self.assertFalse(first['delivery'])

    def test_projects_remain_separate_and_brics_filter_retained(self):
        writer = FakeCollectionWriter()
        rows = [row('BRICS summit joint declaration', 'https://example.com/a'),
                row('Local sports final', 'https://example.com/b')]
        result = run_offline_cycle('brics', rows, CATS, .8, NOW, writer)
        self.assertEqual(result['prepared_count'], 1)
        self.assertEqual(len(writer.snapshot('brics')), 1)
        self.assertEqual(writer.snapshot('geo'), {})
        doc = next(iter(writer.snapshot('brics').values()))
        self.assertEqual(doc['collected_at'], '2026-10-04T08:30:00+00:00')

    def test_invalid_batch_or_clock_leaves_fake_store_unchanged(self):
        writer = FakeCollectionWriter()
        valid = row('BRICS summit', 'https://example.com/a')
        for rows, clock in [([valid, {}], NOW), ([valid], '2026-10-04'),
                            ([dict(valid, extra=object())], NOW),
                            ([dict(valid, extra=float('nan'))], NOW)]:
            with self.assertRaises(ValueError):
                run_offline_cycle('brics', rows, CATS, .8, clock, writer)
            self.assertEqual(writer.snapshot('brics'), {})

    def test_no_arbitrary_backend_or_subclass(self):
        class ExternalBackend(FakeCollectionWriter):
            def write(self, *args, **kwargs):
                raise AssertionError('Must not call arbitrary backend')
        for writer in (object(), ExternalBackend()):
            with self.assertRaises(ValueError):
                run_offline_cycle('geo', [], CATS, .85, NOW, writer)

    def test_empty_selection_is_not_an_insert_or_a_live_write(self):
        writer = FakeCollectionWriter()
        result = run_offline_cycle('brics', [], CATS, .8, NOW, writer)
        self.assertEqual(result['writer']['results'], [])
        self.assertEqual(result['writer']['inserted_count'], 0)
        self.assertEqual(writer.snapshot('brics'), {})

    def test_exact_instance_cannot_override_write(self):
        writer = FakeCollectionWriter()
        called = []
        with self.assertRaises(AttributeError):
            writer.write = lambda *args: called.append(True)
        result = run_offline_cycle('geo', [], CATS, .85, NOW, writer)
        self.assertEqual(called, [])
        self.assertEqual(result['writer']['state'], 'fake_store_only')

    def test_corrupted_fixture_state_is_rejected_before_processing(self):
        writer = FakeCollectionWriter()
        writer._geo = {'x': object()}
        with self.assertRaises(ValueError):
            run_offline_cycle('geo', [], CATS, .85, NOW, writer)
        writer._geo = []
        with self.assertRaises(ValueError):
            run_offline_cycle('brics', [], CATS, .8, NOW, writer)

    def test_project_subclass_rejected_without_executing_hooks(self):
        class Project(str):
            def __eq__(self, other):
                raise AssertionError('Custom equality executed')
        with self.assertRaises(ValueError):
            run_offline_cycle(Project('geo'), [], CATS, .85, NOW, FakeCollectionWriter())

    def test_category_list_subclass_rejected_without_executing_hooks(self):
        class Categories(list):
            def __iter__(self):
                raise AssertionError('Custom iteration executed')
            def __contains__(self, item):
                raise AssertionError('Custom membership executed')
        with self.assertRaises(ValueError):
            run_offline_cycle('geo', [], Categories(CATS), .85, NOW, FakeCollectionWriter())

    def test_category_string_subclass_rejected_without_executing_hooks(self):
        class Category(str):
            def __eq__(self, other):
                raise AssertionError('Custom equality executed')
        with self.assertRaises(ValueError):
            run_offline_cycle('geo', [], [Category('GENERAL')], .85, NOW, FakeCollectionWriter())
