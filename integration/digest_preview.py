"""Preview original Geo report renderers, never send or mark records.

Public sample has no emailed state: digest is a sample, NOT an unsent queue.
IDs are discarded at this boundary. Events snapshot is not wired.
"""
from integration.report_adapters import geo_report_builder
from integration.html_safety import sanitize_html
from integration.renderer_scope import renderer
from integration.geonews_digest import model

def legacy_rows(articles):
 return [{'title':a['title'],'summary':a['summary'],'url':a['url'],'source':a['source'],
  'category':a['category'],'country':a['country'],'risk_level':a['risk_level'],
  'score':a['score'],'credibility':a['credibility'],'corroboration':a['corroboration'],
  'published':a['published'],'created_at':a['created_at'],'_id':'preview-only-no-record-id'} for a in articles]

def preview(rows,kind,now):
 articles,stats=model.normalise_all(rows)
 if kind=='digest':
  selected=model.unemailed_articles(articles,min_score=4)
  result=geo_report_builder(lambda:legacy_rows(selected),lambda days:[])()
  html=result['html'];count=len(selected)
 elif kind=='critical':
  selected=model.critical_since(articles,now,6)
  html=sanitize_html(renderer('geo_critical',{})(legacy_rows(selected)));count=len(selected)
 elif kind=='weekly':
  fn=renderer('geo_weekly',{
   'weekly_top_articles':lambda days,limit:legacy_rows(model.weekly_top_articles(articles,now,days,limit)),
   'category_counts':lambda days:[{'category':c,'cnt':n} for c,n in model.category_counts(articles,now,days)],
   'top_countries':lambda days:[{'country':c,'cnt':n} for c,n in model.top_countries(articles,now,days)]})
  html=sanitize_html(fn());count=len(model.weekly_top_articles(articles,now))
 else:raise ValueError('Exact preview kind required')
 return {'html':html,'kind':kind,'shown_count':count,'state':'dry_run_sample',
 'delivery':False,'writes':False,'scheduler':False,'scope':'newest_supplied_public_geo_sample',
 'unsent_queue_verified':False,'events':'unwired','normalization':stats}
