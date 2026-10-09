# 204: inert legacy SMTP profile configuration adapter

This unit adds `smtp_config204.profile_plan(settings)` and
`binding_data(settings)`. Neither function constructs a sender, TLS context,
connection or capability. No caller uses this adapter yet. AppsScript remains
selected; SMTP fallback and activation remain held. No environment reads,
credential handling, timers, DB writes or sends are introduced.

## Closed input and output

Input is an exact built-in dict. Only `profile`, `host`, `port`, `mode`,
`timeout` keys are accepted. Unknown keys are refused, including credential,
address, environment, enable and TLS weakening options. Profile is exactly
`geo` or `brics`. No normalization, aliases or case folding are applied.
Missing means a missing key, not None or an empty value. Host is required.

| Port | Mode | Outcome |
| --- | --- | --- |
| absent | absent | pinned profile default |
| present | absent | refuse |
| absent | present | refuse |
| present | present | unit174 pair validation |

Values explicitly equal to defaults are accepted as an explicit pair.
Geo defaults to implicit TLS/465; BRICS defaults to required STARTTLS/587.
The two reviewed pairs are accepted for either profile when explicitly set.
Ports accept exact built-in int or canonical ASCII nonzero decimal str,
1..65535. No bool, float, whitespace, leading zero, sign or Unicode digits.
Unit174 then limits ports to the reviewed 465/587 pairs.

Host is an ASCII DNS-style hostname (single labels such as localhost allowed),
1..253 characters, labels 1..63 characters, alphanumeric edges and internal
hyphens only. No trailing dot, scheme, userinfo, port, path, whitespace,
controls or IDN Unicode. IP literals and all-numeric dotted spellings are
refused, including noncanonical IPv4. No DNS lookup is done. Timeout is an
exact int, 1..30 seconds, default 30; bool and float are refused.

"Redacted settings" here means secret-free by input exclusion, not masking:
the output contains only validated profile, hostname, TLS mode, port and
timeout, provenance and fixed policy/hold metadata. Hostnames are returned
unchanged and may be private; output is not claimed safe for public logging.
Exceptions contain only static text, never supplied keys or values. The module
prints nothing. Invalid profiles, including secret-looking values, are refused.
Only exact built-in scalar values are accepted before the input is deep-copied;
no custom deepcopy hooks are run. Results are independent plain dictionaries.
Binding returns only future scalar sender arguments. It supplies no credentials,
addresses or enabled flag, and must not be described as making legacy code safe.

## Pinned source provenance

Original files read from GitHub default branches on 2026-10-09. SHA256 values
below hash the exact UTF-8 file content returned, not a JSON response. These
are source snapshots, not a claim that originals will remain unchanged.

- push2006/geonews `config.py`, lines 50-51: host smtp.gmail.com, port465.
  SHA256 `f7fbf007954c6918fbe2e402863fa29f597fe5d5cb4d60d1001deca8896b21f3`.
- push2006/geonews `reports/email_report.py`, line170: SMTP_SSL with context.
  SHA256 `30d7552def0e9d56f8981f25b3d81ed3475bcc354971aea304a30e6f7d583688`.
- push2006/BRICS- `config.py`, lines29-30: host smtp.gmail.com, port587.
  SHA256 `2419339566c5946dd0daeae7147eba7a49dffdd379b3c34769d6d62860afc82d`.
- push2006/BRICS- `reports/email_report.py`, lines59-60: SMTP then starttls.
  SHA256 `6582d81d184e2c18842f1507d7e46042514c9d0cfbfea7e1202ce8bf1218ac65`.

The adapter does not watch originals. Later upstream default changes are
unnoticed. Tests pin both constants; no live configuration imports are used.

## TLS safety and tests

Unit174 transport_plan supplies hostname verification, no plaintext fallback,
AppsScript-not-replaced and runtime_activation=False. No weaker option exists
in this adapter. Existing reviewed delivery code creates a default verified
SSL context. STARTTLS is called before credentials; an unsupported STARTTLS
raises and prevents login/send, never falling back to plaintext. A mock-only
unit204 test exercises that refusal using returned binding data. This is a
source contract check, not a real-server compatibility or send approval.

Tests cover the complete mixed table, pinned defaults, explicit overrides,
pair refusal, strict ports/modes/hosts/timeouts, closed keys, canary-secret
non-echo, independent output and deep copy, AST import allowlist and patched
socket/getaddrinfo refusal during import and both functions. No network test
or SMTP effect is needed. Unit174 tests run alongside this unit.

## Not closed

Per the snapshot and smtplib source, legacy BRICS STARTTLS calls
server.starttls() without a context (email_report.py line60), falling back to
ssl._create_stdlib_context without certificate/hostname verification; this
weaker legacy path stays live outside this unit as a standing hazard for the
owner's BRICS decision, while landed174 uses create_default_context with
verification (the original BRICS code was not run).

BRICS direct send() remains live code outside this contract. No runtime caller
uses the adapter. Item24 stays open until a reviewed runtime caller and BRICS
exclusion decision exist. Original configurations/callers are unchanged.
No legacy path is made safe by this adapter. SMTP fallback remains unselected
and held; no environment activation, role changes, cutover or live effects.
201c remains held. Source audit and indexed LAND review are separate gates.
