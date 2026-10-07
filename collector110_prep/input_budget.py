"""Inactive bounded full-run capture, before deepcopy/hash/preparation.
This is a resource contract, not process isolation or runtime activation.
"""
import math
from datetime import datetime,timezone
from dateutil.tz import tzutc,tzoffset,tzlocal
class InputRefused(ValueError):pass
MAX_NODES=20000
MAX_BYTES=2*1024*1024
MAX_DEPTH=8

def capture(value):
 """Capture only exact supported builtins/dates. Count repeated subtrees too.
 No recursion beyond MAX_DEPTH. Reject cycles and custom objects before copy.
 Bytes are a conservative bounded UTF-8 content budget, not BSON size proof.
 """
 nodes=0;size=0;ancestors=set()
 def charge(n):
  nonlocal size
  size+=n
  if size>MAX_BYTES:raise InputRefused('Aggregate byte budget')
 def visit(v,depth):
  nonlocal nodes
  nodes+=1
  if nodes>MAX_NODES or depth>MAX_DEPTH:raise InputRefused('Node/depth budget')
  t=type(v);charge(16)
  if v is None or t is bool:return v
  if t is int:
   if not -(2**63)<=v<=2**63-1:raise InputRefused('Signed int64 required')
   return v
  if t is float:
   if not math.isfinite(v):raise InputRefused('Finite float required')
   return v
  if t is str:
   if len(v)>10000:raise InputRefused('String budget')
   try:charge(len(v.encode('utf-8')))
   except UnicodeError:raise InputRefused('UTF-8 required')from None
   return v
  if t is datetime:
   if type(v.tzinfo)not in (timezone,tzutc,tzoffset,tzlocal):raise InputRefused('Reviewed timezone required')
   try:
    offset=v.utcoffset()
    if offset is None:raise ValueError()
    fixed=v.replace(tzinfo=timezone(offset))
    if not 1970<=fixed.astimezone(timezone.utc).year<=2100:raise ValueError()
    charge(len(fixed.isoformat()))
   except (ValueError,OverflowError):raise InputRefused('Date boundary')from None
   return fixed
  if t not in (dict,list):raise InputRefused('Exact plain values required')
  ident=id(v)
  if ident in ancestors:raise InputRefused('Cycle refused')
  if len(v)>(100 if t is dict else 1000):raise InputRefused('Container budget')
  ancestors.add(ident)
  try:
   if t is list:return [visit(x,depth+1)for x in list(v)]
   result={}
   for k,x in list(v.items()):
    if type(k)is not str or len(k)>100:raise InputRefused('Exact bounded string keys')
    visit(k,depth+1);result[k]=visit(x,depth+1)
   return result
  finally:ancestors.remove(ident)
 result=visit(value,0)
 return {'captured':result,'nodes':nodes,'content_bytes':size}
