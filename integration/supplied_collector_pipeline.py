"""Isolated supplied-entry -> supplied-text -> lightweight document research."""
import hashlib,math
from pathlib import Path
from datetime import datetime,timezone
import dateutil
from .supplied_fulltext_fixture import Budget,FulltextRefused,PINS as BASE_PINS
from .supplied_feed_fixture import FeedRefused,_date
ROOT=Path(__file__).resolve().parents[1]
class PipelineRefused(ValueError):pass
PINS=dict(BASE_PINS)|{'integration/supplied_feed_fixture.py': 'ab67713a8a28f27e43d4c70fc2e9d434150ab89788f1db4c9d738ba38c5155ea', 'integration/supplied_fulltext_fixture.py': '1e9f825e002eb9643ea71064859abe9709fa8c874bac5206b6fe34de11c4b8d3'}
def _snapshot(v,depth=0):
 if depth>4:raise PipelineRefused('fixture depth')
 if type(v) in (str,bool,int,float,type(None),datetime):return v
 if type(v) is list:
  if len(v)>300:raise PipelineRefused('fixture list bound')
  return [_snapshot(x,depth+1) for x in v]
 if type(v) is tuple:
  if len(v)>20:raise PipelineRefused('fixture tuple bound')
  return tuple(_snapshot(x,depth+1) for x in v)
 if type(v) is dict:
  if len(v)>100 or any(type(k) is not str for k in v):raise PipelineRefused('fixture dictionary bound')
  return {k:_snapshot(x,depth+1) for k,x in v.items()}
 raise PipelineRefused('fixture exact values')
def prepare_supplied_pipeline(feed,entries,outcomes,*,cutoff,fallback_clock,categories=('TRADE',),threshold=.85,enabled=True,available=True,max_chars=700,max_items=50,timeout=20,http_mode='ok',parser_mode='ok'):
 feed,entries,outcomes,categories=(_snapshot(v) for v in (feed,entries,outcomes,categories))
 if type(feed) not in (tuple,list) or len(feed)!=3 or any(type(v) is not str or not 1<=len(v)<=2000 or not v.strip() for v in feed) or feed[2] not in ('HIGH','MEDIUM','LOW') or type(entries) is not list or len(entries)>100 or type(outcomes) is not dict or len(outcomes)>100:raise PipelineRefused('fixture raw shape')
 if type(categories) not in (list,tuple) or not 1<=len(categories)<=20 or any(type(c) is not str or not 1<=len(c)<=100 for c in categories):raise PipelineRefused('fixture category config')
 if type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1 or type(enabled) is not bool or type(available) is not bool or type(max_chars) is not int or not 1<=max_chars<=9997 or type(max_items) is not int or not 1<=max_items<=100 or type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30:raise PipelineRefused('fixture exact config')
 if type(http_mode) is not str or http_mode not in ('ok','error') or type(parser_mode) is not str or parser_mode not in ('ok','error'):raise PipelineRefused('fixture source mode')
 for d in (cutoff,fallback_clock):
  if type(d) is not datetime or type(d.tzinfo) is not timezone:raise PipelineRefused('fixture exact date')
  try:_date(d)
  except FeedRefused:raise PipelineRefused('fixture date boundary') from None
 for row in entries:
  if type(row) is not dict or len(row)>6 or set(row)-{'title','link','summary','description','published','updated'} or any(type(v) is not str or len(v)>10000 for v in row.values()):raise PipelineRefused('fixture entry shape')
 for u,o in outcomes.items():
  if not 1<=len(u)<=10000 or not u.strip() or type(o) is not dict or set(o)!={'download','extract','text'} or any(type(v) is not str or len(v)>10000 for v in o.values()):raise PipelineRefused('fixture outcome shape')
  if o['download'] not in ('text','empty','error') or o['extract'] not in ('text','empty','error') or o['extract']!='text' and o['text'] or o['download']!='text' and (o['extract']!='empty' or o['text']):raise PipelineRefused('fixture outcome contract')
 if (http_mode=='error' or parser_mode=='error') and outcomes:raise PipelineRefused('source error with supplied outcomes')
 try:
  b=Budget();b.take({'feed':list(feed),'entries':entries,'outcomes':outcomes,'categories':list(categories),'cutoff':cutoff,'fallback':fallback_clock,'enabled':enabled,'available':available,'max_chars':max_chars,'max_items':max_items,'timeout':timeout,'threshold':threshold,'http_mode':http_mode,'parser_mode':parser_mode})
 except FulltextRefused:raise PipelineRefused('fixture raw budget') from None
 if dateutil.__version__!='2.9.0.post0':raise PipelineRefused('reviewed parser version')
 for p,h in PINS.items():
  if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise PipelineRefused('reviewed source drift')
 from .supplied_feed_fixture import prepare_supplied_feed
 from .supplied_fulltext_fixture import prepare_supplied_fulltext
 try:
  selected=prepare_supplied_feed(feed,entries,cutoff=cutoff,fallback_clock=fallback_clock,max_items=max_items,timeout=timeout,http_mode=http_mode,parser_mode=parser_mode)
  if selected['declared_source_mode']=='error':enriched=None
  else:enriched=prepare_supplied_fulltext(selected['candidates'],outcomes,categories=categories,threshold=threshold,enabled=enabled,available=available,max_chars=max_chars)
 except (FeedRefused,FulltextRefused,ValueError):raise PipelineRefused('supplied stage refused') from None
 source_state='declared_error' if enriched is None else ('selected' if selected['candidates'] else 'selected_empty')
 enrichment_state='not_run' if enriched is None else ('disabled' if not enabled else 'unavailable' if not available else 'supplied_outcomes_processed')
 result={'state':'supplied_collector_pipeline_only','notice':'PRIVATE supplied parsed entries/text. No live fetch/XML/health/fullarticle/delivery proof.','source_state':source_state,'enrichment_state':enrichment_state,'selected_candidates':_snapshot(selected['candidates']),'enriched_candidates':_snapshot(enriched['candidates']) if enriched else [],'documents':_snapshot(enriched['documents']) if enriched else [],'source_trace':_snapshot(selected['trace']),'enrichment_trace':_snapshot(enriched['trace']) if enriched else [],'diagnostics':{'coarse_source_errors':list(selected['coarse_errors']),'date_fallback_count':selected['date_fallback_count'],'date_policy':selected['date_policy'],'dateutil_version':selected['dateutil_version']},'input_count':len(entries),'selected_count':selected['selected_count'],'prepared_count':enriched['prepared_count'] if enriched else 0,'network':False,'writes':False,'delivery':False,'telegram_backup':'unwired_not_dropped'}
 try:Budget().take(result)
 except FulltextRefused:raise PipelineRefused('fixture combined output budget') from None
 return result
