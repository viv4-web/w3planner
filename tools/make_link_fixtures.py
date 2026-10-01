#!/usr/bin/env python3
"""Create the share-link fixtures for one app version with the CURRENT code: tests/fixtures/links/<version>.txt
(one link per line) and <version>.json (each link's name and the build it must open as).

    python tools/make_link_fixtures.py --version v24

Fixtures are append-only: this tool refuses to overwrite an existing file, and an old fixture must never be edited
(see CLAUDE.md, "Link compatibility"). Run it again only for a new version whose code changes the link format or the
numbering of skills, mutations or mutagens, so the new links join the old ones. Builds are described here, set directly
into the page state (valid for the rules, see the in-page builder) and the expected state is what was built, not what
was decoded, so a decoding bug cannot hide in the expectation.
"""
import argparse, json, subprocess, sys, tempfile, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import serve
from playwright.sync_api import sync_playwright

# In-page builder. spec: {level, bonus, trees:[ti..], fill:'max'|'start', research:[mutation ids], active, equip:bool, muts:[mutagen ids]}
BUILD = """spec=>{
 render=()=>{};history.replaceState=()=>{};
 S=blank();document.getElementById('lvl').value=spec.level;document.getElementById('bonuspts').value=spec.bonus;
 const research=i=>{if(S.mres[i])return;MUT[i].req.forEach(research);S.mres[i]=1};
 (spec.research||[]).forEach(research);
 if(spec.active!=null&&S.mres[spec.active])S.mact=spec.active;
 // skills: raise levels in dependency order until the budget (or the tree) is used up
 const grow=(ti,cap)=>{let moved=true,n=0;while(moved&&n<cap){moved=false;
   TREES[ti].sk.forEach((s,i)=>{if(S.lv[ti][i]<mx(ti,i)&&available(ti,i)&&spent()<budget()&&n<cap){S.lv[ti][i]++;n++;moved=true}})}};
 (spec.trees||[]).forEach(ti=>grow(ti,spec.fill==='start'?spec.startPoints||12:999));
 if(spec.equip){let k=0;const used=new Set();
   for(let s=0;s<16;s++){if(!slotOpen(s))continue;
     for(let ti=0;ti<4;ti++)for(let i=0;i<20&&TREES[ti]&&i<TREES[ti].sk.length;i++){
       if(S.slots[s]||!S.lv[ti][i]||used.has(ti+'.'+i)||!accepts(s,[ti,i]))continue;S.slots[s]=[ti,i];used.add(ti+'.'+i)}}}
 (spec.muts||[]).forEach((m,g)=>{if(sockOpen(g))S.muts[g]=m});
 enforceLocks();
 const state=()=>({level:+document.getElementById('lvl').value,bonus:+document.getElementById('bonuspts').value,lv:S.lv,slots:S.slots,muts:S.muts,mres:S.mres,mact:S.mact});
 const expect=JSON.parse(JSON.stringify(state())),code=enc().slice(0);
 // sanity: the build must be legal and must survive its own link
 const bad=[];if(spent()>budget())bad.push('overspent '+spent()+'>'+budget());
 const t=dec(code);if(!t)bad.push('does not decode');else{const l=JSON.stringify(expect);
   const got=JSON.stringify({level:+document.getElementById('lvl').value,bonus:+document.getElementById('bonuspts').value,lv:t.lv,slots:t.slots,muts:t.muts,mres:t.mres,mact:t.mact});if(l!==got)bad.push('round trip differs')}
 return {code,expect,bad,spent:spent(),budget:budget()}}"""


