"""Read the preserved Finder bundle without evaluating JavaScript or fetching.

A link identifies system + exact code, not the row position. Only explicit
HS/HSN mentions produce reverse suggestions. No country-to-code inference.
"""
import base64,gzip,hashlib,io,json,re
from pathlib import Path

class FinderIndex:
 def __init__(self,rows,systems):
  self.by_code={};identities={}
  for row in rows:
   if not isinstance(row,list) or len(row)!=6:raise ValueError('Invalid Finder row')
   system,code=row[:2]
   if type(system) is not int or not 0<=system<len(systems) or not isinstance(code,str) or not code or len(code)>64:raise ValueError('Invalid Finder identity')
   if not isinstance(row[2],str):raise ValueError('Invalid Finder description')
   key=(system,code)
   # Finder's Map selects the last row when a source repeats a key.
   identities[key]=row
  for (system,code),row in identities.items():
   # Preserve source rows but do not offer nonnumeric keys the hash router cannot open.
   if not re.fullmatch(r'\d{2,12}',code):continue
   self.by_code.setdefault(code,[]).append({'code':code,'system':systems[system]['tag'],'system_name':systems[system]['name'],'system_index':system,'index_verified':True})
 def for_article(self,article):
  text=str(article.get('title',''))+' '+str(article.get('summary',''))
  codes=dict.fromkeys(re.findall(r'(?<!\w)hs(?:n)?\s*(?:code\s*)?[:#-]?\s*(\d{6,12})(?!\w|\s*[.\-/,]\s*\d|\s+\d)',text,re.I))
  return [dict(context) for code in codes for context in self.by_code.get(code,[])]

def load_bundled_index(root):
 root=Path(root);shell_path=root/'index.html'
 if shell_path.stat().st_size>2_000_000:raise ValueError('Finder shell too large')
 shell=shell_path.read_text()
 names=set(re.findall(r'data\.[0-9a-f]{12}\.js',shell))
 if len(names)!=1:raise ValueError('Exactly one Finder bundle required')
 name=names.pop();bundle_path=root/name
 if bundle_path.stat().st_size>30_000_000:raise ValueError('Finder bundle too large')
 payload=bundle_path.read_bytes()
 if len(payload)>30_000_000 or hashlib.sha256(payload).hexdigest()[:12]!=name[5:17]:raise ValueError('Finder bundle fingerprint mismatch')
 source=payload.decode('utf-8')
 encoded=re.match(r'var DATA_B64 = "([A-Za-z0-9+/=]+)";',source)
 if not encoded:raise ValueError('Finder data literal missing')
 with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded[1],validate=True))) as stream:
  plain=stream.read(100_000_001)
 if len(plain)>100_000_000:raise ValueError('Finder data too large')
 rows=json.loads(plain)
 table=re.search(r'const SYS = \[\n(.*?)\n\];',shell,re.S)
 if not table:raise ValueError('Finder systems missing')
 systems=[{'tag':tag,'name':label} for tag,label in re.findall(r"^  \{ tag: '([A-Z]{2,3})', name: '([^']+)',",table[1],re.M)]
 if not systems or len(systems)!=len(table[1].splitlines()):raise ValueError('Invalid Finder systems')
 supplement=re.search(r'const US_CH97_SUPPLEMENT = (\[.*?\]);',shell)
 if not supplement:raise ValueError('Finder supplement missing')
 if not isinstance(rows,list):raise ValueError('Invalid Finder dataset')
 seen={r[1] for r in rows if isinstance(r,list) and r and r[0]==2}
 for row in json.loads(supplement[1]):
  if row[0]!=2:raise ValueError('Invalid supplement system')
  if row[1] not in seen:rows.append(row);seen.add(row[1])
 return FinderIndex(rows,systems)
