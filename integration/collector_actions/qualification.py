"""Maximum bounded local processing and driver serialization, no DB writes.
Runs inside the same nonroot guard. Live preflight reads independently check
Mongo role/index/ledger before measurement, then close. Fake insert receives
actual writer copies and BSON encoding but never opens a DB connection.
"""
from datetime import datetime,timezone
from types import SimpleNamespace
import copy
from bson import BSON
from integration.geo_collector_contract import prepare_geo_documents
from integration.geo_article_writer import GeoArticleWriter
from integration.collector197_coverage import CoverageCheckpoints,coverage,catalog_fingerprint
from collector109_prep.checkpoint import run_inputs
from collector110_prep.input_budget import capture,InputRefused
from collector113_prep.feed_composition import original_catalog

class CheckpointFixture:
    def __init__(self):
        self.rows={}
        self.write_concern=SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000})
        self.read_concern=SimpleNamespace(document={'level':'majority'})
    def update_one(self,q,u,upsert=False):
        BSON.encode(u['$setOnInsert']);self.rows.setdefault(q['_id'],copy.deepcopy(u['$setOnInsert']))
        return SimpleNamespace(acknowledged=True)
    def find_one(self,q):return copy.deepcopy(self.rows.get(q['_id']))

class InsertFixture:
    def __init__(self):self.count=0
    def insert_many(self,docs,ordered=False):
        # Serialize and retain maximum batch copies, matching writer's driver
        # boundary. Synthetic acknowledgments are never real insert evidence.
        encoded=[BSON.encode(d)for d in docs];assert sum(map(len,encoded))<=3*1024*1024
        self.count=len(docs);return SimpleNamespace(acknowledged=True,inserted_ids=list(range(len(docs))))
class ClientFixture:
    def __init__(self,c):self.c=c
    def __getitem__(self,name):
        if name=='geo_intel':return self
        if name=='articles':return self.c
        raise ValueError()

def maximum_processing():
    stamp=datetime(2026,1,1,tzinfo=timezone.utc)
    rows=[{'title':('Trade tariff '+str(i)+' ')*8,'url':'https://example.invalid/qualification/'+str(i),
      'source':'Fixture only','summary':'tariff export supplychain '+('x'*600),
      'published':stamp,'credibility':'HIGH'}for i in range(1000)]
    cov=coverage({'catalog':catalog_fingerprint(),'all_sources_healthy':False,
      'source_states':[{'index':i,'state':'selected'}for i in range(len(original_catalog()))]})
    inputs=run_inputs(rows,['TRADE','GENERAL'],.99999)
    capture({'inputs':inputs,'coverage':cov})
    cp=CoverageCheckpoints(CheckpointFixture());key='f'*64;cp.put(key,1,inputs,cov)
    saved=cp.get(key,1)
    docs=prepare_geo_documents(saved['inputs']['candidates'],saved['inputs']['active_categories'],saved['inputs']['threshold'])['documents']
    # Exercise writer maximum1000 input independently of dedupe collapsing a
    # corpus, include actual field validation/copies/BSON serialization.
    if not docs:raise ValueError('Qualification processing empty')
    template=docs[0]
    writer_docs=[]
    for i in range(1000):
        d=copy.deepcopy(template);d['title']='Qualification tariff '+str(i)
        d['url']='https://example.invalid/qualification/'+str(i);d['summary']='x'*300
        writer_docs.append(d)
    fixture=InsertFixture();writer=GeoArticleWriter(ClientFixture(fixture),review={
      'mapping':('geo_intel','articles'),'write_permission':True,'unique_url_index_verified':True,'source_contract_verified':True})
    receipt=writer.write(writer_docs,stamp)
    if receipt['attempted']!=1000 or fixture.count!=1000:raise ValueError('Maximum writer fixture refused')
    # Near-byte-budget corpus intentionally also probes refusal boundary. It
    # must fail boundedly before writes, never qualify unlimited input.
    over=copy.deepcopy(rows)
    for row in over:row['summary']='x'*10000
    try:capture({'candidates':over})
    except InputRefused:pass
    else:raise ValueError('Aggregate overbudget accepted')
    return {'maximum_rows':1000,'checkpoint_fixture':True,'writer_bson_fixture':True,
      'aggregate_overbudget_refused':True,'real_db_writes':False}
