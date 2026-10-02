"""The Equipment panel in a real browser: layout, lazy data, chooser for every weapon slot, tooltip with tiers, set bonuses, Equip set, ruleset switch,
keyboard, touch layout, links. Used by tests/run_all.py (online and offline builds) and tests/smoke.py (preview and production)."""

READY = "typeof eqData==='function'&&!!eqData()&&!!CN.data&&!!document.querySelector('#eqbody .eqtile[data-i]')"
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


LEVELS = {"ng": {"Lynx Armor": 17, "Lynx Armor 1": 23, "Lynx Armor 2": 29, "Lynx Armor 3": 34, "Lynx Armor 4": 40, "Lynx School Crossbow": 29, "q702_vampire_mask": 1, "Blunt Bolt Legendary": 1},
          "ng_plus": {"Lynx Armor": 47, "Lynx Armor 1": 53, "Lynx Armor 2": 59, "Lynx Armor 3": 64, "Lynx Armor 4": 70, "NGP Lynx Armor 4": 40, "Lynx School Crossbow": 29, "q702_vampire_mask": 1}}
# hand-calculated from the game's scripts (GetItemLevel, inventoryComponent.ws:305 and gameParams.ws:917; see the report): armor 120/150/180/205/240 -> 17/23/29/34/40 (Grandmaster has the EP1 tag, minus 1),
# NG+ armor 270/300/330/355/390 -> 47/53/59/64/70, crossbow attack power x2.25 -> 32 - 1 - 2 = 29, masks have no branch (level 0 -> 1), the first test of 'Blunt Bolt Legendary' (5) wins -> 1


URSINE = ["Bear School steel sword 4", "Bear School silver sword 4", "Bear School Crossbow", "Broadhead Bolt", "Bear Armor 4", "Bear Gloves 5", "Bear Pants 5", "Bear Boots 5", "q702_vampire_mask"]   # all nine slots; the last card is the mask


def gear(pg, ids):
    return pg.evaluate("""(ids=>{const d=eqData();EQ_SLOTS.forEach((s,i)=>{const it=ids[i]&&d.byId.get(ids[i]);S.gear[i]=it&&it.slot===s?it.n:0});save();eqRender(true);return S.gear.filter(x=>x).length})""", ids)


def openinv(pg):
    """The Inventory screen (the equipment tests work there); the data must be loaded."""
    pg.evaluate("scrGo('inv')"); until(pg, "!document.getElementById('screenInv').hidden")


GEOM = """()=>{const B=s=>{const e=document.querySelector(s);if(!e||!e.getClientRects().length)return null;const r=e.getBoundingClientRect();return{l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)}};
 const tiles=[...document.querySelectorAll('#eqbody .eqtile')].map(t=>t.getBoundingClientRect()).filter(r=>r.width>0);
 return{tabs:B('.scrtabs'),lvl:B('.lvlblock'),right:B('.topright'),tInv:B('#tabInv'),tChar:B('#tabChar'),tAlch:B('#tabAlch'),tGlo:B('#tabGlo'),stabs:[document.getElementById('stabs').scrollWidth,document.getElementById('stabs').clientWidth],prev:B('#scrPrev'),next:B('#scrNext'),left:B('#invLeft'),mid:B('#invMid'),centre:B('.invcentre'),rt:B('#invRight'),wbox:B('.wbox'),cbox:B('.cbox'),bbox:B('.bbox'),mask:B('.maskbox'),abox:B('.abox'),
  sets:B('.invright .eqsec'),tree:B('#treePanel'),slots:B('#slots'),info:B('#info'),sw:document.documentElement.scrollWidth,vw:innerWidth,mintile:Math.min(...tiles.map(r=>Math.min(r.width,r.height))),ntiles:tiles.length}}"""


def copycheck(b, base, check, label):
    """v28b: ONE Copy link control in the top bar, reachable on both screens at every width, also with the slot panel or the phone's slot sheet open; the copied link is the whole current build."""
    if label == "offline": return           # the offline copy can open links but not create them (CFG.share false: no button)
    CLIP = ["clipboard-read", "clipboard-write"]
    def reach(pg, E, tag):
        r = E("""(()=>{const e=document.getElementById('copy'),r=e.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2,t=document.elementFromPoint(x,y);
          return{vis:r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden',inview:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight,top:!!t&&(t===e||e.contains(t)),h:Math.round(r.height),n:document.querySelectorAll('#copy,[aria-label="Copy build link"]').length,al:e.getAttribute('aria-label')}})()""")
        pg.evaluate("navigator.clipboard.writeText('x')"); pg.click("#copy"); ok = until(pg, "navigator.clipboard.readText().then(t=>window.__cp=t)&&!!window.__cp&&window.__cp.indexOf('#v1.')>0") and E("document.getElementById('toastMsg').textContent") == "Link copied" and E("document.getElementById('copy').textContent") == "Link copied"
        check("%s: Copy link is visible, not covered, one element, aria-label 'Copy build link', and clicking says 'Link copied' (%s)" % (tag, r), r["vis"] and r["inview"] and r["top"] and r["n"] == 1 and r["al"] == "Copy build link" and ok, r)
        return r
    for w, h in ((1920, 1080), (1440, 900), (1100, 800), (1024, 768), (390, 844)):
        cx = b.new_context(viewport={"width": w, "height": h}, is_mobile=w < 600, has_touch=w < 600, permissions=CLIP); pg = cx.new_page(); pg.goto(base); until(pg, READY); E = pg.evaluate; tag = "%s: at %d px" % (label, w)
        reach(pg, E, tag + " Character")
        openinv(pg); reach(pg, E, tag + " Inventory (stash)")
        E("document.activeElement&&document.activeElement.blur()"); pg.keyboard.press("Tab")
        pg.click('#eqbody .eqtile[data-i="0"]'); pg.wait_for_selector("#pkgrid .pktile"); r = reach(pg, E, tag + " Inventory (slot %s open)" % ("sheet" if w < 600 else "panel"))
        if w < 600: check("%s: the Copy link tap target is 44 px high on the phone" % tag, r["h"] >= 44, r)
        pg.focus("#copy"); pg.evaluate("window.__cp=''"); pg.keyboard.press("Enter"); check("%s: Copy link works from the keyboard" % tag, until(pg, "navigator.clipboard.readText().then(t=>window.__cp=t)&&!!window.__cp&&window.__cp.indexOf('#v1.')>0"))
        cx.close()
    for scr in ("inv", "char"):
        cx = b.new_context(viewport={"width": 1920, "height": 1080}, permissions=CLIP); pg = cx.new_page(); pg.goto(base); until(pg, READY); E = pg.evaluate
        pg.fill("#lvl", "100"); E("(()=>{const d=eqData();S.gear[0]=d.byId.get('Bear School steel sword 4').n;S.gear[4]=d.byId.get('Bear Armor 4').n;S.cons[0]=CN.byId.get('Mutagen 1').n;S.cons[7]=CN.byId.get('Beast Oil 2').n;S.lv[0][0]=1;S.slots[0]=[0,0];save();eqRender(true)})()")
        E("S.muts[0]=3;S.mres[0]=1;S.mact=0;save()"); E("scrGo('%s')" % scr); until(pg, "S.scr==='%s'" % scr); pg.click("#copy"); until(pg, "navigator.clipboard.readText().then(t=>window.__cp=t)&&!!window.__cp")
        link = E("window.__cp"); want = E("[S.scr,S.cons.join(),S.gear.join(),S.rs,S.lv.flat().join(),S.slots.join('|'),S.muts.join(),S.mres.join(),S.mact,lvl()].join(';')")
        q = cx.new_page(); q.goto(link); until(q, READY); got = q.evaluate("[S.scr,S.cons.join(),S.gear.join(),S.rs,S.lv.flat().join(),S.slots.join('|'),S.muts.join(),S.mres.join(),S.mact,lvl()].join(';')")
        check("%s: copy on %s (level, skills, mutations, gear, consumables, silver oil), open in a new tab: the same build on the same screen (%s)" % (label, scr, link[-60:]), got == want and link.endswith(".s1I") == (scr == "inv") and E("S.cons[7]") > 0 and E("S.gear[0]") > 0, [got, want])
        cx.close()


