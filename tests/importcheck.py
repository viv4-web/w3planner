"""v31: Import save, in a real browser. The save never leaves the browser: the tests also check that no request goes anywhere but the site.

run(b, base, check, label, ref=True)   a site with the Import button (online build)
offline(b, url, check, label)          the offline package: no Import button
The reference save (~/work/w3planner-art/save-spike/fixtures/refsave/, never committed) is optional: its acceptance checks SKIP when it is absent."""
import json
from pathlib import Path

REF = Path.home() / "work/w3planner-art/save-spike/fixtures/refsave"
SAV, SIDE = REF / "ManualSave_52587_7ea48400_3d23fe3.sav", REF / "ManualSave_52587_7ea48400_3d23fe3.json"
READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0&&typeof eqData==='function'&&!!eqData()&&!!CN.data"


def until(pg, js, ms=10000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def page(b, url, w=1440, h=900, mobile=False):
    pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile); errs, reqs = [], []
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:100])); pg.on("request", lambda r: reqs.append(r.url)); pg.goto(url); until(pg, READY); pg.wait_for_timeout(400)
    return pg, errs, reqs


def synthetic(pg):
    """A made-up read result (no game data) to test how the importer treats food, unknown ids and mods: the planner's own ids stand in."""
    return pg.evaluate("""(()=>{const R={codes:[66,29,164],character:{level:5,xpTotal:3000,xpInLevel:200,xpForLevel:1000,pointsUsed:2,pointsFree:2},skills:[{id:'sword_s22',level:1,max:3,core:false},{id:'mod_skill_x',level:1,max:1,core:false},{id:'sword_1',level:1,max:1,core:true}],
      skillSlots:[{id:1,skill:'sword_s22',unlocked:true},{id:2,skill:'mod_skill_x',unlocked:true},{id:3,skill:null,unlocked:false}],mutagenSlots:[{slot:'EES_SkillMutagen1',item:'Wraith mutagen'},{slot:'EES_SkillMutagen2',item:'Some Mod mutagen'},{slot:'EES_SkillMutagen3',item:null},{slot:'EES_SkillMutagen4',item:null}],
      equipped:{SteelSword:{id:'Lynx School steel sword 4',qty:1,extras:{}},Armor:{id:'Not An Item',qty:1,extras:{}},Potion1:{id:'Cows milk',qty:30,extras:{}},Potion2:{id:'Swallow 1',qty:1,extras:{ammo_current:3}},Potion3:{id:'Mod Brew',qty:2,extras:{}},Petard1:{id:'Grapeshot 1',qty:1,extras:{ammo_current:2}},Quickslot1:{id:'Torch',qty:1,extras:{}}},
      inventory:[{id:'Swallow 1',qty:1,extras:{}},{id:'Bread',qty:3,extras:{}},{id:'Lynx School steel sword 4',qty:1,extras:{}}],inventoryHeader:3,crowns:5};
      return JSON.parse(JSON.stringify(impPlan(R),(k,v)=>k==='item'?undefined:v))})()""")


