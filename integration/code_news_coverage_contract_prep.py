"""Shared dormant wire contract. No IO or construction."""
import json
RESOLUTIONS=('unknown_code','not_in_link_model','ambiguous','conflicting_source_rows','unusable_description','invalid_code')
def serialize(body):return json.dumps(body,ensure_ascii=False,allow_nan=False,separators=(', ', ': ')).encode('utf-8')
def script():return '"use strict";globalThis.CODE_NEWS_RESOLUTIONS=Object.freeze('+json.dumps(RESOLUTIONS)+');'
