"""The smoke test's wait for a new deployment (tests/smoke.py wait_for_site), against a fake site that answers with the OLD page
for a while and then the NEW one, and that, like Cloudflare's edge, answers a request with a query string from the new deployment
at once. The v25 promote was rolled back by mistake because the wait used such a query string.

    python tests/test_smoke_wait.py
"""
import hashlib, http.server, sys, threading, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke

OLD, NEW = b'<script>const APP_VERSION="v24";</script>', b'<script>const APP_VERSION="v25";</script>'


def serve(old_answers):
    state = {"n": 0, "paths": []}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            state["paths"].append(self.path); plain = "?" not in self.path
            if plain: state["n"] += 1
            body = OLD if plain and state["n"] <= old_answers else NEW   # a cache-busted URL always reaches the new deployment
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def log_message(self, *a): pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, state, "http://127.0.0.1:%d/" % srv.server_address[1]


class WaitTests(unittest.TestCase):
    def test_waits_through_the_old_page_then_succeeds(self):
        srv, st, url = serve(old_answers=3)
        try: ok, detail = smoke.wait_for_site(url, hashlib.sha256(NEW).hexdigest(), "v25", seconds=10, interval=0.05)
        finally: srv.shutdown()
        self.assertTrue(ok, detail); self.assertGreaterEqual(st["n"], 4)

    def test_polls_the_plain_url_never_a_query_string(self):
        srv, st, url = serve(old_answers=2)
        try: smoke.wait_for_site(url, None, "v25", seconds=10, interval=0.05)
        finally: srv.shutdown()
        self.assertTrue(st["paths"] and all(p == "/" for p in st["paths"]), st["paths"])

    def test_fails_only_after_the_whole_time_when_the_old_page_stays(self):
        srv, st, url = serve(old_answers=10 ** 9)
        try: ok, detail = smoke.wait_for_site(url, hashlib.sha256(NEW).hexdigest(), "v25", seconds=0.4, interval=0.05)
        finally: srv.shutdown()
        self.assertFalse(ok); self.assertIn("v24", detail); self.assertGreater(st["n"], 3)

    def test_needs_both_version_and_content(self):
        srv, st, url = serve(old_answers=0)
        try:
            self.assertTrue(smoke.wait_for_site(url, hashlib.sha256(NEW).hexdigest(), "v25", seconds=1, interval=0.05)[0])
            self.assertFalse(smoke.wait_for_site(url, hashlib.sha256(OLD).hexdigest(), "v25", seconds=0.2, interval=0.05)[0])
            self.assertFalse(smoke.wait_for_site(url, None, "v24", seconds=0.2, interval=0.05)[0])
        finally: srv.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)
