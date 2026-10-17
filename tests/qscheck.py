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


def rules(check):
    """v34: data/QUEST-RULES.json (tools/make_quest_rules.py)"""
    qs = {q["g"]: q for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}; by = {q["id"]: q["g"] for q in qs.values()}
    raw = (ROOT / "data" / "QUEST-RULES.json").read_text(encoding="utf-8"); d = json.loads(raw); R = d["quests"]; gates = {g["id"]: g for g in d["gates"]}
    check("QUEST-RULES.json: every quest in it is a quest of QUESTS.json; only ids, codes and numbers (no game text: every string is a 32-digit GUID, a code of at most 12 characters, or a gate / point name)",
          set(R) <= set(qs) and all(set(r) <= {"s", "h", "c", "a"} for r in R.values()) and all(re.fullmatch(r"[0-9a-f]{32}", g) for g in R) and
          all(re.fullmatch(r"[0-9a-f]{32}", a) for r in R.values() for a in r.get("a", [])) and set(R_ for r in R.values() for R_ in [r.get("s")] if R_) <= {p[0] for p in d["points"]} and len(raw) < 60000)
    check("QUEST-RULES.json: %d gates: the base-game gates in story order (%s) and the Blood and Wine and Hearts of Stone ones" % (len(gates), [g["id"] for g in d["gates"] if g["lane"] == "b"]),
          [g["id"] for g in sorted(d["gates"], key=lambda g: g["x"]) if g["lane"] == "b"] == ["prologue", "isle", "battle", "novigrad3", "skellige3", "naglfar", "ciri", "finish"] and {"bawnight", "baw703", "hos"} <= set(gates) and all(set(g) == {"id", "name", "lane", "x", "done", "next"} for g in gates.values()))
    check("QUEST-RULES.json: Q106 and Q107 fail at Isle of Mists (a whole-quest Failure), the story points of Q402, Q403 and Q111 are Isle of Mists, Battle of Kaer Morhen and Act III",
          R[by["Q106 Keira's bussiness"]]["c"] == [["isle", "q", "f"]] and R[by["Q107 Swamps"]]["c"] == [["isle", "q", "f"]] and R[by["Q402 Isle of Mists"]]["s"] == "i" and R[by["Q403 Battle of Kaer Morhen"]]["s"] == "b" and R[by["Q111 Imlerith"]]["s"] == "3")
    check("QUEST-RULES.json: left out: the temporary toggles (MQ3026 Novigrad Horse Racing has no cutoff) and the demon-mark flag (Q310 Ciri's Night Out has none); Collect 'Em All has no rule; a story point derived by default is stored as unknown (mq1001 Dog Trail has none)",
          "c" not in R.get(by["MQ3026 Novigrad Horse Racing"], {}) and "c" not in R.get(by["Q310 Ciri's Night Out"], {}) and by["Card Game Meta: Gather All"] not in R and "s" not in R.get(by["mq1001 Dog Trail"], {}) and
          sum("s" not in R.get(g, {}) for g in qs) == 191 and sum("s" in r for r in R.values()) == 210)
    check("QUEST-RULES.json: Hearts of Stone and Blood and Wine quests all have their lane as story point; no cutoff is stored for a quest on a toggle", all(R[g]["s"] == "h" for g, q in qs.items() if q["p"] == "ep1") and all(R[g]["s"] == "w" for g, q in qs.items() if q["p"] == "bob"))


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
    tl = E("(()=>{const t=document.getElementById('qsVTime');return{dis:t.disabled,txt:t.textContent}})()")
    check("%s: the view switch has Timeline (enabled since v34), Level band and List; Quests opens in the List (%s)" % (label, tl), not tl["dis"] and tl["txt"] == "Timeline" and E("[QS.view,document.getElementById('qsVList').getAttribute('aria-pressed'),!!document.getElementById('qsRows')]") == ["list", "true", True], tl)
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
    rng = E("(()=>{const v=QS.data.quests.filter(q=>q.r==='ve'&&q.lv!=null&&qsState(q.g)!=='done');return[Math.min(qsMy(),...v.map(q=>q.lv)),Math.max(qsMy(),...v.map(q=>q.lv)),v.length]})()")
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
    pg, errs, reqs = newpage(b, base); E = pg.evaluate; before = [r for r in reqs if "/quests/" in r[1]]; opened(pg); until(pg, "!!QS.desc"); after = [r for r in reqs if "/quests/" in r[1]]
    check("%s: the quest text file is not requested until the Quests tab opens (Next up needs the objective titles), and then once (%d)" % (label, len(after)), not before and len(after) == 1, [before, after]); pg.close()


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
        until(pg, "S.scr==='char'"); opened(pg); until(pg, "!!QS.desc"); nx = E("[...document.querySelectorAll('#qsNext .qscard')].map(c=>[c.querySelector('b').textContent,c.querySelector('em').textContent])")
        check("%s [%s]: Next up leads with the quests that fail at the next gate the save has not passed, each labelled 'Fails at Isle of Mists' (%s)" % (label, sub, nx[:2]), len(nx) == 4 and all(x[1] == "Fails at Isle of Mists" for x in nx), nx)
        isle = E("QS.data.quests.find(q=>q.id==='Q402 Isle of Mists').g"); E("qsMark('%s','done')" % isle); nx = E("[...document.querySelectorAll('#qsNext .qscard')].map(c=>[c.querySelector('b').textContent,c.querySelector('em').textContent])")
        act = [x for x in nx if not x[1].startswith("Fails at")]
        check("%s [%s]: once Isle of Mists counts as passed the next gate is the Battle of Kaer Morhen, and after its quests Next up goes on with the active quests and their current objective (%s)" % (label, sub, nx), nx[0][1] == "Fails at Battle of Kaer Morhen" and act and all(x[0] in names and x[1].startswith("Invented objective") for x in act), nx)
        E("qsMark('%s',null)" % isle)
        E("qsSelect(QS.data.quests.find(q=>q.id==='Q107 Swamps').g)"); d1 = E("document.getElementById('qsDetail').textContent"); cur = E("[...document.querySelectorAll('.qscur li')].map(x=>x.textContent)")
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
    lst = E("document.querySelectorAll('#qsRows .qsrow').length"); pg.click("#qsVBand"); pg.wait_for_timeout(300)
    check("quests: the Quests tab opens in the List with the nine regions and %d quests (%d rows), and the level band draws dots" % (n, lst), ok and n > 300 and lst > 0 and E("document.querySelectorAll('.qsdot').length") > 0, [ok, n, lst])
    pg.click("#qsVList"); pg.fill("#qsQ", "Dairy"); pg.click(".qsrow >> nth=0"); until(pg, "!document.querySelector('#qsDesc').textContent.includes('Loading')"); t = E("document.getElementById('qsDesc').textContent")
    check("quests: the journal text %s (%d characters)" % ("loads" if real else "is reported as not included", len(t)), (len(t) > 80 and "not included" not in t) if real else "not included" in t, t[:80])
    check("quests: no script errors", not errs, errs[:1]); pg.close()


