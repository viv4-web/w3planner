#!/usr/bin/env python3
"""The planner's consumables (v28): potions, decoctions, oils and bombs, from ~/research/consumables-v28.json (made from the game's item XML and en.w3strings).

    python tools/make_consumables.py --research ~/research/consumables-v28.json --game-dir ~/incoming/gamedata --art-dir ~/work/w3planner-art

Writes data/consumables.json (loaded on demand by the page, like the equipment lists), data/consumable_ids.json (the APPEND-ONLY registry: id -> number 1..4095, what a share
link's c1 segment stores; none is ever reused or renumbered), the icon slots `cons/<folder>/<file>` in art/manifest.json (and, with --art-dir, the icons and the four drawn placeholders
copied to <art-dir>/cons/ plus their SHA-1 fingerprints in tools/game-art-hashes.txt). In scope: every potion, decoction, oil and bomb a player can put in a slot. Out: food and drink,
quest and special potions (tags Quest/NoShow), NoEquip items (Potion of Restoration), paint balls and other quest bombs, the Training bomb and items that are not Petard bombs
(the Pheromone bomb is a quick slot item)."""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import w3dec  # noqa: E402

ORDER = ["potion", "decoction", "bomb", "oil"]
TIER_NAMES = {0: "", 1: "Normal", 2: "Enhanced", 3: "Superior"}
CAT_LABEL = {"potion": "Potion", "decoction": "Decoction", "bomb": "Bomb", "oil": "Oil"}
REGISTRY = ROOT / "data" / "consumable_ids.json"


def sanitise(s):
    return re.sub(r"[^a-z0-9_.\-]", "", s.lower().replace(" ", "_").replace("'", ""))


def in_scope(i):
    t = set(i["tags"])
    if i["category"] not in ORDER or t & {"Quest", "NoShow", "NoEquip"}: return False
    if i["category"] == "bomb": return "Petard" in t and i["id"] != "Tutorial Bomb"
    if i["category"] in ("potion", "decoction"): return "Potion" in t
    return True


def num(v):
    f = float(v); return int(f) if f == int(f) else round(f, 4)


def parse(v):
    """'add 20' | 'mult 0.25' | 'add 4; mult 1' | 'add 100..250' -> [(type, value or (lo, hi))]"""
    out = []
    for part in str(v).split(";"):
        m = re.match(r"\s*(add|mult|base)?\s*(-?\d+(?:\.\d+)?)(?:\.\.(-?\d+(?:\.\d+)?))?\s*$", part)
        if m: out.append((m.group(1) or "add", num(m.group(2)) if not m.group(3) else (num(m.group(2)), num(m.group(3)))))
    return out


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", (t or "").replace("<br>", " "))).strip() or None


