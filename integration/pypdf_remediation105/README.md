# Current pypdf offline profile supersedes old locks

This change selects pypdf6.19.0 in BOTH current offline locks. It does not change
requirements-staging.txt, future-deploy lock, legacy runtime requirements,
collectors, DB, mail, Render or current UI. pypdf remains test-only in the basic
preview profile; parsing fixture PDFs is still execution, not zero risk.

Original87 audit and88 build receipt JSON remain byte-identical historical
observations. They describe old pypdf5.0.1 and the old built sgmllib wheel, NOT
these current locks. Their README headings now make that distinction explicit.
Original two lock bytes plus SHA256 are preserved in historical-locks.json and
in git parent d8f89025ae03e36a1f93c93607886535ce2e1905. Historical tests compare
against those exact snapshots. Current-profile focused checks are separate.
No old successful/blocked stage is relabelled as a new execution.

Candidate lock still explicitly lacks a sgmllib wheel hash and is NOT directly
installable. Built lock is the complete25artifact profile: new official pypdf
wheel7e5d6e730e7dae87d560a2cee218b852f6498c8be61966f3cd02ead971e48d14,
and newly built sgmllib wheel a16186785516975fd0f6f8f2a8c944cc0d832e061c9205ea904bf803ac25c0ad.
The sgmllib bytes differ from old88 because wheel builds are not deterministic;
source sdist/hash/source.py unchanged. No byte-identical build claim.

New build: safely inspected original11-member20923-byte sgmllib sdist, no
traversal/link/device members; reviewed setup imports setuptools and reads README.
Bubblewrap unshare-all/network isolated, clearenv, system trees read-only plus
scratch writable; bounded capture120s/CPU60s/AS1GiB/file64MiB/output1MiB and
kill-group/reap. Actual stage/log/argv and source hashes retained. Build-tool
wheel0.37.1/setuptools59.6.0, shared CPython3.10.12/Linuxx86_64, not new OS proof.

All25 wheel hashes inspected/copied. Fresh venv install uses --no-index,
--no-cache-dir,--only-binary=:all:,--require-hashes. This install occurred in the
local host environment, not an OS network namespace; flags are not an OS firewall.
No system-site; pip-check and active default-extra dependency edges pass.
25installed packages and641physical Python-file hashes recorded. Existing
feedparser/sgmllib SDK source pins and fixed parser tests pass. Optional extras
remain excluded. Artifact bytes are local scratch, not a published wheel bundle
or a one-command public-index deployment promise.

The other historical pinned versions are unchanged, including Flask3.0.3,
Werkzeug3.0.6,PyMongo4.8.0,requests2.32.3. This is a pypdf remediation ONLY, not a
security-clean runtime profile. No “all alerts fixed” or provider closure claim.
Future-deploy patched profile94 is separate and unchanged. Provider count/IDs
must be rechecked after the save; dismissals are not remediation evidence.

Upstream four advisory fixes: cross-reference>=6.14.0, ASCIIHex>=6.7.5,
RunLength>=6.7.4, whitespace>=6.15.0;6.19.0covers all four and requiresPython>=3.9.
https://github.com/py-pdf/pypdf/security/advisories/GHSA-55h5-xmcq-c37v
https://github.com/py-pdf/pypdf/security/advisories/GHSA-9m86-7pmv-2852
https://github.com/py-pdf/pypdf/security/advisories/GHSA-f2v5-7jq9-h8cg
https://github.com/py-pdf/pypdf/security/advisories/GHSA-fc8x-2rww-xw9m
https://pypdf.readthedocs.io/en/latest/meta/CHANGELOG.html

Fresh offline-built105 full suite:1166 unique/run successful, one existing
expected limiter failure and one optional pikepdf validator skip. Configured
staging first sweep had one manifest bookkeeping failure after adding evidence
during execution; correction and chunk rerun will be recorded explicitly.
Full build argv recovered from unchanged archived executed script.

Corrected staging chunk8 rerun100PASS after registering evidence. Combined
12chunk final accounting1166 unique/run successful, zero failures/errors,
one existing expected limiter failure and one existing optional pikepdf skip.
First failed chunk preserved in full-staging-regression.json, not erased.
