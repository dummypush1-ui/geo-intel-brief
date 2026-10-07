"""Inactive supplied outcome composition, original enrichment/post-fetch AST."""
from collector117_prep.supplied_cycle import compose_cycle
from collector115_prep.profile import defaults
from integration.supplied_fulltext_fixture import prepare_supplied_fulltext,FulltextRefused
from integration.geo_collector_contract import prepare_geo_documents
from collector110_prep.input_budget import capture
class EnrichmentRefused(ValueError):pass

def prepare_enriched_cycle(settings,evidence,outcomes,*,clock,available=True,max_chars=None):
 if type(available)is not bool:raise EnrichmentRefused('Exact supplied availability')
 if max_chars is None:max_chars=int(defaults()['FULL_TEXT_MAX_CHARS'])
 if type(max_chars)is not int or not 1<=max_chars<=9997:raise EnrichmentRefused('Bounded fulltext config')
 cycle=compose_cycle(settings,evidence,clock=clock);profile=cycle['profile']
 candidates=cycle['candidates'];enabled=profile['source_flags']['ENABLE_FULL_TEXT']
 if type(outcomes)is not dict or len(outcomes)>1000:raise EnrichmentRefused('Supplied outcomes shape')
 expected={a['url']for a in candidates if enabled and available and len(a['summary'])<200}
 if set(outcomes)!=expected:raise EnrichmentRefused('Missing or unused supplied extraction outcome')
 # Preflight capture of full input before per-chunk original AST runs.
 capture({'candidates':candidates,'outcomes':outcomes})
 enriched=[];trace=[]
 for start in range(0,len(candidates),100):
  chunk=candidates[start:start+100]
  urls={a['url']for a in chunk if enabled and available and len(a['summary'])<200}
  out=prepare_supplied_fulltext(chunk,{u:outcomes[u]for u in urls},enabled=enabled,available=available,
                                max_chars=max_chars,categories=profile['active_categories'],threshold=profile['threshold'])
  enriched.extend(out['candidates']);trace.extend(out['trace'])
  capture({'candidates':enriched,'trace':trace})
 docs=prepare_geo_documents(enriched,profile['active_categories'],profile['threshold'])
 capture({'documents':docs['documents']})
 return {'scope':'inactive_supplied_fulltext_cycle','cycle':cycle,'enriched_candidates':enriched,
         'documents':docs['documents'],'enrichment_trace':trace,'fulltext_state':'disabled_by_config'if not enabled else 'unavailable_supplied'if not available else 'supplied_outcomes_processed',
         'pending_gates':list(profile['pending_gates'])+['live_fulltext_fetch_extract_isolation'],
         'full_article_verified':False,'production_ready':False,'network':False,'writes':False,'delivery':False}