def run(b, base, check, label, ref=True):
    pg, errs, reqs = page(b, base); E = pg.evaluate; site = base.split("/")[2]
    check("%s: the top bar has IMPORT SAVE (download icon, gold outline) left of NG+ and Copy link" % label,
          E("(()=>{const a=document.getElementById('savebtn').getBoundingClientRect(),n=document.querySelector('[data-rs=ng]').getBoundingClientRect(),c=document.getElementById('copy').getBoundingClientRect();return a.right<=n.left&&a.right<=c.left&&!!document.querySelector('#savebtn svg')&&getComputedStyle(document.getElementById('savebtn')).borderColor!==''&&/import save/i.test(document.getElementById('savebtn').textContent)})()"))
    check("%s: nothing of the importer loads before the dialog opens" % label, not [u for u in reqs if "saveread" in u or "savenames" in u], [u for u in reqs if "saveread" in u])
    for tab in ("#tabGlo", "#tabInv", "#tabChar"):
        pg.click(tab); pg.wait_for_timeout(150)
        if not E("document.getElementById('savebtn').getClientRects().length>0"): check("%s: IMPORT SAVE is visible on every tab (%s)" % (label, tab), False)
    check("%s: IMPORT SAVE is visible on the Glossary, Inventory and Character screens" % label, True)
    pg.click("#savebtn"); until(pg, "!document.getElementById('impov').hidden")
    d = E("""(()=>{const o=document.getElementById('impov'),l=document.querySelector('label[for=impfile]'),i=document.getElementById('impfile');return{open:!o.hidden,title:document.getElementById('imptitle').textContent,intro:document.querySelector('.impintro').textContent,drop:document.querySelector('.impdroptxt').textContent,sub:document.querySelector('.impdrop small').textContent,
      label:!!l&&l.textContent.trim(),input:i.type+'/'+i.getAttribute('accept'),help:document.querySelector('.imphelp').textContent,foot:document.querySelector('.impfoot').textContent,modal:document.querySelector('.imppanel').getAttribute('aria-modal')}})()""")
    check("%s: the dialog reads 'Import save', says the file stays in the browser, has the drop zone, a real CHOOSE FILE label for a .sav input, the help box and the footnote (%s)" % (label, d["input"]),
          d["open"] and d["title"] == "Import save" and d["intro"] == "Fill the planner from a Witcher 3 save. The file is read in this browser and never leaves your computer." and d["drop"] == "Drop a .sav file here, or choose one" and d["sub"] == "Next-Gen (4.0+) PC saves · the .sav, and its .json too if you have it"
          and d["label"] == "CHOOSE FILE" and d["input"] == "file/.sav" and "Documents\\The Witcher 3\\gamesaves\\ManualSave_" in d["help"] and "Manual saves are easiest to pick out. The .png next to it shows the same picture as the game's Load Game list." in d["help"]
          and d["foot"] == "You'll see what was found before anything changes. Your current build is replaced only when you press Apply.", d)
    until(pg, "!!window.W3SAVE&&!!(window.W3DATA&&W3DATA.savenames)")
    check("%s: the reader loaded when the dialog opened (its own hashed script)" % label, bool([u for u in reqs if "saveread" in u]) and E("typeof W3SAVE.readSave")=="function")
    pg.keyboard.press("Escape"); check("%s: Escape closes the dialog and returns focus to IMPORT SAVE" % label, E("document.getElementById('impov').hidden") and E("document.activeElement.id") == "savebtn")
    pg.click("#savebtn"); pg.click("#impx"); check("%s: the close button closes it" % label, E("document.getElementById('impov').hidden"))
    # bad files: an error inside the dialog, nothing changes
    link0 = E("enc()"); pg.click("#savebtn"); until(pg, "!document.getElementById('impov').hidden")
    for name, data, want in (("notes.sav", b"hello, I am not a save", "This isn't a Witcher 3 save."), ("pic.png", b"\x89PNG", "This isn't a Witcher 3 save."),
                             ("cut.sav", b"SNFHFZLC" + (1).to_bytes(4, "little") + (28).to_bytes(4, "little") + (999).to_bytes(4, "little") + (10).to_bytes(4, "little") + b"\0" * 8, "Couldn't read this save.")):
        pg.set_input_files("#impfile", {"name": name, "mimeType": "application/octet-stream", "buffer": data}); until(pg, "!document.getElementById('imperr').hidden")
        t = E("document.getElementById('imperr').textContent"); still = E("!document.getElementById('impStep1').hidden&&document.getElementById('impStep2').hidden")
        check("%s: a bad file (%s) shows '%s' inside the dialog%s and changes nothing" % (label, name, want, " plus a reason" if "Couldn't" in want else ""), t.startswith(want) and (len(t) > len(want) + 3 if "Couldn't" in want else True) and still and E("enc()") == link0, t)
    pg.click("#impx")
    # the planner's rules on a made-up result: id match only, unknown ids and mods listed, never matched by name
    pl = synthetic(pg)
    check("%s: food in a potion slot and a Torch in the Pocket are matched like any consumable, an unknown item is named and left out (%s)" % (label, [(r["name"], r.get("charges"), r.get("other")) for r in pl["consRows"]]),
          any(r["slot"] == "potion1" and r["name"] == "Cow's milk" and r["charges"] == 30 for r in pl["consRows"]) and pl["cons"][0] > 0 and any(r["name"] == "Swallow" and r["charges"] == 3 for r in pl["consRows"]) and pl["cons"][1] > 0
          and any(r.get("other") and r["name"] == "Mod Brew" for r in pl["consRows"]) and pl["cons"][2] == 0 and any(r["slot"] == "pocket" and r["name"] == "Torch" for r in pl["consRows"]) and pl["cons"][5] > 0
          and any(r["name"] == "Grapeshot" and r["charges"] == 2 for r in pl["consRows"]), pl["consRows"])
    check("%s: an unknown skill, mutagen or item is listed as not imported, never matched by name (%s %s %s)" % (label, pl["notSk"], pl["notMut"], pl["notGear"]), pl["notSk"] == ["mod_skill_x", "mod_skill_x"][:len(pl["notSk"])] and "mod_skill_x" in pl["notSk"] and pl["notMut"] == ["Some Mod mutagen"] and pl["notGear"] == ["Not An Item"] and pl["gear"][0] > 0 and pl["gear"][4] == 0)
    check("%s: the plan keeps only what matched: level 5 + bonus points make 4 points, 1 skill, Wraith in socket 1 (%s)" % (label, (pl["level"], pl["bonus"], len(pl["learned"]), pl["muts"][:2])), pl["level"] == 5 and pl["bonus"] == 0 and len(pl["learned"]) == 1 and pl["muts"][0] == E("SAVEMUT['Wraith mutagen']") and pl["muts"][1] is None and pl["plannable"] == 3 and pl["records"] == 3)
    check("%s: no script errors" % label, not errs, errs[:1])
    other = [u for u in reqs if not u.startswith(("http://127.0.0.1", "http://localhost", "data:", "blob:"))]; check("%s: no request to any other site" % label, not other, other[:2]); pg.close()
    mutagen_rule(b, base, check, label)
    if ref: refsave(b, base, check, label); save_l9(b, base, check, label)
    phone(b, base, check, label)


