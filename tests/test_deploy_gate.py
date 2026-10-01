"""The release gate's own logic (tools/deploy.py), tested with a fake Cloudflare and fake wrangler: nothing is uploaded.

    python tests/test_deploy_gate.py
What must hold: preview never touches production; --promote refuses a build that did not pass on preview; a failing
production smoke test rolls back to the previous deployment (and a passing one never does); a failed rollback is reported.
"""
import contextlib, io, json, sys, tempfile, unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import deploy


class Fake:
    """Stands in for git, wrangler, Cloudflare and the smoke tests."""
    def __init__(self, smoke_results, rollback_error=None):
        self.calls, self.smoke_results, self.rollback_error = [], list(smoke_results), rollback_error

    def wrangler(self, project, branch): self.calls.append(("wrangler", branch)); return 0, "https://abc123.%s.pages.dev" % project

    def smoke(self, url, version, wait, built=True):
        self.calls.append(("smoke", url, built)); r = self.smoke_results.pop(0)   # True, False (a real fault) or "lag" (only edge-lag checks fail)
        return r is True, [] if r is True else [("version is v99", False, "v98")] if r == "lag" else [("a link fixture opens", False, "differs in: lv")]

    def api(self, method, path, **kw):
        self.calls.append((method, path.split("?")[0].rsplit("/", 2)[-2:] if method == "POST" else "GET"))
        if method == "POST":
            if self.rollback_error: raise RuntimeError(self.rollback_error)
            return {}
        if path.endswith("/w3planner"): return {"canonical_deployment": {"id": "prev-0000", "url": "https://prev.w3planner.pages.dev"}}
        return [{"id": "new-1111", "url": "https://new.w3planner.pages.dev", "created_on": "2999-01-01T00:00:00.000Z"}]


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); (self.tmp / "dist/game").mkdir(parents=True); (self.tmp / "dist/game/index.html").write_text('<script>const APP_VERSION="v99";</script>')
        self.gate = self.tmp / "dist/gate-preview.json"
        self.env = mock.patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "t", "CLOUDFLARE_ACCOUNT_ID": "a"})
        self.sleeps = []; self.sleep = mock.patch.object(deploy.time, "sleep", lambda s: self.sleeps.append(s))
        self.args = Namespace(art_dir="art", project="w3planner", dry_run=False, yes=True)
        self.git_out = {("rev-parse", "HEAD"): "c" * 40, ("rev-parse", "--short", "HEAD"): "ccccccc", ("status", "--porcelain"): ""}

    def patched(self, fake):
        return [
            self.env, mock.patch.object(deploy, "ROOT", self.tmp), mock.patch.object(deploy, "GATE_FILE", self.gate), mock.patch.object(deploy, "git", lambda *a: self.git_out.get(a, "")),
            mock.patch.object(deploy, "build", lambda *a, **k: None), mock.patch.object(deploy, "wrangler_deploy", fake.wrangler), mock.patch.object(deploy, "smoke", fake.smoke), mock.patch.object(deploy, "cf_api", fake.api), self.sleep]

    def run_with(self, fake, fn):
        out = io.StringIO()
        with contextlib.ExitStack() as st, contextlib.redirect_stdout(out):
            for p in self.patched(fake): st.enter_context(p)
            try: rc = fn(self.args)
            except SystemExit as e: rc = e.code
        return rc, out.getvalue()

    def passed_gate(self):
        fake = Fake([True]); rc, out = self.run_with(fake, deploy.do_gate); self.assertEqual(rc, 0, out); return fake, out

    def test_gate_deploys_preview_only(self):
        fake, out = self.passed_gate()
        self.assertEqual([c for c in fake.calls if c[0] == "wrangler"], [("wrangler", "preview")]); self.assertIn("GATE PASSED", out); self.assertTrue(self.gate.is_file())

    def test_gate_failure_stops_and_records_nothing(self):
        fake = Fake([False]); rc, out = self.run_with(fake, deploy.do_gate)
        self.assertEqual(rc, 1); self.assertIn("GATE FAILED", out); self.assertFalse(self.gate.exists()); self.assertNotIn(("wrangler", "main"), fake.calls)

    def test_promote_needs_a_passed_preview(self):
        rc, _ = self.run_with(Fake([]), deploy.do_promote); self.assertIn("no passed preview", str(rc))

    def test_promote_refuses_a_changed_build_or_commit(self):
        self.passed_gate(); (self.tmp / "dist/game/index.html").write_text("changed")
        rc, _ = self.run_with(Fake([]), deploy.do_promote); self.assertIn("not the build that passed", str(rc))
        (self.tmp / "dist/game/index.html").write_text('<script>const APP_VERSION="v99";</script>'); self.git_out[("rev-parse", "HEAD")] = "d" * 40
        rc, _ = self.run_with(Fake([]), deploy.do_promote); self.assertIn("checkout changed", str(rc))

    def test_promote_refuses_uncommitted_changes(self):
        self.passed_gate(); self.git_out[("status", "--porcelain")] = " M x"
        rc, _ = self.run_with(Fake([]), deploy.do_promote); self.assertIn("committed code", str(rc))

    def test_promote_success_does_not_roll_back(self):
        self.passed_gate(); fake = Fake([True]); rc, out = self.run_with(fake, deploy.do_promote)
        self.assertEqual(rc, 0, out); self.assertIn("PRODUCTION OK", out); self.assertIn(("wrangler", "main"), fake.calls); self.assertFalse([c for c in fake.calls if c[0] == "POST"])

    def test_failed_production_smoke_rolls_back_to_previous(self):
        self.passed_gate(); fake = Fake([False, True]); rc, out = self.run_with(fake, deploy.do_promote)
        self.assertEqual(rc, 3, out); self.assertIn(("POST", ["prev-0000", "rollback"]), fake.calls); self.assertIn("Rolled back to prev-0000", out)
        self.assertEqual(fake.calls[-1], ("smoke", "https://w3planner.pages.dev/", False))  # re-checked after the rollback, against whatever is live now

    def test_edge_lag_that_clears_does_not_roll_back(self):
        self.passed_gate(); fake = Fake(["lag", "lag", True]); rc, out = self.run_with(fake, deploy.do_promote)
        self.assertEqual(rc, 0, out); self.assertIn("PRODUCTION OK", out); self.assertFalse([c for c in fake.calls if c[0] == "POST"])
        self.assertEqual(self.sleeps, [deploy.RECHECK_WAIT] * 2)

    def test_edge_lag_that_does_not_clear_rolls_back_after_the_rechecks(self):
        self.passed_gate(); fake = Fake(["lag"] * (deploy.RECHECKS + 1) + [True]); rc, out = self.run_with(fake, deploy.do_promote)
        self.assertEqual(rc, 3, out); self.assertIn(("POST", ["prev-0000", "rollback"]), fake.calls); self.assertEqual(self.sleeps, [deploy.RECHECK_WAIT] * deploy.RECHECKS)

    def test_a_real_fault_rolls_back_at_once_without_rechecks(self):
        self.passed_gate(); fake = Fake([False, True]); rc, out = self.run_with(fake, deploy.do_promote)
        self.assertEqual(rc, 3, out); self.assertEqual(self.sleeps, []); self.assertIn(("POST", ["prev-0000", "rollback"]), fake.calls)

    def test_failed_rollback_is_reported_with_the_manual_target(self):
        self.passed_gate(); fake = Fake([False], rollback_error="HTTP 500"); rc, out = self.run_with(fake, deploy.do_promote)
        self.assertEqual(rc, 2); self.assertIn("ROLLBACK FAILED", out); self.assertIn("prev-0000", out)

    def test_serve_binds_loopback_only(self):
        import serve
        s = serve.make_server(self.tmp / "dist/game", 0)
        try: self.assertEqual(s.server_address[0], "127.0.0.1")
        finally: s.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
