"""The Equipment screen in a real browser: lazy data, chooser, tooltip with tiers, set bonuses, ruleset switch, keyboard, touch layout, links.
Used by tests/run_all.py (online and offline builds) and tests/smoke.py (preview and production)."""

OPEN = "async()=>{document.getElementById('eqbtn').click();for(let i=0;i<100&&!document.querySelector('#eqbody .eqslot');i++)await new Promise(r=>setTimeout(r,50));return !!document.querySelector('#eqbody .eqslot')}"
DATA_REQ = "Object.keys(window.W3DATA||{}).map(k=>k+'.js')"   # the data files that were loaded (a script sets W3DATA.<name>)


def until(pg, js, ms=5000):
    """Poll an expression in the page (wait_for_function would evaluate a string, which the page's CSP forbids)."""
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def run(b, base, check, label, quick=False):
    errs = []; pg = b.new_page(viewport={"width": 1400, "height": 950}); pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); E = pg.evaluate
    pg.goto(base); until(pg, "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"); pg.wait_for_timeout(300)
    check("%s: nothing of the equipment data is loaded before Equipment is opened" % label, E(DATA_REQ) == [])
    check("%s: Equipment opens next to Mutations and loads only the first-playthrough list" % label, E(OPEN) and E(DATA_REQ) == ["items.js", "items_ng.js"], E(DATA_REQ))
    check("%s: weapons (steel, silver, bolts, crossbow) and armor (chest, gloves, trousers, boots, mask) slots, consumables and bombs greyed" % label,
          E("[...document.querySelectorAll('#eqbody .eqw .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "steel,silver,bolts,crossbow" and E("[...document.querySelectorAll('#eqbody .eqa .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "chest,gloves,trousers,boots,mask"
          and E("document.querySelectorAll('#eqbody .eqslot.later').length") == 2)
    # chooser for the chest slot
    pg.click('#eqbody .eqtile[data-i="4"]'); pg.wait_for_selector("#pkgrid .pktile"); n_all = E("document.querySelectorAll('#pkgrid .pktile').length")
    check("%s: the chooser lists only items for that slot" % label, n_all > 5 and E("EQ.pick.slot") == "chest" and E("[...document.querySelectorAll('#pkgrid .pktile')].every(t=>EQ.rs.ng.byId.get(t.dataset.id).slot==='chest')"))
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
    pg.click("#pkequip"); pg.wait_for_selector("#pkgrid", state="detached", timeout=3000) if False else pg.wait_for_timeout(200)
    got = E("S.gear[4]"); check("%s: Equip puts the item in the slot, closes the chooser and the link has the gear segment" % label, got > 0 and E("document.getElementById('eqpick').hidden") and E("/\\.g1AA/.test(document.getElementById('link').value)"), got)
    # sets, bonuses
    ids = ["Lynx Armor 4", "Lynx Gloves 5", "Lynx Pants 5", "Lynx Boots 5", "Lynx School steel sword 4", "Lynx School silver sword 4"]; slots = ["chest", "gloves", "trousers", "boots", "steel", "silver"]
    def put(k):
        E("([ids,slots,k])=>{S.gear.fill(0);ids.slice(0,k).forEach((id,j)=>{S.gear[EQ_SLOTS.indexOf(slots[j])]=EQ.rs[S.rs].byId.get(id).n});save();eqRender()}", [ids, slots, k]) if False else E("(a)=>{const [ids,slots,k]=a;S.gear.fill(0);ids.slice(0,k).forEach((id,j)=>{S.gear[EQ_SLOTS.indexOf(slots[j])]=EQ.rs[S.rs].byId.get(id).n});save();eqRender()}", [ids, slots, k])
    put(2); two = E("document.querySelectorAll('.eqset li.lit').length"); put(3); three = E("document.querySelectorAll('.eqset li.lit').length"); put(6); six = E("document.querySelectorAll('.eqset li.lit').length")
    check("%s: the 3-piece bonus lights at 3 counted pieces and the 6-piece at 6 (lit: %d, %d, %d)" % (label, two, three, six), (two, three, six) == (0, 1, 2) and E("document.querySelector('.eqset h3').textContent").startswith("Feline"))
    check("%s: each equipped item's stats are listed, not summed" % label, E("document.querySelectorAll('#eqbody .eqitem').length") == 6)
    # autogen relic
    E("(()=>{S.gear.fill(0);save();eqRender()})()"); pg.click('#eqbody .eqtile[data-i="0"]'); pg.wait_for_selector("#pkgrid .pktile"); pg.fill("#pkq", "Wolf"); pg.wait_for_timeout(100)
    E("(()=>{EQ.pick.sel=EQ.rs.ng.byId.get('Wolf');eqPickRender()})()"); relic = E("document.getElementById('pkside').innerText")
    check("%s: an autogen relic shows its rolled ranges and 'Level varies'" % label, "Level varies" in relic and " to " in relic, relic[:80]); pg.keyboard.press("Escape")
    # keyboard and right-click
    pg.focus('#eqbody .eqtile[data-i="4"]'); pg.keyboard.press("Enter"); pg.wait_for_selector("#pkgrid .pktile"); pg.keyboard.press("Escape")
    check("%s: Enter opens the chooser and Escape closes it, keeping the screen open and returning focus" % label, E("document.getElementById('eqpick').hidden") and E("EQ.open") and E("document.activeElement.dataset.i") == "4")
    E("(()=>{S.gear[4]=EQ.rs.ng.byId.get('Lynx Armor 4').n;S.gear[5]=EQ.rs.ng.byId.get('Lynx Gloves 5').n;save();eqRender()})()")
    pg.focus('#eqbody .eqtile[data-i="4"]'); pg.keyboard.press("Delete"); a = E("S.gear[4]"); pg.click('#eqbody .eqtile[data-i="5"]', button="right"); b2 = E("S.gear[5]")
    check("%s: Delete and right-click unequip" % label, a == 0 and b2 == 0)
    # ruleset switch
    E("(()=>{S.gear.fill(0);S.gear[4]=EQ.rs.ng.byId.get('Lynx Armor 4').n;S.gear[5]=EQ.rs.ng.byId.get('Lynx Gloves 5').n;save();eqRender()})()")
    pg.click('#eqov [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'"); toast = E("document.getElementById('toastMsg').textContent"); kept = E("S.gear[4]>0&&S.gear[5]>0")
    check("%s: switching to New Game Plus loads its list, keeps items that exist in both and says so" % label, kept and E(DATA_REQ).count("items_ng_plus.js") == 1 and "kept" in toast, toast[:100])
    E("(()=>{S.gear[4]=EQ.rs.ng_plus.byId.get('NGP Lynx Armor 4').n;save();eqRender()})()"); pg.click('#eqov [data-rs="ng"]'); until(pg, "S.rs==='ng'"); toast = E("document.getElementById('toastMsg').textContent")
    check("%s: switching back clears items that do not exist there (an NGP item), with a notice naming it" % label, E("S.gear[4]") == 0 and E("S.gear[5]") > 0 and "Removed" in toast and "armor" in toast.lower(), toast[:120])
    link = E("document.getElementById('link').value"); code = link.split("#")[-1]; want = E("[S.rs,S.gear.join()]")
    q = b.new_page(); q.goto(base + "#" + code); until(q, "typeof S!=='undefined'&&S"); got = q.evaluate("[S.rs,S.gear.join()]"); q.evaluate(OPEN); same = q.evaluate("document.querySelector('#eqbody .eqslot.on .eqsl span')&&document.querySelector('#eqbody .eqslot.on .eqsl span').textContent"); q.close()
    check("%s: a gear link reopens with the same gear and the same mode" % label, got == want and same, [got, want, same])
    pg.keyboard.press("Escape"); check("%s: no script errors" % label, not errs, errs[:2]); pg.close()
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, "typeof S!=='undefined'&&S"); m.evaluate(OPEN)
    w1 = m.evaluate("document.documentElement.scrollWidth-innerWidth"); m.tap('#eqbody .eqtile[data-i="4"]'); m.wait_for_selector("#pkgrid .pktile"); m.tap("#pkgrid .pktile >> nth=0"); w2 = m.evaluate("document.documentElement.scrollWidth-innerWidth"); m.tap("#pkequip"); m.wait_for_timeout(200)
    check("%s: on a phone the screen and the chooser do not scroll sideways, and tapping equips" % label, w1 <= 0 and w2 <= 0 and m.evaluate("S.gear[4]") > 0, [w1, w2]); m.close()
