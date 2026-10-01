"""The Equipment panel in a real browser: layout, lazy data, chooser for every weapon slot, tooltip with tiers, set bonuses, Equip set, ruleset switch,
keyboard, touch layout, links. Used by tests/run_all.py (online and offline builds) and tests/smoke.py (preview and production)."""

READY = "typeof eqData==='function'&&!!eqData()&&!!document.querySelector('#eqbody .eqtile[data-i]')"
KEYS = "Object.keys(window.W3DATA||{}).map(k=>k+'.js')"   # the data files that were loaded (a script sets W3DATA.<name>)
BOX = "(sel)=>{const e=document.querySelector(sel);if(!e)return null;const r=e.getBoundingClientRect();return{l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)}}"
CHEST, GLOVES, TROUSERS, BOOTS, STEEL, SILVER = 4, 5, 6, 7, 0, 1
EQ_CHEST, EQ_SILVER = CHEST, SILVER


def until(pg, js, ms=6000):
    """Poll an expression in the page (wait_for_function would evaluate a string, which the page's CSP forbids)."""
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


GEOM = """()=>{const B=s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return{l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)}};
 const rows=s=>[...new Set([...document.querySelectorAll(s)].map(e=>Math.round(e.getBoundingClientRect().top)))].length;
 const tiles=[...document.querySelectorAll('#eqbody .eqtile')].map(t=>{const r=t.getBoundingClientRect();return[r.width,r.height]});
 return{tree:B('#treePanel'),mut:B('#slots'),info:B('#info'),link:(B('#shareRow')&&B('#shareRow').w?B('#shareRow'):B('#importRow')),skills:B('.skillsarea'),eq:B('#eqpanel'),page:B('.page'),c1:B('.eqc1'),c2:B('.eqc2'),c3:B('.eqc3'),vd:B('.vdiv'),
  sw:document.documentElement.scrollWidth,vw:innerWidth,wrows:rows('.eqw .eqslot'),arows:rows('.eqarm .eqslot'),maxratio:Math.max(...tiles.map(t=>t[0]/t[1])),mintile:Math.min(...tiles.map(t=>Math.min(t[0],t[1])))}}"""


def layout(b, base, check, label):
    """The page grid at seven widths (see CLAUDE.md, Equipment panel)."""
    for w, h in ((2560, 1259), (1920, 1080), (1440, 900), (1280, 800), (1024, 768), (768, 900), (390, 844)):
        pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=w < 600, has_touch=w < 600); pg.goto(base); until(pg, READY); g = pg.evaluate(GEOM); tag = "%s: at %d px" % (label, w)
        check("%s: no sideways scroll, and no slot tile wider than 1.05x its height" % tag, g["sw"] <= g["vw"] and g["maxratio"] <= 1.05, [g["sw"], g["vw"], g["maxratio"]])
        if w >= 1440:
            tree, mut, eq, sk = g["tree"], g["mut"], g["eq"], g["skills"]
            check("%s: [tree] [mutations] | [equipment]: tree left, mutations beside it, divider, equipment right; skill detail and link bar span the whole skills area" % tag,
                  tree["l"] < 120 and tree["r"] <= mut["l"] and mut["r"] <= g["vd"]["l"] and g["vd"]["r"] <= eq["l"] and abs(g["info"]["l"] - sk["l"]) <= 2 and abs(g["info"]["r"] - sk["r"]) <= 2 and abs(g["link"]["r"] - sk["r"]) <= 2 and g["info"]["t"] >= max(tree["b"], mut["b"]) - 40, g)
            check("%s: the skills area and the equipment panel have the same height (%d, %d); the page uses its width (equipment right edge %d of %d)" % (tag, sk["h"], eq["h"], eq["r"], g["page"]["r"]),
                  abs(sk["h"] - eq["h"]) <= 2 and eq["r"] >= 0.95 * g["page"]["r"] and g["page"]["w"] <= 2400 and abs(eq["w"] - min(560, max(380, 0.28 * w))) <= 3, g)
            check("%s: the tree is %d px wide and the weapons are one row of 4, the armor %s" % (tag, tree["w"], "one row of 5" if g["arows"] == 1 else "3 + 2"), g["wrows"] == 1 and g["arows"] == (1 if g["c2"]["w"] >= 392 else 2), [g["wrows"], g["arows"], g["c2"]["w"]])
        elif w >= 1024:
            eq, sk = g["eq"], g["skills"]
            check("%s: the skills (tree beside mutations) on top, the equipment panel below at full width in 3 columns (weapons | armor | sets and stats)" % tag,
                  g["tree"]["r"] <= g["mut"]["l"] and eq["t"] >= sk["b"] - 2 and abs(eq["l"] - sk["l"]) <= 2 and abs(eq["r"] - sk["r"]) <= 2 and g["c1"]["r"] <= g["c2"]["l"] and g["c2"]["r"] <= g["c3"]["l"] and g["vd"]["h"] <= 2, g)
        elif w >= 600:
            check("%s: everything stacked: tree, mutations, detail, equipment; 4 slots per row" % tag, g["tree"]["b"] <= g["mut"]["t"] and g["mut"]["b"] <= g["info"]["t"] and g["info"]["b"] <= g["eq"]["t"] and g["wrows"] == 1, g)
        else:
            check("%s: stacked, slots 3 per row (weapons %d rows, armor %d rows), tap targets at least 44 px" % (tag, g["wrows"], g["arows"]), g["tree"]["b"] <= g["mut"]["t"] and g["info"]["b"] <= g["eq"]["t"] and g["wrows"] == 2 and g["arows"] == 2 and g["mintile"] >= 44
                  and pg.evaluate("[...document.querySelectorAll('#eqpanel .eqrs .btn')].every(b=>b.getBoundingClientRect().height>=44)")
                  and pg.evaluate("(()=>{const x=document.querySelector('.eqx');return !x||x.getBoundingClientRect().width-2*parseFloat(getComputedStyle(x,'::before').top)>=44})()"), g)
            pg.click('#eqbody .eqtile[data-i="4"]'); pg.wait_for_selector("#pkgrid .pktile"); full = pg.evaluate("(()=>{const r=document.querySelector('.eqpmodal').getBoundingClientRect();return[Math.round(r.width),Math.round(r.height),innerWidth,innerHeight]})()")
            check("%s: the chooser is full-screen and its tiles are at least 44 px" % tag, full[0] >= full[2] - 2 and full[1] >= full[3] - 2 and pg.evaluate("[...document.querySelectorAll('.pktile')].every(t=>t.getBoundingClientRect().height>=44)"), full)
            check("%s: ... and the Equipment button jumps to the panel" % tag, pg.evaluate("getComputedStyle(document.getElementById('eqbtn')).display") != "none")
        pg.close()


