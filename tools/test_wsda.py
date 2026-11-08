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
    def test_duplicate_ids_rejected(self):
        with patch.object(m,'parse_pest_rows',return_value=[row(1),row(1)]),patch.object(m,'DELAY',0):
            with self.assertRaises(RuntimeError):m.scrape_pest(FakeSession(2),'adjuvant',{})
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
if __name__=='__main__':unittest.main()
