"""Offline composition seam only. Never invokes the114 real fetch runner.
Supplied114-style body evidence -> networkless112 parser -> original selection
-> bounded aggregate candidates. Production health/runtime/write remain gates.
"""
import hashlib
from datetime import datetime,timezone,timedelta
from collector112_prep.parser_runner import parse_supplied_bytes
from integration.supplied_feed_fixture import prepare_supplied_feed
from collector110_prep.input_budget import capture
from .profile import compile_profile,ProfileRefused
class CompositionRefused(ValueError):pass

def compose_supplied(settings,body_evidence,*,clock):
 profile=compile_profile(settings)
 if type(clock)is not datetime or type(clock.tzinfo)is not timezone:
  raise CompositionRefused('Fixed aware clock required')
 if type(body_evidence)is not dict or len(body_evidence)>64:
  raise CompositionRefused('Bounded supplied source evidence required')
 allowed={f[1]:f for f in profile['feeds']}
 if set(body_evidence)-set(allowed):raise CompositionRefused('Unlisted feed evidence')
 cutoff=clock-timedelta(hours=profile['lookback_hours'])
 candidates=[];sources=[];total=0
 # Installed feed order, not order dictated by external payload.
 for spec in profile['feeds']:
  url=spec[1]
  if url not in body_evidence:
   sources.append({'source':spec[0],'state':'not_supplied'});continue
  evidence=body_evidence[url]
  if type(evidence)is not dict or set(evidence)!={'bytes','input_sha256','wire_bytes'}:
   raise CompositionRefused('Evidence shape')
  blob=evidence['bytes'];wire=evidence['wire_bytes'];h=evidence['input_sha256']
  if type(blob)is not bytes or not 1<=len(blob)<=1048576 or type(wire)is not int or not 1<=wire<=1048576 or type(h)is not str or h!=hashlib.sha256(blob).hexdigest():
   raise CompositionRefused('Evidence bytes/hash/count')
  total+=len(blob)
  if total>4*1048576:raise CompositionRefused('Run supplied byte budget')
  parsed=parse_supplied_bytes(blob)
  selected=prepare_supplied_feed(spec,parsed['entries'],cutoff=cutoff,fallback_clock=clock,
                                 max_items=profile['max_items'],timeout=profile['timeout'])
  candidates.extend(selected['candidates'])
  if len(candidates)>1000:raise CompositionRefused('Run candidate limit')
  capture({'candidates':candidates})
  sources.append({'source':spec[0],'state':'supplied_parsed','bozo':parsed['bozo'],
                  'entries':parsed['entry_count'],'projected':len(parsed['entries']),
                  'selected':selected['selected_count'],'date_fallbacks':selected['date_fallback_count']})
 return {'scope':'inactive_supplied_full_catalog_composition','candidates':candidates,
         'source_states':sources,'profile':profile,'network':False,'writes':False,
         'delivery':False,'all_sources_healthy_verified':False}

def prepare_checkpoint_input(settings,body_evidence,*,clock):
 """Compose original catalog then bound the exact111 checkpoint input shape.
 No ledger mutation or writer. Optional enabled-adapter gaps stay explicit.
 """
 from collector109_prep.checkpoint import run_inputs
 result=compose_supplied(settings,body_evidence,clock=clock)
 p=result['profile']
 bound=run_inputs(result['candidates'],p['active_categories'],p['threshold'])
 capture(bound)
 return {'composition':result,'checkpoint_input':bound,'live_write_ready':False,
         'pending_gates':list(p['pending_gates'])}
