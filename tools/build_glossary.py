#!/usr/bin/env python3
"""Build the Glossary content (bestiary, characters, tutorials, books) from the game's own files.

    python tools/build_glossary.py --out ~/work/w3planner-art/glossary           (the defaults point at ~/incoming on the server)
    python tools/build_glossary.py --check --out ~/work/w3planner-art/glossary   verify an existing build, write nothing

The output is GAME CONTENT (text and pictures): like the game art it lives in the private art folder, is never committed, and
tools/build.py copies it into the live build (docs/GLOSSARY.md has the file formats). The public and offline builds contain none of it.

Inputs (all read-only):
  --journal-zip   w3planner-journal.zip made on the PC by tools/pc/extract_journal_on_pc.py: every .journal file of every bundle
  --strings       en.w3strings (decoded with tools/extract/w3dec.py)
  --game-dir      ~/incoming/gamedata: bundles/*.bundle (item XML of the base game and both expansions, for the books), dlc-xml/, inventory/ (icons)
  --image-zips    the zips made by tools/pc/extract_on_pc.py --list tools/pc/glossary-images-<tab>.txt (DDS pictures; the lists are made from the zip's texture index)
  data/consumables.json (this repo): the bestiary's susceptibility chips link to the items it has

What it does, and the decisions behind it (Vivek):
  * bestiary: every creature with a name and text (138 raw, the 9 stubs have none); grouped by the game's category (a DLC creature joins the base group its
    "virtual group" file links to); every description stage in the game's order (the `children` array); susceptibility = itemsUsedAgainstCreature
  * characters: all 116, grouped by pack (base game, Hearts of Stone, Blood and Wine)
  * tutorials: those with a name and text, platform variants (_pad, _ps4, ...) folded into the PC text; pictures only for the 10 real ones
  * books: readable items (not schematics or recipes) that have a body (key <name>_text, or the item id, or a one-line item_desc) + the paintings, maps and sketches
  * pictures: DDS -> WebP q80 with alpha; a flat-colour picture (the game's orange "TODO" tutorial placeholder) is never used
"""
import argparse, collections, hashlib, io, json, re, sys, unicodedata, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import bundle as W3B, cr2w, w3dec   # noqa: E402

HOME = Path.home()
PACKS = {"startup": "base", "bob": "baw", "ep1": "hos", "dlc0": "dlc0"}
PACK_NAME = {"base": "Base game", "hos": "Hearts of Stone", "baw": "Blood and Wine", "dlc0": "Base game"}
SIGNS = {"Aard", "Igni", "Yrden", "Quen", "Axii"}
SCHEMATIC = {"crafting_schematic", "alchemy_recipe", "cooking_recipe"}
# the ten Switch motion-pattern pictures belong to the tutorials of the same name (paired by name, decision by Vivek; the game reads the picture natively)
PICTURE_PAIRS = {"tutorialpatternbombthrow": "TutorialJournalMotionPatternBombs", "tutorialpatterncallhorse": "TutorialJournalMotionPatternHorseSummon",
                 "tutorialpatterncrossbow": "TutorialJournalMotionPatternCrossbow", "tutorialpatternhorseacceleration": "TutorialJournalMotionPatternHorseAcceleration",
                 "tutorialpatternimage": "TutorialJournalMotionPatternDetails", "tutorialpatternsignactivation": "TutorialJournalMotionPatternSignCast",
                 "tutorialpatternstophorse": "TutorialJournalMotionPatternHorseStop", "tutorialpatternuseprimaryconsumable": "TutorialJournalMotionPatternPotion1",
                 "tutorialpatternusesecondaryconsumable": "TutorialJournalMotionPatternPotion2"}
EXPECT = {"bestiary": 129, "characters": 116, "tutorial": 508, "books": 833, "paintings": 44}   # the spike's totals, corrected: 508 tutorials (the 527 counted 19 with no name or text), 833 books (Beledal's grandfather has a body but no title); see docs/GLOSSARY.md


