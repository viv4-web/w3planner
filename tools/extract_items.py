#!/usr/bin/env python3
"""Extract the planner's equipment data from the game's item XML: data/items.json (no art in it, only file names and tokens).

    python tools/extract_items.py --game-dir ~/incoming/gamedata --art-dir ~/work/w3planner-art            write data/items.json, copy the icons, update the manifest and fingerprints
    python tools/extract_items.py --game-dir ~/incoming/gamedata --check                                     only verify that data/items.json is what the game files produce, and print the report

--game-dir holds items/ (def_item_*.xml, dlc18_*, w3r_*), inventory/ (the icons) and en.w3strings. Re-run it for a new game patch.
Everything is read from those files, nothing is typed in by hand except the SETS table below (how the game's own tags and names
group items into sets) and the slot table. What the XML does NOT contain is written as null and reported, not guessed:
  * required level (equipment XML has no level; it is computed by game scripts)
  * set bonuses (the XML only tags the pieces; the bonus abilities and their text are not in the files)
  * the damage/armour of "Autogen" items (relics): the XML only has the formula ranges; the game scales them with the item level
Names: an item's id is its XML name (unique across all files). Display names come from en.w3strings through the item's
localisation_key_name (the same key hash the game uses); stat labels from "attribute_name_<stat>".
"""
import argparse, hashlib, json, re, shutil, sys, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import w3dec  # noqa: E402

# game category -> planner slot. order is the order of the slots in the equipment panel
SLOTS = [("steel", "steelsword", "Steel sword", "weapon"), ("silver", "silversword", "Silver sword", "weapon"), ("crossbow", "crossbow", "Crossbow", "weapon"),
         ("bolts", "bolt", "Bolts", "ammo"), ("chest", "armor", "Armor", "armor"), ("gloves", "gloves", "Gauntlets", "armor"), ("trousers", "pants", "Trousers", "armor"),
         ("boots", "boots", "Boots", "armor"), ("mask", "mask", "Mask", "cosmetic")]
BY_CATEGORY = {c: s for s, c, _, _ in SLOTS}
SLOT_KIND = {s: k for s, _, _, k in SLOTS}
ORDER = {s: i for i, (s, _, _, _) in enumerate(SLOTS)}
QUALITY = {1: "common", 2: "masterwork", 3: "magic", 4: "relic", 5: "set"}  # def_item_quality.xml: Master=2, Magic=3, Relic=4, SetItem=5; Default=1
# witcher school and DLC sets, as the game's data groups them: by tag where the game has one, else by item name
SETS = [
    ("lynx", "Feline", "school", lambda n, t: "LynxSet" in t),
    ("gryphon", "Griffin", "school", lambda n, t: "GryphonSet" in t),
    ("bear", "Ursine", "school", lambda n, t: "BearSet" in t),
    ("wolven", "Forgotten Wolven", "school", lambda n, t: "NetflixSet" in t),
    ("viper", "Viper", "school", lambda n, t: n.startswith("Viper School")),
    ("white_tiger", "White Tiger of the West", "dlc", lambda n, t: n.startswith("White Tiger")),
    ("thousand_flowers", "Thousand Flowers", "dlc", lambda n, t: n.startswith("Dol Blathanna") or n.startswith("White Widow of Dol Blathanna")),
    ("vixen", "Nine-Tailed Vixen", "dlc", lambda n, t: n in ("Steel Vixen", "Silver Vixen")),
    ("scarlet_crest", "Scarlet Crest", "dlc", lambda n, t: n.startswith("Scarlet Crest")),
]
SET_INFO = {s: (name, kind) for s, name, kind, _ in SETS}
TIER_WORDS = [("grandmaster", "Grandmaster"), ("mastercrafted", "Mastercrafted"), ("superior", "Superior"), ("enhanced", "Enhanced")]
DAMAGE = {"SlashingDamage", "SilverDamage", "PiercingDamage", "BludgeoningDamage", "RendingDamage", "FireDamage", "ElementalDamage", "PhysicalDamage"}
SKIP_FILES = ("def_loot",)                      # loot tables: not items
NPC_FILES = ("def_item_npcweapons.xml", "_technical_items_defs.xml")
# the game spells a few stat names differently in the XML and in its strings (checked: each target key exists in en.w3strings)
LABEL_ALIAS = {"staminaregen_armor_mod": "staminaregen", "dismember_chance": "dismember_chance_mult", "instant_kill_chance": "instant_kill_chance_mult",
               "armor_reduction_perc": "armor_reduction", "staggereffect": "stagger"}
AUTOGEN_NOTE = ("Autogen item: the XML holds only the formula ranges (data/items.json autogen.abilities); the game scales damage or armour with the item level, "
                "so the base numbers are not in the files")


