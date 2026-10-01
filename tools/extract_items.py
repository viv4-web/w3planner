#!/usr/bin/env python3
"""Extract the planner's equipment data from the game's own files: data/items.json (no art in it, only file names and tokens).

    python tools/extract_items.py --game-dir ~/incoming/gamedata --art-dir ~/work/w3planner-art     write data/items.json, copy the icons, update the manifest and fingerprints
    python tools/extract_items.py --game-dir ~/incoming/gamedata --check                             only verify that data/items.json is what the game files produce, and print the report

--game-dir holds:
  bundles/xml.bundle, ep1.bundle, bob.bundle   the definition XML (read with tools/extract/bundle.py): base game, Hearts of Stone, Blood and Wine.
                                               Each has gameplay/items and gameplay/abilities (the FIRST PLAYTHROUGH: ruleset "ng") and *_plus folders
                                               (NEW GAME PLUS: ruleset "ng_plus": the same files with higher "legendary" gear and the "NGP ..." carry-over items).
                                               In ng_plus a *_plus file replaces the base file of the same name. Items that are identical in both rulesets are stored once.
                                               Without bundles/, a plain items/ folder (the base-game "uncooked" XML) is read instead (ruleset ng only).
  inventory/                                   the item icons (PNG)
  en.w3strings                                 names and texts (tools/extract/w3dec.py)
  scripts/                                     the game's scripts (.ws): set bonuses, the required-level formula and the tooltip rules are read from them
Everything is read from those files. Typed in here: the SETS table (how the game's tags and names group items) and, for the set bonuses,
BONUSES (a transcription of GetSetBonusTooltipDescription in playerWitcher.ws); every line number cited in the output is looked up in the
scripts at run time and the run fails if what it expects is not there. What the files do not contain is null and reported, not guessed.
"""
import argparse, hashlib, json, math, re, shutil, sys, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import w3dec  # noqa: E402
from bundle import Bundle  # noqa: E402

# game category -> planner slot. The order is the order of the slots in the equipment panel.
SLOTS = [("steel", "steelsword", "Steel sword", "weapon"), ("silver", "silversword", "Silver sword", "weapon"), ("crossbow", "crossbow", "Crossbow", "weapon"),
         ("bolts", "bolt", "Bolts", "ammo"), ("chest", "armor", "Armor", "armor"), ("gloves", "gloves", "Gauntlets", "armor"), ("trousers", "pants", "Trousers", "armor"),
         ("boots", "boots", "Boots", "armor"), ("mask", "mask", "Mask", "cosmetic")]
BY_CATEGORY = {c: s for s, c, _, _ in SLOTS}
SLOT_KIND = {s: k for s, _, _, k in SLOTS}
ORDER = {s: i for i, (s, _, _, _) in enumerate(SLOTS)}
QUALITY = {1: "common", 2: "masterwork", 3: "magic", 4: "relic", 5: "set"}  # inventory tooltip: GetItemRarityDescription (guiTooltipComponent.ws)
TIER_WORDS = [("grandmaster", "Grandmaster", 5), ("mastercrafted", "Mastercrafted", 4), ("superior", "Superior", 3), ("enhanced", "Enhanced", 2)]
# Sets: (id, name, kind, game tag, name rule). A set bonus exists only for the tags the scripts know (EIST_* in playerTypes.ws); the others are plain DLC sets.
SETS = [
    ("lynx", "Feline", "school", "LynxSet", None), ("gryphon", "Griffin", "school", "GryphonSet", None), ("bear", "Ursine", "school", "BearSet", None),
    ("wolf", "Wolven", "school", "WolfSet", None), ("red_wolf", "Manticore", "school", "RedWolfSet", None),
    ("viper", "Viper", "school", "ViperSet", lambda n: n.startswith(("Viper School", "EP1 Viper School"))),
    ("netflix", "Forgotten Wolven", "school", "NetflixSet", None), ("vampire", "Tesham Mutna and Hen Gaidth", "quest", "VampireSet", None),
    ("white_tiger", "White Tiger of the West", "dlc", None, lambda n: n.startswith("White Tiger")),
    ("thousand_flowers", "Thousand Flowers", "dlc", None, lambda n: n.startswith(("Dol Blathanna", "White Widow of Dol Blathanna"))),
    ("vixen", "Nine-Tailed Vixen", "dlc", None, lambda n: n in ("Steel Vixen", "Silver Vixen")),
    ("scarlet_crest", "Scarlet Crest", "dlc", None, lambda n: n.startswith("Scarlet Crest")),
]
SET_INFO = {s: (name, kind, tag) for s, name, kind, tag, _ in SETS}
DAMAGE = {"SlashingDamage", "SilverDamage", "PiercingDamage", "BludgeoningDamage", "RendingDamage", "FireDamage", "ElementalDamage", "PhysicalDamage"}
SKIP_FILES = ("def_loot",)
NPC_FILES = ("def_item_npcweapons.xml", "_technical_items_defs.xml", "def_item_weapons_npc.xml", "def_item_bob_weapons_mon.xml", "def_item_weapons_mon.xml")
PACKAGES = [("xml.bundle", "gameplay"), ("ep1.bundle", "dlc\\ep1\\data\\gameplay"), ("bob.bundle", "dlc\\bob\\data\\gameplay")]  # base game, Hearts of Stone, Blood and Wine
# the game spells a few stat names differently in the XML and in its strings (each target key exists in en.w3strings)
LABEL_ALIAS = {"staminaregen_armor_mod": "staminaregen", "dismember_chance": "dismember_chance_mult", "instant_kill_chance": "instant_kill_chance_mult",
               "armor_reduction_perc": "armor_reduction", "staggereffect": "stagger"}
