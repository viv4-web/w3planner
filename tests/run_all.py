#!/usr/bin/env python3
"""Run every check on a fresh build. Exit code 0 = everything passed.

    python tests/run_all.py                                        the public (placeholder) build
    python tests/run_all.py --variant game --art-dir ../w3planner-art
    python tests/run_all.py --quick                                fewer hostile-link cases (faster)

Setup once:  pip install -r requirements.txt  &&  python -m playwright install chromium
What it does: builds the site, serves it with the security headers from _headers, drives it with a real browser.
"""
import argparse, json, random, shutil, subprocess, sys, tempfile, threading, urllib.parse, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import serve
import linkcheck
import eqcheck
import glcheck
import importcheck
from playwright.sync_api import sync_playwright

RESULTS = []
ALL_TIPS = "(()=>{const o={};TREES.forEach((t,ti)=>t.sk.forEach((s,i)=>{for(let L=1;L<=3;L++)o[ti+'.'+i+'.'+L]=tipText(ti,i,L)}));return o})()"
FULLSTATE = "JSON.stringify([+document.getElementById('lvl').value,+document.getElementById('bonuspts').value,S.lv,S.slots,S.muts,S.mres,S.mact])"
INV = """(()=>{const bad=[];
 S.lv.forEach((row,ti)=>row.forEach((v,i)=>{if(!(Number.isInteger(v)&&v>=0&&v<=TREES[ti].sk[i].max))bad.push('skill level out of range')}));
 S.slots.forEach(x=>{if(x&&!(Number.isInteger(x[0])&&x[0]>=0&&x[0]<4&&Number.isInteger(x[1])&&x[1]>=0&&x[1]<20))bad.push('slot points at a skill that does not exist')});
 S.muts.forEach(m=>{if(m!==null&&!(Number.isInteger(m)&&m>=0&&m<MUTS.length))bad.push('mutagen that does not exist')});
 if(!(S.mact>=-1&&S.mact<12))bad.push('bad active mutation');
 if(!Array.isArray(S.gear)||S.gear.length!==9||!S.gear.every(v=>Number.isInteger(v)&&v>=0&&v<=4095)||!['ng','ng_plus'].includes(S.rs))bad.push('bad gear state');
 const b=+document.getElementById('bonuspts').value,l=+document.getElementById('lvl').value;
 if(!(b>=0&&b<=100))bad.push('bonus points out of range');if(!(l>=1&&l<=100))bad.push('level out of range');
 return [...new Set(bad)]})()"""
ROUNDTRIP = """(()=>{render=()=>{};history.replaceState=()=>{};let seed=20260930;const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};let bad=0,n=0,spec=0;
 for(let it=0;it<80;it++){S=blank();document.getElementById('lvl').value=1+Math.floor(rnd()*100);document.getElementById('bonuspts').value=Math.floor(rnd()*60);
  for(let st=0;st<45;st++){const ti=Math.floor(rnd()*4),i=Math.floor(rnd()*20),r=rnd();
   if(r<.5)add(ti,i);else if(r<.58)rem(ti,i);
   else if(r<.72){const k=Math.floor(rnd()*16);if(slotOpen(k)&&S.lv[ti][i]&&accepts(k,[ti,i])&&!S.slots.some(x=>x&&x[0]===ti&&x[1]===i))S.slots[k]=[ti,i]}
   else if(r<.84){const g=Math.floor(rnd()*4);if(sockOpen(g))S.muts[g]=Math.floor(rnd()*MUTS.length)}
   else if(r<.95){const m=Math.floor(rnd()*12);if(mCanResearch(m))S.mres[m]=1}
   else{const m=Math.floor(rnd()*12);if(S.mres[m])S.mact=m}}
  enforceLocks();if(S.muts.some(x=>x!==null&&x>=9))spec++;
  const before=JSON.stringify([+document.getElementById('lvl').value,+document.getElementById('bonuspts').value,S.lv,S.slots,S.muts,S.mres,S.mact]);
  const t=dec(enc());n++;const after=t?JSON.stringify([+document.getElementById('lvl').value,+document.getElementById('bonuspts').value,t.lv,t.slots,t.muts,t.mres,t.mact]):'REJECTED';
  if(before!==after)bad++}
 return {n,bad,spec}})()"""
A64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  (" + str(detail) + ")") if detail != "" else ""))


