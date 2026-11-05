#!/usr/bin/env python3
"""Refresh the bundled Washington State Dept of Agriculture (WSDA) product index.

Source: public WAPRS / WALTR search at
  https://fortress.wa.gov/agr/pisces/WSDASearch/Default
No public REST API; CSV export postback is broken without ASP.NET client scripts,
so this script paginates the HTML result grids (25 rows/page) politely (~1s between
pages, identifiable User-Agent). Government data meant for public download.

Writes: data/wsda-products.json (compact, searched offline by the app).

Usage: python3 tools/update_wsda.py [--adjuvants] [--minrisk] [--section3] [--fertilizer] [--all]
Default: --adjuvants --minrisk --fertilizer (section3 is large / slow; pass --section3 or --all).
"""
from __future__ import annotations
import argparse, html as htmlmod, json, re, sys, time, urllib.parse, urllib.request, http.cookiejar
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wsda-products.json"
BASE = "https://fortress.wa.gov/agr/pisces/WSDASearch"
UA = "TankMixDataBot/1.0 (+https://briannfink.github.io/tankmix/; offline dataset refresh; ~1 req/s; contact via GitHub briannfink/tankmix)"
DELAY = 1.0

def log(*a):
  print(*a, flush=True)

class Session:
  def __init__(self):
    self.cj = http.cookiejar.CookieJar()
    self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
  def get(self, url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with self.op.open(req, timeout=180) as r:
      return r.read().decode("utf-8", "replace"), r.geturl()
  def post(self, url, fields, referer):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={
      "User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": referer})
    with self.op.open(req, timeout=180) as r:
      return r.read().decode("utf-8", "replace"), r.geturl()

def hidden(html):
  fields = {}
  for m in re.finditer(r"<input[^>]+>", html, re.I):
    tag = m.group(0)
    nm = re.search(r'name="([^"]*)"', tag)
    if not nm: continue
    typ = re.search(r'type="([^"]*)"', tag, re.I)
    val = re.search(r'value="([^"]*)"', tag)
    t = (typ.group(1).lower() if typ else "text")
    if t == "hidden" or nm.group(1).startswith("__"):
      fields[nm.group(1)] = val.group(1) if val else ""
  return fields

def fill_empties(html, f):
  for m in re.finditer(r'<input[^>]*name="([^"]+)"[^>]*>', html, re.I):
    name = m.group(1)
    if name in f: continue
    tag = m.group(0)
    typ = re.search(r'type="([^"]*)"', tag, re.I)
    t = (typ.group(1).lower() if typ else "text")
    if t in ("submit", "button", "image", "checkbox", "radio", "file"): continue
    val = re.search(r'value="([^"]*)"', tag)
    f[name] = val.group(1) if val else ""
  for m in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', html, re.I | re.S):
    name, inner = m.group(1), m.group(2)
    if name in f: continue
    om = re.search(r'<option[^>]*value="([^"]*)"', inner)
    f[name] = om.group(1) if om else ""

def clean(s):
  s = htmlmod.unescape(re.sub(r"<[^>]+>", "", s or ""))
  return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()

def parse_pest_rows(html):
  out = []
  for m in re.finditer(r"<tr[^>]*>(.*?ShowProduct\((\d+)\).*?)</tr>", html, re.I | re.S):
    row, pid = m.group(1), m.group(2)
    tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.I | re.S)
    if len(tds) < 10: continue
    cols = [clean(td) for td in tds]
    lab = re.search(r'href="(\./Uploads/[^"]+\.pdf)"', row, re.I)
    label = ""
    if lab:
      rel = lab.group(1).replace("\\", "/")
      if rel.startswith("./"): rel = rel[2:]
      label = BASE + "/" + rel
    out.append({
      "id": int(pid), "name": cols[0], "reg": cols[1], "company": cols[2], "user": cols[3],
      "ai": cols[4], "rup": cols[5], "signal": cols[6], "type": cols[7], "status": cols[8],
      "exp": cols[9], "cannabis": cols[10] if len(cols) > 10 else "", "sln": cols[11] if len(cols) > 11 else "",
      "label": label, "db": "waprs",
    })
  return out

