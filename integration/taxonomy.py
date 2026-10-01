"""Display-only aliases. Never replace original classifier tags."""
import re
COUNTRIES={'IN':'India','US':'United States','CN':'China','BR':'Brazil','RU':'Russia','ZA':'South Africa','IR':'Iran','EG':'Egypt','AE':'United Arab Emirates','ID':'Indonesia','ET':'Ethiopia','SA':'Saudi Arabia','UK':'United Kingdom','TR':'Turkey','EU':'European Union','CA':'Canada','AU':'Australia','JP':'Japan'}
ALIASES={'usa':'US','u.s.':'US','united states':'US','united states of america':'US','uk':'UK','united kingdom':'UK','türkiye':'TR','turkey':'TR','uae':'AE','united arab emirates':'AE'}
ALIASES.update({v.casefold():k for k,v in COUNTRIES.items()})
def country_code(value):
 text=str(value or '').strip()
 return text.upper() if text.upper() in COUNTRIES else ALIASES.get(text.casefold())
def mentioned_countries(text):
 text=str(text or '').casefold()
 return sorted({code for name,code in ALIASES.items() if len(name)>3 and re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text)})
