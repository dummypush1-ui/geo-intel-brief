import unittest,hashlib,ast
from pathlib import Path
from datetime import datetime,timezone
from integration.stream_revision import revise,RevisionError
from integration.stream_config import configured_streams
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
RAW=b'# fixture comments\nstreams:\n- name: Original\n  country: India\n  type: video\n  video_id: abcdefghijk\n'
def call(raw=RAW,op='add',fields=None,expected=None):return revise(raw,hashlib.sha256(raw).hexdigest() if expected is None else expected,op,fields or {'name':'Tamil','country':'India','link':'https://youtu.be/12345678901'},NOW)
class StreamRevisionTests(unittest.TestCase):
 def test_append_roundtrip_deterministic_closed_fields(self):
  a=call();b=call();self.assertEqual(a['bytes'],b['bytes']);self.assertTrue(a['comment_format_loss']);self.assertFalse(a['persistence'])
  rows=configured_streams(a['bytes'],NOW)['items'];self.assertEqual([r['name'] for r in rows],['Original','Tamil'])
  self.assertNotIn(b'watch_url',a['bytes']);self.assertNotIn(b'embed_url',a['bytes'])
 def test_noop_exactbytes_and_revision_check(self):
  r=call(op='remove',fields={'name':'absent'});self.assertEqual(r['bytes'],RAW);self.assertFalse(r['comment_format_loss'])
  for h in ('a'*64,'A'*64,'short'):
   with self.assertRaises(RevisionError):call(op='remove',fields={'name':'absent'},expected=h)
 def test_remove_casefold_deviation_and_duplicate_refusal(self):
  raw=RAW.replace(b'Original',b'Strasse')
  self.assertTrue(call(raw,op='remove',fields={'name':'STRASSE'})['changed'])
  raw=raw.replace(b'Strasse','Straße'.encode())
  self.assertNotEqual('Straße'.lower(),'STRASSE'.lower())
  self.assertTrue(call(raw,op='remove',fields={'name':'STRASSE'})['changed'])
  duplicate=RAW+RAW.split(b'streams:\n')[1]
  with self.assertRaises(RevisionError):call(duplicate)
 def test_strict_inputs_fixed_error_no_echo(self):
  for raw in (b'\xef\xbb\xbf'+RAW,RAW+b'\x00',b'\xff',b'x'*16385,b'streams: []\n---\nstreams: []',b'streams: &x []',b'streams: []\nstreams: []',b'unknown: []',b'streams: !custom []',b'streams: [{name: 12}]'):
   with self.assertRaisesRegex(RevisionError,'^Invalid stream revision request$'):call(raw)
  with self.assertRaisesRegex(RevisionError,'^Invalid stream revision request$'):call(fields={'name':'SECRET','country':'India','link':'invalidSECRET'})
 def test_original_five_rows_semantics(self):
  raw=Path('intelligence/brics/config/streams.yaml').read_bytes()
  before=configured_streams(raw,NOW)['items'];result=call(raw)
  self.assertEqual(configured_streams(result['bytes'],NOW)['items'][:-1],before)
 def test_import_guard_no_fs_net_env(self):
  tree=ast.parse(Path('integration/stream_revision.py').read_text())
  modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
  self.assertFalse(any(m in ('os','pathlib','requests','socket','pymongo') for m in modules))

 def test_turkish_case_and_casefold_collision_policy(self):
  raw=RAW.replace(b'Original','İ'.encode())
  self.assertEqual('İ'.lower(),'i\u0307');self.assertEqual('İ'.casefold(),'i\u0307')
  # Label combining sequence accepted; same original lower behavior for this case.
  self.assertTrue(call(raw,op='remove',fields={'name':'i\u0307'})['changed'])
  collision=RAW.replace(b'Original','Straße'.encode())+RAW.split(b'streams:\n')[1].replace(b'Original',b'STRASSE')
  with self.assertRaises(RevisionError):call(collision,op='remove',fields={'name':'STRASSE'})
 def test_no_original_writer_import_or_call(self):
  source=Path('integration/stream_revision.py').read_text();tree=ast.parse(source)
  self.assertNotIn('_write_raw_streams',source)
  self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='intelligence.brics.video' for n in ast.walk(tree)))

 def test_parser_budgets_merge_keys_and_row_cap(self):
  for raw in (b'streams: [[[[[[]]]]]]',b'streams: []\n'+b'# line\n'*3000+b'x: ['+b'1,'*1200+b']',b'streams: [{<<: {name: Bad}}]',b'streams: [{12: value}]',b'streams: &a [*a]'):
   with self.assertRaises(RevisionError):call(raw)
  rows=[]
  for n in range(21):rows.append({'name':'fixture'+str(n),'country':'India','type':'video','video_id':'abcdefghijk'})
  import yaml
  with self.assertRaises(RevisionError):call(yaml.safe_dump({'streams':rows}).encode())
 def test_hash_edge_and_normalization(self):
  for h in ('0'*63,'0'*65,'g'*64,'0'*63+'\n',b'0'*64):
   with self.assertRaises(RevisionError):call(expected=h)
  raw=RAW.replace(b'name: Original',b'name: " Original "').replace(b'country: India',b'country: ""').replace(b'video_id: abcdefghijk',b'video_id: https://youtu.be/abcdefghijk\n  channel_id: stray')
  result=call(raw);self.assertTrue(result['comment_format_loss'])
  self.assertNotIn(b'channel_id',result['bytes']);self.assertIn(b'country: Custom',result['bytes'])
 def test_transitive_ast_allowlist_and_banned_names(self):
  allowed={'hashlib','hmac','re','yaml','datetime','threading','unicodedata','urllib.parse','copy','integration.stream_config','integration.brics_streams','integration.youtube_links'}
  banned={'open','__import__','eval','exec','compile','subprocess','requests','socket','os','Path'}
  for file in ('integration/stream_revision.py','integration/stream_config.py','integration/brics_streams.py'):
   tree=ast.parse(Path(file).read_text())
   modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
   self.assertTrue(set(modules)<=allowed,(file,modules))
   self.assertFalse(any(isinstance(n,ast.Name) and n.id in banned for n in ast.walk(tree)),file)
   self.assertFalse(any(m=='intelligence.brics.video' or m.startswith(('os.','subprocess','urllib.request')) for m in modules))
