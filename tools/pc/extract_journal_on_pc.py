#!/usr/bin/env python3
"""Glossary spike, step 1 (run on the PC that has the game). Python 3, nothing to install, READ-ONLY on the game folder, no network.

    python extract_journal_on_pc.py --game-dir "D:\\SteamLibrary\\steamapps\\common\\The Witcher 3"

Keep it in the same folder as extract_on_pc.py (it reuses that file's bundle and texture.cache readers).
It looks in EVERY .bundle under the game folder (content\\content0.., dlc\\*, remaster folders) and copies, unchanged, every file whose path
has a "journal" folder and ends in .journal or .w2je (the bestiary, characters, glossary, tutorials, books and quest journals, base game and DLC),
and it lists every name in every texture.cache (name, width, height, format) so the journal pictures can be found afterwards.
Output: ONE zip on your Desktop, w3planner-journal.zip: journal/<bundle>/<path inside the bundle>, manifest.txt (bundle, path, size, sha256 of each file),
texture-index.txt, report.txt. It prints the zip's SHA256. It refuses to write inside the game folder.
"""
import argparse, hashlib, os, struct, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_on_pc as K


def journal_entries(path):
    """[dict(name, off, size, zsize, comp)] of the journal files of one bundle; None if it is not a bundle."""
    f = K.open_ro(path); out = []
    try:
        h = f.read(K.HEADER)
        if h[:8] != K.BUNDLE_MAGIC: return None
        table = struct.unpack("<3I", h[8:20])[2]; raw = f.read(table)
        for k in range(table // K.ENTRY):
            e = raw[k * K.ENTRY:(k + 1) * K.ENTRY]; name = e[:256].split(b"\0")[0].decode("latin1"); low = name.lower().replace("\\", "/")
            if (low.endswith(".journal") or low.endswith(".w2je")) and ("/journal/" in low or low.startswith("journal/")):
                off, _, size, zsize, crc, comp = struct.unpack("<6I", e[272:296]); out.append({"name": name, "off": off, "size": size, "zsize": zsize, "comp": comp})
    finally:
        f.close()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir"); ap.add_argument("--out", help="the zip to write (default: w3planner-journal.zip on the Desktop)")
    a = ap.parse_args(argv)
    game = a.game_dir or next((d for d in K.GAME_DIRS if os.path.isdir(d)), None)
    while not game or not os.path.isdir(game):
        game = input("Folder of your Witcher 3 installation (the one that contains 'content'): ").strip().strip('"')
    out = os.path.abspath(a.out or os.path.join(K.desktop(), "w3planner-journal.zip"))
    if K.inside(out, game): sys.exit("refusing to write the zip inside the game folder: %s" % out)
    caches, bundles = K.find_files(game); tmp = out + ".part"
    report = ["game folder: %s" % game, "bundles: %d, texture.cache files: %d" % (len(bundles), len(caches))]; manifest = ["bundle\tpath\tsize\tsha256"]; n = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for b in bundles:
            rel = os.path.relpath(b, game).replace("\\", "/")
            try: ents = journal_entries(b)
            except Exception as ex: report.append("skipped bundle %s: %s" % (rel, ex)); continue
            if not ents: continue
            f = K.open_ro(b)
            try:
                for e in ents:
                    try: data = K.read_entry(f, e)
                    except Exception as ex: report.append("FAILED %s in %s: %s" % (e["name"], rel, ex)); continue
                    z.writestr("journal/%s/%s" % (rel.replace("/", "__"), e["name"].replace("\\", "/")), data); n += 1
                    manifest.append("%s\t%s\t%d\t%s" % (rel, e["name"], len(data), hashlib.sha256(data).hexdigest()))
            finally:
                f.close()
            report.append("%s: %d journal files" % (rel, len(ents)))
        tex = ["cache\tname\twidth\theight\tformat"]
        for c in caches:
            try:
                for e in K.read_cache(c): tex.append("%s\t%s\t%d\t%d\t0x%x" % (os.path.relpath(c, game).replace("\\", "/"), e["name"], e["w"], e["h"], e["fmt"]))
            except Exception as ex: report.append("skipped %s: %s" % (c, ex))
        report.append("journal files: %d, texture names: %d" % (n, len(tex) - 1))
        z.writestr("manifest.txt", "\n".join(manifest) + "\n"); z.writestr("texture-index.txt", "\n".join(tex) + "\n"); z.writestr("report.txt", "\n".join(report) + "\n")
    os.replace(tmp, out)
    with K.open_ro(out) as zf: digest = hashlib.sha256(zf.read()).hexdigest()
    print("%d journal files, %d texture names, %d bytes (%.1f MB)\n%s\nSHA256 %s" % (n, len(tex) - 1, os.path.getsize(out), os.path.getsize(out) / 1048576.0, out, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
