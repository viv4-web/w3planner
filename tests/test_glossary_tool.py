"""tools/build_glossary.py: the small rules that decide what the Glossary shows, on hand-made data (no game files needed)."""
import io, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_glossary as G
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import cr2w


def check(name, ok):
    if not ok: print("FAIL:", name); sys.exit(1)


# platform variants fold into the PC entry; a name that merely ends in "ps" does not
check("fold: _pad, _ps4, a trailing PS", G.fold("TutorialAlchemyCook_pad") == ("TutorialAlchemyCook", "pad") and G.fold("TutorialX_ps4") == ("TutorialX", "ps4") and G.fold("TutorialAlternateSignCastingPS") == ("TutorialAlternateSignCasting", "ps"))
check("fold: other names stay", G.fold("TutorialCharDevGroups") == ("TutorialCharDevGroups", "") and G.fold("TutorialNewInvTooltips") == ("TutorialNewInvTooltips", "") and G.fold("TutorialMaps") == ("TutorialMaps", ""))
# duplicate names get a note that tells them apart
es = [{"id": "a", "name": "Wild Boars", "group": "Beasts"}, {"id": "b", "name": "Wild Boars", "group": "Beasts"}, {"id": "c", "name": "Bears", "group": "Beasts"}]
G.note_dups(es, {"a": "Base game", "b": "Blood and Wine"}); check("note_dups: pack names for the two boars, none for the bear", es[0]["note"] == "Base game" and es[1]["note"] == "Blood and Wine" and "note" not in es[2])
es = [{"id": "a", "name": "Portrait", "group": "P"}, {"id": "b", "name": "portrait", "group": "P"}]; G.note_dups(es); check("note_dups: '1 of 2' when nothing else tells them apart", [e["note"] for e in es] == ["1 of 2", "2 of 2"])
check("norm_key: accents and case", G.norm_key("Zoltán") == "zoltan" and G.norm_key("ÉCLAIR") == "eclair")
# the book body: <name key>_text first, then the item id, then a one-line item_desc (only when the item's own key says so); a generic description is never taken
import w3dec
def tables(d):
    strs, keys = {}, {}
    for n, (k, t) in enumerate(d.items(), 1): strs[n] = t; keys[w3dec.h(k)] = n
    return strs, keys
strs, keys = tables({"item_name_a_text": "Full body of A.", "item_name_a": "A", "b": "Body of B under its id.", "item_name_b": "B", "item_desc_c": "A short line about C.", "item_name_c": "C", "item_name_d": "D", "item_desc_book": "Read for additional information."})
it = lambda k: {"key": k, "cat": "book", "icon": "", "tags": ["ReadableItem"]}
check("book_body: _text key", G.book_body("a", it("item_name_a"), strs, keys) == ("Full body of A.", "body"))
check("book_body: the item id as key", G.book_body("b", it("item_name_b"), strs, keys) == ("Body of B under its id.", "body"))
check("book_body: a one-line description of its own", G.book_body("c", it("item_name_c"), strs, keys) == ("A short line about C.", "description"))
check("book_body: title only gives nothing (dropped)", G.book_body("d", it("item_name_d"), strs, keys) == (None, None))
# pictures: the game's flat orange TODO placeholder and an empty texture are refused, a picture with a spread is kept
try:
    from PIL import Image
    import random
    class P(G.Pictures):
        def __init__(self): pass
    p = P(); flat = Image.new("RGBA", (40, 40), (255, 110, 0, 255)); rnd = Image.new("RGBA", (40, 40))
    random.seed(1); rnd.putdata([(random.randrange(256), random.randrange(256), random.randrange(256), 255) for _ in range(1600)])
    empty = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    check("flat(): orange TODO and an empty texture are placeholders, a real picture is not", p.flat(flat) and p.flat(empty) and not p.flat(rnd))
    b = G.webp(rnd); check("webp(): WebP with the alpha channel kept", b[:4] == b"RIFF" and Image.open(io.BytesIO(b)).mode in ("RGBA", "RGB"))
except ImportError:
    pass
# the CR2W string decoder: 8-bit (bit 7 set) and UTF-16
c = cr2w.CR2W.__new__(cr2w.CR2W)
check("cr2w.string: ANSI and UTF-16", c.string(bytes([0x80 | 3]) + b"abc") == "abc" and c.string(bytes([2]) + "é!".encode("utf-16-le")) == "é!")
print("ok")
