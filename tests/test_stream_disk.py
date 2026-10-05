import unittest,tempfile,os,hashlib
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
from integration.stream_disk import DiskStreams,StreamDiskError,StreamDiskConflict,StreamDiskUncertain
RAW=b'streams: []\n';NOW=datetime(2026,1,1,tzinfo=timezone.utc)
FIELDS={'name':'Fixture','country':'India','link':'https://www.youtube.com/watch?v=abcdefghijk'}
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'streams.yaml';self.p.write_bytes(RAW);self.p.chmod(0o600);self.store=DiskStreams(str(self.p),verified_local=True)
 def tearDown(self):self.tmp.cleanup()
 def test_read_write_restart_and_permissions(self):
  before=self.store.read(NOW);r=self.store.update(before['sha256'],'add',FIELDS,NOW);self.assertTrue(r['changed']);self.assertEqual(self.p.stat().st_mode&0o777,0o600)
  self.assertEqual(DiskStreams(str(self.p),verified_local=True).read(NOW)['items'][0]['name'],'Fixture');self.assertEqual(r['sha256'],hashlib.sha256(self.p.read_bytes()).hexdigest())
 def test_stale_revision_no_mutation(self):
  self.store.update(hashlib.sha256(RAW).hexdigest(),'add',FIELDS,NOW);old=self.p.read_bytes()
  with self.assertRaises(StreamDiskConflict):self.store.update(hashlib.sha256(RAW).hexdigest(),'remove',{'name':'Fixture'},NOW)
  self.assertEqual(self.p.read_bytes(),old)
 def test_replace_failure_unchanged_temp_cleanup(self):
  with patch('integration.stream_disk.os.replace',side_effect=OSError('secretpath')):
   with self.assertRaises(StreamDiskError) as e:self.store.update(hashlib.sha256(RAW).hexdigest(),'add',FIELDS,NOW)
  self.assertIsNone(e.exception.__context__);self.assertEqual(self.p.read_bytes(),RAW);self.assertEqual(list(self.p.parent.glob('.streams.yaml.*')),[])
 def test_directory_fsync_failure_uncertain(self):
  real=os.fsync;count=[0]
  def sync(fd):
   count[0]+=1
   if count[0]==2:raise OSError('secretpath')
   real(fd)
  with patch('integration.stream_disk.os.fsync',side_effect=sync):
   with self.assertRaises(StreamDiskUncertain):self.store.update(hashlib.sha256(RAW).hexdigest(),'add',FIELDS,NOW)
  self.assertNotEqual(self.p.read_bytes(),RAW);self.assertEqual(self.store.read(NOW)['items'][0]['name'],'Fixture')
 def test_symlink_and_permissions_refused(self):
  link=self.p.parent/'link';link.symlink_to(self.p)
  with self.assertRaises(StreamDiskError):DiskStreams(str(link),verified_local=True).read(NOW)
  self.p.chmod(0o644)
  with self.assertRaises(StreamDiskError):self.store.read(NOW)
 def test_invalid_transform_unchanged(self):
  with self.assertRaises(StreamDiskError):self.store.update(hashlib.sha256(RAW).hexdigest(),'add',{'name':'broken'},NOW)
  self.assertEqual(self.p.read_bytes(),RAW)
 def test_busy_nonblocking(self):
  lock=self.store._lock()
  try:
   with self.assertRaises(StreamDiskError):self.store.update(hashlib.sha256(RAW).hexdigest(),'add',FIELDS,NOW)
  finally:os.close(lock)
 def test_noop_preserves_raw(self):
  r=self.store.update(hashlib.sha256(RAW).hexdigest(),'remove',{'name':'absent'},NOW);self.assertFalse(r['changed']);self.assertEqual(self.p.read_bytes(),RAW)
 def test_two_process_revision_race_exactly_one_commit(self):
  import multiprocessing
  context=multiprocessing.get_context('fork');start=context.Event();q=context.Queue();revision=hashlib.sha256(RAW).hexdigest()
  def worker(name):
   start.wait()
   try:
    DiskStreams(str(self.p),verified_local=True).update(revision,'add',dict(FIELDS,name=name),NOW);q.put('ok')
   except StreamDiskError:q.put('refused')
  workers=[context.Process(target=worker,args=(n,)) for n in ('One','Two')]
  for p in workers:p.start()
  start.set();outcomes=[q.get(timeout=5) for p in workers]
  for p in workers:p.join(5);self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted(outcomes),['ok','refused']);self.assertEqual(len(self.store.read(NOW)['items']),1)

 def test_control_exception_after_replace_is_uncertain(self):
  real=os.fsync;count=[0]
  def sync(fd):
   count[0]+=1
   if count[0]==2:raise KeyboardInterrupt()
   real(fd)
  with patch('integration.stream_disk.os.fsync',side_effect=sync):
   with self.assertRaises(StreamDiskUncertain):self.store.update(hashlib.sha256(RAW).hexdigest(),'add',FIELDS,NOW)
  self.assertNotEqual(self.p.read_bytes(),RAW)
