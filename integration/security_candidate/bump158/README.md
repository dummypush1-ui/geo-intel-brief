Supplemental candidate-lock validation, October9

The candidate lock has four reviewed bumps plus the PyPI-published sgmllib3k
1.0.0 sdist hash. Frozen original/offline locks are unchanged. The old receipt
and regression-coverage remain historical, not coverage of this bumped lock.
Fresh isolated venv hashed install and pip check passed. pip used legacy
setup.py install for sgmllib3k because wheel was absent. Bootstrap pip and
setuptools versions are recorded but not hash-pinned. The app input hashes
were enforced; this is not a reproduced or independently attested build chain.
Full current-tree regression must pass in the bumped environment before landing.
No runtime profile or deployed environment was changed by this candidate.
