"""Preview original Geo report renderers, never send or mark records.

Public sample has no emailed state: digest is a sample, NOT an unsent queue.
IDs are discarded at this boundary. Optional events use the exact reviewed display gate.
"""
from integration.report_adapters import geo_report_builder
from integration.html_safety import sanitize_html
from integration.report_preview_frame import responsive_preview
from integration.renderer_scope import renderer
from integration.geonews_digest import model
from integration.dashboard_snapshots import DashboardSnapshots
from datetime import date,datetime,timedelta,timezone

def legacy_rows(articles):
 return [{'title':a['title'],'summary':a['summary'],'url':a['url'],'source':a['source'],
  'category':a['category'],'country':a['country'],'risk_level':a['risk_level'],
  'score':a['score'],'credibility':a['credibility'],'corroboration':a['corroboration'],
  'published':a['published'],'created_at':a['created_at'],'_id':'preview-only-no-record-id'} for a in articles]

def preview(rows,kind,now,event_snapshots=None):
 if type(now) is not datetime or type(now.tzinfo) is not timezone:raise ValueError('Fixed aware preview clock required')
 now=now.astimezone(timezone.utc)
 articles,stats=model.normalise_all(rows)
 event_rows=[];event_info={'state':'unwired','shown':0}
 if kind=='digest' and event_snapshots is not None:
  if type(event_snapshots) is not DashboardSnapshots:raise ValueError('Exact reviewed event display gate required')
  panel=event_snapshots('geo')['panels']['geo_events']
  event_info={k:panel[k] for k in ('state','observed_at','rejected_count','truncated') if k in panel}
  if panel['state']=='supplied_snapshot':
   today=now.astimezone(timezone.utc).date();end=today+timedelta(days=90)
   event_rows=[r for r in panel['items'] if today<=date.fromisoformat(r['event_date'])<=end]
  event_info['shown']=len(event_rows)
  event_info['out_of_window']=len(panel['items'])-len(event_rows) if panel['state']=='supplied_snapshot' else 0
  event_info['window_count_scope']='display_capped_snapshot_only'
  event_info['truncation_may_hide_in_window']=bool(panel.get('truncated',False))
 if kind=='digest':
  selected=model.unemailed_articles(articles,min_score=4)
  result=geo_report_builder(lambda:legacy_rows(selected),lambda days:event_rows,now=now)()
  html=result['html'];count=len(selected)
 elif kind=='critical':
  selected=model.critical_since(articles,now,6)
  html=sanitize_html(renderer('geo_critical',{},now=now)(legacy_rows(selected)));count=len(selected)
 elif kind=='weekly':
  fn=renderer('geo_weekly',{
   'weekly_top_articles':lambda days,limit:legacy_rows(model.weekly_top_articles(articles,now,days,limit)),
   'category_counts':lambda days:[{'category':c,'cnt':n} for c,n in model.category_counts(articles,now,days)],
   'top_countries':lambda days:[{'country':c,'cnt':n} for c,n in model.top_countries(articles,now,days)]},now=now)
  html=sanitize_html(fn());count=len(model.weekly_top_articles(articles,now))
 else:raise ValueError('Exact preview kind required')
 if kind in ('digest','weekly'):html=responsive_preview(html)
 return {'html':html,'kind':kind,'shown_count':count,'state':'dry_run_sample',
 'delivery':False,'writes':False,'scheduler':False,'scope':'newest_supplied_public_geo_sample',
 'unsent_queue_verified':False,'events':event_info['state'],'event_snapshot':event_info,'normalization':stats}