AUTOGEN_NOTE = ("Autogen item: the game scales damage or armour with the item level, so its base numbers are not in the XML (only formula ranges, autogen.abilities) and "
                "required_level is null. The UI shows the ranges the XML does give (min to max, as rolled) and the text 'Level varies' (decision: Vivek).")


def tags_of(it):
    t = it.find("tags")
    return [x.strip() for x in (t.text or "").replace("\n", " ").split(",") if x.strip()] if t is not None else []


def num(x):
    f = float(x)
    return int(f) if f == int(f) and "." not in x else round(f, 6)


def sanitise(s):
    return re.sub(r"[^a-z0-9_.\-]", "", s.lower().replace(" ", "_"))


RULESETS = ("ng", "ng_plus")


def xml_sources(game_dir, ruleset):
    """{(package, kind, file name): bytes}: see the module doc."""
    d = Path(game_dir); files = {}
    if any((d / "bundles" / b).is_file() for b, _ in PACKAGES):
        for bname, root in PACKAGES:
            if not (d / "bundles" / bname).is_file(): continue
            b = Bundle(d / "bundles" / bname)
            for folder in ("items", "abilities") + (("items_plus", "abilities_plus") if ruleset == "ng_plus" else ()):          # _plus is read later, so it replaces the base file
                for e in b.match("%s\\%s\\*.xml" % (root, folder)):
                    files[(bname, folder.split("_")[0], e.name.rsplit("\\", 1)[-1])] = b.read(e)
            b.close()
        return files
    for f in sorted((d / "items").glob("*.xml")): files[("items", "items", f.name)] = f.read_bytes()
    return files


class Scripts:
    """The game's .ws files, for line numbers and for the few constants the planner needs."""
    def __init__(self, game_dir):
        self.root = Path(game_dir) / "scripts"; self.cache = {}

    def lines(self, rel):
        if rel not in self.cache:
            p = self.root / rel
            if not p.is_file(): sys.exit("script missing: %s (needed for the set bonuses and the level rule)" % p)
            self.cache[rel] = p.read_text(encoding="utf-8", errors="replace").split("\n")
        return self.cache[rel]

    def find(self, rel, pattern, start=1):
        """1-based line of the first line at or after `start` that matches; fail loudly if the scripts do not contain it."""
        rx = re.compile(pattern)
        for i in range(start - 1, len(self.lines(rel))):
            if rx.search(self.lines(rel)[i]): return i + 1
        sys.exit("the scripts do not contain %r in %s: the planner's reading of them needs updating" % (pattern, rel))

    def ref(self, rel, pattern, start=1):
        return "scripts/%s:%d" % (rel, self.find(rel, pattern, start))

    def const(self, rel, name):
        m = re.search(r"default\s+%s\s*=\s*([0-9.]+)\s*;" % re.escape(name), "\n".join(self.lines(rel)))
        if not m: sys.exit("%s not set in %s" % (name, rel))
        return num(m.group(1))


class Game:
    def __init__(self, game_dir, ruleset, strings=None):
        self.dir = Path(game_dir); self.ruleset = ruleset; self.items, self.abilities, self.file_of, self.parse_failures, self.duplicate_items = {}, {}, {}, [], []
        self.files = xml_sources(game_dir, ruleset); self.ability_file = {}
        for (pkg, kind, fname), blob in sorted(self.files.items()):
            if fname.startswith(SKIP_FILES): continue
            try: root = ET.fromstring(blob.decode("utf-8-sig"))
            except ET.ParseError as e: self.parse_failures.append((fname, str(e))); continue
            for ab in root.iter("ability"):
                if ab.get("name"): self.abilities[ab.get("name")] = ab; self.ability_file[ab.get("name")] = (pkg, kind, fname)
            for it in root.iter("item"):
                n = it.get("name")
                if not n: continue
                if n in self.items: self.duplicate_items.append((n, self.file_of[n], fname))   # a later package redefines an item
                self.items[n], self.file_of[n] = it, fname
        self.strs, self.keys = strings or w3dec.decode(str(self.dir / "en.w3strings"))
        self.unresolved = defaultdict(set)

    def text(self, key):
        return self.strs.get(self.keys.get(w3dec.h(key))) if key else None

    def label(self, stat):
        k = stat.lower()
        return self.text("attribute_name_" + k) or (self.text("attribute_name_" + LABEL_ALIAS[k]) if k in LABEL_ALIAS else None)

    def ability_value(self, ability, attr):
        """(type, min, max) of one attribute of one ability, from the XML."""
        ab = self.abilities.get(ability)
        c = ab.find(attr) if ab is not None else None
        if c is None or c.get("min") is None: sys.exit("ability %s has no attribute %s" % (ability, attr))
        return c.get("type") or "base", float(c.get("min")), float(c.get("max") if c.get("max") is not None else c.get("min"))


