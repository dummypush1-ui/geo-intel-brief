"""Extra response security headers for the public app. Additive after_request.

news_api already sets Cache-Control, X-Robots-Tag, nosniff, Referrer-Policy and the
per-page Content-Security-Policy. This adds only what is missing and never replaces a
header another layer already set.
"""
from flask import request

# Initial max-age is one week on purpose: HSTS is sticky in browsers and the off switch
# cannot undo it. Raise it later once the https-only setup has proven stable.
HSTS = 'max-age=604800'  # 7 days; no includeSubDomains, no preload (hard to undo)
STATIC = (
 ('X-Frame-Options', 'SAMEORIGIN'),
 ('Permissions-Policy', 'geolocation=(), camera=(), microphone=(), payment=(), usb=(), interest-cohort=()'),
 ('Cross-Origin-Opener-Policy', 'same-origin'),
 ('X-Permitted-Cross-Domain-Policies', 'none'),
)


def install_security_headers(app):
 if getattr(app, '_security_headers', False):raise ValueError('Security headers already installed')
 @app.after_request
 def extra_security_headers(response):
  for name, value in STATIC:
   response.headers.setdefault(name, value)
  forwarded = request.headers.get('X-Forwarded-Proto', '').split(',')[-1].strip().lower()
  if request.is_secure or forwarded == 'https':
   response.headers.setdefault('Strict-Transport-Security', HSTS)
  return response
 app._security_headers = True
 return app
