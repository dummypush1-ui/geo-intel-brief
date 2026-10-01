"""Compose original project report builders without importing live launchers.

Factories are injected after store mappings/configuration have been reviewed.
No generic formatter replaces the original Geo/BRICS report selection rules.
"""
from html import escape
from integration.html_safety import sanitize_html
PROJECTS=('finder','geo','brics')
def combined_reports(builders):
 if set(builders)!=set(PROJECTS):raise ValueError('Three explicit report builders required')
 blocks=[];ids={};id_types={};critical=0
 for project in PROJECTS:
  result=builders[project]()
  if not isinstance(result,dict) or not isinstance(result.get('ids'),list):raise ValueError('Report requires IDs list')
  html=result.get('html') or ''
  if not isinstance(html,str):raise ValueError('HTML must be a string')
  html=sanitize_html(html)
  id_types[project]=[]
  for identity in result['ids']:
   kind='objectid' if type(identity).__module__=='bson.objectid' and type(identity).__name__=='ObjectId' else 'str' if isinstance(identity,str) else None
   if kind is None:raise ValueError('Unsupported original ID type')
   id_types[project].append({'value':str(identity),'type':kind})
  ids[project]=list(dict.fromkeys(str(x) for x in result['ids']))
  if any(not x for x in ids[project]):raise ValueError('Empty original ID')
  blocks.append(f'<section data-project="{escape(project)}"><h2>{project.upper()}</h2>{html}</section>')
  critical+=int(result.get('critical_count',0))
 return {'html':'\n'.join(blocks),'project_ids':ids,'project_id_types':id_types,'critical_count':critical,'delivery_path':'apps_script'}
def original_ids(payload,project):
 entries=payload.get('project_id_types',{}).get(project)
 if entries is None:raise ValueError('Original ID types required')
 result=[]
 for entry in entries:
  if entry['type']=='str':result.append(entry['value'])
  elif entry['type']=='objectid' and project=='geo':
   from bson import ObjectId
   result.append(ObjectId(entry['value']))
  else:raise ValueError('Unsupported project ID type')
 if list(dict.fromkeys(str(i) for i in result))!=payload['project_ids'][project]:raise ValueError('ID metadata mismatch')
 return result
