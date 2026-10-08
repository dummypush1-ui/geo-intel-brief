"""Token/phrase match, Unicode casefold and explicit intentional stems only."""
import re
import unicodedata
_STEMS = {
 'geopolit': {'ics','ical','ically'}, 'diplomat': {'s','ic','ically'},
 'sanction': {'s','ed','ing'}, 'tariff': {'s'}, 'embargo': {'es','ed','ing'},
 'export': {'s','ed','ing'}, 'import': {'s','ed','ing'},
 'critical mineral': {'s'}, 'semiconductor': {'s'}, 'risk': {'s','y'},
 'war': {'s'}, 'coup': {'s'}, 'attack': {'ed','ing'},
 'resign': {'ed','ing','ation'},
}

def tokens(text):
    return re.findall(r'[^\W_]+', unicodedata.normalize('NFKC', text).casefold(), re.UNICODE)

def contains(text, term):
    hay = tokens(text); needle = tokens(term)
    if not needle: return False
    for start in range(len(hay)-len(needle)+1):
        segment = hay[start:start+len(needle)]
        if segment == needle: return True
        if segment[:-1] == needle[:-1]:
            final=needle[-1]
            plurals={final+'s',final+'es'} if final.isalpha() and len(final)>=4 else set()
            irregular={'crisis':'crises','shortage':'shortages','alliance':'alliances'}
            if final in irregular:plurals.add(irregular[final])
            if segment[-1] in plurals:return True
        # Only final token can extend an explicit reviewed stem phrase.
        if term.casefold() in _STEMS and segment[:-1] == needle[:-1] and segment[-1] in {needle[-1]+suffix for suffix in _STEMS[term.casefold()]}:
            return True
    return False

_DEMONYMS = {'India':('Indian','Indians'), 'Iran':('Iranian','Iranians'),
 'China':('Chinese',), 'Russia':('Russian','Russians'), 'United States':('American','Americans'),
 'Ukraine':('Ukrainian','Ukrainians'), 'Israel':('Israeli','Israelis'),
 'Japan':('Japanese',), 'Germany':('German','Germans'), 'France':('French',),
 'United Kingdom':('British',), 'Brazil':('Brazilian','Brazilians'),
 'Türkiye':('Turkish',), 'Pakistan':('Pakistani','Pakistanis'),
 'Australia':('Australian','Australians'), 'Indonesia':('Indonesian','Indonesians')}
def country_contains(text,country):
    return contains(text,country) or any(contains(text,d) for d in _DEMONYMS.get(country,()))
