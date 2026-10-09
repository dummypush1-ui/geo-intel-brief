import unittest
from unittest.mock import patch
from integration import scheduler_policy as policy
from datetime import datetime,timezone
from integration.scheduler_policy import canonical_weekday,profile_plan,local_clock,ScheduleRefused
class Schedule(unittest.TestCase):
 def settings(self,profile='geo',**kw):
  p=profile.upper()+'_';return {p+'SCHEDULER_TIMEZONE':kw.get('zone','Asia/Calcutta'),p+'WEEKLY_REPORT_DAY':kw.get('day','Monday'),p+'DAILY_RUN_TIME':kw.get('time','09:00')}
 def test_case_and_invalid_day_no_fallback(self):
  for day in ['Monday','monday','MONDAY']:self.assertEqual(canonical_weekday(day),'monday')
  for day in ['bad',' monday','Monday ',None,'']:
   with self.assertRaises(ScheduleRefused):canonical_weekday(day)
 def test_explicit_namespaces_no_geo_brics_collision(self):
  self.assertEqual(profile_plan('geo',self.settings())['weekday'],'monday')
  self.assertEqual(profile_plan('brics',self.settings('brics',day='Tuesday'))['weekday'],'tuesday')
  with self.assertRaises(ScheduleRefused):profile_plan('geo',self.settings('brics'))
  for zone in ['','Local','Not/AZone',None]:
   with self.assertRaises(ScheduleRefused):profile_plan('geo',self.settings(zone=zone))
 def test_timezone_clock_and_dst_are_aware_not_new_job(self):
  plan=profile_plan('geo',self.settings());self.assertFalse(plan['timer_installed']);self.assertFalse(plan['activation_allowed'])
  self.assertTrue(local_clock(plan,datetime(2026,10,9,3,tzinfo=timezone.utc)).endswith('+05:30'))
  plan=profile_plan('brics',self.settings('brics',zone='America/New_York'))
  self.assertTrue(local_clock(plan,datetime(2026,1,1,tzinfo=timezone.utc)).endswith('-05:00'))
  self.assertTrue(local_clock(plan,datetime(2026,7,1,tzinfo=timezone.utc)).endswith('-04:00'))
  with self.assertRaises(ScheduleRefused):local_clock(plan,datetime(2026,1,1))


class CivilZone206(unittest.TestCase):
 def setUp(self):
  self.old=policy._ZONE_KEYS
  policy._ZONE_KEYS=None
 def tearDown(self):
  policy._ZONE_KEYS=self.old
 def settings(self,profile,zone):
  p=profile.upper()+'_'
  return {p+'SCHEDULER_TIMEZONE':zone,p+'WEEKLY_REPORT_DAY':'Monday',p+'DAILY_RUN_TIME':'09:00'}
 def test_profile_keys_both_profiles_real_aliases(self):
  positives=['UTC','Asia/Calcutta','Asia/Kolkata','America/New_York','US/Eastern','GMT','Zulu','UCT','Etc/GMT+5','EST5EDT']
  negatives=['localtime','posixrules','Factory','posix/UTC','posix/America/New_York','right/UTC','right/America/New_York','SystemV/EST5','','Local','Not/AZone',None,True,[], ' right/UTC','UTC ']
  for profile in ['geo','brics']:
   for zone in positives:self.assertEqual(profile_plan(profile,self.settings(profile,zone))['timezone'],zone)
   for zone in negatives:
    with self.assertRaises(ScheduleRefused):profile_plan(profile,self.settings(profile,zone))
 def test_direct_local_clock_uses_same_zone_rule(self):
  instant=datetime(2026,1,1,tzinfo=timezone.utc)
  for zone in ['right/UTC','posix/UTC','SystemV/EST5','localtime','Factory','posixrules',None,'UTC ']:
   with self.assertRaises(ScheduleRefused):local_clock({'scope':'scheduler_config_plan_only','timezone':zone},instant)
  self.assertEqual(local_clock({'scope':'scheduler_config_plan_only','timezone':'UTC'},instant),'2026-01-01T00:00:00+00:00')
 def test_cache_order_no_scan_for_denied_even_if_listed(self):
  for denied_first in [True,False]:
   policy._ZONE_KEYS=None
   with patch.object(policy,'available_timezones',return_value={'UTC','right/UTC','localtime','posix/UTC','SystemV/EST5'})as scan:
    actions=['right/UTC','UTC','UTC']if denied_first else ['UTC','right/UTC','UTC']
    for zone in actions:
     if zone=='UTC':self.assertEqual(policy._reviewed_zone_key(zone),'UTC')
     else:
      with self.assertRaises(ScheduleRefused)as caught:policy._reviewed_zone_key(zone)
      self.assertEqual(str(caught.exception),'Known civil timezone key required')
    self.assertEqual(scan.call_count,1)
    self.assertEqual(policy._ZONE_KEYS,frozenset({'UTC'}))
 def test_scan_failure_empty_then_retries(self):
  for failed in [set(),{'localtime','right/UTC'},RuntimeError('CANARY206')]:
   policy._ZONE_KEYS=None
   effects=[failed,{'UTC'}]
   with patch.object(policy,'available_timezones',side_effect=effects)as scan:
    with self.assertRaises(ScheduleRefused)as caught:policy._reviewed_zone_key('UTC')
    self.assertEqual(str(caught.exception),'Known civil timezone key required')
    self.assertIsNone(policy._ZONE_KEYS)
    self.assertEqual(policy._reviewed_zone_key('UTC'),'UTC')
    self.assertEqual(scan.call_count,2)
 def test_unavailable_legitimate_alias_fail_closed(self):
  with patch.object(policy,'available_timezones',return_value={'UTC'}):
   with self.assertRaises(ScheduleRefused):policy._reviewed_zone_key('US/Eastern')
   self.assertEqual(policy._reviewed_zone_key('UTC'),'UTC')