def parse_fert_rows(html):
  """Fertilizer grid: ShowProduct opens ViewWALTRProductInfo — columns differ slightly."""
  out = []
  for m in re.finditer(r"<tr[^>]*>(.*?ShowProduct\((\d+)\).*?)</tr>", html, re.I | re.S):
    row, pid = m.group(1), m.group(2)
    tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.I | re.S)
    if len(tds) < 4: continue
    cols = [clean(td) for td in tds]
    lab = re.search(r'href="(\./Uploads/[^"]+\.pdf)"', row, re.I)
    label = ""
    if lab:
      rel = lab.group(1).replace("\\", "/")
      if rel.startswith("./"): rel = rel[2:]
      label = BASE + "/" + rel
    # Heuristic: name, company / reg vary — keep raw cols + best-effort fields
    rec = {
      "id": int(pid), "name": cols[0], "reg": cols[1] if len(cols) > 1 else "",
      "company": cols[2] if len(cols) > 2 else "", "type": "Fertilizer",
      "status": "", "exp": "", "ai": "", "signal": "", "user": "", "rup": "",
      "cannabis": "", "sln": "", "label": label, "db": "waltr",
      "npk": "", "cols": cols,  # temporary; trimmed later
    }
    out.append(rec)
  return out

def current_page(html, colspan="14"):
  pager = re.search(rf'(<td colspan="{colspan}">.*?</td>)', html, re.I | re.S)
  if not pager:
    pager = re.search(r'(<td colspan="\d+">.*?</td>)', html, re.I | re.S)
  if not pager: return None
  m = re.search(r"<span>(\d+)</span>", pager.group(1))
  return int(m.group(1)) if m else None

def next_page_target(html, grid="dgProducts", colspan="14"):
  pager = re.search(rf'(<td colspan="{colspan}">.*?</td>)', html, re.I | re.S)
  if not pager:
    pager = re.search(r'(<td colspan="\d+">.*?</td>)', html, re.I | re.S)
  if not pager: return None
  cell = pager.group(1)
  cur = re.search(r"<span>(\d+)</span>", cell)
  if not cur: return None
  cur_n = int(cur.group(1))
  # Walk pager HTML in order: prefer explicit cur+1; else the first "..." that appears AFTER the current <span>
  pos_cur = cur.end()
  # tokens: (start, end, target_or_None, label)
  tokens = []
  for m in re.finditer(
      r"javascript:__doPostBack\((?:&#39;|')((?:dg|grd)\w*\$ctl\d+\$ctl\d+)(?:&#39;|')[^>]*>([^<]+)</a>",
      cell):
    tokens.append((m.start(), m.group(1), clean(m.group(2))))
  for start, tgt, lab in tokens:
    if lab.isdigit() and int(lab) == cur_n + 1:
      return tgt
  for start, tgt, lab in tokens:
    if "..." in lab and start >= pos_cur:
      return tgt  # forward ellipsis only
  return None

def scrape_pest(session: Session, kind: str, checkboxes: dict) -> list:
  html, url = session.get(BASE + "/Default")
  f = hidden(html); f["btnSearchPest"] = "Search for Pesticide Products"
  html, url = session.post(BASE + "/Default", f, url)
  time.sleep(DELAY)
  f = hidden(html); fill_empties(html, f)
  f.update(checkboxes); f["btnSearch"] = "Search for Products"
  html, url = session.post(BASE + "/PesticideSearch", f, url)
  m = re.search(r'id="lblTotal">(\d+)<', html)
  total = int(m.group(1)) if m else 0
  log(f"[{kind}] total={total}")
  seen = {}
  page = 1
  while True:
    for r in parse_pest_rows(html):
      r["kind"] = kind
      seen[r["id"]] = r
    cur = current_page(html) or page
    if page == 1 or page % 10 == 0:
      log(f"[{kind}] page {cur}: {len(seen)}/{total}")
    if len(seen) >= total > 0: break
    tgt = next_page_target(html)
    if not tgt:
      log(f"[{kind}] stop at page {cur}, have {len(seen)}/{total}")
      break
    time.sleep(DELAY)
    f = hidden(html); fill_empties(html, f); f.update(checkboxes)
    f["__EVENTTARGET"] = tgt; f["__EVENTARGUMENT"] = ""
    html, url = session.post(BASE + "/PesticideSearch", f, url)
    page += 1
    if page > 900: break
  log(f"[{kind}] done {len(seen)}")
  return list(seen.values())

