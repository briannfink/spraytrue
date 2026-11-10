"""Offline fixtures only: never calls WSDA or changes published data."""
import importlib.util, json, pathlib, tempfile, unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('update_wsda',pathlib.Path(__file__).with_name('update_wsda.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def row(i,kind='adjuvant'):
    return {'id':i,'db':'waprs','name':f'Product {i}','kind':kind,'reg':f'WA-{i}'}
class FakeSession:
    def __init__(self,total=2):self.html=f'<span id="lblTotal">{total}</span>'
    def get(self,url):return self.html,url
    def post(self,url,*a):return self.html,url
class Completeness(unittest.TestCase):
    def test_exact_count(self):self.assertEqual(m.verify_complete('adjuvant',2,[row(1),row(2)]),[row(1),row(2)])
    def test_unknown_count(self):
        with self.assertRaisesRegex(RuntimeError,'NOT replaced'):m.verify_complete('x',0,[])
    def test_missing_page(self):
        with self.assertRaises(RuntimeError):m.verify_complete('x',3,[row(1)])
    def test_count_increase(self):
        with self.assertRaises(RuntimeError):m.verify_complete('x',1,[row(1),row(2)])
    def test_pest_parser_stops_early(self):
        with patch.object(m,'parse_pest_rows',return_value=[row(1)]),patch.object(m,'DELAY',0):
            with self.assertRaisesRegex(RuntimeError,'expected 2'):m.scrape_pest(FakeSession(2),'adjuvant',{})
    def test_exact_duplicate_listing_collapses_when_every_source_row_is_parsed(self):
        with patch.object(m,'parse_pest_rows',return_value=[row(1),row(1)]),patch.object(m,'DELAY',0):
            got=m.scrape_pest(FakeSession(2),'adjuvant',{})
        self.assertEqual([r['id'] for r in got],[1])
        self.assertEqual(got.wsda_meta,{'source_rows':2,'duplicate_rows':1})
    def test_conflicting_duplicate_id_rejected(self):
        other=row(1); other={**other,'name':'Different product'}
        with patch.object(m,'parse_pest_rows',return_value=[row(1),other]),patch.object(m,'DELAY',0):
            with self.assertRaisesRegex(RuntimeError,'conflicting'):m.scrape_pest(FakeSession(2),'adjuvant',{})
    def test_short_page_still_rejected(self):
        with patch.object(m,'parse_pest_rows',return_value=[row(1)]),patch.object(m,'PAGE_SIZE',2),patch.object(m,'DELAY',0):
            with self.assertRaisesRegex(RuntimeError,'NOT replaced'):m.scrape_pest(FakeSession(4),'adjuvant',{})
    def test_pest_complete(self):
        with patch.object(m,'parse_pest_rows',return_value=[row(1),row(2)]),patch.object(m,'DELAY',0):
            self.assertEqual(len(m.scrape_pest(FakeSession(2),'adjuvant',{})),2)
    def test_fertilizer_incomplete(self):
        with patch.object(m,'parse_fert_rows',return_value=[]),patch.object(m,'DELAY',0):
            with self.assertRaises(RuntimeError):m.scrape_fert(FakeSession(2))
    def test_failed_refresh_never_writes(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'wsda-products.json';original=json.dumps({'products':[row(77)],'fetched':'2020-01-01T00:00:00Z'});p.write_text(original)
            with patch.object(m,'OUT',p),patch.object(m,'scrape_pest',side_effect=[[row(1)],RuntimeError('incomplete')]),patch.object(m,'scrape_fert') as fert,patch('sys.argv',['update_wsda.py','--adjuvants','--minrisk','--fertilizer']):
                with self.assertRaises(RuntimeError):m.main()
                fert.assert_not_called()
            self.assertEqual(p.read_text(),original)
    def test_success_replaces_only_verified_category_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'wsda-products.json';p.write_text(json.dumps({'products':[row(77),row(9,'25b')],'fetched':'2020-01-01T00:00:00Z'}))
            with patch.object(m,'OUT',p),patch.object(m,'scrape_pest',return_value=[row(1)]),patch('sys.argv',['update_wsda.py','--adjuvants']):m.main()
            out=json.loads(p.read_text());self.assertEqual({r['id']for r in out['products']},{1,9});self.assertTrue(out['refreshes']['adjuvant']['verified']);self.assertEqual(out['last_successful'],'2020-01-01T00:00:00Z')
            self.assertEqual(len(list(pathlib.Path(d).iterdir())),1)
    def test_empty_refresh_retains_last_good(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'wsda-products.json';p.write_text('{"products":[]}')
            with patch.object(m,'OUT',p),patch.object(m,'scrape_pest',return_value=[]),patch('sys.argv',['update_wsda.py','--adjuvants']):
                with self.assertRaises(RuntimeError):m.main()
            self.assertEqual(p.read_text(),'{"products":[]}')
def fert_row(pid, reg, name):
    cells=[reg,'Co','Brand',name,'1-1-1','src','Approved','06/30/2027','',f'<input onclick="return ShowProduct({pid});" />']
    return '<tr>'+''.join(f'<td>{c}</td>' for c in cells)+'</tr>'
def fert_page(total, cur, rows, nxt=None):
    heads=''.join(f'<th>{h}</th>' for h in ['Product #','Company Name','Brand Name','Product Name','Grade','Nutrient Sources','Product Status','Expiration Date','ViewLabel','See More'])
    links=(f"<a href=\"javascript:__doPostBack('dgProducts$ctl29$ctl00','')\">{cur-1}</a>" if cur>1 else '')
    links+=f'<span>{cur}</span>'
    if nxt: links+=f"<a href=\"javascript:__doPostBack('dgProducts$ctl29$ctl02','')\">{nxt}</a>"
    body=''.join(fert_row(*r) for r in rows)
    return f'<html><span id="lblTotal">{total}</span><tr>{heads}</tr>{body}<td colspan="10">{links}</td></html>'
class Scripted:
    """get, then the fertilizer form post, then one post per result page."""
    def __init__(self, pages):
        self.pages=list(pages); self.n=0
    def get(self, url): return '<html></html>', url
    def post(self, url, *a):
        self.n+=1
        if self.n==1: return '<html></html>', url
        return self.pages[self.n-2], url
class FertilizerGrid(unittest.TestCase):
    def scrape(self, pages):
        with patch.object(m,'PAGE_SIZE',2),patch.object(m,'DELAY',0):
            return m.scrape_fert(Scripted(pages))
    def test_nov9_run_is_complete_only_when_all_source_rows_and_pages_were_read(self):
        # Run 42720353597 parsed every fertilizer page and was 4 rows short after id collapse.
        rows=[row(i,'fertilizer') for i in range(8890)]
        pages=list(range(1,357))
        self.assertEqual(len(m.verify_complete('fertilizer',8894,rows,8894,pages)),8890)
        with self.assertRaisesRegex(RuntimeError,'NOT replaced'):m.verify_complete('fertilizer',8894,rows,8890,pages)
        with self.assertRaisesRegex(RuntimeError,'pages'):m.verify_complete('fertilizer',8894,rows,8894,list(range(1,356)))
    def test_same_page_duplicate_listing_is_complete(self):
        # WALTR lists one product twice when two label files exist. Columns match; id matches.
        pages=[fert_page(4,1,[(99090,'0240-0021','Calpril'),(99090,'0240-0021','Calpril')],nxt=2),
               fert_page(4,2,[(100101,'1457-0001','38% Calcium Chloride'),(100102,'1457-0002','35% Calcium Chloride')])]
        got=self.scrape(pages)
        self.assertEqual([r['id'] for r in got],[99090,100101,100102])
        self.assertEqual(got.wsda_meta,{'source_rows':4,'duplicate_rows':1})
        self.assertEqual(got[0]['name'],'Calpril'); self.assertEqual(got[0]['reg'],'0240-0021')
    def test_duplicate_page_rejected(self):
        pages=[fert_page(4,1,[(1,'A-1','One'),(2,'A-2','Two')],nxt=2),
               fert_page(4,2,[(1,'A-1','One'),(2,'A-2','Two')])]
        with self.assertRaisesRegex(RuntimeError,'already-seen'):self.scrape(pages)
    def test_skipped_page_number_rejected(self):
        pages=[fert_page(4,1,[(1,'A-1','One'),(2,'A-2','Two')],nxt=2),
               fert_page(4,3,[(3,'A-3','Three'),(4,'A-4','Four')])]
        with self.assertRaisesRegex(RuntimeError,'server said 3'):self.scrape(pages)
    def test_conflicting_fertilizer_id_does_not_publish(self):
        pages=[fert_page(2,1,[(5,'Z-1','Alpha'),(5,'Z-2','Beta')])]
        with patch.object(m,'PAGE_SIZE',2),patch.object(m,'DELAY',0):
            with self.assertRaisesRegex(RuntimeError,'conflicting'):m.scrape_fert(Scripted(pages))
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'wsda-products.json'; original='{"products":[{"id":9,"kind":"adjuvant","db":"waprs","name":"Keep"}]}'; p.write_text(original)
            with patch.object(m,'OUT',p),patch.object(m,'scrape_fert',side_effect=RuntimeError('conflicting products. Last successful dataset was NOT replaced.')),patch('sys.argv',['update_wsda.py','--fertilizer']):
                with self.assertRaisesRegex(RuntimeError,'NOT replaced'):m.main()
            self.assertEqual(p.read_text(),original)
    def test_duplicate_listing_records_source_rows(self):
        pages=[fert_page(2,1,[(7,'0240-0021','Calpril'),(7,'0240-0021','Calpril')])]
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'wsda-products.json'; p.write_text('{"products":[]}')
            with patch.object(m,'OUT',p),patch.object(m,'PAGE_SIZE',2),patch.object(m,'DELAY',0),patch('sys.argv',['update_wsda.py','--fertilizer']):
                real=m.scrape_fert
                with patch.object(m,'scrape_fert',side_effect=lambda s: real(Scripted(pages))):
                    m.main()
            out=json.loads(p.read_text())
            self.assertEqual([r['id'] for r in out['products']],[7])
            self.assertEqual(out['refreshes']['fertilizer']['duplicate_rows'],1)
            self.assertEqual(out['refreshes']['fertilizer']['source_rows'],2)
            self.assertTrue(out['refreshes']['fertilizer']['verified'])
if __name__=='__main__':unittest.main()
