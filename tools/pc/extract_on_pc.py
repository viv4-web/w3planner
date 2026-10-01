#!/usr/bin/env python3
"""Pull a few files out of your Witcher 3 game folder into ONE zip on your Desktop. Windows or Linux, Python 3, nothing to install.

    python extract_on_pc.py                      asks for the game folder (or finds it), uses missing-icons.txt next to this script
    python extract_on_pc.py --game-dir "C:\\Program Files (x86)\\Steam\\steamapps\\common\\The Witcher 3" --list missing-icons.txt

What it does:
  a) finds every texture.cache under the game folder, reads its index, and extracts ONLY the icons named in the list file
     (one icon path per line, like icons/inventory/armors/bear_armor_4_64x128.png; lines starting with # are ignored;
     anything after a tab is ignored) as raw .dds files (the top mip only, with a DDS header);
  b) finds every *.bundle under the game folder, reads each one's index, and extracts every file that matches
     gameplay/globals/*.csv (tooltip_settings.csv and its neighbours);
  c) writes everything into one zip (w3planner-extract.zip) on your Desktop, plus report.txt (what was found and what was not),
     and prints the number of files and the size.

Second mode, --wolf: looks in EVERY .bundle under the game folder (content0..content*, dlc\\*, the Next-Gen folders) for the definition XML of the Wolf School
gear whose lower tiers are missing from our data (Wolf Armor, Gloves, Pants, Boots, steel and silver swords: the base item and tiers 1-3 or 1-4, and the
NGP copies, with their "<id> _Stats" abilities). It writes w3planner-wolf.zip on the Desktop: every XML file that defines one of them (items and
items_plus, so New Game and New Game Plus), manifest.txt (bundle -> file -> ids), not-found.txt, report.txt and SHA256SUMS.

It only READS the game folder (every game file is opened read-only, nothing is written there, and it refuses to write the zip inside
the game folder). It uses no network: the only modules it imports are argparse, os, struct, sys, zipfile and zlib. Send the zip back.
"""
import argparse, hashlib, os, re, struct, sys, zipfile, zlib

CACHE_MAGIC = 1415070536
FMT = {0x07: b"DXT1", 0x08: b"DXT5", 0x0D: b"DXT3", 0x0A: "BC7", 0x0E: "BC4", 0x0F: "BC5", 0x00: "RGBA", 0xFD: "RGBA"}   # texture.cache format codes
BLOCK_BYTES = {b"DXT1": 8, b"DXT3": 16, b"DXT5": 16, "BC4": 8, "BC5": 16, "BC7": 16}
BUNDLE_MAGIC, HEADER, ENTRY = b"POTATO70", 32, 304
GAME_DIRS = [r"C:\Program Files (x86)\Steam\steamapps\common\The Witcher 3", r"C:\Program Files\Steam\steamapps\common\The Witcher 3",
             r"C:\GOG Games\The Witcher 3 Wild Hunt", r"C:\Program Files (x86)\GOG Galaxy\Games\The Witcher 3 Wild Hunt", r"D:\SteamLibrary\steamapps\common\The Witcher 3"]


def norm(path):
    """lower case, forward slashes, no extension: how paths are compared."""
    p = path.replace("\\", "/").lower().strip("/")
    for ext in (".png", ".xbm", ".dds", ".tga", ".csv"):
        if p.endswith(ext): return p[:-len(ext)]
    return p


def open_ro(path):
    return open(path, "rb")                                             # the only way this script opens a game file


# ---------- texture.cache ----------
def read_cache(path):
    """[entry dict] from a texture.cache index (footer 32 bytes, 52-byte entries, names)."""
    f = open_ro(path); f.seek(-32, 2)
    crc, used, count, strsize, mipcount, magic, ver = struct.unpack("<QIIIIII", f.read(32))
    if magic != CACHE_MAGIC: f.close(); raise ValueError("not a texture.cache")
    f.seek(-(32 + count * 52 + strsize + mipcount * 4), 2); f.read(mipcount * 4)
    names = f.read(strsize).split(b"\0")[:count]; f.seek(-(32 + count * 52), 2); entries = []
    for i in range(count):
        e = struct.unpack("<IiIIIIHHHHiiqBBBB", f.read(52))
        entries.append({"name": names[i].decode("utf-8", "replace"), "page": e[2], "w": e[6], "h": e[7], "fmt": e[13], "cube": e[15], "cache": path})
    f.close(); return entries


