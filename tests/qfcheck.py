"""v39: the quest fail safeguard (data/QUEST_FAILS.json, tools/build_quest_fails.py, src/questfails.js).

data(check)                       the shipped file is exactly the verified link of tests/fixtures/quest_fails/sq106_q401.json (no browser)
tool(check)                       tools/build_quest_fails.py ships verified records only and refuses a candidate (fake candidate files, no browser)
run(b, base, check, label)        states (red + amber, nothing, prompt and its two buttons), no automatic change, List, Timeline, Level band, Next up, failed state, contrast, phone
failures(b, base, check, label)   v39.2: the Quest failures tab (button, rows, order, statuses, hide filter, Details, footer, phone)
banner(b, base, check, label)     v39.1: the banner wording, tab dots, details panel, Go to quest, several links, phone
offline(b, off, check, label)     the same safeguard in the offline package (file://)
Used by tests/run_all.py. Quest GUIDs: Ugly Baby is the failer, Following the Thread the failed quest."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
import qscheck as Q

ROOT = Path(__file__).resolve().parent.parent
UGLY, THREAD = "307d9fcade274740b37341fa6a6a76c7", "9cf4eb23b5bfd24c94fbd8a2a64070b2"
FX = ROOT / "tests" / "fixtures" / "quest_fails" / "sq106_q401.json"


SQ202, Q206, SQ209 = "e19d8c03b676ce499748598b876ba7da", "e10a13b571218a46b0d37b0b9954be3f", "41135ec1f20a1d4aad85cabcea5a1c00"
LINKS = json.loads((ROOT / "data" / "QUEST_FAILS.json").read_text(encoding="utf-8"))["links"]
LEGACY = {UGLY + THREAD, UGLY + SQ202, Q206 + SQ209}
FAILED = sorted({l["failed_guid"] for l in LINKS})
# the tests of the first link (SQ106 <- Q401) keep every other link out of the way: their failed quests are done (nothing to warn, no prompt); `keep` leaves some of them open
ONLY3 = "(()=>{const L=new Set(%s),d=JSON.parse(JSON.stringify(W3DATA.QUEST_FAILS));d.links=d.links.filter(l=>L.has(l.failer_guid+l.failed_guid));QF.init(d);qsRenderAll()})()" % json.dumps(sorted(LEGACY))   # v39.4's world: the three first links only


def seed(manual, quiet=True, keep=()):
    m = {g: "done" for g in FAILED if g != THREAD and g not in keep} if quiet else {}
    m.update(manual)
    return "window.__ROW=%s;localStorage.setItem('w3p.quests.v1',JSON.stringify({v:1,manual:%s,save:null,changed:1}))" % (json.dumps('.qfrowx[data-k="%s%s"]' % (UGLY, THREAD)), json.dumps(m))


def tool_run(*args):
    return subprocess.run([sys.executable, str(ROOT / "tools" / "build_quest_fails.py")] + list(args), capture_output=True, text=True)


def expand(d):
    """the links of the shipped file with their evidence items in place (a shared item is stored once in `ev`, a link holds its index)"""
    return [dict(l, evidence=[dict(d.get("ev", [])[e]) if isinstance(e, int) else e for e in l["evidence"]]) for l in d["links"]]


def data(check):
    sys.path.insert(0, str(ROOT / "tools")); import make_quest_fail_fixtures as MF   # RETIRED: the fixtures of pulled links stay (append-only) and are not checked
    FXD = ROOT / "tests" / "fixtures" / "quest_fails"; fxs = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in sorted(FXD.glob("*.json")) if f.name not in MF.RETIRED}
    d = json.loads((ROOT / "data" / "QUEST_FAILS.json").read_text(encoding="utf-8")); L = expand(d)
    qs = {q["g"]: q for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    check("QUEST_FAILS.json: version 1, the keys v / links / candidates (/ ev), and %d links, one fixture each" % len(L), d["v"] == 1 and set(d) <= {"v", "links", "candidates", "ev"} and {"v", "links", "candidates"} <= set(d) and isinstance(d["candidates"], int) and d["candidates"] >= 0 and len(L) == len(fxs) == 44, [list(d), len(L), len(fxs)])
    key = lambda x: (x.get("failer_guid"), x.get("failed_guid"), x.get("fact"))
    check("every link of QUEST_FAILS.json has a fixture in tests/fixtures/quest_fails (and every fixture a link): %d of each" % len(fxs), {key(l) for l in L} == {key(x) for x in fxs.values()} and len({key(l) for l in L}) == len(L), sorted(fxs)[:3])
    check("QUEST_FAILS.json: shared evidence (`ev`): every index a link holds is an item of `ev`, every item of `ev` is used by 3 or more links, each is {file, block, note}", all(isinstance(e, dict) for l in L for e in l["evidence"]) and all(set(e) == {"file", "block", "note"} for e in d.get("ev", []))
          and all(sum(1 for l in d["links"] if i in l["evidence"]) >= 3 for i in range(len(d.get("ev", [])))) and all(0 <= e < len(d.get("ev", [])) for l in d["links"] for e in l["evidence"] if isinstance(e, int)), len(d.get("ev", [])))
    for name, fx in fxs.items():
        l = next((x for x in L if key(x) == key(fx)), {})
        kind = fx.get("kind", "fact")
        check("%s: the link is the fixture's (GUIDs, kind, fact, comparison, trigger phase) and both GUIDs are quests of QUESTS.json (%s <- %s)" % (name, qs.get(fx["failed_guid"], {}).get("n"), qs.get(fx["failer_guid"], {}).get("n")),
              all(l.get(k) == fx[k] for k in ("failed_guid", "failer_guid", "fact", "op", "trigger_phase")) and l.get("kind") == kind and l.get("effect") == fx.get("effect", "Failure") and fx["failed_guid"] in qs and fx["failer_guid"] in qs and fx["status"] == "verified_gamefiles"
              and qs[fx["failed_guid"]]["n"] == fx["failed_name"] and qs[fx["failer_guid"]]["n"] == fx["failer_name"], l.get("trigger_phase"))
        ev = l.get("evidence", [])
        lab = l.get("trigger_label", "")
        check("%s: evidence has the fail block %d and the step block %d, every item is {file, block, note}, engine effect 'unconfirmed', a noun-phrase trigger label that reads after 'at' (its first word does not end in -ing) and a short name" % (name, fx["fail_block"], fx["setter_block"]),
              {(e["file"], e["block"]) for e in ev} >= {(fx["fail_file"], fx["fail_block"]), (fx["setter_file"], fx["setter_block"])} and all(set(e) == {"file", "block", "note"} for e in ev) and l["engine_effect"] == "unconfirmed" and not lab.split(' ')[0].lower().endswith('ing')
              and (not lab.endswith(".") or lab.endswith("...")) and l.get("trigger_short", "").strip() != "", [lab, len(ev)])
        need = {"fact": ("fact", "op"), "fails_unless_set": ("fact", "op", "condition"), "choice": ("fact", "op", "choice"), "journal_status": ("journal",), "flow": ("flow",)}[kind]
        check("%s: kind %s carries what it needs (%s) and an explicit comparison value" % (name, kind, ", ".join(need)), all(l.get(k) for k in need) and (not l.get("op") or isinstance(l["op"]["value"], int)), [kind, [k for k in need if not l.get(k)]])
        if fx.get("trigger_scene"): check("%s: the trigger scene %s is in the evidence" % (name, fx["trigger_scene"].split("/")[-1]), any(e["file"] == fx["trigger_scene"] for e in ev))
    from collections import Counter
    kc = Counter(l["kind"] for l in L)
    check("QUEST_FAILS.json: the kinds (fact 34, fails_unless_set 4, choice 3, flow 3: v39.12 pulled the one journal_status link, which stood on a repair phase, and added the Cave of Dreams / Battle Preparations link), one Deactivate link (the others fail), 8 links with a premise note (an absent value read as 0), the three first links unchanged",
          dict(kc) == {"fact": 34, "fails_unless_set": 4, "choice": 3, "flow": 3} and [l["trigger_short"] for l in L if l["effect"] == "Deactivate"] == ["end of the fairy-tale quest"] and sum(bool(l.get("premise")) for l in L) == 8
          and {l["failer_guid"] + l["failed_guid"] for l in L} >= LEGACY, dict(kc))
    check("QUEST_FAILS.json: all 3 choice links carry the one traced safe option 'send Keira to Kaer Morhen in For the Advancement of Learning' (the pause's success output), and no label starts with an -ing verb",
          {l["safe"] for l in L if l["kind"] == "choice"} == {"send Keira to Kaer Morhen in For the Advancement of Learning"} and not any(l["trigger_label"].split(" ")[0].lower().endswith("ing") for l in L), [l.get("safe") for l in L if l["kind"] == "choice"])
    check("QUEST_FAILS.json: the wording is plain text, no game text (no quotation marks in the labels, conditions, choices, journal and flow sentences), and the failer of a choice is not the Isle of Mists",
          all(not re.search(r'["]', " ".join(str(l.get(k, "")) for k in ("trigger_label", "trigger_short", "condition", "choice", "journal", "flow", "premise"))) for l in L) and all(l["failer_guid"] != "5ce1c21a55b9cb4bb99706bfd11fa286" for l in L if l["kind"] == "choice"))
    cf = ROOT / "data" / "QUEST_FAILS.candidates.json"
    if cf.exists():
        C = json.loads(cf.read_text(encoding="utf-8")); P = C["pairs"]; V = C["coverage"]
        left_p = sum(p["status"] == "candidate" for p in P); left_c = sum(p["status"] == "candidate" for p in V)
        check("QUEST_FAILS.json: `candidates` (%d) is what is left in the candidates file (%d pairs still candidates + %d coverage candidates; not_a_fail / not_found / rejected do not count)" % (d["candidates"], left_p, left_c),
              d["candidates"] == left_p + left_c == 13 and all(p["status"] in ("verified_gamefiles", "rejected", "candidate") for p in P) and sum(p["status"] == "verified_gamefiles" for p in P) == 3
              and all(str(p.get("rejection", "")).strip() for p in P if p["status"] == "rejected") and all(str(p.get("missing", "")).strip() for p in P if p["status"] == "candidate") and all(not p["gaps"] for p in P if p["status"] == "verified_gamefiles")
              and all(p["status"] in ("verified_gamefiles", "rejected", "candidate", "not_a_fail", "not_found") for p in V) and all(str(p.get("rejection") or p.get("reason") or "").strip() for p in V if p["status"] == "rejected") and all(not p.get("gaps") for p in V if p["status"] == "verified_gamefiles")
              and sum(1 for p in V if p["status"] == "verified_gamefiles") == len(L) == 44 and len({p["checklist_entry"] for p in V}) == len(V))
        check("v39.12: every record of the candidates file is judged per site (a `sites` list), a repair / patch site is always rejected, no shipped link's evidence ends on a bugfixing_phase / patch file, and no record is rejected with a site that is not (%d records)" % (len(P) + len(V)),
              all(isinstance(r.get("sites"), list) for r in P + V) and all(x["status"] == "rejected" for r in P + V for x in r["sites"] if x["kind"] in ("repair", "patch"))
              and all(not re.match(r"(bugfix|patch)", json.loads(f.read_text(encoding="utf-8"))["fail_file"].split("/")[-1], re.I) for f in (ROOT / "tests" / "fixtures" / "quest_fails").glob("*.json") if f.name not in MF.RETIRED)
              and all({x["status"] for x in r["sites"]} == {"rejected"} for r in P + V if r["status"] == "rejected"), len(P + V))
    check("the candidates file is not tracked (.gitignore)", "QUEST_FAILS.candidates.json" in (ROOT / ".gitignore").read_text())


def tool(check):
    sys.path.insert(0, str(ROOT / "tools"))
    import build_quest_fails as T
    quests = {q["g"] for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    good = {"failed_id": "SQ106 Killbill", "failer_id": "Q401 Konsylium", "failed_guid": THREAD, "failer_guid": UGLY, "fact": "q401_gotten_uma", "status": "verified_gamefiles", "engine_effect": "unconfirmed: x",
            "op_original": {"func": "CF_GreaterEqual", "value": 1}, "setter_phase_path": ["part_1.w2phase#15 QUEST - q401_konsylium", "q401_konsylium.w2phase#3423 Collect UMA", "q401_konsylium.w2phase#3545 Stable Master"],
            "evidence": [{"file": "a.w2phase", "block": 1, "note": "n"}], "sites": [{"file": "quests/a.w2phase", "block": 1, "kind": "in_play_wait", "status": "verified_gamefiles"}]}
    cand = dict(good, status="candidate", sites=[{"file": "quests/a.w2phase", "block": 1, "kind": "in_play_wait", "status": "candidate", "missing": "the step"}]); pair0 = dict(good)
    REJ = [{"file": "quests/a.w2phase", "block": 1, "kind": "own_flow", "status": "rejected", "reason": "own flow"}]
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
        check("build_quest_fails (CLI): two records, one verified and one candidate: only the verified one is written, and `candidates` is the number 1 (no names)", r.returncode == 0 and len(w.get("links", [])) == 1 and w["links"][0]["failed_guid"] == THREAD and w.get("candidates") == 1 and "1" * 32 not in o.read_text(), r.stderr[-200:])
        o.unlink(); r = tool_run("--candidates", str(c), "--out", str(o), "--include", "1" * 32)
        check("build_quest_fails (CLI): --include naming the candidate record stops and writes nothing", r.returncode != 0 and not o.exists() and "candidate" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [good, dict(cand, failed_guid="1" * 32), dict(cand, failed_guid="2" * 32, status="rejected", rejection="not a cause", sites=REJ)]})); o.unlink(missing_ok=True); r = tool_run("--candidates", str(c), "--out", str(o))
        w = json.loads(o.read_text()) if o.exists() else {}
        check("build_quest_fails (CLI): verified + candidate + rejected: only the verified one is written; `candidates` counts only the one still being checked (a rejected record is not 'still being checked')", r.returncode == 0 and len(w.get("links", [])) == 1 and w.get("candidates") == 1, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [good, dict(cand, status="rejected", sites=REJ)]})); o.unlink(missing_ok=True); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): a rejected record without a reason stops and writes nothing", r.returncode != 0 and not o.exists() and "without a reason" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [good, dict(cand, status="maybe", sites=REJ)]})); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): an unknown status stops", r.returncode != 0 and "unknown status" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [dict(good, gaps=["x"])]})); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): a verified record whose gaps are not empty stops", r.returncode != 0 and "gaps are not empty" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [cand]})); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): a file with no verified record stops and writes nothing", r.returncode != 0 and not o.exists(), r.stderr[-200:])
    # --- v39.12: the per-site rule: every record is judged per fail site; a repair / patch site never ships and never rejects a record that has an in-play site
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); c = td / "c.json"; o = td / "o.json"
        S = lambda f, b, kind, status, **kw: dict({"file": f, "block": b, "kind": kind, "status": status}, **kw)
        rep_ = S("quests/bugfixing_phase.w2phase", 9, "repair", "rejected", reason="repair"); inp = S("quests/x.w2phase", 5, "in_play_wait", "verified_gamefiles")
        def cli(rec, extra=()):
            c.write_text(json.dumps({"pairs": [good, dict(rec, failed_guid="3" * 32)] + list(extra)})); o.unlink(missing_ok=True); return tool_run("--candidates", str(c), "--out", str(o))
        r = cli(dict(good, sites=[rep_])); check("build_quest_fails (v39.12): a record verified on a repair site alone is refused ('no in-play site is verified')", r.returncode != 0 and "no in-play site is verified" in r.stderr, r.stderr[-200:])
        r = cli(dict(good, sites=[dict(rep_, status="verified_gamefiles"), inp])); check("build_quest_fails (v39.12): a repair / patch site can never be verified (even next to a verified in-play site)", r.returncode != 0 and "never ships" in r.stderr, r.stderr[-200:])
        r = cli(dict(good, sites=[dict(rep_, kind="in_play_wait"), inp])); check("build_quest_fails (v39.12): a site in a bugfixing_phase / patch file must be kind repair / patch", r.returncode != 0 and "bugfixing / patch file" in r.stderr, r.stderr[-200:])
        r = cli(dict(cand, status="rejected", rejection="x", sites=[rep_, S("quests/x.w2phase", 5, "in_play_wait", "candidate", missing="not judged")])); check("build_quest_fails (v39.12): a record is rejected only if EVERY site is rejected (a repair site rejected next to an in-play candidate is refused)", r.returncode != 0 and "not every site is rejected" in r.stderr, r.stderr[-200:])
        r = cli(dict(cand, status="rejected", rejection="x", sites=[rep_, S("quests/x.w2phase", 5, "in_play_wait", "rejected")])); check("build_quest_fails (v39.12): every rejected site needs its own reason", r.returncode != 0 and "own reason" in r.stderr, r.stderr[-200:])
        r = cli(dict(cand, status="rejected", rejection="x", sites=[rep_, S("quests/x.w2phase", 5, "in_play_wait", "rejected", reason="wrong failer")])); w = json.loads(o.read_text()) if o.exists() else {}
        check("build_quest_fails (v39.12): a record whose sites are all rejected, each with a reason, is accepted (and not counted as a candidate)", r.returncode == 0 and w.get("candidates") == 0, r.stderr[-200:])
        r = cli(dict(cand, status="rejected", rejection="x", fail_file="quests/bugfixing_phase.w2phase", fail_block=9, additional_records=[{"file": "cleaver.w2phase", "block": 95}], sites=[rep_])); check("build_quest_fails (v39.12): a pair with additional_records must judge each of them (the Gangs of Novigrad case: the repair site rejected, the in-play wait never judged)", r.returncode != 0 and "sites not judged" in r.stderr and "cleaver.w2phase 95" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [dict(good, sites=None)]})); r = tool_run("--candidates", str(c), "--out", str(o)); check("build_quest_fails (v39.12): a record with no `sites` list is refused", r.returncode != 0 and "no `sites` list" in r.stderr, r.stderr[-200:])
    # --- v39.5: the kinds of the coverage list (`coverage`): validated per kind, unknown kinds refused, gaps and candidates stay out
    cov = {"checklist_entry": "x", "status": "verified_gamefiles", "failed_guid": THREAD, "found_failer": {"guid": UGLY}, "kind": "fact", "effect": "Failure", "fact": "q401_gotten_uma", "op_original": {"func": "CF_GreaterEqual", "value": 1},
           "trigger_phase": "p", "trigger_label": "the talk with somebody", "trigger_short": "somebody", "evidence": [{"file": "a.w2phase", "block": 1, "note": "n"}], "engine_effect": "unconfirmed: x", "gaps": [], "sites": [{"file": "quests/a.w2phase", "block": 1, "kind": "in_play_wait", "status": "verified_gamefiles"}]}
    ok = lambda r: (lambda: T.convert_cov(r, quests))
    def run(f):
        try: return f()
        except SystemExit as e: return str(e)
    check("build_quest_fails: a coverage record of kind 'fact' becomes a link with kind, effect and the stated comparison", isinstance(run(ok(cov)), dict) and run(ok(cov))["kind"] == "fact" and run(ok(cov))["op"] == {"func": "CF_GreaterEqual", "value": 1} and run(ok(cov))["effect"] == "Failure")
    for kind, extra, missing in (("fails_unless_set", {"condition": "done it", "unless_group": "done things"}, "condition"), ("fails_unless_set", {"condition": "done it", "unless_group": "done things"}, "unless_group"), ("choice", {"choice": "to do it", "safe": "do the other thing"}, "choice"), ("choice", {"choice": "to do it", "safe": "do the other thing"}, "safe"), ("journal_status", {"journal": "the journal says so", "fact": None}, "journal"), ("flow", {"flow": "the flow does it", "fact": None}, "flow")):
        good = dict(cov, kind=kind, **extra); bad = {k: v for k, v in good.items() if k != missing}
        check("build_quest_fails: kind %s is accepted with its %s and refused without it" % (kind, missing), isinstance(run(ok(good)), dict) and run(ok(good))["kind"] == kind and isinstance(run(ok(good)).get(missing), str) and "needs %s" % missing in str(run(ok(bad))), [run(ok(bad))])
    for name, rec, word in (("an unknown kind", dict(cov, kind="magic"), "unknown kind"), ("an effect that is neither Failure nor Deactivate", dict(cov, effect="Success"), "effect"), ("a gap", dict(cov, gaps=["x"]), "gaps are not empty"), ("a candidate status", dict(cov, status="candidate"), "status"),
                            ("an unknown GUID", dict(cov, found_failer={"guid": "0" * 32}), "not a quest"), ("no evidence", dict(cov, evidence=[]), "no evidence"), ("a label with a full stop", dict(cov, trigger_label="the talk with somebody."), "full stop"), ("a label that starts with an -ing verb (it must read after 'at')", dict(cov, trigger_label="talking to somebody"), "noun phrase"),
                            ("no short name", dict(cov, trigger_short=""), "trigger_short"), ("an absent value and no premise", dict(cov, op_original={"func": "CF_Greater", "value": None}), "no premise")):
        r = run(ok(rec)); check("build_quest_fails: a coverage record with %s is refused (%s)" % (name, word), isinstance(r, str) and word in r, r)
    # v39.8: no internal name in a string the player reads (underscore ids, 'phase', quest codes, file names); a plain sentence passes
    for field, bad_text in (("advice", "Finish sq202 first."), ("safe_text", "the phase is over"), ("banner_text", "{failer} fails {failed} in mq3012 journal fix"), ("trigger_label", "the q401_gotten_uma wait"), ("trigger_short", "the w2phase block")):
        r = run(ok(dict(cov, **{field: bad_text}))); check("build_quest_fails: %s '%s' is refused (an internal name in player-facing text)" % (field, bad_text), isinstance(r, str) and "internal name" in r, r)
    for bad_text in ("armed once q305_completed is set", "after Q106 Tower is done", "If you have started the phase, finish it", "see sq202_turn_off_security"):
        r = run(lambda: T.convert(dict(pair0, window=bad_text), quests)); check("build_quest_fails: window '%s' is refused (an internal name in player-facing text)" % bad_text, isinstance(r, str) and "internal name" in r, r)
    w = "If you've started part 2 of The Cave of Dreams, finish it before this step."
    r = run(lambda: T.convert(dict(pair0, window=w), quests)); check("build_quest_fails: a plain-English window passes the wording check and is shipped as written", isinstance(r, dict) and r.get("window") == w, r)
    for field, good_text in (("advice", "Finish the Skellige main story and The Last Wish before taking Uma."), ("banner_text", "In the Empress ending, parting with Emhyr fails {failed} if it isn't done.")):
        r = run(ok(dict(cov, **{field: good_text}))); check("build_quest_fails: a plain-English %s passes the wording check and is shipped as written" % field, isinstance(r, dict) and r.get(field) == good_text, r)
    p = run(ok(dict(cov, op_original={"func": "CF_Greater", "value": None}, premise=["absent value reads 0"])))
    check("build_quest_fails: an absent value is shipped as an explicit 0 with the premise written down ('> 0' reading); a default compare with the value 1 becomes CF_Equal; an existence query keeps its query", isinstance(p, dict) and p["op"] == {"func": "CF_Greater", "value": 0} and p["premise"] == "absent value reads 0"
          and run(ok(dict(cov, op_original={"func": None, "value": 1})))["op"] == {"func": "CF_Equal", "value": 1} and run(ok(dict(cov, op_original={"func": None, "value": 1, "query": "QF_DoesExist"})))["op"] == {"func": "CF_GreaterEqual", "value": 1, "query": "QF_DoesExist"}, p)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); c = td / "c.json"; o = td / "o.json"
        c.write_text(json.dumps({"pairs": [], "coverage": [cov, dict(cov, checklist_entry="y", status="candidate", missing="m", sites=[]), dict(cov, checklist_entry="z", status="not_found", sites=[]), dict(cov, checklist_entry="w", status="not_a_fail", sites=[])]})); r = tool_run("--candidates", str(c), "--out", str(o))
        w = json.loads(o.read_text()) if o.exists() else {}
        check("build_quest_fails (CLI): a coverage list with one verified, one candidate, one not_found and one not_a_fail: one link, `candidates` 1 (only the candidate counts)", r.returncode == 0 and len(w.get("links", [])) == 1 and w.get("candidates") == 1 and w["links"][0]["kind"] == "fact", r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [], "coverage": [dict(cov, kind="magic")]})); o.unlink(missing_ok=True); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): an unknown kind stops and writes nothing", r.returncode != 0 and not o.exists() and "unknown kind" in r.stderr, r.stderr[-200:])
        c.write_text(json.dumps({"pairs": [], "coverage": [dict(cov, checklist_entry="a"), dict(cov, checklist_entry="b")]})); o.unlink(missing_ok=True); r = tool_run("--candidates", str(c), "--out", str(o))
        check("build_quest_fails (CLI): two links for the same failer, failed quest and fact stop", r.returncode != 0 and "two links" in r.stderr, r.stderr[-200:])
        many = [dict(cov, checklist_entry="e%d" % i, failed_guid=g, evidence=[{"file": "s.w2phase", "block": 9, "note": "shared"}, {"file": "a.w2phase", "block": i, "note": "own"}]) for i, g in enumerate((THREAD, SQ202, SQ209))]
        c.write_text(json.dumps({"pairs": [], "coverage": many})); o.unlink(missing_ok=True); r = tool_run("--candidates", str(c), "--out", str(o)); w = json.loads(o.read_text()) if o.exists() else {}
        check("build_quest_fails (CLI): an evidence item that three links share is stored once in `ev` and each link holds its index (the others stay in the link)", r.returncode == 0 and w.get("ev") == [{"file": "s.w2phase", "block": 9, "note": "shared"}] and all(l["evidence"][0] == 0 and isinstance(l["evidence"][1], dict) for l in w["links"]), w.get("ev"))
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
    ban = E("[...document.querySelectorAll('.qfbrow p')].map(p=>p.textContent.trim().replace(/\\s+/g,' '))")
    check("%s: Ugly Baby active and Following the Thread NOT started: the banner reads '... fails or closes Following the Thread (Novigrad) at the talk with the stable guard at Crow's Perch. Do Following the Thread first.' (%s)" % (label, ban),
          ban == ["Ugly Baby (Kaer Morhen) fails or closes Following the Thread (Novigrad) at the talk with the stable guard at Crow's Perch. Do Following the Thread first."], ban)
    col = E("[getComputedStyle(document.querySelector('.qfbanner .qfn.red')).color,getComputedStyle(document.querySelector('.qfbanner .qfn.amber')).color,document.querySelector('.qfbanner .qfn.red').textContent,document.querySelector('.qfbanner .qfn.amber').textContent]")
    check("%s: the quest names in the banner are in the red and amber colours (%s)" % (label, col), col == ["rgb(255, 138, 128)", "rgb(240, 180, 82)", "Ugly Baby", "Following the Thread"], col)
    row = E("""(()=>{const w=document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow');return w&&{cls:w.className,chip:w.querySelector('.qfchip').textContent,step:w.querySelector('.qfstep').textContent,aria:w.querySelector('.qsrow').getAttribute('aria-label')}})()""" % UGLY)
    check("%s: List: the failer row is red (qf-fail) with the chip 'Fails 1 quest' and the line naming the step (%s)" % (label, row), row and "qf-fail" in row["cls"] and row["chip"] == "Fails 1 quest"
          and row["step"] == "› The talk with the stable guard at Crow's Perch — Following the Thread fails here" and "fails 1 open quest" in row["aria"], row)
    pg.click('.qsreg[data-r="no"]'); pg.wait_for_timeout(150)
    row = E("""(()=>{const w=document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow');return w&&{cls:w.className,chip:w.querySelector('.qfchip').textContent,step:w.querySelector('.qfstep').textContent,
      sum:w.querySelector('details.qfwhy>summary').textContent,open:w.querySelector('details.qfwhy').open,evopen:w.querySelector('details.qfev').open,h:w.querySelector('details.qfwhy>summary').getBoundingClientRect().height,
      src:w.querySelector('.qfsrc').textContent,chain:w.querySelector('details.qfwhy ol').textContent}})()""" % THREAD)
    check("%s: List: the at-risk row is amber (qf-risk) with the chip 'Do before Ugly Baby', the trigger line and a real <details> 'Why?' (closed, 44 px summary) (%s)" % (label, {k: row[k] for k in ("cls", "chip", "step", "sum", "open")}),
          row and "qf-risk" in row["cls"] and row["chip"] == "Do before Ugly Baby" and row["step"] == "Fails at › The talk with the stable guard at Crow's Perch in Ugly Baby." and row["sum"] == "Why?" and not row["open"] and row["h"] >= 44, row)
    check("%s: 'Why?' holds a plain-language chain, the evidence collapsed inside it and 'Source: remaster game files' (%s)" % (label, row["chain"][:60]), row["chain"].startswith("In Ugly Baby, at the talk with the stable guard at Crow's Perch.") and not re.search(r"[a-z]+\d+_[a-z_]+|phase", row["chain"]) and not row["evopen"] and row["src"] == "Source: remaster game files", row)
    E("document.querySelector('details.qfwhy>summary').click()"); pg.wait_for_timeout(100)
    check("%s: the disclosure opens by click and the evidence list lists the files and blocks (458, 456, 3582)" % label, E("(()=>{const d=document.querySelector('details.qfwhy');d.querySelector('.qfev>summary').click();const t=d.querySelector('.qfev').textContent;return d.open&&['#458','#456','#3582'].every(x=>t.includes(x))})()"))
    # --- Next up
    nx = E("""(()=>{const r={};document.querySelectorAll('#qsNext .qscard').forEach(c=>{r[c.dataset.g]={cls:c.className,txt:c.textContent}});return r})()""")
    check("%s: Next up: a red caution box on the Ugly Baby card and an amber chip on the Following the Thread card (%s)" % (label, [k[:6] for k in nx]), UGLY in nx and THREAD in nx and "qf-fail" in nx[UGLY]["cls"] and "Careful: the talk with the stable guard at Crow's Perch fails Following the Thread." in nx[UGLY]["txt"]
          and "qf-risk" in nx[THREAD]["cls"] and "Do before Ugly Baby" in nx[THREAD]["txt"], nx)
    check("%s: Next up puts the amber quest before the quest that would fail it (%s)" % (label, list(nx)[:2]), list(nx).index(THREAD) < list(nx).index(UGLY))
    # Next up only pushes the amber quest once the failer is active: a fresh player (Ugly Baby not started) keeps the usual Next up, the red and amber marks still show in the List
    pn, _, _ = Q.newpage(b, base, init=seed({})); Q.opened(pn, "no"); Q.until(pn, "!!document.querySelector('.qfrow.qf-risk')"); pn.wait_for_timeout(300)
    fresh = pn.evaluate("[!!document.querySelector('.qfbanner'),!!document.querySelector('.qfrow.qf-risk'),[...document.querySelectorAll('#qsNext .qscard')].map(c=>c.dataset.g).includes('%s')]" % THREAD)
    check("%s: Ugly Baby not started (fresh level-1 state): NO banner (its failer is not active), the amber row is still marked in the List, and Next up does not push Following the Thread forward (%s)" % (label, fresh), fresh == [False, True, False], fresh); pn.close()
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
    check("%s: Timeline: the tooltip of the failer shows the sub-line '› The talk with the stable guard at Crow's Perch — Following the Thread fails here' (%s)" % (label, tip), tip and "› The talk with the stable guard at Crow's Perch — Following the Thread fails here" in tip, tip)
    ratio(pg, '#qsTip .qfsub', "tooltip sub-line", check, label + " contrast")
    pg.mouse.move(2, 2)
    unp = E("""(()=>{const d=document.querySelector('.qsdot[data-g="%s"]');return d?{cls:d.className,aria:d.getAttribute('aria-label')}:null})()""" % THREAD)
    check("%s: Timeline: when Following the Thread has a marker it has the amber ring (qf-risk) and 'at risk: do before Ugly Baby' in its label (%s)" % (label, unp), unp is None or ("qf-risk" in unp["cls"] and "at risk: do before Ugly Baby" in unp["aria"]), unp)
    check("%s: Timeline: the banner is above the views" % label, E("!!document.querySelector('#qfBanner .qfbanner')"))
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


def banner(b, base, check, label):
    """v39.1: the banner of the mockup v3 (started / not started wording, every region tab, names in colour), the region tab dots, the details panel, Go to quest, several links, phone"""
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "active"})); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    tabs = []
    for k in ("wo", "vz", "ve", "no", "sk", "km", "hos", "baw", "oth"):
        pg.click('.qsreg[data-r="%s"]' % k); pg.wait_for_timeout(60); tabs.append(E("!!document.querySelector('#qfBanner .qfbanner')"))
    check("%s: the banner is on every one of the nine region tabs (%s)" % (label, tabs), all(tabs) and len(tabs) == 9, tabs)
    pg.click('.qsreg[data-r="no"]'); pg.wait_for_timeout(100)
    dots = E("""(()=>{const o={};document.querySelectorAll('#qsRegs .qsreg').forEach(t=>{o[t.dataset.r]=[[...t.querySelectorAll('.qfd')].map(d=>d.className.replace('qfd ','')),t.getAttribute('aria-label')]});return o})()""")
    check("%s: region tabs: a red dot on Kaer Morhen (holds the failer) and an amber dot on Novigrad (holds the quest at risk), no dot elsewhere (%s)" % (label, {k: v[0] for k, v in dots.items() if v[0]}),
          dots["km"][0] == ["red"] and dots["no"][0] == ["amber"] and all(not v[0] for k, v in dots.items() if k not in ("km", "no")), dots)
    check("%s: the tab labels say it in words: 'Kaer Morhen, has a quest that fails another, ...' and 'Novigrad, has a quest at risk of failing, ...' (%s)" % (label, [dots["km"][1], dots["no"][1]]),
          (dots["km"][1] or "").startswith("Kaer Morhen, has a quest that fails another, ") and (dots["no"][1] or "").startswith("Novigrad, has a quest at risk of failing, "), dots)
    E("(()=>{QS.byG.get('%s').r='km';qsRenderAll()})()" % THREAD); pg.wait_for_timeout(100)
    both = E("(()=>{const t=document.querySelector('.qsreg[data-r=\"km\"]');return[[...t.querySelectorAll('.qfd')].map(d=>d.className.replace('qfd ','')),t.getAttribute('aria-label')]})()")
    check("%s: a tab holding both gets both dots and both phrases (%s)" % (label, both), both[0] == ["red", "amber"] and "fails another and a quest at risk of failing" in both[1], both)
    E("(()=>{QS.byG.get('%s').r='no';qsRenderAll()})()" % THREAD); pg.wait_for_timeout(100)
    # the details panel
    pn = E("(()=>{const b=document.querySelector('.qfmore'),p=document.getElementById('qfPanel');return[b.textContent,b.getAttribute('aria-expanded'),p.hidden,Math.round(b.getBoundingClientRect().height)]})()")
    check("%s: 'More details' (aria-expanded=false, 44 px) with the panel closed at first (%s)" % (label, pn), pn[0] == "More details" and pn[1] == "false" and pn[2] is True and pn[3] >= 44, pn)
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    pn = E("""(()=>{const b=document.querySelector('.qfmore'),p=document.getElementById('qfPanel'),t=p.textContent.replace(/\\s+/g,' ');return{lab:b.textContent,exp:b.getAttribute('aria-expanded'),vis:!p.hidden&&p.offsetHeight>0,t,
      go:[...p.querySelectorAll('.qfgo')].map(x=>[x.textContent,Math.round(x.getBoundingClientRect().height)]),fin:p.querySelector('.qffin').textContent,fh:Math.round(p.querySelector('.qffin').getBoundingClientRect().height),dd:p.querySelector('details.qfdata').open,
      red:p.querySelector('.qfcard.red .qflab').textContent,amber:p.querySelector('.qfcard.amber .qflab').textContent,n:p.querySelectorAll('.qfdep').length,ev:p.querySelector('details.qfdata li').textContent.length>10}})()""")
    check("%s: 'More details' opens the panel inline: the button reads 'Hide details' (aria-expanded=true), the red card IF YOU DO THIS, AT THIS STEP with the arrow, the amber card THIS QUEST FAILS (%s)" % (label, pn["lab"]), pn["lab"] == "Hide details" and pn["exp"] == "true" and pn["vis"] and pn["red"] == "IF YOU DO THIS"
          and pn["amber"] == "THIS QUEST FAILS" and "AT THIS STEP" in pn["t"] and "AT THIS STEPThe talk with the stable guard at Crow's Perch→" in pn["t"] and pn["t"].index("Collect UMA") > pn["t"].index("Game data (remaster files, full trace)") and "→" in pn["t"], pn)
    check("%s: the cards say 'type · region · level · state' and have a 44 px 'Go to quest ›' each (%s)" % (label, pn["go"]), "Main · Kaer Morhen · level 19 · Active" in pn["t"] and "Secondary · Novigrad · level 11 · Not started" in pn["t"] and pn["go"] == [["Go to quest ›", pn["go"][0][1]]] * 2 and pn["go"][0][1] >= 44, pn["go"])
    check("%s: under the cards: the safe-order sentence (with the not-started line), 'I finished it already' (44 px) and the collapsed 'Game data (remaster files, full trace)' with the evidence (%s)" % (label, pn["fin"]),
          "Safe order: finish Following the Thread, then continue Ugly Baby. If you haven't started it, the game may close it at this step instead." in pn["t"] and pn["fin"] == "I finished it already" and pn["fh"] >= 44 and not pn["dd"]
          and "Game data (remaster files, full trace)" in pn["t"] and pn["ev"] and pn["n"] == 1, pn)
    for sel, what in (('.qfbrow p, .qfn, .qfreg, .qfmore', "banner"), ('.qfcard.red, .qfcard.red .qflab, .qfcard.red .qfbig, .qfcard.red .qfgo', "red card"), ('.qfcard.amber, .qfcard.amber .qflab, .qfcard.amber .qfbig, .qfcard.amber .qfgo', "amber card"),
                      ('.qfstepn, .qfsafe p, .qffin, .qfdata summary, .qfdata li', "panel text")):
        ratio(pg, sel, what, check, label + " contrast")
    pg.click('.qsreg[data-r="km"]'); pg.wait_for_timeout(100)
    check("%s: the panel stays open when the region tab changes (it is a visit-only state) and no storage key was added for it" % label, E("[!document.getElementById('qfPanel').hidden,Object.keys(localStorage).sort().join()]") == [True, "w3p.quests.v1"])
    # Go to quest: region tab switches, the view is kept, the row has focus and its ring pulses
    pg.click('#qfPanel [data-go="%s"]' % THREAD); Q.until(pg, "document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.g==='%s'" % THREAD, 3000)
    g = E("[QS.region,QS.view,document.activeElement.dataset.g,document.activeElement.className.split(' ')[0],!!document.querySelector('.qf-pulse'),document.querySelector('.qsreg.on').dataset.r,!document.getElementById('qfPanel').hidden]")
    check("%s: Go to quest (amber, from the Kaer Morhen tab): the Novigrad tab opens, the List stays, the quest's row has the focus and its ring pulses (%s)" % (label, g), g == ["no", "list", THREAD, "qsrow", True, "no", True], g)
    pg.wait_for_timeout(2300)
    check("%s: the pulse is gone after about 2 s" % label, not E("!!document.querySelector('.qf-pulse')"))
    pg.click("#qsVBand"); pg.click('#qfPanel [data-go="%s"]' % UGLY); Q.until(pg, "document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.g==='%s'" % UGLY, 3000)
    g = E("[QS.region,QS.view,document.activeElement.dataset.g,document.activeElement.className.split(' ')[0],!!document.querySelector('.qf-pulse')]")
    check("%s: Go to quest (red) in the Level band: Kaer Morhen opens, the band stays, the Ugly Baby marker has the focus and pulses (%s)" % (label, g), g == ["km", "band", UGLY, "qsdot", True], g)
    pg.click("#qsVTime"); pg.wait_for_timeout(300); pg.click('#qfPanel [data-go="%s"]' % THREAD); Q.until(pg, "document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.g==='%s'" % THREAD, 3000)
    g = E("[QS.view,document.activeElement.dataset.g,document.activeElement.className.split(' ')[0]]")
    check("%s: Go to quest in the Timeline keeps the Timeline and focuses the marker (%s)" % (label, g), g == ["time", THREAD, "qsdot"], g)
    pg.wait_for_timeout(2300); pg.click("#qsVList"); pg.wait_for_timeout(200)
    pg.emulate_media(reduced_motion="reduce"); pg.click('#qfPanel [data-go="%s"]' % UGLY); Q.until(pg, "!!document.querySelector('.qf-pulse')", 3000)
    rm = E("(()=>{const e=document.querySelector('.qf-pulse');const c=getComputedStyle(e);return[c.animationName,c.outlineStyle,c.outlineWidth]})()")
    check("%s: prefers-reduced-motion: no animation, a plain outline instead (%s)" % (label, rm), rm[0] == "none" and rm[1] == "solid" and rm[2] == "3px", rm)
    pg.emulate_media(reduced_motion="no-preference")
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    check("%s: 'Hide details' closes the panel again" % label, E("[document.getElementById('qfPanel').hidden,document.querySelector('.qfmore').textContent,document.querySelector('.qfmore').getAttribute('aria-expanded')]") == [True, "More details", "false"])
    pg.click(".qfmore"); pg.click(".qffin"); pg.wait_for_timeout(200)
    fin = E("[QS.store.manual['%s'],document.querySelectorAll('.qfbanner,.qf-risk,.qf-fail').length]" % THREAD)
    check("%s: 'I finished it already' sets Following the Thread to done and the warnings go (%s)" % (label, fin), fin == ["done", 0], fin)
    # started: the failed quest is active -> no 'or closes'
    pg.close()
    pg, errs, reqs = Q.newpage(b, base, init=seed({UGLY: "active", THREAD: "active"})); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("document.querySelector('.qfbanner p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: Following the Thread already started: no 'or closes' (%s)" % (label, ban), ban == "Ugly Baby (Kaer Morhen) fails Following the Thread (Novigrad) at the talk with the stable guard at Crow's Perch. Do Following the Thread first.", ban)
    # several links: one summary line, the panel lists them all
    E("""(()=>{const x=QS.data.quests.find(q=>q.id==='Q103 The Race'),d=JSON.parse(JSON.stringify(W3DATA.QUEST_FAILS)),l=d.links.find(l=>l.failer_guid==='%s'&&l.failed_guid==='%s');d.links=[l,Object.assign({},l,{failed_guid:x.g,fact:'other_fact'})];QF.init(d);qsRenderAll()})()""" % (UGLY, THREAD)); pg.wait_for_timeout(200)
    ml = E("[document.querySelector('.qfbanner p').textContent.trim(),document.querySelectorAll('#qfPanel .qfdep').length,document.querySelectorAll('#qsRegs .qfd.amber').length>0]")
    check("%s: two links: one sentence naming the failer and both quests at risk (v39.9) and the panel holds a block for each (%s)" % (label, ml), ml[0] == "Continuing Ugly Baby (Kaer Morhen) fails or closes Ciri's Story: The Race and Following the Thread." and ml[1] == 2, ml)
    pg.close()
    pg, errs, reqs = Q.newpage(b, base, w=390, h=844, mobile=True, init=seed({UGLY: "active"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfbanner')"); pg.tap(".qfmore"); pg.wait_for_timeout(200)
    ph = E("""(()=>{const r=e=>Math.round(e.getBoundingClientRect().height);return{sx:document.documentElement.scrollWidth-innerWidth,w:document.querySelector('#qfBanner').getBoundingClientRect().width<=innerWidth,more:r(document.querySelector('.qfmore')),go:[...document.querySelectorAll('.qfgo')].map(r),fin:r(document.querySelector('.qffin')),sum:r(document.querySelector('.qfdata summary')),cards:document.querySelectorAll('.qfcard').length}})()""")
    check("%s: phone (390 px) with the panel open: no sideways scroll, the cards stack, More details / Go to quest / I finished it already / the data summary are 44 px targets (%s)" % (label, ph), ph["sx"] <= 1 and ph["w"] and ph["more"] >= 44 and all(h >= 44 for h in ph["go"]) and ph["fin"] >= 44 and ph["sum"] >= 44 and ph["cards"] == 2, ph)
    pg.close()


ROW = '.qfrowx[data-k="%s%s"]' % (UGLY, THREAD)


def failures(b, base, check, label):
    """v39.2: the Quest failures tab (mockup v4): the button and its count, every link whatever the region or level, the order, the four statuses, the hide filter, Details, the K footer, phone"""
    cands = json.loads((ROOT / "data" / "QUEST_FAILS.json").read_text(encoding="utf-8"))["candidates"]
    pg, errs, reqs = Q.newpage(b, base, init=seed({}, quiet=False)); E = pg.evaluate; Q.opened(pg, "wo"); pg.fill("#lvl", "1"); E("pointsChanged()"); pg.wait_for_timeout(200)
    btn = E("(()=>{const x=document.getElementById('qsVFails'),l=document.getElementById('qsVList');return{t:x.textContent,hid:x.hidden,txt:x.innerText,after:l.nextElementSibling===x,h:Math.round(x.getBoundingClientRect().height)}})()")
    check("%s: a fourth view button after List reads 'QUEST FAILURES · 44' (the number of verified links), 44 px (%s)" % (label, btn), not btn["hid"] and btn["t"] == "Quest failures · 44" and btn["txt"] == "QUEST FAILURES · 44" and btn["after"] and btn["h"] >= 40, btn)
    ratio(pg, "#qsVFails", "Quest failures button (not pressed)", check, label + " contrast")
    pg.click("#qsVFails"); pg.wait_for_timeout(250)
    ratio(pg, "#qsVFails", "Quest failures button (pressed)", check, label + " contrast")
    st = E("[document.getElementById('qsVFails').getAttribute('aria-pressed'),document.getElementById('qsVList').getAttribute('aria-pressed'),localStorage.getItem('w3p.quests.view'),QS.view,document.querySelectorAll('.qfrowx').length,getComputedStyle(document.querySelector('.qsregnav')).display]")
    check("%s: the button stores its view in w3p.quests.view as 'fails', the region tabs are out of the way and the 44 links are listed (%s)" % (label, st), st[:5] == ["true", "false", "fails", "fails", 44] and st[5] == "none", st)
    row = E("""(()=>{const r=document.querySelector(__ROW),t=e=>r.querySelector(e).innerText.replace(/\\s+/g,' ').trim();return{h:document.querySelector('.qfht h2').textContent,p:document.querySelector('.qfht p').textContent,red:t('.qfblk.red'),mid:t('.qfblk.mid'),amber:t('.qfblk.amber'),st:t('.qfst'),stc:r.querySelector('.qfst').className,det:t('.qfdetb'),hide:document.querySelector('.qfhide').textContent.trim(),cb:document.getElementById('qfHide').checked}})()""")
    check("%s: level 1, nothing started: the row is there (the tab ignores region and level); header text and the four blocks (%s)" % (label, row["red"]), row["h"] == "Every quest that fails another" and row["p"] == "All regions, whatever your level or progress, sorted by the level of the quest that causes the fail. Only links confirmed from the remaster's game files."
          and row["red"] == "IF YOU DO Ugly Baby Main · Kaer Morhen · level 19" and row["mid"] == "AT THIS STEP The talk with the stable guard at Crow's Perch" and row["amber"] == "THIS FAILS Following the Thread Secondary · Novigrad"
          and row["st"] == "Open · plan for it" and "open" in row["stc"] and row["det"] == "Details ›" and row["hide"] == "Hide ones I've dealt with" and not row["cb"], row)
    for sel, what in (('.qfht h2, .qfht p, .qfhide', "header"), ('.qfblk.red, .qfblk.red .qflab, .qfblk.red .qfbig', "red block"), ('.qfblk.amber, .qfblk.amber .qflab, .qfblk.amber .qfbig', "amber block"), ('.qfblk.mid .qfstepn, .qfblk.mid .qflab, .qfdetb', "step block and Details"),
                      ('.qfst', "status chip"), ('.qfnote, .qfnote b', "footnotes")):
        ratio(pg, sel, what, check, label + " contrast")
    E("QS.region='sk';qsRenderView()"); pg.wait_for_timeout(100)
    check("%s: the region tab makes no difference (Skellige selected: the row is still listed)" % label, E("document.querySelectorAll('.qfrowx').length") == 44)
    # order across regions: failer level, then name (synthetic links, drawn from real quests of other regions and levels)
    order = E("""(()=>{const Q=QS.data.quests.filter(q=>q.lv!=null&&q.g!=='%s'&&q.g!=='%s'),by={};Q.forEach(q=>{(by[q.lv]=by[q.lv]||[]).push(q)});
      const lv=Object.keys(by).map(Number).sort((a,b)=>a-b).find(l=>l<19&&new Set(by[l].map(q=>q.r)).size>1&&by[l].length>=2);const same=by[lv].sort((a,b)=>a.n.localeCompare(b.n)),hi=Q.find(q=>q.lv>30&&q.r!==same[0].r),d=JSON.parse(JSON.stringify(W3DATA.QUEST_FAILS)),l0=d.links.find(l=>l.failer_guid==='%s'&&l.failed_guid==='%s');
      const mk=(q,i)=>Object.assign({},l0,{failer_guid:q.g,fact:'f'+i});d.links=[mk(hi,1),l0,mk(same[1],2),mk(same[0],3)];QF.init(d);qsRenderView();
      return{want:[same[0].n,same[1].n,'Ugly Baby',hi.n],got:[...document.querySelectorAll('.qfrowx .qfblk.red .qfbig')].map(e=>e.textContent),lvs:[...document.querySelectorAll('.qfrowx .qfblk.red .qfmeta')].map(e=>e.textContent),btn:document.getElementById('qsVFails').textContent}})()""" % (UGLY, THREAD, UGLY, THREAD))
    check("%s: several links from different regions are sorted by the failer's level, then by name (%s)" % (label, order["lvs"]), order["got"] == order["want"] and order["btn"] == "Quest failures · 4", order)
    pg.close()
    # statuses and the hide filter
    for name, man, chip, cls, vis in (("Open", {}, "Open · plan for it", "open", True), ("Safe (the failed quest is done)", {THREAD: "done"}, "Safe · you finished it", "safe", False), ("Failed", {THREAD: "failed"}, "Failed", "failed", False),
                                     ("Missed (the causing quest is done)", {UGLY: "done"}, "Missed · the causing quest is done", "missed", False), ("Safe (the causing quest failed)", {UGLY: "failed"}, "Safe · the causing quest failed", "safe", False)):
        pg, errs, reqs = Q.newpage(b, base, init=seed(man)); E = pg.evaluate; Q.opened(pg); pg.click("#qsVFails"); pg.wait_for_timeout(200)
        got = E("[document.querySelector(__ROW+' .qfst').textContent,document.querySelector(__ROW+' .qfst').className.split(' ')[1],document.querySelectorAll('.qfrowx').length]"); keys = E("Object.keys(localStorage).sort().join()")
        pg.click("#qfHide"); pg.wait_for_timeout(150)
        n = E("[document.querySelectorAll('.qfrowx').length,document.getElementById('qfHide').checked,!!document.querySelector('.qfrowsx .qfnote'),document.activeElement.id]"); keys2 = E("Object.keys(localStorage).sort().join()")
        check("%s: status %s: the chip says '%s'; 'Hide ones I've dealt with' %s the row (%s), visit-only: no storage key added" % (label, name, chip, "keeps" if vis else "hides", n), got == [chip, cls, 44] and n[0] == (1 if vis else 0) and n[1] and n[3] == "qfHide" and (vis or n[2]) and keys == keys2, [got, n, keys, keys2])
        pg.close()
    # Details opens the dependency panel; Go to quest from it leaves the failures view for the List
    pg, errs, reqs = Q.newpage(b, base, init=seed({})); E = pg.evaluate; Q.opened(pg); pg.click("#qsVFails"); pg.wait_for_timeout(200)
    h = E("[document.querySelector(__ROW+' .qfrdep').hidden,document.querySelector(__ROW+' .qfdetb').getAttribute('aria-expanded'),Math.round(document.querySelector(__ROW+' .qfdetb').getBoundingClientRect().height)]")
    pg.click(ROW + " .qfdetb"); pg.wait_for_timeout(100)
    d = E("""(()=>{const p=document.querySelector(__ROW+' .qfrdep'),t=p.textContent.replace(/\\s+/g,' ');return{vis:!p.hidden&&p.offsetHeight>0,exp:document.querySelector(__ROW+' .qfdetb').getAttribute('aria-expanded'),t,go:p.querySelectorAll('.qfgo').length,fin:!!p.querySelector('.qffin'),data:!!p.querySelector('details.qfdata')&&!p.querySelector('details.qfdata').open}})()""")
    check("%s: Details › opens the dependency panel of that link (IF YOU DO THIS, AT THIS STEP, THIS QUEST FAILS, two Go to quest ›, I finished it already, the collapsed game data) (%s)" % (label, d["exp"]), h[:2] == [True, "false"] and h[2] >= 44 and d["vis"] and d["exp"] == "true" and d["go"] == 2 and d["fin"] and d["data"]
          and all(x in d["t"] for x in ("IF YOU DO THIS", "AT THIS STEP", "THIS QUEST FAILS", "Safe order: finish Following the Thread")), [h, d])
    pg.click(ROW + " .qfdetb"); check("%s: Details › closes it again" % label, E("document.querySelector(__ROW+' .qfrdep').hidden") is True)
    pg.click(ROW + " .qfdetb"); pg.click(ROW + ' .qfrdep [data-go="%s"]' % THREAD); Q.until(pg, "document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.g==='%s'" % THREAD, 3000)
    g = E("[QS.view,QS.region,document.activeElement.className.split(' ')[0],localStorage.getItem('w3p.quests.view')]")
    check("%s: Go to quest from the panel: the failures view has no markers, so the List opens on Novigrad with the quest's row focused (%s)" % (label, g), g == ["list", "no", "qsrow", "list"], g)
    pg.click("#qsVFails"); pg.wait_for_timeout(200); pg.click(ROW + " .qffin"); pg.wait_for_timeout(200)
    check("%s: 'I finished it already' in the panel sets the failed quest to done: the row turns Safe" % label, E("[QS.store.manual['%s'],document.querySelector(__ROW+' .qfst').textContent]" % THREAD) == ["done", "Safe · you finished it"])
    pg.reload(); Q.until(pg, Q.READY); Q.opened(pg); pg.wait_for_timeout(300)
    check("%s: the view is remembered: after a reload Quest failures is open again" % label, E("[QS.view,document.getElementById('qsVFails').getAttribute('aria-pressed'),!!document.querySelector(__ROW)]") == ["fails", "true", True])
    pg.close()
    # the footer
    pg, errs, reqs = Q.newpage(b, base, init=seed({}) + ";localStorage.setItem('w3p.quests.view','fails')"); E = pg.evaluate; Q.opened(pg); pg.wait_for_timeout(300)
    f = E("[QS.view,!!document.querySelector(__ROW),(document.querySelector('.qfcand')||{}).textContent]")
    check("%s: view 'fails' stored: it opens on Quest failures; the footer says '%d more possible fail links found in the game files are still being checked.' (the number comes from the data) (%s)" % (label, cands, f), f == ["fails", True, "%d more possible fail links found in the game files are still being checked." % cands], f)
    E("(()=>{const d=JSON.parse(JSON.stringify(W3DATA.QUEST_FAILS));d.candidates=0;QF.init(d);qsRenderView()})()"); pg.wait_for_timeout(100)
    check("%s: with 0 candidates the footer line is hidden" % label, E("[!!document.querySelector('.qfcand'),!!document.querySelector(__ROW)]") == [False, True])
    pg.close()
    # phone
    pg, errs, reqs = Q.newpage(b, base, w=390, h=844, mobile=True, init=seed({})); E = pg.evaluate; Q.opened(pg); pg.tap("#qsVFails"); pg.wait_for_timeout(300); pg.tap(".qfdetb"); pg.wait_for_timeout(150)
    ph = E("""(()=>{const R=e=>e.getBoundingClientRect(),bl=[...document.querySelector(__ROW+' .qfr1').children].map(e=>R(e)),vb=[...document.querySelectorAll('.qsviews .qsv')].filter(x=>!x.hidden).map(e=>Math.round(R(e).top)),row=R(document.querySelector(__ROW));
      return{sx:document.documentElement.scrollWidth-innerWidth,stack:bl.length===4&&bl.every((r,i)=>i===0||r.top>=bl[i-1].bottom-1)&&bl.every(r=>Math.abs(r.left-bl[0].left)<2),inside:row.right<=innerWidth+1,wrap:new Set(vb).size>1,det:Math.round(R(document.querySelector(__ROW+' .qfdetb')).height),hide:Math.round(R(document.querySelector('.qfhide')).height)}})()""")
    check("%s: phone (390 px): the four blocks stack, the view-button row wraps, no sideways scroll, Details and the filter are 44 px (%s)" % (label, ph), ph["sx"] <= 1 and ph["stack"] and ph["inside"] and ph["wrap"] and ph["det"] >= 44 and ph["hide"] >= 44, ph)
    check("%s: no page error" % label, not errs, errs[:1])
    pg.close()


def multi(b, base, check, label):
    """v39.4: the real links together (three of them: Ugly Baby fails Following the Thread and The Last Wish, King's Gambit fails The Cave of Dreams): banner summary, the panel, tab dots, the order of Quest failures, a single Skellige link, and a quest that fails one quest while another would fail it"""
    pg, errs, _ = Q.newpage(b, base, init=seed({UGLY: "active", Q206: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')"); E(ONLY3); pg.wait_for_timeout(250)
    t = E("document.querySelector('.qfbrow p').textContent.trim()")
    check("%s: three links live: one sentence per failer, in the order of their levels (v39.9) (%s)" % (label, t), t == "Continuing King's Gambit (Skellige) fails or closes The Cave of Dreams. Continuing Ugly Baby (Kaer Morhen) fails or closes Following the Thread and The Last Wish.", t)
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    pn = E("""(()=>{const p=document.getElementById('qfPanel');return{n:p.querySelectorAll('.qfdep').length,fails:[...p.querySelectorAll('.qfdep .qfcard.amber .qfbig')].map(e=>e.textContent).sort(),by:[...p.querySelectorAll('.qfdep .qfcard.red .qfbig')].map(e=>e.textContent),t:p.innerText.replace(/\\s+/g,' '),pub:(()=>{const c=p.cloneNode(true);c.querySelectorAll('details.qfdata').forEach(x=>x.remove());return c.textContent.replace(/\\s+/g,' ')})()}})()""")
    check("%s: the panel lists every link (%s)" % (label, pn["fails"]), pn["n"] == 3 and pn["fails"] == ["Following the Thread", "The Cave of Dreams", "The Last Wish"] and sorted(pn["by"]) == ["King's Gambit", "Ugly Baby", "Ugly Baby"], pn)
    check("%s: the Cave of Dreams block names the step and its time limit; the Last Wish block its limit (%s)" % (label, "Kaer Trolde"), "AT THIS STEP The gate of Kaer Trolde Keep, on the way to report to Crach →" in pn["t"] and "AT THIS STEP The talk with the stable guard at Crow's Perch →" in pn["t"]
          and "If you've started part 2 of The Cave of Dreams, finish it before this step." in pn["t"] and "Finish the Skellige main story and The Last Wish before taking Uma. If you take Uma first, The Last Wish fails as soon as it starts." in pn["t"]
          and "Safe order: finish The Last Wish" not in pn["t"] and not re.search(r"[A-Za-z]+\d*_[A-Za-z_]+|phase|\b(?:sq|q|mq)\d+", pn["pub"]), pn["t"][:200])
    dots = E("""(()=>{const o={};document.querySelectorAll('#qsRegs .qsreg').forEach(t=>{o[t.dataset.r]=[[...t.querySelectorAll('.qfd')].map(d=>d.className.replace('qfd ','')),t.getAttribute('aria-label')]});return o})()""")
    check("%s: region tabs with the real data: Kaer Morhen red, Novigrad amber, Skellige both (the failer King's Gambit and the at-risk Last Wish and Cave of Dreams), nothing else (%s)" % (label, {k: v[0] for k, v in dots.items() if v[0]}),
          dots["km"][0] == ["red"] and dots["no"][0] == ["amber"] and dots["sk"][0] == ["red", "amber"] and all(not v[0] for k, v in dots.items() if k not in ("km", "no", "sk"))
          and dots["sk"][1].startswith("Skellige, has a quest that fails another and a quest at risk of failing"), dots)
    pg.click("#qsVFails"); pg.wait_for_timeout(250)
    ordr = E("[...document.querySelectorAll('.qfrowx')].map(r=>r.querySelector('.qfblk.red .qfbig').textContent+' > '+r.querySelector('.qfblk.amber .qfbig').textContent)")
    check("%s: Quest failures lists the three, sorted by the failer's level (King's Gambit 18, Ugly Baby 19) then the failed quest's name (%s)" % (label, ordr), ordr == ["King's Gambit > The Cave of Dreams", "Ugly Baby > Following the Thread", "Ugly Baby > The Last Wish"] and E("document.getElementById('qsVFails').textContent") == "Quest failures · 3", ordr)
    pg.close()
    # one Skellige link
    pg, errs, _ = Q.newpage(b, base, init=seed({UGLY: "done", Q206: "active", SQ202: "done"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "sk"); Q.until(pg, "!!document.querySelector('.qfbanner')"); E(ONLY3); pg.wait_for_timeout(250)
    t = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: one link left (King's Gambit): %s" % (label, t), t == "King's Gambit fails or closes The Cave of Dreams at the gate of Kaer Trolde Keep, on the way to report to Crach. Do The Cave of Dreams first.", t)
    pr = E("[...document.querySelectorAll('.qfprompt p')].map(p=>p.textContent)")
    check("%s: Ugly Baby done with Following the Thread still open: its prompt shows (%s)" % (label, pr), pr == ["Ugly Baby is done. Following the Thread would have failed along the way."], pr)
    pg.close()
    # a quest that fails one quest and is at risk from another (synthetic second link: The Last Wish fails Heroesmead)
    pg, errs, _ = Q.newpage(b, base, init=seed({UGLY: "active", Q206: "done"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "sk"); Q.until(pg, "!!document.querySelector('.qfbanner')"); E(ONLY3); pg.wait_for_timeout(250)
    E("""(()=>{const x=QS.data.quests.find(q=>q.id==='Q208 Heroesmead'),d=JSON.parse(JSON.stringify(W3DATA.QUEST_FAILS)),l=d.links.find(l=>l.failed_guid==='%s'&&l.failer_guid==='%s'),keep=d.links.filter(l=>%s.includes(l.failer_guid+l.failed_guid));d.links=keep.concat([Object.assign({},l,{failer_guid:'%s',failed_guid:x.g,fact:'synthetic',trigger_label:'Finish The Last Wish',trigger_short:'ending'})]);QF.init(d);qsRenderAll()})()""" % (SQ202, UGLY, json.dumps(sorted(LEGACY)), SQ202)); pg.wait_for_timeout(250)
    row = E("""(()=>{const w=document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow');return w&&{cls:w.className,chips:[...w.querySelectorAll('.qfchip')].map(c=>c.textContent),aria:w.querySelector('.qsrow').getAttribute('aria-label')}})()""" % SQ202)
    check("%s: a quest that fails one quest and is at risk from another shows both: red and amber classes, both chips, both phrases in its label (%s)" % (label, row), row and "qf-fail" in row["cls"] and "qf-risk" in row["cls"] and row["chips"] == ["Fails 1 quest", "Do before Ugly Baby"] and "fails 1 open quest" in row["aria"] and "at risk: do before Ugly Baby" in row["aria"], row)
    ratio(pg, '.qfrow.qf-fail.qf-risk, .qfrow.qf-fail.qf-risk .qsrn2 b, .qfrow.qf-fail.qf-risk>.qfextra', "red-and-amber row", check, label + " contrast")
    nx = E("""(()=>{const c=document.querySelector('#qsNext .qscard[data-g="%s"]');return c&&{cls:c.className,t:c.textContent}})()""" % SQ202)
    check("%s: its Next up card has the red class, the caution box and the amber chip (%s)" % (label, nx and nx["cls"]), nx and "qf-fail" in nx["cls"] and "qf-risk" in nx["cls"] and "Careful: Finish The Last Wish fails Q208" not in nx["t"] and "Careful:" in nx["t"] and "Do before Ugly Baby" in nx["t"], nx)
    pg.click("#qsVBand"); pg.wait_for_timeout(250)
    dot = E("""(()=>{const d=document.querySelector('.qsdot[data-g="%s"]');return d&&{cls:d.className,aria:d.getAttribute('aria-label')}})()""" % SQ202)
    check("%s: its Level band dot has both rings (%s)" % (label, dot), dot and "qf-fail" in dot["cls"] and "qf-risk" in dot["cls"] and "fails 1 open quest" in dot["aria"] and "at risk: do before Ugly Baby" in dot["aria"], dot)
    E("qsSelect('%s')" % SQ202); pg.wait_for_timeout(250)
    det = E("[document.querySelectorAll('#qsDetail .qfbox.red').length,document.querySelectorAll('#qsDetail .qfbox.amber').length]")
    check("%s: its detail panel has the red box and the amber box (%s)" % (label, det), det == [1, 1], det)
    check("%s: no page error" % label, not errs, errs[:1])
    pg.close()


ISLE = "5ce1c21a55b9cb4bb99706bfd11fa286"


def _q():
    qs = {q["g"]: q for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    return qs, {q["n"]: q["g"] for q in qs.values()}


def kinds(b, base, check, label):
    """v39.5: the five kinds, the grouping of the Isle of Mists prompt (banner, panel, Quest failures tab), a choice that never says 'do it first', 39 rows on a phone"""
    qs, nm = _q()
    isle_failed = sorted(l["failed_guid"] for l in LINKS if l["failer_guid"] == ISLE)
    VELEN, SQ101, Q109 = nm["Brothers In Arms: Velen"], nm["A Favor for a Friend"], nm["For the Advancement of Learning"]
    # --- the Isle of Mists group: one banner line, the list in the panel, one header in the tab
    pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", ISLE: "active"}, keep=isle_failed)); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("[...document.querySelectorAll('.qfbrow p')].map(p=>p.textContent.trim().replace(/\\s+/g,' '))")
    check("%s: the Isle of Mists: ONE banner sentence naming the first two quests by level and counting the rest, 'Continuing The Isle of Mists (Kaer Morhen) fails or closes Ciri's Room, A Favor for a Friend and 10 more, and 4 more unless you've gathered allies.' (the three choices are not on it: their failers are not active; the Isle of Mists is active) (%s)" % (label, ban), ban == ["Continuing The Isle of Mists (Kaer Morhen) fails or closes Ciri's Room, A Favor for a Friend and 10 more, and 4 more unless you've gathered allies."], ban)
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    pn = E("""(()=>{const p=document.getElementById('qfPanel'),g=p.querySelector('.qfdepg');return{groups:p.querySelectorAll('.qfdepg').length,singles:[...p.querySelectorAll('.qfdep:not(.qfdepg)')].map(d=>d.querySelector('.qfcard.red .qflab').textContent),li:g.querySelectorAll('.qfgl li').length,main:g.querySelectorAll('.qfgl:not(.qfgu) li').length,sub:g.querySelectorAll('.qfgu li').length,
      lab:g.innerText.replace(/\\s+/g,' '),names:[...g.querySelectorAll('.qfgl li b')].map(e=>e.textContent),unl:[...g.querySelectorAll('.qfunl')].map(e=>e.textContent),go:[...g.querySelectorAll('.qfgl .qfgo')].length,fin:[...g.querySelectorAll('.qfgl .qffin')].length}})()""")
    want = sorted(qs[g]["n"] for g in isle_failed)
    check("%s: the panel lists the group once (the failer card, the step, THESE 12 QUESTS FAIL, then 'Fail unless done first (4)', one line per quest with Go to quest and I finished it already), and no choice blocks (their failers are not active) (%s)" % (label, pn["lab"][:80]),
          pn["groups"] == 1 and pn["li"] == 16 and sorted(pn["names"]) == want and pn["go"] == 16 and pn["fin"] == 16 and pn["singles"] == [] and "THESE 12 QUESTS FAIL" in pn["lab"] and "Fail unless done first (4)" in pn["lab"] and pn["main"] == 12 and pn["sub"] == 4 and pn["lab"].index("THESE 12 QUESTS FAIL") < pn["lab"].index("Fail unless done first (4)") and "The portal prompt in The Isle of Mists" in pn["lab"]
          and "Safe order: finish these quests, then continue The Isle of Mists." in pn["lab"], pn)
    check("%s: the four Brothers In Arms lines start with the full quest name and give their own condition ('Brothers In Arms: Skellige fails at the portal prompt in The Isle of Mists unless you've recruited allies in Skellige first.', Novigrad, Nilfgaard 'got Emhyr's help in Nilfgaard', Velen 'recruited Keira in Velen') (%s)" % (label, pn["unl"]), sorted(pn["unl"]) == sorted("%s fails at the portal prompt in The Isle of Mists unless you've %s first." % (n_, c) for n_, c in (("Brothers In Arms: Skellige", "recruited allies in Skellige"), ("Brothers In Arms: Novigrad", "recruited allies in Novigrad"), ("Brothers In Arms: Nilfgaard", "got Emhyr's help in Nilfgaard"), ("Brothers In Arms: Velen", "recruited Keira in Velen"))), pn["unl"])
    ratio(pg, '.qfdepg, .qfdepg .qfgl li, .qfdepg .qfgl li b, .qfdepg .qfunl, .qfdepg .qfmeta', "grouped panel", check, label + " contrast")
    row = E("""(()=>{const w=document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow');return w&&{chip:w.querySelector('.qfchip').textContent,steps:[...w.querySelectorAll('.qfstep')].map(x=>x.textContent)}})()""" % ISLE)
    check("%s: the Isle of Mists row: the chip 'Fails 16 quests' and ONE step line, not sixteen (split in the two parts) (%s)" % (label, row), row and row["chip"] == "Fails 16 quests" and row["steps"] == ["› Accepting the portal prompt in The Isle of Mists — 12 open quests fail here, and 4 more unless you've gathered allies"], row)
    pg.click("#qsVFails"); pg.wait_for_timeout(250)
    tb = E("""(()=>{const gs=[...document.querySelectorAll('.qfgrp')];return{n:document.querySelectorAll('.qfrowx').length,heads:gs.map(g=>g.querySelector('.qfgh').innerText.replace(/\\s+/g,' ')),rows:gs.map(g=>g.querySelectorAll('.qfrowx').length),
      isle:[...gs[1].querySelectorAll('.qfrowx .qfblk.amber .qfbig')].map(e=>e.textContent),sub:gs[1].querySelectorAll('.qfgsub').length,subtxt:(gs[1].querySelector('.qfgsub')||{}).textContent,subpos:[...gs[1].children].findIndex(c=>c.classList.contains('qfgsub')),lv:[...gs[1].querySelectorAll('.qfrowx .qfblk.amber .qfmeta')].map(e=>e.textContent.split('level ')[1]),choice:[...document.querySelectorAll('.qfrowx:not(.qfgrp .qfrowx) .qfblk.red .qflab')].map(e=>e.textContent).filter(t=>t==='IF YOU CHOOSE').length,
      unl:gs[1].querySelectorAll('.qfblk.mid .qflab').length,sent:[...gs[1].querySelectorAll('.qfblk.mid .qfunl')].map(e=>e.textContent)}})()""")
    lv = lambda g: qs[g]["lv"] if qs[g]["lv"] is not None else 1e9
    unl = {l["failed_guid"] for l in LINKS if l["kind"] == "fails_unless_set"}
    exp = [qs[g]["n"] for g in sorted((g for g in isle_failed if g not in unl), key=lambda g: (lv(g), qs[g]["n"]))] + [qs[g]["n"] for g in sorted(unl, key=lambda g: (lv(g), qs[g]["n"]))]
    check("%s: Quest failures: 44 rows, four shared-trigger headers (White Orchard 3, the Isle of Mists 16, Battle Preparations 4 since v39.12, On Thin Ice 4), each group's rows sorted by the failed quest's level then name (the Isle of Mists: 12 rows, then the sub-group 'Fail unless done first' with its 4); three choice rows stand on their own (%s)" % (label, tb["heads"]),
          tb["n"] == 44 and len(tb["heads"]) == 4 and tb["rows"] == [3, 16, 4, 4] and "The Incident at White Orchard" in tb["heads"][0] and "3 quests fail here" in tb["heads"][0] and "The portal prompt in The Isle of Mists" in tb["heads"][1] and "12 quests fail here, 4 more unless done first" in tb["heads"][1] and tb["sub"] == 1 and tb["subtxt"] == "Fail unless done first" and tb["subpos"] == 1 + 12
          and "The start of Act III in Skellige" in tb["heads"][2] and tb["isle"] == exp and tb["choice"] == 3 and tb["unl"] == 4, tb)
    check("%s: Quest failures: the four Brothers In Arms rows of the sub-group carry the full sentence, starting with the quest name (%s)" % (label, tb["sent"]), sorted(tb["sent"]) == sorted("%s fails at the portal prompt in The Isle of Mists unless you've %s first." % (n_, c) for n_, c in (("Brothers In Arms: Skellige", "recruited allies in Skellige"), ("Brothers In Arms: Novigrad", "recruited allies in Novigrad"), ("Brothers In Arms: Nilfgaard", "got Emhyr's help in Nilfgaard"), ("Brothers In Arms: Velen", "recruited Keira in Velen"))), tb["sent"])
    ratio(pg, '.qfgh, .qfgh .qfbig, .qfgh .qfmeta, .qfgh .qfstepn, .qfgn', "group header", check, label + " contrast")
    ratio(pg, '.qfgrp .qfblk.amber, .qfgrp .qfblk.amber .qfbig, .qfgrp .qfblk.amber .qfmeta, .qfgrp .qfunl', "group rows", check, label + " contrast")
    check("%s: no page error" % label, not errs, errs[:1])
    pg.close()
    # --- v39.8: banner scope. A fresh level-1 state has no banner; with Ugly Baby active the banner and its panel show Ugly Baby's two links and nothing else; every link stays in the Quest failures tab
    pg, errs, _ = Q.newpage(b, base, init=seed({}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km"); pg.wait_for_timeout(600)
    nb = E("[document.querySelectorAll('.qfbanner').length,document.querySelectorAll('#qfPanel .qfdep').length]"); E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(200)
    check("%s: fresh level-1 state: no banner and no panel, but the Quest failures tab still lists all 44 links (%s)" % (label, nb), nb == [0, 0] and E("document.querySelectorAll('.qfrowx').length") == 44, nb)
    pg.close()
    pg, errs, _ = Q.newpage(b, base, init=seed({UGLY: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    sc = E("[...document.querySelectorAll('#qfPanel .qfdep')].map(d=>d.getAttribute('aria-label'))"); E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(200)
    check("%s: Ugly Baby active: the banner panel holds exactly Ugly Baby's two links (Following the Thread, The Last Wish), nothing else; the tab still lists all 44 (%s)" % (label, sc), sorted(sc) == ["Ugly Baby fails Following the Thread", "Ugly Baby fails The Last Wish"] and E("document.querySelectorAll('.qfrowx').length") == 44, sc)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    # --- phone: about 44 rows
    pg, errs, _ = Q.newpage(b, base, w=390, h=844, mobile=True, init=seed({}, quiet=False)); E = pg.evaluate; Q.opened(pg); pg.tap("#qsVFails"); pg.wait_for_timeout(300)
    ph = E("""(()=>{const R=e=>e.getBoundingClientRect(),rows=[...document.querySelectorAll('.qfrowx')];return{n:rows.length,sx:document.documentElement.scrollWidth-innerWidth,out:rows.filter(r=>R(r).right>innerWidth+1).length,det:Math.min(...[...document.querySelectorAll('.qfdetb')].map(e=>Math.round(R(e).height))),
      heads:[...document.querySelectorAll('.qfgh')].every(h=>R(h).right<=innerWidth+1),h:Math.round(document.querySelector('.qfall').getBoundingClientRect().height)}})()""")
    check("%s: phone (390 px), 44 rows with the four group headers: no sideways scroll, every row and header inside the screen, the Details buttons 44 px (%s)" % (label, ph), ph["n"] == 44 and ph["sx"] <= 1 and ph["out"] == 0 and ph["heads"] and ph["det"] >= 44, ph)
    pg.tap(".qfgrp .qfdetb"); pg.wait_for_timeout(150)
    ph = E("document.documentElement.scrollWidth-innerWidth")
    check("%s: phone: a grouped row's Details opens without a sideways scroll (%s)" % (label, ph), ph <= 1)
    check("%s: phone: no page error" % label, not errs, errs[:1]); pg.close()
    # --- fails_unless_set (one link) and the choice outcomes
    def rowinfo(pg, g):
        pg.evaluate("(r)=>{QS.region=r;qsSetView('list');qsRenderAll()}", qs[g]["r"]); pg.wait_for_timeout(150)
        return pg.evaluate("""(g)=>{const r=document.querySelector('.qsrow[data-g="'+g+'"]'),w=r&&r.closest('.qfrow');return w&&{cls:w.className,chips:[...w.querySelectorAll('.qfchip')].map(c=>c.textContent),steps:[...w.querySelectorAll('.qfstep')].map(x=>x.textContent),txt:w.innerText.replace(/\\s+/g,' ')}}""", g)
    pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", ISLE: "active"}, keep=[VELEN])); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: fails_unless_set, one link: '<Failed> (<region>) fails at the portal prompt in <failer> (<region>) unless you've <condition> first.' and no 'Do ... first' (%s)" % (label, ban),
          re.fullmatch(r"Brothers In Arms: Velen fails at the portal prompt in The Isle of Mists unless you've recruited Keira in Velen first\.", ban) is not None and "Do " not in ban, ban)
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    t = E("[...document.querySelectorAll('#qfPanel .qfdep')].map(d=>d.innerText.replace(/\\s+/g,' '))")
    check("%s: its panel block: one sentence, then 'To keep it, do this before the portal prompt in The Isle of Mists.' (the condition once, no repeat) (and no choice blocks: their failers are not open) (%s)" % (label, len(t)),
          len(t) == 1 and "Brothers In Arms: Velen fails at the portal prompt in The Isle of Mists unless you've recruited Keira in Velen first. To keep it, do this before the portal prompt in The Isle of Mists." in t[0] and "IF YOU DO THIS" in t[0] and t[0].count("recruited Keira") == 1, t)
    vel = rowinfo(pg, VELEN)
    check("%s: the failed quest's row says 'Do before The Isle of Mists' and 'Fails at › The portal prompt in The Isle of Mists unless you've recruited Keira in Velen.' (%s)" % (label, vel and vel["chips"]),
          vel and vel["chips"] == ["Do before The Isle of Mists"] and "Fails at › The portal prompt in The Isle of Mists unless you've recruited Keira in Velen." in vel["txt"], vel)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    # three choices live with the Isle group: the banner has the group only, the panel the group and the three choices, no 'do first' anywhere for them
    pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", ISLE: "active", SQ101: "active", Q109: "active"}, keep=[VELEN, SQ101, Q109])); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("[...document.querySelectorAll('.qfbrow p')].map(p=>p.textContent.trim().replace(/\\s+/g,' '))")
    check("%s: choices live, the Isle and both choice failers active: one sentence per failer, the two choices that fail the same quest in one (v39.9) (%s)" % (label, ban), ban == ["Choosing to fail the date with Keira in A Favor for a Friend (Velen) fails Brothers In Arms: Velen. Choosing to defeat Keira or to let Keira leave for Radovid in For the Advancement of Learning (Velen) fails Brothers In Arms: Velen. Continuing The Isle of Mists (Kaer Morhen) fails A Favor for a Friend and For the Advancement of Learning, and 1 more unless you've gathered allies."], ban)
    pg.click(".qfmore"); pg.wait_for_timeout(100)
    t = E("[...document.querySelectorAll('#qfPanel .qfdep:not(.qfdepg)')].map(d=>d.innerText.replace(/\\s+/g,' '))")
    check("%s: but the panel has the three choice blocks: IF YOU CHOOSE, 'This is a choice, not an order: no quest can be done first to avoid it. To keep Brothers In Arms: Velen, <the safe option>.' (send Keira to Kaer Morhen in For the Advancement of Learning / don't fail the date with Keira in A Favor for a Friend), no 'Safe order', no 'I finished it already' (%s)" % (label, [c[:40] for c in t]),
          len(t) == 3 and all("IF YOU CHOOSE" in c and "This is a choice, not an order: no quest can be done first to avoid it. To keep Brothers In Arms: Velen, " in c and "make the other choice" not in c and "Safe order" not in c and "I finished it already" not in c and "first." not in c.replace("avoid it.", "") for c in t)
          and sum("IF YOU CHOOSE To defeat Keira" in c and "send Keira to Kaer Morhen in For the Advancement of Learning." in c for c in t) == 1 and sum("IF YOU CHOOSE To fail the date with Keira" in c and "send Keira to Kaer Morhen in For the Advancement of Learning." in c for c in t) == 1
          and sum("IF YOU CHOOSE To let Keira leave for Radovid" in c and "send Keira to Kaer Morhen in For the Advancement of Learning." in c for c in t) == 1, t)
    vel = rowinfo(pg, VELEN)
    check("%s: Velen's row: the amber chip names only The Isle of Mists (a choice never says 'Do before'), and no line mentions the choices (%s)" % (label, vel and vel["chips"]), vel and vel["chips"] == ["Do before The Isle of Mists"] and "Choosing" not in vel["txt"], vel)
    pg.click("#qsVFails"); pg.wait_for_timeout(250)
    cr = E("""(()=>{const rs=[...document.querySelectorAll('.qfrowx')].filter(r=>r.querySelector('.qfblk.red .qflab')&&r.querySelector('.qfblk.red .qflab').textContent==='IF YOU CHOOSE');return rs.map(r=>({k:r.dataset.k,t:r.innerText.replace(/\\s+/g,' '),st:r.querySelector('.qfst').textContent}))})()""")
    check("%s: Quest failures: the three choice rows read IF YOU CHOOSE (the option, in the failer), THE CHOICE, THIS FAILS Brothers In Arms: Velen, and the status 'Open · decided in the quest' (%s)" % (label, [c["t"][:70] for c in cr]),
          len(cr) == 3 and len({c["k"] for c in cr}) == 3 and all("THE CHOICE" in c["t"] and "THIS FAILS Brothers In Arms: Velen" in c["t"] and c["st"] == "Open · decided in the quest" for c in cr) and sum("IF YOU CHOOSE To defeat Keira in For the Advancement of Learning" in c["t"] for c in cr) == 1
          and sum("IF YOU CHOOSE To fail the date with Keira in A Favor for a Friend" in c["t"] for c in cr) == 1 and sum("IF YOU CHOOSE To let Keira leave for Radovid in For the Advancement of Learning" in c["t"] for c in cr) == 1, [c["t"] for c in cr])
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    # a choice is on the banner only while its failer is active: the Isle done, A Favor for a Friend active
    pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", ISLE: "done", SQ101: "active"}, keep=[VELEN, SQ101])); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: choice, failer active: the banner says 'Choosing to fail the date with Keira in A Favor for a Friend fails Brothers In Arms: Velen. To keep Brothers In Arms: Velen, send Keira to Kaer Morhen in For the Advancement of Learning.' with no 'Do ... first' (%s)" % (label, ban),
          re.fullmatch(r"Choosing to fail the date with Keira in A Favor for a Friend fails Brothers In Arms: Velen\. To keep Brothers In Arms: Velen, send Keira to Kaer Morhen in For the Advancement of Learning\.", ban) is not None and "first" not in ban, ban)
    row = rowinfo(pg, SQ101); v = rowinfo(pg, VELEN)
    check("%s: choice: the failer's row is red with the chip 'Fails 1 quest' and '› Choosing to fail the date with Keira — Brothers In Arms: Velen fails' (%s); Velen's row has no amber class" % (label, row and row["steps"]),
          row and "qf-fail" in row["cls"] and row["steps"] == ["› Choosing to fail the date with Keira — Brothers In Arms: Velen fails"] and row["chips"] == ["Fails 1 quest"] and (v is None or "qf-risk" not in v["cls"]), [row, v])
    nx = E("[...document.querySelectorAll('#qsNext .qscard')].map(c=>c.dataset.g).includes('%s')" % VELEN)
    check("%s: choice: Velen is not pushed forward in Next up (the failer being active does not make it a 'do first')" % label, nx is False, nx)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", ISLE: "done"}, keep=[VELEN, SQ101])); E = pg.evaluate; Q.opened(pg, "km"); pg.wait_for_timeout(300)
    nb = E("!document.querySelector('.qfbanner')"); E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(200)
    check("%s: choice, failer not started: no banner, but the Quest failures tab has its row" % label, nb and E("document.querySelectorAll('.qfrowx').length") == 44 and E("document.querySelectorAll('.qfrowx .qflab').length") > 0)
    pg.close()
    # --- journal_status, flow, a Deactivate link, a single fails_unless_set link: the existing sentence ('Do ... first') or 'closes'
    for name, keep, rx, failer in (("flow (Amidst the Mill's Grist)", "Amidst the Mill's Grist", r"Where Children Toil, Toys Waste Away(?: \([^)]+\))? fails or closes Amidst the Mill's Grist(?: \([^)]+\))? at the toy storage conversation in Where Children Toil, Toys Waste Away\. Do Amidst the Mill's Grist first\.", "Where Children Toil, Toys Waste Away"),
                           ("flow, Deactivate (Duck, Duck, Goosed!)", "Duck, Duck, Goosed!", r"Beyond Hill and Dale\.\.\.(?: \([^)]+\))? closes Duck, Duck, Goosed!(?: \([^)]+\))? at the end of the Beyond Hill and Dale\.\.\. quest\. Do Duck, Duck, Goosed! first\.", "Beyond Hill and Dale..."),
                           ("fact (Cabaret)", "Cabaret", r"The Isle of Mists(?: \([^)]+\))? fails or closes Cabaret(?: \([^)]+\))? at the portal prompt in The Isle of Mists\. Do Cabaret first\.", "The Isle of Mists")):
        pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", nm[failer]: "active"}, keep=[nm[keep]])); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
        ban = E("[...document.querySelectorAll('.qfbrow p')].map(p=>p.textContent.trim().replace(/\\s+/g,' '))")
        check("%s: %s: one banner line with the kind's sentence (%s)" % (label, name, ban), len(ban) == 1 and re.fullmatch(rx, ban[0]) is not None, ban)
        pg.click(".qfmore"); pg.wait_for_timeout(100)
        sf = E("document.querySelector('#qfPanel .qfsafe p').innerText.replace(/\\s+/g,' ')+' | '+document.querySelector('#qfPanel .qfcard.amber .qflab').textContent")
        check("%s: %s: the panel says 'Safe order: finish ..., then continue ...' and %s (%s)" % (label, name, "THIS QUEST CLOSES" if "Duck" in keep else "THIS QUEST FAILS", sf), sf.startswith("Safe order: finish %s, then continue" % keep) and sf.endswith("THIS QUEST CLOSES" if "Duck" in keep else "THIS QUEST FAILS"), sf)
        check("%s: %s: no page error" % (label, name), not errs, errs[:1]); pg.close()
    pg, errs, _ = Q.newpage(b, base, init=seed({THREAD: "done", ISLE: "active"}, keep=[nm["Brothers In Arms: Skellige"]])); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: fails_unless_set (Skellige): '... fails at accepting the portal prompt in The Isle of Mists unless you've recruited allies in Skellige first.' (%s)" % (label, ban), "unless you've recruited allies in Skellige first." in ban and "Do " not in ban and ban.startswith("Brothers In Arms: Skellige fails at the portal prompt in The Isle of Mists unless"), ban)
    pg.close()


def gate(b, base, check, label):
    """v39.6: the Isle of Mists gate is passed when Q402 is done (the save reader cannot read facts); a save between the objective "travel to the Isle" and the portal prompt keeps the quests open and failing at the gate; no objective of Q402 passes it"""
    qs, nm = _q()
    pg, errs, _ = Q.newpage(b, base, init=seed({}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km")
    isle = qs[nm["The Isle of Mists"]]
    p = E("""(a)=>{const gt=QS.R.gmap.get('isle'),cab=QS.byG.get(a.cab),r=[];r.push(qsPassed(gt),(qsFailsAt(cab)||{}).id||null,'obj' in gt);
      QS.store.manual[a.isle]='active';QS.store.save={q:{},o:{}};a.o.forEach(g=>{QS.store.save.o[g]='active'});r.push(qsPassed(gt));
      QS.store.save.o[a.o[0]]='done';r.push(qsPassed(gt),(qsFailsAt(cab)||{}).id||null);                               // a save after the objective "travel to the Isle", before the prompt
      a.o.forEach(g=>{QS.store.save.o[g]='done'});r.push(qsPassed(gt),(qsFailsAt(cab)||{}).id||null,qsFailsAtGate(cab,gt));   // every objective of Q402 done, the quest itself still active
      QS.store.manual[a.isle]='done';r.push(qsPassed(gt),(qsFailsAt(cab)||{}).id||null);delete QS.store.manual[a.isle];QS.store.manual[a.battle]='active';r.push(qsPassed(gt));return r}""",
          {"cab": nm["Cabaret"], "isle": isle["g"], "o": isle["o"], "battle": nm["The Battle of Kaer Morhen"]})
    check("%s: the Isle of Mists gate: not passed with no progress (Cabaret fails at it); a save with Q402 active and its 'travel to the Isle' objective DONE (between the objective and the prompt) or every objective done: still not passed, Cabaret still open and failing at the gate; Q402 done: passed; Q403 started: passed (%s)" % (label, p),
          p == [False, "isle", False, False, False, "isle", False, "isle", True, True, None, True], p)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()


def v399(b, base, check, label):
    """v39.9: the banner names the quests (2 / 3 / >3 at risk, two failers, 390 px), the tie order in Quest failures, the prompt in the strip + the detail panel + the List row + the failures row (one state, cleared together),
    and 'Can fail: ...' instead of 'Not missable as far as computed' for every quest that is on a fail link"""
    qs, nm = _q()
    FLESH, ISLE = nm["Flesh for Sale"], nm["The Isle of Mists"]
    # --- the banner with the real data: Ugly Baby active, both quests at risk open
    for w, h, mob in ((1440, 950, False), (390, 844, True)):
        pg, errs, _ = Q.newpage(b, base, w=w, h=h, mobile=mob, init=seed({UGLY: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
        pg.click(".qfmore"); pg.wait_for_timeout(150)
        r = E("""(()=>{const p=document.querySelector('.qfbrow p'),m=document.querySelector('.qfmore');return{t:p.textContent.trim().replace(/\\s+/g,' '),sx:document.documentElement.scrollWidth-innerWidth,pw:p.scrollWidth-p.clientWidth,r:Math.round(document.querySelector('.qfbanner').getBoundingClientRect().right)-innerWidth,more:m.textContent,mh:Math.round(m.getBoundingClientRect().height)}})()""")
        check("%s: %d px: Ugly Baby active, both quests open: 'Continuing Ugly Baby (Kaer Morhen) fails or closes Following the Thread and The Last Wish.', the More details button kept (44 px, now 'Hide details'), no sideways scroll (%s)" % (label, w, r),
              r["t"] == "Continuing Ugly Baby (Kaer Morhen) fails or closes Following the Thread and The Last Wish." and r["more"] == "Hide details" and r["mh"] >= 44 and r["sx"] <= 1 and r["pw"] <= 1 and r["r"] <= 0, r)
        check("%s: %d px: no page error" % (label, w), not errs, errs[:1]); pg.close()
        pg, errs, _ = Q.newpage(b, base, w=w, h=h, mobile=mob, init=seed({ISLE: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
        pg.click(".qfmore"); pg.wait_for_timeout(150)
        r = E("""(()=>{const p=document.querySelector('.qfbrow p');return{t:p.textContent.trim().replace(/\\s+/g,' '),n:document.querySelectorAll('.qfbrow p').length,deps:document.querySelectorAll('#qfPanel .qfdep').length,sx:document.documentElement.scrollWidth-innerWidth,pw:p.scrollWidth-p.clientWidth,pn:document.getElementById('qfPanel').scrollWidth-document.getElementById('qfPanel').clientWidth}})()""")
        check("%s: %d px: The Isle of Mists active (16 links): one sentence, the first two quests by level, 'and 10 more', 'and 4 more unless you've gathered allies'; the panel open; no sideways scroll (%s)" % (label, w, r),
              r["t"] == "Continuing The Isle of Mists (Kaer Morhen) fails or closes Ciri's Room, A Favor for a Friend and 10 more, and 4 more unless you've gathered allies." and r["n"] == 1 and r["sx"] <= 1 and r["pw"] <= 1 and r["pn"] <= 1, r)
        check("%s: %d px: no page error" % (label, w), not errs, errs[:1]); pg.close()
    # --- 2, 3 and 4 quests at risk for one failer (synthetic links from the real one), and the cap
    pg, errs, _ = Q.newpage(b, base, init=seed({UGLY: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    names = ["Ciri's Room", "An Invitation from Keira Metz", "Return to Crookback Bog", "A Matter of Life and Death"]   # levels 5, 6, 9, 12
    got = []
    for n, want in ((2, "Continuing Ugly Baby (Kaer Morhen) fails or closes Ciri's Room and An Invitation from Keira Metz."),
                    (3, "Continuing Ugly Baby (Kaer Morhen) fails or closes Ciri's Room, An Invitation from Keira Metz and Return to Crookback Bog."),
                    (4, "Continuing Ugly Baby (Kaer Morhen) fails or closes Ciri's Room, An Invitation from Keira Metz and 2 more.")):
        E("""(a)=>{const d=JSON.parse(JSON.stringify(W3DATA.QUEST_FAILS)),l=d.links.find(l=>l.failer_guid===a.u&&l.failed_guid===a.t);
          d.links=a.n.slice(0,a.k).map((g,i)=>Object.assign({},l,{failed_guid:a.g[g],fact:'f'+i}));QF.init(d);qsRenderAll()}""", {"u": UGLY, "t": THREAD, "n": names, "k": n, "g": nm}); pg.wait_for_timeout(200)
        t = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
        got.append(t); check("%s: %d quests at risk for one failer: %s (%s)" % (label, n, want, t), t == want, t)
    pg.close()
    # --- the order of Quest failures: by the failer's level, then by its story point (QUEST-RULES.json `s`, the order of `points`); a tie with no story-point difference keeps the old order
    pg, errs, _ = Q.newpage(b, base, init=seed({})); E = pg.evaluate; Q.opened(pg); E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(250)
    ORD = """[...document.querySelectorAll('.qfrowsx > *')].map(e=>QS.byG.get((e.dataset.k||e.querySelector('.qfrowx').dataset.k).slice(0,32)).n)"""   # the failer of each entry, in the order shown
    o = E(ORD); lv = {q["n"]: q["lv"] for q in qs.values()}
    check("%s: Quest failures: sorted by the failer's level (%s)" % (label, [lv[x] for x in o]), [lv[x] for x in o] == sorted(lv[x] for x in o), o)
    i, j = o.index("Imperial Audience"), o.index("The Incident at White Orchard")
    check("%s: the level-2 tie Imperial Audience / The Incident at White Orchard: both are story point 'p' with the same predecessors, so no field orders them and the old order (by name) stays (%s)" % (label, (i, j)),
          i < j and E("(()=>{const r=QS.R.quests;return r['%s'].s===r['%s'].s&&JSON.stringify(r['%s'].a)===JSON.stringify(r['%s'].a)})()" % (nm["Imperial Audience"], nm["The Incident at White Orchard"], nm["Imperial Audience"], nm["The Incident at White Orchard"])), (i, j))
    o2 = E("""(a)=>{QS.R.quests[a.t].s='e';QS.R.quests[a.e].s='3';qsRenderAll();return %s}""" % ORD, {"t": nm["On Thin Ice"], "e": nm["Something Ends, Something Begins"]})
    check("%s: two failers of one level: the earlier story point comes first (On Thin Ice and Something Ends, Something Begins, level 30, story points swapped here so the name order disagrees) (%s)" % (label, o2[o2.index("Something Ends, Something Begins") - 1:][:3]), o2.index("Something Ends, Something Begins") + 1 == o2.index("On Thin Ice"), o2)
    o3 = E("""(a)=>{QS.R.quests[a.t].s='3';QS.R.quests[a.e].s='3';qsRenderAll();return %s}""" % ORD, {"t": nm["On Thin Ice"], "e": nm["Something Ends, Something Begins"]})
    check("%s: the same story point: back to the name order" % label, o3.index("On Thin Ice") < o3.index("Something Ends, Something Begins"), o3)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    # --- the prompt is where the quest was marked done, and everywhere else: one state
    FOUR = """(()=>({strip:document.querySelectorAll('#qfPrompts .qfprompt').length,detail:!!document.querySelector('#qsDetail .qsprog + .qfinl .qfprompt'),
      row:!!(document.querySelector('.qsrow[data-g="%s"]')&&document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow')&&document.querySelector('.qsrow[data-g="%s"]').closest('.qfrow').querySelector('.qfprompt')),
      fails:!!document.querySelector('.qfrowx[data-k="%s%s"] .qfinl .qfprompt'),all:document.querySelectorAll('.qfprompt').length,man:QS.store.manual['%s']||null}))()""" % (THREAD, THREAD, THREAD, THREAD, FLESH, FLESH)
    def start(w=1440, h=950, mob=False):
        pg, errs, _ = Q.newpage(b, base, w=w, h=h, mobile=mob, init=seed({THREAD: "done"}, quiet=False)); Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
        pg.evaluate("qsSelect('%s')" % THREAD); pg.wait_for_timeout(250); return pg, errs
    pg, errs = start(); E = pg.evaluate
    f = E(FOUR); txt = E("[...document.querySelectorAll('.qfprompt')].map(p=>p.querySelector('p').textContent+'|'+[...p.querySelectorAll('button')].map(x=>x.textContent).join(','))")
    check("%s: Following the Thread marked done, Flesh for Sale open: the same prompt is in the strip, under MY PROGRESS in the detail panel and on the quest's List row, and the hand mark was not changed (%s)" % (label, f),
          f["strip"] == 1 and f["detail"] and f["row"] and f["all"] == 3 and f["man"] is None, f)
    check("%s: the three copies say the same and offer the same two actions plus the close button (%s)" % (label, txt[0]), len(set(txt)) == 1 and txt[0] == "Following the Thread is done. Flesh for Sale would have failed along the way.|Mark it failed,I finished it first,×", txt)
    E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(250); f = E(FOUR)
    check("%s: in Quest failures the row of that link carries it too (and the strip stays) (%s)" % (label, f), f["fails"] and f["strip"] == 1 and f["all"] == 3, f)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    for where, sel, want in (("the detail panel", '#qsDetail .qfprompt [data-a="done"]', "done"), ("the List row", '.qfrow .qfprompt [data-a="failed"]', "failed"), ("the strip", '#qfPrompts .qfprompt [data-a="done"]', "done")):
        pg, errs = start(); E = pg.evaluate; pg.click(sel); pg.wait_for_timeout(250); f = E(FOUR)
        check("%s: answering in %s sets Flesh for Sale to %s and clears the prompt in every place (%s)" % (label, where, want, f), f["man"] == want and f["all"] == 0, f)
        check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    pg, errs = start(); E = pg.evaluate; E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(250); pg.click('.qfrowx .qfinl [data-a="failed"]'); pg.wait_for_timeout(250); f = E(FOUR)
    check("%s: answering in the Quest failures row clears it everywhere (%s)" % (label, f), f["man"] == "failed" and f["all"] == 0, f)
    pg.close()
    pg, errs = start(); E = pg.evaluate; pg.click('#qsDetail .qfprompt .qfx2'); pg.wait_for_timeout(250); f = E(FOUR)
    check("%s: closing it with × in the detail panel closes every copy and changes no state (%s)" % (label, f), f["all"] == 0 and f["man"] is None, f)
    pg.close()
    pg, errs = start(390, 844, True); E = pg.evaluate
    ph = E("""(()=>({sx:document.documentElement.scrollWidth-innerWidth,h:[...document.querySelectorAll('.qfinl .qfprompt button')].map(x=>Math.round(x.getBoundingClientRect().height)).filter(x=>x>0),w:[...document.querySelectorAll('.qfprompt')].every(p=>p.getBoundingClientRect().right<=innerWidth)}))()""")
    check("%s: 390 px: the copies beside the quest do not scroll sideways and their buttons are 44 px (%s)" % (label, ph), ph["sx"] <= 1 and ph["w"] and len(ph["h"]) >= 3 and all(x >= 44 for x in ph["h"]), ph)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    # --- "Can fail" instead of "Not missable as far as computed"
    pg, errs, _ = Q.newpage(b, base, init=seed({}, quiet=False)); E = pg.evaluate; Q.opened(pg, "km")
    res = E("""(a)=>{const out={};a.forEach(g=>{qsSelect(g);const r=document.querySelector('#qsDetail .qsrules');out[g]={t:r?r.textContent.replace(/\\s+/g,' '):'',gate:!!(r&&r.querySelector('.qsfailsat,.qsloses')),can:r?r.querySelectorAll('.qfcan').length:0,no:r?r.querySelectorAll('.qsnomiss').length:0}});return out}""", sorted({l["failer_guid"] for l in LINKS} | {l["failed_guid"] for l in LINKS}))
    bad = [qs[g]["n"] for g, v in res.items() if "Not missable" in v["t"] or v["no"]]
    check("%s: none of the %d quests on a fail link says 'Not missable as far as computed' (%s)" % (label, len(res), bad), len(res) == len({l["failer_guid"] for l in LINKS} | {l["failed_guid"] for l in LINKS}) and not bad, bad)
    atrisk = {l["failed_guid"] for l in LINKS}
    miss = [qs[g]["n"] for g in atrisk if not res[g]["gate"] and not res[g]["can"]]
    check("%s: every at-risk quest without a gate rule of its own has a 'Can fail' line (%d of %d; the rest say 'Fails at ...') (%s)" % (label, sum(1 for g in atrisk if res[g]["can"]), len(atrisk), miss), not miss, miss)
    t = {k: res[nm[k]]["t"] for k in ("Following the Thread", "Brothers In Arms: Velen", "Imperial Audience")}
    check("%s: Following the Thread says 'Can fail: do it before Ugly Baby'; Brothers In Arms: Velen says 'Can fail at The Isle of Mists unless you've recruited Keira in Velen first' and 'Can fail by a choice in ...'; a quest that only fails others has no such line (%s)" % (label, t),
          "Can fail: do it before Ugly Baby" in t["Following the Thread"] and "Can fail at The Isle of Mists unless you've recruited Keira in Velen first" in t["Brothers In Arms: Velen"] and "Can fail by a choice in A Favor for a Friend" in t["Brothers In Arms: Velen"]
          and "Can fail" not in t["Imperial Audience"], t)
    E("qsSelect('%s')" % THREAD); pg.wait_for_timeout(150); pg.click("#qsDetail .qfcan .qslink"); pg.wait_for_timeout(200)
    check("%s: the failer's name in the line opens that quest (%s)" % (label, E("QS.sel")), E("QS.sel") == UGLY)
    n = E("""(()=>{const links=new Set(%s);for(const q of QS.data.quests){if(links.has(q.g))continue;qsSelect(q.g);if(document.querySelector('#qsDetail .qsnomiss'))return document.querySelector('#qsDetail .qsnomiss').textContent}return null})()""" % json.dumps(sorted({l["failer_guid"] for l in LINKS} | {l["failed_guid"] for l in LINKS})))
    check("%s: a quest with no fail link and no other rule still says 'Not missable as far as computed' (%s)" % (label, n), n == "Not missable as far as computed", n)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()


def v3910(b, base, check, label):
    """v39.10: (A) no action on one quest changes the stored state of another, and a stale page cannot write back a store that lacks quests saved elsewhere; (B) every warning is drawn once, whatever redraws the view"""
    qs, nm = _q()
    MANY = {UGLY: "active", SQ202: "done", Q206: "failed", nm["The Isle of Mists"]: "active", nm["Faithful Friend"]: "failed", nm["Ciri's Room"]: "done", nm["Imperial Audience"]: "active"}
    X = nm["The Incident at White Orchard"]                                                  # a quest nobody seeded
    GET = "(()=>JSON.stringify(Object.fromEntries(Object.entries(JSON.parse(localStorage.getItem('w3p.quests.v1')||'{\"manual\":{}}').manual).sort())))()"
    def fresh(manual, w=1440, h=950, mob=False, region="km", quiet=False):
        pg, errs, _ = Q.newpage(b, base, w=w, h=h, mobile=mob, init=seed(manual, quiet=quiet)); Q.opened(pg, region); pg.wait_for_timeout(300); return pg, errs
    def same(pg, what, allowed=None, expect=None):
        """the stored manual marks after `what` equal the seed, except `allowed` ({guid: new state}) which must have changed exactly so"""
        before = json.loads(pg.evaluate(GET)); what(); pg.wait_for_timeout(200); after = json.loads(pg.evaluate(GET))
        want = dict(before); want.update(allowed or {})
        for k in [k for k, v in want.items() if v is None]: del want[k]
        mem = pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(QS.store.manual).sort()))")
        return after == want and json.loads(mem) == after, {k[:6]: (before.get(k), after.get(k)) for k in set(before) | set(after) if before.get(k) != after.get(k)}
    # --- A1: every action, every other quest unchanged
    pg, errs = fresh(MANY); E = pg.evaluate; bad = []
    acts = [("region tabs", lambda: [(pg.click('.qsreg[data-r="%s"]' % r), pg.wait_for_timeout(60)) for r in ("wo", "vz", "ve", "no", "sk", "km", "hos", "baw", "oth")], None),
            ("select a quest", lambda: E("qsSelect('%s',true)" % X), None), ("Hide done", lambda: pg.click("#qsHide"), None), ("Hide done off", lambda: pg.click("#qsHide"), None),
            ("kind chip", lambda: pg.click('.qschip[data-k="main"]'), None), ("search", lambda: pg.fill("#qsQ", "a"), None), ("Level band", lambda: pg.click("#qsVBand"), None), ("Timeline", lambda: pg.click("#qsVTime"), None),
            ("List", lambda: pg.click("#qsVList"), None), ("Quest failures", lambda: pg.click("#qsVFails"), None), ("Hide ones I've dealt with", lambda: pg.click("#qfHide"), None), ("Details", lambda: pg.click(".qfdetb"), None),
            ("Hide ones off", lambda: pg.click("#qfHide"), None), ("List again", lambda: pg.click("#qsVList"), None)]
    for name, fn, al in acts:
        ok, d = same(pg, fn, al); bad += [] if ok else [(name, d)]
    check("%s: seven quests seeded with different states: region tabs, selecting a quest, Hide done, a kind chip, search, the four views, Hide ones I've dealt with and Details change no stored state (%s)" % (label, bad), not bad and not errs, bad or errs[:1]); pg.close()
    for st in ("none", "active", "done", "failed"):
        pg, errs = fresh(MANY); E = pg.evaluate; E("qsSelect('%s',true)" % X); pg.wait_for_timeout(200)
        ok, d = same(pg, lambda: pg.click('#qsDetail .qsmark[data-s="%s"]' % st), {X: st})
        ok2, d2 = same(pg, lambda: pg.click('#qsDetail .qsclear'), {X: None}) if st != "none" or True else (True, 0)
        check("%s: MY PROGRESS: %s on one quest changes only that quest, and Follow my save only that quest (%s | %s)" % (label, st, d, d2), ok and ok2 and not errs, [d, d2]); pg.close()
    pg, errs = fresh(MANY, region="no"); E = pg.evaluate
    ok, d = same(pg, lambda: (pg.click('.qsrow[data-g="%s"]' % nm["Following the Thread"]), pg.wait_for_timeout(150), pg.click('#qsDetail .qsmark[data-s="done"]')), {nm["Following the Thread"]: "done"})
    check("%s: the List row then MY PROGRESS: only Following the Thread changes (%s)" % (label, d), ok and not errs, d)
    for a, want in (("failed", "failed"), ("done", "done"), ("close", None)):
        ok, d = same(pg, lambda: pg.click('%s .qfprompt [data-a="%s"]' % ("#qfPrompts" if a == "close" else "#qsDetail", a)) if False else (E("document.querySelector('#qfPrompts .qfprompt [data-a=\"%s\"]').click()" % a) if E("!!document.querySelector('#qfPrompts .qfprompt [data-a=\"%s\"]')" % a) else None), {nm["Flesh for Sale"]: want} if want else None)
        check("%s: the prompt's %s changes only Flesh for Sale (%s)" % (label, "'" + a + "'" if a == "close" else a, d), ok, d)
        if a != "close": pg.close(); pg, errs = fresh(dict(MANY, **{nm["Following the Thread"]: "done"}), region="no"); E = pg.evaluate
    pg.close()
    # --- A2: a page whose copy of the store is stale (another tab saved quests it does not know) never writes the old copy back
    ctx = b.new_context(viewport={"width": 1440, "height": 950}); p1 = ctx.new_page(); p2 = ctx.new_page(); er = []
    for p in (p1, p2): p.on("pageerror", lambda e: er.append(str(e).split("\n")[0][:100]))
    p1.goto(base); Q.until(p1, Q.READY); p1.keyboard.press("q"); Q.until(p1, "S.scr==='q'&&document.querySelectorAll('#qsRegs .qsreg').length===9"); p1.click('.qsreg[data-r="no"]'); p1.wait_for_timeout(200)   # p1 has read an empty store
    p2.goto(base); Q.until(p2, Q.READY); p2.evaluate("localStorage.setItem('w3p.quests.v1',JSON.stringify({v:1,manual:{'%s':'active'},save:null,changed:1}))" % UGLY); p2.wait_for_timeout(300)   # the seed, written from another tab
    p1.evaluate("qsSelect('%s',true)" % THREAD); p1.wait_for_timeout(200); p1.click('#qsDetail .qsmark[data-s="done"]'); p1.wait_for_timeout(300)
    got = json.loads(p1.evaluate(GET))
    check("%s: another tab seeded Ugly Baby active while this page held an empty store: marking Following the Thread done keeps Ugly Baby active in the store (%s)" % (label, {k[:6]: v for k, v in got.items()}), got == {UGLY: "active", THREAD: "done"} and json.loads(p1.evaluate("JSON.stringify(QS.store.manual)")) == got, got)
    p1.evaluate("QS.store.manual={}"); p1.evaluate("qsSelect('%s',true)" % nm["Imperial Audience"]); p1.wait_for_timeout(150); p1.click('#qsDetail .qsmark[data-s="active"]'); p1.wait_for_timeout(300)   # even when the page missed the change completely
    got = json.loads(p1.evaluate(GET))
    check("%s: even when the page's copy is emptied behind its back, a mark adds to what is stored, it does not replace it (%s)" % (label, {k[:6]: v for k, v in got.items()}), got == {UGLY: "active", THREAD: "done", nm["Imperial Audience"]: "active"}, got)
    check("%s: no page error" % label, not er, er[:1]); ctx.close()
    # --- B: every warning is drawn once, whatever redraws the view
    ONCE = """(()=>{const v=[],n=(s,r)=>(r||document).querySelectorAll(s).length;
      document.querySelectorAll('#qsNext .qscard').forEach(c=>{if(n('.qfcaution',c)>1||n('.qfchip',c)>1)v.push('next up card '+c.dataset.g.slice(0,4)+': '+n('.qfcaution',c)+' cautions, '+n('.qfchip',c)+' chips')});
      document.querySelectorAll('.qfrow').forEach(w=>{if(w.parentNode.closest('.qfrow')||n('.qfextra',w)>1||n('.qsrow',w)!==1||n('.qfprompt',w)>1)v.push('list row '+w.querySelector('.qsrow').dataset.g.slice(0,4))});
      document.querySelectorAll('.qsrow[aria-label],.qsdot[aria-label]').forEach(r=>{const a=r.getAttribute('aria-label');if((a.match(/at risk: do before/g)||[]).length>1||(a.match(/, fails \\d+ open quest/g)||[]).length>1)v.push('label '+a.slice(0,60))});
      if(n('#qsDetail .qfdet')>1||n('#qsDetail .qfinl')>1)v.push('detail panel');if(n('#qfBanner .qfbanner')>1||n('.qfbrow p')>1)v.push('banner');
      document.querySelectorAll('#qsRegs .qfdots').forEach(d=>{if(d.children.length>2||d.parentNode.querySelectorAll('.qfdots').length>1)v.push('tab dots')});
      const k=[...document.querySelectorAll('.qfrowx')].map(r=>r.dataset.k);if(new Set(k).size!==k.length)v.push('failures rows repeated');
      return{v,caut:n('#qsNext .qfcaution'),chips:n('#qsNext .qfchip'),fr:n('.qfrowx')}})()"""
    pg, errs = fresh({UGLY: "active"}); E = pg.evaluate; E0 = E(ONCE); steps = [("start", E0)]
    for r in ("wo", "vz", "ve", "no", "sk", "km", "hos", "baw", "oth", "km"): pg.click('.qsreg[data-r="%s"]' % r); pg.wait_for_timeout(120); steps.append(("tab " + r, E(ONCE)))
    for g in (THREAD, UGLY, nm["The Last Wish"], nm["Flesh for Sale"], UGLY): E("qsSelect('%s',true)" % g); pg.wait_for_timeout(500); steps.append(("open " + qs[g]["n"], E(ONCE)))
    for lab, js in (("Hide done", "document.getElementById('qsHide').click()"), ("kind chip", "document.querySelector('.qschip[data-k=\"main\"]').click()"), ("search", "(()=>{const i=document.getElementById('qsQ');i.value='a';i.dispatchEvent(new Event('input'))})()"),
                    ("Level band", "document.getElementById('qsVBand').click()"), ("Timeline", "document.getElementById('qsVTime').click()"), ("Quest failures", "document.getElementById('qsVFails').click()"), ("List", "document.getElementById('qsVList').click()")):
        E(js); pg.wait_for_timeout(250); steps.append((lab, E(ONCE)))
    bad = [(n, r["v"]) for n, r in steps if r["v"]]; counts = {r["caut"] for n, r in steps}, {r["chips"] for n, r in steps}
    check("%s: Ugly Baby active: after every region tab, opening five quests, Hide done, a kind chip, search and the four views each warning is drawn once: no card, row, label, panel, banner or tab dot repeated (%s)" % (label, bad or counts), not bad and not errs, bad or errs[:1])
    check("%s: Next up keeps exactly its two cautions (Ugly Baby's, Following the Thread's) and two 'Do before' chips through all %d steps (%s)" % (label, len(steps), counts), counts == ({2}, {2}), counts)
    pg.close()


def gangs(b, base, check, label):
    """v39.11: Get Junior's meeting with Radovid fails The Gangs of Novigrad (44th link): the drawer, the banner, the prompt, the Quest failures row"""
    qs, nm = _q(); GJ, GN = nm["Get Junior"], nm["The Gangs of Novigrad"]
    pg, errs, _ = Q.newpage(b, base, init=seed({GJ: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    ban = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: Get Junior active: the banner names the link with the step: 'Get Junior ... fails or closes The Gangs of Novigrad at the meeting with Radovid. Do The Gangs of Novigrad first.' (%s)" % (label, ban),
          ban.startswith("Get Junior") and "The Gangs of Novigrad at the meeting with Radovid. Do The Gangs of Novigrad first." in ban and ("fails or closes" in ban), ban)
    E("qsSelect('%s',true)" % GN); pg.wait_for_timeout(300)
    t = E("document.querySelector('#qsDetail .qsrules').textContent.replace(/\\s+/g,' ')")
    check("%s: the drawer of The Gangs of Novigrad says 'Can fail: do it before Get Junior' and not 'Not missable as far as computed' (%s)" % (label, t), "Can fail: do it before Get Junior" in t and "Not missable" not in t, t)
    pg.click("#qsDetail .qfcan .qslink"); pg.wait_for_timeout(200)
    check("%s: the name in that line opens Get Junior" % label, E("QS.sel") == GJ)
    row = E("""(()=>{const r=document.querySelector('.qsrow[data-g="%s"]');return r&&r.closest('.qfrow')&&r.closest('.qfrow').textContent})()""" % GJ)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    pg, errs, _ = Q.newpage(b, base, init=seed({GJ: "done"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pr = E("document.querySelector('#qfPrompts .qfprompt p').textContent")
    check("%s: Get Junior done, The Gangs of Novigrad open: the prompt asks about it (%s)" % (label, pr), pr == "Get Junior is done. The Gangs of Novigrad would have failed along the way.", pr)
    E("qsSetView('fails');qsRenderAll()"); pg.wait_for_timeout(250)
    r = E("""(()=>{const x=document.querySelector('.qfrowx[data-k="%s%s"] .qfr1');return x&&x.textContent.replace(/\\s+/g,' ')})()""" % (GJ, GN))   # the visible row (the Game data section is collapsed and may name files)
    check("%s: the Quest failures tab has the row: IF YOU DO Get Junior, at the meeting with Radovid, THIS FAILS The Gangs of Novigrad (%s)" % (label, (r or "")[:160]),
          r and "Get Junior" in r and "The meeting with Radovid" in r and "The Gangs of Novigrad" in r and not re.search(r"[A-Za-z]+\d*_[A-Za-z_]+|phase", r), r)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()


def v3912(b, base, check, label):
    """v39.12: Battle Preparations also fails The Cave of Dreams (the second output of the pause in its graph); The Soldier Statuette's link (a repair phase only) is gone"""
    qs, nm = _q(); BPR, CAVE, KG, SOLD = nm["Battle Preparations"], nm["The Cave of Dreams"], nm["King's Gambit"], nm["The Soldier Statuette"]
    pg, errs, _ = Q.newpage(b, base, init=seed({}, quiet=False)); E = pg.evaluate; Q.opened(pg, "sk"); E("qsSelect('%s',true)" % CAVE); pg.wait_for_timeout(300)
    t = E("(()=>{const d=document.createElement('div');d.innerHTML=QF.line('%s');return[...d.querySelectorAll('.qfcan')].map(p=>p.textContent.trim())})()" % CAVE)
    check("%s: The Cave of Dreams has one 'Can fail' line per failer, King's Gambit and Battle Preparations (it keeps its own 'Fails at ...' gate line in the drawer, which the lines never replace), and no 'Not missable' (%s)" % (label, t), sorted(t) == ["Can fail: do it before Battle Preparations", "Can fail: do it before King's Gambit"] and "Not missable" not in E("document.querySelector('#qsDetail .qsrules').textContent"), t)
    E("qsSelect('%s',true)" % SOLD); pg.wait_for_timeout(300)
    t = E("document.querySelector('#qsDetail .qsrules').textContent.replace(/\\s+/g,' ')")
    check("%s: The Soldier Statuette no longer has a 'Can fail: do it before Battle Preparations' line (that link stood on a repair phase alone) (%s)" % (label, t), "Can fail" not in t and "Battle Preparations" not in t.split("Fails at")[0], t)
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()
    pg, errs, _ = Q.newpage(b, base, init=seed({BPR: "active"}, quiet=False)); E = pg.evaluate; Q.opened(pg, "sk"); Q.until(pg, "!!document.querySelector('.qfbanner')"); pg.click(".qfmore"); pg.wait_for_timeout(150)
    panel = E("document.getElementById('qfPanel').innerText.replace(/\\s+/g,' ')")
    ban = E("document.querySelector('.qfbrow p').textContent.trim().replace(/\\s+/g,' ')")
    check("%s: Battle Preparations active: the panel lists The Cave of Dreams among the quests that fail at the start of Act III in Skellige (and the banner names the first two by level) (%s)" % (label, ban),
          "The Cave of Dreams" in panel and "THESE 4 QUESTS FAIL" in panel and ban.startswith("Continuing Battle Preparations") and " and 2 more" in ban, [ban, panel[:200]])
    check("%s: no page error" % label, not errs, errs[:1]); pg.close()


def offline(b, off, check, label):
    pg, errs, reqs = Q.newpage(b, off, init=seed({UGLY: "active"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfbanner')")
    t = E("[document.querySelector('.qfbanner')&&document.querySelector('.qfbanner').textContent.trim(),!!document.querySelector('.qfrow.qf-risk'),typeof QF,!!(window.W3DATA&&W3DATA.QUEST_FAILS)]")
    check("%s: the offline package has the safeguard: banner, amber row, QF script and data loaded from the package (%s)" % (label, t), t[0].startswith("Ugly Baby (Kaer Morhen) fails or closes Following the Thread (Novigrad)") and t[1] and t[2] == "object" and t[3], t)
    pg.close()
    pg, errs, reqs = Q.newpage(b, off, init=seed({UGLY: "done"})); E = pg.evaluate; Q.opened(pg, "no"); Q.until(pg, "!!document.querySelector('.qfprompt')")
    pg.click('.qfprompt [data-a="failed"]'); pg.wait_for_timeout(200)
    check("%s: offline: the prompt's 'Mark it failed' works (hand mark failed)" % label, E("QS.store.manual['%s']" % THREAD) == "failed" and not errs, errs[:1])
    pg.close()
    pg, errs, reqs = Q.newpage(b, off, init=seed({})); E = pg.evaluate; Q.opened(pg); pg.click("#qsVFails"); pg.wait_for_timeout(250)
    o = E("[document.getElementById('qsVFails').textContent,document.querySelectorAll('.qfrowx').length,document.querySelector(__ROW+' .qfst').textContent,localStorage.getItem('w3p.quests.view')]")
    check("%s: offline: the Quest failures tab works (button count, the row, its status, the view stored) (%s)" % (label, o), o == ["Quest failures · 44", 44, "Open · plan for it", "fails"] and not errs, o)
    pg.close()
