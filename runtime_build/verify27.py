from scripts.doc_lookup import source_bytes, source_text
"""local CPython3.10.12 Linuxx86_64 venv build/import proof, never target closure."""
import hashlib,json,pathlib,sys
SCOPE='local CPython3.10.12 Linuxx86_64 venv build/import proof'
def digest(p):return hashlib.sha256(source_bytes(p)).hexdigest()
def verify(directory,rows):
 root=pathlib.Path(directory)
 actual={p.name for p in root.iterdir() if p.is_file()}
 expected={r['filename'] for r in rows}
 if len(expected)!=len(rows):raise ValueError('duplicate artifact')
 if actual!=expected or any(p.is_symlink() or not p.is_file() for p in root.iterdir()):raise ValueError('missing/extra/nonregular artifact')
 for r in rows:
  name=r['filename']
  if name!=pathlib.PurePosixPath(name).name or '/' in name or '\\'in name or name in ('.','..'):raise ValueError('artifact filename')
  if digest(root/name)!=r['sha256']:raise ValueError('artifact hash mismatch')
 return sorted(expected)
def source(root,manifest):
 root=pathlib.Path(root)
 for name,value in manifest['files'].items():
  p=root/name
  if p.is_symlink() or digest(p)!=value:raise ValueError('source drift '+name)
 return manifest['anchor']
def main():
 here=pathlib.Path(__file__).resolve().parent
 m=json.loads((here/'artifacts.json').read_text());a=verify(sys.argv[1],m['artifacts']);s=source(sys.argv[2],json.loads((here/'source-allowlist.json').read_text()))
 print(json.dumps({'scope':SCOPE,'source_anchor':s,'artifacts':a,'selected_profile':'current25-gunicorn26-no-optional-extras','claim':'input validation only'},sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
