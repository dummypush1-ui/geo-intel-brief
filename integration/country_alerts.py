"""Pure bounded memory watch transition. No timers, accounts or delivery."""
import hashlib,json,re,unicodedata
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from datetime import datetime,timezone
RISKS={'CRITICAL','HIGH','MODERATE','LOW'}
CATEGORIES={'GEOPOLITICS','CONFERENCE','TRADE','SANCTIONS','RISK','RESEARCH','GENERAL'}
class Refused(ValueError):pass

def text(value,cap,empty=False):
 if type(value) is not str or len(value)>cap or (not empty and not value) or any(unicodedata.category(c).startswith('C') for c in value):raise Refused('Invalid bounded scalar')
 return value

def safe_url(value):
 text(value,2048)
 try:
  p=urlsplit(value);port=p.port
  if any(c.isspace() for c in value):raise ValueError()
  if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or '\\' in value or port is not None and not 1<=port<=65535:raise ValueError()
  normalized=urlunsplit((p.scheme,p.netloc.lower(),p.path or '/',p.query,''))
 except ValueError:raise Refused('Invalid public URL') from None
 return normalized

def public_url(value):
 p=urlsplit(value)
 return urlunsplit((p.scheme,p.netloc,p.path,'',''))

def stamp_utc(value):
 text(value,40)
 d=datetime.fromisoformat(value)
 if d.tzinfo is None or d.utcoffset()!=__import__('datetime').timedelta(0) or not 1970<=d.year<=2100 or value!=d.astimezone(timezone.utc).isoformat():raise Refused('Canonical UTC clock required')
 return value

def label(value):
 text(value,100)
 if value!=value.strip():raise Refused('Exact trimmed label required')
 return value

def rule_doc(rule,labels):
 if type(labels) is not list or not 1<=len(labels)<=300 or len(set(label(x) for x in labels))!=len(labels):raise Refused('Label catalogue required')
 if type(rule) is not dict or set(rule)!={'owner','id','version','countries','risks','categories'}:raise Refused('Closed rule required')
 owner=text(rule['owner'],100);rid=text(rule['id'],100)
 if type(rule['version']) is not int or not 0<=rule['version']<=10**9:raise Refused('Version required')
 out={}
 for key,cap,allowed in [('countries',20,set(labels)),('risks',4,RISKS),('categories',7,CATEGORIES)]:
  values=rule[key]
  if type(values) is not list or len(values)>cap or any(type(x) is not str or x not in allowed for x in values) or len(set(values))!=len(values):raise Refused('Exact rule labels required')
  out[key]=sorted(values)
 signature=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'owner':owner,'id':rid,'version':rule['version'],**out},signature

def payload(row,*,stored=False):
 keys={'article_key','project','url','title','summary','source','original_country','risk_level','category','published_at'}
 if type(row) is not dict or set(row)!=keys:raise Refused('Exact public alert fields required')
 if row['project'] not in ('geo','brics') or type(row['project']) is not str:raise Refused('Exact project required')
 url=safe_url(row['url']);key=text(row['article_key'],64)
 if not re.fullmatch('[0-9a-f]{64}',key) or not stored and key!=hashlib.sha256((row['project']+'\n'+url).encode()).hexdigest():raise Refused('Identity mismatch')
 out={'article_key':key,'project':row['project'],'url':public_url(url)}
 for name,cap in [('title',200),('summary',600),('source',100),('original_country',100),('risk_level',30),('category',30),('published_at',100)]:out[name]=text(row[name],cap,empty=name!='title')
 return out, row['project']+':'+key

def fresh(rule,signature):return {'owner':rule['owner'],'rule_id':rule['id'],'version':rule['version'],'signature':signature,'initialized':False,'observed_at':None,'seen':[],'inbox':[]}

