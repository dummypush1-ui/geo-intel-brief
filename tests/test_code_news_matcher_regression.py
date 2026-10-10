import unittest
class SharedRegexRegression(unittest.TestCase):
 def test_whitespace_cpu(self):
  import time
  from integration.code_news_links import explicit_mentions
  for s in ['HS'+' '*16000+'x','HSN'+' '*16000+'x','HS code'+' '*16000+'x','HS8517'+' '*16000+'9']:
   start=time.process_time();self.assertEqual(list(explicit_mentions(s)),[]);self.assertLess((time.process_time()-start)*1000,50)
 def test_whitespace_original_evidence(self):
  from integration.code_news_links import explicit_mentions
  s='x HS'+(' '*50)+'code\t:\n8517; HSN\t851700'
  self.assertEqual(list(explicit_mentions(s)),[('HS','8517',s[2:s.index(';')]),('HSN','851700','HSN\t851700')])
 def test_split_suffix_never_lost(self):
  from integration.code_news_links import explicit_mentions
  for n in [1,8,9,16,100,16000]:
   for delim in ['', '.', '-', '/', ',']:
    self.assertEqual(list(explicit_mentions('HS8517'+' '*n+delim+' '*n+'9')),[])
 def test_long_gap_still_matches(self):
  from integration.code_news_links import explicit_mentions
  s='HS'+' '*15990+'8517';self.assertEqual(list(explicit_mentions(s)),[('HS','8517',s)])

class LandedCRegression(unittest.TestCase):
 def test_for_news_whitespace_cpu(self):
  import time
  from integration.code_news_links import Links
  model=Links([dict(system='HS',edition='2022',code='8517',description='Phone')],[])
  row=dict(article_key='a',title='HS',summary=' '*15999+'x')
  start=time.process_time();self.assertEqual(model.for_news(row)['items'],[]);self.assertLess((time.process_time()-start)*1000,50)
class DifferentialParity(unittest.TestCase):
 def test_mixed_case_explicit(self):
  from integration.code_news_links import explicit_mentions
  self.assertEqual(list(explicit_mentions('hs8517; Hsn code:851700; hS 8517')),[('hs','8517','hs8517'),('Hsn','851700','Hsn code:851700'),('hS','8517','hS 8517')])
 def test_seeded_old_regex_differential(self):
  import re,random
  from integration.code_news_links import explicit_mentions
  old=re.compile(r'(?<!\w)(HSN|HS)\s*(?:code\s*)?[:#-]?\s*([0-9]{4}(?:[0-9]{2}){0,4})(?!\w|\s*[.\-/,]\s*\d|\s+\d)',re.I)
  rng=random.Random(20261011)
  atoms=['HS','HSN','hs','Hsn','code','CODE','8517','851700','123456789012','9',' ', '\t','\n','\r\n','\u00a0','\u2003','\u200b',':','#','-','/',',','.',';','x','é','_', '🇮🇳','١','²','HSC','CHS']
  for i in range(3000):
   s=''.join(rng.choices(atoms,k=rng.randrange(1,50)))
   expected=[(x.group(1),x.group(2),x.group(0))for x in old.finditer(s)]
   self.assertEqual(list(explicit_mentions(s)),expected,(i,repr(s)))
