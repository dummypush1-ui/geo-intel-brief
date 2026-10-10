"""27c executor-discovery preparation; Docker/CP312 NOT RUN; 27/28/29 OPEN"""
import unittest,pathlib,sys,json
from unittest.mock import patch
import prepare as p
ROOT=pathlib.Path(sys.argv[1]).resolve();sys.argv=sys.argv[:1]
class Tests(unittest.TestCase):
 def test_default_no_sideeffects(self):
  with patch('subprocess.run')as sub,patch('socket.socket')as sock,patch.object(pathlib.Path,'write_text')as write,patch.object(pathlib.Path,'read_text')as read:
   self.assertEqual(p.dispatch([])['state'],'NOT RUN');sub.assert_not_called();sock.assert_not_called();write.assert_not_called();read.assert_not_called()
 def test_gateoff_stagea(self):
  with patch('subprocess.run')as sub,patch('socket.socket')as sock:
   self.assertEqual(p.dispatch(['--stage','A'])['state'],'NOT RUN');sub.assert_not_called();sock.assert_not_called()
 def test_wrongstage(self):self.assertEqual(p.dispatch(['--stage','wrong'])['state'],'REFUSED')
 def test_unknown_args(self):self.assertEqual(p.dispatch(['--unknown','yes'])['state'],'REFUSED')
 def test_stageB_noanchor(self):self.assertEqual(p.dispatch(['--stage','B','--gate','on'])['state'],'REFUSED')
 def test_stageB_claimedanchor_noexecutor(self):self.assertEqual(p.dispatch(['--stage','B','--gate','on','--stage-a-anchor','untrusted.json'])['state'],'REFUSED')
 def test_gateon_still_notexecuted(self):
  with patch('subprocess.run')as sub,patch('socket.socket')as sock:
   self.assertEqual(p.dispatch(['--stage','A','--gate','on','--source',str(ROOT)])['state'],'NOT RUN');sub.assert_not_called();sock.assert_not_called()
 def test_execute_function_refused(self):
  with patch('subprocess.run')as sub:
   with self.assertRaises(p.Refused):p.execute_reviewed(['docker'],None)
   sub.assert_not_called()
 def test_source_drift(self):self.assertEqual(p.dispatch(['--stage','A','--gate','on','--source','/missing'])['state'],'REFUSED')
 def test_fixture_identical(self):
  expected=[{'package':'fixture','version':'2'}];out=p.compare(expected,expected);self.assertEqual(out['outcome'],'MATCH');self.assertFalse(out['install_permitted'])
 def test_fixture_added(self):self.assertEqual(p.compare([{'package':'fixture','version':'2'}],[{'package':'fixture','version':'2'},{'package':'extra','version':'1'}])['outcome'],'STOP')
 def test_fixture_version_skew(self):self.assertEqual(p.compare([{'package':'fixture','version':'2'}],[{'package':'fixture','version':'3'}])['changed'],['fixture'])
 def test_fixture_downgrade(self):self.assertEqual(p.compare([{'package':'fixture','version':'2'}],[{'package':'fixture','version':'1'}])['outcome'],'STOP')
 def test_fixture_removed(self):self.assertEqual(p.compare([{'package':'fixture','version':'2'}],[])['outcome'],'STOP')
if __name__=='__main__':unittest.main()