def dds_header(w, h, fmt):
    """DDS header for the top mip only. fmt: a FMT value."""
    flags = 0x1 | 0x2 | 0x4 | 0x1000
    if fmt == "RGBA":
        flags |= 0x8; linear = w * 4; pf = struct.pack("<II4sIIIII", 32, 0x41, b"\0\0\0\0", 32, 0xFF, 0xFF00, 0xFF0000, 0xFF000000)
    else:
        flags |= 0x80000; linear = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * BLOCK_BYTES[fmt]
        pf = struct.pack("<II4sIIIII", 32, 0x4, b"DX10" if fmt == "BC7" else {"BC4": b"ATI1", "BC5": b"ATI2"}.get(fmt, fmt), 0, 0, 0, 0, 0)
    hdr = b"DDS " + struct.pack("<IIIIIII", 124, flags, h, w, linear, 0, 1) + b"\0" * 44 + pf + struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
    if fmt == "BC7": hdr += struct.pack("<IIIII", 98, 3, 0, 1, 0)          # DXGI_FORMAT_BC7_UNORM, 2D texture
    return hdr


def top_mip_size(w, h, fmt):
    return w * h * 4 if fmt == "RGBA" else max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * BLOCK_BYTES[fmt]


def texture_dds(entry):
    """The icon as a .dds file's bytes."""
    fmt = FMT.get(entry["fmt"])
    if fmt is None: raise ValueError("unknown texture format 0x%x" % entry["fmt"])
    if entry["cube"]: raise ValueError("cube map")
    f = open_ro(entry["cache"])
    try:
        f.seek(entry["page"] * 4096); zsize, size, idx = struct.unpack("<IIB", f.read(9)); data = zlib.decompress(f.read(zsize))
    finally:
        f.close()
    need = top_mip_size(entry["w"], entry["h"], fmt)
    if len(data) < need: raise ValueError("texture data is %d bytes, %d expected" % (len(data), need))
    return dds_header(entry["w"], entry["h"], fmt) + data[:need]


def match_icons(wanted, entries):
    """{wanted path: entry or None}, {wanted path: reason}. A wanted path matches the entry whose path ends with the same last 4, then 3, then 2 parts (unique only)."""
    index = {}
    for e in entries:
        parts = norm(e["name"]).split("/")
        for k in (2, 3, 4):
            if len(parts) >= k: index.setdefault("/".join(parts[-k:]), []).append(e)
    found, why = {}, {}
    for w in wanted:
        parts = norm(w).split("/"); found[w] = None; why[w] = "no texture with that name"
        for k in (4, 3, 2):
            if len(parts) < k: continue
            hits = index.get("/".join(parts[-k:]), [])
            if len(hits) == 1: found[w] = hits[0]; why.pop(w, None); break
            if len(hits) > 1: why[w] = "%d textures match the last %d parts" % (len(hits), k); break
    return found, why


# ---------- bundles ----------
def snappy(data):
    i = n = shift = 0
    while True:
        b = data[i]; i += 1; n |= (b & 0x7F) << shift; shift += 7
        if b < 0x80: break
    out = bytearray()
    while i < len(data):
        tag = data[i]; i += 1; kind = tag & 3
        if kind == 0:
            ln = tag >> 2
            if ln >= 60: nb = ln - 59; ln = int.from_bytes(data[i:i + nb], "little"); i += nb
            ln += 1; out += data[i:i + ln]; i += ln; continue
        if kind == 1: ln = ((tag >> 2) & 7) + 4; off = ((tag >> 5) << 8) | data[i]; i += 1
        elif kind == 2: ln = (tag >> 2) + 1; off = int.from_bytes(data[i:i + 2], "little"); i += 2
        else: ln = (tag >> 2) + 1; off = int.from_bytes(data[i:i + 4], "little"); i += 4
        for _ in range(ln): out.append(out[-off])
    if len(out) != n: raise ValueError("snappy size mismatch")
    return bytes(out)


