#!/usr/bin/env python3
"""Every item id the game's files REFER to but the XML we have does not DEFINE, for tools/pc/extract_on_pc.py --missing.

    python tools/make_wanted_items.py --game-dir ~/incoming/gamedata [--out tools/pc/wanted-items.txt]

References: item_cond, item_extension, loot_entry, ingredient, schematic, recipe, usable_item and card entries and bare <item name=> lines in the item
XML of the base game, Hearts of Stone and Blood and Wine (items and items_plus), and the name literals the scripts hand to AddAnItem and the like (plus
literals that share a family with a defined item). Minus every <item ... category=> definition in those files. Also: every gear or consumable looking name
string of en.w3strings that no defined item uses (its key hash is listed, so the PC script can recognise a definition by its localisation key). Prints the
counts by category (sets by school, relics, other weapons and armour, consumables, other) and writes the list file."""
import argparse, collections, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "extract"))
from bundle import Bundle  # noqa: E402
import w3dec  # noqa: E402

PACKAGES = [("xml.bundle", "gameplay"), ("ep1.bundle", "dlc\\ep1\\data\\gameplay"), ("bob.bundle", "dlc\\bob\\data\\gameplay")]
TAG, ATT = re.compile(r'<(\w+)\b((?:[^>"]|"[^"]*")*)>'), re.compile(r'([\w:]+)\s*=\s*"([^"]*)"')
REF = {("loot_entry", "name"), ("ingredient", "item_name"), ("schematic", "name_name"), ("schematic", "craftedItem_name"), ("recipe", "cookedItem_name"), ("item_extension", "name"),
       ("item_cond", "name"), ("usable_item", "name"), ("card", "item")}
CALL = re.compile(r"\b(AddAnItem|AddItem|GetItemsByName|GetItemId|HasItem|GetItemQuantityByName|RemoveItem|EquipItem|AddAndEquipItem|NewGamePlusAdjustDLCItem|AddItemByName|GetItemFromSlot|GiveItem)\s*\(\s*'([^']+)'")
LIT = re.compile(r"'([A-Za-z][A-Za-z0-9 _'\-\.]{2,60}?)'")
GEAR = re.compile(r"\b(armor|armour|boots|gauntlets?|gloves|trousers|pants|sword|crossbow|mask|bolts?|oil|bomb|decoction|potion|mutagen|elixir|schematic|diagram|cuirass|helmet|hood|saber|sabre|axe|mace|dagger|bow)\b", re.I)
SCHOOLS = [("Wolf (Wolven)", r"(?<![a-z])wolf(?![a-z])(?! pelt| liver| hour)|wolven"), ("Red Wolf (Manticore)", r"red wolf|manticore"), ("Lynx (Feline)", r"lynx|feline"), ("Gryphon (Griffin)", r"gryphon|griffin"),
           ("Bear (Ursine)", r"(?<![a-z])bear(?![a-z])|ursine"), ("Viper", r"viper"), ("Netflix (Forgotten Wolven)", r"netflix"), ("Vampire", r"vampire")]
fam = lambda s: re.sub(r"\s*\d+$", "", re.sub(r"^(NGP|EP1|EP2|q\d+_)\s*", "", s)).strip().lower()


