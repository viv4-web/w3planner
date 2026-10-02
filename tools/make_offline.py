#!/usr/bin/env python3
"""Build the offline (standalone) package from the same files that make up the website.

    python tools/make_offline.py                      run from a checkout of the repository
    python tools/make_offline.py --site DIR --out DIR

The package contains the website's index.html UNCHANGED. What differs offline:
  * config.js           mode "offline" instead of "online", plus the address of the website
  * privacy.html        the hosting paragraph
  * README-OFFLINE.txt  instructions
The tool refuses to package the game's own artwork (folder "assets/") unless --allow-game-art is given.
Standard library only.
"""
import argparse, hashlib, re, sys, zipfile
from pathlib import Path

ONLINE_URL = "https://w3planner.pages.dev/"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)  # fixed timestamps, so the same input gives the same file contents
PAGES = ["index.html", "help.html", "about.html", "privacy.html", "support.html", "pages.css"]
IMG_REF = re.compile(r"\b((?:art|assets)/[0-9a-f]{12}\.(?:png|jpg))")

OFFLINE_HOSTING = ("<h2>Hosting</h2><p>This is the offline copy. It runs entirely on your computer and makes no network "
                   "requests. Links you open from it, such as the website or GitHub, open in your browser and are covered "
                   "by those sites' own privacy policies.</p>")

SHARING_OPEN_ONLY = """LINKS
This offline copy can OPEN build links but does not create them.
To open a link someone sent you, paste it into the "Open a shared link" box.
To share a build with someone, use the website: {url}
"""

SHARING_FULL = """SHARING BUILDS
"Copy link" gives you a link that works on the website: {url}
To open a link that someone sent you, paste it into the "Open a shared link" box under the build link.
"""

README_TEXT = """Build Planner (offline) {version}
=================================
An unofficial, fan-made skill tree, mutation and build planner. Free.
Not affiliated with or endorsed by CD PROJEKT RED.

HOW TO USE (Windows PC; also works on Mac and Linux with any modern browser)
1. Extract the whole zip first (right-click, Extract All). Do not open files from inside the zip.
2. Open the extracted folder and double-click index.html.
   It opens in your web browser (Chrome, Edge or Firefox).
3. Bookmark that page if you like. Everything runs on your computer and nothing is sent anywhere.

{sharing}
SAFETY
This is a plain web page, not a program: there is no installer. Only download it from
https://github.com/viv4-web/w3planner/releases and compare the checksum of your download with
SHA256SUMS.txt on that page. Copies from anywhere else cannot be trusted, because anyone can change and
re-share the files. Links you open are read only as numbers and are checked; anything unusual is rejected.

UPDATING
New versions are published at https://github.com/viv4-web/w3planner/releases
Download the new zip and replace this folder. The version number is shown at the bottom of the page.

GOOD TO KNOW
- This offline copy uses simple placeholder artwork instead of the game's art, so it looks different from the website.
- Skill names, descriptions and numbers are the game's own data.
- Bugs and ideas: https://github.com/viv4-web/w3planner/issues
"""


DATA_REF = re.compile(r"data/[a-z0-9_]+\.[0-9a-f]{12}\.js")


