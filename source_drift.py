"""Source drift report for the preserved geonews/BRICS files. Read-only, no network.

Checks preservation-manifest.json against the working tree (local drift) and,
when given a JSON map of upstream hashes, against the original repos (upstream
drift). Upstream hashes must be supplied by the operator; nothing is fetched.
Upstream map shape: {"<source_repo>/<source_path>": "<sha256>"}.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drift_report(root=ROOT, manifest=None, upstream=None):
    root = Path(root)
    if manifest is None:
        manifest = json.loads((root / 'preservation-manifest.json').read_text())
    entries = manifest['source_files']
    rep = {'total': len(entries), 'missing': [], 'local_drift': [],
           'modified_from_source': [], 'identical_to_source': 0,
           'upstream_drift': [], 'upstream_unknown': [], 'upstream_checked': upstream is not None}
    for e in entries:
        p = root / e['path']
        if not p.is_file():
            rep['missing'].append(e['path'])
        elif _sha(p) != e['sha256']:
            rep['local_drift'].append(e['path'])
        if e['sha256'] == e['source_sha256']:
            rep['identical_to_source'] += 1
        else:
            rep['modified_from_source'].append({'path': e['path'], 'changes': e.get('changes', [])})
        if upstream is not None:
            key = e['source_repo'] + '/' + e['source_path']
            if key not in upstream:
                rep['upstream_unknown'].append(key)
            elif upstream[key] != e['source_sha256']:
                rep['upstream_drift'].append(key)
    rep['ok'] = not (rep['missing'] or rep['local_drift'] or rep['upstream_drift'])
    return rep


def main(argv):
    upstream = None
    if '--upstream' in argv:
        upstream = json.loads(Path(argv[argv.index('--upstream') + 1]).read_text())
    rep = drift_report(upstream=upstream)
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0 if rep['ok'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
