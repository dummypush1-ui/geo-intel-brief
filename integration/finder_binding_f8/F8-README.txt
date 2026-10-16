F8: isolated package/root/proof identity binding prerequisite, not public cutover

Default OFF MERGED_FINDER_BINDING_PREP_ENABLED=false. OFF before any file read.
ON takes an internal archive path, expected SHA256 and already staged root. No
HTTP/env source path or hash selector. The expected hash is a review reference,
not proof anyone approved the contents or public disclosure. No permission is
created by constructing Binding or ProofProfile. Operator review and eventual
owner-approved activation remain separate gates. Caller paths are in-process
review/test seams. No output path, archive extraction, provider/DB/credentials,
scheduler or deployment; module only reads. Work off Render in an offline review
worker. File hashes stream in64KiBchunks, but existing candidate derivation still
has the F7memory requirements. Source and artifact paths must be regular files
without symlinked parents. A mutable staged root is never a freshness promise.

Closed F7package:15sorted unique entries, fixed14payload names with one exact
fingerprinted data bundle;40MiBcompressed,140MiBdeclared total,64MiBper entry,
2MiBJSON. ZIP normal regular-file permissions, DEFLATED, no encryption. Expected
ZIP hash and entry reads use the same opened archive descriptor. Each payload is
streamed and SHA256/length checked (ZIP CRC errors hold). DuplicateJSONfields,
unknown manifest keys, old/new source/edition/index/render/receipt mix rejected.
Original upstream2files SHA256 and GitblobSHA1 match the F3receipt and F2report;
receipt source/baseline and0sanctions-removals match. This checks the supplied
receipt, not a fresh GitHub acquisition or proof of current official accuracy.
The full staged root matches every14payload hash/length. Files outside those
names are not selected and none are served by this unit.

FinderProof now accepts an explicit frozen ProofProfile of6source pins, exact
HS/INeditions and binary artifact SHA. Default constructor/verify_sources keeps
existing last-good globals/source behavior. Profile pins/editions closed and
immutable; every lookup rehashes its own6sourcefiles and binaryproof using the
existing boundedpread/search/leaflock. Profile proof rejects symlinked source
parents and artifact, invalid/duplicate records, source/artifact drift and
cross-edition identities. Default old and candidate new instances coexist
without modifying any module globals. Non-numeric/unsupported/ambiguous
identities stay refused; preserved labels remain edition_verified=false.

Real held F7ZIP4648c425...01c90 and stagedroot passed all14payload checks.
CandidateINsnapshot:aa056ad4e0cf and oldINsnapshot:d6d1b417562b simultaneously
bound090121 with the same normalizeddescription, each rejecting the other's
edition. Same binaryproof SHA is not inferred identity across editions; each
instance still checks its own explicit source/indexpins at every lookup.

This closes only the immutable proof-identity prerequisite, not atomic18consumer
composition. No news_api/builder/publicroute/UIedition/PWAcache changed. The
remaining consumer matrix is in ATOMIC-CONSUMERS.txt. Independent review of
composition must tie all consumer choices to one Binding and fail construction
on any missing participant. Existing public last-good defaults stay unchanged.

Review caveats: rejecting every symlink in the root parent chain can also reject
legitimate symlinked mount layouts; use a real regular staging path rather than
weakening that boundary. Provenance is read whole after the64MiBZIPentry cap,
then its2MiBJSONcap is checked, so a refused oversized receipt can still briefly
allocate up to64MiB. proof() rehashes all14rootpayload files on every call before
constructing the bounded6source/binary proof; repeated calls are not free and
should not be used as a per-request factory in a web process.
