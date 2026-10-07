"""Inactive installation profile parity candidate; no env/network/client reads.
Supplied allowlist is structural installation input, not proof of user approval.
"""
from .base_profile import compile_profile,ProfileRefused
from collector113_prep.transport_policy import endpoint_plan
from collector109_prep.fetch_stage import _valid_feeds
class ExtraFeedsRefused(ValueError):pass

def compile_installed_profile(settings,*,reviewed_extra_urls=()):
 if type(settings)is not dict or any(type(k)is not str or type(v)is not str or len(v)>2000 for k,v in settings.items()):raise ExtraFeedsRefused('Exact bounded installation settings')
 if type(reviewed_extra_urls)is not tuple or len(reviewed_extra_urls)>32 or any(type(u)is not str for u in reviewed_extra_urls)or len(set(reviewed_extra_urls))!=len(reviewed_extra_urls):raise ExtraFeedsRefused('Frozen distinct installation allowlist')
 base={k:v for k,v in settings.items()if k!='EXTRA_RSS_FEEDS'}
 p=compile_profile(base)
 extras=[u.strip()for u in settings.get('EXTRA_RSS_FEEDS','').split(',')if u.strip()]
 if len(extras)>32 or len(set(extras))!=len(extras):raise ExtraFeedsRefused('Duplicate/oversized configured extras require review')
 if any(u not in reviewed_extra_urls for u in extras):raise ExtraFeedsRefused('Configured extra URL not in installation allowlist')
 # Validate even unused manifest entries so dormant unsafe URLs cannot linger.
 for u in reviewed_extra_urls:
  endpoint_plan((('Custom',u,'MEDIUM'),),u,('8.8.8.8',),'8.8.8.8')
 feeds=p['feeds']+tuple(('Custom',u,'MEDIUM')for u in extras)
 _valid_feeds(feeds)
 for _,u,_ in feeds:endpoint_plan(feeds,u,('8.8.8.8',),'8.8.8.8')
 p['feeds']=feeds;p['scope']='inactive_installed_extra_feed_profile';p['configured_extra_count']=len(extras)
 p['pending_gates']+=['installation_allowlist_owner_review','extra_feed_live_availability','max_items_above200_resource_policy']
 p['allowlist_authority_verified']=False
 return p
