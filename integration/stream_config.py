"""Bounded original BRICS YAML stream snapshot parser, no filesystem/network.

Explicit supplied UTF-8 bytes only. No default path, original imports or writes.
Converts original configuration to the existing strict stream grammar. Does
not claim configured stream availability, persistence, or current live state.
"""
import hashlib
import yaml
from integration.brics_streams import enrich,name_key
from datetime import datetime,timezone
MAX_BYTES=16384
class StreamConfigError(ValueError):pass
class StrictLoader(yaml.SafeLoader):pass

def mapping(loader,node,deep=False):
 out={}
 for key_node,value_node in node.value:
  if key_node.tag!='tag:yaml.org,2002:str':raise StreamConfigError('String keys required')
  key=loader.construct_object(key_node,deep=deep)
  if key in out:raise StreamConfigError('Duplicate keys')
  out[key]=loader.construct_object(value_node,deep=deep)
 return out
StrictLoader.add_constructor('tag:yaml.org,2002:map',mapping)

def configured_streams(raw,observed_at):
 if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:raise StreamConfigError('Bounded UTF-8 snapshot required')
 if type(observed_at) is not datetime or type(observed_at.tzinfo) is not timezone:raise StreamConfigError('Fixed aware observation required')
 try:
  text=raw.decode('utf-8')
  tokens=0
  for token in yaml.scan(text):
   tokens+=1
   if tokens>1000:raise StreamConfigError('Token budget')
   if isinstance(token,(yaml.tokens.AliasToken,yaml.tokens.AnchorToken,yaml.tokens.TagToken,yaml.tokens.DirectiveToken)):raise StreamConfigError('YAML aliases/tags/directives not supported')
  depth=0;events=0
  for event in yaml.parse(text):
   events+=1
   if events>1000:raise StreamConfigError('Event budget')
   if isinstance(event,(yaml.events.MappingStartEvent,yaml.events.SequenceStartEvent)):depth+=1
   if depth>4:raise StreamConfigError('Depth budget')
   if isinstance(event,(yaml.events.MappingEndEvent,yaml.events.SequenceEndEvent)):depth-=1
  data=yaml.load(text,Loader=StrictLoader)
  if type(data) is not dict or set(data)!={'streams'} or type(data['streams']) is not list or len(data['streams'])>20:raise StreamConfigError('Exact bounded stream envelope required')
  rows=[];names=set();row_index=None
  for row_index,row in enumerate(data['streams'],1):
   if type(row) is not dict or set(row)-{'name','country','type','video_id','channel_id'} or any(type(v) is not str or len(v)>200 for v in row.values()):raise StreamConfigError('Exact scalar stream fields required')
   item=enrich(row);key=name_key(item['name'])
   if key in names:raise StreamConfigError('Duplicate names')
   names.add(key);rows.append(item)
  return {'observed_at':observed_at.astimezone(timezone.utc).isoformat(),'items':rows,'sha256':hashlib.sha256(raw).hexdigest(),'scope':'supplied_original_configuration','availability':'not_checked','persistence':False}
 except (ValueError,UnicodeError,OverflowError,yaml.YAMLError,RecursionError):
  index=locals().get('row_index')
  raise StreamConfigError('Invalid stream configuration snapshot'+(' at row '+str(index) if index is not None else '')) from None
