#!/usr/bin/env python3
"""Build data/QUEST_FAILS.json (v39.5): the verified "quest A's progress fails quest B" links the Quests screen warns about.

    python tools/build_quest_fails.py                      (reads data/QUEST_FAILS.candidates.json, writes data/QUEST_FAILS.json)
    python tools/build_quest_fails.py --check              (compares with the committed file)
    python tools/build_quest_fails.py --include <failed guid>   (also demands that this record is in: stops when it is not verified)

The candidates file (never committed: the output of the quest-graph spike, `status` per record) has two lists. `pairs` (v39, the first three links) and `coverage` (the coverage audit of v39.5).
Only a record whose status is exactly "verified_gamefiles" gets in; every other record is refused (listed, never copied). Statuses: verified_gamefiles (shipped), rejected (checked, cannot happen in play
or is no cause of its own: needs a `rejection` text; not shipped, not counted), candidate (still being checked: needs what is `missing`; counted in `candidates`), not_a_fail and not_found (coverage audit:
answered, not counted). The tool stops when nothing is verified, when a verified record has gaps, a GUID that is not a quest of data/QUESTS.json, no evidence, or a field its kind needs is missing.
`candidates` is a number and nothing else. No game text: GUIDs, a fact name, a comparison, block numbers and short labels of our own.

Every link has a `kind`:
  fact              the failer's step sets a story fact; the failed quest waits for it and fails ("Do <failed> first")
  fails_unless_set  the failed quest is tested once at the trigger and fails unless its own fact is already set (Brothers In Arms at the Isle of Mists portal prompt); needs `condition` (what saves it, from its evidence) and `unless_group` (the shared phrase for the banner: "gathered allies")
  choice            a choice outcome in the failer; there is no "do it first"; needs `choice` (the option in plain words) and `safe` (the option that keeps the quest)
  journal_status    the failed quest fails on a journal state of the failer (no fact); needs `journal`
  flow              a Failure / Deactivate placed in the failer's own flow (no fact needed); needs `flow`
`premise` (optional) is an evidence note: the comparison reads an absent value as 0 ("> 0" / "== 0"), see docs/QUESTS.md. `effect` is Failure or Deactivate (closes). Evidence items that
three or more links share (the Isle of Mists setter) are stored once in `ev` and referenced by their index.
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "data" / "QUEST_FAILS.candidates.json"
OUT = ROOT / "data" / "QUEST_FAILS.json"
GUID = re.compile(r"[0-9a-f]{32}")
# our own wording per (failer guid, fact) for the records of the first list (`pairs`): what the player does, and a short name for it. A verified `pairs` record without a row here is refused.
HUMAN = {
    ("307d9fcade274740b37341fa6a6a76c7", "q401_gotten_uma"): dict(trigger_label="talking to the stable guard at Crow's Perch", trigger_short="stable guard"),
    ("e10a13b571218a46b0d37b0b9954be3f", "q206_party_started"): dict(trigger_label="going through the gate of Kaer Trolde Keep to report to Crach", trigger_short="gates of Kaer Trolde Keep"),
}
STATUSES = ("verified_gamefiles", "rejected", "candidate", "not_a_fail", "not_found")
KINDS = ("fact", "fails_unless_set", "choice", "journal_status", "flow")
KIND_NEEDS = {"fact": ("fact", "op"), "fails_unless_set": ("fact", "op", "condition", "unless_group"), "choice": ("fact", "op", "choice", "safe"), "journal_status": ("journal",), "flow": ("flow",)}
EFFECTS = ("Failure", "Deactivate")
SHARE_MIN = 3        # an evidence item used by this many links goes to the shared table


def phases(rec):
    """'Collect UMA > Stable Master': the phase names inside the failer's own quest container (the path after 'QUEST - <file>')"""
    path = [re.sub(r"^.*?#\d+\s*", "", p).strip() for p in (rec.get("setter_phase_path") or [])]
    cut = [i for i, p in enumerate(path) if p.startswith("QUEST - ")]
    names = path[cut[-1] + 1:] if cut else path[-2:]
    return " > ".join(names)


def norm_op(op, kind, who):
    """-> {func, value[, query]} with the value stated. An absent value is only accepted for CF_Greater and the default compare (it reads 0) and then the link must carry a `premise`; returns (op, used_premise)"""
    func, value, query = op.get("func"), op.get("value"), op.get("query")
    used = False
    if func is None: func = "CF_GreaterEqual" if query == "QF_DoesExist" else "CF_Equal"
    if not str(func).startswith("CF_"): sys.exit("refusing %s: the comparison is not stated in the file (func %r)" % (who, func))
    if value is None:
        if func not in ("CF_Greater", "CF_Equal"): sys.exit("refusing %s: the comparison value is not stated and %s has no reading for it" % (who, func))
        value = 0; used = True
    o = dict(func=func, value=value)
    if query: o["query"] = query
    return o, used


