"""Explicit TLS/port contract. No credentials, connection or send on import."""
import math
class SMTPPolicyRefused(ValueError):pass

def transport_plan(profile, mode, port, timeout=30):
 if profile not in ('geo','brics') or type(profile)is not str:
  raise SMTPPolicyRefused('Explicit mail profile required')
 if type(mode)is not str or mode not in ('implicit_tls','starttls') or type(port)is not int:
  raise SMTPPolicyRefused('Explicit TLS mode and integer port required')
 if (mode,port) not in (('implicit_tls',465),('starttls',587)):
  raise SMTPPolicyRefused('Reviewed TLS mode/port pair required')
 if type(timeout)not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30:
  raise SMTPPolicyRefused('Bounded SMTP timeout required')
 return {'profile':profile,'mode':mode,'port':port,'timeout':timeout,
         'tls_hostname_verified':True,'plaintext_fallback':False,'selected_sendpath':'AppsScript_not_replaced',
         'runtime_activation':False}
