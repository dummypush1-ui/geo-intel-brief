"""Closed collector-path WSGI dispatch, no broader public route permission."""
class CollectorDispatcher:
    def __init__(self,public,collector):self.public=public;self.collector=collector
    def __call__(self,environ,start_response):
        path=environ.get('PATH_INFO','')
        if path=='/api/collect' or path.startswith('/api/collect/status/'):
            return self.collector(environ,start_response)
        return self.public(environ,start_response)
