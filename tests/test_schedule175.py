import unittest
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