LEVELS = {"ng": {"Lynx Armor": 17, "Lynx Armor 1": 23, "Lynx Armor 2": 29, "Lynx Armor 3": 34, "Lynx Armor 4": 40, "Lynx School Crossbow": 29, "q702_vampire_mask": 1, "Blunt Bolt Legendary": 1},
          "ng_plus": {"Lynx Armor": 47, "Lynx Armor 1": 53, "Lynx Armor 2": 59, "Lynx Armor 3": 64, "Lynx Armor 4": 70, "NGP Lynx Armor 4": 40, "Lynx School Crossbow": 29, "q702_vampire_mask": 1}}
# hand-calculated from the game's scripts (GetItemLevel, inventoryComponent.ws:305 and gameParams.ws:917; see the report): armor 120/150/180/205/240 -> 17/23/29/34/40 (Grandmaster has the EP1 tag, minus 1),
# NG+ armor 270/300/330/355/390 -> 47/53/59/64/70, crossbow attack power x2.25 -> 32 - 1 - 2 = 29, masks have no branch (level 0 -> 1), the first test of 'Blunt Bolt Legendary' (5) wins -> 1


SCALE = """()=>{const R=s=>{const e=document.querySelector(s);return e?e.getBoundingClientRect():null};
 const n=R('#treePanel .node .frame'),ts=R('#treePanel svg'),ms=R('#slots'),info=R('#info'),sr=R('#shareRow'),link=sr&&sr.width?sr:R('#importRow');
 const w=[...document.querySelectorAll('.eqw .eqtile')].map(e=>e.getBoundingClientRect().width),a=[...document.querySelectorAll('.eqarm .eqtile')].map(e=>e.getBoundingClientRect().width);
 return{vh:innerHeight,y:scrollY,node:n.width,ts:ts.width,ms:ms.width,tt:R('#treePanel').top,mt:ms.top,info:info.bottom,link:link.bottom,w:w,a:a}}"""


def scalecheck(b, base, check, label):
    """One scale drives the tree and the mutation grid (min of width, height and 1.0 = native icon size); the tile size is shared; the detail box and link bar stay in the first screen."""
    for w, h in ((2560, 1440), (1920, 1080), (1440, 900), (1280, 800)):
        pg = b.new_page(viewport={"width": w, "height": h}); pg.goto(base); until(pg, READY); pg.wait_for_timeout(300); g = pg.evaluate(SCALE); tag = "%s: at %dx%d" % (label, w, h)
        st, sm = g["ts"] / 700, g["ms"] / 717.5
        check("%s: the detail box and the link bar are fully inside the window without scrolling (%d, %d of %d)" % (tag, g["info"], g["link"], h), g["y"] == 0 and g["info"] <= h and g["link"] <= h, g)
        check("%s: tree icons are not upscaled (tile %.1f px, native 84 at scale 1)" % (tag, g["node"]), g["node"] <= 84 + 1.5, g)
        check("%s: tree and mutation grid have the same scale (%.3f, %.3f) and start at the same height" % (tag, st, sm), abs(st - sm) <= 0.01 * max(st, sm) and abs(g["tt"] - g["mt"]) <= 6, g)
        check("%s: weapon and armor tiles are the same size (%s, %s)" % (tag, sorted(set(round(x) for x in g["w"])), sorted(set(round(x) for x in g["a"]))), max(g["w"] + g["a"]) - min(g["w"] + g["a"]) <= 1.5, g)
        pg.close()


