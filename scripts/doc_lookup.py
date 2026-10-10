"""Read exact historical documentation sections from the single root README.

No filesystem monkeypatching, writes, activation or runtime app imports.
"""
import hashlib
import json
from pathlib import Path

_MARKER = b'<!-- ORIGINAL-DOC '
_END = b'\n<!-- END-ORIGINAL-DOC -->'

def documentation(root):
    raw = (Path(root) / 'README.md').read_bytes()
    docs = {}
    offset = 0
    while True:
        start = raw.find(_MARKER, offset)
        if start < 0:
            return docs
        end = raw.find(b' -->\n', start)
        if end < 0:
            raise ValueError('Malformed documentation section')
        row = json.loads(raw[start + len(_MARKER):end])
        if set(row) != {'path', 'bytes', 'sha256'}:
            raise ValueError('Documentation section shape')
        name, size, digest = row['path'], row['bytes'], row['sha256']
        if (type(name) is not str or not name.endswith('.md') or name == 'README.md'
                or name.startswith('/') or '\\' in name
                or any(p in ('', '.', '..') for p in name.split('/'))
                or name in docs or type(size) is not int or not 0 <= size <= 1048576
                or type(digest) is not str or len(digest) != 64):
            raise ValueError('Documentation section identity')
        begin = end + len(b' -->\n')
        content = raw[begin:begin + size]
        if raw[begin + size:begin + size + len(_END)] != _END:
            raise ValueError('Documentation section length')
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError('Documentation section hash')
        docs[name] = content
        offset = begin + size + len(_END)

def source_bytes(path, root=None):
    """Regular source file, or exact archived .md bytes at its former path."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Source symlink refused')
    if path.is_file():
        return path.read_bytes()
    if root is None:
        root = Path(__file__).resolve().parents[1]
    root = Path(root).resolve()
    try:
        name = path.resolve().relative_to(root).as_posix()
    except ValueError:
        raise ValueError('Source outside documentation root') from None
    if not name.endswith('.md'):
        raise FileNotFoundError(path)
    docs = documentation(root)
    if name not in docs:
        raise FileNotFoundError(path)
    return docs[name]

def source_text(path, root=None):
    return source_bytes(path, root).decode('utf-8')