def layoutcheck(b, base, check, label):
    """The two screens at seven widths: the top bar, the Character screen (the v26 layout, no equipment), the Inventory screen (stash | slot boxes | silhouette | armour, sets, stats) and how it folds."""
    for w, h in ((2560, 1259), (1920, 1080), (1440, 900), (1280, 800), (1024, 768), (768, 900), (390, 844)):
        pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=w < 600, has_touch=w < 600); pg.goto(base); until(pg, READY); tag = "%s: at %d px" % (label, w); E = pg.evaluate
        c = E(GEOM)
        check("%s: Character screen (the default): no sideways scroll, tree and skill slots visible, no equipment boxes, tabs: Glossary, Alchemy, Inventory, Character (seven in the bar, in a row%s)" % (tag, ", scrolling sideways on the phone" if w < 600 else ""),
              c["sw"] <= c["vw"] and c["tree"] and c["slots"] and not c["wbox"] and c["tGlo"]["l"] < c["tAlch"]["l"] < c["tInv"]["l"] < c["tChar"]["l"] and (c["stabs"][0] > c["stabs"][1] and c["prev"]["w"] >= 34 and c["next"]["w"] >= 34 if w < 600 else c["prev"]["r"] <= c["tGlo"]["l"] + 1 and c["tChar"]["r"] <= c["next"]["l"] + 1), c)
        if w >= 1500:
            check("%s: top bar: level block left, tabs in the middle, ruleset and Copy link right" % tag, c["lvl"]["r"] <= c["tabs"]["l"] and c["tabs"]["r"] <= c["right"]["l"] and abs((c["tabs"]["l"] + c["tabs"]["r"]) / 2 - w / 2) < 60, c)
        else:
            check("%s: top bar: the tabs and arrows come first, the level block, ruleset and Copy link below" % tag, c["tabs"]["t"] < c["lvl"]["t"] and c["tabs"]["t"] < c["right"]["t"] and c["tabs"]["l"] >= 0 and c["tabs"]["r"] <= w, c)
        openinv(pg); g = E(GEOM)
        check("%s: Inventory: no sideways scroll, no skill tree, a 44 px tap target on every slot tile (smallest %s)" % (tag, g["mintile"]), g["sw"] <= g["vw"] and not g["tree"] and g["ntiles"] == 15 and (w >= 600 or g["mintile"] >= 44), g)
        if w >= 1440:
            check("%s: Inventory: stash | weapons, consumables, bombs, mask | silhouette | armour, sets, item stats, left to right; the boxes stack top to bottom" % tag,
                  g["left"]["r"] <= g["mid"]["l"] and g["mid"]["r"] <= g["centre"]["l"] + 1 and g["centre"]["r"] <= g["rt"]["l"] + 1 and g["wbox"]["b"] <= g["cbox"]["t"] and g["cbox"]["b"] <= g["bbox"]["t"] and g["bbox"]["b"] <= g["mask"]["t"] and g["abox"]["b"] <= g["sets"]["t"], g)
        elif w >= 1024:
            check("%s: Inventory: the equipment on top, the stash (and the slot panel) below it" % tag, g["left"]["t"] >= max(g["mid"]["b"], g["rt"]["b"]) - 2 and g["mid"]["r"] <= g["rt"]["l"] + 1, g)
        else:
            check("%s: Inventory: everything stacked: weapons, consumables, bombs, mask, then armour, sets, stats, then the stash" % tag, g["mid"]["b"] <= g["rt"]["t"] + 2 and g["rt"]["b"] <= g["left"]["t"] + 2 and g["wbox"]["b"] <= g["cbox"]["t"], g)
        pg.close()


def screencheck(b, base, check, label):
    """Switching screens with the tabs, the arrows and a swipe; the screen is in the link as s1I; the shared controls are on both screens."""
    pg = b.new_page(viewport={"width": 1500, "height": 950}); pg.goto(base); until(pg, READY); E = pg.evaluate
    vis = lambda sel: E("(s=>{const e=document.querySelector(s);return !!e&&e.getClientRects().length>0})", sel)
    shared = lambda: all(vis(s) for s in ("#lvl", "#bonuspts", '#topbar [data-rs="ng"]', '#topbar [data-rs="ng_plus"]')) and (E("CFG.share===false") or vis("#copy"))     # the offline copy cannot make links, so it has no Copy link
    check("%s: opens on Character: its screen shown, Inventory hidden, no s1 segment in the link, Character tab selected" % label, vis("#screenChar") and not vis("#screenInv") and E("S.scr") == "char" and not E("/\\.s1I/.test(location.hash)") and E("document.getElementById('tabChar').getAttribute('aria-selected')") == "true", E("location.hash"))
    check("%s: Level, Bonus points, NG / NG+ and Copy link are on the Character screen" % label, shared())
    check("%s: Alchemy is greyed, says 'in game only' and does not leave Character (it opens the in-game-only panel: tests/glcheck.py)" % label, E("(()=>{const a=document.getElementById('tabAlch');return /in game only/.test(a.textContent)&&a.classList.contains('off')})()") and E("(()=>{document.getElementById('tabAlch').click();return S.scr})()") == "char" and E("(()=>{const o=!document.getElementById('igov').hidden;document.getElementById('igclose').click();return o})()"))
    check("%s: on Character the right arrow is disabled and the left arrow is not" % label, E("document.getElementById('scrNext').disabled") and not E("document.getElementById('scrPrev').disabled"))
    pg.click("#scrPrev"); pg.wait_for_timeout(100)
    check("%s: the left arrow goes to Inventory: its screen shown, s1I in the link, the active tab is the filled gold block (%s)" % (label, E("getComputedStyle(document.getElementById('tabInv')).backgroundColor")),
          vis("#screenInv") and not vis("#screenChar") and E("S.scr") == "inv" and E("/\\.s1I$/.test(location.hash)") and E("getComputedStyle(document.getElementById('tabInv')).backgroundColor") == "rgb(200, 168, 107)" and E("getComputedStyle(document.getElementById('tabChar')).backgroundColor") != "rgb(200, 168, 107)")
    check("%s: Level, Bonus points, NG / NG+ and Copy link are on the Inventory screen too; on Inventory both arrows work (Glossary is to the left, Character to the right)" % label, shared() and not E("document.getElementById('scrPrev').disabled") and not E("document.getElementById('scrNext').disabled"))
    pg.click("#scrNext"); pg.wait_for_timeout(100)
    check("%s: the right arrow goes back to Character (no s1 segment again)" % label, E("S.scr") == "char" and vis("#screenChar") and not E("/\\.s1I/.test(location.hash)"))
    pg.click("#tabInv"); pg.wait_for_timeout(100); a = E("S.scr"); pg.click("#tabChar"); pg.wait_for_timeout(100)
    check("%s: the tabs switch screens (Inventory, then Character)" % label, a == "inv" and E("S.scr") == "char")
    pg.fill("#lvl", "55"); pg.click("#tabInv"); pg.wait_for_timeout(100)
    check("%s: the level set on one screen is the level on the other (%s)" % (label, E("document.getElementById('lvl').value")), E("document.getElementById('lvl').value") == "55" and E("lvl()") == 55)
    code = E("location.hash.slice(1)"); q = b.new_page(); q.goto(base + "#" + code); until(q, READY)
    check("%s: a link made on Inventory opens on Inventory" % label, q.evaluate("S.scr") == "inv" and q.evaluate("!document.getElementById('screenInv').hidden") and q.evaluate("document.getElementById('screenChar').hidden")); q.close(); pg.close()
    # swipe on a phone: left = next, right = previous; not from the skill tree (it drags)
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, READY); E = m.evaluate
    SW = """([sel,dx])=>{const el=document.querySelector(sel),r=el.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+Math.min(40,r.height/2),mk=(t,cx)=>new Touch({identifier:7,target:el,clientX:cx,clientY:y});
      el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,cancelable:true,touches:[mk(el,x)],changedTouches:[mk(el,x)]}));
      el.dispatchEvent(new TouchEvent('touchend',{bubbles:true,cancelable:true,touches:[],changedTouches:[mk(el,x+dx)]}));return S.scr}"""
    on_tree = E(SW, ["#treePanel", -140]); on_char = E(SW, ["#treeHint", 140]); on_inv = E(SW, ["#invMid", -140]) if False else None
    check("%s: 390 px: a swipe that starts on the skill tree does nothing (%s); a swipe right from the Character text goes to Inventory (%s)" % (label, on_tree, on_char), on_tree == "char" and on_char == "inv")
    left = E(SW, ["#invMid", -140]); right = E(SW, ["#invMid", 140]); short = E(SW, ["#invMid", -30])
    check("%s: 390 px: on Inventory a swipe left goes to Character (%s), a swipe right back (%s), a short swipe does nothing (%s)" % (label, left, right, short), left == "char" and right == "inv" and short == "inv")
    m.close()


