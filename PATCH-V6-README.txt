HSN Finder patch v6 - India HSN/SAC master + search fixes (2026-09-22)
======================================================================
WHAT CHANGED
1. DATASET (all 66 datachunk files - replace every one):
   - 310,632 codes now (was 265,169 in your repo). This syncs your repo with the
     live app dataset: Hong Kong, South Africa and Peru were missing from the repo.
   - India HSN refreshed from the official GST-portal HSN/SAC workbook you sent:
     +145 new 8-digit lines, 10 description updates.
   - NEW: India SAC services codes (681 codes, chapter 99) - construction, legal,
     transport services etc. now searchable by code AND name, no captcha.
2. src/app.js:
   - Exact national codes (7+ digits) show as a DIRECT-HIT first row with an
     "exact match" badge (India lines first). Example: 27101939 now opens the real
     India line (Aviation Turbine Fuel) instead of hiding under 271019.
   - Codes with NO match fall back to the 6-digit international root (then the
     4-digit heading) with a plain note explaining the fallback.
   - HSN vs international HS compare block on India detail pages (both wordings
     side by side when they differ).
   - 20th system chip: SAC. Dataset build tag bumped (gen15).
3. src/aliases.ts: 31 trade short names now resolve (hsd, lpg, ms, atf, pvc,
   hdpe, ldpe, pp, pet, abs, tmt, gi, cng, png, furnace oil, ev, solar panel...).

HOW TO APPLY
Upload src/ over your repo's src/ (all 68 files). Commit. 2 min, fresh tab.
build.mjs and automate.mjs do NOT change this time. Comtrade key stays in the
Actions secret. NOTE: please do NOT paste AI keys into src/app.js - the repo is
public; use the in-app key box. Rotate the keys you already committed.

PROVENANCE
HSN/SAC master: official GST portal workbook (user-provided xlsx, 22 Sep 2026).
Everything baked in - no live calls, no captcha.
