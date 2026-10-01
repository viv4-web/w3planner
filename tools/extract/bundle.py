#!/usr/bin/env python3
"""Read The Witcher 3 .bundle files (a public format): list what is inside and extract files by glob. Standard library only.

    python tools/extract/bundle.py list    ~/incoming/gamedata/bundles/xml.bundle [--glob 'gameplay\\items\\*']
    python tools/extract/bundle.py extract ~/incoming/gamedata/bundles/xml.bundle --glob 'gameplay\\items\\*.xml' --out /tmp/xml
    python tools/extract/bundle.py extract ~/incoming/gamedata/bundles/ep1.bundle  --glob '*\\weapons\\*.xbm' --out /tmp/tex
    python tools/extract/bundle.py info    ~/incoming/gamedata/bundles/*.bundle

Format ("POTATO70"):
    32-byte header: magic, u32 bundle size, u32 dummy size, u32 info-table size, 12 bytes more (not needed)
    info table at 32: entries of 304 bytes: name[256] (zero padded, backslash paths), hash[16], u32 data offset, u32 0,
                      u32 size (uncompressed), u32 size on disk, u32 crc32, u32 compression, 8 zero bytes
    data: each file at its offset, `size on disk` bytes
    compression: 0 none, 1 zlib, 2 snappy, 3 doboz, 4 lz4, 5 lz4 high compression (same block format as 4)
zlib, snappy and lz4 are implemented here in plain Python (and tested in tests/test_bundle.py). Doboz is NOT implemented: no
bundle we have uses it (the expansion bundles hold only 0 and 1), and a decoder written without a sample to test it against would
only look right. A file that needs it raises BundleError naming the file.
"""
import argparse, fnmatch, struct, sys, zlib
from pathlib import Path

ENTRY = 304
HEADER = 32
MAGIC = b"POTATO70"
NAMES = {0: "none", 1: "zlib", 2: "snappy", 3: "doboz", 4: "lz4", 5: "lz4hc"}


class BundleError(Exception):
    pass


def snappy_decompress(data):
    """Raw snappy block (not the framing format)."""
    i, n, shift = 0, 0, 0
    while True:                                   # varint: uncompressed length
        b = data[i]; i += 1; n |= (b & 0x7F) << shift; shift += 7
        if b < 0x80: break
    out = bytearray()
    while i < len(data):
        tag = data[i]; i += 1; kind = tag & 3
        if kind == 0:                             # literal
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59; ln = int.from_bytes(data[i:i + nb], "little"); i += nb
            ln += 1; out += data[i:i + ln]; i += ln; continue
        if kind == 1: ln = ((tag >> 2) & 7) + 4; off = ((tag >> 5) << 8) | data[i]; i += 1
        elif kind == 2: ln = (tag >> 2) + 1; off = int.from_bytes(data[i:i + 2], "little"); i += 2
        else: ln = (tag >> 2) + 1; off = int.from_bytes(data[i:i + 4], "little"); i += 4
        if off == 0 or off > len(out): raise BundleError("snappy: bad copy offset")
        for _ in range(ln): out.append(out[-off])  # overlapping copies repeat bytes, so copy one by one
    if len(out) != n: raise BundleError("snappy: expected %d bytes, got %d" % (n, len(out)))
    return bytes(out)


def lz4_decompress(data, size):
    """One LZ4 block (no frame); `size` is the uncompressed size."""
    i, out = 0, bytearray()
    while i < len(data):
        token = data[i]; i += 1; ln = token >> 4
        if ln == 15:
            while True:
                b = data[i]; i += 1; ln += b
                if b != 255: break
        out += data[i:i + ln]; i += ln
        if i >= len(data): break                  # the last sequence has only literals
        off = int.from_bytes(data[i:i + 2], "little"); i += 2; ml = token & 15
        if ml == 15:
            while True:
                b = data[i]; i += 1; ml += b
                if b != 255: break
        ml += 4
        if off == 0 or off > len(out): raise BundleError("lz4: bad match offset")
        for _ in range(ml): out.append(out[-off])
    if len(out) != size: raise BundleError("lz4: expected %d bytes, got %d" % (size, len(out)))
    return bytes(out)


