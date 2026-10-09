# Optional GNews and event source checks

GNews uses the provider's `published date` field through the shared strict
publication-date policy. Missing, invalid, incomplete, naive/unknown-zone and
future values produce no candidate. Observation time is only a validation bound,
never the publication date. Known dates are stored in UTC ISO form. No provider
calls or GNews activation were made. ENABLE_GNEWS remains false by default.

Field evidence read from the provider source and README:
https://github.com/ranahaani/GNews/blob/master/gnews/gnews.py
https://github.com/ranahaani/GNews/blob/master/README.md
This documents current upstream field semantics, not certification of an installed
optional SDK version. Alternate backends or missing fields fail held rather than
using a synthetic time. No durable quarantine or source-completeness claim.

EVENTS is empty, not a fabricated placeholder. save_event requires a nonblank
name (at most 512 characters) and canonical valid YYYY-MM-DD before connecting.
Additional event fields remain compatible. This is minimum write validation,
not independent verification that a real event exists. Existing events were not
edited, deleted, loaded or reseeded.

collector120's inactive supplied-data adapter tracks reviewed source bytes and
accepts the actual publication field. Its fixtures now supply real synthetic
publication evidence instead of relying on the old fake-now behavior. Historical
stage evidence remains historical; no installed SDK/transport/schedule proof.