def random_code(r):
    ch = lambda n, alpha: "".join(r.choice(alpha) for _ in range(n))
    v = r.choice(["v1"] * 9 + ["v2", "x", ""])
    parts = [v, ch(r.choice([27] * 8 + [0, 5, 80]), A64 if r.random() < .95 else A64 + "%!*"), ch(r.choice([32] * 6 + [24, 0, 2, 64]), A64),
             ch(r.choice([4] * 8 + [0, 9]), "-0123456789xXabcz"), r.choice([str(r.randint(1, 100))] * 3 + ["0", "-5", "1e9", "abc", str(r.randint(101, 99999))]),
             r.choice([str(r.randint(0, 100))] * 3 + ["-7", "1e300", "zzz", str(r.randint(101, 99999))]), r.choice(["0", "zz", "1n", "", "x" * 50, "9" * 40]), r.choice(["0", "13", "99", "-3", "q", "7"])]
    return ".".join(parts[:r.choice([3, 4, 5, 8, 8, 8])])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["placeholder", "game"], default="placeholder"); ap.add_argument("--art-dir")
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--keep", action="store_true", help="keep the temporary build folder")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="w3test-")); site = tmp / "site"
    cmd = [sys.executable, str(ROOT / "tools" / "build.py"), "--variant", a.variant, "--out", str(site)] + (["--art-dir", a.art_dir] if a.art_dir else [])
    if subprocess.run(cmd).returncode: sys.exit("build failed")
    server = serve.make_server(site, 0); port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start(); base = "http://127.0.0.1:%d/" % port
    # the Glossary tests build the site once more, with the tiny FAKE glossary (tests/fixtures/glossary); the build under test (public or live) is checked on its own
    gsite = tmp / "gsite"
    if subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), "--variant", "placeholder", "--glossary-dir", str(ROOT / "tests/fixtures/glossary"), "--out", str(gsite)], stdout=subprocess.DEVNULL).returncode: sys.exit("fixture build failed")
    gserver = serve.make_server(gsite, 0); threading.Thread(target=gserver.serve_forever, daemon=True).start(); gbase = "http://127.0.0.1:%d/" % gserver.server_address[1]
    ref = json.loads((ROOT / "tests/fixtures/tooltips_ref.json").read_text())
    print("\n== Equipment data (data/items.json, items_ng.json, items_ng_plus.json) ==")
    items = json.loads((ROOT / "data/items.json").read_text(encoding="utf-8")); manifest = json.loads((ROOT / "art/manifest.json").read_text()); slots = {x["id"] for x in items["slots"]}
    per = {rs: json.loads((ROOT / ("data/items_%s.json" % rs)).read_text(encoding="utf-8"))["items"] for rs in items["rulesets"]}; recs = [r for v in per.values() for r in v]
    check("%d + %d items (ng, ng_plus); ids unique within each ruleset; default ruleset ng; every slot, set and name valid" % (len(per["ng"]), len(per["ng_plus"])),
          all(len({r["id"] for r in v}) == len(v) for v in per.values()) and items["default_ruleset"] == "ng" and all(r["slot"] in slots and (r.get("set") is None or r["set"] in items["sets"]) and r["name"] for r in recs)
          and all(p in {r["id"] for r in per[rs]} for s_ in items["sets"].values() for rs in per for p in s_[rs]["pieces"]))
    check("the items are not in the small file and not embedded: items.json %d KB, items_ng.json %d KB, items_ng_plus.json %d KB" % tuple(len((ROOT / "data" / n).read_bytes()) // 1024 for n in ("items.json", "items_ng.json", "items_ng_plus.json")),
          "items" not in items and (ROOT / "data/items.json").stat().st_size < 100_000)
    sb = [(s_, b) for s_, v in items["sets"].items() for b in v["bonuses"]]
    check("every set bonus has its thresholds, a filled text and a script and XML source (%d bonuses)" % len(sb), len(sb) == 13 and all(b["pieces"] in (3, 6) and "$S$" not in b["text"] and any(x.startswith("scripts/") for x in b["source"]) for _, b in sb), [s_ for s_, b in sb if "$S$" in b["text"]])
    lvl = lambda rs, i: next(r["required_level"] for r in per[rs] if r["id"] == i)
    reg = json.loads((ROOT / "data/item_ids.json").read_text(encoding="utf-8"))["ids"]
    check("every item has its registry number (data/item_ids.json: append-only, 1 to 4095)", all(reg.get(r["id"]) == r["n"] for r in recs) and len(set(reg.values())) == len(reg) and max(reg.values()) <= 4095)
    check("required levels follow the game's formula (a Grandmaster Feline armor needs level 40 in ng, 70 in ng_plus)", lvl("ng", "Lynx Armor 4") == 40 and lvl("ng_plus", "Lynx Armor 4") == 70)
    check("autogen relics have no level and say it varies", all(r.get("level_varies") and r.get("required_level") is None for r in recs if r.get("autogen")) and any(r.get("autogen") for r in recs))
    shown = [e for r in recs for e in r.get("base", []) + r.get("bonuses", []) if "line" in e]
    check("stat lines follow tooltip_settings.csv (%d rows; stats sorted by line, percent flags set)" % len(items["stat_display"]), len(items["stat_display"]) > 80 and shown and all(r.get("base", []) == sorted(r.get("base", []), key=lambda e: e.get("line", 9999)) for r in recs)
          and all(e["percent"] for e in shown if e.get("type") == "mult"))
    pending = {n.strip() for l in (ROOT / "tools" / "pending-icons.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#") for n in l.split("\t")[1].split(";")}   # items whose icon is not extracted yet
    nopic = sorted(r["id"] for r in recs if not r.get("icon"))
    check("every item has its icon, except the ones listed in tools/pending-icons.txt (%d pending), and no pending item has one" % len(pending), all(i in pending for i in nopic) and not [r["id"] for r in recs if r.get("icon") and r["id"] in pending], [i for i in nopic if i not in pending][:3])
    icon_ids = sorted({r["icon"][len("@@img:"):-2] for r in recs if r.get("icon")}); item_slots = sorted(k for k in manifest if k.startswith("items/") and "/ph-" not in k)
    check("every icon token has a manifest slot, and no manifest slot is unused", icon_ids == item_slots, sorted(set(icon_ids) ^ set(item_slots))[:3])
    check("every equipment icon shows the drawn placeholder of its slot in the public build", all(manifest[i].get("placeholder_as") == "items/ph-" + next(r["slot"] for r in recs if r.get("icon") == "@@img:%s@@" % i) and (ROOT / "art/placeholder" / (manifest[i]["placeholder_as"] + ".png")).is_file() for i in icon_ids))
    if a.variant == "game": check("the private art folder has every equipment icon", all((Path(a.art_dir) / (i + ".png")).is_file() for i in icon_ids), [i for i in icon_ids if not (Path(a.art_dir) / (i + ".png")).is_file()][:3])
    print("\n== Consumables data (data/consumables.json, consumable_ids.json) ==")
    cd = json.loads((ROOT / "data/consumables.json").read_text(encoding="utf-8")); citems = cd["items"]; creg = json.loads((ROOT / "data/consumable_ids.json").read_text(encoding="utf-8"))["ids"]
    check("%d consumables: ids unique, every one has its registry number (data/consumable_ids.json: append-only, 1 to 4095), categories potion, decoction, bomb, oil only" % len(citems),
          len({i["id"] for i in citems}) == len(citems) and all(creg.get(i["id"]) == i["n"] for i in citems) and len(set(creg.values())) == len(creg) and max(creg.values()) <= 4095 and {i["cat"] for i in citems} == {"potion", "decoction", "bomb", "oil"})
    check("oils say which sword they fit (SteelOil: 6 of 36, SilverOil: all), no oil, bomb or potion carries a level, every consumable has a name, an icon token and a manifest slot",
          sum(1 for i in citems if i["cat"] == "oil" and i.get("steel")) == 6 and all(i.get("silver") for i in citems if i["cat"] == "oil") and all(i["name"] and i["icon"] and i["icon"][len("@@img:"):-2] in manifest for i in citems))
    if a.variant == "game": check("the private art folder has every consumable icon and the four drawn placeholders", all((Path(a.art_dir) / (i["icon"][len("@@img:"):-2] + ".png")).is_file() for i in citems), [i["id"] for i in citems if not (Path(a.art_dir) / (i["icon"][len("@@img:"):-2] + ".png")).is_file()][:3])
    N = 60 if a.quick else 300
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        print("\n== The page (%s build, served with its security headers) ==" % a.variant)
        pg = b.new_page(viewport={"width": 1500, "height": 950}); errs, ext, fails = [], [], []
        pg.add_init_script("window.__v=[];document.addEventListener('securitypolicyviolation',e=>window.__v.push(e.violatedDirective+' '+e.blockedURI))")
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("requestfailed", lambda r: fails.append(r.url[-40:]))
        pg.on("request", lambda r: ext.append(r.url) if not r.url.startswith(("http://127.0.0.1:%d" % port, "data:")) else None)
        resp = pg.goto(base); pg.wait_for_timeout(900); E = pg.evaluate
        check("loads without script errors", not errs, errs[:1]); check("makes no requests to other sites", not ext, ext[:2]); check("no failed requests", not fails, fails[:2])
        check("no Content-Security-Policy violations", E("window.__v") == [], E("window.__v")); h = resp.headers
        check("security headers are sent", all(h.get(k) for k in ("content-security-policy", "x-content-type-options", "x-frame-options")))
        tips = E(ALL_TIPS); bad = [k for k in ref if ref[k] != tips.get(k)]
        check("all %d skill tooltips match the reference" % len(ref), not bad, bad[:3])
        print("\n== Behaviour ==")
        check("starts at level 1 with one open slot", E("lvl()") == 1 and E("[0,1,2,3,4,5,6,7,8,9,10,11].filter(slotOpen).length") == 1)
        pg.locator('#slots g.node[data-k="1"]').click(); pg.wait_for_timeout(100)
        check("clicking a locked slot explains what it needs", (not pg.locator("#toast").is_hidden()) and "unlocks at" in pg.inner_text("#toastMsg"))
        i = E("TREES[1].sk.findIndex(s=>!s.req.length)"); pg.locator('.tab[data-k="1"]').click(); node = lambda: pg.locator('#treePanel g.node[data-i="%d"]' % i)
        node().click(); node().click(); pg.wait_for_timeout(100)
        check("adding a point with none left explains why", "No skill points left" in pg.inner_text("#toastMsg") and E("S.lv[1][%d]" % i) == 0)
        E("document.getElementById('lvl').value=40;pointsChanged()"); pg.wait_for_timeout(100); node().click(); node().click(); pg.wait_for_timeout(100)
        check("a skill point can be added once there are points", E("S.lv[1][%d]" % i) >= 1)
        src = node().bounding_box(); dst = pg.locator('#slots g.node[data-k="0"]').bounding_box()
        pg.mouse.move(src["x"] + src["width"] / 2, src["y"] + src["height"] / 2); pg.mouse.down(); pg.mouse.move(dst["x"] + 20, dst["y"] + 20, steps=8)
        pg.mouse.move(dst["x"] + dst["width"] / 2, dst["y"] + dst["height"] / 2, steps=6); pg.mouse.up(); pg.wait_for_timeout(100)
        check("a skill can be dragged into a slot", E("JSON.stringify(S.slots[0])") == "[1,%d]" % i)
        pg.click("#mutbtn"); pg.wait_for_timeout(150); bb = pg.locator('#mweb .mn[data-i="3"]').bounding_box(); x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * .4
        pg.mouse.move(x, y); pg.wait_for_timeout(60); pg.mouse.click(x, y); pg.wait_for_timeout(100); check("a mutation can be researched by clicking it", E("S.mres[3]") == 1)
        pg.mouse.move(700, 120); pg.wait_for_timeout(50); pg.click("#mundo"); pg.wait_for_timeout(100); check("the Undo research button works", E("S.mres[3]") == 0)
        sp = E("MUTS.filter(m=>m.special)"); lesser = {"red": 0, "blue": 3, "green": 6}
        check("36 mutagens: 9 regular and 27 special (9 per colour)", E("MUTS.length") == 36 and len(sp) == 27 and all(E("MUTS.filter(m=>m.special&&m.c==='%s').length" % c) == 9 for c in lesser))
        check("every special mutagen has the bonus of the Lesser mutagen of its colour", E("MUTS.filter(m=>m.special).every(m=>{const l=MUTS[{red:0,blue:3,green:6}[m.c]];return m.v===l.v&&m.syn===l.syn&&m.stat===l.stat&&m.pct===l.pct})"))
        print("\n== Links ==")
        E("document.getElementById('lvl').value=40;document.getElementById('bonuspts').value=5;pointsChanged();S.muts[0]=MUTS.findIndex(m=>m.label==='Wraith');S.muts[1]=35;save()")
        code = E("document.getElementById('link').value.split('#')[1]"); link_state = E(FULLSTATE); q = b.new_page(); q.goto(base + "#" + code); q.wait_for_timeout(500)
        check("a link with special mutagens reopens identically", q.evaluate(FULLSTATE) == link_state); q.close()
        problems, note = linkcheck.append_only_problems(); check("link fixtures are append-only (%s)" % note, not problems, "; ".join(problems))
        linkcheck.check_fixtures(b, base, "online", check)
        print("\n== Equipment screen ==")
        eqcheck.run(b, base, check, "online", a.quick)
        print("\n== Top bar and Glossary ==")
        check("the public build has no glossary files, the live build has the real ones", ((site / "glossary").is_dir()) == (a.variant == "game") and (a.variant == "game" or not any("glossary" in p.name for p in site.rglob("*"))))
        glcheck.run(b, gbase, check, "online", main=base, real=a.variant == "game", quick=a.quick)
        print("\n== Import save ==")
        importcheck.run(b, base, check, "online")
        nd = shutil.which("node"); nr = subprocess.run([nd, str(ROOT / "tests/test_saveread.js")], capture_output=True, text=True) if nd else None
        check("the save reader without a browser: LZ4, header errors, sidecar, the mutagen table, the reference save when the local fixture is present", (nr is None) or nr.returncode == 0, (nr.stderr or nr.stdout).strip()[-300:] if nr else "node not found: skipped")
        rt = b.new_page(); rt.goto(base); rt.wait_for_timeout(600); r = rt.evaluate(ROUNDTRIP); rt.close(); check("%d random builds survive a link round trip unchanged (%d with special mutagens)" % (r["n"], r["spec"]), r["bad"] == 0, r["bad"])
        h2 = b.new_page(viewport={"width": 1300, "height": 900}); herrs = []; h2.on("pageerror", lambda e: herrs.append(str(e).split("\n")[0][:80])); h2.goto(base); h2.wait_for_timeout(700)
        h2.evaluate("document.getElementById('bonuspts').value=20;pointsChanged();const i=TREES[1].sk.findIndex(s=>!s.req.length);add(1,i);add(1,i);S.slots[0]=[1,i];S.muts[0]=3;save();openMut()")
        valid = h2.evaluate("document.getElementById('link').value.split('#')[1]"); p = valid.split("."); rep = lambda k, v: ".".join(p[:k] + [v] + p[k + 1:])
        gear = ".g1A" + "A" * 18; bad_gear = [valid + x for x in (".g1", ".g1A", ".g1AAA", ".g1C" + "A" * 18, ".g1A" + "A" * 17, ".g1A" + "A" * 19, ".g1A" + "!" * 18, ".x" + "A" * 19, ".g2A" + "A" * 18, gear + gear, ".g1B" + "-" * 18, ".G1A" + "A" * 18)]
        ok_gear = [valid + gear, valid + ".g1B" + "_" * 18]
        crafted = bad_gear + ok_gear + [rep(2, "//" * 16), rep(3, "xxxx"), rep(3, "9999"), rep(1, "%" * 27), rep(4, "1e9"), "v1.!!!.???", "v1." + "A" * 100000] + [random_code(random.Random(k)) for k in range(N)]
        problems = []
        for c in crafted:
            herrs.clear(); h2.evaluate("h=>{location.hash=h}", c); h2.wait_for_timeout(20); inv = h2.evaluate(INV)
            if herrs or inv: problems.append((c[:30], herrs[:1], inv))
        h2.evaluate("h=>{location.hash=h}", valid); h2.wait_for_timeout(50)
        check("%d hostile or malformed links: no crash, no impossible build" % len(crafted), not problems, problems[:1]); check("the page still works afterwards", h2.evaluate("document.getElementById('slots').children.length>0"))
        print("\n== Pages and layout ==")
        for name in ("help.html", "about.html", "privacy.html", "support.html"):
            rr = pg.request.get(base + name); check("%s is served" % name, rr.status == 200 and "<title>" in rr.text())
        cc = lambda path: pg.request.get(base + path).headers.get("cache-control", "")
        check("HTML is served with Cache-Control: no-cache (/, index.html, help.html)", all("no-cache" in cc(x) for x in ("", "index.html", "help.html")), [cc(x) for x in ("", "index.html", "help.html")])
        font = next(f for f in sorted((ROOT / "static/fonts").rglob("*")) if f.is_file()).relative_to(ROOT / "static"); img0 = E("MUTIMG[0]")
        check("fonts and hashed images stay cached for a year", "immutable" in cc(str(font)) and (a.variant != "game" or "immutable" in cc(img0)), [cc(str(font)), cc(img0)])
        m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True); m.goto(base); m.wait_for_timeout(500)
        check("no sideways scrolling on a phone", m.evaluate("document.documentElement.scrollWidth-innerWidth") <= 0)
        print("\n== Release gate logic (tools/deploy.py, with a fake Cloudflare) ==")
        gt = subprocess.run([sys.executable, str(ROOT / "tests/test_deploy_gate.py")], capture_output=True, text=True)
        check("preview never touches production; promote and automatic rollback behave", gt.returncode == 0, "" if gt.returncode == 0 else gt.stderr.strip()[-300:])
        for label, script in (("the PC extract tool and its importer (fake game folder, read-only, stdlib only)", "test_pc_tools.py"), ("big data is a separate hashed script file, never embedded in index.html", "test_build_lazy.py"), ("the Glossary tool: tutorial platform folding, duplicate-name notes, book bodies, placeholder pictures", "test_glossary_tool.py")):
            ru = subprocess.run([sys.executable, str(ROOT / "tests" / script)], capture_output=True, text=True); check(label, ru.returncode == 0, "" if ru.returncode == 0 else ru.stderr.strip()[-300:])
        bt = subprocess.run([sys.executable, str(ROOT / "tests/test_bundle.py")], capture_output=True, text=True)
        check("the W3 bundle reader: format, zlib, snappy, lz4 (hand-made data)", bt.returncode == 0, "" if bt.returncode == 0 else bt.stderr.strip()[-300:])
        sw = subprocess.run([sys.executable, str(ROOT / "tests/test_smoke_wait.py")], capture_output=True, text=True)
        check("the smoke test waits for a new deployment on the plain URL, never a cache-busted one", sw.returncode == 0, "" if sw.returncode == 0 else sw.stderr.strip()[-300:])
        if a.variant == "placeholder":
            print("\n== Offline package ==")
            rel = tmp / "release"; res = subprocess.run([sys.executable, str(ROOT / "tools/make_offline.py"), "--site", str(site), "--out", str(rel)], capture_output=True, text=True)
            check("the offline package builds", res.returncode == 0, res.stderr.strip()[-120:])
            if res.returncode == 0:
                zp = next(rel.glob("BuildPlanner-offline-*.zip")); ex_dir = tmp / "Build Planner (offline test)"; zipfile.ZipFile(zp).extractall(ex_dir)
                off = "file://" + urllib.parse.quote(str(next(ex_dir.iterdir()))) + "/index.html"; o = b.new_page(viewport={"width": 1500, "height": 950}); oerr, onet = [], []
                o.on("pageerror", lambda e: oerr.append(str(e))); o.on("request", lambda r: onet.append(r.url) if r.url.startswith("http") else None); o.goto(off); o.wait_for_timeout(900); OE = o.evaluate
                check("opens from a folder with spaces in its name, no errors", not oerr, oerr[:1]); check("makes no network requests", not onet, onet[:2])
                vis = lambda s: OE("(()=>{const e=document.querySelector('%s');return !!e&&e.offsetParent!==null})()" % s)
                check("offline copy cannot create links, only open them", (not vis("#copy")) and vis("#imp"))
                otips = OE(ALL_TIPS); check("offline tooltips match the reference", all(ref[k] == otips.get(k) for k in ref))
                linkcheck.check_fixtures(b, off, "offline", check)
                eqcheck.run(b, off, check, "offline", a.quick)
                glcheck.publicbuild(b, off, None, glcheck.GLINK, check, "offline")
                importcheck.offline(b, off, check, "offline")
                check("the offline package contains no glossary", not any("glossary" in n.lower() for n in zipfile.ZipFile(zp).namelist()))
                o.fill("#imp", "https://w3planner.pages.dev/#" + code); o.click("#impbtn"); o.wait_for_timeout(300)
                check("a link from the website opens in the offline copy", OE(FULLSTATE) == link_state)
                o.fill("#imp", "https://example.com/"); o.click("#impbtn"); check("a link with no build in it is refused and does not navigate", o.url.startswith("file://") and "does not look" in o.inner_text("#impmsg"))
        else:
            print("\n(offline package checks skipped: the offline package never contains game art)")
        b.close()
    server.shutdown(); gserver.shutdown()
    if not a.keep: shutil.rmtree(tmp, ignore_errors=True)
    failed = [r for r in RESULTS if not r[1]]
    print("\n%d checks: %d passed, %d failed" % (len(RESULTS), len(RESULTS) - len(failed), len(failed)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
