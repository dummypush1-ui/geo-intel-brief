"""Served-copy offline seam. Original source reviewed for196 token removal; public snapshot only."""
import re,hashlib,base64
from integration.branding_meta import HeadTags
from integration.finder_network import manual_ships_shell

DATA_NAME='data.d6d1b417562b.js'
PWA_REGISTER="""if ('serviceWorker' in navigator && location.protocol === 'https:' && location.hostname === 'finder-hsn-codee.onrender.com') {
    window.addEventListener('load', function () { navigator.serviceWorker.register('./sw.js').catch(function () {}); });
  }"""

OFFLINE_SHA = '2e8521b733d94955ef9ec5e0b85399a78dfff5d50836a174fb180cd08ed9c6e3'

def shell(original):
 if hashlib.sha256(original.encode()).hexdigest()!=OFFLINE_SHA:raise ValueError('Offline source requires review')
 original=HeadTags(original).stripped()
 original=manual_ships_shell(original)
 # All offline network capabilities disabled, including code-level fetch.
 for name in ('AI_PROXY_URL','AIS_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS'):
  pattern=r'(const\s+'+name+r"\s*=\s*)'[^']*'"
  original,n=re.subn(pattern,lambda m:m[1]+"''",original)
  if n!=1:raise ValueError('Offline key seam changed')
 # Device's same-origin provider keys/notes/AI outputs are not public data.
 # Offline is intentionally session-only state, and never reads localStorage.
 if 'localStorage' not in original or '<script>' not in original or '</head>' not in original or '<body>' not in original:raise ValueError('Offline rewrite seam changed')
 original=original.replace('localStorage','OFFLINE_STORE')
 original=original.replace('<script>',"<script>\nconst OFFLINE_STORE = {getItem(){return null;},setItem(){},removeItem(){}};\nconst fetch = async()=>{throw new Error('Offline snapshot: live network disabled');};\n",1)
 # Original offline build is self-contained and has no SW registration.
 scripts=re.findall(r'<script>(.*?)</script>',original,re.S|re.I)
 hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts)
 original=original.replace('</head>',"<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src "+hashes+"; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'\"></head>",1)
 original=original.replace('<body>', '<body><p style="padding:12px;background:#fff3cd;color:#493b10">Public offline Finder snapshot. No private news, saved keys or notes. Live features off. Local edits last for this page only.</p>',1)
 return original

def opt_in(original):
 if original.count(PWA_REGISTER)!=1:raise ValueError('PWA registration seam changed')
 original=original.replace(PWA_REGISTER,'/* Registration requires explicit device opt-in. */')
 original=original.replace('href="/workspace/manifest.webmanifest"','href="./offline-manifest.webmanifest"')
 return original.rsplit('</body>',1)[0]+'<section style="padding:16px"><h2>Public offline Finder</h2><p>Store the public snapshot on this device. Private news/accounts are never cached. Existing same-origin keys and notes are not read by the offline copy.</p><button id="finder-offline-save">Store public snapshot on this device</button><button id="finder-offline-clear">Clear offline Finder snapshot</button><a href="./offline.html">Open public offline snapshot</a><p id="finder-offline-status" role="status"></p></section><script src="./offline-control.js"></script></body>'+original.rsplit('</body>',1)[1]