def lz4(data, size):
    i, out = 0, bytearray()
    while i < len(data):
        token = data[i]; i += 1; ln = token >> 4
        if ln == 15:
            while True:
                b = data[i]; i += 1; ln += b
                if b != 255: break
        out += data[i:i + ln]; i += ln
        if i >= len(data): break
        off = int.from_bytes(data[i:i + 2], "little"); i += 2; ml = token & 15
        if ml == 15:
            while True:
                b = data[i]; i += 1; ml += b
                if b != 255: break
        for _ in range(ml + 4): out.append(out[-off])
    if len(out) != size: raise ValueError("lz4 size mismatch")
    return bytes(out)


def bundle_csvs(path):
    """[(internal path, bytes or None, why not)] for every gameplay/globals/*.csv in one bundle."""
    f = open_ro(path); out = []
    try:
        h = f.read(HEADER)
        if h[:8] != BUNDLE_MAGIC: return None
        table = struct.unpack("<3I", h[8:20])[2]; raw = f.read(table)
        for k in range(table // ENTRY):
            e = raw[k * ENTRY:(k + 1) * ENTRY]; name = e[:256].split(b"\0")[0].decode("latin1"); low = name.replace("\\", "/").lower()
            if not low.endswith(".csv") or "gameplay/globals/" not in low or "/" in low.split("gameplay/globals/", 1)[1]: continue
            off, _, size, zsize, crc, comp = struct.unpack("<6I", e[272:296]); f.seek(off); blob = f.read(zsize)
            try:
                data = blob if comp == 0 else zlib.decompress(blob) if comp == 1 else snappy(blob) if comp == 2 else lz4(blob, size) if comp in (4, 5) else None
                out.append((name, data, None if data is not None else "compression %d is not supported here" % comp))
            except Exception as ex:
                out.append((name, None, "could not decompress: %s" % ex))
    finally:
        f.close()
    return out


# ---------- --wolf: item definition XML for the Wolf School gear ----------
WOLF_SLOTS = {"Wolf Armor": 3, "Wolf Gloves": 4, "Wolf Pants": 4, "Wolf Boots": 4, "Wolf School steel sword": 3, "Wolf School silver sword": 3}
WOLF_KNOWN = ["Wolf Armor 4", "Wolf Gloves 5", "Wolf Pants 5", "Wolf Boots 5", "Wolf School steel sword 4", "Wolf School silver sword 4"]   # controls: already in B&W, so the search must find them
WOLF_RE = re.compile(rb'<(item|ability)\b[^>]*?\bname\s*=\s*"((?:NGP )?Wolf (?:School|Armor|Gloves|Pants|Boots)[^"]*)"')   # a definition, not an item_cond / item_extension / loot reference


def wolf_ids():
    """[(id, is control)]: for every slot the base item and its tiers, with and without the NGP prefix."""
    out = []
    for base, top in WOLF_SLOTS.items():
        for pre in ("", "NGP "):
            out += [(pre + base, False)] + [("%s%s %d" % (pre, base, n), False) for n in range(1, top + 1)]
    out += [(pre + k, True) for k in WOLF_KNOWN for pre in ("", "NGP ")]
    return out


def bundle_xml(path):
    """[(internal path, bytes or None, why not)] for every .xml in one bundle (None for a bundle that is not one)."""
    f = open_ro(path); out = []
    try:
        h = f.read(HEADER)
        if h[:8] != BUNDLE_MAGIC: return None
        table = struct.unpack("<3I", h[8:20])[2]; raw = f.read(table)
        for k in range(table // ENTRY):
            e = raw[k * ENTRY:(k + 1) * ENTRY]; name = e[:256].split(b"\0")[0].decode("latin1")
            if not name.lower().endswith(".xml"): continue
            off, _, size, zsize, crc, comp = struct.unpack("<6I", e[272:296]); f.seek(off); blob = f.read(zsize)
            try:
                data = blob if comp == 0 else zlib.decompress(blob) if comp == 1 else snappy(blob) if comp == 2 else lz4(blob, size) if comp in (4, 5) else None
                out.append((name, data, None if data is not None else "compression %d is not supported here" % comp))
            except Exception as ex:
                out.append((name, None, "could not decompress: %s" % ex))
    finally:
        f.close()
    return out


def wolf_defs(data):
    """{(kind, name)} of the Wolf definitions in one XML file."""
    return {(m.group(1).decode(), m.group(2).decode("latin1")) for m in WOLF_RE.finditer(data)} if b"Wolf" in data else set()


def run_wolf(game, bundles, z, report):
    """Search every bundle, write the matching files plus manifest.txt, not-found.txt, report.txt and SHA256SUMS into z. Returns (files with a hit, wanted ids not found)."""
    ids = wolf_ids(); seen = {}; manifest = []; skipped = []; nxml = 0; hashes = []

    def put(arc, data):
        z.writestr(arc, data); hashes.append("%s  %s" % (hashlib.sha256(data).hexdigest(), arc))
    for b in bundles:
        rel = os.path.relpath(b, game).replace("\\", "/")
        try: res = bundle_xml(b)
        except Exception as ex: report.append("skipped bundle %s: %s" % (rel, ex)); continue
        if res is None: report.append("skipped %s: not a bundle" % rel); continue
        for name, data, reason in res:
            nxml += 1
            if data is None: skipped.append("%s :: %s (%s)" % (rel, name, reason)); continue
            defs = wolf_defs(data)
            if not defs: continue
            internal = name.replace("\\", "/"); put("xml/%s/%s" % (rel, internal), data)
            for kind, n in defs: seen.setdefault((kind, n), []).append("%s :: %s" % (rel, internal))
            manifest.append("%s -> %s\n      %s" % (rel, internal, "; ".join("%s %s" % (k, n) for k, n in sorted(defs, key=lambda d: (d[1], d[0])))))
    nf = []
    for i, ctl in ids:
        for kind, n in (("item", i), ("ability", i + " _Stats")):
            if (kind, n) not in seen: nf.append("%s %s%s" % (kind, n, "   (control: it is already in the B&W data, so a miss here means the search is wrong)" if ctl else ""))
    put("manifest.txt", ("bundle (relative to the game folder) -> file inside it, and the Wolf definitions found there\n\n" + ("\n".join(manifest) or "(nothing found)") + "\n").encode("utf-8"))
    put("not-found.txt", ("searched for, no definition found in any bundle:\n" + ("\n".join(nf) or "(everything was found)") + "\n\nXML files that could not be read (they may hide a definition):\n" + ("\n".join(skipped) or "(none)") + "\n").encode("utf-8"))
    report.append("searched %d bundles, %d xml files; %d files with a Wolf definition; %d wanted definitions not found; %d xml files unreadable" % (len(bundles), nxml, len(manifest), len(nf), len(skipped)))
    put("report.txt", ("\n".join(report) + "\n").encode("utf-8"))
    z.writestr("SHA256SUMS", "\n".join(hashes) + "\n")
    return len(manifest), nf


# ---------- the run ----------
def find_files(root):
    caches, bundles = [], []
    for d, _, names in os.walk(root):
        for n in names:
            if n.lower() == "texture.cache": caches.append(os.path.join(d, n))
            elif n.lower().endswith(".bundle"): bundles.append(os.path.join(d, n))
    return sorted(caches), sorted(bundles)


def read_list(path):
    out = []
    with open(path, encoding="utf-8-sig") as f:                         # the list file: read only
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"): out.append(line.split("\t")[0].strip())
    return out


def desktop():
    home = os.path.expanduser("~")
    for p in (os.path.join(os.environ.get("USERPROFILE", home), "Desktop"), os.path.join(os.environ.get("USERPROFILE", home), "OneDrive", "Desktop"), os.path.join(home, "Desktop")):
        if os.path.isdir(p): return p
    return home


def inside(path, folder):
    a, b = os.path.abspath(path), os.path.abspath(folder)
    try: return os.path.commonpath([a, b]) == b
    except ValueError: return False                                    # different drives


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir"); ap.add_argument("--list", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "missing-icons.txt"))
    ap.add_argument("--out", help="the zip to write (default: w3planner-extract.zip, or w3planner-wolf.zip with --wolf, on the Desktop)")
    ap.add_argument("--wolf", action="store_true", help="instead of icons and CSV: find the item definition XML of the Wolf School gear in every bundle")
    a = ap.parse_args(argv)
    game = a.game_dir or next((d for d in GAME_DIRS if os.path.isdir(d)), None)
    while not game or not os.path.isdir(game):
        game = input("Folder of your Witcher 3 installation (the one that contains 'content'): ").strip().strip('"')
    out = os.path.abspath(a.out or os.path.join(desktop(), "w3planner-wolf.zip" if a.wolf else "w3planner-extract.zip"))
    if inside(out, game): sys.exit("refusing to write the zip inside the game folder: %s" % out)
    if a.wolf:
        caches, bundles = find_files(game); tmp = out + ".part"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            hits, nf = run_wolf(game, bundles, z, ["game folder: %s" % game, "mode: --wolf", "bundles: %d" % len(bundles)])
        os.replace(tmp, out)
        with zipfile.ZipFile(out) as z: count = len(z.namelist())
        with open_ro(out) as zf: digest = hashlib.sha256(zf.read()).hexdigest()
        print("%d files (%d xml files with a Wolf definition), %d bytes (%.1f MB)\n%s\nSHA256 %s\n%d wanted definition(s) not found (listed in not-found.txt inside the zip)" % (count, hits, os.path.getsize(out), os.path.getsize(out) / 1048576.0, out, digest, len(nf)))
        return 0
    if not os.path.isfile(a.list): sys.exit("list file not found: %s" % a.list)
    wanted = read_list(a.list); caches, bundles = find_files(game)
    report = ["game folder: %s" % game, "list: %s (%d icons)" % (a.list, len(wanted)), "texture.cache files: %d, bundles: %d" % (len(caches), len(bundles))]
    entries = []
    for c in caches:
        try: entries += read_cache(c)
        except Exception as ex: report.append("skipped %s: %s" % (c, ex))
    found, why = match_icons(wanted, entries); n = 0; tmp = out + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for w in wanted:
            e = found.get(w)
            if e is None: report.append("MISSING icon %s: %s" % (w, why.get(w))); continue
            try: z.writestr("icons/" + os.path.splitext(w.replace("\\", "/"))[0] + ".dds", texture_dds(e)); n += 1; report.append("icon %s <- %s (%s)" % (w, e["name"], os.path.basename(os.path.dirname(e["cache"])) or "cache"))
            except Exception as ex: report.append("FAILED icon %s (%s): %s" % (w, e["name"], ex))
        icons = n; csvs = 0
        for b in bundles:
            try: res = bundle_csvs(b)
            except Exception as ex: report.append("skipped bundle %s: %s" % (b, ex)); continue
            for name, data, reason in res or []:
                if data is None: report.append("FAILED csv %s in %s: %s" % (name, os.path.basename(b), reason)); continue
                z.writestr("csv/%s/%s" % (os.path.basename(b), name.replace("\\", "/")), data); csvs += 1; report.append("csv %s <- %s" % (name, os.path.basename(b)))
        report.append("extracted: %d icons of %d wanted, %d csv files" % (icons, len(wanted), csvs)); z.writestr("report.txt", "\n".join(report) + "\n")
    os.replace(tmp, out)
    with zipfile.ZipFile(out) as z: count = len(z.namelist())
    print("%d files (%d icons, %d csv, report.txt), %d bytes (%.1f MB)\n%s" % (count, icons, csvs, os.path.getsize(out), os.path.getsize(out) / 1048576.0, out))
    missing = [l for l in report if l.startswith(("MISSING", "FAILED"))]
    if missing: print("%d problem(s), see report.txt inside the zip, first: %s" % (len(missing), missing[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
