"""Explicit profile weekday/IANA clock plan. No timers/jobs or mail clients."""
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from datetime import datetime,timezone
import re
DAYS=('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
class ScheduleRefused(ValueError):pass

def canonical_weekday(value):
 if type(value)is not str or value.strip()!=value or value.lower() not in DAYS:
  raise ScheduleRefused('Explicit canonical weekday required; no Monday fallback')
 return value.lower()

def profile_plan(profile,settings):
 if type(profile)is not str or profile not in ('geo','brics') or type(settings)is not dict:
  raise ScheduleRefused('Exact Geo/BRICS profile and settings required')
 # Never fall back to shared unprefixed env config or other profile values.
 prefix=profile.upper()+'_';fields={prefix+k for k in ('SCHEDULER_TIMEZONE','WEEKLY_REPORT_DAY','DAILY_RUN_TIME')}
 if set(settings)!=fields:raise ScheduleRefused('Closed namespaced scheduler settings required')
 zone=settings[prefix+'SCHEDULER_TIMEZONE'];day=canonical_weekday(settings[prefix+'WEEKLY_REPORT_DAY']);clock=settings[prefix+'DAILY_RUN_TIME']
 if type(zone)is not str or not zone or zone.strip()!=zone:raise ScheduleRefused('Explicit IANA scheduler timezone required')
 try:ZoneInfo(zone)
 except (ZoneInfoNotFoundError,ValueError,TypeError):raise ScheduleRefused('Known installed IANA zone required')from None
 if type(clock)is not str or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',clock):raise ScheduleRefused('Exact 24h HH:MM clock required')
 return {'scope':'scheduler_config_plan_only','profile':profile,'timezone':zone,'weekday':day,'time':clock,
         'timer_installed':False,'collection':False,'delivery':False,'activation_allowed':False,
         'dst_policy':'scheduler_engine_installation_review_required_no_inferred_occurrence'}

def local_clock(plan,instant):
 if type(plan)is not dict or plan.get('scope')!='scheduler_config_plan_only' or type(instant)is not datetime or instant.tzinfo is None or instant.utcoffset() is None:
  raise ScheduleRefused('Prepared plan and aware instant required')
 return instant.astimezone(ZoneInfo(plan['timezone'])).isoformat()