def stats_of(game, item):
    """(entries, ability names, missing ability names). Entry: {stat, label, type, min, max, ability} or {stat, label, effect: true, ability}."""
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


# ---- the game's required-level rule: GetItemLevel in components/inventoryComponent.ws (the tooltip) with the stat steps of gameParams.ws ----
def required_level(category, entries, quality, tags, name):
    """Level shown as "Requires level N" for an item whose numbers are in the XML. The formula is transcribed from the scripts (cited in rules.required_level).
    Attributes that the item does not define count as 0 (an assumption: the engine's default is not in the scripts)."""
    def base(attr):  # valueBase: the base-type entries, max of the roll
        return sum(e.get("max", e["min"]) for e in entries if e.get("stat") == attr and e.get("type") == "base")
    def mult(attr):
        return sum(e.get("max", e["min"]) for e in entries if e.get("stat") == attr and e.get("type") == "mult")
    level = None
    if category in ("armor", "boots", "gloves", "pants"):
        lo, step = {"armor": (25, 5), "boots": (5, 2), "gloves": (1, 2), "pants": (5, 2)}[category]; level = math.floor(1 + (base("armor") - lo) / step)
    elif category in ("steelsword", "silversword"):
        order = ["SlashingDamage", "BludgeoningDamage", "RendingDamage", "ElementalDamage", "FireDamage", "SilverDamage", "PiercingDamage"] if category == "steelsword" else \
                ["SilverDamage", "BludgeoningDamage", "RendingDamage", "ElementalDamage", "FireDamage", "PiercingDamage"]
        lo, step = (25, 8) if category == "steelsword" else (90, 10); f = sum(base(a) - 1 for a in order); level = math.ceil(1 + (1 + f - lo) / step)
    elif category == "crossbow":
        m = mult("attack_power"); level = 1
        for t, v in ((1.01, 2), (1.1, 4), (1.2, 8), (1.3, 11), (1.4, 15), (1.5, 19), (1.6, 22), (1.7, 25), (1.8, 27), (1.9, 32)):
            if m > t: level = v
    elif category == "bolt":
        level = {"Tracking Bolt": 2, "Bait Bolt": 2, "Blunt Bolt": 2, "Broadhead Bolt": 10, "Target Point Bolt": 5, "Split Bolt": 15, "Explosive Bolt": 20, "Blunt Bolt Legendary": 12,
                 "Broadhead Bolt Legendary": 20, "Target Point Bolt Legendary": 15, "Split Bolt Legendary": 24, "Explosive Bolt Legendary": 26}.get(name, 0)
    else:
        return None
    level -= 1
    if level < 1: level = 1
    if category == "bolt": level -= {5: 14, 4: 10, 3: 6, 2: 4}.get(quality, 0)
    elif quality == 5: level -= 2
    elif quality == 4: level -= 1
    if level < 1: level = 1
    if "OlgierdSabre" in tags: level -= 3
    if quality in (4, 5) and "EP1" in tags: level -= 1
    return level


def tier_of(display):
    low = (display or "").lower()
    return next(((w, r) for k, w, r in TIER_WORDS if k in low), ("Basic", 1))


