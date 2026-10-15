F1: isolated merged Finder rebuild and consumer-review boundary

Status: default-OFF candidate. This is the first refresh-connection unit, not
completed daily data refresh or current-source proof. Real parent 761f8f56.

The old Finder refresh.yml runs automate.mjs, which can make source/AI calls,
write files, publish issues/PRs and commit. Copying it into the merge unchanged
would bypass current safety gates and stale the merged offline/AI/code-news
source pins and identity artifacts. F1 instead selects an exact OFF flag before
any filesystem/Git/build operation. ON rebuilds the actual preserved catalogue
with the pinned real build.mjs in disposable scratch. No secret environment,
.git, updater state, old automate/server process, source/network/provider call,
AI request, issue/PR, Git publish, pin update or deploy is selected.

A closed supplied-candidate API accepts only existing data-source paths, exact
UTF-8 content hashes, at most150 files, 32MiB each and64MiB total. App/style/build,
proxy/workflow/env/state files and arbitrary paths are excluded. Inputs are
candidate facts, not approval. Isolated build source/assets reject symlinks.
The generated index/offline/data/SW must be a single hash-identified dataset,
matching offline content and SW reference. Node vm.Script checks syntax without
executing generated browser code. Build and syntax timeouts hold, not retry.

Unchanged rebuild is explicitly not a source refresh. Changed candidate output
returns exact old/new file hashes, orphan deletion proposals and the affected
merged consumer-review list. It remains held. F1 never blindly repins new output,
never overwrites last-good files and never grants publication authority. Candidate
scratch is removed after inspection; no claim of uploaded candidate data is made.
The paste-ready workflow is held as finder-refresh-prep.yml.txt for the owner
to add through GitHub UI. No active workflow is added by this commit. Its job
is gated by missing-by-default repository variable
MERGED_FINDER_REFRESH_PREP_ENABLED == true, read-only token and concurrency.
It runs only this rebuild-review path. Original cron03:30UTC is retained as
source scheduling intent; no schedule has been enabled or dispatched. It does
not install Poppler or inherit original broad git-add/commit/push or auto-GST.

Remaining connection units
- Controlled Comtrade/partner/market/sanctions/source acquisition, status and
  durable cadence with last-good retention, source-specific policy checks.
- Independent AI cost/privacy approval before alias/description/GST draft use.
- Atomic merged consumer rebinding: offline/data shell pins, code-news index,
  snapshot editions, identity proof, AI hooks, static/PWA paths and tests/pixels.
- Prepared output delivery and reviewer checks, then separately authorized
  branch-bound publication and uncertain-outcome reconciliation, no force/retry.
- One scheduler owner, host capacity, source credentials where needed and final
  enablement/cutover. Building this module supplies none of that permission.

Source parity target: current Finder repo, not merely a macro feature count.
Audit found195 top-level function declarations; nested/arrow bindings and actual
control sites are recorded too. Existing merged proxy/report/AIS safety changes
stay preserved. This unit changes no original app/proxy/data/build source bytes.
