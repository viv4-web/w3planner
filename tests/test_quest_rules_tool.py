#!/usr/bin/env python3
"""v35: tools/make_quest_rules.py - the unplaced split (`u`) and the choice rows (`k`). Fake inputs for the stop-hard cases; the real spike files (local, never committed) when present.
Exit 0 = all passed."""
import csv, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_quest_rules as M

FAIL = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  (" + str(detail) + ")") if detail != "" else ""))
    if not ok: FAIL.append(name)


def stops(fn, *a):
    try: fn(*a)
    except SystemExit as e: return str(e.code)
    return None


def tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t"); w.writerow(header); w.writerows(rows)


qinfo = {("%032x" % i): {"g": "%032x" % i, "id": "Q%d" % i, "o": ["%032x" % (100 + i)]} for i in range(1, 7)}
id2g = {q["id"]: g for g, q in qinfo.items()}
G = list(qinfo)
d = Path(tempfile.mkdtemp(prefix="w3qr-"))
HEAD = ["quest_id", "name", "reason_group", "story_point", "confidence", "ungated", "window_end_cutoffs", "notes", "evidence"]
rows = lambda ids, ung: [[i, "", "", "", "unknown", "ungated" if i in ung else "", "", "", ""] for i in ids]
out = {G[0]: {"s": "a"}, G[1]: {"s": "p"}}
tsv(d / "p.tsv", HEAD, rows(["Q3", "Q4", "Q5", "Q6"], {"Q3", "Q4", "Q5"}))
read = M.read_tsv(d / "p.tsv", ["quest_id", "ungated", "confidence"])
check("placements: 3 ungated + 1 unknown = the 4 quests with no story point", M.apply_placements(out, qinfo, id2g, read) == (3, 1) and out[G[5]] == {"u": "unknown"} and out[G[2]] == {"u": "ungated"} and "u" not in out[G[0]])
check("placements: missing file stops", "missing input" in (stops(M.read_tsv, d / "nope.tsv", ["quest_id"]) or ""))
check("placements: a missing column stops", "columns" in (stops(M.read_tsv, d / "p.tsv", ["quest_id", "nothing"]) or ""))
for name, ids, msg in (("a quest short", ["Q3", "Q4", "Q5"], "does not match"), ("a quest too many", ["Q3", "Q4", "Q5", "Q6", "Q1"], "does not match"), ("a duplicate", ["Q3", "Q4", "Q5", "Q6", "Q6"], "twice"), ("an unknown id", ["Q3", "Q4", "Q5", "Q9"], "not a quest")):
    tsv(d / "q.tsv", HEAD, rows(ids, set(ids)))
    check("placements: counts that do not add up stop (%s)" % name, msg in (stops(M.apply_placements, {G[0]: {"s": "a"}, G[1]: {"s": "p"}}, qinfo, id2g, M.read_tsv(d / "q.tsv", ["quest_id", "ungated"])) or ""))
tsv(d / "q.tsv", HEAD, [["Q3", "", "", "", "", "yes", "", "", ""]] + rows(["Q4", "Q5", "Q6"], set()))
check("placements: a bad `ungated` value stops", "ungated column" in (stops(M.apply_placements, {G[0]: {"s": "a"}, G[1]: {"s": "p"}}, qinfo, id2g, M.read_tsv(d / "q.tsv", ["quest_id", "ungated"])) or ""))
CH = ["row", "class", "quest", "quest_guid", "objective_guid", "holder_quest"]
o = {}
r = [["1", "keep-quest", "Q1", G[0], "", ""], ["2", "keep-quest", "Q2", G[1], "", "Q3"], ["3", "keep-obj", "Q4", G[3], qinfo[G[3]]["o"][0], ""], ["4", "drop", "Q5", G[4], "", ""]]
check("choices: keep-quest [q], cross-quest [q, holder], keep-obj [o, objective]; drop adds nothing", M.apply_choices(o, qinfo, id2g, [dict(zip(CH, x)) for x in r]) == (2, 1, 1) and o == {G[0]: {"k": [["q"]]}, G[1]: {"k": [["q", G[2]]]}, G[3]: {"k": [["o", qinfo[G[3]]["o"][0]]]}}, o)
for name, bad in (("an unknown class", ["1", "maybe", "Q1", G[0], "", ""]), ("a quest guid that is not the quest's", ["1", "keep-quest", "Q1", G[1], "", ""]), ("an objective of another quest", ["1", "keep-obj", "Q1", G[0], qinfo[G[1]]["o"][0], ""]), ("an unknown holder", ["1", "keep-quest", "Q1", G[0], "", "Q99"])):
    check("choices: %s stops" % name, stops(M.apply_choices, {}, qinfo, id2g, [dict(zip(CH, bad))]) is not None)
# the committed file and, when the spike is here, the real run
R = json.loads((ROOT / "data" / "QUEST-RULES.json").read_text(encoding="utf-8"))["quests"]
n = lambda v: sum(r.get("u") == v for r in R.values())
check("committed QUEST-RULES.json: 157 ungated + 34 unknown = 191", (n("ungated"), n("unknown")) == (157, 34))
if (M.SPIKE35 / "placements.tsv").is_file() and (M.SPIKE / "rules.json").is_file():
    data, _, _, v = M.build()
    check("the tool on the real spike: 157 + 34 = 191, 4 keep-quest + 3 keep-obj + 14 drop, and the committed file is what it writes", (v["ungated"], v["unknown"]) == (157, 34) and (v["keep_quest"], v["keep_obj"], v["drop"]) == (4, 3, 14)
          and (ROOT / "data" / "QUEST-RULES.json").read_text(encoding="utf-8") == json.dumps(data, separators=(",", ":")) + "\n", v)
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "make_quest_rules.py"), "--check", "--placements", str(d / "none.tsv")], capture_output=True, text=True)
    check("the tool run with a missing placements.tsv fails hard (exit %d)" % p.returncode, p.returncode != 0 and "missing input" in p.stderr)
else: print("  SKIP  the tool on the real spike files (not present)")
print("\n%d failed" % len(FAIL) if FAIL else "\nall passed"); sys.exit(1 if FAIL else 0)
