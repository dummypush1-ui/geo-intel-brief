"""Separate supplied-input composition. Never a collector or sender."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,math
from bson import ObjectId
ROOT=Path(__file__).resolve().parents[1]
PINS={'integration/geo_collector_contract.py': 'f2bc6c906633e06aba66b21a54901a634279e2d336cfa9d5697d134691292f49', 'integration/geo_queue_fixture.py': '466cae30e3ea627d0814120b4e8fd809da68a0233c8d2c3578ed005b48558289', 'integration/report_adapters.py': 'af267f1950dc9fe0ed25757e1d3f380180239b7c89fa9bc6f0d872b8a1f7072a', 'integration/renderer_scope.py': '468c9e4d02a744130636d3de9db0a3935c5de4b5e049c61748905a39176cd61b', 'integration/html_safety.py': 'a0bc8ddc593dec52ae915e4a6590def75bc25a1ea073ce68e19cbc5ad59dfa37', 'integration/report_styles.py': 'a65de5a98d013d933af811a139fe0850569e9b632ffc941e9275e4faec067321', 'integration/news_view.py': 'd24256b4467b6acc81bbb4d9e0f689c42b52511443fe1fa0feb3725b06416b1f', 'integration/dashboard_model.py': '2a771a65358b9f62bb014d614cf8c0dea07b048edd8c7be93e7d8c467209a4f0', 'integration/fake_collection_writer.py': 'f209fe293d3fab5702476682b9b7d3a659ddaea466dc3e9d88e52a56dbd05c64', 'intelligence/geo/collectors/rss.py': 'a882d01629181b8a14f1d6a2b9a695f3acd7aab83aae7a80165349689f84daef', 'intelligence/geo/processing/classifier.py': '5a87baba3a28b778d0d6b7a3091129e94a618c45ae346a99e13204790f2787ac', 'intelligence/geo/processing/dedupe.py': '8326042d8a2adccafc690f86c47cc9baa67240792ef90060750313c81fb7382e', 'intelligence/geo/reports/email_report.py': '5e4ded3763f61e88eb35df6228b993f75f81131c1ca87ed0a524e1d6d8e94efd', 'intelligence/geo/apps_script/Code.gs': 'a5db615b74bb21c4bcfac59cde71edd97379621914421d3ea2b3ab765c7bc62b', 'intelligence/__init__.py': '8b587ea2a31fd4ee4b95581cf7ca65d7d13a219eab9006a79f1ddda890ba88b8', 'intelligence/geo/__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'intelligence/geo/processing/__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'integration/__init__.py': '5d961509258c047783dbe624ffaa01940143f0e09e8e19cf4e595372fd5c0a88', 'integration/public_news.py': '08a002863831a1e7cf9336e10b2f9d61aa1ce0ecf4b4367027dd34ed1dbd8145'}
CANDIDATE_FIELDS={'title','url','source','summary','published','credibility'}
QUEUE_FIELDS={'_id','emailed','title','summary','url','source','category','country','risk_level','score','credibility','corroboration','published','created_at'}
class FixtureRefused(ValueError):pass

def _pins():
 for path,pin in PINS.items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=pin:raise ValueError()

def _snapshot(candidates,queue,categories,threshold,clock):
 # Exact types checked before any iteration or caller hooks.
 if type(candidates) is not list or type(queue) is not list or len(candidates)>100 or len(queue)>100:raise ValueError()
 if type(categories) is not list or not 1<=len(categories)<=20 or type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1:raise ValueError()
 if type(clock) is not datetime or type(clock.tzinfo) is not timezone:raise ValueError()
 clock=clock.astimezone(timezone.utc)
 if not 1970<=clock.year<=2100:raise ValueError()
 budget=[0,0]
 def scalar(value):
  budget[0]+=1
  if budget[0]>5000:raise ValueError()
  t=type(value)
  if t is str:
   if len(value)>16000:raise ValueError()
   for c in value:
    n=ord(c)
    if 0xD800<=n<=0xDFFF:raise ValueError()
    budget[1]+=1 if n<128 else 2 if n<2048 else 3 if n<65536 else 4
    if budget[1]>1024*1024:raise ValueError()
   return value
  budget[1]+=128
  if budget[1]>1024*1024:raise ValueError()
  if value is None or t is bool:return value
  if t in (int,float) and math.isfinite(value) and -2**53<=value<=2**53:return value
  if t is ObjectId:return ObjectId(value.binary)
  if t is datetime and type(value.tzinfo) is timezone:
   d=value.astimezone(timezone.utc)
   if 1970<=d.year<=2100:return value.replace()
  raise ValueError()
 cats=[scalar(c) for c in categories]
 if any(type(c) is not str or not 1<=len(c)<=100 for c in cats):raise ValueError()
 out=[]
 for rows,fields,kind in ((candidates,CANDIDATE_FIELDS,'candidate'),(queue,QUEUE_FIELDS,'queue')):
  snapshot=[];identities=set()
  for r in rows:
   budget[0]+=1
   if budget[0]>5000 or type(r) is not dict or len(r)>len(fields):raise ValueError()
   if any(type(k) is not str or k not in fields for k in r):raise ValueError()
   d={k:scalar(v) for k,v in r.items()}
   if kind=='candidate':
    if any(type(d.get(k)) is not str or not d[k].strip() for k in ('title','url','source')) or type(d.get('summary')) is not str or type(d.get('published')) is not datetime:raise ValueError()
    if 'credibility' in d and d['credibility'] not in ('HIGH','MEDIUM','LOW'):raise ValueError()
   else:
    if type(d.get('_id')) is not ObjectId or d['_id'] in identities or 'score' not in d:raise ValueError()
    identities.add(d['_id'])
    if 'emailed' in d and d['emailed'] is not None and type(d['emailed']) is not bool:raise ValueError()
    for k,v in d.items():
     if k in ('_id','emailed'):continue
     if k in ('score','corroboration'):
      if type(v) not in (int,float) or not 0<=v<=1000000:raise ValueError()
     elif type(v) is not str:raise ValueError()
    published=d.get('published','')
    date=datetime.fromisoformat(published.replace('Z','+00:00'))
    if date.tzinfo is None or not 1970<=date.astimezone(timezone.utc).year<=2100:raise ValueError()
   snapshot.append(d)
  out.append(snapshot)
 return out[0],out[1],cats,threshold,clock

def prepare_fixture(candidates,queue,categories,threshold,clock):
 failed=False;result=None
 try:
  a,b,c,t,now=_snapshot(candidates,queue,categories,threshold,clock)
  # Source verification before importing any processing or renderer dependency.
  _pins()
  from integration.geo_collector_contract import prepare_geo_documents
  from integration.geo_queue_fixture import build_supplied_queue
  docs=prepare_geo_documents(a,c,t)
  q=build_supplied_queue(b,now)
  notice='<p>Offline renderer differential only. Events omitted, not verified zero. Fetched and displayed fixture counts are separate. Fixed UTC header. No verified unsent queue, delivery or marking receipt.</p>'
  html=q['html']
  marker=html.find('>',html.find('<body')) if '<body' in html else -1
  labeled=html[:marker+1]+notice+html[marker+1:] if marker>=0 else '<div>'+notice+html+'</div>'
  preview={'html':labeled,'scope':'renderer_differential_only_not_current_digest','events_scope':q['events_scope'],'clock_scope':'fixed_UTC_fixture_header','fetched_fixture_count':q['fetched_count'],'displayed_fixture_count':q['displayed_count'],'fetched_fixture_critical_count':q['critical_count'],'displayed_fixture_critical_count':q['displayed_critical_count'],'unsent_queue_verified':False,'marking_policy':q['marking_policy'],'delivery':False,'writes':False,'network':False}
  result={'state':'offline_collector_mail_preparation_only','prepared':docs,'queue_diagnostic':q,'mail_preview':preview,'network':False,'writes':False,'delivery':False,'fulltext':'unwired_not_dropped','telegram_backup':'unwired_not_dropped'}
 except (ValueError,TypeError,OverflowError,RecursionError,OSError):failed=True
 if failed:raise FixtureRefused('Supplied composition refused')
 return result
