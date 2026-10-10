import unittest
from datetime import datetime,timezone,timedelta
from urllib.parse import urlparse,parse_qs
from integration.weather_public_prep import *
class Tests(unittest.TestCase):
 def setUp(self):self.now=datetime(2026,10,11,tzinfo=timezone.utc);self.r={'timezone':'GMT','utc_offset_seconds':0,'current_units':dict(UNITS),'current':{'time':'2026-10-11T00:00','interval':900,'temperature_2m':30,'relative_humidity_2m':70,'weather_code':3,'wind_speed_10m':12,'wind_direction_10m':180}}
 def obj(self):return typed('INBOM',self.r,fetched_at=self.now)
 def test_url_fixed(self):
  u=urlparse(url('INBOM'));self.assertEqual(u.scheme,'https');self.assertEqual(u.netloc,'api.open-meteo.com');self.assertEqual(u.path,'/v1/forecast');self.assertEqual(set(parse_qs(u.query)),{'latitude','longitude','current','timezone','forecast_days'});self.assertEqual(parse_qs(u.query)['latitude'],['18.9667'])
 def test_params(self):
  for x in [[],[('place','bad')],[('place','INBOM'),('place','INMAA')],[('latitude','18')]]:
   with self.assertRaises(Refused):params(x)
 def test_source_attribution(self):self.assertEqual(display(self.obj(),now=self.now)['source'],SOURCE)
 def test_missing_source_refused(self):
  o=self.obj();del o['source']
  with self.assertRaises(Refused):display(o,now=self.now)
 def test_units_refused(self):
  self.r['current_units']['wind_speed_10m']='mph'
  with self.assertRaises(Refused):self.obj()
 def test_null_not_zero(self):self.r['current']['temperature_2m']=None;self.assertEqual(self.obj()['values']['temperature_2m'],{'state':'unavailable','value':None,'unit':'°C'})
 def test_ranges(self):
  for v in [True,float('nan'),float('inf'),1000]:
   self.r['current']['temperature_2m']=v
   with self.assertRaises(Refused):self.obj()
 def test_timezone(self):
  self.r['timezone']='Asia/Kolkata'
  with self.assertRaises(Refused):self.obj()
 def test_timeparse(self):
  for s in ['2026-99-01T00:00','tomorrow','2026-10-11T00:00+05:30']:
   self.r['current']['time']=s
   with self.assertRaises(Refused):self.obj()
 def test_stale_explicit(self):self.assertEqual(display(self.obj(),now=self.now+timedelta(seconds=1000))['freshness'],'stale_forecast')
 def test_stale_expired(self):
  with self.assertRaises(Refused):display(self.obj(),now=self.now+timedelta(seconds=3601))
 def test_cache_key(self):
  c=Cache();c.put('INBOM',self.obj());self.assertEqual(c.get('INBOM',self.now)['age_seconds'],0)
  with self.assertRaises(Refused):c.put('18.9667,72.8667',self.obj())
 def test_oversize(self):
  self.r['extra']='x'*65536
  with self.assertRaises(Refused):self.obj()
 def test_exact_catalogue_codes_no_alias(self):
  self.assertEqual(set(PORTS),{'INBOM','INMAA','INKOC'});self.assertEqual(params([('place','INKOC')]),'INKOC')
  with self.assertRaises(Refused):params([('place','INCOK')])

 def test_zero_utc_offset(self):
  self.r['utc_offset_seconds']=19800
  with self.assertRaises(Refused):self.obj()
 def test_exact_current_keys(self):
  self.r['current']['unexpected']=1
  with self.assertRaises(Refused):self.obj()
 def test_interval_bounds(self):
  for v in [0,3601,True]:
   self.r['current']['interval']=v
   with self.assertRaises(Refused):self.obj()
 def test_weather_code_int(self):
  self.r['current']['weather_code']=3.0
  with self.assertRaises(Refused):self.obj()
 def test_fetched_utc_aware(self):
  for t in [datetime(2026,10,11),self.now.astimezone(timezone(timedelta(hours=5)))]:
   with self.assertRaises(Refused):typed('INBOM',self.r,fetched_at=t)
 def test_scope(self):self.assertEqual(self.obj()['scope'],'land_forecast_not_marine_or_safety')
 def test_future_fetched_refused(self):
  with self.assertRaises(Refused):display(self.obj(),now=self.now-timedelta(seconds=1))
 def test_cache_identity(self):
  with self.assertRaises(Refused):Cache().put('INKOC',self.obj())
 def test_forecast_days_and_ranges(self):
  self.assertEqual(parse_qs(urlparse(url('INBOM')).query)['forecast_days'],['1'])
  for k,v in [('relative_humidity_2m',101),('relative_humidity_2m',-1),('wind_direction_10m',361),('wind_direction_10m',-1)]:
   old=self.r['current'][k];self.r['current'][k]=v
   with self.assertRaises(Refused):self.obj()
   self.r['current'][k]=old
 def test_catalogue_pin(self):
  import os
  p=os.environ.get('WEATHER_SOURCE_ROOT',str(__import__('pathlib').Path(__file__).resolve().parents[1]))+'/src/worldports.ts'
  self.assertTrue(verify_catalogue(p))
 def test_naive_fetched_string_refused(self):
  o=self.obj();o['fetched_at']='2026-10-11T00:00:00'
  with self.assertRaises(Refused):display(o,now=self.now)
