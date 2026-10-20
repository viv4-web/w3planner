#!/usr/bin/env python3
"""Build data/QUEST_FAILS.json (v39): the verified "quest A's progress fails quest B" links the Quests screen warns about.

    python tools/build_quest_fails.py                      (reads data/QUEST_FAILS.candidates.json, writes data/QUEST_FAILS.json)
    python tools/build_quest_fails.py --check              (compares with the committed file)
    python tools/build_quest_fails.py --include <failed guid>   (also demands that this record is in: stops when it is not verified)

The candidates file (never committed: it is the output of the quest-graph spike, `status` per record) holds every link the game files seem to show. Only a record whose status is exactly
"verified_gamefiles" gets in; every other record is refused (listed, never copied). Statuses: verified_gamefiles (shipped), rejected (checked, cannot happen in play or is no cause of its own: needs
a `rejection` text; not shipped, not counted) and candidate (still being checked: only these are counted in `candidates`). The tool stops when nothing is verified, when a verified record has no human wording in HUMAN below,
or when a GUID is not a quest of data/QUESTS.json. `candidates` is the number of refused records (the Quest failures tab says how many are still being checked), a number and nothing else. No game text: GUIDs, a fact name, a comparison, block numbers and short labels of our own.
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "QUEST_FAILS.candidates.json"
OUT = ROOT / "data" / "QUEST_FAILS.json"
GUID = re.compile(r"[0-9a-f]{32}")
# our own wording per (failer guid, fact): what the player does, and a short name for it. A verified link without a row here is refused.
HUMAN = {
    ("307d9fcade274740b37341fa6a6a76c7", "q401_gotten_uma"): dict(trigger_label="Talk to the stable guard at Crow's Perch", trigger_short="stable guard"),
    ("e10a13b571218a46b0d37b0b9954be3f", "q206_party_started"): dict(trigger_label="Go through the gate of Kaer Trolde Keep to report to Crach", trigger_short="gates of Kaer Trolde Keep"),
}
STATUSES = ("verified_gamefiles", "rejected", "candidate")


def phases(rec):
    """'Collect UMA > Stable Master': the phase names inside the failer's own quest container (the path after 'QUEST - <file>')"""
    path = [re.sub(r"^.*?#\d+\s*", "", p).strip() for p in (rec.get("setter_phase_path") or [])]
    cut = [i for i, p in enumerate(path) if p.startswith("QUEST - ")]
    names = path[cut[-1] + 1:] if cut else path[-2:]
    return " > ".join(names)


def convert(rec, quests):
    """one candidate record -> one link; SystemExit with the reason when it may not be shipped"""
    who = "%s <- %s" % (rec.get("failed_id"), rec.get("failer_id"))
    if rec.get("status") != "verified_gamefiles":
        sys.exit("refusing %s: status is %r, only \"verified_gamefiles\" may be shipped" % (who, rec.get("status")))
    for k in ("failed_guid", "failer_guid"):
        if not GUID.fullmatch(str(rec.get(k))) or rec[k] not in quests:
            sys.exit("refusing %s: %s %r is not a quest of data/QUESTS.json" % (who, k, rec.get(k)))
    h = HUMAN.get((rec["failer_guid"], rec.get("fact")))
    if not h:
        sys.exit("refusing %s: no wording for (%s, %s) in HUMAN" % (who, rec["failer_guid"], rec.get("fact")))
    op = rec.get("op_original") or {}
    if op.get("value") is None or not str(op.get("func", "")).startswith("CF_"):
        sys.exit("refusing %s: the comparison is not stated in the file (func %r, value %r)" % (who, op.get("func"), op.get("value")))
    ev = [dict(file=e["file"], block=e["block"], note=e["note"]) for e in rec.get("evidence") or []]
    if rec.get("gaps"):
        sys.exit("refusing %s: gaps are not empty (%d)" % (who, len(rec["gaps"])))
    if not ev:
        sys.exit("refusing %s: no evidence" % who)
    eff = "unconfirmed" if str(rec.get("engine_effect", "")).startswith("unconfirmed") else str(rec.get("engine_effect") or "unconfirmed")
    o = dict(func=op["func"], value=op["value"])
    if op.get("query"): o["query"] = op["query"]
    link = dict(failed_guid=rec["failed_guid"], failer_guid=rec["failer_guid"], fact=rec["fact"], op=o,
                trigger_phase=rec.get("trigger_phase") or phases(rec), trigger_label=h["trigger_label"], trigger_short=h["trigger_short"], evidence=ev, engine_effect=eff)
    if rec.get("window"): link["window"] = rec["window"]
    return link


def build(cand, quests, include=()):
    recs = cand["pairs"] if isinstance(cand, dict) else cand
    for r in recs:
        if r.get("status") not in STATUSES: sys.exit("refusing %s <- %s: unknown status %r" % (r.get("failed_id"), r.get("failer_id"), r.get("status")))
        if r["status"] == "rejected" and not str(r.get("rejection") or "").strip(): sys.exit("refusing %s <- %s: rejected without a reason" % (r.get("failed_id"), r.get("failer_id")))
    by_failed = {r.get("failed_guid"): r for r in recs}
    for g in include:
        if g not in by_failed:
            sys.exit("refusing %s: not in the candidates file" % g)
        convert(by_failed[g], quests)            # stops when it is not verified
    ok = [r for r in recs if r.get("status") == "verified_gamefiles"]
    if not ok:
        sys.exit("nothing is verified_gamefiles: nothing to write")
    links = [convert(r, quests) for r in ok]
    refused = [r for r in recs if r.get("status") != "verified_gamefiles"]
    left = [r for r in refused if r["status"] == "candidate"]
    return dict(v=1, links=links, candidates=len(left)), refused      # candidates = how many records are still being checked (not the rejected ones): a number only, no names or details


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default=str(CANDIDATES)); ap.add_argument("--out", default=str(OUT)); ap.add_argument("--quests", default=str(ROOT / "data" / "QUESTS.json"))
    ap.add_argument("--include", action="append", default=[], help="a failed quest GUID that must be shipped (stops when its record is not verified)"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cand = json.loads(Path(a.candidates).read_text(encoding="utf-8")); quests = {q["g"] for q in json.loads(Path(a.quests).read_text(encoding="utf-8"))["quests"]}
    data, refused = build(cand, quests, a.include); blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False) + "\n"
    print("%d verified link(s) written; %d record(s) refused (status is not verified_gamefiles): %d rejected, %d still candidate" % (len(data["links"]), len(refused), len(refused) - data["candidates"], data["candidates"]), file=sys.stderr)
    if a.check:
        ok = Path(a.out).read_text(encoding="utf-8") == blob; print("OK: matches" if ok else "DIFFERENT: run tools/build_quest_fails.py"); sys.exit(0 if ok else 1)
    Path(a.out).write_text(blob, encoding="utf-8"); print("wrote %s (%d bytes)" % (a.out, len(blob)), file=sys.stderr)


if __name__ == "__main__":
    main()
