# 225: composed supplied preflight DATA only

A pass means "these supplied rows and these supplied bytes agree". Nothing about
an authenticated read, history completeness, freshness, current inactivity,
delivery or authority. A wholly invented self-consistent graph and matching blob
passes. Omitted and stale inputs can pass. Sender scope 222 is not consumed, so
this preflight is NOT a send gate. All prior open items remain open.

OFF is static before arguments or imports. ON accepts the closed field union of
221's renderer/snapshot inputs and 224's native inputs. There is no supplied
exclusion_projection, stage result, sender scope or recipient list parameter.
Extra fields refuse. No default fingerprint, nonce, history or native rows.
Closed argument check, exact list caps (1000 rows, 128 receipts, 10000 articles)
and three exact tuple receipt caps (10000 each) precede imports, copying or sort.
Subclasses of those containers refuse. Stage owners check the remaining types.

224 runs first with the explicit native rows, fingerprint and history manifest.
Its projection object alone goes directly to 223, once. 223 owns the chain into
221 and 218/219. No separate body generation, cached stage result or override.
No 223 call if 224 refuses. No partial success result. Fingerprint/nonce/native
inputs are forwarded by identity without conversion or defaults. The displayed
receipt tuples are never altered to fit the derived projection.

224 includes EVERY acknowledged article in the supplied graph, even articles
whose old receipts are not supplied. 223 requires the email tuple to equal that
FULL set exactly. Subsets and supersets refuse. Telegram/whatsapp tuples are
validated but not unioned; their IDs remain unexcluded in an email candidate.
The supplied graph is the sole source of the email exclusion set here. This says
nothing about whether that set is real history.

Input container structure is copied recursively for a deep comparison after both
stages, retaining scalar identity to avoid unvalidated scalar deepcopy hooks.
Immutable scalar types are validated by their owning stages. No stage may mutate
any caller input, including native rows or displayed receipts. Depth is bounded.
Only ON imports are copy, 224 and 223; no 212 import or enabled ledger constructor.

One fixed error is raised outside except with no upstream text, cause or context.
The output is constant state/preflight_match/note and False flags only. No stage
result, projection, channel, IDs, counts, hashes, body or native data is returned.
Flags send_allowed, ready, owner_approval, source_authenticated, history_verified,
current_state_verified, receipt_membership_verified, source_complete, durable,
ledger_wired and production_wired remain False.

No production caller edge, DB read/check/write/create, send, ledger mutation,
store, environment/property change, deployment, trigger, activation, mount or
cutover. Apps Script selected, SMTP fallback held, 217 held and 201c write held.
Sender blocker 222, authenticated native read, history authority, provenance,
durable body and owner-approved recipients and words remain open.