def stat_lines(it, L, ruleset_stats):
    """The effect numbers the game's data gives, without charges, duration and toxicity (those have their own fields)."""
    out = []
    for k, v in ruleset_stats.items():
        if k in ("quality", "level", "ammo", "duration", "toxicity", "toxicity_offset", "tags", "ability_disable_duration") or "resist_reduction" in k: continue
        p = parse(v)
        if not p: continue
        t, x = p[0]
        label = L("attribute_name_" + k.lower()) or {"burning_chance": "Burning chance", "explosionFireDamage": "Explosion fire damage", "ignoreArmor": "Ignores armor", "duration_out_of_cloud": "Effect duration outside the cloud"}.get(k, k)
        out.append({"label": label, "v": x, "pct": t == "mult" or k == "burning_chance"})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--research", required=True); ap.add_argument("--game-dir", required=True); ap.add_argument("--art-dir")
    a = ap.parse_args(); game = Path(a.game_dir).expanduser()
    src = [i for i in json.loads(Path(a.research).expanduser().read_text())["items"] if in_scope(i)]
    strs, keys = w3dec.decode(str(game / "en.w3strings")); L = lambda k: strs.get(keys.get(w3dec.h(k))) if k else None
    src.sort(key=lambda i: (ORDER.index(i["category"]), i["family"], i["tier_number"] or 0, i["id"]))
    reg = json.loads(REGISTRY.read_text())["ids"] if REGISTRY.is_file() else {}
    for i in src:
        if i["id"] not in reg: reg[i["id"]] = max(reg.values(), default=0) + 1
    if max(reg.values()) > 4095 or len(set(reg.values())) != len(reg): sys.exit("consumable id registry out of range or not unique")
    inv = game / "inventory"; icons, items, missing = {}, [], []
    for i in src:
        st = {k: v for k, v in i["stats"].items()}
        tier = i["tier_number"] or 0
        if i["category"] == "decoction" and i["family"] != "White Raffards Decoction": tier = 0
        tox = next((x[1] for x in parse(st.get("toxicity", "")) if x[0] == "add"), None) if "toxicity" in st else None
        dur = next((x[1] for x in parse(st.get("duration", "")) if x[0] == "add"), None) if "duration" in st else None
        ch = next((x[1] for x in parse(st.get("ammo", "")) if x[0] == "add"), None) if "ammo" in st else None
        rec = {"id": i["id"], "n": reg[i["id"]], "name": i["name"], "cat": i["category"], "fam": i["family"], "tier": tier, "tier_name": TIER_NAMES[tier] if tier else None,
               "tox": tox, "dur": dur, "ch": ch, "desc": clean(i["description"]), "stats": stat_lines(i, L, st), "tags": i["tags"], "dlc": i["dlc"]}
        if i["category"] == "decoction" and "toxicity_offset" in st: rec["tox_offset"] = next((x[1] for x in parse(st["toxicity_offset"]) if x[0] == "add"), None)
        if i["category"] == "oil": rec["steel"] = "SteelOil" in i["tags"]; rec["silver"] = "SilverOil" in i["tags"]
        if i.get("ng_plus_differs"):
            ngp = i["ng_plus_differs"]; rec["ngp"] = {"stats": stat_lines(i, L, ngp), "dur": next((x[1] for x in parse(ngp.get("duration", "")) if x[0] == "add"), None) if "duration" in ngp else None,
                                                    "ch": next((x[1] for x in parse(ngp.get("ammo", "")) if x[0] == "add"), None) if "ammo" in ngp else None}
        ic = i.get("icon") or {}; f = ic.get("file")
        if f:
            p = Path(f.replace("~", str(Path.home()))); rel = p.relative_to(inv); sid = "cons/%s/%s" % (sanitise(rel.parent.name), sanitise(rel.stem)); icons[sid] = (p, i["category"])
            rec["icon"] = "@@img:%s@@" % sid
        else:
            rec["icon"] = "@@img:cons/ph-%s@@" % i["category"]; missing.append(i["id"])
        rec["icon_path"] = ic.get("path_in_game"); items.append(rec)
    meta = {"version": 1, "note": "from the game's item XML and strings (tools/make_consumables.py); ids are numbers in data/consumable_ids.json, append-only", "categories": {k: CAT_LABEL[k] for k in ORDER},
            "tiers": {"1": "Normal", "2": "Enhanced", "3": "Superior"}}
    out = dict(meta, items=[{k: v for k, v in r.items() if k not in ("icon_path", "tags", "dlc") and v not in (None, [], "")} for r in items])
    (ROOT / "data" / "consumables.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    REGISTRY.write_text(json.dumps({"version": 1, "note": "append-only: never reuse or renumber (share links store these numbers)", "ids": dict(sorted(reg.items(), key=lambda kv: kv[1]))}, indent=0, ensure_ascii=False) + "\n", encoding="utf-8")
    mp = ROOT / "art" / "manifest.json"; m = json.loads(mp.read_text()); m = {k: v for k, v in m.items() if not k.startswith("cons/")}
    for k in ORDER: m["cons/ph-" + k] = {"game": "png", "placeholder": "png"}
    for sid, (_, cat) in sorted(icons.items()): m[sid] = {"game": "png", "placeholder": "png", "placeholder_as": "cons/ph-" + cat}
    mp.write_text(json.dumps(m, indent=1) + "\n")
    if a.art_dir:
        ad = Path(a.art_dir); hp = ROOT / "tools" / "game-art-hashes.txt"; lines = hp.read_text().splitlines(); have = {l.split()[0] for l in lines if l.strip() and not l.startswith("#")}; add = []
        for sid, (p, _) in sorted(icons.items()):
            d = ad / (sid + ".png"); d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, d); h = hashlib.sha1(d.read_bytes()).hexdigest()
            if h not in have: add.append("%s  %s.png" % (h, sid)); have.add(h)
        for k in ORDER:                                                       # the drawn placeholders: the game build shows them for an item without an icon
            d = ad / "cons" / ("ph-%s.png" % k); d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / "art" / "placeholder" / "cons" / ("ph-%s.png" % k), d)
        hp.write_text("\n".join(lines + add) + "\n")
    import collections
    print("%d consumables: %s; %d registry numbers (max %d); %d icon slots; no icon: %s" % (len(items), dict(collections.Counter(r["cat"] for r in items)), len(reg), max(reg.values()), len(icons), missing))


if __name__ == "__main__":
    main()
