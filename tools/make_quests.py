#!/usr/bin/env python3
"""Build the Quests data (v33) from the game's own journal files.

    python tools/make_quests.py                       writes data/QUESTS.json and ~/work/w3planner-art/quests/ (the defaults point at ~/incoming on the server)
    python tools/make_quests.py --check               verify the existing files, write nothing

Inputs (read-only): ~/incoming/w3planner-journal.zip (every .journal file, made on the PC by tools/pc/extract_journal_on_pc.py), ~/incoming/gamedata/en.w3strings,
~/incoming/gamedata/csv/**/*quest_levels*.csv (the level of each quest). Nothing else: no third-party guide, wiki or spreadsheet (docs/QUESTS.md).

Outputs
  data/QUESTS.json            the quest list (committed, like the item lists): per quest the journal GUID (how a save names it), id, name, type, region, level, pack and the objectives
                              (objective GUID + title). Names and objective titles are short labels; the journal TEXT is not in here.
  <art-dir>/quests/desc.json  the journal descriptions {quest id: [text, ...]}. GAME TEXT: like the Glossary it stays in the private art folder, never committed;
                              tools/build.py turns it into one hashed script of the live build, loaded when a quest is opened.
  <art-dir>/quests/manifest.json
The decisions behind it are in docs/QUESTS.md.
"""
import argparse, collections, glob, hashlib, json, os, re, struct, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import cr2w, w3dec   # noqa: E402

HOME = Path.home()
VERSION = 1
# tabs, in order (decisions by Vivek, 2026-10-17): the region of a base-game or free-DLC quest comes from its `world` code in the journal file; the two expansions are
# tabs of their own by pack; code 8 and quests with no code go to the last tab, never guessed. The code -> place mapping is read from the quest ids, not from a file.
REGIONS = [("wo", "White Orchard"), ("vz", "Vizima"), ("ve", "Velen"), ("no", "Novigrad"), ("sk", "Skellige"), ("km", "Kaer Morhen"),
           ("hos", "Hearts of Stone"), ("baw", "Blood and Wine"), ("oth", "Other & epilogue")]
WORLD = {4: "wo", 5: "vz", 9: "ve", 1: "no", 2: "sk", 3: "km"}
PACK_REGION = {"ep1": "hos", "bob": "baw"}
# debug and placeholder entries, dropped from the data entirely: no title, the journal groups "testlevel" ([PL] Exploration, [Interaction]) and the E3 / press-demo leftovers
DROP_GROUPS = {"testlevel", "Demo Quests"}
# levels the CSVs name with a different key than the quest id (the quest's `baseName`): id -> (key found in the CSV, why). Everything else is matched by the exact id
# (case and surrounding spaces ignored); a quest with no source keeps level null (the page shows "—, not computed yet").
LEVEL_KEY = {"plegmund_poi_0%d" % i: ("plegmund", "the CSV has one row for the five Big Feet to Fill quests") for i in range(1, 6)}
LEVEL_KEY["ep1poi26b"] = ("ep1poi26", "the CSV row of the same point of interest, without the trailing b")


def log(*a): print(*a, file=sys.stderr)


def read_levels(game_dir):
    """{lowercased key: (level, relative file, line)} from every quest_levels CSV of the base game and the DLC; a key in two files with different levels is reported."""
    out, clash = {}, []
    # the canonical quest_levels.csv of each package first; the extra files (dlc10's th1009 copies) only fill keys the canonical ones lack
    files = sorted(glob.glob(str(game_dir / "csv" / "**" / "*quest_levels*.csv"), recursive=True), key=lambda f: (os.path.basename(f) != "quest_levels.csv", f))
    for f in files:
        rel = os.path.relpath(f, game_dir / "csv")
        for n, line in enumerate(open(f, "rb").read().decode("utf-8-sig", errors="replace").splitlines(), 1):
            p = line.split(";")
            if n == 1 or len(p) < 2 or not p[0].strip(): continue
            try: lv = int(p[1].strip())
            except ValueError: continue
            k = p[0].strip().lower()
            if k in out and out[k][0] != lv: clash.append((k, out[k], (lv, rel, n)))
            out.setdefault(k, (lv, rel, n))
    return out, clash


def read_journal(zpath, strs):
    """quests {guid: dict}, groups {guid: base name}, kids {parent guid: [(cls, order, guid, title)]} of every quest journal file."""
    quests, groups, kids = {}, {}, collections.defaultdict(list)
    z = zipfile.ZipFile(zpath)
    for name in sorted(z.namelist()):
        if not name.endswith(".journal") or "/quests/" not in name: continue
        try: c = cr2w.CR2W(z.read(name))
        except Exception: continue
        m = re.search(r"content__content0__bundles__([a-z0-9]+)\.bundle|dlc__([A-Za-z0-9]+)__", name)
        pack = (m.group(1) or m.group(2)) if m else "?"
        for k in c.chunks:
            p = {n: d for n, t, d in k["props"]}
            if "guid" not in p: continue
            g, cl = p["guid"].hex(), k["cls"]
            title = lambda key: strs.get(c.string_id(p[key])) if key in p else None
            order = struct.unpack_from("<I", p["order"], 0)[0] if "order" in p else 0
            par = p["parentGuid"].hex() if "parentGuid" in p else None
            if cl == "CJournalQuestGroup": groups[g] = c.string(p["baseName"])
            elif cl == "CJournalQuest":
                quests[g] = dict(g=g, id=c.string(p["baseName"]), name=title("title"), parent=par, pack=pack,
                                 type=c.names[struct.unpack_from("<H", p["type"], 0)[0]] if "type" in p else None,
                                 world=struct.unpack_from("<I", p["world"], 0)[0] if "world" in p else None)
            elif cl in ("CJournalQuestPhase", "CJournalQuestObjective", "CJournalQuestDescriptionGroup", "CJournalQuestDescriptionEntry") and par:
                kids[par].append((cl, order, g, title("description") if cl == "CJournalQuestDescriptionEntry" else title("title")))
    return quests, groups, kids


