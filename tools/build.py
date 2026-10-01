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

    def lazy(match):
        name = match.group(1); p = ROOT / "data" / ("%s.json" % name)
        if not p.is_file(): sys.exit("missing data file for @file:%s" % name)
        blob = ('(window.W3DATA=window.W3DATA||{}).%s=%s;\n' % (name, tokens(read(p)).strip())).encode("utf-8")
        fname = "data/%s.%s.js" % (name, hashlib.sha1(blob).hexdigest()[:12]); files[fname] = blob
        return json.dumps(fname)

    src = Path(a.src)
    css = tokens(read(src / "app.css"))
    js = re.sub(r"/\*@file:([a-z0-9_]+)\*/", lazy, tokens(re.sub(r"/\*@data:([A-Z_]+)\*/", data, read(src / "app.js"))))
    html = tokens(read(src / "index.html")).replace("{{css}}", css).replace("{{js}}", js)
    (out / "index.html").write_bytes(html.encode("utf-8"))
    for name, blob in files.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(blob)
    shutil.copytree(ROOT / "static", out, dirs_exist_ok=True)
    print("Built %s variant into %s (%d images, index.html %d KB)" % (a.variant, out, len(files), len(html) // 1024))


if __name__ == "__main__":
    main()
