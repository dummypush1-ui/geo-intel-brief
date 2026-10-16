"""Per-app candidate selection; no deployment, global repin or source mutation.
Only an exact F8 binding is accepted through an internal builder parameter.
"""
import hashlib,re,json
from dataclasses import dataclass
from pathlib import Path
from flask import Response,request
from integration.finder_binding_f8 import Binding
from integration.finder_offline import _candidate_safety_shell
ROOT=Path(__file__).resolve().parents[2];FLAG='PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED';KEY='finder_composition_f9'
class Held(ValueError):pass
@dataclass(frozen=True)
class Selection:
 binding:Binding
 rendered:str
 editions:tuple
 def verify(self):self.binding.verify()

def prepare(env,binding=None):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise Held('Exact Finder composition flag required')
 if flag=='false':
  if binding is not None:raise Held('Candidate binding supplied while composition off')
  return None
 if type(binding)is not Binding or env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise Held('Exact internal candidate binding and public composition required')
 pins=json.loads((ROOT/'integration/finder_composition_f9/pins.json').read_text())
 expected={'integration/'+name for name in ('news_api.py','finder_offline.py','finder_network.py','finder_nested.py','finder_binding_f8/__init__.py','finder_identity_proof_prep.py','news_finder_navigation_prep.py','public_ai_finder_bridge.py','code_news_disk.py','code_news_coverage_binding_prep.py','code_news_coverage_route_prep.py','code_news_public.py','relationship_navigation.py','code_news_coverage_ui_prep.py','public_ai_answers.py','public_live_builder.py','public_preview_builder.py')}
 if type(pins)is not dict or set(pins)!=expected or any(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h for n,h in pins.items()):raise Held('Candidate composition consumer drift')
 binding.verify()
 raw=(binding.root/'offline.html').read_text();rendered=_candidate_safety_shell(raw)
 expected=next(pin for n,size,pin in binding.files if n=='review/public-offline.html')
 if hashlib.sha256(rendered.encode()).hexdigest()!=expected:raise Held('Candidate safe-render derivation drift')
 return Selection(binding,rendered,binding.profile.editions)

def selected(app):
 value=app.extensions.get(KEY)
 return value if type(value)is Selection else None

def edition_asset(text,selection):
 # One exact edition object, not a global source hash or data-row replacement.
 seam="const editions={HS:'2022',IN:'snapshot:d6d1b417562b'}"
 if text.count(seam)!=1:raise Held('Candidate edition asset seam drift')
 edition=dict(selection.editions)['IN']
 return text.replace(seam,"const editions={HS:'2022',IN:'"+edition+"'}",1)

def install(app,selection):
 if type(selection)is not Selection or KEY in app.extensions:raise Held('One exact Finder selection per app required')
 selection.verify()
 old=app.view_functions.get('offline_finder_snapshot')
 from integration.news_api import offline_finder_snapshot
 if old is not offline_finder_snapshot:raise Held('Original offline view required before selection')
 def candidate():
  if request.method=='HEAD':return Response(status=200,mimetype='text/html')
  try:selection.verify()
  except Exception:return Response('Finder candidate unavailable. Last-good source unchanged.',503,mimetype='text/plain')
  return Response(selection.rendered,mimetype='text/html')
 app.view_functions['offline_finder_snapshot']=candidate
 app.extensions[KEY]=selection;app.extensions['finder_composition_view_f9']=candidate
 closed=[False]
 def close():
  if closed[0]:return
  closed[0]=True
  coverage=app.extensions.get('coverage_close')
  try:
   if callable(coverage):coverage()
  finally:
   service=app.extensions.get('code_news_public')
   if service is not None and service.model is not None:service.model.close()
 app.extensions['finder_composition_close_f9']=close
 import atexit
 atexit.register(close)
