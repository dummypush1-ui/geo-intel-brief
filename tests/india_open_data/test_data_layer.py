# Copyright (c) 2026 Push. All rights reserved.
import unittest
from integration.india_open_data.data_layer import *
from tests.india_open_data.fixtures import spec,CSV
from integration.india_open_data.core import import_export,stage_snapshot


class LayerTests(unittest.TestCase):
    def reader(self):
        data=stage_snapshot({'state':'complete','records':import_export(CSV,'csv',spec())},
                            {},'niti_health_test','2026-10-08T23:00:00+05:30')
        return GovernmentDataReader(data),data
    def test_exact_filters_not_substring(self):
        r,_=self.reader()
        self.assertEqual(r.read('niti_health_test',district='Nilgiris')['matched'],1)
        self.assertEqual(r.read('niti_health_test',district='Nil')['matched'],0)
        self.assertEqual(r.read('niti_health_test',metric='Literacy',period='2021')['matched'],1)
    def test_missing_and_empty_distinct(self):
        r,_=self.reader()
        self.assertEqual(r.read('unknown')['state'],'unavailable')
        self.assertEqual(r.read('niti_health_test',state='Unknown')['state'],'available')
    def test_detached_input_and_output(self):
        r,data=self.reader();data.clear()
        first=r.read('niti_health_test');first['records'][0]['value_decimal']='999'
        self.assertEqual(r.read('niti_health_test')['records'][0]['value_decimal'],'72.500')
    def test_limits_and_input_validation(self):
        r,_=self.reader()
        for limit in (0,1001,True,'100'):
            with self.assertRaises(ValueError):r.read('niti_health_test',limit=limit)
        with self.assertRaises(ValueError):GovernmentDataReader({'x':{'state':'partial'}})
    def test_plan_only_isolated_no_ddl(self):
        r=storage_plan('geo_intel','government_data_candidate')
        self.assertFalse(r['provision_allowed']);self.assertEqual(r['ttl_indexes'],[])
        for name in ('articles','events','mail_receipts','system_data'):
            with self.assertRaises(ValueError):storage_plan('geo_intel',name)

if __name__=='__main__':unittest.main()