def norm_key(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()


def log(*a): print(*a, file=sys.stderr)


# ---------------------------------------------------------------- journals
class Journals:
    def __init__(self, zpath, strs):
        self.strs, self.entries, self.groups, self.group_files = strs, [], {}, {}
        z = zipfile.ZipFile(zpath)
        for name in sorted(z.namelist()):
            low = name.lower()
            if not low.endswith(".journal"): continue
            bm = re.search(r"([a-z0-9]+)\.bundle", low.split("/")[1]); pack = PACKS.get(bm.group(1)) if bm else None
            tab = next((k for k in ("bestiary", "characters", "tutorial") if "/journal/%s/" % k in low), None)
            if not tab or not pack: continue
            self.read(z.read(name), pack, tab, name.rsplit("/", 1)[-1][:-8])

    def text(self, p):
        i = cr2w.u32(p, 0); return i, self.strs.get(i)

    def read(self, data, pack, tab, stem):
        c = cr2w.CR2W(data); ch = c.chunks; P = lambda k: {n: d for n, t, d in k["props"]}
        def kids(k):
            p = P(k).get("children")
            return c.ptrs(p) if p else [x["idx"] for x in ch if x["parent"] == k["idx"]]
        def stages(k, group, entry):
            """[(string id, text)] of the description entries below k, in the game's order: the bestiary menu inserts each active entry before the first one with a
            greater `order` (glossaryBestiaryMenu.ws GetDescription), so it is ascending `order`, ties in child order; the character menu uses child order."""
            out = []
            def one(d):
                q = P(d)
                if "description" in q: out.append((cr2w.u32(q["order"], 0) if "order" in q else 0, self.text(q["description"])))
            for ci in kids(k):
                g = ch[ci - 1]
                if group and g["cls"] == group:
                    for di in kids(g):
                        if ch[di - 1]["cls"] == entry: one(ch[di - 1])
                elif g["cls"] == entry: one(g)
            if group: out.sort(key=lambda x: x[0])      # stable
            return [t for _, t in out]
        for k in ch:
            p = P(k); cl = k["cls"]
            if "guid" in p and cl.endswith("Group"):
                self.groups[p["guid"].hex()] = {"cls": cl, "name": self.strs.get(self.text(p["name"])[0]) if "name" in p else None, "file": stem,
                                                "link": c.string(p["linkedObjectPath"]) if "linkedObjectPath" in p else None}
            if cl not in ("CJournalCreature", "CJournalCharacter", "CJournalTutorial"): continue
            e = {"pack": pack, "tab": tab, "file": stem, "id": c.string(p["baseName"]), "tag": c.cname(p["uniqueScriptIdentifier"]), "parent": p["parentGuid"].hex() if "parentGuid" in p else None,
                 "name": self.text(p["name"])[1] if "name" in p else None, "image": c.string(p["image"]) if "image" in p else None}
            if cl == "CJournalCreature":
                e["weak"] = c.cnames(p["itemsUsedAgainstCreature"]) if "itemsUsedAgainstCreature" in p else []
                e["stages"] = stages(k, "CJournalCreatureDescriptionGroup", "CJournalCreatureDescriptionEntry")
            elif cl == "CJournalCharacter": e["stages"] = stages(k, None, "CJournalCharacterDescription")
            else: e["stages"] = [self.text(p["description"])]
            self.entries.append(e)


def note_dups(entries, alt=None):
    """Two entries with the same name in one group (Wild Boars: base game and Blood and Wine; eight Portraits of Geralt) get a small `note` so the list can tell them apart."""
    seen = collections.defaultdict(list)
    for e in entries: seen[(e.get("group"), norm_key(e["name"]))].append(e)
    for v in seen.values():
        if len(v) > 1:
            for i, e in enumerate(v): e["note"] = (alt or {}).get(e["id"]) if alt and len({alt.get(x["id"]) for x in v}) > 1 else "%d of %d" % (i + 1, len(v))


def fold(tag):
    """A tutorial tag without its platform suffix (_pad, _ps4, _ps, _controller, _xbox, ... or a trailing capital PS) and the suffix: ('TutorialAlchemyCook', 'pad')."""
    m = re.search(r"(_pad|_ps4|_ps|_controller|_xbox|_x1|_nx)$", tag, re.I) or re.search(r"(?<=[a-z])PS$", tag)
    return (tag[:m.start()] if m else tag), (m.group(0).strip("_").lower() if m else "")


def usable(e): return bool(e.get("name")) and any(s for _, s in e["stages"])


# ---------------------------------------------------------------- pictures
class Pictures:
    """DDS pictures from the zips and the existing PNG icons: a dict key -> PIL image, flat-colour ones refused."""
    def __init__(self, zips, game_dir):
        from PIL import Image
        self.Image, self.by, self.refused = Image, {}, []
        for zp in zips:
            if not Path(zp).is_file(): log("missing image zip:", zp); continue
            z = zipfile.ZipFile(zp)
            for n in z.namelist():
                if n.lower().endswith(".dds"): self.by.setdefault(n.lower()[len("icons/"):-4], (z, n))
        self.inv = {str(p.relative_to(Path(game_dir) / "inventory")).lower()[:-4]: p for p in (Path(game_dir) / "inventory").rglob("*.png")}

    def load(self, z, n):
        im = self.Image.open(io.BytesIO(z.read(n))); im.load(); return im.convert("RGBA")

    def find(self, kind, stem):
        """The picture for journal image `stem` (bestiary_alp.png) of kind bestiary / characters / tutorials."""
        sub = {"bestiary": "textures/journal/bestiary/", "characters": "textures/journal/characters/", "tutorials": "textures/glossary/tutorials/"}[kind]
        stem = re.sub(r"\.(png|dds)$", "", stem.lower()); hits = [v for k, v in self.by.items() if sub in k and k.endswith("/" + stem)]
        return self.load(*hits[0]) if hits else None

    def icon(self, path):
        """An item icon (icons/inventory/<dir>/<file>) from the zip, else from the PNGs already on the server."""
        key = re.sub(r"\.(dds|png)$", "", path.replace("\\", "/").lower()); key = re.sub(r"^icons/inventory/", "", key)
        if "icons/inventory/" + key in self.by: return self.load(*self.by["icons/inventory/" + key]), key
        if key in self.inv: im = self.Image.open(self.inv[key]); im.load(); return im.convert("RGBA"), key
        return None, key

    def flat(self, im):
        import numpy as np
        a = np.asarray(im).astype(float); m = a[..., 3] > 10; rgb = a[..., :3][m] if m.any() else a[..., :3].reshape(-1, 3)
        return float(rgb.std(axis=0).mean()) < 8     # real pictures have a spread of 18 or more; the orange TODO placeholder is 3.6, an empty texture 0


def webp(im, thumb=False):
    if thumb:
        im = im.copy(); im.thumbnail((64, 64), im.LANCZOS if hasattr(im, "LANCZOS") else 1)
    b = io.BytesIO(); im.save(b, "WEBP", quality=80); return b.getvalue()


# ---------------------------------------------------------------- books
def xml_items(game_dir):
    """Every item definition with the ReadableItem or Painting tag, from the base game and both expansions (XML out of the bundles, plus dlc-xml/)."""
    blobs = []
    for bn, pat in (("xml", "gameplay\\items\\*.xml"), ("bob", "dlc\\bob\\data\\gameplay\\items\\*.xml"), ("ep1", "dlc\\ep1\\data\\gameplay\\items\\*.xml")):
        b = W3B.Bundle(Path(game_dir) / "bundles" / (bn + ".bundle"))
        blobs += [b.read(e) for e in b.match(pat)]; b.close()
    blobs += [p.read_bytes() for p in sorted((Path(game_dir) / "dlc-xml").glob("*/items/*.xml"))]
    items = {}
    for raw in blobs:
        s = raw.decode("utf-8-sig", "replace")
        for m in re.finditer(r"<item\s(.*?)>(.*?)</item>", s, re.S):
            a = m.group(1); tg = re.search(r"<tags>(.*?)</tags>", m.group(2), re.S); tags = [x.strip() for x in tg.group(1).split(",")] if tg else []
            if "ReadableItem" not in tags and "Painting" not in tags: continue
            g = lambda k: (re.search(k + r'\s*=\s*"([^"]*)"', a) or [None, ""])[1]
            items[re.search(r'name\s*=\s*"([^"]+)"', a).group(1)] = {"cat": g("category"), "key": g("localisation_key_name"), "icon": g("icon_path"), "tags": tags}
    return items


def book_body(item_id, it, strs, keys):
    sid = lambda t: keys.get(w3dec.h(t)); key = it["key"]; slug = re.sub(r"[^a-z0-9]+", "_", item_id.lower()).strip("_")
    for t in (key + "_text", key.replace("item_name_", "") + "_text", slug + "_text", item_id):
        i = sid(t)
        if i and strs.get(i) and t != key: return strs[i], "body"
    i = sid("item_desc_" + slug) or sid(key.replace("item_name_", "item_desc_"))
    if i and strs.get(i) and key.replace("item_name_", "") == slug: return strs[i], "description"
    return None, None


# ---------------------------------------------------------------- build
def dump(out, name, obj, files):
    blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"); (out / name).write_bytes(blob); files[name] = len(blob)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="the art folder's glossary/ folder (never committed)")
    ap.add_argument("--journal-zip", default=str(HOME / "incoming/w3planner-journal.zip")); ap.add_argument("--strings", default=str(HOME / "incoming/gamedata/en.w3strings"))
    ap.add_argument("--game-dir", default=str(HOME / "incoming/gamedata"))
    ap.add_argument("--image-zips", nargs="*", default=[str(HOME / "incoming" / n) for n in ("glossary-bestiary.zip", "glossary-characters.zip", "glossary-tutorials.zip", "glossary-books.zip", "w3-glossary-paintings.zip")])
    ap.add_argument("--update-hashes", action="store_true", help="append the SHA-1 of every picture written to tools/game-art-hashes.txt (the guard against committing game art)")
    ap.add_argument("--check", action="store_true", help="only verify the counts of an existing output folder")
    a = ap.parse_args(); out = Path(a.out)
    if a.check:
        m = json.loads((out / "manifest.json").read_text(encoding="utf-8")); bad = {k: (m["counts"].get(k), v) for k, v in EXPECT.items() if m["counts"].get(k) != v}
        print("counts:", m["counts"]); print("differs from the spike's totals:", bad or "no"); return 1 if bad else 0
    strs, keys = w3dec.decode(a.strings); J = Journals(a.journal_zip, strs); P = Pictures(a.image_zips, a.game_dir)
    cons = {i["id"]: i for i in json.loads((ROOT / "data/consumables.json").read_text(encoding="utf-8"))["items"]}
    (out / "img").mkdir(parents=True, exist_ok=True); written, files, counts = {}, {}, {}

    def put(rel, data):
        (out / rel).parent.mkdir(parents=True, exist_ok=True); (out / rel).write_bytes(data); written[rel] = hashlib.sha1(data).hexdigest(); return "@@gimg:%s@@" % rel[len("img/"):-5]

    def picture(kind, stem, tag):
        im = P.find(kind, stem)
        if im is None: return None, None
        if P.flat(im): P.refused.append(stem); return None, None
        return put("img/%s/%s.webp" % (tag, stem[:-4].lower()), webp(im)), put("img/%s/t/%s.webp" % (tag, stem[:-4].lower()), webp(im, True))

    # group names: the base game's group files give the categories; a DLC creature joins the group its virtual group links to
    stem_group = {g["file"].lower(): g["name"] for g in J.groups.values() if g["cls"] == "CJournalCreatureGroup" and g["name"]}
    def category(e):
        g = J.groups.get(e["parent"])
        if not g: return None
        if g["cls"] == "CJournalCreatureGroup": return g["name"]
        return stem_group.get((g["link"] or "").replace("\\", "/").rsplit("/", 1)[-1][:-8].lower())
    sortkey = lambda e: (norm_key(e["name"]), e["id"])

    # bestiary
    bs, entries = [e for e in J.entries if e["tab"] == "bestiary"], []
    for e in sorted((e for e in bs if usable(e)), key=sortkey):
        cat = category(e)
        if not cat: log("bestiary entry without a category, dropped:", e["id"]); continue
        img, th = picture("bestiary", e["image"], "bestiary") if e["image"] else (None, None)
        weak = [{"k": "item", "id": w, "name": cons[w]["name"]} if w in cons else {"k": "sign" if w in SIGNS else "label", "name": w} for w in e["weak"]]
        entries.append({"id": e["id"], "name": e["name"], "group": cat, "img": img, "thumb": th, "stages": [s for _, s in e["stages"] if s], "weak": weak})
    groups = sorted({x["group"] for x in entries}, key=norm_key); counts["bestiary"] = len(entries)
    entries.sort(key=lambda x: (groups.index(x["group"]), norm_key(x["name"]), x["id"])); note_dups(entries, {e["id"]: PACK_NAME[e["pack"]] for e in bs})
    dump(out, "bestiary.json", {"tab": "bestiary", "groups": groups, "entries": entries}, files)
    log("bestiary:", len(entries), "of", len(bs), "raw; dropped stubs:", [e["id"] for e in bs if not usable(e)])

    # characters
    cs = [e for e in J.entries if e["tab"] == "characters"]; entries = []
    for e in sorted((e for e in cs if usable(e)), key=sortkey):
        img, th = picture("characters", e["image"], "characters") if e["image"] else (None, None)
        entries.append({"id": e["id"], "name": e["name"], "group": PACK_NAME[e["pack"]], "img": img, "thumb": th, "stages": [s for _, s in e["stages"] if s]})
    cg = ["Base game", "Hearts of Stone", "Blood and Wine"]; entries.sort(key=lambda x: (cg.index(x["group"]), norm_key(x["name"]), x["id"])); note_dups(entries)
    counts["characters"] = len(entries); dump(out, "characters.json", {"tab": "characters", "groups": ["Base game", "Hearts of Stone", "Blood and Wine"], "entries": entries}, files)

    # tutorials: platform variants fold into the unsuffixed (PC) text
    ts = [e for e in J.entries if e["tab"] == "tutorial"]; byb = collections.defaultdict(list)
    for e in (x for x in ts if usable(x)): byb[fold(e["tag"])[0].lower()].append(e)
    rank = {"": 0, "pad": 1, "controller": 2, "ps4": 3, "ps": 4, "xbox": 5}; pair = {v: k for k, v in PICTURE_PAIRS.items()}; entries = []
    for base, v in byb.items():
        e = sorted(v, key=lambda x: rank.get(fold(x["tag"])[1], 9))[0]
        stem = pair.get(e["tag"]) or (e["image"].replace("\\", "/").rsplit("/", 1)[-1][:-4] if e["image"] else None)   # explicit field (PlaystyleDualGrip) or the name pairing
        img = None
        if stem:
            im = P.find("tutorials", stem + ".png")
            if im is not None and not P.flat(im): img = put("img/tutorials/%s.webp" % stem.lower(), webp(im))
        grp = J.groups.get(e["parent"], {}).get("name")
        entries.append({"id": e["id"], "name": e["name"], "group": grp, "img": img, "stages": [s for _, s in e["stages"] if s], "variants": len(v)})
    entries.sort(key=sortkey); counts["tutorial"] = len(entries); dump(out, "tutorial.json", {"tab": "tutorial", "entries": entries}, files)
    log("tutorials: %d usable of %d raw, %d after folding variants, %d with a picture; placeholder pictures refused: %d" % (sum(1 for x in ts if usable(x)), len(ts), len(entries), sum(1 for x in entries if x["img"]), len(P.refused)))

    # books and paintings
    items, index, bodies, missing_icon = xml_items(a.game_dir), [], collections.defaultdict(dict), []
    for iid, it in sorted(items.items()):
        if it["cat"] in SCHEMATIC: continue
        name = strs.get(keys.get(w3dec.h(it["key"]))) if it["key"] else None
        if not name: continue                                                                    # nameless: unused items
        paint = "Painting" in it["tags"]
        if paint:
            slug = iid; im, _ = P.icon("icons/inventory/paintings/%s.png" % iid)
            if im is None: log("painting without a picture:", iid); continue
            index.append({"id": iid, "name": name, "kind": "painting", "group": "Paintings & maps", "img": put("img/paintings/%s.webp" % iid.lower(), webp(im)), "thumb": put("img/paintings/t/%s.webp" % iid.lower(), webp(im, True))}); continue
        body, how = book_body(iid, it, strs, keys)
        if not body: continue                                                                    # title only: dropped (decision)
        kind = "quest" if "Quest" in it["tags"] else "book" if it["cat"] == "book" else "note"
        im, key = P.icon(it["icon"]) if it["icon"] else (None, None)
        if im is None: missing_icon.append(iid)
        ref = put("img/books/%s.webp" % key.replace("/", "__"), webp(im)) if im is not None else None
        index.append({"id": iid, "name": name, "kind": kind, "group": "Books", "img": ref, "thumb": ref}); bodies[kind][iid] = body
    index.sort(key=lambda e: (e["group"] != "Books", norm_key(e["name"]), e["id"])); note_dups(index); counts["books"] = sum(1 for e in index if e["kind"] != "painting"); counts["paintings"] = sum(1 for e in index if e["kind"] == "painting")
    dump(out, "books_index.json", {"tab": "books", "groups": ["Books", "Paintings & maps"], "entries": index}, files)
    for kind, d in bodies.items(): dump(out, "books_%s.json" % kind, {"kind": kind, "text": d}, files)
    log("books: %d with text, %d paintings; items without an icon: %s" % (counts["books"], counts["paintings"], missing_icon))

    manifest = {"version": 1, "counts": counts, "files": files, "pictures": len(written), "expect": EXPECT}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    if a.update_hashes:
        hp = ROOT / "tools" / "game-art-hashes.txt"; have = set(hp.read_text().split()); new = sorted(h for h in written.values() if h not in have)
        with open(hp, "a", encoding="utf-8") as f: f.writelines("%s  glossary/%s\n" % (written_h, rel) for rel, written_h in sorted(written.items()) if written_h in new)
        log("fingerprints appended:", len(new))
    print("counts:", counts, "| pictures:", len(written), "| differs from the spike:", {k: (counts.get(k), v) for k, v in EXPECT.items() if counts.get(k) != v} or "no")
    return 0


if __name__ == "__main__":
    sys.exit(main())
