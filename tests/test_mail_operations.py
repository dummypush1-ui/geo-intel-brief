# Copyright (c) 2026 Push. All rights reserved.
import unittest
from feature_mail_mount.operations import schedule_plan,recovery_plan


def schedule(**changes):
    r={'digest_times':['10:00','22:00'],'digest_interval_hours':0,'critical_interval_minutes':0,
       'weekly_day':'','weekly_time':'','timezone':'Asia/Calcutta'};r.update(changes);return r


def snapshots(phase='send_returned',state='started'):
    b={'receipt':'a'*64,'hash':'b'*64,'attempt':'n'*24,'phase':phase}
    r={'receipt':'a'*64,'hash':'b'*64,'attempt':'n'*24 if state in ('started','acknowledged') else None,
       'state':state,'scope':'bridge_send_returned_not_delivery' if state=='acknowledged' else 'no_send_proof'}
    return b,r


class Tests(unittest.TestCase):
    def test_explicit_times_off_other_kinds(self):
        p=schedule_plan(schedule());self.assertEqual(len(p['triggers']),2);self.assertFalse(p['installation_allowed']);self.assertFalse(p['delete_other_triggers'])
    def test_interval_weekly_critical(self):
        p=schedule_plan(schedule(digest_times=[],digest_interval_hours=1,critical_interval_minutes=30,weekly_day='MONDAY',weekly_time='09:00'))
        self.assertEqual(len(p['triggers']),3);self.assertEqual(p['triggers'][0]['style'],'hours')
    def test_bad_times_and_conflicts(self):
        for changes in ({'digest_times':['24:00']},{'digest_times':['10:00','10:00']},{'digest_interval_hours':1},
                        {'digest_times':[]},{'digest_times':[],'digest_interval_hours':3},
                        {'weekly_day':'MONDAY'},{'critical_interval_minutes':True},{'timezone':'Unknown/Zone'}):
            with self.assertRaises(ValueError):schedule_plan(schedule(**changes))
    def test_schedule_closed_no_secrets(self):
        with self.assertRaises(ValueError):schedule_plan(schedule(secret='DO_NOT_COPY'))
    def test_ack_only(self):
        p=recovery_plan(*snapshots());self.assertEqual(p['proposal'],'propose_ack_only_no_send');self.assertFalse(p['send_allowed']);self.assertFalse(p['ack_allowed'])
    def test_acked_clear_proposal(self):
        p=recovery_plan(*snapshots('sending','acknowledged'));self.assertEqual(p['proposal'],'propose_clear_pending_after_current_readback');self.assertFalse(p['clear_allowed'])
    def test_unknown_phase_never_resends(self):
        for phase in ('claiming','sending'):
            for state in ('prepared','started'):
                p=recovery_plan(*snapshots(phase,state));self.assertEqual(p['proposal'],'hold_manual_reconciliation');self.assertFalse(p['new_nonce_allowed'])
    def test_unclaimed_existing_nonce_proposal(self):
        p=recovery_plan(*snapshots('pending','prepared'));self.assertEqual(p['proposal'],'propose_resume_existing_nonce_via_normal_claim');self.assertFalse(p['send_allowed'])
    def test_binding_mismatch_holds(self):
        for field,value in (('receipt','0'*64),('hash','0'*64),('attempt','x'*24)):
            b,r=snapshots();r[field]=value;self.assertEqual(recovery_plan(b,r)['proposal'],'hold_manual_reconciliation')
    def test_false_delivery_claim_refused(self):
        b,r=snapshots();r['scope']='delivered'
        with self.assertRaises(ValueError):recovery_plan(b,r)
    def test_closed_recovery_schema(self):
        b,r=snapshots();b['new_nonce']=True
        with self.assertRaises(ValueError):recovery_plan(b,r)
    def test_no_expiry_takeover(self):
        b,r=snapshots('sending','started');p=recovery_plan(b,r)
        self.assertFalse(p['automatic_retry']);self.assertTrue(p['current_evidence_required']);self.assertFalse(p['delivery_verified'])
