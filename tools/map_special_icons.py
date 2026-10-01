#!/usr/bin/env python3
"""Give each of the 27 special mutagens its own icon from the game: write data/SPECIAL_MUT_ICONS.json (file names only, no art)
and copy the icons into the private art folder (<art-dir>/mutagen_potions/, never into this repo).

    python tools/map_special_icons.py --xml ~/incoming/def_item_alchemy_mutagens.xml --icons ~/incoming/mutagen_potions \\
                                      --art-dir ~/work/w3planner-art [--check]

Where the facts come from:
  * def_item_alchemy_mutagens.xml: the game's mutagen items ("Mutagen 1" to "Mutagen 28") with icon_path="icons/inventory/mutagen_potions/<file>.png".
    The XML carries NO display names (those are in en.w3strings), so a label is matched to an item by the monster name inside the icon's file name.
  * data/SPECIAL_MUT.json: our 27 labels and colours (from the ingredient items, see docs/DATA-PIPELINE.md).
How a label is matched (recorded as "how" in the output):
  name      the label and the file name agree after normalising ("katakan_mutagen.png" is Katakan)
  alias     the game spells the monster differently (czart is Chort, d'ao is Earth Elemental, ekimma is Ekimmara, leshy is Leshen, fogling is Foglet)
  inferred  the file name names no monster of ours (alghoul, lamia_ekimma, volcanic_gryphon, griphon). Each of these is the only unmatched icon
            of its colour left for the only unmatched label of that colour that fits, see INFERRED below.
Fails loudly if a label has no icon, an item or file is used twice, an icon is missing, or the colour of the picture (red, blue or green) is not
the colour of the label. The colour check is independent evidence for the "inferred" rows.
Note: the game reuses some pictures (several mutagens share one identical image); that is a fact of the game files, reported but not an error.
"""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PREFIX = ("quest_",)  # quest-only mutagens are not in the planner
ALIASES = {"czart": "chort", "d'ao": "earth elemental", "ekimma": "ekimmara", "leshy": "leshen", "ancient leshy": "ancient leshen", "fogling": "foglet"}
INFERRED = {  # file stem -> label. Not named by the file; chosen because the label is the only one of that colour left (see the module doc)
    "alghoul": "Greater Foglet",       # red; the other red labels all have their own named icon
    "volcanic_gryphon": "Archgriffin",  # red; the green gryphon icon is griphon, so this one is the red Archgriffin
    "griphon": "Griffin",               # green
    "lamia_ekimma": "Ekhidna",          # blue
}


def stem_name(file):
    s = Path(file).stem
    return s[: -len("_mutagen")] if s.endswith("_mutagen") else s


def norm(s): return re.sub(r"\s+", " ", s.replace("_", " ")).strip().lower()


def sanitise(file):
    """No apostrophes or other awkward characters in the file we ship: d'ao_mutagen.png -> dao_mutagen.png."""
    return re.sub(r"[^a-z0-9_.\-]", "", file.lower())


def colour_of(path):
    """red, blue or green by the saturated pixels of the picture."""
    from PIL import Image
    import numpy as np
    a = np.array(Image.open(path).convert("RGBA")).astype(float) / 255; m = a[..., 3] > .3; r, g, b = a[..., 0][m], a[..., 1][m], a[..., 2][m]
    w = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b))
    sc = {"red": (w * np.clip(r - np.maximum(g, b), 0, 1)).sum(), "blue": (w * np.clip(b - np.maximum(r, g), 0, 1)).sum(), "green": (w * np.clip(g - np.maximum(r, b), 0, 1)).sum()}
    return max(sc, key=sc.get)


def build(xml_path, icons_dir):
    items = re.findall(r'<item name="(Mutagen \d+)"[^>]*?icon_path="icons/inventory/mutagen_potions/([^"]+)"', Path(xml_path).read_text(encoding="utf-8-sig"))
    items = [(n, f) for n, f in items if not f.startswith(SKIP_PREFIX)]
    labels = json.loads((ROOT / "data" / "SPECIAL_MUT.json").read_text(encoding="utf-8"))
    if len(items) != len(labels): sys.exit("the XML has %d usable mutagen items but data/SPECIAL_MUT.json has %d special mutagens" % (len(items), len(labels)))
    by_label = {norm(l): (l, c) for l, c in labels}; rows = {}
    for item, file in items:
        stem = norm(stem_name(file)); inferred = INFERRED.get(stem_name(file))
        if inferred: key, how = norm(inferred), "inferred"
        elif stem in ALIASES: key, how = ALIASES[stem], "alias"
        else: key, how = stem, "name"
        if key not in by_label: sys.exit("no special mutagen matches %s (%s, looked for %r)" % (item, file, key))
        if key in rows: sys.exit("two game items match %r: %s and %s" % (by_label[key][0], rows[key]["item"], item))
        label, colour = by_label[key]
        if not (Path(icons_dir) / file).is_file(): sys.exit("icon file missing: %s" % (Path(icons_dir) / file))
        got = colour_of(Path(icons_dir) / file)
        if got != colour: sys.exit("%s: the picture is %s but the mutagen is %s (%s)" % (file, got, colour, label))
        rows[key] = {"label": label, "colour": colour, "item": item, "original": file, "file": sanitise(file), "how": how}
    missing = [l for l, _ in labels if norm(l) not in rows]
    if missing: sys.exit("no icon for: %s" % ", ".join(missing))
    out = [rows[norm(l)] for l, _ in labels]  # same order as SPECIAL_MUT.json
    if len({r["file"] for r in out}) != len(out): sys.exit("two special mutagens would share one icon file")
    if len({r["item"] for r in out}) != len(out): sys.exit("two special mutagens share one game item")
    for r in out: r["img"] = "@@img:mutagen_potions/%s@@" % Path(r["file"]).stem
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml", required=True); ap.add_argument("--icons", required=True); ap.add_argument("--art-dir", required=True)
    ap.add_argument("--check", action="store_true", help="only verify; write and copy nothing")
    a = ap.parse_args(); rows = build(a.xml, a.icons)
    same = {}
    for r in rows: same.setdefault(hashlib.sha1((Path(a.icons) / r["original"]).read_bytes()).hexdigest(), []).append(r["label"])
    shared = [v for v in same.values() if len(v) > 1]
    print("matched %d special mutagens (%d by name, %d by alias, %d inferred); %d distinct pictures" % (len(rows), *[sum(r["how"] == h for r in rows) for h in ("name", "alias", "inferred")], len(same)))
    for v in shared: print("  the game uses one picture for: " + ", ".join(v))
    if a.check: return
    dest = Path(a.art_dir) / "mutagen_potions"; dest.mkdir(parents=True, exist_ok=True)
    for r in rows: shutil.copyfile(Path(a.icons) / r["original"], dest / r["file"])
    (ROOT / "data" / "SPECIAL_MUT_ICONS.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote data/SPECIAL_MUT_ICONS.json and copied %d icons to %s" % (len(rows), dest))


if __name__ == "__main__":
    main()
