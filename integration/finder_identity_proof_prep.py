"""Dormant source binding only. No href, mount, route, environment or DB work.

Bound means one offline row and one resolved index row with the same normalized
plain description. Labels are preserved source claims, not verified editions.
The fixed-record proof is read with bounded pread, never decoded into a map.
"""
import hashlib
import os
import re
import struct
import unicodedata
from pathlib import Path
from threading import Lock
from dataclasses import dataclass
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[1]
RECORD = struct.Struct('>B12s32s')
CHUNK = 65536
MAX_ARTIFACT = 2000000
EDITIONS = {'HS': '2022', 'IN': 'snapshot:d6d1b417562b'}
SYSTEMS = {'HS': 0, 'IN': 1}
ARTIFACT = 'integration/finder_identity_proof.bin'
ARTIFACT_SHA = 'bfbea25e82ffaddadae5b8e6175ce27d1872477c96d31e085d1a0056fb6e6fc2'
PINS = {
 'offline.html': '0e2e85ea54f276c3c50984e8c26b9400e1deee9f4b8a035a8866e56c2455b65b',
 'index.html': '8e1ce9c7fa5da880085afb2b8a20e6fbc3195d8b24f4ffdde4bee09c787d0967',
 'data.d6d1b417562b.js': 'd6d1b417562bad99e7b434605d63966772749d573375fb10d74ee52cb6bb82f6',
 'integration/code_news_index/manifest.json': '6edbda1415380b9b99f1f28a79ced563cd72b3ab4ab6323a35cfd531b62e17ea',
 'integration/code_news_index/codes.idx': '4f6487562fd144ef42f75724581fc4d206bf2f0df7b78ce6c66270bffff3fb03',
 'integration/code_news_index/rows.jsonl': 'e258d3a5ae3f285ab135a0c262a30501135b59b8e7bcb3fdd0b0dcd802d1f502',
}
class Unavailable(ValueError):
 pass

@dataclass(frozen=True)
class ProofProfile:
 """Explicit internal candidate identity. Never an approval or public input."""
 pins:tuple
 editions:tuple
 artifact_sha256:str
 def validate(self):
  if type(self.pins)is not tuple or any(type(row)is not tuple or len(row)!=2 or any(type(v)is not str for v in row)for row in self.pins):raise Unavailable('Exact proof profile pins required')
  pins=dict(self.pins)
  required={'offline.html','index.html','integration/code_news_index/manifest.json','integration/code_news_index/codes.idx','integration/code_news_index/rows.jsonl'}
  if len(pins)!=6 or len(self.pins)!=6 or not required<set(pins):raise Unavailable('Closed proof profile sources required')
  data=next(n for n in pins if n not in required)
  if not re.fullmatch(r'data\.[a-f0-9]{12}\.js',data)or any(not re.fullmatch('[a-f0-9]{64}',v)for v in pins.values())or data[5:17]!=pins[data][:12]:raise Unavailable('Exact proof profile hashes required')
  if type(self.editions)is not tuple or self.editions!=(('HS','2022'),('IN','snapshot:'+pins[data][:12]))or type(self.artifact_sha256)is not str or not re.fullmatch('[a-f0-9]{64}',self.artifact_sha256):raise Unavailable('Exact proof edition/artifact binding required')

def normalized_description(value):
 """NFC then Unicode whitespace collapse; case/punctuation are preserved.
 No duplicate is collapsed, even if its normalized description is identical.
 """
 if type(value) is not str or not 1 <= len(value) <= 4000 or any(ord(c) < 32 and c not in '\n\t' for c in value):
  raise Unavailable('Description unavailable')
 result = ' '.join(unicodedata.normalize('NFC', value).split())
 if not result:
  raise Unavailable('Description unavailable')
 return result

def digest_path(path):
 h = hashlib.sha256()
 with Path(path).open('rb', buffering=0) as f:
  while chunk := f.read(CHUNK):
   h.update(chunk)
 return h.hexdigest()

def verify_sources(root,profile=None):
 if profile is not None:
  if type(profile)is not ProofProfile:raise Unavailable('Exact proof profile required')
  profile.validate()
 for name, expected in (PINS.items()if profile is None else profile.pins):
  if profile is not None and (any(p.is_symlink()for p in (Path(root)/name,*(Path(root)/name).parents))or not (Path(root)/name).is_file()):raise Unavailable('Regular proof sources required')
  if digest_path(Path(root) / name) != expected:
   raise Unavailable('Proof source drift')

