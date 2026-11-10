"""Offline checks for the single Pages publication path. No GitHub calls."""
import importlib.util, pathlib, unittest
ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("wait_for_pages", pathlib.Path(__file__).with_name("wait_for_pages.py"))
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)

OLD = "b4dfca617737ac030dd599a0e8c34baaa17dc9ee"
NEW = "e4586264f059eeb6421bddd279a1616ae74d1a96"

def build(sha, status, message=None):
  return {"commit": sha, "status": status, "error": {"message": message}}

class Decide(unittest.TestCase):
  def test_previous_success_is_not_this_commit(self):
    self.assertEqual(w.decide([build(OLD, "built")], NEW)[0], "wait")
  def test_data_commit_built(self):
    state, detail = w.decide([build(NEW, "built"), build(OLD, "built")], NEW)
    self.assertEqual(state, "success")
    self.assertEqual(detail["commit"], NEW)
  def test_in_progress_waits(self):
    self.assertEqual(w.decide([build(NEW, "building")], NEW)[0], "wait")
  def test_errored_build_fails(self):
    state, detail = w.decide([build(NEW, "errored", "deployment failed")], NEW)
    self.assertEqual(state, "failure")
    self.assertIn("deployment failed", detail)
  def test_recovered_build_wins_over_an_earlier_error(self):
    self.assertEqual(w.decide([build(NEW, "built"), build(NEW, "errored", "blocked")], NEW)[0], "success")
  def test_empty_list_waits(self):
    self.assertEqual(w.decide([], NEW)[0], "wait")

class Wait(unittest.TestCase):
  def run_wait(self, responses, timeout=30, poll=10):
    clock = {"t": 0}
    pending = list(responses)
    def fetch():
      return pending.pop(0) if len(pending) > 1 else pending[0]
    def sleep(n):
      clock["t"] += n
    def now():
      return clock["t"]
    return w.wait_for_commit(NEW, fetch, sleep, now, timeout, poll)
  def test_waits_until_the_data_commit_is_built(self):
    got = self.run_wait([[build(OLD, "built")], [build(NEW, "building")], [build(NEW, "built")]])
    self.assertEqual(got["commit"], NEW)
  def test_timeout_while_only_the_old_commit_is_built(self):
    with self.assertRaisesRegex(RuntimeError, "did not publish"):
      self.run_wait([[build(OLD, "built")]], timeout=20, poll=10)
  def test_error_fails_immediately(self):
    with self.assertRaisesRegex(RuntimeError, "blocked"):
      self.run_wait([[build(NEW, "errored", "blocked")]])

class Workflow(unittest.TestCase):
  def setUp(self):
    self.text = (ROOT / ".github/workflows/update-wsda.yml").read_text()
  def test_one_publication_path(self):
    self.assertNotIn("uses: actions/deploy-pages", self.text)
    self.assertNotIn("uses: actions/upload-pages-artifact", self.text)
    self.assertNotIn("id-token:", self.text)
    self.assertNotIn("environment:", self.text)
    self.assertIn("pages: write", self.text)
    self.assertIn("contents: write", self.text)
    self.assertIn("python3 tools/wait_for_pages.py", self.text)
    self.assertIn("data/wsda-products.json wsda-products.json preview/wsda-products.json sw.js", self.text)
    self.assertIn("python3 tools/update_wsda.py --adjuvants --minrisk --fertilizer", self.text)
    self.assertIn("python3 -m unittest discover -s tools -p 'test_*.py' -v", self.text)
if __name__ == "__main__":
  unittest.main()
