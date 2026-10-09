# 218: supplied email candidate, not approved or sent

Default OFF returns disabled flags before reading arguments/importing selection.
Explicit True uses actual202 normalization and193 selection for email. Input is
original closed supplied rows, supplied exact UTC datetime, explicit published or
created_at policy, per-channel ObjectId receipt tuples, section limit1..60 and
fixed offset config. No DB URL/client/read, current-state check, send, marking,
archive, ledger, network, scheduler or live mount exists. No sender uses218.

ONE candidate contains Last 24 hours and Last 7 days (includes last 24 hours).
Both windows are inclusive: [asof-24h,asof] and [asof-7d,asof]. An overlapping
article appears in both sections. Each section selects score>=4 rows after exact
supplied email membership exclusion, ordered score descending, normalized
published descending, ObjectId descending. Receipt fixtures are caller-supplied
per-channel membership, not DB checks or authenticated complete send history.
Legacy emailed flags do not establish per-channel membership. Entire input is
validated, including excluded/old rows. IDs dedupe for212's ObjectId identity;
sorted union<=120 is binding data, not permission to prepare a ledger receipt.

Subject is fixed text plus supplied UTC timestamp, never an article title.
Body uses exact fixed-offset arithmetic, no timezone database. offset_label must
exactly equal its signed HH:MM offset_minutes, e.g.+05:30. Near midnight can shift
the calendar day while preserving the same instant. Label does not assert a zone
or DST rule. No clock is read inside.

Every display string goes through203 plain Unicode control/format neutralization
then HTML escaping (&,<,>,double/single quotes). Text uses the same neutralized
values and article order. Surrogates refuse via202/193; bidi, zero-width, NUL/C1
controls become spaces. URLs follow203's closed HTTPS/no-userinfo/no-controls/
no-whitespace/host/length/port rule: unsafe links refuse the WHOLE candidate,
including excluded rows. They are not silently dropped. href is escaped.
No images/tracking/remote fonts/style block/JS. Inline CSS and presentation tables
are a candidate layout, not proof of Gmail/Outlook or dark-mode compatibility.

Combined subject+html+text UTF8 cap80KiB; separate HTML-only cap60KiB gives extra
headroom against email-client clipping, not a measured Gmail limit. Overflow
refuses ALL with fixed Email candidate held; no truncation, reselect or dropped
identity. Multibyte boundaries at cap-1/cap/cap+1 are tested. Source fields remain
bounded under193/202, so even a legal input can hold on output size.

Empty selection returns skip=True and flags only: NO subject/html/text/digest or
candidate field from which an accidental212prepare can be assembled. Nonempty
result has candidate data and SHA256 canonical sorted-key/separator/ensure_ascii
JSON digest of every candidate field including renderer_version,
digest_algorithm,kind,date_field,asof_utc,offset_minutes/label,subject/html/text,
ordered section names/headings/IDs/counts,sortedunion andskip. It binds THIS
candidate only, not content approval or immutable archive proof. Same inputs
produce independent equal outputs. The owner has not approved wording/recipients.
send_allowed/ready/archive_proof remainFalse, not review flags a caller may toggle.

Visual evidence: local headless Chrome desktop and mobile screenshots inspected
for readable wrapping, headings, overlap and no horizontal overflow. Browser
pixels do not verify email-client rendering. Actual Outlook/Gmail tests remain
open. No real email, remote resource, DB or Google service was used.

Events, weekly/critical, historical exclusion completeness, immutable body archive,
212 enforcement/import/mapping/control preservation, marking, sender/recipient/
final words, reconciliation, mailv1 128-cap handling, deployed Host, real mount
and live workflow remain open.217staysheld,216unselected. AppsScriptselected/
SMTPfallbackheld/201cwriteheld.9am target is not readiness or live permission.

193 ignores emailed=True for this selection: only the supplied email receipt tuple
excludes an article.218 cannot verify those fixtures. Digest covers the rendered
candidate, not original input rows; distinct source snapshots rendering an equal
candidate share a digest. Text prints raw safe URLs and Article ID lines. A future
real renderer must decide whether those IDs belong in the owner-facing body.
Content remains a candidate, without owner-approved wording or recipient.
