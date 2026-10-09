# Optional bcrypt private preview verification

Stored PREVIEW_PASSWORD_HASH may be exact$2b$ cost10-14 canonical60chars, bcrypt5.0.0.
Legacy scrypt/PBKDF2 remains compatible and unchanged. Existing defaults stay OFF.
No hash migration, password changes, secret generation, account activation or
public login. Do not treat bcrypt as an upgrade over scrypt: OWASP recommends
Argon2id/scrypt first, bcrypt for compatibility. Keep config/cost review separate.

Password1-72UTF8bytes, rejectoversize insteadtruncate/prehash. Strictboundedformat
before import/hashing; canonicalterminalsalt/checksum bits, exactversion checked.
No expensive startup hash. Existingserialslot/ratequota/CSRF/cookie/logout retained.
Verifiererrorsfixed503,releaseslot,no exceptionsecretlogging. Hashes/environment
must still be set by owner securely; no exposure/rotation effect in this unit.

Publishedbinarywheel5.0.0downloadedfromPyPI,hashmatchesreleaseJSON; Apache2license
inspected, no runtime dependency; optionaltest/typecheck extras notinstalled.
Installedlocallywheel/no-sourcebuild,realcheckpwsmoke/tests;pip-auditnewdependency
only5.0.0returnedno-known-vulns. Notwholeappsecurityproof or reproduciblebuildclaim.
requirements-staging exactpin. Historical25packageofflineaudit/build records stay
unchanged; bcrypt is supplemental pinned_addition inventory with ownreceipt, not
silently added to old lock. requirements-future-deploy.lock oldlockdoes NOT install
bcrypt; don'tselectbcryptconfigonthatlockuntilseparatereviewedlockrefresh. No wheel
vendored, production/platforminstallation must use reviewed package index/artifact.

Sources:
https://pypi.org/project/bcrypt/
https://github.com/pyca/bcrypt/blob/5.0.0/README.rst
https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
