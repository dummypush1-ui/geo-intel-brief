"""Generate private-staging integrity metadata, excluding temporary files."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'staging-manifest.json','integration/MAIL-CONTRACT.md','integration/FILE-MAP.txt','integration/file-connections.json','UPLOAD-INSTRUCTIONS.txt','PATCH-V6-README.txt'}
def commit_files():
 return sorted(p for p in ROOT.rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in EXCLUDED and not any(x in p.parts for x in ('__pycache__','.git','node_modules','.venv','.github')))
def manifest(test_count):
 return {'state':'private_staging','collection':False,'mail':False,'scraper':False,'tests':test_count,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in commit_files()]}
if __name__=='__main__':
 import sys
 (ROOT/'staging-manifest.json').write_text(json.dumps(manifest(int(sys.argv[1])),indent=2)+'\n')
