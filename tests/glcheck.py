"""v29: the top bar with the greyed in-game-only tabs and the Glossary screen, in a real browser.

run(b, fix, check, label, main=None, real=False)
  fix   URL of a site built with the tiny FAKE glossary (tests/fixtures/glossary): every behaviour is tested there
  main  URL of the site the rest of the suite uses; real=True when it was built with the game's glossary (the live build): the real counts and every real
        susceptibility chip are tested there; real=False when it is the public build: it must say the glossary is not included, and request nothing
Used by tests/run_all.py (online and offline builds) and tests/smoke.py (preview and production, real data)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "glossary"
READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"
ROWS = "document.querySelectorAll('#glRows .glrow').length"
GLINK = "v1.AAAAAAAAAAAAAAAAAAAAAAAAAAA.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.----.1.0.0.0.s1G"      # a Glossary link (made by hand: no skills, no gear), for the public build
REAL_COUNTS = {"bestiary": 129, "characters": 116, "tutorial": 508, "books": 877}      # tools/build_glossary.py EXPECT: books = 833 books + 44 paintings & maps


def until(pg, js, ms=8000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def opened(pg, tab=None):
    pg.evaluate("scrGo('glo')"); ok = until(pg, "!document.getElementById('screenGlo').hidden&&%s>0" % ROWS)
    if tab: pg.click('.glst[data-t="%s"]' % tab); ok = ok and until(pg, "document.querySelector('.glst.on').dataset.t==='%s'&&%s>0" % (tab, ROWS))
    return ok


def newpage(b, url, w=1440, h=900, mobile=False):
    pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile); errs, reqs = [], []
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); pg.on("request", lambda r: reqs.append(r.url)); pg.goto(url); until(pg, READY); pg.wait_for_timeout(500)
    return pg, errs, reqs


def maplink(b, url, check, label):
    """The World Map panel: a plain link to witcher3map.com first, then Open Inventory and Open Glossary; no other tab's panel has the link."""
    pg, errs, reqs = newpage(b, url); E = pg.evaluate; pg.click("#tabMap")
    r = E("""(()=>{const o=document.getElementById('igov'),a=document.getElementById('igMap'),kids=[...o.querySelectorAll('.igbtns > *')].filter(x=>!x.hidden);return{open:!o.hidden,order:kids.map(x=>x.textContent.trim()),tag:a.tagName,href:a.getAttribute('href'),target:a.getAttribute('target'),rel:a.getAttribute('rel'),vis:a.getClientRects().length>0,
      h:Math.round(a.getBoundingClientRect().height),cls:a.className,aria:a.getAttribute('aria-label'),focus:document.activeElement.id}})()""")
    check("%s: the World Map panel has the link first: 'Open witcher3map.com ↗' to https://witcher3map.com, target _blank, rel noopener noreferrer, then Open Inventory and Open Glossary (%s)" % (label, r),
          r["open"] and r["order"] == ["Open witcher3map.com ↗", "Open Inventory", "Open Glossary"] and r["tag"] == "A" and r["href"] == "https://witcher3map.com" and r["target"] == "_blank" and r["rel"] == "noopener noreferrer" and r["vis"] and r["h"] >= 44 and "btn" in r["cls"] and r["focus"] == "igMap", r)
    pg.keyboard.press("Escape"); others = []
    for tid in ("tabAlch", "tabQuests", "tabMed"):
        pg.click("#" + tid); others.append(E("document.getElementById('igMap').getClientRects().length")); pg.keyboard.press("Escape")
    s = E("[S.scr,location.hash.indexOf('s1')<0]"); check("%s: no other tab's panel shows the link (%s), the map tab stays greyed, and opening the panel leaves the screen and the link alone" % (label, others), others == [0, 0, 0] and s == ["char", True] and E("document.getElementById('tabMap').classList.contains('off')"), [others, s])
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def barcheck(b, fix, check, label):
    pg, errs, reqs = newpage(b, fix); E = pg.evaluate
    tabs = E("[...document.querySelectorAll('#stabs .stab')].map(b=>b.childNodes[0].textContent.trim())")
    check("%s: the top bar reads Glossary, Alchemy, Inventory, World Map, Quests, Character, Meditation (%s)" % (label, tabs), tabs == ["Glossary", "Alchemy", "Inventory", "World Map", "Quests", "Character", "Meditation"], tabs)
    live = E("[...document.querySelectorAll('#stabs .stab:not(.off)')].map(b=>b.id)"); off = E("[...document.querySelectorAll('#stabs .stab.off')].map(b=>[b.id,b.querySelector('small').textContent])")
    check("%s: Glossary, Inventory and Character are live; the other four are greyed with an 'in game only' line" % label, live == ["tabGlo", "tabInv", "tabChar"] and [x[0] for x in off] == ["tabAlch", "tabMap", "tabQuests", "tabMed"] and all(x[1] == "in game only" for x in off), [live, off])
    why = {"tabAlch": ("Alchemy", "Crafting happens in the game; plan consumables in Inventory slots."), "tabMap": ("World Map", "The world map is in-game only. For an interactive map, use witcher3map.com, a free, ad-free fan project (CC BY-NC-SA)."),
           "tabQuests": ("Quests", "Quest progress lives in the game."), "tabMed": ("Meditation", "Meditation can only be done in the game.")}
    for tid, (title, reason) in why.items():
        pg.click("#" + tid); r = E("(()=>{const o=document.getElementById('igov');return{open:!o.hidden,title:document.getElementById('igtitle').textContent,only:o.querySelector('.igonly').textContent,why:document.getElementById('igwhy').textContent,btns:[...o.querySelectorAll('.igbtns button')].map(b=>b.textContent),focus:document.activeElement.id,screen:S.scr}})()")
        ok = r["open"] and r["title"] == title and r["only"] == "In-game feature only." and r["why"] == reason and r["btns"] == ["Open Inventory", "Open Glossary"] and r["screen"] == "char"
        pg.keyboard.press("Escape"); closed = E("document.getElementById('igov').hidden") and E("document.activeElement.id") == tid
        check("%s: clicking %s opens the in-game-only panel (title, 'In-game feature only.', its reason, Open Inventory / Open Glossary); Escape closes it and returns focus (%s)" % (label, title, r), ok and closed, r)
    pg.click("#tabQuests"); pg.click("#igInv"); a = E("[S.scr,document.getElementById('igov').hidden]"); pg.click("#tabMed"); pg.click("#igGlo"); c = E("[S.scr,document.getElementById('igov').hidden]")
    check("%s: 'Open Inventory' and 'Open Glossary' in the panel go there (%s, %s)" % (label, a, c), a == ["inv", True] and c == ["glo", True], [a, c])
    pg.click("#tabChar"); steps = []
    for sel in ("#scrPrev", "#scrPrev", "#scrNext", "#scrNext"):
        if not E("document.querySelector('%s').disabled" % sel): pg.click(sel)
        steps.append(E("S.scr"))
    check("%s: the arrows step Character, Inventory, Glossary and back, skipping the greyed tabs, and are disabled at each end (%s)" % (label, steps), steps == ["inv", "glo", "inv", "char"], steps)
    pg.click("#tabGlo"); e1 = E("[document.querySelector('#scrPrev').disabled,document.querySelector('#scrNext').disabled]"); pg.click("#tabChar"); e2 = E("[document.querySelector('#scrPrev').disabled,document.querySelector('#scrNext').disabled]")
    check("%s: on Glossary the left arrow is disabled, on Character the right one (%s, %s)" % (label, e1, e2), e1 == [True, False] and e2 == [False, True], [e1, e2])
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()
    # 1920 and 390: the bar fits, level left, NG and Copy link right, nothing scrolls sideways, Copy link is a 44 px target on the phone
    for w, h in ((1920, 1080), (1100, 800), (390, 844)):
        pg, errs, reqs = newpage(b, fix, w, h, w < 600); opened(pg)
        g = pg.evaluate("""(()=>{const B=s=>{const r=document.querySelector(s).getBoundingClientRect();return{l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),h:Math.round(r.height)}};
          return{lvl:B('.lvlblock'),tabs:B('.scrtabs'),right:B('.topright'),copy:B('#copy'),sw:document.documentElement.scrollWidth,vw:innerWidth,stabsW:[document.getElementById('stabs').scrollWidth,document.getElementById('stabs').clientWidth]}})()""")
        if w >= 1500: ok = g["lvl"]["r"] <= g["tabs"]["l"] and g["tabs"]["r"] <= g["right"]["l"] and abs(g["lvl"]["t"] - g["tabs"]["t"]) < 40
        else: ok = g["tabs"]["b"] <= g["lvl"]["t"] + 2 and g["right"]["r"] <= w and g["copy"]["r"] <= w
        if w < 600: ok = ok and g["copy"]["h"] >= 44 and g["stabsW"][0] > g["stabsW"][1]
        check("%s: Glossary at %d px: the bar fits (Level left, NG and Copy link right or below, tabs %s), no sideways scroll, Copy link reachable (%s)" % (label, w, "scroll sideways on the phone" if w < 600 else "in a row", g), ok and g["sw"] <= g["vw"], g); pg.close()


