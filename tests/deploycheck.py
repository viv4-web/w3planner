"""v39.6: the deploy guard (../deploy/deploy.sh, outside this repo: the test is skipped when that folder is missing).

guard(check)   deploy.sh refuses to publish when the dist's recorded build commit is not the planner's git HEAD, or when the dist is older than the planner's last commit; `deploy.sh build` runs build.sh.
               A scratch copy of deploy.sh and hash.sh, a scratch planner repo, a fake dist and fake ssh / rsync in PATH: nothing is ever sent anywhere.
Used by tests/run_all.py."""
import os, shutil, subprocess, tempfile
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent.parent.parent / "deploy"


def sh(cmd, cwd, env=None, stdin=""):
    return subprocess.run(cmd, cwd=cwd, env=env, input=stdin, capture_output=True, text=True)


def guard(check):
    if not (DEPLOY / "deploy.sh").exists():
        print("  (deploy guard test skipped: %s not found)" % DEPLOY); return
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); dep = td / "deploy"; pl = td / "w3planner"; bin_ = td / "bin"; dep.mkdir(); pl.mkdir(); bin_.mkdir()
        for n in ("deploy.sh", "hash.sh"): shutil.copy(DEPLOY / n, dep / n)
        (dep / "build.sh").write_text("#!/usr/bin/env bash\necho built > \"$(dirname \"$0\")/build.ran\"\n"); (dep / "build.sh").chmod(0o755)
        for n in ("ssh", "rsync"): (bin_ / n).write_text("#!/usr/bin/env bash\necho \"fake %s $*\" >> \"%s/net.log\"\necho \">f..t...... x\"\nexit 0\n" % (n, td)); (bin_ / n).chmod(0o755)
        (dep / "dist" / "witcher-3").mkdir(parents=True); (dep / "dist" / "index.html").write_text("home"); (dep / "dist" / "witcher-3" / "index.html").write_text("planner"); (dep / "dist" / ".htaccess").write_text("x")
        env = dict(os.environ, PATH=str(bin_) + os.pathsep + os.environ["PATH"], GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        sh(["git", "init", "-q"], pl, env); (pl / "a.txt").write_text("1"); sh(["git", "add", "."], pl, env); sh(["git", "commit", "-q", "-m", "one"], pl, env)
        head = lambda: sh(["git", "rev-parse", "HEAD"], pl, env).stdout.strip()
        ctime = lambda: int(sh(["git", "log", "-1", "--format=%ct"], pl, env).stdout.strip())
        def record(commit, built):
            (dep / "dist.sha256").write_text(sh(["bash", str(dep / "hash.sh")], dep, env).stdout.strip() + "\n"); (dep / "dist.commit").write_text(commit + "\n"); (dep / "dist.built").write_text(str(built) + "\n")
        def run(mode="preview", stdin="n\n"):
            (td / "net.log").unlink(missing_ok=True); r = sh(["bash", str(dep / "deploy.sh"), mode], dep, dict(env, W3_PLANNER=str(pl)), stdin); return r, (td / "net.log").exists()
        record(head(), ctime() + 5)
        r, net = run()
        check("deploy.sh: the dist built from git HEAD after the last commit passes the guard (it goes on to the dry run and asks before the real deploy; nothing is deployed here)", "REFUSED" not in r.stderr and "aborted, nothing changed" in r.stdout and r.returncode == 1, r.stdout[-200:] + r.stderr[-200:])
        built_old = head(); (pl / "a.txt").write_text("2"); sh(["git", "commit", "-qam", "two"], pl, env)
        r, net = run()
        check("deploy.sh: a new commit after the build (the dist's recorded commit is not git HEAD) is refused before any ssh or rsync call", r.returncode != 0 and "REFUSED" in r.stderr and built_old in r.stderr and head() in r.stderr and not net, r.stderr[-300:])
        record(head(), ctime() - 1)
        r, net = run()
        check("deploy.sh: a dist built before the last commit (same commit hash, older time) is refused as older, before any ssh or rsync call", r.returncode != 0 and "older than the planner's last commit" in r.stderr and not net, r.stderr[-300:])
        (dep / "dist.commit").unlink(); record(head(), ctime() + 5); (dep / "dist.commit").unlink()
        r, net = run()
        check("deploy.sh: a dist with no recorded build commit is refused", r.returncode != 0 and "REFUSED" in r.stderr and "unknown commit" in r.stderr and not net, r.stderr[-300:])
        record(head(), ctime() + 5); (dep / "dist" / "witcher-3" / "index.html").write_text("changed")
        r, net = run()
        check("deploy.sh: a dist changed after the build (hash mismatch) is still refused", r.returncode != 0 and "hash mismatch" in r.stderr and not net)
        (dep / "dist" / "witcher-3" / "index.html").write_text("planner"); record(head(), ctime() + 5)
        r, net = run("live")
        check("deploy.sh live: the same guard comes first (no APPROVED file: refused, and the commit check is not skipped for it)", r.returncode != 0 and "REFUSED" in r.stderr and not net, r.stderr[-200:])
        sh(["git", "commit", "-q", "--allow-empty", "-m", "three"], pl, env)
        r, net = run("live")
        check("deploy.sh live: a new commit after the build is refused for live too", r.returncode != 0 and "was built from" in r.stderr and not net, r.stderr[-200:])
        r, net = run("build", "")
        check("deploy.sh build: runs build.sh (and nothing else)", r.returncode == 0 and (dep / "build.ran").exists() and not net, r.stderr[-200:])
        r, _ = run("bogus", "")
        check("deploy.sh: an unknown mode prints the usage (build|preview|live)", r.returncode == 2 and "build|preview|live" in r.stderr, r.stderr)
