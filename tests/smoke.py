#!/usr/bin/env python3
"""Smoke tests against a running site (a local build, a preview deployment, or production).

    python tests/smoke.py --url https://w3planner.pages.dev/
    python tests/smoke.py --url https://preview.w3planner.pages.dev/ --expect-index dist/game/index.html --wait 90

Checks: the page loads without console errors, failed requests or Content-Security-Policy violations; the security headers
and the version are right; every image loads; every link fixture (all versions) opens correctly; a new link can be
created and reopened. With --expect-index / --expect-version it first polls the plain URL (no query string, no special headers:
exactly what a browser loads) until the site serves that index.html and version, for up to --wait seconds, so a deployment
that is still spreading through Cloudflare's edge is not mistaken for a broken one. Only then can a check fail. Exit code 0 = all passed.
"""
import argparse, hashlib, json, re, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import linkcheck
from playwright.sync_api import sync_playwright

NEEDED_HEADERS = ("content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy")


def fetch(url):
    """GET exactly what a browser's first visit gets: the plain URL, no cache-buster, no cache headers."""
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "w3planner-smoke"}), timeout=20) as r: return r.status, r.read()


def wait_for_site(url, want_sha=None, want_version=None, seconds=0, interval=5):
    """Poll `url` until it serves an index.html with this sha256 and this APP_VERSION (whichever are given), for at most `seconds`.
    Returns (ok, detail). It polls the plain URL because a cache-busting query string can reach the new deployment while the
    plain URL, the one people and the browser use, is still answered from Cloudflare's edge cache with the old one."""
    end, last = time.time() + seconds, "no answer"
    while True:
        try:
            st, body = fetch(url); sha = hashlib.sha256(body).hexdigest(); m = re.search(rb'APP_VERSION="([^"]*)"', body); ver = m.group(1).decode() if m else None
            if st == 200 and (want_sha is None or sha == want_sha) and (want_version is None or ver == want_version): return True, ""
            last = "HTTP %d, version %s, index.html sha256 %s..." % (st, ver, sha[:12])
        except Exception as e: last = str(e)[:100]
        if time.time() >= end: return False, "still not serving the expected build after %ds: %s" % (seconds, last)
        time.sleep(interval)


def run_smoke(url, expect_version=None, expect_index=None, wait=0, results=None):
    """Returns (ok, results). results = list of (name, ok, detail)."""
    url = url if url.endswith("/") else url + "/"; res = results if results is not None else []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail)); print(("  PASS  " if ok else "  FAIL  ") + name + (("  (" + str(detail) + ")") if detail != "" else ""), flush=True)

    if expect_index or expect_version:
        sha = hashlib.sha256(Path(expect_index).read_bytes()).hexdigest() if expect_index else None; ok, detail = wait_for_site(url, sha, expect_version, wait)
        check("%s serves the build that was deployed (waited for the plain URL)" % url, ok, detail)
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
        if expect_index: check("the page is served with Cache-Control: no-cache (so a new version shows at once)", "no-cache" in h.get("cache-control", ""), h.get("cache-control"))
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
