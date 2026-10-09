"""Bounded Linux child runner; fixed corpus/config only, no arbitrary commands."""
import sys,os,json,subprocess,selectors,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
from integration.supplied_feed_fixture import _date,FeedRefused
BASE=Path(__file__).parent;ROOT=BASE.parents[1]
from integration.supplied_fulltext_fixture import Budget,FulltextRefused
FILE_PINS={'child.py': '8ed514e89f64f6d5f24b5133a965081b6638a042d27d24b8776040605c188fed', 'corpus.py': 'e7158b210f562b68ecd74bb79d26549779a80ff539c08e3409b5d7177ae9af5e', 'corpus-pins.json': 'e91ac2743f799cd59e9fcc663fcf75577cfa95bdf883081f1010104094fd1303', 'sdk-pins.json': '9ba077de033c7f86ab15f4608e93f8a012b89a30500c91b64b5dbdc92d71ea58'}
class ParserRefused(ValueError):pass
CASES=frozenset(('rss','atom','empty','broken_entries','broken_empty','internal_entity','empty_dates'))
def run_fixed_parser(case,*,cutoff,fallback_clock,max_items=50):
 if type(case) is not str or case not in CASES or type(max_items) is not int or not 1<=max_items<=100:raise ParserRefused('fixed case/config required')
 for d in (cutoff,fallback_clock):
  if type(d) is not datetime or type(d.tzinfo) is not timezone:raise ParserRefused('fixed clock required')
  try:_date(d)
  except FeedRefused:raise ParserRefused('date boundary') from None
 if sys.platform!='linux':raise ParserRefused('Linux resource controls required')
 for name,h in FILE_PINS.items():
  if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=h:raise ParserRefused('reviewed fixture drift')
 q={'case':case,'cutoff':cutoff.isoformat(),'clock':fallback_clock.isoformat(),'max_items':max_items};wire=json.dumps(q).encode();assert len(wire)<=16384
 p=subprocess.Popen([sys.executable,str(BASE/'child.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','PYTHONPATH':str(ROOT)},start_new_session=True)
 chunks={p.stdout:bytearray(),p.stderr:bytearray()};sel=selectors.DefaultSelector();total=0;deadline=time.monotonic()+10
 try:
  p.stdin.write(wire);p.stdin.close()
  for f in chunks:os.set_blocking(f.fileno(),False);sel.register(f,selectors.EVENT_READ)
  while sel.get_map():
   remaining=deadline-time.monotonic()
   if remaining<=0:raise ParserRefused('child timeout')
   for key,_ in sel.select(min(remaining,.1)):
    b=os.read(key.fileobj.fileno(),65536)
    if not b:sel.unregister(key.fileobj);continue
    total+=len(b)
    if total>1048576:raise ParserRefused('child output overflow')
    chunks[key.fileobj].extend(b)
  p.wait(timeout=max(.001,deadline-time.monotonic()))
  if p.returncode!=0 or chunks[p.stderr]:raise ParserRefused('child refused')
  try:r=json.loads(chunks[p.stdout])
  except (ValueError,UnicodeError):raise ParserRefused('child protocol refused') from None
  pins=json.loads((BASE/'corpus-pins.json').read_text())
  if type(r) is not dict or r.get('case')!=case or r.get('config_echo')!=q or r.get('corpus_hash')!=pins[case] or r.get('feedparser_version')!='6.0.11' or r.get('oracle_equal') is not True:raise ParserRefused('child protocol refused')
  expected={'scope','case','corpus_hash','config_echo','feedparser_version','backend','bozo','bozo_label','field_presence','candidates','entry_count','oracle_equal','network_guard_checks','network','writes','delivery'}
  if set(r)!=expected or type(r['bozo']) is not bool or type(r['entry_count']) is not int or not 0<=r['entry_count']<=100 or type(r['candidates']) is not list or len(r['candidates'])>100 or type(r['field_presence']) is not list or len(r['field_presence'])!=r['entry_count'] or r['network'] is not False or r['writes'] is not False or r['delivery'] is not False or r['network_guard_checks']!=3:raise ParserRefused('child protocol shape')
  for row in r['candidates']:
   if type(row) is not dict or set(row)!={'title','url','source','credibility','summary','published'} or any(type(v) is not str or len(v)>10000 for v in row.values()):raise ParserRefused('child candidate shape')
   try:_date(datetime.fromisoformat(row['published']))
   except (ValueError,TypeError):raise ParserRefused('child candidate date') from None
  try:Budget().take(r)
  except FulltextRefused:raise ParserRefused('child protocol budget') from None
  return r
 except (subprocess.TimeoutExpired,OSError):raise ParserRefused('child execution refused') from None
 finally:
  if p.poll() is None:p.kill()
  p.wait();sel.close()
  for f in chunks:f.close()
