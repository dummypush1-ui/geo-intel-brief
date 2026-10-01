"""Add merged branding to served copies, never rewrite the preserved Finder."""
from html import escape
from urllib.parse import urlsplit
import re
from html.parser import HTMLParser
from pathlib import Path
TITLE='Geo Intel Brief'
DESCRIPTION='Trade-code finder with Geo and BRICS news context.'
ASSET_PATH='/workspace/branding/'
def valid_origin(value):
 if not value:return None
 u=urlsplit(value)
 if u.scheme!='https' or not u.hostname or u.username or u.password or u.path not in ('','/') or u.query or u.fragment or any(c.isspace() for c in value):raise ValueError('Verified HTTPS origin required')
 return value.rstrip('/')
class HeadTags(HTMLParser):
 def __init__(self,html):
  super().__init__(convert_charrefs=False);self.html=html;self.offsets=[0];self.remove=[]
  for m in re.finditer('\n',html):self.offsets.append(m.end())
 def handle_starttag(self,tag,attrs):
  data=dict(attrs);remove=False
  if tag=='meta':
   key=(data.get('property') or data.get('name') or '').lower()
   remove=key.startswith(('og:','twitter:')) or key=='robots'
  if tag=='link':
   rel=set((data.get('rel') or '').lower().split())
   remove=bool(rel & {'icon','shortcut','apple-touch-icon','apple-touch-icon-precomposed','mask-icon','manifest'})
  if remove:
   line,col=self.getpos();start=self.offsets[line-1]+col;self.remove.append((start,start+len(self.get_starttag_text())))
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
 def stripped(self):
  self.feed(self.html);out=self.html
  for a,b in reversed(self.remove):out=out[:a]+out[b:]
  return out
def brand_head(html,public_base=None):
 base=valid_origin(public_base)
 html=HeadTags(html).stripped()
 tags=[f'<link rel="icon" href="{ASSET_PATH}favicon.ico" sizes="16x16 32x32 48x48">',f'<link rel="icon" type="image/png" sizes="48x48" href="{ASSET_PATH}icon-48.png">',f'<link rel="apple-touch-icon" sizes="180x180" href="{ASSET_PATH}apple-touch-icon.png">','<link rel="manifest" href="/workspace/manifest.webmanifest" crossorigin="use-credentials">','<meta name="robots" content="noindex,nofollow">',f'<meta property="og:title" content="{TITLE}">',f'<meta property="og:description" content="{DESCRIPTION}">','<meta property="og:type" content="website">','<meta name="twitter:card" content="summary_large_image">',f'<meta name="twitter:title" content="{TITLE}">',f'<meta name="twitter:description" content="{DESCRIPTION}">']
 if base:
  image=escape(base+ASSET_PATH+'og-image.png',quote=True)
  tags.extend([f'<meta property="og:image" content="{image}">','<meta property="og:image:width" content="1200">','<meta property="og:image:height" content="630">',f'<meta name="twitter:image" content="{image}">'])
 return re.sub(r'</head\s*>',lambda m:'\n'.join(tags)+'\n'+m.group(0),html,count=1,flags=re.I)
