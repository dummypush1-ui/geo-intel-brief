# 28b1 actual portable test fixes

Only two tests and derived metadata change. The production loader is unchanged. Run the focused tests with `python -m unittest tests.geospatial.test_map_route tests.test_dependency_audit`. Run `python portable_validation28b/negative_tests.py` to confirm that escaped recursion, accepted unsafe shape and ambient marker evaluation fail. Mutated files are restored even on failure.

Real depth 2000 never reports ok; allowed reasons are unreadable or bad_shape. Recursion and nested-array shape have separate exact refusal checks. Audit receipt identity supplies the historical marker environment; remaining keys are fixed labelled test context. The real pypdf historical requirement is checked as true for 3.10 and false for 3.12. Ambient 3.12 is mocked during the entire closure test. CPython 3.12 execution is NOT RUN.

The old 28a allowlist, receipts and logs remain historical bytes. Its unchanged runner on this tree fails at expected source drift. Historical cache verification still skips as unverified; current interpreter tag checks are unchanged. Validators, pikepdf, TZ, 512MB and profile conflicts remain open. Item 28 is OPEN. No production activation.
