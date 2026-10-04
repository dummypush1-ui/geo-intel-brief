"""Shared public news boundary. Independently written (c)2026 Push.

Only exact canonical approved field names pass. Case variants of private OR
public keys never upgrade into canonical fields; case-insensitive collisions
are omitted rather than selecting an ambiguous field. Values are deep copied.
"""
from copy import deepcopy
PUBLIC_NEWS_FIELDS=('article_key','project','url','title','summary','source',
 'original_country','category','published_at','collected_at','risk_level',
 'credibility','score','corroboration_count')

READ_STORE_FIELDS=('_id','id','url','title','summary','source','country','category',
 'published','created_at','collected_at','risk_level','credibility','score','corroborated_by')

def public_news_row(row):
    if type(row) is not dict:raise ValueError('Plain news row required')
    folded={}
    for key in row:
        if type(key) is str:folded.setdefault(key.casefold(),[]).append(key)
    return {key:deepcopy(row[key]) for key in PUBLIC_NEWS_FIELDS
            if key in row and folded.get(key.casefold())==[key]}