def specs(info):
    """The ~40 builds. info = {ntrees, nmut, nmutagen, special:[ids], regular:[ids], mut_cols:[...]}"""
    out = []
    add = lambda name, **kw: out.append((name, kw))
    all_t = list(range(info["ntrees"])); all_m = list(range(info["nmut"]))
    add("empty, level 1", level=1, bonus=0)
    add("empty, level 100 with 100 bonus points", level=100, bonus=100)
    add("level 100, no bonus points, red tree", level=100, bonus=0, trees=[0], fill="max", equip=True)
    for t in all_t:
        add("starter build, tree %d (level 20)" % t, level=20, bonus=0, trees=[t], fill="start", equip=True)
    for t in all_t:
        add("tree %d fully raised, slots filled (level 100, 100 bonus)" % t, level=100, bonus=100, trees=[t], fill="max", equip=True)
    add("level 1, 100 bonus points, one tree", level=1, bonus=100, trees=[1], fill="start", equip=True)
    add("every tree, every mutation, four special mutagens (full build)", level=100, bonus=100, research=all_m, active=info["nmut"] - 1,
        trees=all_t, fill="max", equip=True, muts=info["special"][:4])
    add("all mutations researched, none active", level=100, bonus=100, research=all_m, trees=[1], fill="max", equip=True)
    for m in all_m:
        add("mutation %d researched and active, mutation slots filled" % m, level=100, bonus=100, research=[m], active=m, trees=all_t, fill="max", equip=True, muts=[info["regular"][m % 9]])
    sp = info["special"]
    for k in range(0, len(sp), 4):
        add("special mutagens %s" % ",".join(map(str, sp[k:k + 4])), level=60, bonus=0, trees=[1], fill="max", equip=True, muts=sp[k:k + 4])
    rg = info["regular"]
    for k in range(0, len(rg), 4):
        add("regular mutagens %s" % ",".join(map(str, rg[k:k + 4])), level=60, bonus=0, trees=[2], fill="max", equip=True, muts=rg[k:k + 4])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True, help="the app version whose code makes the links, e.g. v24")
    a = ap.parse_args()
    d = ROOT / "tests/fixtures/links"; d.mkdir(parents=True, exist_ok=True)
    txt, js = d / (a.version + ".txt"), d / (a.version + ".json")
    if txt.exists() or js.exists(): sys.exit("%s fixtures already exist: fixtures are append-only, never regenerate or edit them" % a.version)
    site = Path(tempfile.mkdtemp(prefix="w3fix-")) / "site"
    if subprocess.run([sys.executable, str(ROOT / "tools/build.py"), "--variant", "placeholder", "--out", str(site)]).returncode: sys.exit("build failed")
    have = subprocess.run(["grep", "-o", 'APP_VERSION="[^"]*"', str(site / "index.html")], capture_output=True, text=True).stdout.strip()
    if have != 'APP_VERSION="%s"' % a.version: sys.exit("the code being built says %s, not %s" % (have, a.version))
    server = serve.make_server(site, 0); threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/" % server.server_address[1]); pg.wait_for_timeout(700)
        info = pg.evaluate("""({ntrees:TREES.length,nmut:MUT.length,nmutagen:MUTS.length,
            special:MUTS.map((m,i)=>m.special?i:-1).filter(i=>i>=0),regular:MUTS.map((m,i)=>m.special?-1:i).filter(i=>i>=0)})""")
        rows, seen = [], set()
        for name, spec in specs(info):
            r = pg.evaluate(BUILD, spec)
            if r["bad"] or errs: sys.exit("could not build %r: %s %s" % (name, r["bad"], errs[:1]))
            if r["code"] in seen: sys.exit("duplicate link for %r" % name)
            seen.add(r["code"]); rows.append({"name": name, "code": r["code"], "expect": r["expect"]})
        b.close()
    server.shutdown()
    txt.write_text("".join(r["code"] + "\n" for r in rows), encoding="utf-8")
    js.write_text(json.dumps({r["code"]: {"name": r["name"], "expect": r["expect"]} for r in rows}, indent=1) + "\n", encoding="utf-8")
    print("wrote %d links to %s and %s" % (len(rows), txt.relative_to(ROOT), js.relative_to(ROOT)))


if __name__ == "__main__":
    main()
