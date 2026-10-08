"""Ordered supplied-feed research, global enrichment/docs once. No live collector."""
import math,hashlib
from pathlib import Path
from datetime import datetime,timezone
import dateutil
from .supplied_collector_pipeline import _snapshot,PipelineRefused,PINS as BASE_PINS
from .supplied_fulltext_fixture import Budget,FulltextRefused
from .supplied_feed_fixture import FeedRefused,_date
ROOT=Path(__file__).resolve().parents[1]
PINS=dict(BASE_PINS)|{'integration/supplied_collector_pipeline.py':'6ba618d6f77872fd60a9055891183b8b50647aa924ad62851eda4dc9e10aeb4a'}
class MultiFeedRefused(ValueError):pass
def _validate(batches,outcomes,categories,cutoff,fallback_clock,threshold,enabled,available,max_chars,max_items,timeout):
 if type(batches) is not list or len(batches)>4 or type(outcomes) is not dict or len(outcomes)>100:raise MultiFeedRefused('raw containers')
 # Each batch is snapshotted separately to retain82 helper's depth bound.
 try:batches=[_snapshot(b) for b in batches];outcomes=_snapshot(outcomes);categories=_snapshot(categories)
 except PipelineRefused:raise MultiFeedRefused('raw exact values') from None
 if type(categories) not in (list,tuple) or not 1<=len(categories)<=20 or any(type(c) is not str or not 1<=len(c)<=100 for c in categories):raise MultiFeedRefused('category config')
 if type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1 or type(enabled) is not bool or type(available) is not bool or type(max_chars) is not int or not 1<=max_chars<=9997 or type(max_items) is not int or not 1<=max_items<=100 or type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30:raise MultiFeedRefused('exact config')
 for d in (cutoff,fallback_clock):
  if type(d) is not datetime or type(d.tzinfo) is not timezone:raise MultiFeedRefused('exact date')
  try:_date(d)
  except FeedRefused:raise MultiFeedRefused('date boundary') from None
 total=0
 for b in batches:
  if type(b) is not dict or set(b)!={'feed','entries','http_mode','parser_mode'}:raise MultiFeedRefused('closed batch')
  f=b['feed'];entries=b['entries']
  if type(f) not in (tuple,list) or len(f)!=3 or any(type(v) is not str or not 1<=len(v)<=2000 or not v.strip() for v in f) or f[2] not in ('HIGH','MEDIUM','LOW') or type(entries) is not list or len(entries)>100:raise MultiFeedRefused('feed shape')
  for mode in (b['http_mode'],b['parser_mode']):
   if type(mode) is not str or mode not in ('ok','error'):raise MultiFeedRefused('source mode')
  total+=len(entries)
  if total>100:raise MultiFeedRefused('total entry cap')
  for r in entries:
   if type(r) is not dict or len(r)>6 or set(r)-{'title','link','summary','description','published','updated'} or any(type(v) is not str or len(v)>10000 for v in r.values()):raise MultiFeedRefused('entry shape')
 for u,o in outcomes.items():
  if not 1<=len(u)<=10000 or not u.strip() or type(o) is not dict or set(o)!={'download','extract','text'} or any(type(v) is not str or len(v)>10000 for v in o.values()):raise MultiFeedRefused('outcome shape')
  if o['download'] not in ('text','empty','error') or o['extract'] not in ('text','empty','error') or o['extract']!='text' and o['text'] or o['download']!='text' and (o['extract']!='empty' or o['text']):raise MultiFeedRefused('outcome consistency')
 budget_batches=[dict(b,feed=list(b['feed'])) for b in batches]
 try:Budget().take({'batches':budget_batches,'outcomes':outcomes,'categories':list(categories),'cutoff':cutoff,'fallback':fallback_clock,'threshold':threshold,'enabled':enabled,'available':available,'max_chars':max_chars,'max_items':max_items,'timeout':timeout})
 except FulltextRefused:raise MultiFeedRefused('raw aggregate budget') from None
 return batches,outcomes,categories,total
def prepare_supplied_multi_feed(batches,outcomes,*,cutoff,fallback_clock,categories=('TRADE',),threshold=.85,enabled=True,available=True,max_chars=700,max_items=50,timeout=20):
 batches,outcomes,categories,total=_validate(batches,outcomes,categories,cutoff,fallback_clock,threshold,enabled,available,max_chars,max_items,timeout)
 if dateutil.__version__!='2.9.0.post0':raise MultiFeedRefused('parser version drift')
 for p,h in PINS.items():
  if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise MultiFeedRefused('source drift')
 from .supplied_feed_fixture import prepare_supplied_feed
 from .supplied_fulltext_fixture import prepare_supplied_fulltext
 selected=[];diagnostics=[];source_trace=[];errors=0
 try:
  for i,b in enumerate(batches):
   r=prepare_supplied_feed(b['feed'],b['entries'],cutoff=cutoff,fallback_clock=fallback_clock,max_items=max_items,timeout=timeout,http_mode=b['http_mode'],parser_mode=b['parser_mode'])
   failed=r['declared_source_mode']=='error';errors+=int(failed)
   selected.extend(r['candidates']);source_trace.extend(dict(t,feed_ordinal=i) for t in r['trace'])
   diagnostics.append({'ordinal':i,'state':'declared_error' if failed else 'selected' if r['selected_count'] else 'selected_empty','input_count':len(b['entries']),'selected_count':r['selected_count'],'coarse_errors':list(r['coarse_errors']),'date_fallback_count':r['date_fallback_count']})
  enriched=prepare_supplied_fulltext(selected,outcomes,enabled=enabled,available=available,max_chars=max_chars,categories=categories,threshold=threshold)
 except (FeedRefused,FulltextRefused,ValueError):raise MultiFeedRefused('supplied stage refused') from None
 state='all_failed' if batches and errors==len(batches) else 'partially_failed' if errors else 'selected' if selected else 'all_empty'
 result={'state':state,'supplied_scope':'PRIVATE supplied observations, not complete/live/verified collector','coverage_verified':False,'enrichment_state':'disabled' if not enabled else 'unavailable' if not available else 'supplied_outcomes_processed','selected_candidates':_snapshot(selected),'enriched_candidates':_snapshot(enriched['candidates']),'documents':_snapshot(enriched['documents']),'feed_diagnostics':diagnostics,'source_trace':source_trace,'enrichment_trace':_snapshot(enriched['trace']),'input_count':total,'selected_count':len(selected),'prepared_count':enriched['prepared_count'],'date_policy':'partial dates fixed UTC default; missing/unknown fallback unverified','network':False,'writes':False,'delivery':False,'telegram_backup':'unwired_not_dropped'}
 try:Budget().take(result)
 except FulltextRefused:raise MultiFeedRefused('combined output budget') from None
 return result
