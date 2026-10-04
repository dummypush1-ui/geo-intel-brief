# Offline collection cycle

`run_offline_cycle` connects supplied-candidate processing to an exact
`FakeCollectionWriter` instance. It is not a live collector or database adapter
and is not imported by the runtime. Categories, threshold, zoned clock and
synthetic failure URLs must be explicit. Reusing the same fixture writer allows
repeat-cycle duplicate tests. Separate Geo and BRICS maps stay separate.

The fixture writer uses slots, so instance method overrides are refused. The
cycle calls the class implementation directly and requires both internal maps
to be exact dictionaries containing bounded plain JSON before processing.
This is a trusted Python fixture, not a security sandbox against arbitrary
code that replaces class definitions or imported functions.

Candidates are checked as bounded plain JSON before processing. Writer batch
validation precedes fake-store changes. Processing exceptions propagate; they
are not reported as success. No transaction across projects is provided.

The limits in COLLECTION_PREPARE_LIMITS.md and FAKE_WRITER_LIMITS.md still apply:
copied processing rules may drift; URL identity is exact; field semantics are
not fully validated; nested container limits are not a total memory/CPU budget;
failures are synthetic and do not model real MongoDB errors, races or indexes.
No source-policy approval, real collection mapping, runtime wiring, scheduler,
alerts, mail, migration, live write or old-app shutdown is added by this module.

The reviewed entry point is run_offline_cycle only. Direct calls to
prepare_candidates or FakeCollectionWriter.snapshot/write have weaker type
boundaries, including subclass hooks. Keep them internal and harden them before
wiring any other caller. The cycle validates clock and synthetic failure URLs
in write(), after pure preparation; invalid values raise before fake-store
changes, but preparation can occur first. Geo extraction remains unwired.