def read_xml(path):
    return ET.parse(path).getroot()


def tags_of(it):
    t = it.find("tags")
    return [x.strip() for x in (t.text or "").replace("\n", " ").split(",") if x.strip()] if t is not None else []


def num(x):
    f = float(x)
    return int(f) if f == int(f) and "." not in x else round(f, 6)


def sanitise(s):
    return re.sub(r"[^a-z0-9_.\-]", "", s.lower().replace(" ", "_"))


class Game:
    def __init__(self, game_dir):
        self.dir = Path(game_dir); self.items, self.abilities, self.file_of, self.parse_failures = {}, {}, {}, []
        for f in sorted((self.dir / "items").glob("*.xml")):
            if f.name.startswith(SKIP_FILES): continue
            try: root = read_xml(f)
            except ET.ParseError as e: self.parse_failures.append((f.name, str(e))); continue
            for ab in root.iter("ability"):
                if ab.get("name"): self.abilities[ab.get("name")] = ab        # a later file wins (2 duplicate names exist, both outside equipment)
            for it in root.iter("item"):
                n = it.get("name")
                if not n: continue
                if n in self.items: sys.exit("two items called %r (%s and %s)" % (n, self.file_of[n], f.name))
                self.items[n], self.file_of[n] = it, f.name
        self.strs, self.keys = w3dec.decode(str(self.dir / "en.w3strings"))
        self.unresolved = defaultdict(set)

    def text(self, key):
        return self.strs.get(self.keys.get(w3dec.h(key))) if key else None

    def label(self, stat):
        k = stat.lower()
        return self.text("attribute_name_" + k) or (self.text("attribute_name_" + LABEL_ALIAS[k]) if k in LABEL_ALIAS else None)


def stats_of(game, item):
    """(entries, ability names, missing ability names). Entry: {stat, label, type, min, max, ability} or {stat, label, effect: true}."""
    ba = item.find("base_abilities"); names = [a.text.strip() for a in ba.findall("a")] if ba is not None else []
    entries, missing = [], []
    for n in names:
        ab = game.abilities.get(n)
        if ab is None: missing.append(n); continue
        for c in ab:
            if c.tag == "tags": continue
            lab = game.label(c.tag)
            if lab is None: game.unresolved[c.tag].add(item.get("name"))
            if c.get("is_ability") == "true": entries.append({"stat": c.tag, "label": lab, "effect": True, "ability": n}); continue
            if c.get("min") is None: continue
            e = {"stat": c.tag, "label": lab, "type": c.get("type") or "base", "min": num(c.get("min")), "ability": n}
            if c.get("max") is not None and num(c.get("max")) != e["min"]: e["max"] = num(c.get("max"))
            entries.append(e)
    return entries, names, missing


