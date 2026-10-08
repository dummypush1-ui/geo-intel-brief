import unittest,subprocess,sys
from unittest.mock import patch
from datetime import datetime,timezone
from integration.feedparser_audit.runner import *
D=datetime(2026,1,2,12,tzinfo=timezone.utc)
class Tests(unittest.TestCase):
 def run_case(self,case='rss'):return run_fixed_parser(case,cutoff=D.replace(day=1),fallback_clock=D)
 def test_corpus_real_parser_bozo_oracle(self):
  for case in CASES:
   r=self.run_case(case);self.assertTrue(r['oracle_equal']);self.assertEqual(r['network_guard_checks'],3);self.assertFalse(r['network'])
  self.assertTrue(self.run_case('broken_entries')['bozo']);self.assertFalse(self.run_case('broken_entries')['candidates']);self.assertTrue(self.run_case('broken_empty')['bozo']);self.assertFalse(self.run_case('broken_empty')['candidates'])
 def test_atom_rss_presence_values(self):
  r=self.run_case('atom');self.assertIn('தமிழ்',r['candidates'][0]['title']);self.assertIn('summary',r['field_presence'][0]);self.assertEqual(r['candidates'][0]['summary'],'Trade content')
  r=self.run_case('empty_dates');self.assertEqual(r['candidates'],[])
 def test_invalid_no_spawn_hooks(self):
  class Text(str):
   def __hash__(self):raise AssertionError('hook')
  with patch('integration.feedparser_audit.runner.subprocess.Popen',side_effect=AssertionError('spawn')):
   for case in (Text('rss'),'unknown',b'rss',None):
    with self.assertRaises(ParserRefused):self.run_case(case)
   with self.assertRaises(ParserRefused):run_fixed_parser('rss',cutoff=D,fallback_clock=D,max_items=True)
 def test_drift_before_spawn(self):
  with patch.dict(FILE_PINS,{'corpus.py':'0'*64}),patch('integration.feedparser_audit.runner.subprocess.Popen',side_effect=AssertionError('spawn')):
   with self.assertRaises(ParserRefused):self.run_case()
 def fault(self,script,clock=None):
  # Trusted test-only process fault; never caller-controllable runtime argv.
  real=subprocess.Popen;children=[]
  def spawn(*a,**k):
   p=real([sys.executable,'-c',script],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);children.append(p);return p
  with patch('integration.feedparser_audit.runner.subprocess.Popen',side_effect=spawn):
   if clock:
    with patch('integration.feedparser_audit.runner.time.monotonic',side_effect=clock):
     with self.assertRaises(ParserRefused):self.run_case()
   else:
    with self.assertRaises(ParserRefused):self.run_case()
  self.assertTrue(all(p.poll() is not None for p in children))
 def test_crash_and_protocol_kill_reap(self):
  self.fault('import sys;sys.stdin.read();sys.exit(1)');self.fault('import sys;sys.stdin.read();print("bad")')
 def test_output_overflow_kill_reap(self):self.fault('import sys;sys.stdin.read();sys.stdout.write("x"*1100000);sys.stdout.flush()')
 def test_timeout_kill_reap(self):self.fault('import sys,time;sys.stdin.read();time.sleep(30)',clock=[0,11])
