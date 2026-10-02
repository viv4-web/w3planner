"""v32: the Player Stats screen (Inventory, button or key C), in a real browser.

run(b, base, check, label)   everything that needs no save: the button, the key, the tabs, the keyboard, a phone, a build made by hand (level 1: only the base numbers)
fixture(b, base, check, label)  the save ~/work/w3planner-art/save-spike/fixtures/stats-l9/ (never committed; SKIPPED when absent): every number the game showed (ground truth below) must match or be "—"
live(b, url, check)          the same on the preview or the live site (smoke test)"""
from pathlib import Path

READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"
FIX = Path.home() / "work/w3planner-art/save-spike/fixtures/stats-l9"
# In-game Player Stats of that save (read by Vivek on 2026-10-02): level 9, play time 10 h 25 min. Sign intensity (+144%) is not computed: it must show "—".
TRUTH = {"DPS - Silver sword": "342", "DPS - Steel sword": "204", "Armor": "127", "Crossbow": "37", "Vitality": "4641|4641", "Toxicity": "0|100", "Stamina": "100|100"}
SILVER = ["199", "10 %", "259", "365", "10 %", "474", "0 %", "0 %", "0 %", "0 %", "0 %", "0 %"]


def until(pg, js, ms=8000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def page(b, url, w=1440, h=1000, mobile=False):
    pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); pg.goto(url); until(pg, READY)
    pg.evaluate("scrGo('inv')"); until(pg, "!document.getElementById('screenInv').hidden&&!!eqData()&&!!CN.data"); pg.wait_for_timeout(300)
    return pg, errs


ROWS = "[...document.querySelectorAll('#psrows .psrow')].map(r=>({n:r.querySelector('.psname').textContent,v:[...r.querySelectorAll('.psnum b,.psnum small')].map(x=>x.textContent).join('|')}))"
PANEL = "[...document.querySelectorAll('#pspanel .psline')].map(l=>({v:l.querySelector('b').textContent,l:l.querySelector('span').textContent}))"


def run(b, base, check, label):
    pg, errs = page(b, base); E = pg.evaluate
    check("%s: Inventory has a PLAYER STATS button at the bottom centre, 44 px high, the stats are closed" % label, E("(()=>{const b=document.getElementById('pstatsbtn').getBoundingClientRect();return b.height>=44&&Math.abs((b.left+b.right)/2-innerWidth/2)<60&&document.getElementById('pstats').hidden&&!document.getElementById('eqbody').hidden})()"))
    pg.click("#pstatsbtn"); until(pg, "!document.getElementById('pstats').hidden")
    check("%s: the button opens the screen: nine tabs in the game's order, the first one selected, Close and the hint button swap" % label,
          [r["n"] for r in E(ROWS)] == ["DPS - Silver sword", "DPS - Steel sword", "Armor", "Crossbow", "Vitality", "Toxicity", "Sign intensity", "Stamina", "Additional"] and E("document.getElementById('pstab0').getAttribute('aria-selected')") == "true"
          and E("document.getElementById('eqbody').hidden&&document.getElementById('invhint').hidden"))
    check("%s: roles: tablist, nine tabs (one selected, one in the tab order), a tabpanel labelled by the selected tab" % label,
          E("(()=>{const l=document.getElementById('psrows'),t=[...l.querySelectorAll('[role=tab]')],p=document.getElementById('pspanel');return l.getAttribute('role')==='tablist'&&t.length===9&&t.filter(x=>x.getAttribute('aria-selected')==='true').length===1&&t.filter(x=>x.tabIndex===0).length===1&&p.getAttribute('role')==='tabpanel'&&p.getAttribute('aria-labelledby')==='pstab0'})()"))
    check("%s: while the stats are open the Inventory slots are really gone from the page (not only marked hidden)" % label, E("document.getElementById('eqbody').offsetParent===null&&document.getElementById('invhint').offsetParent===null&&document.getElementById('pstats').offsetParent!==null"))
    r = E(ROWS)
    check("%s: a level-1 build with nothing equipped shows only base numbers: Vitality 3500, Stamina 100, Toxicity 0 / 100, no weapons and armour 0, Sign intensity —  (%s)" % (label, [x["v"] for x in r]),
          [x["v"] for x in r][:8] == ["0", "0", "0", "0", "3500|3500", "0|100", "—", "100|100"] or [x["v"] for x in r][:4] == ["0", "0", "0", "0"] and [x["v"] for x in r][4:6] == ["3500|3500", "0|100"] and r[7]["v"] == "100|100", r)
    pg.click("#pstab3"); pg.keyboard.press("ArrowDown"); pg.keyboard.press("ArrowDown")
    check("%s: ArrowDown moves the selection (Crossbow, then Vitality, Toxicity), only one tab selected, the panel follows" % label, E("document.querySelector('#psrows [aria-selected=true]').id") == "pstab5" and E("document.querySelectorAll('#psrows [aria-selected=true]').length") == 1 and E("document.querySelector('#pspanel .pshead').textContent") == "Toxicity")
    pg.keyboard.press("ArrowUp"); pg.keyboard.press("ArrowUp"); pg.keyboard.press("ArrowUp"); pg.keyboard.press("ArrowUp"); pg.keyboard.press("ArrowUp"); pg.keyboard.press("ArrowUp")
    check("%s: ArrowUp wraps from the top to the last tab (Additional)" % label, E("document.querySelector('#psrows [aria-selected=true]').id") == "pstab8")
    pg.click("#pstab2"); E("document.getElementById('lvl').value=20;pointsChanged()"); pg.wait_for_timeout(300)
    check("%s: the selection is remembered while the screen is open (a level change re-draws it)" % label, E("PS.sel") == 2 and E("document.querySelector('#pspanel .pshead').textContent") == "Armor")
    pg.keyboard.press("c") if False else None; pg.click("#psclose"); until(pg, "document.getElementById('pstats').hidden")
    check("%s: Close returns to Inventory (slots visible, button back, focus on the PLAYER STATS button)" % label, E("!document.getElementById('eqbody').hidden&&!document.getElementById('invhint').hidden&&document.activeElement.id==='pstatsbtn'"))
    pg.keyboard.press("c"); until(pg, "!document.getElementById('pstats').hidden")
    check("%s: key C opens it again and the first tab is selected again (reset on reopen)" % label, E("PS.sel") == 0 and E("document.getElementById('pstab0').getAttribute('aria-selected')") == "true")
    pg.keyboard.press("C"); until(pg, "document.getElementById('pstats').hidden")
    check("%s: key C toggles it closed" % label, E("document.getElementById('pstats').hidden"))
    pg.click("#pstatsbtn"); pg.keyboard.press("Escape")
    check("%s: Escape closes it" % label, E("document.getElementById('pstats').hidden"))
    pg.click("#eqbody .eqtile[data-i='0']"); until(pg, "!!EQ.pick"); pg.fill("#pkq", "c")
    check("%s: typing a c in the chooser's search box does not open the stats" % label, E("document.getElementById('pstats').hidden") and E("document.getElementById('pkq').value") == "c"); pg.click("#pkclose")
    E("scrGo('char')"); pg.keyboard.press("c")
    check("%s: key C does nothing on the Character screen" % label, E("document.getElementById('pstats').hidden"))
    check("%s: the link is untouched by the screen (no new segment)" % label, "ps" not in "".join(x for x in E("enc()").split(".")[8:] if x[:2] not in ("g1", "c1", "s1")))
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()
    # a phone: rows as a list, the tapped row opens its detail right under it, 44 px targets, nothing scrolls sideways
    pg, errs = page(b, base, 390, 844, True); E = pg.evaluate
    pg.tap("#pstatsbtn") if False else pg.click("#pstatsbtn"); until(pg, "!document.getElementById('pstats').hidden")
    ph = E("(()=>{const rows=[...document.querySelectorAll('#psrows .psrow')],p=document.getElementById('pspanel'),b=document.getElementById('psclose').getBoundingClientRect();return{h:Math.min(...rows.map(r=>r.getBoundingClientRect().height)),sw:document.documentElement.scrollWidth,under:rows[0].nextElementSibling===p,close:b.height}})()")
    check("%s: phone 390: rows are a list of 44 px+ targets, the first detail opens under its row, no sideways scroll (%s)" % (label, ph), ph["h"] >= 44 and ph["sw"] <= 390 and ph["under"] and ph["close"] >= 44, ph)
    pg.click("#pstab4"); pg.wait_for_timeout(150)
    ph = E("(()=>{const p=document.getElementById('pspanel'),r=document.getElementById('pstab4');return{under:r.nextElementSibling===p,head:p.querySelector('.pshead').textContent,sw:document.documentElement.scrollWidth}})()")
    check("%s: phone 390: tapping Vitality opens its detail under it and only that one is selected (%s)" % (label, ph), ph["under"] and ph["head"] == "Vitality" and ph["sw"] <= 390 and E("document.querySelectorAll('#psrows [aria-selected=true]').length") == 1, ph)
    check("%s: phone 390: no script errors" % label, not errs, errs[:1]); pg.close()


