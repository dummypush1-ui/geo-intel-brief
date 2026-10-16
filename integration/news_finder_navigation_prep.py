"""Default-OFF E001 only. Preserved snapshot navigation, never legal clearance."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
from integration.cross_link_schema_prep import link

FLAG='PUBLIC_NEWS_FINDER_LINKS_ENABLED'
PATH='/workspace/finder/offline.html'
MARKER='finder_offline_copy_mount'
EDITIONS={'HS':'2022','IN':'snapshot:d6d1b417562b'}
LABELS={'HS':'Open in the preserved Finder snapshot (labeled HS 2022)',
        'IN':'Open in the preserved Finder snapshot (India HSN label)'}
VIEW_SHA='77137ebf1d8debef70bc49bdc0a253c9b4845429135431af9e8e46328217dff7'

@dataclass(frozen=True)
class OfflineMount:
 view:object
 endpoint:str
 path:str
 public_scope:bool

def enabled(env):
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise ValueError('Exact Finder links flag')
 return flag=='true'

def install_mount(app):
 # Called only by public builder after actual transformed view and public allow
 # policy are installed. No caller-provided marker or environment assertion.
 from integration.news_api import offline_finder_snapshot
 from integration.finder_composition_f9 import selected
 selection=selected(app)
 if selection is not None:
  view=app.extensions.get('finder_composition_view_f9')
  if not callable(view)or app.view_functions.get('offline_finder_snapshot')is not view:raise ValueError('Candidate offline view unavailable')
  app.extensions[MARKER]=OfflineMount(view,'offline_finder_snapshot',PATH,True);return
 app.extensions[MARKER]=OfflineMount(offline_finder_snapshot,'offline_finder_snapshot',PATH,True)

def mounted(app):
 from integration.news_api import offline_finder_snapshot
 marker=app.extensions.get(MARKER)
 from integration.finder_composition_f9 import selected
 selection=selected(app)
 if selection is not None:
  view=app.extensions.get('finder_composition_view_f9')
  if type(marker)is not OfflineMount or marker.view is not view or app.view_functions.get(marker.endpoint)is not view or marker.path!=PATH or marker.endpoint!='offline_finder_snapshot'or marker.public_scope is not True:return False
  try:selection.verify()
  except Exception:return False
  return any(r.rule==PATH and r.endpoint==marker.endpoint and {'GET','HEAD'}<=r.methods for r in app.url_map.iter_rules())
 if type(marker)is not OfflineMount or marker.path!=PATH or marker.endpoint!='offline_finder_snapshot' or marker.public_scope is not True or marker.view is not offline_finder_snapshot or app.view_functions.get(marker.endpoint)is not offline_finder_snapshot:return False
 source=Path(__file__).with_name('news_api.py')
 if hashlib.sha256(source.read_bytes()).hexdigest()!=VIEW_SHA:return False
 return any(r.rule==PATH and r.endpoint==marker.endpoint and {'GET','HEAD'}<=r.methods for r in app.url_map.iter_rules())

def target_fields(target,editions=None):
 editions=EDITIONS if editions is None else editions
 if type(target)is not dict:return None
 t={k:target.get(k) for k in ('system','edition','code')}
 if any(type(v)is not str for v in t.values()) or t['system'] not in editions or t['edition']!=editions[t['system']]:return None
 import re
 if not re.fullmatch(r'[0-9]{4}(?:[0-9]{2}){0,4}',t['code']):return None
 return t

def prepare(proof,target):
 """Once per quota-admitted resolved manual start, outside News lock.
 Exceptions including TimeoutError become unavailable, never scan failure.
 No slot has been reserved yet. Quota admit remains one attempt per start.
 """
 from integration.finder_identity_proof_prep import FinderProof
 editions=dict(proof.editions)if type(proof)is FinderProof and proof.profile is not None else None
 t=target_fields(target,editions)
 unavailable={'state':'unavailable','target':t}
 if t is None:return unavailable
 try:
  result=proof.bound(t['system'],t['edition'],t['code'])
  if type(result)is not dict or result.get('state')!='bound_preserved_snapshot' or result.get('edition_verified')is not False or any(result.get(k)!=v for k,v in t.items()):return unavailable
  from integration.finder_identity_proof_prep import normalized_description
  digest=hashlib.sha256(normalized_description(target.get('description')).encode()).hexdigest()
  if result.get('normalized_description_sha256')!=digest:return unavailable
  return {'state':'bound','target':t}
 except Exception:return unavailable

def valid_evidence(evidence,editions=None):
 return type(evidence)is dict and set(evidence)=={'state','target'} and evidence['state']in ('bound','unavailable') and (evidence['target']is None and evidence['state']=='unavailable' or target_fields(evidence['target'],editions)==evidence['target'] and evidence['target']is not None)

def decorate(app,evidence):
 from integration.finder_composition_f9 import selected
 selection=selected(app);editions=dict(selection.editions)if selection else None
 if not valid_evidence(evidence,editions):raise ValueError('Navigation evidence unavailable')
 t=evidence['target']
 out={'state':'unavailable','target':t,'url':None,'label':'Finder link unavailable','edition_verified':False}
 if evidence['state']!='bound' or t is None or not mounted(app):return out
 result=link('code',t,verified_identity=True)
 out.update(state='ready',url=result['url'],label=LABELS[t['system']])
 return out