def conscheck(b, base, check, label):
    """Consumables: the data, what a slot accepts (the slot rule), the c1 and s1 link segments, unknown prefixes, old links re-encoding byte for byte."""
    pg = b.new_page(viewport={"width": 1500, "height": 950}); pg.goto(base); until(pg, READY); E = pg.evaluate
    cats = E("(()=>{const o={};CN.data.items.forEach(i=>o[i.cat]=(o[i.cat]||0)+1);return o})()")
    check("%s: the consumables: 34 potions, 31 decoctions, 25 bombs, 36 oils, 111 food and drink, 2 Pocket items (%s); every id has a registry number, no number twice" % (label, cats), cats == {"potion": 34, "decoction": 31, "bomb": 25, "oil": 36, "food": 111, "pocket": 2} and E("new Set(CN.data.items.map(i=>i.n)).size") == 239, cats)
    R = E("""(()=>{const g=id=>CN.byId.get(id),a=(k,id)=>cnAccepts(k,g(id));return{
      potionSlots:[1,2,3,4].every(i=>a('potion'+i,'Swallow 3')&&a('potion'+i,'Mutagen 1')&&a('potion'+i,'White Raffards Decoction 2')),
      potionNoOilBomb:[1,2,3,4].every(i=>!a('potion'+i,'Beast Oil 2')&&!a('potion'+i,'Hanged Man Venom 1')&&!a('potion'+i,'Dancing Star 2')),
      bombSlots:a('petard1','Dancing Star 2')&&a('petard1','Snow Ball')&&!a('petard1','Swallow 1')&&!a('petard1','Mutagen 1')&&!a('petard1','Beast Oil 1')&&!a('petard1','Cows milk')&&!a('petard1','Torch'),
      foodSlots:[1,2,3,4].every(i=>a('potion'+i,'Cows milk')&&a('potion'+i,'Bottled water')&&a('potion'+i,'Beauclair White')&&!a('potion'+i,'Torch')),
      pocket:a('pocket','Torch')&&a('pocket','Oil Lamp')&&!a('pocket','Dancing Star 2')&&!a('pocket','Swallow 1')&&!a('pocket','Cows milk')&&!a('pocket','Beast Oil 1')&&CN.bySlot.pocket.length===2,
      steel:a('oil_steel','Beast Oil 2')&&a('oil_steel','Hanged Man Venom 3')&&!a('oil_steel','Cursed Oil 2')&&!a('oil_steel','Necrophage Oil 1')&&!a('oil_steel','Swallow 1'),
      silver:a('oil_silver','Cursed Oil 2')&&a('oil_silver','Beast Oil 1')&&a('oil_silver','Vampire Oil 3')&&!a('oil_silver','Dancing Star 1'),
      steelN:CN.bySlot.oil_steel.length,silverN:CN.bySlot.oil_silver.length,potionN:CN.bySlot.potion1.length,bombN:CN.bySlot.petard1.length,pocketN:CN.bySlot.pocket.length,nothing:!cnAccepts('potion1',null)&&!cnAccepts('chest',CN.byId.get('Swallow 1'))}})()""")
    check("%s: slot rule: potion slots take potions, decoctions and food and drink and never an oil or a bomb; the Bomb slot only bombs; the Pocket only Torch and Candle lantern; the steel sword takes only SteelOil oils (6), the silver sword every oil (36) (%s)" % (label, R),
          R["potionSlots"] and R["potionNoOilBomb"] and R["bombSlots"] and R["foodSlots"] and R["pocket"] and R["steel"] and R["silver"] and (R["steelN"], R["silverN"], R["potionN"], R["bombN"]) == (6, 36, 176, 25) and R["nothing"], R)
    SET = "(ids)=>{const d=CN.byId;S.cons=ids.map(x=>x?d.get(x).n:0);return enc()}"
    ids = ["Swallow 3", "Mutagen 1", "Cat 2", "White Raffards Decoction 3", "Dancing Star 3", "Torch", "Beast Oil 3", "Vampire Oil 2"]
    code = E(SET, ids); seg = [x for x in code.split(".") if x.startswith("c1")]
    back = E("(c=>{const s=dec(c);return s&&s.cons.join()})", code); want = E("(ids=>ids.map(x=>CN.byId.get(x).n).join())", ids)
    check("%s: c1 round trip: one c1 segment of 18 characters (c1 + 8 slots x 2), the same 8 numbers come back (%s)" % (label, seg), len(seg) == 1 and len(seg[0]) == 18 and back == want, [seg, back, want])
    check("%s: no consumables, no c1 segment; link order is g1, c1, s1" % label, "c1" not in E("(()=>{S.cons.fill(0);return enc()})()") and E("(i=>{S.cons=i.map(x=>CN.byId.get(x).n);S.gear[4]=eqData().byId.get('Lynx Armor 4').n;S.scr='inv';const p=enc().split('.').slice(8).map(x=>x.slice(0,2));S.cons.fill(0);S.gear.fill(0);S.scr='char';return p.join()})", ids) == "g1,c1,s1")
    base_code = E("(()=>{S.cons.fill(0);S.gear.fill(0);S.scr='char';S.rs='ng';return enc()})()")
    tolerant = E("(c)=>{const s=dec(c+'.z9ABC');return !!s&&dec(c+'.z9ABC.y2').cons.every(x=>x===0)}", base_code)
    bad = E("(c)=>[c+'.c1ABC',c+'.c1'+'A'.repeat(17),c+'.s1X',c+'.s1I.s1I',c+'.Q9AB',c+'.1xAB',c+'.9z',c+'.g1AAAAAAAAAAAAAAAAAAAAA.g1AAAAAAAAAAAAAAAAAAAAA',c+'.c1'+'A'.repeat(15)+'!'].map(x=>dec(x))", base_code)
    check("%s: a well-formed unknown prefix is ignored (z9, y2); malformed or repeated known segments and ill-shaped ones are rejected (%s)" % (label, bad.count(None)), tolerant and all(x is None for x in bad), bad)
    # every fixture link: decoding then encoding gives the same link, byte for byte (the 16-slot links; older ones had 12 slots)
    import json, linkcheck
    fixtures, _ = linkcheck.load_fixtures(); same, diff = 0, []
    for fx in fixtures:
        if fx["kind"] == "legacy" or len(fx["code"].split(".")[2]) != 32: continue
        r = E("(c)=>{const s=dec(c);if(!s)return null;S=s;enforceLocks();return enc()}", fx["code"])
        if r == fx["code"]: same += 1
        else: diff.append((fx["name"][:30], fx["code"][-30:], (r or "")[-30:]))
    check("%s: every link made before v28 re-encodes byte for byte (%d links)" % (label, same), not diff and same > 30, diff[:3])
    # v31b: a bomb in the old second bomb slot (now the Pocket): moved to the Bomb slot when that is empty, dropped when it holds a bomb; either way said on screen, and the link text is not rewritten on open
    old = E("(()=>{S.cons=[0,0,0,0,0,CN.byId.get('Samum 1').n,0,0];const a=enc();S.cons=[0,0,0,0,CN.byId.get('Dancing Star 3').n,CN.byId.get('Samum 1').n,0,0];return [a,enc()]})()")
    res = []
    for code in old:
        q = b.new_page(viewport={"width": 1400, "height": 950}); q.goto(base + "#" + code); until(q, READY); until(q, "typeof CN!=='undefined'&&!!CN.data&&document.getElementById('toastMsg').textContent.length>0")
        res.append(q.evaluate("[S.cons.slice(4,6).map(n=>n?CN.byN.get(n).name:null),location.hash.slice(1),document.getElementById('toastMsg').textContent]")); q.close()
    check("%s: an old link with a bomb in the second bomb slot: moved to the Bomb slot when it is empty, dropped when not; said on screen; the link text is unchanged (%s)" % (label, [r[0] for r in res]),
          res[0][0] == ["Samum", None] and "moved to the Bomb slot" in res[0][2] and res[1][0] == ["Superior Dancing Star", None] and "removed" in res[1][2] and res[0][1] == old[0] and res[1][1] == old[1], res)
    pg.close()


