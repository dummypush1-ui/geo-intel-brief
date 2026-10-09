import unittest,re,json
from unittest.mock import patch
from pathlib import Path
import bcrypt
from integration.preview_access import PreviewAccess
class Bcrypt(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.encoded=bcrypt.hashpw(b'fixture-only-password',bcrypt.gensalt(rounds=10)).decode()
 def make(self):
  self.access=PreviewAccess('https://preview.example',self.encoded);self.c=self.access.build('fixture-only-session-key-'+'a'*48).test_client();return re.search(r'name="csrf" value="([^"]+)"',self.c.get('/login',base_url='https://preview.example').text)[1]
 def post(self,token,pw):return self.c.post('/login',base_url='https://preview.example',headers={'Origin':'https://preview.example'},data={'csrf':token,'password':pw})
 def test_actual_login_wrong_correct_cookies(self):
  t=self.make();self.assertEqual(self.post(t,'wrong').status_code,401);r=self.post(t,'fixture-only-password');self.assertEqual(r.status_code,303)
  for v in ['Secure','HttpOnly','SameSite=Strict']:self.assertIn(v,r.headers['Set-Cookie'])
 def test_byte_limits_no_reservation_and_no_truncation(self):
  t=self.make()
  for pw in ['a'*73,'தமிழ்'*10,'']:
   self.assertEqual(self.post(t,pw).status_code,400)
  self.assertEqual(self.access.attempts,[])
  with patch('bcrypt.checkpw',return_value=False)as check:
   self.assertEqual(self.post(t,'a'*72).status_code,401);self.assertEqual(len(check.call_args[0][0]),72)
 def test_closed_format_cost_and_version_startup_no_hash(self):
  with patch('bcrypt.checkpw',side_effect=AssertionError('startup hash')):
   PreviewAccess('https://preview.example',self.encoded)
  for h in [self.encoded.replace('$10$','$09$'),self.encoded.replace('$10$','$15$'),self.encoded.replace('$2b$','$2a$'),self.encoded+'x',self.encoded[:28]+'A'+self.encoded[29:]]:
   with self.assertRaises(ValueError):PreviewAccess('https://preview.example',h)
  with patch('bcrypt.__version__','wrong'):
   with self.assertRaises(ValueError):PreviewAccess('https://preview.example',self.encoded)
 def test_failure_fixed_and_limiter_slot_released(self):
  t=self.make()
  with patch('bcrypt.checkpw',side_effect=ValueError('SECRET')):
   r=self.post(t,'fixture');self.assertEqual(r.status_code,503);self.assertNotIn('SECRET',r.text)
  self.assertEqual(self.post(t,'fixture-only-password').status_code,303)
 def test_dependency_pin_receipt_scope(self):
  d=json.loads(Path('integration/bcrypt189/dependency.json').read_text());self.assertEqual(bcrypt.__version__,d['version']);self.assertEqual(d['audit']['dependencies'][0]['vulns'],[]);self.assertEqual(d['license'],'Apache-2.0');self.assertIn('bcrypt==5.0.0',Path('requirements-staging.txt').read_text())
