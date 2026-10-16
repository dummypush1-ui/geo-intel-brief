"""Only served-copy picks seam. Preserved original and offline fetch stay inert."""
from pathlib import Path
import hashlib,re,base64
ROOT=Path(__file__).resolve().parents[1]
PIN='0e2e85ea54f276c3c50984e8c26b9400e1deee9f4b8a035a8866e56c2455b65b'
START='async function assistRun(cands) {'
END='\nfunction paintResults() {'
REPLACEMENT='''async function assistRun(cands) {
 const candidates=cands.slice(0,4).map(i=>{const e=S.db.entries[i],system=SYS[e[0]].tag;return {system,edition:system==='HS'?'2022':'snapshot:d6d1b417562b',code:String(e[1])};});
 if(parent===window){const slot=el('assist-slot');if(slot)slot.textContent='Open Finder inside the news workspace to ask about these preserved candidates.';return;}
 parent.postMessage({type:'public-ai-question-v1',mode:'finder',question:V.q.slice(0,1000),candidates},location.origin);
}'''
def transform(html,selection=None):
 replacement=REPLACEMENT
 if selection is not None:
  from integration.finder_composition_f9 import Selection
  if type(selection)is not Selection:raise ValueError('Exact Finder selection required')
  selection.verify()
  replacement=replacement.replace('snapshot:d6d1b417562b',dict(selection.editions)['IN'])
 elif hashlib.sha256((ROOT/'offline.html').read_bytes()).hexdigest()!=PIN:raise ValueError('Finder source drift')
 if html.count(START)!=1 or html.count(END)!=1:raise ValueError('Finder assist seam drift')
 start=html.index(START);end=html.index(END,start)
 html=html[:start]+replacement+html[end:]
 html=html.replace('Live features off. Local edits last for this page only.','Only manual AI picks can open the parent workspace. Live provider fetch remains off. Local edits last for this page only.')
 # Existing inert OFFLINE_STORE remains inert. Rebuild script hashes after edit.
 html=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',html,count=1)
 scripts=re.findall(r'<script>(.*?)</script>',html,re.S|re.I)
 hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in scripts)
 html=html.replace('</head>', '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src '+hashes+'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'; form-action \'none\'; base-uri \'none\'"></head>',1)
 return html
