"""Single-pass text-reference decoding and structural markup removal.
Copyright (c) 2026 Push. All rights reserved.
Parser behavior reviewed on CPython 3.10.12; target runtime remains held.
"""
from html.parser import HTMLParser
from html.entities import html5

# Exact semicolon-terminated keys only. No HTML5 legacy-prefix repair.
_NAMES = {key[:-1]: value for key, value in html5.items() if key.endswith(";")}
_HEX = "0123456789abcdefABCDEF"
_HTML_ELEMENTS = frozenset("a abbr acronym address applet area article aside audio b base basefont bdi bdo big blockquote body br button canvas caption center cite code col colgroup data datalist dd del details dfn dialog dir div dl dt em embed fieldset figcaption figure font footer form frame frameset h1 h2 h3 h4 h5 h6 head header hgroup hr html i iframe img input ins kbd label legend li link main map mark menu meta meter nav nobr noframes noscript object ol optgroup option output p param picture plaintext pre progress q rp rt ruby s samp script search section select slot small source span strike strong style sub summary sup table tbody td template textarea tfoot th thead time title tr track tt u ul var video wbr xmp".split())
_BARE_ATTRIBUTES = frozenset("disabled checked selected multiple readonly required hidden autofocus open controls loop muted autoplay reversed novalidate allowfullscreen download async defer nomodule itemscope nowrap playsinline clear compact ismap nohref noshade frameborder border inert formnovalidate default scoped seamless typemustmatch truespeed declare noresize".split())



def decode_once(text):
    """Decode exact bounded refs, never scan replacement text again."""
    out = []; cursor = 0
    while cursor < len(text):
        if text[cursor] != "&":
            out.append(text[cursor]); cursor += 1; continue
        # Longest named reference is small; bounded lookahead avoids giant ints.
        end = text.find(";", cursor + 1, cursor + 35)
        if end < 0:
            out.append("&"); cursor += 1; continue
        body = text[cursor + 1:end]; value = None
        if body.startswith("#"):
            digits = body[1:]; base = 10
            if digits.startswith(("x", "X")):
                digits = digits[1:]; base = 16
            alphabet = _HEX if base == 16 else "0123456789"
            if 1 <= len(digits) <= 12 and all(c in alphabet for c in digits):
                number = int(digits, base)
                if (0 < number <= 0x10FFFF and not 0xD800 <= number <= 0xDFFF
                    and (number >= 32 or number in (9, 10, 13))
                    and not 127 <= number <= 159
                    and not 0xFDD0 <= number <= 0xFDEF
                    and number & 0xFFFF not in (0xFFFE, 0xFFFF)):
                    value = chr(number)
        else:
            value = _NAMES.get(body)
        if value is None:
            # Only consume '&' so later independent references remain visible.
            out.append("&"); cursor += 1
        else:
            out.append(value); cursor = end + 1
    return "".join(out)


class _Markup(HTMLParser):
    """Remove raw source spans, never reconstruct text/entity parser events."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.source = text; self.lines = [0]; self.spans = []; self.hidden = None
        self.masked = self._declarations(text)
        for index, char in enumerate(text):
            if char == "\n": self.lines.append(index + 1)

    def _declarations(self, text):
        # Remove complete declarations/comments/PIs by raw source spans. Mask
        # even incomplete '<!' prefixes so version-specific declaration parsing
        # never asserts or swallows literal trailing text. No HTML regex.
        chars = list(text); cursor = 0
        while cursor < len(text) - 1:
            if text[cursor:cursor + 2] not in ("<!", "<?"):
                cursor += 1; continue
            start = cursor
            if text.startswith("<!--", start):
                end = text.find("-->", start + 4)
                end = end + 3 if end >= 0 else -1
            elif text.startswith("<![", start):
                end = text.find("]>", start + 3)
                end = end + 2 if end >= 0 else -1
            else:
                end = -1; quote = None; index = start + 2
                while index < len(text):
                    char = text[index]
                    if quote is not None:
                        if char == quote: quote = None
                    elif char in ("'", '"'): quote = char
                    elif char == ">": end = index + 1; break
                    index += 1
            if end >= 0:
                self.spans.append((start, end))
                for index in range(start, end):
                    if chars[index] != "\n": chars[index] = " "
                cursor = end
            else:
                chars[start] = " "; cursor += 2
        return "".join(chars)

    def _offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def _event_end(self):
        start = self._offset(); end = self.source.find(">", start)
        return start, end + 1 if end >= 0 else start

    def handle_starttag(self, tag, attrs):
        start = self._offset(); raw = self.get_starttag_text(); end = start + len(raw)
        # Prose 'if a<b and c>d' is syntactically ambiguous to HTMLParser.
        # Preserve a start tag with unknown bare attributes rather than eat it.
        if tag in ("script", "style"):
            if self.hidden is None: self.hidden = (tag, start)
            return
        if (tag not in _HTML_ELEMENTS and any(value is None for _, value in attrs)
            or any(value is None and name not in _BARE_ATTRIBUTES for name, value in attrs)):
            return
        if self.hidden is None: self.spans.append((start, end))

    def handle_startendtag(self, tag, attrs):
        if self.hidden is None:
            if tag not in ("script", "style") and (
                tag not in _HTML_ELEMENTS and any(value is None for _, value in attrs)
                or any(value is None and name not in _BARE_ATTRIBUTES for name, value in attrs)):
                return
            start = self._offset(); self.spans.append((start, start + len(self.get_starttag_text())))

    def handle_endtag(self, tag):
        start, end = self._event_end()
        if self.hidden is not None:
            if tag == self.hidden[0]:
                self.spans.append((self.hidden[1], end)); self.hidden = None
        else: self.spans.append((start, end))

    def handle_comment(self, data):
        if self.hidden is None:
            start = self._offset(); end = self.source.find("-->", start + 4)
            if end >= 0: self.spans.append((start, end + 3))

    def handle_decl(self, decl):
        if self.hidden is None: self.spans.append(self._event_end())

    def handle_pi(self, data):
        if self.hidden is None: self.spans.append(self._event_end())

    def unknown_decl(self, data):
        if self.hidden is None:
            start = self._offset(); end = self.source.find("]>", start)
            if end >= 0: self.spans.append((start, end + 2))

    def text(self):
        self.feed(self.masked); self.close()
        if self.hidden is not None: self.spans.append((self.hidden[1], len(self.source)))
        out = []; cursor = 0
        for start, end in sorted(self.spans):
            if end <= cursor: continue
            out.append(self.source[cursor:max(cursor, start)]); out.append(" "); cursor = end
        out.append(self.source[cursor:])
        return "".join(out)


def strip_html_once(text):
    """Remove actual and once-encoded markup; no recursive entity decoding.

    Unterminated ordinary tags/comments remain literal. Unclosed script/style
    drops its remainder. NBSP and all Unicode whitespace collapse to ASCII space.
    This is plain text, not a safe-HTML renderer or stored-data migration.
    """
    if not text: return ""
    text = _Markup(text).text()
    text = decode_once(text)
    text = _Markup(text).text()
    return " ".join(text.split())
