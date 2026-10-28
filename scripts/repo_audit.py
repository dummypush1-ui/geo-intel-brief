#!/usr/bin/env python3
"""Inventory repository files and report exact-content duplicates.

This is a read-only audit helper. It never deletes or modifies repository files.
Run from any directory: python scripts/repo_audit.py [repository-root]
"""
from __future__ import annotations

import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and not path.is_symlink():
            files.append(path)

    by_hash: dict[str, list[str]] = defaultdict(list)
    by_area: Counter[str] = Counter()
    by_ext: Counter[str] = Counter()
    sizes: list[tuple[int, str]] = []
    total_bytes = 0

    for path in files:
        rel = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        by_hash[digest].append(rel)
        parts = Path(rel).parts
        by_area[parts[0] if len(parts) > 1 else "(root)"] += 1
        name = path.name
        by_ext[path.suffix.lower() or "[no extension]"] += 1
        size = path.stat().st_size
        total_bytes += size
        sizes.append((size, rel))

    duplicates = [(digest, paths) for digest, paths in by_hash.items() if len(paths) > 1]
    print("# Repository audit")
    print(f"- Root: `{root}`")
    print(f"- Files scanned: **{len(files)}**")
    print(f"- Total bytes: **{total_bytes:,}**")
    print(f"- Exact-content duplicate groups: **{len(duplicates)}**")
    print(f"- Paths in duplicate groups: **{sum(len(p) for _, p in duplicates)}**")
    print("\n## Top-level areas")
    for name, count in by_area.most_common():
        print(f"- `{name}`: {count}")
    print("\n## Extensions")
    for name, count in by_ext.most_common():
        print(f"- `{name}`: {count}")
    print("\n## Largest files")
    for size, name in sorted(sizes, reverse=True)[:25]:
        print(f"- {size:,} bytes — `{name}`")
    print("\n## Exact-content duplicates")
    for digest, paths in sorted(duplicates, key=lambda item: (-len(item[1]), item[0])):
        print(f"- SHA-256 `{digest}`:")
        for name in sorted(paths):
            print(f"  - `{name}`")
    print("\nNote: identical bytes do not prove safe deletion. Check imports, build inputs, manifests, licenses and historical-evidence requirements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
