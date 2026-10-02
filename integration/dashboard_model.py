"""Read-only loaded-sample dashboard signals, not whole-database counts.

No legacy app imports, classification changes, database writes or live reads.
Missing source/stream/event snapshots remain unavailable, never zero.
"""
from collections import Counter
from datetime import datetime,timezone
from math import isfinite
def date_view(value):
 try:
  d=value if isinstance(value,datetime) else datetime.fromisoformat(str(value).replace("Z","+00:00"))
  if d.tzinfo is None:return None
  return d.astimezone(timezone.utc).isoformat()
 except (ValueError,TypeError,OverflowError):return None

def signals(row,project):
 out={}
 if project=='geo':
  for key,allowed in [('risk_level',('CRITICAL','HIGH','MODERATE','LOW')),('credibility',('HIGH','MEDIUM','LOW'))]:
   value=row.get(key)
   out[key]=value if isinstance(value,str) and value in allowed else None
  score=row.get('score')
  try:out['score']=score if type(score) in (int,float) and isfinite(score) else None
  except OverflowError:out['score']=None
 else:
  corroboration=row.get('corroborated_by')
  out['corroboration_count']=len(corroboration) if isinstance(corroboration,list) and all(isinstance(v,str) for v in corroboration) else None
 return out

def loaded_stats(rows,project,now=None):
 if project not in ('geo','brics'):raise ValueError('Exact project required')
 now=now or datetime.now(timezone.utc)
 if now.tzinfo is None:raise ValueError('Zoned clock required')
 selected=[r for r in rows if r['project']==project]
 result={'scope':'loaded_read_view','not_total_database':True,'loaded_count':len(selected),'events_state':'unavailable','source_status_state':'unavailable','streams_state':'unavailable'}
 if project=='geo':
  counts=lambda key:dict(Counter(r.get(key) for r in selected if r.get(key)))
  result.update(risk_levels=counts('risk_level'),credibility_levels=counts('credibility'),missing_risk_count=sum(not r.get('risk_level') for r in selected),missing_credibility_count=sum(not r.get('credibility') for r in selected))
  recent=[]
  for r in selected:
   stamp=date_view(r.get('collected_at'))
   if stamp and 0<=(now-datetime.fromisoformat(stamp)).total_seconds()<=86400:recent.append(r)
  result['critical_24h_loaded']=sum(r.get('risk_level')=='CRITICAL' for r in recent)
  result['critical_missing_time_count']=sum(r.get('risk_level')=='CRITICAL' and not date_view(r.get('collected_at')) for r in selected)
 else:
  # Original critical policy and source cycle status are not supplied here.
  result['critical_state']='unavailable_without_original_policy'
  result['corroboration_counts']=dict(Counter(str(r['corroboration_count']) for r in selected if r.get('corroboration_count') is not None))
  result['missing_corroboration_count']=sum(r.get('corroboration_count') is None for r in selected)
 return result
