#!/usr/bin/env python3
"""v35.1: the deploy guard (tools/art_guard.py, run by tools/deploy.py). Each required input is removed (or emptied) in a TEMPORARY COPY of the art folder and the guard must fail,
both the function and the real `deploy.py --dry-run` (which must stop before building anything). The real art folder is only read. Skips the copy parts when it is absent."""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import art_guard as G

ART = Path.home() / "work" / "w3planner-art"
FAIL = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  (" + str(detail)[:160] + ")") if detail != "" else ""))
    if not ok: FAIL.append(name)


def fresh(tmp, name):
    d = tmp / name
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(ART, d, ignore=shutil.ignore_patterns("quest-spike", "save-spike", ".git")); return d


def used_slots():
    out = set()
    for sub in ("src", "data", "static"):
        for p in (ROOT / sub).rglob("*"):
            if p.is_file() and p.suffix in (".js", ".css", ".html", ".json"): out.update(re.findall(r"@@img:([a-z0-9_/\-]+)@@", p.read_text(encoding="utf-8", errors="replace")))
    return sorted(out)


def damage(art, what):
    g, q = art / "glossary", art / "quests"; man = json.loads((ROOT / "art" / "manifest.json").read_text(encoding="utf-8")); sid = used_slots()[0]; slot = art / ("%s.%s" % (sid, man[sid]["game"]))
    gfile = sorted(p for p in g.glob("*.json") if p.name != "manifest.json")[0]
    def empty(p): p.unlink(); p.write_bytes(b"")
    {"glossary/ removed": lambda: shutil.rmtree(g), "glossary/manifest.json removed": lambda: (g / "manifest.json").unlink(), "glossary/manifest.json empty": lambda: empty(g / "manifest.json"),
     "a glossary data file removed": lambda: gfile.unlink(), "a glossary data file empty": lambda: empty(gfile), "glossary/img/ removed": lambda: shutil.rmtree(g / "img"),
     "quests/ removed": lambda: shutil.rmtree(q), "quests/desc.json removed": lambda: (q / "desc.json").unlink(), "quests/desc.json empty": lambda: empty(q / "desc.json"),
     "quests/manifest.json removed": lambda: (q / "manifest.json").unlink(), "an art slot removed": lambda: slot.unlink(), "an art slot empty": lambda: empty(slot)}[what]()


CASES = ["glossary/ removed", "glossary/manifest.json removed", "glossary/manifest.json empty", "a glossary data file removed", "a glossary data file empty", "glossary/img/ removed",
         "quests/ removed", "quests/desc.json removed", "quests/desc.json empty", "quests/manifest.json removed", "an art slot removed", "an art slot empty"]
if ART.is_dir():
    tmp = Path(tempfile.mkdtemp(prefix="w3guard-")); ok = fresh(tmp, "ok")
    check("the guard passes on an untouched copy of the art folder (%d art slots used)" % len(used_slots()), G.check_inputs(ok, ROOT) == [], G.check_inputs(ok, ROOT)[:2])
    for c in CASES:
        d = fresh(tmp, "bad"); damage(d, c); bad = G.check_inputs(d, ROOT)
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "deploy.py"), "--art-dir", str(d), "--dry-run"], capture_output=True, text=True)
        check("input check fails with %s" % c, bool(bad), bad[:1])
        check("deploy.py --dry-run stops at the guard with %s (exit %d, nothing built)" % (c, p.returncode), p.returncode != 0 and "DEPLOY GUARD" in p.stderr + p.stdout and "Built game variant" not in p.stdout, (p.stderr + p.stdout)[-160:])
    check("the real art folder is untouched (still passes)", G.check_inputs(ART, ROOT) == [])
    shutil.rmtree(tmp)
else: print("  SKIP  the art-folder copies (no art folder here)")
# the built output and the size comparison: a small fake dist and a fake production
tmp = Path(tempfile.mkdtemp(prefix="w3guard-dist-")); art = tmp / "art"; (art / "glossary").mkdir(parents=True)
(art / "glossary" / "manifest.json").write_text(json.dumps({"files": ["bestiary.json", "tutorial.json"], "counts": {}})); (art / "glossary" / "bestiary.json").write_text("{}")
def mk(name, html='<script>const a={"glossary":1},b={"quests":1}</script>'):
    d = tmp / name
    for n, size in (("glossary/bestiary.aaaaaaaaaaaa.js", 1000), ("glossary/tutorial.bbbbbbbbbbbb.js", 500), ("glossary/img/x.webp", 10), ("quests/desc.cccccccccccc.js", 2000), ("assets/a.png", 5)):
        p = d / n; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x" * size)
    (d / "index.html").write_text(html); return d
d = mk("good"); check("the built output check passes on a complete dist", G.check_dist(d, art) == [], G.check_dist(d, art))
for what, rm in (("glossary data file", "glossary/tutorial.bbbbbbbbbbbb.js"), ("glossary pictures", "glossary/img/x.webp"), ("quest text", "quests/desc.cccccccccccc.js"), ("assets", "assets/a.png")):
    d = mk("d-" + what.replace(" ", "")); (d / rm).unlink()
    if what == "assets": shutil.rmtree(d / "assets")
    check("the built output check fails without the %s" % what, bool(G.check_dist(d, art)), G.check_dist(d, art)[:1])
d = mk("nomap", "<script>x=/*@glossary*/null;y=/*@quests*/null</script>"); check("the built output check fails when index.html carries no Glossary / Quests map", len(G.check_dist(d, art)) >= 2, G.check_dist(d, art))
live = {"glossary/bestiary": 1000, "glossary/tutorial": 500, "quests/desc": 2000}
page = '"glossary/bestiary.aaaaaaaaaaaa.js" "glossary/tutorial.bbbbbbbbbbbb.js" "quests/desc.cccccccccccc.js"'
def fetch(url):
    if url.rstrip("/").count("/") <= 2 or "cb=" in url: return page.encode()
    return b"y" * live[("quests/desc" if "quests" in url else "glossary/" + re.search(r"glossary/([a-z_]+)\.", url).group(1))]
bad, rep = G.check_sizes(mk("sz"), "https://prod.example/", fetch); check("sizes equal to production's pass (%s)" % rep[0].split("  ")[0].strip(), bad == [] and len(rep) == 3, [bad, rep])
d = mk("small"); (d / "quests/desc.cccccccccccc.js").write_bytes(b"x" * 1599); bad, rep = G.check_sizes(d, "https://prod.example/", fetch)
check("a data file at 79.95%% of production's size fails, with the sizes in the report (%s)" % (bad[:1]), len(bad) == 1 and "1599" in bad[0] and "2000" in bad[0], bad)
d = mk("edge"); (d / "quests/desc.cccccccccccc.js").write_bytes(b"x" * 1600); check("exactly 80% passes", G.check_sizes(d, "https://prod.example/", fetch)[0] == [])
d = mk("gone"); (d / "glossary/tutorial.bbbbbbbbbbbb.js").unlink(); check("a file production has and the build lacks fails", len(G.check_sizes(d, "https://prod.example/", fetch)[0]) == 1)
def boom(url): raise OSError("no network")
check("an unreadable production fails hard (not silently skipped)", len(G.check_sizes(mk("net"), "https://prod.example/", boom)[0]) == 1)
check("a production page with no data to compare fails hard", len(G.check_sizes(mk("nodata"), "https://prod.example/", lambda u: b"<html></html>")[0]) == 1)
shutil.rmtree(tmp); print("\n%d failed" % len(FAIL) if FAIL else "\nall passed"); sys.exit(1 if FAIL else 0)
