"""Pure supplied-row plan for ONE digest:24h+7d,per-channelreceipt exclusions.
No database, renderer, receipt store, sender, marker, scheduler or default date.
Supplied exclusions are NOT authenticated delivery evidence.
"""
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from hashlib import sha256
import json,math
from bson import ObjectId
CHANNELS=('email','telegram','whatsapp')
FIELDS=('title','summary','url','source','category','country','risk_level','score','credibility','corroboration','published','created_at')

def _clock(value):
 if type(value)is not datetime or type(value.tzinfo)is not timezone:raise ValueError('fixed aware clock')
 return value.astimezone(timezone.utc)

def _stamp(value):
 if type(value)is not str or not value or len(value)>100:raise ValueError('zoned date required')
 try:
  stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
  if stamp.tzinfo is None:raise ValueError()
  return stamp.astimezone(timezone.utc)
 except (ValueError,OverflowError):raise ValueError('zoned date required')from None

def query_plan(now,*,date_field,channel,limit=60):
 """Normalized-date logical plan, NOT raw Mongo string-date predicates."""
 now=_clock(now)
 if date_field not in ('published','created_at'):raise ValueError('explicit date policy required')
 if channel not in CHANNELS:raise ValueError('explicit channel required')
 if type(limit)is not int or not 1<=limit<=60:raise ValueError('bounded section limit')
 return {'scope':'pure_normalized_date_plan_not_executed','date_field':date_field,'channel':channel,
  'sections':({'name':'last_24h','start_inclusive':(now-timedelta(hours=24)).isoformat(),'end_inclusive':now.isoformat()},
              {'name':'last_7days','start_inclusive':(now-timedelta(days=7)).isoformat(),'end_inclusive':now.isoformat()}),
  'section_overlap':'24h_also_in_7days_no_global_display_count_inferred',
  'selection_order':('score_desc','normalized_published_desc','ObjectId_desc'),
  'display_min_score':4,'section_limit':limit,'cap_policy':'display_eligible_before_each_section_cap',
  'receipt_policy':'exclude_supplied_displayed_ids_for_exact_channel_all_time',
  'raw_mongo_query':None,'schema_policy':'mixed_string_dates_require_verified_normalized_date_adapter_before_live_query',
  'delivery':False,'writes':False,'network':False}

def select_supplied(rows,now,*,date_field,channel,displayed_receipts,limit=60):
 """Validate WHOLE bounded input before selecting, even excluded/bad old rows.

Exact injected per-channel ObjectId tuples model all-time displayed receipts.
They are fixture facts only, no completeness/identity/send proof inferred.
The seven-day section includes24h; unionidsdedup prevents doublemark candidate,
not an implemented marker or a delivered/no-repeat guarantee.
"""
 plan=query_plan(now,date_field=date_field,channel=channel,limit=limit);now=_clock(now)
 if type(displayed_receipts)is not dict or set(displayed_receipts)!=set(CHANNELS):raise ValueError('exact per-channel receipt fixture')
 receipt_copy={}
 for c,ids in displayed_receipts.items():
  if type(ids)is not tuple or len(ids)>10000 or any(type(i)is not ObjectId for i in ids)or len(set(ids))!=len(ids):raise ValueError('bounded unique receipt fixture')
  receipt_copy[c]=tuple(ObjectId(i.binary)for i in ids)
 excluded=set(receipt_copy[channel]);clean=[];seen=set();total=0
 if type(rows)is not list or len(rows)>1000:raise ValueError('bounded supplied rows')
 for row in rows:
  if type(row)is not dict or any(type(k)is not str or k not in FIELDS+('_id','emailed')for k in row):raise ValueError('plain closed row')
  if type(row.get('_id'))is not ObjectId or row['_id']in seen:raise ValueError('unique ObjectId')
  if 'emailed'in row and row['emailed']is not None and type(row['emailed'])is not bool:raise ValueError('scalar emailed schema')
  seen.add(row['_id']);item={}
  for key in FIELDS:
   value=row.get(key,1 if key=='corroboration'else'MEDIUM'if key=='credibility'else'')
   if key in ('score','corroboration'):
    if type(value)not in (int,float)or not math.isfinite(value)or not 0<=value<=1000000:raise ValueError('finite numeric schema')
   elif type(value)is not str or len(value)>16000 or any(0xD800<=ord(c)<=0xDFFF for c in value):raise ValueError('bounded text schema')
   item[key]=value
  published=_stamp(item['published']);chosen=_stamp(item[date_field])
  item['_id']=ObjectId(row['_id'].binary)
  if 'emailed'in row:item['emailed']=row['emailed']
  total+=len(json.dumps(item,ensure_ascii=False,separators=(',',':'),default=str).encode())+1
  if total>2*1024*1024:raise ValueError('snapshot bytes')
  clean.append((item,published,chosen))
 eligible=sorted((x for x in clean if x[0]['_id']not in excluded and x[0]['score']>=4),key=lambda x:(x[0]['score'],x[1],x[0]['_id']),reverse=True)
 sections={}
 for name,delta in (('last_24h',timedelta(hours=24)),('last_7days',timedelta(days=7))):
  pool=[x[0]for x in eligible if now-delta<=x[2]<=now]
  sections[name]={'rows':deepcopy(pool[:limit]),'eligible_count':len(pool),'truncated':len(pool)>limit}
 union=tuple(dict.fromkeys(r['_id']for s in sections.values()for r in s['rows']))
 identity={'rows':[x[0]for x in clean],'receipts':receipt_copy,'plan':plan}
 return {'plan':plan,'sections':sections,'displayed_union_ids':union,'displayed_union_scope':'fixture_selection_NOT_delivery_receipt_or_mark_permission',
  'snapshot_id':sha256(json.dumps(identity,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest(),
  'receipt_source':'supplied_fixture_NOT_verified_delivery_or_complete_all_time_ledger',
  'legacy_emailed_policy':'ignored_for_channel_selection_not_per_channel_receipt',
  'unsent_queue_verified':False,'delivery':False,'writes':False,'network':False}