def build_ruleset(g, sc):
    """The equipment of one ruleset (ng or ng_plus): (items, icons, report)."""
    report = {"parse_failures": g.parse_failures, "notes": [], "duplicate_item_definitions": len(g.duplicate_items)}
    generic_desc = Counter(it.get("localisation_key_description") for it in g.items.values())
    rows = []
    for name, it in g.items.items():
        cat = it.get("category")
        if cat not in BY_CATEGORY or g.file_of[name] in NPC_FILES: continue
        tags = tags_of(it); slot = BY_CATEGORY[cat]
        if "NoShow" in tags and cat != "mask": continue
        entries, abnames, missing = stats_of(g, it)
        q = int(sum(e["min"] for e in entries if e["stat"] == "quality"))
        plain = name[4:] if name.startswith("NGP ") else name
        sets = [s for s, _, _, tag, rule in SETS if (tag and tag in tags) or (rule and rule(plain))]
        if len(sets) > 1: sys.exit("%s matches several sets: %s" % (name, sets))
        fname = g.file_of[name]
        if sets: group, sid = ("quest_set" if SET_INFO[sets[0]][1] == "quest" else SET_INFO[sets[0]][1]), sets[0]
        elif slot == "crossbow" and "crossbow" in fname.lower(): group, sid = "crossbow", None
        elif slot == "bolts" and "bolt" in fname.lower(): group, sid = "bolt", None
        elif slot == "mask" and "NoShow" not in tags: group, sid = "mask", None
        elif q == 4 and slot not in ("crossbow", "bolts", "mask") and "SecondaryWeapon" not in tags: group, sid = "relic", None
        else: continue
        if group == "relic":
            if name.startswith("Top Notch"): report["notes"].append("excluded generic: %s" % name); continue
            if re.search(r"[ _]crafted$", name): report["notes"].append("excluded crafted duplicate: %s" % name); continue
        rows.append((name, it, tags, slot, entries, abnames, missing, q, group, sid, fname))

    icons, items, missing_icons = {}, [], defaultdict(list)
    for name, it, tags, slot, entries, abnames, missing, q, group, sid, fname in rows:
        disp = g.text(it.get("localisation_key_name"))
        if disp is None: report["notes"].append("excluded, no display name in the strings: %s" % name); continue
        tier_name, tier = tier_of(disp) if sid else (None, None)
        ic = it.get("icon_path"); src = rel = None
        if ic:
            rel = ic.replace("\\", "/").replace("icons/inventory/", "", 1); src = g.dir / "inventory" / rel
            if not src.is_file(): missing_icons[ic].append(name); src = None
        slot_id = None
        if src:
            sub, stem = Path(rel).parent.name, Path(rel).stem; slot_id = "items/%s/%s" % (sanitise(sub), sanitise(stem)); icons[slot_id] = (src, sanitise(Path(rel).name))
        if group == "mask" and not slot_id: continue                       # masks: only those with a real icon
        desc_key = it.get("localisation_key_description"); desc = g.text(desc_key) if desc_key and generic_desc[desc_key] <= 3 else None
        autogen = "Autogen" in tags and group in ("relic", "school", "dlc", "quest_set")
        base = [e for e in entries if not e.get("effect") and (e["stat"] in DAMAGE or e["stat"] == "armor" or e["stat"].endswith("_resistance_perc") or e["stat"].startswith("physical_resistance"))]
        bonus = [e for e in entries if e not in base and e["stat"] not in ("quality", "weight")]
        weight = next((e["min"] for e in entries if e["stat"] == "weight"), None)
        if weight is None and it.get("weight"): weight = num(it.get("weight"))
        enh = int(it.get("enhancement_slots")) if it.get("enhancement_slots") is not None else None
        lvl = None if autogen else required_level(it.get("category"), entries, q, tags, name)
        rec = {"id": name, "name": disp, "slot": slot, "group": group, "set": sid, "carry_over": name[4:] if name.startswith("NGP ") else None, "legendary": ("legendary" in (disp or "").lower()) or None,
               "tier": tier, "tier_name": tier_name, "quality": q or None, "quality_name": QUALITY.get(q), "required_level": lvl,
               "armor_class": next((c for t, c in (("LightArmor", "light"), ("MediumArmor", "medium"), ("HeavyArmor", "heavy")) if t in tags), None) if SLOT_KIND[slot] == "armor" else None,
               "weight": weight, "price": num(it.get("price")) if it.get("price") else None,
               "base": [{k: v for k, v in e.items() if k != "ability"} for e in base], "bonuses": [{k: v for k, v in e.items() if k != "ability"} for e in bonus],
               "enhancement_slots": enh, "enhancement_kind": {"weapon": "rune", "armor": "glyph"}.get(SLOT_KIND[slot]) if enh else None,
               "set_bonus_piece": ("SetBonusPiece" in tags) or None, "quest": (("Quest" in tags) or bool(re.match(r"^(q|mq|sq)\d", name))) or None,
               "autogen": bool(autogen) or None, "level_varies": bool(autogen) or None, "description": desc, "icon_path": ic, "icon": "@@img:%s@@" % slot_id if slot_id else None,
               "tags": tags, "abilities": abnames, "file": fname}
        if missing: report["notes"].append("%s: abilities not defined in the files: %s" % (name, missing))
        items.append(rec)
    ids = {r["id"] for r in items}
    for r in items:
        if r["carry_over"] and r["carry_over"] not in ids: r["carry_over"] = None   # "NGP X" is the carry-over copy of X, when X is in the data
    for path, names in sorted(missing_icons.items()): report["notes"].append("icon file missing (%d items, e.g. %s): %s" % (len(names), names[0], path))
    report["items_without_icon_by_set"] = dict(Counter((r["set"] or r["group"]) for r in items if not r["icon"]))
    report["unresolved_stat_labels"] = {k: sorted(v)[:3] for k, v in sorted(g.unresolved.items())}
    return items, icons, report


