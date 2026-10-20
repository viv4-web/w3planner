"""v37: the canonical address of the pages, and the handoff from w3planner.pages.dev, in a real browser.

canonical(check, site)                  five pages, one canonical each, no hash (no browser); offline_canonical(check, files): the offline package has none
run(b, site, tmp, check)                two local servers stand in for the two addresses (different ports are different origins, so localStorage does not cross):
                                        the OLD one serves tools/make_pages_redirect.py's output, the NEW one serves the build under /witcher-3/
Used by tests/run_all.py.

v38: notice(b, site, tmp, check, label) - the handoff notices stay until closed (x or Esc), in every browser run_all.py can start; redirect_targets(check, tmp) - the redirect page names no address but SITE_URL."""
import base64, json, re, shutil, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import serve, make_pages_redirect  # noqa: E402
from linkcheck import READY, FULL_STATE  # noqa: E402

PAGES = ["index.html", "help.html", "about.html", "privacy.html", "support.html"]
SITE_URL = "https://buildplanner.net/witcher-3/"
G1, G2 = "16c6c2f7e7a7bf4fa1fb373ac8cfb80f", "db56ea162c8b9744af4b43ee4cb1d247"
KEYS = make_pages_redirect.KEYS
LINK = [l for l in (ROOT / "tests/fixtures/links/v27.txt").read_text().split() if ".g1B" in l][-1]
NOTICE_TEXT = "(()=>{const n=document.getElementById('hoNotice');if(!n.hidden)return document.getElementById('hoMsg').textContent;const t=document.getElementById('toast');return t.hidden?'':document.getElementById('toastMsg').textContent})()"
b64 = lambda o: base64.urlsafe_b64encode((o if isinstance(o, str) else json.dumps(o)).encode()).decode().rstrip("=")
store = lambda manual, changed, save=None: json.dumps({"v": 1, "manual": manual, "save": save, "changed": changed})


def canonical(check, site):
    got = {}
    for p in PAGES:
        t = (Path(site) / p).read_text(encoding="utf-8"); got[p] = re.findall(r'<link rel="canonical" href="([^"]*)">', t)
    want = {p: [SITE_URL + ("" if p == "index.html" else p)] for p in PAGES}
    check("every page of the website has exactly one canonical, built from siteUrl in static/config.js: /witcher-3/, help, about, privacy, support (no hash)", got == want and all("#" not in v[0] for v in got.values()), got)


def offline_canonical(check, offline_files):
    bad = [n for n, t in offline_files.items() if "canonical" in t]
    check("the offline package's pages have no canonical", len(offline_files) == 5 and not bad, bad)


