## Historical receipt, superseded current lock

This document and its JSON receipt describe historical increment87/88, not the current lock. Current pypdf105 supersession: ../pypdf_remediation105/README.md. Original lock bytes/hashes remain in historical-locks.json and git d8f8902.

# Separate offline build and fresh-install experiment

Increment88, separate from immutable87 blocked audit. Receipt records source
members/hashes, build-tool Python-file metadata, interpreter and exact argv,
isolated stages, produced wheel and complete installed metadata. Orchestrator
text is the executed evidence, NOT a general-purpose installer or launcher.
It uses fixed author scratch paths and reviewed inputs; do not run it blindly.

Bubblewrap unshare-all enforces separate network/user/mount namespaces, only
/usr,/lib,/lib64 read-only plus writable scratch, /proc and /dev. No host home,
project credentials, downloads or inherited env/PYTHONPATH/user-site. Explicit
controlled HOME/TMP and resource CPU60s/AS1GiB/FSIZE64MiB, wall120s/output1MiB,
kill-process-group and reap. Probe verified missing host paths and refused
external connection before setup execution. This is a local Linux boundary,
not a certificate for arbitrary code, other hosts or production collectors.
Build script/setup/config/README/source exact bytes reviewed. Archive permits
only regular files/directories, <=32members/100000bytes, no traversal/links/
devices. Wheel equivalent limits, metadata one Name/Version, no dependencies,
compatible tags, same sgmllib source hash. Single build: deterministic wheel
bytes NOT claimed. Original87 lock/requirements/configured venv unchanged.

25 verified wheel hashes in separate requirements-offline-built.txt. Fresh
venv has no system-site-packages, explicit copied/rehashed artifact directory,
--no-index --no-cache-dir --only-binary=:all: --require-hashes; pip-check and
metadata closure verified. pip/setuptools are bootstrap, not app closure.
Base CPython/Expat/OS shared with host, not independently reproduced. Tool
Python-file hashes are recorded, not every shared-library/interpreter input.

Smoke allowlist feedparser/sgmllib/dateutil.parser/xml.parsers.expat only.
Unchanged85 guarded child verifies32feedparser Python pins, sgmllib source,
Expat backend and fixed RSS original-AST oracle. No production config imports.
No trafilatura or pikepdf silently added, no manual Playwright/browser binary
reproduction. Fresh full-suite is separate and pending until recorded.

Private wheel/artifact bytes are in author scratch, not published by this
receipt. A text lock alone is not a usable distributed artifact bundle.
No live functionality/Render/Atlas/delivery/cutover claim follows any pass.

Review correction: original executed runner had cleanup gaps and is retained
only as historical evidence. runner.py replaces capture: deadline begins just
after Popen, drains until both EOF and exit, bounded nonblocking stdin/output,
finally kills process group and reaps on every path. Fault tests cover closed
stdout-then-sleep, crash, oversized output and wall timeout. The separate
post-build Debian tool-hash fallback is preserved with command/digest/timing;
it is not represented as part of the original build entrypoint. Source copy
is writable scratch, NOT a read-only project mount. Future full suites run
from copied scratch, never production source/service credentials.