def build(game_dir):
    strings = w3dec.decode(str(Path(game_dir) / "en.w3strings")); sc = Scripts(game_dir); per, icons, notes, unresolved, dup = {}, {}, [], {}, {}
    games = {}
    for rs in RULESETS:
        if rs == "ng_plus" and not any((Path(game_dir) / "bundles" / b).is_file() for b, _ in PACKAGES): continue
        g = games[rs] = Game(game_dir, rs, strings); items, ic, rep = build_ruleset(g, sc); per[rs] = items; icons.update(ic)
        notes += ["[%s] %s" % (rs, n) for n in rep["notes"]]; unresolved.update(rep["unresolved_stat_labels"]); dup[rs] = rep["duplicate_item_definitions"]
        notes += ["[%s] XML file the parser could not read (not needed: nothing in it is used): %s" % (rs, f) for f in rep["parse_failures"]]
    # one record per distinct item: identical in both rulesets -> one record with rulesets [ng, ng_plus]
    merged = {}
    for rs, items in per.items():
        for r in items:
            key = (r["id"], json.dumps(r, sort_keys=True))
            if key in merged: merged[key]["rulesets"].append(rs)
            else: merged[key] = dict(r, rulesets=[rs])
    items = list(merged.values())
    for rs in per:
        seen = [r["id"] for r in items if rs in r["rulesets"]]
        if len(seen) != len(set(seen)): sys.exit("two different items called the same in ruleset %s" % rs)
    items.sort(key=lambda r: (ORDER[r["slot"]], ["school", "quest_set", "dlc", "relic", "crossbow", "bolt", "mask"].index(r["group"]), r["set"] or "", r["tier"] or 0, r["id"], r["rulesets"]))
    sets_out, bonus_all = {}, {}
    for rs, g in games.items(): bonus_all[rs], set_rules = set_bonuses(g, sc)
    for s, name, kind, tag, _ in SETS:
        sets_out[s] = {"name": name, "kind": kind, "tag": tag}
        for rs in per:
            mine = [r for r in items if r["set"] == s and rs in r["rulesets"]]
            sets_out[s][rs] = {"pieces": [r["id"] for r in mine], "slots": sorted({r["slot"] for r in mine}, key=ORDER.get), "tiers": sorted({r["tier"] for r in mine}),
                               "bonus_pieces": [r["id"] for r in mine if r["set_bonus_piece"]]}
        b = [bonus_all[rs].get(s, []) for rs in per]
        if any(x != b[0] for x in b): sys.exit("the set bonus of %s differs between rulesets: store them per ruleset" % s)
        sets_out[s]["bonuses"] = b[0]
    g0 = next(iter(games.values()))
    ag = {n: [{k: v for k, v in (("stat", c.tag), ("type", c.get("type")), ("min", num(c.get("min"))), ("max", num(c.get("max")) if c.get("max") is not None else None)) if v is not None}
              for c in a if c.get("min") is not None] for n, a in g0.abilities.items() if n.startswith("autogen_")}
    data = {"version": 4, "default_ruleset": "ng", "rulesets": {"ng": "first playthrough (gameplay/items, gameplay/abilities)", "ng_plus": "New Game Plus (the *_plus folders); 'NGP X' items are the carry-over copies of X"},
            "slots": [{"id": s, "category": c, "label": l, "kind": k} for s, c, l, k in SLOTS], "sets": sets_out, "rules": rules(g0, sc, set_rules),
            "autogen": {"note": AUTOGEN_NOTE, "abilities": ag}, "items": items}
    report = {"notes": notes, "unresolved_stat_labels": unresolved, "duplicate_item_definitions": dup, "per_ruleset": {rs: len(v) for rs, v in per.items()},
              "items_without_icon_by_set": dict(Counter((r["set"] or r["group"]) for r in items if not r["icon"])), "parse_failures": []}
    return data, icons, report


