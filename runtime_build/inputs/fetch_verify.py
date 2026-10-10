"""Candidate fetch stage only; expected ledgers fixed before network fetch."""
import pathlib,json,urllib.request,urllib.parse,hashlib,sys
root=pathlib.Path(__file__).resolve().parent;out=pathlib.Path(sys.argv[1]);out.mkdir()
rows=json.loads((root/'wheel-ledger.json').read_text())['packages']
for row in rows:
 if row['profile']=='build-source':continue
 url=row['origin_url'];assert urllib.parse.urlparse(url).hostname=='files.pythonhosted.org'
 response=urllib.request.urlopen(url,timeout=60);assert urllib.parse.urlparse(response.url).hostname=='files.pythonhosted.org'
 raw=response.read();assert len(raw)==row['size']and hashlib.sha256(raw).hexdigest()==row['sha256'];(out/row['filename']).write_bytes(raw)
# Local sgml output is NOT fetched: complete reviewed anchor required separately.
