"""The W3 .bundle reader (tools/extract/bundle.py): the format, zlib, snappy and lz4, with hand-made data (no game file needed).

    python tests/test_bundle.py
Doboz is not implemented (see the module doc); a file that needs it must raise a clear error.
"""
import struct, sys, tempfile, unittest, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "extract"))
import bundle


def make_bundle(path, files):
    """files: [(name, plain bytes, compression code, stored bytes)] -> a POTATO70 bundle written to path."""
    n = len(files); table = n * bundle.ENTRY; off = bundle.HEADER + table; entries, data = b"", b""
    for name, plain, comp, stored in files:
        entries += name.encode().ljust(256, b"\0") + b"\x11" * 16 + struct.pack("<6I", off + len(data), 0, len(plain), len(stored), zlib.crc32(plain), comp) + b"\0" * 8
        data += stored
    header = bundle.MAGIC + struct.pack("<3I", off + len(data), 0, table) + b"\0" * 12
    Path(path).write_bytes(header + entries + data)


SNAPPY_ABC = bytes([9, 0x08]) + b"abc" + bytes([0x16, 3, 0])          # literal "abc", then copy 6 bytes from 3 back (2-byte offset): abcabcabc
SNAPPY_RUN = bytes([10, 0x00]) + b"a" + bytes([0x15, 1])             # literal "a", copy 9 from 1 back (1-byte offset, overlapping): aaaaaaaaaa
SNAPPY_NEAR = bytes([8, 0x0C]) + b"abcd" + bytes([0x01, 4])           # literal "abcd", copy 4 from 4 back: abcdabcd
LZ4_MATCH = b"\x40abcd\x04\x00" + b"\x10e"                           # literals "abcd", match 4 from 4 back, last literals "e": abcdabcde
LZ4_LONG = b"\xf0\x05" + b"x" * 20                                   # 15 + 5 literals, no match


class BundleTests(unittest.TestCase):
    def test_snappy(self):
        self.assertEqual(bundle.snappy_decompress(SNAPPY_ABC), b"abcabcabc"); self.assertEqual(bundle.snappy_decompress(SNAPPY_RUN), b"a" * 10)
        self.assertEqual(bundle.snappy_decompress(SNAPPY_NEAR), b"abcdabcd")
        with self.assertRaises(bundle.BundleError): bundle.snappy_decompress(bytes([9, 0x08]) + b"abc" + bytes([0x16, 9, 0]))   # offset beyond the output

    def test_lz4(self):
        self.assertEqual(bundle.lz4_decompress(LZ4_MATCH, 9), b"abcdabcde"); self.assertEqual(bundle.lz4_decompress(LZ4_LONG, 20), b"x" * 20)
        with self.assertRaises(bundle.BundleError): bundle.lz4_decompress(LZ4_MATCH, 10)                                          # wrong promised size

    def test_read_list_glob_extract(self):
        files = [("gameplay\\items\\a.xml", b"<a/>" * 30, 1, zlib.compress(b"<a/>" * 30)), ("gameplay\\items_plus\\a.xml", b"plus", 0, b"plus"),
                 ("tex\\x.xbm", b"abcabcabc", 2, SNAPPY_ABC), ("tex\\y.xbm", b"abcdabcde", 4, LZ4_MATCH), ("tex\\z.xbm", b"nope", 3, b"\0\0")]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.bundle"; make_bundle(p, files); b = bundle.Bundle(p)
            self.assertEqual([e.name for e in b.entries], [f[0] for f in files])
            self.assertEqual([e.name for e in b.match("gameplay\\items\\*.xml")], ["gameplay\\items\\a.xml"])           # items, not items_plus
            self.assertEqual(len(b.match("*.xbm")), 3); self.assertEqual(len(b.match("TEX/*")), 3)                      # case and slash style do not matter
            self.assertEqual(b.read(b.entries[0]), b"<a/>" * 30); self.assertEqual(b.read(b.entries[1]), b"plus")
            self.assertEqual(b.read(b.entries[2]), b"abcabcabc"); self.assertEqual(b.read(b.entries[3]), b"abcdabcde")
            with self.assertRaises(bundle.BundleError) as cm: b.read(b.entries[4])
            self.assertIn("Doboz", str(cm.exception))
            self.assertEqual(bundle.extract(b, "gameplay\\items_plus\\*", Path(d) / "out"), 1); self.assertEqual((Path(d) / "out/gameplay/items_plus/a.xml").read_bytes(), b"plus")

    def test_rejects_other_files(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "x").write_bytes(b"NOTABUNDLE" * 20)
            with self.assertRaises(bundle.BundleError): bundle.Bundle(Path(d, "x"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