# ---- set bonuses: a transcription of GetSetBonusTooltipDescription (playerWitcher.ws) with the values read from the ability XML and the texts from en.w3strings ----
PW = "game/player/playerWitcher.ws"; PT = "game/player/playerTypes.ws"; GP = "game/gameParams.ws"
# per set: [(bonus number, EISB constant, string key, [parameter...])]; a parameter is (ability, attribute, how) or ("pieces", 1) or ("literal", number)
#   how: add = valueAdditive (the XML min of a type add attribute), mult = valueMultiplicative; "x100" multiplies by 100, "-1" subtracts 1 first
BONUSES = {
    "lynx": [(1, "EISB_Lynx_1", "skill_desc_lynx_set_ability1", [("LynxSetBonusEffect", "duration", "add"), ("LynxSetBonusEffect", "lynx_dmg_boost", "add x100"), ("pieces", 1)]),
             (2, "EISB_Lynx_2", "skill_desc_lynx_set_ability2", [("setBonusAbilityLynx_2", "lynx_2_dmg_boost", "add x100"), ("setBonusAbilityLynx_2", "lynx_2_adrenaline_cost", "add")])],
    "gryphon": [(1, "EISB_Gryphon_1", "skill_desc_gryphon_set_ability1", [("GryphonSetBonusEffect", "duration", "add")]),
                (2, "EISB_Gryphon_2", "skill_desc_gryphon_set_ability2", [("GryphonSetBonusYrdenEffect", "trigger_scale", "add -1 x100"), ("GryphonSetBonusYrdenEffect", "staminaRegen", "mult x100"),
                                                                          ("GryphonSetBonusYrdenEffect", "spell_power", "mult x100"), ("GryphonSetBonusYrdenEffect", "gryphon_set_bns_dmg_reduction", "add x100")])],
    "bear": [(1, "EISB_Bear_1", "skill_desc_bear_set_ability1", [("setBonusAbilityBear_1", "quen_reapply_chance", "mult x100"), ("pieces", 1)]),
             (2, "EISB_Bear_2", "skill_desc_bear_set_ability2", [("setBonusAbilityBear_2", "quen_dmg_boost", "mult x100")])],
    # the script maps Wolf_1 to the ability2 text and Wolf_2 to the ability1 text (as written in GetSetBonusTooltipDescription)
    "wolf": [(1, "EISB_Wolf_1", "skill_desc_wolf_set_ability2", [("current", 1)]), (2, "EISB_Wolf_2", "skill_desc_wolf_set_ability1", [])],
    "red_wolf": [(1, "EISB_RedWolf_1", "skill_desc_red_wolf_set_ability1", []), (2, "EISB_RedWolf_2", "skill_desc_red_wolf_set_ability2", [("setBonusAbilityRedWolf_2", "amount", "add")])],
    "vampire": [(1, "EISB_Vampire", "skill_desc_vampire_set_ability1", [("setBonusAbilityVampire", "life_percent", "add"), ("pieces", 1)])],
    "netflix": [(1, "EISB_Netflix_1", "skill_desc_netflix_set_ability1", []), (2, "EISB_Netflix_2", "skill_desc_netflix_set_ability2", [])],
}


def fmt(x):
    x = round(x, 2)
    return str(int(x)) if x == int(x) else ("%g" % x)


def set_bonuses(g, sc):
    minor = sc.const(GP, "ITEMS_REQUIRED_FOR_MINOR_SET_BONUS"); major = sc.const(GP, "ITEMS_REQUIRED_FOR_MAJOR_SET_BONUS")
    out = {}; start = sc.find(PW, r"function GetSetBonusTooltipDescription")
    for sid, specs in BONUSES.items():
        out[sid] = []
        for nr, eisb, key, params in specs:
            text = g.text(key)
            if text is None: sys.exit("no string %s for %s" % (key, eisb))
            values, per_piece, parts = [], None, []
            for p in params:
                if p[0] == "current": per_piece = p[1]; parts.append("{current}")                  # one parameter: p[1] times the pieces worn
                elif p[0] == "literal": v = p[1]; parts.append(fmt(v)); values.append(v)
                elif p[0] == "pieces": per_piece = values[-1]; parts.append("{current}")        # "Current bonus": the value of the parameter before it times the pieces worn
                else:
                    kind, lo, hi = g.ability_value(p[0], p[1]); v = lo; how = p[2].split()
                    if "-1" in how: v -= 1
                    if "x100" in how: v *= 100
                    parts.append(fmt(v)); values.append(v)
            for part in parts: text = text.replace("$S$", part, 1)                              # StrReplace replaces the first $S$ each time (localizedContent.ws)
            if "$S$" in text: sys.exit("%s: %d parameters do not fill the text of %s" % (eisb, len(params), key))
            src = [sc.ref(PW, r"case %s:\s*tempString" % eisb, start), sc.ref(PT, r"\b%s\b" % eisb)]
            for p in params:
                if p[0] not in ("literal", "pieces", "current"):
                    pkg, kind, fname = g.ability_file[p[0]]; lines = g.files[(pkg, kind, fname)].decode("utf-8-sig").split("\n")
                    src.append("%s/%s/%s:%d" % (pkg.replace(".bundle", ""), kind, fname, next(i + 1 for i, l in enumerate(lines) if 'name="%s"' % p[0] in l)))
            out[sid].append({"pieces": minor if nr == 1 else major, "bonus": eisb, "text": text, "string": key, "values": [fmt(v) for v in values],
                             "per_piece": fmt(per_piece) if per_piece is not None else None, "source": sorted(set(src))})
    rules_ = {"minor_pieces": minor, "major_pieces": major, "counted_pieces_tag": "SetBonusPiece",
              "source": [sc.ref(GP, "ITEMS_REQUIRED_FOR_MINOR_SET_BONUS = "), sc.ref(GP, "ITEMS_REQUIRED_FOR_MAJOR_SET_BONUS = "), sc.ref(GP, "ITEM_SET_TAG_BONUS = "), sc.ref(PW, r"function UpdateItemSetBonuses"),
                       sc.ref(PW, r"function IsSetBonusActive"), sc.ref(PW, r"function GetSetBonusTooltipDescription")]}
    return out, rules_


