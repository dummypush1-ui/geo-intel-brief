Item17 source/runtime fix149. No execution or deployment in this change.
Source changes are prepared in memory. DRY does not write source chunks/maps,
generated files, temporary build files or Git; configured Comtrade and Gemini
calls can still happen when an operator later runs it with keys. DRY is not an
offline switch. Tests replace fetch and never use keys or network.
Non-DRY builds in a disposable snapshot. Source checkout remains unchanged even
if build/Git fails. Missing Git identity config prepares only, not local rebuild.
With configured Git, clean tracked checkout HEAD must equal captured remote HEAD
before reads and again before publish. One tree contains source edits,index,
offline,SW and one exact SHA256-named datafile. Only old root data.<12hex>.js
paths from the complete prior remote tree may be deleted. No other delete path.
Non-force ref update uses a commit parented on captured base. Concurrent sibling
branch move rejects rather than overwriting. Commit/ref failure is not retried;
uncertain ref response needs manual readback/reconciliation. Local snapshot can
remain stale after successful publication; next run holds until checkout matches.
Root Finder assets remain root Finder assets. Integration Geo HOME is untouched.
Actual regenerated dataset history/source matching is item18, not proven here.
No preservation hash exception, activation, provider key or trigger changes.

Operator recovery: after publication re-pull or redeploy the committed remote
HEAD into a clean Git checkout before the next publication run. Stale/dirty
checkout is intentionally held, not rebased automatically. Missing .git/HEAD
fails at preflight with a fixed explanatory message before provider requests.
A failed/timed-out PATCH may already have landed; inspect remote HEAD and the
created commit before doing anything else. No automatic resend/retry.
Static build.mjs inspection: input reads are exclusively src/ files and
vendor/pako-inflate.min.js; it reads no root templates/package/config. The
disposable copy list src/,vendor/,build.mjs covers that exact build surface.
