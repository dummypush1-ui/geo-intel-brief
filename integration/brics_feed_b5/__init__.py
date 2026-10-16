"""Bounded supplied BRICS parsed-feed preparation, never a live collector.

No imported legacy launcher/config, callbacks, network, XML parser, database,
clock, schedule, alert or delivery. Not mounted by any application builder.
"""
import hashlib,json,math,re
from datetime import datetime,timezone
from pathlib import Path
from integration.collection_prepare import prepare_candidates
ROOT=Path(__file__).resolve().parents[2]
FLAG='BRICS_SUPPLIED_FEED_PREP_ENABLED'
PINS={
 'intelligence/brics/collectors/rss.py':'936a244b97187892bc9cd889d2b2d465742cf2c424af777c0ff91fd4bfb822f7',
 'intelligence/brics/collectors/official.py':'fe49cf5f9f503593b44bbaf8cae5edea3bf0a4b3c47887ea23e553064f757f9d',
 'intelligence/brics/processing/classifier.py':'66ca3047bf14d69f13267b80b794b7cda3d2d41b8a301ce0c641e5c7697ce0fd',
 'intelligence/brics/processing/dedupe.py':'7be9129a52699d0fd73474520035094210f7829d0ba156afda2895e97652105b',
 'integration/brics_processing_offline.py':'049546d8e83a0db291b04b7741db09cd5468bd9dd2d2e9dc284b0bb1ffd73345',
 'integration/collection_prepare.py':'2d0886b3126dfd4da4c7fa647ff414afbd27a6032204a8f9ad2be046f86c25b2'}
class Held(ValueError):pass

def text(value,cap):
 if type(value)is not str or len(value)>cap or len(value.encode('utf-8'))>cap*4:raise Held('Bounded exact text required')
 return value

def clean(value):return re.sub(r'<[^>]+>','',value).strip()

