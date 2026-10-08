# Copyright (c) 2026 Push. All rights reserved.
"""Explicitly registered blueprint, never auto-mounted on an existing app."""
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory, Response
from .model import snapshot
from .filters import parse_filters, filter_snapshot
from .detail import detail
from .export import to_csv


def create_blueprint(*, reader, authorize, finder_index=None):
    if not callable(reader) or not callable(authorize):
        raise ValueError('Explicit supplied reader and authorization required')
    bp = Blueprint('world_views', __name__, url_prefix='/workspace/world')
    ui = Path(__file__).with_name('ui')

    @bp.before_request
    def gate():
        if request.method not in ('GET', 'HEAD'):
            return jsonify(error='Read-only view'), 405
        try:
            allowed = authorize(request)
        except Exception:
            allowed = False
        if allowed is not True:
            return jsonify(error='World view access denied'), 403

    @bp.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'"
        return response

    @bp.get('')
    def page():
        return send_from_directory(ui, 'world.html')

    @bp.get('/assets/<name>')
    def asset(name):
        if name not in ('world.js', 'world.css'):
            return jsonify(error='Not found'), 404
        return send_from_directory(ui, name)

    def read_snapshot():
        return snapshot(reader(), finder_index)

    @bp.get('/data')
    def data():
        try:
            filters = parse_filters(request.args)
        except ValueError:
            return jsonify(error='Invalid filters'), 400
        try:
            data = read_snapshot()
        except Exception:
            return jsonify(error='World view temporarily unavailable'), 503
        try:
            return jsonify(filter_snapshot(data, filters))
        except Exception:
            return jsonify(error='World view temporarily unavailable'), 503

    @bp.get('/article/<key>')
    def article(key):
        if request.args:
            return jsonify(error='Unsupported detail parameters'), 400
        try:
            result = detail({'items': [], 'scope': 'supplied_read_view'}, key)
        except ValueError:
            return jsonify(error='Invalid article key'), 400
        try:
            result = detail(read_snapshot(), key)
        except Exception:
            return jsonify(error='World view temporarily unavailable'), 503
        if result is None:
            return jsonify(error='Not in supplied snapshot'), 404
        return jsonify(result)

    @bp.get('/export.csv')
    def export_csv():
        try:
            filters = parse_filters(request.args)
        except ValueError:
            return jsonify(error='Invalid filters'), 400
        try:
            data = read_snapshot()
        except Exception:
            return jsonify(error='World view temporarily unavailable'), 503
        try:
            data = filter_snapshot(data, filters)
            body = to_csv(data)
        except Exception:
            return jsonify(error='World view temporarily unavailable'), 503
        response = Response(body, mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename="world-supplied.csv"'
        response.headers['X-Export-Scope'] = 'supplied_read_view_not_full_database'
        return response

    return bp