URSINE = ["Bear School steel sword 4", "Bear School silver sword 4", "Bear School Crossbow", "Broadhead Bolt", "Bear Armor 4", "Bear Gloves 5", "Bear Pants 5", "Bear Boots 5", "q702_vampire_mask"]   # all nine slots; the last card is the mask


def gear(pg, ids):
    return pg.evaluate("""(ids=>{const d=eqData();EQ_SLOTS.forEach((s,i)=>{const it=ids[i]&&d.byId.get(ids[i]);S.gear[i]=it&&it.slot===s?it.n:0});save();eqRender(true);return S.gear.filter(x=>x).length})""", ids)


def scrollcheck(b, base, check, label):
    """The panel's scroller ends at the panel's bottom edge, so the last stats card is reachable at every size; the header stays; stacked layouts have no inner scroll."""
    for w, h in ((2560, 1440), (1920, 1080), (1440, 900), (1280, 800), (390, 844)):
        pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=w < 600, has_touch=w < 600); pg.goto(base); until(pg, READY); pg.fill("#lvl", "100"); n = gear(pg, URSINE); pg.wait_for_timeout(300); tag = "%s: at %dx%d" % (label, w, h)
        if w >= 1440:
            before = pg.evaluate("document.querySelector('#eqpanel .eqrs').getBoundingClientRect().top")
            r = pg.evaluate("""()=>{const b=document.getElementById('eqbody');b.scrollTop=1e6;const A=document.getElementById('eqpanel').getBoundingClientRect(),B=b.getBoundingClientRect(),c=[...document.querySelectorAll('#eqbody .eqitem')].pop().getBoundingClientRect();
              return{n:document.querySelectorAll('#eqbody .eqitem').length,panelB:A.bottom,bodyB:B.bottom,lastB:c.bottom,lastT:c.top,bodyT:B.top,head:document.querySelector('#eqpanel .eqrs').getBoundingClientRect().top,scrolls:b.scrollHeight>b.clientHeight,end:Math.abs(b.scrollHeight-b.clientHeight-b.scrollTop)<=1}}""")
            check("%s: scrolled to the end, the last stats card (%d cards) is fully inside the panel's visible box" % (tag, r["n"]), n == 9 and r["n"] == 9 and r["end"] and r["lastB"] <= r["bodyB"] + 0.5 and r["lastB"] <= r["panelB"] and r["lastT"] >= r["bodyT"], r)
            check("%s: the scroller ends at the panel's bottom edge (%.0f, %.0f) and the header (title, level, mode toggle) stays put (%.0f, %.0f)" % (tag, r["bodyB"], r["panelB"], before, r["head"]), abs(r["panelB"] - r["bodyB"]) <= 3 and abs(before - r["head"]) <= 0.5 and r["scrolls"], r)
        else:
            r = pg.evaluate("""()=>{const b=document.getElementById('eqbody');window.scrollTo(0,1e7);const c=[...document.querySelectorAll('#eqbody .eqitem')].pop().getBoundingClientRect();return{inner:b.scrollHeight>b.clientHeight+1,ov:getComputedStyle(b).overflowY,lastB:c.bottom,vh:innerHeight}}""")
            check("%s: stacked: no inner scroll, and the last stats card is reachable with the page scroll (bottom %d of %d)" % (tag, r["lastB"], r["vh"]), not r["inner"] and r["ov"] == "visible" and 0 < r["lastB"] <= r["vh"], r)
        pg.close()
    pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.goto(base); until(pg, READY); pg.fill("#lvl", "100"); E = pg.evaluate
    gear(pg, URSINE[:3] + ["", "Bear Armor 4", "Bear Gloves 5", "Bear Pants 5", "Bear Boots 5"]); h3 = E("document.querySelector('.eqset h3').textContent"); notes = E("[...document.querySelectorAll('.eqset p.dim')].map(p=>p.textContent)"); cb = E("eqCur(2).name")
    check("%s: Ursine swords + 4 armor + the Basic crossbow: '6 counted, 7 worn', and the crossbow is named with the real reason (%s)" % (label, notes), "6 counted, 7 worn" in h3 and len(notes) == 1 and notes[0] == cb + " is not counted: crossbows and bolts carry no set bonus tag in the game data, so they never count.", [h3, notes, cb])
    gear(pg, ["Bear School steel sword 3", "Bear School silver sword 4", "", "", "Bear Armor 4", "Bear Gloves 5", "Bear Pants 5", "Bear Boots 5"]); notes = E("[...document.querySelectorAll('.eqset p.dim')].map(p=>p.textContent)")
    check("%s: a lower-tier piece is not counted because of its tier, and the note says which tier counts (%s)" % (label, notes), len(notes) == 1 and "only the Grandmaster tier carries the set bonus tag" in notes[0] and "steel sword" in notes[0].lower(), notes)
    pg.close()