def invcheck(b, base, check, label):
    """The Inventory flow: the stash, the slot panel for a consumable slot, Equip, the oil row of a sword, 'Affected by', the link, a phone's full-screen sheet."""
    pg = b.new_page(viewport={"width": 1920, "height": 1080}); pg.goto(base); until(pg, READY); E = pg.evaluate; openinv(pg); pg.fill("#lvl", "100")
    E("(()=>{S.gear.fill(0);S.cons.fill(0);S.slots=S.slots.map(()=>null);save();eqRender(true)})()")
    check("%s: the stash is empty: five sub-tab icons, an empty state, 'Import save (coming later)' disabled (%s)" % (label, E("document.getElementById('stash').innerText")[:70].replace("\n", " ")),
          E("document.querySelectorAll('#stash .sttab').length") == 5 and "Your stash fills when you import a save. Click any slot to plan." in E("document.getElementById('stash').innerText") and E("document.getElementById('stimport').disabled")
          and E("[...document.querySelectorAll('#stash .sttab')].map(b=>b.title).join()") == "Crafting components,Quest items,Food & drink, Roach,Alchemy,Weapons & Armor" and E("document.querySelectorAll('#stash .sttab.on').length") == 1)
    pg.click('#stash .sttab >> nth=3'); a = E("document.querySelector('#stash .stname').textContent"); pg.click('#stash .sttab >> nth=0')
    check("%s: the sub-tabs switch (Alchemy is the fourth: %s); the active one is outlined" % (label, a), a.lower() == "alchemy" and E("document.querySelector('#stash .sttab.on').dataset.t") == "0")
    # a potion slot
    pg.click('#eqbody .eqtile[data-i="9"]'); pg.wait_for_selector("#pkgrid .pktile")
    title = E("document.getElementById('pktitle').textContent"); n_all = E("document.querySelectorAll('#pkgrid .pktile').length"); stash_hidden = E("document.getElementById('stash').hidden")
    pg.click('.chip[data-k="potion"]'); n_p = E("document.querySelectorAll('#pkgrid .pktile').length"); pg.click('.chip[data-k="decoction"]'); n_d = E("document.querySelectorAll('#pkgrid .pktile').length"); pg.click('.chip[data-k="food"]'); n_f = E("document.querySelectorAll('#pkgrid .pktile').length"); pg.click('.chip[data-k="all"]')
    check("%s: clicking a consumable slot replaces the stash with the panel '%s': %d cards, Potions %d, Decoctions %d, Food & drink %d; no oil or bomb among them; 'Only items in my stash' is disabled" % (label, title, n_all, n_p, n_d, n_f),
          title == "Potion 1 · all items that fit" and stash_hidden and (n_all, n_p, n_d, n_f) == (176, 34, 31, 111) and E("[...document.querySelectorAll('#pkgrid .pktile')].every(t=>['potion','decoction','food'].includes(CN.byId.get(t.dataset.id).cat))") and E("document.getElementById('pkstash').disabled")
          and E("document.querySelectorAll('#oilrow').length") == 0, [title, n_all, n_p, n_d, n_f])
    pg.fill("#pkq", "superior swallow"); pg.wait_for_timeout(100); cards = E("[...document.querySelectorAll('#pkgrid .pktile span')].map(s=>s.textContent)")
    pg.click('#pkgrid .pktile[data-id="Swallow 3"]'); tip = E("document.getElementById('pkside').innerText")
    check("%s: search 'superior swallow' leaves one card; its detail shows toxicity, duration, charges and the effect (%s)" % (label, cards), cards == ["Superior Swallow"] and "Toxicity" in tip and "Duration" in tip and "Charges" in tip and "Accelerates Vitality" in tip, [cards, tip[:200]])
    pg.click("#pkequip"); pg.wait_for_timeout(150)
    check("%s: Equip puts Superior Swallow in Potion 1, closes the panel (the stash is back), the slot shows it, Item stats list it with base values, no totals" % label,
          E("S.cons[0]") == E("CN.byId.get('Swallow 3').n") and E("document.getElementById('eqpick').hidden") and not E("document.getElementById('stash').hidden") and E("!!document.querySelector('.eqslot.cons.on[data-i=\"9\"] img')")
          and E("[...document.querySelectorAll('#invRight .eqitem h4')].map(h=>h.textContent).join()") == "Superior Swallow" and "Toxicity" in E("document.querySelector('#invRight .eqitem').innerText") and E("/\\.c1/.test(document.getElementById('link').value)"))
    # a bomb slot
    pg.click('#eqbody .eqtile[data-i="13"]'); pg.wait_for_selector("#pkgrid .pktile"); nb = E("document.querySelectorAll('#pkgrid .pktile').length"); chips = E("document.querySelectorAll('.chip').length"); pg.keyboard.press("Escape")
    check("%s: a bomb slot lists the 25 bombs only (no chips)" % label, nb == 25 and chips == 0 and E("document.getElementById('eqpick').hidden") and not E("document.getElementById('stash').hidden"))
    # swords and oils: equip a silver sword first, then choose an oil in its panel
    E("(()=>{S.gear[1]=eqData().byId.get('Lynx School silver sword 4').n;S.gear[0]=eqData().byId.get('Lynx School steel sword 4').n;save();eqRender(true)})()")
    pg.click('#eqbody .eqtile[data-i="1"]'); pg.wait_for_selector("#oilrow .oiltile"); n_silver = E("document.querySelectorAll('#oilrow .oiltile').length"); title = E("document.getElementById('pktitle').textContent"); sel = E("document.querySelector('#pkgrid .pktile.sel')&&document.querySelector('#pkgrid .pktile.sel').dataset.id")
    pg.click('#oilrow .oiltile[data-n="%d"]' % E("CN.byId.get('Beast Oil 2').n")); pg.wait_for_timeout(150)
    check("%s: the silver sword's panel ('%s') has an Oil row with 'No oil' and the 36 oils; the worn sword is preselected (%s); choosing Beast Oil 2 applies it (S.cons[7])" % (label, title, sel),
          title == "Silver sword · all items that fit" and n_silver == 37 and sel == "Lynx School silver sword 4" and E("S.cons[7]") == E("CN.byId.get('Beast Oil 2').n") and E("document.querySelector('#oilrow .oiltile.sel').dataset.n") == str(E("S.cons[7]")))
    check("%s: the sword's Item stats show 'Oil: Enhanced beast oil', the tile has an oil badge, the oil has its own stats entry; the panel stays open" % label,
          "Oil: Enhanced beast oil" in E("document.querySelector('#invRight .eqitem .eqoil')&&[...document.querySelectorAll('#invRight .eqitem')].map(x=>x.innerText).join('|')") and E("!!document.querySelector('.eqslot[data-i=\"1\"] .oilbadge')") and "Silver sword oil" in E("document.getElementById('invRight').innerText") and not E("document.getElementById('eqpick').hidden"))
    pg.keyboard.press("Escape"); pg.click('#eqbody .eqtile[data-i="0"]'); pg.wait_for_selector("#oilrow .oiltile"); n_steel = E("document.querySelectorAll('#oilrow .oiltile').length"); names = E("[...document.querySelectorAll('#oilrow .oiltile span')].map(s=>s.textContent).join()")
    check("%s: the steel sword's Oil row offers only the 6 oils with the SteelOil tag plus 'No oil' (%d: %s)" % (label, n_steel, names[:80]), n_steel == 7 and "Beast oil" in names and "Hanged Man" in names and "Cursed" not in names, names)
    pg.keyboard.press("Escape")
    # no oil, and the link
    pg.click('#eqbody .eqtile[data-i="1"]'); pg.click('#oilrow .oiltile[data-n="0"]'); gone = E("S.cons[7]"); pg.click('#oilrow .oiltile[data-n="%d"]' % E("CN.byId.get('Beast Oil 2').n")); pg.keyboard.press("Escape")
    code = E("document.getElementById('link').value").split("#")[-1]; want = E("[S.scr,S.cons.join(),S.gear.join()]")
    q = b.new_page(viewport={"width": 1920, "height": 1080}); q.goto(base + "#" + code); until(q, READY); got = q.evaluate("[S.scr,S.cons.join(),S.gear.join()]")
    shown = q.evaluate("[!document.getElementById('screenInv').hidden,!!document.querySelector('.eqslot.cons.on[data-i=\"9\"] img'),!!document.querySelector('.eqslot[data-i=\"1\"] .oilbadge'),document.querySelector('#invRight').innerText.indexOf('Oil: Enhanced beast oil')>=0]"); q.close()
    check("%s: 'No oil' removes it (%s); copy link, open in a new tab: the Inventory screen, the potion in slot 1 and the oil on the silver sword come back (%s)" % (label, gone, shown), gone == 0 and got == want and all(shown), [got, want, shown])
    # Affected by: names of the skills and mutations of this build that change the item
    E("""(()=>{let ti=-1,i=-1;TREES.forEach((t,a)=>t.sk.forEach((s,k)=>{if(s.id==='alchemy_s14'){ti=a;i=k}}));S.lv[ti][i]=1;S.slots[0]=[ti,i];S.cons[0]=CN.byId.get('Mutagen 1').n;eqRender(true)})()""")
    nm = lambda i: E("TREES.flatMap(t=>t.sk).find(s=>s.id==='%s').name" % i); adapt, effic = nm("alchemy_s14"), nm("alchemy_s8")
    aff = E("document.getElementById('invRight').innerText"); tip = E("(()=>{const t=document.querySelector('.eqtile[data-i=\"9\"]');t.focus();return document.getElementById('eqtip').innerText})()")
    check("%s: 'Affected by' names %s for a decoction when that skill is equipped (names only), and nothing for a bomb" % (label, adapt), ("Affected by: " + adapt) in aff and ("Affected by: " + adapt) in tip and E("(()=>{S.cons[4]=CN.byId.get('Samum 1').n;eqRender(true);return document.getElementById('invRight').innerText.split('Samum')[1]})()").find("nothing in this build") >= 0, aff[-200:])
    E("""(()=>{let ti=-1,i=-1;TREES.forEach((t,a)=>t.sk.forEach((s,k)=>{if(s.id==='alchemy_s8'){ti=a;i=k}}));S.lv[ti][i]=1;S.slots[1]=[ti,i];eqRender(true)})()""")
    eff = E("document.getElementById('invRight').innerText")
    check("%s: %s on a bomb: 'Affected by' names it, with the in-game text and the note that the scripts only change crafting yield" % (label, effic), effic in eff and "+1 bomb per slot" in eff and "only add it to the number of bombs a recipe makes" in eff, eff[-300:])
    check("%s: nothing is computed: no totals in Item stats" % label, "total" not in E("document.querySelector('#invRight .eqsec:last-child h3').innerText").lower() or "not added up" in E("document.querySelector('#invRight .eqsec:last-child h3').innerText"))
    # a hand-made link with an oil in a potion slot loses it
    bad = E("(()=>{S.cons[1]=CN.byId.get('Beast Oil 1').n;S.cons[6]=CN.byId.get('Cursed Oil 1').n;return cnValidate()+':'+S.cons[1]+':'+S.cons[6]})()")
    check("%s: an oil in a potion slot, or a silver-only oil on the steel sword (hand-made link), is dropped (%s)" % (label, bad), bad == "2:0:0", bad)
    check("%s: the Item stats heading says base values, not added up" % label, "base values" in E("document.querySelector('#invRight .eqsec:last-child h3').innerText"))
    pg.close()
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, READY); m.evaluate("scrGo('inv')"); until(m, "!document.getElementById('screenInv').hidden")
    m.tap('#eqbody .eqtile[data-i="10"]'); m.wait_for_selector("#pkgrid .pktile"); r = m.evaluate("(()=>{const r=document.querySelector('.eqpmodal').getBoundingClientRect(),p=document.getElementById('eqpick').getBoundingClientRect(),tb=document.getElementById('topbar').getBoundingClientRect();return[Math.round(r.width),Math.round(p.height+tb.bottom),innerWidth,innerHeight,getComputedStyle(document.getElementById('eqpick')).position]})()")
    ok_tiles = m.evaluate("[...document.querySelectorAll('.pktile,.chip,#pkclose')].every(t=>t.getBoundingClientRect().height>=40)")
    check("%s: 390 px: tapping a slot opens the panel as a full-screen sheet below the top bar (%s), its cards and buttons are tap sized" % (label, r), r[0] >= r[2] - 2 and r[1] >= r[3] - 2 and r[4] == "fixed" and ok_tiles, r)
    m.tap("#pkgrid .pktile >> nth=2"); m.tap("#pkequip"); m.wait_for_timeout(200)
    check("%s: 390 px: tapping a card and Equip equips it, the sheet closes, nothing scrolls sideways" % label, m.evaluate("S.cons[1]")>0 and m.evaluate("document.getElementById('eqpick').hidden") and m.evaluate("document.documentElement.scrollWidth-innerWidth") <= 0, m.evaluate("S.cons.join()")); m.close()


