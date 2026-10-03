"""Bounded inline email design grammar. No resource-loading CSS or page overlays.

Preserves decorative color/gradient, spacing, typography and table sizing only.
No stylesheets, selectors, custom properties, escapes, comments, url(), var(),
positioning, dimension clipping, opacity, transparent/alpha text colors,
display hiding, animations or external fonts. Decoration can still reduce contrast;
this is a resource/execution boundary, not a text-visibility guarantee. Unsupported email
clients may show a solid fallback instead of gradients. Not delivery approval.
"""
import re
NAMES=set('aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen transparent currentcolor'.split())
def color(v):
 if v.lower() in NAMES or re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{1}|[0-9a-fA-F]{3}|[0-9a-fA-F]{5})?',v):return True
 m=re.fullmatch(r'(rgb|rgba)\(([0-9.,% ]+)\)',v.lower())
 if not m:return False
 parts=[p.strip() for p in m[2].split(',')]
 if len(parts)!=(4 if m[1]=='rgba' else 3):return False
 try:
  for p in parts[:3]:
   if not re.fullmatch(r'\d+(?:\.\d+)?%?',p) or not 0<=float(p.rstrip('%'))<=(100 if p.endswith('%') else 255):return False
  return len(parts)==3 or bool(re.fullmatch(r'(?:0(?:\.\d+)?|1(?:\.0+)?)',parts[3]))
 except ValueError:return False

def comma_parts(v):
 parts=[];depth=0;start=0
 for i,c in enumerate(v):
  if c=='(':depth+=1
  elif c==')':depth-=1
  if depth<0 or depth>1:return None
  if c==',' and depth==0:parts.append(v[start:i].strip());start=i+1
 if depth:return None
 return parts+[v[start:].strip()]

def gradient(v):
 m=re.fullmatch(r'linear-gradient\((.+)\)',v,re.I)
 if not m:return False
 parts=comma_parts(m[1])
 if not parts:return False
 if re.fullmatch(r'(?:[+-]?\d{1,3}(?:\.\d{1,2})?deg|to (?:left|right|top|bottom)(?: (?:left|right|top|bottom))?)',parts[0],re.I):parts=parts[1:]
 if not 2<=len(parts)<=8:return False
 for stop in parts:
  if color(stop):continue
  match=re.fullmatch(r'(.+) (\d{1,3}(?:\.\d{1,2})?)%',stop)
  if not match or not color(match[1]) or float(match[2])>100:return False
 return True

def length(v,percent=True):
 if v=='0':return True
 m=re.fullmatch(r'(\d+(?:\.\d{1,3})?)(px|pt|em|rem|%)',v)
 if not m:return False
 n=float(m[1]);return n<=(100 if m[2]=='%' else 1000 if m[2] in ('px','pt') else 50) and (percent or m[2]!='%')

def valid(key,v):
 if key=='color':return color(v) and v.lower()!='transparent' and not v.lower().startswith('rgba') and not (v.startswith('#') and len(v) in (5,9))
 if key=='background-color':return color(v)
 if key=='background':return color(v) or gradient(v)
 if key=='background-image':return gradient(v)
 if key=='font-family':return bool(re.fullmatch(r'[a-zA-Z][a-zA-Z0-9 ,\-]{0,160}',v))
 if key=='font-size':return bool(re.fullmatch(r'(?:[89]|[1-9]\d)(?:\.\d{1,2})?(?:px|pt)',v))
 if key=='font-weight':return v in ('normal','bold','bolder','lighter') or v in {str(i) for i in range(100,1000,100)}
 enums={'font-style':('normal','italic','oblique'),'text-align':('left','right','center','justify'),'text-decoration':('none','underline','line-through','overline'),'text-transform':('none','uppercase','lowercase','capitalize'),'border-collapse':('collapse','separate'),'vertical-align':('top','middle','bottom','baseline'),'word-break':('normal','break-word','break-all'),'overflow-wrap':('normal','break-word','anywhere')}
 if key in enums:return v in enums[key]
 if key in ('width','max-width','min-width','height','max-height'):return False
 if key=='line-height':return v=='normal' or (bool(re.fullmatch(r'\d(?:\.\d{1,3})?',v)) and 0.5<=float(v)<=5) 
 if key=='opacity':return False
 if key in ('margin','padding','border-radius','border-spacing') or key in {p+'-'+side for p in ('margin','padding') for side in ('top','right','bottom','left')}:
  parts=v.split();return 1<=len(parts)<=4 and all(length(p) for p in parts)
 if key in ('border','border-left','border-right','border-top','border-bottom'):
  m=re.fullmatch(r'(\S+) (solid|dashed|dotted|double) (.+)',v);return bool(m and length(m[1],False) and color(m[3])) or v in ('0','none')
 return False

def safe_style(value):
 if not isinstance(value,str) or len(value)>4000:return ''
 out=[]
 def append(declaration):
  if len(out)>=64 or len(';'.join(out+[declaration]))>4000:return False
  out.append(declaration);return True
 for part in value.split(';')[:64]:
  if not part.strip():continue
  if any(c in part for c in '\\@<>!{}') or '/*' in part or '*/' in part or any(ord(c)<32 or ord(c)>126 for c in part):continue
  pair=part.split(':',1)
  if len(pair)!=2:continue
  key,v=(s.strip() for s in pair);key=key.lower()
  if len(v)>500:continue
  if valid(key,v):
   # Solid fallback before gradient for clients that don't support gradients.
   if key=='background' and gradient(v):
    stops=comma_parts(v[v.index('(')+1:-1]);colors=[re.sub(r' \d{1,3}(?:\.\d{1,2})?%$','',stop) for stop in stops];first=next((stop for stop in colors if color(stop)),None)
    if first and (not out or out[-1]!='background-color:'+first):
     if len(out)>=63 or len(';'.join(out+['background-color:'+first,key+':'+v]))>4000:break
     append('background-color:'+first)
   if not append(key+':'+v):break
 return ';'.join(out)