class Entry:
    def __init__(self, name, offset, size, zsize, crc, comp):
        self.name, self.offset, self.size, self.zsize, self.crc, self.comp = name, offset, size, zsize, crc, comp

    def __repr__(self): return "<%s %d bytes, %s>" % (self.name, self.size, NAMES.get(self.comp, self.comp))


class Bundle:
    def __init__(self, path):
        self.path = Path(path); self.f = open(path, "rb"); h = self.f.read(HEADER)
        if h[:8] != MAGIC: raise BundleError("%s: not a W3 bundle (magic %r)" % (path, h[:8]))
        self.size, _, table = struct.unpack("<3I", h[8:20])
        if table % ENTRY: raise BundleError("%s: info table size %d is not a multiple of %d" % (path, table, ENTRY))
        raw = self.f.read(table); self.entries = []
        for k in range(table // ENTRY):
            e = raw[k * ENTRY:(k + 1) * ENTRY]; name = e[:256].split(b"\0")[0].decode("latin1")
            off, _, size, zsize, crc, comp = struct.unpack("<6I", e[272:296]); self.entries.append(Entry(name, off, size, zsize, crc, comp))

    def close(self): self.f.close()

    def match(self, pattern=None):
        """Entries whose path matches the glob (case-insensitive, / or \\ both work, a bare pattern also matches the file name)."""
        if not pattern: return list(self.entries)
        p = pattern.lower().replace("/", "\\")
        return [e for e in self.entries if fnmatch.fnmatchcase(e.name.lower(), p) or fnmatch.fnmatchcase(e.name.lower().rsplit("\\", 1)[-1], p)]

    def read(self, entry):
        self.f.seek(entry.offset); raw = self.f.read(entry.zsize)
        if len(raw) != entry.zsize: raise BundleError("%s: truncated data for %s" % (self.path.name, entry.name))
        c = entry.comp
        if c == 0: out = raw
        elif c == 1: out = zlib.decompress(raw)
        elif c == 2: out = snappy_decompress(raw)
        elif c in (4, 5): out = lz4_decompress(raw, entry.size)
        elif c == 3: raise BundleError("%s: Doboz compression is not implemented (see the module doc)" % entry.name)
        else: raise BundleError("%s: unknown compression %d" % (entry.name, c))
        if len(out) != entry.size: raise BundleError("%s: expected %d bytes, got %d" % (entry.name, entry.size, len(out)))
        return out


def extract(bundle, pattern, out_dir, flat=False):
    n = 0
    for e in bundle.match(pattern):
        dest = Path(out_dir) / (e.name.rsplit("\\", 1)[-1] if flat else e.name.replace("\\", "/"))
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(bundle.read(e)); n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["list", "extract", "info"]); ap.add_argument("bundles", nargs="+")
    ap.add_argument("--glob", help="path pattern, e.g. 'gameplay\\items\\*.xml' or '*.xbm'"); ap.add_argument("--out", help="folder for extract")
    ap.add_argument("--flat", action="store_true", help="extract: write only file names, no folders")
    a = ap.parse_args()
    for path in a.bundles:
        b = Bundle(path)
        if a.cmd == "info":
            from collections import Counter
            print("%s: %d files, compression %s" % (b.path.name, len(b.entries), dict(Counter(NAMES.get(e.comp, e.comp) for e in b.entries))))
        elif a.cmd == "list":
            for e in b.match(a.glob): print("%10d  %-5s  %s" % (e.size, NAMES.get(e.comp, e.comp), e.name))
        else:
            if not a.out: sys.exit("extract needs --out")
            print("%s: extracted %d files to %s" % (b.path.name, extract(b, a.glob, a.out, a.flat), a.out))


if __name__ == "__main__":
    main()
