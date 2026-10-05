# Supplied page-watch snapshot contract

Pure supplied HTML/snapshot comparison. No fetch, source allowlist/authorization,
policy approval, store, mail, timer, route or source activation. Nilgiried fixed
report labels are NOT derived from URL: accepted arbitrary URLs do not establish
that source or ownership. Caller must bind source identity before sharing/use.
Observation timestamp is self-claimed, not verified capture/time truth. Hash is
integrity, not authenticity or proof a page was actually fetched.

Signatures retained. validate_snapshot now returns fresh canonical plain dict,
previously returned None. Closed keys url/observed_at/text/sha256/method, exact
plain str/dict types; old baseline shapes from snapshot re-canonicalize. Unknown
keys/missing method reject. No input mutation, silent NFC or text re-normalization.
Extraction still normalizes visible whitespace; any changed extraction rules
would appear as changed text, not semantic event verification.

URL <=2048chars, HTTP(S), scheme/host lowercase, fragment/defaultport removed,
empty path /, query unchanged. Reject userinfo, bad port, controls/whitespace,
backslash, lone surrogates and non-ASCII host. Limited equivalence only: no
percent/path/query/IDNA semantic normalization or source authorization.
Timestamp plainstr<=64, aware ISO parsed, original+UTC years1970..2100, offset
validated by datetime parser. Canonical UTC fixed microseconds, idempotent.
Compare canonical UTC strings; older instant rejects, equal stamp samehash
unchanged, equal stamp differenthash conflict. Older real observation represented
by later local-clock string now rejects. No future-clock truth check exists.

Original HTML2MB cap superseded by the parser input tightening below. Text <=2MB UTF8, min30chars, <=20000lines,
each <=100000chars checked before hash/diff. Surrogates reject cleanly.
Exact lowercase64hex SHA256 after caps. Diff allowed only when BOTH sides
<=1000lines and <=100000UTF8bytes, else changed with fixed diff-omitted summary.
This bounds difflib input, not a formal worst-case CPU deadline. Identical large
hashes return unchanged without diff. Existing small diff format retained by
golden byte-string test;80line/12000char display truncation remains. Added
result diff_omitted flag; summary labels observed change, not event verification.
No report renderer change, no persisted baseline rewrite/migration.

Earlier contract run20tests PASS (superseded by24-test parser bundle) covers old regression, offset chronology/equal
conflict, URL/time canonicalization/idempotence, shape/hash/caps, one-character
and repetitive lines fallback, unchanged large input, fresh copies, input
mutation and golden small diff. Report tests retain escaping/separate no-send
contract. Existing app is not importing a source watcher into runtime here.

HTML parser CPU is not bounded by the new line/diff caps: crafted <=2MB HTML
was observed by review to take about13.8seconds (predates this fix). This prior observation predates the new delimiter/event caps below; no
interrupting wall-clock limit implemented. This is not safe untrusted
live source ingestion without further parser work. Timestamp accepted ISO forms
depend on Python version (3.11+ is more lenient); configured tests use3.10.12.
Year bounds checked on original local year AND resulting UTC year. Naive/date-
only timestamps or missing-method old baselines now reject. An invalid retained
baseline needs an explicit reviewed re-baseline, not automatic silent repair.
Report title/source remain fixed Nilgiried strings for ANY accepted URL.

## Parser input tightening (supersedes2MB HTML acceptance)

HTML now <=128KiB UTF8 AND chars, raw '<' count<=4000, every delimiter span
between raw '<'/'>' <=4096chars before HTMLParser. This conservative preflight
rejects giant tags/attributes/comments/text runs, not a new tokenizer or exact
HTML token semantics. Nested delimiters can split a lexical token; total input
cap remains the bound. Parsed start/end/data/comment/decl/PI/unknown-decl event
budget8000 and existing depth500. Strict rejection keeps caller's previous
baseline unchanged. Smaller-page compatibility break explicit: formerly accepted
large legitimate pages can now reject. No fallback to partial/empty baseline.

24 configured tests PASS including direct event budget, UTF8/size/delimiter/
span limits, nested-unclosed '<a>'x500+'</b>'x3000, giantattribute/comment,
nearcapaccepted example and ordinary text golden. Six crafted measurements in
subprocess, timeout2s for entire harness (not runtime): observed worst~0.095s
nested-unclosed and~0.054s nested-within. Platform/version-specific observations,
not formal CPU deadline or hostile-HTML safety guarantee. Actual HTMLParser
can spend work before callback; malformed/nested cases may still be expensive.
No runtime subprocess or timeout is added, no live source activation.

Compatibility examples: inline script/JSON-LD longer than4096chars, plain
<p> text longer than4096chars, and pages over roughly3000tags may reject
(delimiter/events count structure, not a precise tag-count guarantee). These
were formerly accepted even if hidden script text was ignored. Timing numbers
above were measured on Python3.10.12 only; other versions/platforms unverified.
Existing broad-except maps parser exceptions to fixed malformed error, losing
specific diagnostics intentionally; do not treat that as a detailed fault code.
