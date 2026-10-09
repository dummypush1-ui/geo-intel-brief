# 205: next Geo report occurrence, calculation only

`next_occurrence` answers only "next after the anchor". A missed occurrence is
never reported or replayed. This is not a schedule, timer, job, claim, durable
ledger or exactly-once mechanism. No caller is wired. No collection or mail
function is imported or invoked. No environment configuration or current-clock
read is introduced, but zone data has the environment dependency described below.

Input: exact unit175 Geo namespaced settings, required explicit `cadence`
(daily/weekly), `ambiguous` (first/second/refuse) and `nonexistent` (skip/refuse).
No DST policy defaults. Anchor must be an exact datetime whose tzinfo is the
singleton timezone.utc; naive, nonzero-offset and subclass inputs are refused.
Anchor microseconds are retained in strict UTC comparison; candidate wall times
have second and microsecond zero. Equality is not "next".

Fifteen local calendar dates are searched, including the anchor's local date.
Weekly uses175's canonical weekday; daily still validates the closed settings
but does not use that weekday for selection. This bound permits a weekly skip
through New York's spring-forward Sunday02:30 to the following Sunday (14 days
when the previous Sunday occurrence equals the anchor). Result is `next`, or
`none_in_window` with null occurrence fields. No silent extension of the window.
Skipped future nonexistent times are counted. Past gaps are not missed reports.
Datetime-range overflow and unusable zone data return a static refusal.

For each wall time, fold0 and fold1 are converted to UTC and back. A candidate
exists only if both wall fields and fold round-trip. A gap is skipped or refused,
never shifted. An ambiguous future wall time is refused or selects fold0 (first)
or fold1 (second); these terms mean wall-clock repeats only, not positive/negative
DST or standard/summer time. If the selected repeat already passed, calculation
moves to a later date, not to the other repeat. Thus an anchor at first/between
repeats with policy first chooses a later date; second can select the remaining
fold1. At or after both repeats all policies skip that past wall time. This does
not catch up a missed first occurrence. Policy refusal can hold the whole result.

Result includes UTC ISO instant, local ISO instant with offset, offset seconds,
fold, local weekday, explicit policy labels, cadence, configured zone, inspected
window and source provenance. Fixed flags say no timer/activation/catch-up.

## Zone data and reproducibility

Python zoneinfo normally searches TZPATH, which can be set by PYTHONTZPATH at
process startup, and then the tzdata package. Unit175 validation inherits those
sources. This module takes its imported TZPATH snapshot, reads the selected TZif
bytes, hashes them, and uses ZoneInfo.from_file on those same bytes (not the
ZoneInfo process cache) for calculation. If no system file exists, it reads the
tzdata package resource. No zone bytes are downloaded. It performs local file
reads, so it is not a filesystem-free or literally environment-independent pure
function. Updating PYTHONTZPATH/reset_tzpath after module import does not update
this module's imported TZPATH; restart/reload is needed.

Provenance: source `system_TZPATH` or `tzdata_package`; SHA256 of actual zonefile;
system tzdata version from that root's tzdata.zi when available (else null);
installed tzdata package version when available (else null). Package metadata is
not evidence that the package supplied the selected system zone. These labels
are local-source diagnostics, not authenticated production provenance. Non-IANA host keys localtime, posixrules and Factory are explicitly refused.
Unit175 alone still accepts those keys; its independent follow-up remains open.
Unknown zone keys/read/parse failures refuse with static text, never echo supplied keys.

Author expected New York/Lord Howe/Apia/Sao Paulo/Dublin values were computed
using system IANA tzdata2025b. The installed fallback package is2026.4, not the
source used for those results. Older or different production timezone data can
differ. Tests pin observed expected instants; they are not universal timezone
policy or proof that a production server has current data.

## Legacy difference, not equivalence

Actual original snapshots were read from GitHub on2026-10-09:
- push2006/geonews scheduler.py SHA256
  `dc42e6147db678d3ad93d62f3412cd521230a040296a405e60d77588b99936a0`:
  lines111-116 use schedule.every().day.at and invalid-weekday Monday fallback.
- push2006/BRICS- scheduler.py SHA256
  `8e57b8aa7aeed25d4b9723d5235861b8f4be38c336de6be79e32bc713ba63f26`:
  lines54-57 install two collector intervals and each DIGEST_TIMES entry;
  this file installs no weekly report schedule.

Original Geo uses process-local timezone through schedule library and silently
falls back to Monday on invalid weekday. This planner uses an explicitly
configured zone and refuses invalid weekday per175. No legacy equivalence is
claimed. A UTC server's original09:00 process-local run would be09:00UTC, while
an IST-configured09:00 planner yields03:30UTC. This owner-visible timing change
requires the item25 decision before any wiring. Original code was not run.

BRICS intervals, multiple digest times and weekly-not-installed behavior remain
outside this unit. Existing legacy schedulers/configuration are unchanged.
Item25 stays open until reviewed caller/engine and profile decisions exist;
production DST policy, missed-run/restart behavior, durable claims and exact
send times remain separate gates. AppsScript selection, SMTP fallback hold,
201c and Atlas/live-effect holds are unchanged.

## Test scope

14 focused tests (11 new +3 unit175): fixed IST strict equality/microseconds,
midnight/week boundary/leapday, weekly skip across NY gap beyond seven days,
NY folds before/at/between/after repeats, Lord Howe30minute fold, Apia whole-day
skip2011-12-30, Sao Paulo nonexistent midnight2018-11-04, negative-DST Dublin,
exact UTC anchors and policies, static zone failure and provenance. Synthetic
empty-iteration test exercises none_in_window's shape (not real-zone evidence).
AST rejects effect-library imports. No original scheduler, real timer, mail,
collector, DB or production timezone source was executed or verified.
