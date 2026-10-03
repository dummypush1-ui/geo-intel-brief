"""Offline supplied-candidate processing, not a collector or write path.

Calls preserved pure classification/dedupe functions only, never launchers,
fetchers, stores, alerts or Telegram backups. Explicit active categories and
threshold are caller-supplied configuration, not recovered production settings.
Geo keeps classification-before-dedupe and the original 300-character stored
summary preview. BRICS keeps dedupe/classify/category-filter/BRICS-filter order.
Copies input so preserved mutation-based helpers cannot alter caller fixtures.
No clock, IDs or collection times invented; those belong to a reviewed writer.
This covers the processing seam only, not fetching, persistence or full parity.
"""
from copy import deepcopy

def prepare_candidates(project,candidates,active_categories,threshold):
 if project not in ('geo','brics') or not isinstance(candidates,list) or len(candidates)>1000:raise ValueError('Bounded explicit project candidates required')
 if not isinstance(active_categories,list) or not active_categories or any(not isinstance(c,str) or not c for c in active_categories):raise ValueError('Explicit category configuration required')
 if type(threshold) not in (float,int) or not 0<threshold<=1:raise ValueError('Explicit dedupe threshold required')
 for row in candidates:
  if not isinstance(row,dict) or any(not isinstance(row.get(k),str) for k in ('title','url','source','summary')) or not row['title'].strip() or not row['url']:raise ValueError('Candidate text fields required')
 rows=deepcopy(candidates)
 if project=='geo':
  from intelligence.geo.processing.classifier import classify
  from intelligence.geo.processing.dedupe import dedupe_articles
  for row in rows:row['category'],row['score'],row['risk_level'],row['country']=classify(row['title'],row['summary'])
  deduped=dedupe_articles(rows,threshold=threshold,score_key='score')
  selected=[r for r in deduped if r['category'] in active_categories]
  for row in selected:row['summary']=row['summary'][:300]
 else:
  from integration.brics_processing_offline import dedupe,classify,filter_brics
  deduped=dedupe(rows,threshold=threshold)
  for row in deduped:row['category']=classify(row)
  selected=filter_brics([r for r in deduped if r['category'] in active_categories])
 return {'project':project,'state':'offline_prepared_not_persisted','candidate_count':len(candidates),'deduped_count':len(deduped),'prepared_count':len(selected),'items':selected,'network':False,'writes':False,'delivery':False}
