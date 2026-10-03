"""v32: the Player Stats screen (top-bar button on every tab, key C), in a real browser.

run(b, base, check, label)      everything that needs no save: the button on every tab, the key, the tabs, the keyboard, a phone, a planned build with ranges, a level-1 build (only the base numbers)
fixture(b, base, check, label)  two saves (never committed; SKIPPED when absent): ~/work/w3planner-art/save-spike/fixtures/stats-l9/ and stats-l9b/: every number the game showed must match, or be "—"
live(b, url, check)             run() on the preview or the live site (smoke test)"""
from pathlib import Path

READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"
FIXD = Path.home() / "work/w3planner-art/save-spike/fixtures"
# In-game Player Stats, read by Vivek. Sign intensity: +144% (stats-l9) and +191% (stats-l9b), with every Sign line of stats-l9b (SIGNS_B) and Stamina regeneration in combat 20/s (v32c: computed, not "—").
SIGNS_B = ["+191 %", "", "139 % Stagger", "0 Telekinetic damage", "", "290 Fire damage", "100 % Burning", "", "610 Physical damage reduction", "", "35 % Slowdown", "342 Shock damage", "33.50s Duration", "", "14.25s Duration"]
TRUTH_A = {"DPS - Silver sword": "342", "DPS - Steel sword": "204", "Armor": "127", "Crossbow": "37", "Vitality": "4641|4641", "Toxicity": "0|100", "Stamina": "100|100"}
SILVER_A = ["199", "10 %", "259", "365", "10 %", "474", "0 %", "0 %", "0 %", "0 %", "0 %", "0 %"]
TRUTH_B = {"DPS - Silver sword": "399", "DPS - Steel sword": "234", "Armor": "127", "Crossbow": "38", "Vitality": "4473|4473", "Toxicity": "0|100", "Stamina": "100|100"}
SILVER_B = ["233", "10 %", "293", "427", "10 %", "537", "0 %", "0 %", "0 %", "0 %", "0 %", "0 %"]
ROWS = "[...document.querySelectorAll('#psrows .psrow')].map(r=>({n:r.querySelector('.psname').textContent,v:[...r.querySelectorAll('.psnum b,.psnum small')].map(x=>x.textContent).join('|')}))"
PANEL = "[...document.querySelectorAll('#pspanel .psline')].map(l=>({v:l.querySelector('b').textContent,l:l.querySelector('span').textContent}))"


def until(pg, js, ms=8000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def page(b, url, w=1440, h=1000, mobile=False, scr="inv"):
    pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); pg.goto(url); until(pg, READY)
    pg.evaluate("scrGo('%s')" % scr); until(pg, "!!eqData()&&!!CN.data"); pg.wait_for_timeout(300)
    return pg, errs


