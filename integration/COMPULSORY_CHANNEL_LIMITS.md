# Compulsory channel preview

Republic is the sole admin-defined compulsory channel. Its existing configured video ID is retained, not verified currently live. Al Jazeera English, France24 English, DW News and ANI News are removable defaults. Up to 20 additional/removable channels use local browser settings only; the fixed record is always composed from code, never localStorage. This is a preview configuration, not multi-user roles/auth or tamper-proof enforcement against someone editing the app itself.

Legacy saved full lists migrate in memory by removing any duplicate of the Republic video ID and retaining its configured admin name. A saved empty list means Republic alone. No DB writes, remote persistence, alerts or timers. Per-user saved settings wait for reviewed login/storage design. Existing URL validation, delayed player creation, muted playback and YouTube fallback are retained.
