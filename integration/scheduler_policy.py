"""Explicit profile weekday/IANA clock plan. No timers/jobs or mail clients."""
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError,available_timezones
from datetime import datetime,timezone
import re
DAYS=('monday','tuesday','wednesday','thursday','friday','saturday','sunday')
class ScheduleRefused(ValueError):pass

_ZONE_KEYS=None
_DENIED_ZONE_KEYS=frozenset(('localtime','posixrules','Factory'))
_DENIED_ZONE_PREFIXES=('posix/','right/','SystemV/')

def _reviewed_zone_key(value):
 global _ZONE_KEYS
 if type(value)is not str or not value or value.strip()!=value:
  raise ScheduleRefused('Known civil timezone key required')
 if value in _DENIED_ZONE_KEYS or value.startswith(_DENIED_ZONE_PREFIXES):
  raise ScheduleRefused('Known civil timezone key required')
 if _ZONE_KEYS is None:
  try:
   listed=available_timezones()
   if type(listed)is not set or not listed or any(type(k)is not str for k in listed):
    raise ValueError('Invalid listing')
   accepted=frozenset(k for k in listed if k not in _DENIED_ZONE_KEYS and not k.startswith(_DENIED_ZONE_PREFIXES))
   if not accepted:raise ValueError('No civil keys')
  except Exception:
   raise ScheduleRefused('Known civil timezone key required')from None
  _ZONE_KEYS=accepted
 if value not in _ZONE_KEYS:raise ScheduleRefused('Known civil timezone key required')
 return value

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
 _reviewed_zone_key(zone)
 try:ZoneInfo(zone)
 except (ZoneInfoNotFoundError,ValueError,TypeError):raise ScheduleRefused('Known installed IANA zone required')from None
 if type(clock)is not str or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',clock):raise ScheduleRefused('Exact 24h HH:MM clock required')
 return {'scope':'scheduler_config_plan_only','profile':profile,'timezone':zone,'weekday':day,'time':clock,
         'timer_installed':False,'collection':False,'delivery':False,'activation_allowed':False,
         'dst_policy':'scheduler_engine_installation_review_required_no_inferred_occurrence'}

def local_clock(plan,instant):
 if type(plan)is not dict or plan.get('scope')!='scheduler_config_plan_only' or type(instant)is not datetime or instant.tzinfo is None or instant.utcoffset() is None:
  raise ScheduleRefused('Prepared plan and aware instant required')
 zone=_reviewed_zone_key(plan.get('timezone'))
 return instant.astimezone(ZoneInfo(zone)).isoformat()