def run(b, base, check, label):
    pg, errs = page(b, base); E = pg.evaluate
    top = E("(()=>{const b=document.getElementById('pstatsbtn'),r=b.getBoundingClientRect(),ids=[...b.parentNode.children].map(x=>x.id||x.className);return{h:r.height,parent:b.parentNode.className,ids,inInv:!!document.getElementById('invhint')}})()")
    check("%s: PLAYER STATS is in the top bar next to NG / NG+ / COPY LINK (and IMPORT SAVE on the website), 44 px high, and the Inventory has no button of its own (%s)" % (label, top["ids"]),
          top["h"] >= 44 and "pstatsbtn" in top["ids"] and "copy" in top["ids"] and "rsg" in top["ids"] and not top["inInv"], top)
    for scr, name in (("inv", "Inventory"), ("char", "Character"), ("glo", "Glossary")):
        E("scrGo('%s')" % scr); pg.wait_for_timeout(300); pg.click("#pstatsbtn"); until(pg, "!document.getElementById('pstats').hidden")
        opened = E("document.getElementById('screens').hidden&&document.getElementById('pstats').offsetParent!==null&&document.getElementById('pstab0').getAttribute('aria-selected')==='true'")
        pg.keyboard.press("Escape"); until(pg, "document.getElementById('pstats').hidden")
        back = E("(s=>!document.getElementById('screens').hidden&&S.scr===s&&document.activeElement.id==='pstatsbtn')", scr)
        pg.keyboard.press("c"); until(pg, "!document.getElementById('pstats').hidden"); k_open = E("PS.open"); pg.keyboard.press("C"); until(pg, "document.getElementById('pstats').hidden"); k_closed = not E("PS.open")
        check("%s: on %s the button opens it over the tab, Escape returns to the same tab with focus on the button, key C opens and closes it" % (label, name), opened and back and k_open and k_closed, [opened, back, k_open, k_closed])
    E("scrGo('inv')"); pg.wait_for_timeout(200); pg.click("#pstatsbtn"); until(pg, "!document.getElementById('pstats').hidden")
    check("%s: while it is open the tab's content is really gone from the page (not only marked hidden), the screen is there" % label, E("document.getElementById('eqbody').offsetParent===null&&document.getElementById('pstats').offsetParent!==null"))
    check("%s: nine tabs in the game's order, the first one selected" % label, [r["n"] for r in E(ROWS)] == ["DPS - Silver sword", "DPS - Steel sword", "Armor", "Crossbow", "Vitality", "Toxicity", "Sign intensity", "Stamina", "Additional"] and E("document.getElementById('pstab0').getAttribute('aria-selected')") == "true")
    check("%s: roles: tablist, nine tabs (one selected, one in the tab order), a tabpanel labelled by the selected tab" % label,
          E("(()=>{const l=document.getElementById('psrows'),t=[...l.querySelectorAll('[role=tab]')],p=document.getElementById('pspanel');return l.getAttribute('role')==='tablist'&&t.length===9&&t.filter(x=>x.getAttribute('aria-selected')==='true').length===1&&t.filter(x=>x.tabIndex===0).length===1&&p.getAttribute('role')==='tabpanel'&&p.getAttribute('aria-labelledby')==='pstab0'})()"))
    r = E(ROWS)
    check("%s: a level-1 build with nothing equipped shows only base numbers: Vitality 3500, Stamina 100, Toxicity 0 / 100, no weapons, armour 0, Sign intensity +0 %% (%s)" % (label, [x["v"] for x in r]),
          [x["v"] for x in r][:4] == ["0", "0", "0", "0"] and r[4]["v"] == "3500|3500" and r[5]["v"] == "0|100" and r[6]["v"] == "+0 %" and r[7]["v"] == "100|100", r)
    pg.click("#pstab4"); d = [(x["v"], x["l"]) for x in E(PANEL)]
    check("%s: a level-1 build: Vitality regeneration 1/s and 1/s in the game's words, in the game's order (%s)" % (label, d), d == [("1/s", "Vitality regeneration outside of combat"), ("1/s", "Vitality regeneration per enemy killed during combat")], d)
    pg.click("#pstab7"); d = [(x["v"], x["l"]) for x in E(PANEL)]
    check("%s: Stamina: regeneration out of combat 100/s, in combat 10/s (ConGeralt 0.1 x 100) (%s)" % (label, d), d == [("100/s", "Stamina regeneration out of combat"), ("10/s", "Stamina regeneration in combat")], d)
    pg.click("#pstab3"); pg.keyboard.press("ArrowDown"); pg.keyboard.press("ArrowDown")
    check("%s: ArrowDown moves the selection (Crossbow, then Vitality, Toxicity), only one tab selected, the panel follows" % label, E("document.querySelector('#psrows [aria-selected=true]').id") == "pstab5" and E("document.querySelectorAll('#psrows [aria-selected=true]').length") == 1 and E("document.querySelector('#pspanel .pshead').textContent") == "Toxicity")
    for _ in range(6): pg.keyboard.press("ArrowUp")
    check("%s: ArrowUp wraps from the top to the last tab (Additional)" % label, E("document.querySelector('#psrows [aria-selected=true]').id") == "pstab8")
    pg.click("#pstab2"); E("document.getElementById('lvl').value=20;pointsChanged()"); pg.wait_for_timeout(300)
    check("%s: the selection is remembered while the screen is open (a level change re-draws it)" % label, E("PS.sel") == 2 and E("document.querySelector('#pspanel .pshead').textContent") == "Armor")
    pg.click("#psclose"); until(pg, "document.getElementById('pstats').hidden"); pg.click("#pstatsbtn"); until(pg, "!document.getElementById('pstats').hidden")
    check("%s: reopened, the first tab is selected again (reset on reopen)" % label, E("PS.sel") == 0)
    pg.keyboard.press("Escape")
    E("scrGo('glo')"); until(pg, "!document.getElementById('screenGlo').hidden"); 
    if E("!!document.getElementById('glQ')&&document.getElementById('glQ').offsetParent!==null"):
        pg.click("#glQ"); pg.keyboard.type("c")
        check("%s: typing a c in the Glossary search box does not open the stats" % label, E("!PS.open") and E("document.getElementById('glQ').value") == "c")
    E("scrGo('inv')"); pg.wait_for_timeout(200); pg.click("#eqbody .eqtile[data-i='0']"); until(pg, "!!EQ.pick"); pg.fill("#pkq", "c")
    check("%s: typing a c in the chooser's search box does not open the stats" % label, E("!PS.open") and E("document.getElementById('pkq').value") == "c"); pg.click("#pkclose")
    check("%s: the link is untouched by the screen (no new segment)" % label, "ps" not in "".join(x for x in E("enc()").split(".")[8:] if x[:2] not in ("g1", "c1", "s1")))
    # a planned build: an item that gives a stat within a range shows min–max, never a midpoint; a sword whose damage the data does not hold shows —
    E("""(()=>{document.getElementById('lvl').value=50;document.getElementById('bonuspts').value=0;pointsChanged();const d=eqData();S.gear[EQ_SLOTS.indexOf('crossbow')]=d.byId.get('Crossbow 4').n;S.gear[EQ_SLOTS.indexOf('steel')]=d.byId.get('Cleaver').n;save();eqRender(true);psRender()})()""")
    pg.wait_for_timeout(300); pg.click("#pstatsbtn") if not E("PS.open") else None; until(pg, "PS.open"); rr = {x["n"]: x["v"] for x in E(ROWS)}
    lo = E("(()=>{const a=psPass(false),b=psPass(true);return[a.rows.crossbow.v,b.rows.crossbow.v]})()")
    check("%s: planned Crossbow 4 (attack power 1.3 to 1.7): the Crossbow row reads min–max (%s), the ends are the lowest and the highest pass, never a midpoint" % (label, rr["Crossbow"]), rr["Crossbow"] == "%d–%d" % tuple(lo) and lo[0] < lo[1], [rr, lo])
    check("%s: planned Cleaver (its damage is not in the data): DPS - Steel sword shows —, not a number made of the level alone (%s)" % (label, rr["DPS - Steel sword"]), rr["DPS - Steel sword"] == "—", rr)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()
    # a phone: the button is a 44 px icon in the top bar, rows are a list, the tapped row opens its detail under it, nothing scrolls sideways
    pg, errs = page(b, base, 390, 844, True); E = pg.evaluate
    bt = E("(()=>{const r=document.getElementById('pstatsbtn').getBoundingClientRect(),ids=[...document.querySelectorAll('.topright .btn')].map(b=>b.getBoundingClientRect().height).filter(h=>h>0);return{w:r.width,h:r.height,min:Math.min(...ids),sw:document.documentElement.scrollWidth}})()")
    check("%s: phone 390: the top-bar button is a 44 px icon beside the others, nothing scrolls sideways (%s)" % (label, bt), bt["w"] >= 44 and bt["h"] >= 44 and bt["min"] >= 44 and bt["sw"] <= 390, bt)
    pg.click("#pstatsbtn"); until(pg, "!document.getElementById('pstats').hidden")
    ph = E("(()=>{const rows=[...document.querySelectorAll('#psrows .psrow')],p=document.getElementById('pspanel'),b=document.getElementById('psclose').getBoundingClientRect();return{h:Math.min(...rows.map(r=>r.getBoundingClientRect().height)),sw:document.documentElement.scrollWidth,under:rows[0].nextElementSibling===p,close:b.height}})()")
    check("%s: phone 390: rows are a list of 44 px+ targets, the first detail opens under its row (%s)" % (label, ph), ph["h"] >= 44 and ph["sw"] <= 390 and ph["under"] and ph["close"] >= 44, ph)
    pg.click("#pstab4"); pg.wait_for_timeout(150)
    ph = E("(()=>{const p=document.getElementById('pspanel'),r=document.getElementById('pstab4');return{under:r.nextElementSibling===p,head:p.querySelector('.pshead').textContent,sw:document.documentElement.scrollWidth}})()")
    check("%s: phone 390: tapping Vitality opens its detail under it, only that one selected (%s)" % (label, ph), ph["under"] and ph["head"] == "Vitality" and ph["sw"] <= 390 and E("document.querySelectorAll('#psrows [aria-selected=true]').length") == 1, ph)
    check("%s: phone 390: no script errors" % label, not errs, errs[:1]); pg.close()