def kind_of(q, group):
    n = q["name"]
    if group == "Gwint" or n.startswith("Gwent:") or q["id"] == "Card Game Meta: Gather All": return "gwent"
    if re.match(r"Races?:", n): return "race"
    if n.startswith("Fists of Fury"): return "fist"
    return {"Story": "main", "Chapter": "main", "Side": "side", "MonsterHunt": "contract", "TreasureHunt": "treasure"}[q["type"] or "Story"]


def build(zpath, game_dir):
    strs, _ = w3dec.decode(str(game_dir / "en.w3strings"))
    quests, groups, kids = read_journal(zpath, strs)
    levels, clash = read_levels(game_dir)
    sub = lambda g, cl: [x for x in sorted(kids[g], key=lambda x: x[1]) if x[0] == cl]
    out, desc, dropped, fixes, nolevel = [], {}, [], [], []
    for g, q in quests.items():
        grp = groups.get(q["parent"])
        if not q["name"] or grp in DROP_GROUPS: dropped.append((q["id"], q["name"], grp)); continue
        key = q["id"].strip().lower(); src = None
        if key in levels: src = levels[key]
        elif q["id"] in LEVEL_KEY and LEVEL_KEY[q["id"]][0] in levels:
            src = levels[LEVEL_KEY[q["id"]][0]]; fixes.append((q["id"], q["name"], LEVEL_KEY[q["id"]][0], LEVEL_KEY[q["id"]][1], src))
        if src is None: nolevel.append((q["id"], q["name"]))
        region = PACK_REGION.get(q["pack"]) or WORLD.get(q["world"], "oth")
        objs = [[o[2], o[3]] for ph in sub(g, "CJournalQuestPhase") for o in sub(ph[2], "CJournalQuestObjective") if o[3]]
        out.append(dict(g=g, id=q["id"], n=q["name"], t=kind_of(q, grp), r=region, lv=src[0] if src else None, p=q["pack"], o=objs, _w=q["world"], _grp=grp))
        texts = [e[3] for dg in sub(g, "CJournalQuestDescriptionGroup") for e in sub(dg[2], "CJournalQuestDescriptionEntry") if e[3]]
        if texts: desc[q["id"]] = texts
    out.sort(key=lambda x: (x["lv"] is None, x["lv"] or 0, x["n"], x["id"]))
    return out, desc, dropped, fixes, nolevel, clash


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal-zip", default=str(HOME / "incoming" / "w3planner-journal.zip"))
    ap.add_argument("--game-dir", default=str(HOME / "incoming" / "gamedata"))
    ap.add_argument("--art-dir", default=str(HOME / "work" / "w3planner-art"))
    ap.add_argument("--out", default=str(ROOT / "data" / "QUESTS.json"))
    ap.add_argument("--check", action="store_true", help="build in memory and compare with the files on disk; write nothing")
    a = ap.parse_args()
    quests, desc, dropped, fixes, nolevel, clash = build(a.journal_zip, Path(a.game_dir))
    data = dict(v=VERSION, regions=[list(r) for r in REGIONS], quests=[{k: v for k, v in q.items() if not k.startswith("_")} for q in quests])
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    dblob = json.dumps(desc, ensure_ascii=False, separators=(",", ":")) + "\n"
    man = dict(version=VERSION, counts=dict(quests=len(quests), descriptions=len(desc)), files=["desc.json"], sha1=hashlib.sha1(dblob.encode()).hexdigest()[:12])
    log("quests %d (dropped %d), with a description %d, objectives %d, level known %d, level missing %d" % (len(quests), len(dropped), len(desc), sum(len(q["o"]) for q in quests),
        sum(q["lv"] is not None for q in quests), len(nolevel)))
    log("by region:", dict(collections.Counter(q["r"] for q in quests))); log("by kind:", dict(collections.Counter(q["t"] for q in quests))); log("by pack:", dict(collections.Counter(q["p"] for q in quests)))
    log("level CSV keys with two different levels:", clash or "none")
    log("DROPPED:"); [log("  %-34r %-40r group=%s" % d) for d in dropped]
    log("LEVEL from a differently-named CSV key:"); [log("  %-24s %-36s <- %s (%d, %s:%d) %s" % (i, n[:36], k, s[0], s[1], s[2], why)) for i, n, k, why, s in fixes]
    log("NO LEVEL (no source):"); [log("  %-34r %s" % x) for x in nolevel]
    log("NO CODE or code 8 (tab Other & epilogue):"); [log("  %-34r %-44s world=%s group=%s" % (q["id"], q["n"][:44], q["_w"], q["_grp"])) for q in quests if q["r"] == "oth"]
    if a.check:
        ok = Path(a.out).read_text(encoding="utf-8") == blob and (Path(a.art_dir) / "quests" / "desc.json").read_text(encoding="utf-8") == dblob
        print("OK: files match" if ok else "DIFFERENT: run tools/make_quests.py"); sys.exit(0 if ok else 1)
    Path(a.out).write_text(blob, encoding="utf-8")
    qd = Path(a.art_dir) / "quests"; qd.mkdir(parents=True, exist_ok=True)
    (qd / "desc.json").write_text(dblob, encoding="utf-8"); (qd / "manifest.json").write_text(json.dumps(man) + "\n")
    log("wrote %s (%d bytes) and %s" % (a.out, len(blob), qd))


if __name__ == "__main__":
    main()
