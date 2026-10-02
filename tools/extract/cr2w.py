"""A small reader for The Witcher 3's CR2W resources (the .journal files of the glossary), standard library only.

    c = CR2W(data)                      data: the file's bytes
    c.names                             the name table (strings every property refers to)
    c.chunks                            [{cls, parent, size, off, idx, props}]  idx is 1-based, parent 0 = none
    props                               [(name, type, raw bytes)] in file order

Layout (checked on 1,444 journal files of the game and both expansions): 40-byte header, then ten (offset, count, crc) tables; table 0 is
the string area, 1 the names (8 bytes each: offset into the string area, hash), 2 the imports, 4 the chunk headers (24 bytes each:
class name index, flags, parent, data size, data offset, ...). Each chunk's data starts with one zero byte, then properties:
name index u16, type index u16, size u32 (counting its own 4 bytes), data. Helpers below decode the few types the journal uses.
"""
import struct


def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]


class CR2W:
    def __init__(self, data):
        b = self.b = bytes(data)
        if b[:4] != b"CR2W": raise ValueError("not a CR2W file")
        tab = [(u32(b, 0x28 + 12 * i), u32(b, 0x2C + 12 * i)) for i in range(10)]
        so, sz = tab[0]; sb = b[so:so + sz]; no, nc = tab[1]
        self.names = []
        for i in range(nc):
            off = u32(b, no + 8 * i); self.names.append(sb[off:sb.index(b"\0", off)].decode("latin1"))
        co, cc = tab[4]; self.chunks = []
        for i in range(cc):
            o = co + 24 * i
            self.chunks.append({"cls": self.names[u16(b, o)], "parent": u32(b, o + 4), "size": u32(b, o + 8), "off": u32(b, o + 12), "idx": i + 1})
        for c in self.chunks: c["props"] = self._props(c)

    def _props(self, c):
        b, o, end, out = self.b, c["off"] + 1, c["off"] + c["size"], []
        while o + 2 <= end:
            n = u16(b, o)
            if n == 0: break
            ty, sz = u16(b, o + 2), u32(b, o + 4)
            if sz < 4 or o + 4 + sz > end: break
            out.append((self.names[n], self.names[ty], b[o + 8:o + 4 + sz])); o += 4 + sz
        return out

    # ---- decoders for the property types the journal uses ----
    def string(self, d):
        """A String: length (6 bits, bit 6 = a second byte follows), bit 7 set = 8-bit characters, clear = UTF-16."""
        b = d[0]; n = b & 0x3F; o = 1
        if b & 0x40: n |= (d[1] & 0x7F) << 6; o = 2
        return d[o:o + n].decode("latin1") if b & 0x80 else d[o:o + 2 * n].decode("utf-16-le")

    def cname(self, d): return self.names[u16(d, 0)]
    def string_id(self, d): return u32(d, 0)              # LocalizedString: a number into the game's string file
    def cnames(self, d): n = u32(d, 0); return [self.names[u16(d, 4 + 2 * i)] for i in range(n)]
    def ptrs(self, d): n = u32(d, 0); return [u32(d, 4 + 4 * i) for i in range(n)]   # chunk numbers (1-based)
