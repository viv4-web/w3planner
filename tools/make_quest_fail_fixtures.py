#!/usr/bin/env python3
"""Write tests/fixtures/quest_fails/<failed>_<failer>[_<fact>].json: one fixture per link of data/QUEST_FAILS.json (v39.5).

    python tools/make_quest_fail_fixtures.py          (writes the missing ones; the three of v39 are kept as they are)
    python tools/make_quest_fail_fixtures.py --check  (stops when a link has no fixture or a fixture disagrees with its link)

A fixture is what the test compares the shipped link with: the GUIDs, kind, fact, comparison, trigger phase, and the two blocks the link stands on (where the step is, where the Failure /
Deactivate input is) in the game's quest graphs. The block table below was read from the game files (coverage audit, v39.5); a test checks that both blocks are in the link's evidence.
No game text: names of our own quests as in QUESTS.json, file names, block numbers."""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FXD = ROOT / "tests" / "fixtures" / "quest_fails"
# (failed quest name, failer quest name, fact or None) -> (step file, step block, fail file, fail block). Files are given by name; the full path is the one in the link's evidence.
ISLE = ("q402_ciri.w2phase", 1047)
T = {
    ("A Favor for a Friend", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq101_keira.w2phase", 19),
    ("An Eye for an Eye", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq312_quest.w2phase", 6),
    ("A Dangerous Game", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq310_dangerous_game.w2phase", 1195),
    ("Cabaret", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq303_brothel.w2phase", 1274),
    ("A Deadly Plot", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq315_talar.w2phase", 9),
    ("Redania's Most Wanted", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq302_philippa.w2phase", 341),
    ("Now or Never", "The Isle of Mists", "q402_escort_completed"): ISLE + ("q309_casablanca.w2phase", 212),
    ("A Matter of Life and Death", "The Isle of Mists", "q402_escort_completed"): ISLE + ("sq301_triss.w2phase", 5),
    ("Return to Crookback Bog", "The Isle of Mists", "q402_escort_completed"): ISLE + ("q107_swamps.w2phase", 1114),
    ("Ciri's Room", "The Isle of Mists", "q402_escort_completed"): ISLE + ("q103_ciris_room.w2phase", 82),
    ("For the Advancement of Learning", "The Isle of Mists", "q402_escort_completed"): ISLE + ("q109_wrapup.w2phase", 234),
    ("An Invitation from Keira Metz", "The Isle of Mists", "q402_escort_completed"): ISLE + ("q106_tower.w2phase", 1018),
    ("Brothers In Arms: Skellige", "The Isle of Mists", "q402_skellige_allies_gathered"): ("q402_ciri.w2phase", 500, "q402_ciri.w2phase", 1097),
    ("Brothers In Arms: Novigrad", "The Isle of Mists", "q402_novigrad_allies_gathered"): ("q402_ciri.w2phase", 797, "q402_ciri.w2phase", 1084),
    ("Brothers In Arms: Nilfgaard", "The Isle of Mists", "q402_talked_to_emhyr"): ("q402_ciri.w2phase", 1011, "q402_ciri.w2phase", 1062),
    ("Brothers In Arms: Velen", "The Isle of Mists", "q109_keira_to_km"): ("q109_wrapup.w2phase", 172, "q402_ciri.w2phase", 1077),
    ("Brothers In Arms: Velen", "For the Advancement of Learning", "q109_keira_defeated"): ("q109_wrapup.w2phase", 61, "q402_ciri.w2phase", 761),
    ("Brothers In Arms: Velen", "For the Advancement of Learning", "q109_keira_to_radovid"): ("q109_wrapup.w2phase", 180, "q402_ciri.w2phase", 761),
    ("Brothers In Arms: Velen", "A Favor for a Friend", "sq101_date_with_keira_was_failed"): ("sq101_keira.w2phase", 405, "q402_ciri.w2phase", 761),
    ("Possession", "Battle Preparations", "q210_on_quest"): ("q210_precanaris.w2phase", 1871, "q203_him.w2phase", 1542),
    ("King's Gambit", "Battle Preparations", "q210_on_quest"): ("q210_precanaris.w2phase", 1871, "q206_berserkers.w2phase", 1656),
    ("Coronation", "Battle Preparations", "q210_on_quest"): ("q210_precanaris.w2phase", 1871, "q208_heroesmead.w2phase", 210),
    ("Berengar's Blade", "The Battle of Kaer Morhen", "q403_council"): ("q403_council.w2phase", 159, "mq4005_sword.w2phase", 6),
    ("Missing in Action", "The Incident at White Orchard", "q002_prologue_point_of_no_return"): ("q002_emhyr.w2phase", 531, "mq0001_missing_brother.w2phase", 593),
    ("Twisted Firestarter", "The Incident at White Orchard", "q002_prologue_point_of_no_return"): ("q002_emhyr.w2phase", 531, "mq0005_dwarven_blacksmith.w2phase", 657),
    ("On Death's Bed", "The Incident at White Orchard", "q002_village_ending_sequence_started"): ("q002_emhyr.w2phase", 539, "part_1_sidequests.w2phase", 87),
    ("Contract: Devil by the Well", "Imperial Audience", "q002_left_village"): ("q002_emhyr.w2phase", 351, "mq0003_freshwater.w2phase", 1130),
    ("Contract: Devil by the Well", "On Thin Ice", "q501_naglfar_arrived"): ("q501_eredin.w2phase", 1268, "mq0003_freshwater.w2phase", 1146),
    ("Reason of State", "On Thin Ice", "q501_naglfar_arrived"): ("q501_eredin.w2phase", 1268, "mq3035_emhyr.w2phase", 29),
    ("The Soldier Statuette", "Battle Preparations", None): ("bugfixing_phase.w2phase", 2103, "bugfixing_phase.w2phase", 2076),
    ("A Midnight Clear", "Dead Man's Party", "q602_done"): ("q602_wedding.w2phase", 514, "q602_romance.w2phase", 262),
    ("Flesh for Sale", "Following the Thread", "sq106_hammond_knows"): ("sq106_hammond.w2phase", 45, "mq2020_flesh_for_cash_business.w2phase", 81),
    ("Amidst the Mill's Grist", "Where Children Toil, Toys Waste Away", None): ("q702_hunt.w2phase", 75, "q702_hunt.w2phase", 33),
    ("The Warble of a Smitten Knight", "The Night of Long Fangs", "q704_long_night_starts"): ("q704_01_beginning.w2phase", 42, "sq701_tournament.w2phase", 4399),
    ("The Perks of Being a Jailbird", "Burlap is the New Stripe", "q705_stash_disabled"): ("q705_epilog.w2phase", 1204, "q705_epilog.w2phase", 1836),
    ("A Frying Pan, Spick and Span", "On Thin Ice", "q501_naglfar_arrived"): ("q501_eredin.w2phase", 1268, "mq0004_locked_shed.w2phase", 191),
    ("Precious Cargo", "On Thin Ice", "q501_naglfar_arrived"): ("q501_eredin.w2phase", 1268, "mq0002_missing_goods.w2phase", 508),
    ("Faithful Friend", "Something Ends, Something Begins", None): ("q504_ciri_empress.w2phase", 33, "q504_ciri_empress.w2phase", 58),
    ("The Lord of Undvik", "Through Time and Space", "q210_quest_start"): ("q210_depart_novigrad.w2phase", 7, "q202_giant.w2phase", 2936),
    ("The Gangs of Novigrad", "Get Junior", "q302_whoreson_found"): ("q302_mafia.w2phase", 660, "cleaver.w2phase", 95),
    ("Duck, Duck, Goosed!", "Beyond Hill and Dale...", "q704_ft_goose_done"): ("q704_02_fairy_tale.w2phase", 19, "q704_02_fairy_tale.w2phase", 23),
}


def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def evidence(l, table):
    return [dict(table[e]) if isinstance(e, int) else e for e in l["evidence"]]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    d = json.loads((ROOT / "data" / "QUEST_FAILS.json").read_text(encoding="utf-8")); qs = {q["g"]: q for q in json.loads((ROOT / "data" / "QUESTS.json").read_text(encoding="utf-8"))["quests"]}
    old = {f.name for f in FXD.glob("*.json")}; made = set(); bad = []
    for l in d["links"]:
        failed, failer = qs[l["failed_guid"]], qs[l["failer_guid"]]
        key = (failed["n"], failer["n"], l.get("fact"))
        if l["kind"] in ("journal_status", "flow") and key not in T: key = (failed["n"], failer["n"], None)
        row = T.get(key)
        name = "%s_%s%s.json" % (slug(failed["id"]), slug(failer["id"]), ("_" + l["fact"]) if l.get("fact") and sum(1 for x in d["links"] if x["failed_guid"] == l["failed_guid"] and x["failer_guid"] == l["failer_guid"]) > 1 else "")
        # the three links of v39 keep their fixture names (sq106_q401, sq202_q401, sq209_q206)
        legacy = {("SQ106 Killbill", "Q401 Konsylium"): "sq106_q401.json", ("SQ202 Yen", "Q401 Konsylium"): "sq202_q401.json", ("SQ209 Cave of Dreams", "Q206 Berserkers"): "sq209_q206.json"}
        name = legacy.get((failed["id"], failer["id"]), name); made.add(name)
        if name in legacy.values():
            if not (FXD / name).exists(): bad.append(name)
            continue
        if row is None: sys.exit("no block row in T for %s" % (key,))
        fx = {"link": "%s: %s fails %s" % (l["kind"], l.get("fact") or l["trigger_short"], failed["n"]), "kind": l["kind"], "failed_guid": failed["g"], "failed_name": failed["n"], "failed_id": failed["id"],
              "failer_guid": failer["g"], "failer_name": failer["n"], "failer_id": failer["id"], "fact": l.get("fact"), "op": l.get("op"), "effect": l["effect"],
              "setter_file": next(e["file"] for e in evidence(l, d.get("ev", [])) if e["file"].endswith("/" + row[0]) and e["block"] == row[1]), "setter_block": row[1],
              "fail_file": next(e["file"] for e in evidence(l, d.get("ev", [])) if e["file"].endswith("/" + row[2]) and e["block"] == row[3]), "fail_block": row[3],
              "trigger_phase": l["trigger_phase"], "trigger_scene": None, "status": "verified_gamefiles", "engine_effect": "unconfirmed"}
        txt = json.dumps(fx, indent=1, ensure_ascii=False)
        p = FXD / name
        if a.check:
            if not p.exists() or json.loads(p.read_text(encoding="utf-8")) != fx: bad.append(name)
        else: p.write_text(txt, encoding="utf-8")
    extra = sorted(old - made) if not a.check else sorted({f.name for f in FXD.glob("*.json")} - made)
    if bad or extra: sys.exit("fixtures out of step: missing / different %s, with no link %s" % (bad, extra))
    print("%d fixtures for %d links" % (len(made), len(d["links"])))


if __name__ == "__main__":
    main()
