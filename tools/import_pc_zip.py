#!/usr/bin/env python3
"""Server side of tools/pc/extract_on_pc.py: unpack the zip Vivek's PC made.

    python tools/import_pc_zip.py --zip ~/incoming/w3planner-extract.zip --game-dir ~/incoming/gamedata

Icons (icons/<path>.dds) become PNG files in <game-dir>/inventory/ where the extractor looks for them (the path after icons/inventory/);
csv files (csv/<bundle>/<internal path>) go to <game-dir>/csv/<internal path>. Then run tools/extract_items.py to add the icons (it copies
them to the private art folder and updates the manifest and the guard fingerprints). Needs Pillow for the DDS to PNG conversion
(DXT1, DXT3, DXT5, BC4, BC5, BC7 and plain RGBA). The zip is treated as untrusted input: names with .. or absolute paths are refused.
"""
import argparse, io, sys, zipfile
from pathlib import Path


def safe(name):
    p = Path(name)
    return not p.is_absolute() and ".." not in p.parts and "\\" not in name and not name.startswith("/")


def import_zip(zip_path, game_dir):
    from PIL import Image
    game = Path(game_dir); done = {"icons": 0, "csv": 0, "failed": []}
    with zipfile.ZipFile(zip_path) as z:
        bad = [n for n in z.namelist() if not safe(n)]
        if bad: sys.exit("refusing the zip: unsafe file names, e.g. %r" % bad[0])
        for n in z.namelist():
            if n.startswith("icons/") and n.endswith(".dds"):
                rel = n[len("icons/"):-len(".dds")]
                rel = rel[len("icons/inventory/"):] if rel.startswith("icons/inventory/") else rel
                dest = game / "inventory" / (rel + ".png"); dest.parent.mkdir(parents=True, exist_ok=True)
                try: Image.open(io.BytesIO(z.read(n))).convert("RGBA").save(dest); done["icons"] += 1
                except Exception as e: done["failed"].append("%s: %s" % (n, e))
            elif n.startswith("csv/") and n.endswith(".csv"):
                rest = n.split("/", 2)
                if len(rest) < 3: continue
                dest = game / "csv" / rest[2]; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(z.read(n)); done["csv"] += 1
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", required=True); ap.add_argument("--game-dir", required=True)
    a = ap.parse_args(); r = import_zip(a.zip, a.game_dir)
    print("%d icons converted to PNG in %s/inventory/, %d csv files in %s/csv/" % (r["icons"], a.game_dir, r["csv"], a.game_dir))
    for f in r["failed"]: print("FAILED " + f)
    print("next: python tools/extract_items.py --game-dir %s --art-dir ~/work/w3planner-art" % a.game_dir)
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
