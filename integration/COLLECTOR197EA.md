# 197e-a job source and owner diagnostic

Default OFF. No running scheduler, production provider, activation, account or
Atlas changes. This is a one-shot injected composition and read-only/local
runtime preflight, not an unattended collector. Web RuntimeEvidence unchanged.

Design allocation: four feed workers256MiB + four parsers256MiB =2048MiB AS;
coordinator256MiB; parent512MiB; kernel/bwrap/overhead allocation256MiB; total
3072MiB. These are design caps, not measured RSS or a proof that overhead fits.
Parent/coordinator get actual RLIMIT_AS before application imports in their
job launch paths. All children inherit parent bounds until tighter limits.
Feed/parser limits unchanged. 90s cycle,70s fetch cutoff,25s feeds, four active
sources unchanged; partial failed/unstarted coverage persists honestly.

Enabled composition requires exact injected JobRuntimeEvidence (no WSGI field),
fresh<=120s, observed available>=3072MiB, protected exclusive current cgroup-v2
memory.max3072MiB, swap.max0, oom.group1,512MiB parent and256MiB coordinator,
actual PID+nested isolation, source pins and independently verified aggregate
guard. The record's activation reference is not authority itself. A production
provider must bind it to original scoped owner approval. None exists here.
No environment READY flag bypass; direct CLI only accepts --diagnose. Unsupported
host returns supported=false; never opens Atlas from diagnostics.

Same dedicated writer URI, exact Atlas articles/jobs/checkpoints mappings,
majority/journal, pre-existing roles/indexes/ledger, durable CAS and immutable
coverage, no replay/takeover, uncertain writes locked. History64 remains a
fail-closed limit. No purge/reset/rotation in this unit. Long-term cadence needs
197e-b archival/status/coverage contract. No ten-minute delivery guarantee.

## Owner-operated diagnostic after source landing

This runs only synthetic allocations and local checks, with NO Atlas secrets,
production activation or collector fetch/write. It creates disposable fixture
cgroups on the GitHub runner, then removes them. Privileged setup is explicit;
no privileged setup was run during source preparation. Never run on Render.

Owner pastes the workflow below via GitHub UI. We never push .github files.
Replace REVIEWED_SOURCE_SHA with the independently reviewed landed source SHA,
not a moving branch. The checkout action v4 tag was resolved via git ls-remote
at source preparation to11d5960a326750d5838078e36cf38b85af677262. No other actions.
No schedule, pull_request trigger, production secret or persistent checkout creds.
Requires public dummypush1-ui/geo-intel-brief on standard Ubuntu VM (not slim).
The workflow must NOT be enabled or submitted automatically by this unit.

```yaml
name: Collector197e read-only diagnostic
on:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  diagnostic:
    if: github.repository == 'dummypush1-ui/geo-intel-brief' && github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: REVIEWED_SOURCE_SHA
          persist-credentials: false
      - name: Install bounded diagnostic dependencies
        shell: bash
        run: |
          set -euo pipefail
          sudo -n apt-get update
          sudo -n apt-get install -y bubblewrap
          python3 -m venv .collector-job-env
          .collector-job-env/bin/python -m pip install --require-hashes -r requirements-future-deploy.lock
      - name: Disposable aggregate guard diagnostics only
        shell: bash
        run: |
          set -euo pipefail
          sudo -n /bin/bash integration/collector197_job_diagnostic.sh --diagnose
```

Unpinned Ubuntu/apt host tooling is not an immutable application lock; actual
kernel/bwrap/isolation behavior must be observed. Dependency lock hashes remain
mandatory and missing wheel/hash refuses. Pinning source and action protects
reviewed code identity, not arbitrary runner/image changes. No silent fallback.
If controller delegation, cgroup events/peak, sudo, isolation or dependencies
are unavailable, diagnostic fails/returns unsupported. Send only the diagnostic
JSON and synthetic peak/events from run logs, no secrets. The diagnostic does
not supply a production runtime provider and never enables collector code.

## Validation scope

Locally proven: parent/coordinator allocation refusal, closed job record/default
OFF/no provider, real local unsupported facts, existing coordinator isolation
regressions. Mocked protected cgroup validation tests are source tests only.
Aggregate kernel OOM-group and synthetic overhead proof DEFERRED to the owner
GitHub diagnostic because current test host cgroup is shared/read-only. Even a
successful synthetic fixture is not actual workload peak/overhead evidence;
production stays blocked until real guard and adversarial/workload evidence.

Sources:
https://docs.github.com/en/actions/reference/runners/github-hosted-runners
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
``GitHub public standard Ubuntu4CPU/16GB and passwordlesssudo`` is capability,
not user approval; scheduling can delay/drop, public idle workflows disable.
