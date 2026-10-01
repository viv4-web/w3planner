"""Big data is never embedded: a source that says /*@file:items_ng*/ gets a separate script file, hashed, with the icon tokens resolved,
and index.html only gets the file's URL.

    python tests/test_build_lazy.py
"""
import json, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class LazyTests(unittest.TestCase):
    def test_marker_becomes_a_url_and_the_data_a_separate_file(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); src = d / "src"; shutil.copytree(ROOT / "src", src); plain = d / "plain"
            for name, extra in (("plain", ""), ("lazy", "\nconst ITEMS_NG_URL=/*@file:items_ng*/;\n")):
                out = d / name
                if extra: (src / "app.js").write_text((ROOT / "src/app.js").read_text(encoding="utf-8") + extra, encoding="utf-8")
                r = subprocess.run([sys.executable, str(ROOT / "tools/build.py"), "--variant", "placeholder", "--src", str(src), "--out", str(out)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            html = (d / "lazy/index.html").read_text(encoding="utf-8"); m = re.search(r'ITEMS_NG_URL="(data/items_ng\.[0-9a-f]{12}\.js)"', html)
            self.assertTrue(m, "the marker was not replaced by the file URL"); f = d / "lazy" / m.group(1); self.assertTrue(f.is_file())
            self.assertLess(len((d / "lazy/index.html").read_bytes()) - len((d / "plain/index.html").read_bytes()), 200)      # only the URL, not the data
            text = f.read_text(encoding="utf-8"); self.assertTrue(text.startswith("(window.W3DATA=window.W3DATA||{}).items_ng="))
            self.assertNotIn("@@img:", text)                                                                                 # tokens resolved for this variant
            payload = json.loads(text[text.index(").items_ng=") + len(").items_ng="):].rstrip().rstrip(";")); self.assertGreater(len(payload["items"]), 100)
            icon = next(r["icon"] for r in payload["items"] if r["icon"]); self.assertTrue((d / "lazy" / icon).is_file(), icon)  # the placeholder file exists in the build
            self.assertFalse(list((d / "plain").glob("data")), "no marker, no data folder")


if __name__ == "__main__":
    unittest.main(verbosity=2)
