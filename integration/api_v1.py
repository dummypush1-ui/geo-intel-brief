"""Exact read-only v1 alias contract. Same handler, auth and payload as legacy.
No private endpoints, writes, redirect, argument rewriting or dynamic path map.
"""
READ_ALIASES=(
 '/api/news','/api/news-page','/api/news-stats','/api/dashboard-signals',
 '/api/dashboard-snapshots','/api/sample-volume','/api/critical-stories',
 '/api/source-health','/api/country-page','/api/country-signals','/api/map-data',
 '/api/story-groups','/api/news-export.csv',
)
def versioned(path):return '/api/v1/'+path.removeprefix('/api/')
def install(app):
 for index,path in enumerate(READ_ALIASES):
  rules=[r for r in app.url_map.iter_rules()if r.rule==path and 'GET'in r.methods]
  if len(rules)!=1:raise ValueError('Exact read alias target required')
  app.add_url_rule(versioned(path),endpoint='v1_read_'+str(index),view_func=app.view_functions[rules[0].endpoint],methods=['GET'])
