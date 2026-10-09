"""Closed read-route input shapes. Validate after auth, before reader access."""
from urllib.parse import unquote_to_bytes
from integration.api_v1 import READ_ALIASES,versioned
NEWS={'project':5,'q':200,'category':100,'country':100,'sort':20}
SHAPES={
 '/api/news':NEWS,'/api/news-export.csv':NEWS,'/api/sample-volume':NEWS,
 '/api/news-page':{**NEWS,'limit':3,'cursor':256},
 '/api/news-stats':{'project':5},'/api/dashboard-signals':{'project':5},
 '/api/dashboard-snapshots':{'project':5},'/api/country-page':{'project':5,'country':100},
 '/api/country-signals':{'country':100},'/api/tariff-evidence':{'jurisdiction':2},
 '/api/weekly-report.pdf':{'start':10,'end':10},
 '/api/source-health':{},'/api/critical-stories':{},'/api/map-data':{},'/api/story-groups':{},
}
SHAPES.update({versioned(p):SHAPES[p]for p in READ_ALIASES})
def valid(path,args,raw):
 if path not in SHAPES:return True
 shape=SHAPES[path]
 if len(raw)>2048 or set(args)-set(shape):return False
 try:unquote_to_bytes(raw).decode('utf-8','strict')
 except UnicodeError:return False
 for k,values in args.lists():
  if len(values)!=1:return False
  v=values[0]
  if len(v)>shape[k] or any(ord(c)<32 or ord(c)==127 for c in v):return False
  try:v.encode('utf-8','strict')
  except UnicodeError:return False
 return True