def fixture(b, base, check, label):
    for sub, truth, silver, play, effects in (("stats-l9", TRUTH_A, SILVER_A, "10 Hours 25 Minutes", False), ("stats-l9b", TRUTH_B, SILVER_B, "10 Hours 59 Minutes", True)):
        d = FIXD / sub; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
        if not sav: print("  SKIP  %s: Player Stats against the %s save (fixture not present)" % (label, sub)); continue
        pg, errs = page(b, base, scr="char"); E = pg.evaluate
        check("%s [%s]: no play time before a save is imported" % (label, sub), E("PS.play") is None)
        pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden"); pg.wait_for_timeout(600)
        until(pg, "!!eqData()&&!!CN.data"); pg.keyboard.press("c"); until(pg, "!document.getElementById('pstats').hidden")
        got = {x["n"]: x["v"] for x in E(ROWS)}; bad = {k: (got.get(k), v) for k, v in truth.items() if got.get(k) != v}
        check("%s [%s]: every row the game showed matches and Sign intensity is %s (%s)" % (label, sub, "+144 %" if sub == "stats-l9" else "+191 %", got), not bad and got.get("Sign intensity") == ("+144 %" if sub == "stats-l9" else "+191 %"), bad)
        dd = [x["v"] for x in E(PANEL)]
        check("%s [%s]: Silver sword detail (%s)" % (label, sub, dd), dd == silver, dd)
        pg.click("#pstab4"); v = [(x["v"], x["l"]) for x in E(PANEL)]
        check("%s [%s]: Vitality regeneration 1/s and 1/s (%s)" % (label, sub, v), v == [("1/s", "Vitality regeneration outside of combat"), ("1/s", "Vitality regeneration per enemy killed during combat")], v)
        pg.click("#pstab6")
        sg = [E("document.querySelector('#psrows .psrow.sel .psnum').textContent")] + [(x["v"] + " " + x["l"]).strip() if x["v"] else "" for x in E(PANEL)]
        if sub == "stats-l9b": check("%s [%s]: every Sign intensity line is the game's (+191%%, Aard 139%% / 0, Igni 290 / 100%%, Quen 610, Yrden 35%% / 342 / 33.50s, Axii 14.25s) (%s)" % (label, sub, sg), sg == [SIGNS_B[0]] + [x.replace(" Stagger", " Stagger") for x in SIGNS_B[1:]], sg)
        else: check("%s [%s]: Sign intensity %s and every Sign line has a number (no \"—\", the save's own ability list agrees with the model) (%s)" % (label, sub, got["Sign intensity"], sg), sg[0] == "+144 %" and not any("—" in x for x in sg), sg)
        pg.click("#pstab7"); v = [x["v"] for x in E(PANEL)]
        check("%s [%s]: Stamina regeneration out of combat 100/s, in combat %s (%s)" % (label, sub, "20/s, the game's" if sub == "stats-l9b" else "19/s (the model; the game's number was not read for this save)", v), v == ["100/s", "20/s" if sub == "stats-l9b" else "19/s"], v)
        pg.click("#pstab8"); v = [x["v"] for x in E(PANEL)]
        check("%s [%s]: Additional: herbs, instant kill, human and monster experience all 0 %% (%s)" % (label, sub, v), v == ["0 %"] * 4, v)
        check("%s [%s]: TOTAL PLAY TIME %s" % (label, sub, play), E("(p=>{const t=document.getElementById('pstime');return !t.hidden&&t.textContent.replace(/\\s+/g,' ').includes(p)})", play))
        eff = E("document.getElementById('pseff').textContent")
        check("%s [%s]: the active effects of the save are named (%s)" % (label, sub, eff), (("Enhanced Weapons" in eff and "Quen Sign" in eff) if effects else not eff), eff)
        check("%s [%s]: every value is a number, a range or —" % (label, sub), all(x["v"] in ("—", "") or any(c.isdigit() for c in x["v"]) for i in range(9) for x in (pg.click("#pstab%d" % i) or E(PANEL))))
        check("%s [%s]: no script errors" % (label, sub), not errs, errs[:1]); pg.close()


