"""Existing seven fixed synthetic parser cases -> supplied enrichment/doc research."""
import hashlib,math,dateutil
from pathlib import Path
from datetime import datetime,timezone
from .feedparser_audit.runner import CASES,FILE_PINS,ParserRefused
from .supplied_fulltext_fixture import Budget,FulltextRefused,PINS as BASE_PINS
from .supplied_feed_fixture import _date,FeedRefused
from .supplied_collector_pipeline import _snapshot,PipelineRefused
ROOT=Path(__file__).resolve().parents[1]
PINS=dict(BASE_PINS)|{'integration/feedparser_audit/runner.py':'6de3e28af80928e0e34812bb699d13b935887b12b5153d85bc507ad8bc1e576e','integration/supplied_feed_fixture.py':'a282f5340e48d93221d73f1db918aff84c98e47cc969ee0500f2b5fae638fc2a','integration/supplied_fulltext_fixture.py':'412cd557d6751c16b7b94ea04549898543e4642caca996d332827ead5bb1c49e','integration/supplied_collector_pipeline.py':'52549f5dcb144df8eb31618c79549665844678c824a56795cdca2582010663c3'}
PINS.update({'integration/feedparser_audit/'+p:h for p,h in FILE_PINS.items()})
class FixedPipelineRefused(ValueError):pass
def prepare_fixed_parser_pipeline(case,outcomes,*,synthetic=False,cutoff,fallback_clock,categories=('TRADE',),threshold=.85,enabled=True,available=True,max_chars=700,max_items=50):
 if synthetic is not True or type(case) is not str or case not in CASES or type(outcomes) is not dict or len(outcomes)>100:raise FixedPipelineRefused('fixed synthetic case required')
 try:outcomes=_snapshot(outcomes);categories=_snapshot(categories)
 except PipelineRefused:raise FixedPipelineRefused('exact raw values') from None
 if type(categories) not in (list,tuple) or not 1<=len(categories)<=20 or any(type(c) is not str or not 1<=len(c)<=100 for c in categories) or type(threshold) not in (int,float) or not math.isfinite(threshold) or not 0<threshold<=1 or type(enabled) is not bool or type(available) is not bool or type(max_chars) is not int or not 1<=max_chars<=9997 or type(max_items) is not int or not 1<=max_items<=100:raise FixedPipelineRefused('exact config')
 for d in (cutoff,fallback_clock):
  if type(d) is not datetime or type(d.tzinfo) is not timezone:raise FixedPipelineRefused('fixed date')
  try:_date(d)
  except FeedRefused:raise FixedPipelineRefused('date boundary') from None
 for u,o in outcomes.items():
  if not 1<=len(u)<=10000 or not u.strip() or type(o) is not dict or set(o)!={'download','extract','text'} or any(type(v) is not str or len(v)>10000 for v in o.values()):raise FixedPipelineRefused('closed outcome')
  if o['download'] not in ('text','empty','error') or o['extract'] not in ('text','empty','error') or o['extract']!='text' and o['text'] or o['download']!='text' and (o['extract']!='empty' or o['text']):raise FixedPipelineRefused('outcome consistency')
 if not (enabled and available) and outcomes:raise FixedPipelineRefused('disabled/unavailable requires no outcomes')
 try:Budget().take({'case':case,'outcomes':outcomes,'categories':list(categories),'cutoff':cutoff,'fallback':fallback_clock,'threshold':threshold,'enabled':enabled,'available':available,'max_chars':max_chars,'max_items':max_items})
 except FulltextRefused:raise FixedPipelineRefused('input budget') from None
 if dateutil.__version__!='2.9.0.post0':raise FixedPipelineRefused('parser version')
 for p,h in PINS.items():
  if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise FixedPipelineRefused('source drift')
 from .feedparser_audit.runner import run_fixed_parser
 from .supplied_fulltext_fixture import prepare_supplied_fulltext
 try:
  parsed=run_fixed_parser(case,cutoff=cutoff,fallback_clock=fallback_clock,max_items=max_items);selected=[]
  for row in parsed['candidates']:
   r=dict(row);d=datetime.fromisoformat(r['published'])
   if type(d.tzinfo) is not timezone:raise FixedPipelineRefused('parsed fixed timezone required')
   _date(d);r['published']=d;selected.append(r)
  enriched=prepare_supplied_fulltext(_snapshot(selected),outcomes,categories=categories,threshold=threshold,enabled=enabled,available=available,max_chars=max_chars)
 except (ParserRefused,FeedRefused,FulltextRefused,ValueError):raise FixedPipelineRefused('fixed supplied stage refused') from None
 result={'scope':'PRIVATE FIXED SYNTHETIC PARSER/SUPPLIED TEXT PIPELINE, NOT LIVE OR FOR DELIVERY','synthetic_assertion_only':True,'case':case,'parser_metadata':{'corpus_hash':parsed['corpus_hash'],'feedparser_version':parsed['feedparser_version'],'backend':parsed['backend'],'bozo':parsed['bozo'],'bozo_label':parsed['bozo_label'],'field_presence':_snapshot(parsed['field_presence'])},'selection_state':'selected' if selected else 'selected_empty','enrichment_state':'disabled' if not enabled else 'unavailable' if not available else 'supplied_outcomes_processed','selected_candidates':_snapshot(selected),'enriched_candidates':_snapshot(enriched['candidates']),'documents':_snapshot(enriched['documents']),'enrichment_trace':_snapshot(enriched['trace']),'selected_count':len(selected),'prepared_count':enriched['prepared_count'],'network':False,'writes':False,'delivery':False,'coverage_verified':False,'telegram_backup':'unwired_not_dropped'}
 try:Budget().take(result)
 except FulltextRefused:raise FixedPipelineRefused('combined output budget') from None
 return result
