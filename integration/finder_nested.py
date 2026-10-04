"""Narrow served-preview shortlist scroll port. Preserved Finder untouched."""
import re
TABLE="'<table class=\"sl-table\"><tbody>' + rows + '</tbody></table></div>';"
REPLACEMENT="'<div class=\"finder-shortlist-scroll\" role=\"region\" aria-label=\"Shortlist table, scroll horizontally if needed\" tabindex=\"0\"><table class=\"sl-table\"><tbody>' + rows + '</tbody></table></div></div>';"
STYLE='<style id="finder-nested-shortlist">.finder-shortlist-scroll{max-width:100%;overflow-x:auto;padding-bottom:4px}.finder-shortlist-scroll:focus-visible{outline:2px solid #125b92;outline-offset:2px}@media print{.finder-shortlist-scroll{overflow:visible;max-width:none}}</style>'
def shortlist_scroll(shell):
 if type(shell) is not str or shell.count(TABLE)!=1:raise ValueError('Finder shortlist seam changed')
 script_spans=list(re.finditer(r'<script\b[^>]*>.*?</script>',shell,re.S|re.I))
 matches=[m for m in re.finditer(r'</head>\s*<body\b',shell,re.I) if not any(x.start()<=m.start()<x.end() for x in script_spans)]
 if len(matches)!=1:raise ValueError('Finder real head seam changed')
 position=matches[0].start()
 shell=shell[:position]+STYLE+shell[position:]
 return shell.replace(TABLE,REPLACEMENT)
