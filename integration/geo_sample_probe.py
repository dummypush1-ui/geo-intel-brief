"""Offline injected sample probe. No environment, route or source grant.

Read operations under a write-capable credential, not verified read-only access.
The caller owns credential choice and trusted bounded client-factory review.
"""
from datetime import datetime,timezone
from integration.geonews_digest._safe import parse_dt
import math
LABEL='read operations under a write-capable credential, not verified read-only access'
FIELDS=('created_at','published','score')

def _date(value,*,zoned):
 if type(value) is datetime:
  return not zoned and (value.tzinfo is None or type(value.tzinfo) is timezone)
 if type(value) is not str or not 1<=len(value)<=100:return False
 try:
  parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
  return not zoned or parsed.tzinfo is not None
 except (ValueError,OverflowError):return False

def _compatible(key,value):
 if key=='score':return type(value) in (int,float) and math.isfinite(value) and -10**12<=value<=10**12
 if key=='created_at':return type(value) is str and parse_dt(value) is not None
 return _date(value,zoned=True)

def _result(state,count=0,counts=None,reason=None):
 return {'state':state,'mapping':['geo_intel','articles'],'credential_scope':LABEL,
         'sampled_rows':count,'sample_cap':20,'sample_only':True,
         'no_full_history_proof':True,'probe_issues_no_writes':True,
         'unavailable_reason':reason if state=='unavailable' else None,
         'read_only_privileges_verified':False,
         'compatibility':counts if counts is not None else {}}

def _failure(exc):
 try:
  from pymongo.errors import ExecutionTimeout,NetworkTimeout,ConnectionFailure
 except ImportError:return 'source_unavailable'
 if isinstance(exc,ExecutionTimeout):return 'query_timeout'
 if isinstance(exc,NetworkTimeout):return 'io_timeout'
 if isinstance(exc,ConnectionFailure):return 'connection_unavailable'
 return 'source_unavailable'

def probe_geo_sample(uri,*,client_factory):
 """One explicit trusted injection. Never log/return URI, row values or errors.

No privilege proof, retry, snapshot, index/role query or gate mutation.
Provider BSON allocation precedes validation. Timeouts are per operation,
not an end-to-end deadline or hard wire-memory bound. Caller must not log URI.
 """
 client=None;cursor=None;result=_result('unavailable');control=None
 try:
  if type(uri) is not str or not uri or len(uri)>8192 or not callable(client_factory):raise ValueError()
  client=client_factory(uri,serverSelectionTimeoutMS=5000,connect=False)
  if client is None:raise ValueError()
  cursor=client['geo_intel']['articles'].find({}, {'created_at':1,'published':1,'score':1,'_id':0})
  cursor.sort('created_at',-1);cursor.limit(20);cursor.max_time_ms(2000)
  count=0;counts={k:{'compatible':0,'incompatible':0,'missing':0} for k in FIELDS}
  for row in cursor:
   if count>=20 or type(row) is not dict or len(row)>3 or any(type(k) is not str or k not in FIELDS for k in row):raise ValueError()
   # Validate inert bounded types before consulting any value; no custom hooks.
   for v in row.values():
    if v is None or type(v) in (int,float,bool):continue
    if type(v) is str and len(v)<=100:continue
    if type(v) is datetime and (v.tzinfo is None or type(v.tzinfo) is timezone):continue
    raise ValueError()
   for k in FIELDS:
    bucket='missing' if k not in row else ('compatible' if _compatible(k,row[k]) else 'incompatible')
    counts[k][bucket]+=1
   count+=1
  result=_result('sample' if count else 'empty',count,counts)
 except Exception as exc:
  result=_result('unavailable',reason=_failure(exc))
 except BaseException as exc:
  control=exc
 finally:
  # Try both closes even on interruption. Ordinary cleanup error refuses result.
  for resource in (cursor,client):
   if resource is not None:
    try:resource.close()
    except Exception:result=_result('unavailable',reason='cleanup_unavailable')
    except BaseException as exc:
     if control is None:control=exc
 if control is not None:raise control
 return result
