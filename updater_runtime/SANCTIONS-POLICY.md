Sanctions refresh policy

The inclusive count envelope is 85% to 115%, calculated with integers. Empty
base bootstrap and valid outliers are held, not discarded. They are written to
state/sanctions-review.json with exact ordered rows and a SHA-256 over list+rows.
Candidates survive fetch failures. Changed candidates retain earlier unresolved
hashes in candidate_history. Applying a reviewed hash removes only that exact
hash; other pending candidates remain. An operator can review these rows and
supply reviewedHashes for the exact
candidate. A different fetch cannot inherit the approval. A zero-row or
malformed candidate cannot be approved. This source interface grants no
permission to perform a real refresh or to approve a sanctions dataset.

Old list rows and their success labels stay on refusal. Each automatic list
has health state, last_attempt, last_success (null if unknown), stale and
manual_review in SANCTIONS_META. The automate log reports this structured
state; the escalation counter measures attempts, not days. Global checked
advances only when both OFAC and EU refresh successfully. UFLPA is untouched.
Candidate rows are stored only for local operator review, not automatically
published or committed by this module. Writes use sibling temporary files and
rename; dataset and review file are not one atomic transaction.

No actual sanctions feed, dataset refresh, build or deployment was run to
validate this change. Tests use temporary files and supplied synthetic bodies.
Existing baked Finder UI is not rebuilt by this source change. New health is
visible to the updater/operator, not yet a rendered user-facing stale banner.

Intended design: there is no production approval endpoint or CLI. An operator
hand-edits the reviewedHashes argument after inspecting exact candidate rows.
A stale reviewed hash blocks even an in-range update for that list. This is
conservative by design. Health and last_attempt changes mean the sanctions
source file may differ daily even when old rows are retained.

The dependency audit hash covers canonical import-inventory source_baseline
files (path and SHA-256), not the whole preservation or staging manifest. The
new root test file is in those scopes, so its addition changes the audit hash.