def run(b, fix, check, label, main=None, real=False, quick=False):
    barcheck(b, fix, check, label); maplink(b, fix, check, label)
    man = json.loads((FIX / "manifest.json").read_text())["counts"]; want = {"bestiary": man["bestiary"], "characters": man["characters"], "tutorial": man["tutorial"], "books": man["books"] + man["paintings"]}
    # nothing loads before Glossary opens, then only what the tab needs
    pg, errs, reqs = newpage(b, fix); E = pg.evaluate; gl = lambda: [u.rsplit("/", 1)[-1] for u in reqs if "/glossary/" in u]
    check("%s: no Glossary request until the Glossary screen opens (%s)" % (label, gl()), not gl(), gl())
    opened(pg); g1 = gl(); js = [x for x in g1 if x.endswith(".js")]
    check("%s: opening Glossary loads only the Bestiary file and its pictures (%s)" % (label, js), len(js) == 1 and js[0].startswith("bestiary."), js)
    pg.click('.glst[data-t="characters"]'); until(pg, "document.querySelector('.glst.on').dataset.t==='characters'&&%s>0" % ROWS); js = [x for x in gl() if x.endswith(".js")]
    check("%s: another tab's file loads when that tab opens (%s)" % (label, js), len(js) == 2 and js[1].startswith("characters."), js)
    opened(pg, "books"); js = [x.split(".")[0] for x in gl() if x.endswith(".js")]
    check("%s: Books loads its small index and only the body file of the opened book, not the others (%s)" % (label, js), "books_index" in js and "books_book" in js and "books_note" not in js and "books_quest" not in js and "tutorial" not in js, js)
    # counts and the layout of every tab
    for tab in ("bestiary", "tutorial", "characters", "books"):
        opened(pg, tab); r = E("""(()=>{const rows=[...document.querySelectorAll('#glRows .glrow')];return{n:rows.length,count:document.getElementById('glCount').textContent,groups:[...document.querySelectorAll('#glRows .glgroup')].map(g=>g.textContent),
          thumbs:document.querySelectorAll('#glRows .glth').length,names:[...document.querySelectorAll('#glRows .glrow')].map(r=>r.querySelector('b').textContent)}})()""")
        check("%s: %s lists %d entries (%s)" % (label, tab, want[tab], r["count"]), r["n"] == want[tab] and str(want[tab] if tab != "books" else man["books"]) in r["count"], r)
        if tab == "tutorial": check("%s: the Tutorial list has no thumbnails and is grouped by the game's categories (%s)" % (label, r["groups"][:4]), r["thumbs"] == 0 and len(r["groups"]) >= 3, r)
        else: check("%s: %s rows have a thumbnail, grouped under headings (%s)" % (label, tab, r["groups"]), r["thumbs"] == r["n"] and len(r["groups"]) >= 2, r)
        if tab in ("bestiary", "characters", "books", "tutorial"):
            order = E("""(()=>{const f=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
              return[...document.querySelectorAll('#glRows .glgrp')].every(g=>{const n=[...g.querySelectorAll('.glrow b')].map(b=>b.textContent);return n.every((x,i)=>!i||f(n[i-1])<=f(x))})})()""")
            check("%s: %s is A to Z inside each group" % (label, tab), order)
    opened(pg, "bestiary")
    # groups fold and unfold
    vis = "(()=>({heads:[...document.querySelectorAll('#glRows .glgroup.tog')].map(h=>h.getAttribute('aria-expanded')),rows:document.querySelectorAll('#glRows .glgrp:not([hidden]) .glrow').length,all:document.querySelectorAll('#glRows .glrow').length,count:document.getElementById('glCount').textContent,fold:document.getElementById('glFold').textContent}))()"
    f0 = E(vis); pg.click('#glRows .glgroup.tog'); f1 = E(vis); pg.click('#glRows .glgroup.tog'); f2 = E(vis)
    check("%s: Bestiary groups fold: clicking Beasts hides its rows and says so, clicking again shows them; the count does not change (%s -> %s -> %s)" % (label, f0["rows"], f1["rows"], f2["rows"]),
          f0["heads"] == ["true", "true"] and f1["heads"] == ["false", "true"] and f1["rows"] == f0["rows"] - 4 and f1["all"] == f0["all"] and f2["rows"] == f0["rows"] and f1["count"] == f0["count"], [f0, f1, f2])
    pg.click('#glFold'); g1 = E(vis); pg.click('#glFold'); g2 = E(vis)
    check("%s: 'Collapse all' folds every group and becomes 'Expand all', which unfolds them (%s, %s)" % (label, g1["fold"], g2["fold"]), g1["rows"] == 0 and g1["fold"] == "Expand all" and g2["rows"] == f0["rows"] and g2["fold"] == "Collapse all", [g1, g2])
    pg.click('#glFold'); pg.fill("#glQ", "griffin"); pg.wait_for_timeout(450); h1 = E(vis + "")
    d1 = E("document.querySelector('#glRows .glgroup.tog').getAttribute('aria-disabled')"); pg.fill("#glQ", ""); pg.wait_for_timeout(450); h2 = E(vis)
    check("%s: a search opens the groups that have results; clearing it brings the folds back (%s then %s)" % (label, h1["heads"], h2["heads"]), h1["rows"] >= 1 and "true" in h1["heads"] and d1 == "true" and h2["heads"] == ["false", "false"], [h1, h2, d1])
    E("glSelect('bestiary','alpha_wolf')"); h3 = E(vis); check("%s: opening an entry of a folded group unfolds that group (%s)" % (label, h3["heads"]), h3["heads"][0] == "true", h3)
    E("(()=>{const c=GL.col.bestiary;Object.keys(c).forEach(k=>c[k]=false);glRenderList()})()")
    # entry view: every stage labelled in order, the game's markup becomes elements, nothing is injected
    pg.click('.glrow[data-id="alpha_wolf"]'); until(pg, "document.getElementById('glTitle').textContent==='Alpha Wolf'")
    v = E("""(()=>{const t=document.getElementById('glText');return{labels:[...t.querySelectorAll('.glstlabel')].map(x=>x.textContent),i:!!t.querySelector('i'),b:!!t.querySelector('b'),color:!!t.querySelector('span[style*="color"]'),key:[...t.querySelectorAll('.glkey')].map(x=>x.textContent),
      raw:/[<>]/.test(t.textContent),pic:document.querySelector('#glPic img')&&document.querySelector('#glPic img').getAttribute('src'),weak:[...document.querySelectorAll('#glWeak .glchip')].map(c=>[c.tagName,c.textContent])}})()""")
    check("%s: an entry shows all its stages labelled Entry 1, 2, the game's tags as elements, a [Select] button placeholder, no raw tags (%s)" % (label, v["labels"]), v["labels"] == ["Entry 1", "Entry 2"] and v["i"] and v["b"] and v["color"] and v["key"] == ["[Select]"] and not v["raw"], v)
    kl = E("['GUI_PC_Select','End_Color','Color_Gwint','CastSign','ICO_HansaHideout','IK_LeftMouse','GI_AxisLeftY,1','AttackWithAlternateLight_mod','q301_drawing_oven'].map(glKeyLabel)")
    check("%s: the game's <<placeholders>> read as small words, colour switches vanish (%s)" % (label, kl), kl == ["Select", None, None, "Cast Sign", "Hansa Hideout", "Left Mouse", "Axis Left Y", "Attack With Alternate Light", "picture"], kl)
    check("%s: the picture is a hashed file in glossary/img (%s)" % (label, v["pic"]), bool(v["pic"]) and v["pic"].startswith("glossary/img/") and v["pic"].endswith(".webp"), v["pic"])
    check("%s: SUSCEPTIBILITY: items are buttons, a sign is a plain label (%s)" % (label, v["weak"]), [w[0] for w in v["weak"]] == ["BUTTON", "BUTTON", "SPAN"] and v["weak"][2][1] == "Aard", v["weak"])
    pg.click('.glrow[data-id="stone_golem"]'); until(pg, "document.getElementById('glTitle').textContent==='Stone Golem'")
    inert = E("({pwned:window.__pwned,img:!!document.querySelector('#glText img'),script:!!document.querySelector('#glText script'),text:document.getElementById('glText').textContent.includes('stays text'),nopic:!!document.querySelector('#glPic .glnopic')})")
    check("%s: markup in the text is inert (no script, no image, nothing runs) and an entry without a picture says so (%s)" % (label, inert), inert["pwned"] is None and not inert["img"] and not inert["script"] and inert["text"] and inert["nopic"], inert)
    # every susceptibility chip lands on its Inventory card
    chips = E("[...new Set(glEntries('bestiary').flatMap(e=>e.weak.filter(w=>w.k==='item').map(w=>w.id)))]"); bad = []
    for cid in chips:
        eid = E("glEntries('bestiary').find(e=>e.weak.some(w=>w.id==='%s')).id" % cid); E("scrGo('glo')"); until(pg, "!document.getElementById('screenGlo').hidden"); opened(pg, "bestiary")
        E("glSelect('bestiary','%s')" % eid); until(pg, "document.querySelector('.glchip[data-id=\"%s\"]')" % cid); pg.click('.glchip[data-id="%s"]' % cid)
        ok = until(pg, "S.scr==='inv'&&!!EQ.pick&&!!document.querySelector(\"#pkgrid .pktile.sel[data-id='%s'], #oilrow .oiltile.hl\")" % cid, 5000)
        if ok:
            ok = E("(()=>{const it=CN.byId.get('%s'),p=EQ.pick;if(it.cat==='oil')return(p.i===0||p.i===1)&&!!document.querySelector('#oilrow .oiltile.hl[data-n=\"'+it.n+'\"]')&&(p.i===0)===(CN.bySlot[CN_SLOTS[6]]||[]).includes(it);return p.i===(it.cat==='bomb'?13:9)&&p.sel===it&&document.querySelector('#pkgrid .pktile.sel').dataset.id==='%s'})()" % (cid, cid))
        if not ok: bad.append(cid)
    check("%s: every susceptibility chip (%d items) opens Inventory at its card: potions in the Potion panel, bombs in the Bomb panel, oils in the Oil row of the sword they fit%s" % (label, len(chips), (" FAILED: %s" % bad) if bad else ""), not bad, bad)
    # search: this tab
    E("scrGo('glo')"); opened(pg, "bestiary"); pg.fill("#glQ", "ZOLTAN"); until(pg, "%s===1" % ROWS)
    s1 = E("({n:%s,count:document.getElementById('glCount').textContent,title:document.getElementById('glTitle').textContent,mark:[...document.querySelectorAll('#glText mark')].map(m=>m.textContent),groups:document.querySelectorAll('#glRows .glgroup').length})" % ROWS)
    check("%s: search in this tab is case- and accent-insensitive, filters the list in place and highlights the match (%s)" % (label, s1), s1["n"] == 1 and s1["title"] == "Zoltán's Hound" and s1["mark"] == ["Zoltán"] and "1 of" in s1["count"], s1)
    pg.fill("#glQ", "wolf"); pg.wait_for_timeout(500); until(pg, "%s>=1" % ROWS); s2 = E("[...document.querySelectorAll('#glRows .glrow b')].map(b=>b.textContent)")
    check("%s: a word found only in the text of an entry finds it too (%s)" % (label, s2), "Alpha Wolf" in s2, s2)
    pg.fill("#glQ", "qqqq"); pg.wait_for_timeout(500); until(pg, "!!document.querySelector('#glRows .glhint')"); check("%s: a search with no match says so" % label, "Nothing matches" in E("document.querySelector('#glRows .glhint').textContent"))
    pg.fill("#glQ", ""); until(pg, "%s===%d" % (ROWS, want["bestiary"]))
    # keyboard: the list, the sub-tabs
    pg.focus('#glRows .glrow'); pg.keyboard.press("ArrowDown"); kb = E("[document.activeElement.dataset.id,document.querySelector('#glRows .glrow.on')&&document.querySelector('#glRows .glrow.on').dataset.id,document.getElementById('glTitle').textContent]")
    pg.focus('#glSubs .glst.on'); pg.keyboard.press("ArrowRight"); until(pg, "document.querySelector('.glst.on').dataset.t==='tutorial'"); kt = E("document.querySelector('.glst.on').dataset.t")
    check("%s: keyboard: Arrow Down moves through the list and opens the entry, Arrow Right switches the sub-tab (%s, %s)" % (label, kb, kt), kb[0] == kb[1] and kb[2] and kt == "tutorial", [kb, kt])
    opened(pg, "bestiary")
    # search: all tabs
    pg.click("#glAll"); pg.fill("#glQ", "wolf"); until(pg, "!!document.querySelector('#glRows .glrow[data-all]')")
    a = E("""(()=>({pressed:document.getElementById('glAll').getAttribute('aria-pressed'),heads:[...document.querySelectorAll('#glRows .glgroup')].map(g=>g.textContent),count:document.getElementById('glCount').textContent,
      rows:[...document.querySelectorAll('#glRows .glrow')].map(r=>[r.dataset.tab,r.dataset.id,r.querySelector('.glsnip').textContent,!!r.querySelector('.glsnip mark')]),books:[...document.querySelectorAll('#glRows .glrow')].filter(r=>r.dataset.tab==='books').length}))()""")
    check("%s: ALL TABS replaces the list with results grouped by tab with counts, each saying 'name match' or showing a highlighted snippet (%s)" % (label, a["heads"]), a["pressed"] == "true" and any(h.startswith("Bestiary (") for h in a["heads"]) and any(h.startswith("Books (3)") for h in a["heads"])
          and all(r[2] == "name match" or r[3] for r in a["rows"]) and any(r[2] == "name match" for r in a["rows"]) and any(r[3] for r in a["rows"]) and "results in" in a["count"], a)
    pg.click('#glRows .glrow[data-all][data-tab="books"][data-id="bk2"]'); until(pg, "document.querySelector('.glst.on').dataset.t==='books'&&document.getElementById('glTitle').textContent==='Letter from Ada'")
    c = E("({tab:document.querySelector('.glst.on').dataset.t,all:document.getElementById('glAll').getAttribute('aria-pressed'),sel:document.querySelector('#glRows .glrow.on')&&document.querySelector('#glRows .glrow.on').dataset.id,mark:[...document.querySelectorAll('#glText mark')].map(m=>m.textContent.toLowerCase())})")
    check("%s: clicking a result switches to its tab, selects the entry and highlights the matched word in the text (%s)" % (label, c), c["tab"] == "books" and c["all"] == "false" and c["sel"] == "bk2" and c["mark"] == ["wolf"], c)
    opened(pg, "books"); pg.fill("#glQ", "chapter two"); until(pg, "%s===1" % ROWS); k = E("[document.getElementById('glTitle').textContent,[...document.querySelectorAll('#glText mark')].length]")
    check("%s: Books text search loads the body files and finds a phrase inside a book (%s)" % (label, k), k[0] == "A Treatise on Wolves" and k[1] >= 1, k)
    # the link carries the screen only
    pg.fill("#glQ", ""); E("document.getElementById('glQ').dispatchEvent(new Event('input'))"); pg.wait_for_timeout(300)
    link = E("enc()"); check("%s: the link has only the screen (s1G); the tab, the entry and the search are not in it (%s)" % (label, link[-24:]), link.endswith(".s1G") and link.count(".") == 8 and "wolf" not in link, link)
    q = b.new_page(viewport={"width": 1300, "height": 900}); q.goto(fix + "#" + link); until(q, READY); st = q.evaluate("[S.scr,!document.getElementById('screenGlo').hidden,document.getElementById('screenChar').hidden]"); q.close()
    check("%s: a link ending in s1G opens on Glossary (%s)" % (label, st), st == ["glo", True, True], st)
    d = E("(()=>{const s=dec(enc().replace(/\\.s1G$/,''));return s&&s.scr})()"); check("%s: without the segment a link opens on Character" % label, d == "char", d)
    pg.close()
    # a phone: the list or the entry, one at a time
    pg, errs, reqs = newpage(b, fix, 390, 844, True); E = pg.evaluate; opened(pg)
    p0 = E("({list:getComputedStyle(document.getElementById('glList')).display,view:getComputedStyle(document.getElementById('glView')).display,search:Math.round(document.getElementById('glQ').getBoundingClientRect().top),subs:[document.getElementById('glSubs').scrollWidth,document.getElementById('glSubs').clientWidth],sw:document.documentElement.scrollWidth,sel:document.querySelectorAll('#glRows .glrow.on').length})")
    check("%s: phone, 390 px: the list fills the screen with Search on top, the sub-tabs scroll sideways, nothing else does (%s)" % (label, p0), p0["list"] != "none" and p0["view"] == "none" and p0["search"] < 420 and p0["subs"][0] > p0["subs"][1] and p0["sw"] <= 390 and p0["sel"] == 0, p0)
    pg.tap('.glrow[data-id="alpha_wolf"]'); until(pg, "document.getElementById('screenGlo').classList.contains('gl-detail')")
    p1 = E("(()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return{list:getComputedStyle(document.getElementById('glList')).display,view:getComputedStyle(document.getElementById('glView')).display,back:Math.round(r('#glBack').height),pic:r('#glPic').top<r('#glTitle').top,sw:document.documentElement.scrollWidth}})()")
    check("%s: phone: tapping an entry opens it full screen, picture on top then the text, with a back arrow (%s)" % (label, p1), p1["list"] == "none" and p1["view"] != "none" and p1["back"] >= 44 and p1["pic"] and p1["sw"] <= 390, p1)
    pg.tap("#glBack"); until(pg, "!document.getElementById('screenGlo').classList.contains('gl-detail')")
    p2 = E("[getComputedStyle(document.getElementById('glList')).display!=='none',document.querySelector('#glRows .glrow.on')?1:0]"); check("%s: phone: the back arrow returns to the list at the same entry (%s)" % (label, p2), p2 == [True, 1], p2)
    cp = E("(()=>{const r=document.getElementById('copy').getBoundingClientRect();return r.height>=44&&r.right<=innerWidth&&r.bottom<=innerHeight+2000})()"); check("%s: phone: Copy link is a 44 px target on the Glossary screen" % label, cp)
    check("%s: no script errors on the Glossary screens" % label, not errs, errs[:1]); pg.close()
    pg, errs, reqs = newpage(b, fix); E = pg.evaluate; opened(pg, "tutorial"); pg.click('#glRows .glgroup.tog'); t1 = E("({heads:[...document.querySelectorAll('#glRows .glgroup.tog')].map(h=>h.getAttribute('aria-expanded')),rows:document.querySelectorAll('#glRows .glgrp:not([hidden]) .glrow').length,fold:document.getElementById('glFold').textContent,hidden:document.getElementById('glFold').hidden})")
    check("%s: Tutorial categories fold too (%s)" % (label, t1), t1["heads"] == ["false", "true", "true"] and t1["rows"] == 2 and t1["fold"] == "Collapse all" and not t1["hidden"], t1); pg.close()
    publicbuild(b, main, fix, link, check, label, real)


