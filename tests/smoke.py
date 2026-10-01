#!/usr/bin/env python3
"""Smoke tests against a running site (a local build, a preview deployment, or production).

    python tests/smoke.py --url https://w3planner.pages.dev/
    python tests/smoke.py --url https://preview.w3planner.pages.dev/ --expect-index dist/game/index.html --wait 90

Checks: the page loads without console errors, failed requests or Content-Security-Policy violations; the security headers
and the version are right; every image loads; every link fixture (all versions) opens correctly; a new link can be
created and reopened. With --expect-index / --expect-version it first waits, for up to --wait seconds, until the site serves that
index.html and version TWICE IN A ROW to the very browser that runs the checks (a fresh browser context each time, the plain URL,
no cache-buster), so a deployment that is still spreading through Cloudflare's edge is not mistaken for a broken one. A Python
HTTP client is not good enough: after the v25 and v26 promotes it saw the new page while the browser, seconds later, still saw
the old one. Only then can a check fail. Exit code 0 = all passed.
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


def browser_fetch(browser):
    """A fetch() that is a real browser visit: a fresh context (no HTTP cache, no cookies) loading the plain URL."""
    def get(url):
        ctx = browser.new_context()
        try: r = ctx.new_page().goto(url, timeout=30000); return r.status, r.body()
        finally: ctx.close()
    return get


def wait_for_site(url, want_sha=None, want_version=None, seconds=0, interval=5, fetch=fetch, confirmations=2):
    """Wait until `fetch(url)` returns an index.html with this sha256 and this APP_VERSION (whichever are given) `confirmations` times
    in a row, for at most `seconds`. Returns (ok, detail). The plain URL is used because a cache-busting query string can reach the new
    deployment while the plain URL, the one people use, is still answered with the old one; and the fetch should be the browser that
    runs the checks, because two clients asking at the same moment can be answered differently while Cloudflare's edge catches up."""
    end, last, streak = time.time() + seconds, "no answer", 0
    if seconds <= 0: confirmations = 1                                       # no time to wait: one look
    while True:
        try:
            st, body = fetch(url); sha = hashlib.sha256(body).hexdigest(); m = re.search(rb'APP_VERSION="([^"]*)"', body); ver = m.group(1).decode() if m else None
            if st == 200 and (want_sha is None or sha == want_sha) and (want_version is None or ver == want_version):
                streak += 1
                if streak >= confirmations: return True, ""
            else: streak = 0; last = "HTTP %d, version %s, index.html sha256 %s..." % (st, ver, sha[:12])
        except Exception as e: streak = 0; last = str(e)[:100]
        if time.time() >= end: return False, "still not serving the expected build after %ds: %s" % (seconds, last)
        time.sleep(interval)


def run_smoke(url, expect_version=None, expect_index=None, wait=0, results=None):
    """Returns (ok, results). results = list of (name, ok, detail)."""
    url = url if url.endswith("/") else url + "/"; res = results if results is not None else []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail)); print(("  PASS  " if ok else "  FAIL  ") + name + (("  (" + str(detail) + ")") if detail != "" else ""), flush=True)

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        if expect_index or expect_version:
            sha = hashlib.sha256(Path(expect_index).read_bytes()).hexdigest() if expect_index else None
            ok, detail = wait_for_site(url, sha, expect_version, wait, fetch=browser_fetch(b))
            check("%s serves the build that was deployed (browser, plain URL, twice in a row)" % url, ok, detail)
            if not ok: b.close(); return False, res
        pg = b.new_page(viewport={"width": 1500, "height": 950}); errs, fails, bad = [], [], []
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
        if expect_version and ver != expect_version: b.close(); return False, res           # the edge answered the old page: the other checks would only test that page, so this is the one (lag-style) failure
        imgs = pg.evaluate("[...document.images].filter(i=>!(i.complete&&i.naturalWidth>0)).map(i=>i.src.slice(-40))"); check("every image on the page loads", not imgs, imgs[:3])
        linkcheck.check_fixtures(b, url, "fixtures", check)
        if pg.evaluate("!!document.getElementById('eqbtn')"):
            import eqcheck
            eqcheck.run(b, url, check, "equipment")
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
