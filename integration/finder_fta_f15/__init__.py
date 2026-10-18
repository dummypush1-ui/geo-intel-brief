"""Default-OFF rate-source drawer on a verified noncached served copy only."""
import base64,hashlib,json,re
from pathlib import Path
from flask import request
from integration.finder_composition_f9 import Selection
from integration.finder_report_f11 import head_insert
from integration.public_ai_answers import Refused
FLAG='PUBLIC_FINDER_FTA_STAGING_ENABLED'
ROOT=Path(__file__).resolve().parent
SEAMS=('const FTA_UAE = {','const FTA_UAE_UNPARSED = [','const FTA_AU = {',
 'India-UAE CEPA Appendix 2A-A (Tariff Schedule of UAE, in force 1 May 2022',
 'Australia-India ECTA Annex 2A (Tariff Schedule of Australia, in force 29 Dec 2022)')
def enabled(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Refused('Plain environment required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Refused('Exact FTA staging flag required')
 if value=='true'and env.get('PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED')!='true':raise Refused('Selected source required')
 return value=='true'
def prepare(env,selection):
 if not enabled(env):return None
 if type(selection)is not Selection:raise Refused('Exact selected source required')
 selection.verify()
 source=(selection.binding.root/'offline.html').read_text()
 if any(x not in source for x in SEAMS):raise Refused('FTA source attribution seam drift')
 return selection

def transform(html,selection):
 if type(selection)is not Selection:raise Refused('Exact selected source required')
 selection.verify()
 if type(html)is not str or len(html)>40*1024*1024 or html.count('</body>')<1 or 'id="f15-staging-style"'in html:raise Refused('One bounded served-copy transform required')
 if "const fetch = async()=>{throw new Error('Offline snapshot: live network disabled');};"not in html:raise Refused('Network-disabled served copy required')
 meta={'Source revision':selection.binding.source_revision,'Package SHA256':selection.binding.package_sha256,'Offline source SHA256':next(pin for name,size,pin in selection.binding.files if name=='offline.html'),'Proof scope':'Supplied artifact integrity only, not official freshness'}
 script=(ROOT/'finder.js').read_text()
 if script.count('/*F15_META*/')!=1:raise Refused('FTA staging metadata seam drift')
 script=script.replace('/*F15_META*/',json.dumps(meta,separators=(',',':')).replace('<','\\u003c'))
 at=html.rfind('</body>');html=html[:at]+'<script>'+script+'</script>'+html[at:]
 html=head_insert(html,'<style id="f15-staging-style">#f15-staging{overflow-wrap:anywhere;min-width:0;max-width:100%;width:100%;box-sizing:border-box}#f15-staging section{min-width:0;max-width:100%}#f15-staging summary{min-height:44px;cursor:pointer;font-weight:600}#f15-staging dt{font-weight:600;margin-top:12px}#f15-staging dd{margin:4px 0}#f15-staging dl{display:block}#f15-staging select{min-height:44px;max-width:100%}.f15-table{overflow-x:auto;min-width:0;max-width:100%;width:100%}.f15-table table{border-collapse:collapse;width:100%;font-size:13px}.f15-table td,.f15-table th{border:1px solid #ddd;padding:8px;text-align:left;min-width:100px}</style>')
 html,n=re.subn(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',html,count=1)
 if n!=1:raise Refused('Exact served-copy CSP required')
 hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in re.findall(r'<script>(.*?)</script>',html,re.S|re.I))
 return head_insert(html,'<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src '+hashes+'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'; form-action \'none\'; base-uri \'none\'">')
def install(app,selection):
 from integration.finder_composition_f9 import selected
 if selected(app)is not selection:raise Refused('Same app selection required')
 @app.after_request
 def fta_staging(response):
  if request.path=='/workspace/finder/offline.html'and response.status_code==200 and request.method!='HEAD':
   response.direct_passthrough=False;response.set_data(transform(response.get_data(as_text=True),selection))
  return response
 app.extensions['finder_fta_f15']=selection