GUTTER = """()=>{const b=document.getElementById('eqbody'),cs=getComputedStyle(b),r=b.getBoundingClientRect();
 const sbw=b.offsetWidth-b.clientWidth-parseFloat(cs.borderLeftWidth)-parseFloat(cs.borderRightWidth);
 const edge=r.left+parseFloat(cs.borderLeftWidth)+b.clientWidth-parseFloat(cs.paddingRight);   /* the content box's right edge, left of the scrollbar */
 const v=[...b.querySelectorAll('.eqgrid b')].map(e=>{const q=e.getBoundingClientRect();return{r:q.right,h:q.height,t:e.textContent}});
 const lh=Math.max(...v.map(x=>x.h));return{n:v.length,sbw:sbw,pr:parseFloat(cs.paddingRight),edge:edge,over:v.filter(x=>x.r>edge+0.5).map(x=>x.t+'@'+x.r).slice(0,5),maxr:Math.max(...v.map(x=>x.r)),wrapped:v.filter(x=>x.h>lh*1.5).length,gutter:cs.scrollbarGutter,pcts:v.filter(x=>/%/.test(x.t)).length}}"""


def guttercheck(b, base, check, label):
    """The scrollbar never sits on the stat values: every value's right edge is inside the scroller's content box (left of the scrollbar and its gap), and a value like '11 %' stays on one line."""
    for w, h in ((2560, 1440), (1920, 1080), (1440, 900), (1280, 800)):
        pg = b.new_page(viewport={"width": w, "height": h}); pg.goto(base); until(pg, READY); pg.fill("#lvl", "100"); gear(pg, URSINE); pg.wait_for_timeout(300); g = pg.evaluate(GUTTER)
        check("%s: at %dx%d (%s): %d stat values, all end inside the scroller's content box (right edge %.1f, scrollbar %d px, padding %d px, gutter %s), %d with a %% sign, none wrapped" % (label, w, h, "scrolling panel" if w >= 1440 else "stacked, no inner scroll", g["n"], g["edge"], g["sbw"], g["pr"], g["gutter"], g["pcts"]),
              g["n"] > 20 and g["pcts"] > 0 and not g["over"] and (w < 1440 or g["pr"] >= 12) and g["wrapped"] == 0, g)
        pg.close()


