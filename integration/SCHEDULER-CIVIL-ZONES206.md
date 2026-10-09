# 206: civil zone key validation for unit175

Host-dependent and leap-second variant keys are refused; real IANA aliases
are accepted subject to host availability. Zone data and the listing are
whatever the host/tzdata package provides, not verified current production data.
An older/minimal host may lack a legitimate alias and will refuse it (fail closed).

One shared helper validates the zone key in both profile_plan and local_clock.
Type must be exact str, nonempty, with no surrounding whitespace. Case-sensitive
exact keys localtime, posixrules and Factory are refused before any scan;
case-sensitive prefixes posix/, right/ and SystemV/ are also refused. right/UTC
is explicitly blocked as a leap-second variant. No normalization or broad
ban of legitimate alias trees is introduced. Remaining keys must belong to
zoneinfo.available_timezones(), minus the same explicit exclusions.

The accepted frozenset is cached per process on the first successful validation,
not at import. First use scans system timezone files and/or installed tzdata
resources through zoneinfo; subsequent use checks membership without rescanning.
No environment configuration, download or timer is added. An empty listing,
malformed listing, listing with no accepted keys or scan exception returns static
ScheduleRefused; failure is NOT cached, so the next call retries. A successful
listing remains cached even if a later requested key is not listed.
Reload/restart is needed to refresh the listing after host tzdata/TZPATH changes.
This is not a synchronized multiworker cache or a guarantee that concurrent first
calls scan only once; sequential validation uses one successful scan. The actual
ZoneInfo lookup is still required and may fail if a listed file is unusable.

Geo and BRICS settings use this same rule. local_clock now applies it even to
hand-built plan dictionaries with the expected scope; other prepared-plan fields
are still trusted as before, so this is not full forged-plan validation.
No return shape, weekday canonicalization, clock parsing, DST calculation,
profile selection, timer or caller is changed. No legacy scheduler is run.

205 source, tests and doc stay byte-unchanged. Its call into profile_plan inherits
the widened refusal. Its own three-key check remains redundant and harmless.
Its source provenance/calculation limitations still apply. Item25 remains open
until caller/engine/profile decisions and activation gates are reviewed. No
AppsScript/SMTP/collector/DB/live effect or201c change is introduced.

Tests add five methods to unit175: both profiles' exact/prefix refusals and
legitimate positives, direct local_clock refusal, cache count in both deny-first
and accept-first order, scan empty/raise then retry, and absent legitimate alias
fail-closed behavior. Tests reset/restore the per-process cache so mocks do not
depend on order. right/UTC is refused even if a mocked listing contains it.
Positives include UTC, Asia/Calcutta, Asia/Kolkata, America/New_York, US/Eastern,
GMT, Zulu, UCT, Etc/GMT+5 and EST5EDT on the tested host. Their presence is not a
claim that every host supplies them. Existing unit175 and all205 tests rerun.

The unchanged205 doc sentence "Unit175 alone still accepts those keys; its
independent follow-up remains open" is superseded by206's shared key validation.