def scrape_fert(session: Session) -> list:
  html, url = session.get(BASE + "/Default")
  f = hidden(html); f["btnSearchFert"] = "Search for Fertilizer Products"
  html, url = session.post(BASE + "/Default", f, url)
  time.sleep(DELAY)
  f = hidden(html); fill_empties(html, f); f["btnSearch"] = "Search for Products"
  html, url = session.post(BASE + "/FertilizerSearch", f, url)
  # discover grid + colspan from first pager
  m = re.search(r'id="lblTotal">(\d*)<', html)
  total = int(m.group(1)) if m and m.group(1) else 0
  log(f"[fertilizer] total={total}")
  # Inspect headers once
  ths = [clean(t) for t in re.findall(r"<th[^>]*>(.*?)</th>", html, re.I | re.S)]
  log(f"[fertilizer] columns: {ths[:12]}")
  seen = {}
  page = 1
  grid = "dgProducts"
  gm = re.search(r"__doPostBack\((?:&#39;|')((?:dg|grd)\w*)\$ctl", html)
  if gm: grid = gm.group(1)
  while True:
    rows = parse_fert_rows(html)
    # map columns by header if possible
    for r in rows:
      cols = r.pop("cols", [])
      # try to find status/exp/npk from headers
      def col(name_substr):
        for i, h in enumerate(ths):
          if name_substr.lower() in h.lower() and i < len(cols):
            return cols[i]
        return ""
      if ths:
        r["name"] = col("Product Name") or col("Brand Name") or r["name"]
        r["reg"] = col("Product #") or col("Reg") or col("WSDA") or r["reg"]
        r["company"] = col("Company") or r["company"]
        r["status"] = col("Status") or r["status"]
        r["exp"] = col("Expir") or r["exp"]
        grade = col("Grade")
        if grade: r["npk"] = grade
        src = col("Nutrient Sources")
        if src: r["ai"] = src
      r["kind"] = "fertilizer"
      seen[r["id"]] = r
    cur = current_page(html) or page
    if page == 1 or page % 10 == 0:
      log(f"[fertilizer] page {cur}: {len(seen)}/{total}")
    if total and len(seen) >= total: break
    if not rows and page > 1: break
    tgt = next_page_target(html, grid=grid)
    if not tgt:
      log(f"[fertilizer] stop at page {cur}, have {len(seen)}/{total}")
      break
    time.sleep(DELAY)
    f = hidden(html); fill_empties(html, f)
    f["__EVENTTARGET"] = tgt; f["__EVENTARGUMENT"] = ""
    html, url = session.post(BASE + "/FertilizerSearch", f, url)
    page += 1
    if page > 900: break
  log(f"[fertilizer] done {len(seen)}")
  return list(seen.values())

def compact(products):
  """Drop empty strings; keep stable key order for gzip-friendly diffs."""
  keys = ["id","name","reg","company","type","status","exp","ai","signal","user","rup","label","kind","db","npk","cannabis","sln"]
  out = []
  for p in products:
    row = {}
    for k in keys:
      v = p.get(k)
      if v is None or v == "": continue
      row[k] = v
    out.append(row)
  return out

def is_epa_reg(reg: str) -> bool:
  """Section 3 / distributor EPA-style numbers vs WA adjuvant-style."""
  r = (reg or "").strip().upper()
  if not r: return False
  # classic EPA: 524-549 or 100-1001-12345 (distributor)
  if re.fullmatch(r"\d{1,6}-\d{1,5}(?:-\d{1,5})?", r):
    # WA adjuvant regs often look similar; callers also use product type
    return True
  return False

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--adjuvants", action="store_true")
  ap.add_argument("--minrisk", action="store_true")
  ap.add_argument("--section3", action="store_true")
  ap.add_argument("--fertilizer", action="store_true")
  ap.add_argument("--all", action="store_true")
  args = ap.parse_args()
  if not any([args.adjuvants, args.minrisk, args.section3, args.fertilizer, args.all]):
    args.adjuvants = args.minrisk = args.fertilizer = True
  if args.all:
    args.adjuvants = args.minrisk = args.section3 = args.fertilizer = True

  # Merge with existing file so partial refreshes keep other kinds
  existing = []
  if OUT.exists():
    try:
      existing = json.loads(OUT.read_text()).get("products") or []
    except Exception:
      existing = []
  by_id = {(p.get("db","waprs"), p["id"]): p for p in existing if "id" in p}

  s = Session()
  if args.adjuvants:
    for p in scrape_pest(s, "adjuvant", {"chkSpray": "on"}):
      by_id[(p["db"], p["id"])] = p
  if args.minrisk:
    for p in scrape_pest(s, "25b", {"chk25b": "on"}):
      by_id[(p["db"], p["id"])] = p
  if args.section3:
    for p in scrape_pest(s, "section3", {"chkSection3": "on"}):
      by_id[(p["db"], p["id"])] = p
  if args.fertilizer:
    for p in scrape_fert(s):
      by_id[(p["db"], p["id"])] = p

  products = compact(sorted(by_id.values(), key=lambda p: (p.get("kind",""), p.get("name",""), p.get("id",0))))
  counts = {}
  for p in products:
    counts[p.get("kind") or "other"] = counts.get(p.get("kind") or "other", 0) + 1
  payload = {
    "source": "WSDA WAPRS/WALTR public search",
    "url": BASE + "/Default",
    "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "counts": counts,
    "n": len(products),
    "products": products,
  }
  OUT.parent.mkdir(parents=True, exist_ok=True)
  OUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
  log(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(products)} products) counts={counts}")

if __name__ == "__main__":
  main()
