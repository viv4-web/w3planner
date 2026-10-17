#!/usr/bin/env python3
"""Ruleset audit (v31e): every number the planner shows must follow the NG / NG+ switch.

    python tools/audit_rulesets.py --game-dir ~/incoming/gamedata            audit: shipped data against the game's XML, one table per area (exit 1 on any difference)
    python tools/audit_rulesets.py --game-dir ~/incoming/gamedata --write    also regenerate what is derived from the XML:
                                                                              data/TIPDATA.json  `ab` (NG values of every skill ability) and `abp` (the abilities whose NG+ record differs)
                                                                              tests/fixtures/ruleset_truth.json  (what tests/run_all.py compares the build with, no game files needed)

Which file feeds which ruleset (also in CLAUDE.md, "Rulesets"): NG = gameplay/abilities and gameplay/items; NG+ = the same file names in gameplay/abilities_plus and gameplay/items_plus,
which replace the base file (xml.bundle, then ep1.bundle and bob.bundle, then ~/incoming/gamedata/dlc-xml). `tools/extract_items.xml_sources` is the one place that applies that rule.

Tables are written to docs/audit-v31e/*.tsv (one row per id, level and ruleset: planner, XML, status). Only the XML and the shipped files are read; nothing is guessed.
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "tools" / "extract"))
import extract_items as EI  # noqa: E402

RULESETS = ("ng", "ng_plus")
TYPE_KEY = {"add": "a", "mult": "m", "base": "b", None: "b"}


# ---- a reader for the game's XML that does not need well-formed XML (geralt_skills.xml repeats attributes on one tag) ----
def text_of(blob):
    return re.sub(r"<!--.*?-->", "", blob.decode("utf-8-sig", errors="replace"), flags=re.S)


def abilities_in(txt):
    """{ability: [(tag, {attr: value})]} for every <ability name="..."> block"""
    out = {}
    for m in re.finditer(r'<ability\s+name\s*=\s*"([^"]+)"[^>]*?(?<!/)>(.*?)</ability>', txt, re.S):          # a self-closing <ability .../> has no body
        out[m.group(1)] = [(c.group(1), dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', c.group(2)))) for c in re.finditer(r"<([A-Za-z_]\w*)\s+([^>]*?)/?>", m.group(2))]     # a later definition replaces an earlier one, as in extract_items
    return out


def files_of(g, folder, names=None):
    """raw XML of one ruleset's `folder` ('abilities' or 'items'), in the order they are applied"""
    return [(k, v) for k, v in sorted(g.files.items()) if k[1] == folder and (names is None or any(k[2].startswith(n) for n in names))]


# ---- skills: the ability values every tooltip function reads ----
def skill_values(g, ids):
    """{ability: {attribute: {b, a, m}}} for the given ability names, from the ruleset's geralt_skills*.xml, common_abilities.xml, effects.xml and geralt_stats.xml"""
    out = {}
    for _, blob in files_of(g, "abilities", ("geralt_skills", "common_abilities", "effects.xml", "geralt_stats")):
        for name, kids in abilities_in(text_of(blob)).items():
            if name not in ids: continue
            d = out.setdefault(name, {})
            for tag, at in kids:
                if tag == "tags" or "min" not in at or at.get("type") not in (None, "base", "add", "mult"): continue
                d.setdefault(tag, {"b": 0, "a": 0, "m": 0})[TYPE_KEY[at.get("type")]] = float(at["min"])
    return out


def skill_ids():
    data = json.loads((ROOT / "data/DATA.json").read_text()); fn = (ROOT / "data/TIPFN.js").read_text()
    ids = [s[0] for tree in data for s in tree]
    ids += sorted({m.group(1) for m in re.finditer(r'AA\("(\w+)",', fn)})
    ids += ["magic_1", "magic_2", "magic_3", "magic_4", "magic_5"]       # the five Signs' own abilities (Player Stats, v32c: Yrden trap_duration, Axii duration, Quen shield_health, ...)
    return ids


def build_ab(games):
    """ab = the NG table; abp = for each ability whose NG+ record differs, the NG+ record"""
    ids = set(skill_ids()); tables = {rs: skill_values(g, ids) for rs, g in games.items()}
    cur = json.loads((ROOT / "data/TIPDATA.json").read_text())["ab"]
    order = [i for i in cur if i in tables["ng"]] + sorted(i for i in tables["ng"] if i not in cur)
    ab = {i: tables["ng"][i] for i in order}
    abp = {i: tables["ng_plus"][i] for i in order if i in tables["ng_plus"] and tables["ng_plus"][i] != tables["ng"][i]}
    for i in tables["ng_plus"]:
        if i not in tables["ng"]: sys.exit("ability %s exists only in NG+: add a way to hide it in NG" % i)
    return ab, abp, tables