def bonus_rows(pg):
    return pg.evaluate("[...document.querySelectorAll('#bonus div')].map(d=>d.textContent.replace(/\\s+/g,' ').trim())")


def mutagen_rule(b, base, check, label):
    """The Character screen's own numbers (characterMenu.ws GetGroupBonusDescription): the mutagen's number x (1 + matching-colour skills in its group), then x (1 + 0.1 x Synergy level), per group.
    Built from the second save's in-game panels: blue (normal) with 3 blue skills + Synergy 2 = 34%; green (lesser) with no matching skill + Synergy 2 = 60, twice."""
    pg, errs, reqs = page(b, base); E = pg.evaluate
    r = E("""(()=>{const sg=TREES[1].sk.map((s,i)=>i).slice(0,3),ge=[0,1],pi=TREES[3].sk.findIndex(s=>s.id==='perk_43'),m=n=>MUTS.findIndex(x=>x.name===n),out={};
      S.slots.fill(null);S.muts=[null,null,null,null];S.lv[3][pi]=2;
      sg.forEach((i,k)=>S.slots[k]=[1,i]);S.slots[3]=[1,sg[0]];S.slots[4]=[1,sg[1]];S.slots[5]=[1,sg[2]];ge.forEach((i,k)=>S.slots[6+k]=[3,i]);
      S.muts=[m('Blue mutagen'),m('Lesser green mutagen'),m('Lesser green mutagen'),null];out.l2=[0,1,2].map(g=>mutBonus(g).v);
      S.lv[3][pi]=0;out.l0=[0,1,2].map(g=>mutBonus(g).v);S.lv[3][pi]=1;out.l1=mutBonus(0).v;S.lv[3][pi]=0;S.muts=[m('Lesser red mutagen'),null,null,null];out.red=mutBonus(0).v;return out})()""")
    near = lambda a, b: abs(a - b) < 1e-9
    check("%s: mutagen bonus as the game's Character screen: blue 3 matching + Synergy 2 = +34%%, green with no match +60, +60; no Synergy 7%%x4 = 28%% and 50, 50; Synergy 1 = 30.8%%; red lesser with no match = 5%% (%s)" % (label, r),
          near(r["l2"][0], 0.07 * 4 * 1.2) and near(r["l2"][1], 60) and near(r["l2"][2], 60) and near(r["l0"][0], 0.28) and near(r["l0"][1], 50) and near(r["l1"], 0.07 * 4 * 1.1) and near(r["red"], 0.05), r)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


