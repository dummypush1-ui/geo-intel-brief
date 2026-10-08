# Copyright (c) 2026 Push. All rights reserved.
"""Synthetic inputs only. Network blocked for every test including imports."""
from contextlib import ExitStack
from copy import deepcopy
import importlib
import socket
import unittest
from unittest.mock import patch

NOW = '2026-10-08T12:00:00Z'
EVIDENCE = {'evidence_id': 'fixture:evidence', 'url': 'https://example.invalid/carrier-fixture',
            'publisher': 'Synthetic fixture', 'release': 'fixture-v1', 'observed_at': '2026-10-08T00:00:00Z',
            'expires_at': '2026-10-09T00:00:00Z', 'rights_state': 'synthetic_fixture', 'scope': 'fixture_only'}
CARRIER = {'carrier_id': 'fixture:carrier', 'name': 'Synthetic Ocean Company',
           'aliases': ['Synthetic Fleet'], 'mode': 'maritime', 'evidence_ids': ['fixture:evidence']}
PORTS = [{'location_id': 'fixture:port_' + x, 'name': 'Synthetic Port ' + x,
          'function': 'port', 'evidence_ids': ['fixture:evidence']} for x in ('a', 'b', 'c')]
LEG = {'origin': 'fixture:port_a', 'destination': 'fixture:port_b', 'departure_at': NOW,
       'arrival_at': '2026-10-08T13:00:00Z', 'classifier': 'estimated'}
ROUTE = {'route_id': 'fixture:route', 'carrier_id': 'fixture:carrier', 'service': 'Synthetic service',
         'valid_from': '2026-10-08T00:00:00Z', 'valid_until': '2026-10-09T00:00:00Z',
         'legs': [LEG], 'evidence_ids': ['fixture:evidence']}
EVENT = {'event_id': 'fixture:event', 'subject_id': 'fixture:subject', 'category': 'transport',
         'code': 'arrived', 'classifier': 'actual', 'event_at': '2026-10-08T01:00:00Z',
         'source_recorded_at': '2026-10-08T02:00:00Z', 'revision': 1,
         'location_id': 'fixture:port_a', 'cancelled': False, 'evidence_ids': ['fixture:evidence']}


def deny_network(*args, **kwargs):
    raise AssertionError('Carrier A network forbidden')


class CarrierCoreTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for target in ('socket.socket', 'socket.create_connection', 'socket.getaddrinfo',
                       'socket.gethostbyname', 'socket.gethostbyname_ex'):
            self.stack.enter_context(patch(target, side_effect=deny_network))
        self.m = importlib.import_module('feature_carrier_prep.models')
        self.e = importlib.import_module('feature_carrier_prep.evidence')
        self.r = importlib.import_module('feature_carrier_prep.registry')
        self.routes = importlib.import_module('feature_carrier_prep.route_catalog')
        self.t = importlib.import_module('feature_carrier_prep.timeline')
        self.ev = self.e.catalog([deepcopy(EVIDENCE)], as_of=NOW)
        self.carriers = self.r.carriers([deepcopy(CARRIER)], self.ev)
        self.ports = self.r.locations(deepcopy(PORTS), self.ev)

    def event(self, rows):
        return self.t.prepare(rows, self.ports, self.ev, as_of=NOW)

    def route(self, rows):
        return self.routes.catalog(rows, self.carriers, self.ports, self.ev, as_of=NOW)

    def test_socket_block_really_enforced(self):
        for action in (lambda: socket.socket(), lambda: socket.create_connection(('example.invalid', 443)),
                       lambda: socket.getaddrinfo('example.invalid', 443)):
            with self.assertRaisesRegex(AssertionError, 'network forbidden'):
                action()

    def test_loopback_guard(self):
        for host in ('127.0.0.1', '::1'):
            self.assertEqual(self.m.loopback_host(host), host)
        for host in ('0.0.0.0', '::', '192.168.1.1', 'localhost', '127.0.0.1.evil', None, '::1%eth0'):
            with self.subTest(host=host), self.assertRaises(ValueError):
                self.m.loopback_host(host)

    def test_fixture_identifiers_and_closed_records(self):
        for key in ('MSK', 'INMAA', 'ABCD1234567', 'fixture:', 'fixture:A', 'fixture:a\n', [], True):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.m.fixture_id(key)
        for bad in ({**EVENT, 'booking_number': 'real-like'}, {k: v for k, v in EVENT.items() if k != 'event_id'}):
            with self.assertRaises(ValueError): self.event([bad])
        for field in ('event_id', 'subject_id'):
            with self.assertRaises(ValueError): self.event([{**EVENT, field: 'ABCD1234567'}])

    def test_timestamp_validation_and_offsets(self):
        self.assertEqual(self.m.timestamp(NOW), self.m.timestamp('2026-10-08T17:30:00+05:30'))
        for value in (NOW[:-1], '2026-02-30T12:00:00Z', '2026-10-08T12:00:00+99:00', '2026-10-08', None, float('nan')):
            with self.subTest(value=value), self.assertRaises(ValueError): self.m.timestamp(value)

    def test_evidence_expiry_and_unverified_labels(self):
        stale = self.e.catalog([EVIDENCE], as_of='2026-10-09T00:00:00Z')
        self.assertEqual(stale['fixture:evidence']['state'], 'stale')
        self.assertFalse(stale['fixture:evidence']['verified_live'])
        for field, value in (('url', 'https://smdg.org/'), ('rights_state', 'approved'),
                             ('scope', 'live'), ('observed_at', '2026-10-10T00:00:00Z'),
                             ('expires_at', '2026-10-07T00:00:00Z')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.e.catalog([{**EVIDENCE, field: value}], as_of=NOW)
        with self.assertRaises(ValueError): self.e.catalog([EVIDENCE, EVIDENCE], as_of=NOW)

    def test_registry_exact_lookup_and_no_alias_guess(self):
        self.assertEqual(self.r.lookup(self.carriers, 'Synthetic Fleet'), 'fixture:carrier')
        self.assertIsNone(self.r.lookup(self.carriers, 'synthetic fleet'))
        self.assertIsNone(self.r.lookup(self.carriers, 'Synthetic Fleet mentioned'))
        for row in ({**CARRIER, 'mode': 'air'}, {**CARRIER, 'aliases': ['Synthetic Ocean Company']},
                    {**CARRIER, 'evidence_ids': ['fixture:missing']}, {**CARRIER, 'name': 'Bad\nName'}):
            with self.assertRaises(ValueError): self.r.carriers([row], self.ev)
        with self.assertRaises(ValueError):
            self.r.carriers([CARRIER, {**CARRIER, 'carrier_id': 'fixture:other'}], self.ev)
        with self.assertRaises(ValueError): self.r.locations([{**PORTS[0], 'function': 'airport'}], self.ev)

    def test_route_continuity_order_and_no_inference(self):
        leg2 = {**LEG, 'origin': 'fixture:port_b', 'destination': 'fixture:port_c',
                'departure_at': '2026-10-08T13:30:00Z', 'arrival_at': '2026-10-08T14:30:00Z'}
        out = self.route([{**ROUTE, 'legs': [LEG, leg2]}])['fixture:route']
        self.assertFalse(out['live'])
        self.assertEqual(out['legs'][0]['classifier'], 'estimated')
        for leg in ({**LEG, 'destination': 'fixture:unknown'}, {**LEG, 'destination': LEG['origin']},
                    {**LEG, 'arrival_at': '2026-10-08T11:00:00Z'}, {**LEG, 'classifier': 'guess'},
                    {**LEG, 'arrival_at': '2026-10-10T00:00:00Z'}, {**LEG, 'classifier': 'actual'}):
            with self.assertRaises(ValueError): self.route([{**ROUTE, 'legs': [leg]}])
        for legs in ([], [LEG, LEG], [LEG, {**leg2, 'departure_at': NOW}]):
            with self.assertRaises(ValueError): self.route([{**ROUTE, 'legs': legs}])
        with self.assertRaises(ValueError): self.route([{**ROUTE, 'carrier_id': 'fixture:unknown'}])
        with self.assertRaises(ValueError): self.route([ROUTE, ROUTE])

    def test_route_validity_states(self):
        for asof, expected in (('2026-10-09T00:00:00Z', 'stale'), ('2026-10-07T00:00:00Z', 'not_yet_valid')):
            out = self.routes.catalog([ROUTE], self.carriers, self.ports, self.ev, as_of=asof)
            self.assertEqual(out['fixture:route']['state'], expected)

    def test_timeline_dedup_revision_cancellation_and_order(self):
        new = {**EVENT, 'revision': 2, 'source_recorded_at': '2026-10-08T03:00:00Z', 'cancelled': True}
        out = self.event([new, EVENT, EVENT])
        self.assertEqual(len(out['items']), 1)
        self.assertTrue(out['items'][0]['cancelled'])
        self.assertEqual(out['items'][0]['revision'], 2)
        self.assertEqual(out['deduplicated_input_count'], 1)
        self.assertEqual(out['superseded_revision_count'], 1)
        self.assertFalse(out['live_tracking'])
        self.assertEqual(self.event([])['items'], [])

    def test_revision_conflicts_and_identity(self):
        for changed in ({**EVENT, 'cancelled': True}, {**EVENT, 'subject_id': 'fixture:other'},
                        {**EVENT, 'revision': 2, 'source_recorded_at': '2026-10-08T01:00:00Z'}):
            with self.assertRaises(ValueError): self.event([EVENT, changed])
        r2 = {**EVENT, 'revision': 2, 'source_recorded_at': '2026-10-08T04:00:00Z'}
        r3 = {**EVENT, 'revision': 3, 'source_recorded_at': '2026-10-08T05:00:00Z'}
        r1bad = {**EVENT, 'source_recorded_at': '2026-10-08T04:30:00Z'}
        with self.assertRaises(ValueError): self.event([r3, r2, r1bad])

    def test_revision_cap(self):
        with self.assertRaisesRegex(ValueError, '32 revisions'):
            self.event([{**EVENT, 'revision': n} for n in range(1, 34)])

    def test_timeline_contract_rejects_unsafe_values(self):
        for field, value in (('revision', True), ('revision', 0), ('revision', 1000001), ('cancelled', 1),
                             ('category', 'iot'), ('category', []), ('code', 'loaded'),
                             ('classifier', 'inferred'), ('location_id', 'fixture:missing'),
                             ('source_recorded_at', '2026-10-09T00:00:00Z'),
                             ('event_at', '2026-10-08T03:00:00Z')):
            with self.subTest(field=field), self.assertRaises(ValueError): self.event([{**EVENT, field: value}])
        planned = {**EVENT, 'classifier': 'planned', 'event_at': '2026-10-10T00:00:00Z'}
        self.assertEqual(self.event([planned])['items'][0]['classifier'], 'planned')

    def test_caps_reject_before_processing(self):
        for fn, rows in ((lambda x: self.r.carriers(x, self.ev), [None]*201),
                         (lambda x: self.r.locations(x, self.ev), [None]*2001),
                         (self.route, [None]*1001), (self.event, [None]*5001)):
            with self.assertRaises(ValueError): fn(rows)
        with self.assertRaises(ValueError): self.route([{**ROUTE, 'legs': [None]*21}])
        with self.assertRaises(ValueError): self.r.carriers([{**CARRIER, 'aliases': ['x']*11}], self.ev)

    def test_outputs_do_not_mutate_inputs(self):
        route, event, carrier = deepcopy(ROUTE), deepcopy(EVENT), deepcopy(CARRIER)
        out = self.route([route]); out['fixture:route']['legs'][0]['origin'] = 'fixture:changed'
        self.assertEqual(route, ROUTE)
        out = self.event([event]); out['items'][0]['evidence_ids'].append('fixture:changed')
        self.assertEqual(event, EVENT)
        out = self.r.carriers([carrier], self.ev); out['fixture:carrier']['aliases'].append('changed')
        self.assertEqual(carrier, CARRIER)


if __name__ == '__main__':
    unittest.main()
