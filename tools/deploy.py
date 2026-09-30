#!/usr/bin/env python3
"""Deploy the live site (the build with the game's art) to Cloudflare Pages.

    python tools/deploy.py --art-dir ../w3planner-art                 production deploy (asks first)
    python tools/deploy.py --art-dir ../w3planner-art --branch my-test   preview deploy, not production
    python tools/deploy.py --art-dir ../w3planner-art --dry-run          build and check, upload nothing

Needs, in the environment:  CLOUDFLARE_API_TOKEN  (a token with Cloudflare Pages: Edit and nothing else)
                            CLOUDFLARE_ACCOUNT_ID
STATUS: written without access to Cloudflare, so the upload step is UNTESTED. Before the first real deploy run
`npx wrangler pages deploy --help` and check the flags below still exist.
"""
import argparse, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, **kw):
    print("$ " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=ROOT, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--art-dir", required=True, help="the private art repo (checked out next to this one)")
    ap.add_argument("--project", default="w3planner", help="Cloudflare Pages project name")
    ap.add_argument("--branch", default="main", help="main = production; any other name = a preview deployment")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--yes", action="store_true", help="skip the confirmation question")
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()

    if not a.dry_run:
        missing = [v for v in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID") if not os.environ.get(v)]
        if missing: sys.exit("set these environment variables first: " + ", ".join(missing))
    dirty = run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    if dirty and a.branch == "main": print("WARNING: uncommitted changes in the working tree:\n" + dirty)
    if run([sys.executable, "tools/check_no_game_art.py"]).returncode: sys.exit("the public repo contains game art; fix that first")
    if not a.skip_tests and run([sys.executable, "tests/run_all.py", "--variant", "game", "--art-dir", a.art_dir]).returncode:
        sys.exit("tests failed; nothing was deployed")
    if run([sys.executable, "tools/build.py", "--variant", "game", "--art-dir", a.art_dir, "--out", "dist/game"]).returncode:
        sys.exit("build failed")
    if a.dry_run: sys.exit(print("dry run finished: dist/game is ready, nothing was uploaded") or 0)
    print("\nAbout to upload dist/game to Cloudflare Pages project '%s', branch '%s' (%s)." % (a.project, a.branch, "PRODUCTION" if a.branch == "main" else "preview"))
    if not a.yes and input("Type DEPLOY to continue: ").strip() != "DEPLOY": sys.exit("cancelled")
    sys.exit(run(["npx", "--yes", "wrangler", "pages", "deploy", "dist/game", "--project-name", a.project, "--branch", a.branch]).returncode)


if __name__ == "__main__":
    main()
