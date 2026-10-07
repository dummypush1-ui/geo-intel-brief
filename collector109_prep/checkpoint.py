"""Inactive full-run input checkpoint. Fixture only, not durable persistence."""
import copy
import hashlib
import json
import math
from datetime import datetime, timezone
from dateutil.tz import tzutc, tzoffset, tzlocal

class CheckpointRefused(ValueError):
 pass

def _freeze(v):
 """Tagged encoding: no literal container can collide with a scalar/date."""
 t=type(v)
 if t is dict:
  if any(type(k) is not str for k in v):raise CheckpointRefused('String keys required')
  return ['dict',[[k,_freeze(v[k])] for k in sorted(v)]]
 if t is list:return ['list',[_freeze(x) for x in v]]
 if v is None:return ['null']
 if t is bool:return ['bool',v]
 if t is int:return ['int',str(v)]
 if t is float:
  if not math.isfinite(v):raise CheckpointRefused('Finite floats required')
  return ['float',v.hex()]
 if t is str:return ['str',v]
 if t is datetime and type(v.tzinfo) in (timezone,tzutc,tzoffset,tzlocal):
  if v.utcoffset() is None:raise CheckpointRefused('Aware date required')
  return ['datetime',v.isoformat(),v.fold]
 raise CheckpointRefused('Plain checkpoint values required')

def digest(key,fence,inputs):
 return hashlib.sha256(json.dumps(_freeze({'job':key,'fence':fence,'inputs':inputs}),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def run_inputs(candidates,categories,threshold):
 if type(candidates)is not list or len(candidates)>1000 or type(categories)is not list or not 1<=len(categories)<=20 or any(type(c)is not str or not 1<=len(c)<=100 for c in categories) or type(threshold)not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1:
  raise CheckpointRefused('Bounded run inputs required')
 result={'candidates':copy.deepcopy(candidates),'active_categories':copy.deepcopy(categories),'threshold':threshold}
 _freeze(result)
 return result

class FixtureCheckpoints:
 """In-memory fixture. Per-job immutable; exact key/fence integrity checked."""
 def __init__(self):self._rows={}
 def put(self,key,fence,inputs):
  if type(key)is not str or len(key)!=64 or any(c not in '0123456789abcdef' for c in key) or type(fence)is not int or fence<1:raise CheckpointRefused('Exact checkpoint identity required')
  if type(inputs)is not dict or set(inputs)!={'candidates','active_categories','threshold'}:raise CheckpointRefused('Full inputs required')
  inputs=run_inputs(inputs['candidates'],inputs['active_categories'],inputs['threshold'])
  h=digest(key,fence,inputs)
  if key in self._rows:
   if self._rows[key]['hash']!=h:raise CheckpointRefused('Checkpoint immutable per job')
   return h
  self._rows[key]={'hash':h,'inputs':copy.deepcopy(inputs)}
  return h
 def get(self,key,fence):
  if type(key)is not str or type(fence)is not int:raise CheckpointRefused('Exact checkpoint read required')
  row=self._rows.get(key)
  if row is None or row['hash']!=digest(key,fence,row['inputs']):raise CheckpointRefused('Checkpoint unavailable or integrity failed')
  return copy.deepcopy(row['inputs'])
 def __init_subclass__(cls,**k):raise TypeError('Fixture cannot be subclassed')
