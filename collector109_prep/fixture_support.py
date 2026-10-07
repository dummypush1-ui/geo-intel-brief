import copy,threading
from types import SimpleNamespace
class CASCollection:
 def __init__(self):self.doc=None;self.lock=threading.Lock();self.calls=0
 def update_one(self,q,u,upsert=False):
  with self.lock:
   self.calls+=1
   if self.doc is None:self.doc={'_id':q['_id'],**copy.deepcopy(u['$setOnInsert'])}
   return SimpleNamespace(acknowledged=True)
 def find_one(self,q):
  with self.lock:self.calls+=1;return copy.deepcopy(self.doc)
 def replace_one(self,q,d):
  with self.lock:
   self.calls+=1;ok=all(self.doc.get(k)==v for k,v in q.items())
   if ok:self.doc=copy.deepcopy(d)
   return SimpleNamespace(acknowledged=True,matched_count=int(ok))
