"""Loopback-only private review preparation. No default auth bypass or auto-run."""
from .models import loopback_host


def build(environ, reader):
    from integration.preview_access import create_preview_from_env
    from .api import mount_private
    if type(environ) is not dict or environ.get('PREVIEW_ACCESS_ENABLED') != 'true':
        raise ValueError('Existing private preview authentication required')
    return mount_private(create_preview_from_env(environ), reader)


def serve(app, *, host='127.0.0.1', port=8779, ssl_context):
    host = loopback_host(host)
    if type(port) is not int or not 1024 <= port <= 65535 or ssl_context is None:
        raise ValueError('Explicit TLS and unprivileged port required')
    app.run(host=host, port=port, ssl_context=ssl_context, debug=False, use_reloader=False)