TOK = {"main": "#d8b45a", "side": "#9fb7d9", "contract": "#e0707a", "treasure": "#6fc29a", "gwent": "#b79be6", "race": "#5ccfd0", "fist": "#d2955f"}
KNAME = {"main": "Main", "side": "Secondary", "contract": "Contracts", "treasure": "Treasure hunts", "gwent": "Gwent", "race": "Races", "fist": "Fistfights"}
SHAPE = {"main": ("polygon", 4), "side": ("circle", 0), "contract": ("polygon", 3), "treasure": ("rect", 0), "gwent": ("polygon", 6), "race": ("polygon", 10), "fist": ("polygon", 12)}


def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def lum(c):
    f = lambda v: (v / 255 / 12.92) if v / 255 <= .03928 else ((v / 255 + .055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in c); return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b): x, y = sorted((lum(a), lum(b)), reverse=True); return (x + .05) / (y + .05)


def viewmemory(b, base, check, label):
    """v33c: the Level band / List choice is remembered (localStorage w3p.quests.view) and wins on load, with the tab in the URL and with NO quest progress stored (v33b skipped the view when nothing else was stored)."""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg)
    first = E("[QS.view,localStorage.getItem('w3p.quests.v1'),localStorage.getItem('w3p.quests.view')]")
    pg.click("#qsVBand"); pg.reload(); until(pg, READY); ok1 = opened(pg); a = E("[QS.view,location.hash.endsWith('.s1Q'),!!document.getElementById('qsBand'),localStorage.getItem('w3p.quests.v1')]")
    check("%s: Level band chosen with no progress stored, then a reload with s1Q in the URL: it opens in the Level band (%s)" % (label, a), first == ["list", None, None] and ok1 and a == ["band", True, True, None], [first, a])
    pg.click("#qsVList"); pg.reload(); until(pg, READY); opened(pg); c = E("[QS.view,!!document.getElementById('qsRows')]")
    q2, _, _ = newpage(b, base, hash=E("location.hash")); opened(q2); d = q2.evaluate("QS.view")
    check("%s: and back to the List: it stays in the List after a reload (%s); a new tab of the same browser profile would read the same key" % (label, c), c == ["list", True] and d == "list", [c, d]); q2.close()
    pg.evaluate("localStorage.setItem('w3p.quests.view','bogus')"); pg.reload(); until(pg, READY); opened(pg)
    check("%s: an unknown stored view is ignored (List)" % label, E("QS.view") == "list"); check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def colours(b, base, check, label):
    """v33c: colour and shape by quest type, defined once as CSS tokens; status stays in the icon shape and fill; the type is also named in text."""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg)
    tk = E("(()=>{const s=getComputedStyle(document.documentElement);return Object.fromEntries(['main','side','contract','treasure','gwent','race','fist'].map(k=>[k,s.getPropertyValue('--t-'+k).trim().toLowerCase()]))})()")
    check("%s: the seven type colours are CSS tokens (Main #d8b45a, Secondary #9fb7d9, Contracts #e0707a, Treasure hunts #6fc29a, Gwent #b79be6, Races #5ccfd0, Fistfights #d2955f) (%s)" % (label, tk), tk == TOK, tk)
    low = min(contrast(rgb(v), rgb("#171310")) for v in TOK.values())
    check("%s: every type colour reads on the panel background with a contrast of at least 4.5:1 (lowest %.1f)" % (label, low), low >= 4.5, low)
    pg.click('.qsreg[data-r="ve"]'); got = {}
    for k in TOK:
        if E("document.querySelector('.qschip[data-k=\"%s\"]').disabled" % k): continue
        pg.click('.qschip[data-k="%s"]' % k); got[k] = E("(()=>{const r=document.querySelector('#qsRows .qsrow b'),c=document.querySelector('.qschip.on[data-k=\"%s\"]'),cs=x=>getComputedStyle(x);return[cs(r).color,cs(c).backgroundColor,cs(c).color]})()" % k)
    css = lambda h: "rgb(%d, %d, %d)" % rgb(h)
    check("%s: in the List the name text takes the colour of its type and the selected type chip is filled with it (%d types in Velen: %s)" % (label, len(got), sorted(got)), len(got) >= 5 and all(v[0] == css(TOK[k]) and v[1] == css(TOK[k]) for k, v in got.items()), got)
    pg.click('.qschip[data-k="all"]'); g = E("document.querySelector('#qsRows .qsrow').dataset.g"); k0 = E("QS.byG.get('%s').t" % g)
    pg.click('#qsRows .qsrow >> nth=0'); pg.click('.qsmark[data-s="done"]'); pg.click('.qschip[data-k="all"]')
    d = E("(()=>{const r=document.querySelector('#qsRows .qsrow[data-g=\"%s\"]'),n=[...document.querySelectorAll('#qsRows .qsrow.st-none b')][0];return[getComputedStyle(r.querySelector('b')).opacity,r.querySelector('svg').getAttribute('class'),n?getComputedStyle(n).opacity:null,getComputedStyle(document.querySelector('.qstitle')).color]})()" % g)
    check("%s: a done row has its name at 60%% opacity and a check in its type colour; not-started names stay at full opacity; the drawer/detail title takes the type colour (%s)" % (label, d), d[0] == "0.6" and "qs-done" in d[1] and ("t-" + k0) in d[1] and d[2] == "1" and d[3] == css(TOK[k0]), d)
    check("%s: the separate green for done is gone (no element is coloured #6cbc4a)" % label, E("[...document.querySelectorAll('.qsic,.qsrow b,.qslv')].every(e=>getComputedStyle(e).color!=='rgb(108, 188, 74)')"))
    cd = E("(()=>{const c=document.querySelector('#qsNext .qscard b');return c?[getComputedStyle(c).color,QS.byG.get(document.querySelector('#qsNext .qscard').dataset.g).t]:null})()")
    check("%s: the Next up card title takes the colour of its type (%s)" % (label, cd), cd and cd[0] == css(TOK[cd[1]]), cd)
    # band: shapes by type, legend
    pg.click("#qsVBand"); pg.click('.qsreg[data-r="ve"]'); pg.wait_for_timeout(250)
    lg = E("[...document.querySelectorAll('.qslegend li')].map(li=>({t:li.textContent.trim(),c:getComputedStyle(li).color,tag:li.querySelector('svg').firstElementChild.tagName.toLowerCase(),pts:(li.querySelector('svg').firstElementChild.getAttribute('points')||'').trim().split(/\\s+/).filter(Boolean).length,fill:getComputedStyle(li.querySelector('svg')).fill}))")
    check("%s: the legend under the band names the seven types, each with its own shape (diamond, circle, triangle, square, hexagon, star, plus) in its colour (%s)" % (label, [x["t"] for x in lg]),
          [x["t"] for x in lg] == list(KNAME.values()) and all(x["c"] == css(TOK[k]) and (x["tag"], x["pts"] if x["tag"] == "polygon" else 0) == SHAPE[k] for x, k in zip(lg, TOK)), lg)
    # a failed quest drawn outlined with an x; active filled; not started outline only
    pick = lambda k, n=0: E("document.querySelectorAll('.qsdot.t-%s')[%d].dataset.g" % (k, n)); g1, g2, g3 = pick("side"), pick("treasure"), pick("contract")
    E("qsMark('%s','failed');qsMark('%s','active')" % (g1, g2)); pg.wait_for_timeout(200)
    ds = """(g=>{const d=document.querySelector('.qsdot[data-g="'+g+'"]'),s=d.querySelector('svg'),c=getComputedStyle(d);return{k:d.className,color:c.color,fill:getComputedStyle(s).fill,x:!!s.querySelector('.x'),tag:s.firstElementChild.tagName.toLowerCase(),w:d.offsetWidth,h:d.offsetHeight,btn:d.tagName}})"""
    f1, f2, f3 = pg.evaluate(ds, g1), pg.evaluate(ds, g2), pg.evaluate(ds, g3)
    check("%s: band dots take the shape and colour of their type: not started = outline only, active = filled, failed = outline with a small × (%s %s %s)" % (label, f1["fill"], f2["fill"], f3["fill"]),
          f1["btn"] == "BUTTON" and (f1["tag"], f1["color"], f1["fill"], f1["x"]) == ("circle", css(TOK["side"]), "none", True) and (f2["tag"], f2["color"], f2["x"]) == ("rect", css(TOK["treasure"]), False) and f2["fill"] == css(TOK["treasure"])
          and (f3["tag"], f3["fill"], f3["x"]) == ("polygon", "none", False) and f3["w"] == 14 == f3["h"], [f1, f2, f3])
    pg.hover('.qsdot[data-g="%s"]' % g2); tip = E("document.getElementById('qsTip').textContent"); pg.mouse.move(5, 5)
    pg.click('.qsdot[data-g="%s"]' % g2); pg.wait_for_timeout(300); dm = E("document.querySelector('#qsDetail .qsmeta').textContent")
    check("%s: the tooltip and the drawer still name the type and the status in text, so colour is never the only cue (%s | %s)" % (label, tip[:70], dm), "Treasure hunts" in tip and "Active" in tip and "Treasure hunts" in dm, [tip, dm])
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def banddone(b, base, check, label):
    """v33d: the Level band's own 'Show done' toggle (off by default, remembered in this browser, not in the link, separate from the List's Hide done), done dots, and the axis always holding the player's level."""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); pg.click("#qsVBand"); pg.click('.qsreg[data-r="wo"]'); pg.fill("#lvl", "9"); pg.evaluate("pointsChanged()"); pg.wait_for_timeout(250)
    wo = E("QS.data.quests.filter(q=>q.r==='wo'&&q.lv!=null).map(q=>q.lv)"); lo_q, hi_q = min(wo), max(wo)
    E("QS.data.quests.filter(q=>q.r==='wo'&&q.lv!=null).slice(0,3).forEach(q=>qsMark(q.g,'done'))"); pg.wait_for_timeout(200)
    nd = E("QS.data.quests.filter(q=>q.r==='wo'&&q.lv!=null&&qsState(q.g)==='done').length"); notd = [lv for lv in wo]
    off = E("[document.getElementById('qsShowDone').getAttribute('aria-pressed'),document.querySelectorAll('.qsdot.done').length,document.querySelector('.qsbnote').textContent.slice(0,40),localStorage.getItem('w3p.quests.banddone')]")
    check("%s: the Level band has its own 'Show done' toggle above the band, off by default: no done dots, the footnote says they are hidden (%s)" % (label, off), off[0] == "false" and off[1] == 0 and "hidden" in off[2], off)
    AX = """(()=>{const R=e=>e.getBoundingClientRect(),ax=[...document.querySelectorAll('.qsbplot.axis span')],c=t=>{const e=ax.find(x=>x.textContent===String(t));return e?R(e).left+R(e).width/2:null},pl=document.querySelector('.qsbplot.head'),me=document.querySelector('.qsbplot.head .qsme');
      return{axis:ax.map(e=>+e.textContent),line:R(me).left,c6:c(%d),c9:c(9),pw:R(pl).width,ml:document.querySelector('.qsml').textContent,z:document.querySelector('.qsbplot.head .qsz5')?R(document.querySelector('.qsbplot.head .qsz5')).width:0,slot:R(pl).width/ax.length}})()"""
    a = E(AX % hi_q)
    check("%s: White Orchard (quests %d to %d) at level 9: the axis runs to 9 and 'You · 9' sits right of the level-%d slot, on the 9 (%s)" % (label, lo_q, hi_q, hi_q, {k: a[k] for k in ("c6", "c9", "line")}),
          a["axis"][-1] == 9 and a["axis"][0] == min(lo_q, 9) and a["axis"] == list(range(a["axis"][0], 10)) and a["c6"] is not None and a["line"] > a["c6"] + a["slot"] * (9 - hi_q - 1) and abs(a["line"] - a["c9"]) < 1.5 and a["ml"] == "You · 9", a)
    pg.fill("#lvl", "20"); pg.evaluate("pointsChanged()"); pg.wait_for_timeout(250); z = E(AX % hi_q)
    check("%s: at level 20 the axis runs to 20 and the 5%% zone follows the same scale (up to level 10: %.0f px of %.0f px slot)" % (label, z["z"], z["slot"]), z["axis"][-1] == 20 and abs(z["z"] - (10 - z["axis"][0] + 1) * z["slot"]) < 2, z)
    pg.fill("#lvl", "9"); pg.evaluate("pointsChanged()"); pg.wait_for_timeout(200)
    pg.click("#qsShowDone"); pg.wait_for_timeout(250)
    on = E("""(()=>{const d=[...document.querySelectorAll('.qsdot.done')],s=d[0]&&d[0].querySelector('svg'),sh=s&&s.firstElementChild,cs=sh&&getComputedStyle(sh);return{n:d.length,ck:d.every(x=>x.querySelector('.ck')),fo:cs&&cs.fillOpacity,fill:cs&&cs.fill,col:d[0]&&getComputedStyle(d[0]).color,pressed:document.getElementById('qsShowDone').getAttribute('aria-pressed'),
      note:document.querySelector('.qsbnote').textContent.slice(0,45),ls:localStorage.getItem('w3p.quests.banddone'),hash:location.hash,hide:document.getElementById('qsHide')}})()""")
    k0 = E("QS.byG.get(document.querySelector('.qsdot.done').dataset.g).t")
    check("%s: Show done on: %d done dots, each the filled shape in its type colour at 35%% opacity with a small check, the footnote changes, the choice is stored (w3p.quests.banddone) and not in the link (%s)" % (label, on["n"], {k: on[k] for k in ("fo", "fill", "note", "ls")}),
          on["n"] == nd and on["ck"] and on["fo"] == "0.35" and on["fill"] == on["col"] and on["col"] == "rgb(%d, %d, %d)" % rgb(TOK[k0]) and on["pressed"] == "true" and "shown faintly" in on["note"] and on["ls"] == "1" and on["hash"].endswith(".s1Q") and "done" not in on["hash"], on)
    pg.reload(); until(pg, READY); opened(pg); pr = E("[QS.view,QS.showDone,document.getElementById('qsShowDone').getAttribute('aria-pressed')]")
    pg.click("#qsVList"); hd = E("[document.getElementById('qsHide').getAttribute('aria-pressed'),[...document.querySelectorAll('#qsRows .qsrow.st-done')].length]")
    pg.click("#qsHide"); sd = E("QS.showDone")
    check("%s: the toggle is remembered after a reload, and separate from the List's Hide done (list: Hide done %s, %s done rows; turning it on leaves Show done %s)" % (label, hd[0], hd[1], sd), pr == ["band", True, "true"] and hd[0] == "false" and hd[1] >= 0 and sd is True, [pr, hd, sd])
    pg.click("#qsHide"); pg.click("#qsVBand"); pg.click("#qsShowDone"); off2 = E("[document.querySelectorAll('.qsdot.done').length,localStorage.getItem('w3p.quests.banddone')]")
    check("%s: Show done off again hides them and stores 0 (%s)" % (label, off2), off2 == [0, "0"], off2)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def timeline(b, base, check, label):
    """v34: the Timeline without a save: columns, lanes, gates, rings, unknown placement, Show done, drawer, view memory."""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); h0 = E("location.hash"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(200)
    cols = E("[...document.querySelectorAll('.qstc')].map(e=>e.textContent)"); rows = E("[...document.querySelectorAll('#qsTL .qsblabel')].map(e=>e.textContent)")
    check("%s: Timeline: columns Prologue, Act I, Isle of Mists, Battle of Kaer Morhen, Act III, Epilogue; rows by region, then the Hearts of Stone and Blood and Wine lanes; the region tabs are not shown (%s)" % (label, rows),
          cols == ["Prologue", "Act I", "Isle of Mists", "Battle of Kaer Morhen", "Act III", "Epilogue"] and rows == ["White Orchard", "Vizima", "Velen", "Novigrad", "Skellige", "Kaer Morhen", "Other & epilogue", "Hearts of Stone", "Blood and Wine"] and E("getComputedStyle(document.querySelector('.qsregnav')).display") == "none", [cols, rows])
    gl = E("[...document.querySelectorAll('.qsgl')].map(e=>e.textContent)")
    check("%s: Timeline: the gates are vertical bars with labels (Isle of Mists, Battle of Kaer Morhen, the Night of Long Fangs ...) (%s)" % (label, gl[:4]), {"Isle of Mists", "Battle of Kaer Morhen", "The Night of Long Fangs (Q704)", "Leaving White Orchard", "Game finished"} <= set(gl) and E("document.querySelectorAll('#qsTL .qstlhead .qsgate').length") == 8, gl)
    check("%s: Timeline: no 'You' marker without a save; the view is not in the link and is remembered (%s)" % (label, E("QS.view")), E("document.querySelectorAll('#qsTL .qsme').length") == 0 and E("location.hash") == h0 and E("localStorage.getItem('w3p.quests.view')") == "time", h0)
    st = E("""(()=>{const known=q=>QS.R.quests[q.g]&&QS.R.quests[q.g].s,open=QS.data.quests.filter(q=>known(q)&&QS.timeDone===false&&qsState(q.g)!=='done');const dots=[...document.querySelectorAll('#qsTL .qsdot')],more=[...document.querySelectorAll('#qsTL .qsmore')].reduce((a,b)=>a+(b.textContent[0]==='+'?+b.textContent.slice(1):0),0);
      const unk=new Set(QS.data.quests.filter(q=>!known(q)).map(q=>q.g));return{dots:dots.length,more:more,want:open.length,unkDrawn:dots.filter(d=>unk.has(d.dataset.g)).length,unkN:unk.size,summary:document.querySelector('#qsUnk summary').textContent,items:document.querySelectorAll('#qsUnk .qsunkl .qsrow').length,
      rings:document.querySelectorAll('#qsTL .qsdot .qsring').length,wantRings:open.filter(q=>qsFailsAt(q)).length,ringOnFails:[...document.querySelectorAll('#qsTL .qsring')].filter(r=>r.closest('.qsdot')).every(r=>r.closest('.qsdot').classList.contains('fails'))}})()""")
    check("%s: Timeline: every quest with a known story point is drawn once (%d dots + %d in '+n' chips of %d), none of the %d quests without one; they are in the collapsed row '%s' (%d listed)" % (label, st["dots"], st["more"], st["want"], st["unkN"], st["summary"], st["items"]),
          st["dots"] + st["more"] >= st["want"] and st["unkDrawn"] == 0 and st["summary"] == "Placement not computed yet (%d)" % st["unkN"] and st["items"] == st["unkN"] == 191 and not E("document.getElementById('qsUnk').open"), st)
    check("%s: Timeline: a quest with a confirmed cutoff the save has not passed gets an orange ring (%d rings = %d such quests), and its tooltip says 'Fails at <gate>'" % (label, st["rings"], st["wantRings"]), st["rings"] == st["wantRings"] > 20 and st["ringOnFails"] and True, st)
    pg.hover('#qsTL .qsdot.fails >> nth=0'); tip = E("document.getElementById('qsTip').textContent"); pg.mouse.move(5, 5)
    check("%s: Timeline: tooltip of a ringed dot (%s)" % (label, tip[:80]), "Fails at " in tip and "·" in tip, tip)
    g = E("document.querySelector('#qsTL .qsdot.fails').dataset.g"); pg.click('#qsTL .qsdot.fails >> nth=0'); pg.wait_for_timeout(350)
    dr = E("(()=>{const d=document.getElementById('qsDetail');return{open:document.getElementById('screenQ').classList.contains('qs-open'),txt:d.textContent,sel:QS.sel}})()")
    check("%s: Timeline: a click opens the drawer, which says the story point and 'Fails at <gate>' (%s)" % (label, dr["txt"][:100]), dr["open"] and "Story point:" in dr["txt"] and "Fails at " in dr["txt"] and dr["sel"] == g, dr["txt"][:200])
    pg.keyboard.press("Escape"); pg.wait_for_timeout(250)
    k0 = E("localStorage.getItem('w3p.quests.banddone')"); n0 = E("document.querySelectorAll('#qsTL .qsdot.done').length")
    E("qsMark(QS.data.quests.find(q=>QS.R.quests[q.g]&&QS.R.quests[q.g].s==='a'&&q.r==='ve').g,'done')"); pg.wait_for_timeout(200); n1 = E("document.querySelectorAll('#qsTL .qsdot.done').length")
    pg.click("#qsShowDoneT"); pg.wait_for_timeout(250); n2 = E("document.querySelectorAll('#qsTL .qsdot.done').length"); ls = [E("localStorage.getItem('w3p.quests.timedone')"), E("localStorage.getItem('w3p.quests.banddone')")]
    check("%s: Timeline: Show done is its own toggle (off: %d done dots; on: %d; kept in w3p.quests.timedone, the band's key stays %s) and the footnote follows it" % (label, n1, n2, ls[1]), n0 == 0 == n1 and n2 == 1 and ls == ["1", k0] and "shown faintly" in E("document.querySelector('#qsView .qsbnote:last-child').textContent"), [n0, n1, n2, ls])
    pg.reload(); until(pg, READY); opened(pg); pv = E("[QS.view,QS.timeDone,document.getElementById('qsVTime').getAttribute('aria-pressed'),location.hash===%s]" % json.dumps(h0))
    check("%s: Timeline: the view and Show done are remembered after a reload (%s)" % (label, pv), pv == ["time", True, "true", True], pv)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def timelinesave(b, base, check, label):
    """v34: Timeline, Missable panel, Next up and drawer with the two fixture saves."""
    for sub in ("stats-l9b", "stats-l9"):
        d = FIXD / sub; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
        if not sav: print("  SKIP  %s: Timeline against the %s save (fixture not present)" % (label, sub)); continue
        pg, errs, _ = newpage(b, base); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
        opened(pg); until(pg, "!!QS.R&&!!QS.desc"); h0 = E("location.hash"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(200)
        you = E("(()=>{const m=document.querySelector('#qsTL .qstlhead .qsml'),i=document.querySelector('#qsTL .qstlhead .qsme'),c=[...document.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect()),x=i.getBoundingClientRect().left;return{t:m.textContent,col:c.findIndex(r=>x>=r.left-6&&x<=r.right+6),on:document.querySelector('.qstc.on').textContent}})()")
        passed = E("[...document.querySelectorAll('#qsTL .qstlhead .qsgate')].map((e,i)=>e.classList.contains('passed')?QS.R.gates.filter(g=>g.lane==='b').sort((a,b)=>a.x-b.x)[i].id:null).filter(Boolean)")
        check("%s [%s]: Timeline: 'You' stands at Act I; no cutoff after Leaving White Orchard is passed (Isle of Mists, the Battle ... are not): passed = %s" % (label, sub, passed), you["t"] == "You · Act I" and you["col"] == 1 and you["on"] == "Act I" and passed == ["prologue"], [you, passed])
        miss = E("(()=>{const m=document.getElementById('qsMiss');return{vis:!m.hidden,h:m.querySelector('h3').textContent.trim(),n:+m.querySelector('.qsmn').textContent,names:[...m.querySelectorAll('.qsmissec>.qsmis .qsmi b')].map(e=>e.textContent),foot:m.querySelector('.qsmfoot').textContent,obj:(m.querySelector('.qsmobj summary')||{}).textContent}})()")
        check("%s [%s]: Missable panel above Next up: '%s', %d open quests that fail at Isle of Mists, among them Q106 and Q107 (An Invitation from Keira Metz, Return to Crookback Bog); footnote %r" % (label, sub, miss["h"], miss["n"], miss["foot"]),
              miss["vis"] and miss["h"].startswith("MISSABLE BEFORE ISLE OF MISTS".title().replace("Of", "of")) or miss["h"].lower().startswith("missable before isle of mists"), miss)
        check("%s [%s]: Missable: the count is the list, it holds Q106 and Q107 and no quest that is Done or Failed in the save, the footnote is 'From the game's quest graphs'" % (label, sub), miss["n"] == len(miss["names"]) >= 8 and "An Invitation from Keira Metz" in miss["names"] and "Return to Crookback Bog" in miss["names"] and miss["foot"] == "From the game's quest graphs"
              and E("[...document.querySelectorAll('#qsMiss .qsmi')].every(b=>['none','active','inactive'].includes(qsState(b.dataset.g)))") and E("document.getElementById('qsMiss').compareDocumentPosition(document.getElementById('qsNext'))&Node.DOCUMENT_POSITION_FOLLOWING") != 0, miss)
        pg.click("#qsMiss .qsmi >> nth=0"); pg.wait_for_timeout(300); dtx = E("document.getElementById('qsDetail').textContent")
        check("%s [%s]: a Missable item opens the drawer (%s)" % (label, sub, dtx[:60]), E("document.getElementById('screenQ').classList.contains('qs-open')") and "Fails at Isle of Mists" in dtx, dtx[:200]); pg.keyboard.press("Escape")
        for qid in ("Q106 Keira's bussiness", "Q107 Swamps"):
            E("qsSelect(QS.data.quests.find(q=>q.id===%s).g)" % json.dumps(qid)); pg.wait_for_timeout(250); t = E("document.getElementById('qsDetail').textContent")
            check("%s [%s]: the drawer of %s says 'Fails at Isle of Mists' and its story point (%s)" % (label, sub, qid, t[t.find("Story point"):t.find("Story point") + 40]), "Fails at Isle of Mists" in t and "Story point:" in t and "Not missable" not in t, t[:200])
        pg.keyboard.press("Escape")
        E("qsSelect(QS.data.quests.find(q=>q.id==='Card Game Meta: Gather All').g)"); pg.wait_for_timeout(250); t = E("document.getElementById('qsDetail').textContent"); cg = E("qsState(QS.data.quests.find(q=>q.id==='Card Game Meta: Gather All').g)")
        check("%s [%s]: Collect 'Em All stays Failed (the save's state is never changed by a rule) and is not missable as far as computed" % (label, sub), cg == "failed" and "Not missable as far as computed" in t and "In your save: <b>" not in t and "Failed" in t, [cg, t[:160]]); pg.keyboard.press("Escape")
        E("qsSelect(QS.data.quests.find(q=>q.id==='Q105 Witches').g)"); pg.wait_for_timeout(250); aft = E("[...document.querySelectorAll('#qsDetail .qsafter .qslink')].map(b=>b.textContent)")
        check("%s [%s]: the drawer of Ladies of the Wood says 'Opens after' with links to the previous quest first (%s)" % (label, sub, aft), aft[:1] == ["The Nilfgaardian Connection"] and 1 <= len(aft) <= 4, aft)
        E("document.querySelector('#qsDetail .qsafter .qslink').click()"); pg.wait_for_timeout(250); check("%s [%s]: the link opens that quest (%s)" % (label, sub, E("QS.byG.get(QS.sel).n")), E("QS.byG.get(QS.sel).n") == "The Nilfgaardian Connection"); pg.keyboard.press("Escape")
        un = E("(()=>{const k=g=>QS.R.quests[g]&&QS.R.quests[g].s,u=new Set(QS.data.quests.filter(q=>!k(q.g)).map(q=>q.g));return[[...document.querySelectorAll('#qsTL .qsdot')].filter(d=>u.has(d.dataset.g)).length,u.size]})()")
        check("%s [%s]: Timeline: no quest with an unknown story point is drawn (%d of them, all in the collapsed row)" % (label, sub, un[1]), un[0] == 0 and un[1] == 191, un)
        check("%s [%s]: the link is unchanged (view, gates and progress are not in it)" % (label, sub), E("location.hash") == h0 and not re.search(r"[0-9a-f]{32}|time", E("location.hash")), E("location.hash"))
        # passing a gate by the main quests' states
        isle = E("QS.data.quests.find(q=>q.id==='Q402 Isle of Mists').g"); E("qsMark('%s','done')" % isle); pg.wait_for_timeout(250)
        miss2 = E("(()=>{const m=document.getElementById('qsMiss');return{h:m.querySelector('h3').textContent.trim().toLowerCase(),names:[...m.querySelectorAll('.qsmissec>.qsmis .qsmi b')].map(e=>e.textContent)}})()")
        check("%s [%s]: once Q402 Isle of Mists is Done the Isle of Mists gate counts as passed: the panel moves on to the Battle of Kaer Morhen (%s) and Q106 is no longer listed" % (label, sub, miss2["names"]), miss2["h"].startswith("missable before battle of kaer morhen") and "An Invitation from Keira Metz" not in miss2["names"], miss2)
        E("qsMark('%s',null)" % isle); check("%s [%s]: no script errors" % (label, sub), not errs, errs[:1]); pg.close()


def timelinephone(b, base, check, label):
    pg, errs, _ = newpage(b, base, w=390, h=844, mobile=True); E = pg.evaluate; opened(pg); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
    sw = E("document.documentElement.scrollWidth-innerWidth"); inner = E("(()=>{const e=document.getElementById('qsTL');return[e.scrollWidth>e.clientWidth,getComputedStyle(e).overflowX]})()"); small = E("[...document.querySelectorAll('.qsv:not(:disabled),#qsShowDoneT,.qsunk summary')].filter(e=>e.getBoundingClientRect().height<43.5).length")
    pg.click('#qsTL .qsdot >> nth=0'); pg.wait_for_timeout(350); dr = E("(()=>{const d=document.getElementById('qsDetail').getBoundingClientRect();return[Math.round(d.width),innerWidth,Math.round(d.top)]})()")
    check("%s: 390 px: the Timeline scrolls sideways inside its own box (%s), the page does not (%d), the controls are 44 px (%d too small), a dot opens the full-screen drawer (%s)" % (label, inner, sw, small, dr), sw <= 1 and inner == [True, "auto"] and small == 0 and dr[0] == dr[1] and dr[2] == 0, [sw, inner, small, dr])
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()
