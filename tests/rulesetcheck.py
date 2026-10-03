"""v31e: every value follows the NG / NG+ switch, checked against numbers taken from the game's XML.

run(b, base, check, label)
  b      the Playwright browser; base the URL of the site under test; check(name, ok, detail) records a result
Truth: tests/fixtures/ruleset_truth.json, made by `python tools/audit_rulesets.py --game-dir ~/incoming/gamedata --write` from gameplay/abilities and gameplay/items (NG) and the *_plus
folders (NG+). The tests need no game files. What is checked:
  1. every skill at 1/3, 2/3 and 3/3 in both rulesets: the tooltip the build shows equals the tooltip the same formulas give with the XML's own ability values
  2. the NG / NG+ button switches the tooltips at once, without reloading the page
  3. every consumable (potions, decoctions, bombs, oils) in both rulesets: toxicity, duration, charges and effect numbers
  4. every item of both equipment lists: the stat numbers
  5. explicit cases with the numbers written out (Pyrotechnics, Delayed Recovery, bombs, gear)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRUTH = json.loads((ROOT / "tests" / "fixtures" / "ruleset_truth.json").read_text())
RS = ("ng", "ng_plus")
ALL_TIPS = "(()=>{const o={};TREES.forEach((t,ti)=>t.sk.forEach((s,i)=>{for(let L=1;L<=3;L++)o[s.id+'|'+s.name+'|'+L]=tipText(ti,i,L)}));return o})()"
WITH_TRUTH = """([rs,ab])=>{S.rs=rs;const keep=[TIPDATA.ab,TIPDATA.abp],shipped=%s;TIPDATA.ab=ab;TIPDATA.abp={};let want;try{want=%s}finally{TIPDATA.ab=keep[0];TIPDATA.abp=keep[1]}return [shipped,want]}""" % (ALL_TIPS, ALL_TIPS)
CONS = """async rs=>{await cnLoad();S.rs=rs;const o={};CN.data.items.forEach(it=>{if(it.cat==='food'||it.cat==='pocket')return;const v=cnView(it);o[it.id]={tox:it.tox==null?null:it.tox,dur:v.dur==null?null:v.dur,ch:v.ch==null?null:v.ch,stats:v.stats.map(s=>[s.label,s.v])}});return o}"""


def until(pg, js, ms=8000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def tip(pg, rs, skill, level):
    return pg.evaluate("([rs,id,L])=>{S.rs=rs;for(let ti=0;ti<4;ti++){const i=TREES[ti].sk.findIndex(s=>s.id===id);if(i>=0)return tipText(ti,i,L)}}", [rs, skill, level])


def stat_key(s):
    return (s[0], json.dumps(s[1]))


def item_rows(it):
    return ";".join("%s|%s|%s|%s" % r for r in sorted((e["stat"], e["type"], e["min"], e.get("max", e["min"])) for e in (it.get("base") or []) + (it.get("bonuses") or []) if not e.get("effect")))


def run(b, base, check, label="online"):
    print("\n== NG / NG+: every value follows the switch (%s) ==" % label)
    pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(base); until(pg, "typeof S!=='undefined'&&S&&typeof tipText==='function'&&document.getElementById('slots').children.length>0")
    # 1. skills, generated: every skill and level in both rulesets
    total = 0
    for rs in RS:
        shipped, want = pg.evaluate(WITH_TRUTH, [rs, TRUTH["ab"][rs]]); bad = [k for k in want if shipped.get(k) != want[k]]; total += len(want)
        check("%s: all %d skill tooltips equal what the XML's values give" % (rs, len(want)), not bad and len(want) == 240, bad[:3])
    differing = sorted(i for i in TRUTH["ab"]["ng"] if TRUTH["ab"]["ng"][i] != TRUTH["ab"]["ng_plus"].get(i))
    shipped_abp = pg.evaluate("Object.keys(TIPDATA.abp).sort()")
    check("only the abilities whose NG+ values differ are stored twice (the rest stays shared)", shipped_abp == differing, [shipped_abp, differing])
    # 2. the button switches at once, no reload
    pg.evaluate("window.__same=1;S.rs='ng';save()")
    shown = {}
    for rs in RS:
        pg.click('#topbar .rsg [data-rs="%s"]' % rs); ok = until(pg, "S.rs==='%s'" % rs)
        shown[rs] = (ok, pg.evaluate("(()=>{const ti=2,i=TREES[ti].sk.findIndex(s=>s.id==='alchemy_s10');return tipText(ti,i,3)})()"), pg.evaluate("window.__same"))
    check("the NG / NG+ button changes Pyrotechnics 3/3 at once (150, then 300) and the page is not reloaded",
          shown["ng_plus"][0] and "deal 300 damage" in shown["ng_plus"][1] and "deal 150 damage" in shown["ng"][1] and shown["ng"][2] == 1 and shown["ng_plus"][2] == 1, shown)
    # 3. consumables, both rulesets
    for rs in RS:
        got = pg.evaluate(CONS, rs); want = TRUTH["consumables"][rs]; bad = []
        for k, w in want.items():
            g = got.get(k)
            if g is None or [g["tox"], g["dur"], g["ch"]] != [w["tox"], w["dur"], w["ch"]] or sorted(g["stats"], key=stat_key) != sorted(w["stats"], key=stat_key): bad.append(k)
        check("%s: %d consumables show the XML's toxicity, duration, charges and effect numbers" % (rs, len(want)), not bad and len(want) > 100, bad[:3])
    # 4. items, both lists
    for rs in RS:
        lst = json.loads((ROOT / "data" / ("items_ng.json" if rs == "ng" else "items_ng_plus.json")).read_text())["items"]; want = TRUTH["items"][rs]
        bad = [it["id"] for it in lst if item_rows(it) != want.get(it["id"])]
        check("%s: the stat numbers of all %d items equal the XML's" % (rs, len(lst)), not bad and len(lst) == len(want), bad[:3])
    # 5. explicit cases
    pyro = {rs: [tip(pg, rs, "alchemy_s10", L) for L in (1, 2, 3)] for rs in RS}
    check("Pyrotechnics, NG: 50, 100, 150 damage at 1/3, 2/3, 3/3", all(("deal %d damage" % v) in t for v, t in zip((50, 100, 150), pyro["ng"])), pyro["ng"])
    check("Pyrotechnics, NG+: 100, 200, 300 damage at 1/3, 2/3, 3/3", all(("deal %d damage" % v) in t for v, t in zip((100, 200, 300), pyro["ng_plus"])), pyro["ng_plus"])
    dr = {rs: [tip(pg, rs, "alchemy_s3", L) for L in (1, 2, 3)] for rs in RS}
    check("Delayed Recovery, NG: Toxicity above 70%, 65%, 55% (toxicity_threshold_lvl1-3)", all(("above %d%%," % v) in t for v, t in zip((70, 65, 55), dr["ng"])), dr["ng"])
    check("Delayed Recovery, NG+: the data has only toxicity_threshold, which the script never reads, so the game's own formula gives 0%", all("above 0%," in t for t in dr["ng_plus"]), dr["ng_plus"])
    pg.evaluate("S.rs='ng'")
    cons = lambda rs, cid: next(x for x in pg.evaluate("async rs=>{await cnLoad();S.rs=rs;return CN.data.items.map(it=>[it.id,cnView(it).stats])}", rs) if x[0] == cid)[1]
    sv = lambda rs, cid: {s["label"]: s["v"] for s in cons(rs, cid)}
    check("Superior Dancing Star: Fire damage 100 in NG, 250 in NG+", sv("ng", "Dancing Star 3")["Fire damage"] == 100 and sv("ng_plus", "Dancing Star 3")["Fire damage"] == 250, [sv("ng", "Dancing Star 3"), sv("ng_plus", "Dancing Star 3")])
    check("Superior Grapeshot: Physical damage 450 in NG, 900 in NG+", sv("ng", "Grapeshot 3")["Physical damage"] == 450 and sv("ng_plus", "Grapeshot 3")["Physical damage"] == 900, [sv("ng", "Grapeshot 3"), sv("ng_plus", "Grapeshot 3")])
    check("Superior Dragon's Dream: Fire damage 300 in NG, 450 to 600 in NG+", sv("ng", "Dragons Dream 3")["Fire damage"] == 300 and sv("ng_plus", "Dragons Dream 3")["Fire damage"] == [450, 600], [sv("ng", "Dragons Dream 3"), sv("ng_plus", "Dragons Dream 3")])
    ng = {i["id"]: i for i in json.loads((ROOT / "data/items_ng.json").read_text())["items"]}; pl = {i["id"]: i for i in json.loads((ROOT / "data/items_ng_plus.json").read_text())["items"]}
    st = lambda it, stat: next(e["min"] for e in (it["base"] + it["bonuses"]) if e["stat"] == stat)
    check("Viper steel sword: Slashing damage 55 in NG, 295 in NG+", st(ng["Viper School steel sword"], "SlashingDamage") == 55 and st(pl["Viper School steel sword"], "SlashingDamage") == 295)
    check("White Tiger of the West vambraces: piercing resistance 1% in NG, 6% in NG+", st(ng["White Tiger Gloves"], "piercing_resistance_perc") == 0.01 and st(pl["White Tiger Gloves"], "piercing_resistance_perc") == 0.06)
    check("no script errors while switching rulesets", not errs, errs[:1])
    pg.close()
