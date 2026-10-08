"""Explicitly injected Blueprint. Existing application guard remains mandatory."""
from pathlib import Path
from flask import Blueprint, jsonify, request, Response, send_from_directory
from .models import closed
from . import evidence, registry, route_catalog, timeline, news_context
from .ui import PAGE


def blueprint(reader):
    if not callable(reader):
        raise ValueError('Explicit supplied reader required')
    bp = Blueprint('carrier_preview', __name__, url_prefix='/carrier-preview')
    @bp.get('/')
    def home():
        return Response(PAGE, mimetype='text/html')
    @bp.get('/assets/<name>')
    def assets(name):
        if name not in ('carrier.js', 'carrier.css'):
            return jsonify(error='Not found'), 404
        return send_from_directory(Path(__file__).parent / 'static', name)
    @bp.get('/api/<kind>')
    def data(kind):
        if kind not in ('carriers', 'routes', 'events', 'sources', 'context'):
            return jsonify(error='Not found'), 404
        if set(request.args) - {'page'} or len(request.args.getlist('page')) > 1:
            return jsonify(error='Invalid page'), 400
        page = request.args.get('page', '1')
        if len(page) > 3 or not page.isascii() or not page.isdigit() or not 1 <= int(page) <= 100:
            return jsonify(error='Invalid page'), 400
        try:
            supplied = reader()
            closed(supplied, {'evidence', 'carriers', 'locations', 'routes', 'events', 'articles', 'as_of'})
            ev = evidence.catalog(supplied['evidence'], as_of=supplied['as_of'])
            carriers = registry.carriers(supplied['carriers'], ev)
            locations = registry.locations(supplied['locations'], ev)
            routes = route_catalog.catalog(supplied['routes'], carriers, locations, ev, as_of=supplied['as_of'])
            events = timeline.prepare(supplied['events'], locations, ev, as_of=supplied['as_of'])
            context, context_capped = [], False
            if kind == 'context':
                for carrier in carriers.values():
                    for item in news_context.prepare(supplied['articles'], carrier)['items']:
                        if len(context) == 100:
                            context_capped = True
                            break
                        context.append({**item, 'carrier_id': carrier['carrier_id']})
                    if context_capped:
                        break
            rows = {'context': context, 'carriers': list(carriers.values()), 'routes': list(routes.values()),
                    'events': events['items'], 'sources': list(ev.values())}[kind]
            offset = (int(page)-1)*100
            return jsonify(items=rows[offset:offset+100], scope='fixture_only', page=int(page),
                           truncated=context_capped or len(rows)>offset+100, context_capped=context_capped,
                           context_limit=100 if kind == 'context' else None, live_tracking=False)
        except Exception:
            return jsonify(error='Supplied fixture unavailable'), 503
    return bp


def mount_private(app, reader):
    """Only the existing guarded private API factory can receive this Blueprint."""
    from integration.news_api import create_app
    # Validate factory provenance and an installed global request guard. This is
    # an integration constraint, not a substitute for an operator permission.
    if app.import_name != create_app.__module__ or not any(f.__name__ == 'guard' and f.__module__ == create_app.__module__ for f in app.before_request_funcs.get(None, [])):
        raise ValueError('Existing private-route guard required')
    app.register_blueprint(blueprint(reader))
    return app
