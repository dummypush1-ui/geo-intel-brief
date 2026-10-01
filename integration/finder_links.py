"""Use a verified finder index mapping, never fabricate a code destination."""
from urllib.parse import urlsplit

def finder_link(base,system_index,entry_index,verified=False):
 u=urlsplit(base)
 if u.scheme not in ('https','http') or not u.hostname or u.query or u.fragment or u.username or u.password:raise ValueError('Verified finder base URL required')
 if not verified:return None
 for n in (system_index,entry_index):
  if not isinstance(n,int) or isinstance(n,bool) or n<0:raise ValueError('Invalid finder index')
 return base.rstrip('/')+('' if u.path.endswith('.html') else '/')+'#code='+str(system_index)+':'+str(entry_index)