def levelcheck(b, base, check, label, pg):
    """The level requirement: the game blocks GetItemLevel(item) > GetLevel() (r4Player.ws:11723). Only the Level field counts."""
    E = pg.evaluate

    def opener(i, ident):
        pg.click('#eqbody .eqtile[data-i="%d"]' % i); pg.wait_for_selector("#pkgrid .pktile"); E("(id=>{EQ.pick.sel=eqData().byId.get(id);eqPickRender()})", ident)

    def start(level, bonus=0):
        pg.keyboard.press("Escape") if not E("document.getElementById('eqpick').hidden") else None
        pg.fill("#lvl", str(level)); pg.fill("#bonuspts", str(bonus)); E("(()=>{S.gear.fill(0);save();eqRender(true)})()")
    if E("S.rs") != "ng": pg.click('#eqpanel [data-rs="ng"]'); until(pg, "S.rs==='ng'")
    start(1); opener(EQ_CHEST, "Lynx Armor 1")
    side = E("document.getElementById('pkside').innerText"); why = E("(document.getElementById('pkwhy')||{}).textContent||''")
    check("%s: Level 1, Feline Enhanced chest: Equip is disabled and says 'Requires level 23'; the level is red in the tooltip and on the tile" % label,
          E("document.getElementById('pkequip').disabled") and why == "Requires level 23" and E("document.querySelectorAll('#pkside .eqt-lvl.bad').length") == 1 and E("document.querySelectorAll('#pkgrid .pktile.low .pkreq').length") > 0, [why, side[:60]])
    pg.dblclick("#pkgrid .pktile.sel"); pg.wait_for_timeout(100)
    check("%s: ... double-click and Enter do not equip it either" % label, E("S.gear[4]") == 0 and not E("document.getElementById('eqpick').hidden"))
    pg.focus("#pkgrid .pktile.sel"); pg.keyboard.press("Enter"); pg.wait_for_timeout(100)
    check("%s: ... (Enter)" % label, E("S.gear[4]") == 0)
    start(23); opener(EQ_CHEST, "Lynx Armor 1")
    check("%s: Level raised to its requirement (23): Equip is enabled and works" % label, not E("document.getElementById('pkequip').disabled") and E("!document.getElementById('pkwhy')"))
    pg.click("#pkequip"); pg.wait_for_timeout(100)
    check("%s: ... the chest is equipped" % label, E("S.gear[4]") > 0 and E("document.querySelectorAll('.eqslot.low').length") == 0)
    start(1, 100); opener(EQ_CHEST, "Lynx Armor 1")
    check("%s: Level 1 with 100 bonus points: still disabled (bonus points never count)" % label, E("document.getElementById('pkequip').disabled") and E("S.gear[4]") == 0 and E("document.getElementById('total').textContent") == "100")
    # Equip set between tiers: Mastercrafted (34) at Level 33 equips what the level allows (the Basic crossbow, 29) and lists the rest
    start(33); opener(EQ_CHEST, "Lynx Armor 3")
    note = E("document.getElementById('pkside').innerText")
    check("%s: Equip set at Level 33 on a Mastercrafted piece (34): the note names the skipped pieces with their levels" % label, "Skipped, level too low" in note and "Chest armor (requires level 34)" in note and "Steel sword (requires level 34)" in note, note[-260:])
    pg.click("#pkequipset"); pg.wait_for_timeout(200)
    have = E("(()=>{const o={};EQ_SLOTS.forEach((s,i)=>{const it=eqCur(i);if(it)o[s]=it.id});return o})()")
    check("%s: ... only the pieces the level allows are equipped (the crossbow); the others stay empty" % label, have == {"crossbow": "Lynx School Crossbow"}, have)
    start(34); opener(EQ_CHEST, "Lynx Armor 3"); pg.click("#pkequipset"); pg.wait_for_timeout(200)
    check("%s: ... at Level 34 the whole Mastercrafted set goes on, with no 'skipped' note" % label, E("EQ_SLOTS.map((s,i)=>eqCur(i)).filter(it=>it&&it.set==='lynx').length") == 7)
    # equip at a high level, then lower Level: the gear stays, marked
    start(100); opener(EQ_CHEST, "Lynx Armor 4"); pg.click("#pkequip"); pg.wait_for_timeout(100)
    pg.fill("#lvl", "30"); until(pg, "!!document.querySelector('.eqslot.low')")
    low = E("[S.gear[4]>0, document.querySelectorAll('.eqslot.low').length, (document.querySelector('.eqslot.low .eqbadge')||{}).textContent, (document.querySelector('.eqwarn')||{}).textContent||'']")
    border = E("getComputedStyle(document.querySelector('.eqslot.low .eqtile')).borderTopColor")
    check("%s: lowering Level to 30 keeps the Grandmaster chest, marks the slot with a red border and 'Level too low', and adds a warning line" % label,
          low[0] and low[1] == 1 and low[2] == "Level too low" and "chest armor (level 40)" in low[3] and border.startswith("rgb(192, 57, 43)"), [low, border])
    code = E("document.getElementById('link').value").split("#")[-1]; want = E("[S.rs,S.gear.join(),lvl()]")
    q = b.new_page(); q.goto(base + "#" + code); until(q, READY); got = q.evaluate("[S.rs,S.gear.join(),lvl()]"); shown = q.evaluate("[document.querySelectorAll('.eqslot.low').length,!!document.querySelector('.eqwarn')]"); q.close()
    check("%s: the link round-trips both the level and the gear, and the reopened page shows the warning" % label, got == want and want[2] == 30 and want[1].split(",")[4] != "0" and shown == [1, True], [got, want, shown])
    pg.fill("#lvl", "40"); until(pg, "!document.querySelector('.eqslot.low')")
    check("%s: raising Level back to 40 clears the marks" % label, E("document.querySelectorAll('.eqwarn').length") == 0)
    # the required levels of the sample items, both rulesets, against the hand calculation in LEVELS
    for rs, want_lv in LEVELS.items():
        if E("S.rs") != rs: pg.click('#eqpanel [data-rs="%s"]' % rs); until(pg, "S.rs==='%s'&&!!eqData()" % rs)
        got = E("(l=>{const o={};Object.keys(l).forEach(k=>{const it=eqData().byId.get(k);o[k]=it?it.required_level:'missing'});return o})", want_lv)
        check("%s: required levels in %s match the scripts (%s)" % (label, rs, ", ".join("%s %s" % kv for kv in list(want_lv.items())[:3]) + ", ..."), got == want_lv, got)
    relic = E("(()=>{const it=eqData().byId.get('Wolf');return it?eqLevel(it).t:''})()"); pg.click('#eqpanel [data-rs="ng"]'); until(pg, "S.rs==='ng'"); relic = E("eqLevel(eqData().byId.get('Wolf')).t")
    check("%s: an autogen relic is never blocked (the level is rolled when it drops) and says 'Level varies'" % label, relic.startswith("Level varies") and not E("eqLow(eqData().byId.get('Wolf'))"), relic)
    start(100)


