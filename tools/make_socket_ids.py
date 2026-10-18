#!/usr/bin/env python3
"""The planner's runes and glyphs (v36), from the game's item and ability XML of both rulesets and en.w3strings.

    python tools/make_socket_ids.py --game-dir ~/incoming/gamedata --art-dir ~/work/w3planner-art

Writes data/socket_ids.json: the APPEND-ONLY registry (id -> number 1..4095, 0 = empty socket; what a share link's r1 segment stores; none is ever reused or renumbered, CLAUDE.md
rule 10) with each rune's and glyph's display name, kind, family, tier and its effect values for the first playthrough (ng) and New Game Plus (ngp). Only names and the stat labels the
planner already uses (attribute_name_<stat>) are kept; no description text. With --art-dir it copies the icons the server has to <art-dir>/sock/<file>.png (never committed), adds their
slots to art/manifest.json (public and offline builds show one drawn placeholder per kind) and SHA-1 fingerprints to tools/game-art-hashes.txt, and lists the icons the server lacks
(those entries show a lettered disc). --check verifies the committed file and prints the report.
Sources: items/def_item_upgrades.xml (xml.bundle), items/def_item_ep1_upgrades.xml (ep1.bundle); the ability named by the item's <ability> list ("Rune dazhbog _Stats"), per ruleset
(a *_plus file replaces the base file, extract_items.xml_sources). Which gear takes which: enhancement_slots and enhancement_kind in data/items_*.json (weapons rune, armour glyph)."""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "tools" / "extract"))
import extract_items as E  # noqa: E402
import w3dec  # noqa: E402

REGISTRY = ROOT / "data" / "socket_ids.json"
TIERS = {"lesser": 1, "normal": 2, "greater": 3}
# the one ability that makes a mutually exclusive "rarity" change, not a stat (Glyph of Infusion): kept as an item with no effect
GENERIC = {"Relic _Stats", "Magic _Stats"}


def parse(b):
    try: return ET.fromstring(b.decode("utf-8-sig").replace("</schematic>>", "</schematic>"))
    except ET.ParseError: return None


def walk(game, rs):
    items, abil = {}, {}
    for (pk, kind, name), b in E.xml_sources(game, rs).items():
        r = parse(b)
        if r is None: continue
        for it in r.iter("item"):
            n = it.get("name")
            if n and re.match(r"(Rune|Glyph) ", n) and not n.endswith(" schematic"): items[n] = it
        for a in r.iter("ability"):
            if re.match(r"(Rune|Glyph)", a.get("name", "")): abil[a.get("name")] = a
    return items, abil


