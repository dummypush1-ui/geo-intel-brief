"""Responsive private preview frame over sanitized original renderer output.

Never used by mail builders or original source. Fixed CSS only, no scripts,
remote resources or external fonts. Re-sanitize before appending trusted frame
so source HTML cannot smuggle its own style/meta/script into this boundary.
"""
from integration.html_safety import sanitize_html
PREFIX='''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body { margin:0; }
body > table { width:100% !important; }
body > table > tbody > tr > td > table, body > table > tr > td > table {
 width:100% !important; max-width:700px; box-sizing:border-box;
}
td,th { overflow-wrap:anywhere; }
a { overflow-wrap:anywhere; }
@media(max-width:480px) {
 body > table { padding:12px 0 !important; }
 td { padding-left:12px !important; padding-right:12px !important; }
}
</style></head><body>'''
def responsive_preview(html):
 if type(html) is not str:raise ValueError('Exact preview HTML required')
 clean=sanitize_html(html)
 # Sanitizer canonicalizes tags; keep original body contents and table order.
 if not clean.startswith('<html><body') or not clean.endswith('</body></html>'):raise ValueError('Original preview body shape required')
 start=clean.index('>',clean.index('<body'))+1
 body_open=clean[clean.index('<body'):start]
 return PREFIX[:-len('<body>')]+body_open+clean[start:-len('</body></html>')]+'</body></html>'