def canon(x):
    return json.loads(json.dumps(x, sort_keys=True), parse_float=lambda s: round(float(s), 6))


# ---- items and consumables ----
def item_entries(g, ids):
    """{item: sorted [(ability, stat, type, min, max)]} from base_abilities of the item XML and the ability definitions of the same ruleset"""
    ab = {}
    for _, blob in files_of(g, "abilities") + files_of(g, "items"):          # item XML defines abilities too (bombs, gear)
        for name, kids in abilities_in(text_of(blob)).items(): ab[name] = kids
    out = {}
    for _, blob in files_of(g, "items"):
        txt = text_of(blob); starts = list(re.finditer(r'<item\s+name\s*=\s*"([^"]+)"', txt))
        for k, m in enumerate(starts):                      # an item runs to the next named <item>: bound_items hold plain <item>x</item> inside it
            if m.group(1) not in ids: continue
            rows = []; body = txt[m.end(): starts[k + 1].start() if k + 1 < len(starts) else len(txt)]
            for a in re.findall(r"<base_abilities>(.*?)</base_abilities>", body, re.S):
                for n in re.findall(r"<a>\s*([^<]+?)\s*</a>", a):
                    for tag, at in ab.get(n, []):
                        if tag in ("tags", "quality", "weight") or at.get("is_ability") == "true" or "min" not in at: continue
                        rows.append((tag, at.get("type") or "base", EI.num(at["min"]), EI.num(at["max"]) if "max" in at else EI.num(at["min"])))
            out[m.group(1)] = sorted(rows)
    return out


def shipped_item_entries(it):
    rows = []
    for e in (it.get("base") or []) + (it.get("bonuses") or []):
        if e.get("effect"): continue
        rows.append((e["stat"], e["type"], e["min"], e.get("max", e["min"])))
    return sorted(rows)


def items_audit(games):
    """rows (id, name, ruleset, shipped, xml, status) for every item of the two shipped lists, and the XML numbers by ruleset for the test fixture"""
    rows, truth = [], {}
    for rs, g in games.items():
        lst = json.loads((ROOT / ("data/items_ng.json" if rs == "ng" else "data/items_ng_plus.json")).read_text())["items"]
        xml = item_entries(g, {it["id"] for it in lst}); truth[rs] = {}
        for it in lst:
            have, want = shipped_item_entries(it), xml.get(it["id"])
            truth[rs][it["id"]] = ";".join("%s|%s|%s|%s" % r for r in (want or []))
            rows.append((it["id"], it["name"], rs, ";".join("%s %s %s-%s" % r for r in have), ";".join("%s %s %s-%s" % r for r in (want or [])), "ok" if want is not None and [r for r in have] == want else "WRONG"))
    return rows, truth


EXCLUDED = ("quality", "level", "ammo", "duration", "toxicity", "toxicity_offset", "tags", "ability_disable_duration")


def pick(entries, stat, typ="add"):
    """the last entry wins: Basilisk decoction (Mutagen 23) lists duration twice (1800 and 3960) in both rulesets; the planner shows 3960"""
    got = [e[2] for e in entries if e[0] == stat and e[1] == typ]
    return got[-1] if got else None
    return None


def consumable_view(g, cid, label):
    """what the page shows for one consumable in one ruleset, from the item XML: toxicity, duration, charges and the effect lines [(label, value)]"""
    ent = item_entries(g, {cid}).get(cid)
    if ent is None: return None
    stats = []
    for tag, typ, lo, hi in ent:
        if tag in EXCLUDED or "resist_reduction" in tag: continue
        stats.append((label(tag), lo if lo == hi else [lo, hi]))
    return {"tox": pick(ent, "toxicity"), "dur": pick(ent, "duration"), "ch": pick(ent, "ammo"), "stats": sorted(stats, key=lambda s: (s[0], json.dumps(s[1])))}


def shipped_consumable_view(it, rs):
    g = it.get("ngp") if rs == "ng_plus" else None
    stats = (g and g.get("stats")) or it.get("stats") or []
    return {"tox": it.get("tox"), "dur": g["dur"] if g and g.get("dur") is not None else it.get("dur"), "ch": g["ch"] if g and g.get("ch") is not None else it.get("ch"),
            "stats": sorted(((s["label"], s["v"] if not isinstance(s["v"], list) else s["v"]) for s in stats), key=lambda s: (s[0], json.dumps(s[1])))}