def publicbuild(b, main, fix, link, check, label, real=False):
    if main: maplink(b, main, check, label)
    """The site the suite builds for the rest of its checks: the public (and offline) build says the glossary is not included; the live build has the real one."""
    if not main: return
    pg, errs, reqs = newpage(b, main); E = pg.evaluate; gl = lambda: [u for u in reqs if "/glossary/" in u]
    if True:
        if not real:
            E("scrGo('glo')"); pg.wait_for_timeout(600)
            m = E("({msg:document.getElementById('glMsg').textContent,shown:!document.getElementById('glMsg').hidden,body:document.getElementById('glBody').hidden,subs:document.querySelector('#screenGlo .glsub').hidden,rows:%s})" % ROWS)
            check("%s: the public build says 'Glossary content is not included in this build.' and shows no list, with no Glossary request (%s)" % (label, m), m["msg"] == "Glossary content is not included in this build." and m["shown"] and m["body"] and m["subs"] and not m["rows"] and not gl(), [m, gl()])
            q = b.new_page(viewport={"width": 1300, "height": 900}); q.goto(main + "#" + link); until(q, READY); q.wait_for_timeout(400); ok = q.evaluate("[S.scr,!document.getElementById('glMsg').hidden]"); q.close()
            check("%s: a Glossary link opens the same message in the public build (%s)" % (label, ok), ok == ["glo", True], ok)
            check("%s: the public page holds no glossary data" % label, not E("typeof GL_FILES!=='undefined'&&GL_FILES!==null"))
        else:
            counts = {}
            for tab in ("bestiary", "tutorial", "characters", "books"):
                opened(pg, tab); counts[tab] = E(ROWS)
            check("%s: the live build lists %s (bestiary 129, characters 116, tutorials 508, books and paintings 877)" % (label, counts), counts == REAL_COUNTS, counts)
            gc = E("GL_FILES.counts"); check("%s: and its manifest says %s" % (label, gc), gc.get("bestiary") == 129 and gc.get("characters") == 116 and gc.get("tutorial") == 508 and gc.get("books") == 833 and gc.get("paintings") == 44, gc)
            opened(pg, "tutorial"); pics = E("(()=>{const o=[];glEntries('tutorial').forEach(e=>{if(e.img)o.push(e.name)});return o})()")
            check("%s: only 10 tutorials have a picture and none is a placeholder (%s)" % (label, pics), len(pics) == 10, pics)
            opened(pg, "bestiary"); chips = E("[...new Set(glEntries('bestiary').flatMap(e=>e.weak.filter(w=>w.k==='item').map(w=>w.id)))]"); bad = []
            for cid in chips:
                eid = E("glEntries('bestiary').find(e=>e.weak.some(w=>w.id==='%s')).id" % cid); E("scrGo('glo')"); until(pg, "!document.getElementById('screenGlo').hidden"); opened(pg, "bestiary"); E("glSelect('bestiary',%s)" % json.dumps(eid))
                until(pg, "document.querySelector('.glchip[data-id=\"%s\"]')" % cid); pg.click('.glchip[data-id="%s"]' % cid)
                if not until(pg, "S.scr==='inv'&&!!EQ.pick&&!!document.querySelector(\"#pkgrid .pktile.sel[data-id='%s'], #oilrow .oiltile.hl\")" % cid, 5000): bad.append(cid)
            check("%s: every one of the live build's %d susceptibility items opens Inventory at its card%s" % (label, len(chips), (" FAILED: %s" % bad) if bad else ""), len(chips) >= 20 and not bad, bad)
            check("%s: no script errors" % label, not errs, errs[:1])
        pg.close()