def build(game_dir):
    g = Game(game_dir); report = {"parse_failures": g.parse_failures, "notes": []}
    generic_desc = Counter(it.get("localisation_key_description") for it in g.items.values())
    rows, unassigned_q5 = [], []
    for name, it in g.items.items():
        cat = it.get("category")
        if cat not in BY_CATEGORY or g.file_of[name] in NPC_FILES: continue
        tags = tags_of(it); slot = BY_CATEGORY[cat]
        if "NoShow" in tags and cat != "mask": continue
        entries, abnames, missing = stats_of(g, it)
        q = int(sum(e["min"] for e in entries if e["stat"] == "quality"))
        sets = [s for s, _, _, pred in SETS if pred(name, tags)]
        if len(sets) > 1: sys.exit("%s matches several sets: %s" % (name, sets))
        fname = g.file_of[name]
        if sets: group, sid = SET_INFO[sets[0]][1], sets[0]
        elif slot == "crossbow" and fname == "def_item_weapons_crossbow.xml": group, sid = "crossbow", None
        elif slot == "bolts" and fname == "def_item_bolts.xml": group, sid = "bolt", None
        elif slot == "mask" and "NoShow" not in tags: group, sid = "mask", None
        elif q == 4 and slot not in ("crossbow", "bolts", "mask") and "SecondaryWeapon" not in tags: group, sid = "relic", None   # axes and maces are secondary weapons
        else:
            if q == 5: unassigned_q5.append(name)
            continue
        rows.append((name, it, tags, slot, entries, abnames, missing, q, group, sid, fname))
    report["quality5_items_not_in_a_set"] = unassigned_q5

    # tiers: items of one set and slot whose names differ only by a trailing number form a chain, in number order
    chains = defaultdict(list)
    for r in rows:
        if r[9]:
            m = re.match(r"^(.*?)(?: (\d+))?$", r[0]); chains[(r[9], r[3], m.group(1))].append((int(m.group(2) or 0), r[0]))
    tier = {}
    for (_, _, _), lst in chains.items():
        for i, (_, n) in enumerate(sorted(lst), 1): tier[n] = i

    icons, items, autogen_used, missing_icons = {}, [], set(), defaultdict(list)
    for name, it, tags, slot, entries, abnames, missing, q, group, sid, fname in rows:
        disp = g.text(it.get("localisation_key_name"))
        if disp is None: report["notes"].append("no display name for %s" % name)
        low = (disp or "").lower()
        tier_name = next((w for k, w in TIER_WORDS if k in low), "Basic") if sid else None
        ic = it.get("icon_path")
        src = None
        if ic:
            rel = ic.replace("\\", "/").replace("icons/inventory/", "", 1); src = g.dir / "inventory" / rel
            if not src.is_file(): missing_icons[ic].append(name); src = None
        slot_id = None
        if src:
            sub, stem = Path(rel).parent.name, Path(rel).stem; slot_id = "items/%s/%s" % (sanitise(sub), sanitise(stem)); icons[slot_id] = (src, sanitise(Path(rel).name))
        desc_key = it.get("localisation_key_description"); desc = g.text(desc_key) if desc_key and generic_desc[desc_key] <= 3 else None
        autogen = "Autogen" in tags and group in ("relic", "school", "dlc")
        base = [e for e in entries if not e.get("effect") and (e["stat"] in DAMAGE or e["stat"] == "armor" or e["stat"].endswith("_resistance_perc") or e["stat"].startswith("physical_resistance"))]
        bonus = [e for e in entries if e not in base and e["stat"] not in ("quality", "weight")]
        weight = next((e["min"] for e in entries if e["stat"] == "weight"), None)
        if weight is None and it.get("weight"): weight = num(it.get("weight"))
        enh = int(it.get("enhancement_slots") or 0) if it.get("enhancement_slots") is not None else None
        rec = {"id": name, "name": disp, "slot": slot, "group": group, "set": sid, "tier": tier.get(name), "tier_name": tier_name,
               "quality": q, "quality_name": QUALITY.get(q), "required_level": None,
               "armor_class": next((c for t, c in (("LightArmor", "light"), ("MediumArmor", "medium"), ("HeavyArmor", "heavy")) if t in tags), None) if SLOT_KIND[slot] == "armor" else None,
               "weight": weight, "price": num(it.get("price")) if it.get("price") else None,
               "base": [{k: v for k, v in e.items() if k != "ability"} for e in base], "bonuses": [{k: v for k, v in e.items() if k != "ability"} for e in bonus],
               "enhancement_slots": enh, "enhancement_kind": {"weapon": "rune", "armor": "glyph"}.get(SLOT_KIND[slot]) if enh else None,
               "set_bonus_piece": ("SetBonusPiece" in tags) or None, "crafted": bool(re.search(r"[ _]crafted$", name)) or None, "autogen": bool(autogen) or None, "description": desc, "icon_path": ic, "icon": "@@img:%s@@" % slot_id if slot_id else None,
               "tags": tags, "abilities": abnames, "file": fname}
        if missing: report["notes"].append("%s: abilities not defined in the files: %s" % (name, missing))
        if autogen: autogen_used.add(name)
        items.append(rec)
    for path, names in sorted(missing_icons.items()): report["notes"].append("icon file missing (%d items, e.g. %s): %s" % (len(names), names[0], path))
    items.sort(key=lambda r: (ORDER[r["slot"]], ["school", "dlc", "relic", "crossbow", "bolt", "mask"].index(r["group"]), r["set"] or "", r["tier"] or 0, r["id"]))
    sets = {}
    for s, name, kind, _ in SETS:
        pieces = [r["id"] for r in items if r["set"] == s]
        sets[s] = {"name": name, "kind": kind, "pieces": pieces, "slots": sorted({r["slot"] for r in items if r["set"] == s}, key=ORDER.get),
                   "tiers": max([r["tier"] for r in items if r["set"] == s] or [0]), "bonus_piece_tag": sorted(r["id"] for r in items if r["set"] == s and r["set_bonus_piece"]), "bonuses": None}
    ag = {n: [{k: v for k, v in (("stat", c.tag), ("type", c.get("type")), ("min", num(c.get("min"))), ("max", num(c.get("max")) if c.get("max") is not None else None)) if v is not None}
              for c in a if c.get("min") is not None] for n, a in g.abilities.items() if n.startswith("autogen_")}
    data = {"version": 1, "game_files": sorted({r["file"] for r in items}), "slots": [{"id": s, "category": c, "label": l, "kind": k} for s, c, l, k in SLOTS],
            "sets": sets, "autogen": {"note": AUTOGEN_NOTE, "abilities": ag},
            "notes": {"required_level": "not in the equipment XML (computed by game scripts): null",
                      "set_bonuses": "not in the XML (the pieces are only tagged); sets[*].bonuses is null",
                      "stat_values": "min/max are the raw XML numbers; type is the game's: base, add, mult. Percentages are fractions (0.1 = 10%). A max means the value is rolled between min and max"},
            "items": items}
    report["unresolved_stat_labels"] = {k: sorted(v)[:3] for k, v in sorted(g.unresolved.items())}
    return data, icons, report