def run(b, base, check, label, quick=False):
    errs, events = [], []; pg = b.new_page(viewport={"width": 1400, "height": 950}); pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); E = pg.evaluate
    pg.on("load", lambda p: events.append("load")); pg.on("request", lambda r: events.append("data") if "/data/items" in r.url else None)
    pg.goto(base); check("%s: the panel shows right away and the equipment data loads after the page has loaded, only items.js and items_ng.js" % label, until(pg, READY) and E(KEYS) == ["items.js", "items_ng.js"] and events.index("load") < (events.index("data") if "data" in events else 99), [events[:4], E(KEYS)])
    layout(b, base, check, label); scalecheck(b, base, check, label); scrollcheck(b, base, check, label); guttercheck(b, base, check, label)
    pg.fill("#lvl", "100")      # the planner starts at Level 1 and the game blocks items above the level, so the walk-through below runs at the top level
    check("%s: weapons (steel, silver, crossbow, bolts) then armor (chest, gloves, trousers, boots, mask); one greyed strip \"Consumables & bombs, coming later\"" % label,
          E("[...document.querySelectorAll('#eqbody .eqw .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "steel,silver,crossbow,bolts" and E("[...document.querySelectorAll('#eqbody .eqarm .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "chest,gloves,trousers,boots,mask"
          and E("document.querySelector('#eqbody .eqstrip').textContent") == "Consumables & bombs, coming later" and E("document.querySelectorAll('#eqbody .eqstrip').length") == 1)
    # the chooser for EVERY weapon slot, and Equip
    for slot, i in (("steel", 0), ("silver", 1), ("bolts", 3), ("crossbow", 2)):
        pg.click('#eqbody .eqtile[data-i="%d"]' % i); pg.wait_for_selector("#pkgrid .pktile"); n = E("document.querySelectorAll('#pkgrid .pktile').length"); only = E("[...document.querySelectorAll('#pkgrid .pktile')].every(t=>EQ.rs[S.rs].byId.get(t.dataset.id).slot===EQ.pick.slot)")
        pg.click("#pkequip"); pg.wait_for_timeout(150)
        check("%s: the %s chooser lists %d items of that slot only, and Equip puts one in the slot" % (label, slot, n), n > 5 and only and E("S.gear[%d]" % i) > 0 and E("document.getElementById('eqpick').hidden") and E("document.querySelectorAll('#eqbody .eqslot.on')[%d]" % 0) is not None, (n, only))
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()")
    # chooser for the chest slot
    pg.click('#eqbody .eqtile[data-i="4"]'); pg.wait_for_selector("#pkgrid .pktile"); n_all = E("document.querySelectorAll('#pkgrid .pktile').length")
    pg.select_option("#pkset", "set:lynx"); sets_n = E("document.querySelectorAll('#pkgrid .pktile').length")
    pg.fill("#pkq", "grandmaster"); search_n = E("document.querySelectorAll('#pkgrid .pktile').length")
    check("%s: set filter and search narrow the list (%d, then %d of %d)" % (label, sets_n, search_n, n_all), 0 < search_n <= sets_n < n_all)
    tier_names = E("[...document.querySelectorAll('#pkside .eqchip')].map(c=>c.textContent).join()")
    check("%s: the tooltip has a tier selector from Basic to Grandmaster" % label, tier_names == "Basic,Enhanced,Superior,Mastercrafted,Grandmaster", tier_names)
    pg.click('#pkside .eqchip:has-text("Basic")'); basic = E("EQ.pick.sel.id"); pg.click('#pkside .eqchip:has-text("Grandmaster")'); top = E("EQ.pick.sel.id")
    check("%s: the tier chips switch the item" % label, basic != top and E("EQ.pick.sel.tier") == 5, [basic, top])
    E("document.getElementById('lvl').value=1;pointsChanged()"); pg.click('#pkside .eqchip:has-text("Grandmaster")')
    check("%s: 'Requires level' is red above the character level and plain at or below it" % label, E("!!document.querySelector('#pkside .eqt-lvl.bad')")); E("document.getElementById('lvl').value=100;pointsChanged()"); pg.click('#pkside .eqchip:has-text("Basic")')
    check("%s: ... (plain at level 100)" % label, not E("!!document.querySelector('#pkside .eqt-lvl.bad')"))
    check("%s: stats follow tooltip_settings.csv (a percentage line has 'NN %%', lines in the CSV order)" % label, E("(()=>{const l=[...document.querySelectorAll('#pkside .eqt-line')];return l.length>2&&l.some(x=>/\\d %$/.test(x.lastChild.textContent))})()"))
    pg.click("#pkequip"); pg.wait_for_timeout(200); got = E("S.gear[4]")
    check("%s: Equip puts the item in the slot, closes the chooser and the link has the gear segment" % label, got > 0 and E("document.getElementById('eqpick').hidden") and E("/\\.g1AA/.test(document.getElementById('link').value)"), got)
    # sets, bonuses (first playthrough: only Grandmaster pieces carry the set bonus tag)
    ids = ["Lynx Armor 4", "Lynx Gloves 5", "Lynx Pants 5", "Lynx Boots 5", "Lynx School steel sword 4", "Lynx School silver sword 4"]; slots = ["chest", "gloves", "trousers", "boots", "steel", "silver"]
    def put(k): E("(a)=>{const [ids,slots,k]=a;S.gear.fill(0);ids.slice(0,k).forEach((id,j)=>{S.gear[EQ_SLOTS.indexOf(slots[j])]=EQ.rs[S.rs].byId.get(id).n});save();eqRender(true)}", [ids, slots, k])
    put(2); two = E("document.querySelectorAll('.eqset li.lit').length"); put(3); three = E("document.querySelectorAll('.eqset li.lit').length"); put(6); six = E("document.querySelectorAll('.eqset li.lit').length")
    check("%s: the 3-piece bonus lights at 3 counted pieces and the 6-piece at 6 (lit: %d, %d, %d)" % (label, two, three, six), (two, three, six) == (0, 1, 2) and E("document.querySelector('.eqset h3').textContent").startswith("Feline"))
    check("%s: each equipped item's stats are listed, not summed" % label, E("document.querySelectorAll('#eqbody .eqitem').length") == 6)
    fs = E("[parseFloat(getComputedStyle(document.querySelector('#eqbody .eqgrid')).fontSize),parseFloat(getComputedStyle(document.querySelector('#eqbody .eqset li')).fontSize),parseFloat(getComputedStyle(document.querySelector('#info p')).fontSize)]")
    check("%s: the sets and item stats text is at least the body size of the skill detail box (%s)" % (label, fs), fs[0] >= fs[2] and fs[1] >= fs[2], fs)
    # autogen relic: no Equip set button
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()"); pg.click('#eqbody .eqtile[data-i="0"]'); pg.wait_for_selector("#pkgrid .pktile"); pg.fill("#pkq", "Wolf"); pg.wait_for_timeout(100)
    E("(()=>{EQ.pick.sel=EQ.rs.ng.byId.get('Wolf');eqPickRender()})()"); relic = E("document.getElementById('pkside').innerText")
    check("%s: an autogen relic shows its rolled ranges and 'Level varies', and has no Equip set button (absent, not disabled)" % label, "Level varies" in relic and " to " in relic and E("document.querySelectorAll('#pkequipset').length") == 0, relic[:80]); pg.keyboard.press("Escape")
    # Equip set, in New Game Plus where every tier carries the set bonus tag
    pg.click('#eqpanel [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'&&!!eqData()"); E("(()=>{S.gear.fill(0);save();eqRender(true)})()")
    pg.click('#eqbody .eqtile[data-i="4"]'); pg.wait_for_selector("#pkgrid .pktile"); E("(()=>{EQ.pick.sel=EQ.rs.ng_plus.byId.get('Lynx Armor 1');eqPickRender()})()")
    note = E("(document.querySelector('#pkside .pknote')||{}).textContent||''")
    check("%s: Enhanced Feline chest: Equip set is visible, says what it will do and names the tier fallback (the crossbow has only a Basic version)" % label, E("document.querySelectorAll('#pkequipset').length") == 1 and "6 pieces" not in note and "Nearest tier used" in note and "Crossbow" in note, note[:200])
    E("(()=>{window.__rs=0;const o=history.replaceState.bind(history);history.replaceState=(...a)=>{window.__rs++;return o(...a)};window.__hl=history.length})()")
    pg.click("#pkequipset"); pg.wait_for_timeout(200)
    want = {"chest": "Lynx Armor 1", "gloves": "Lynx Gloves 2", "trousers": "Lynx Pants 2", "boots": "Lynx Boots 2", "steel": "Lynx School steel sword 1", "silver": "Lynx School silver sword 1", "crossbow": "Lynx School Crossbow"}
    have = E("(()=>{const o={};EQ_SLOTS.forEach((s,i)=>{const it=eqCur(i);if(it)o[s]=it.id});return o})()")
    check("%s: Equip set equips all Feline armor, both swords and the crossbow at Enhanced (Basic where there is no Enhanced), and closes the chooser" % label, have == want and E("document.getElementById('eqpick').hidden"), [have, want])
    check("%s: ... the set card shows 6 counted pieces with both bonuses lit" % label, E("document.querySelectorAll('.eqset li.lit').length") == 2 and "6 counted" in E("document.querySelector('.eqset h3').textContent"), E("document.querySelector('.eqset h3').textContent"))
    check("%s: ... the link was written once and no history entry was added (%d write)" % (label, E("window.__rs")), E("window.__rs") == 1 and E("history.length") == E("window.__hl"))
    code = E("document.getElementById('link').value").split("#")[-1]; wanted = E("[S.rs,S.gear.join()]")
    q = b.new_page(); q.goto(base + "#" + code); until(q, READY); got_link = q.evaluate("[S.rs,S.gear.join()]"); shown = q.evaluate("document.querySelectorAll('#eqbody .eqslot.on').length"); q.close()
    check("%s: copy link, reload: the same set and the same mode" % label, got_link == wanted and shown == 7, [got_link, wanted, shown])
    # Equip set with the keyboard (Shift+Enter in the chooser grid), same-tier pieces replace what was there
    E("(()=>{S.gear.fill(0);S.gear[2]=EQ.rs.ng_plus.byId.get('Crossbow 1')?EQ.rs.ng_plus.byId.get('Crossbow 1').n:0;save();eqRender(true)})()")
    pg.focus('#eqbody .eqtile[data-i="4"]'); pg.keyboard.press("Enter"); pg.wait_for_selector("#pkgrid .pktile"); pg.select_option("#pkset", "set:bear"); pg.wait_for_timeout(150); pg.focus("#pkgrid .pktile >> nth=0"); pg.keyboard.press("Shift+Enter"); pg.wait_for_timeout(200)
    check("%s: Shift+Enter on a set item in the chooser equips the whole set (keyboard)" % label, E("EQ_SLOTS.map((s,i)=>eqCur(i)).filter(it=>it&&it.set==='bear').length") >= 6 and E("document.getElementById('eqpick').hidden"))
    # keyboard and right-click
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()"); pg.focus('#eqbody .eqtile[data-i="4"]'); pg.keyboard.press("Enter"); pg.wait_for_selector("#pkgrid .pktile"); pg.keyboard.press("Escape")
    check("%s: Enter opens the chooser and Escape closes it, returning focus to the slot" % label, E("document.getElementById('eqpick').hidden") and E("document.activeElement.dataset.i") == "4")
    E("(()=>{S.gear[4]=EQ.rs.ng_plus.byId.get('Lynx Armor 4').n;S.gear[5]=EQ.rs.ng_plus.byId.get('Lynx Gloves 5').n;save();eqRender(true)})()")
    pg.focus('#eqbody .eqtile[data-i="4"]'); pg.keyboard.press("Delete"); a = E("S.gear[4]"); pg.click('#eqbody .eqtile[data-i="5"]', button="right"); b2 = E("S.gear[5]")
    check("%s: Delete and right-click unequip" % label, a == 0 and b2 == 0)
    # ruleset switch
    pg.click('#eqpanel [data-rs="ng"]'); until(pg, "S.rs==='ng'"); E("(()=>{S.gear.fill(0);S.gear[4]=EQ.rs.ng.byId.get('Lynx Armor 4').n;S.gear[5]=EQ.rs.ng.byId.get('Lynx Gloves 5').n;save();eqRender(true)})()")
    pg.click('#eqpanel [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'"); toast = E("document.getElementById('toastMsg').textContent"); kept = E("S.gear[4]>0&&S.gear[5]>0")
    check("%s: switching to New Game Plus keeps items that exist in both and says so" % label, kept and "kept" in toast, toast[:100])
    E("(()=>{S.gear[4]=EQ.rs.ng_plus.byId.get('NGP Lynx Armor 4').n;save();eqRender(true)})()"); pg.click('#eqpanel [data-rs="ng"]'); until(pg, "S.rs==='ng'"); toast = E("document.getElementById('toastMsg').textContent")
    check("%s: switching back clears items that do not exist there (an NGP item), with a notice naming it" % label, E("S.gear[4]") == 0 and E("S.gear[5]") > 0 and "Removed" in toast and "armor" in toast.lower(), toast[:120])
    code = E("document.getElementById('link').value").split("#")[-1]; want = E("[S.rs,S.gear.join()]")
    q = b.new_page(); q.goto(base + "#" + code); until(q, READY); got = q.evaluate("[S.rs,S.gear.join()]"); same = q.evaluate("document.querySelector('#eqbody .eqslot.on .eqsl span')&&document.querySelector('#eqbody .eqslot.on .eqsl span').textContent"); q.close()
    check("%s: a gear link reopens with the same gear and the same mode" % label, got == want and same, [got, want, same])
    levelcheck(b, base, check, label, pg)
    check("%s: no script errors" % label, not errs, errs[:2]); pg.close()
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, READY); m.fill("#lvl", "100")
    m.tap('#eqbody .eqtile[data-i="4"]'); m.wait_for_selector("#pkgrid .pktile"); m.tap("#pkgrid .pktile >> nth=0"); w2 = m.evaluate("document.documentElement.scrollWidth-innerWidth"); m.tap("#pkequip"); m.wait_for_timeout(200)
    check("%s: on a phone the chooser does not scroll sideways, and tapping equips" % label, w2 <= 0 and m.evaluate("S.gear[4]") > 0, w2); m.close()
