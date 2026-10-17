"""v33: the Quests screen, the quest data and the save's journal, in a real browser.

data(check)                      data/QUESTS.json: shape, regions, drops, the level fixes (no browser)
run(b, base, check, label)       the screen on a build with the FAKE journal text (tests/fixtures/quests): tab, key Q, link, regions, views, list, band, detail, progress, chip, storage
fixture(b, base, check, label)   stats-l9b (29 done / 15 active / 1 failed / 1 inactive) and stats-l9 (28/13/1/1) through Import save; import over existing progress
phone(b, base, check, label)     390 px: nothing scrolls sideways, every control is a 44 px target
text(b, base, check, label, real)the journal text: the live build has it, the public build says it is not included
Used by tests/run_all.py. The saves are local fixtures (never committed): those parts skip when they are absent."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXD = Path.home() / "work" / "w3planner-art" / "save-spike" / "fixtures"
READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"
REGIONS = ["White Orchard", "Vizima", "Velen", "Novigrad", "Skellige", "Kaer Morhen", "Hearts of Stone", "Blood and Wine", "Other & epilogue"]
CHIPS = ["All", "Main", "Secondary", "Contracts", "Treasure hunts", "Gwent", "Races", "Fistfights", "Hide done"]
# the quests of each fixture save whose journal state is Active (the spike's list, from the game's own files and the save)
ACTIVE_L9 = ["An Invitation from Keira Metz", "Count Reuven's Treasure", "Destination: Skellige", "Evil's Soft First Touches", "Fencing Lessons", "Get Junior", "In Ciri's Footsteps", "Master Armorers",
             "Of Dairy and Darkness", "Return to Crookback Bog", "Scavenger Hunt: Viper School Gear", "Temerian Valuables", "The Gangs of Novigrad"]
ACTIVE_L9B = sorted([n for n in ACTIVE_L9 if n != "Temerian Valuables"] + ["Scavenger Hunt: Griffin School Gear", "Scavenger Hunt: Griffin School Gear Upgrade Diagrams - Part 1", "Scavenger Hunt: Griffin School Gear Upgrade Diagrams - Part 2"])
ACTIVE_L9 = sorted(ACTIVE_L9)
# the level hand-fixes (tools/make_quests.py LEVEL_KEY, plus the dlc10 CSV the old glob missed) and the quests that have no level source
FIXED = {"plegmund_poi_01": 40, "plegmund_poi_02": 40, "plegmund_poi_03": 40, "plegmund_poi_04": 40, "plegmund_poi_05": 40, "ep1poi26b": 38, "Wolf Set": 14, "Wolf Upgrades 1A": 21, "Wolf Upgrades 1B": 21,
         "Wolf Upgrades 2": 29, "Wolf Upgrades 2b": 29, "Wolf Upgrades 3": 34, "Wolf Upgrades 3b": 34}
NO_LEVEL = {"cammerlengo", "mq1060_armor_upgrades", "Q309 Novigrad Under Control 2", "Q401 Megascope"}


def until(pg, js, ms=8000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def newpage(b, url, w=1440, h=950, mobile=False, init=None, hash=""):
    pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile, accept_downloads=True); errs, reqs = [], []
    if init: pg.add_init_script(init)
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); pg.on("request", lambda r: reqs.append((r.method, r.url))); pg.goto(url + hash); until(pg, READY); pg.wait_for_timeout(300)
    return pg, errs, reqs


def opened(pg, region=None):
    pg.keyboard.press("q") if pg.evaluate("S.scr") != "q" else None
    ok = until(pg, "S.scr==='q'&&!document.getElementById('qsBody').hidden&&document.querySelectorAll('#qsRegs .qsreg').length===9")
    if region: pg.click('.qsreg[data-r="%s"]' % region)
    return ok


def data(check):
    d = json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8")); qs = d["quests"]; labels = dict(d["regions"])
    check("QUESTS.json: %d quests, each with a journal GUID, id, name, type, region, level (or null), pack and objectives; GUIDs and ids unique" % len(qs),
          all(re.fullmatch(r"[0-9a-f]{32}", q["g"]) and q["id"] and q["n"] and q["t"] in ("main", "side", "contract", "treasure", "gwent", "race", "fist") and q["r"] in labels and q["p"] in ("startup", "bob", "ep1", "dlc0")
              and (q["lv"] is None or 1 <= q["lv"] <= 60) and isinstance(q["o"], list) and isinstance(q["d"], list) and q.get("hs", 1) == 1 for q in qs) and len({q["g"] for q in qs}) == len(qs) == len({q["id"] for q in qs}))
    check("QUESTS.json: the nine tabs in the briefed order", [r[1] for r in d["regions"]] == REGIONS, d["regions"])
    check("QUESTS.json: all 26 Hearts of Stone quests are in the Hearts of Stone tab and all 83 Blood and Wine quests in Blood and Wine, and nothing else is", {q["g"] for q in qs if q["r"] == "hos"} == {q["g"] for q in qs if q["p"] == "ep1"} and
          sum(q["p"] == "ep1" for q in qs) == 26 and {q["g"] for q in qs if q["r"] == "baw"} == {q["g"] for q in qs if q["p"] == "bob"} and sum(q["p"] == "bob" for q in qs) == 83)
    check("QUESTS.json: no debug or placeholder entry ([Interaction], [PL] Exploration, the E3 and press-demo leftovers) and every name is a real title",
          not [q["id"] for q in qs if q["n"].startswith("[") or q["id"] in ("Interactions", "Exploration", "E3 2013", "E3 2013 Fake", "E3 2014", "E3 2014 Griffin", "MS 2014 Werewolf", "BidDebugQuest", "BidDebugQuest2", "Combat")])
    by = {q["id"]: q for q in qs}
    check("QUESTS.json: the %d levels fixed from a differently-named row (Big Feet to Fill 40, Dark Legacy 38, the Wolf School scavenger hunts 14 to 34)" % len(FIXED), all(by[k]["lv"] == v for k, v in FIXED.items()), {k: by[k]["lv"] for k in FIXED if by[k]["lv"] != FIXED[k]})
    check("QUESTS.json: the four quests with no level source keep an empty level, never a guess (%s)" % sorted(NO_LEVEL), {q["id"] for q in qs if q["lv"] is None} == NO_LEVEL, sorted(q["id"] for q in qs if q["lv"] is None))
    check("QUESTS.json: Other & epilogue holds only base-game quests, none from an expansion", all(q["r"] != "oth" or q["p"] in ("startup", "dlc0") for q in qs) and sum(q["r"] == "oth" for q in qs) > 0)
    check("QUESTS.json: objectives and journal entries are lists of GUIDs only (6 objectives of Q704 Starting are also in Q704B Fairy Land and 1 of Q310 is in a Chapter 3 quest: the game files repeat them); no objective title and no journal text is in the file (v33b)",
          all(len({g for g in q["o"]}) == len(q["o"]) and all(re.fullmatch(r"[0-9a-f]{32}", g) for g in q["o"] + q["d"]) for q in qs) and not any(k in q for q in qs for k in ("desc", "text", "obj")) and "\"o\":[[" not in (ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))
    check("QUESTS.json: the Hearts of Stone XP rule is flagged (hs) only on the ten quests whose rewards are named q60: q601intro, q602romance, q602wedding, q603 x4, q604mansion, q605finale", {q["id"] for q in qs if q.get("hs")} == {"q601intro", "q602romance", "q602wedding", "q603painting", "q603bank", "q603getinman", "q603vaultspecialist", "q603diversion", "q604mansion", "q605finale"})
    REG = {"SQ106 Killbill": "no", "mq3031_aging_romance": "no", "mq2048_msg_in_a_bottle": "sk", "SQ108 Master Blacksmith": "ve", "LW_Prologue_Deserter_Camps": "wo", "Q402 Allies for Kaer Morhen": "km", "Q402 Isle of Mists": "km"}
    check("QUESTS.json: the seven hand-assigned regions (Following the Thread and Black Pearl: Novigrad; From a Land Far, Far Away: Skellige; Master Armorers: Velen; Deserters: White Orchard; Brothers in Arms and The Isle of Mists: Kaer Morhen); the other seven stay in Other & epilogue", all(by[k]["r"] == v for k, v in REG.items()) and sorted(q["n"] for q in qs if q["r"] == "oth") == sorted(["Collect 'Em All", "Faithful Friend", "Gwent: Old Pals", "Gwent: Playing Innkeeps", "In Ciri's Footsteps", "Something Ends, Something Begins", "Something Ends, Something Begins"]))
    check("QUESTS.json: Ladies of the Wood (Q105 Witches) is there: main, Velen, level 6 (the E3 2014 demo copy 'The Ladies of the Wood' is dropped)", (by["Q105 Witches"]["n"], by["Q105 Witches"]["t"], by["Q105 Witches"]["r"], by["Q105 Witches"]["lv"]) == ("Ladies of the Wood", "main", "ve", 6) and "E3 2014" not in by)
    kinds = {k for q in qs for k in [q["t"]]}
    check("QUESTS.json: Gwent, Races and Fistfights are told apart from the game's own titles (%s)" % sorted(kinds), {"gwent", "race", "fist"} <= kinds and by["Q103 The Race"]["t"] == "main" and by["mq6001merchant"]["t"] == "race" and by["NVG: Fist Fighting"]["t"] == "fist")


def run(b, base, check, label):
    pg, errs, reqs = newpage(b, base); E = pg.evaluate
    tabs = E("[...document.querySelectorAll('#stabs .stab')].map(b=>b.childNodes[0].textContent.trim())")
    check("%s: Quests is a live tab between Inventory and Character, no longer greyed (%s)" % (label, tabs), tabs.index("Quests") == tabs.index("Character") - 1 and tabs.index("Inventory") < tabs.index("Quests") and not E("document.getElementById('tabQuests').classList.contains('off')") and E("!document.getElementById('tabQuests').dataset.ig"))
    base_link = E("enc()")
    pg.keyboard.press("q"); ok = opened(pg); link = E("location.hash")
    check("%s: key Q opens Quests and the open tab is in the link as s1Q, and only that (%s)" % (label, link[-12:]), ok and E("S.scr") == "q" and link.endswith(".s1Q") and link[:-4] == "#" + base_link and E("document.getElementById('tabQuests').getAttribute('aria-selected')") == "true")
    pg.focus("#lvl"); pg.keyboard.press("q"); stay = E("S.scr"); pg.fill("#lvl", "9"); pg.evaluate("document.activeElement.blur()")
    check("%s: Q typed in a field does not switch screens (%s)" % (label, stay), stay == "q")
    q2, _, _ = newpage(b, base, hash="#" + base_link + ".s1Q"); okq = until(q2, "S.scr==='q'&&!document.getElementById('qsBody').hidden")
    check("%s: a link ending in s1Q opens on Quests; without it a link opens on Character" % label, okq and q2.evaluate("dec(enc().replace(/\\.s1Q$/,'')).scr") == "char"); q2.close()
    regs = E("[...document.querySelectorAll('#qsRegs .qsreg')].map(b=>[b.querySelector('.qsrn').textContent,b.querySelector('small').textContent])")
    check("%s: the nine region tabs, each with its %% done (%s)" % (label, regs), [r[0] for r in regs] == REGIONS and all(re.fullmatch(r"\d+% done", r[1]) for r in regs), regs)
    tl = E("(()=>{const t=document.getElementById('qsVTime');return{dis:t.disabled,txt:t.textContent,title:t.title}})()")
    check("%s: the view switch has Timeline (disabled, 'Needs base-game quest data · coming next'), Level band and List; Quests opens in the List (%s)" % (label, tl), tl["dis"] and "Needs base-game quest data · coming next" in tl["txt"] and E("[QS.view,document.getElementById('qsVList').getAttribute('aria-pressed'),!!document.getElementById('qsRows')]") == ["list", "true", True], tl)
    cr = E("(()=>{const a=document.querySelector('.qscredit a');return{h:a.href,t:a.target,r:a.rel,x:a.textContent,p:a.parentNode.textContent}})()")
    check("%s: the credit link to ChrisRi's Optimal Quest Order Guide opens in a new tab and is a plain link (%s)" % (label, cr), cr["h"] == "https://docs.google.com/spreadsheets/d/1p2R7Mz8FJMkhnKuloh2gpebW_3jMk3vc2EsFslf4mNc" and cr["t"] == "_blank" and "noopener" in cr["r"] and cr["x"] == "Witcher 3 Optimal Quest Order Guide by ChrisRi"
          and cr["p"].startswith("For a hand-curated order with tips, see the"), cr)
    # next up
    nx = E("[...document.querySelectorAll('#qsNext .qscard')].map(c=>c.querySelector('b').textContent)")
    check("%s: Next up shows 4 cards (%s)" % (label, nx), len(nx) == 4, nx)
    # the list
    pg.click("#qsVList"); pg.wait_for_timeout(100); pg.click('.qsreg[data-r="ve"]')
    ch = E("[...document.querySelectorAll('.qschip')].map(c=>c.textContent)"); lv = E("[...document.querySelectorAll('#qsRows .qsrow .qslv')].map(e=>e.classList.contains('na')?null:+e.textContent)")
    nn = [x for x in lv if x is not None]
    check("%s: the List has the chips %s, rows ordered by level (%d in Velen), each with a status icon, name and level" % (label, CHIPS, len(lv)), ch == CHIPS and nn == sorted(nn) and len(lv) == E("QS.data.quests.filter(q=>q.r==='ve').length") and E("document.querySelectorAll('#qsRows .qsrow svg.qsic').length") == len(lv), ch)
    pg.click('.qschip[data-k="treasure"]'); tr = E("[...document.querySelectorAll('#qsRows .qsrow')].length"); pg.click('.qschip[data-k="all"]')
    check("%s: a type chip filters the list (Treasure hunts: %d of %d)" % (label, tr, len(lv)), 0 < tr < len(lv) and tr == E("QS.data.quests.filter(q=>q.r==='ve'&&q.t==='treasure').length"))
    pg.fill("#qsQ", "tale"); s1 = E("[...document.querySelectorAll('#qsRows .qsrow b')].map(e=>e.textContent)"); pg.fill("#qsQ", "")
    check("%s: search finds quests by name in every region (%s)" % (label, s1[:3]), s1 and all("tale" in x.lower() for x in s1) and E("QS.data.quests.filter(q=>q.n.toLowerCase().includes('tale')).length") == len(s1))
    # a quest with no level
    pg.click('.qsreg[data-r="%s"]' % E("QS.data.quests.find(q=>q.lv==null).r")); na = E("(()=>{const e=document.querySelector('#qsRows .qslv.na');return e?{t:e.textContent,tt:e.title}:null})()")
    check("%s: a quest with no level shows — and the tooltip 'not computed yet', last in the list (%s)" % (label, na), na == {"t": "—", "tt": "not computed yet"} and E("[...document.querySelectorAll('#qsRows .qslv')].pop().classList.contains('na')"), na)
    # detail + progress by hand
    pg.click('.qsreg[data-r="ve"]'); pg.click('.qsrow >> nth=0'); g = E("QS.sel"); det = E("(()=>{const d=document.getElementById('qsDetail');return{h:d.querySelector('h2').textContent,meta:d.querySelector('.qsmeta').textContent,marks:[...d.querySelectorAll('.qsmark')].map(x=>x.textContent.trim())}})()")
    check("%s: the detail shows name, 'type · region · level', save status and the four My progress buttons (%s)" % (label, det), det["marks"] == ["Not started", "Active", "Done", "Failed"] and det["meta"].count("·") == 2 and "In your save" not in E("document.getElementById('qsDetail').textContent") and "No save imported" in E("document.getElementById('qsDetail').textContent"), det)
    pg.click('.qsmark[data-s="done"]'); h = E("location.hash"); st = E("localStorage.getItem('w3p.quests.v1')")
    check("%s: My progress > Done is kept in localStorage w3p.quests.v1 and is NOT in the link (%s)" % (label, h[-24:]), E("qsState(QS.sel)") == "done" and g in (st or "") and h.endswith(".s1Q") and g not in h and not re.search(r"[0-9a-f]{32}", h), st)
    pct = E("document.querySelector('.qsreg[data-r=\"ve\"] small').textContent"); check("%s: the region's %% done follows (%s)" % (label, pct), pct != "0% done")
    pg.click('.qschip#qsHide'); hid = E("[...document.querySelectorAll('#qsRows .qsrow')].every(r=>r.dataset.g!==QS.sel)"); pg.click('.qschip#qsHide')
    check("%s: Hide done hides the quest just marked done" % label, hid)
    pg.reload(); until(pg, READY); pg.keyboard.press("q"); opened(pg)
    check("%s: after a reload the mark is still there" % label, E("qsState('%s')" % g) == "done")
    # level band (v33b: full width, range = the quests shown, 24 px per level at least, 14 px dots side by side, a drawer for the detail)
    pg.fill("#lvl", "30"); pg.evaluate("pointsChanged()"); pg.click("#qsVBand"); pg.click('.qsreg[data-r="ve"]'); pg.wait_for_timeout(250)
    rng = E("(()=>{const v=QS.data.quests.filter(q=>q.r==='ve'&&q.lv!=null&&qsState(q.g)!=='done');return[Math.min(...v.map(q=>q.lv)),Math.max(...v.map(q=>q.lv)),v.length]})()")
    BAND = """(()=>{const R=e=>e.getBoundingClientRect(),pl=document.querySelector('.qsbplot.head'),ax=[...document.querySelectorAll('.qsbplot.axis span')],xs=ax.map(e=>R(e).left+R(e).width/2),z=document.querySelector('.qsbplot.head .qsz5'),
      me=document.querySelector('.qsbplot.head .qsme'),ml=document.querySelector('.qsml'),zl=[...document.querySelectorAll('.qszl')],dots=[...document.querySelectorAll('.qsdot')],rows=[...document.querySelectorAll('.qsbrow')],ov=(a,b)=>!(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top);
      return{axis:ax.map(e=>+e.textContent),step:xs.length>1?Math.min(...xs.slice(1).map((x,i)=>x-xs[i])):99,pw:R(pl).width,z:z?R(z).width:0,zl:zl.map(e=>e.textContent),line:R(me).left-R(pl).left,ml:ml.textContent,overlap:zl.some(e=>ov(R(e),R(ml))),
      dots:dots.length,dsz:[...new Set(dots.map(d=>Math.round(d.offsetWidth)))],dtag:[...new Set(dots.map(d=>d.tagName))],minrow:rows.length?Math.min(...rows.map(r=>R(r).height)):0,
      maxlines:rows.length?Math.max(...rows.map(r=>new Set([...r.querySelectorAll('.qsdot,.qsmore')].map(d=>d.style.top)).size)):0,more:[...document.querySelectorAll('.qsmore')].map(b=>b.textContent),
      wide:R(document.querySelector('.qscentre')).width>=R(document.getElementById('screenQ')).width-70,labels:[...document.querySelectorAll('.qsblabel')].map(e=>e.textContent)}})()"""
    bd = E(BAND); slot = bd["pw"] / (rng[1] - rng[0] + 1); nvis = rng[2]
    check("%s: Level band: x from the lowest to the highest level shown (%d to %d), every level labelled, at least 24 px per level (%.1f px), 14 px dots that are buttons, rows of at least 56 px, never more than 3 lines (%s)" % (label, rng[0], rng[1], bd["step"], {k: bd[k] for k in ("step", "dsz", "minrow", "maxlines")}),
          bd["axis"] == list(range(rng[0], rng[1] + 1)) and bd["step"] >= 23.9 and bd["dsz"] == [14] and bd["dtag"] == ["BUTTON"] and bd["minrow"] >= 55.9 and bd["maxlines"] <= 3 and bd["wide"] and bd["labels"][0] == "Main", bd)
    check("%s: Level band: a line at my level (30) labelled 'You · 30', the hatched 5%% XP zone up to level 20 with its label inside it, 'full XP' beside it, no label over the line's label (%s)" % (label, {k: bd[k] for k in ("z", "zl", "line", "ml", "overlap")}),
          abs(bd["z"] - (min(20, rng[1]) - rng[0] + 1) * slot) < 2 and bd["zl"] == ["5% XP", "full XP"] and abs(bd["line"] - (30 - rng[0] + .5) * slot) < 2 and bd["ml"] == "You · 30" and not bd["overlap"], bd)
    nd = E("QS.data.quests.filter(q=>q.r==='ve'&&q.lv!=null&&qsState(q.g)!=='done').length")
    shown = bd["dots"] + sum(int(m[1:]) for m in bd["more"] if m[0] == "+")
    check("%s: Level band: one dot per quest that has a level and is not done (%d), a '+n' chip stands for the rest of a cell that overflows (%s)" % (label, nd, bd["more"]), shown == nd and E("document.querySelectorAll('.qsdot.done').length") == 0, [bd["dots"], bd["more"], nd])
    if bd["more"]:
        n0 = bd["dots"]; pg.click(".qsmore >> nth=0"); n1 = E("document.querySelectorAll('.qsdot').length"); lab = E("document.querySelector('.qsmore[aria-expanded=true]').textContent")
        check("%s: '+n' opens the whole cell (%d dots become %d) and the chip becomes '−'" % (label, n0, n1), n1 > n0 and lab == "−", [n0, n1, lab]); pg.click(".qsmore[aria-expanded=true]")
    # side by side: a region with few levels has wide slots, so dots of one level share a line
    pg.click('.qsreg[data-r="wo"]'); pg.wait_for_timeout(200)
    sb = E("""(()=>{const by={};[...document.querySelectorAll('.qsdot')].forEach(d=>{const k=d.closest('.qsbrow').dataset.k+(d.closest('.qsbrow').querySelector('.qsblabel').textContent)+'|'+Math.round((parseFloat(d.style.left)+7)/ (document.querySelector('.qsbplot.head').offsetWidth/document.querySelectorAll('.qsbplot.axis span').length));(by[k]=by[k]||[]).push([parseFloat(d.style.left),d.style.top])});
      return Object.values(by).filter(l=>l.length>=2).some(l=>new Set(l.map(x=>x[1])).size===1&&new Set(l.map(x=>x[0])).size===l.length)})()""")
    check("%s: dots of the same level sit side by side on one line in a wide slot (White Orchard)" % label, sb)
    pg.click('.qsreg[data-r="ve"]'); pg.wait_for_timeout(200)
    pg.hover(".qsdot >> nth=0"); t1 = E("(()=>{const t=document.getElementById('qsTip');return{vis:!t.hidden,txt:t.textContent,name:QS.byG.get(document.querySelector('.qsdot').dataset.g).n}})()"); pg.mouse.move(5, 5)
    pg.focus(".qsdot >> nth=1"); t2 = E("(()=>{const t=document.getElementById('qsTip');return{vis:!t.hidden,txt:t.textContent,name:QS.byG.get(document.querySelectorAll('.qsdot')[1].dataset.g).n}})()")
    check("%s: hovering or focusing a dot shows a tooltip: name, type · region · level, status (%s)" % (label, t2["txt"][:80]), t1["vis"] and t1["name"] in t1["txt"] and t2["vis"] and t2["name"] in t2["txt"] and t2["txt"].count("·") >= 2 and "Velen" in t2["txt"] and "Not started" in t2["txt"] or "Active" in t2["txt"], [t1, t2])
    pg.evaluate("document.activeElement.blur()"); pg.mouse.move(5, 5); hid = E("document.getElementById('qsTip').hidden")
    pg.press("body", "Tab"); kb = E("document.activeElement.className")
    check("%s: the tooltip goes away when the dot loses focus (%s)" % (label, hid), hid)
    # the drawer
    dpre = E("(()=>{const d=document.getElementById('qsDetail');return[getComputedStyle(d).visibility,document.getElementById('screenQ').classList.contains('qs-open')]})()")
    pg.click(".qsdot >> nth=2"); pg.wait_for_timeout(350)
    dr = E("(()=>{const d=document.getElementById('qsDetail'),r=d.getBoundingClientRect(),tb=document.getElementById('topbar').getBoundingClientRect();return{vis:getComputedStyle(d).visibility,w:Math.round(r.width),right:Math.round(r.right),iw:innerWidth,top:Math.round(r.top),tbb:Math.round(tb.bottom),open:document.getElementById('screenQ').classList.contains('qs-open'),title:d.querySelector('h2').textContent,focus:document.activeElement.id,sel:QS.byG.get(QS.sel).n}})()")
    check("%s: clicking a dot opens the detail as a drawer from the right (closed before: %s; now %dpx wide at the right edge, below the top bar) with the quest's name, focus on ×" % (label, dpre, dr["w"]), dpre == ["hidden", False] and dr["vis"] == "visible" and dr["open"] and 300 <= dr["w"] <= 460 and dr["right"] == dr["iw"] and dr["top"] >= dr["tbb"] - 1 and dr["title"] == dr["sel"] and dr["focus"] == "qsClose", dr)
    pg.click("#qsClose"); pg.wait_for_timeout(300)
    c1 = E("[document.getElementById('screenQ').classList.contains('qs-open'),getComputedStyle(document.getElementById('qsDetail')).visibility,document.activeElement.classList.contains('qsdot')]")
    pg.click(".qsdot >> nth=2"); pg.wait_for_timeout(300); pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    c2 = E("[document.getElementById('screenQ').classList.contains('qs-open'),getComputedStyle(document.getElementById('qsDetail')).visibility,document.activeElement.classList.contains('qsdot')]")
    check("%s: × and Escape close the drawer and give the focus back to the dot (%s, %s)" % (label, c1, c2), c1 == [False, "hidden", True] and c2 == [False, "hidden", True], [c1, c2])
    pg.click("#qsVList"); pg.click(".qsrow >> nth=0"); lc = E("[getComputedStyle(document.getElementById('qsClose')).display,getComputedStyle(document.getElementById('qsDetail')).position,document.getElementById('screenQ').classList.contains('qs-band')]")
    check("%s: in the List the detail is a permanent column (no ×, not a drawer): %s" % (label, lc), lc[0] == "none" and lc[1] in ("sticky", "relative") and lc[2] is False, lc)
    pg.click("#qsVBand"); pg.reload(); until(pg, READY); opened(pg); pv = E("[QS.view,localStorage.getItem('w3p.quests.view'),location.hash.endsWith('.s1Q')]")
    check("%s: the chosen view is remembered in this browser (localStorage w3p.quests.view) and is not in the link (%s)" % (label, pv), pv == ["band", "band", True] and not re.search(r"band|list", E("location.hash")), pv)
    pg.fill("#lvl", "1"); pg.evaluate("pointsChanged()"); pg.wait_for_timeout(200); l1 = E(BAND)
    check("%s: at level 1 there is no 5%% XP zone and no zone labels, the line is 'You · 1' (%s)" % (label, {k: l1[k] for k in ("z", "zl", "ml")}), l1["z"] == 0 and l1["zl"] == [] and l1["ml"] == "You · 1", l1)
    pg.click("#qsVList")
    # XP rule
    xp = E("""(()=>{const n={lv:30,p:'startup'},h={lv:32,p:'ep1',hs:1},o={lv:32,p:'ep1'};return[qsXp(n,40),qsXp(n,39),qsXp(n,20),qsXp(h,30),qsXp(h,38),qsXp(h,39),qsXp(h,42),qsXp(h,22),qsXp(h,50),qsXp({lv:null,p:'startup'},9),qsXp(h,32),qsXp(o,30),qsXp(o,42),qsXp(o,22)]})()""")
    check("%s: the XP rule of r4Game.ws (5%% at 10 or more levels under yours; 16%% per level up to 150%% only for the q60 rewards (hs), 5%% when the scaled value reaches 0; the other Hearts of Stone quests use the plain rule) (%s)" % (label, xp), [round(x, 2) if x is not None else None for x in xp] == [.05, 1, 1, 1.32, .04, .05, .05, 1, .05, None, 1, 1, .05, 1], xp)
    pg.fill("#lvl", "5"); pg.evaluate("pointsChanged()")
    # chip + storage
    pg.click("#qsChip"); m = E("(()=>{const m=document.getElementById('qsMenu');return{open:!m.hidden,txt:m.textContent,btns:[...m.querySelectorAll('.btn')].map(x=>x.textContent.trim())}})()")
    check("%s: the chip 'Saved in this browser ▾' opens a menu with the count marked, the last change, Export progress, Load progress file and Reset (%s)" % (label, m["btns"]), E("document.getElementById('qsChip').textContent") == "Saved in this browser ▾" and m["open"] and m["btns"] == ["Export progress (.json)", "Load progress file", "Reset"]
          and "1 quest marked" in m["txt"] and "Last change:" in m["txt"], m)
    with pg.expect_download() as dl: pg.click("#qsExport")
    body = Path(dl.value.path()).read_text(); ex = json.loads(body)
    check("%s: Export progress downloads w3planner-quests.json (%s) holding the marks, and nothing else of the build" % (label, dl.value.suggested_filename), dl.value.suggested_filename == "w3planner-quests.json" and ex["v"] == 1 and ex["manual"] == {g: "done"} and set(ex) <= {"app", "kind", "exported", "v", "manual", "save", "changed"}, ex)
    tmp = Path("/tmp") / "w3p-q-progress.json"; tmp.write_text(body)
    pg.click("#qsReset"); conf = E("document.getElementById('qsResetYes')!==null"); pg.click("#qsResetNo"); kept = E("qsMarked()")
    pg.click("#qsReset"); pg.click("#qsResetYes"); gone = E("[qsMarked(),localStorage.getItem('w3p.quests.v1')]")
    check("%s: Reset asks first (Keep it leaves the mark, Reset removes it) (%s %s)" % (label, kept, gone), conf and kept == 1 and gone[0] == 0 and (gone[1] is None), [conf, kept, gone])
    pg.set_input_files("#qsLoadFile", str(tmp)); until(pg, "qsMarked()===1"); loaded = E("qsState('%s')" % g)
    tmp.write_text('{"hello":1}'); pg.set_input_files("#qsLoadFile", str(tmp)); pg.wait_for_timeout(300); bad = E("document.getElementById('qsMsg2').textContent")
    check("%s: Load progress file restores the exported marks; a file that is not progress is refused with a message (%s)" % (label, bad), loaded == "done" and "isn't a w3planner quest progress file" in bad, [loaded, bad]); tmp.unlink()
    pg.keyboard.press("Escape"); check("%s: Escape closes the menu" % label, E("document.getElementById('qsMenu').hidden"))
    # nothing leaves the page: only GETs of the site's own files
    bad = [r for r in reqs if r[0] != "GET"]
    check("%s: the whole visit made only GET requests for the site's own files; no quest data went anywhere (%d requests)" % (label, len(reqs)), not bad and all(r[1].startswith(base.rstrip("/")) or r[1].startswith("data:") for r in reqs), bad[:2])
    check("%s: no script errors" % label, not errs, errs[:2]); pg.close()
    # storage that throws: the screen works for the visit and the chip says so
    init = "Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})"
    pg, errs, _ = newpage(b, base, init=init); E = pg.evaluate; ok = opened(pg); chip = E("document.getElementById('qsChip').textContent")
    pg.click("#qsVList"); pg.click(".qsrow >> nth=0"); pg.click('.qsmark[data-s="active"]'); st = E("qsState(QS.sel)"); chip2 = E("document.getElementById('qsChip').textContent")
    check("%s: with storage blocked the screen still works for the visit and the chip says 'Not saved in this browser' (%s / %s, mark %s)" % (label, chip, chip2, st), ok and st == "active" and chip2 == "Not saved in this browser ▾" and not errs, [chip, chip2, errs[:1]]); pg.close()


def text(b, base, check, label, real):
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); pg.fill("#qsQ", "Dairy"); pg.click(".qsrow >> nth=0")
    until(pg, "!document.querySelector('#qsDesc').textContent.includes('Loading')"); t0 = E("[document.querySelectorAll('#qsDesc p:not(.dim)').length,(document.querySelector('.qsspoil')||{}).textContent]")
    check("%s: with no save the journal starts collapsed behind 'Show full journal (spoilers)' (%s)" % (label, t0), t0 == [0, "Show full journal (spoilers)"], t0)
    pg.click(".qsspoil"); until(pg, "document.querySelectorAll('#qsDesc p').length>0"); t = E("document.getElementById('qsDesc').textContent"); n = E("document.querySelectorAll('#qsDesc p').length"); want = E("QS.byG.get(QS.sel).d.length")
    if real: check("%s: the live build shows the whole journal when asked (%d entries, %d characters), loaded when the quest opens" % (label, n, len(t)), n == want and len(t) > 200 and "not included" not in t and E("!!window.W3DATA.quests_desc") and E("document.querySelector('.qsspoil').textContent") == "Hide full journal", t[:80])
    else:
        check("%s: the whole journal on request: every entry as a paragraph, the game's tags as elements, not markup (%d entries, %s)" % (label, n, t[:50]), n == want == 4 and E("document.querySelector('#qsDesc i')!==null&&document.querySelector('#qsDesc b')!==null") and "<i>" not in t, t)
    pg.click(".qsspoil"); back = E("document.querySelectorAll('#qsDesc p:not(.dim)').length"); check("%s: 'Hide full journal' collapses it again" % label, back == 0)
    pg.close()
    pg, errs, reqs = newpage(b, base); E = pg.evaluate; opened(pg)
    check("%s: no quest text script is requested before a quest is opened" % label, not [r for r in reqs if "/quests/" in r[1]] or real, [r for r in reqs if "/quests/" in r[1]]); pg.close()


def publicbuild(b, base, check, label):
    pg, errs, reqs = newpage(b, base); E = pg.evaluate; opened(pg); pg.click(".qsrow >> nth=0"); pg.wait_for_timeout(400); t = E("document.getElementById('qsDesc').textContent"); d = E("document.getElementById('qsDetail').textContent")
    check("%s: the public build says the journal text and the objectives' text are not included, and requests none (%s)" % (label, t), "not included" in t and ("objectives (their text is not included" in d or "No objectives" in d) and not [r for r in reqs if "/quests/" in r[1]] and not errs, [t, errs[:1]]); pg.close()


def fixture(b, base, check, label):
    for sub, want, names in (("stats-l9b", {"done": 29, "active": 15, "failed": 1, "inactive": 1}, ACTIVE_L9B), ("stats-l9", {"done": 28, "active": 13, "failed": 1, "inactive": 1}, ACTIVE_L9)):
        d = FIXD / sub; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
        if not sav: print("  SKIP  %s: Quests against the %s save (fixture not present)" % (label, sub)); continue
        pg, errs, reqs = newpage(b, base); E = pg.evaluate
        pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden")
        sec = E("(()=>{const s=[...document.querySelectorAll('.impsec')].find(x=>x.querySelector('.imphead b').textContent==='Quests');return s?{t:s.textContent,dest:s.querySelector('.impdest').textContent}:null})()")
        check("%s [%s]: the import review has a Quests section: counts, 'Stays on this computer', no compare table when there is no progress yet (%s)" % (label, sub, sec and sec["t"][:90]), sec and "%d done" % want["done"] in sec["t"] and sec["dest"] == "Stays on this computer" and "Keep my hand-ticks" not in sec["t"], sec)
        pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden"); until(pg, "QS.data&&!!QS.store.save")
        c = E("(()=>{const c={};QS.data.quests.forEach(q=>{const s=qsSaveState(q.g);if(s!=='none')c[s]=(c[s]||0)+1});return c})()")
        act = sorted(E("QS.data.quests.filter(q=>qsSaveState(q.g)==='active').map(q=>q.n)"))
        check("%s [%s]: %s" % (label, sub, "the save's journal gives %d done, %d active, %d failed, %d inactive (%s)" % (want["done"], want["active"], want["failed"], want["inactive"], c)), c == want, c)
        check("%s [%s]: the active quests are the spike's list (%s)" % (label, sub, act), act == names, [x for x in act if x not in names] + [x for x in names if x not in act])
        check("%s [%s]: the failed quest is Collect 'Em All and the inactive one Novigrad, Closed City II" % (label, sub), E("QS.data.quests.filter(q=>qsSaveState(q.g)==='failed').map(q=>q.n)") == ["Collect 'Em All"] and E("QS.data.quests.filter(q=>qsSaveState(q.g)==='inactive').map(q=>q.n)") == ["Novigrad, Closed City II"])
        until(pg, "S.scr==='char'"); opened(pg); nx = E("[...document.querySelectorAll('#qsNext .qscard')].map(c=>[c.querySelector('b').textContent,c.querySelector('em').textContent])")
        check("%s [%s]: Next up leads with active quests and shows the current objective of each (%s)" % (label, sub, nx[:2]), len(nx) == 4 and all(x[0] in names for x in nx) and all(x[1] and "not known" not in x[1] for x in nx[:2]), nx)
        pg.click(".qscard >> nth=0"); d1 = E("document.getElementById('qsDetail').textContent"); cur = E("[...document.querySelectorAll('.qscur li')].map(x=>x.textContent)")
        check("%s [%s]: the detail of an active quest names its current objective(s) and says 'In your save: Active' (%s)" % (label, sub, cur), "In your save: Active" in d1 and len(cur) >= 1, d1[:120])
        pr = E("document.querySelectorAll('.qsobjs li.active').length+document.querySelectorAll('.qsobjs li.done').length")
        pg.fill("#qsQ", "") if E("!!document.getElementById('qsQ')") else None
        E("qsSelect(QS.data.quests.find(q=>q.id==='mq1002 Rezydencja').g)"); until(pg, "!document.querySelector('#qsDesc').textContent.includes('Loading')")
        want_e = E("(q=>q.d.filter(g=>QS.store.save.e[g]&&QS.store.save.e[g]!=='inactive').length)(QS.byG.get(QS.sel))"); got_e = E("document.querySelectorAll('#qsDesc p:not(.dim)').length"); btn = E("(document.querySelector('.qsspoil')||{}).textContent")
        check("%s [%s]: with a save only the journal entries the save has shown are listed (%d of 4), plus 'Show full journal (spoilers)'" % (label, sub, want_e), 1 <= want_e < 4 and got_e == want_e and btn == "Show full journal (spoilers)", [want_e, got_e, btn])
        pg.click(".qsspoil"); all_e = E("document.querySelectorAll('#qsDesc p:not(.dim)').length"); check("%s [%s]: the button shows the whole journal (%d entries)" % (label, sub, all_e), all_e == 4)
        E("QS.reveal.clear();qsRenderDetail()"); until(pg, "!document.querySelector('#qsDesc').textContent.includes('Loading')")
        check("%s [%s]: the objective list marks done and active objectives from the save (%d marked)" % (label, sub, pr), pr >= 1)
        h = E("location.hash")
        check("%s [%s]: nothing of the save's journal is in the link (%s)" % (label, sub, h[-20:]), not re.search(r"[0-9a-f]{32}", h) and h.endswith(".s1Q"))
        st = json.loads(E("localStorage.getItem('w3p.quests.v1')")); check("%s [%s]: the progress in localStorage holds the save's states only for quests, objectives and journal entries of the list (%d quests, %d objectives, %d entries)" % (label, sub, len(st["save"]["q"]), len(st["save"]["o"]), len(st["save"]["e"])), len(st["save"]["q"]) == sum(want.values()) and st["manual"] == {} and len(st["save"]["e"]) > 0)
        if sub == "stats-l9b":
            # over existing progress: hand ticks, then the compare table and the three choices
            g1 = E("QS.data.quests.find(q=>qsSaveState(q.g)==='none'&&q.r==='ve').g"); g2 = E("QS.data.quests.find(q=>qsSaveState(q.g)==='active').g")
            E("qsMark('%s','done');qsMark('%s','done')" % (g1, g2))
            pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden")
            ct = E("(()=>{const s=[...document.querySelectorAll('.impsec')].find(x=>x.querySelector('.imphead b').textContent==='Quests');return{t:s.textContent,rows:[...s.querySelectorAll('table tr')].map(r=>[...r.children].map(c=>c.textContent)),radios:[...s.querySelectorAll('input[type=radio]')].map(r=>[r.value,r.checked,r.parentNode.textContent])}})()")
            check("%s: importing over progress shows a compare table (Now | Keep my hand-ticks | Replace all) and three choices, default 'Use save, keep my hand-ticks' (%s)" % (label, ct["radios"]), ct["rows"][0] == ["", "Now", "Keep my hand-ticks", "Replace all"] and [r[0] for r in ct["radios"]] == ["keep", "replace", "cancel"] and ct["radios"][0][1:] == [True, "Use save, keep my hand-ticks"]
                  and ct["radios"][1][2] == "Replace everything with save" and ct["radios"][2][2].startswith("Cancel") and "2 of your hand-ticks differ" in ct["t"], ct)
            rows = {r[0]: r[1:] for r in ct["rows"][1:]}
            check("%s: the table counts what each choice leaves (Done: now, keep my hand-ticks, replace all = the save's 29: %s)" % (label, rows.get("Done")), rows["Done"][2] == "29" and int(rows["Done"][1]) >= 29, rows)
            pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
            check("%s: 'keep my hand-ticks' keeps both marks over the new save" % label, E("[qsState('%s'),qsState('%s'),qsHand()]" % (g1, g2)) == ["done", "done", 2])
            pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.check('input[name="impq"][value="replace"]'); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
            check("%s: 'Replace everything with save' drops the hand-ticks (%s)" % (label, E("qsHand()")), E("[qsState('%s'),qsState('%s'),qsHand()]" % (g1, g2)) == ["none", "active", 0])
            E("qsMark('%s','done')" % g1); pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.check('input[name="impq"][value="cancel"]'); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
            check("%s: 'Cancel' leaves the quest progress exactly as it was (%s)" % (label, E("qsHand()")), E("[qsState('%s'),qsHand()]" % g1) == ["done", 1])
        check("%s [%s]: no script errors; only GET requests" % (label, sub), not errs and all(r[0] == "GET" for r in reqs), errs[:1]); pg.close()


def phone(b, base, check, label):
    pg, errs, _ = newpage(b, base, w=390, h=844, mobile=True); E = pg.evaluate; ok = opened(pg)
    wide = lambda: E("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth")
    out = {"band": wide()}; pg.click("#qsVList"); pg.wait_for_timeout(100); out["list"] = wide(); pg.click(".qsrow >> nth=0"); pg.wait_for_timeout(100); out["detail"] = wide()
    small = E("[...document.querySelectorAll('.qsreg,.qsv:not(:disabled),.qschip:not(:disabled),.qsmark,.qsback,#qsChip,.qsrow')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().height<43.5).map(e=>e.className+':'+Math.round(e.getBoundingClientRect().height))")
    check("%s: 390 px: the Quests screen never scrolls sideways (%s) and every control is a 44 px target (%s)" % (label, out, small[:3]), ok and all(v <= 1 for v in out.values()) and not small, [out, small[:4]])
    onlydetail = E("(()=>{const c=document.querySelector('.qscentre'),d=document.getElementById('qsDetail');return[getComputedStyle(c).display,getComputedStyle(d).display]})()")
    pg.click("#qsBack"); back = E("getComputedStyle(document.querySelector('.qscentre')).display")
    check("%s: 390 px: a quest opens on its own and Back returns to the list (%s, %s)" % (label, onlydetail, back), onlydetail == ["none", "block"] and back != "none")
    pg.click("#qsVBand"); pg.click('.qsreg[data-r="ve"]'); pg.click(".qsdot >> nth=0"); pg.wait_for_timeout(350)
    dr = E("(()=>{const d=document.getElementById('qsDetail').getBoundingClientRect(),c=document.getElementById('qsClose').getBoundingClientRect();return{w:Math.round(d.width),iw:innerWidth,top:Math.round(d.top),cw:Math.round(c.width),ch:Math.round(c.height),sw:document.documentElement.scrollWidth-innerWidth}})()")
    check("%s: 390 px: in the Level band the drawer fills the screen with a 44 px × and nothing scrolls sideways (%s)" % (label, dr), dr["w"] == dr["iw"] and dr["cw"] >= 44 and dr["ch"] >= 44 and dr["sw"] <= 1 and dr["top"] == 0, dr); pg.click("#qsClose"); pg.click("#qsVList")
    pg.click("#qsChip"); r = E("(()=>{const m=document.getElementById('qsMenu').getBoundingClientRect();return[m.left>=0,m.right<=innerWidth,m.bottom<=innerHeight]})()")
    check("%s: 390 px: the progress menu fits on the screen (%s)" % (label, r), all(r)); check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def live(b, url, check):
    """Smoke test of a deployed site (preview or production): the Quests tab opens with the nine regions and the quest list; the journal text loads when the build has it (the live build) or says it is not included."""
    pg, errs, reqs = newpage(b, url); E = pg.evaluate; ok = opened(pg); n = E("QS.data.quests.length"); real = E("QS_DESC!==null")
    check("quests: the Quests tab opens with the nine regions and %d quests, and the level band draws dots" % n, ok and n > 300 and E("document.querySelectorAll('.qsdot').length") > 0, [ok, n])
    pg.click("#qsVList"); pg.fill("#qsQ", "Dairy"); pg.click(".qsrow >> nth=0"); until(pg, "!document.querySelector('#qsDesc').textContent.includes('Loading')"); t = E("document.getElementById('qsDesc').textContent")
    check("quests: the journal text %s (%d characters)" % ("loads" if real else "is reported as not included", len(t)), (len(t) > 80 and "not included" not in t) if real else "not included" in t, t[:80])
    check("quests: no script errors", not errs, errs[:1]); pg.close()