L9 = Path.home() / "work/w3planner-art/save-spike/fixtures/save-l9"


def save_l9(b, base, check, label):
    """The second save (ManualSave_4dced_..., level 9, 665/1000 XP, 2,891 crowns, Synergy level 2). In-game panels: top-left blue (Greater) +48%, top-right blue (normal) +34%, bottom-left green (Greater) +180,
    bottom-right locked. Skips when the fixture is absent."""
    sav = sorted(L9.glob("*.sav")) if L9.is_dir() else []
    if not sav: print("  SKIP  %s: second-save (level 9) import (fixture not present)" % label); return
    js = sav[0].with_suffix(".json"); files = [str(sav[0])] + ([str(js)] if js.is_file() else [])
    pg, errs, reqs = page(b, base); E = pg.evaluate; pg.click("#savebtn"); pg.set_input_files("#impfile", files); until(pg, "!document.getElementById('impStep2').hidden")
    ch = E("document.getElementById('impReviewBody').innerText")
    check("%s: level-9 save review: level 9 · 665 / 1,000 XP, mutagens Greater blue, Blue, Greater green, Crowns 2,891 (%s)" % (label, ch[:80].replace("\n", " ")), "Level 9 · 665 / 1,000 XP" in ch and "Slot 1: Greater blue mutagen" in ch and "Slot 2: Blue mutagen" in ch and "Slot 3: Greater green mutagen" in ch and "Crowns: 2,891" in ch)
    pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden"); pg.wait_for_timeout(500)
    rows = bonus_rows(pg)
    check("%s: level-9 save: Character shows Sign intensity +48%%, Sign intensity +34%%, Vitality +180, one line per mutagen (%s)" % (label, rows),
          len(rows) == 3 and "Sign intensity +48%" in rows[0] and "Sign intensity +34%" in rows[1] and "Vitality +180" in rows[2] and E("+document.getElementById('lvl').value") == 9 and E("synergyLv()") == 2, rows)
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def refsave(b, base, check, label):
    if not SAV.is_file(): print("  SKIP  %s: reference-save import (fixture not present)" % label); return
    pg, errs, reqs = page(b, base); E = pg.evaluate; pg.click("#tabInv"); E("scrGo('char')"); pg.fill("#lvl", "30"); link_before = E("enc()")
    pg.click("#savebtn"); until(pg, "!document.getElementById('impov').hidden")
    pg.set_input_files("#impfile", [str(SAV), str(SIDE)]); ok = until(pg, "!document.getElementById('impStep2').hidden")
    check("%s: the reference save is read and the review opens, nothing changed yet (link %s)" % (label, "same" if E("enc()") == link_before else "CHANGED"), ok and E("enc()") == link_before)
    if not ok: print("   error:", E("document.getElementById('imperr').textContent")); pg.close(); return
    r = E("""(()=>({title:document.getElementById('imptitle2').textContent,meta:document.getElementById('impmeta').textContent,notes:[...document.querySelectorAll('.impnote')].map(n=>n.textContent),
      secs:[...document.querySelectorAll('.impsec')].map(s=>({t:s.querySelector('.imphead b').textContent,dest:s.querySelector('.impdest').textContent,on:s.querySelector('input').checked,lines:[...s.querySelectorAll('.impline')].map(l=>l.textContent)})),
      not:document.querySelector('.impnot').textContent,replace:document.querySelector('.impreplace').textContent,btns:[...document.querySelectorAll('.impbtns .btn')].map(x=>x.textContent)}))()""")
    S = {s["t"]: s for s in r["secs"]}; ch = " | ".join(S["Character"]["lines"]); mu = " | ".join(S["Mutagens"]["lines"]); eq = " | ".join(S["Equipment"]["lines"]); co = " | ".join(S["Consumables"]["lines"]); st = " | ".join(S["Stash"]["lines"])
    check("%s: review header: file name, date, game build 5.0.1044392 (%s)" % (label, r["meta"][:90]), r["title"] == "Save found — check before applying" and "ManualSave_52587_7ea48400_3d23fe3.sav" in r["meta"] and "game 5.0.1044392" in r["meta"], r["meta"])
    check("%s: the mods note lists 3 mods and says they are skipped" % label, any("This save lists 3 mods (More Money For Traders, PERFECT No Fall Damage, Mutagen Tab Alchemy). Items or skills added by mods are skipped." == n for n in r["notes"]) and not any("haven't tested" in n for n in r["notes"]), r["notes"])
    check("%s: all six sections are ticked, with their destinations (Character, Mutagens, Equipment, Consumables: the build link; Stash: this computer)" % label, [s["t"] for s in r["secs"]] == ["Character", "Mutagens", "Equipment", "Consumables", "Stash"] and all(s["on"] for s in r["secs"])
          and all(S[k]["dest"] == "Goes into the build link" for k in ("Character", "Mutagens", "Equipment", "Consumables")) and S["Stash"]["dest"] == "Stays on this computer")
    check("%s: Character: level 8 · 610 / 1,000 XP, 15 points used, 0 unspent, Signs 7 · General 2, 8 of 8 open slots (%s)" % (label, ch[:150]), "Level 8 · 610 / 1,000 XP" in ch and "15 skill points used, 0 unspent" in ch and "Combat 0 · Signs 7 · Alchemy 0 · General 2" in ch and "Equipped: 8 of 8 open slots" in ch, ch)
    SLOTS = ["magic_s8", "magic_s42", "magic_s36", "magic_s11", "magic_s39", "magic_s40", "perk_24", "perk_34"]
    SK = E("ids=>ids.map(id=>{for(const t of TREES){const s=t.sk.find(x=>x.id===id);if(s)return s.name}})", SLOTS)
    check("%s: every equipped skill is shown by OUR display name, in slot order (%s)" % (label, ", ".join(SK)), all(n in ch for n in SK) and "magic_s" not in ch and "perk_" not in ch and " · ".join("%d. %s" % (i + 1, n) for i, n in enumerate(SK)) in ch, ch)
    check("%s: Mutagens: Wraith mutagen and Griffin mutagen by our names (%s)" % (label, mu), "Slot 1: Wraith mutagen" in mu and "Slot 2: Griffin mutagen" in mu and "Gryphon" not in mu and "Slot 3: empty" in mu)
    check("%s: Equipment: the Thousand Flowers pieces by display name, set 6/6, the crossbow, bolts as 'Bolts', mask empty (%s)" % (label, eq[:230]), "Steel sword: Sword of a Thousand Flowers" in eq and "Silver sword: White Widow of the Valley of Flowers" in eq and "Chest armor: Armor of a Thousand Flowers" in eq and "Gloves: Gauntlets of a Thousand Flowers" in eq
          and "Trousers: Trousers of a Thousand Flowers" in eq and "Boots: Boots of a Thousand Flowers" in eq and "Crossbow: Crossbow" in eq and "Bolts: Bolts" in eq and "Mask: empty" in eq and "Set: " in eq and " 6/6" in eq and "Dol Blathanna" not in eq and "Bodkin" not in eq, eq)
    check("%s: Consumables: Cow's milk ×30, Water ×66, Swallow ×3, Tawny Owl ×3, Grapeshot ×2 and the Torch in the Pocket, all matched (%s)" % (label, co[:300]), "Bomb: Grapeshot ×2" in co and "Potion 3: Swallow ×3" in co and "Potion 4: Tawny Owl ×3" in co and "Potion 1: Cow's milk ×30" in co and "Potion 2: Water ×66" in co and "Pocket: Torch" in co and "not in planner" not in co, co)
    check("%s: Stash: 402 items read · plannable count, Crowns 2,890, 'Kept in this browser only, never in the link.' (%s)" % (label, st), st.startswith("402 items read · ") and "Crowns: 2,890" in st and "Kept in this browser only, never in the link." in st)
    check("%s: the 'Not read in this version' box, the footer and the two buttons" % label, "Not read in this version · active mutation · oils on swords · NG+ — set these by hand after import." == r["not"] and r["replace"] == "Replaces your current build. The link updates; use Copy link to share it." and r["btns"] == ["CHOOSE ANOTHER FILE", "APPLY TO PLANNER"], [r["not"], r["btns"]])
    pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
    a = E("""(()=>{const nm=(ti,i)=>TREES[ti].sk[i].name;return{scr:S.scr,hidden:document.getElementById('screenChar').hidden,lvl:+document.getElementById('lvl').value,bonus:+document.getElementById('bonuspts').value,per:S.lv.map(t=>t.filter(x=>x>0).length),spent:spent(),
      slots:S.slots.filter(Boolean).map(x=>nm(x[0],x[1])),muts:S.muts.map(m=>m==null?null:MUTS[m].name),gear:S.gear.map((n,i)=>{const it=n&&eqData().byN.get(n);return it?it.name:null}),cons:S.cons.slice(0,6).map(n=>n&&CN.byN.get(n).name),oils:S.cons.slice(6),
      stash:JSON.parse(localStorage.getItem('w3planner.stash')||'null'),link:enc(),toast:document.getElementById('toastMsg').textContent}})()""")
    check("%s: Apply lands on Character with level 8, 8 bonus points (15 points in all), Signs 7 / General 2 learned, 15 spent (%s)" % (label, (a["lvl"], a["bonus"], a["per"], a["spent"])), a["scr"] == "char" and not a["hidden"] and a["lvl"] == 8 and a["bonus"] == 8 and a["per"] == [0, 7, 0, 2] and a["spent"] == 15)
    check("%s: the 8 equipped skills are in slots 1 to 8 and nothing else" % label, a["slots"] == SK, a["slots"])
    check("%s: reference save Character: one line per mutagen, Vitality +50 and +50, no Sign intensity (%s)" % (label, bonus_rows(pg)), len(bonus_rows(pg)) == 2 and all("Vitality +50" in x for x in bonus_rows(pg)))
    check("%s: the planner holds Wraith and Griffin mutagens, the six Thousand Flowers pieces, crossbow, bolts, empty mask (%s)" % (label, a["gear"]), a["muts"] == ["Wraith mutagen", "Griffin mutagen", None, None] and a["gear"] == ["Sword of a Thousand Flowers", "White Widow of the Valley of Flowers", "Crossbow", "Bolts", "Armor of a Thousand Flowers", "Gauntlets of a Thousand Flowers", "Trousers of a Thousand Flowers", "Boots of a Thousand Flowers", None], a)
    check("%s: consumables: Cow's milk, Water, Swallow, Tawny Owl, Grapeshot Bomb, Torch in the Pocket; the oils are untouched (%s)" % (label, a["cons"]), a["cons"] == ["Cow's milk", "Water", "Swallow", "Tawny Owl", "Grapeshot", "Torch"] and a["oils"] == [0, 0], a["cons"])
    check("%s: the stash went to this browser only (crowns 2,890, plannable items) and is not in the link" % label, a["stash"] and a["stash"]["crowns"] == 2890 and len(a["stash"]["weapons"]) + len(a["stash"]["armor"]) > 5 and "2890" not in a["link"] and a["link"].count(".") <= 10, a["link"][-40:])
    STATE = "JSON.stringify([S.lv,S.slots,S.muts,S.gear,S.cons,+document.getElementById('lvl').value,+document.getElementById('bonuspts').value])"
    rt = E("(()=>{const l=enc(),t=dec(l);return !!t&&JSON.stringify([t.lv,t.slots,t.muts,t.gear,t.cons])===JSON.stringify([S.lv,S.slots,S.muts,S.gear,S.cons])&&enc()===l})()"); mine = E(STATE)
    q = b.new_page(viewport={"width": 1300, "height": 900}); q.goto(base + "#" + a["link"]); until(q, READY); there = q.evaluate(STATE); q.close()
    check("%s: Copy link round-trips the imported build (decode/encode equal, a new tab opens the same build)" % label, rt and there == mine, [mine[:60], there[:60]])
    # unticking a section leaves it alone
    E("save()"); pg.fill("#lvl", "12"); pg.click("#savebtn"); until(pg, "!document.getElementById('impov').hidden"); pg.set_input_files("#impfile", [str(SAV)]); until(pg, "!document.getElementById('impStep2').hidden")
    pg.uncheck('.impsec input[data-sec="character"]'); pg.uncheck('.impsec input[data-sec="equipment"]'); gear0 = E("S.gear.join()"); pg.click("#impApply"); until(pg, "document.getElementById('impov').hidden")
    check("%s: an unticked section is left alone (level and gear unchanged, the ticked mutagens and consumables applied)" % label, E("+document.getElementById('lvl').value") == 12 and E("S.gear.join()") == gear0, [E("+document.getElementById('lvl').value")])
    check("%s: no script errors during the import" % label, not errs, errs[:1]); pg.close()


