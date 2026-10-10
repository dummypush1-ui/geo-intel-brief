"""Extract only pinned preserved Finder bytes; no evaluation/network/currentness."""
import re,json,gzip,base64,hashlib,io
from pathlib import Path
class Refused(ValueError):pass

def extract(root,*,expected_shell_sha256,expected_bundle_sha256):
 root=Path(root);shell_path=root/'index.html'
 if shell_path.stat().st_size>2000000:raise Refused('Shell cap')
 raw=shell_path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected_shell_sha256:raise Refused('Pinned shell mismatch')
 shell=raw.decode('utf-8');names=set(re.findall(r'data\.[0-9a-f]{12}\.js',shell))
 if len(names)!=1:raise Refused('One data bundle required')
 name=names.pop();p=root/name
 if p.stat().st_size>30000000:raise Refused('Bundle cap')
 data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()
 if digest!=expected_bundle_sha256 or digest[:12]!=name[5:17]:raise Refused('Pinned bundle mismatch')
 encoded=re.match(r'var DATA_B64 = "([A-Za-z0-9+/=]+)";',data.decode('utf-8'))
 if not encoded:raise Refused('Data literal missing')
 with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded[1],validate=True)))as f:plain=f.read(100000001)
 if len(plain)>100000000:raise Refused('Expanded cap')
 rows=json.loads(plain)
 table=re.search(r'const SYS = \[\n(.*?)\n\];',shell,re.S)
 if not table:raise Refused('Systems missing')
 systems=[]
 for line in table[1].splitlines():
  m=re.fullmatch(r"  \{ tag: '([A-Z]{2,3})', name: '([^']+)', src: '(.*)', url: '([^']+)' \},",line)
  if not m:raise Refused('System literal changed')
  tag,label,claimed_source,claimed_url=m.groups()
  systems.append(dict(tag=tag,name=label,source_claim=claimed_source,source_url_claim=claimed_url,edition='2022'if tag=='HS'else'snapshot:'+digest[:12],edition_scope='preserved_WCO_HS2022_label_not_current_verified'if tag=='HS'else'preserved_snapshot_not_current_national_edition'))
 supplement=re.search(r'const US_CH97_SUPPLEMENT = (\[.*?\]);',shell)
 if not supplement or type(rows)is not list:raise Refused('Supplement/rows missing')
 seen={r[1]for r in rows if type(r)is list and len(r)==6 and r[0]==2}
 for row in json.loads(supplement[1]):
  if type(row)is not list or len(row)!=6 or row[0]!=2:raise Refused('Invalid supplement')
  if row[1]not in seen:rows.append(row);seen.add(row[1])
 result={};source_rows=[];conflicts=set();duplicates=0;skipped=0
 for row in rows:
  if type(row)is not list or len(row)!=6 or type(row[0])is not int or not 0<=row[0]<len(systems)or any(type(row[i])is not str for i in (1,2,4,5))or type(row[3])not in (str,type(None)):raise Refused('Invalid row')
  si,code,description,parent,chapter,_=row
  if len(code)>64 or len(description)>8000 or (parent is not None and len(parent)>64):raise Refused('Bounded catalogue cell')
  if not re.fullmatch('[0-9]{2,12}',code):skipped+=1;continue
  system=systems[si];key=(system['tag'],system['edition'],code)
  if key in result:
   duplicates+=1
   if result[key]['description']!=description:conflicts.add(key)
  record=dict(system=key[0],edition=key[1],code=code,description=description,parent_code=parent,chapter=chapter,system_index=si,description_sha256=hashlib.sha256(description.encode()).hexdigest(),edition_scope=system['edition_scope'])
  source_rows.append(record);result[key]=record
 # Parent is taken ONLY from source row, never fabricated from numeric prefix.
 for row in source_rows:
  parent=result.get((row['system'],row['edition'],row['parent_code']))
  row['parent_state']='conflicting_source_rows'if (row['system'],row['edition'],row['parent_code'])in conflicts else'resolved'if parent else'root_or_missing_in_snapshot'
  row['identity_state']='conflicting_source_rows'if (row['system'],row['edition'],row['code'])in conflicts else'nonconflicting_source_rows'
 return dict(state='source_bound_snapshot_not_live_legal_verification',shell_sha256=expected_shell_sha256,bundle_sha256=digest,bundle=name,systems=systems,rows=source_rows,unique_identity_count=len(result),duplicate_source_rows=duplicates,conflicting_keys=[{'system':k[0],'edition':k[1],'code':k[2]}for k in sorted(conflicts)],unsupported_keys_skipped=skipped)

def model_rows(snapshot):
 unique={}
 for r in snapshot['rows']:
  if r['identity_state']=='conflicting_source_rows':continue
  unique[(r['system'],r['edition'],r['code'])]=r
 return [{k:r[k]for k in ('system','edition','code','description')}for r in unique.values()if len(r['code'])in (4,6,8,10,12)and 1<=len(r['description'])<=4000 and not any(ord(c)<32 and c not in '\n\t' for c in r['description'])]

def candidate_vocabulary(snapshot):
 lookup={(r['system'],r['code']):r for r in snapshot['rows']}
 # Tiny explicit proposal. Never infer aliases from arbitrary descriptions.
 proposals=[('rice','1006',['rice'],['Rice University','Condoleezza Rice']),('coffee','0901',['coffee'],['coffee table','coffee tables','coffee shop','coffee shops','coffee mug','coffee mugs','Coffee County']),('telephones','8517',['smartphones','smartphone'],['smartphone app','smartphone apps'])]
 rules=[]
 for commodity,code,phrases,excludes in proposals:
  r=lookup.get(('HS',code))
  if not r:raise Refused('Proposal heading missing')
  rules.append(dict(id='proposal-'+commodity+'-'+code,system=r['system'],edition=r['edition'],code=code,commodity=commodity,phrases=phrases,trade_cues=['exports','imports','tariff','export ban','import ban','export restrictions','import restrictions','export controls','chip ban','sanctions'],exclude_phrases=excludes,source_description_sha256=r['description_sha256'],review_state='draft',review_limits=['article-wide exclusion','negation not handled','trade cue may refer to another commodity','no current duty or classification claim']))
 return rules

def omission_ledger(snapshot):
 unique={}
 for row in snapshot['rows']:
  key=(row['system'],row['edition'],row['code'])
  state=('conflicting_source_rows'if row['identity_state']=='conflicting_source_rows'else'not_in_link_model'if len(row['code'])not in (4,6,8,10,12)else'unusable_description'if not 1<=len(row['description'])<=4000 or any(ord(c)<32 and c not in '\n\t' for c in row['description'])else None)
  if state:unique[key]=dict(system=key[0],edition=key[1],code=key[2],state=state)
 return list(unique.values())
