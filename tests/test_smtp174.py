import unittest
from unittest.mock import patch
from integration.smtp_policy import transport_plan,SMTPPolicyRefused
from integration.geonews_digest.delivery import smtp_sender,DeliveryError,DeliveryDisabled
class SMTP(unittest.TestCase):
 def sender(self,**kw):return smtp_sender(enabled=True,host='smtp.example.org',user='u',password='SECRET',mail_from='a@example.org',mail_to='b@example.org',**kw)
 def test_exact_profile_modes_and_invalid_combinations(self):
  for profile in ['geo','brics']:
   for mode,port in [('implicit_tls',465),('starttls',587)]:self.assertFalse(transport_plan(profile,mode,port)['plaintext_fallback'])
  for mode,port in [('none',25),('starttls',465),('implicit_tls',587),('starttls',True)]:
   with self.assertRaises(SMTPPolicyRefused):transport_plan('geo',mode,port)
 def test_implicit_tls465(self):
  with patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL') as ssl,patch('integration.geonews_digest.delivery.smtplib.SMTP') as plain:
   self.sender()('subject','body');ssl.assert_called_once();plain.assert_not_called();ssl.return_value.__enter__.return_value.starttls.assert_not_called()
 def test_starttls587_before_credentials(self):
  with patch('integration.geonews_digest.delivery.smtplib.SMTP') as plain,patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL') as ssl:
   self.sender(port=587,tls_mode='starttls',profile='brics')('subject','body');ssl.assert_not_called();s=plain.return_value.__enter__.return_value
   self.assertEqual([x[0] for x in s.method_calls],['ehlo','starttls','ehlo','login','sendmail'])
 def test_tls_failure_never_sends_or_exposes_secret(self):
  import smtplib
  with patch('integration.geonews_digest.delivery.smtplib.SMTP') as plain:
   s=plain.return_value.__enter__.return_value;s.starttls.side_effect=smtplib.SMTPException('SECRET')
   with self.assertRaises(DeliveryError) as e:self.sender(port=587,tls_mode='starttls')('s','b')
   self.assertNotIn('SECRET',str(e.exception));s.login.assert_not_called();s.sendmail.assert_not_called()
 def test_off_switch_before_connection(self):
  with patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL') as ssl:
   with self.assertRaises(DeliveryDisabled):smtp_sender(host='h',user='u',password='SECRET',mail_from='a@example.org',mail_to='b@example.org')
   ssl.assert_not_called()
