Item20 pure source edit guard, not tax grounding approval.
GST replacement uses a function, preserving $ forms literally. $1 was already
literal in the original noncapture regex; $&/$backtick/$apostrophe were not.
Exact single declarations/final terminators; loose same-code row count refuses
nonstandard indentation instead of inserting a duplicate. Insert adds missing
last-row comma. Closed change schema accepts 2/4/6/8-digit codes, finite rate
syntax <=100%, nonempty bounded/control-free descriptions and known source URL.
Proposer emits only code/rate/description/source through that same validator;
invalid row shape is counted as rejected and skipped, allowing other rows to
continue. The rejected count is included in the job result. Strict applyGst
validation still refuses a malformed stored proposal before output writes. Grounding
errors/2digit scope are still item21, not settled by syntactic validity.
Alias filter and helper share exact ^[a-z][a-z0-9 -]{1,38}$ and word-set bounds.
Failed edit validation writes nothing; counts follow verified pure result, not
an attempted replacement. Scripts are not run live here. apply-gst is local
PR preparation only; merging rates still requires review. Actual write/disk
failure is reported by the filesystem; multi-file durability is not claimed.
