#!/usr/bin/env python3
"""Regenerate the placeholder art (art/placeholder/*) from code.

    python tools/artgen/generate.py --check          compare what the code draws with the committed files
    python tools/artgen/generate.py --write         overwrite the committed files

Needs Pillow and numpy. The drawing is deterministic on one machine; other Pillow/numpy versions can differ by a few
pixels, so --check compares decoded pixels and reports whether the bytes are identical too.
"""
import argparse, io, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import artgen as A
from PIL import Image


def encode(im, fmt, q=None):
    b = io.BytesIO()
    if fmt == "jpg":
        im.convert("RGB").save(b, "JPEG", quality=q, optimize=True)
    else:
        im.save(b, "PNG", optimize=True)
    return b.getvalue()


def jobs():
    """id -> (image, format, jpeg quality). Ids are the slot names used in art/manifest.json."""
    J = {}
    add = lambda i, im, f="png", q=None: J.__setitem__(i, (im, f, q))
    for i in range(5): add("ga/treebg-%d" % i, A.tree_bg(i), "jpg", 84)
    for i in range(4):
        add("ga/tilebg-%d" % i, A.tile_bg(i))
        add("ga/tilefr-%d" % i, A.frame(128, A.TREE[i]["glow"] + (255,), 4))
    add("ga/fravail", A.frame(128, (150, 140, 125, 255), 3)); add("ga/frlock", A.frame(128, (72, 66, 58, 255), 3)); add("ga/frsel", A.sel_frame(152))
    for k in range(5): add("ga/tab-%d" % k, A.tab_icon(k))
    bars = {"red": (200, 50, 40), "blue": (40, 100, 220), "green": (60, 140, 40), "amber": (190, 120, 30)}
    for c, rgb in bars.items(): add("ga/bar-" + c, A.bar(rgb))
    for c in ("green", "red", "blue"): add("css/bar-" + c, A.bar(bars[c]))
    add("ga/orn", A.ornament())
    for k in ("grey", "red", "blue", "green", "gold"): add("ga/cell-" + k, A.cell_img(k))
    add("ga/master", A.master_img()); add("ga/mutbg", A.mut_bg(), "jpg", 82); add("ga/msel", A.sel_ring())
    data = json.loads((ROOT / "data" / "DATA.json").read_text(encoding="utf-8"))
    extra = json.loads((ROOT / "data" / "EXTRA.json").read_text(encoding="utf-8"))
    for ti, tree in enumerate(extra):
        for j, row in enumerate(tree):
            add("skill/" + data[ti][j][0], A.skill_icon(row[0], ti, j))
    for m in json.loads((ROOT / "data" / "MUT.json").read_text(encoding="utf-8")):
        add("mutation/%d" % m["n"], A.mutation_icon(m["n"]))
    for ci, c in enumerate(("red", "blue", "green")):
        for t in range(3): add("mutagen/%d" % (ci * 3 + t), A.mutagen_img(c, t))
        add("mutagen/%d" % (9 + ci), A.mutagen_unique(c))
    for slot in A.ITEM_SLOTS: add("items/ph-" + slot, A.item_placeholder(slot))
    for kind in A.CONS_KINDS: add("cons/ph-" + kind, A.cons_placeholder(kind))
    add("art/skill_slot_empty", A.slot_empty()); add("art/skill_slot_locked", A.padlock()); add("art/mutagen_slot_empty", A.mut_slot_empty())
    add("lock/sock", A.padlock()); add("lock/slot", A.padlock())
    add("css/body-bg", A.helix_bg()); add("img/skill-point", A.skill_point())
    return J


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true"); g.add_argument("--write", action="store_true")
    a = ap.parse_args()
    manifest = json.loads((ROOT / "art" / "manifest.json").read_text())
    J = jobs()
    missing = sorted({k for k, v in manifest.items() if "placeholder_as" not in v} ^ set(J))  # slots that borrow another slot's placeholder draw nothing of their own
    if missing: sys.exit("generator and manifest disagree on: %s" % missing[:8])
    same_bytes = same_pixels = 0; bad = []
    for sid, (im, fmt, q) in J.items():
        dest = ROOT / "art" / "placeholder" / ("%s.%s" % (sid, manifest[sid]["placeholder"]))
        blob = encode(im, fmt, q)
        if a.write:
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(blob); continue
        cur = dest.read_bytes()
        if cur == blob: same_bytes += 1; same_pixels += 1
        else:
            x, y = Image.open(io.BytesIO(cur)), Image.open(io.BytesIO(blob))
            (same_pixels := same_pixels + 1) if (x.size == y.size and x.convert("RGBA").tobytes() == y.convert("RGBA").tobytes()) else bad.append(sid)
    if a.write: print("wrote %d files" % len(J)); return
    print("%d images: %d byte-identical, %d pixel-identical, %d different" % (len(J), same_bytes, same_pixels, len(bad)))
    if bad: sys.exit("different: %s" % bad[:8])


if __name__ == "__main__":
    main()
