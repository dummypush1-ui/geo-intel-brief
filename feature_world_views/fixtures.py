# Copyright (c) 2026 Push. All rights reserved.
from flask import Flask
from integration.finder_index import FinderIndex
from .routes import create_blueprint

RAW = {'geo': [{'title': 'India HS code 090111 coffee report', 'url': 'https://example.com/story',
 'country': 'India', 'source': 'Supplied example', 'summary': 'HS code 090111. No rate evidence.',
 'category': 'TRADE', 'created_at': '2026-10-08T12:00:00+00:00', 'token': 'PRIVATE'}]}
INDEX = FinderIndex([[0, '090111', 'Coffee', 0, 0, 0]], [{'tag': 'IN', 'name': 'India HSN'}])

def app(reader=lambda: RAW, authorize=lambda req: True):
    app = Flask(__name__)
    app.register_blueprint(create_blueprint(reader=reader, authorize=authorize, finder_index=INDEX))
    return app.test_client()

