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

CSV_QUOTE='const q = (s) => \'"\' + String(s).replace(/"/g, \'""\') + \'"\';'
CSV_SAFE=r'''const q = (s) => {
      let raw = String(s).replace(/\0/g, ''), text = '';
      for (let i = 0; i < raw.length; i++) {
        const c = raw.charCodeAt(i);
        if (c >= 0xD800 && c <= 0xDBFF) {
          const next = raw.charCodeAt(i + 1);
          if (next >= 0xDC00 && next <= 0xDFFF) text += raw[i] + raw[++i];
          else text += '\uFFFD';
        } else text += c >= 0xDC00 && c <= 0xDFFF ? '\uFFFD' : raw[i];
      }
      const probe = text.replace(/^[\s\p{Cf}\p{Z}\x00-\x1f\x7f-\x9f]*/u, '');
      if (/^[\t\r\n]/.test(text) || /^[=+@-]/.test(probe)) text = "'" + text;
      return '"' + text.replace(/"/g, '""') + '"';
    };'''
def shortlist_csv_safe(shell):
 if type(shell) is not str or shell.count(CSV_QUOTE)!=1:raise ValueError('Finder CSV quote seam changed')
 return shell.replace(CSV_QUOTE,CSV_SAFE)