def effects(a):
    """[(stat, type, value)] of an ability node: min (and max when different) of each stat; an <X is_ability> child is the effect the game applies, not a stat."""
    out = []
    if a is None: return out
    for c in a:
        if c.tag == "tags" or c.get("min") is None: continue
        num = lambda x: int(x) if float(x) == int(float(x)) else float(x)
        lo, hi = num(c.get("min")), num(c.get("max", c.get("min")))
        out.append([c.tag, c.get("type", "add"), lo if lo == hi else [lo, hi]])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", required=True); ap.add_argument("--art-dir"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args(); game = Path(a.game_dir).expanduser()
    R = {rs: walk(game, rs) for rs in ("ng", "ng_plus")}
    strs, keys = w3dec.decode(str(game / "en.w3strings")); L = lambda k: strs.get(keys.get(w3dec.h(k))) if k else None
    names = sorted(set(R["ng"][0]) | set(R["ng_plus"][0]))
    reg = {r["id"]: r["n"] for r in json.loads(REGISTRY.read_text())["items"]} if REGISTRY.is_file() else {}
    for n in sorted(names, key=lambda s: (s.startswith("Glyph"), s)):      # first generation: runes 1 to 32, glyphs 33 to 61; later ids are appended
        if n not in reg: reg[n] = max(reg.values(), default=0) + 1
    if max(reg.values()) > 4095 or len(set(reg.values())) != len(reg): sys.exit("socket id registry out of range or not unique")
    inv = game / "inventory"; out, icons, missing = [], {}, []
    for n in sorted(names, key=lambda s: reg[s]):
        both = [r for r in ("ng", "ng_plus") if n in R[r][0]]
        it = R[both[0]][0][n]; kind = "rune" if n.startswith("Rune") else "glyph"
        fam = re.match(r"(?:Rune|Glyph) (\w+)", n).group(1); tier = "lesser" if n.endswith(" lesser") else "greater" if n.endswith(" greater") else "normal"
        ab = [x.text for x in it.iter("a")]; fx = {}
        for r, k in (("ng", "ng"), ("ng_plus", "ngp")):
            if r not in both: continue
            node = R[r][1].get(ab[0]) if ab else None
            fx[k] = [] if ab and ab[0] in GENERIC else effects(node)
        rec = {"id": n, "n": reg[n], "name": L(it.get("localisation_key_name")), "kind": kind, "fam": fam, "tier": TIERS[tier], "tier_name": tier.capitalize(), "fx": fx["ng"]}
        if "ng_plus" in both and fx["ngp"] != fx["ng"]: rec["fxp"] = fx["ngp"]
        if both != ["ng", "ng_plus"]: rec["only"] = both[0]
        ic = (it.get("icon_path") or "").replace("icons/inventory/", "")
        p = inv / ic
        if ic and p.is_file():
            sid = "sock/" + re.sub(r"[^a-z0-9_.\-]", "", p.stem.lower()); icons[sid] = (p, kind); rec["icon"] = "@@img:%s@@" % sid
        else:
            missing.append(n)
        out.append(rec)
    stats = sorted({e[0] for r in out for e in r["fx"] + r.get("fxp", [])})
    lbl = {}
    for s in stats:
        t = L("attribute_name_" + s.lower()) or L("attribute_name_" + s)
        if t: lbl[s] = t
    data = {"version": 1, "note": "from the game's item and ability XML (tools/make_socket_ids.py); n is append-only: never reuse or renumber (share links store these numbers)",
            "labels": lbl, "items": out}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    if a.check:
        ok = REGISTRY.is_file() and REGISTRY.read_text() == text
        print("data/socket_ids.json %s the game files" % ("matches" if ok else "DIFFERS from"))
        if not ok: sys.exit(1)
    else:
        REGISTRY.write_text(text, encoding="utf-8")
        mp = ROOT / "art" / "manifest.json"; m = json.loads(mp.read_text()); m = {k: v for k, v in m.items() if not k.startswith("sock/")}
        for k in ("rune", "glyph"): m["sock/ph-" + k] = {"game": "png", "placeholder": "png"}
        for sid, (_, kind) in sorted(icons.items()): m[sid] = {"game": "png", "placeholder": "png", "placeholder_as": "sock/ph-" + kind}
        mp.write_text(json.dumps(m, indent=1) + "\n")
        if a.art_dir:
            ad = Path(a.art_dir).expanduser(); hp = ROOT / "tools" / "game-art-hashes.txt"; lines = hp.read_text().splitlines(); have = {l.split()[0] for l in lines if l.strip() and not l.startswith("#")}; add = []
            for sid, (p, _) in sorted(icons.items()):
                d = ad / (sid + ".png"); d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, d); h = hashlib.sha1(d.read_bytes()).hexdigest()
                if h not in have: add.append("%s  %s.png" % (h, sid)); have.add(h)
            for k in ("rune", "glyph"):
                d = ad / "sock" / ("ph-%s.png" % k); d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / "art" / "placeholder" / "sock" / ("ph-%s.png" % k), d)
            hp.write_text("\n".join(lines + add) + "\n")
    import collections
    print("%d entries: %s; registry max %d; %d icons on the server; no icon (lettered disc): %s" % (len(out), dict(collections.Counter(r["kind"] for r in out)), max(reg.values()), len(icons), missing))


if __name__ == "__main__":
    main()
