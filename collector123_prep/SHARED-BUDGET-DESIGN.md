# Inactive shared budget composition candidate

Original114 fetch supervisor plus original112 isolated parser runner, modified
parser to accept bounded remaining timeout and kill/reap process group on failure.
116 composition starts25s monotonic budget before profile, forwards remaining
budget to fetch and parser, refuses parser start after expiry, discards selected
result if completion check is expired. No real fetch/network/send/store.

This is not hard whole-request supervision. Trusted in-process profile, hash,
selection/capture, JSON parsing and cleanup can pass25s before the next boundary
check. Thread/request timeout cannot kill those phases. Hard request supervision,
original configuration parity, real runtime bubblewrap capability/deployment,
transport unframed truncation/header behavior/pins, per-cycle budgets remain gates.
Scratch parser code reads the fixed local original installation directory solely
to exercise current isolation; installation path must be package-relative+reviewed
if staged. No caller-selected path. Earlier source files unchanged.

Staging: parser BASE now package-relative fixed collector112_prep sibling path;
network_selection imports its own relative parser; tests use package imports.
Not mounted into app. No original112/114/116 files or pins changed.
