"""Research/candidate build only. Exact pinned archives, no runtime downloads."""
import json,struct,zipfile,hashlib,math,sys
from pathlib import Path
SRC=Path(sys.argv[1]);OUT=Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
PINS={'ne.zip':'0f243aeac8ac6cf26f0417285b0bd33ac47f1b5bdb719fd3e0df37d03ea37110','wpi-2019.zip':'0717cdace0d446b8b16be35c94cc1c4136f23157d8268a8e52b957797cb357ae'}
def dbf(raw):
 count=struct.unpack_from('<I',raw,4)[0];head,size=struct.unpack_from('<HH',raw,8);fields=[];i=32
 while raw[i]!=13:
  x=raw[i:i+32];fields.append((x[:11].split(b'\0')[0].decode(),x[16]));i+=32
 rows=[]
 for n in range(count):
  b=raw[head+n*size:head+(n+1)*size];pos=1;r={}
  for k,l in fields:r[k]=b[pos:pos+l].decode('utf-8').strip(' \x00');pos+=l
  if b[:1]!=b'*':rows.append(r)
 return rows
def area(r):return sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(r,r[1:]))/2
def inside(p,r):
 x,y=p;yes=False
 for a,b in zip(r,r[1:]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
zs={}
for name,h in PINS.items():
 raw=(SRC/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==h;z=zipfile.ZipFile(SRC/name)
 pins=json.loads((SRC/'archive-pins.json').read_text())[name]['members'];assert set(z.namelist())==set(pins)
 for n,meta in pins.items():
  assert '/'not in n and '\\'not in n;assert len(z.read(n))==meta['bytes'];assert hashlib.sha256(z.read(n)).hexdigest()==meta['sha256']
 assert sum(x.file_size for x in z.infolist()) <= (64*1024*1024 if name.startswith('wpi')else 2*1024*1024)
 zs[name]=z
z=zs['ne.zip'];assert z.read('ne_110m_admin_0_countries.VERSION.txt').strip()==b'5.1.1';rows=dbf(z.read('ne_110m_admin_0_countries.dbf'));raw=z.read('ne_110m_admin_0_countries.shp');offset=100;features=[];holes=0
for row in rows:
 idx,size=struct.unpack_from('>ii',raw,offset);b=raw[offset+8:offset+8+2*size];offset+=8+2*size;assert struct.unpack_from('<i',b)[0]==5
 count,npts=struct.unpack_from('<ii',b,36);starts=list(struct.unpack_from('<'+'i'*count,b,44))+[npts];points=[list(struct.unpack_from('<dd',b,44+4*count+16*i))for i in range(npts)];
 for xy in points:
  # Exact two RUS floating artifacts only; all other out-of-range values refuse.
  if row['ADM0_A3']=='RUS' and xy in [[180.00000000000006,71.51571433642829],[180.00000000000006,70.83219920854673]]:xy[0]=180.0
 rings=[points[a:b]for a,b in zip(starts,starts[1:])];outer=[[ring]for ring in rings if area(ring)<0]
 for ring in rings:
  if area(ring)>=0:
   possible=[p for p in outer if inside(ring[0],p[0])];assert possible;min(possible,key=lambda p:abs(area(p[0]))).append(ring);holes+=1
 assert len(outer)<=32 and all(len(p)<=8 for p in outer)
 for p in outer:
  for ring in p:
   assert 4<=len(ring)<=1024 and ring[0]==ring[-1]
   for xy in ring:assert all(math.isfinite(v)for v in xy)and -180<=xy[0]<=180 and -90<=xy[1]<=90
 geom={'type':'Polygon','coordinates':outer[0]}if len(outer)==1 else {'type':'MultiPolygon','coordinates':outer}
 features.append({'type':'Feature','id':row['ADM0_A3'],'properties':{'id':row['ADM0_A3'],'name':row['ADMIN']},'geometry':geom})
assert len(features)==177
countries={'type':'FeatureCollection','features':features};ports=[]
for x in dbf(zs['wpi-2019.zip'].read('WPI.dbf')):
 p={'id':'WPI2019-'+str(int(float(x['INDEX_NO']))),'name':x['PORT_NAME'],'country_code':x['COUNTRY'],'lat':float(x['LATITUDE']),'lon':float(x['LONGITUDE'])};assert -90<=p['lat']<=90 and -180<=p['lon']<=180;ports.append(p)
ports.sort(key=lambda x:int(x['id'].split('-')[1]));assert len(ports)==3630 and len({p['id']for p in ports})==3630
# Only unambiguous exact country ADMIN names. No ISO/-99/sovereignty guessing.
alias={f['properties']['name']:f['id']for f in features};assert len(alias)==177;assert 'Congo'not in alias
for name,value in [('countries.json',countries),('ports.json',ports),('crosswalk.json',alias)]:
 b=json.dumps(value,ensure_ascii=True,separators=(',',':')).encode();assert len(b)<=524288;(OUT/name).write_bytes(b)
print(json.dumps({'countries':len(features),'ports':len(ports),'holes':holes,'max_rings_per_polygon':max(len(p)for f in features for p in ([f['geometry']['coordinates']]if f['geometry']['type']=='Polygon'else f['geometry']['coordinates'])),'pins':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in OUT.iterdir()if p.is_file()}},indent=2))
