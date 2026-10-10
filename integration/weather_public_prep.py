"""Pure W1 fixture preparation. No HTTP, Flask, environment or activation."""
import json,math,hashlib,re
from datetime import datetime,timezone
from urllib.parse import urlencode
class Refused(ValueError):pass
SOURCE={'name':'Open-Meteo','url':'https://open-meteo.com/','licence':'CC BY 4.0'}
SOURCE_PIN={'path':'src/worldports.ts','commit':'f7f78e76b6a9e907c10ef7cb10dbcc601c3fd861','sha256':'91aa7053de41ef9184276e904012f6e1641cb761d53a2e0baca5ce9165d8782f'}
PORTS={'INBOM':('Mumbai (Bombay)',18.9667,72.8667),'INMAA':('Chennai (Madras)',13.1,80.3),'INKOC':('Kochi (Cochin)',9.9667,76.2333)}
UNITS={'time':'iso8601','interval':'seconds','temperature_2m':'°C','relative_humidity_2m':'%','weather_code':'wmo code','wind_speed_10m':'km/h','wind_direction_10m':'°'}
FIELDS=('temperature_2m','relative_humidity_2m','weather_code','wind_speed_10m','wind_direction_10m')
RANGES={'temperature_2m':(-90,65),'relative_humidity_2m':(0,100),'weather_code':(0,99),'wind_speed_10m':(0,500),'wind_direction_10m':(0,360)}
def params(pairs):
 if type(pairs)is not list or len(pairs)!=1 or pairs[0][0]!='place' or pairs[0][1]not in PORTS:raise Refused('Exact catalogue place required')
 return pairs[0][1]
def url(place):
 if place not in PORTS:raise Refused('Unknown place')
 _,lat,lon=PORTS[place]
 return 'https://api.open-meteo.com/v1/forecast?'+urlencode({'latitude':lat,'longitude':lon,'current':','.join(FIELDS),'timezone':'UTC','forecast_days':1})
def utc(s):
 if type(s)is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?',s):raise Refused('Exact UTC ISO time')
 try:return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
 except ValueError:raise Refused('UTC time')
def typed(place,raw,*,fetched_at):
 if place not in PORTS or type(raw)is not dict:raise Refused('Shape')
 if len(json.dumps(raw,ensure_ascii=False).encode())>65536:raise Refused('Response byte cap')
 if raw.get('timezone')!='GMT' or raw.get('utc_offset_seconds')!=0:raise Refused('UTC timezone required')
 if raw.get('current_units')!=UNITS:raise Refused('Unit mismatch')
 row=raw.get('current')
 if type(row)is not dict or set(row)!={'time','interval',*FIELDS}:raise Refused('Current schema')
 timestamp=utc(row['time'])
 if type(row['interval'])is not int or not 1<=row['interval']<=3600:raise Refused('Interval')
 out={}
 for k in FIELDS:
  v=row[k]
  if v is None:out[k]={'state':'unavailable','value':None,'unit':UNITS[k]};continue
  if type(v)not in (int,float) or not math.isfinite(v) or not RANGES[k][0]<=v<=RANGES[k][1] or k=='weather_code' and type(v)is not int:raise Refused('Range')
  out[k]={'state':'forecast','value':v,'unit':UNITS[k]}
 if type(fetched_at)is not datetime or fetched_at.tzinfo!=timezone.utc:raise Refused('UTC fetched time')
 return {'place':place,'label':PORTS[place][0],'forecast_time':timestamp.isoformat(),'fetched_at':fetched_at.isoformat(),'values':out,'source':dict(SOURCE),'scope':'land_forecast_not_marine_or_safety'}
def display(obj,*,now):
 if obj.get('source')!=SOURCE:raise Refused('Attribution required')
 if now.tzinfo!=timezone.utc:raise Refused('UTC now')
 try:fetched=datetime.fromisoformat(obj['fetched_at'])
 except (ValueError,TypeError,KeyError):raise Refused('Fetched time')
 if fetched.tzinfo!=timezone.utc:raise Refused('Fetched time UTC')
 age=(now-fetched).total_seconds()
 if not 0<=age<=3600:raise Refused('Stale beyond one hour')
 return dict(obj,age_seconds=int(age),freshness='cached_forecast' if age<=900 else 'stale_forecast',attribution='Weather data by Open-Meteo (CC BY 4.0)')
class Cache:
 def __init__(self):self.rows={}
 def put(self,place,obj):
  if place not in PORTS or obj.get('place')!=place:raise Refused('Fixed place cache key')
  self.rows[place]=obj
 def get(self,place,now):
  if place not in PORTS:raise Refused('Fixed place cache key')
  return display(self.rows[place],now=now) if place in self.rows else None

def verify_catalogue(path):
 from pathlib import Path
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SOURCE_PIN['sha256']:raise Refused('Catalogue pin drift')
 text=raw.decode()
 for code,(name,lat,lon) in PORTS.items():
  pattern=r'\["'+re.escape(name)+r'", "India", "'+code+r'", ([0-9.]+), ([0-9.]+),'
  hit=re.search(pattern,text)
  if hit is None or (float(hit[1]),float(hit[2]))!=(lat,lon):raise Refused('Catalogue identity drift')
 return True
