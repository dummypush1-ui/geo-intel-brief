# Explicit local stream file CAS, no activation

DiskStreams needs an explicit reviewed absolute path to an existing operator-
prepared file in an owned private directory. No default/live path, mkdir,
initial config, route, environment selection, network or status polling. This
increment tests temporary directories only. Render ephemeral storage is NOT
claimed durable: a persistent volume, path ownership, backups and permissions
must be verified before activation. It never changes the user's live config.

Linux nonblocking flock on an adjacent 0600 lock file serializes cooperative
writers on one host. Lock covers load, SHA expected revision, reviewed revise
transform, same-directory 0600 temporary file, fsync, atomic replace and parent
fsync. Busy and stale requests are refused, never silently overwrite. Read
snapshot also takes lock. Existing original parser/grammar and expected-revision
transform reused. Changed YAML loses comments/format, reported in result.

Bounded 16KiB regular single-link owner-only file; O_NOFOLLOW refuses final
symlink. Constructor checks parent chain and private immediate directory. This
is not hostile shared-directory safe: parent replacement/rogue noncooperative
writers/lock deletion/path races can bypass cooperative protocol. No distributed
or multi-host filesystem guarantee. A no-op preserves raw bytes; its result says
fsync completed local only, but does not perform a new sync because no write.

Pre-replace failures leave old file untouched and remove temp. After replace,
fsync failure is uncertain: new bytes may be present but durable-on-crash not
proved, no retry. Caller must read back under separate authority if needed.
Actual power loss/filesystem crash/NFS/Render volume were not tested. Cleanup
and descriptor close best-effort, no hostile syscall sandbox.

9 tests local and extracted: read/write/restart, permission, stale revision,
replace failure/temp cleanup, directory fsync uncertainty, symlink/unsafe mode,
invalid transform, busy lock, no-op and two-process same-revision race.
Repro python -m unittest tests.test_stream_disk -v with PyYAML 6.0.2 and existing
integration tree. Stream availability remains not_checked; no UI or accounts
wiring. This is storage preparation, not the finished merged application.

Review SAFE for trusted-local-operator scope (9/9). Busy and invalid source
both return the same coarse unavailable error, intentionally indistinguishable.
The adjacent .lock file persists and may be created even if the source later
fails validation. Lock identity is not tied to data-file inode; all cooperating
writers must use the same path and leave its lock file in place. External
replacement/deletion is outside this trusted-directory scope. BaseException
inside read/update is converted after cleanup; after replace it is uncertain,
including KeyboardInterrupt.10 final local tests include that regression.