def transition(state,rule,source,labels,*,operation='observe',alert_id=None):
 """Returns new copy or unchanged state copy with refused/unavailable status.

Closed available envelope with integrity digest proves supplied consistency,
not external ownership/currentness. Observation time is not publication time.
 """
 # Reject non-inert state without invoking hooks; only JSON exact builtins.
 def clone(x,depth=0):
  if depth>12:raise Refused('State depth')
  if x is None or type(x) in (str,bool,int):return x
  if type(x) is list and len(x)<=2000:return [clone(v,depth+1) for v in x]
  if type(x) is dict and len(x)<=30 and all(type(k) is str for k in x):return {k:clone(v,depth+1) for k,v in x.items()}
  raise Refused('Inert state required')
 try:old=clone(state)
 except Refused:return {'status':'refused','state':None,'new_alerts':[],'scope':'memory_only_not_sent'}
 try:
  r,sig=rule_doc(rule,labels)
  if state is None:work=fresh(r,sig)
  else:
   work=clone(old)
   if type(work) is not dict or set(work)!=set(fresh(r,sig)) or work['owner']!=r['owner'] or work['rule_id']!=r['id'] or type(work['initialized']) is not bool or type(work['version']) is not int or not 0<=work['version']<=10**9 or type(work['signature']) is not str or not re.fullmatch('[0-9a-f]{64}',work['signature']) or type(work['seen']) is not list or len(work['seen'])>2000 or any(type(x) is not str or not re.fullmatch('(geo|brics):[0-9a-f]{64}',x) for x in work['seen']) or len(set(work['seen']))!=len(work['seen']) or type(work['inbox']) is not list or len(work['inbox'])>200:raise Refused('Bound state required')
   if work['initialized']:
    stamp_utc(work['observed_at'])
   elif work['observed_at'] is not None or work['seen'] or work['inbox']:raise Refused('Uninitialized state invalid')
   inbox_ids=set();inbox_keys=set()
   for item in work['inbox']:
    if type(item) is not dict or set(item)!={'id','identity','article','observed_at','state','wording'} or item['identity'] not in work['seen'] or item['state'] not in ('pending-review','read','dismissed') or item['wording']!='newly seen in supplied sample, not newly published':raise Refused('Inbox state invalid')
    article,identity=payload(item['article'],stored=True)
    if article!=item['article'] or identity!=item['identity'] or item['id']!=hashlib.sha256((r['owner']+'\n'+r['id']+'\n'+identity).encode()).hexdigest():raise Refused('Inbox identity invalid')
    stamp=stamp_utc(item['observed_at'])
    if stamp>work['observed_at'] or item['id'] in inbox_ids or item['identity'] in inbox_keys:raise Refused('Inbox clock or duplicate invalid')
    inbox_ids.add(item['id']);inbox_keys.add(item['identity'])
   if work['version']>r['version']:raise Refused('Rule rollback refused')
  if operation not in ('observe','rebaseline','read','dismiss'):raise Refused('Operation required')
  if work['signature']!=sig:
   if operation!='rebaseline':raise Refused('Explicit rebaseline required')
   work=fresh(r,sig)
  work['version']=r['version']
  if operation in ('read','dismiss'):
   if type(alert_id) is not str:raise Refused('Exact alert required')
   found=[x for x in work['inbox'] if x['id']==alert_id]
   if len(found)!=1:raise Refused('Exact alert required')
   found[0]['state']='read' if operation=='read' else 'dismissed'
   return {'status':'committed','state':clone(work),'new_alerts':[],'scope':'memory_only_not_sent'}
  source=clone(source)
  if type(source) is not dict or set(source)!={'status','observed_at','rows','sha256'}:raise Refused('Source envelope required')
  if source['status']=='unavailable' and source['rows']==[] and source['observed_at'] is None and source['sha256'] is None:return {'status':'unavailable','state':old,'new_alerts':[],'scope':'memory_only_not_sent'}
  if source['status']!='available' or type(source['rows']) is not list or len(source['rows'])>100:raise Refused('Available bounded source required')
  stamp=text(source['observed_at'],40);d=datetime.fromisoformat(stamp.replace('Z','+00:00'))
  if d.tzinfo is None or not 1970<=d.year<=2100:raise Refused('Aware observation required')
  stamp=stamp_utc(d.astimezone(timezone.utc).isoformat())
  if work['observed_at'] is not None and stamp<work['observed_at']:raise Refused('Observation rollback refused')
  inert_rows=clone(source['rows'])
  encoded=json.dumps(inert_rows,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()
  if len(encoded)>100000 or type(source['sha256']) is not str or source['sha256']!=hashlib.sha256(encoded).hexdigest():raise Refused('Source integrity refused')
  rows={};raw_rows={}
  for row in inert_rows:
   public,identity=payload(row)
   if identity in raw_rows and raw_rows[identity]!=row:raise Refused('Conflicting identity')
   raw_rows[identity]=row;rows[identity]=public
  if operation=='rebaseline':work=fresh(r,sig)
  seen=set(work['seen']);added=[]
  for identity in sorted(rows):
   a=rows[identity]
   if identity not in seen and work['initialized'] and a['original_country'] in r['countries'] and a['risk_level'] in RISKS and a['category'] in CATEGORIES and (not r['risks'] or a['risk_level'] in r['risks']) and (not r['categories'] or a['category'] in r['categories']):
    aid=hashlib.sha256((r['owner']+'\n'+r['id']+'\n'+identity).encode()).hexdigest()
    added.append({'id':aid,'identity':identity,'article':a,'observed_at':stamp,'state':'pending-review','wording':'newly seen in supplied sample, not newly published'})
   seen.add(identity)
  if len(seen)>2000 or len(work['inbox'])+len(added)>200:raise Refused('Capacity refused')
  work['seen']=sorted(seen);work['inbox']+=added;work['initialized']=True;work['observed_at']=stamp
  return {'status':'committed','state':clone(work),'new_alerts':clone(added),'scope':'memory_only_not_sent'}
 except (Refused,ValueError,TypeError,OverflowError,RecursionError):return {'status':'refused','state':old,'new_alerts':[],'scope':'memory_only_not_sent'}
