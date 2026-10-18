"""Deploy guard (v35.1): the live build must never silently lose its game content.

tools/build.py skips the Glossary and the Quests journal text when their folder is missing (the public build has none), so a live build made from an art folder
without them would look fine, pass most checks and ship without them. This module is what tools/deploy.py runs around the build:

  check_inputs(art_dir)         BEFORE the build: every art input the live build reads exists and is not empty
                                  - every art slot the sources and data use (<art-dir>/<slot>.<game extension>, from art/manifest.json)
                                  - glossary/manifest.json, every data file it lists, and glossary/img/ with pictures in it
                                  - quests/manifest.json and quests/desc.json (valid JSON, not empty)
  check_dist(dist, art_dir)     AFTER the build: dist/game has the outputs: glossary/<name>.<hash>.js for every glossary data file and glossary/img/*.webp, quests/desc.<hash>.js,
                                  assets/ files, and index.html carries the Glossary and Quests maps (not the `null` the public build has)
  check_sizes(dist, live_url)   the data files are not much smaller than the ones production serves now: under 80 % of the live size is a failure (the sizes are reported)

Each returns a list of problems; `guard()` in tools/deploy.py exits with all of them. Tested in tests/test_art_guard.py."""
import json, re, urllib.request
from pathlib import Path

MIN_RATIO = 0.8


def _size(p):
    p = Path(p)
    return p.stat().st_size if p.is_file() else None


def _json(p):
    try: return json.loads(Path(p).read_text(encoding="utf-8")), None
    except Exception as e: return None, "%s: not valid JSON (%s)" % (p, str(e)[:60])


def check_inputs(art_dir, root):
    art = Path(art_dir); bad = []
    if not art.is_dir(): return ["art folder not found: %s" % art]
    manifest = json.loads((Path(root) / "art" / "manifest.json").read_text(encoding="utf-8"))
    used = set()   # the slots the live build reads: the @@img:...@@ tokens of the sources and the data files (the placeholder-only slots, items/ph-*, are never read from the art folder)
    for sub in ("src", "data", "static"):
        for p in (Path(root) / sub).rglob("*"):
            if p.is_file() and p.suffix in (".js", ".css", ".html", ".json"): used.update(re.findall(r"@@img:([a-z0-9_/\-]+)@@", p.read_text(encoding="utf-8", errors="replace")))
    if not used: bad.append("no art slot found in the sources (the guard cannot tell what the build reads)")
    for sid in sorted(used):
        if sid not in manifest: bad.append("art slot %s is used in the source but not in art/manifest.json" % sid); continue
        f = art / ("%s.%s" % (sid, manifest[sid]["game"])); s = _size(f)
        if not s: bad.append("art slot %s: %s" % (sid, "missing" if s is None else "empty") + " (%s)" % f)
    g = art / "glossary"
    if not g.is_dir(): bad.append("glossary/ is missing in the art folder (%s): the live build would ship without the Glossary" % g)
    else:
        gm = None
        if not _size(g / "manifest.json"): bad.append("glossary/manifest.json is %s" % ("missing" if _size(g / "manifest.json") is None else "empty"))
        else:
            gm, err = _json(g / "manifest.json")
            if err: bad.append(err)
        for name in sorted((gm or {}).get("files", [])):
            if not _size(g / name): bad.append("glossary/%s is %s" % (name, "missing" if _size(g / name) is None else "empty"))
        imgs = [p for p in (g / "img").rglob("*.webp") if p.stat().st_size] if (g / "img").is_dir() else []
        if not imgs: bad.append("glossary/img/ has no pictures")
    q = art / "quests"
    if not q.is_dir(): bad.append("quests/ is missing in the art folder (%s): the live build would ship without the journal and objective text" % q)
    else:
        for n in ("manifest.json", "desc.json"):
            s = _size(q / n)
            if not s: bad.append("quests/%s is %s" % (n, "missing" if s is None else "empty"))
            else:
                _, err = _json(q / n)
                if err: bad.append(err)
    return bad


def check_dist(dist, art_dir):
    d = Path(dist); bad = []
    html = (d / "index.html").read_text(encoding="utf-8") if (d / "index.html").is_file() else ""
    if not html: return ["%s/index.html is missing" % d]
    if "/*@glossary*/null" in html: bad.append("index.html has no Glossary map (the build skipped the Glossary)")
    if "/*@quests*/null" in html: bad.append("index.html has no Quests text map (the build skipped the journal and objective text)")
    gm = Path(art_dir) / "glossary" / "manifest.json"
    names = [n[:-5] for n in json.loads(gm.read_text(encoding="utf-8")).get("files", []) if n.endswith(".json")] if gm.is_file() else []
    for n in names:
        if not [p for p in (d / "glossary").glob(n + ".*.js") if p.stat().st_size]: bad.append("dist has no glossary/%s.<hash>.js" % n)
    if not names: bad.append("no glossary data files to look for")
    if not [p for p in (d / "glossary" / "img").glob("*.webp")] if (d / "glossary" / "img").is_dir() else True: bad.append("dist has no glossary/img pictures")
    if not [p for p in (d / "quests").glob("desc.*.js") if p.stat().st_size]: bad.append("dist has no quests/desc.<hash>.js")
    if not (d / "assets").is_dir() or not any((d / "assets").iterdir()): bad.append("dist has no assets/ (the game art)")
    return bad


def _fetch(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "Accept-Encoding": "identity", "User-Agent": "w3planner-deploy"})
    with urllib.request.urlopen(req, timeout=30) as r: return r.read()


def live_sizes(live_url, fetch=_fetch):
    """{'glossary/<name>': bytes, 'quests/desc': bytes} of the data files the live page points to"""
    html = fetch(live_url + ("&" if "?" in live_url else "?") + "cb=1").decode("utf-8", "replace"); out = {}
    for m in re.finditer(r'"((?:glossary/([a-z_]+)|quests/(desc))\.[0-9a-f]{12}\.js)"', html):
        out["glossary/" + m.group(2) if m.group(2) else "quests/desc"] = len(fetch(live_url.rstrip("/") + "/" + m.group(1)))
    return out


def local_sizes(dist):
    out = {}
    for p in (Path(dist) / "glossary").glob("*.js"): out["glossary/" + p.name.rsplit(".", 2)[0]] = p.stat().st_size
    for p in (Path(dist) / "quests").glob("desc.*.js"): out["quests/desc"] = p.stat().st_size
    return out


def check_sizes(dist, live_url, fetch=_fetch):
    """-> (problems, report lines). A data file under MIN_RATIO of the live one is a problem; a file production has and the build lacks too."""
    try: live = live_sizes(live_url, fetch)
    except Exception as e: return ["could not read the production sizes from %s (%s); fix that or pass --no-size-compare" % (live_url, str(e)[:80])], []
    mine = local_sizes(dist); bad = []; rep = []
    if not live: return ["production %s shows no Glossary or Quests data to compare with; pass --no-size-compare if that is expected" % live_url], []
    for k in sorted(live):
        a, b = mine.get(k), live[k]
        rep.append("%-26s build %s  production %d bytes%s" % (k, "missing" if a is None else "%d bytes" % a, b, "" if a is None else "  (%d%%)" % round(100 * a / b)))
        if a is None: bad.append("%s is in production (%d bytes) but not in this build" % (k, b))
        elif a < MIN_RATIO * b: bad.append("%s is %d bytes, under %d%% of production's %d bytes" % (k, a, round(100 * MIN_RATIO), b))
    return bad, rep
