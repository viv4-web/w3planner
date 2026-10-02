"""Link compatibility: every link ever made must still open as the build it was made for.

Fixtures (tests/fixtures):
  legacy_links.json      links made by v7 to v23: {code, expect: [level, bonus, skills, first 12 slots, mutagens, researched, active], made_by}
  links/<version>.txt    one link per line, made by that version's code (v24 and later)
  links/<version>.json   {code: {name, expect: {level, bonus, lv, slots, muts, mres, mact}}} for every line of the .txt
Fixtures are append-only: see append_only_problems(). A failing link test blocks a release (CLAUDE.md).
"""
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
LEGACY_STATE = "[+document.getElementById('lvl').value,+document.getElementById('bonuspts').value,S.lv,S.slots.slice(0,12),S.muts,S.mres,S.mact]"
FULL_STATE = "({level:+document.getElementById('lvl').value,bonus:+document.getElementById('bonuspts').value,lv:S.lv,slots:S.slots,muts:S.muts,mres:S.mres,mact:S.mact,gear:S.gear,ruleset:S.rs,cons:S.cons,screen:S.scr})"
READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"


def load_fixtures():
    """Returns (fixtures, problems). A fixture is {kind, version, name, code, expect}."""
    out, problems = [], []
    for e in json.loads((FIX / "legacy_links.json").read_text()):
        out.append({"kind": "legacy", "version": e["made_by"], "name": "link made by " + e["made_by"], "code": e["code"], "expect": e["expect"]})
    for txt in sorted((FIX / "links").glob("*.txt")):
        js = txt.with_suffix(".json")
        if not js.is_file(): problems.append("%s has no matching .json" % txt.name); continue
        codes = [c for c in txt.read_text().split("\n") if c.strip()]; exp = json.loads(js.read_text())
        if len(set(codes)) != len(codes): problems.append("%s lists a link twice" % txt.name)
        if set(codes) != set(exp): problems.append("%s and %s do not list the same links" % (txt.name, js.name))
        for c in codes:
            if c in exp: out.append({"kind": "full", "version": txt.stem, "name": exp[c]["name"], "code": c, "expect": exp[c]["expect"]})
    return out, problems


def open_and_compare(browser, base, fx):
    """Open one fixture link in a fresh page at `base` (a site URL or the offline index.html) and compare the build. Returns (ok, detail)."""
    pg = browser.new_page(viewport={"width": 1300, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100]))
    try:
        pg.goto(base + "#" + fx["code"]); pg.wait_for_function(READY, timeout=15000)
        if fx["kind"] == "legacy":
            got, ex = pg.evaluate(LEGACY_STATE), fx["expect"]
            ok = got[:5] == ex[:5] and (ex[5] is None or (got[5] == ex[5] and got[6] == ex[6])); detail = "" if ok else "expected %s, got %s" % (json.dumps(ex)[:80], json.dumps(got)[:80])
        else:
            if fx["expect"].get("cons") and any(fx["expect"]["cons"]): [pg.wait_for_timeout(100) for _ in range(150) if not pg.evaluate("typeof CN!=='undefined'&&!!CN.data&&typeof EQ!=='undefined'&&!EQ.err&&!!eqData()")]; pg.wait_for_timeout(500)   # the consumable data loads after the page; the bomb rule below runs when it has
            got = pg.evaluate(FULL_STATE); ex = dict(fx["expect"]); bad0 = []
            if fx["version"] < "v31b" and ex.get("cons") and ex["cons"][5]:
                # v31b: the second bomb slot became the Pocket. A bomb an older link holds there moves to the Bomb slot when that is empty, else it is dropped (the fixture itself is never edited)
                c = list(ex["cons"]); c[4], c[5] = (c[5] if not c[4] else c[4]), 0; ex["cons"] = c
                if pg.evaluate("location.hash.slice(1)") != fx["code"]: bad0 = ["the link text was rewritten on open"]
            bad = [k for k in ex if got.get(k) != ex[k]] + bad0
            if fx["version"] < "v28" and (got["screen"] != "char" or any(got["cons"])): bad.append("screen/cons (a link made before v28 opens on Character with no consumables)")
            ok = not bad; detail = "differs in: " + ", ".join(bad) if bad else ""
        if errs: ok, detail = False, "script error: " + errs[0]
        return ok, detail
    except Exception as e:
        return False, "page did not open: " + str(e).split("\n")[0][:100]
    finally:
        pg.close()


def check_fixtures(browser, base, label, check):
    """Run every fixture against `base`. `check(name, ok, detail)` records each result."""
    fixtures, problems = load_fixtures()
    check("%s: link fixtures are well formed (%d links)" % (label, len(fixtures)), not problems, "; ".join(problems))
    for fx in fixtures:
        ok, detail = open_and_compare(browser, base, fx)
        check("%s: %s link opens as expected (%s)" % (label, fx["version"], fx["name"][:50]), ok, detail)


def _git_show(ref, path):
    r = subprocess.run(["git", "show", "%s:%s" % (ref, path)], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def append_only_problems():
    """Compare the fixtures here with those on main: nothing may be edited or removed, only added.
    Returns (problems, note). `note` says so when there was no main to compare with (a shallow checkout)."""
    ref = next((r for r in ("origin/main", "main") if subprocess.run(["git", "rev-parse", "--verify", "-q", r], cwd=ROOT, capture_output=True).returncode == 0), None)
    if not ref: return [], "no main branch to compare with, append-only check skipped"
    ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "tests/fixtures", "data/item_ids.json"], cwd=ROOT, capture_output=True, text=True).stdout.split()   # item_ids.json: the numbers a gear link stores
    problems = []
    for path in ls:
        if path.endswith("tooltips_ref.json") or path.endswith("README.md") or path.startswith("tests/fixtures/glossary/"): continue   # the fake Glossary content (binary pictures too) is rewritten by tests/make_glossary_fixture.py: not a link fixture
        old, cur = _git_show(ref, path), (ROOT / path).read_text() if (ROOT / path).is_file() else None
        if cur is None: problems.append("%s was deleted" % path); continue
        if path.endswith(".txt"):
            lost = set(old.split("\n")) - set(cur.split("\n")); lost.discard("")
            if lost: problems.append("%s lost or changed %d links" % (path, len(lost)))
        elif path.endswith("item_ids.json"):
            o, c = json.loads(old)["ids"], json.loads(cur)["ids"]; lost = [k for k in o if c.get(k) != o[k]]
            if lost: problems.append("%s renumbered or dropped %d ids (append-only)" % (path, len(lost)))
        elif path.endswith(".json"):
            o, c = json.loads(old), json.loads(cur)
            if isinstance(o, dict): lost = [k for k in o if c.get(k) != o[k]]
            else: lost = [e for e in o if e not in c]
            if lost: problems.append("%s lost or changed %d entries" % (path, len(lost)))
    return problems, "compared with " + ref
