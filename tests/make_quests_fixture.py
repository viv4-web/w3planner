#!/usr/bin/env python3
"""Write the FAKE Quests journal text the tests build the site with (tests/fixtures/quests): invented sentences for every quest of data/QUESTS.json, same layout as
tools/make_quests.py writes to the art folder ({quest id: {"d": [journal entry, ...], "o": [objective title, ...]}}). Nothing here is game content.

    python tests/make_quests_fixture.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures" / "quests"
RICH = {"mq1002 Rezydencja": 1, "Q107 Swamps": 0}      # entry number that carries a second paragraph, italics and bold, to test the markup


def main():
    qs = json.loads((ROOT / "data/QUESTS.json").read_text(encoding="utf-8"))["quests"]; desc = {}
    for q in qs:
        d = ["Invented journal entry %d." % (i + 1) for i in range(len(q["d"]))]
        if q["id"] in RICH and d: d[RICH[q["id"]]] = "Invented journal text, paragraph one.<br>Paragraph two has <i>italics</i> and a <b>bold</b> word."
        desc[q["id"]] = {"d": d, "o": ["Invented objective %d." % (i + 1) for i in range(len(q["o"]))]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "desc.json").write_text(json.dumps(desc, separators=(",", ":")) + "\n", encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({"version": 1, "counts": {"quests": len(qs), "descriptions": len(desc)}, "files": ["desc.json"], "sha1": "fake"}) + "\n")
    print("wrote", len(desc), "fake quests")


if __name__ == "__main__":
    main()
