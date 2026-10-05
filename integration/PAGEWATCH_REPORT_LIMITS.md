# Bounded supplied page-watch preview report

No source fetching/authentication, mail, marking, storage, routes or scheduler.
Function signature/return keys retained; valid small legacy HTML bytes retained
against the explicit test string by golden test (not an independently retrieved
original report). All rendered title/summary/URL escaped, no str coercion.

Exact plain dict/list/str/bool values only, depth4, dict24keys/key64chars, list1,
per-string2MBUTF8 and aggregate4MBUTF8 before semantic rendering. These bound
validation, not caller input parsing/allocation. Closed result/row keys accept
actual compare output and small legacy report input; unknown keys/non-dict rows
reject. Optional snapshot validates canonical integrity, but NOT row association,
opaque id binding, URL source ownership or actual observation truth. No metadata
or hash authenticates report contents. ids are opaque/unverified, never deletion
or sent-state authority. Baseline/unchanged must have no rows; no report sent.

Required id nonempty128chars, title200(default Page changed), summary12100chars,
URL canonical page-watch2048chars; The character caps bound UTF8 allocation; no distinct4x-character safety
claim. Unicode Cc/Cf/Zl/Zp controls and bidi formats rejected except
summary CR/LF/TAB. Other optional row fields strings256chars (summary_html80000)
or emailed exactbool. Unused fields never rendered, but malformed values reject.
No mutation or new fixed-source binding. Page-watch producer still emits fixed
Nilgiried labels for arbitrary accepted URL; caller must bind reviewed source.
No ID relation/comparison provenance proof follows from escaped HTML.

30 configured tests PASS across report/snapshot/parser,6new report tests:
compare integration, legacy golden bytes, script-title/summary escaping,
customhooks/bool/int no-coercion, malformed/bounds/closedrows/flags, no mutation.
Standalone bundle reproduces these tests. No live integration or UI claim.

Forged changed results can pass syntactic checks; IDs/URL never authorize
runtime wiring, disclosure, send or marking. Must bind provenance separately.
Snapshot diff falls back to omitted message for forbidden controls, not silent
text normalization; raw snapshot text/hash remain unchanged.
