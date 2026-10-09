"""Scratch inactive supplied cycle. No network, clients, writer or schedulers."""
from datetime import datetime,timezone
from pathlib import Path
import json,os,stat
import collector112_prep.parser_runner as parser_installation
import hashlib
from collector115_prep.profile import compile_profile
from collector115_prep.composition import compose_supplied,CompositionRefused
from collector112_prep.parser_runner import ParserRefused
from collector110_prep.input_budget import capture
class CycleRefused(ValueError):pass
class InstallationRefused(CycleRefused):pass
ROOT=Path(__file__).resolve().parents[1]
PINS_PATH=Path(__file__).resolve().parent/"dependency-pins177.json"

def verify_installation():
 try:
  pins=json.loads(PINS_PATH.read_text())
  for path,h in pins.items():
   if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=h:raise InstallationRefused("Dependency source drift")
  path=Path(parser_installation.BWRAP)
  mode=path.stat().st_mode
  if not stat.S_ISREG(mode)or not os.access(path,os.X_OK):raise InstallationRefused("Isolation binary unavailable")
 except (OSError,ValueError,TypeError)as e:
  raise InstallationRefused("Installation verification failed")from None


def compose_cycle(settings,evidence,*,clock):
 verify_installation()
 profile=compile_profile(settings)
 if type(clock)is not datetime or type(clock.tzinfo)is not timezone:raise CycleRefused('Exact fixed clock')
 if type(evidence)is not dict or len(evidence)>64:raise CycleRefused('Supplied mapping shape')
 allowed={f[1]:f for f in profile['feeds']}
 if any(type(k)is not str for k in evidence)or set(evidence)-set(allowed):raise CycleRefused('Unlisted evidence')
 # Validate ALL evidence and aggregate byte size before running any parser.
 total=0
 for url,r in evidence.items():
  if type(r)is not dict or set(r)!={'bytes','input_sha256','wire_bytes'}:raise CycleRefused('Evidence shape')
  blob=r['bytes'];h=r['input_sha256'];wire=r['wire_bytes']
  if type(blob)is not bytes or not 1<=len(blob)<=1048576 or type(h)is not str or h!=hashlib.sha256(blob).hexdigest() or type(wire)is not int or not 1<=wire<=1048576:raise CycleRefused('Evidence bytes/hash/count')
  total+=len(blob)
  if total>4194304:raise CycleRefused('Whole cycle body budget')
 candidates=[];states=[]
 for spec in profile['feeds']:
  url=spec[1]
  if url not in evidence:
   states.append({'source':spec[0],'state':'not_supplied'});continue
  try:one=compose_supplied(settings,{url:evidence[url]},clock=clock)
  except ParserRefused:
   states.append({'source':spec[0],'state':'source_or_parser_refused','selected':0});continue
  # Inherited composition/config/source drift remains a loud whole-run failure;
  # not a catch-all that disguises trusted installation drift as source outage.
  source=next(x for x in one['source_states']if x['source']==spec[0])
  source=dict(source)
  source['state']='parsed_bozo_unverified'if source['bozo']else 'selected'if source['selected']else 'selected_empty'
  states.append(source);candidates.extend(one['candidates'])
  if len(candidates)>1000:raise CycleRefused('Whole cycle candidate budget')
  capture({'candidates':candidates})
 profile=dict(profile);profile['pending_gates']=list(profile['pending_gates'])+['extra_rss_feeds_parity','real_wire_evidence','network_cycle_runtime','parser_runtime_refusal_classification','dependency_preflight_TOCTOU']
 return {'scope':'inactive_failure_tolerant_supplied_cycle','candidates':candidates,
         'source_states':states,'profile':profile,'supplied_count':len(evidence),
         'refused_count':sum(x['state']=='source_or_parser_refused'for x in states),
         'bozo_count':sum(x['state']=='parsed_bozo_unverified'for x in states),
         'all_sources_healthy_verified':False,'production_ready':False,'network':False,'writes':False,'delivery':False}
