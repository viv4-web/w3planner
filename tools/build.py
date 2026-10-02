#!/usr/bin/env python3
"""Build the site from source.

    python tools/build.py --variant placeholder --out dist/placeholder
    python tools/build.py --variant game --art-dir ../w3planner-art --out dist/game

Variants
  placeholder  the public build: original placeholder art from art/placeholder (no game art)
  game         the live-site build: the game's own art, read from --art-dir (the private art repo)

Images are copied to assets/ (game) or art/ (placeholder) under content-hash names, and the page refers to them
by those names. A source may also say /*@file:NAME*/: data/NAME.json is then written as a script data/NAME.<hash>.js
(it sets W3DATA.NAME), loaded on demand by a <script> tag (the page's CSP forbids fetch), and the marker becomes the file's URL.
Big data (the equipment lists) never goes into index.html. The output is a plain static folder that can be served or deployed as it is.
Standard library only.
"""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = ".built-by-w3planner"


def read(p):
    return Path(p).read_bytes().decode("utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["placeholder", "game"], required=True)
    ap.add_argument("--art-dir", help="folder with the art files (required for the game variant)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--src", default=str(ROOT / "src"), help="source folder (index.html, app.css, app.js); default src/")
    ap.add_argument("--glossary-dir", help="Glossary content (made by tools/build_glossary.py). The game variant reads <art-dir>/glossary by itself; the public build never has any "
                    "(it shows \"not included\"); this option exists for the tests, which build with a tiny fake one (tests/fixtures/glossary)")
    a = ap.parse_args()

    if a.variant == "game":
        if not a.art_dir:
            sys.exit("the game variant needs --art-dir (the private art repo)")
        art_dir = Path(a.art_dir)
    else:
        art_dir = ROOT / "art" / "placeholder"
    if not art_dir.is_dir():
        sys.exit("art folder not found: %s" % art_dir)
    folder = "assets" if a.variant == "game" else "art"

    out = Path(a.out)
    if out.exists():
        if not (out / MARK).exists() and any(out.iterdir()):
            sys.exit("refusing to overwrite %s: it was not created by this tool" % out)
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARK).write_text("generated; safe to delete\n")

    manifest = json.loads(read(ROOT / "art" / "manifest.json"))
    files = {}

    def img(match):
        sid = match.group(1)
        if sid not in manifest:
            sys.exit("unknown art id in the source: %s" % sid)
        # a slot may say "placeholder_as": the public build then shows that slot's placeholder (the equipment icons share one drawn placeholder per slot)
        if a.variant == "placeholder" and manifest[sid].get("placeholder_as"):
            sid = manifest[sid]["placeholder_as"]
        ext = manifest[sid][a.variant]
        src = art_dir / (sid + "." + ext)
        if not src.is_file():
            sys.exit("missing art file: %s" % src)
        data = src.read_bytes()
        name = "%s/%s.%s" % (folder, hashlib.sha1(data).hexdigest()[:12], ext)
        files[name] = data
        return name

    tokens = lambda t: re.sub(r"@@img:([a-z0-9_/\-]+)@@", img, t)

    def data(match):
        name = match.group(1)
        for ext in ("json", "js"):
            p = ROOT / "data" / ("%s.%s" % (name, ext))
            if p.is_file():
                return tokens(read(p))
        sys.exit("missing data file for %s" % name)

    def lazyjs(match):   # /*@lazyjs:NAME*/: src/NAME.js becomes its own hashed script (data/NAME.<hash>.js), loaded on demand; the marker becomes its URL
        name = match.group(1); p = Path(a.src) / ("%s.js" % name)
        if not p.is_file(): sys.exit("missing source file for @lazyjs:%s" % name)
        blob = p.read_bytes(); fname = "data/%s.%s.js" % (name, hashlib.sha1(blob).hexdigest()[:12]); files[fname] = blob
        return json.dumps(fname)

    def lazy(match):
        name = match.group(1); p = ROOT / "data" / ("%s.json" % name)
        if not p.is_file(): sys.exit("missing data file for @file:%s" % name)
        blob = ('(window.W3DATA=window.W3DATA||{}).%s=%s;\n' % (name, tokens(read(p)).strip())).encode("utf-8")
        fname = "data/%s.%s.js" % (name, hashlib.sha1(blob).hexdigest()[:12]); files[fname] = blob
        return json.dumps(fname)

    # Glossary (game text and pictures): game variant only, from <art-dir>/glossary, never committed. Each data file becomes glossary/<name>.<hash>.js (it sets
    # W3DATA.glossary_<name>), each picture glossary/img/<hash>.webp; the page only gets the small map of URLs (/*@glossary*/), loaded on demand like the equipment lists.
    gdir = Path(a.glossary_dir) if a.glossary_dir else (art_dir / "glossary" if a.variant == "game" else None)
    gloss = None
    if gdir and (gdir / "manifest.json").is_file():
        gm = json.loads(read(gdir / "manifest.json")); gfiles = {}
        def gimg(m):
            f = gdir / "img" / (m.group(1) + ".webp")
            if not f.is_file(): sys.exit("glossary picture missing: %s" % f)
            blob = f.read_bytes(); name = "glossary/img/%s.webp" % hashlib.sha1(blob).hexdigest()[:12]; files[name] = blob; return name
        for name in sorted(gm["files"]):
            if not name.endswith(".json"): continue
            key = name[:-5]; blob = ('(window.W3DATA=window.W3DATA||{}).glossary_%s=%s;\n' % (key, re.sub(r"@@gimg:([A-Za-z0-9_/\-]+)@@", gimg, read(gdir / name)).strip())).encode("utf-8")
            gfiles[key] = "glossary/%s.%s.js" % (key, hashlib.sha1(blob).hexdigest()[:12]); files[gfiles[key]] = blob
        gloss = {"files": gfiles, "counts": gm["counts"]}

    src = Path(a.src)
    extra = lambda *names: "".join(("\n" + read(src / n)) for n in names if (src / n).is_file())   # screens.css, equipment.js, consumables.js, screens.js: more source of the same page (one scope), in this order
    css = tokens(read(src / "app.css") + extra("screens.css", "glossary.css", "importsave.css"))
    js = re.sub(r"/\*@lazyjs:([a-z0-9_]+)\*/", lazyjs, re.sub(r"/\*@file:([a-z0-9_]+)\*/", lazy, tokens(re.sub(r"/\*@data:([A-Z_]+)\*/", data, read(src / "app.js") + extra("equipment.js", "consumables.js", "screens.js", "glossary.js", "importsave.js")))))
    if gloss: js = js.replace("/*@glossary*/null", json.dumps(gloss, separators=(",", ":")))
    html = tokens(read(src / "index.html")).replace("{{css}}", css).replace("{{js}}", js)
    (out / "index.html").write_bytes(html.encode("utf-8"))
    for name, blob in files.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(blob)
    shutil.copytree(ROOT / "static", out, dirs_exist_ok=True)
    print("Built %s variant into %s (%d files, index.html %d KB%s)" % (a.variant, out, len(files), len(html) // 1024, ", Glossary included" if gloss else ""))


if __name__ == "__main__":
    main()
