"""Use a verified finder index mapping, never fabricate a code destination."""
from urllib.parse import urlsplit
import re

def finder_link(base,system_index,code,verified=False):
 u=urlsplit(base)
 if u.scheme not in ('https','http') or not u.hostname or u.query or u.fragment or u.username or u.password:raise ValueError('Verified finder base URL required')
 if not verified:return None
 if type(system_index) is not int or system_index<0:raise ValueError('Invalid finder system')
 if not isinstance(code,str) or not re.fullmatch(r'\d{2,12}',code):raise ValueError('Exact Finder code string required')
 return base.rstrip('/')+('' if u.path.endswith('.html') else '/')+'#code='+str(system_index)+':'+str(code)
