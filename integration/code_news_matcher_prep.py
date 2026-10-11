"""Pure bounded explicit-only D2 matcher. No public/store/IO wiring."""
from integration.code_news_links import explicit_mentions,text,Refused
MAX_MENTIONS=32

def for_article(model,target,article):
 if model.rules:raise Refused('Explicit-only matcher requires empty reviewed vocabulary')
 if type(article)is not dict or not {'article_key','title','summary'}<=set(article):raise Refused('Article shape')
 key=text(article['article_key'],100);title=text(article['title'],2000)
 if type(article['summary'])is not str or len(article['summary'])>16000:raise Refused('Summary cap')
 hits=[]
 for hit in explicit_mentions(title+'\n'+article['summary']):
  if len(hits)==MAX_MENTIONS:return {'state':'evidence_refused_mentions_limit','items':[],'coverage':'article_refused','not_exhaustive':True}
  hits.append(hit)
 out=[]
 for label,code,evidence in hits:
  resolved=model.resolve(code,'HS'if label.upper()=='HS'else'IN')
  if len(code)==4 and resolved['state']!='resolved':continue
  # Exact reported identities only. Explicit mention is not legal proof.
  for item in resolved['items']:
   if resolved['state']=='resolved'and all(item[k]==target[k]for k in ('system','edition','code')):
    out.append(dict(article_key=key,kind='reported_code_mention',evidence=evidence,target=dict(item),legal_classification_verified=False));break
 return {'state':'checked','items':out,'coverage':'bounded_explicit_mentions_checked','not_exhaustive':True}
