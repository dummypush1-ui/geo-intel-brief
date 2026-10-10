"""Offline pinned-source index build. Does not touch DB/network or source files."""
from pathlib import Path
import json,hashlib,struct,collections
from integration.code_news_catalogue import extract,model_rows,omission_ledger
ROOT=Path(__file__).resolve().parents[1]
def build(root=ROOT):
 root=Path(root);pins=json.loads((root/'integration/code_news_pins.json').read_text());snapshot=extract(root,**pins)
 grouped=collections.defaultdict(list)
 for row in model_rows(snapshot):grouped[row['code']].append(dict(row,state='resolved'))
 for row in omission_ledger(snapshot):grouped[row['code']].append(row)
 folder=root/'integration/code_news_index';folder.mkdir(exist_ok=True)
 record=struct.Struct('>12sQI');offset=0
 with(folder/'rows.jsonl').open('wb')as rows,(folder/'codes.idx').open('wb')as idx:
  for code in sorted(grouped):
   payload=json.dumps(sorted(grouped[code],key=lambda r:(r['system'],r['edition'])),ensure_ascii=True,separators=(',',':')).encode()+b'\n'
   if len(payload)>65536 or len(grouped[code])>100:raise ValueError('Oversized rowgroup')
   idx.write(record.pack(code.encode().ljust(12,b' '),offset,len(payload)));rows.write(payload);offset+=len(payload)
 manifest={'format':'code_news_flat_v1','source_pins':pins,'code_count':len(grouped),'identity_count':sum(map(len,grouped.values())),'scope':'preserved_snapshot_not_current_official_verification','files':{}}
 for name in('codes.idx','rows.jsonl'):
  p=folder/name;manifest['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 return manifest
if __name__=='__main__':print(json.dumps(build(),indent=2))