def consumables_audit(games):
    cons = json.loads((ROOT / "data/consumables.json").read_text())["items"]; rows, truth = [], {}
    for rs, g in games.items():
        def label(k):
            return g.text("attribute_name_" + k.lower()) or {"burning_chance": "Burning chance", "explosionFireDamage": "Explosion fire damage", "ignoreArmor": "Ignores armor",
                                                           "duration_out_of_cloud": "Effect duration outside the cloud"}.get(k, k)
        truth[rs] = {}
        for it in cons:
            if it["cat"] in ("food", "pocket"): continue                 # food and the Pocket items have no numbers of their own that differ; their effects are not shown
            want = consumable_view(g, it["id"], label); have = shipped_consumable_view(it, rs)
            if want is None: rows.append((it["id"], it["name"], rs, json.dumps(have), "(not in this ruleset's XML)", "WRONG")); continue
            if it["cat"] == "decoction": want["tox"] = have["tox"] if want["tox"] is None else want["tox"]
            truth[rs][it["id"]] = want
            same = {k: have[k] for k in ("tox", "dur", "ch")} == {k: want[k] for k in ("tox", "dur", "ch")} and have["stats"] == want["stats"]
            rows.append((it["id"], it["name"], rs, json.dumps(have, ensure_ascii=False), json.dumps(want, ensure_ascii=False), "ok" if same else "WRONG"))
    return rows, truth


# ---- mutagens and mutations: the XML is identical in both rulesets; compare with the shipped table anyway ----
def mutagen_audit(games):
    rows = []; muts = json.loads((ROOT / "data/MUTS.json").read_text())
    for rs, g in games.items():
        ab = {}
        for _, blob in files_of(g, "items", ("def_item_ingredients",)): ab.update(abilities_in(text_of(blob)))        # the mutagen abilities are defined next to the ingredients
        for m in muts:
            name = {"lesser": "lesser_mutagen_color_%s", "normal": "mutagen_color_%s", "greater": "greater_mutagen_color_%s"}[m["tier"]] % m["c"]
            kids = ab.get(name) or []
            want = next((float(at["min"]) for tag, at in kids if tag == m["stat"] and "min" in at), None)
            rows.append((name, m["name"], rs, m["v"], want, "ok" if want is not None and abs(want - m["v"]) < 1e-9 else "CHECK"))
    return rows


def mutation_audit(games):
    rows = []; muts = json.loads((ROOT / "data/MUT.json").read_text())
    for rs, g in games.items():
        txt = "".join(text_of(b) for k, b in files_of(g, "abilities", ("geralt_mutations",)))
        defs = {int(m.group(1)): dict(zip(("r", "b", "g", "sp"), map(int, m.groups()[1:]))) for m in re.finditer(
            r'<mutation\s+type_name="mutation(\d+)"\s+redMutagenPoints="(\d+)"\s+blueMutagenPoints="(\d+)"\s+greenMutagenPoints="(\d+)"\s+skillPoints="(\d+)"', txt)}
        for m in muts:
            want = defs.get(m["n"]); have = {k: m[k] for k in ("r", "b", "g", "sp")}
            rows.append(("mutation%d" % m["n"], m["name"], rs, json.dumps(have), json.dumps(want), "ok" if want == have else "WRONG"))
    return rows



def skill_level_table(tables):
    """rows (id, name, level, ruleset, planner, xml, status) for every skill at 1, 2 and 3: the tooltip of a fresh build against the tooltip the same formulas give with the XML's own ability values"""
    import functools, http.server, subprocess, tempfile, threading, socketserver
    from playwright.sync_api import sync_playwright
    out = Path(tempfile.mkdtemp(prefix="w3audit-"))
    subprocess.run([sys.executable, str(ROOT / "tools/build.py"), "--variant", "placeholder", "--out", str(out)], check=True, capture_output=True)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(out))); threading.Thread(target=srv.serve_forever, daemon=True).start()
    js = """([rs,ab])=>{S.rs=rs;const all=()=>{const o={};TREES.forEach((t,ti)=>t.sk.forEach((s,i)=>{for(let L=1;L<=3;L++)o[s.id+'|'+s.name+'|'+L]=tipText(ti,i,L)}));return o},keep=[TIPDATA.ab,TIPDATA.abp],shipped=all();
        TIPDATA.ab=ab;TIPDATA.abp={};let want;try{want=all()}finally{TIPDATA.ab=keep[0];TIPDATA.abp=keep[1]}return [shipped,want]}"""
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto("http://127.0.0.1:%d/" % srv.server_address[1]); pg.wait_for_function("typeof tipText==='function'&&typeof TREES!=='undefined'")
        for rs in RULESETS:
            shipped, want = pg.evaluate(js, [rs, tables[rs]])
            for k, w in want.items():
                i, name, lv = k.split("|"); rows.append((i, name, lv, rs, shipped[k].replace("\n", " / "), w.replace("\n", " / "), "ok" if shipped[k] == w else "WRONG"))
        b.close()
    srv.shutdown(); return rows

