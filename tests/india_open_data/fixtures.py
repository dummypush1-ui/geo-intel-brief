# Copyright (c) 2026 Push. All rights reserved.
from integration.india_open_data.core import source_spec

def spec(**changes):
    d = dict(dataset_id='niti_health_test', publisher='NITI Aayog',
             source_url='https://ndap.niti.gov.in/', provider='ndap_export',
             dataset_date=None, coverage='Synthetic fixture, not published coverage',
             columns={'metric': 'Indicator', 'value': 'Value', 'unit': 'Unit',
                      'state': 'State', 'district': 'District', 'period': 'Year'},
             license_url='https://ndap.niti.gov.in/', reuse_reviewed=False)
    d.update(changes)
    return source_spec(**d)


CSV = b'Indicator,Value,Unit,State,District,Year\nLiteracy,72.500,percent,Tamil Nadu,Nilgiris,2021\n'
ROW = dict(Indicator='Literacy', Value='72.500', Unit='percent',
           State='Tamil Nadu', District='Nilgiris', Year='2021')
UUID = '2ed5b97a-d5bc-404b-a8f3-2a08f20c0b8f'

