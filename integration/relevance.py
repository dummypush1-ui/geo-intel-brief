"""Explainable suggestions. Never a tariff update or legal screening result."""
import re
from integration.taxonomy import country_code,mentioned_countries

def match(context,article):
 text=(str(article.get('title',''))+' '+str(article.get('summary',''))).casefold()
 code=str(context.get('code') or '')
 reasons=[]
 # Require an explicit HS/HSN label, not any accidental numeric sequence.
 if re.fullmatch(r'\d{6,10}',code) and re.search(r'\bhs(?:n)?\s*(?:code\s*)?[:#-]?\s*'+re.escape(code)+r'(?!\d)',text):
  reasons.append({'type':'explicit_code','value':code,'scope':str(context.get('system') or ''),'edition':str(context.get('edition') or '')})
 terms=context.get('product_terms') or []
 if not isinstance(terms,list) or len(terms)>20 or any(not isinstance(t,str) or len(t)>200 for t in terms):raise ValueError('Invalid product terms')
 for term in terms:
  term=str(term).strip().casefold()
  if len(term)>=3 and re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',text):reasons.append({'type':'product_term','value':term})
 country=country_code(context.get('country'))
 if country and country in mentioned_countries(text):reasons.append({'type':'country_context','value':country})
 return {'reasons':reasons,'precise':any(r['type']=='explicit_code' for r in reasons),'duty_change_verified':False}
