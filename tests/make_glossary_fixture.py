#!/usr/bin/env python3
"""Write the tiny FAKE Glossary content the tests build the site with (tests/fixtures/glossary). Invented text and drawn 24 px pictures:
nothing here is game content. Same file layout as tools/build_glossary.py makes (docs/GLOSSARY.md). Run it again only to change the fixture.

    python tests/make_glossary_fixture.py
"""
import io, json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures" / "glossary"
cons = {i["id"]: i for i in json.loads((ROOT / "data/consumables.json").read_text(encoding="utf-8"))["items"]}


def pic(rel, color, size=24):
    im = Image.new("RGBA", (size, size), color + (255,)); d = ImageDraw.Draw(im); d.ellipse([size // 4, size // 4, size * 3 // 4, size * 3 // 4], fill=(255, 255, 255, 200))
    b = io.BytesIO(); im.save(b, "WEBP", quality=80); p = OUT / "img" / (rel + ".webp"); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b.getvalue()); return "@@gimg:%s@@" % rel


def item(i): return {"k": "item", "id": i, "name": cons[i]["name"]}


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mk = lambda id, name, group, color, stages, weak=None, note=None, img=True: {"id": id, "name": name, "group": group, "img": pic("bestiary/" + id, color) if img else None, "thumb": pic("bestiary/t/" + id, color, 16) if img else None,
                                                                                  "stages": stages, "weak": weak or [], **({"note": note} if note else {})}
    best = [mk("alpha_wolf", "Alpha Wolf", "Beasts", (120, 90, 60), ["<i>Never turn your back.</i><br>- a huntsman<br>", "<br>The pack leader is <font color=\"#CD7D03\">cunning</font> and <b>fast</b>. Use <<GUI_PC_Select>> to dodge."],
               [item("Beast Oil 2"), item("Swallow 1"), {"k": "sign", "name": "Aard"}]),
            mk("zoltan_hound", "Zoltán's Hound", "Beasts", (90, 60, 40), ["A hound owned by Zoltán Chivay, who swears it can count."], [item("Silver Dust Bomb 1"), item("Vampire Oil 1"), item("Black Blood 1"), {"k": "label", "name": "Chain Proto"}]),
            mk("boars_a", "Wild Boars", "Beasts", (100, 70, 50), ["Boars of the base game."], [item("Beast Oil 1")], "Base game"),
            mk("boars_b", "Wild Boars", "Beasts", (100, 80, 50), ["Boars of Toussaint."], [item("Beast Oil 3")], "Blood and Wine"),
            mk("griffin", "Griffin", "Relicts", (60, 80, 110), ["A griffin nests on the cliff.", "Griffins hate Yrden."], [{"k": "sign", "name": "Yrden"}, {"k": "sign", "name": "Igni"}]),
            mk("stone_golem", "Stone Golem", "Relicts", (80, 80, 80), ["Test of inert markup: <script>window.__pwned=1</script><img src=x onerror=\"window.__pwned=2\"> stays text."], [], None, False)]
    best.sort(key=lambda e: (["Beasts", "Relicts"].index(e["group"]), e["name"].lower()))   # the build tool writes entries in display order
    dump("bestiary.json", {"tab": "bestiary", "groups": ["Beasts", "Relicts"], "entries": best})
    ch = lambda id, name, group, color, stages: {"id": id, "name": name, "group": group, "img": pic("characters/" + id, color), "thumb": pic("characters/t/" + id, color, 16), "stages": stages}
    chars = [ch("ada", "Ada Quill", "Base game", (140, 60, 60), ["A bard of some renown."]), ch("bram", "Bram the Smith", "Base game", (60, 120, 60), ["Forges swords.", "He also mends pots.", "Tells no one why."]),
             ch("cleo", "Cleó of the Fen", "Hearts of Stone", (70, 70, 140), ["Keeps bees."]), ch("dov", "Dov Marrow", "Blood and Wine", (130, 110, 40), ["A knight errant.", "Afraid of geese."])]
    dump("characters.json", {"tab": "characters", "groups": ["Base game", "Hearts of Stone", "Blood and Wine"], "entries": chars})
    tut = [{"id": "TutA", "name": "Combat basics", "group": "Combat", "img": None, "stages": ["Press <<GUI_PC_Select>> to strike."], "variants": 1},
           {"id": "TutB", "name": "Dodging", "group": "Combat", "img": None, "stages": ["Dodge with the <b>dodge key</b>."], "variants": 2},
           {"id": "TutC", "name": "Motion Patterns", "group": "Console", "img": pic("tutorials/motion", (200, 200, 200), 40), "stages": ["Roll the controller to the right."], "variants": 1},
           {"id": "TutD", "name": "Motion Patterns", "group": "Signs", "img": None, "stages": ["Another one with the same name."], "variants": 1}]
    tg = ["Combat", "Console", "Signs"]; tut.sort(key=lambda e: (tg.index(e["group"]), e["name"].lower()))
    dump("tutorial.json", {"tab": "tutorial", "groups": tg, "entries": tut})
    bk = lambda id, name, kind, color: {"id": id, "name": name, "kind": kind, "group": "Books", "img": pic("books/" + id, color, 16), "thumb": "@@gimg:books/%s@@" % id}
    idx = [bk("bk1", "A Treatise on Wolves", "book", (110, 70, 40)), bk("bk2", "Letter from Ada", "note", (200, 180, 120)), bk("bk3", "Orders of the Day", "quest", (150, 150, 100)),
           {"id": "pt1", "name": "Portrait of a Bard", "kind": "painting", "group": "Paintings & maps", "img": pic("paintings/pt1", (150, 90, 90), 32), "thumb": pic("paintings/t/pt1", (150, 90, 90), 16), "note": "1 of 2"},
           {"id": "pt2", "name": "Portrait of a Bard", "kind": "painting", "group": "Paintings & maps", "img": pic("paintings/pt2", (90, 90, 150), 32), "thumb": pic("paintings/t/pt2", (90, 90, 150), 16), "note": "2 of 2"}]
    dump("books_index.json", {"tab": "books", "groups": ["Books", "Paintings & maps"], "entries": idx})
    dump("books_book.json", {"kind": "book", "text": {"bk1": "Wolves are <i>shy</i>.<br><br>Chapter two: why the wolf is not a dog."}})
    dump("books_note.json", {"kind": "note", "text": {"bk2": "Dear friend,<br>the wolf trouble is over. Zoltán says hello."}})
    dump("books_quest.json", {"kind": "quest", "text": {"bk3": "Take the wolf pelts to the smith."}})
    files = sorted(p.name for p in OUT.glob("*.json") if p.name != "manifest.json")
    (OUT / "manifest.json").write_text(json.dumps({"version": 1, "fake": True, "counts": {"bestiary": len(best), "characters": len(chars), "tutorial": len(tut), "books": 3, "paintings": 2}, "files": {f: 0 for f in files}}, indent=1) + "\n", encoding="utf-8")
    print("wrote", OUT, "(%d files)" % sum(1 for _ in OUT.rglob("*") if _.is_file()))


if __name__ == "__main__":
    main()
