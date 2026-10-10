"""Proposed query contract, no Flask/API/UI installed.
Codes and mixed code-like input never enter generic numeric news search.
"""
import re
from integration.code_news_links import Refused

def query_plan(model,query,*,system=None,edition=None):
 if type(query)is not str or not 1<=len(query)<=200:raise Refused('Bounded query')
 query=query.strip()
 if not query:raise Refused('Query required')
 labelled=re.fullmatch(r'(?i)(HSN|HS)\s*(?:[-:]?\s*code\s*)?[:#-]?\s*([0-9]{2,12})',query)
 if labelled:
  label,code=labelled.groups();label_system='IN'if label.upper()=='HSN'else'HS'
  if system is not None and system!=label_system:return {'mode':'code','state':'label_system_conflict','items':[],'generic_q':None}
  return dict(model.resolve(code,label_system,edition),mode='code',generic_q=None)
 if re.fullmatch('[0-9]{2,12}',query):return dict(model.resolve(query,system,edition),mode='code',generic_q=None)
 # Pick explicit refusal of mixed input, no silent stripping/reinterpretation.
 # Any decimal digit in keyword input is held, including Unicode and O/0 typos.
 if any(c.isdecimal()for c in query):return {'mode':'code','state':'mixed_or_malformed_code','items':[],'generic_q':None}
 return {'mode':'keywords','state':'keyword_search','query':query,'generic_q':query}
