#!/usr/bin/env python3
"""Build the FINAL version of https://w3planner.pages.dev: every request is sent to the same path, query and hash on https://buildplanner.net/witcher-3/.

    python tools/make_pages_redirect.py --out dist/pages-redirect [--target https://buildplanner.net/witcher-3/]

Output: index.html (Cloudflare Pages answers every path that is not a file with it, because there is no 404.html), _headers (the planner's own) and _redirects.
Why a page and not only a rule: localStorage does not cross addresses, so before leaving, the page reads the quest keys and puts them in the hash for the new site (import=toolarge when they do not fit: the new site shows a notice)
(src/app.js HANDOFF, src/quests.js hoMerge; CLAUDE.md "Handoff"). A `/* ... 301` rule in _redirects would answer before the page runs and the quest data would be lost,
so _redirects only has the four static pages, which hold no data. Standard library only. Nothing is uploaded by this tool."""
import argparse, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = "https://buildplanner.net/witcher-3/"
KEYS = ["w3p.quests.v1", "w3p.quests.view", "w3p.quests.banddone", "w3p.quests.timedone", "w3p.quests.timescope"]
STASH = "w3planner.stash"
STATIC = ["help", "about", "privacy", "support"]
LIMIT = 1000000   # characters of base64url the new site accepts (src/app.js HANDOFF)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Moved to buildplanner.net</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="%(target)s">
<noscript><meta http-equiv="refresh" content="0;url=%(target)s"></noscript>
<style>body{font:16px/1.5 system-ui,sans-serif;background:#071514;color:#e9efe9;margin:0;padding:48px 16px;text-align:center}a{color:#d9b45a}</style>
</head><body>
<p>The Witcher 3 build planner has moved to <a href="%(target)s">%(host)s</a>.</p>
<p id="msg">Taking you there&hellip;</p>
<script>
(function () {
  var T = %(target_js)s, KEYS = %(keys)s, STASH = %(stash)s, LIMIT = %(limit)d;
  var path = location.pathname.replace(/^\\/+/, ""), h = location.hash.slice(1), extra = [];
  try {
    // a hash that is not a build code (for example a page anchor) is kept as it is and carries no data
    if (/^[A-Za-z0-9._-]*$/.test(h)) {
      var o = {}, n = 0, i, v;
      for (i = 0; i < KEYS.length; i++) { v = localStorage.getItem(KEYS[i]); if (v !== null) { o[KEYS[i]] = v; n++; } }
      if (n) {
        var bytes = new TextEncoder().encode(JSON.stringify(o)), s = "";
        for (i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
        var e = btoa(s).replace(/\\+/g, "-").replace(/\\//g, "_").replace(/=+$/, "");
        extra.push("import=" + (e.length <= LIMIT ? e : "toolarge"));   // too big for a URL: the new site says so instead of skipping silently
      }
      if (localStorage.getItem(STASH) !== null) extra.push("stash=1");
    }
  } catch (x) { /* no storage here: just redirect */ }
  if (extra.length) h = h ? h + "&" + extra.join("&") : extra.join("&");
  location.replace(T + path + location.search + (h ? "#" + h : ""));
})();
</script>
</body></html>
"""


def build(out, target=TARGET):
    if not target.startswith(("https://", "http://127.0.0.1")) or not target.endswith("/"): sys.exit("--target must be an https:// address ending in /")
    out = Path(out)
    if out.exists():
        if not (out / ".built-by-make_pages_redirect").exists() and any(out.iterdir()): sys.exit("refusing to overwrite %s: it was not created by this tool" % out)
        shutil.rmtree(out)
    out.mkdir(parents=True); (out / ".built-by-make_pages_redirect").write_text("generated; safe to delete\n")
    host = target.split("//", 1)[1].rstrip("/")
    (out / "index.html").write_text(PAGE % {"target": target, "host": host, "target_js": json.dumps(target), "keys": json.dumps(KEYS), "stash": json.dumps(STASH), "limit": LIMIT}, encoding="utf-8")
    shutil.copyfile(ROOT / "static" / "_headers", out / "_headers")
    rules = ["# path-level 301s for the static pages only (no data lives there). The planner itself, '/' and everything else is answered by index.html, which carries the quest data over.",
             "# Do NOT add '/*  <target>:splat  301': it would answer before index.html runs and the quest data would be lost."]
    for p in STATIC: rules += ["/%s.html  %s%s.html  301" % (p, target, p), "/%s  %s%s.html  301" % (p, target, p)]
    (out / "_redirects").write_text("\n".join(rules) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dist/pages-redirect"); ap.add_argument("--target", default=TARGET)
    a = ap.parse_args(); o = build(a.out, a.target); print("Built the pages.dev redirect into %s (index.html, _headers, _redirects) -> %s" % (o, a.target))