def normalise(text):
    """Ignore which image files a page uses, and any spacing next to an image reference (used by --compare)."""
    text = DATA_REF.sub("data/DATA.js", text)      # on-demand data files: their names carry a hash of content that names image files
    text = IMG_REF.sub("IMG", text)
    text = re.sub(r'\s*("IMG")\s*', r'\1', text)
    return re.sub(r'("IMG"),\s+', r'\1,', text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default=str(Path(__file__).resolve().parent.parent / "dist" / "placeholder"), help="built site folder containing index.html (default: dist/placeholder; build it first with tools/build.py)")
    ap.add_argument("--out", default="dist/release", help="output folder (default: dist/release)")
    ap.add_argument("--online-url", default=ONLINE_URL, help="address of the website, used for share links")
    ap.add_argument("--allow-game-art", action="store_true", help="allow packaging the game's own artwork (assets/)")
    ap.add_argument("--allow-share", action="store_true", help="let the offline copy create share links (default: it can only open links)")
    ap.add_argument("--compare", metavar="INDEX_HTML", help="check another index.html (for example the live site's) runs the same code, ignoring image files")
    a = ap.parse_args()

    site = Path(a.site)
    idx_bytes = (site / "index.html").read_bytes()
    idx = idx_bytes.decode("utf-8")
    m = re.search(r'const APP_VERSION="([^"]+)"', idx)
    if not m:
        sys.exit("index.html has no APP_VERSION")
    version = m.group(1)

    refs = set(IMG_REF.findall(idx))
    folders = {r.split("/")[0] for r in refs}
    if "assets" in folders and not a.allow_game_art:
        sys.exit("index.html uses the game's own artwork (assets/). The offline package ships placeholder art only. Use --allow-game-art to override.")
    if not folders:
        sys.exit("index.html refers to no image files; is this the right folder?")
    img_dir = sorted(folders)[0]

    missing = sorted(r for r in refs if not (site / r).is_file())
    if missing:
        sys.exit("index.html refers to files that are missing: " + ", ".join(missing[:5]))
    for f in PAGES:
        if not (site / f).is_file():
            sys.exit("missing file: " + f)
    fonts = sorted(p for p in (site / "fonts").glob("*") if p.is_file())
    images = sorted(p for p in (site / img_dir).glob("*") if p.is_file())
    if not fonts:
        sys.exit("missing fonts/")

    privacy = (site / "privacy.html").read_text(encoding="utf-8")
    privacy, n = re.subn(r"<h2>Hosting</h2><p>.*?</p>", lambda _m: OFFLINE_HOSTING, privacy, count=1, flags=re.S)
    if n != 1:
        sys.exit("privacy.html: the hosting paragraph was not found (was the page wording changed?)")

    entries = []
    for f in PAGES:
        entries.append((f, privacy.encode("utf-8") if f == "privacy.html" else (site / f).read_bytes()))
    if a.allow_share:
        config = 'window.PLANNER_CONFIG = { mode: "offline", siteUrl: "%s", shareBase: "%s" };\n' % (a.online_url, a.online_url)
    else:
        config = 'window.PLANNER_CONFIG = { mode: "offline", share: false, siteUrl: "%s" };\n' % a.online_url
    entries.append(("config.js", config.encode("utf-8")))
    entries.append(("README-OFFLINE.txt", README_TEXT.format(version=version, url=a.online_url, sharing=(SHARING_FULL if a.allow_share else SHARING_OPEN_ONLY).format(url=a.online_url)).replace("\n", "\r\n").encode("utf-8")))
    for p in fonts + images:
        entries.append((p.relative_to(site).as_posix(), p.read_bytes()))
    for ref in sorted(set(DATA_REF.findall(idx))):                        # the equipment data, loaded on demand by a script tag (works from a folder)
        if not (site / ref).is_file(): sys.exit("index.html refers to a data file that is missing: " + ref)
        entries.append((ref, (site / ref).read_bytes()))

    root = "BuildPlanner-offline-" + version
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    zpath = out / (root + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(entries):
            zi = zipfile.ZipInfo(root + "/" + name, FIXED_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data)

    zsha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (out / "SHA256SUMS.txt").write_text("%s  %s\n" % (zsha, zpath.name), encoding="utf-8")
    packed_index = dict(entries)["index.html"]
    assert packed_index == idx_bytes, "index.html must be packaged unchanged"
    print("Built %s  (%d files, %d KB)" % (zpath, len(entries), zpath.stat().st_size // 1024))
    print("  version            %s" % version)
    print("  zip sha256         %s  (also written to %s)" % (zsha, out / "SHA256SUMS.txt"))
    print("  share links        %s" % ("can be created (--allow-share)" if a.allow_share else "opened only (default)"))
    print("  index.html sha256  %s  (byte-for-byte the website's file)" % hashlib.sha256(idx_bytes).hexdigest()[:16])

    if a.compare:
        other = Path(a.compare).read_text(encoding="utf-8")
        n1, n2 = normalise(idx), normalise(other)
        if n1 == n2:
            print("  compare            OK: %s runs the same code, apart from image files" % a.compare)
        else:
            i = next((k for k, (x, y) in enumerate(zip(n1, n2)) if x != y), min(len(n1), len(n2)))
            sys.exit("  compare            DIFFERENT at character %d: %r vs %r" % (i, n1[max(0, i - 40):i + 40], n2[max(0, i - 40):i + 40]))


if __name__ == "__main__":
    main()