def evidence_of(rec, who):
    ev = [dict(file=e["file"], block=e["block"], note=e["note"]) for e in rec.get("evidence") or []]
    if not ev: sys.exit("refusing %s: no evidence" % who)
    return ev


def check_wording(l, who):
    for k in ("trigger_label", "trigger_short", "trigger_phase"):
        if not str(l.get(k, "")).strip(): sys.exit("refusing %s: %s is empty" % (who, k))
    if not l["trigger_label"][:1].islower() or (l["trigger_label"].endswith(".") and not l["trigger_label"].endswith("...")): sys.exit("refusing %s: the trigger label is not a lowercase noun phrase that reads after 'at', without a full stop: %r" % (who, l["trigger_label"]))


def convert(rec, quests):
    """one record of `pairs` -> one link of kind 'fact'; SystemExit with the reason when it may not be shipped"""
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
    ev = evidence_of(rec, who)
    if rec.get("gaps"):
        sys.exit("refusing %s: gaps are not empty (%d)" % (who, len(rec["gaps"])))
    eff = "unconfirmed" if str(rec.get("engine_effect", "")).startswith("unconfirmed") else str(rec.get("engine_effect") or "unconfirmed")
    o = dict(func=op["func"], value=op["value"])
    if op.get("query"): o["query"] = op["query"]
    link = dict(kind="fact", effect="Failure", failed_guid=rec["failed_guid"], failer_guid=rec["failer_guid"], fact=rec["fact"], op=o,
                trigger_phase=rec.get("trigger_phase") or phases(rec), trigger_label=h["trigger_label"], trigger_short=h["trigger_short"], evidence=ev, engine_effect=eff)
    if rec.get("window"): link["window"] = rec["window"]
    check_wording(link, who)
    return link


def convert_cov(rec, quests):
    """one record of `coverage` -> one link of any kind"""
    who = "%s (%s)" % (rec.get("checklist_entry"), rec.get("kind"))
    if rec.get("status") != "verified_gamefiles":
        sys.exit("refusing %s: status is %r, only \"verified_gamefiles\" may be shipped" % (who, rec.get("status")))
    kind = rec.get("kind")
    if kind not in KINDS: sys.exit("refusing %s: unknown kind %r (one of %s)" % (who, kind, ", ".join(KINDS)))
    failer = (rec.get("found_failer") or {}).get("guid")
    for k, g in (("failed_guid", rec.get("failed_guid")), ("failer_guid", failer)):
        if not GUID.fullmatch(str(g)) or g not in quests: sys.exit("refusing %s: %s %r is not a quest of data/QUESTS.json" % (who, k, g))
    if rec.get("gaps"): sys.exit("refusing %s: gaps are not empty (%d)" % (who, len(rec["gaps"])))
    for k in KIND_NEEDS[kind]:
        if not rec.get(k) and not (k == "op" and rec.get("op_original")): sys.exit("refusing %s: kind %s needs %s" % (who, kind, k))
    eff = rec.get("effect")
    if eff not in EFFECTS: sys.exit("refusing %s: effect %r (Failure or Deactivate)" % (who, eff))
    link = dict(kind=kind, effect=eff, failed_guid=rec["failed_guid"], failer_guid=failer)
    used = False
    if rec.get("fact"):
        if not rec.get("op_original"): sys.exit("refusing %s: a fact with no comparison" % who)
        link["fact"] = rec["fact"]; link["op"], used = norm_op(rec["op_original"], kind, who)
    if used and not rec.get("premise"): sys.exit("refusing %s: the comparison value is absent in the file and the record has no premise" % who)
    link.update(trigger_phase=rec.get("trigger_phase") or "", trigger_label=rec.get("trigger_label") or "", trigger_short=rec.get("trigger_short") or "")
    for k in ("trigger_gerund", "condition", "unless_group", "choice", "safe", "journal", "flow"):
        if rec.get(k): link[k] = rec[k]
    if rec.get("premise"): link["premise"] = "; ".join(rec["premise"]) if isinstance(rec["premise"], list) else str(rec["premise"])
    if rec.get("window") and kind == "fact" and rec.get("shipped"): link["window"] = rec["window"]
    link["evidence"] = evidence_of(rec, who)
    link["engine_effect"] = "unconfirmed" if str(rec.get("engine_effect", "")).startswith("unconfirmed") else str(rec.get("engine_effect") or "unconfirmed")
    check_wording(link, who)
    return link


