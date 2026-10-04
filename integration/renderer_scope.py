"""Load allowlisted original renderer definitions without importing originals.

This is a capability-minimal renderer scope, not a hostile-code sandbox.
Only hash-pinned reviewed AST definitions and literal constants are compiled.
No config/database/email modules, source imports, or send helpers are executed.
"""
import ast
import hashlib
import html
import datetime
import symtable
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
# These pins cover entire original files. Changes need explicit re-review.
PINS = {'geo_digest': '4ecf02ce731c13fe1f7115edfc5edbf5b3aabe91db9a1d279645eda63b321b49', 'geo_critical': '2b7337883500bea2085fb8180599bcf5bd1e957f21757db3a2c5be311b39517f', 'geo_weekly': 'f09f7576c26e274f5b419ad13cbe9c962610cca0d553d8763b52ea48099694c3', 'brics_digest': '5aea6483892617f90b9905885e08d91fda2a3f644b02a10ee54e39ecfd2c90a8'}
SPECS={
 'geo_digest':('intelligence/geo/reports/email_report.py',('_group_articles','_section_html','build_digest'),('CATEGORY_LABELS','RISK_COLORS','MIN_SCORE')),
 'geo_critical':('intelligence/geo/reports/critical_alert.py',('build_html',),()),
 'geo_weekly':('intelligence/geo/reports/weekly_report.py',('build_html',),('CATEGORY_LABELS',)),
 'brics_digest':('intelligence/brics/reports/email_report.py',('build_digest',),()),
}
BUILTINS={'list':list,'dict':dict,'len':len,'sum':sum,'sorted':sorted,'str':str}

def renderer(kind,dependencies,now=None):
 path,names,constants=SPECS[kind]
 source=(ROOT/path).read_bytes()
 if hashlib.sha256(source).hexdigest()!=PINS[kind]:raise ValueError('Renderer requires review')
 tree=ast.parse(source,filename=path)
 body=[];values={}
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in names:
   if node.decorator_list or any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(node)):raise ValueError('Renderer dependency changed')
   body.append(node)
  elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in constants:
   values[node.targets[0].id]=ast.literal_eval(node.value)
 if {n.name for n in body}!=set(names) or set(values)!=set(constants):raise ValueError('Renderer definition missing')
 formats=('%d %B %Y','%d %b %Y','%d %b %Y | %H:%M')
 if now is None:now=datetime.datetime.now(datetime.timezone.utc)
 if type(now) is not datetime.datetime or type(now.tzinfo) is not datetime.timezone:raise ValueError('Fixed aware renderer clock required')
 now=now.astimezone(datetime.timezone.utc)
 date_text={fmt:now.strftime(fmt) for fmt in formats}
 clock=SimpleNamespace(strftime=lambda fmt:date_text[fmt])
 scope={'__builtins__':dict(BUILTINS),'html':SimpleNamespace(escape=html.escape),'defaultdict':defaultdict,
 'datetime':SimpleNamespace(now=lambda:clock),'UPCOMING_DAYS':90,
 'ACTIVE_CATEGORIES':['GEOPOLITICS','CONFERENCE','TRADE','SANCTIONS','RISK','RESEARCH','GENERAL'],
 'DASHBOARD_BASE_URL':'','TRIGGER_SECRET':''}
 if kind=='brics_digest':scope['datetime']=SimpleNamespace(date=SimpleNamespace(today=lambda:clock))
 allowed={'geo_digest':{'unemailed_articles','upcoming_events'},'geo_critical':set(),
 'geo_weekly':{'weekly_top_articles','category_counts','top_countries'},'brics_digest':{'load_streams'}}[kind]
 if set(dependencies)!=allowed or not all(callable(v) for v in dependencies.values()):raise ValueError('Exact renderer dependencies required')
 scope.update(values);scope.update(dependencies)
 module=ast.Module(body=body,type_ignores=[])
 checked_source=ast.unparse(module)
 symbols=symtable.symtable(checked_source,path,'exec')
 def global_refs(table):
  found={s.get_name() for s in table.get_symbols() if s.is_global() and s.is_referenced()}
  for child in table.get_children():found.update(global_refs(child))
  return found
 if not global_refs(symbols).issubset(set(scope)|set(BUILTINS)|set(names)):raise ValueError('Unsupported renderer global')
 exec(compile(ast.parse(checked_source),path,'exec'),scope)
 return scope['build_digest' if kind.endswith('digest') else 'build_html']