def live(b, url, check):
    """Smoke test of a deployed live site (preview or production): the four tabs list the real counts, the pictures load, no errors."""
    pg, errs, reqs = newpage(b, url); E = pg.evaluate; bad = []; pg.on("response", lambda r: bad.append("%d %s" % (r.status, r.url[-50:])) if r.status >= 400 else None); counts = {}
    for tab in ("bestiary", "tutorial", "characters", "books"):
        ok = opened(pg, tab); counts[tab] = E(ROWS) if ok else None
        pg.wait_for_timeout(600); counts[tab + "_pics"] = E("[...document.querySelectorAll('#glRows img')].filter(i=>i.complete&&i.naturalWidth>0).length>0&&[...document.querySelectorAll('#glRows img')].filter(i=>i.complete&&i.naturalWidth===0).length===0")
    check("glossary: the four tabs list %s and their pictures load" % {k: v for k, v in counts.items() if "pics" not in k}, all(counts[k] == v for k, v in REAL_COUNTS.items()) and all(counts[k + "_pics"] for k in ("bestiary", "characters", "books")), counts)
    pg.click('.glst[data-t="bestiary"]'); until(pg, "document.querySelector('.glst.on').dataset.t==='bestiary'"); pg.wait_for_timeout(500)
    big = E("(()=>{const i=document.querySelector('#glPic img');return !!i&&i.complete&&i.naturalWidth>100})()"); check("glossary: the creature picture loads", big)
    check("glossary: no script errors and no HTTP errors", not errs and not bad, (errs + bad)[:2]); pg.close()