def share(links):
    """evidence items that SHARE_MIN or more links have in common go to one table; a link keeps the index (an int) in place of the item"""
    cnt = {}
    for l in links:
        for e in {(e["file"], e["block"], e["note"]) for e in l["evidence"]}: cnt[e] = cnt.get(e, 0) + 1
    table = [e for e, n in sorted(cnt.items()) if n >= SHARE_MIN]
    idx = {e: i for i, e in enumerate(table)}
    for l in links:
        l["evidence"] = [idx[(e["file"], e["block"], e["note"])] if (e["file"], e["block"], e["note"]) in idx else e for e in l["evidence"]]
    return [dict(file=f, block=b, note=n) for f, b, n in table]


def build(cand, quests, include=()):
    pairs = cand["pairs"] if isinstance(cand, dict) else cand
    cov = cand.get("coverage", []) if isinstance(cand, dict) else []
    recs = [("pairs", r) for r in pairs] + [("coverage", r) for r in cov]
    for src, r in recs:
        name = "%s <- %s" % (r.get("failed_id"), r.get("failer_id")) if src == "pairs" else r.get("checklist_entry")
        if r.get("status") not in STATUSES: sys.exit("refusing %s: unknown status %r" % (name, r.get("status")))
        if r["status"] == "rejected" and not str(r.get("rejection") or "").strip(): sys.exit("refusing %s: rejected without a reason" % name)
    by_failed = {}
    for src, r in recs: by_failed.setdefault(r.get("failed_guid"), []).append((src, r))
    cv = lambda src, r: convert(r, quests) if src == "pairs" else convert_cov(r, quests)
    for g in include:
        if g not in by_failed: sys.exit("refusing %s: not in the candidates file" % g)
        for src, r in by_failed[g]:
            if not (src == "coverage" and r.get("shipped")): cv(src, r)               # stops when it is not verified
    shipped_pairs = {(r["failed_guid"], r["failer_guid"]) for src, r in recs if src == "pairs" and r["status"] == "verified_gamefiles"}
    links = []
    for src, r in recs:
        if r["status"] != "verified_gamefiles": continue
        if src == "coverage" and r.get("shipped"): continue              # the pairs list holds the first three, with their own evidence
        links.append(cv(src, r))
    if not links: sys.exit("nothing is verified_gamefiles: nothing to write")
    seen = set()
    for l in links:
        k = (l["failer_guid"], l["failed_guid"], l.get("fact") or l.get("journal") or l.get("flow"))
        if k in seen: sys.exit("two links for %s" % (k,))
        seen.add(k)
    links.sort(key=lambda l: (l["failer_guid"], l["failed_guid"], l.get("fact") or ""))
    ev = share(links)
    refused = [r for src, r in recs if r["status"] != "verified_gamefiles"]
    left = [r for r in refused if r["status"] == "candidate"]
    data = dict(v=1, links=links, candidates=len(left))                  # candidates = how many records are still being checked (not the rejected, not_a_fail or not_found ones): a number only
    if ev: data["ev"] = ev
    return data, refused


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default=str(CANDIDATES)); ap.add_argument("--out", default=str(OUT)); ap.add_argument("--quests", default=str(ROOT / "data" / "QUESTS.json"))
    ap.add_argument("--include", action="append", default=[], help="a failed quest GUID that must be shipped (stops when its record is not verified)"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cand = json.loads(Path(a.candidates).read_text(encoding="utf-8")); quests = {q["g"] for q in json.loads(Path(a.quests).read_text(encoding="utf-8"))["quests"]}
    data, refused = build(cand, quests, a.include); blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False) + "\n"
    print("%d verified link(s) written; %d record(s) refused (status is not verified_gamefiles): %d candidate (counted), %d rejected / not_a_fail / not_found" % (len(data["links"]), len(refused), data["candidates"], len(refused) - data["candidates"]), file=sys.stderr)
    if a.check:
        ok = Path(a.out).read_text(encoding="utf-8") == blob; print("OK: matches" if ok else "DIFFERENT: run tools/build_quest_fails.py"); sys.exit(0 if ok else 1)
    Path(a.out).write_text(blob, encoding="utf-8"); print("wrote %s (%d bytes)" % (a.out, len(blob)), file=sys.stderr)


if __name__ == "__main__":
    main()