def summarise(data, report):
    items = data["items"]; out = ["%d items" % len(items), "per slot: " + ", ".join("%s %d" % (s["id"], sum(r["slot"] == s["id"] for r in items)) for s in data["slots"])]
    out.append("per group: " + ", ".join("%s %d" % (k, v) for k, v in sorted(Counter(r["group"] for r in items).items())))
    for s, info in data["sets"].items():
        by = defaultdict(Counter)
        for r in items:
            if r["set"] == s: by[r["tier"]][r["slot"]] += 1
        out.append("set %-17s %-24s %2d pieces; tiers: %s" % (s, info["name"], len(info["pieces"]), "; ".join("T%d %s" % (t, "/".join(sorted(c, key=ORDER.get))) for t, c in sorted(by.items()))))
    out.append("quality: " + ", ".join("%s %d" % (k, v) for k, v in sorted(Counter(str(r["quality_name"]) for r in items).items())))
    out.append("autogen items (damage/armour not in the XML): %d" % sum(bool(r["autogen"]) for r in items))
    out.append("items without an icon: %d" % sum(r["icon"] is None for r in items))
    out.append("stat labels that do not resolve in the strings: %s" % report["unresolved_stat_labels"])
    out.extend("note: " + n for n in report["notes"][:30]); out.append("parse failures: %s" % report["parse_failures"])
    return "\n".join(out)


def update_manifest(icons):
    """art/manifest.json: one slot per icon (the game build reads <art-dir>/<id>.png); the public build shows the drawn placeholder of the item's slot."""
    p = ROOT / "art" / "manifest.json"; m = json.loads(p.read_text())
    m = {k: v for k, v in m.items() if not k.startswith("items/")}
    for sid in SLOT_IDS_WITH_PLACEHOLDER: m["items/ph-" + sid] = {"game": "png", "placeholder": "png"}
    for sid in sorted(icons): m[sid] = {"game": "png", "placeholder": "png", "placeholder_as": "items/ph-" + ICON_SLOT[sid]}
    p.write_text(json.dumps(m, indent=1) + "\n")


SLOT_IDS_WITH_PLACEHOLDER = [s for s, _, _, _ in SLOTS]
ICON_SLOT = {}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", required=True); ap.add_argument("--art-dir", help="copy the icons to <art-dir>/items/ and register them (the private art folder, never this repo)")
    ap.add_argument("--check", action="store_true", help="verify data/items.json against the game files; write nothing")
    a = ap.parse_args()
    data, icons, report = build(a.game_dir); text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    for r in data["items"]:
        if r["icon"]: ICON_SLOT[r["icon"][len("@@img:"):-2]] = r["slot"]
    print(summarise(data, report))
    out = ROOT / "data" / "items.json"
    if a.check:
        if not out.is_file() or out.read_text(encoding="utf-8") != text: sys.exit("data/items.json is not what the game files produce: re-run without --check")
        print("data/items.json is up to date"); return
    out.write_text(text, encoding="utf-8"); update_manifest(icons)
    print("wrote %s (%d KB), %d icon slots in art/manifest.json" % (out.relative_to(ROOT), len(text) // 1024, len(icons)))
    if a.art_dir:
        hashes = ROOT / "tools" / "game-art-hashes.txt"; lines = hashes.read_text().splitlines(); have = {l.split()[0] for l in lines if l.strip() and not l.startswith("#")}; add = []
        for sid, (src, _) in sorted(icons.items()):
            dest = Path(a.art_dir) / (sid + ".png"); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, dest)
            d = hashlib.sha1(dest.read_bytes()).hexdigest()
            if d not in have: add.append("%s  %s.png" % (d, sid)); have.add(d)
        hashes.write_text("\n".join(lines + add) + "\n")
        print("copied %d icons to %s/items/, added %d fingerprints to tools/game-art-hashes.txt" % (len(icons), a.art_dir, len(add)))


if __name__ == "__main__":
    main()