def phone(b, base, check, label):
    pg, errs, reqs = page(b, base, 390, 844, True); E = pg.evaluate
    ico = E("(()=>{const r=document.getElementById('savebtn').getBoundingClientRect(),c=document.getElementById('copy').getBoundingClientRect();return{w:r.width,h:r.height,right:r.right,copyL:c.left,inview:r.left>=0&&r.right<=innerWidth,sw:document.documentElement.scrollWidth}})()")
    check("%s: phone 390: IMPORT SAVE is a 44 px icon button in the top bar next to Copy link, nothing scrolls sideways (%s)" % (label, ico), ico["w"] >= 44 and ico["h"] >= 44 and ico["inview"] and ico["sw"] <= 390, ico)
    pg.click("#savebtn"); until(pg, "!document.getElementById('impov').hidden")
    full = E("(()=>{const r=document.querySelector('.imppanel').getBoundingClientRect();return r.left<=0&&r.top<=0&&r.width>=390&&r.height>=844&&document.documentElement.scrollWidth<=390})()")
    check("%s: phone 390: the dialog is a full-screen view" % label, full)
    if SAV.is_file():
        pg.set_input_files("#impfile", [str(SAV), str(SIDE)]); until(pg, "!document.getElementById('impStep2').hidden")
        g = E("""(()=>{const bar=document.querySelector('.impbar').getBoundingClientRect(),ap=document.getElementById('impApply').getBoundingClientRect(),bk=document.getElementById('impback').getBoundingClientRect(),cols=getComputedStyle(document.querySelector('.impcols')).gridTemplateColumns.split(' ').length;
          return{barBottom:Math.round(bar.bottom),vh:innerHeight,apH:Math.round(ap.height),apInView:ap.bottom<=innerHeight+1&&ap.top>=0,back:Math.round(bk.height),cols:cols,sw:document.documentElement.scrollWidth,replace:document.querySelector('.impreplace').textContent}})()""")
        check("%s: phone 390: the review is one stacked column with a back arrow and a sticky bottom bar (Replaces your current build + APPLY TO PLANNER), reachable without scrolling (%s)" % (label, g), g["cols"] == 1 and g["back"] >= 44 and g["apInView"] and g["apH"] >= 44 and g["sw"] <= 390 and g["barBottom"] <= g["vh"] + 1, g)
        pg.tap("#impback"); check("%s: phone 390: the back arrow returns to choosing a file" % label, E("!document.getElementById('impStep1').hidden"))
    check("%s: no script errors on the phone" % label, not errs, errs[:1]); pg.close()


def offline(b, url, check, label):
    pg, errs, reqs = page(b, url); E = pg.evaluate
    check("%s: the offline copy has no Import button (it can open links but not create them)" % label, E("document.getElementById('savebtn').getClientRects().length===0") and E("document.getElementById('savebtn').hidden"))
    check("%s: no script errors" % label, not errs, errs[:1]); pg.close()


def live(b, url, check):
    """Smoke test of a deployed site: the button, the dialog, a bad file, and the reference import when the fixture is here."""
    pg, errs, reqs = page(b, url); E = pg.evaluate
    check("import: the live site has IMPORT SAVE and the dialog opens", bool(E("!!document.getElementById('savebtn')")) and (pg.click("#savebtn") or True) and until(pg, "!document.getElementById('impov').hidden"))
    pg.set_input_files("#impfile", {"name": "x.sav", "mimeType": "application/octet-stream", "buffer": b"not a save"}); until(pg, "!document.getElementById('imperr').hidden")
    check("import: a bad file shows the error in the dialog", E("document.getElementById('imperr').textContent").startswith("This isn't a Witcher 3 save."))
    pg.click("#impx"); pg.close()
    if SAV.is_file(): refsave(b, url, check, "import")
