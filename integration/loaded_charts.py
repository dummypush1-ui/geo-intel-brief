"""Supplied-view UTC volume chart and explicit original BRICS keyword policy.

No legacy import/default keywords/live settings. Policy keywords must be supplied
and reviewed. Original matching uses lowercase substring, not classification or
corroboration proof. Unlike the old window helper, future times are excluded.
The chart is a loaded-sample chart, never a database-total or completeness claim.
Input must be deduped normalized rows; duplicates are counted as supplied.
Daily buckets cover consecutive UTC calendar days including today's partial day,
not a rolling 168/336-hour window. Recent matches include the exact 24h boundary.
More than 1000 rows raises ValueError rather than truncating. Callers handle it.
Verified is a caller assertion, not independent configuration verification. The
validated keywords tuple must not be reassigned. A policy supplied for Geo is
ignored; this adapter only applies the original keyword policy to BRICS.
"""
from datetime import datetime,timezone,timedelta
from integration.news_view import date_view
from integration.public_news import public_news_row
class BricsKeywordPolicy:
 def __init__(self,keywords,verified=False):
  if verified is not True or not isinstance(keywords,list) or not 1<=len(keywords)<=100 or any(not isinstance(k,str) or not k.strip() or len(k)>200 for k in keywords):raise ValueError('Reviewed bounded original keywords required')
  self.keywords=tuple(k.strip().lower() for k in keywords)
 def matches(self,row):
  title=row.get('title');summary=row.get('summary')
  text=((title if isinstance(title,str) else '')+' '+(summary if isinstance(summary,str) else '')).lower()
  return any(k in text for k in self.keywords)

def loaded_chart(rows,project,now,policy=None):
 stamp=date_view(now)
 if not stamp or not isinstance(rows,list) or len(rows)>1000 or project not in ('geo','brics'):raise ValueError('Bounded supplied rows, project and zoned clock required')
 clock=datetime.fromisoformat(stamp);days=7 if project=='geo' else 14
 dates=[(clock.date()-timedelta(days=i)).isoformat() for i in range(days-1,-1,-1)];counts=dict.fromkeys(dates,0)
 selected=[public_news_row(r) for r in rows if type(r) is dict and r.get('project')==project];missing=0;future=0;recent=[]
 for row in selected:
  collected=date_view(row.get('collected_at'))
  if not collected:missing+=1;continue
  at=datetime.fromisoformat(collected)
  if at>clock:future+=1;continue
  if at.date().isoformat() in counts:counts[at.date().isoformat()]+=1
  if (clock-at).total_seconds()<=86400:recent.append(row)
 result={'project':project,'scope':'loaded_read_view','not_total_database':True,'as_of':stamp,'days':days,'daily_volume':[{'date':d,'count':counts[d]} for d in dates],'missing_time_count':missing,'future_time_count':future}
 if project=='brics':
  if policy is None:result['critical_state']='unavailable_without_original_policy'
  elif type(policy) is not BricsKeywordPolicy:raise ValueError('Exact reviewed keyword policy required')
  else:result.update(critical_state='supplied_keyword_policy',critical_24h_loaded=sum(policy.matches(r) for r in recent),critical_keyword_matches_missing_time=sum(policy.matches(r) and not date_view(r.get('collected_at')) for r in selected))
 return result
