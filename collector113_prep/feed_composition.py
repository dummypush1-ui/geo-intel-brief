"""Original selection composed with isolated112 parsing, supplied HTTP only.
Default catalog is AST-literal-loaded from hash-pinned original source, avoiding
imports that could instantiate live DB/report clients. Extra feeds require an
installation-owned reviewed allowlist; no client-supplied URLs are fetched.
"""
import ast
import hashlib
from pathlib import Path
from collector113_prep.transport_policy import endpoint_plan, decode_response
from collector112_prep.parser_runner import parse_supplied_bytes
from integration.supplied_feed_fixture import prepare_supplied_feed, PINS

ROOT = Path(__file__).resolve().parents[1]
class CompositionRefused(ValueError):
    pass

def original_catalog():
    path = 'intelligence/geo/collectors/rss.py'
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINS[path]:
        raise CompositionRefused('Original catalog drift')
    tree = ast.parse(raw)
    node = next(n for n in tree.body if type(n) is ast.Assign and
                any(type(t) is ast.Name and t.id == 'DEFAULT_FEEDS' for t in n.targets))
    return tuple(ast.literal_eval(node.value))

def select_response(feeds, url, *, answers, peer, status, headers, chunks,
                    deadline, clock, cutoff, fallback_clock, max_items=50):
    """One feed, no writer, clients, scheduler, real DNS, TLS or HTTP effects."""
    plan = endpoint_plan(feeds, url, answers, peer)
    decoded = decode_response(status, headers, chunks, deadline=deadline, clock=clock)
    parsed = parse_supplied_bytes(decoded['bytes'])
    spec = next(f for f in feeds if f[1] == url)
    selected = prepare_supplied_feed(spec, parsed['entries'], cutoff=cutoff,
                                     fallback_clock=fallback_clock, max_items=max_items)
    return {'scope': 'inactive_supplied_response_original_selection',
            'selection': selected, 'parser_bozo': parsed['bozo'],
            'parser_entry_count': parsed['entry_count'],
            'parser_projection_count': len(parsed['entries']),
            'input_sha256': parsed['input_sha256'], 'endpoint_plan': plan,
            'wire_bytes': decoded['wire_bytes'], 'decoded_bytes': decoded['decoded_bytes'],
            'network': False, 'writes': False, 'delivery': False}
