import unittest
from unittest.mock import patch
from integration.public_preview_builder import build_public_preview
from integration.weather_ui import PATHS,enabled
from tests.test_weather_public import BuilderTests,LiveBuilderTests,env,BASE
class WeatherUI(unittest.TestCase):
 def test_default_closed(self):
  a=build_public_preview(BuilderTests().base())
  for p in PATHS:self.assertEqual(a.test_client().get(p,base_url=BASE).status_code,403)
 def test_ui_off_badge_no_service(self):
  a=build_public_preview(dict(BuilderTests().base(),PUBLIC_WEATHER_UI_ENABLED='true'));c=a.test_client()
  self.assertNotIn('public_weather',a.extensions);r=c.get('/workspace/weather',base_url=BASE)
  self.assertEqual(r.status_code,200);self.assertIn('data-weather-available="false"',r.text);self.assertIn('Weather unavailable (OFF)',r.text);self.assertIn('disabled',r.text);self.assertIn('Sec-Fetch-Site: none',r.text);self.assertIn('403',r.text)
  for p in PATHS:
   r=c.get(p,base_url=BASE);self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
 def test_on_without_auto_IO(self):
  a=build_public_preview(dict(BuilderTests().base(),**env(),PUBLIC_WEATHER_UI_ENABLED='true'));s=a.extensions['public_weather'];s.get=lambda p:(_ for _ in ()).throw(AssertionError('IO'))
  r=a.test_client().get('/workspace/weather',base_url=BASE);self.assertEqual(r.status_code,200);self.assertIn('data-weather-available="true"',r.text);self.assertEqual(s.attempts,0)
 def test_live_ui_off_on(self):
  t=LiveBuilderTests()
  for ui in ('false','true'):
   a=t.make(dict(t.base(),PUBLIC_WEATHER_UI_ENABLED=ui));r=a.test_client().get('/workspace/weather',base_url=BASE);self.assertEqual(r.status_code,200 if ui=='true'else 403)
   self.assertNotIn('public_weather',a.extensions)
 def test_invalid_flag(self):
  with self.assertRaises(ValueError):enabled({'PUBLIC_WEATHER_UI_ENABLED':'yes'})
class WeatherUIHeaders(unittest.TestCase):
 CSP="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
 def test_module_hook_without_global_headers(self):
  from flask import Flask
  from integration.weather_ui import install
  app=Flask(__name__);install(app,False);c=app.test_client()
  for p in PATHS:
   r=c.get(p);self.assertEqual(r.headers['Content-Security-Policy'],self.CSP);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(r.headers['Referrer-Policy'],'no-referrer')
 def test_reorder_overrides_earlier_global(self):
  from flask import Flask
  from integration.weather_ui import install
  a=Flask(__name__)
  @a.after_request
  def global_headers(r):r.headers['Content-Security-Policy']='GLOBAL';r.headers['Cache-Control']='GLOBAL';r.headers['X-Content-Type-Options']='GLOBAL';return r
  install(a,False);hooks=a.after_request_funcs[None];self.assertEqual(hooks[0].__name__,'weather_ui_headers');self.assertEqual(hooks[-1].__name__,'global_headers')
  for p in PATHS:
   r=a.test_client().get(p);self.assertEqual(r.headers['Content-Security-Policy'],self.CSP);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
 def test_actual_builder_exact_CSP(self):
  a=build_public_preview(dict(BuilderTests().base(),PUBLIC_WEATHER_UI_ENABLED='true'))
  for p in PATHS:self.assertEqual(a.test_client().get(p,base_url=BASE).headers['Content-Security-Policy'],self.CSP)
 def test_live_ui_available_matches_weather_flag(self):
  t=LiveBuilderTests()
  for weather in (False,True):
   e=dict(t.base(),PUBLIC_WEATHER_UI_ENABLED='true')
   if weather:e.update(env())
   a=t.make(e);r=a.test_client().get('/workspace/weather',base_url=BASE)
   self.assertIn('data-weather-available="'+('true'if weather else'false')+'"',r.text)
   self.assertEqual('public_weather'in a.extensions,weather)
   if weather:self.assertEqual(a.extensions['public_weather'].attempts,0)
