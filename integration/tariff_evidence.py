"""Passive tariff-document evidence ledger. Independently written (c)2026 Push.

A supplied reviewed-document row is not a current-rate recommendation. No
fetch, DB, monitor, legal inference or delivery. Trusted operator review and
source retrieval happen outside this pure data adapter.
"""
from datetime import datetime,date,timezone
from urllib.parse import urlsplit
import re,unicodedata,json

# Exact official publisher hosts selected from inspected official publications.
HOSTS={'IN':{'www.cbic.gov.in','cbic.gov.in','www.indiabudget.gov.in'},
       'US':{'www.usitc.gov','hts.usitc.gov','www.federalregister.gov'},
       'EU':{'eur-lex.europa.eu','taxation-customs.ec.europa.eu','ec.europa.eu'}}
FIELDS={'id','jurisdiction','nomenclature','edition','codes','document_id','source_url','published_date','effective_dates','excerpt','conditions','review_state','reviewed_at'}

def text(v,maxlen):
    return type(v) is str and bool(v.strip()) and len(v)<=maxlen and not any(unicodedata.category(c)[0]=='C' for c in v)

def legal_date(v):
    if type(v) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',v):raise ValueError('Exact calendar date required')
    return date.fromisoformat(v).isoformat()

def official_url(value,jurisdiction):
    if type(value) is not str or len(value)>1000 or any(c.isspace() or ord(c)<32 or c in '\\%' for c in value):raise ValueError('Safe exact official URL required')
    u=urlsplit(value)
    if u.scheme!='https' or u.hostname not in HOSTS[jurisdiction] or u.username or u.password or u.port not in (None,443) or u.fragment:raise ValueError('Exact official publisher URL required')
    return value

def canonical_stamp(value):
    if type(value) is not str or not 1<=len(value)<=64:raise ValueError('Bounded zoned timestamp required')
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None or not 1970<=d.year<=2100:raise ValueError()
        d=d.astimezone(timezone.utc)
        if not 1970<=d.year<=2100:raise ValueError()
        return d
    except (ValueError,OverflowError):raise ValueError('Bounded zoned timestamp required') from None

def plain_row(item):
    if type(item) is not dict or len(item)!=len(FIELDS) or any(type(k) is not str for k in item) or set(item)!=FIELDS:raise ValueError('Exact evidence fields required')
    out={}
    for key,value in item.items():
        if key in ('codes','effective_dates'):
            cap=100 if key=='codes' else 20
            if type(value) is not list or len(value)>cap or any(type(v) is not str or len(v)>12 for v in value):raise ValueError('Bounded plain evidence list')
            for v in value:
                try:v.encode("utf-8")
                except UnicodeError:raise ValueError("Invalid evidence list text") from None
            out[key]=list(value)
        elif key=='reviewed_at' and value is None:out[key]=None
        elif type(value) is str and len(value)<=2000:
            try:value.encode('utf-8')
            except UnicodeError:raise ValueError('Invalid evidence text') from None
            out[key]=value
        else:raise ValueError('Plain evidence values required')
    return out

class TariffEvidenceSnapshot:
    __slots__=('_observed_at','_items')
    def __init__(self,observed_at,items):
        stamp=canonical_stamp(observed_at)
        if type(items) is not list or len(items)>1000:raise ValueError('Bounded supplied list required')
        normalized=[];seen=set();total_bytes=0
        for item in items:
            r=plain_row(item)
            for k,cap in [('id',100),('nomenclature',80),('edition',100),('document_id',200),('excerpt',2000),('conditions',1000)]:
                if not text(r[k],cap):raise ValueError('Bounded evidence text required')
            if r['id'] in seen:raise ValueError('Duplicate evidence identity')
            seen.add(r['id'])
            if type(r['jurisdiction']) is not str or r['jurisdiction'] not in HOSTS:raise ValueError('Reviewed jurisdiction required')
            official_url(r['source_url'],r['jurisdiction'])
            if type(r['codes']) is not list or len(r['codes'])>100 or any(type(c) is not str or not re.fullmatch(r'[0-9]{2,12}',c) for c in r['codes']) or len(set(r['codes']))!=len(r['codes']):raise ValueError('Exact separate code strings required')
            r['published_date']=legal_date(r['published_date'])
            if type(r['effective_dates']) is not list or len(r['effective_dates'])>20:raise ValueError('Explicit effective date list required')
            r['effective_dates']=[legal_date(v) for v in r['effective_dates']]
            if type(r['review_state']) is not str or r['review_state'] not in ('candidate','document_reviewed'):raise ValueError('Explicit review state required')
            if r['review_state']=='candidate':
                if r['reviewed_at'] is not None:raise ValueError('Candidate cannot claim review time')
            else:
                if type(r['reviewed_at']) is not str:raise ValueError('Review time required')
                review=canonical_stamp(r['reviewed_at'])
                if review.tzinfo is None or review.astimezone(timezone.utc)>stamp.astimezone(timezone.utc):raise ValueError('Review time cannot exceed capture')
                r['reviewed_at']=review.astimezone(timezone.utc).isoformat()
            # Sum of compact UTF8 NORMALIZED rows, excludes envelope/separators.
            total_bytes+=len(json.dumps(r,ensure_ascii=False,separators=(",",":")).encode("utf-8"))
            if total_bytes>2_000_000:raise ValueError("Evidence snapshot bytes")
            normalized.append(r)
        self._observed_at=stamp.astimezone(timezone.utc).isoformat();self._items=normalized

    def view(self,now,jurisdiction=''):
        if type(now) is not datetime or type(now.tzinfo) is not timezone:raise ValueError('Explicit zoned clock required')
        if type(jurisdiction) is not str or jurisdiction and jurisdiction not in HOSTS:raise ValueError('Known jurisdiction required')
        age=(now.astimezone(timezone.utc)-datetime.fromisoformat(self._observed_at)).total_seconds()
        if age<0:raise ValueError('Future capture rejected')
        items=[r for r in [plain_row(r) for r in self._items] if not jurisdiction or r['jurisdiction']==jurisdiction]
        items.sort(key=lambda r:(r['published_date'],r['id']),reverse=True)
        return {'state':'supplied_document_evidence','observed_at':self._observed_at,'age_seconds':int(age),'items':items[:100],'total_supplied':len(items),'truncated':len(items)>100,'limit':100,'scope':'supplied_evidence_not_complete_tariff_history','current_rates_verified':False,'legal_effect_independently_verified':False,'network':False,'delivery':False,'polling':False}
