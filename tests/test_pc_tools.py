"""tools/pc/extract_on_pc.py (the script Vivek runs on his Windows PC) and tools/import_pc_zip.py (the server side), against a small FAKE game folder:
a texture.cache and a bundle with CSV files. Checks what comes out, that the game folder is not touched, that the script only uses the standard
modules it promises and no network, and that a hostile zip is refused.

    python tests/test_pc_tools.py
"""
import ast, contextlib, hashlib, io, os, struct, sys, tempfile, unittest, zipfile, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "pc")); sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "tests"))
import extract_on_pc as pc
import import_pc_zip
import test_bundle

RED565 = struct.pack("<HHI", 0xF800, 0x0000, 0)                # a DXT1 block: every pixel red


def make_cache(path, textures):
    """textures: [(name, w, h, fmt code, raw bytes of the top mip)] -> a texture.cache (pages of 4096 bytes, then names, entries, footer)."""
    body, entries, names = b"", b"", b""
    for i, (name, w, h, fmt, raw) in enumerate(textures):
        z = zlib.compress(raw + b"\0" * 16)                       # a lower mip may follow the top one
        body += (struct.pack("<IIB", len(z), len(raw) + 16, 0) + z).ljust(4096 * ((9 + len(z) + 4095) // 4096), b"\0")
        entries += struct.pack("<IiIIIIHHHHiiqBBBB", 0, 0, i, 0, 0, 0, w, h, 1, 1, 0, 0, 0, fmt, 0, 0, 0); names += name.encode() + b"\0"
    footer = struct.pack("<QIIIIII", 0, len(textures), len(textures), len(names), 0, pc.CACHE_MAGIC, 0)
    Path(path).write_bytes(body + names + entries + footer)


def tree_state(root):
    return sorted((str(p), p.stat().st_size, hashlib.sha1(p.read_bytes()).hexdigest()) for p in Path(root).rglob("*") if p.is_file())


class PcToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); t = Path(self.tmp.name); self.game = t / "The Witcher 3"; (self.game / "content/content0/bundles").mkdir(parents=True); (self.game / "dlc/bob/content").mkdir(parents=True)
        make_cache(self.game / "content/content0/texture.cache", [("gameplay\\gui_new\\icons\\inventory\\armors\\bear_armor_4_64x128.xbm", 8, 8, 0x07, RED565 * 4),
                                                                   ("gameplay\\gui_new\\icons\\inventory\\weapons\\other.xbm", 8, 8, 0x07, RED565 * 4)])
        make_cache(self.game / "dlc/bob/content/texture.cache", [("icons\\inventory\\weapons\\bob_sword_64x128.xbm", 4, 4, 0x00, bytes([10, 20, 30, 255]) * 16),
                                                                  ("icons\\inventory\\armors\\dupe.xbm", 4, 4, 0x07, RED565), ("gameplay\\x\\icons\\inventory\\armors\\dupe.xbm", 4, 4, 0x07, RED565)])
        csv = b"attribute,color,percent\nSlashingDamage,red,0\n"
        test_bundle.make_bundle(self.game / "content/content0/bundles/misc.bundle", [("gameplay\\globals\\tooltip_settings.csv", csv, 1, zlib.compress(csv)), ("gameplay\\globals\\sub\\no.csv", b"x", 0, b"x"),
                                                                                    ("gameplay\\items\\x.xml", b"<a/>", 0, b"<a/>"), ("dlc\\ep1\\data\\gameplay\\globals\\more.csv", b"a,b\n", 0, b"a,b\n"),
                                                                                    ("gameplay\\globals\\doboz.csv", b"x", 3, b"\0")])
        self.list = t / "missing-icons.txt"
        self.list.write_text("# comment\nicons/inventory/armors/bear_armor_4_64x128.png\tBear Armor 4; NGP Bear Armor 4\n\nicons/inventory/weapons/bob_sword_64x128.png\tBob sword\n"
                             "icons/inventory/armors/not_there_64x128.png\tnothing\nicons/inventory/armors/dupe.png\tambiguous\n", encoding="utf-8")
        self.zip = t / "Desktop" / "out.zip"; self.zip.parent.mkdir()

    def tearDown(self): self.tmp.cleanup()

    def run_tool(self, extra=()):
        out = io.StringIO()
        with contextlib.redirect_stdout(out): rc = pc.main(["--game-dir", str(self.game), "--list", str(self.list), "--out", str(self.zip)] + list(extra))
        return rc, out.getvalue()

    def test_extracts_only_what_was_asked_and_never_touches_the_game_folder(self):
        before = tree_state(self.game); rc, out = self.run_tool(); self.assertEqual(rc, 0); self.assertEqual(tree_state(self.game), before)       # nothing written, nothing changed
        z = zipfile.ZipFile(self.zip); names = sorted(z.namelist())
        self.assertEqual(names, ["csv/misc.bundle/dlc/ep1/data/gameplay/globals/more.csv", "csv/misc.bundle/gameplay/globals/tooltip_settings.csv", "icons/icons/inventory/armors/bear_armor_4_64x128.dds",
                                 "icons/icons/inventory/weapons/bob_sword_64x128.dds", "report.txt"])                                                    # not other.xbm, sub/no.csv, x.xml, doboz.csv
        self.assertEqual(z.read("csv/misc.bundle/gameplay/globals/tooltip_settings.csv"), b"attribute,color,percent\nSlashingDamage,red,0\n")
        rep = z.read("report.txt").decode(); self.assertIn("MISSING icon icons/inventory/armors/not_there_64x128.png", rep); self.assertIn("2 textures match", rep); self.assertIn("compression 3 is not supported", rep)
        self.assertRegex(out, r"5 files \(2 icons, 2 csv, report.txt\), \d+ bytes"); self.assertIn(str(self.zip), out); self.assertIn("problem(s)", out)

    def test_the_dds_files_are_real_textures(self):
        from PIL import Image
        self.run_tool(); z = zipfile.ZipFile(self.zip)
        red = Image.open(io.BytesIO(z.read("icons/icons/inventory/armors/bear_armor_4_64x128.dds"))).convert("RGBA"); self.assertEqual(red.size, (8, 8)); self.assertEqual(red.getpixel((3, 3)), (255, 0, 0, 255))
        rgba = Image.open(io.BytesIO(z.read("icons/icons/inventory/weapons/bob_sword_64x128.dds"))).convert("RGBA"); self.assertEqual(rgba.size, (4, 4)); self.assertEqual(rgba.getpixel((1, 1)), (10, 20, 30, 255))

    def test_dxt5_and_a_hostile_cache_name(self):
        from PIL import Image
        dxt5 = bytes([255, 0, 0, 0, 0, 0, 0, 0]) + RED565; p = Path(self.tmp.name) / "c" / "texture.cache"; p.parent.mkdir()
        make_cache(p, [("icons\\inventory\\armors\\a5.xbm", 4, 4, 0x08, dxt5)]); e = pc.read_cache(str(p))[0]; self.assertEqual((e["w"], e["h"], e["fmt"]), (4, 4, 0x08))
        with Image.open(io.BytesIO(pc.texture_dds(e))) as im: self.assertEqual(im.convert("RGBA").getpixel((2, 2)), (255, 0, 0, 255))
        found, why = pc.match_icons(["icons/inventory/armors/a5.png", "icons/inventory/armors/zz.png"], [e]); self.assertIs(found["icons/inventory/armors/a5.png"], e); self.assertIsNone(found["icons/inventory/armors/zz.png"])

    def test_refuses_to_write_inside_the_game_folder(self):
        with self.assertRaises(SystemExit) as cm: self.run_tool(["--out", str(self.game / "content" / "x.zip")])
        self.assertIn("refusing", str(cm.exception)); self.assertFalse((self.game / "content" / "x.zip").exists())

    def test_only_standard_modules_and_no_network(self):
        tree = ast.parse((ROOT / "tools/pc/extract_on_pc.py").read_text(encoding="utf-8")); mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import): mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom): mods.add(n.module.split(".")[0])
        self.assertEqual(mods, {"argparse", "hashlib", "os", "re", "struct", "sys", "zipfile", "zlib"})
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"]
        for c in calls:                                                                                                                    # every open() reads: no write, append or exclusive mode anywhere
            mode = next((k.value.value for k in c.keywords if k.arg == "mode"), c.args[1].value if len(c.args) > 1 else "r"); self.assertTrue(set(mode) <= set("rb"), mode)
        os_used = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "os"}
        self.assertEqual(os_used - {"path", "walk", "environ", "replace"}, set())                                                          # no remove, rename, mkdir, makedirs, chmod ...
        zips = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "ZipFile"]
        self.assertEqual(len([c for c in zips if len(c.args) > 1 and c.args[1].value == "w"]), 2)                                      # the zips that are written: icons/csv and --wolf (each to out + ".part", then renamed)

    def test_wolf_mode_finds_definitions_in_any_bundle_and_reports_what_is_missing(self):
        item = lambda n: ('<item name="%s" category="armor"><tags>WolfSet</tags></item>' % n).encode()
        ab = lambda n: ('<ability name="%s _Stats"><armor type="add" min="1"/></ability>' % n).encode()
        a = b"<redxml><definitions><abilities>" + ab("Wolf Armor 1") + ab("Wolf Armor 4") + b"</abilities><items>" + item("Wolf Armor 1") + item("NGP Wolf Armor 1") + item("Wolf Armor 4") + b"""
            <item_cond name="Wolf Armor 2" collapse="false"/><item_extension name="Wolf Armor 3"/><item
              name = "Wolf Boots 2" category="boots"/></items></definitions></redxml>"""
        decoy = b'<recipes><item_cond name="Wolf Gloves 1"/></recipes>'
        nxt = self.game / "dlc/dlc_next_gen/content/bundles"; nxt.mkdir(parents=True)
        test_bundle.make_bundle(nxt / "nextgen.bundle", [("dlc\\dlc_next_gen\\data\\gameplay\\items_plus\\def_item_armor.xml", a, 1, zlib.compress(a)), ("gameplay\\items\\decoy.xml", decoy, 0, decoy), ("textures\\x.xbm", b"Wolf", 0, b"Wolf")])
        before = tree_state(self.game); out = io.StringIO()
        with contextlib.redirect_stdout(out): rc = pc.main(["--game-dir", str(self.game), "--out", str(self.zip), "--wolf"])
        self.assertEqual(rc, 0); self.assertEqual(tree_state(self.game), before)
        z = zipfile.ZipFile(self.zip); names = sorted(z.namelist())
        self.assertEqual(names, ["SHA256SUMS", "manifest.txt", "not-found.txt", "report.txt", "xml/dlc/dlc_next_gen/content/bundles/nextgen.bundle/dlc/dlc_next_gen/data/gameplay/items_plus/def_item_armor.xml"])   # the decoy and the texture are not copied
        man = z.read("manifest.txt").decode(); self.assertIn("dlc/dlc_next_gen/content/bundles/nextgen.bundle -> dlc/dlc_next_gen/data/gameplay/items_plus/def_item_armor.xml", man)
        for found in ("item Wolf Armor 1", "item NGP Wolf Armor 1", "item Wolf Boots 2", "ability Wolf Armor 1 _Stats"): self.assertIn(found, man)
        nf = z.read("not-found.txt").decode(); self.assertNotIn("item Wolf Armor 1\n", nf); self.assertNotIn("item Wolf Boots 2\n", nf)
        for missing in ("item Wolf Armor 2\n", "item Wolf Armor 3\n", "item Wolf Gloves 1\n", "ability NGP Wolf Armor 1 _Stats\n", "item Wolf School steel sword 3\n"): self.assertIn(missing, nf)
        self.assertIn("item Wolf Gloves 5   (control", nf); self.assertNotIn("item Wolf Armor 4   (control", nf)         # a control that is found is not listed
        sums = dict(l.split("  ", 1)[::-1] for l in z.read("SHA256SUMS").decode().splitlines())
        self.assertEqual(sorted(sums), [n for n in names if n != "SHA256SUMS"])
        for n, h in sums.items(): self.assertEqual(h, hashlib.sha256(z.read(n)).hexdigest())
        self.assertRegex(out.getvalue(), r"SHA256 [0-9a-f]{64}"); self.assertEqual(hashlib.sha256(self.zip.read_bytes()).hexdigest(), out.getvalue().split("SHA256 ")[1].split()[0])

    def test_importer_makes_pngs_and_csv_and_refuses_a_hostile_zip(self):
        from PIL import Image
        self.run_tool(); dest = Path(self.tmp.name) / "gamedata"; r = import_pc_zip.import_zip(self.zip, dest); self.assertEqual((r["icons"], r["csv"], r["failed"]), (2, 2, []))
        with Image.open(dest / "inventory/armors/bear_armor_4_64x128.png") as im: self.assertEqual(im.size, (8, 8)); self.assertTrue((dest / "csv/gameplay/globals/tooltip_settings.csv").is_file())
        evil = Path(self.tmp.name) / "evil.zip"
        with zipfile.ZipFile(evil, "w") as z: z.writestr("csv/x/../../../../etc/evil.csv", b"x")
        with self.assertRaises(SystemExit): import_pc_zip.import_zip(evil, Path(self.tmp.name) / "g2")
        self.assertFalse((Path(self.tmp.name) / "g2").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
