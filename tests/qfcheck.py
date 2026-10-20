"""v39: the quest fail safeguard (data/QUEST_FAILS.json, tools/build_quest_fails.py, src/questfails.js).

data(check)                       the shipped file is exactly the verified link of tests/fixtures/quest_fails/sq106_q401.json (no browser)
tool(check)                       tools/build_quest_fails.py ships verified records only and refuses a candidate (fake candidate files, no browser)
run(b, base, check, label)        states (red + amber, nothing, prompt and its two buttons), no automatic change, List, Timeline, Level band, Next up, failed state, contrast, phone
offline(b, off, check, label)     the same safeguard in the offline package (file://)
Used by tests/run_all.py. Quest GUIDs: Ugly Baby is the failer, Following the Thread the failed quest."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
import qscheck as Q

ROOT = Path(__file__).resolve().parent.parent
UGLY, THREAD = "307d9fcade274740b37341fa6a6a76c7", "9cf4eb23b5bfd24c94fbd8a2a64070b2"
FX = ROOT / "tests" / "fixtures" / "quest_fails" / "sq106_q401.json"


def seed(manual):
    return "localStorage.setItem('w3p.quests.v1',JSON.stringify({v:1,manual:%s,save:null,changed:1}))" % json.dumps(manual)


def tool_run(*args):
    return subprocess.run([sys.executable, str(ROOT / "tools" / "build_quest_fails.py")] + list(args), capture_output=True, text=True)


def data(check):
    fx = json.loads(FX.read_text(encoding="utf-8")); d = json.loads((ROOT / "data" / "QUEST_FAILS.json").read_text(encoding="utf-8")); L = d["links"]
    qs = {q["g"]: q for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    l = L[0] if L else {}
    check("QUEST_FAILS.json: version 1 and exactly one link, the verified SQ106 <- Q401 one of the fixture", d["v"] == 1 and len(L) == 1 and set(d) == {"v", "links"}, [x.get("fact") for x in L])
    check("QUEST_FAILS.json: the link is the fixture's (failed and failer GUID, fact, comparison, trigger phase)", all(l.get(k) == fx[k] for k in ("failed_guid", "failer_guid", "fact", "op", "trigger_phase")) and fx["trigger_phase"] == "Collect UMA > Stable Master", l)
    check("QUEST_FAILS.json: both GUIDs are quests of QUESTS.json (Following the Thread, Ugly Baby)", qs[l["failed_guid"]]["n"] == "Following the Thread" and qs[l["failer_guid"]]["n"] == "Ugly Baby", l)
    ev = l["evidence"]
    check("QUEST_FAILS.json: the evidence holds the fail block 458, the pause 456, the setter 3582 and the trigger scene of the fixture; the engine effect stays 'unconfirmed'",
          {(e["file"].split("/")[-1], e["block"]) for e in ev} >= {("sq106_killbill.w2phase", 458), ("sq106_killbill.w2phase", 456), ("q401_konsylium.w2phase", 3582)} and any(e["file"] == fx["trigger_scene"] for e in ev)
          and l["engine_effect"] == "unconfirmed" and all(set(e) == {"file", "block", "note"} for e in ev) and l["trigger_label"] == "Talk to the stable guard at Crow's Perch", l.get("engine_effect"))
    check("QUEST_FAILS.json: the candidates file is not tracked (.gitignore) and the fixture says verified_gamefiles", "QUEST_FAILS.candidates.json" in (ROOT / ".gitignore").read_text() and fx["status"] == "verified_gamefiles")


def tool(check):
    sys.path.insert(0, str(ROOT / "tools"))
    import build_quest_fails as T
    quests = {q["g"] for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    good = {"failed_id": "SQ106 Killbill", "failer_id": "Q401 Konsylium", "failed_guid": THREAD, "failer_guid": UGLY, "fact": "q401_gotten_uma", "status": "verified_gamefiles", "engine_effect": "unconfirmed: x",
            "op_original": {"func": "CF_GreaterEqual", "value": 1}, "setter_phase_path": ["part_1.w2phase#15 QUEST - q401_konsylium", "q401_konsylium.w2phase#3423 Collect UMA", "q401_konsylium.w2phase#3545 Stable Master"],
            "evidence": [{"file": "a.w2phase", "block": 1, "note": "n"}]}
    cand = dict(good, status="candidate")
    try: out = T.convert(good, quests)
    except SystemExit as e: out = str(e)
    check("build_quest_fails: a verified_gamefiles record becomes a link (phase 'Collect UMA > Stable Master', engine effect 'unconfirmed')", isinstance(out, dict) and out["trigger_phase"] == "Collect UMA > Stable Master" and out["engine_effect"] == "unconfirmed", out)
    try: T.convert(cand, quests); r = None
    except SystemExit as e: r = str(e)
    check("build_quest_fails: a candidate record is refused (SystemExit naming the status)", r is not None and "candidate" in r, r)
    for name, rec in (("an unknown GUID", dict(good, failed_guid="0" * 32)), ("a missing comparison value", dict(good, op_original={"func": "CF_Equal", "value": None})), ("no evidence", dict(good, evidence=[])), ("a fact with no wording", dict(good, fact="other_fact"))):
        try: T.convert(rec, quests); r = None
        except SystemExit as e: r = str(e)
        check("build_quest_fails: a verified record with %s is refused" % name, r is not None, r)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); c = td / "c.json"; o = td / "o.json"
        c.write_text(json.dumps({"pairs": [good, dict(cand, failed_guid="1" * 32)]})); r = tool_run("--candidates", str(c), "--out", str(o))
        w = json.loads(o.read_text()) if o.exists() else {}
        check("build_quest_fails (CLI): two records, one verified and one candidate: only the verified one is written", r.returncode == 0 and len(w.get("links", [])) == 1 and w["links"][0]["failed_guid"] == THREAD, r.stderr[-200:])
        o.unlink(); r = tool_run("--candidates", str(c), "--out", str(o), "--include", "1" * 32)
        check("build_quest_fails (CLI): --include naming the candidate record stops and writes nothing", r.returncode != 0 and not o.exists() and "candidate" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [cand]})); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): a file with no verified record stops and writes nothing", r.returncode != 0 and not o.exists(), r.stderr[-200:])
    cf = ROOT / "data" / "QUEST_FAILS.candidates.json"
    if cf.exists():
        r = tool_run("--check")
        check("build_quest_fails --check: the committed data/QUEST_FAILS.json is what the candidates file gives", r.returncode == 0, (r.stdout + r.stderr)[-200:])
    else: print("  (build_quest_fails --check skipped: the local candidates file is absent)")


BG = """e=>{let x=e;while(x){const c=getComputedStyle(x).backgroundColor,m=c.match(/[\\d.]+/g);if(m&&(m.length<4||+m[3]>.9))return m.slice(0,3).map(Number);x=x.parentElement}return[13,12,10]}"""


def ratio(pg, sel, what, check, label, minimum=4.5):
    """the lowest contrast of a text element: its colour against the first opaque background behind it"""
    r = pg.evaluate("""([sel,bgf])=>{const bg=eval(bgf),out=[];document.querySelectorAll(sel).forEach(e=>{if(!e.offsetParent&&getComputedStyle(e).position!=='fixed')return;const m=getComputedStyle(e).color.match(/[\\d.]+/g).map(Number);out.push([m.slice(0,3),bg(e),(e.textContent||'').trim().slice(0,30)])});return out}""", [sel, BG])
    worst = min(((Q.contrast(tuple(int(v) for v in a), tuple(int(v) for v in b)), t) for a, b, t in r), default=(99, ""))
    check("%s: %s text has at least 4.5:1 contrast (%d element(s), lowest %.2f %r)" % (label, what, len(r), worst[0], worst[1]), len(r) > 0 and worst[0] >= minimum, worst)


def run(b, base, check, label):
    both = seed({UGLY: "active"})
    pg, errs, reqs = Q.newpage(b, base, init=both); E = pg.evaluate; Q.opened(pg, "km")
    keys0 = E("Object.keys(localStorage).sort()"); man0 = E("JSON.stringify(QS.store.manual)")
    Q.until(pg, "!!document.querySelector('.qfbanner')")
    # --- state 1: both open -> red + amber
    ban = E("[...document.querySelectorAll('.qfbanner p')].map(p=>p.textContent.trim())")
    check("%s: Ugly Baby active and Following the Thread not started: the banner reads 'Continuing Ugly Baby fails 1 open quest. Do the amber one first.' (%s)" % (label, ban), ban == ["Continuing Ugly Baby fails 1 open quest. Do the amber one first."], ban)
    row = E("""(()=>{const w=document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow');return w&&{cls:w.className,chip:w.querySelector('.qfchip').textContent,step:w.querySelector('.qfstep').textContent,aria:w.querySelector('.qsrow').getAttribute('aria-label')}})()""" % UGLY)
    check("%s: List: the failer row is red (qf-fail) with the chip 'Fails 1 quest' and the line naming the step (%s)" % (label, row), row and "qf-fail" in row["cls"] and row["chip"] == "Fails 1 quest"
          and row["step"] == "› Talk to the stable guard at Crow's Perch — Following the Thread fails here" and "fails 1 open quest" in row["aria"], row)
    pg.click('.qsreg[data-r="no"]'); pg.wait_for_timeout(150)
    row = E("""(()=>{const w=document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow');return w&&{cls:w.className,chip:w.querySelector('.qfchip').textContent,step:w.querySelector('.qfstep').textContent,
      sum:w.querySelector('details.qfwhy>summary').textContent,open:w.querySelector('details.qfwhy').open,evopen:w.querySelector('details.qfev').open,h:w.querySelector('details.qfwhy>summary').getBoundingClientRect().height,
      src:w.querySelector('.qfsrc').textContent,chain:w.querySelector('details.qfwhy ol').textContent}})()""" % THREAD)
    check("%s: List: the at-risk row is amber (qf-risk) with the chip 'Do before Ugly Baby', the trigger line and a real <details> 'Why?' (closed, 44 px summary) (%s)" % (label, {k: row[k] for k in ("cls", "chip", "step", "sum", "open")}),
          row and "qf-risk" in row["cls"] and row["chip"] == "Do before Ugly Baby" and row["step"] == "Fails at › Talk to the stable guard at Crow's Perch in Ugly Baby." and row["sum"] == "Why?" and not row["open"] and row["h"] >= 44, row)
    check("%s: 'Why?' holds a plain-language chain, the evidence collapsed inside it and 'Source: remaster game files' (%s)" % (label, row["chain"][:60]), "q401_gotten_uma" in row["chain"] and not row["evopen"] and row["src"] == "Source: remaster game files", row)
    E("document.querySelector('details.qfwhy>summary').click()"); pg.wait_for_timeout(100)
    check("%s: the disclosure opens by click and the evidence list lists the files and blocks (458, 456, 3582)" % label, E("(()=>{const d=document.querySelector('details.qfwhy');d.querySelector('.qfev>summary').click();const t=d.querySelector('.qfev').textContent;return d.open&&['#458','#456','#3582'].every(x=>t.includes(x))})()"))
    # --- Next up
    nx = E("""(()=>{const r={};document.querySelectorAll('#qsNext .qscard').forEach(c=>{r[c.dataset.g]={cls:c.className,txt:c.textContent}});return r})()""")
    check("%s: Next up: a red caution box on the Ugly Baby card and an amber chip on the Following the Thread card (%s)" % (label, [k[:6] for k in nx]), UGLY in nx and THREAD in nx and "qf-fail" in nx[UGLY]["cls"] and "Careful: Talk to the stable guard at Crow's Perch fails Following the Thread." in nx[UGLY]["txt"]
          and "qf-risk" in nx[THREAD]["cls"] and "Do before Ugly Baby" in nx[THREAD]["txt"], nx)
    check("%s: Next up puts the amber quest before the quest that would fail it (%s)" % (label, list(nx)[:2]), list(nx).index(THREAD) < list(nx).index(UGLY))
    # Next up only pushes the amber quest once the failer is active: a fresh player (Ugly Baby not started) keeps the usual Next up, the red and amber marks still show in the List
    pn, _, _ = Q.newpage(b, base, init=seed({})); Q.opened(pn, "no"); Q.until(pn, "!!document.querySelector('.qfbanner')")
    fresh = pn.evaluate("[!!document.querySelector('.qfbanner'),!!document.querySelector('.qfrow.qf-risk'),[...document.querySelectorAll('#qsNext .qscard')].map(c=>c.dataset.g).includes('%s')]" % THREAD)
    check("%s: Ugly Baby not started: the List is marked (banner, amber row) but Next up does not push Following the Thread forward (%s)" % (label, fresh), fresh == [True, True, False], fresh); pn.close()
    # --- no automatic change
    check("%s: nothing was changed by itself: the stored marks are the seed and no new storage key exists (%s)" % (label, keys0), E("JSON.stringify(QS.store.manual)") == man0 and E("Object.keys(localStorage).sort()") == keys0 and "w3p.quests.failack" not in keys0 and not E("document.querySelector('.qfprompt')"))
    # --- contrast (the red row is in the Kaer Morhen tab, the amber one in Novigrad)
    pg.click('.qsreg[data-r="km"]'); pg.wait_for_timeout(150); ratio(pg, '.qfrow.qf-fail .qsrn2 b, .qfrow.qf-fail .qslv, .qf-fail>.qfextra', "red row", check, label + " contrast"); pg.click('.qsreg[data-r="no"]'); pg.wait_for_timeout(150)
    for sel, what in (('.qfbanner p, .qfbanner b', "banner"), ('.qfrow.qf-risk .qsrn2 b, .qf-risk>.qfextra, .qfwhy summary, .qfwhy li, .qfwhy .qfsrc', "amber row"),
                      ('.qfchip', "chip"), ('.qfcaution', "caution box")):
        ratio(pg, sel, what, check, label + " contrast")
    # --- Timeline and Level band: ring, label, sub-line in the tooltip
    pg.click('.qsreg[data-r="km"]'); pg.click("#qsVTime"); pg.wait_for_timeout(300)
    dot = E("""(()=>{const d=document.querySelector('.qsdot[data-g="%s"]');return d&&{cls:d.className,aria:d.getAttribute('aria-label')}})()""" % UGLY)
    check("%s: Timeline: the Ugly Baby marker has the red ring (qf-fail) and says 'fails 1 open quest' in its label (%s)" % (label, dot), dot and "qf-fail" in dot["cls"] and "fails 1 open quest" in dot["aria"], dot)
    pg.hover('.qsdot[data-g="%s"]' % UGLY); pg.wait_for_timeout(150)
    tip = E("(()=>{const t=document.getElementById('qsTip');return !t.hidden&&t.textContent})()")
    check("%s: Timeline: the tooltip of the failer shows the sub-line '› Talk to the stable guard at Crow's Perch — Following the Thread fails here' (%s)" % (label, tip), tip and "› Talk to the stable guard at Crow's Perch — Following the Thread fails here" in tip, tip)
    ratio(pg, '#qsTip .qfsub', "tooltip sub-line", check, label + " contrast")
    pg.mouse.move(2, 2)
    unp = E("""(()=>{const d=document.querySelector('.qsdot[data-g="%s"]');return d?{cls:d.className,aria:d.getAttribute('aria-label')}:null})()""" % THREAD)
    check("%s: Timeline: when Following the Thread has a marker it has the amber ring (qf-risk) and 'at risk: do before Ugly Baby' in its label (%s)" % (label, unp), unp is None or ("qf-risk" in unp["cls"] and "at risk: do before Ugly Baby" in unp["aria"]), unp)
    check("%s: Timeline: the banner is above the chart" % label, E("!!document.querySelector('#qsView > .qfbanner:first-child')"))
    pg.click("#qsVBand"); pg.wait_for_timeout(300)
    dot = E("""(()=>{const d=document.querySelector('.qsdot[data-g="%s"]');return d&&{cls:d.className,aria:d.getAttribute('aria-label')}})()""" % UGLY)
    check("%s: Level band: the Ugly Baby dot has the red ring and the label says it fails 1 open quest (%s)" % (label, dot), dot and "qf-fail" in dot["cls"] and "fails 1 open quest" in dot["aria"], dot)
    pg.click('.qsreg[data-r="no"]'); pg.wait_for_timeout(300)
    dot = E("""(()=>{const d=document.querySelector('.qsdot[data-g="%s"]');return d&&{cls:d.className,aria:d.getAttribute('aria-label')}})()""" % THREAD)
    check("%s: Level band: the Following the Thread dot has the amber dashed ring (qf-risk) and 'at risk: do before Ugly Baby' (%s)" % (label, dot), dot and "qf-risk" in dot["cls"] and "at risk: do before Ugly Baby" in dot["aria"], dot)
    # within one cell the at-risk quest sorts above (before) its failer: put both in the same region, type and level in memory and draw again
    order = E("""(()=>{const a=QS.byG.get('%s'),f=QS.byG.get('%s');a.r=f.r;a.t=f.t;a.lv=f.lv;QS.region=f.r;qsRenderView();const ds=[...document.querySelectorAll('.qsdot')].map(d=>d.dataset.g);return[ds.indexOf('%s'),ds.indexOf('%s')]})()""" % (THREAD, UGLY, THREAD, UGLY))
    check("%s: Level band: in one cell the at-risk quest comes before its failer (positions %s)" % (label, order), order[0] >= 0 and order[1] >= 0 and order[0] < order[1], order)
    pg.close()
    # --- state 2: the failed quest is done -> nothing shows
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "active", THREAD: "done"})); E = pg.evaluate; Q.opened(pg, "km"); pg.wait_for_timeout(300)
    n = E("[document.querySelectorAll('.qfbanner,.qfrow,.qfprompt,.qf-fail,.qf-risk,.qfchip').length,!!document.querySelector('#qsNext .qfcaution')]")
    check("%s: Following the Thread done and Ugly Baby active: nothing is shown (no banner, no red, no amber, no prompt) (%s)" % (label, n), n == [0, False], n)
    E("qsMark('%s','failed')" % THREAD); pg.wait_for_timeout(150)
    check("%s: Following the Thread failed: nothing is shown either" % label, E("document.querySelectorAll('.qfbanner,.qfrow.qf-fail,.qfrow.qf-risk,.qfchip').length") == 0)
    pg.close()
    # --- state 3: the failer done, the failed quest open -> the prompt
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pr = E("""(()=>{const p=document.querySelector('.qfprompt');return p&&{t:p.querySelector('p').textContent,role:p.getAttribute('role'),b:[...p.querySelectorAll('button')].map(x=>[x.textContent,Math.round(x.getBoundingClientRect().height),x.getAttribute('aria-label')]),n:document.querySelectorAll('.qfprompt').length,ban:!!document.querySelector('.qfbanner')}})()""")
    check("%s: Ugly Baby done, Following the Thread open: the prompt 'Ugly Baby is done. Following the Thread would have failed along the way.' with its two buttons (role=status, 44 px), no red or amber (%s)" % (label, pr), pr and pr["t"] == "Ugly Baby is done. Following the Thread would have failed along the way."
          and pr["role"] == "status" and [x[0] for x in pr["b"][:2]] == ["Mark it failed", "I finished it first"] and all(x[1] >= 44 for x in pr["b"]) and pr["b"][2][2] == "Close this notice" and not pr["ban"] and pr["n"] == 1, pr)
    ratio(pg, '.qfprompt p, .qfprompt .btn', "prompt", check, label + " contrast")
    man = E("JSON.stringify(QS.store.manual)")
    pg.press(".qfprompt .btn", "Escape"); pg.wait_for_timeout(100)
    check("%s: Esc inside the prompt closes it, and changes no state (%s)" % (label, man), not E("document.querySelector('.qfprompt')") and E("JSON.stringify(QS.store.manual)") == man)
    E("QF.paint();qsRenderAll()"); pg.wait_for_timeout(100)
    check("%s: a closed prompt stays closed for the visit (it comes back on the next visit: the answer is a state, not a stored dismissal)" % label, not E("document.querySelector('.qfprompt')"))
    pg.close()
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pg.click(".qfprompt .qfx2"); pg.wait_for_timeout(100)
    check("%s: the × button closes the prompt" % label, not E("document.querySelector('.qfprompt')"))
    pg.close()
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pg.click('.qfprompt [data-a="failed"]'); pg.wait_for_timeout(200)
    st = E("[QS.store.manual['%s'],!!document.querySelector('.qfprompt'),document.querySelector('.qsrow[data-g=\"%s\"]').closest('.qfrow')&&document.querySelector('.qsrow[data-g=\"%s\"]').closest('.qfrow').textContent,document.querySelector('.qsrow[data-g=\"%s\"] .qsic').getAttribute('class')]" % (THREAD, THREAD, THREAD, THREAD))
    check("%s: 'Mark it failed' sets the hand mark to failed (the × outline stays) and the row says 'by Ugly Baby (stable guard)' (%s)" % (label, st[:2] + [(st[2] or '')[-40:]]), st[0] == "failed" and not st[1] and "by Ugly Baby (stable guard)" in (st[2] or "") and "qs-failed" in st[3], st)
    ratio(pg, '.qfby', "failed 'by' line", check, label + " contrast")
    pg.close()
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pg.click('.qfprompt [data-a="done"]'); pg.wait_for_timeout(200)
    st = E("[QS.store.manual['%s'],!!document.querySelector('.qfprompt'),!!document.querySelector('.qfrow')]" % THREAD)
    check("%s: 'I finished it first' sets the hand mark to done and the prompt goes (%s)" % (label, st), st == ["done", False, False], st)
    pg.close()
    # --- the prompt also sits on the failed quest's own detail panel; failer details say what they fail
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); E("qsSelect('%s')" % THREAD); pg.wait_for_timeout(200)
    check("%s: the failed quest's detail panel carries the same prompt" % label, E("!!document.querySelector('#qsDetail .qfprompt')"))
    pg.close()
    pg, errs, reqs = Q.newpage(b, base, init=both); E = pg.evaluate; Q.opened(pg, "km"); E("qsSelect('%s')" % UGLY); pg.wait_for_timeout(250)
    d1 = E("document.querySelector('#qsDetail .qfbox.red')&&document.querySelector('#qsDetail .qfbox.red').textContent")
    E("qsSelect('%s')" % THREAD); pg.wait_for_timeout(250)
    d2 = E("document.querySelector('#qsDetail .qfbox.amber')&&document.querySelector('#qsDetail .qfbox.amber').textContent.slice(0,120)")
    check("%s: detail panels: the failer says 'Fails 1 quest' and the step; the failed quest says 'Do before Ugly Baby' with its Why? (%s | %s)" % (label, d1, d2), d1 and "Fails 1 quest" in d1 and "fails here" in d1 and d2 and "Do before Ugly Baby" in d2, [d1, d2])
    check("%s: no page error and no request to another host" % label, not errs and not [r for r in reqs if r[1].startswith("http") and not r[1].startswith(base)], errs[:1])
    pg.close()
    # --- phone
    pg, errs, reqs = Q.newpage(b, base, w=390, h=844, mobile=True, init=both); E = pg.evaluate; Q.opened(pg, "no"); pg.wait_for_timeout(300)
    ph = E("""(()=>{const w=document.querySelector('.qfrow'),s=w&&w.querySelector('summary');return{sx:document.documentElement.scrollWidth-innerWidth,ban:document.querySelector('.qfbanner').getBoundingClientRect().width<=innerWidth,sum:s&&Math.round(s.getBoundingClientRect().height)}})()""")
    check("%s: phone (390 px): the red/amber rows and the banner do not scroll sideways, the Why? summary is a 44 px target (%s)" % (label, ph), ph["sx"] <= 1 and ph["ban"] and ph["sum"] >= 44, ph)
    pg.close()


def offline(b, off, check, label):
    pg, errs, reqs = Q.newpage(b, off, init=seed({UGLY: "active"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    t = E("[document.querySelector('.qfbanner')&&document.querySelector('.qfbanner').textContent.trim(),!!document.querySelector('.qfrow.qf-risk'),typeof QF,!!(window.W3DATA&&W3DATA.QUEST_FAILS)]")
    check("%s: the offline package has the safeguard: banner, amber row, QF script and data loaded from the package (%s)" % (label, t), t[0] == "Continuing Ugly Baby fails 1 open quest. Do the amber one first." and t[1] and t[2] == "object" and t[3], t)
    pg.close()
    pg, errs, reqs = Q.newpage(b, off, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pg.click('.qfprompt [data-a="failed"]'); pg.wait_for_timeout(200)
    check("%s: offline: the prompt's 'Mark it failed' works (hand mark failed)" % label, E("QS.store.manual['%s']" % THREAD) == "failed" and not errs, errs[:1])
    pg.close()
