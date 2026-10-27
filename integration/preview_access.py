"""Preview access without a login.

There is no password, session or sign-in page. Only read-only routes that serve
sanitized public news rows (integration.public_news whitelist) and the static
public pages are allowed. Writes, the mail/sent-marking route, the private
dashboard and the whole-store pagers stay denied. PREVIEW_ACCESS_ENABLED (default
false) must be true to serve anything, and data still needs the default-OFF read flags.
"""
PUBLIC_POST=frozenset({'/api/related-news','/api/finder-context','/critical','/weekly'})
DENIED=frozenset({'/mark-emailed','/dashboard','/api/export-full.csv','/api/news-page','/api/v1/news-page','/api/brics/streams'})
READ=('GET','HEAD')

def public_read(req):
    """Allow only public-safe reads. Everything else stays denied."""
    path=req.path
    if path in DENIED:return False
    if req.method in READ:return True
    return req.method=='POST' and path in PUBLIC_POST

def create_preview_from_env(environ,reader=None,**kwargs):
    from integration.news_api import create_app
    # PREVIEW_ACCESS_ENABLED is the explicit opt-in to serve the public-read preview.
    # Default false keeps every route denied, as before. No login is involved.
    if environ.get('PREVIEW_ACCESS_ENABLED','false').lower()!='true':return create_app(**kwargs)
    return create_app(reader=reader,authorize=public_read,**kwargs)
