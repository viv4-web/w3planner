"""v32: the Player Stats screen (top-bar button on every tab, key C), in a real browser.

run(b, base, check, label)      everything that needs no save: the button on every tab, the key, the tabs, the keyboard, a phone, a planned build with ranges, a level-1 build (only the base numbers)
fixture(b, base, check, label)  two saves (never committed; SKIPPED when absent): ~/work/w3planner-art/save-spike/fixtures/stats-l9/ and stats-l9b/: every number the game showed must match, or be "—"
live(b, url, check)             run() on the preview or the live site (smoke test)"""
from pathlib import Path

READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"
FIXD = Path.home() / "work/w3planner-art/save-spike/fixtures"
# In-game Player Stats, read by Vivek. Sign intensity (+144% / +191%) is not computed: it must show "—".
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
    check("%s: a level-1 build with nothing equipped shows only base numbers: Vitality 3500, Stamina 100, Toxicity 0 / 100, no weapons, armour 0, Sign intensity — (%s)" % (label, [x["v"] for x in r]),
          [x["v"] for x in r][:4] == ["0", "0", "0", "0"] and r[4]["v"] == "3500|3500" and r[5]["v"] == "0|100" and r[6]["v"] == "—" and r[7]["v"] == "100|100", r)
    pg.click("#pstab4"); d = [(x["v"], x["l"]) for x in E(PANEL)]
    check("%s: a level-1 build: Vitality regeneration 1/s and 1/s in the game's words, in the game's order (%s)" % (label, d), d == [("1/s", "Vitality regeneration outside of combat"), ("1/s", "Vitality regeneration per enemy killed during combat")], d)
    pg.click("#pstab7"); d = [(x["v"], x["l"]) for x in E(PANEL)]
    check("%s: Stamina: regeneration out of combat 100/s, in combat — (not matched with the game yet) (%s)" % (label, d), d == [("100/s", "Stamina regeneration out of combat"), ("—", "Stamina regeneration in combat")], d)
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
        check("%s [%s]: every row the game showed matches and Sign intensity is — (%s)" % (label, sub, got), not bad and got.get("Sign intensity") == "—", bad)
        dd = [x["v"] for x in E(PANEL)]
        check("%s [%s]: Silver sword detail (%s)" % (label, sub, dd), dd == silver, dd)
        pg.click("#pstab4"); v = [(x["v"], x["l"]) for x in E(PANEL)]
        check("%s [%s]: Vitality regeneration 1/s and 1/s (%s)" % (label, sub, v), v == [("1/s", "Vitality regeneration outside of combat"), ("1/s", "Vitality regeneration per enemy killed during combat")], v)
        pg.click("#pstab7"); v = [x["v"] for x in E(PANEL)]
        check("%s [%s]: Stamina regeneration out of combat 100/s, in combat — (%s)" % (label, sub, v), v == ["100/s", "—"], v)
        pg.click("#pstab8"); v = [x["v"] for x in E(PANEL)]
        check("%s [%s]: Additional: herbs, instant kill, human and monster experience all 0 %% (%s)" % (label, sub, v), v == ["0 %"] * 4, v)
        check("%s [%s]: TOTAL PLAY TIME %s" % (label, sub, play), E("(p=>{const t=document.getElementById('pstime');return !t.hidden&&t.textContent.replace(/\\s+/g,' ').includes(p)})", play))
        eff = E("document.getElementById('pseff').textContent")
        check("%s [%s]: the active effects of the save are named (%s)" % (label, sub, eff), (("Enhanced Weapons" in eff and "Quen Sign" in eff) if effects else not eff), eff)
        check("%s [%s]: every value is a number, a range or —" % (label, sub), all(x["v"] == "—" or any(c.isdigit() for c in x["v"]) for i in range(9) for x in (pg.click("#pstab%d" % i) or E(PANEL))))
        check("%s [%s]: no script errors" % (label, sub), not errs, errs[:1]); pg.close()


def live(b, url, check):
    run(b, url, check, "stats")
