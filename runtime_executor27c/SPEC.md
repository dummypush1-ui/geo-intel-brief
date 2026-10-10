# 27c inert executor-discovery preparation

27c executor-discovery preparation; Docker/CP312 NOT RUN; 27/28/29 OPEN

This unit does NOT implement execution, failure capture, or Stage B. A future adapter needs its own contract and review. Failure-log retention is OPEN, not satisfied. The package is local preparation only, not selected by any workflow or application.

Baseline: 4cf969029042c29b8e5ea0c604c0d1b52d4db34d. Existing runtime_build, workflows, portable_validation28 and workflow_package29 are unchanged. No new binaries are added. The existing CA deb and supplied keyring would be reused by pinned hash, not copied into this package.

## Default and refusal paths

prepare.py with no arguments returns NOT RUN without reading pins, writing files, using the network or starting subprocesses. Stage A with its technical gate off does the same. Unknown, duplicate, missing or wrong arguments return REFUSED.

Gate ON inspects source pins only and returns NOT RUN. Stage B always returns REFUSED, even if a caller supplies an anchor filename. A filename does not authenticate approval. execute_reviewed raises before any subprocess call. The execution adapter is absent. Tests mock subprocess, socket, read and write paths and confirm zero calls on the default path.

A technical opt-in is not owner permission or executor capability. Any future Docker pull, build, dispatch or package execution needs a separately reviewed adapter and the owner's separate approval for that task.

## Stage A is not implemented

plan_only.sh contains only printf and exit. It has no executable apt, dpkg, Docker, fetch or install path, including through arguments or environment variables. Dockerfile.discovery is a FROM scratch placeholder with no COPY, RUN or entrypoint. Neither file implements Stage A.

The comparison function is exercised only on labelled fixtures. Identical fixture pairs return MATCH, but install_permitted remains false. Added, changed, downgraded or removed fixture pairs return STOP. Actual target-plan acquisition, parsing and comparison are unimplemented and OPEN. Fixtures are not real apt evidence.

The base image anchor records apt 2.8.3. Target executor behaviour is unobserved. The local apt 2.4.14 metadata/base-status simulation from 27b is not reused as target execution evidence. A future Stage A must stop before installation, return its real plan for review, and compare the resulting name/version pairs with the reviewed 146-pair anchor. Any difference requires a new anchor round. Even a match does not grant installation permission.

## Fixed trust tiers

Registry digests: observed from the registry's own responses and re-observed by two parties. Tag 24.04 is mutable, discovery only. Observed at 2026-10-10, not a claim of what the tag points to later.

Apt metadata: signature-valid against a keyring SUPPLIED from the workspace, not independently authenticated. Fingerprint matches a public Ubuntu-hosted mailing-list page - corroboration, not a trust bootstrap. Reviewer's gpgv run used the same supplied keyring, so it adds reproducibility but no new authentication. The Dockerfile's apt trust path (keyring package or key file) must be pinned by hash in the inputs and named as such.

noble InRelease dates 25 Apr 2024 (release pocket); updates/security 8 Oct 2026. Snapshot id 20261009T000000Z is the single pin for all three. Record that pocket dates differ. Apt behaviour with snapshot URL + these suites must be fixed in apt.sources; the apt.sources hash is what build-args.REVIEWED_APT_SOURCES_SHA256 carries.

The CA deb is the ONE reviewed repo-binary exception: the existing runtime_build/inputs/ca-certificates-bootstrap.deb, 139,430 bytes. It is not duplicated here. The derived bootstrap bundle is the concatenation of 121 sorted Mozilla PEMs, not the system bundle and not blacklist-equivalent. Its exact hash is in the reviewed derivation ledger. Bootstrap extraction does not run postinst or disable TLS verification. Future normal package installation would be a separate action and may run postinst.

Upstream index and network availability remain unreviewed for future execution. The default path does not create an input directory or fetch anything.

## Stage B is queued, not implemented

Only after a real Stage A has an accepted anchor and a capable executor route may a separately reviewed adapter install needed packages and record the actual CP312 interpreter, binary hash and toolchain.

stage-b-input-pins.json records hashes, versions and URLs for pip 26.2.1, setuptools 84.0.0, wheel 0.45.1, packaging 26.3 and the sgmllib3k sdist. These are pinned inputs, not verified CP312 execution. The ledger includes the nine reviewed source members and fixed SOURCE_DATE_EPOCH 1704067200.

Future source execution needs two fresh venvs, full-resolver offline hashed build tools and executor-side proof that networking is disabled. Docker --network none text alone is not proof. Namespace/no-route verification output must be included, or the execution is BLOCKED. Do not assume bwrap works inside Docker.

The two output wheels must be byte-compared and the outcome stated plainly, even if they differ. The CP312 wheel hash is a Stage B output to be reviewed before any application install. It must not be inferred from the 27a wheel or historical d697b1ce wheel. The historical artifact remains unavailable and unused. No application.lock is created here.

## Failure evidence and remaining obligations

A future adapter must retain bounded failure logs, stop reasons, stage identities and timeout/kill/reap evidence under its own reviewed contract. This package implements none of those execution features. 29b owns a workflow wrapper with always(); the existing workflow's upload-on-failure gap remains unchanged.

OPEN: no application source copy, no 209 helper or goldens, Gunicorn 22 vs 23, bcrypt 5, extras, native private internals, historical wheel recovery, own CP312 sgmllib anchor, real apt/Docker discovery, 28b actual fixes and pin review, and 29b ready lock/application source/failure-evidence wrapper. No Render, ABI, 512 MB or runtime-ready claim.

Local checks cover shell syntax, 14 unit/fixture/negative tests and two byte-identical default semantic receipts. There is no image, venv or environment-wide reproducibility claim. The 29a receipt remains 82d2cd9d432ebca4851ef53957b32a5ae1bc751cc2022284cb09a16cb82d0d94 because its read paths are unchanged.

Commands for local preparation only:

    python3 runtime_executor27c/prepare.py
    python3 runtime_executor27c/prepare.py --stage A --gate on --source /path/to/baseline
    python3 runtime_executor27c/test_prepare.py /path/to/baseline
