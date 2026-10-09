"""Compatibility seam for original selection; no requests or in-process XML parser.
Explicit installation only. Transport and parser are fixed reviewed processes.
One response handle owns a single parsed projection; never accepts an arbitrary
URL as parser input. No fallback if isolation/source verification fails.
"""
import hashlib,math,time
from collector113_prep.transport_policy import endpoint_plan
from collector124_prep.runner import run_fetch
from collector128_prep.parser_runner import parse_supplied_bytes

class RSSRefused(ValueError):pass
class ParsedHandle:
 def __init__(self,owner,entries,deadline):
  self._owner=owner;self.entries=entries;self._deadline=deadline;self._used=False
 @property
 def content(self):return self
 def raise_for_status(self):
  if time.monotonic()>=self._deadline:raise RSSRefused('RSS deadline')

class BoundedRSSDriver:
 def __init__(self,feeds,*,enabled=False,projection_limit=40):
  if type(enabled)is not bool or type(feeds)is not tuple or not 1<=len(feeds)<=64:raise RSSRefused('RSS installation shape')
  if type(projection_limit)is not int or not 1<=projection_limit<=200:raise RSSRefused('RSS projection cap')
  for spec in feeds:
   if type(spec)is not tuple or len(spec)!=3 or any(type(v)is not str or not v.strip() or len(v)>2000 for v in spec):raise RSSRefused('RSS source shape')
   endpoint_plan(feeds,spec[1],('8.8.8.8',),'8.8.8.8')
  if len({f[1]for f in feeds})!=len(feeds):raise RSSRefused('RSS duplicate source')
  self._feeds=feeds;self._enabled=enabled;self._projection=projection_limit
 def get(self,url,*,timeout,headers):
  if not self._enabled:raise RSSRefused('RSS installation held')
  if type(timeout)not in(int,float) or not math.isfinite(timeout) or not 0<timeout<=30:raise RSSRefused('RSS timeout')
  if type(headers)is not dict or set(headers)!={'User-Agent'} or type(headers['User-Agent'])is not str or len(headers['User-Agent'])>200:raise RSSRefused('RSS header contract')
  if type(url)is not str or url not in {f[1]for f in self._feeds}:raise RSSRefused('RSS source not installed')
  deadline=time.monotonic()+min(25,timeout)
  try:
   fetched=run_fetch(self._feeds,url,timeout=min(25,timeout))
   keys={'bytes','input_sha256','wire_bytes','url','peer','tls_hostname_verified','delivery'}
   if type(fetched)is not dict or set(fetched)!=keys or fetched['url']!=url or fetched['tls_hostname_verified']is not True or fetched['delivery']is not False:raise RSSRefused('RSS fetch protocol')
   blob=fetched['bytes']
   if type(blob)is not bytes or not 1<=len(blob)<=1048576 or fetched['input_sha256']!=hashlib.sha256(blob).hexdigest() or type(fetched['wire_bytes'])is not int or not 1<=fetched['wire_bytes']<=1048576:raise RSSRefused('RSS bytes protocol')
   endpoint_plan(self._feeds,url,(fetched['peer'],),fetched['peer'])
   remaining=deadline-time.monotonic()
   if remaining<=0:raise RSSRefused('RSS deadline')
   parsed=parse_supplied_bytes(blob,timeout=min(10,remaining),projection_limit=self._projection)
   if parsed['bozo']:raise RSSRefused('RSS malformed document')
   if time.monotonic()>=deadline:raise RSSRefused('RSS deadline')
   return ParsedHandle(self,parsed['entries'],deadline)
  except Exception:raise RSSRefused('RSS source refused')from None
 def parse(self,handle):
  if type(handle)is not ParsedHandle or handle._owner is not self or handle._used:raise RSSRefused('RSS opaque handle')
  handle.raise_for_status();handle._used=True;return handle