def live(b, url, check):
    run(b, url, check, "stats")


def rulesets(b, base, check, label):
    """v31e: the active-effect numbers follow the NG / NG+ switch (gameplay/abilities_effects_potions.xml vs the _plus file)"""
    pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(base); pg.wait_for_function("typeof psPick==='function'&&typeof S!=='undefined'&&S")
    get = lambda rs, k, n: pg.evaluate("([rs,k,n])=>{S.rs=rs;return psPick(k,n)||null}", [rs, k, n])
    fm = {rs: [get(rs, "eff", "FullMoonEffect_Level%d" % L)["vitality"]["add"] for L in (1, 2, 3)] for rs in ("ng", "ng_plus")}
    wr = {rs: [get(rs, "eff", "WhiteRaffardDecoctionEffect_Level%d" % L)["vitality"]["mult"] for L in (1, 2)] for rs in ("ng", "ng_plus")}
    check("%s: Full Moon +300, 650, 1000 Vitality in NG and +600, 1100, 1500 in NG+" % label, fm == {"ng": [300, 650, 1000], "ng_plus": [600, 1100, 1500]}, fm)
    check("%s: White Raffard's Decoction +35%%, 60%% in NG and +60%%, 80%% in NG+" % label, wr == {"ng": [0.35, 0.6], "ng_plus": [0.6, 0.8]}, wr)
    check("%s: Swallow level 1 and the Mutagen 08 and 09 effects are read as the XML says (a self-closing ability tag does not swallow the next one)" % label,
          get("ng", "eff", "SwallowEffect_Level1") is not None and get("ng", "eff", "Mutagen08Effect") is None and get("ng", "eff", "Mutagen09Effect")["touch"] == ["spell_power"])
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