def tiercheck(b, base, check, label):
    """The picker shows every tier as its own card (full in-game name, tier label), a family together from Basic to Grandmaster; the Tier filter and the search narrow the cards; the tooltip is the selected card only;
    the worn item is selected when the picker opens and nothing is selected when nothing is worn."""
    pg = b.new_page(viewport={"width": 1920, "height": 1080}); pg.goto(base); until(pg, READY); E = pg.evaluate; openinv(pg)
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()"); pg.fill("#lvl", "30"); pg.click('#eqbody .eqtile[data-i="%d"]' % CHEST); pg.wait_for_selector("#pkgrid .pktile")
    CARDS = "[...document.querySelectorAll('#pkgrid .pktile')].map(t=>({title:t.querySelector('span').textContent,tier:(t.querySelector('.pktr')||{}).textContent||'',low:t.classList.contains('low'),sel:t.classList.contains('sel'),worn:t.classList.contains('worn')}))"
    check("%s: opened with nothing worn: nothing is selected, the detail says so (%s)" % (label, E("document.getElementById('pkside').textContent")), E("document.querySelectorAll('#pkgrid .pktile.sel').length") == 0 and "Select an item" in E("document.getElementById('pkside').textContent"))
    pg.fill("#pkq", "griffin"); pg.wait_for_timeout(100); cards = E(CARDS)
    check("%s: Chest armor, search 'griffin': 5 cards, one per tier, each with its full in-game name and a tier label, Basic to Grandmaster (%s)" % (label, [(c["title"], c["tier"]) for c in cards]),
          [c["tier"] for c in cards] == ["Basic", "Enhanced", "Superior", "Mastercrafted", "Grandmaster"] and [c["title"] for c in cards] == ["Griffin armor", "Enhanced Griffin armor", "Superior Griffin armor", "Mastercrafted Griffin armor", "Grandmaster Griffin armor"], cards)
    check("%s: ... at Level 30 the Mastercrafted (34) and Grandmaster (40) cards are greyed but visible, the others are not (%s)" % (label, [c["low"] for c in cards]), [c["low"] for c in cards] == [False, False, False, True, True], cards)
    pg.click('#pkgrid .pktile[data-id="Gryphon Armor 1"]'); tip = E("document.querySelector('#pkside .eqt-name').textContent"); sets = E("document.querySelector('#pkside .eqt-set').textContent"); chips = E("document.querySelectorAll('#pkside .eqchip').length")
    check("%s: clicking the Enhanced card: the tooltip is that item only, no tier chips (%s | %s | %d chips)" % (label, tip, sets, chips), tip == "Enhanced Griffin armor" and "does not count toward the set bonus in First playthrough" in sets and chips == 0, [tip, sets, chips])
    pg.select_option("#pktier", "Grandmaster"); pg.wait_for_timeout(100); n = E("document.querySelectorAll('#pkgrid .pktile').length"); sel = E("document.querySelectorAll('#pkgrid .pktile.sel').length")
    check("%s: Tier filter 'Grandmaster' (with the search 'griffin') leaves 1 card, and the Enhanced selection is cleared (%d cards, %d selected)" % (label, n, sel), n == 1 and sel == 0, [n, sel])
    pg.fill("#pkq", ""); pg.select_option("#pkset", "set:gryphon"); pg.wait_for_timeout(100); n = E("document.querySelectorAll('#pkgrid .pktile').length")
    check("%s: ... the same filter with the Griffin set filter and no search: 1 card (%d)" % (label, n), n == 1, n)
    pg.select_option("#pktier", "all"); pg.select_option("#pkset", "all"); pg.fill("#pkq", "enhanced griffin"); pg.wait_for_timeout(100); cards = E(CARDS)
    check("%s: search 'enhanced griffin' leaves 1 card (%s)" % (label, [c["title"] for c in cards]), [c["title"] for c in cards] == ["Enhanced Griffin armor"], cards)
    pg.fill("#pkq", "griffin"); pg.wait_for_timeout(100); n = E("document.querySelectorAll('#pkgrid .pktile').length")
    check("%s: search 'griffin' alone: all 5 Griffin cards again (%d)" % (label, n), n == 5, n)
    pg.fill("#pkq", ""); pg.keyboard.press("Escape"); pg.fill("#lvl", "40"); E("(()=>{const d=eqData();S.gear[%d]=d.byId.get('Gryphon Armor 2').n;save();eqRender(true)})()" % CHEST)
    pg.click('#eqbody .eqtile[data-i="%d"]' % CHEST); pg.wait_for_selector("#pkgrid .pktile"); pg.wait_for_timeout(200); tip = E("(document.querySelector('#pkside .eqt-name')||{}).textContent"); cards = E(CARDS)
    vis = E("(()=>{const t=document.querySelector('#pkgrid .pktile.sel'),g=document.getElementById('pkgrid').getBoundingClientRect(),r=t&&t.getBoundingClientRect();return !!r&&r.top>=g.top-1&&r.bottom<=g.bottom+1})()")
    tile = E("document.querySelector('#eqbody .eqtile[data-i=\"%d\"]').getAttribute('aria-label')" % CHEST); st = E("document.querySelector('#eqbody .eqitem h4').textContent")
    check("%s: reopened with a Superior Griffin chest worn: its card is selected, marked worn and in view; the slot tile and Item stats keep the full name (%s | %s | %s)" % (label, tip, tile, st),
          tip == "Superior Griffin armor" and [c["title"] for c in cards if c["sel"]] == ["Superior Griffin armor"] and [c["title"] for c in cards if c["worn"]] == ["Superior Griffin armor"] and vis and "Superior Griffin armor" in tile and st == "Superior Griffin armor", [tip, cards, vis, tile, st])
    pg.close()


