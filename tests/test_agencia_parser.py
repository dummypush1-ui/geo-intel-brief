import unittest
from integration.agencia_parser import agencia_article
URL='https://agenciagov.ebc.com.br/noticias/202610/trade-story'
TITLE='Trade story Brazil'
HTML='<head><meta property="og:title" content="'+TITLE+'"><meta property="og:url" content="'+URL+'"><meta name="DC.date.created" content="2026-10-01T10:00:00-03:00"></head><h1>Banner</h1><article id="content"><h1 class="titulo-noticia-conteudo">'+TITLE+'</h1><div class="texto-conteudo"><p>'+('Trade details. '*20)+'</p></div><p>Unrelated footer</p></article>'
class AgenciaParserTests(unittest.TestCase):
 def parse(self,h=HTML,url=URL,robots='User-agent: *\nAllow: /',reviewed=True):return agencia_article(h,url,'2026-10-02T00:00:00Z',robots,reviewed)
 def test_scope_and_dates(self):
  r=self.parse();self.assertEqual(r['title'],TITLE);self.assertNotIn('Unrelated',r['summary']);self.assertEqual(r['published'],'');self.assertEqual(r['source_created_at'],'2026-10-01T13:00:00+00:00')
 def test_policy_and_routes(self):
  for url in [URL+'?q=1',URL.replace('202610','other'),URL.replace('agenciagov.ebc.com.br','evil.com'),URL+'/@@images']:
   with self.assertRaises(ValueError):self.parse(url=url)
  with self.assertRaises(ValueError):self.parse(reviewed=False)
  with self.assertRaises(ValueError):self.parse(robots='User-agent: *\nDisallow: /')
 def test_ambiguous_and_truncated(self):
  for h in [HTML.replace('</h1>','',2),HTML.replace('</article>',''),HTML+'<article id="content"></article>',HTML.replace('property="og:title"','property="other"'),HTML.replace('content="'+TITLE+'"','content="Wrong"')]:
   with self.assertRaises(ValueError):self.parse(h)
 def test_hidden_void_and_nested_content(self):
  h=HTML.replace('</p></div>','</p><img hidden><div hidden><p>SECRET</p></div><p>VISIBLE</p></div>');r=self.parse(h);self.assertNotIn('SECRET',r['summary']);self.assertIn('VISIBLE',r['summary'])
 def test_malformed_hidden_refused(self):
  h=HTML.replace('</p></div>','</p><div hidden><p>SECRET</div><p>VISIBLE</p></div>')
  with self.assertRaises(ValueError):self.parse(h)
 def test_hidden_title_and_root_refused(self):
  for h in [HTML.replace('<article id="content">','<article id="content" hidden>'),HTML.replace('class="titulo-noticia-conteudo"','class="titulo-noticia-conteudo" aria-hidden=" TRUE "')]:
   with self.assertRaises(ValueError):self.parse(h)
 def test_naive_creation_not_publication(self):self.assertIsNone(self.parse(HTML.replace('2026-10-01T10:00:00-03:00','2026-10-01T10:00:00'))['source_created_at'])
