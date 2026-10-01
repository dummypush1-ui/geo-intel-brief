"""Existing BRICS database reader. SQLite mode=ro, never initialize a store."""
from pathlib import Path
import sqlite3
class SQLiteArticlesReader:
 def __init__(self,path,verified=False,limit=100):
  if not verified:raise ValueError('Verified existing BRICS path required')
  if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=1000:raise ValueError('Invalid read limit')
  self.path=Path(path).resolve();self.limit=limit
 def __call__(self):
  if not self.path.is_file():raise FileNotFoundError('Existing BRICS database is unavailable')
  # URI path encodes special chars. ro avoids creating or editing a database.
  conn=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True,timeout=5)
  conn.row_factory=sqlite3.Row
  try:
   conn.execute('PRAGMA query_only=ON')
   rows=conn.execute('SELECT * FROM articles ORDER BY collected_at DESC LIMIT ?',(self.limit,)).fetchall()
   return {'brics':[dict(row) for row in rows]}
  finally:conn.close()
