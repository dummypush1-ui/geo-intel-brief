"""W3 shell candidate. Independent UI gate, no automatic provider request."""
from pathlib import Path
PATHS=frozenset(('/workspace/weather','/workspace/assets/weather.js','/workspace/assets/weather.css'))
def enabled(env):
 value=env.get('PUBLIC_WEATHER_UI_ENABLED','false')
 if value not in ('true','false'):raise ValueError('Exact weather UI flag')
 return value=='true'
def install(app,weather_available=False):
 from flask import Response,request
 root=Path(__file__).resolve().parent/'ui'
 @app.get('/workspace/weather')
 def weather_shell():
  html=(root/'weather.html').read_text()
  return Response(html.replace('data-weather-available="false"','data-weather-available="true"'if weather_available else'data-weather-available="false"'),mimetype='text/html')
 @app.get('/workspace/assets/weather.js')
 def weather_script():return Response((root/'weather.js').read_text(),mimetype='application/javascript')
 @app.get('/workspace/assets/weather.css')
 def weather_style():return Response((root/'weather.css').read_text(),mimetype='text/css')
 @app.after_request
 def weather_ui_headers(response):
  if request.path in PATHS:
   response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
   response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
  return response
 hooks=app.after_request_funcs[None];hooks.remove(weather_ui_headers);hooks.insert(0,weather_ui_headers)
