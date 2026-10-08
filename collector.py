"""Single entry for the inactive Geo collector chain (effective stage 130 closure).

Additive facade: re-exports the reviewed stage objects unchanged, so behavior is
identical to importing them from the collector1NN_prep packages. Nothing is
copied, edited, started or imported at runtime elsewhere, and nothing here
touches the network, environment or database. Live collection stays off.

SUPERSEDED stage copies (kept for hash-pinned history, not used by this chain):
collector115 profile/composition, collector116/123/127 network_selection,
collector114/124 duplicate runner, collector126 extra_profile, collector128/112
duplicate parser runner.
"""
from collector110_prep.input_budget import capture
from collector113_prep.feed_composition import original_catalog
from collector113_prep.transport_policy import endpoint_plan, decode_response
from collector124_prep.runner import run_fetch, FetchRefused
from collector128_prep.parser_runner import parse_supplied_bytes, ParserRefused
from collector129_prep.supplied_feed import prepare_supplied_feed
from collector130_prep.base_profile import compile_profile, defaults, ProfileRefused
from collector130_prep.extra_profile import compile_installed_profile, ExtraFeedsRefused
from collector130_prep.network_selection import select_installed_source, SelectionRefused

CHAIN_MODULES = (
    'collector110_prep.input_budget',
    'collector113_prep.feed_composition',
    'collector113_prep.transport_policy',
    'collector124_prep.runner',
    'collector128_prep.parser_runner',
    'collector129_prep.supplied_feed',
    'collector130_prep.base_profile',
    'collector130_prep.extra_profile',
    'collector130_prep.network_selection',
)
__all__ = ['capture', 'original_catalog', 'endpoint_plan', 'decode_response', 'run_fetch',
           'FetchRefused', 'parse_supplied_bytes', 'ParserRefused', 'prepare_supplied_feed',
           'compile_profile', 'defaults', 'ProfileRefused', 'compile_installed_profile',
           'ExtraFeedsRefused', 'select_installed_source', 'SelectionRefused', 'CHAIN_MODULES']