def rules(g, sc, set_rules):
    """How the game shows and computes equipment numbers, with the script lines it comes from (verified to exist when this runs)."""
    IC = "game/components/inventoryComponent.ws"; GT = "game/gui/_old/components/guiTooltipComponent.ws"
    return {
        "set_bonus": {"minor_pieces": set_rules["minor_pieces"], "major_pieces": set_rules["major_pieces"], "counted_pieces_tag": "SetBonusPiece",
                      "text": "A piece counts only if it has the SetBonusPiece tag and its set tag; at 3 pieces the first bonus is active, at 6 the second (Vampire has one bonus at 3). See sets[*].bonuses.",
                      "source": set_rules["source"]},
        "required_level": {"where": "inventoryComponent.GetItemLevel, shown as 'Requires level N' (red when above the player's level)",
                           "armor": "floor(1 + (armor - 25) / 5); boots and trousers: floor(1 + (armor - 5) / 2); gloves: floor(1 + (armor - 1) / 2)",
                           "steel sword": "ceil(1 + (1 + sum(damage_i - 1) - 25) / 8) over slashing, bludgeoning, rending, elemental, fire, silver, piercing",
                           "silver sword": "ceil(1 + (1 + sum(damage_i - 1) - 90) / 10) over silver, bludgeoning, rending, elemental, fire, piercing",
                           "crossbow": "by attack_power multiplier: >1.01 2, >1.1 4, >1.2 8, >1.3 11, >1.4 15, >1.5 19, >1.6 22, >1.7 25, >1.8 27, >1.9 32",
                           "bolts": "a fixed level per bolt name, minus 14/10/6/4 for quality 5/4/3/2",
                           "then": "minus 1; at least 1; set gear (quality 5) minus 2, relic (4) minus 1; at least 1; EP1-tagged relic or set gear minus 1; 'OlgierdSabre' minus 3 (capped at the player's maximum level)",
                           "assumption": "an attribute the item does not define counts as 0 (the engine default is not in the scripts); not computed for Autogen items",
                           "source": [sc.ref(IC, r"function GetItemLevel\(item"), sc.ref("game/gameParams.ws", r"function GetItemLevel\(itemCategory"), sc.ref(IC, r"function GetItemLevelColorById")]},
        "primary_stat": {"steel sword": "SlashingDamage, label 'Damage'", "silver sword": "SilverDamage, label 'Damage'", "armor, gloves, boots, trousers": "armor",
                         "crossbow": "'Damage' = the equipped bolt's primary stat (Bodkin Bolt PiercingDamage if none) x the crossbow's attack_power multiplier",
                         "shown": "rounded to a whole number; steel swords never list SilverDamage and silver swords never list SlashingDamage in the stat list",
                         "source": [sc.ref(IC, r"function GetItemPrimaryStatImplById"), sc.ref(IC, r"function GetItemTooltipAttributes"), sc.ref(GT, r"function GetCrossbowPrimatyStat")]},
        "stat_list": {"value": "a multiplicative value is a percentage (value x 100, rounded, 'NN %'); focus_gain is shown as is; other values are rounded to a whole number",
                      "order_color_percent": "the order, colour and percentage flag of each line come from gameplay/globals/tooltip_settings.csv, which is NOT in the files we have",
                      "source": [sc.ref(GT, r"function AddItemStats"), sc.ref(IC, r"function GetItemTooltipAttributes")]},
        "quality": {"1": "common", "2": "masterwork", "3": "magic", "4": "relic", "5": "set (witcher gear)", "source": [sc.ref(GT, r"function GetItemRarityDescription")]},
        "ng_plus": {"text": "Two rulesets. ng = first playthrough (gameplay/items): the witcher gear tiers Basic to Grandmaster, levels 17 to 40; only the top tier carries SetBonusPiece. ng_plus = New Game Plus (the *_plus folders): "
                            "the same ids are redefined as 'legendary' gear (levels 47 to 70, every tier counts for set bonuses) and 'NGP X' are carry-over copies of the first-playthrough items (same stats as X in ng); NewGamePlusReplaceItem swaps X for 'NGP X' when a "
                            "New Game Plus starts. The tooltip also adds (NG+ level - minimum NG+ level) x the autogen_fixed damage/armour step to the primary stat. Both rulesets also have a few items named 'Legendary ...' (e.g. Manticore, level 70).",
                    "source": [sc.ref(GT, r"function IncreaseNGPPrimaryStatValue"), sc.ref(PW, r"function NewGamePlusReplaceNetflixSet")]},
        "autogen": {"text": AUTOGEN_NOTE}}


def split(data):
    """{file name: text}: data/items.json (sets, rules, slots: small) and one data/items_<ruleset>.json per ruleset (its items, loaded on demand: the UI never embeds them in index.html)."""
    meta = {k: v for k, v in data.items() if k != "items"}; out = {"items.json": json.dumps(meta, indent=1, ensure_ascii=False) + "\n"}
    for rs in data["rulesets"]:
        recs = [{k: v for k, v in r.items() if k != "rulesets"} for r in data["items"] if rs in r["rulesets"]]
        out["items_%s.json" % rs] = json.dumps({"ruleset": rs, "items": recs}, indent=1, ensure_ascii=False) + "\n"
    return out