SIGN_LV9 = ["+11 %", "", "49 % Stagger", "0 Telekinetic damage", "", "111 Fire damage", "49 % Burning", "", "222 Physical damage reduction", "", "25 % Slowdown", "0 Shock damage", "11.10s Duration", "", "5.55s Duration"]
SIGN_LV9_TRAP = ["+11 %", "", "49 % Stagger", "0 Telekinetic damage", "", "111 Fire damage", "49 % Burning", "", "222 Physical damage reduction", "", "25 % Slowdown", "133 Shock damage", "16.10s Duration", "", "5.55s Duration"]


def signs(b, base, check, label):
    """v32c: a planned build, worked out by hand from the game's formulas and XML, in both rulesets.
    Level 9, nothing else: the Sign power of every Sign is 1 + the level bonus (Lvl2 to Lvl9: 3 x 0.02 + 5 x 0.01 = 0.11) = 1.11 (all_PC_ability gives the 1).
      total +11 %; Aard stagger 1.11 / 2 - 4 x 0.016 = 49 %; Igni 100 x 1.11 = 111; burning (1 + ln 1.11) / 2 - 0.064 = 49 %; Quen 200 x 1.11 = 222;
      Yrden slowdown (0.20 + 0.25 x 1.11 / 4) x (1 - 0.064) = 25 %, duration 10 x 1.11 = 11.10 s; Axii 5 x 1.11 = 5.55 s; Stamina in combat 100 x 0.1 = 10/s.
    Plus Sustained Glyphs (Yrden trap_duration +5) and Magic Trap (Shock damage 120) equipped: Yrden duration 10 x 1.11 + 5 = 16.10 s, Shock 120 x 1.11 = 133, Stamina 100 x (0.1 + 2 x 0.005) = 11/s."""
    pg, errs = page(b, base, scr="char"); E = pg.evaluate
    E("(()=>{document.getElementById('lvl').value=9;document.getElementById('bonuspts').value=0;pointsChanged()})()"); pg.keyboard.press("c"); until(pg, "!document.getElementById('pstats').hidden")
    def lines():
        pg.click("#pstab6"); a = [E("document.querySelector('#psrows .psrow.sel .psnum').textContent")] + [(x["v"] + " " + x["l"]).strip() if x["v"] else "" for x in E(PANEL)]
        pg.click("#pstab7"); return a, [x["v"] for x in E(PANEL)]
    def switch(rs):
        pg.click('#topbar .rsg [data-rs="%s"]' % rs); until(pg, "S.rs==='%s'&&!!eqData()" % rs); E("psRender()"); pg.wait_for_timeout(150)
    for rs in ("ng", "ng_plus"):
        switch(rs); sg, st = lines()
        check("%s: planned level 9, nothing equipped, %s: Sign intensity +11 %% and every line as worked out by hand (%s)" % (label, rs, sg), sg == SIGN_LV9, sg)
        check("%s: planned level 9, nothing equipped, %s: Stamina regeneration in combat 10/s (%s)" % (label, rs, st), st == ["100/s", "10/s"], st)
    E("""(()=>{const f=id=>{for(let ti=0;ti<4;ti++){const i=TREES[ti].sk.findIndex(s=>s.id===id);if(i>=0)return[ti,i]}};
      [['magic_s42',0],['magic_s3',1]].forEach(([id,k])=>{const [ti,i]=f(id);S.lv[ti][i]=1;S.slots[k]=[ti,i]});psRender()})()""")
    for rs in ("ng", "ng_plus"):
        switch(rs); sg, st = lines()
        check("%s: planned level 9 with Sustained Glyphs and Magic Trap, %s: Yrden duration 16.10s, Shock damage 133 (%s)" % (label, rs, sg), sg == SIGN_LV9_TRAP, sg)
        check("%s: the same build, %s: Stamina regeneration in combat 11/s (0.1 + 2 x 0.005) (%s)" % (label, rs, st), st == ["100/s", "11/s"], st)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()
