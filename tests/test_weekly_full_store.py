import io
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from threading import Thread, Event, Lock
from pypdf import PdfReader
from integration import weekly_full_store as f
from integration import public_weekly_pdf as w
from integration.news_api import create_app

START=datetime(2026,10,1,tzinfo=timezone.utc)
END=datetime(2026,10,5,tzinfo=timezone.utc)
URL=w.PATH+'?start=2026-10-01&end=2026-10-05'

def row(n=0, **extra):
    return dict(title='Older publication '+str(n),url='https://example.com/'+str(n),
                published='2026-10-02T00:00:00Z',created_at='2026-10-12T00:00:00Z',**extra)

class Cursor:
    def __init__(self, rows): self.rows=iter(rows);self.closed=False;self.settings=[]
    def sort(self,n):self.settings.append(('sort',n));return self
    def batch_size(self,n):self.settings.append(('batch',n));return self
    def max_time_ms(self,n):self.settings.append(('timeout',n));return self
    def __next__(self):return next(self.rows)
    def close(self):self.closed=True

class Store:
    def __init__(self,rows):self.rows=rows;self.calls=[]
    def find(self,q,p):self.calls.append((q,p));self.cursor=Cursor(self.rows);return self.cursor

class Tests(unittest.TestCase):
    def setUp(self):
        with w._RATE_LOCK:w._STARTS.clear()
    def test_beyond_sample_and_public_projection(self):
        s=Store([dict(row(i),published='2026-10-12T00:00:00Z')for i in range(100)]+[row(100,private='SECRET')])
        rows,scope=f.PeriodReader(s)(START,END)
        self.assertEqual(len(rows),1);self.assertIn('100',rows[0]['title']);self.assertNotIn('SECRET',repr(rows))
        self.assertTrue(s.cursor.closed);self.assertEqual(s.calls[0][0],{})
        self.assertEqual(s.calls[0][1],{k:1 for k in f.READ_STORE_FIELDS})
        self.assertEqual(s.cursor.settings,[('sort',[('_id',1)]),('batch',100),('timeout',2000)])
    def test_boundaries_and_publication_not_collection(self):
        s=Store([dict(row(0),published='2026-10-01T05:30:00+05:30'),dict(row(1),published='2026-10-05T00:00:00Z'),dict(row(2),published='2026-09-30T23:59:59Z')])
        self.assertEqual(len(f.PeriodReader(s)(START,END)[0]),1)
    def test_cap_failures_close(self):
        for key,value,rows in [('MAX_SCAN',2,[row(i)for i in range(3)]),('MAX_ROWS',2,[row(i)for i in range(3)]),('MAX_BYTES',1,[row()])]:
            s=Store(rows)
            with patch.object(f,key,value),self.assertRaises(ValueError):f.PeriodReader(s)(START,END)
            self.assertTrue(s.cursor.closed)
    def test_time_failure_and_source_error_close(self):
        s=Store([row()]);clock=Mock(side_effect=[0,0,11])
        with self.assertRaises(ValueError):f.PeriodReader(s,clock=clock)(START,END)
        self.assertTrue(s.cursor.closed)
        s=Store([dict(row(),published='bad')])
        with self.assertRaises(ValueError):f.PeriodReader(s)(START,END)
        self.assertTrue(s.cursor.closed)
    def test_exact_boundary_scan_succeeds(self):
        s=Store([row(i)for i in range(2)])
        with patch.object(f,'MAX_SCAN',2),patch.object(f,'MAX_ROWS',2):self.assertEqual(len(f.PeriodReader(s)(START,END)[0]),2)
    def test_route_period_reader_cheap_head_and_no_sample_fallback(self):
        s=Store([row(i)for i in range(101)]);sample=Mock(side_effect=AssertionError('sample'))
        app=create_app(authorize=lambda _:True);w.install(app,sample,period_reader=f.PeriodReader(s))
        c=app.test_client();self.assertEqual(c.head(URL).status_code,200);self.assertEqual(s.calls,[])
        r=c.get(URL);self.assertEqual(r.status_code,200)
        text=' '.join(''.join(p.extract_text()for p in PdfReader(io.BytesIO(r.data)).pages).split())
        self.assertIn('101 news items',text);self.assertIn('101 rows scanned',text);self.assertIn('not a snapshot',text);self.assertIn('Weekly period-news report',text);sample.assert_not_called()
        self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertTrue(s.cursor.closed)
        with patch.object(f,'MAX_ROWS',1):self.assertEqual(c.get(URL).status_code,503)
        sample.assert_not_called()
    def test_undated_duplicates_and_invalid_are_distinct(self):
        undated=row(1);undated.pop('published')
        s=Store([row(),row(),undated]);rows,scope=f.PeriodReader(s)(START,END)
        self.assertEqual(len(rows),1);self.assertEqual(scope['duplicates'],1);self.assertEqual(scope['undated'],1)
        app=create_app(authorize=lambda _:True);w.install(app,Mock(),period_reader=f.PeriodReader(s))
        r=app.test_client().get(URL)
        text=' '.join(''.join(p.extract_text()for p in PdfReader(io.BytesIO(r.data)).pages).split())
        self.assertIn('undated: 1',text);self.assertIn('duplicate period identities: 1',text)
    def test_store_too_large_distinct_error_and_render_not_called(self):
        s=Store([row(i)for i in range(3)]);app=create_app(authorize=lambda _:True);w.install(app,Mock(),period_reader=f.PeriodReader(s))
        with patch.object(f,'MAX_SCAN',2),patch('integration.weekly_report._render.render_pdf',side_effect=AssertionError('render')):
            r=app.test_client().get(URL);self.assertEqual(r.status_code,503);self.assertIn('Store too large',r.json['error'])
        self.assertTrue(s.cursor.closed)
    def test_each_dependency_and_factory_guard(self):
        from integration.public_live_builder import build_public_live_preview
        from tests.test_code_news_coverage_binding_prep import LIVE
        env=dict(LIVE,PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_NEWS_FULL_PAGES_ENABLED='true',**{f.FLAG:'true'})
        for name in ('PUBLIC_WEEKLY_PDF_ENABLED','PUBLIC_NEWS_READ_ENABLED','PUBLIC_NEWS_FULL_PAGES_ENABLED'):
            factory=Mock(side_effect=AssertionError('factory'))
            with self.assertRaises(ValueError):build_public_live_preview(dict(env,**{name:'false'}),client_factory=factory)
            factory.assert_not_called()
    def test_concurrent_third_request_no_cursor(self):
        entered=Event();release=Event();lock=Lock();starts=[];stores=[Store([row()])for _ in range(3)]
        def make_reader(store):
            real=f.PeriodReader(store)
            def read(start,end):
                with lock:
                    starts.append(store)
                    if len(starts)==2:entered.set()
                release.wait(5)
                return real(start,end)
            return read
        apps=[]
        for store in stores:
            app=create_app(authorize=lambda _:True);w.install(app,Mock(),period_reader=make_reader(store));apps.append(app)
        threads=[Thread(target=lambda a=a:a.test_client().get(URL))for a in apps[:2]]
        for t in threads:t.start()
        try:
            self.assertTrue(entered.wait(3));self.assertEqual(apps[2].test_client().get(URL).status_code,429);self.assertEqual(stores[2].calls,[])
        finally:
            release.set()
            for t in threads:t.join(5)
        self.assertTrue(all(s.cursor.closed for s in stores[:2]))
    def test_live_mounted_state_and_india_date_edges(self):
        from integration.public_live_builder import build_public_live_preview
        from tests.test_code_news_coverage_binding_prep import LIVE,ORIGIN
        s=Store([dict(row(0),published='2026-09-30T18:30:00Z'),dict(row(1),published='2026-10-04T18:30:00Z')])
        class Client:
            def __getitem__(self,key):return self
            def find(self,q,p):return s.find(q,p)
            def close(self):pass
        env=dict(LIVE,PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_NEWS_FULL_PAGES_ENABLED='true',PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',**{f.FLAG:'true'})
        app=build_public_live_preview(env,client_factory=lambda *a,**k:Client())
        self.addCleanup(app.extensions['whole_news_pages'].close)
        self.assertIs(app.extensions['public_weekly_full_store'],True)
        r=app.test_client().get(URL,base_url=ORIGIN);self.assertEqual(r.status_code,200)
        text=' '.join(''.join(p.extract_text()for p in PdfReader(io.BytesIO(r.data)).pages).split())
        self.assertIn('1 news items',text);self.assertIn('exclusive',text);self.assertIn('Asia/Kolkata',text)
        s2=Store([row()]);app2=create_app(authorize=lambda _:True);w.install(app2,Mock(return_value={'geo':[]}),period_reader=None)
        self.assertFalse(app2.extensions['public_weekly_full_store'])
    def test_each_budget_before_render(self):
        for name,value,data in [('MAX_SCAN',2,[row(i)for i in range(3)]),('MAX_ROWS',2,[row(i)for i in range(3)]),('MAX_BYTES',1,[row()])]:
            app=create_app(authorize=lambda _:True);w.install(app,Mock(),period_reader=f.PeriodReader(Store(data)))
            with patch.object(f,name,value),patch('integration.weekly_report._render.render_pdf',side_effect=AssertionError('render')):
                self.assertEqual(app.test_client().get(URL).status_code,503)
        app=create_app(authorize=lambda _:True);w.install(app,Mock(),period_reader=f.PeriodReader(Store([row()]),clock=Mock(side_effect=[0,0,11])))
        with patch('integration.weekly_report._render.render_pdf',side_effect=AssertionError('render')):
            self.assertEqual(app.test_client().get(URL).status_code,503)
    def test_deadline_after_eof_negative_clock_and_exact_bytes(self):
        for times in ([0,0,0,11],[0,-1]):
            store=Store([row()])
            with self.assertRaises(ValueError):f.PeriodReader(store,clock=Mock(side_effect=times))(START,END)
            self.assertTrue(store.cursor.closed)
        import json
        from integration.public_weekly_pdf import _bounded_rows
        size=len(json.dumps(_bounded_rows({'geo':[row()]})[0],ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())
        with patch.object(f,'MAX_BYTES',size):self.assertEqual(len(f.PeriodReader(Store([row()]))(START,END)[0]),1)
    def test_budget_and_boundary_mutants(self):
        from pathlib import Path
        import time,json
        source=Path(f.__file__).read_text()
        cases=[('scan','scanned > MAX_SCAN','scanned > MAX_SCAN + 1','MAX_SCAN',2,3),
               ('rows','len(rows) >= MAX_ROWS','len(rows) > MAX_ROWS','MAX_ROWS',2,3),
               ('bytes','size > MAX_BYTES','size < -1','MAX_BYTES',1,1),
               ('time','0 <= elapsed <= MAX_SECONDS','0 <= elapsed <= MAX_SECONDS + 100','MAX_SECONDS',1,1)]
        for name,old,new,budget,value,count in cases:
            self.assertEqual(source.count(old),1)
            ns={'__name__':'integration.weekly_full_store_mutant'};exec(compile(source.replace(old,new),name,'exec'),ns);ns[budget]=value
            clock=Mock(side_effect=[0,0,2,2])if name=='time'else time.monotonic
            self.assertTrue(ns['PeriodReader'](Store([row(i)for i in range(count)]),clock=clock)(START,END)[0])
            with patch.object(f,budget,value),self.assertRaises(ValueError):
                f.PeriodReader(Store([row(i)for i in range(count)]),clock=Mock(side_effect=[0,0,2,2])if name=='time'else time.monotonic)(START,END)
        ns={'__name__':'integration.weekly_full_store_mutant'};exec(compile(source.replace('start <= stamp < end','start <= stamp <= end'),'end','exec'),ns)
        endrow=dict(row(),published=END.isoformat());self.assertEqual(len(ns['PeriodReader'](Store([endrow]))(START,END)[0]),1)
        self.assertEqual(len(f.PeriodReader(Store([endrow]))(START,END)[0]),0)
    def test_zoned_and_row_shape_guards(self):
        from pathlib import Path
        source=Path(f.__file__).read_text()
        ns={'__name__':'integration.weekly_full_store_mutant'};exec(compile(source.replace('or d.tzinfo is None',''),'zone','exec'),ns)
        self.assertEqual(ns['PeriodReader'](Store([]))(START.replace(tzinfo=None),END.replace(tzinfo=None))[0],[])
        with self.assertRaises(ValueError):f.PeriodReader(Store([]))(START.replace(tzinfo=None),END.replace(tzinfo=None))
        with patch.object(f,'_bounded_rows',return_value=[]),self.assertRaises(f.PeriodUnavailable):f.PeriodReader(Store([row()]))(START,END)
        # Removing length check still fails at public[0] and is normalized to
        # PeriodUnavailable. Equivalent failure mutant, not a survival claim.
    def test_served_copy_replacement_targets_present(self):
        from pathlib import Path
        js=(w.ROOT/'integration/ui/public_weekly.js').read_text()
        for target in ['latest-100 supplied sample','supplied sample rows only, not complete weekly history',"if(r.status===503){status.textContent='Supplied-news PDF unavailable. Try manually later. No report saved or sent.';return;}"]:
            self.assertEqual(js.count(target),1,target)
        html=(w.ROOT/'integration/ui/weekly.html').read_text()
        self.assertEqual(html.count('PRIVATE STAGING'),1)
        # PUBLIC SUPPLIED NEWS and latest100 label are inserted by install.
        app=create_app(authorize=lambda _:True);w.install(app,Mock(),period_reader=f.PeriodReader(Store([])))
        page=app.test_client().get('/workspace/weekly').text
        self.assertIn('PUBLIC PERIOD NEWS',page);self.assertNotIn('Latest-100 sample',page)
    def test_env_gates(self):
        self.assertFalse(f.enabled({}))
        for env in [{f.FLAG:'yes'},{f.FLAG:'true'}]:
            with self.assertRaises(ValueError):f.enabled(env)
        self.assertTrue(f.enabled({f.FLAG:'true','PUBLIC_WEEKLY_PDF_ENABLED':'true','PUBLIC_NEWS_READ_ENABLED':'true','PUBLIC_NEWS_FULL_PAGES_ENABLED':'true'}))

if __name__=='__main__':unittest.main()
