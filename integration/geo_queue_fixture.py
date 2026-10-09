"""Geo original-compatibility supplied queue fixture. No source reads or sends.

fetched_ids is NOT a receipt. Marking policy is explicitly undecided.
"""
from datetime import datetime,timezone
from hashlib import sha256
import json,math,re
from html import unescape
from urllib.parse import unquote
from bson import ObjectId
from integration.report_adapters import geo_report_builder
FIELDS=('title','summary','url','source','category','country','risk_level','score','credibility','corroboration','published','created_at')
MARKING_POLICY='open_fetched_vs_displayed_decision'

def query_plan(*,limit=60):
 if type(limit) is not int or not 1<=limit<=60:raise ValueError('fixture limit')
 return {'query':{'emailed':{'$ne':True}},'projection':{k:1 for k in FIELDS+('_id','emailed')},'sort':[('score',-1),('published',-1),('_id',-1)],'limit':limit,'max_time_ms':2000,'scope':'pure_plan_not_executed','limit_scope':'original_default' if limit==60 else 'fixture_only'}

def build_supplied_queue(rows,now,*,limit=60):
 query_plan(limit=limit)
 if type(rows) is not list or len(rows)>1000:raise ValueError('bounded supplied rows')
 if type(now) is not datetime or type(now.tzinfo) is not timezone:raise ValueError('fixed aware clock')
 now=now.astimezone(timezone.utc);clean=[];seen=set();total=0
 # Validate entire supplied snapshot before filtering, including unsupported sent rows.
 for row in rows:
  if type(row) is not dict or any(type(k) is not str or k not in FIELDS+('_id','emailed') for k in row):raise ValueError('plain closed row')
  if 'emailed' in row and row['emailed'] is not None and type(row['emailed']) is not bool:raise ValueError('emailed scalar schema')
  if type(row.get('_id')) is not ObjectId or row['_id'] in seen:raise ValueError('unique ObjectId')
  seen.add(row['_id']);item={}
  for field in FIELDS:
   value=row.get(field,1 if field=='corroboration' else 'MEDIUM' if field=='credibility' else '')
   if field in ('score','corroboration'):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1000000:raise ValueError('finite numeric schema')
   elif type(value) is not str or len(value)>16000 or any(0xD800<=ord(c)<=0xDFFF for c in value):raise ValueError('bounded text schema')
   item[field]=value
  try:
   stamp=datetime.fromisoformat(item['published'].replace('Z','+00:00'))
   if stamp.tzinfo is None:raise ValueError()
  except (ValueError,OverflowError):raise ValueError('zoned published string') from None
  item['_id']=ObjectId(row['_id'].binary)
  if 'emailed' in row:item['emailed']=row['emailed']
  encoded=json.dumps(item,ensure_ascii=False,separators=(',',':'),default=str).encode()
  total+=len(encoded)+1
  if total>2*1024*1024:raise ValueError('snapshot bytes')
  clean.append(item)
 selected=sorted((r for r in clean if r.get('emailed') is not True),key=lambda r:(r['score'],r['published'],r['_id']),reverse=True)[:limit]
 displayed=[r for r in selected if r['score']>=4]
 result=geo_report_builder(lambda:selected,lambda days:[],now=now)()
 html=result['html']
 # IDs are internal only and must not occur in rendered text/links/attributes.
 identity_probe=unquote(unescape(unescape(html))).casefold()
 if any(str(r['_id']).casefold() in identity_probe for r in clean):raise ValueError('identity in rendered output')
 snapshot_id=sha256(json.dumps({'rows':clean,'limit':limit},ensure_ascii=False,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
 return {'html':html,'critical_count':sum(r['risk_level']=='CRITICAL' for r in selected),'displayed_critical_count':sum(r['risk_level']=='CRITICAL' for r in displayed),'fetched_ids':tuple(r['_id'] for r in selected),'displayed_ids':tuple(r['_id'] for r in displayed),'fetched_count':len(selected),'displayed_count':len(displayed),'marking_policy':MARKING_POLICY,'snapshot_source':'supplied_fixture','events_scope':'omitted_fixture_events_not_verified_zero','html_scope':'renderer_differential_only_not_current_digest','displayed_ids_scope':'displayed_fixture_selection_not_delivery_receipt','unsent_queue_verified':False,'snapshot_id':snapshot_id,'observed_at':now.isoformat(),'limit_scope':'original_default' if limit==60 else 'fixture_only','delivery':False,'writes':False,'tie_order':'ObjectId_DESC_addition_not_original_tie_guarantee'}
