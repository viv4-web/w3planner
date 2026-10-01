#!/usr/bin/env python3
"""The release gate: build and test the live site (the build with the game's art), try it on a preview deployment,
and only then, when told to, put it into production.

    python tools/deploy.py --art-dir ../w3planner-art            the gate: checks, build, PREVIEW deploy, smoke tests, report. Stops there.
    python tools/deploy.py --art-dir ../w3planner-art --serve    build and serve dist/game on 127.0.0.1 only (for a port forward). Deploys nothing.
    python tools/deploy.py --art-dir ../w3planner-art --dry-run  checks and build only, upload nothing
    python tools/deploy.py --art-dir ../w3planner-art --promote  PRODUCTION: the build that passed on preview, then smoke tests on the
                                                                  live site; if they fail, roll back to the previous deployment

The gate, in order:
  1. no game art in the repo, the full test suite on the game build (never --quick), build dist/game
  2. preview deployment to the branch "preview" (never production), then tests/smoke.py against the preview URL
     (page loads, no console errors, every link fixture opens, a new link can be created and reopened)
  3. a short report, and stop. Production needs --promote, after a person has said yes.
--promote refuses unless dist/game is exactly the build (same git commit, same files) that passed on preview.
After the production upload it runs the same smoke tests against https://<project>.pages.dev. If they fail it rolls
production back to the previous production deployment through the Cloudflare API and reports. That rollback is the only
thing this script does without asking.

Needs, in the environment:  CLOUDFLARE_API_TOKEN  (a token with Cloudflare Pages: Edit and nothing else)
                            CLOUDFLARE_ACCOUNT_ID
(Load them with  set -a; . ~/.config/w3planner/cf.env; set +a  and never print them.)
"""
import argparse, calendar, hashlib, json, os, re, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
PREVIEW_BRANCH = "preview"
GATE_FILE = ROOT / "dist" / "gate-preview.json"  # outside dist/game, so it is never uploaded
API = os.environ.get("CF_API_BASE", "https://api.cloudflare.com/client/v4")


