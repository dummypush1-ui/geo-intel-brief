import copy
import unittest
from types import SimpleNamespace
from bson.son import SON
from integration.collector197_preflight import inspect_writer, PreflightRefused, REQUIRED

class Cursor(list):
    def close(self):pass
class Collection:
    def __init__(self,db,name):
        self.database=db;self.name=name
        self.rows=[SON([('name','_id_'),('key',SON([('_id',1)]))])]
        if name=='articles':self.rows.append(SON([('name','url_1'),('key',SON([('url',1)])),('unique',True),('collation',{'locale':'simple'})]))
    def list_indexes(self,**kw):return Cursor(copy.deepcopy(self.rows))
    def find_one(self,q,**kw):return {'_id':'geo108','revision':0,'fingerprint':'a'*64,'fence':0,'active':None,'history':[]}
class Database:
    def __init__(self,client):self.client=client;self.name='geo_intel';self.cs={n:Collection(self,n)for n in REQUIRED}
    def get_collection(self,n,**kw):
        c=self.cs[n];c.write_concern=kw['write_concern'];c.read_concern=kw['read_concern'];return c
class Client:
    def __init__(self):
        self.db=Database(self);self.admin=self;self.calls=[]
        self.grants=[{'resource':{'db':'geo_intel','collection':n},'actions':list(a)}for n,a in REQUIRED.items()]
    def __getitem__(self,n):return self.db
    def command(self,q):
        self.calls.append(q)
        if 'hello' in q:return {'ok':1,'setName':'fixture','isWritablePrimary':True}
        return {'ok':1,'authInfo':{'authenticatedUsers':[{'user':'fixture','db':'admin'}],'authenticatedUserPrivileges':self.grants}}
class Tests(unittest.TestCase):
    def setUp(self):self.c=Client()
    def test_son_live_driver_shape(self):
        out=inspect_writer(self.c,'a'*64);self.assertTrue(out['role_index_ttl_observed'])
        self.assertEqual(out['ledger'].profile,'geo108')
    def test_wildcard_refused(self):
        self.c.grants[0]['resource']['collection']=''
        with self.assertRaises(PreflightRefused):inspect_writer(self.c,'a'*64)
    def test_extra_destructive_actions_refused(self):
        for action in ('remove','createIndex','dropCollection','createCollection','collMod'):
            self.setUp();self.c.grants[0]['actions'].append(action)
            with self.assertRaises(PreflightRefused):inspect_writer(self.c,'a'*64)
    def test_ttl_any_mapping_refused(self):
        for n in REQUIRED:
            self.setUp();self.c.db.cs[n].rows[0]['expireAfterSeconds']=10
            with self.assertRaises(PreflightRefused):inspect_writer(self.c,'a'*64)
    def test_partial_sparse_collation_unique_refused(self):
        for k,v in (('partialFilterExpression',{'url':{'$exists':True}}),('sparse',True),('collation',{'locale':'en'}),('unique',False)):
            self.setUp();self.c.db.cs['articles'].rows[1][k]=v
            with self.assertRaises(PreflightRefused):inspect_writer(self.c,'a'*64)
    def test_missing_grant_refused(self):
        for n in range(3):
            self.setUp();self.c.grants[n]['actions'].pop()
            with self.assertRaises(PreflightRefused):inspect_writer(self.c,'a'*64)
    def test_wrong_profile_fingerprint_refused(self):
        with self.assertRaises(PreflightRefused):inspect_writer(self.c,'b'*64)
    def test_no_initialization_or_writes_surface(self):
        out=inspect_writer(self.c,'a'*64)
        self.assertEqual(self.c.calls,[{'connectionStatus':1,'showPrivileges':True},{'hello':1}])
        self.assertEqual(set(out),{'ledger','articles','checkpoints','role_index_ttl_observed'})
    def test_errors_no_details(self):
        self.c.command=lambda *a:(_ for _ in ()).throw(RuntimeError('private-URI-fixture'))
        with self.assertRaises(PreflightRefused) as e:inspect_writer(self.c,'a'*64)
        self.assertNotIn('private',str(e.exception))
