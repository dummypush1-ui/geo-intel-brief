Monitor issue health, item22

List requests check HTTP status and validate every page. Up to 100 pages of
100 open issues are searched before creating. Malformed/truncated/pagination
cap and transport errors fail closed. PRs do not satisfy duplicate issue checks.
Creation requires HTTP201 and valid number/title/URL acknowledgement. 5xx or
transport/bad acknowledgement is uncertain, not a success or blind resend.
Each retry lists first; this prevents duplicate creation when a previous lost
acknowledgement actually created a visible open issue. Concurrent creators or
GitHub list visibility lag remain possible races; this is not exactly-once.

Per-source pending_issues is keyed by title and persists independently of the
source signature, which may already have advanced. Failed, uncertain and
disabled requests keep pending; created/existing clears only that title. Retry
runs before the next source signature check, including when source is offline.
Invalid issue configuration is failed issue health, not a source exception.
No token means disabled and pending remains until configuration is supplied.

Sanctions escalation now retries every attempt at or after seven failures,
instead of only the seventh. Each retry checks all open pages first. If an old
issue is closed, another issue may be created on a later attempt; persistent
listing failure reports failed and creates nothing. These are attempts, not
verified daily cadence. monitor/automate log structured issue health.

No issue was sent and no monitor/trigger was installed during these tests.
The source interface does not authorize communication; activation and issue
sends still need user scope. Tests use private temporary state and fake calls.
