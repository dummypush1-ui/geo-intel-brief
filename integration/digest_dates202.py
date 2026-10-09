"""Pure bounded date projection for 193. No DB query, fallback or migration."""
from datetime import datetime,timezone
import re,json
from integration.digest_windows193 import select_supplied,FIELDS

# Offset required, no whitespace/week dates/basic dates/implicit local timezone.
STAMP=re.compile(r'\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3}(?:\d{3})?)?(?:Z|[+-]\d{2}:\d{2})\Z')

def normalize_date(value):
 """Return UTC ISO text, preserving microseconds. Refuse naive BSON dates.

PyMongo commonly decodes BSON Date as naive UTC by default. The adapter cannot
infer that provenance; caller must configure/verify aware decoding separately.
No string date can supply a missing publication/collection date implicitly.
"""
 if type(value)is str:
  if len(value)>100 or STAMP.fullmatch(value)is None:raise ValueError('Explicit zoned timestamp required')
  if not value.endswith('Z') and (int(value[-5:-3])>23 or int(value[-2:])>59 or value.endswith('-00:00')):raise ValueError('Known valid timestamp offset required')
  try:value=datetime.fromisoformat(value[:-1]+'+00:00'if value.endswith('Z')else value)
  except (ValueError,OverflowError):raise ValueError('Valid zoned timestamp required')from None
 elif type(value)is not datetime:raise ValueError('Explicit zoned timestamp required')
 # Fixed offset only, so custom tz callbacks and ambiguous local DST are absent.
 if type(value.tzinfo)is not timezone:raise ValueError('Fixed aware timestamp required')
 try:return value.astimezone(timezone.utc).isoformat(timespec='microseconds')
 except (ValueError,OverflowError):raise ValueError('Timestamp range held')from None

def select_normalized(rows,now,*,date_field,channel,displayed_receipts,limit=60):
 """Validate entire bounded projection, then invoke unchanged 193 selection.

Supplied rows must already be the closed digest projection. Never drops fields,
truncates rows/text, guesses missing dates or excludes corrupt old/sent rows.
No completeness, DB snapshot, authenticated receipt or no-repeat proof inferred.
"""
 if type(rows)is not list or len(rows)>1000:raise ValueError('Bounded plain row projection required')
 projected=[];total=0;kinds={'strings':0,'aware_datetimes':0}
 for row in rows:
  if type(row)is not dict or any(type(k)is not str or k not in FIELDS+('_id','emailed')for k in row):raise ValueError('Closed row projection required')
  # Validate non-date scalar bounds before copying untrusted large values.
  for k,v in row.items():
   if k in ('published','created_at','_id','emailed'):continue
   if k in ('score','corroboration'):continue # 193 validates finite numeric shape.
   if type(v)is not str or len(v)>16000:raise ValueError('Bounded row text required')
  out=dict(row)
  for k in ('published','created_at'):
   v=row.get(k);out[k]=normalize_date(v)
   kinds['strings'if type(v)is str else'aware_datetimes']+=1
  total+=len(json.dumps(out,ensure_ascii=False,separators=(',',':'),default=str).encode())+1
  if total>2*1024*1024:raise ValueError('Normalized snapshot byte cap')
  projected.append(out)
 result=select_supplied(projected,now,date_field=date_field,channel=channel,displayed_receipts=displayed_receipts,limit=limit)
 result['date_adapter']={'scope':'supplied_projection_only','format':'UTC_ISO_microseconds','input_kinds':kinds,'naive_dates':'refused','missing_date_fallback':False,'raw_mongo_query':None,'migration':False}
 return result
