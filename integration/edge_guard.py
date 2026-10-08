"""Edge guard for public routes: rate limit, input validation, honeypot paths.

Additive Flask middleware. Installed once by an entrypoint; it never changes
route handlers. State is in memory and per process (each gunicorn worker keeps
its own counters), so limits are per worker. No network, disk or database use.
"""
import logging
import re
import time
from urllib.parse import unquote_to_bytes
from collections import OrderedDict
from threading import Lock
from flask import jsonify, request

HONEYPOT_PATHS = frozenset((
 '/.env', '/.git/config', '/.git/head', '/wp-login.php', '/wp-admin', '/xmlrpc.php',
 '/phpmyadmin', '/pma', '/admin.php', '/administrator', '/cgi-bin/', '/vendor/phpunit',
 '/actuator/env', '/server-status', '/config.json', '/backup.zip', '/db.sql'))
EXEMPT_PATHS = frozenset(('/health',))
ALLOWED_METHODS = frozenset(('GET', 'HEAD', 'POST', 'OPTIONS', 'DELETE'))
_CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

DEFAULTS = {
 'rate_limit': 120,        # requests per window per client
 'window_seconds': 60.0,
 'ban_seconds': 900.0,     # honeypot or flood ban length
 'max_clients': 10000,     # bound on tracked clients
 'max_path': 512,
 'max_query_string': 2048,
 'max_args': 20,
 'max_value': 512,
 'max_body': 65536,
 'honeypot_strikes': 3,    # honeypot hits before a ban (a page can make a visitor hit one)
}


def client_ip(req, trusted_hops=1):
 """Client address. Behind one trusted proxy (Render) use the last XFF entry
 the proxy appended; a client-supplied left side is never trusted."""
 xff = req.headers.get('X-Forwarded-For', '')
 parts = [p.strip() for p in xff.split(',') if p.strip()]
 if trusted_hops > 0 and len(parts) >= trusted_hops:
  return parts[-trusted_hops][:64]
 return (req.remote_addr or 'unknown')[:64]


class EdgeGuard:
 def __init__(self, clock=time.monotonic, trusted_hops=1, **limits):
  unknown = set(limits) - set(DEFAULTS)
  if unknown:raise ValueError('Unknown edge guard limit')
  self.cfg = {**DEFAULTS, **limits}
  for k, v in self.cfg.items():
   if type(v) not in (int, float) or isinstance(v, bool) or v <= 0:raise ValueError('Positive edge guard limits required')
  self.clock = clock
  self.trusted_hops = trusted_hops
  self._lock = Lock()
  self._hits = OrderedDict()   # ip -> (window_start, count)
  self._bans = OrderedDict()   # ip -> ban_until
  self._strikes = OrderedDict()  # ip -> (first_strike_time, count)

 def _banned(self, ip, now):
  until = self._bans.get(ip)
  if until is None:return False
  if now >= until:
   del self._bans[ip];return False
  return True

 def ban(self, ip):
  with self._lock:
   self._bans[ip] = self.clock() + self.cfg['ban_seconds']
   self._bans.move_to_end(ip)
   while len(self._bans) > self.cfg['max_clients']:self._bans.popitem(last=False)

 def strike(self, ip):
  """Record a honeypot hit. True once the client reached the strike limit."""
  now = self.clock()
  with self._lock:
   first, count = self._strikes.get(ip, (now, 0))
   if now - first >= self.cfg['ban_seconds']:first, count = now, 0
   count += 1
   self._strikes[ip] = (first, count)
   self._strikes.move_to_end(ip)
   while len(self._strikes) > self.cfg['max_clients']:self._strikes.popitem(last=False)
   return count >= self.cfg['honeypot_strikes']

 def allow_rate(self, ip):
  now = self.clock()
  with self._lock:
   if self._banned(ip, now):return False
   start, count = self._hits.get(ip, (now, 0))
   if now - start >= self.cfg['window_seconds']:start, count = now, 0
   count += 1
   self._hits[ip] = (start, count)
   self._hits.move_to_end(ip)
   while len(self._hits) > self.cfg['max_clients']:self._hits.popitem(last=False)
   return count <= self.cfg['rate_limit']

 def invalid(self, req):
  """Return a short reason string for malformed input, else None."""
  c = self.cfg
  if req.method not in ALLOWED_METHODS:return 'method'
  if len(req.path) > c['max_path'] or _CONTROL.search(req.path):return 'path'
  qs = req.query_string or b''
  if len(qs) > c['max_query_string']:return 'query'
  try:text = qs.decode('utf-8')
  except UnicodeDecodeError:return 'query'
  if _CONTROL.search(text):return 'query'
  try:unquote_to_bytes(text).decode('utf-8')
  except UnicodeDecodeError:return 'query'
  n = 0
  for key, vals in req.args.lists():
   for v in vals:
    n += 1
    if len(key) > 64 or len(v) > c['max_value'] or _CONTROL.search(key) or _CONTROL.search(v):return 'query'
  if n > c['max_args']:return 'query'
  length = req.content_length
  if length is not None and length > c['max_body']:return 'body'
  return None

 def check(self, req):
  """Return None to continue, or (reason, status) to reject."""
  path = req.path
  if path in EXEMPT_PATHS:return None
  ip = client_ip(req, self.trusted_hops)
  low = path.lower().rstrip('/') or '/'
  if low in HONEYPOT_PATHS or any(low.startswith(p.rstrip('/') + '/') for p in HONEYPOT_PATHS if p.endswith('/')):
   if self.strike(ip):self.ban(ip)
   return ('not found', 404)
  with self._lock:
   banned = self._banned(ip, self.clock())
  if banned:return ('rate limited', 429)
  if not self.allow_rate(ip):return ('rate limited', 429)
  reason = self.invalid(req)
  if reason:return ('invalid ' + reason, 413 if reason == 'body' else 400)
  return None


def install_edge_guard(app, guard=None, **limits):
 """Register the guard so it runs before every other before_request hook."""
 if getattr(app, '_edge_guard', None) is not None:raise ValueError('Edge guard already installed')
 guard = guard or EdgeGuard(**limits)
 def edge_guard():
  rejected = guard.check(request)
  if rejected is None:return None
  message, status = rejected
  response = jsonify(error=message)
  response.status_code = status
  if status == 429:response.headers['Retry-After'] = str(int(guard.cfg['window_seconds']))
  return response
 app.before_request_funcs.setdefault(None, []).insert(0, edge_guard)
 app._edge_guard = guard
 return app


def edge_limits_from_env(environ):
 """Return install limits from env, or None when the guard is not switched on.

 Off unless EDGE_GUARD_ENABLED is exactly true (any case, spaces ignored). An invalid
 EDGE_RATE_LIMIT keeps the default and logs a warning instead of failing boot.
 """
 if environ.get('EDGE_GUARD_ENABLED', 'false').strip().lower() != 'true':return None
 limits = {}
 raw = environ.get('EDGE_RATE_LIMIT', '').strip()
 if raw:
  if raw.isascii() and raw.isdigit() and 0 < int(raw) <= 1000000:limits['rate_limit'] = int(raw)
  else:logging.getLogger(__name__).warning('Ignoring invalid EDGE_RATE_LIMIT; using default %s', DEFAULTS['rate_limit'])
 return limits
