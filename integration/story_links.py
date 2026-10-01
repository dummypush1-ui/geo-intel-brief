"""Reversible display grouping. Does not delete or write original articles."""
from difflib import SequenceMatcher
from integration.news_view import safe_url

def groups(rows):
 result={}
 for row in rows:
  url=safe_url(row.get('url'))
  if url:result.setdefault(url,[]).append(row.copy())
 return [{'url':url,'profiles':profiles,'match':'same_url'} for url,profiles in result.items()]

def possible_related(left,right,threshold=.9):
 return safe_url(left.get('url'))!=safe_url(right.get('url')) and SequenceMatcher(None,str(left.get('title','')).casefold(),str(right.get('title','')).casefold()).ratio()>=threshold
