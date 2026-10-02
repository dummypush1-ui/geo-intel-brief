"""Fixture-only Geo rolling-seven-day breakdown over supplied normalized rows.

Never reads a store or imports a legacy app. Caller supplies a deduped normalized
view and explicit zoned clock. Duplicates are counted as supplied. The original
category/country query uses created_at >= UTC now minus seven days, not calendar
day buckets. This adapter uses normalized collected_at (Geo created_at mapping),
includes the exact cutoff, excludes future dates rather than copying the old
query's future-date bug, and labels its result as a sample, never store totals.
Missing times and older/future rows are counted separately. Empty country values
are omitted like the original query; missing categories are counted separately.
Top countries uses eight entries like the original default, ties lexical for
repeatable fixtures. More than 1000 rows or malformed normalized input raises
ValueError rather than truncating or guessing. No API/UI/runtime wiring.
"""
from collections import Counter
from datetime import datetime,timedelta
from integration.news_view import date_view

def geo_rolling_breakdown(rows,now):
 stamp=date_view(now)
 if not stamp or not isinstance(rows,list) or len(rows)>1000:raise ValueError('Bounded normalized view and zoned clock required')
 clock=datetime.fromisoformat(stamp)
 try:cutoff=clock-timedelta(days=7)
 except OverflowError:raise ValueError('Clock outside supported window') from None
 if any(not isinstance(r,dict) or r.get('project') not in ('geo','brics') for r in rows):raise ValueError('Normalized project rows required')
 selected=[r for r in rows if r['project']=='geo']
 for row in selected:
  if any(not isinstance(row.get(k),str) for k in ('category','original_country')):raise ValueError('Normalized category and country required')
 categories=Counter();countries=Counter();missing=older=future=in_window=missing_category=missing_country=0
 for row in selected:
  at=date_view(row.get('collected_at'))
  if not at:missing+=1;continue
  at=datetime.fromisoformat(at)
  if at>clock:future+=1;continue
  if at<cutoff:older+=1;continue
  in_window+=1
  if row['category']:categories[row['category']]+=1
  else:missing_category+=1
  if row['original_country']:countries[row['original_country']]+=1
  else:missing_country+=1
 ordered=lambda counts,key:[{key:label,'count':count} for label,count in sorted(counts.items(),key=lambda item:(-item[1],item[0]))]
 country_rows=ordered(countries,'country')
 return {'project':'geo','scope':'loaded_read_view','not_total_database':True,'window':'rolling_7_days_inclusive_cutoff','as_of':stamp,'cutoff':cutoff.isoformat(),'loaded_count':len(selected),'in_window_count':in_window,'missing_time_count':missing,'future_time_count':future,'outside_window_count':older,'categories':ordered(categories,'category'),'top_countries':country_rows[:8],'country_limit':8,'other_country_story_count':sum(row['count'] for row in country_rows[8:]),'missing_category_count':missing_category,'missing_country_count':missing_country}
