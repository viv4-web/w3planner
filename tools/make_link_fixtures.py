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
import argparse, json, re, subprocess, sys, tempfile, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import serve
from playwright.sync_api import sync_playwright

# In-page builder. spec: {level, bonus, trees:[ti..], fill:'max'|'start', research:[mutation ids], active, equip:bool, muts:[mutagen ids]}
BUILD = """async spec=>{
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
 // gear (v27 and later): the items are chosen by id from the real data, stored as their registry numbers
 if(spec.rs){const rs=spec.rs;await eqLoad(rs);S.rs=rs;Object.entries(spec.gear||{}).forEach(([slot,id])=>{const it=EQ.rs[rs].byId.get(id);if(!it||it.slot!==slot)throw new Error('bad gear '+slot+' '+id);S.gear[EQ_SLOTS.indexOf(slot)]=it.n})}
 if(spec.cons){await cnLoad();Object.entries(spec.cons).forEach(([k,id])=>{const it=CN.byId.get(id);if(!it||!cnAccepts(k,it))throw new Error('bad consumable '+k+' '+id);S.cons[CN_SLOTS.indexOf(k)]=it.n})}
 if(spec.scr)S.scr=spec.scr;
 const state=()=>({level:+document.getElementById('lvl').value,bonus:+document.getElementById('bonuspts').value,lv:S.lv,slots:S.slots,muts:S.muts,mres:S.mres,mact:S.mact,gear:S.gear,ruleset:S.rs,cons:S.cons,screen:S.scr});
 const expect=JSON.parse(JSON.stringify(state())),code=enc().slice(0);
 // sanity: the build must be legal and must survive its own link
 const bad=[];if(spent()>budget())bad.push('overspent '+spent()+'>'+budget());
 const t=dec(code);if(!t)bad.push('does not decode');else{const l=JSON.stringify(expect);
   const got=JSON.stringify({level:+document.getElementById('lvl').value,bonus:+document.getElementById('bonuspts').value,lv:t.lv,slots:t.slots,muts:t.muts,mres:t.mres,mact:t.mact,gear:t.gear,ruleset:t.rs,cons:t.cons,screen:t.scr});if(l!==got)bad.push('round trip differs')}
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


def gear_specs():
    """v27: share links that carry the gear segment (g1): every slot alone in both rulesets, full sets, a mix with skills and mutagens, empty gear."""
    out = []; add = lambda name, **kw: out.append((name, kw))
    full = {"steel": "Lynx School steel sword 4", "silver": "Lynx School silver sword 4", "crossbow": "Lynx School Crossbow", "bolts": "Explosive Bolt Legendary", "chest": "Lynx Armor 4",
            "gloves": "Lynx Gloves 5", "trousers": "Lynx Pants 5", "boots": "Lynx Boots 5", "mask": "Geralt mask Nilf"}
    add("no gear, first playthrough (no gear segment at all)", level=1, bonus=0)
    add("no gear, New Game Plus (the segment is only the mode)", level=1, bonus=0, rs="ng_plus")
    for rs, label in (("ng", "first playthrough"), ("ng_plus", "New Game Plus")):
        for slot, item in full.items():
            add("%s only, %s" % (slot, label), level=60, bonus=0, rs=rs, gear={slot: item})
    add("full gear, Feline Grandmaster, first playthrough", level=100, bonus=100, rs="ng", gear=full)
    add("full gear, Feline legendary, New Game Plus", level=100, bonus=100, rs="ng_plus", gear=dict(full, mask="Wolf Bandana"))
    add("mixed sets, first playthrough", level=100, bonus=100, rs="ng", gear={"steel": "Wolf School steel sword 4", "silver": "Aerondight", "chest": "Bear Armor 4", "gloves": "Gryphon Gloves 5", "boots": "Wolf Boots 5", "trousers": "Red Wolf Pants 2", "bolts": "Bodkin Bolt"})
    add("highest item numbers in every slot", level=100, bonus=100, rs="ng_plus", gear={"steel": None, "silver": None})   # replaced below
    add("skills, mutagens and gear together", level=100, bonus=100, trees=[1], fill="max", equip=True, research=[0, 1, 2], active=2, muts=[9, 18, 27, 3], rs="ng", gear=full)
    return out


def gear_specs_b():
    """v27b: links with the items added after the first v27 fixtures (Wolf School tiers 1-4, DLC Temerian, Nilfgaardian, Skellige, Nekker boots, the DLC13 crossbows, and their NGP copies):
    each in both rulesets where it exists, a full Basic Wolven set, mixes with older items, and the highest item numbers."""
    out = []; add = lambda name, **kw: out.append((name, kw))
    wolf = {"steel": "Wolf School steel sword", "silver": "Wolf School silver sword", "chest": "Wolf Armor", "gloves": "Wolf Gloves 1", "trousers": "Wolf Pants 1", "boots": "Wolf Boots 1"}
    add("Wolven Basic set, first playthrough", level=100, bonus=0, rs="ng", gear=wolf)
    add("Wolven Basic set, New Game Plus", level=100, bonus=0, rs="ng_plus", gear=wolf)
    add("Wolven Mastercrafted set, first playthrough", level=100, bonus=0, rs="ng", gear={"steel": "Wolf School steel sword 3", "silver": "Wolf School silver sword 3", "chest": "Wolf Armor 3", "gloves": "Wolf Gloves 4", "trousers": "Wolf Pants 4", "boots": "Wolf Boots 4"})
    add("Legendary Wolven Basic set, New Game Plus (the NGP ids)", level=100, bonus=0, rs="ng_plus", gear={"steel": "NGP Wolf School steel sword", "silver": "NGP Wolf School silver sword", "chest": "NGP Wolf Armor", "gloves": "NGP Wolf Gloves 1", "trousers": "NGP Wolf Pants 1", "boots": "NGP Wolf Boots 1"})
    add("Wolven Enhanced chest only, first playthrough", level=60, bonus=0, rs="ng", gear={"chest": "Wolf Armor 1"})
    add("Temerian armor set, first playthrough", level=100, bonus=0, rs="ng", gear={"chest": "DLC1 Temerian Armor", "gloves": "DLC1 Temerian Gloves", "trousers": "DLC1 Temerian Pants", "boots": "DLC1 Temerian Boots"})
    add("Temerian armor set, New Game Plus (NGP copies)", level=100, bonus=0, rs="ng_plus", gear={"chest": "NGP DLC1 Temerian Armor", "gloves": "NGP DLC1 Temerian Gloves", "trousers": "NGP DLC1 Temerian Pants", "boots": "NGP DLC1 Temerian Boots"})
    add("Nilfgaardian and Skellige pieces mixed, first playthrough", level=100, bonus=0, rs="ng", gear={"chest": "DLC5 Nilfgaardian Armor", "gloves": "DLC14 Skellige Gloves", "trousers": "DLC5 Nilfgaardian Pants", "boots": "DLC14 Skellige Boots"})
    add("Nekker boots and the Elven crossbow, first playthrough", level=100, bonus=0, rs="ng", gear={"boots": "Nekker Boots", "crossbow": "DLC13 Elven Crossbow"})
    add("Skellige crossbow, New Game Plus", level=100, bonus=0, rs="ng_plus", gear={"crossbow": "DLC13 Skellige Crossbow"})
    add("new and old items together, first playthrough", level=100, bonus=100, trees=[1], fill="max", equip=True, rs="ng", gear={"steel": "Wolf School steel sword 2", "silver": "Lynx School silver sword 4", "chest": "Wolf Armor 4", "boots": "Nekker Boots", "crossbow": "DLC13 Nilfgaardian Crossbow"})
    add("highest item numbers in every slot (after the v27b import)", level=100, bonus=100, rs="ng_plus", gear={"steel": None, "silver": None})   # replaced below
    return out


def gear_specs_v28():
    """v28: links with the consumables segment (c1) and the Inventory screen (s1I), in both rulesets, with and without gear and skills."""
    out = []; add = lambda name, **kw: out.append((name, kw))
    cons = {"potion1": "Swallow 3", "potion2": "Mutagen 1", "potion3": "Cat 2", "potion4": "White Raffards Decoction 3", "petard1": "Dancing Star 3", "petard2": "Samum 1", "oil_steel": "Beast Oil 3", "oil_silver": "Vampire Oil 2"}
    gear = {"steel": "Lynx School steel sword 4", "silver": "Lynx School silver sword 4", "chest": "Lynx Armor 4", "gloves": "Lynx Gloves 5", "trousers": "Lynx Pants 5", "boots": "Lynx Boots 5"}
    add("every consumable slot and both oils, Character screen, first playthrough", level=100, bonus=0, rs="ng", cons=cons)
    add("every consumable slot and both oils, Inventory screen, first playthrough", level=100, bonus=0, rs="ng", cons=cons, scr="inv")
    add("Inventory screen, nothing equipped", level=1, bonus=0, scr="inv")
    add("Inventory screen with gear and every consumable slot, New Game Plus", level=100, bonus=100, rs="ng_plus", cons=cons, gear=gear, scr="inv")
    add("one decoction and one bomb only, Character screen", level=60, bonus=0, rs="ng", cons={"potion3": "Mutagen 28", "petard2": "Snow Ball"})
    add("oils only (steel and silver), Inventory screen", level=60, bonus=0, rs="ng", cons={"oil_steel": "Hanged Man Venom 1", "oil_silver": "Necrophage Oil 3"}, scr="inv")
    add("skills, mutagens, gear and consumables together, Inventory screen", level=100, bonus=100, trees=[2], fill="max", equip=True, research=[0, 1, 2], active=2, muts=[9, 18, 27, 3], rs="ng", gear=gear, cons=cons, scr="inv")
    add("highest consumable numbers in every slot", level=100, bonus=100, rs="ng", cons={"potion1": "Mutagen 28", "potion2": "White Raffards Decoction 3", "potion3": "Thunderbolt 3", "potion4": "White Honey 3", "petard1": "White Frost 3", "petard2": "Snow Ball", "oil_steel": "Hanged Man Venom 3", "oil_silver": "Vampire Oil 3"})
    return out


def gear_specs_v29():
    """v29: links that end in s1G (the Glossary screen is open), alone and with skills, mutagens, gear and consumables, in both rulesets; plus the same build on Inventory and on Character for comparison."""
    out = []; add = lambda name, **kw: out.append((name, kw))
    cons = {"potion1": "Swallow 3", "potion2": "Mutagen 1", "potion3": "Cat 2", "potion4": "White Raffards Decoction 3", "petard1": "Dancing Star 3", "petard2": "Samum 1", "oil_steel": "Beast Oil 3", "oil_silver": "Specter Oil 2"}
    gear = {"steel": "Lynx School steel sword 4", "silver": "Lynx School silver sword 4", "chest": "Lynx Armor 4", "gloves": "Lynx Gloves 5", "trousers": "Lynx Pants 5", "boots": "Lynx Boots 5"}
    add("Glossary screen, empty build, level 1", level=1, bonus=0, scr="glo")
    add("Glossary screen, level 100 with 100 bonus points", level=100, bonus=100, scr="glo")
    add("Glossary screen with gear and every consumable slot, first playthrough", level=100, bonus=0, rs="ng", gear=gear, cons=cons, scr="glo")
    add("Glossary screen, New Game Plus, gear and consumables", level=100, bonus=100, rs="ng_plus", gear=gear, cons=cons, scr="glo")
    add("Glossary screen with skills, mutations, mutagens, gear and consumables together", level=100, bonus=100, trees=[1], fill="max", equip=True, research=[0, 1, 2], active=2, muts=[9, 18, 27, 3], rs="ng", gear=gear, cons=cons, scr="glo")
    add("the same full build on the Inventory screen", level=100, bonus=100, trees=[1], fill="max", equip=True, research=[0, 1, 2], active=2, muts=[9, 18, 27, 3], rs="ng", gear=gear, cons=cons, scr="inv")
    add("the same full build on the Character screen", level=100, bonus=100, trees=[1], fill="max", equip=True, research=[0, 1, 2], active=2, muts=[9, 18, 27, 3], rs="ng", gear=gear, cons=cons)
    return out


def gear_specs_v31b():
    """v31b: the second bomb slot is the Pocket, and the potion slots take food and drink. Torch and Oil Lamp in the Pocket, food and drink in every potion slot, with a bomb, with oils, on Inventory and Character."""
    out = []; add = lambda name, **kw: out.append((name, kw))
    cons = {"potion1": "Cows milk", "potion2": "Bottled water", "potion3": "Swallow 3", "potion4": "Cat 2", "petard1": "Dancing Star 3", "pocket": "Torch", "oil_steel": "Beast Oil 3", "oil_silver": "Vampire Oil 2"}
    gear = {"steel": "Lynx School steel sword 4", "silver": "Lynx School silver sword 4", "chest": "Lynx Armor 4", "gloves": "Lynx Gloves 5", "trousers": "Lynx Pants 5", "boots": "Lynx Boots 5"}
    add("Torch in the Pocket and food in two potion slots, Inventory screen", level=100, bonus=0, rs="ng", cons=cons, scr="inv")
    add("the same on Character, New Game Plus, with gear", level=100, bonus=100, rs="ng_plus", cons=cons, gear=gear)
    add("Oil Lamp in the Pocket only", level=40, bonus=0, rs="ng", cons={"pocket": "Oil Lamp"}, scr="inv")
    add("food and drink only, in all four potion slots", level=60, bonus=0, rs="ng", cons={"potion1": "Cows milk", "potion2": "Bottled water", "potion3": "Beauclair White", "potion4": "Kaedwenian Stout"}, scr="inv")
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
    app = re.sub(r"[a-z]+$", "", a.version)                      # v27b: more links made by the v27 code (new items)
    if have != 'APP_VERSION="%s"' % app: sys.exit("the code being built says %s, not %s" % (have, app))
    server = serve.make_server(site, 0); threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:%d/" % server.server_address[1]); pg.wait_for_timeout(700)
        info = pg.evaluate("""({ntrees:TREES.length,nmut:MUT.length,nmutagen:MUTS.length,
            special:MUTS.map((m,i)=>m.special?i:-1).filter(i=>i>=0),regular:MUTS.map((m,i)=>m.special?-1:i).filter(i=>i>=0)})""")
        rows, seen = [], set()
        use = specs(info) if a.version == "v24" else gear_specs() if a.version == "v27" else gear_specs_b() if a.version == "v27b" else gear_specs_v28() if a.version == "v28" else gear_specs_v29() if a.version == "v29" else gear_specs_v31b() if a.version == "v31b" else sys.exit("no fixture recipe for %s: add one to this tool" % a.version)
        top = pg.evaluate("async rs=>{await eqLoad(rs);const o={};EQ_SLOTS.forEach(s=>{const l=EQ.rs[rs].bySlot[s]||[];o[s]=l.reduce((a,b)=>a.n>b.n?a:b).id});return o}", "ng_plus") if a.version in ("v27", "v27b") else {}
        for name, spec in use:
            if spec.get("gear") == {"steel": None, "silver": None}: spec = dict(spec, gear=top)
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
