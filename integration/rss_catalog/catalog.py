"""Pure disabled-feed catalog validation. No requests, config writes or activation.

Copyright (c)2026 Push. Publisher research observations do not grant reuse rights.
"""
from copy import deepcopy
from urllib.parse import urlsplit,parse_qsl,urlunsplit
import re,unicodedata,ipaddress
from datetime import date
FIELDS={'id','publisher','feed_url','category_hint','country_hint','language_hint','discovery','captured_http_status','captured_item_count','captured_latest_date','robots_observation','candidate_validation','terms_state','enabled'}
ROOT_FIELDS={'schema_version','captured_date','network','activation','copyright_terms_verified','source','items'}

def validate_catalog(data):
 if type(data) is not dict or set(data)!=ROOT_FIELDS or type(data['schema_version']) is not int or data['schema_version']!=1 or data['network'] is not False or data['activation'] is not False or data['copyright_terms_verified'] is not False or data['source']!='independent_publisher_feed_inventory':raise ValueError('Disabled independent catalog required')
 if type(data['items']) is not list or len(data['items'])>1000:raise ValueError('Bounded candidates required')
 if type(data['captured_date']) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',data['captured_date']):raise ValueError('Capture date required')
 date.fromisoformat(data['captured_date'])
 seen=set();ids=set();out=deepcopy(data)
 for row in out['items']:
  if type(row) is not dict or set(row)!=FIELDS or row['enabled'] is not False or row['terms_state']!='unverified':raise ValueError('Disabled unknown-terms candidate required')
  for k in ('publisher','feed_url','category_hint','country_hint','language_hint','discovery','robots_observation','candidate_validation'):
   if type(row[k]) is not str or not row[k].strip() or len(row[k])>1000 or any(unicodedata.category(c)[0]=='C' for c in row[k]):raise ValueError('Bounded candidate strings required')
  if not row['publisher'].strip() or row['candidate_validation'] not in ('reachable_parseable','needs_review'):raise ValueError('Candidate status required')
  u=urlsplit(row['feed_url'])
  if u.scheme not in ('http','https') or not u.hostname or u.username is not None or u.password is not None or u.fragment or any(c.isspace() or c in '\\' for c in row['feed_url']):raise ValueError('Safe candidate feed URL required')
  try:port=u.port
  except ValueError:raise ValueError('Valid port required') from None
  if port is not None and not 1<=port<=65535:raise ValueError('Valid port required')
  host=u.hostname.lower()
  if host=='localhost' or host.endswith(('.localhost','.local','.internal','.lan')):raise ValueError('Public hostname required')
  query_keys={k.casefold().replace('-','_') for k,v in parse_qsl(u.query,keep_blank_values=True)}
  if any(k in ('token','password','passwd','pwd','api_key','apikey','key','secret','access_token','auth','authorization','signature','credential') or any(t in k for t in ('token','password','secret','credential')) for k in query_keys):raise ValueError('Credential-like query rejected')
  canonical_url=urlunsplit((u.scheme,host+(':'+str(port) if port else ''),u.path,u.query,''))
  try:address=ipaddress.ip_address(host)
  except ValueError:
   if not host.isascii() or len(host)>253 or not all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',part) for part in host.split('.')) or len(host.split('.'))<2:raise ValueError('ASCII DNS hostname required')
   if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*',host.split('.')[-1]) or any(part.lower().startswith('0x') for part in host.split('.')):raise ValueError('No numeric/shorthand host')
  else:
   if address.version==6 and (address in ipaddress.ip_network('::/96') or address in ipaddress.ip_network('64:ff9b::/96')):raise ValueError('Embedded IPv4 rejected')
   if not address.is_global:raise ValueError('Public IP literal required')
  if type(row['id']) is not str or not re.fullmatch('[0-9a-f]{16}',row['id']):raise ValueError('Candidate identity required')
  if canonical_url in seen or row['id'] in ids:raise ValueError('Duplicate candidate')
  seen.add(canonical_url);ids.add(row['id'])
  for k in ('captured_http_status','captured_item_count'):
   if row[k] is not None and (type(row[k]) is not int or row[k]<0 or row[k]>1000000):raise ValueError('Bounded historical observation required')
  if row['captured_http_status'] is not None and not 100<=row['captured_http_status']<=599:raise ValueError('HTTP status100-599 required')
  if row['captured_latest_date'] is not None:
   latest=row['captured_latest_date']
   if type(latest) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',latest):raise ValueError('ISO latest date required')
   date.fromisoformat(latest)
 return out
