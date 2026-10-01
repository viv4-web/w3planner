#!/usr/bin/env python3
"""Smoke tests against a running site (a local build, a preview deployment, or production).

    python tests/smoke.py --url https://w3planner.pages.dev/
    python tests/smoke.py --url https://preview.w3planner.pages.dev/ --expect-index dist/game/index.html --wait 90

Checks: the page loads without console errors, failed requests or Content-Security-Policy violations; the security headers
and the version are right; every image loads; every link fixture (all versions) opens correctly; a new link can be
created and reopened. With --expect-index it first waits until the site serves that exact index.html, so a
deployment that is still spreading is not mistaken for a broken one. Exit code 0 = all passed.
"""
import argparse, hashlib, json, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import linkcheck
from playwright.sync_api import sync_playwright

NEEDED_HEADERS = ("content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy")


def fetch(url):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + "smoke=%d" % time.time(), headers={"Cache-Control": "no-cache", "User-Agent": "w3planner-smoke"})
    with urllib.request.urlopen(req, timeout=20) as r: return r.status, r.read()


def wait_for_index(url, want_sha, seconds):
    """Wait until `url` serves an index.html with this sha256. Returns (ok, detail)."""
    end, last = time.time() + seconds, "no answer"
    while True:
        try:
            st, body = fetch(url); got = hashlib.sha256(body).hexdigest()
            if st == 200 and got == want_sha: return True, ""
            last = "HTTP %d, index.html sha256 %s..." % (st, got[:12])
        except Exception as e: last = str(e)[:100]
        if time.time() >= end: return False, "still not serving the expected index.html: " + last
        time.sleep(5)


def run_smoke(url, expect_version=None, expect_index=None, wait=0, results=None):
    """Returns (ok, results). results = list of (name, ok, detail)."""
    url = url if url.endswith("/") else url + "/"; res = results if results is not None else []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail)); print(("  PASS  " if ok else "  FAIL  ") + name + (("  (" + str(detail) + ")") if detail != "" else ""), flush=True)

    if expect_index:
        sha = hashlib.sha256(Path(expect_index).read_bytes()).hexdigest(); ok, detail = wait_for_index(url, sha, wait)
        check("%s serves the index.html that was built" % url, ok, detail)
        if not ok: return False, res
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1500, "height": 950}); errs, fails, bad = [], [], []
        pg.add_init_script("window.__v=[];document.addEventListener('securitypolicyviolation',e=>window.__v.push(e.violatedDirective+' '+e.blockedURI))")
        pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:120]))
        pg.on("console", lambda m: errs.append("console: " + m.text[:120]) if m.type == "error" else None)
        pg.on("requestfailed", lambda r: fails.append(r.url[-60:]))
        pg.on("response", lambda r: bad.append("%d %s" % (r.status, r.url[-60:])) if r.status >= 400 else None)
        try:
            resp = pg.goto(url, timeout=30000); pg.wait_for_function(linkcheck.READY, timeout=15000); pg.wait_for_timeout(500)
        except Exception as e:
            check("page loads", False, str(e).split("\n")[0][:120]); b.close(); return False, res
        check("page loads (HTTP %d)" % resp.status, resp.status == 200)
        check("no console errors or script errors", not errs, errs[:2]); check("no failed requests", not fails, fails[:2]); check("no HTTP errors", not bad, bad[:2])
        check("no Content-Security-Policy violations", pg.evaluate("window.__v") == [], pg.evaluate("window.__v"))
        h = resp.headers; check("security headers are sent", all(h.get(k) for k in NEEDED_HEADERS), [k for k in NEEDED_HEADERS if not h.get(k)])
        ver = pg.evaluate("APP_VERSION"); check("version is %s" % (expect_version or ver), not expect_version or ver == expect_version, ver)
        imgs = pg.evaluate("[...document.images].filter(i=>!(i.complete&&i.naturalWidth>0)).map(i=>i.src.slice(-40))"); check("every image on the page loads", not imgs, imgs[:3])
        linkcheck.check_fixtures(b, url, "fixtures", check)
        # a new link can be created and reopened
        try:
            E = pg.evaluate; i = E("TREES[1].sk.findIndex(s=>!s.req.length)")
            E("document.getElementById('lvl').value=40;document.getElementById('bonuspts').value=3;pointsChanged()"); pg.locator('.tab[data-k="1"]').click()
            node = pg.locator('#treePanel g.node[data-i="%d"]' % i); node.click(); node.click(); pg.wait_for_timeout(200)
            E("S.muts[0]=MUTS.findIndex(m=>m.special);save()"); made = E("document.getElementById('link').value").split("#")[-1]; want = E(linkcheck.FULL_STATE)
            q = b.new_page(); q.goto(url + "#" + made); q.wait_for_function(linkcheck.READY, timeout=15000); got = q.evaluate(linkcheck.FULL_STATE); q.close()
            check("a new link can be created and reopened", made.startswith("v1.") and want["lv"][1][i] >= 1 and got == want, made[:20])
        except Exception as e:
            check("a new link can be created and reopened", False, str(e).split("\n")[0][:120])
        b.close()
    return all(r[1] for r in res), res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True); ap.add_argument("--expect-version"); ap.add_argument("--expect-index", help="path of the built index.html the site must serve")
    ap.add_argument("--wait", type=int, default=0, help="seconds to wait for --expect-index to appear")
    a = ap.parse_args(); ok, res = run_smoke(a.url, a.expect_version, a.expect_index, a.wait)
    print("\n%d checks: %d passed, %d failed" % (len(res), sum(r[1] for r in res), sum(not r[1] for r in res))); sys.exit(0 if ok else 1)