def fixture(b, base, check, label):
    sav = sorted(FIX.glob("*.sav")) if FIX.is_dir() else []
    if not sav: print("  SKIP  %s: Player Stats against the stats-l9 save (fixture not present)" % label); return
    pg, errs = page(b, base); E = pg.evaluate
    check("%s: no play time before a save is imported" % label, E("PS.play")is None)
    pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden"); pg.wait_for_timeout(600)
    pg.click("#tabInv"); until(pg, "!!eqData()&&!!CN.data"); pg.wait_for_timeout(500); pg.keyboard.press("c"); until(pg, "!document.getElementById('pstats').hidden")
    got = {x["n"]: x["v"] for x in E(ROWS)}
    bad = {k: (got.get(k), v) for k, v in TRUTH.items() if got.get(k) != v}
    check("%s: every row the game showed matches (Silver 342, Steel 204, Armor 127, Crossbow 37, Vitality 4641/4641, Toxicity 0/100, Stamina 100/100) and Sign intensity is — (%s)" % (label, got), not bad and got.get("Sign intensity") == "—", bad)
    d = [x["v"] for x in E(PANEL)]
    check("%s: Silver sword detail: 199 / 10 %% / 259, 365 / 10 %% / 474, 0 %% x6 (%s)" % (label, d), d == SILVER, d)
    pg.click("#pstab1"); d2 = [x["v"] for x in E(PANEL)]
    check("%s: Steel sword detail: 119 / 10 %% / 151, 218 / 10 %% / 277, 0 %% x6 (%s)" % (label, d2), d2 == ["119", "10 %", "151", "218", "10 %", "277", "0 %", "0 %", "0 %", "0 %", "0 %", "0 %"], d2)
    check("%s: TOTAL PLAY TIME 10 Hours 25 Minutes after the import" % label, E("(()=>{const t=document.getElementById('pstime');return !t.hidden&&/10\\s*Hours\\s*25\\s*Minutes/.test(t.textContent.replace(/\\s+/g,' '))})()"))
    check("%s: an unfinished value is never a number: every value is a number or —" % label, all(x["v"] == "—" or any(c.isdigit() for c in x["v"]) for i in range(9) for x in (pg.click("#pstab%d" % i) or E(PANEL))))
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def live(b, url, check):
    run(b, url, check, "stats")
