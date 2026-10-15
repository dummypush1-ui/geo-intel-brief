"""Reproducible build-time proof. Does NOT rebuild or write the existing index.
Large source decoding is confined to this generator, never runtime lookup.
Whole-list equality is recorded diagnostic data and is NOT binding evidence.
"""
import base64
import collections
import gzip
import hashlib
import io
import json
import re
from pathlib import Path
from integration.finder_identity_proof_prep import (ROOT, RECORD, EDITIONS, SYSTEMS, ARTIFACT,
 normalized_description, verify_sources, Unavailable)
INDEX_RECORD = __import__('struct').Struct('>12sQI')
FRAGMENT = "const m = location.hash.match(/^#code=(\\d+):(\\d+)$/);"
LOOKUP = "const i = m ? S.db.keyToIdx.get(Number(m[1]) + ':' + m[2]) : undefined;"
UNKNOWN = "} else if (S.sel !== null || S.cmpA !== null || S.showList) back();"

def decode_payload(source):
 literals = re.findall(r'var DATA_B64 = "([A-Za-z0-9+/=]+)";', source)
 if len(literals) != 1:
  raise Unavailable('One data literal required')
 with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(literals[0], validate=True))) as f:
  plain = f.read(100000001)
 if len(plain) > 100000000:
  raise Unavailable('Expanded source cap')
 rows = json.loads(plain)
 if type(rows) is not list or len(rows) > 400000:
  raise Unavailable('Source rows cap')
 return rows, hashlib.sha256(literals[0].encode()).hexdigest()

def source_systems(shell):
 block = re.search(r'const SYS = \[\n(.*?)\n\];', shell, re.S)
 if not block:
  raise Unavailable('Systems missing')
 tags = re.findall(r"^  \{ tag: '([A-Z]{2,3})', name: '([^']+)', src: '(.*)', url: '([^']+)' \},$", block[1], re.M)
 if len(tags) != 22 or [t[0] for t in tags[:2]] != ['HS', 'IN']:
  raise Unavailable('Systems changed')
 return tags

def offline_identities(rows, tags, editions=None):
 editions = EDITIONS if editions is None else editions
 for row in rows:
  if type(row) is not list or len(row) != 6 or type(row[0]) is not int or not 0 <= row[0] < len(tags) or type(row[1]) is not str or type(row[2]) is not str:
   raise Unavailable('Malformed offline row')
  tag = tags[row[0]][0]
  yield {'system': tag, 'edition': editions.get(tag, 'unsupported'), 'code': row[1], 'description': row[2]}

def derive_records(offline, indexed, editions=None):
 """Exact multiplicity on each side. No list-parity or last-row shortcut."""
 editions = EDITIONS if editions is None else editions
 groups = collections.defaultdict(list)
 for row in offline:
  if row['system'] in SYSTEMS:
   groups[(row['system'], row['edition'], row['code'])].append(row)
 candidates = collections.defaultdict(list)
 for row in indexed:
  if row['system'] in SYSTEMS:
   candidates[(row['system'], row['edition'], row['code'])].append(row)
 records = []; reasons = collections.Counter()
 for key in sorted(set(groups) | set(candidates)):
  system, edition, code = key
  if system not in SYSTEMS or edition != editions[system]:
   reasons['unsupported_identity'] += 1; continue
  a = groups.get(key, []); b = candidates.get(key, [])
  if len(a) != 1 or len(b) != 1:
   reasons['offline_count_' + str(len(a)) + '_index_count_' + str(len(b))] += 1; continue
  if b[0].get('state') != 'resolved' or not re.fullmatch(r'[0-9]{4}(?:[0-9]{2}){0,4}', code):
   reasons['not_resolved_or_code_shape'] += 1; continue
  try:
   left = normalized_description(a[0]['description']); right = normalized_description(b[0].get('description'))
  except Unavailable:
   reasons['unusable_description'] += 1; continue
  if left != right:
   reasons['description_mismatch'] += 1; continue
  records.append(RECORD.pack(SYSTEMS[system], code.encode().ljust(12, b' '), hashlib.sha256(left.encode()).digest()))
 return b''.join(sorted(records)), dict(sorted(reasons.items()))

def indexed_rows(root):
 folder = root / 'integration/code_news_index'
 # Already pinned by verify_sources; validate positional rowgroup relation too.
 previous = b''; end = 0
 with (folder / 'codes.idx').open('rb') as idx, (folder / 'rows.jsonl').open('rb') as data:
  while raw := idx.read(INDEX_RECORD.size):
   if len(raw) != INDEX_RECORD.size:
    raise Unavailable('Short index record')
   code, offset, length = INDEX_RECORD.unpack(raw)
   if code <= previous or offset != end or not 1 <= length <= 65536:
    raise Unavailable('Index relation changed')
   data.seek(offset); payload = data.read(length)
   if len(payload) != length:
    raise Unavailable('Short index group')
   rows = json.loads(payload)
   if type(rows) is not list or len(rows) > 100 or any(r.get('code') != code.rstrip(b' ').decode() for r in rows):
    raise Unavailable('Index row relation changed')
   yield from rows
   previous = code; end = offset + length
  if end != (folder / 'rows.jsonl').stat().st_size:
   raise Unavailable('Index EOF changed')

def generate(root=ROOT):
 root = Path(root); verify_sources(root)
 offline_shell = (root / 'offline.html').read_text(); online_shell = (root / 'index.html').read_text()
 tags = source_systems(offline_shell)
 if tags != source_systems(online_shell):
  raise Unavailable('Source labels differ')
 for shell in (offline_shell, online_shell):
  if any(shell.count(seam) != 1 for seam in (FRAGMENT, LOOKUP, UNKNOWN)):
   raise Unavailable('Fragment handler changed')
 def row_digest(items):
  h = hashlib.sha256()
  for item in items:
   h.update(json.dumps(item, ensure_ascii=True, separators=(',', ':')).encode() + b'\n')
  return h.digest()
 rows, encoded_sha = decode_payload(offline_shell)
 count = len(rows); offline_digest = row_digest(rows)
 del rows
 bundle, _ = decode_payload((root / 'data.d6d1b417562b.js').read_text())
 parity = len(bundle) == count and row_digest(bundle) == offline_digest
 if count != 340232 or not parity:
  raise Unavailable('Pinned raw parity changed')
 del bundle, online_shell
 rows, _ = decode_payload(offline_shell)
 payload, reasons = derive_records(offline_identities(rows, tags), indexed_rows(root))
 report = {'offline_rows': len(rows), 'bundle_rows': 340232, 'raw_list_equal_diagnostic_only': parity,
           'encoded_offline_sha256': encoded_sha, 'artifact_bytes': len(payload),
           'record_bytes': RECORD.size, 'bound_count': len(payload) // RECORD.size,
           'artifact_sha256': hashlib.sha256(payload).hexdigest(), 'not_bound_reasons': reasons,
           'fragment_handler': FRAGMENT, 'fragment_has_edition': False,
           'edition_field_exists': False, 'labels_verified': False,
           'source_labels': [{'system': t[0], 'name_claim': t[1], 'source_claim': t[2]} for t in tags[:2]]}
 return payload, report

if __name__ == '__main__':
 payload, report = generate()
 (ROOT / ARTIFACT).write_bytes(payload)
 print(json.dumps(report, indent=2))