class FinderProof:
 """Leaf lock: hash/read/close only; no callbacks or other lock acquisition.
 Source pins stream on init AND lookup, so source drift fails before approval.
 This trades bounded IO for no large RAM map and no cached freshness assertion.
 """
 def __init__(self, root=ROOT,*,profile=None):
  self.root = Path(root); self.profile=profile; self.lock = Lock(); self.fd = None; self.closed = False
  try:
   if profile is not None:
    if type(profile)is not ProofProfile:raise Unavailable('Exact proof profile required')
    profile.validate()
   self.editions=MappingProxyType(dict(EDITIONS if profile is None else profile.editions))
   self.artifact_sha256=ARTIFACT_SHA if profile is None else profile.artifact_sha256
   self._verify_sources()
   if profile is not None and ((self.root/ARTIFACT).is_symlink()or not (self.root/ARTIFACT).is_file()):raise Unavailable('Regular proof artifact required')
   self.fd = os.open(self.root / ARTIFACT, os.O_RDONLY)
   self.size = os.fstat(self.fd).st_size
   if not 0 < self.size <= MAX_ARTIFACT or self.size % RECORD.size:
    raise Unavailable('Proof length unavailable')
   self.count = self.size // RECORD.size
   self._verify_artifact()
   previous = None
   for i in range(self.count):
    system, code, description = RECORD.unpack(self._read(RECORD.size, i * RECORD.size))
    key = (system, code)
    plain = code.rstrip(b' ')
    if system not in (0, 1) or not re.fullmatch(rb'[0-9]{4}(?:[0-9]{2}){0,4}', plain) or code != plain.ljust(12, b' ') or (previous is not None and key <= previous):
     raise Unavailable('Proof record unavailable')
    previous = key
  except Exception:
   self.close(); raise Unavailable('Finder proof unavailable') from None
 def _verify_sources(self):
  if self.profile is None:verify_sources(self.root)
  else:verify_sources(self.root,self.profile)
 def _read(self, length, offset):
  raw = os.pread(self.fd, length, offset)
  if len(raw) != length:
   raise Unavailable('Short proof read')
  return raw
 def _verify_artifact(self):
  if self.profile is not None and (self.root/ARTIFACT).is_symlink():raise Unavailable('Regular proof artifact required')
  descriptor = os.fstat(self.fd); current = (self.root / ARTIFACT).stat()
  if (descriptor.st_dev, descriptor.st_ino) != (current.st_dev, current.st_ino) or descriptor.st_size != self.size:
   raise Unavailable('Proof size drift')
  h = hashlib.sha256()
  for offset in range(0, self.size, CHUNK):
   h.update(self._read(min(CHUNK, self.size - offset), offset))
  if h.hexdigest() != self.artifact_sha256:
   raise Unavailable('Proof hash drift')
 def close(self):
  with self.lock:
   if self.closed:
    return
   self.closed = True
   if self.fd is not None:
    os.close(self.fd); self.fd = None
 def bound(self, system, edition, code):
  if type(system) is not str or system not in SYSTEMS or type(edition) is not str or edition != self.editions[system] or type(code) is not str or not re.fullmatch(r'[0-9]{4}(?:[0-9]{2}){0,4}', code):
   return None
  try:
   with self.lock:
    if self.closed:
     return None
    self._verify_sources()
    self._verify_artifact()
    needle = (SYSTEMS[system], code.encode().ljust(12, b' ')); lo = 0; hi = self.count
    while lo < hi:
     mid = (lo + hi) // 2
     si, key, sha = RECORD.unpack(self._read(RECORD.size, mid * RECORD.size))
     if (si, key) < needle:
      lo = mid + 1
     else:
      hi = mid
    if lo >= self.count:
     return None
    si, key, sha = RECORD.unpack(self._read(RECORD.size, lo * RECORD.size))
    if (si, key) != needle:
     return None
   return {'system': system, 'edition': edition, 'code': code, 'system_index': si,
           'normalized_description_sha256': sha.hex(), 'state': 'bound_preserved_snapshot',
           'label': 'labeled HS 2022 / preserved snapshot' if system == 'HS' else 'India HSN / preserved snapshot',
           'edition_verified': False}
  except (OSError, ValueError):
   return None
