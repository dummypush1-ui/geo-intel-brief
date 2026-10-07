"""Inactive direct composition; not app-imported or mounted. Mock-fetch tests.
No transport/parser/writer injection in production API, only installed settings.
"""
from datetime import datetime,timezone,timedelta
import hashlib
from collector114_prep.runner import run_fetch,FetchRefused
from collector112_prep.parser_runner import parse_supplied_bytes,ParserRefused
from collector115_prep.profile import compile_profile
from integration.supplied_feed_fixture import prepare_supplied_feed
from collector110_prep.input_budget import capture
class SelectionRefused(ValueError):pass

def select_installed_source(settings,url,*,clock):
 profile=compile_profile(settings)
 if type(clock)is not datetime or type(clock.tzinfo)is not timezone:raise SelectionRefused('Fixed installation clock required')
 if type(url)is not str:raise SelectionRefused('Exact installed URL')
 spec=next((f for f in profile['feeds']if f[1]==url),None)
 if spec is None:raise SelectionRefused('Source not installed')
 pending=list(profile['pending_gates'])+['combined_request_deadline','network_header_encoding_parity']
 def refusal(state):
  return {'scope':'inactive_network_selection_candidate','source':spec[0],'state':state,'candidates':[], 'pending_gates':pending,'live_write_ready':False,'writes':False,'delivery':False}
 try: fetched=run_fetch(profile['feeds'],url,timeout=profile['timeout'])
 except FetchRefused:return refusal('fetch_refused')
 expected={'bytes','input_sha256','wire_bytes','url','peer','tls_hostname_verified','delivery'}
 if type(fetched)is not dict or set(fetched)!=expected or fetched['url']!=url or fetched['tls_hostname_verified']is not True or fetched['delivery']is not False:
  raise SelectionRefused('Fixed fetch protocol')
 blob=fetched['bytes']
 if type(blob)is not bytes or not 1<=len(blob)<=1048576 or fetched['input_sha256']!=hashlib.sha256(blob).hexdigest() or type(fetched['wire_bytes'])is not int or not 1<=fetched['wire_bytes']<=1048576:
  raise SelectionRefused('Fetch bytes/hash/count')
 try:parsed=parse_supplied_bytes(blob)
 except (ParserRefused,OSError):return refusal('parse_refused')
 cutoff=clock-timedelta(hours=profile['lookback_hours'])
 selected=prepare_supplied_feed(spec,parsed['entries'],cutoff=cutoff,fallback_clock=clock,max_items=profile['max_items'],timeout=profile['timeout'])
 candidates=capture({'candidates':selected['candidates']})['captured']['candidates']
 return {'scope':'inactive_network_selection_candidate','source':spec[0],
         'state':'parsed_bozo_unverified'if parsed['bozo']else 'selected'if candidates else 'selected_empty',
         'candidates':candidates,'entry_count':parsed['entry_count'],'projected_count':len(parsed['entries']),
         'date_fallbacks':selected['date_fallback_count'],'pending_gates':pending,
         'source_healthy_verified':False,'live_write_ready':False,'writes':False,'delivery':False}
