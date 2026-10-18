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
          set(R) <= set(qs) and all(set(r) <= {"s", "h", "c", "a", "u", "k"} for r in R.values()) and all(re.fullmatch(r"[0-9a-f]{32}", g) for g in R) and
          all(re.fullmatch(r"[0-9a-f]{32}", a) for r in R.values() for a in r.get("a", [])) and set(R_ for r in R.values() for R_ in [r.get("s")] if R_) <= {p[0] for p in d["points"]} and len(raw) < 60000)
    check("QUEST-RULES.json: %d gates: the base-game gates in story order (%s) and the Blood and Wine and Hearts of Stone ones" % (len(gates), [g["id"] for g in d["gates"] if g["lane"] == "b"]),
          [g["id"] for g in sorted(d["gates"], key=lambda g: g["x"]) if g["lane"] == "b"] == ["prologue", "isle", "battle", "novigrad3", "skellige3", "naglfar", "ciri", "finish"] and {"bawnight", "baw703", "hos"} <= set(gates) and all(set(g) - {"code", "real"} == {"id", "name", "lane", "x", "done", "next"} for g in gates.values())
          and all(re.fullmatch(r"Q\d{3}", g["code"]) for g in gates.values() if "code" in g) and [i for i, g in gates.items() if g.get("real")] == ["bawnight"] and gates["isle"]["code"] == "Q402" and "code" not in gates["finish"])
    check("QUEST-RULES.json: Q106 and Q107 fail at Isle of Mists (a whole-quest Failure), the story points of Q402, Q403 and Q111 are Isle of Mists, Battle of Kaer Morhen and Act III",
          R[by["Q106 Keira's bussiness"]]["c"] == [["isle", "q", "f"]] and R[by["Q107 Swamps"]]["c"] == [["isle", "q", "f"]] and R[by["Q402 Isle of Mists"]]["s"] == "i" and R[by["Q403 Battle of Kaer Morhen"]]["s"] == "b" and R[by["Q111 Imlerith"]]["s"] == "3")
    check("QUEST-RULES.json: left out: the temporary toggles (MQ3026 Novigrad Horse Racing has no cutoff) and the demon-mark flag (Q310 Ciri's Night Out has none); Collect 'Em All has no rule; a story point derived by default is stored as unknown (mq1001 Dog Trail has none)",
          "c" not in R.get(by["MQ3026 Novigrad Horse Racing"], {}) and "c" not in R.get(by["Q310 Ciri's Night Out"], {}) and "s" not in R.get(by["Card Game Meta: Gather All"], {}) and "s" not in R.get(by["mq1001 Dog Trail"], {}) and
          sum("s" not in R.get(g, {}) for g in qs) == 191 and sum("s" in r for r in R.values()) == 210)
    U = {g: r["u"] for g, r in R.items() if "u" in r}; K = {g: r["k"] for g, r in R.items() if "k" in r}
    check("QUEST-RULES.json (v35): every quest with no story point has `u` (ungated 157 + unknown 34 = 191), no placed quest has one, the 3 'likely' ones carry nothing but `unknown`", len(U) == 191 and sum(v == "ungated" for v in U.values()) == 157 and sum(v == "unknown" for v in U.values()) == 34
          and set(U) == {g for g in qs if "s" not in R.get(g, {})} and all(v in ("ungated", "unknown") for v in U.values()) and all(set(R[by[i]]) == {"u"} or set(R[by[i]]) <= {"u", "c", "a", "k"} for i in ("SQ302 Philippa", "mq1057: The Great Spirit", "NML Hunt: Fogling")) and all(U[by[i]] == "unknown" for i in ("SQ302 Philippa", "mq1057: The Great Spirit", "NML Hunt: Fogling")))
    check("QUEST-RULES.json (v35): `k` (can fail by a choice) = [['q']] own conversation, [['q', quest guid]] through another quest, [['o', objective guid]]; guids of QUESTS.json only; 7 quests (4 whole-quest, 3 objective)", len(K) == 7 and
          all(e[0] in "qo" and ((e[0] == "q" and len(e) in (1, 2) and (len(e) == 1 or e[1] in qs and e[1] != g)) or (e[0] == "o" and len(e) == 2 and e[1] in qs[g]["o"])) for g, es in K.items() for e in es) and sum(e[0] == "q" for es in K.values() for e in es) == 4 and sum(e[0] == "o" for es in K.values() for e in es) == 3)
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
    check("%s: Timeline: columns Prologue, Act I, Isle of Mists, Battle of Kaer Morhen, Act III, Epilogue; rows by region (the Hearts of Stone and Blood and Wine lanes are the two other scopes); the region tabs are not shown (%s)" % (label, rows),
          cols == ["Prologue", "Act I", "Isle of Mists", "Battle of Kaer Morhen", "Act III", "Epilogue"] and rows == ["White Orchard", "Vizima", "Velen", "Novigrad", "Skellige", "Kaer Morhen", "Other & epilogue"] and E("getComputedStyle(document.querySelector('.qsregnav')).display") == "none", [cols, rows])
    gk = E("[...document.querySelectorAll('#qsTL ~ .qsgkey .qsgk, .qsgkey .qsgk')].map(e=>e.textContent)")
    check("%s: Timeline: the gates are numbered (8 in the base game; bars only on the 3 column edges); the names are in the key above the chart, not inside it (%s)" % (label, gk[:3]),
          len(gk) == 8 and gk[1].startswith("2Isle of Mists") and gk[2].startswith("3Battle of Kaer Morhen") and E("document.querySelectorAll('#qsTL .qstlhead .qsgate').length") == 3 and E("[...document.querySelectorAll('#qsTL .qstlhead .qsgb')].map(e=>e.textContent).join('')") == "12345678" and True
          and E("document.querySelectorAll('#qsTL .qsgl').length") == 0, gk)
    check("%s: Timeline: no 'You' marker without a save; the view is not in the link and is remembered (%s)" % (label, E("QS.view")), E("document.querySelectorAll('#qsTL .qsme').length") == 0 and E("location.hash") == h0 and E("localStorage.getItem('w3p.quests.view')") == "time", h0)
    st = E("""(()=>{const known=q=>QS.R.quests[q.g]&&QS.R.quests[q.g].s,open=QS.data.quests.filter(q=>known(q)&&'pai b3e'.includes(known(q))&&QS.timeDone===false&&qsState(q.g)!=='done');const dots=[...document.querySelectorAll('#qsTL .qsdot')],more=[...document.querySelectorAll('#qsTL .qsmore')].reduce((a,b)=>a+(b.textContent[0]==='+'?+b.textContent.slice(1):0),0);
      const unk=new Set(QS.data.quests.filter(q=>!known(q)).map(q=>q.g));return{dots:dots.length,more:more,want:open.length,unkDrawn:dots.filter(d=>unk.has(d.dataset.g)).length,unkN:unk.size,summary:[...document.querySelectorAll('.qsug summary')].map(s=>s.textContent).join(' | '),items:document.querySelectorAll('.qsug .qsdot').length+[...document.querySelectorAll('.qsug .qsmore')].reduce((a,e)=>a+(e.textContent[0]==='+'?+e.textContent.slice(1):0),0),
      rings:document.querySelectorAll('#qsTL .qsfb').length,wantRings:document.querySelectorAll('#qsTL .qsfl').length,ringOnFails:document.querySelectorAll('#qsTL .qsfd,#qsTL .qsring').length===0,anyFail:open.filter(q=>qsFailsAt(q)).length}})()""")
    check("%s: Timeline: every quest with a known story point is drawn once (%d dots + %d in '+n' chips of %d), none of the %d quests without one; they are in the collapsed row '%s' (%d listed)" % (label, st["dots"], st["more"], st["want"], st["unkN"], st["summary"], st["items"]),
          st["dots"] + st["more"] >= st["want"] and st["unkDrawn"] == 0 and st["summary"] == "No story gate found (157) | Not computed yet (34)" and st["items"] == st["unkN"] == 191 and E("document.getElementById('qsNoGate').open") and not E("document.getElementById('qsNotComputed').open"), st)
    check("%s: Timeline: a quest with a confirmed cutoff the save has not passed has no orange dot or ring; its tooltip says 'Fails at <gate>' (%d such quests; %d brackets, %d labels)" % (label, st["anyFail"], st["rings"], st["wantRings"]), st["rings"] == st["wantRings"] and st["ringOnFails"] and st["anyFail"] > 15, st)
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
        you = E("(()=>{const m=document.querySelector('#qsTL .qstfoot .qsyou'),i=document.querySelector('#qsTL .qstlhead .qsme'),c=[...document.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect()),x=i.getBoundingClientRect().left;return{t:m.textContent,col:c.findIndex(r=>x>=r.left-6&&x<=r.right+6),on:document.querySelector('.qstc.on').textContent}})()")
        passed = E("[...document.querySelectorAll('#qsTL .qstlhead .qsgate')].map((e,i)=>e.classList.contains('passed')?QS.R.gates.filter(g=>g.lane==='b').sort((a,b)=>a.x-b.x)[i].id:null).filter(Boolean)")
        check("%s [%s]: Timeline: 'You' stands at Act I; no cutoff after Leaving White Orchard is passed (Isle of Mists, the Battle ... are not): passed = %s" % (label, sub, passed), you["t"] == "You are here" and you["col"] == 1 and you["on"] == "Act I" and passed == ["prologue"], [you, passed])
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