def run(b, site, tmp, check):
    new_root = Path(tmp) / "handoff-new"; shutil.copytree(site, new_root / "witcher-3")
    ns = serve.make_server(new_root, 0); threading.Thread(target=ns.serve_forever, daemon=True).start(); NEW = "http://127.0.0.1:%d/witcher-3/" % ns.server_address[1]
    old_dir = make_pages_redirect.build(Path(tmp) / "handoff-old", NEW)
    (old_dir / "x").mkdir(); shutil.copyfile(old_dir / "index.html", old_dir / "x/y.html")   # Cloudflare Pages answers any unknown path with index.html; this local server does not
    os_ = serve.make_server(old_dir, 0); threading.Thread(target=os_.serve_forever, daemon=True).start(); OLD = "http://127.0.0.1:%d/" % os_.server_address[1]
    check("the pages.dev redirect build has index.html, _headers, _redirects with the four static pages and no catch-all rule",
          all((old_dir / f).is_file() for f in ("index.html", "_headers", "_redirects")) and len(re.findall(r"^/\S+\s+\S+\s+301$", (old_dir / "_redirects").read_text(), re.M)) == 8
          and not re.search(r"^/\*", (old_dir / "_redirects").read_text(), re.M))
    qs_src = (ROOT / "src/quests.js").read_text(encoding="utf-8")
    check("the five handoff keys are the five w3p.quests.* constants of quests.js and of the redirect page",
          sorted(re.findall(r"const QS(?:_[A-Z]+)?_KEY='(w3p\.quests\.[a-z0-9]+)'", qs_src)) == sorted(KEYS) and all(k in (old_dir / "index.html").read_text() for k in KEYS))

    def visit(url, seed_old=None, seed_new=None, wait_new=True):
        """a fresh browser context; seed_old/seed_new: {key: value} written to that address's localStorage before its own scripts run"""
        ctx = b.new_context(viewport={"width": 1440, "height": 950}); pg = ctx.new_page(); errs, dlg = [], []
        pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:120])); pg.on("dialog", lambda d: (dlg.append(d.message), d.dismiss()))
        for origin, seed in ((OLD, seed_old), (NEW, seed_new)):
            if seed: ctx.add_init_script("if(location.origin===%s){const s=%s;for(const k in s)localStorage.setItem(k,s[k])}" % (json.dumps(origin.rstrip("/").split("/witcher-3")[0]), json.dumps(seed)))
        pg.goto(url)
        if wait_new:
            pg.wait_for_url(NEW + "**", timeout=15000); pg.wait_for_function(READY, timeout=15000); pg.wait_for_timeout(400)
        return ctx, pg, errs, dlg

    ls = lambda pg, k: pg.evaluate("localStorage.getItem(%s)" % json.dumps(k))
    toast = lambda pg: pg.evaluate(NOTICE_TEXT)   # v38: the handoff notices are the persistent #hoNotice, not the fading toast
    manual = lambda pg: (json.loads(ls(pg, "w3p.quests.v1") or "null") or {}).get("manual")

    # 1. a plain link, a page with a query and an anchor
    ctx, pg, errs, dlg = visit(OLD); check("handoff: the plain old address lands on /witcher-3/ with a blank build (the app writes it) and no import, no script errors, nothing in localStorage", pg.url.startswith(NEW) and "import" not in pg.url and pg.evaluate("location.hash").startswith("#v1.") and not errs and pg.evaluate("localStorage.length") == 0, (pg.url, errs)); ctx.close()
    ctx, pg, errs, dlg = visit(OLD + "x/y.html?x=1#controls", wait_new=False); pg.wait_for_url(NEW + "x/y.html**", timeout=15000)
    check("handoff: path, query and anchor are kept (x/y.html?x=1#controls)", pg.url == NEW + "x/y.html?x=1#controls", pg.url); ctx.close()
    # 2. a build link opens as the same build
    ctx, pg, errs, dlg = visit(OLD + "#" + LINK); st = pg.evaluate(FULL_STATE); h = pg.evaluate("location.hash")
    ctx2, pg2, _, _ = visit(NEW + "#" + LINK, wait_new=False); pg2.wait_for_function(READY, timeout=15000); pg2.wait_for_timeout(300)
    check("handoff: a build link keeps its hash and opens as the same build (%s...)" % LINK[:30], h == "#" + LINK and st == pg2.evaluate(FULL_STATE) and not errs, (h, errs)); ctx.close(); ctx2.close()
    # 3. quest data and preferences come over, the hash is cleaned, the build stays; the quests screen sees them
    seed = {"w3p.quests.v1": store({G1: "done", G2: "active"}, 1000), "w3p.quests.view": "band", "w3p.quests.banddone": "1", "w3p.quests.timescope": "hos"}
    ctx, pg, errs, dlg = visit(OLD + "#" + LINK, seed_old=seed)
    check("handoff: quest progress and the preferences arrive, the address is clean (no import=), the build hash is kept, a notice says so",
          manual(pg) == {G1: "done", G2: "active"} and ls(pg, "w3p.quests.view") == "band" and ls(pg, "w3p.quests.banddone") == "1" and ls(pg, "w3p.quests.timescope") == "hos" and ls(pg, "w3p.quests.timedone") is None
          and pg.evaluate("location.hash") == "#" + LINK and "import" not in pg.url and "quest progress was brought over" in toast(pg) and not errs, (manual(pg), pg.evaluate("location.hash")[:60], toast(pg), errs))
    pg.evaluate("qsStoreInit()"); check("handoff: the Quests screen reads the imported progress (QS.store)", pg.evaluate("QS.store.manual['%s']" % G1) == "done" and pg.evaluate("QS.view") == "band"); ctx.close()
    # 4. the stash: a flag only, never the data
    ctx, pg, errs, dlg = visit(OLD + "#" + LINK, seed_old={"w3planner.stash": json.dumps({"crafting": [{"id": "x", "qty": 3}]})})
    check("handoff: a stash on the old address shows 'Re-import your save to restore your stash.' and is NOT copied; the address is clean",
          "Re-import your save to restore your stash." in toast(pg) and ls(pg, "w3planner.stash") is None and pg.evaluate("location.hash") == "#" + LINK and not errs, (toast(pg), errs)); ctx.close()
    ctx, pg, errs, dlg = visit(OLD, seed_old={"w3planner.stash": "{}", "w3p.quests.v1": store({G1: "failed"}, 5)})
    check("handoff: quests and stash together, with no build in the hash: one notice with both, no import left in the address", manual(pg) == {G1: "failed"} and "restore your stash" in toast(pg) and "quest progress" in toast(pg) and "import" not in pg.url, (manual(pg), toast(pg))); ctx.close()

    # 5. on the new site: the newer data wins, preferences are never overwritten
    base = {G1: "active"}
    imp = lambda o: "#" + LINK + "&import=" + b64(o)
    ctx, pg, errs, dlg = visit(NEW + imp({"w3p.quests.v1": store({G1: "done", G2: "done"}, 1000), "w3p.quests.view": "band"}), seed_new={"w3p.quests.v1": store(base, 5000), "w3p.quests.view": "list"}, wait_new=False); pg.wait_for_function(READY, timeout=15000); pg.wait_for_timeout(300)
    check("handoff: existing data that is newer wins a conflict (G1 stays active), the other quest is added, an existing preference is kept", manual(pg) == {G1: "active", G2: "done"} and ls(pg, "w3p.quests.view") == "list", manual(pg)); ctx.close()
    ctx, pg, errs, dlg = visit(NEW + imp({"w3p.quests.v1": store({G1: "done"}, 9000)}), seed_new={"w3p.quests.v1": store({G1: "active", G2: "done"}, 100)}, wait_new=False); pg.wait_for_function(READY, timeout=15000); pg.wait_for_timeout(300)
    check("handoff: imported data that is newer wins a conflict, what only the old data holds is kept", manual(pg) == {G1: "done", G2: "done"} and json.loads(ls(pg, "w3p.quests.v1"))["changed"] == 9000, manual(pg)); ctx.close()
    # 6. hostile payloads
    def hostile(name, hash_, ok_ls, seed_new=None, keep_hash=False, notice=None):
        ctx, pg, errs, dlg = visit(NEW + hash_, seed_new=seed_new, wait_new=False); pg.wait_for_function(READY, timeout=15000); pg.wait_for_timeout(300)
        polluted = pg.evaluate("({}).polluted===undefined&&Object.prototype.polluted===undefined"); keys = sorted(pg.evaluate("Object.keys(localStorage)")); hs = pg.evaluate("location.hash")
        check("handoff, hostile: %s" % name, not errs and not dlg and polluted and ok_ls(pg, keys) and (keep_hash is None or ("import=" in hs) == keep_hash) and (notice is None or notice in toast(pg)), (errs, dlg, polluted, keys, hs[:50], toast(pg)[:80])); ctx.close()
    none = lambda pg, keys: keys == []
    hostile("text that is not base64url is left alone (the build decoder rejects the hash and the app writes a blank build; nothing is stored)", "#import=!!!<script>alert(1)</script>", none, keep_hash=None)
    hostile("base64url of text that is not JSON is dropped with a notice, nothing is stored", "#" + LINK + "&import=" + b64("not json {"), none, notice="could not be brought over")
    for label, payload in (("a JSON array", "[1,2]"), ("a JSON string", '"x"'), ("null", "null"), ("a number", "7")):
        hostile("%s is dropped with a notice, nothing is stored" % label, "#" + LINK + "&import=" + b64(payload), none, notice="could not be brought over")
    hostile("invalid UTF-8 bytes are dropped with a notice", "#" + LINK + "&import=" + base64.urlsafe_b64encode(b"\xff\xfe{}").decode().rstrip("="), none, notice="could not be brought over")
    evil = store({"<script>": "done", "x" * 32: "done", G1: "<img src=x onerror=alert(1)>", G2: "done"}, "1e9", {"at": "x", "file": "<b>f</b>" * 100, "q": {G1: "done", "bad": "done"}, "o": {}, "e": {}})
    hostile("__proto__, unknown keys, bad GUIDs and values, markup in a file name: only the five keys are written and only clean values survive",
            "#" + LINK + "&import=" + b64('{"__proto__":{"polluted":1},"evil":"x","w3p.quests.v1":%s,"w3p.quests.view":"<img src=x onerror=alert(1)>","w3p.quests.timedone":5}' % json.dumps(evil)),
            lambda pg, keys: keys == ["w3p.quests.v1"] and (lambda o: o["manual"] == {G2: "done"} and o["changed"] == 0 and o["save"]["q"] == {G1: "done"} and len(o["save"]["file"]) <= 120 and "<img" not in json.dumps(o))(json.loads(ls(pg, "w3p.quests.v1"))))
    hostile("a value that is not a string is ignored", "#" + LINK + "&import=" + b64({"w3p.quests.v1": {"v": 1, "manual": {G1: "done"}}, "w3p.quests.view": 3}), none)
    hostile("an oversized import (1,000,001 characters) is dropped with a notice, nothing is stored", "#" + LINK + "&import=" + "A" * 1000001, none, notice="could not be brought over")
    hostile("an unknown extra token is not ours: nothing is imported or stored (the build decoder rejects the hash)", "#" + LINK + "&import=" + b64({"w3p.quests.v1": store({G1: "done"}, 1)}) + "&foo=1", none, keep_hash=None)
    hostile("a second import= token: nothing is imported or stored", "#" + LINK + "&import=" + b64({"w3p.quests.view": "band"}) + "&import=" + b64({"w3p.quests.view": "list"}), none, keep_hash=None)
    hostile("data of a version this one cannot read (existing key with v:2) is never overwritten", "#" + LINK + "&import=" + b64({"w3p.quests.v1": store({G1: "done"}, 1)}),
            lambda pg, keys: ls(pg, "w3p.quests.v1") == '{"v":2,"future":true}', seed_new={"w3p.quests.v1": '{"v":2,"future":true}'})
    # 6b. too large to carry: a notice, never silence
    hostile("import=toolarge shows the 'too large' notice and stores nothing", "#" + LINK + "&import=toolarge", none, notice="too large to bring over")
    ctx, pg, errs, dlg = visit(OLD + "#" + LINK, seed_old={"w3p.quests.v1": "x" * 800000, "w3planner.stash": "{}"})
    check("handoff: a quest store too big for the address makes the old page send import=toolarge: the new site says so (and the stash flag still works), nothing is stored, no import left",
          "too large to bring over" in toast(pg) and "restore your stash" in toast(pg) and pg.evaluate("Object.keys(localStorage)") == [] and "import" not in pg.url and not errs, (toast(pg)[:120], errs)); ctx.close()
    # 7. the same hash on the OLD address with hostile storage does not break the redirect
    ctx, pg, errs, dlg = visit(OLD + "#" + LINK, seed_old={"w3p.quests.v1": "not json at all {{{", "w3p.quests.view": "<b>x</b>"})
    check("handoff: unreadable or hostile values on the old address still redirect; the new site rejects them without errors (nothing stored beyond what is valid)", not errs and not dlg and ls(pg, "w3p.quests.v1") is None and ls(pg, "w3p.quests.view") is None, (errs, dlg, toast(pg))); ctx.close()
    ns.shutdown(); os_.shutdown()