def run(cmd, **kw):
    print("$ " + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, **kw)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def tree_hash(directory):
    """One hash for every file (name and content) in a folder."""
    h = hashlib.sha256()
    for p in sorted(Path(directory).rglob("*")):
        if p.is_file(): h.update(str(p.relative_to(directory)).encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


# ---- Cloudflare API (token comes from the environment and is never printed) ----
def cf_api(method, path, **_):
    req = urllib.request.Request(API + path, method=method, headers={"Authorization": "Bearer " + os.environ["CLOUDFLARE_API_TOKEN"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError("Cloudflare API %s %s failed: HTTP %d %s" % (method, path.split("?")[0], e.code, e.read()[:200].decode("utf8", "replace")))
    if not body.get("success"): raise RuntimeError("Cloudflare API %s %s failed: %s" % (method, path.split("?")[0], body.get("errors")))
    return body["result"]


def project_path(project): return "/accounts/%s/pages/projects/%s" % (os.environ["CLOUDFLARE_ACCOUNT_ID"], project)


def current_production(project):
    """The deployment production serves right now: {id, url} or None."""
    d = (cf_api("GET", project_path(project)) or {}).get("canonical_deployment")
    return {"id": d["id"], "url": d.get("url")} if d else None


def latest_deployment(project, env, after):
    """The newest deployment of this environment created after `after` (epoch seconds), or None."""
    for d in cf_api("GET", project_path(project) + "/deployments?env=%s&per_page=5" % env):
        if calendar.timegm(time.strptime(d["created_on"][:19], "%Y-%m-%dT%H:%M:%S")) >= after - 60: return {"id": d["id"], "url": d["url"]}
    return None


def rollback(project, previous_id):
    return cf_api("POST", project_path(project) + "/deployments/%s/rollback" % previous_id)


def wrangler_deploy(project, branch):
    """Upload dist/game. Returns (exit code, deployment URL found in wrangler's output or None)."""
    p = subprocess.Popen(["npx", "--yes", "wrangler", "pages", "deploy", "dist/game", "--project-name", project, "--branch", branch], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = ""
    for line in p.stdout: print(line, end="", flush=True); out += line
    m = re.search(r"https://[a-z0-9]+\.[a-z0-9-]+\.pages\.dev", out)
    return p.wait(), m.group(0) if m else None


def smoke(url, expect_version, wait, built=True):
    """Smoke-test a site. With built=True it must serve exactly dist/game/index.html (waiting up to `wait` seconds for that)."""
    import smoke as smoke_tests
    ok, res = smoke_tests.run_smoke(url, expect_version=expect_version, expect_index=str(ROOT / "dist/game/index.html") if built else None, wait=wait)
    return ok, [r for r in res if not r[1]]


def app_version():
    m = re.search(r'APP_VERSION="([^"]*)"', (ROOT / "dist/game/index.html").read_text(encoding="utf-8")); return m.group(1) if m else None


def build(art_dir, full_tests=True):
    if run([sys.executable, "tools/check_no_game_art.py"]).returncode: sys.exit("the public repo contains game art; fix that first")
    if full_tests and run([sys.executable, "tests/run_all.py", "--variant", "game", "--art-dir", art_dir]).returncode: sys.exit("the full test suite failed; nothing was deployed")
    if run([sys.executable, "tools/build.py", "--variant", "game", "--art-dir", art_dir, "--out", "dist/game"]).returncode: sys.exit("build failed")


def need_env():
    missing = [v for v in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID") if not os.environ.get(v)]
    if missing: sys.exit("set these environment variables first: " + ", ".join(missing))


def do_serve(a):
    import serve
    build(a.art_dir, full_tests=False)
    srv = serve.make_server(ROOT / "dist/game", a.port)  # make_server binds 127.0.0.1 only, never another address
    print("\nServing dist/game (the build with the game's art, NOT tested by this command) at http://127.0.0.1:%d/ , reachable only from this machine." % srv.server_address[1])
    print("Forward the port from your own machine (VSCodium: Ports panel, or: ssh -L %d:127.0.0.1:%d <server>). Ctrl+C to stop." % (srv.server_address[1], srv.server_address[1]), flush=True)
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\nstopped")


def do_gate(a):
    """Steps 1 to 3. Returns the exit code."""
    if not a.dry_run: need_env()
    dirty = git("status", "--porcelain")
    if dirty: print("WARNING: uncommitted changes in the working tree (they are in this build):\n" + dirty)
    build(a.art_dir)
    if a.dry_run: print("dry run finished: dist/game is ready, nothing was uploaded"); return 0
    version, started = app_version(), time.time()
    print("\nUploading dist/game as a PREVIEW (branch '%s') of project '%s'; production is not touched." % (PREVIEW_BRANCH, a.project), flush=True)
    code, url = wrangler_deploy(a.project, PREVIEW_BRANCH)
    if code: print("\nGATE FAILED: wrangler exited with %d (the error is above). Nothing reached production." % code); return 1
    dep = latest_deployment(a.project, "preview", started) or {}
    url = url or dep.get("url")
    if not url: print("\nGATE FAILED: the preview was uploaded but I could not find its URL."); return 1
    print("\nSmoke tests against the preview %s" % url, flush=True)
    ok, failed = smoke(url, version, wait=120)
    if not ok:
        print("\nGATE FAILED on the preview %s. %d check(s) failed: %s\nNothing reached production." % (url, len(failed), "; ".join(f[0] for f in failed[:5]))); return 1
    GATE_FILE.write_text(json.dumps({"commit": git("rev-parse", "HEAD"), "dirty": bool(dirty), "tree": tree_hash(ROOT / "dist/game"), "version": version, "preview_url": url,
                                     "deployment_id": dep.get("id"), "passed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1) + "\n")
    print("\n== GATE PASSED ==\nversion %s, commit %s%s\npreview deployment %s  %s\nfull test suite and preview smoke tests passed.\nProduction is unchanged. After a yes: python tools/deploy.py --art-dir %s --promote"
          % (version, git("rev-parse", "--short", "HEAD"), " (+ uncommitted changes)" if dirty else "", dep.get("id", "?"), url, a.art_dir)); return 0


def do_promote(a):
    need_env()
    if not (ROOT / "dist/game/index.html").is_file() or not GATE_FILE.is_file(): sys.exit("no passed preview on record: run the gate first (without --promote)")
    g = json.loads(GATE_FILE.read_text())
    if g["dirty"] or git("status", "--porcelain"): sys.exit("production is only built from committed code: commit (or stash) everything and run the gate again")
    if git("rev-parse", "HEAD") != g["commit"]: sys.exit("the checkout changed since the preview passed (commit %s): run the gate again" % g["commit"][:7])
    if tree_hash(ROOT / "dist/game") != g["tree"]: sys.exit("dist/game is not the build that passed on the preview: run the gate again")
    version = app_version(); prod = "https://%s.pages.dev/" % a.project
    print("\nAbout to put %s (the build that passed on the preview %s) into PRODUCTION, project '%s'." % (version, g["preview_url"], a.project))
    if not a.yes and input("Type DEPLOY to continue: ").strip() != "DEPLOY": sys.exit("cancelled")
    previous = current_production(a.project)
    print("previous production deployment: %s" % (previous["id"] if previous else "none (no automatic rollback possible)"), flush=True)
    started = time.time(); code, _ = wrangler_deploy(a.project, "main")
    if code: print("\nPRODUCTION UPLOAD FAILED: wrangler exited with %d (the error is above). Production is unchanged unless wrangler says otherwise." % code); return 1
    new = latest_deployment(a.project, "production", started) or {}
    print("\nSmoke tests against production %s" % prod, flush=True)
    ok, failed = smoke(prod, version, wait=300)  # the plain URL can lag behind the upload for a few minutes
    if ok:
        print("\n== PRODUCTION OK ==\nversion %s is live at %s\nnew deployment %s %s\nprevious deployment (rollback target): %s" % (version, prod, new.get("id", "?"), new.get("url", ""), previous["id"] if previous else "none")); return 0
    print("\n== PRODUCTION SMOKE TESTS FAILED (%d): %s ==" % (len(failed), "; ".join(f[0] + (" (%s)" % f[2] if f[2] != "" else "") for f in failed[:5])))
    if not previous: print("No previous production deployment is known, so no automatic rollback. Decide what to do."); return 2
    print("Rolling production back to the previous deployment %s ..." % previous["id"], flush=True)
    try: rollback(a.project, previous["id"])
    except Exception as e: print("ROLLBACK FAILED: %s\nProduction may still be serving the bad deployment %s. Roll back by hand to %s." % (e, new.get("id", "?"), previous["id"])); return 2
    ok2, failed2 = smoke(prod, None, 0, built=False)
    print("Rolled back to %s. Smoke tests after the rollback: %s. The bad deployment was %s." % (previous["id"], "passed" if ok2 else "STILL FAILING: " + "; ".join(f[0] for f in failed2[:3]), new.get("id", "?"))); return 3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--art-dir", required=True, help="the private art folder (next to this repo)")
    ap.add_argument("--project", default="w3planner", help="Cloudflare Pages project name")
    ap.add_argument("--serve", action="store_true", help="build and serve dist/game on 127.0.0.1 only; deploy nothing")
    ap.add_argument("--port", type=int, default=8080, help="port for --serve")
    ap.add_argument("--dry-run", action="store_true", help="checks and build only; upload nothing")
    ap.add_argument("--promote", action="store_true", help="PRODUCTION: deploy the build that passed on preview, smoke-test it, roll back on failure")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation question for --promote")
    a = ap.parse_args()
    if sum([a.serve, a.dry_run, a.promote]) > 1: sys.exit("use only one of --serve, --dry-run, --promote")
    if a.serve: do_serve(a); return 0
    sys.exit(do_promote(a) if a.promote else do_gate(a))


if __name__ == "__main__":
    main()
