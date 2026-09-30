#!/usr/bin/env python3
"""Fail if any file in this repository is, byte for byte, one of the game's images.

The game's artwork must never be committed to the public repository (not even briefly: git history is forever).
tools/game-art-hashes.txt holds SHA-1 fingerprints only; a fingerprint reveals nothing about the picture.

    python tools/check_no_game_art.py            scan the whole working tree
    python tools/check_no_game_art.py --staged   scan what is about to be committed (used by the pre-commit hook)
"""
import argparse, hashlib, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tga", ".dds", ".tif", ".tiff"}
SKIP = {".git", "dist", "node_modules", "__pycache__", ".venv"}


def load():
    return {l.split()[0] for l in (ROOT / "tools" / "game-art-hashes.txt").read_text().splitlines() if l.strip() and not l.startswith("#")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--staged", action="store_true")
    a = ap.parse_args()
    bad, hashes, n = [], load(), 0
    if a.staged:
        names = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
        for name in filter(None, names):
            if Path(name).suffix.lower() in IMG:
                blob = subprocess.run(["git", "show", ":" + name], cwd=ROOT, capture_output=True, check=True).stdout
                n += 1
                if hashlib.sha1(blob).hexdigest() in hashes: bad.append(name)
    else:
        for p in ROOT.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMG and not (set(p.relative_to(ROOT).parts) & SKIP):
                n += 1
                if hashlib.sha1(p.read_bytes()).hexdigest() in hashes: bad.append(str(p.relative_to(ROOT)))
    if bad:
        print("STOP: these files are the game's artwork and must not be in the public repository:")
        for b in bad: print("  ", b)
        sys.exit(1)
    print("OK: %d image files checked, none is game artwork" % n)


if __name__ == "__main__":
    main()
