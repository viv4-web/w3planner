#!/usr/bin/env python3
"""Build data/QUEST-RULES.json (v34): story point, cutoffs ("fails at <gate>") and predecessors of every quest, from the quest-graph spike.

    python tools/make_quest_rules.py                 (reads ~/work/w3planner-art/quest-spike/v34/rules.json, writes data/QUEST-RULES.json, prints what it left out)
    python tools/make_quest_rules.py --check         (compares with the committed file)

The spike (quest-spike/FORMAT-NOTES-v34.md, never committed) reads the game's .w2quest / .w2phase graphs: a story phase sets a fact, another quest's graph tests it and a
journal block's Failure or Deactivate input fires. This tool keeps only what that gives, nothing else, and no game text (ids and numbers only):
  * a cutoff is kept only when a Failure / Deactivate input of a journal block is reachable from the test (that is how the spike finds them), and its fact is not a temporary
    toggle: facts with "pause", "unpause" or "failsafe" in the name are dropped (mq3026_race_pause, q602_pants_failsafe ...)
  * a story point that the spike derived "by default (no gate found)" is stored as unknown (no `s`)
  * the cutoffs of the spike are merged into the gates of GATES below (the confirmed story points of no return) and each gate says when a save has passed it
docs/QUESTS.md ("Timeline, missables, unlock chains") has the rules and the numbers.
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPIKE = Path.home() / "work" / "w3planner-art" / "quest-spike" / "v34"
POINTS = [("p", "Prologue"), ("a", "Act I"), ("i", "Isle of Mists"), ("b", "Battle of Kaer Morhen"), ("3", "Act III"), ("e", "Epilogue"), ("h", "Hearts of Stone"), ("w", "Blood and Wine")]
SP = {"Prologue": "p", "Act I free roam": "a", "Isle of Mists": "i", "Battle of Kaer Morhen": "b", "Act III": "3", "Epilogue": "e", "Hearts of Stone start": "h", "Blood and Wine start": "w"}
TOGGLE = re.compile(r"pause|failsafe", re.I)
# facts left out although a Failure / Deactivate input follows them: a state of the game, not a point of no return
EXCLUDE = {"q601_geralt_has_demon_mark": "a Hearts of Stone state flag (the demon mark): it fails an objective of Q310, it is not a story gate"}
# the gates: the spike's cutoff names -> one gate. lane b = the base game columns (x: 0 = left edge of Prologue, 1 = Act I, 2 = Isle of Mists, 3 = Battle, 4 = Act III, 5 = Epilogue, 6 = right edge),
# lane w / h = the expansions, laid out by quest level (x = a level). `done`: the quests whose Success passes the gate; `next`: the quests that exist once it is passed (rule: docs/QUESTS.md).
GATES = [
    dict(id="prologue", name="Leaving White Orchard", lane="b", x=1.0, cuts=["Prologue: White Orchard"], done=["Q002 Griffin hunt"], next=["Q101 Agent"]),
    dict(id="isle", name="Isle of Mists", lane="b", x=2.0, cuts=["Isle of Mists: leaving for the Isle (q402_escort_completed)", "Isle of Mists: Brothers in Arms / Isle (internal facts)"], done=["Q402 Isle of Mists"], next=["Q403 Battle of Kaer Morhen"]),
    dict(id="battle", name="Battle of Kaer Morhen", lane="b", x=3.0, cuts=["Battle of Kaer Morhen"], done=["Q403 Battle of Kaer Morhen"], next=["Q110 Postbattle"]),
    dict(id="novigrad3", name="Act III: Novigrad (Q310)", lane="b", x=4.3, cuts=["Act III: Novigrad (Q310)"], done=["Q310 Ciri's Night Out"], next=["Q311 The Spiral"]),
    dict(id="skellige3", name="Act III: Skellige (Q210)", lane="b", x=4.55, cuts=["Act III: Skellige (Q210 starts)"], done=["Q210 Pre Canaris"], next=["Q501 Eredin"]),
    dict(id="naglfar", name="The Naglfar arrives (Q501)", lane="b", x=4.8, cuts=["Act III: the Naglfar arrives (Q501)"], done=["Q501 Eredin"], next=["Q502 Avallach"]),
    dict(id="ciri", name="Ciri's fate", lane="b", x=5.25, cuts=["Epilogue: Ciri's fate (q502/q110)"], done=["Q502 Avallach"], next=["Q503 NEW Ciri Dead", "Q504 Ciri Empress", "Q505 Ciri Free"]),
    dict(id="finish", name="Game finished", lane="b", x=5.7, cuts=["Game finished (after the epilogue)"], done=["Q503 NEW Ciri Dead", "Q504 Ciri Empress", "Q505 Ciri Free"], next=[]),
    dict(id="baw701", name="The Beast of Toussaint (Q701)", lane="w", x=35.9, cuts=["Blood and Wine: Q701 The Beast of Toussaint (q701_done)", "Blood and Wine: Q701 The Beast of Toussaint (q701_opening_done)"], done=["Q701_Festival"], next=["Q702 Dettlaff"]),
    dict(id="baw702", name="Blood Run (Q702)", lane="w", x=36.9, cuts=["Blood and Wine: Q702 Blood Run (q702_play_buttler_scene)", "Blood and Wine: Q702 Blood Run (q702_wight_killed)"], done=["Q702 Dettlaff"], next=["Q703 All for one"]),
    dict(id="baw703", name="Capture the Castle done (Q703)", lane="w", x=47.2, cuts=["Blood and Wine: Capture the Castle, Q703 (q703_done)"], done=["Q703 All for one"], next=["Q704 Starting"]),
    dict(id="bawnight", name="The Night of Long Fangs (Q704)", lane="w", x=47.6, cuts=["Blood and Wine: The Night of Long Fangs starts (Q704)"], done=[], next=["Q704 Starting"], real=True),
    dict(id="baw704", name="Tesham Mutna done (Q704)", lane="w", x=49.1, cuts=["Blood and Wine: Q704 Tesham Mutna (q704_done)"], done=["Q704 Dettlaff"], next=["Q705 Home"]),
    dict(id="baw705", name="The epilogue (Q705)", lane="w", x=49.6, cuts=["Blood and Wine: Q705 epilogue (q705_catacombs_active)", "Blood and Wine: Q705 epilogue (q705_completed)"], done=["Q705 Home"], next=[]),
    dict(id="hos", name="Dead Man's Party done (Q602)", lane="h", x=33.5, cuts=["Hearts of Stone: main quest result"], done=["q602wedding"], next=["q603bank"]),
]
# the story section a save is in: the highest whose quests have an entry (any state) in it
ENTER = {"p": ["Q001 Dream", "Q001 Find Yennefer", "Q002 Griffin hunt"], "a": ["Q101 Agent"], "i": ["Q402 Isle of Mists"], "b": ["Q403 Battle of Kaer Morhen"], "3": ["Q110 Postbattle"], "e": ["Q503 NEW Ciri Dead", "Q504 Ciri Empress", "Q505 Ciri Free"],
         "h": ["q601intro"], "w": ["Q701_Festival"]}


def build(spike=SPIKE):
    R = json.loads((spike / "rules.json").read_text(encoding="utf-8")); Q = json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]
    qinfo = {q["g"]: q for q in Q}; gid = set(qinfo); id2g = {q["id"]: q["g"] for q in Q}
    cname = {c["id"]: c["name"] for c in R["cutoffs"]}; byname = {n: g for g in GATES for n in g["cuts"]}
    for g in GATES:
        for k in g["done"] + g["next"] + [x for v in ENTER.values() for x in v]:
            if k not in id2g: sys.exit("unknown quest id in GATES / ENTER: %r" % k)
    out = {}; dropped = []; gate_of_cut = {}
    for c in R["cutoffs"]:
        if c["name"] not in byname: dropped.append(("cutoff with no gate", c["name"]))
    unknown = 0; nk = 0
    for g, r in R["quests"].items():
        if g not in gid: continue
        rec = {}
        spb = r.get("spb") or ""
        if r.get("sp") and not spb.startswith("default") and r["sp"] in SP:
            rec["s"] = SP[r["sp"]]; rec["h"] = "c" if spb.startswith("container") else "g"
        else:
            unknown += 1
        cuts = {}
        for e in r.get("cut", []):
            name = cname.get(e["c"])
            if TOGGLE.search(e["f"]): dropped.append(("toggle / failsafe fact %s" % e["f"], "%s on %s" % (e["how"], r["id"]))); continue
            if e["f"] in EXCLUDE: dropped.append(("fact %s (%s)" % (e["f"], EXCLUDE[e["f"]]), "%s on %s" % (e["how"], r["id"]))); continue
            gt = byname.get(name)
            if not gt: continue
            lv = "q" if e["lv"] == "Quest" else "o"; how = "f" if e["how"] == "Failure" else "d"
            k = (gt["id"], lv, how)
            # a whole-quest effect covers the objective one of the same gate
            cuts[k] = 1
        keys = sorted(cuts)
        keys = [k for k in keys if not (k[1] == "o" and any(x[0] == k[0] and x[1] == "q" for x in keys))]
        if keys: rec["c"] = [list(k) for k in keys]
        after = []; me = qinfo[g]
        for kind in ("flow", "journal", "fact"):
            for u in r.get("u", []):
                if u["k"] != kind: continue
                ids = u.get("q") if kind == "flow" else [u.get("q")] if kind == "journal" else u.get("by", [])
                for i in ids or []:
                    if i not in id2g or id2g[i] == g or id2g[i] in after: continue
                    p = qinfo[id2g[i]]
                    # a fact setter is a weaker link than a phase that feeds the start: no Gwent / race / fistfight quest, nothing of a clearly higher level (a prerequisite is not harder)
                    if kind == "fact" and (p["t"] in ("gwent", "race", "fist") or (p["lv"] is not None and me["lv"] is not None and p["lv"] > me["lv"] + 2)): continue
                    after.append(id2g[i])
        if after: rec["a"] = after[:4]
        if rec: out[g] = rec
    used = {k[0] for rec in out.values() for k in rec.get("c", [])}
    gates = []
    for gt in GATES:
        if gt["id"] not in used: dropped.append(("gate with no confirmed effect left", gt["name"])); continue
        # `code`: the quest code the gate is named by: in its name, else the code of the one quest whose Success passes it (v34.1: the gate key shows it); `real`: the one cutoff that is real (not a level of a rule)
        m = re.search(r"\((Q\d{3})\)", gt["name"]) or (re.match(r"(Q\d{3})", gt["done"][0]) if len(gt["done"]) == 1 else None)
        gate = dict(id=gt["id"], name=gt["name"], lane=gt["lane"], x=gt["x"], done=[id2g[i] for i in gt["done"]], next=[id2g[i] for i in gt["next"]])
        if m: gate["code"] = m.group(1)
        if gt.get("real"): gate["real"] = 1
        gates.append(gate)
    data = dict(v=1, points=[list(p) for p in POINTS], gates=gates, enter={k: [id2g[i] for i in v] for k, v in ENTER.items()}, quests=out)
    return data, dropped, unknown


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); ap.add_argument("--spike", default=str(SPIKE)); a = ap.parse_args()
    data, dropped, unknown = build(Path(a.spike)); blob = json.dumps(data, separators=(",", ":")) + "\n"
    q = data["quests"]
    print("quests with a story point: %d, unknown (stored without `s`): %d; with a cutoff: %d (whole-quest %d); with predecessors: %d; gates: %d" % (sum("s" in r for r in q.values()), unknown,
          sum("c" in r for r in q.values()), sum(any(k[1] == "q" for k in r.get("c", [])) for r in q.values()), sum("a" in r for r in q.values()), len(data["gates"])), file=sys.stderr)
    for what, detail in dropped: print("LEFT OUT: %s: %s" % (what, detail), file=sys.stderr)
    p = ROOT / "data" / "QUEST-RULES.json"
    if a.check:
        ok = p.read_text(encoding="utf-8") == blob; print("OK: matches" if ok else "DIFFERENT: run tools/make_quest_rules.py"); sys.exit(0 if ok else 1)
    p.write_text(blob, encoding="utf-8"); print("wrote %s (%d bytes)" % (p, len(blob)), file=sys.stderr)


if __name__ == "__main__":
    main()
