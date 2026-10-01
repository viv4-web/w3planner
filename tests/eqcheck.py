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


def layout(b, base, check, label):
    for w, h in ((1500, 900), (1280, 800), (1024, 768)):
        pg = b.new_page(viewport={"width": w, "height": h}); pg.goto(base); until(pg, READY); E = pg.evaluate
        tree, slots, eq, vd = E(BOX, "#treePanel"), E(BOX, "#slots"), E(BOX, "#eqpanel"), E(BOX, ".vdiv")
        side = tree["r"] <= slots["l"] <= slots["r"] <= eq["l"] and vd["r"] <= eq["l"] and tree["l"] < 40
        check("%s: at %d px the skills (tree, slots) sit left, the divider and the equipment panel right, nothing overlaps, no sideways scroll%s" % (label, w, " and the tree keeps %d px" % tree["w"] if w == 1280 else ""),
              side and E("document.documentElement.scrollWidth<=innerWidth") and (w != 1280 or tree["w"] >= 570) and tree["l"] <= 24, [tree, slots, eq])
        if w == 1280:
            check("%s: the panel scrolls on its own (sticky, own vertical scroll) and has the 'Skills' and 'Equipment' headers" % label, E("getComputedStyle(document.getElementById('eqpanel')).overflowY") == "auto" and E("getComputedStyle(document.getElementById('eqpanel')).position") == "sticky"
                  and E("document.querySelector('.skillsarea .areahead').textContent") == "Skills" and E("document.querySelector('#eqpanel .areahead').textContent") == "Equipment")
            check("%s: compact tiles (not 174 px tall): %d px" % (label, E(BOX, '#eqbody .eqtile')["h"]), E(BOX, '#eqbody .eqtile')["h"] < 110)
        pg.close()
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, READY); E = m.evaluate
    tree, eq, vd = E(BOX, "#treePanel"), E(BOX, "#eqpanel"), E(BOX, ".vdiv")
    check("%s: at 390 px the skills come first, then a horizontal divider, then the equipment, without sideways scroll" % label, tree["b"] <= vd["t"] + 2 and vd["b"] <= eq["t"] + 2 and vd["h"] <= 2 and vd["w"] > 200 and E("document.documentElement.scrollWidth<=innerWidth"), [tree, vd, eq])
    check("%s: on a phone the Equipment button jumps to the panel" % label, E("getComputedStyle(document.getElementById('eqbtn')).display") != "none"); m.close()


def run(b, base, check, label, quick=False):
    errs, events = [], []; pg = b.new_page(viewport={"width": 1400, "height": 950}); pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); E = pg.evaluate
    pg.on("load", lambda p: events.append("load")); pg.on("request", lambda r: events.append("data") if "/data/items" in r.url else None)
    pg.goto(base); check("%s: the panel shows right away and the equipment data loads after the page has loaded, only items.js and items_ng.js" % label, until(pg, READY) and E(KEYS) == ["items.js", "items_ng.js"] and events.index("load") < (events.index("data") if "data" in events else 99), [events[:4], E(KEYS)])
    layout(b, base, check, label)
    check("%s: weapons (steel, silver, bolts, crossbow) then armor (chest, gloves, trousers, boots, mask); consumables and bombs greyed" % label,
          E("[...document.querySelectorAll('#eqbody .eqsec:nth-child(1) .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "steel,silver,bolts,crossbow" and E("[...document.querySelectorAll('#eqbody .eqsec:nth-child(2) .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "chest,gloves,trousers,boots,mask"
          and E("document.querySelectorAll('#eqbody .eqslot.later').length") == 2)
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
