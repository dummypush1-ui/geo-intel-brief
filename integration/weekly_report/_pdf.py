# Copyright (c) 2026 Push
"""Minimal own PDF 1.4 writer: 390x780 pt phone-shaped pages, two base-14 fonts (Helvetica and
Helvetica-Bold, WinAnsi, not embedded), text, rectangles, lines, URI links.

Pure: stdlib only, no I/O, no env-var or settings reads, no clock reads.
Output is a function of the input only (byte-identical for identical input).
"""
import hashlib
import zlib
from datetime import timezone

from . import _metrics

# Phone-shaped page: 390 pt wide so a fit-to-width view on a 390 px phone is 1:1.
PAGE_W = 390.0
PAGE_H = 780.0
MIN_FONT_PT = 9.0
MM = 72.0 / 25.4
_W = {"F1": _metrics.REGULAR, "F2": _metrics.BOLD}


def to_winansi(text):
    """Text -> cp1252 bytes; anything unencodable becomes '?' (stated limit)."""
    return text.encode("cp1252", "replace")


def text_width(text, size, bold=False):
    tab = _W["F2" if bold else "F1"]
    total = 0
    for b in to_winansi(text):
        total += tab[b - 32] if 32 <= b <= 255 else tab[0]
    return total * size / 1000.0


def wrap(text, size, bold, max_w):
    """Greedy word wrap; over-long words are split by characters."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = word if not cur else cur + " " + word
            if text_width(cand, size, bold) <= max_w:
                cur = cand
                continue
            if cur:
                lines.append(cur)
                cur = ""
            while text_width(word, size, bold) > max_w and len(word) > 1:
                n = len(word)
                while n > 1 and text_width(word[:n], size, bold) > max_w:
                    n -= 1
                lines.append(word[:n])
                word = word[n:]
            cur = word
        lines.append(cur)
    return lines or [""]


def _esc(b):
    out = bytearray()
    for c in b:
        if c in (0x28, 0x29, 0x5C):
            out += b"\\" + bytes([c])
        elif c < 32 or c > 126:
            out += b"\\%03o" % c
        else:
            out.append(c)
    return bytes(out)


def _n(x):
    s = ("%.2f" % x).rstrip("0").rstrip(".")
    return s or "0"


class Page:
    def __init__(self):
        self.ops = []
        self.links = []  # (x0, y0, x1, y1, url)

    def text(self, x, y, s, size, bold=False, color=(0, 0, 0)):
        self.ops.append(b"%s %s %s rg BT /%s %s Tf %s %s Td (%s) Tj ET" % (
            _n(color[0]).encode(), _n(color[1]).encode(), _n(color[2]).encode(),
            b"F2" if bold else b"F1", _n(size).encode(), _n(x).encode(), _n(y).encode(),
            _esc(to_winansi(s))))

    def rect(self, x, y, w, h, fill=None, stroke=None, line=0.5):
        parts = []
        if fill:
            parts.append(b"%s %s %s rg" % tuple(_n(c).encode() for c in fill))
        if stroke:
            parts.append(b"%s %s %s RG %s w" % (tuple(_n(c).encode() for c in stroke) + (_n(line).encode(),)))
        op = b"B" if fill and stroke else (b"f" if fill else b"S")
        parts.append(b"%s %s %s %s re %s" % (_n(x).encode(), _n(y).encode(), _n(w).encode(), _n(h).encode(), op))
        self.ops.append(b" ".join(parts))

    def hline(self, x0, x1, y, color=(0, 0, 0), line=0.5):
        self.ops.append(b"%s %s %s RG %s w %s %s m %s %s l S" % (
            _n(color[0]).encode(), _n(color[1]).encode(), _n(color[2]).encode(), _n(line).encode(),
            _n(x0).encode(), _n(y).encode(), _n(x1).encode(), _n(y).encode()))

    def link(self, x0, y0, x1, y1, url):
        self.links.append((x0, y0, x1, y1, url))


def _hex16(s):
    return "<FEFF" + s.encode("utf-16-be", "replace").hex().upper() + ">"


def _date(dt):
    u = dt.astimezone(timezone.utc)
    return "(D:%04d%02d%02d%02d%02d%02dZ)" % (u.year, u.month, u.day, u.hour, u.minute, u.second)


def build_pdf(pages, title, subject, creator, created_at):
    """pages: list[Page]. Returns bytes. URLs must already be validated ASCII."""
    objs = []  # index i -> bytes of object (i+1)

    def add(b):
        objs.append(b)
        return len(objs)

    catalog = add(b"")        # 1 filled later
    pages_obj = add(b"")      # 2 filled later
    f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    info = add(("<< /Title %s /Subject %s /Creator %s /Producer %s /CreationDate %s /ModDate %s >>" % (
        _hex16(title), _hex16(subject), _hex16(creator), _hex16(creator),
        _date(created_at), _date(created_at))).encode("ascii"))
    kids = []
    digest = hashlib.sha256()
    for pg in pages:
        content = b"\n".join(pg.ops)
        digest.update(content)
        comp = zlib.compress(content, 9)
        cobj = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(comp) + comp + b"\nendstream")
        annots = []
        for (x0, y0, x1, y1, url) in pg.links:
            a = add(b"<< /Type /Annot /Subtype /Link /Rect [%s %s %s %s] /Border [0 0 0] "
                    b"/A << /S /URI /URI (%s) >> >>" % (_n(x0).encode(), _n(y0).encode(), _n(x1).encode(),
                                                      _n(y1).encode(), _esc(url.encode("ascii"))))
            annots.append(a)
        ann = (b" /Annots [%s]" % b" ".join(b"%d 0 R" % a for a in annots)) if annots else b""
        p = add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %s %s] /Contents %d 0 R "
                b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >>%s >>" % (
                    pages_obj, _n(PAGE_W).encode(), _n(PAGE_H).encode(), cobj, f1, f2, ann))
        kids.append(p)
    objs[pages_obj - 1] = b"<< /Type /Pages /Count %d /Kids [%s] >>" % (
        len(kids), b" ".join(b"%d 0 R" % k for k in kids))
    objs[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_obj
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, body in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    ident = digest.hexdigest()[:32].upper().encode()
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R /ID [<%s> <%s>] >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, catalog, info, ident, ident, xref)
    return bytes(out)
