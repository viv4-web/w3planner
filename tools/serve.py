#!/usr/bin/env python3
"""Serve a built site folder locally and apply the rules in its _headers file, so the security headers
(Content-Security-Policy and friends) behave the way they do on Cloudflare.

    python tools/serve.py --dir dist/placeholder --port 8080
"""
import argparse, functools, http.server, re
from pathlib import Path


def load_rules(directory):
    rules, cur = [], None
    p = Path(directory) / "_headers"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            if not line.startswith((" ", "\t")):
                cur = (line.strip(), []); rules.append(cur)
            elif cur is not None and ": " in line:
                k, v = line.strip().split(": ", 1); cur[1].append((k, v))
    return rules


class Handler(http.server.SimpleHTTPRequestHandler):
    rules = []

    def end_headers(self):
        path = self.path.split("?")[0]
        for pat, headers in self.rules:
            if re.fullmatch(re.escape(pat).replace(r"\*", ".*"), path):
                for k, v in headers:
                    self.send_header(k, v)
        super().end_headers()

    def log_message(self, *a):
        pass


def make_server(directory, port):
    Handler.rules = load_rules(directory)
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=str(directory)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True); ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    print("Serving %s at http://127.0.0.1:%d/ (Ctrl+C to stop)" % (a.dir, a.port))
    make_server(a.dir, a.port).serve_forever()
