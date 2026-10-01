"""The Equipment panel in a real browser: layout, lazy data, chooser for every weapon slot, tooltip with tiers, set bonuses, Equip set, ruleset switch,
keyboard, touch layout, links. Used by tests/run_all.py (online and offline builds) and tests/smoke.py (preview and production)."""

READY = "typeof eqData==='function'&&!!eqData()&&!!document.querySelector('#eqbody .eqtile[data-i]')"
KEYS = "Object.keys(window.W3DATA||{}).map(k=>k+'.js')"   # the data files that were loaded (a script sets W3DATA.<name>)
BOX = "(sel)=>{const e=document.querySelector(sel);if(!e)return null;const r=e.getBoundingClientRect();return{l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)}}"
CHEST, GLOVES, TROUSERS, BOOTS, STEEL, SILVER = 4, 5, 6, 7, 0, 1


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
            check("%s: the tree is %d px wide and the weapons are one row of 4, the armor %s" % (tag, tree["w"], "one row of 5" if g["arows"] == 1 else "3 + 2"), g["wrows"] == 1 and g["arows"] == (1 if eq["w"] - 30 >= 392 else 2), [g["wrows"], g["arows"], eq["w"]])
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


def run(b, base, check, label, quick=False):
    errs, events = [], []; pg = b.new_page(viewport={"width": 1400, "height": 950}); pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); E = pg.evaluate
    pg.on("load", lambda p: events.append("load")); pg.on("request", lambda r: events.append("data") if "/data/items" in r.url else None)
    pg.goto(base); check("%s: the panel shows right away and the equipment data loads after the page has loaded, only items.js and items_ng.js" % label, until(pg, READY) and E(KEYS) == ["items.js", "items_ng.js"] and events.index("load") < (events.index("data") if "data" in events else 99), [events[:4], E(KEYS)])
    layout(b, base, check, label)
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
    check("%s: no script errors" % label, not errs, errs[:2]); pg.close()
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, READY)
    m.tap('#eqbody .eqtile[data-i="4"]'); m.wait_for_selector("#pkgrid .pktile"); m.tap("#pkgrid .pktile >> nth=0"); w2 = m.evaluate("document.documentElement.scrollWidth-innerWidth"); m.tap("#pkequip"); m.wait_for_timeout(200)
    check("%s: on a phone the chooser does not scroll sideways, and tapping equips" % label, w2 <= 0 and m.evaluate("S.gear[4]") > 0, w2); m.close()