def write_tsv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\t".join(header) + "\n" + "\n".join("\t".join(str(c).replace("\t", " ").replace("\n", " ") for c in r) for r in rows) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", default=str(Path.home() / "incoming" / "gamedata")); ap.add_argument("--write", action="store_true"); ap.add_argument("--levels", action="store_true", help="also write the per-skill, per-level tooltip table (builds the site, needs Playwright)"); ap.add_argument("--out", default=str(ROOT / "docs" / "audit-v31e"))
    a = ap.parse_args(); out = Path(a.out)
    strings = EI.w3dec.decode(str(Path(a.game_dir) / "en.w3strings")); games = {rs: EI.Game(a.game_dir, rs, strings) for rs in RULESETS}
    bad = 0

    # skills: the shipped ability tables against the XML
    ab, abp, tables = build_ab(games); tip = json.loads((ROOT / "data/TIPDATA.json").read_text()); srows = []
    for rs in RULESETS:
        have = {i: (abp[i] if rs == "ng_plus" and i in tip.get("abp", {}) else tip["ab"][i]) for i in tip["ab"]} if rs == "ng_plus" else tip["ab"]
        if rs == "ng_plus": have = {i: tip.get("abp", {}).get(i, tip["ab"][i]) for i in tip["ab"]}
        for i in sorted(tables[rs]):
            for attr in sorted(set(tables[rs][i]) | set(have.get(i, {}))):
                w, h = tables[rs][i].get(attr), have.get(i, {}).get(attr)
                ok = w is not None and h is not None and canon(w) == canon(h)
                srows.append((i, attr, rs, json.dumps(h), json.dumps(w), "ok" if ok else "WRONG"))
    write_tsv(out / "skill_abilities.tsv", ("ability", "attribute", "ruleset", "planner", "xml", "status"), srows)
    diff_ids = sorted(abp)
    print("skills: %d ability attributes checked in each ruleset; abilities whose NG+ record differs from NG: %s" % (len({(r[0], r[1]) for r in srows}), ", ".join(diff_ids)))
    bad += sum(r[5] != "ok" for r in srows)

    if a.levels:
        lrows = skill_level_table(tables); write_tsv(out / "skills.tsv", ("id", "name", "level", "ruleset", "planner", "xml", "status"), lrows)
        print("skill tooltips (80 skills x 3 levels x 2 rulesets): %s" % dict(Counter((r[3], r[6]) for r in lrows))); bad += sum(r[6] != "ok" for r in lrows)
    irows, itruth = items_audit(games); write_tsv(out / "items.tsv", ("id", "name", "ruleset", "planner", "xml", "status"), irows)
    print("items: %s" % dict(Counter((r[2], r[5]) for r in irows))); bad += sum(r[5] != "ok" for r in irows)
    crows, ctruth = consumables_audit(games); write_tsv(out / "consumables.tsv", ("id", "name", "ruleset", "planner", "xml", "status"), crows)
    print("consumables: %s" % dict(Counter((r[2], r[5]) for r in crows))); bad += sum(r[5] != "ok" for r in crows)
    mrows = mutagen_audit(games); write_tsv(out / "mutagens.tsv", ("ability", "name", "ruleset", "planner", "xml", "status"), mrows)
    print("mutagens: %s" % dict(Counter((r[2], r[5]) for r in mrows))); bad += sum(r[5] != "ok" for r in mrows)
    nrows = mutation_audit(games); write_tsv(out / "mutations.tsv", ("id", "name", "ruleset", "planner", "xml", "status"), nrows)
    print("mutations: %s" % dict(Counter((r[2], r[5]) for r in nrows))); bad += sum(r[5] != "ok" for r in nrows)

    if a.write:
        tip["ab"] = ab; tip["abp"] = abp
        (ROOT / "data/TIPDATA.json").write_text(json.dumps(tip, separators=(",", ":"), ensure_ascii=False))
        truth = {"note": "made by tools/audit_rulesets.py --write from the game's XML: skill ability values (both rulesets), item numbers, consumable numbers",
                 "ab": {"ng": tables["ng"], "ng_plus": tables["ng_plus"]}, "items": itruth, "consumables": ctruth}
        (ROOT / "tests/fixtures/ruleset_truth.json").write_text(json.dumps(truth, separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n")
        print("wrote data/TIPDATA.json (ab, abp) and tests/fixtures/ruleset_truth.json")
    print("%d differences" % bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