BARJS = """(()=>{const out=[];document.querySelectorAll('#qsTL .qsbrow .qsbplot').forEach(p=>{const bars=[...p.querySelectorAll('.qsgate')].map(b=>b.getBoundingClientRect()),ms=[...p.querySelectorAll('.qsdot,.qsmore')].map(m=>m.getBoundingClientRect());
  bars.forEach(b=>ms.forEach(m=>{if(!(b.right<=m.left+.5||b.left>=m.right-.5))out.push([Math.round(b.left),Math.round(m.left),Math.round(m.right)])}))});
  return{crossings:out,bars:document.querySelectorAll('#qsTL .qsbrow .qsbplot .qsgate').length,markers:document.querySelectorAll('#qsTL .qsbrow .qsdot,#qsTL .qsbrow .qsmore').length}})()"""


def nobar(pg, check, label):
    r = pg.evaluate(BARJS)
    check("%s: v34.2 (c) no gate bar crosses a marker: %d bars, %d markers, %d crossings %s" % (label, r["bars"], r["markers"], len(r["crossings"]), r["crossings"][:3]), r["bars"] > 0 and r["markers"] > 0 and not r["crossings"], r)


def timeline2(b, base, check, label):
    """v34.2 without a save: pure functions (column width, leftover share, cell layout, order), the width filled, bars on edges only, spacing, key on one line, scopes and their memory."""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
    u = E("""({w:[0,1,5,6,11,25,40].map(n=>qsColW(n)),m:qsColW(1,148),sh:[qsShare([100,200],600),qsShare([100,200],250)],
      pl:[[0,6,100,false],[0,7,100,false],[0,7,100,true],[3,10,274,false],[3,20,274,false],[25,0,274,false],[2,3,100,false]].map(a=>{const p=qsCellPlace(...a);return[p.per,p.over,p.fS,p.rS,p.chip&&p.chip.blk+p.chip.idx,p.lines,p.more]})})""")
    check("%s: v34.2 column width: 100 px at least, else the longer of two lines of 20 px markers with a 6 px gap and 10 px padding, 10 a line at most: %s, with a header minimum %s" % (label, u["w"], u["m"]), u["w"] == [100, 100, 100, 100, 170, 274, 274] and u["m"] == 148, u)
    check("%s: v34.2 the leftover is shared in proportion to the content (100+200 in 600 -> 200+400); no leftover, no change (%s)" % (label, u["sh"]), u["sh"] == [[200, 400], [100, 200]], u["sh"])
    check("%s: v34.2 cell layout (per line, over, shown F, shown R, chip, lines, more): 3 a line in 100 px; 6 fit; 7 give 5 + a '+2' chip; expanded the chip follows on a third line; 3 failing + 10 fit in 274 px; 3 + 20 give 3 + 9 and '+11'; 25 failing give 19 and '+6'; 2 failing + 3 others in 100 px fit in two lines (%s)" % (label, u["pl"]),
          u["pl"] == [[3, False, 0, 6, None, 2, 0], [3, True, 0, 5, "r5", 2, 2], [3, True, 0, 7, "r7", 3, 0], [10, False, 3, 10, None, 2, 0], [10, True, 3, 9, "r9", 2, 11], [10, True, 19, 0, "f19", 2, 6], [3, False, 2, 3, None, 2, 0]], u["pl"])
    ordr = E("""(()=>{const g=QS.R.gmap.get('isle'),l=QS.data.quests.filter(q=>QS.R.quests[q.g]&&QS.R.quests[q.g].s==='a'&&q.r==='no'),o=qsCellOrder(l,g),f=q=>qsFailsAtGate(q,g)?0:1,ty=q=>QS_KINDS.findIndex(k=>k[0]===q.t);
      let ok=true;for(let i=1;i<o.length;i++){if(f(o[i])<f(o[i-1])||(f(o[i])===f(o[i-1])&&ty(o[i])<ty(o[i-1])))ok=false}return{n:o.length,same:o.length===l.length,ok,fails:o.filter(q=>f(q)===0).length,firstMain:o.findIndex(q=>q.t==='main'),lastFail:o.map(f).lastIndexOf(0),firstOther:o.findIndex(q=>f(q)===1)}})()""")
    check("%s: v34.2 cell order: the quests that fail at the next gate first, then by type in legend order (%s)" % (label, ordr), ordr["ok"] and ordr["same"] and ordr["n"] == 25 and ordr["fails"] > 0 and ordr["firstOther"] == ordr["lastFail"] + 1, ordr)
    # the width is filled, and shared in proportion to the content
    wd = E("""(()=>{const t=document.getElementById('qsTL'),p=t.querySelector('.qsbplot.head'),c=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().width+12),secs=['p','a','i','b','3','e'],
      cnt=secs.map(s=>Math.max(0,...QS_TROWS.map(r=>QS.data.quests.filter(q=>q.r===r&&QS.R.quests[q.g]&&QS.R.quests[q.g].s===s&&qsState(q.g)!=='done').length))),raw=cnt.map(n=>qsColW(n));
      return{plot:Math.round(p.getBoundingClientRect().width),box:t.clientWidth,scroll:t.scrollWidth>t.clientWidth+1,c:c.map(Math.round),cnt,ratio:c.map((w,i)=>w/raw[i]),tabs:[...document.querySelectorAll('#qsScope .qssc')].map(e=>[e.textContent,e.getAttribute('aria-pressed')]),vis:!document.getElementById('qsScope').hidden}})()""")
    rr = wd["ratio"]
    check("%s: v34.2 the chart fills the box (plot %d px, box %d, no sideways scroll) and the columns share the leftover in proportion to their content (width / content = %s); scope tabs: %s" % (label, wd["plot"], wd["box"], [round(x, 2) for x in rr], wd["tabs"]),
          abs(wd["plot"] - (wd["box"] - 114)) <= 3 and not wd["scroll"] and max(rr) - min(rr) < .02 and rr[0] > 1.2 and wd["vis"] and wd["tabs"] == [["Base game", "true"], ["Hearts of Stone", "false"], ["Blood and Wine", "false"]], wd)
    bar = E("""(()=>{const t=document.getElementById('qsTL'),cl=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().left-6),cw=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().width+12),bars=[...t.querySelectorAll('.qstlhead .qsgate')].map(e=>[e.dataset.gates,e.getBoundingClientRect().left]),
      bd=[...t.querySelectorAll('.qstlhead .qsgb')].map(e=>{const r=e.getBoundingClientRect();return[e.textContent,r.left+r.width/2]}),colOf=x=>cl.findIndex((l,i)=>x>=l&&x<=l+cw[i]+.5),rowbars=[...t.querySelectorAll('.qsbrow')].map(r=>r.querySelectorAll('.qsgate').length);
      return{bars:bars.map(b=>b[0]),onEdge:bars.every(b=>cl.some(l=>Math.abs(l-b[1])<1.5)),cols:bd.map(x=>colOf(x[1])),lefts:bd.map(x=>Math.round(x[1])),rowbars:[...new Set(rowbars)],none:!bars.some(b=>cl.every((l,i)=>Math.abs(l-b[1])>1.5&&b[1]>l&&b[1]<l+cw[i]))}})()""")
    check("%s: v34.2 bars only on column edges: gates 1, 2, 3 (%s); gates 4, 5, 6 in Act III and 7, 8 in the Epilogue are badges only, side by side %s, no line through the cells (%d bars in each row)" % (label, bar["bars"], bar["lefts"][3:], bar["rowbars"][0]),
          bar["bars"] == ["1", "2", "3"] and bar["onEdge"] and bar["none"] and bar["cols"][3:] == [4, 4, 4, 5, 5] and bar["lefts"][4] - bar["lefts"][3] == 24 and bar["lefts"][5] - bar["lefts"][4] == 24 and bar["lefts"][7] - bar["lefts"][6] == 24 and bar["rowbars"] == [3], bar)
    nobar(pg, check, label)
    gk = E("""(()=>{const li=[...document.querySelectorAll('.qsgkey .qsgk')];return{n:li.length,tops:[...new Set(li.map(e=>Math.round(e.getBoundingClientRect().top)))],txt:li.map(e=>e.textContent),title:li.map(e=>e.title),badge:li.map(e=>e.querySelector('.qsgb').title),w:innerWidth}})()""")
    check("%s: v34.2 gate key on one line at %d px: badge and short name ('%s'), the quest code is in the tooltip ('%s')" % (label, gk["w"], gk["txt"][1], gk["badge"][1]), gk["n"] == 8 and len(gk["tops"]) == 1 and gk["txt"][1] == "2Isle of Mists" and not any("(Q" in t for t in gk["txt"]) and gk["badge"][1] == "Isle of Mists (Q402)" and gk["title"][1] == "Isle of Mists (Q402)" and gk["txt"][7] == "8Game finished", gk)
    lg = E("document.querySelector('#qsView .qslegend').textContent")
    check("%s: v34.2 legend: 'Fails at the next gate you haven't passed' with a sample bracket, the '+N More in this cell' chip, no orange dot" % label, "Fails at the next gate you haven't passed" in lg and "+NMore in this cell" in lg and "Orange dot" not in lg and E("document.querySelectorAll('.qslegend .qsl-fb .qsfb').length") == 1 and E("document.querySelectorAll('#qsTL .qsfd, .qsring').length") == 0, lg)
    sp = E("""(()=>{const t=document.getElementById('qsTL'),cl=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().left-6),cw=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().width+12),res={dx:[],dy:[],size:new Set(),padl:[],lines:0,per:0,rowh:[]};
      t.querySelectorAll('.qsbrow').forEach(row=>{res.rowh.push(Math.round(row.getBoundingClientRect().height));const cells=new Map();row.querySelectorAll('.qsdot').forEach(d=>{const r=d.getBoundingClientRect();res.size.add(r.width+'x'+r.height);const i=cl.findIndex((l,k)=>r.left>=l-.5&&r.left<l+cw[k]);if(!cells.has(i))cells.set(i,[]);cells.get(i).push(r)});
       cells.forEach((rs,i)=>{const tops=[...new Set(rs.map(r=>Math.round(r.top)))].sort((a,b)=>a-b);res.lines=Math.max(res.lines,tops.length);tops.forEach(tp=>{const line=rs.filter(r=>Math.round(r.top)===tp).sort((a,b)=>a.left-b.left);res.per=Math.max(res.per,line.length);line.slice(1).forEach((r,k)=>res.dx.push(Math.round(r.left-line[k].left)));});res.padl.push(Math.round(Math.min(...rs.map(r=>r.left))-cl[i]))})});
      return{dx:[...new Set(res.dx)],size:[...res.size],padl:[...new Set(res.padl)],lines:res.lines,per:res.per,rowh:Math.min(...res.rowh)}})()""")
    check("%s: v34.2 spacing: markers 20 px (%s) every 26 px (a 6 px gap: %s), 10 px from the cell's edge (%s), at most 10 a line (%d) and 2 lines a cell (%d), rows 56 px at least (%d)" % (label, sp["size"], sp["dx"], sp["padl"], sp["per"], sp["lines"], sp["rowh"]),
          sp["size"] == ["20x20"] and sp["dx"] == [26] and sp["padl"] == [10] and sp["per"] <= 10 and sp["lines"] <= 2 and sp["rowh"] >= 56, sp)
    # the +N chip: Act I / Novigrad: 25 quests, per 10, two lines: 19 + '+6'
    row = "#qsTL .qsbrow >> nth=3"; k = 't:base:no:a'; ch = E("(()=>{const b=document.querySelector('.qsmore[data-cell=\"%s\"]');return b&&b.textContent})()" % k)
    h0 = pg.locator(row).bounding_box()["height"]; n0 = E("document.querySelectorAll('#qsTL .qsdot').length")
    pg.click('.qsmore[data-cell="%s"]' % k); pg.wait_for_timeout(200); h1 = pg.locator(row).bounding_box()["height"]; n1 = E("document.querySelectorAll('#qsTL .qsdot').length"); t1 = E("document.querySelector('.qsmore[data-cell=\"%s\"]').textContent" % k); foc = E("document.activeElement.dataset.cell")
    nobar(pg, check, label + " (cell expanded)")
    pg.click('.qsmore[data-cell="%s"]' % k); pg.wait_for_timeout(200); h2 = pg.locator(row).bounding_box()["height"]; t2 = E("document.querySelector('.qsmore[data-cell=\"%s\"]').textContent" % k)
    pg.click('.qsmore[data-cell="%s"]' % k); pg.reload(); until(pg, READY); opened(pg); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(200)
    check("%s: v34.2 a '+N' chip (%s) expands its cell in place (row %d -> %d px, %d -> %d markers, chip '%s', focus kept), a second click collapses it (%d px, '%s'); a reload forgets it" % (label, ch, h0, h1, n0, n1, t1, h2, t2),
          ch == "+6" and h1 > h0 and n1 == n0 + 6 and t1 == "−" and foc == k and h2 == h0 and t2 == "+6" and E("document.querySelector('#qsTL .qsmore').textContent") == "+6" and not E("Object.keys(localStorage).some(k=>/cell|more|expand/i.test(k))"), [ch, h0, h1, n0, n1, t1, foc, h2, t2])
    # scopes
    hs = {}
    for sc, tab, pack, ng, rowname in (("hos", "Hearts of Stone", "Hearts of Stone", 1, "Hearts of Stone"), ("bob", "Blood and Wine", "Blood and Wine", 6, "Blood and Wine")):
        pg.click('#qsScope [data-scope="%s"]' % sc); pg.wait_for_timeout(250)
        hs[sc] = E("""(()=>{const t=document.getElementById('qsTL'),cl=[...t.querySelectorAll('.qsbaxis span')].map(e=>e.getBoundingClientRect()),cw=cl.map(r=>r.left+r.width/2),lefts=[...t.querySelectorAll('.qscol')].map(e=>e.getBoundingClientRect().left),bars=[...t.querySelectorAll('.qstlhead .qsgate')].map(e=>[e.dataset.gates,e.getBoundingClientRect().left]),
          bd=[...t.querySelectorAll('.qstlhead .qsgb')].map(e=>{const r=e.getBoundingClientRect();return[e.textContent,Math.round(r.left+r.width/2)]}),w=[...t.querySelectorAll('.qsbaxis span')].map((e,i,a)=>i?parseFloat(e.style.left)-parseFloat(a[i-1].style.left):null).filter(Boolean),plot=t.querySelector('.qsbplot.head').getBoundingClientRect().width;
          return{key:[...document.querySelectorAll('.qsgkey .qsgk')].map(e=>e.textContent),note:(document.querySelector('.qsscnote')||{}).textContent,rows:[...t.querySelectorAll('.qsblabel')].map(e=>e.textContent),badges:bd.map(x=>x[0]).join(''),bd,bars:bars.map(b=>b[0]),barsOnEdge:bars.every(b=>lefts.some(l=>Math.abs(l-b[1])<1.5)),
          real:[...document.querySelectorAll('.qsgk.real')].map(e=>e.textContent),realBar:t.querySelectorAll('.qsgb.real').length,minstep:Math.min(...w),plot:Math.round(plot),box:t.clientWidth,unk:[...document.querySelectorAll('.qsug summary')].map(s=>s.textContent).join(' | '),pressed:[...document.querySelectorAll('#qsScope .qssc')].map(e=>e.getAttribute('aria-pressed')).join(),mem:localStorage.getItem('w3p.quests.timescope'),cols:t.querySelectorAll('.qstc').length,hash:location.hash}})()""")
        x = hs[sc]
        check("%s: v34.2 scope %s: one lane by level, the note, %d numbered gate%s (bars %s on the edge before their level's column, badges side by side), no unplaced quest in this pack so no 'No story gate found' / 'Not computed yet' section, remembered" % (label, tab, ng, "s" if ng > 1 else "", x["bars"]),
              x["rows"] == [rowname] and x["note"] == "Laid out by quest level: every %s quest shares one story point in the game's quest graphs." % pack and len(x["key"]) == ng and x["badges"] == "".join(str(i + 1) for i in range(ng)) and x["barsOnEdge"] and x["minstep"] >= 100 and x["unk"] == "" and x["mem"] == sc and x["cols"] == 0
              and (x["bars"] == ["1", "2", "3,4", "5,6"] and x["bd"][3][1] - x["bd"][2][1] == 24 and x["bd"][5][1] - x["bd"][4][1] == 24 if sc == "bob" else x["bars"] == ["1"])
              and (x["real"] == ["4The Night of Long Fangs real cutoff"] if sc == "bob" else not x["real"]) and (x["realBar"] == 1 if sc == "bob" else x["realBar"] == 0) and x["pressed"] == ",".join("true" if k == sc else "false" for k in ("base", "hos", "bob")), x)
        check("%s: v34.2 scope %s: the chart fills the box when its columns are narrower than it (plot %d px, box %d)" % (label, tab, x["plot"], x["box"]), x["plot"] >= x["box"] - 117, x)
        nobar(pg, check, label + " " + tab)
    check("%s: v34.2 Blood and Wine key: six gates, the Night of Long Fangs is the real cutoff with a gold outlined badge (%s)" % (label, hs["bob"]["key"]), len(hs["bob"]["key"]) == 6 and hs["bob"]["key"][3] == "4The Night of Long Fangs real cutoff" and E("getComputedStyle(document.querySelector('.qsgkey .qsgb.real')).borderTopColor") == "rgb(240, 212, 138)" and E("document.querySelector('.qsgkey .qsgk.real').title") == "The Night of Long Fangs (Q704)", hs["bob"]["key"])
    check("%s: v34.2 the scope is not in the link" % label, hs["bob"]["hash"] == E("location.hash") and "timescope" not in E("location.hash"), hs["bob"]["hash"])
    pg.reload(); until(pg, READY); opened(pg); sc2 = E("[QS.tscope,QS.view]"); pg.click("#qsVTime") if sc2[1] != "time" else None; until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(200)
    check("%s: v34.2 the scope is remembered after a reload (%s)" % (label, sc2), sc2[0] == "bob" and E("[...document.querySelectorAll('#qsTL .qsblabel')].map(e=>e.textContent)") == ["Blood and Wine"], sc2)
    pg.evaluate("localStorage.setItem('w3p.quests.timescope','nonsense')"); pg.reload(); until(pg, READY); opened(pg); pg.click("#qsVTime") if E("QS.view") != "time" else None; until(pg, "!!document.getElementById('qsTL')")
    check("%s: v34.2 a stored scope that is not one of the three falls back to the base game" % label, E("QS.tscope") == "base" and E("document.querySelectorAll('#qsTL .qstc').length") == 6, E("QS.tscope"))
    pg.click('#qsVList'); pg.wait_for_timeout(150); check("%s: v34.2 the scope tabs show only in the Timeline" % label, E("document.getElementById('qsScope').hidden"), None)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def timeline2save(b, base, check, label):
    """v34.2 with the level-9 save: 6a gate 1 grey, 6b You are here, fail groups, 6c no bar crosses a marker."""
    for sub in ("stats-l9b", "stats-l9"):
        d = FIXD / sub; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
        if not sav: print("  SKIP  %s: v34.2 Timeline against the %s save (fixture not present)" % (label, sub)); continue
        pg, errs, _ = newpage(b, base); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
        opened(pg); until(pg, "!!QS.R&&!!QS.desc"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
        gk = E("qsGateKey('b').map(k=>[k.n,k.g.id,k.passed,k.name,k.code])"); dom = E("[...document.querySelectorAll('.qsgkey .qsgk')].map(e=>[e.querySelector('.qsgb').classList.contains('passed'),e.textContent])")
        check("%s [%s]: v34.2 gate numbering: 1 Leaving White Orchard is passed, 2..8 are not (%s); the key marks only gate 1 '· passed'" % (label, sub, [(k[0], k[2]) for k in gk]), [(k[0], k[2]) for k in gk] == [(i + 1, i == 0) for i in range(8)] and gk[1][3:] == ["Isle of Mists", "Q402"]
              and dom[0][0] and dom[0][1] == "1Leaving White Orchard · passed" and not any(x[0] or "passed" in x[1] for x in dom[1:]), [gk, dom])
        g6 = E("""(()=>{const c=e=>getComputedStyle(e),b1=document.querySelector('#qsTL .qstlhead .qsgate[data-gates="1"]'),b2=document.querySelector('#qsTL .qstlhead .qsgate[data-gates="2"]'),bg=[...document.querySelectorAll('#qsTL .qstlhead .qsgb')],kb=[...document.querySelectorAll('.qsgkey .qsgb')];
          return{bar1:[c(b1).borderLeftColor,c(b1).borderLeftStyle],bar2:[c(b2).borderLeftColor,c(b2).borderLeftStyle],badge1:c(bg[0]).backgroundColor,badge2:c(bg[1]).backgroundColor,key1:c(kb[0]).backgroundColor,rows:[...document.querySelectorAll('#qsTL .qsbrow .qsgate[data-gates="1"]')].map(e=>c(e).borderLeftColor)}})()""")
        check("%s [%s]: v34.2 (a) gate 1 is passed, so its bar (%s) and badge (%s) are grey, in the key too (%s); gate 2 stays orange (%s, %s)" % (label, sub, g6["bar1"], g6["badge1"], g6["key1"], g6["bar2"][0], g6["badge2"]),
              g6["bar1"] == ["rgb(143, 133, 117)", "dashed"] and g6["badge1"] == "rgb(107, 99, 85)" and g6["key1"] == "rgb(107, 99, 85)" and g6["bar2"][0] == "rgb(240, 138, 36)" and g6["badge2"] == "rgb(240, 138, 36)" and set(g6["rows"]) == {"rgb(143, 133, 117)"}, g6)
        ym = E("""(()=>{const l=document.querySelector('#qsTL .qstfoot .qsyou'),i=document.querySelector('#qsTL .qstlhead .qsme'),gz=Math.max(...[...document.querySelectorAll('#qsTL .qsgate')].map(g=>+getComputedStyle(g).zIndex)),c=[...document.querySelectorAll('#qsTL .qstlhead .qstc')].map(e=>e.getBoundingClientRect()),on=document.querySelector('#qsTL .qstlhead .qstc.on'),tint=document.querySelector('#qsTL .qstlhead .qscolbg'),
          x=i.getBoundingClientRect().left,t=l.getBoundingClientRect(),box=document.getElementById('qsTL').getBoundingClientRect(),ci=getComputedStyle(i),cl=getComputedStyle(l),bx=[...document.querySelectorAll('#qsTL .qstlhead .qsgate')].map(g=>g.getBoundingClientRect().left);
          return{n:document.querySelectorAll('#qsTL .qsme').length,col:c.findIndex(r=>x>=r.left-6&&x<=r.right+6),on:on.textContent,line:ci.borderLeftColor,w:ci.borderLeftWidth,z:+ci.zIndex,gz,label:l.textContent,tr:cl.textTransform,lbg:cl.backgroundColor,clear:bx.every(b=>Math.abs(b-x)>4),
          inBox:t.left>=box.left&&t.right<=box.right&&t.bottom<=box.bottom+1,vis:cl.visibility,tintOn:!!tint&&Math.abs(tint.getBoundingClientRect().left-c[1].left+6)<2,bottom:t.top>=[...document.querySelectorAll('#qsTL .qsbrow')].pop().getBoundingClientRect().bottom-1}})()""")
        check("%s [%s]: v34.2 (b) 'You are here': a pale-gold #f0d48a 2 px line (%s) above every bar (z %d > %d) and clear of them, in the Act I column (%s), in the head and the rows (%d lines), the label '%s' at the bottom inside the chart, the Act I column tinted" % (label, sub, ym["line"], ym["z"], ym["gz"], ym["on"], ym["n"] - 2, ym["label"]),
              ym["line"] == "rgb(240, 212, 138)" and ym["w"] == "2px" and ym["z"] > ym["gz"] and ym["clear"] and ym["col"] == 1 and ym["on"] == "Act I" and ym["n"] == 9 and ym["label"] == "You are here" and ym["tr"] == "uppercase" and ym["lbg"] == "rgb(240, 212, 138)" and ym["inBox"] and ym["vis"] == "visible" and ym["tintOn"] and ym["bottom"], ym)
        fg = E("""(()=>{const g=QS.R.gmap.get('isle'),t=document.getElementById('qsTL'),br=[...t.querySelectorAll('.qsfb')].map(e=>e.getBoundingClientRect()),dots=[...t.querySelectorAll('.qsdot')].map(d=>({r:d.getBoundingClientRect(),f:qsFailsAtGate(QS.byG.get(d.dataset.g),g),cls:d.className,col:getComputedStyle(d).color})),
          inside=(r,b)=>{const cx=r.left+r.width/2,cy=r.top+r.height/2;return cx>=b.left&&cx<=b.right&&cy>=b.top&&cy<=b.bottom+4},lab=[...t.querySelectorAll('.qsfl')].map(e=>e.textContent);
          return{brackets:br.length,labels:[...new Set(lab)],failing:dots.filter(d=>d.f).length,failOut:dots.filter(d=>d.f&&!br.some(b=>inside(d.r,b))).length,otherIn:dots.filter(d=>!d.f&&br.some(b=>inside(d.r,b))).length,orange:dots.filter(d=>d.col==='rgb(240, 138, 36)').length,types:dots.every(d=>/ t-(main|side|contract|treasure|gwent|race|fist) /.test(d.cls+' ')),fd:t.querySelectorAll('.qsfd,.qsring').length,
          badge:[...t.querySelectorAll('.qsfl .qsgb')].every(b=>b.textContent==='2')}})()""")
        check("%s [%s]: v34.2 fail groups: %d quests that fail at gate 2 (Isle of Mists) each sit in one of %d orange brackets labelled %s, nothing else is in a bracket, the markers keep their type shape and colour, no orange dot" % (label, sub, fg["failing"], fg["brackets"], fg["labels"]),
              fg["brackets"] > 0 and fg["labels"] == ["fails at 2"] and fg["failing"] > 5 and fg["failOut"] == 0 and fg["otherIn"] == 0 and fg["orange"] == 0 and fg["types"] and fg["fd"] == 0 and fg["badge"], fg)
        fo = E("""(()=>{const g=QS.R.gmap.get('isle'),t=document.getElementById('qsTL'),res=[];t.querySelectorAll('.qsbrow').forEach(row=>{const cl=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().left-6),cw=[...t.querySelectorAll('.qstc')].map(e=>e.getBoundingClientRect().width+12),m=new Map();
          row.querySelectorAll('.qsdot').forEach(d=>{const r=d.getBoundingClientRect(),i=cl.findIndex((l,k)=>r.left>=l-.5&&r.left<l+cw[k]);if(!m.has(i))m.set(i,[]);m.get(i).push([r.top,qsFailsAtGate(QS.byG.get(d.dataset.g),g)])});
          m.forEach(a=>{const f=a.filter(x=>x[1]).map(x=>x[0]),o=a.filter(x=>!x[1]).map(x=>x[0]);if(f.length&&o.length)res.push(Math.max(...f)<Math.min(...o))})});return{cells:res.length,ok:res.every(Boolean)}})()""")
        check("%s [%s]: v34.2 in a cell the group that fails comes first, above the others (%d cells with both)" % (label, sub, fo["cells"]), fo["cells"] > 0 and fo["ok"], fo)
        nobar(pg, check, label + " [%s]" % sub)
        for sc in ("hos", "bob"):
            pg.click('#qsScope [data-scope="%s"]' % sc); pg.wait_for_timeout(200)
            kp = E("[...document.querySelectorAll('.qsgkey .qsgk')].map(e=>e.classList.contains('passed'))"); lane = {"hos": "h", "bob": "w"}[sc]
            st = E("QS.data.quests.some(q=>QS.R.quests[q.g]&&QS.R.quests[q.g].s==='%s'&&qsState(q.g)!=='none'&&q.lv!=null)" % lane); n = E("document.querySelectorAll('#qsTL .qsyou').length")
            check("%s [%s]: v34.2 scope %s: no gate passed; 'You are here' only if the save has started a quest of that pack (%s -> %d label)" % (label, sub, sc, st, n), not any(kp) and n == (1 if st else 0), [kp, st, n])
            nobar(pg, check, label + " [%s] %s" % (sub, sc))
        check("%s [%s]: no script errors" % (label, sub), not errs, errs[:1]); pg.close()


def timeline2phone(b, base, check, label):
    pg, errs, _ = newpage(b, base, w=390, h=844, mobile=True); E = pg.evaluate; opened(pg); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
    for sc in ("base", "hos", "bob"):
        pg.click('#qsScope [data-scope="%s"]' % sc); pg.wait_for_timeout(250)
        m = E("""(()=>{const t=document.getElementById('qsTL'),s=document.getElementById('qsScope').getBoundingClientRect(),k=document.querySelector('.qsgkey').getBoundingClientRect(),sc=[...document.querySelectorAll('#qsScope .qssc')].map(e=>e.getBoundingClientRect()),li=[...document.querySelectorAll('.qsgkey .qsgk')].map(e=>Math.round(e.getBoundingClientRect().top));
          return{page:document.documentElement.scrollWidth-innerWidth,box:[t.scrollWidth>t.clientWidth,getComputedStyle(t).overflowX],keyIn:k.right<=innerWidth,wraps:new Set(li).size>1||li.length<2,tabsIn:s.right<=innerWidth&&s.left>=0,h:Math.round(Math.min(...sc.map(r=>r.height)))}})()""")
        check("%s: v34.2 390 px, scope %s: the chart scrolls inside its own box, the page does not (%d), the key and the tabs wrap inside the screen, the tabs are 44 px (%s)" % (label, sc, m["page"], m), m["page"] <= 1 and m["box"] == [True, "auto"] and m["keyIn"] and m["wraps"] and m["tabsIn"] and m["h"] >= 44, m)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


# v34.3: "Missable, story point unknown" under the Timeline
STRIPJS = """(()=>{const lane=({base:null,hos:'h',bob:'w'})[QS.tscope],keys=qsGateKey(lane||'b'),cols=QS_TCOLS.map(c=>c[0]),inScope=s=>lane?s===lane:cols.includes(s),R=QS.R,Q=QS.data.quests,out={gates:[],bad:[]};
  const strip=g=>[...document.querySelectorAll('#qsMU .qsmug[data-gate="'+g+'"] .qsdot')].map(d=>d.dataset.g),unkRows=new Set([...document.querySelectorAll('.qsug .qsdot')].map(b=>b.dataset.g)),grid=[...document.querySelectorAll('#qsTL .qsdot')].map(d=>d.dataset.g);
  // from the raw rules: the whole-quest cutoffs of a quest in this lane, in story order; an open quest sits at its earliest gate not passed, any other at its earliest
  const raw=q=>{const r=R.quests[q.g];return r&&r.c?r.c.filter(c=>c[1]==='q'&&R.gmap.get(c[0])&&R.gmap.get(c[0]).lane===(lane||'b')).map(c=>R.gmap.get(c[0])).sort((a,b)=>a.x-b.x):[]},
   at=q=>{const c=raw(q);if(!c.length)return null;const open=['none','active','inactive'].includes(qsState(q.g));return(open&&c.find(g=>!qsPassed(g))||c[0]).id};
  const chips=[...document.querySelectorAll('#qsTL .qsmore')].reduce((a,e)=>a+(e.textContent[0]==='+'?+e.textContent.slice(1):0),0),shown=q=>QS.timeDone||qsState(q.g)!=='done';
  keys.forEach(k=>{const mine=Q.filter(q=>at(q)===k.g.id),placed=mine.filter(q=>R.quests[q.g]&&R.quests[q.g].s&&inScope(R.quests[q.g].s)),unplaced=mine.filter(q=>!(R.quests[q.g]&&R.quests[q.g].s)),open=q=>['none','active','inactive'].includes(qsState(q.g));
   const inStrip=strip(k.g.id),want=unplaced.filter(shown).map(q=>q.g),failDots=[...document.querySelectorAll('#qsTL .qsdot.fails')].map(d=>d.dataset.g).filter(g=>{const q=QS.byG.get(g);return qsFailsAt(q)===k.g&&inScope(R.quests[g].s)});
   const wantFails=k.passed?[]:placed.filter(open).map(q=>q.g);   // a passed gate has no bracket
   if(JSON.stringify([...inStrip].sort())!==JSON.stringify([...want].sort()))out.bad.push(['strip',k.g.id,inStrip.length,want.length]);
   if(failDots.some(g=>!wantFails.includes(g))||wantFails.length-failDots.length>chips)out.bad.push(['bracket',k.g.id,failDots.length,wantFails.length]);   // a '+N' chip may hold the ones that do not fit
   unplaced.forEach(q=>{if(unkRows.has(q.g))out.bad.push(['repeated in the collapsed row',q.n]);if(grid.includes(q.g))out.bad.push(['drawn in the grid',q.n])});
   out.gates.push([k.n,k.g.id,k.passed,failDots.length,inStrip.length,open&&0])});
  const all=[...document.querySelectorAll('#qsMU .qsdot')].map(d=>d.dataset.g);out.dup=all.length-new Set(all).size;out.total=all.length;
  // the panel (lanes b and w, the next gate not passed): the open quests it lists = the ones in that gate's bracket + the ones in that gate's strip group
  const ml=qsMissLists().find(m=>m.gate.lane===(lane||'b'));out.panel=ml?{gate:ml.gate.id,n:ml.whole.length,ok:JSON.stringify(ml.whole.map(q=>q.g).sort())===JSON.stringify([...Q.filter(q=>qsFailsAtGate(q,ml.gate)&&((R.quests[q.g]&&R.quests[q.g].s&&inScope(R.quests[q.g].s))||strip(ml.gate.id).includes(q.g))).map(q=>q.g)].sort())}:null;
  out.vis=!!document.getElementById('qsMU');out.sum=[...document.querySelectorAll('.qsug summary')].map(s=>s.textContent).join(' | ');return out})()"""


def missunknown(b, base, check, label):
    """v34.3: the strip 'Missable, story point unknown': the quests with a whole-quest cutoff and no story point, by the gate they fail at."""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(200)
    for sc in ("base", "hos", "bob"):
        pg.click('#qsScope [data-scope="%s"]' % sc); pg.wait_for_timeout(200); r = E(STRIPJS)
        check("%s: v34.3 no save (%s): no strip (the Missable panel is not there either), the two sections hold all the unplaced quests of the scope (no strip to take any out), the brackets are the grid's own (%s)" % (label, sc, r["sum"]),
              not r["vis"] and r["sum"] == ("No story gate found (157) | Not computed yet (34)" if sc == "base" else "") and E("document.getElementById('qsMiss').hidden") and not [x for x in r["bad"] if x[0] != "strip" and x[0] != "repeated in the collapsed row"], r)
    ks = E("Object.keys(localStorage).sort()"); check("%s: v34.3 no new storage keys (%s) and the link is unchanged" % (label, ks), all(k.startswith("w3p.quests.") for k in ks) and not [k for k in ks if re.search(r"strip|miss|unknown", k)] and not re.search(r"[0-9a-f]{32}|miss", E("location.hash")), ks)
    check("%s: v35 APP_VERSION is v35" % label, E("APP_VERSION") == "v35")
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()
    for sub in ("stats-l9b", "stats-l9"):
        d = FIXD / sub; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
        if not sav: print("  SKIP  %s: v34.3 strip against the %s save (fixture not present)" % (label, sub)); continue
        pg, errs, _ = newpage(b, base); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
        opened(pg); until(pg, "!!QS.R&&!!QS.desc"); h0 = E("location.hash"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
        r = E(STRIPJS); g = E("[...document.querySelectorAll('#qsMU .qsmug')].map(x=>[x.dataset.gate,x.classList.contains('passed'),[...x.querySelectorAll('.qsdot')].map(d=>QS.byG.get(d.dataset.g).n)])")
        ttl = E("document.querySelector('#qsMU h3').textContent"); help_ = E("document.querySelector('#qsMU .qsbnote').textContent")
        check("%s [%s]: v34.3 Base game: the strip '%s' sits under the grid with the help line, with Redania's Most Wanted under the Isle of Mists gate (%s)" % (label, sub, ttl, g[0]),
              ttl == "Missable, story point unknown" and help_ == "These can be missed, but the game files don't say where in the story they open." and g[0][0] == "isle" and "Redania's Most Wanted" in g[0][2]
              and E("document.getElementById('qsTL').compareDocumentPosition(document.getElementById('qsMU'))&Node.DOCUMENT_POSITION_FOLLOWING") != 0 and E("document.getElementById('qsMU').compareDocumentPosition(document.querySelector('.qslegend'))&Node.DOCUMENT_POSITION_FOLLOWING") != 0, [ttl, g])
        rm = E("(()=>{const q=QS.data.quests.find(q=>q.n==='Redania\\'s Most Wanted');return{inUnk:[...document.querySelectorAll('.qsug .qsdot')].some(e=>e.dataset.g===q.g),inGrid:!!document.querySelector('#qsTL .qsdot[data-g=\"'+q.g+'\"]'),inStrip:!!document.querySelector('#qsMU .qsmug[data-gate=\"isle\"] .qsdot[data-g=\"'+q.g+'\"]'),cut:QS.R.quests[q.g].c,s:QS.R.quests[q.g].s}})()")
        check("%s [%s]: v34.3 Redania's Most Wanted (Novigrad, no story point, failed by the Isle of Mists cut) is in the strip under that gate, not in the grid and not under 'No story gate found / Not computed yet' (%s)" % (label, sub, rm), rm["inStrip"] and not rm["inUnk"] and not rm["inGrid"] and rm["s"] is None, rm)
        check("%s [%s]: v35 the two sections lost exactly the strip's quests (and the done ones, hidden without Show done) (%s; %d in the strip)" % (label, sub, r["sum"], r["total"]), sum(int(x) for x in re.findall(r"\((\d+)\)", r["sum"])) + r["total"] + E("QS.data.quests.filter(q=>!(QS.R.quests[q.g]&&QS.R.quests[q.g].s)&&qsState(q.g)==='done').length") == 191 and r["total"] == 8 and r["dup"] == 0, r)
        check("%s [%s]: v34.3 invariant, Base game, every gate: the open quests that fail at a gate = those in its bracket (placed) + those in its strip group; none drawn twice; the Missable panel's list at the next gate = bracket + strip group (%s)" % (label, sub, r["panel"]), not r["bad"] and r["panel"] and r["panel"]["ok"] and r["panel"]["gate"] == "isle" and r["panel"]["n"] == 10, r)
        order = E("[...document.querySelectorAll('#qsMU .qsmug')].map(x=>x.dataset.gate+(x.classList.contains('passed')?'*':''))")
        check("%s [%s]: v34.3 groups: the next gate not passed first, then the others in story order, passed gates last and dashed grey (%s)" % (label, sub, order), order == ["isle", "battle", "novigrad3", "skellige3", "prologue*"], order)
        st = E("""(()=>{const c=e=>getComputedStyle(e),g=document.querySelector('#qsMU .qsmug[data-gate="isle"]'),p=document.querySelector('#qsMU .qsmug.passed'),b1=g.querySelector('.qsgb'),b2=p.querySelector('.qsgb'),fb=document.querySelector('#qsTL .qsfl'),d=g.querySelector('.qsdot'),q=QS.byG.get(d.dataset.g),ref=document.createElement('div');ref.innerHTML=qsShape(q.t,qsState(q.g));
          return{label:g.querySelector('.qsfl').textContent,num:b1.textContent,key:qsGateKey('b')[1].n,bd:[c(g).borderTopColor,c(g).borderTopStyle],pd:[c(p).borderTopColor,c(p).borderTopStyle],pnum:b2.textContent,pbg:c(b2).backgroundColor,lab:c(g.querySelector('.qsfl')).color,gridlab:c(fb).color,svg:d.innerHTML===ref.innerHTML,cls:d.className,col:c(d).color,gridcol:c(document.querySelector('#qsTL .qsdot.t-side')).color,size:[d.getBoundingClientRect().width,d.getBoundingClientRect().height],
          pstat:p.querySelector('.qsdot').className}})()""")
        check("%s [%s]: v34.3 the strip uses the grid's look: orange 'fails at <n>' bracket with the gate's number from the key (%s = %s), the same type shape and colour and status fill as the grid's markers, 20 px; passed = dashed grey with a grey badge (%s)" % (label, sub, st["num"], st["key"], st["pd"]),
              st["label"].startswith("fails at 2") and st["num"] == str(st["key"]) and st["bd"] == ["rgb(240, 138, 36)", "solid"] and st["pd"] == ["rgb(143, 133, 117)", "dashed"] and st["pnum"] == "1" and st["pbg"] == "rgb(107, 99, 85)" and st["lab"] == st["gridlab"] and st["svg"] and st["col"] == st["gridcol"] and st["size"] == [20, 20], st)
        # tooltip, drawer
        pg.hover('#qsMU .qsmug[data-gate="isle"] .qsdot >> nth=0'); tip = E("document.getElementById('qsTip').textContent"); pg.mouse.move(5, 5)
        check("%s [%s]: v34.3 the tooltip of a strip entry says name, type, status and 'Fails at Isle of Mists' (%s)" % (label, sub, tip[:90]), "Redania's Most Wanted" in tip and "Fails at Isle of Mists" in tip and "Secondary" in tip, tip)
        pg.click('#qsMU .qsmug[data-gate="isle"] .qsdot >> nth=0'); pg.wait_for_timeout(350); dr = E("(()=>{const d=document.getElementById('qsDetail');return{open:document.getElementById('screenQ').classList.contains('qs-open'),txt:d.textContent,sel:QS.byG.get(QS.sel).n}})()")
        check("%s [%s]: v34.3 a click on a strip entry opens the same drawer (%s)" % (label, sub, dr["txt"][:80]), dr["open"] and dr["sel"] == "Redania's Most Wanted" and "Fails at Isle of Mists" in dr["txt"] and "— not computed yet" in dr["txt"], dr["txt"][:200])
        pg.keyboard.press("Escape"); pg.wait_for_timeout(250); foc = E("document.activeElement.dataset.g===QS.byG.get(QS.sel).g||document.activeElement.className")
        check("%s [%s]: v34.3 Escape closes the drawer and puts the focus back on a marker of that quest (%s)" % (label, sub, foc), E("!document.getElementById('screenQ').classList.contains('qs-open')") and E("(document.activeElement.dataset||{}).g===QS.sel"), foc)
        txt = E("document.getElementById('qsMU').textContent"); names = E("QS.data.quests.map(q=>q.n)")
        check("%s [%s]: v34.3 spoiler rules: the strip has quest names and gate names only, no journal or objective text (%d characters)" % (label, sub, len(txt)), E("(()=>{const m=document.getElementById('qsMU');return[...m.querySelectorAll('.qsdot')].every(d=>d.children.length===1&&d.firstElementChild.tagName.toLowerCase()==='svg')&&m.querySelectorAll('p').length===1})()") and len(txt) < 900, txt[:200])
        # a state change: Q402 Isle of Mists done passes gate 2
        isle = E("QS.data.quests.find(q=>q.id==='Q402 Isle of Mists').g"); E("qsMark('%s','done')" % isle); pg.wait_for_timeout(250); r2 = E(STRIPJS); o2 = E("[...document.querySelectorAll('#qsMU .qsmug')].map(x=>x.dataset.gate+(x.classList.contains('passed')?'*':''))")
        st2 = E("(()=>{const q=QS.data.quests.find(q=>q.n==='Redania\\'s Most Wanted');return[qsState(q.g),!!document.querySelector('#qsMU .qsmug.passed[data-gate=\"isle\"] .qsdot[data-g=\"'+q.g+'\"]')]})()")
        check("%s [%s]: v34.3 invariant after the Isle of Mists gate is passed: groups %s; Redania's Most Wanted keeps its status (%s) under the passed gate, dashed grey; every gate still adds up" % (label, sub, o2, st2[0]), not r2["bad"] and o2[0] == "battle" and "isle*" in o2 and o2[-1].endswith("*") and st2[1] and st2[0] == "none", [r2, o2, st2])
        # failed and done keep their status; done hides unless Show done
        dv = E("QS.data.quests.find(q=>q.n==='Contract: Devil by the Well').g"); rg = E("QS.data.quests.find(q=>q.n==='Redania\\'s Most Wanted').g"); E("qsMark('%s','done');qsMark('%s','failed')" % (dv, rg)); pg.wait_for_timeout(250)
        a = E("(()=>{const f=g=>document.querySelector('#qsMU .qsdot[data-g=\"'+g+'\"]');return{dv:!!f('%s'),rg:f('%s')&&f('%s').className}})()" % (dv, rg, rg)); pg.click("#qsShowDoneT"); pg.wait_for_timeout(250)
        b2 = E("(()=>{const e=document.querySelector('#qsMU .qsdot[data-g=\"%s\"]');return e&&e.className})()" % dv); r3 = E(STRIPJS)
        check("%s [%s]: v34.3 a Done quest follows Show done like the grid (hidden, then shown as 'done'), a Failed one keeps its failed look (%s, %s)" % (label, sub, a, b2), not a["dv"] and " failed" in a["rg"] and b2 and " done" in b2 and not r3["bad"], [a, b2, r3["bad"]])
        E("qsMark('%s',null);qsMark('%s',null);qsMark('%s',null)" % (dv, rg, isle)); pg.click("#qsShowDoneT"); pg.wait_for_timeout(200)
        for sc in ("hos", "bob"):
            pg.click('#qsScope [data-scope="%s"]' % sc); pg.wait_for_timeout(200); r4 = E(STRIPJS)
            check("%s [%s]: v34.3 scope %s: every gate adds up (bracket + strip), no strip (no quest of the pack lacks a story point and is missable), the base game's quests are not shown here (%d gates)" % (label, sub, sc, len(r4["gates"])), not r4["bad"] and not r4["vis"] and r4["gates"], r4)
        pg.click('#qsScope [data-scope="base"]'); pg.wait_for_timeout(200)
        ks = E("Object.keys(localStorage).sort()"); check("%s [%s]: v34.3 no new storage keys (%s: only the existing w3p.quests.* ones), the link is unchanged" % (label, sub, ks), E("location.hash") == h0 and not [k for k in ks if re.search(r"strip|miss|unknown", k)] and all(k.startswith(("w3p.quests.", "w3planner.", "w3p.")) for k in ks))
        check("%s [%s]: no script errors" % (label, sub), not errs, errs[:1]); pg.close()
    d = FIXD / "stats-l9b"; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
    if sav:
        pg, errs, _ = newpage(b, base, w=390, h=844, mobile=True); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
        opened(pg); until(pg, "!!QS.R&&!!QS.desc"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
        m = E("(()=>{const s=document.getElementById('qsMU').getBoundingClientRect();return{page:document.documentElement.scrollWidth-innerWidth,in:s.right<=innerWidth+1&&s.left>=0,groups:[...document.querySelectorAll('#qsMU .qsmug')].every(g=>g.getBoundingClientRect().right<=innerWidth+1)}})()")
        pg.click('#qsMU .qsdot >> nth=0'); pg.wait_for_timeout(350); dr = E("(()=>{const d=document.getElementById('qsDetail').getBoundingClientRect();return[Math.round(d.width),innerWidth]})()")
        check("%s: v34.3 390 px: the strip wraps inside the screen and the page does not scroll sideways (%s); a marker opens the full-screen drawer (%s)" % (label, m, dr), m["page"] <= 1 and m["in"] and m["groups"] and dr[0] == dr[1], [m, dr])
        check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


# ---------------------------------------------------------------- v35: the unplaced quests split, "can fail by a choice"
SPIKE35 = Path.home() / "work" / "w3planner-art" / "quest-spike" / "v35"
KNOWN_KEYS = {"w3p.quests.v1", "w3p.quests.view", "w3p.quests.banddone", "w3p.quests.timedone", "w3p.quests.timescope"}
HELP_NOGATE = "They open when you reach the place, meet the person or find the item. The game files show no story point for them."
HELP_UNKNOWN = "The game files have a story gate for these that we can't read yet."


def verified_rows():
    """the rows of choices-verified.tsv (local, never committed); None when the file is absent"""
    f = SPIKE35 / "choices-verified.tsv"
    if not f.is_file(): return None
    import csv
    return list(csv.DictReader(f.open(encoding="utf-8"), delimiter="\t"))


def leaks(pg):
    """internal scene output or fact names (from the local evidence column) and snake_case tokens in the screen's text"""
    txt = pg.evaluate("document.getElementById('screenQ').innerText"); bad = sorted(set(re.findall(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b", txt)))
    rows = verified_rows() or []
    names = {m for r in rows for m in re.findall(r'scene output "([^"]+)"', r["evidence"])}
    bad += [n for n in names if re.search(r"[A-Z_ 0-9]", n[1:]) and re.search(r"\b%s\b" % re.escape(n), txt)]   # plain English words (done, bye) are not told apart from the interface text
    return bad


def v35(b, base, check, label):
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); until(pg, "!!QS.R&&!!QS.desc"); h0 = E("location.hash")
    rows = verified_rows(); R = json.loads((ROOT / "data" / "QUEST-RULES.json").read_text(encoding="utf-8"))["quests"]; names = {q["g"]: q for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    # --- the Timeline bottom, no save
    pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
    s1 = E("(()=>{const a=document.getElementById('qsNoGate'),c=document.getElementById('qsNotComputed');return{a:a.querySelector('summary').textContent,ao:a.open,ah:a.querySelector('.qsbnote').textContent,c:c.querySelector('summary').textContent,co:c.open,ch:c.querySelector('.qsbnote').textContent,order:[...document.querySelectorAll('#qsTL,#qsMU,.qslegend,#qsNoGate,#qsNotComputed')].map(e=>e.id||e.className),old:!!document.getElementById('qsUnk')||/Placement not computed/.test(document.getElementById('qsView').textContent)}})()")
    check("%s: v35 Timeline bottom, no save: 'No story gate found (157)' open with its help line, then 'Not computed yet (34)' collapsed with its help line; the old 'Placement not computed yet' row is gone (%s)" % (label, s1["a"] + " / " + s1["c"]),
          s1["a"] == "No story gate found (157)" and s1["ao"] and s1["ah"] == HELP_NOGATE and s1["c"] == "Not computed yet (34)" and not s1["co"] and s1["ch"] == HELP_UNKNOWN and not s1["old"] and s1["order"][-2:] == ["qsNoGate", "qsNotComputed"], s1)
    g = E("""(()=>{const rows=[...document.querySelectorAll('#qsNoGate .qsugrow')],all=[...document.querySelectorAll('#qsNoGate .qsdot,#qsNotComputed .qsdot')];
      return{labels:rows.map(r=>r.querySelector('.qsblabel').textContent),markers:all.every(d=>d.querySelector('svg.qsshape')&&/^qsdot t-/.test(d.className)),chips:[...document.querySelectorAll('#qsNoGate .qsmore')].length,
      kinds:[...document.querySelectorAll('#qsNoGate .qsdot')].every(d=>QS.R.quests[d.dataset.g].u==='ungated'),kinds2:(document.getElementById('qsNotComputed').open=true,[...document.querySelectorAll('#qsNotComputed .qsdot')].every(d=>QS.R.quests[d.dataset.g].u==='unknown'||!QS.R.quests[d.dataset.g]))}})()""")
    check("%s: v35 the section is grouped by region like the grid rows (%s), same markers, '+N' chips (%d), only 'ungated' quests in the first section and only 'unknown' ones in the second" % (label, g["labels"], g["chips"]), g["labels"][0] == "White Orchard" and "Velen" in g["labels"] and g["markers"] and g["chips"] > 0 and g["kinds"] and g["kinds2"], g)
    pg.click("#qsNoGate .qsmore >> nth=0"); pg.wait_for_timeout(150); more = E("document.querySelector('#qsNoGate .qsmore').textContent"); pg.click("#qsNoGate .qsmore >> nth=0"); pg.wait_for_timeout(100)
    check("%s: v35 the chip expands its row in place ('−') and folds it back" % label, more == "−" and E("document.querySelector('#qsNoGate .qsmore').textContent[0]") == "+", more)
    ung = E("document.querySelector('#qsNoGate .qsdot').dataset.g"); unk = E("(document.getElementById('qsNotComputed').open=true,document.querySelector('#qsNotComputed .qsdot').dataset.g)")
    pg.click('#qsNoGate .qsdot >> nth=0'); pg.wait_for_timeout(300); d1 = E("[document.querySelector('#qsDetail .qsrule').textContent,QS.sel,document.getElementById('screenQ').classList.contains('qs-open')]")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200); pg.click('#qsNotComputed .qsdot >> nth=0'); pg.wait_for_timeout(300); d2 = E("[document.querySelector('#qsDetail .qsrule').textContent,QS.sel]")
    check("%s: v35 a click opens the drawer; 'Story point:' says 'no story gate found' for an ungated quest and '— not computed yet' for an unknown one (%s | %s)" % (label, d1[0], d2[0]),
          d1[0] == "Story point: no story gate found" and d1[1] == ung and d1[2] and d2[0] == "Story point: — not computed yet" and d2[1] == unk, [d1, d2])
    pg.keyboard.press("Escape")
    # --- the marker and the drawer block on the keep rows
    keep = {}
    for g_, es in ((g_, r["k"]) for g_, r in R.items() if "k" in r): keep[g_] = es
    if rows is not None:
        vk = {r["quest_guid"] for r in rows if r["class"].startswith("keep")}
        check("%s: v35 choices-verified.tsv (%d keep, %d drop) and the quest rules agree: exactly the keep rows' quests carry `k`, no drop-only quest does" % (label, len(vk), sum(r["class"] == "drop" for r in rows)),
              vk == set(keep) and not ({r["quest_guid"] for r in rows if r["class"] == "drop"} - vk) & set(keep), [vk ^ set(keep)])
        for r in rows:
            e = keep.get(r["quest_guid"], [])
            if r["class"] == "keep-quest": ok = (["q", names[[q for q in names if names[q]["id"] == r["holder_quest"]][0]]["g"]] if r["holder_quest"] else ["q"]) in e
            elif r["class"] == "keep-obj": ok = ["o", r["objective_guid"]] in e
            else: ok = True
            if not ok: check("%s: v35 row %s (%s) is in the quest rules" % (label, r["row"], r["class"]), False, e)
    # list view: every keep quest has the ring marker and the 'by choice' tag, every other quest none
    pg.click("#qsVList"); pg.wait_for_timeout(200); E("QS.q='';QS.kind='all';QS.hide=false"); out = {}
    for rg in [x[0] for x in E("QS.data.regions")]:
        E("QS.region='%s';qsRenderAll()" % rg); out[rg] = E("[...document.querySelectorAll('#qsRows .qsrow')].map(r=>[r.dataset.g,r.classList.contains('choice'),!!r.querySelector('.qsbych'),getComputedStyle(r,'::after').content])")
    flat = [x for v in out.values() for x in v]; seen = {x[0] for x in flat if x[1]}
    check("%s: v35 list: the ring and the 'by choice' tag are on the %d keep quests and on no other (%d rows)" % (label, len(keep), len(flat)), seen == set(keep) and all(x[1] == x[2] for x in flat) and all(x[3] != "none" for x in flat if x[1]), [seen ^ set(keep)])
    # drawer: the block for every keep quest
    res = {}
    for g_ in keep:
        pg.evaluate("QS.reveal.clear();qsSelect('%s',true)" % g_); pg.wait_for_timeout(120)
        res[g_] = E("(()=>{const c=document.getElementById('qsChoice');return c?{h:c.querySelector('h3').textContent,rows:[...c.querySelectorAll('.qschrow')].map(p=>p.textContent),foot:c.querySelector('.qsmfoot').textContent,links:[...c.querySelectorAll('.qslink')].map(b=>b.dataset.g)}:null})()")
    bad = []
    for g_, es in keep.items():
        x = res[g_]
        if not x or x["h"] != "Can fail by choice" or x["foot"] != "From the game's quest graphs." or len(x["rows"]) != len(es): bad.append((names[g_]["n"], x)); continue
        for e, t in zip(es, x["rows"]):
            if e == ["q"] and t != "A choice in this quest's conversation ends it as failed.": bad.append((names[g_]["n"], t))
            if e[0] == "q" and len(e) == 2 and not (t == "Fails through a choice in " + names[e[1]]["n"] and x["links"] == [e[1]]): bad.append((names[g_]["n"], t))
            if e[0] == "o" and not t.startswith("A choice can close"): bad.append((names[g_]["n"], t))
    check("%s: v35 drawer: every keep quest has the CAN FAIL BY CHOICE block with the wording for its kind and the footer (%d quests)" % (label, len(keep)), not bad and len(res) == len(keep), bad[:3])
    nob = [g_ for g_ in names if g_ not in keep]
    pg.evaluate("QS.reveal.clear();qsSelect('%s',true)" % nob[0]); pg.wait_for_timeout(100)
    check("%s: v35 a quest that is not a keep row has no block and no marker (%s)" % (label, names[nob[0]]["n"]), E("!document.getElementById('qsChoice')"))
    gangs = [g_ for g_ in keep if names[g_]["id"] == "Q302 War Of Gangs"][0]
    check("%s: v35 The Gangs of Novigrad (one keep-obj row, three drop rows: the casino dwarves, both reward variants) shows exactly one entry" % label, len(res[gangs]["rows"]) == 1 and res[gangs]["rows"][0].startswith("A choice can close"), res[gangs])
    # cross-quest link
    fp = [g_ for g_ in keep if any(len(e) == 2 and e[0] == "q" for e in keep[g_])]
    ok = []
    for g_ in fp:
        pg.evaluate("qsSelect('%s',true)" % g_); pg.wait_for_timeout(100); pg.click("#qsChoice .qslink"); pg.wait_for_timeout(150); holder = [e[1] for e in keep[g_] if len(e) == 2][0]
        ok.append(E("[QS.sel,document.querySelector('#qsDetail .qstitle').textContent]") == [holder, names[holder]["n"]])
    check("%s: v35 the cross-quest link opens the other quest's drawer (%d links)" % (label, len(fp)), fp and all(ok), ok)
    # spoiler rule: a quest the save has not reached keeps the objective title behind the full-journal button
    wh = [g_ for g_ in keep if keep[g_][0][0] == "o"][0]; pg.evaluate("QS.reveal.clear();qsSelect('%s',true)" % wh); pg.wait_for_timeout(150)
    t0 = E("document.querySelector('#qsChoice .qschrow').textContent"); title = E("QS.desc[QS.byG.get('%s').id].o[QS.byG.get('%s').o.indexOf('%s')]" % (wh, wh, keep[wh][0][1]))
    pg.click(".qsspoil"); pg.wait_for_timeout(150); t1 = E("document.querySelector('#qsChoice .qschrow').textContent")
    check("%s: v35 spoiler rule: before the full journal is shown the block says 'A choice can close an objective.' (%s) and hides the title; after 'Show full journal (spoilers)' it names it (%s)" % (label, t0[:60], t1[:70]),
          title and title not in t0 and t0.startswith("A choice can close an objective") and t1 == "A choice can close the objective: %s." % title.rstrip("."), [t0, t1])
    # leaks and storage
    bad = leaks(pg); ks = E("Object.keys(localStorage).sort()"); src = (ROOT / "src" / "quests.js").read_text(encoding="utf-8")
    check("%s: v35 no internal scene output or fact name appears in the screen (%s)" % (label, bad[:3]), not bad, bad)
    check("%s: v35 no new storage keys (%s; the source names only the five known ones) and the link is unchanged" % (label, ks), set(ks) <= KNOWN_KEYS and set(re.findall(r"'(w3p\.[a-z0-9.]+)'", src)) == KNOWN_KEYS and E("location.hash") == h0, ks)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def v35save(b, base, check, label):
    d = FIXD / "stats-l9b"; sav = sorted(d.glob("*.sav")) if d.is_dir() else []
    if not sav: print("  SKIP  %s: v35 against the stats-l9b save (fixture not present)" % label); return
    pg, errs, _ = newpage(b, base); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
    opened(pg); until(pg, "!!QS.R&&!!QS.desc"); h0 = E("location.hash"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
    COUNT = """(()=>{const n=s=>{const e=document.querySelector(s+' summary');return e?+e.textContent.match(/\\((\\d+)\\)/)[1]:0},pk=QS.tscope,pack=q=>q.p==='ep1'?'hos':q.p==='bob'?'bob':'base',un=QS.data.quests.filter(q=>!(QS.R.quests[q.g]&&QS.R.quests[q.g].s)&&pack(q)===pk),
      strip=document.querySelectorAll('#qsMU .qsdot').length,a=n('#qsNoGate'),c=n('#qsNotComputed'),dots=[...document.querySelectorAll('.qsug .qsdot')].map(d=>d.dataset.g),st=new Set([...document.querySelectorAll('#qsMU .qsdot')].map(d=>d.dataset.g));
      return{strip,a,c,unplaced:un.length,done:un.filter(q=>qsState(q.g)==='done').length,showDone:QS.timeDone,overlap:dots.filter(g=>st.has(g)).length,dup:dots.length-new Set(dots).size,
       shown:document.querySelectorAll('.qsug .qsdot').length+[...document.querySelectorAll('.qsug .qsmore')].reduce((s,e)=>s+(e.textContent[0]==='+'?+e.textContent.slice(1):0),0)}})()"""
    for sc in ("base", "hos", "bob"):
        pg.click('#qsScope [data-scope="%s"]' % sc); pg.wait_for_timeout(250)
        for sd in (False, True):
            if E("QS.timeDone") != sd: pg.click("#qsShowDoneT"); pg.wait_for_timeout(200)
            r = E(COUNT); tot = r["strip"] + r["a"] + r["c"] + (0 if sd else r["done"])
            check("%s [stats-l9b]: v35 scope %s, Show done %s: strip %d + 'No story gate found' %d + 'Not computed yet' %d%s = all %d unplaced quests of the scope; the strip is not repeated; markers shown = counts" % (label, sc, "on" if sd else "off", r["strip"], r["a"], r["c"], "" if sd else " + %d done hidden" % r["done"], r["unplaced"]),
                  tot == r["unplaced"] and r["overlap"] == 0 and r["dup"] == 0 and r["shown"] == r["a"] + r["c"] and (r["strip"] == 8 if sc == "base" else r["strip"] == 0), r)
        if E("QS.timeDone"): pg.click("#qsShowDoneT"); pg.wait_for_timeout(150)
    pg.click('#qsScope [data-scope="base"]'); pg.wait_for_timeout(200)
    order = E("[...document.querySelectorAll('#qsMU .qsmug')].map(x=>x.dataset.gate+(x.classList.contains('passed')?'*':'')+':'+x.querySelectorAll('.qsdot').length).join()")
    check("%s [stats-l9b]: v35 the strip is unchanged: 8 quests under the same gates (%s)" % (label, order), E("document.querySelectorAll('#qsMU .qsdot').length") == 8 and order.startswith("isle:") and order.endswith("prologue*:1"), order)
    mis = E("[...document.querySelectorAll('#qsMiss .qsmi, #qsNext .qscard.fails')].map(e=>e.dataset.g)")
    check("%s [stats-l9b]: v35 choice quests are not added to the Missable panel or Next up's 'Fails at' cards: every one listed has a gate cutoff (%d listed)" % (label, len(mis)), mis and all("c" in E("QS.R.quests['%s']" % g) for g in mis), mis)
    # a reached quest shows its objective title at once
    g = E("QS.data.quests.find(q=>q.id==='Q302 War Of Gangs').g"); pg.evaluate("QS.reveal.clear();qsSelect('%s',true)" % g); pg.wait_for_timeout(200); t = E("document.querySelector('#qsChoice .qschrow').textContent")
    check("%s [stats-l9b]: v35 The Gangs of Novigrad (active in the save) names the objective: %s" % (label, t[:70]), t.startswith("A choice can close the objective: "), t)
    # markers on the grid, the strip legend
    leg = E("[...document.querySelectorAll('.qslegend li')].map(e=>e.textContent)"); ring = E("(()=>{const d=document.querySelector('#qsTL .qsdot.choice');if(!d)return null;const a=getComputedStyle(d,'::after');return{pos:[a.right,a.bottom],bd:a.borderTopColor,pe:a.position}})()")
    pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')")
    check("%s [stats-l9b]: v35 legend has 'Can fail by a choice'; the ring sits at the bottom right in cream (%s)" % (label, ring), "Can fail by a choice" in leg and ring and ring["pe"] == "absolute" and ring["pos"] == ["-2px", "-2px"] and ring["bd"] == "rgb(244, 234, 210)", [leg, ring])
    ks = E("Object.keys(localStorage)"); check("%s [stats-l9b]: v35 no storage key beyond the known ones (%s; the save import's own stash is the only other) and the link is unchanged (%s -> %s)" % (label, ks, h0[:20], E("location.hash")[:20]), set(ks) <= KNOWN_KEYS | {"w3planner.stash"} and E("location.hash") == h0)
    check("%s [stats-l9b]: no script errors" % label, not errs, errs[:1]); pg.close()
    pg, errs, _ = newpage(b, base, w=390, h=844, mobile=True); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); until(pg, "!document.getElementById('impStep2').hidden"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
    opened(pg); until(pg, "!!QS.R&&!!QS.desc"); pg.click("#qsVTime"); until(pg, "!!document.getElementById('qsTL')"); pg.wait_for_timeout(250)
    m = E("(()=>{const s=document.getElementById('qsNoGate').getBoundingClientRect();return{page:document.documentElement.scrollWidth-innerWidth,in:s.right<=innerWidth+1&&s.left>=0,rows:[...document.querySelectorAll('.qsug .qsbplot')].every(e=>e.getBoundingClientRect().right<=innerWidth+1),sum:Math.round(document.querySelector('.qsug summary').getBoundingClientRect().height)}})()")
    check("%s [stats-l9b]: v35 390 px: the two sections stay inside the screen, the page does not scroll sideways, the summary is a 44 px target (%s)" % (label, m), m["page"] <= 1 and m["in"] and m["rows"] and m["sum"] >= 44, m)
    check("%s [stats-l9b, phone]: no script errors" % label, not errs, errs[:1]); pg.close()


def v35public(b, base, check, label):
    """the public build has no objective titles: the block says 'an objective'"""
    pg, errs, _ = newpage(b, base); E = pg.evaluate; opened(pg); until(pg, "!!QS.R")
    g = E("QS.data.quests.find(q=>q.id==='SQ104 Werewolf').g"); pg.evaluate("qsSelect('%s',true)" % g); pg.wait_for_timeout(200); t = E("document.querySelector('#qsChoice .qschrow').textContent")
    check("%s: v35 without objective titles the block says 'an objective' (%s)" % (label, t), t == "A choice can close an objective." and not errs, errs[:1]); pg.close()
