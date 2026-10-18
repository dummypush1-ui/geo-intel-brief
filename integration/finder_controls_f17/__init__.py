"""Default-OFF paperwork and control source sheet on a verified noncached served copy only."""
import base64,hashlib,json,re
from pathlib import Path
from flask import request
from integration.finder_composition_f9 import Selection
from integration.finder_report_f11 import head_insert
from integration.public_ai_answers import Refused
FLAG='PUBLIC_FINDER_CONTROL_EVIDENCE_ENABLED'
ROOT=Path(__file__).resolve().parent
SEAMS=('const DOC_BASE_OUT = [','const DOC_BASE_IN = [','const DOC_EXTRA = [','const CERT_RULES = [','const CERT_SRC = ','const SCOMET = {','const ADD_MEASURES = M;','const ADD_SRC = ')
def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Refused('Plain environment required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Refused('Exact control evidence flag required')
 if value=='true'and env.get('PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED')!='true':raise Refused('Selected source required')
 return value=='true'
def prepare(env,selection):
 if not enabled(env):return None
 if type(selection)is not Selection:raise Refused('Exact selected source required')
 selection.verify()
 source=(selection.binding.root/'offline.html').read_text()
 if any(x not in source for x in SEAMS):raise Refused('Control source attribution seam drift')
 return selection

def transform(html,selection):
 if type(selection)is not Selection:raise Refused('Exact selected source required')
 selection.verify()
 if type(html)is not str or len(html)>40*1024*1024 or html.count('</body>')<1 or 'id="f17-controls-style"'in html:raise Refused('One bounded served-copy transform required')
 if "const fetch = async()=>{throw new Error('Offline snapshot: live network disabled');};"not in html:raise Refused('Network-disabled served copy required')
 meta={'Source revision':selection.binding.source_revision,'Package SHA256':selection.binding.package_sha256,'Offline source SHA256':next(pin for name,size,pin in selection.binding.files if name=='offline.html'),'Proof scope':'Supplied artifact integrity only, not official freshness'}
 script=(ROOT/'finder.js').read_text()
 if script.count('/*F17_META*/')!=1:raise Refused('control evidence metadata seam drift')
 script=script.replace('/*F17_META*/',json.dumps(meta,separators=(',',':')).replace('<','\\u003c'))
 at=html.rfind('</body>');html=html[:at]+'<script>'+script+'</script>'+html[at:]
 html=head_insert(html,'<style id="f17-controls-style">#f17-controls{overflow-wrap:anywhere;min-width:0;max-width:100%;width:100%;box-sizing:border-box}#f17-controls summary{min-height:44px;cursor:pointer;font-weight:600}#f17-controls dt{font-weight:600;margin-top:12px}#f17-controls dd{margin:4px 0}#f17-controls dl{display:block}</style>')
 html,n=re.subn(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',html,count=1)
 if n!=1:raise Refused('Exact served-copy CSP required')
 hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in re.findall(r'<script>(.*?)</script>',html,re.S|re.I))
 return head_insert(html,'<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src '+hashes+'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'; form-action \'none\'; base-uri \'none\'">')
def install(app,selection):
 from integration.finder_composition_f9 import selected
 if selected(app)is not selection:raise Refused('Same app selection required')
 @app.after_request
 def control_evidence(response):
  if request.path=='/workspace/finder/offline.html'and response.status_code==200 and request.method!='HEAD':
   response.direct_passthrough=False;response.set_data(transform(response.get_data(as_text=True),selection))
  return response
 app.extensions['finder_controls_f17']=selection
