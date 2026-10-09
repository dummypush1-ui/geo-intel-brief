"""Dormant legacy screening is held, not a verified sanctions data service.

The old CSV routine used an identifier as a name and substring matches were
not entity screening. No callers or activation are added. The independent
sanctions-refresh.mjs pipeline is outside this legacy module and unchanged.
"""

class LegacySanctionsHeld(PermissionError):
    """A hold is not a successful empty list or a clean screening result."""


def update_ofac_names():
    raise LegacySanctionsHeld('Legacy sanctions CSV import held: reviewed schema and source installation required')


def screen_text(text, names):
    raise LegacySanctionsHeld('Legacy sanctions screening held: reviewed name matching required')