def countcheck(b, base, check, label):
    """Set pieces count by the SetBonusPiece tag of the chosen ruleset only (playerWitcher.ws:10972-10981): Basic Feline counts 0 in the first playthrough, per the data in New Game Plus, Grandmaster 3 and 6;
    the tooltip and the Equip set note say so; the new Wolf School tiers group like the other sets; new items round-trip through the link."""
    pg = b.new_page(viewport={"width": 1920, "height": 1080}); pg.goto(base); until(pg, READY); E = pg.evaluate; openinv(pg); pg.fill("#lvl", "100")
    BASIC = ["Lynx School steel sword", "Lynx School silver sword", "Lynx School Crossbow", "", "Lynx Armor", "Lynx Gloves 1", "Lynx Pants 1", "Lynx Boots 1"]
    GM = ["Lynx School steel sword 4", "Lynx School silver sword 4", "Lynx School Crossbow", "", "Lynx Armor 4", "Lynx Gloves 5", "Lynx Pants 5", "Lynx Boots 5"]
    CARD = "[document.querySelector('.eqset h3').textContent,document.querySelectorAll('.eqset li.lit').length]"
    gear(pg, BASIC); a = E(CARD); data = E("EQ_SLOTS.map((s,i)=>eqCur(i)).filter(it=>it&&it.set_bonus_piece).length")
    check("%s: a full Basic Feline set (7 pieces) in the first playthrough counts 0 pieces, no bonus lit (%s)" % (label, a), a[0].endswith("0 counted, 7 worn") and a[1] == 0 and data == 0, [a, data])
    pg.click('#topbar [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'&&!!eqData()"); pg.wait_for_timeout(300); c = E(CARD); data = E("EQ_SLOTS.map((s,i)=>eqCur(i)).filter(it=>it&&it.set_bonus_piece).length"); kept = E("S.gear.filter(Boolean).length")
    check("%s: ... the same build switched to New Game Plus: the Sets panel is recomputed from that ruleset's tags (%s; %d of %d pieces carry the tag)" % (label, c, data, kept), kept == 7 and data == 6 and c[0].endswith("6 counted, 7 worn") and c[1] == 2, [c, data, kept])
    pg.click('#topbar [data-rs="ng"]'); until(pg, "S.rs==='ng'"); pg.wait_for_timeout(300); a2 = E(CARD)
    check("%s: ... and back to the first playthrough: 0 counted again (%s)" % (label, a2), a2[0].endswith("0 counted, 7 worn") and a2[1] == 0, a2)
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()"); gear(pg, ["", "", "", "", "Lynx Armor 4", "Lynx Gloves 5", "Lynx Pants 5", ""]); three = E(CARD)
    gear(pg, GM); six = E(CARD)
    check("%s: Grandmaster Feline in the first playthrough: 3 pieces light the 3-piece bonus, 6 pieces light both (%s, %s)" % (label, three, six), three[0].endswith("3 counted, 3 worn"), [three, six])
    check("%s: ... lit bonuses: 1 at 3 counted pieces, 2 at 6 counted (%s, %s)" % (label, three[1], six[1]), three[1] == 1 and six[1] == 2 and six[0].endswith("6 counted, 7 worn"), [three, six])
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()"); pg.click('#eqbody .eqtile[data-i="%d"]' % CHEST); pg.wait_for_selector("#pkgrid .pktile"); pg.fill("#pkq", "feline"); pg.wait_for_timeout(100)
    pg.click('#pkgrid .pktile[data-id="Lynx Armor 1"]'); tip = E("document.querySelector('#pkside .eqt-set').textContent"); note = E("[...document.querySelectorAll('#pkside .pknote')].map(p=>p.textContent).join(' | ')")
    check("%s: tooltip on a non-counting tier: '%s' and the Equip set note says what will not count and which tier does (%s)" % (label, tip, note),
          tip == "Feline \u00b7 does not count toward the set bonus in First playthrough (no set bonus tag in the game data)" and "will not count toward the set bonus in First playthrough (no set bonus tag in the game data); only the Grandmaster tier counts." in note, [tip, note])
    pg.click('#pkgrid .pktile[data-id="Lynx Armor 4"]'); tip = E("document.querySelector('#pkside .eqt-set').textContent")
    check("%s: ... the Grandmaster tier says it counts (%s)" % (label, tip), tip == "Feline \u00b7 counts toward the set bonus", tip)
    pg.keyboard.press("Escape")
    # the Wolven cards: one per tier, a family together, Legendary as separate cards
    WOLF = "[...document.querySelectorAll('#pkgrid .pktile')].map(t=>t.querySelector('span').textContent).filter(c=>/^(enhanced |superior |mastercrafted |grandmaster )?(legendary |legendary )?wolven armor$/i.test(c))"
    pg.click('#eqbody .eqtile[data-i="%d"]' % CHEST); pg.wait_for_selector("#pkgrid .pktile"); pg.fill("#pkq", "wolven armor"); pg.wait_for_timeout(100); cards = E(WOLF)
    check("%s: first playthrough: the Wolven armor cards, one per tier, Basic to Grandmaster (%s)" % (label, cards), cards == ["Wolven armor", "Enhanced Wolven armor", "Superior Wolven armor", "Mastercrafted Wolven armor", "Grandmaster Wolven armor"], cards)
    pg.keyboard.press("Escape"); pg.click('#topbar [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'"); pg.click('#eqbody .eqtile[data-i="%d"]' % CHEST); pg.wait_for_selector("#pkgrid .pktile"); pg.fill("#pkq", "wolven armor"); pg.wait_for_timeout(100); cards = E(WOLF)
    check("%s: New Game Plus: Wolven armor and Legendary Wolven armor are separate cards, each Basic to Grandmaster, each family together (%s)" % (label, cards),
          cards == ["Wolven armor", "Enhanced Wolven armor", "Superior Wolven armor", "Mastercrafted Wolven armor", "Grandmaster Wolven armor", "Legendary Wolven armor", "Enhanced legendary Wolven armor", "Superior legendary Wolven armor", "Mastercrafted legendary Wolven armor", "Grandmaster legendary Wolven armor"]
          or cards == ["Legendary Wolven armor", "Enhanced legendary Wolven armor", "Superior legendary Wolven armor", "Mastercrafted legendary Wolven armor", "Grandmaster legendary Wolven armor", "Wolven armor", "Enhanced Wolven armor", "Superior Wolven armor", "Mastercrafted Wolven armor", "Grandmaster Wolven armor"], cards)
    pg.keyboard.press("Escape"); pg.click('#topbar [data-rs="ng"]'); until(pg, "S.rs==='ng'")
    # new items round-trip through the link
    NEW = {"steel": "Wolf School steel sword 2", "chest": "Wolf Armor 1", "gloves": "DLC1 Temerian Gloves", "boots": "Nekker Boots", "crossbow": "DLC13 Elven Crossbow"}
    E("(ids=>{const d=eqData();S.gear.fill(0);EQ_SLOTS.forEach((s,i)=>{if(ids[s])S.gear[i]=d.byId.get(ids[s]).n});save();eqRender(true)})", NEW); code = E("location.hash.slice(1)"); want = E("S.gear.join()")
    q = b.new_page(); q.goto(base + "#" + code); until(q, READY); got = q.evaluate("[S.rs,S.gear.join(),EQ_SLOTS.map((s,i)=>eqCur(i)&&eqCur(i).id)]"); q.close()
    ids = [NEW.get(s) for s in ("steel", "silver", "crossbow", "bolts", "chest", "gloves", "trousers", "boots", "mask")]
    check("%s: Wolf School, Temerian, Nekker and DLC13 items round-trip through the link (%s)" % (label, code), got[0] == "ng" and got[1] == want and [x for x in got[2] if x] == [NEW[s] for s in ("steel", "crossbow", "chest", "gloves", "boots")], [got, want])
    n = E("eqData().byId.get('Wolf Armor 1').n"); old = E("eqData().byId.get('Lynx Armor 4').n")
    check("%s: new items got new numbers after the old ones; old numbers did not move (Wolf Armor 1 = %d, Lynx Armor 4 = %d)" % (label, n, old), n > 572 and old == 275, [n, old])
    pg.close()


def levelcheck(b, base, check, label, pg):
    """The level requirement: the game blocks GetItemLevel(item) > GetLevel() (r4Player.ws:11723). Only the Level field counts."""
    E = pg.evaluate

    def opener(i, ident):
        pg.click('#eqbody .eqtile[data-i="%d"]' % i); pg.wait_for_selector("#pkgrid .pktile"); E("(id=>{EQ.pick.sel=eqData().byId.get(id);eqPickRender()})", ident)

    def start(level, bonus=0):
        pg.keyboard.press("Escape") if not E("document.getElementById('eqpick').hidden") else None
        pg.fill("#lvl", str(level)); pg.fill("#bonuspts", str(bonus)); E("(()=>{S.gear.fill(0);save();eqRender(true)})()")
    if E("S.rs") != "ng": pg.click('#topbar [data-rs="ng"]'); until(pg, "S.rs==='ng'")
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
        if E("S.rs") != rs: pg.click('#topbar [data-rs="%s"]' % rs); until(pg, "S.rs==='%s'&&!!eqData()" % rs)
        got = E("(l=>{const o={};Object.keys(l).forEach(k=>{const it=eqData().byId.get(k);o[k]=it?it.required_level:'missing'});return o})", want_lv)
        check("%s: required levels in %s match the scripts (%s)" % (label, rs, ", ".join("%s %s" % kv for kv in list(want_lv.items())[:3]) + ", ..."), got == want_lv, got)
    relic = E("(()=>{const it=eqData().byId.get('Wolf');return it?eqLevel(it).t:''})()"); pg.click('#topbar [data-rs="ng"]'); until(pg, "S.rs==='ng'"); relic = E("eqLevel(eqData().byId.get('Wolf')).t")
    check("%s: an autogen relic is never blocked (the level is rolled when it drops) and says 'Level varies'" % label, relic.startswith("Level varies") and not E("eqLow(eqData().byId.get('Wolf'))"), relic)
    start(100)


def run(b, base, check, label, quick=False):
    errs, events = [], []; pg = b.new_page(viewport={"width": 1400, "height": 950}); pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); E = pg.evaluate
    pg.on("load", lambda p: events.append("load")); pg.on("request", lambda r: events.append("data") if ("/data/items" in r.url or "/data/consumables" in r.url) else None)
    pg.goto(base); check("%s: the equipment and consumables data load after the page has loaded, only items.js, items_ng.js and consumables.js" % label, until(pg, READY) and sorted(E(KEYS)) == ["consumables.js", "items.js", "items_ng.js"] and events.index("load") < (events.index("data") if "data" in events else 99), [events[:4], E(KEYS)])
    layoutcheck(b, base, check, label); copycheck(b, base, check, label); screencheck(b, base, check, label); conscheck(b, base, check, label); invcheck(b, base, check, label); tiercheck(b, base, check, label); countcheck(b, base, check, label)
    openinv(pg)
    pg.fill("#lvl", "100")      # the planner starts at Level 1 and the game blocks items above the level, so the walk-through below runs at the top level
    check("%s: the slot boxes: weapons (steel, silver, bolts, crossbow), consumables (4), bomb and Pocket, mask; armor (chest, gloves, trousers, boots); the second one is a Pocket" % label,
          E("[...document.querySelectorAll('#eqbody .wbox .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "steel,silver,bolts,crossbow" and E("[...document.querySelectorAll('#eqbody .cbox .eqtile[data-i]')].map(b=>b.dataset.i).join()") == "9,10,11,12"
          and E("[...document.querySelectorAll('#eqbody .bbox .eqtile[data-i]')].map(b=>b.dataset.i).join()") == "13,14" and E("[...document.querySelectorAll('#eqbody .maskbox .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "mask"
          and E("[...document.querySelectorAll('#eqbody .abox .eqtile[data-i]')].map(b=>EQ_SLOTS[b.dataset.i]).join()") == "chest,gloves,trousers,boots" and E("document.querySelectorAll('#eqbody .eqtile').length") == 15 and E("[...document.querySelectorAll('#eqbody .bbox .eqsl b')].map(b=>b.textContent).join()") == "Bomb,Pocket" and "Bomb 2" not in E("document.getElementById('eqbody').innerText")
          and E("[...document.querySelectorAll('#eqbody .boxcap')].map(b=>b.textContent).join()") == "Consumables,Bomb and pocket")
    # the chooser for EVERY weapon slot, and Equip
    for slot, i in (("steel", 0), ("silver", 1), ("bolts", 3), ("crossbow", 2)):
        pg.click('#eqbody .eqtile[data-i="%d"]' % i); pg.wait_for_selector("#pkgrid .pktile"); n = E("document.querySelectorAll('#pkgrid .pktile').length"); only = E("[...document.querySelectorAll('#pkgrid .pktile')].every(t=>EQ.rs[S.rs].byId.get(t.dataset.id).slot===EQ.pick.slot)")
        pg.click("#pkgrid .pktile >> nth=0"); pg.click("#pkequip"); pg.wait_for_timeout(150)    # nothing is selected until a card is clicked
        check("%s: the %s chooser lists %d items of that slot only, and Equip puts one in the slot" % (label, slot, n), n > 5 and only and E("S.gear[%d]" % i) > 0 and E("document.getElementById('eqpick').hidden") and E("document.querySelectorAll('#eqbody .eqslot.on')[%d]" % 0) is not None, (n, only))
    E("(()=>{S.gear.fill(0);save();eqRender(true)})()")
    # chooser for the chest slot
    pg.click('#eqbody .eqtile[data-i="4"]'); pg.wait_for_selector("#pkgrid .pktile"); n_all = E("document.querySelectorAll('#pkgrid .pktile').length")
    pg.select_option("#pkset", "set:lynx"); sets_n = E("document.querySelectorAll('#pkgrid .pktile').length")
    pg.fill("#pkq", "grandmaster"); search_n = E("document.querySelectorAll('#pkgrid .pktile').length")
    check("%s: set filter and search narrow the list (%d, then %d of %d)" % (label, sets_n, search_n, n_all), 0 < search_n <= sets_n < n_all)
    tier_names = E("[...document.querySelectorAll('#pktier option')].map(c=>c.textContent).join()")
    check("%s: the picker has a Tier filter: All tiers, then Basic to Grandmaster" % label, tier_names == "All tiers,Basic,Enhanced,Superior,Mastercrafted,Grandmaster", tier_names)
    pg.fill("#pkq", ""); pg.click('#pkgrid .pktile[data-id="Lynx Armor"]'); basic = E("EQ.pick.sel.id"); pg.click('#pkgrid .pktile[data-id="Lynx Armor 4"]'); top = E("EQ.pick.sel.id")
    check("%s: clicking a card selects exactly that item (Basic %s, Grandmaster %s)" % (label, basic, top), basic == "Lynx Armor" and top == "Lynx Armor 4" and E("EQ.pick.sel.tier") == 5, [basic, top])
    E("document.getElementById('lvl').value=1;pointsChanged()"); pg.click('#pkgrid .pktile[data-id="Lynx Armor 4"]')
    check("%s: 'Requires level' is red above the character level and plain at or below it" % label, E("!!document.querySelector('#pkside .eqt-lvl.bad')")); E("document.getElementById('lvl').value=100;pointsChanged()"); pg.click('#pkgrid .pktile[data-id="Lynx Armor"]')
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
    pg.click('#topbar [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'&&!!eqData()"); E("(()=>{S.gear.fill(0);save();eqRender(true)})()")
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
    pg.click('#topbar [data-rs="ng"]'); until(pg, "S.rs==='ng'"); E("(()=>{S.gear.fill(0);S.gear[4]=EQ.rs.ng.byId.get('Lynx Armor 4').n;S.gear[5]=EQ.rs.ng.byId.get('Lynx Gloves 5').n;save();eqRender(true)})()")
    pg.click('#topbar [data-rs="ng_plus"]'); until(pg, "S.rs==='ng_plus'"); toast = E("document.getElementById('toastMsg').textContent"); kept = E("S.gear[4]>0&&S.gear[5]>0")
    check("%s: switching to New Game Plus keeps items that exist in both and says so" % label, kept and "kept" in toast, toast[:100])
    E("(()=>{S.gear[4]=EQ.rs.ng_plus.byId.get('NGP Lynx Armor 4').n;save();eqRender(true)})()"); pg.click('#topbar [data-rs="ng"]'); until(pg, "S.rs==='ng'"); toast = E("document.getElementById('toastMsg').textContent")
    check("%s: switching back clears items that do not exist there (an NGP item), with a notice naming it" % label, E("S.gear[4]") == 0 and E("S.gear[5]") > 0 and "Removed" in toast and "armor" in toast.lower(), toast[:120])
    code = E("document.getElementById('link').value").split("#")[-1]; want = E("[S.rs,S.gear.join()]")
    q = b.new_page(); q.goto(base + "#" + code); until(q, READY); got = q.evaluate("[S.rs,S.gear.join()]"); same = q.evaluate("document.querySelector('#eqbody .eqslot.on .eqsl span')&&document.querySelector('#eqbody .eqslot.on .eqsl span').textContent"); q.close()
    check("%s: a gear link reopens with the same gear and the same mode" % label, got == want and same, [got, want, same])
    levelcheck(b, base, check, label, pg)
    check("%s: no script errors" % label, not errs, errs[:2]); pg.close()
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True); m.goto(base); until(m, READY); m.fill("#lvl", "100"); openinv(m)
    m.tap('#eqbody .eqtile[data-i="4"]'); m.wait_for_selector("#pkgrid .pktile"); m.tap("#pkgrid .pktile >> nth=0"); w2 = m.evaluate("document.documentElement.scrollWidth-innerWidth"); m.tap("#pkequip"); m.wait_for_timeout(200)
    check("%s: on a phone the chooser does not scroll sideways, and tapping equips" % label, w2 <= 0 and m.evaluate("S.gear[4]") > 0, w2); m.close()