def summarise(data, report):
    items = data["items"]; out = ["%d distinct items (%s records per ruleset)" % (len(items), report["per_ruleset"]), "per slot: " + ", ".join("%s %d" % (s["id"], sum(r["slot"] == s["id"] for r in items)) for s in data["slots"])]
    out.append("per group: " + ", ".join("%s %d" % (k, v) for k, v in sorted(Counter(r["group"] for r in items).items())))
    out.append("in rulesets: " + ", ".join("%s %d" % ("+".join(k), v) for k, v in sorted(Counter(tuple(r["rulesets"]) for r in items).items())))
    for s, info in data["sets"].items():
        for rs in report["per_ruleset"]:
            by = Counter((r["tier"]) for r in items if r["set"] == s and rs in r["rulesets"]); d = info[rs]
            out.append("set %-16s %-9s %-26s %3d pieces (%2d count for the bonus), %d bonuses; tiers: %s" % (s, rs, info["name"], len(d["pieces"]), len(d["bonus_pieces"]), len(info["bonuses"]),
                                                                                                     ", ".join("T%s=%d" % (t, c) for t, c in sorted(by.items(), key=lambda kv: kv[0] or 0))))
    out.append("quality: " + ", ".join("%s %d" % (k, v) for k, v in sorted(Counter(str(r["quality_name"]) for r in items).items())))
    out.append("autogen items: %d; with a required level: %d" % (sum(bool(r["autogen"]) for r in items), sum(r["required_level"] is not None for r in items)))
    out.append("items without an icon: %d %s" % (sum(r["icon"] is None for r in items), report["items_without_icon_by_set"]))
    out.append("duplicate item definitions across packages: %s" % report["duplicate_item_definitions"])
    out.append("stat labels that do not resolve in the strings: %s" % report["unresolved_stat_labels"])
    out.extend("note: " + n for n in report["notes"][:25]); out.append("(%d notes in all)" % len(report["notes"]))
    return "\n".join(out)


SLOT_IDS_WITH_PLACEHOLDER = [s for s, _, _, _ in SLOTS]
ICON_SLOT = {}


def update_manifest(icons):
    """art/manifest.json: one slot per icon (the game build reads <art-dir>/<id>.png); the public build shows the drawn placeholder of the item's slot."""
    p = ROOT / "art" / "manifest.json"; m = json.loads(p.read_text())
    m = {k: v for k, v in m.items() if not k.startswith("items/")}
    for sid in SLOT_IDS_WITH_PLACEHOLDER: m["items/ph-" + sid] = {"game": "png", "placeholder": "png"}
    for sid in sorted(icons): m[sid] = {"game": "png", "placeholder": "png", "placeholder_as": "items/ph-" + ICON_SLOT[sid]}
    p.write_text(json.dumps(m, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", required=True); ap.add_argument("--art-dir", help="copy the icons to <art-dir>/items/ and register them (the private art folder, never this repo)")
    ap.add_argument("--check", action="store_true", help="verify data/items*.json against the game files; write nothing")
    ap.add_argument("--missing-icons", help="also write the icon files that items refer to but inventory/ lacks (the list tools/pc/extract_on_pc.py reads)")
    a = ap.parse_args()
    data, icons, report = build(a.game_dir); files = split(data)
    for r in data["items"]:
        if r["icon"]: ICON_SLOT[r["icon"][len("@@img:"):-2]] = r["slot"]
    used = {r["icon"][len("@@img:"):-2] for r in data["items"] if r["icon"]}; icons = {k: v for k, v in icons.items() if k in used}   # icons of dropped items are not needed
    print(summarise(data, report))
    if a.missing_icons:
        miss = defaultdict(set)
        for r in data["items"]:
            if not r["icon"] and r["icon_path"]: miss[r["icon_path"].replace("\\", "/")].add(r["id"])
        Path(a.missing_icons).write_text("# item icons the game data refers to that are not in inventory/ (path, then the items using it); read by tools/pc/extract_on_pc.py\n" +
                                         "".join("%s\t%s\n" % (k, "; ".join(sorted(v)[:6])) for k, v in sorted(miss.items())), encoding="utf-8")
        print("wrote %s (%d icon files)" % (a.missing_icons, len(miss)))
    if a.check:
        bad = [n for n, t in files.items() if not (ROOT / "data" / n).is_file() or (ROOT / "data" / n).read_text(encoding="utf-8") != t]
        if bad: sys.exit("%s is not what the game files produce: re-run without --check" % ", ".join("data/" + n for n in bad))
        print("data/items*.json is up to date"); return
    for n, t in files.items(): (ROOT / "data" / n).write_text(t, encoding="utf-8")
    update_manifest(icons)
    print("wrote %s; %d icon slots in art/manifest.json" % (", ".join("data/%s (%d KB)" % (n, len(t) // 1024) for n, t in files.items()), len(icons)))
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
