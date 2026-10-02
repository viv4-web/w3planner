#!/usr/bin/env python3
"""Make the two small data files the save import needs (v31), from the game's own files:

    python tools/make_save_data.py --game-dir ~/incoming/gamedata            (writes data/SAVEMUT.json and data/savenames.json; --check only verifies)

  data/SAVEMUT.json   {save item id: index into the planner's MUTS (0-8 regular red/blue/green x lesser/normal/greater, 9-35 the 27 special ones in SPECIAL_MUT order)}
                      The save names a skill mutagen by its game item id ("Gryphon mutagen"); our mutagens are named by their localised name ("Griffin mutagen"), so the table is made once,
                      here, by matching the game's localised names (item XML + en.w3strings) with ours. The importer then matches by id only.
  data/savenames.json {save item id: localised name} for the items a quick slot can hold that the planner does not plan (food, drink, torch...): Cows milk -> "Cow's milk", Bottled water -> "Water".
Standard library plus tools/extract. Nothing here is game art; names are the game's text, like the item names in data/items_ng.json.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import bundle as W3B, w3dec   # noqa: E402


def norm(s): return re.sub(r"\s+", " ", unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()).strip()


def xml_files(game_dir, patterns):
    """(file name, text) of every item XML in the base bundle, both expansions and dlc-xml/ whose file name matches one of the prefixes."""
    for bn, pat in (("xml", "gameplay\\items\\*.xml"), ("bob", "dlc\\bob\\data\\gameplay\\items\\*.xml"), ("ep1", "dlc\\ep1\\data\\gameplay\\items\\*.xml")):
        b = W3B.Bundle(Path(game_dir) / "bundles" / (bn + ".bundle"))
        for e in b.match(pat):
            fn = e.name.rsplit("\\", 1)[-1]
            if fn.startswith(patterns): yield fn, b.read(e).decode("utf-8-sig", "replace")
        b.close()
    for p in sorted((Path(game_dir) / "dlc-xml").glob("*/items/*.xml")):
        if p.name.startswith(patterns): yield p.name, p.read_text(encoding="utf-8-sig", errors="replace")


def items(text):
    for m in re.finditer(r"<item\s(.*?)>", text, re.S):
        a = m.group(1); n = re.search(r'\bname\s*=\s*"([^"]+)"', a); k = re.search(r'localisation_key_name\s*=\s*"([^"]*)"', a)
        if n and k: yield n.group(1), k.group(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", default=str(Path.home() / "incoming/gamedata")); ap.add_argument("--check", action="store_true")
    a = ap.parse_args(); strs, keys = w3dec.decode(str(Path(a.game_dir) / "en.w3strings"))
    disp = lambda key: strs.get(keys.get(w3dec.h(key)))
    base, spec = json.loads((ROOT / "data/MUTS.json").read_text(encoding="utf-8")), json.loads((ROOT / "data/SPECIAL_MUT.json").read_text(encoding="utf-8"))
    ours = {norm(n): i for i, n in enumerate([m["name"] for m in base] + [lb + " mutagen" for lb, _ in spec])}
    alias, miss = {}, []
    for fn, text in xml_files(a.game_dir, ("def_item_ingredients",)):
        for iid, key in items(text):
            if re.search(r"mutagen", iid, re.I) and not iid.startswith("Recipe"):
                d = disp(key)
                if d and norm(d) in ours: alias[iid] = ours[norm(d)]
                else: miss.append((iid, d))
    names = {}
    for fn, text in xml_files(a.game_dir, ("def_item_edibles", "def_item_misc")):
        for iid, key in items(text):
            d = disp(key)
            if d: names[iid] = d
    if len(alias) != 36 or sorted(alias.values()) != list(range(36)): sys.exit("the mutagen table is not one id per mutagen: %d ids, unmapped %s" % (len(alias), miss))
    out = {"SAVEMUT.json": alias, "savenames.json": dict(sorted(names.items()))}
    for fn, obj in out.items():
        blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), indent=None) + "\n"
        if a.check: print(fn, "ok" if (ROOT / "data" / fn).read_text(encoding="utf-8") == blob else "DIFFERS")
        else: (ROOT / "data" / fn).write_text(blob, encoding="utf-8"); print("wrote data/%s (%d entries)" % (fn, len(obj)))


if __name__ == "__main__":
    main()
