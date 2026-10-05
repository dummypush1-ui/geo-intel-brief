"""Pure expected-revision check/stream byte transform, NOT atomic persistence."""
import hashlib,hmac,re
import yaml
from datetime import datetime,timezone
from integration.stream_config import configured_streams,MAX_BYTES
from integration.brics_streams import FixtureStreams
STORED=('name','country','type','video_id','channel_id')
class RevisionError(ValueError):pass

def revise(raw,expected_revision,operation,fields,observed_at):
 try:
  if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES or raw.startswith(b'\xef\xbb\xbf') or b'\x00' in raw:raise ValueError()
  raw.decode('utf-8',errors='strict')
  if type(expected_revision) is not str or re.fullmatch('[0-9a-f]{64}',expected_revision,re.ASCII) is None:raise ValueError()
  digest=hashlib.sha256(raw).hexdigest()
  if not hmac.compare_digest(expected_revision,digest):raise RevisionError('Stream revision conflict')
  if type(fields) is not dict or any(type(k) is not str or type(v) is not str for k,v in fields.items()):raise ValueError()
  if operation=='add':
   if set(fields)!={'name','country','link'}:raise ValueError()
  elif operation=='remove':
   if set(fields)!={'name'}:raise ValueError()
  else:raise ValueError()
  parsed=configured_streams(raw,observed_at)
  fixture=FixtureStreams(parsed['items'])
  if operation=='add':fixture.add(fields['name'],fields['country'],fields['link']);changed=True
  else:changed=fixture.remove(fields['name'])
  if not changed:return {'bytes':raw,'sha256':digest,'changed':False,'comment_format_loss':False,'scope':'supplied_bytes_expected_revision_only','persistence':False,'availability':'not_checked'}
  stored=[{k:r[k] for k in STORED if k in r} for r in fixture.load()]
  new=yaml.safe_dump({'streams':stored},sort_keys=False,allow_unicode=True,default_flow_style=False,explicit_start=False,explicit_end=False,width=1000,indent=2,line_break='\n').encode('utf-8')
  if not 0<len(new)<=MAX_BYTES or new.startswith(b'\xef\xbb\xbf') or b'\x00' in new:raise ValueError()
  reparsed=configured_streams(new,observed_at)
  if reparsed['items']!=fixture.load():raise ValueError()
  return {'bytes':new,'sha256':hashlib.sha256(new).hexdigest(),'changed':True,'comment_format_loss':True,'scope':'supplied_bytes_expected_revision_only','persistence':False,'availability':'not_checked'}
 except RevisionError:raise
 except Exception:raise RevisionError('Invalid stream revision request') from None