def category(k):
    l = k.lower()
    for name, rx in SCHOOLS:
        if re.search(rx, l) and re.search(r"sword|armor|armour|gloves|gauntlet|boots|pants|trousers|jacket|upgrade|schematic|crossbow|mask|diagram", l): return "set: " + name
    if re.search(r"relic|autogen|top notch|legendary", l): return "relic"
    if re.search(r"potion|\boil\b|oil \d|bomb|decoction|mutagen|petard|elixir|venom|philtre|antidote|swallow|blizzard|thunderbolt|full moon|black blood|white honey|golden oriole|tawny owl|maribor forest|killer whale|dancing star|grapeshot|samum|puffball|dragon.s dream|dwimeri|dimeri|silver dust|white frost|recipe for", l): return "consumable"
    if re.search(r"sword|armor|armour|gloves|gauntlet|boots|pants|trousers|mask|crossbow|bolt|axe|mace|club|dagger|helm|hood|cuirass|hauberk|shield|saber|sabre|blade|bow\b|upgrade|rune|glyph", l): return "other weapon/armour"
    return "other"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--game-dir", required=True); ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "pc" / "wanted-items.txt"))
    a = ap.parse_args(argv); d = Path(a.game_dir).expanduser(); defined, refs, have_ab = set(), collections.defaultdict(set), set()
    for bname, root in PACKAGES:
        b = Bundle(d / "bundles" / bname)
        for folder in ("abilities", "abilities_plus"):
            for e in b.match("%s\\%s\\*.xml" % (root, folder)): have_ab |= {m.group(1) for m in re.finditer(r'<ability\b[^>]*?\bname\s*=\s*"([^"]+)"', re.sub(r"<!--.*?-->", "", b.read(e).decode("utf-8-sig", "replace"), flags=re.S))}
        for folder in ("items", "items_plus"):
            for e in b.match("%s\\%s\\*.xml" % (root, folder)):
                t = re.sub(r"<!--.*?-->", "", b.read(e).decode("utf-8-sig", "replace"), flags=re.S)
                have_ab |= {m.group(1) for m in re.finditer(r'<ability\b[^>]*?\bname\s*=\s*"([^"]+)"', t)}
                for m in TAG.finditer(t):
                    tag, at = m.group(1), dict(ATT.findall(m.group(2)))
                    if tag == "item" and "name" in at:
                        (defined.add(at["name"]) if "category" in at else refs[at["name"]].add("xml: bare item"))
                    for k, v in at.items():
                        if (tag, k) in REF and v.strip(): refs[v].add("xml: %s.%s" % (tag, k))
        b.close()
    lits = collections.defaultdict(set)
    for f in (d / "scripts").rglob("*.ws"):
        t = re.sub(r"/\*.*?\*/", "", re.sub(r"//[^\n]*", "", f.read_text(encoding="utf-8", errors="replace")), flags=re.S)
        for m in CALL.finditer(t): refs[m.group(2)].add("script: item call")
        for m in LIT.finditer(t): lits[m.group(1)].add(f.name)
    fams = {fam(x) for x in defined}
    for k in lits:
        if k not in defined and fam(k) in fams and len(k) > 4 and any(c.isupper() or c.isdigit() for c in k): refs[k].add("script: name literal of a known family")
    missing = {k.strip(): v for k, v in refs.items() if k.strip() and k not in defined}
    strs, keys = w3dec.decode(str(d / "en.w3strings")); used = set()
    for bname, root in PACKAGES:
        b = Bundle(d / "bundles" / bname)
        for folder in ("items", "items_plus"):
            for e in b.match("%s\\%s\\*.xml" % (root, folder)):
                for m in re.finditer(r'localisation_key_(?:name|description)\s*=\s*"([^"]+)"', b.read(e).decode("utf-8-sig", "replace")): used.add(keys.get(w3dec.h(m.group(1))))
        b.close()
    orphans = sorted((kh, strs[sid]) for kh, sid in keys.items() if sid not in used and sid in strs and len(strs[sid]) < 70 and "\n" not in strs[sid] and GEAR.search(strs[sid]))
    groups = collections.defaultdict(list)
    for k in sorted(missing): groups[category(k)].append(k)
    lines = ["# written by tools/make_wanted_items.py: ids the game files refer to but the XML we have does not define (tab separated: id, category, where it is referenced)"]
    for c in sorted(groups):
        for k in groups[c]: lines.append("%s\t%s\t%s" % (k, c, ", ".join(sorted(missing[k]))))
    lines.append("# name keys: gear or consumable looking strings of en.w3strings that no defined item uses (hash of the key, text). A definition whose localisation_key_name has one of these hashes is wanted too")
    lines += ["#key\t%d\t%s" % (kh, t) for kh, t in orphans]
    lines.append("# abilities we already have (the PC script does not copy those): one per line")
    lines += ["#have\t" + n for n in sorted(have_ab)]
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("abilities already defined: %d" % len(have_ab)); print("defined: %d, referenced: %d, referenced but not defined: %d, unused gear-like name strings: %d" % (len(defined), len(refs), len(missing), len(orphans)))
    for c in sorted(groups): print("  %-30s %4d   e.g. %s" % (c, len(groups[c]), "; ".join(groups[c][:4])))
    srcs = collections.Counter(s.split(":")[0] for v in missing.values() for s in {x.split(":")[0] for x in v})
    print("  by source (an id can have both):", dict(srcs), "| xml only:", sum(1 for v in missing.values() if all(x.startswith("xml") for x in v)), "| script only:", sum(1 for v in missing.values() if all(x.startswith("script") for x in v)))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
