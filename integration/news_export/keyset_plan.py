"""Pure original-order Mongo keyset query plan, no client or cursor execution.

Collection/schema/snapshot identity are operator-reviewed prerequisites, not
proved by this planner. Geo score/published DESC; BRICS collected_at DESC. _id
DESC is a deterministic tie-break addition where originals had no tie-break.
Only typed homogeneous fields supported; mixed/null/missing source sort fields
require preflight typed-count == total-count before any execution: Mongo $lt
can silently omit incompatible types/missing keys on later pages. Mongo-only.
"""
from dataclasses import dataclass
from datetime import datetime,timezone
import math
import re
from bson import ObjectId
from .original_contract import GEO_FIELDS,BRICS_FIELDS

class KeysetPlanError(ValueError):pass
@dataclass(frozen=True)
class Resume:
 project:str
 values:tuple

ORDER={'geo':(('score',-1),('published',-1),('_id',-1)),
       'brics':(('collected_at',-1),('_id',-1))}

def _identity(value):
 return type(value) is ObjectId

def resume(project,row):
 """Make internal typed continuation from an explicit projected source row.

 ObjectId never leaves the raw pager contract as CSV content. Timestamps are
 Geo zoned ISO strings or BRICS exact naive UTC producer strings,
 not coerced datetime/BSON/null values; this contract
 requires source strings sorted lexicographically, as original Mongo sort.
 """
 if project not in ORDER or type(row) is not dict:raise KeysetPlanError('project/row')
 values=[]
 for field,direction in ORDER[project]:
  value=row.get(field)
  if field=='_id':
   if not _identity(value):raise KeysetPlanError('ObjectId identity schema required')
  elif field=='score':
   if type(value) not in (int,float) or not math.isfinite(value) or not -10**12<=value<=10**12:raise KeysetPlanError('Finite numeric score schema required')
  else:
   if type(value) is not str or not 1<=len(value)<=100:raise KeysetPlanError('Project timestamp string schema required')
   try:
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if project=='brics':
     # Exact datetime.utcnow().isoformat(): naive UTC, optional six digits.
     if d.tzinfo is not None or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{6})?',value,re.ASCII):raise ValueError()
    elif d.tzinfo is None:raise ValueError()
   except (ValueError,OverflowError):raise KeysetPlanError('Project timestamp string schema required') from None
  values.append(value)
 return Resume(project,tuple(values))

def query_plan(project,after=None,limit=500):
 """Closed projection/order/filter plan. No public request parsing or execution.

 Source input cap and original filter-after-cap are enforced by the consumer;
 never push category/country/q/critical into this query, as that changes the
 originals' cap-before-filter behavior. Limit<=1000 page, no skip/offset/index.
 """
 if project not in ORDER or type(limit) is not int or not 1<=limit<=1000:raise KeysetPlanError('project/limit')
 order=ORDER[project];query={}
 if after is not None:
  if type(after) is not Resume or after.project!=project or type(after.values) is not tuple or len(after.values)!=len(order):raise KeysetPlanError('internal continuation required')
  # Revalidate fields; dataclass construction alone does not validate types.
  checked=resume(project,{k:v for (k,d),v in zip(order,after.values)})
  terms=[]
  for i,(field,direction) in enumerate(order):
   term={order[j][0]:checked.values[j] for j in range(i)}
   term[field]={'$lt':checked.values[i]};terms.append(term)
  query={'$or':terms}
 fields=GEO_FIELDS if project=='geo' else BRICS_FIELDS
 projection={k:1 for k in fields}
 projection['_id']=1
 if project=='brics':projection['summary']=1 # original critical predicate input
 return {'query':query,'projection':projection,'sort':list(order),'limit':limit,
         'max_time_ms':2000,'project':project,'scope':'pure_plan_not_executed'}

def page_resume(project,rows,previous=None,*,limit=500):
 """Validate strict descending page keys and return internal continuation.

 Original source-field order retained, with descending ObjectId tie-break.
 This validates returned rows only, not global source schema/coverage.
 """
 query_plan(project,previous,limit)
 if type(rows) is not list or len(rows)>limit:raise KeysetPlanError('bounded page')
 last=previous
 for row in rows:
  current=resume(project,row)
  if last is not None:
   if not current.values<last.values:raise KeysetPlanError('strict source order required')
  last=current
 return last
