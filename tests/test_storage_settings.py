import unittest,tempfile,sqlite3
from pathlib import Path
from integration.storage_settings import StorageSettings
from integration.sqlite_reader import SQLiteArticlesReader
class SettingsTests(unittest.TestCase):
 def test_original_fallbacks(self):
  s=StorageSettings.from_env({});self.assertEqual((s.geo_database,s.geo_articles,s.brics_backend,s.brics_database,s.brics_sqlite_path),('geo_intel','articles','mongodb','newsbot','data/newsbot.db'));self.assertFalse(s.read_enabled)
 def test_env_overrides(self):
  s=StorageSettings.from_env({'GEO_MONGODB_DB_NAME':'other','GEO_ARTICLES_COLLECTION':'geo_rows','BRICS_STORAGE_BACKEND':'mongodb','BRICS_MONGODB_DB':'brics_db','BRICS_ARTICLES_COLLECTION':'brics_rows','NEWS_READ_ENABLED':'true'})
  self.assertEqual((s.geo_database,s.geo_articles,s.brics_backend,s.brics_database,s.brics_articles),('other','geo_rows','mongodb','brics_db','brics_rows'));self.assertTrue(s.read_enabled)
 def test_legacy_vars_fallback(self):
  s=StorageSettings.from_env({'MONGODB_DB_NAME':'legacy_geo','MONGODB_DB':'legacy_brics','STORAGE_BACKEND':'sqlite','SQLITE_PATH':'existing.db'})
  self.assertEqual((s.geo_database,s.brics_database,s.brics_sqlite_path),('legacy_geo','legacy_brics','existing.db'))
 def test_secrets_not_repr(self):
  s=StorageSettings.from_env({'GEO_MONGODB_URI':'fixture-sensitive-geo','BRICS_MONGODB_URI':'fixture-sensitive-brics'});self.assertNotIn('fixture-sensitive',repr(s))
 def test_invalid_backend(self):
  with self.assertRaises(ValueError):StorageSettings.from_env({'BRICS_STORAGE_BACKEND':'wrong'})
 def test_sqlite_read_only(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'existing.db';c=sqlite3.connect(p);c.execute('CREATE TABLE articles(id TEXT,title TEXT,url TEXT,collected_at TEXT,emailed INTEGER)');c.execute("INSERT INTO articles VALUES('hash','News','https://example.invalid/a','2026-10-01',1)");c.commit();c.close();before=p.read_bytes()
   result=SQLiteArticlesReader(p,verified=True)();self.assertEqual(result['brics'][0]['emailed'],1);self.assertEqual(p.read_bytes(),before)
 def test_missing_not_created(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'missing.db'
   with self.assertRaises(FileNotFoundError):SQLiteArticlesReader(p,verified=True)()
   self.assertFalse(p.exists())
