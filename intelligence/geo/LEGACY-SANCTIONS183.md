# Dormant legacy sanctions hold

The legacy CSV import and text screening now raise LegacySanctionsHeld rather
than returning an empty success or misleading substring match. No transport
imports or network calls remain in this module. No callers or activation added.

The former CSV selected the first column. OFAC's current data specification
identifies it as ent_num (identifier) and the second as SDN_Name. That defect is
not repaired by assuming a position without a reviewed complete schema fixture.
Substring checks also do not establish entity identity or sanctions status.

Official field evidence:
https://ofac.treasury.gov/system/files/126/dat_spec.txt
https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/tutorial-on-the-use-of-list-related-legacy-flat-files

A future parser/matcher needs schema, bounded transport, name/alias coverage and
reviewed matching before use. This change supplies no current list, last-good
cache, screening result, sanctions clearance or production-readiness claim.
The independent sanctions-refresh.mjs pipeline and its review policy are unchanged.
