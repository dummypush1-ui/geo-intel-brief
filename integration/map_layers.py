"""Pure WGS84 supplied layers. No routes, clients, geocoding or source proof."""
import math,re,hashlib,json
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlunsplit
from integration.country_alerts import text

def clock(value):
 text(value,40);d=datetime.fromisoformat(value.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError()
 d=d.astimezone(timezone.utc)
 if not 1970<=d.year<=2100:raise ValueError()
 return d

def coordinate(value,low,high):
 if type(value) not in (int,float) or not low<=value<=high or not math.isfinite(value):raise ValueError()
 return value

def url(value,*,identity=False):
 text(value,2048)
 p=urlsplit(value);port=p.port
 if p.scheme not in ('https','http') or not p.hostname or p.username or p.password or '\\' in value or any(c.isspace() for c in value) or port is not None and not 1<=port<=65535:raise ValueError()
 return urlunsplit((p.scheme,p.netloc.lower(),p.path or '/',p.query if identity else '',''))

def bbox(value):
 if type(value) is not dict or set(value)!={'south','north','west','east','antimeridian'} or type(value['antimeridian']) is not bool:raise ValueError()
 out={k:coordinate(value[k],-90 if k in ('south','north') else -180,90 if k in ('south','north') else 180) for k in ('south','north','west','east')}
 if out['south']>out['north'] or value['antimeridian']!=(out['west']>out['east']):raise ValueError()
 return dict(out,antimeridian=value['antimeridian'])

def age(stamp,now,limit):
 if stamp is None:return 'unknown'
 delta=(now-clock(stamp)).total_seconds()
 if delta < -300:return 'future'
 return 'fresh' if delta<=limit else 'stale'

def point(row,kind,box,now):
 common={'id','name','lat','lon','source_url'}
 extra={'ports':{'country','dataset','version','licence','provenance'},'vessels':{'imo','mmsi','reported_at'},'news':{'project','article_key','url','published_at','located_at'}}[kind]
 if type(row) is not dict or len(row)!=len(common|extra) or any(type(k) is not str for k in row) or set(row)!=common|extra:raise ValueError()
 out={k:text(row[k],100 if k!='source_url' else 2048) for k in ('id','name')}
 out['lat']=coordinate(row['lat'],-90,90);out['lon']=coordinate(row['lon'],-180,180);out['source_url']=url(row['source_url'])
 if not box['south']<=out['lat']<=box['north'] or not (box['west']<=out['lon']<=box['east'] if not box['antimeridian'] else out['lon']>=box['west'] or out['lon']<=box['east']):raise ValueError()
 out['kind']=kind;out['coordinates']='supplied WGS84 decimal degrees, lat/lon, not inferred'
 if kind=='ports':
  for k in ('country','dataset','version','licence'):out[k]=text(row[k],100)
  if row['provenance'] not in ('unverified_fixture','reference_metadata_supplied') or type(row['provenance']) is not str:raise ValueError()
  out['provenance']=row['provenance'];out['freshness']='dated_reference_not_live';out['source_verified']=False
 elif kind=='vessels':
  for k,length in [('imo',7),('mmsi',9)]:
   v=text(row[k],length,empty=True)
   if v and not re.fullmatch('[0-9]{'+str(length)+'}',v):raise ValueError()
   out[k]=v
  reported=row['reported_at']
  out['reported_at']=None if reported is None else clock(reported).isoformat();out['freshness']=age(out['reported_at'],now,900);out['identifier_checksum_checked']=False
 else:
  if type(row['project']) is not str or row['project'] not in ('geo','brics'):raise ValueError()
  original=url(row['url'],identity=True);key=text(row['article_key'],64)
  if key!=hashlib.sha256((row['project']+'\n'+original).encode()).hexdigest():raise ValueError()
  out.update(project=row['project'],article_key=key,url=url(row['url']))
  for k in ('published_at','located_at'):out[k]=None if row[k] is None else clock(row[k]).isoformat()
  out['freshness']=age(out['located_at'],now,86400);out['publication_is_not_geolocation_time']=True
 return out

def bounded_input(value,depth=0,budget=None):
 if budget is None:budget=[0]
 budget[0]+=1
 if depth>8 or budget[0]>10000:raise ValueError()
 if value is None or type(value) in (bool,int,float):
  if type(value) is int and not -10**12<=value<=10**12 or type(value) is float and not math.isfinite(value):raise ValueError()
  return value
 if type(value) is str and len(value)<=2048:return value
 if type(value) is list and len(value)<=100:return [bounded_input(v,depth+1,budget) for v in value]
 if type(value) is dict and len(value)<=15 and all(type(k) is str and len(k)<=100 for k in value):return {k:bounded_input(v,depth+1,budget) for k,v in value.items()}
 raise ValueError()

def build_layers(envelope,*,now):
 """Layer-local atomic refusal. Other valid layers retained, failed marked invalid.

100 points each, no truncation. Supplied provenance cannot establish authority.
 """
 unavailable={'status':'invalid','layers':{},'scope':'supplied_memory_only_not_live'}
 try:
  current=clock(now)
  envelope=bounded_input(envelope)
  if len(json.dumps(envelope,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())>1048576:raise ValueError()
  if type(envelope) is not dict or set(envelope)!={'bbox','layers'} or type(envelope['layers']) is not dict or set(envelope['layers'])!={'ports','vessels','news'}:raise ValueError()
  box=bbox(envelope['bbox']);layers={}
 except (ValueError,TypeError,OverflowError):return unavailable
 for kind,layer in envelope['layers'].items():
  try:
   if type(layer) is not dict or set(layer)!={'status','observed_at','points'} or type(layer['status']) is not str or layer['status'] not in ('available','empty','unavailable') or type(layer['points']) is not list or len(layer['points'])>100:raise ValueError()
   status=layer['status'];stamp=layer['observed_at']
   if status=='unavailable':
    if stamp is not None or layer['points']:raise ValueError()
    layers[kind]={'status':'unavailable','observed_at':None,'age':'unknown','points':[]};continue
   observed=clock(stamp).isoformat()
   if (status=='empty')!= (not layer['points']):raise ValueError()
   points={};raw={};vessel_ids={}
   for row in layer['points']:
    p=point(row,kind,box,current);identity=(p['project']+':'+p['article_key']) if kind=='news' else p['id']
    if kind=='news':p['id']=identity
    if kind=='vessels':
     for field in ('imo','mmsi'):
      v=p[field]
      if v:
       previous=vessel_ids.get((field,v))
       if previous is not None and previous!=p['id']:raise ValueError()
       vessel_ids[(field,v)]=p['id']
    compared=dict(row)
    if kind=='news':compared.pop('id')
    if identity in raw and raw[identity]!=compared:raise ValueError()
    raw[identity]=compared;points[identity]=p
   if len(json.dumps(list(points.values()),ensure_ascii=False,separators=(',',':')).encode())>524288:raise ValueError()
   layers[kind]={'status':status,'observed_at':observed,'age':age(observed,current,86400),'points':[points[k] for k in sorted(points)]}
  except (ValueError,TypeError,OverflowError):layers[kind]={'status':'invalid','observed_at':None,'age':'unknown','points':[]}
 result={'status':'supplied','layers':layers,'bbox':box,'now':current.isoformat(),'scope':'supplied_memory_only_not_live'}
 if len(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode())>1048576:return unavailable
 return result
