#!/usr/bin/env python3
"""Wait until GitHub Pages has built one commit.

This repo publishes from branch main. A push of the data commit starts that
build. Callers must not also call actions/deploy-pages: that API records the
workflow's starting SHA and blocks the branch build of the new commit.

The network fetch is separate so tests can supply Pages build records.
"""
from __future__ import annotations
import json, os, sys, time, urllib.error, urllib.request

def decide(builds, sha):
  """Return ('success', build), ('failure', message), or ('wait', message)."""
  matches = [b for b in builds or [] if b.get("commit") == sha]
  built = [b for b in matches if b.get("status") == "built"]
  if built:
    return "success", built[0]
  errored = [b for b in matches if b.get("status") in ("errored", "error", "failed")]
  if errored:
    message = (errored[0].get("error") or {}).get("message") or errored[0].get("status")
    return "failure", f"GitHub Pages failed to publish {sha}: {message}"
  if matches:
    return "wait", f"Pages build for {sha} is {matches[0].get('status')}"
  latest = (builds or [{}])[0].get("commit")
  return "wait", f"Pages has no build for {sha} yet; latest is {latest or 'none'}"

def wait_for_commit(sha, fetch_builds, sleep, monotonic, timeout, poll):
  deadline = monotonic() + timeout
  while True:
    state, detail = decide(fetch_builds(), sha)
    if state == "success":
      return detail
    if state == "failure":
      raise RuntimeError(detail)
    if monotonic() >= deadline:
      raise RuntimeError(f"GitHub Pages did not publish {sha} within {int(timeout)}s ({detail})")
    print(detail, flush=True)
    sleep(poll)

def fetch_pages_builds(repo, token, urlopen=urllib.request.urlopen):
  req = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/pages/builds?per_page=10",
    headers={
      "Authorization": f"Bearer {token}",
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "SprayTrue-pages-wait",
    },
  )
  try:
    with urlopen(req, timeout=30) as resp:
      body = json.load(resp)
  except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", "replace")[:500]
    raise RuntimeError(f"GitHub Pages builds request failed: HTTP {exc.code} {detail}") from exc
  if not isinstance(body, list):
    raise RuntimeError("GitHub Pages builds response was not a list")
  return body

def main():
  sha = os.environ.get("PAGES_SHA", "").strip()
  repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
  token = os.environ.get("GITHUB_TOKEN", "").strip()
  if not sha or not repo or not token:
    raise RuntimeError("PAGES_SHA, GITHUB_REPOSITORY, and GITHUB_TOKEN are required")
  timeout = float(os.environ.get("PAGES_TIMEOUT_SECONDS", "600"))
  poll = float(os.environ.get("PAGES_POLL_SECONDS", "10"))
  build = wait_for_commit(
    sha,
    lambda: fetch_pages_builds(repo, token),
    time.sleep,
    time.monotonic,
    timeout,
    poll,
  )
  print(f"GitHub Pages built {sha} (status {build.get('status')})", flush=True)

if __name__ == "__main__":
  try:
    main()
  except Exception as exc:
    print(f"Pages publication failed: {exc}", file=sys.stderr, flush=True)
    sys.exit(1)
