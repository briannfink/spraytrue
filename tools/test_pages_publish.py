"""Offline checks for the single Pages publication path. No GitHub calls."""
import importlib.util, os, pathlib, subprocess, sys, unittest
from unittest.mock import patch
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

def wait_step_env(text):
  """Env mapping on the Wait for Pages step. Later keys do not count."""
  lines = text.splitlines()
  start = next(i for i, line in enumerate(lines) if line.strip() == "- name: Wait for Pages to publish the data commit")
  env = {}
  in_env = False
  for line in lines[start + 1:]:
    if line.startswith("      - "):
      break
    stripped = line.strip()
    if stripped == "env:":
      in_env = True
      continue
    if not in_env:
      continue
    if not line.startswith("          ") or stripped.startswith("#"):
      if stripped and not stripped.startswith("#"):
        break
      continue
    key, sep, val = stripped.partition(":")
    if sep:
      env[key] = val.strip().strip("'\"")
  return env

class StepEnv(unittest.TestCase):
  def test_wait_step_wires_every_name_the_script_requires(self):
    text = (ROOT / ".github/workflows/update-wsda.yml").read_text()
    env = wait_step_env(text)
    self.assertEqual(w.missing_required({key: "present" for key in env}), [])
    self.assertEqual(env["GITHUB_TOKEN"], "${{ github.token }}")
    self.assertEqual(env["GITHUB_REPOSITORY"], "${{ github.repository }}")
    self.assertEqual(env["PAGES_SHA"], "${{ steps.commit.outputs.sha }}")
    # The job token is not an ambient variable. Only the step env is visible.
    wired = {key: ("value" if raw.startswith("${{") else raw) for key, raw in env.items()}
    with patch.dict(os.environ, wired, clear=True), patch.object(w, "wait_for_commit", return_value={"status": "built"}) as waited:
      w.main()
    waited.assert_called_once()
  def test_step_without_token_exits_the_way_review_reproduced(self):
    env = os.environ.copy()
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    env.update({
      "PAGES_SHA": NEW,
      "PAGES_TIMEOUT_SECONDS": "600",
      "PAGES_POLL_SECONDS": "10",
      "GITHUB_REPOSITORY": "briannfink/spraytrue",
    })
    proc = subprocess.run([sys.executable, str(ROOT / "tools/wait_for_pages.py")], env=env, capture_output=True, text=True)
    self.assertEqual(proc.returncode, 1)
    self.assertIn("PAGES_SHA, GITHUB_REPOSITORY, and GITHUB_TOKEN are required", proc.stderr)
if __name__ == "__main__":
  unittest.main()