def prepare(env,*,sources=None,outcomes=None,tiers=(1,2),categories=None,threshold=None,checked_at=None,include_official=False):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise Held('Exact supplied-feed flag required')
 if flag=='false':return None
 if type(sources)is not list or not 1<=len(sources)<=50 or type(outcomes)is not dict or len(outcomes)>50:raise Held('Bounded supplied sources/outcomes required')
 if type(tiers)is not tuple or not tiers or any(type(t)is not int or t not in (1,2)for t in tiers)or len(set(tiers))!=len(tiers):raise Held('Exact RSS tier selection required')
 if type(include_official)is not bool:raise Held('Exact official disposition required')
 if type(categories)is not list or not 1<=len(categories)<=6 or any(type(c)is not str or c not in ('GEOPOLITICS','TRADE','SANCTIONS','RISK','CONFERENCE','GENERAL')for c in categories)or len(set(categories))!=len(categories):raise Held('Explicit BRICS categories required')
 if type(threshold)not in (int,float)or not math.isfinite(threshold)or not 0<threshold<=1:raise Held('Explicit dedupe threshold required')
 text(checked_at,64)
 try:
  stamp=datetime.fromisoformat(checked_at.replace('Z','+00:00'))
  if stamp.tzinfo is None or stamp.utcoffset()!=timezone.utc.utcoffset(stamp):raise ValueError()
 except ValueError:raise Held('Supplied UTC observation timestamp required')from None
 # Exact plain closed fields only; reject all hostile/custom objects before
 # JSON size accounting or processing. Source index, not name, is identity.
 checked=[];selected=[]
 for i,s in enumerate(sources):
  if type(s)is not dict or any(type(k)is not str for k in s)or set(s)-{'name','country','url','tier','type','enabled'}or not {'name','url','tier','type'}<=set(s):raise Held('Closed source fields required')
  for k in ('name','url'):text(s[k],2048)
  text(s.get('country',''),200)
  if not s['name'].strip()or not s['url'].strip()or type(s['tier'])is not int or s['tier']not in (1,2,3)or type(s['type'])is not str or s['type']not in ('rss','scrape')or type(s.get('enabled',True))is not bool:raise Held('Explicit source shape required')
  if (s['type']=='rss')!=(s['tier']in (1,2)):raise Held('Source type/tier mismatch')
  checked.append(dict(s))
  if s.get('enabled',True)and s['type']=='rss'and s['tier']in tiers:selected.append(i)
 if any(type(k)is not int for k in outcomes)or set(outcomes)!=set(selected):raise Held('Exactly one outcome per selected source index required')
 copied={};input_bytes=0
 for i in selected:
  o=outcomes[i]
  if type(o)is not dict or any(type(k)is not str for k in o)or set(o)!={'state','bozo','entries'}or type(o['state'])is not str or o['state']not in ('feed','error')or type(o['bozo'])is not bool or type(o['entries'])is not list or len(o['entries'])>100:raise Held('Closed supplied parsed-feed outcome required')
  if o['state']=='error'and(o['entries']or o['bozo']):raise Held('Error outcome has no parsed data')
  entries=[]
  for e in o['entries']:
   if type(e)is not dict or any(type(k)is not str for k in e)or set(e)-{'title','link','summary','published','updated'}:raise Held('Closed parsed entry required')
   row={k:text(v,10000)for k,v in e.items()};input_bytes+=sum(len(v.encode('utf-8'))for v in row.values())
   if input_bytes>2*1024*1024:raise Held('Supplied input byte budget exceeded')
   entries.append(row)
  copied[i]={'state':o['state'],'bozo':o['bozo'],'entries':entries}
 if len(json.dumps([checked,copied],ensure_ascii=True).encode())>2*1024*1024:raise Held('Supplied input byte budget exceeded')
 for n,h in PINS.items():
  if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h:raise Held('Reviewed BRICS source drift')
 raw=[];statuses=[]
 for i,s in enumerate(checked):
  base={'source_index':i,'name':s['name'],'checked_at':checked_at,'count':0}
  if not s.get('enabled',True):statuses.append(dict(base,status='disabled',message='disabled in supplied source snapshot'));continue
  if i not in copied:continue
  o=copied[i];entries=o['entries']
  if o['state']=='error'or(o['bozo']and not entries):statuses.append(dict(base,status='error',message='declared supplied source failure'));continue
  statuses.append(dict(base,status='warning'if o['bozo']else'ok',count=len(entries),message='parse warning, used anyway'if o['bozo']else''))
  for e in entries[:30]:
   raw.append({'title':clean(e.get('title','')),'url':e.get('link','').strip(),'source':s['name'],'country':s.get('country',''),'summary':clean(e.get('summary',''))[:500],'published':e.get('published',e.get('updated',''))})
 if len(raw)>1000:raise Held('Prepared candidate count exceeds bounded processing capacity')
 # Preserve original empty-title/URL parsed rows in the extraction evidence,
 # but fail the combined processing rather than silently drop or invent them.
 try:processed=prepare_candidates('brics',raw,categories,threshold)
 except ValueError:raise Held('Supplied candidates refused by processing boundary')from None
 result={'state':'supplied_brics_feed_prepared_only','notice':'Private supplied parsed entries. Not live HTTP/XML/source-health/current-news proof.',
  'tiers':list(tiers),'source_statuses':statuses,'status_count_policy':'parsed entries before 30-entry cap, dedupe, category/relevance filtering and storage',
  'parsed_candidates':raw,'processing':processed,
  'official_disposition':'held_original_homepage_stub_not_article_extraction'if include_official else'not_requested',
  'official_source_indexes':[i for i,s in enumerate(checked)if s['type']=='scrape']if include_official else[],
  'network':False,'xml_parsed':False,'writes':False,'schedules':False,'delivery':False,'critical_alerts':False,'production_mounted':False}
 if len(json.dumps(result,ensure_ascii=True).encode())>2*1024*1024:raise Held('Prepared output byte budget exceeded')
 return result