def redirect_targets(check, tmp):
    """the page built for production (default target) sends the visitor nowhere but https://buildplanner.net/witcher-3/: no other address in the page, its rules, or the argument of location.replace"""
    out = make_pages_redirect.build(Path(tmp) / "handoff-prod"); page = (out / "index.html").read_text(encoding="utf-8"); rules = (out / "_redirects").read_text(encoding="utf-8")
    urls = set(re.findall(r"https?://[A-Za-z0-9./_~%-]+", page)); rurls = {u for l in rules.splitlines() if l and not l.startswith("#") for u in l.split()[1:2]}
    check("redirect page (production target): the only address in index.html is %s (canonical, noscript refresh, link, script), and location.replace sends to it" % SITE_URL,
          urls == {SITE_URL} and make_pages_redirect.TARGET == SITE_URL and re.findall(r"location\.(?:replace|href\s*=|assign)\(?\s*([A-Za-z]+)", page) == ["T"], (urls, make_pages_redirect.TARGET))
    check("redirect page (production target): every _redirects rule points under %s" % SITE_URL, bool(rurls) and all(u.startswith(SITE_URL) for u in rurls), rurls)


def notice(b, site, tmp, check, label):
    """v38: the handoff notices (progress brought over, too large, stash) stay on screen until the user closes them: still visible after 10 s, a close button (x, keyboard focusable) closes them, so does Esc;
    role=status, aria-live=polite; above the Import save dialog; an ordinary toast still fades after its own time and does not hide them; the stash sentence's 'Re-import your save' opens the Import save dialog"""
    root = Path(tmp) / ("handoff-notice-" + label); new_root = root / "new"; shutil.copytree(site, new_root / "witcher-3")
    ns = serve.make_server(new_root, 0); threading.Thread(target=ns.serve_forever, daemon=True).start(); NEW = "http://127.0.0.1:%d/witcher-3/" % ns.server_address[1]
    old_dir = make_pages_redirect.build(root / "old", NEW); os_ = serve.make_server(old_dir, 0); threading.Thread(target=os_.serve_forever, daemon=True).start(); OLD = "http://127.0.0.1:%d/" % os_.server_address[1]
    L = " (%s)" % label

    def visit(url, seed):
        ctx = b.new_context(viewport={"width": 1440, "height": 950}); pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:120]))
        ctx.add_init_script("if(location.origin===%s){const s=%s;for(const k in s)localStorage.setItem(k,s[k])}" % (json.dumps(OLD.rstrip("/")), json.dumps(seed)))
        pg.goto(url); pg.wait_for_url(NEW + "**", timeout=15000); pg.wait_for_function(READY, timeout=15000); pg.wait_for_timeout(400)
        return ctx, pg, errs
    vis = lambda pg, i: pg.evaluate("(()=>{const e=document.getElementById(%s);return !!e&&!e.hidden&&getComputedStyle(e).display!=='none'})()" % json.dumps(i))
    text = lambda pg: pg.evaluate("document.getElementById('hoMsg').textContent")

    # three variants, opened together so one 10 s wait covers all of them
    seeds = {"progress brought over": ({"w3p.quests.v1": store({G1: "done"}, 1000)}, "quest progress was brought over from the old address."),
             "too large": ({"w3p.quests.v1": "x" * 800000}, "too large to bring over automatically"),
             "stash": ({"w3planner.stash": "{}"}, "Re-import your save to restore your stash.")}
    runs = {k: visit(OLD + "#" + LINK, s) for k, (s, _) in seeds.items()}
    for k, (ctx, pg, errs) in runs.items():
        n = pg.evaluate("(()=>{const n=document.getElementById('hoNotice');return{role:n.getAttribute('role'),live:n.getAttribute('aria-live'),x:document.getElementById('hoX').tagName,label:document.getElementById('hoX').getAttribute('aria-label')}})()")
        check("handoff notice (%s): shown with the current text, role=status, aria-live=polite, a close button with a label%s" % (k, L),
              vis(pg, "hoNotice") and seeds[k][1] in text(pg) and n == {"role": "status", "live": "polite", "x": "BUTTON", "label": "Close this notice"} and not errs, (text(pg)[:100], n, errs))
    # an ordinary toast and a rebuild next to the stash notice, then the wait
    ctx, pg, errs = runs["stash"]
    pg.evaluate("save()"); pg.evaluate("notify('An ordinary toast.')"); pg.wait_for_timeout(300)   # save() hides the toast by design, so it goes first
    box = lambda i: pg.evaluate("(()=>{const r=document.getElementById(%s).getBoundingClientRect();return[r.top,r.bottom]})()" % json.dumps(i))
    nb, tb = box("hoNotice"), box("toast")
    check("an ordinary toast shows next to the notice without covering it, and a build change (save()) does not hide the notice%s" % L, vis(pg, "toast") and vis(pg, "hoNotice") and tb[1] <= nb[0] + 1, (nb, tb))
    pg.wait_for_timeout(10000)
    for k, (ctx, pg2, errs) in runs.items():
        check("handoff notice (%s): still visible after 10 s%s" % (k, L), vis(pg2, "hoNotice"), text(pg2)[:80])
    check("the ordinary toast still fades by itself (6.5 s) while the notice stays%s" % L, not vis(pg, "toast") and vis(pg, "hoNotice"))
    # the stash sentence: text unchanged, 'Re-import your save' is a button that opens Import save, the notice is above that dialog
    a = pg.locator("#hoMsg button.holink")
    check("stash notice: 'Re-import your save' is a button and the sentence reads 'Re-import your save to restore your stash.'%s" % L, a.count() == 1 and a.inner_text() == "Re-import your save" and text(pg) == "Re-import your save to restore your stash.", text(pg))
    a.click(); pg.wait_for_timeout(300)
    top = pg.evaluate("(()=>{const r=document.getElementById('hoNotice').getBoundingClientRect(),e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return !!e&&document.getElementById('hoNotice').contains(e)})()")
    check("the Import save dialog opens from the notice, and the notice is drawn above the dialog%s" % L, vis(pg, "impov") and top and vis(pg, "hoNotice"), (vis(pg, "impov"), top))
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    check("Esc with the dialog open closes the dialog first and leaves the notice%s" % L, not vis(pg, "impov") and vis(pg, "hoNotice"))
    # close: keyboard focus, then click
    pg.focus("#hoX"); check("the close button can take keyboard focus%s" % L, pg.evaluate("document.activeElement.id") == "hoX")
    pg.click("#hoX"); pg.wait_for_timeout(200)
    check("clicking the close button hides the notice, and the space is given back to toasts%s" % L, not vis(pg, "hoNotice") and not pg.evaluate("document.body.classList.contains('ho-open')"))
    ctx2, pg2, e2 = runs["progress brought over"]; pg2.focus("#hoX"); pg2.keyboard.press("Enter"); pg2.wait_for_timeout(200)
    check("the close button works from the keyboard (Enter)%s" % L, not vis(pg2, "hoNotice"))
    ctx3, pg3, e3 = runs["too large"]; pg3.keyboard.press("Escape"); pg3.wait_for_timeout(200)
    check("Esc closes the notice%s" % L, not vis(pg3, "hoNotice"))
    for c, _, _ in runs.values(): c.close()
    # the next visit to the planner has no notice: it is not remembered anywhere
    ctx, pg, errs = visit(NEW + "#" + LINK, {}); check("a plain visit shows no notice%s" % L, not vis(pg, "hoNotice")); ctx.close()
    ns.shutdown(); os_.shutdown()
