"""v36: runes and glyphs in sockets, in a real browser.

data(check)                        data/socket_ids.json: 61 entries (32 runes, 29 glyphs), numbers 1..61, append-only against main, no game text beyond names and stat labels
run(b, base, check, label)         the discs, the picker (kind filter, tabs, search, Remove, keyboard), the item card, capacity per ruleset, NG / NG+ and item swaps, the r1 segment (round trip, order,
                                   byte-identical old links, hostile links, drops on decode), Player Stats, a phone
imported(b, base, check, label)    sockets-1 (never committed; SKIPPED when absent): silver sword = Dazhbog runestone, chest = lesser Glyph of Igni; the other saves import with no sockets
"""
import json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXD = Path.home() / "work/w3planner-art/save-spike/fixtures"
READY = "typeof S!=='undefined'&&S&&document.getElementById('slots').children.length>0"
A64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def until(pg, js, ms=10000):
    for _ in range(ms // 50):
        if pg.evaluate(js): return True
        pg.wait_for_timeout(50)
    return False


def page(b, url, w=1500, h=1000, mobile=False, scr="inv"):
    pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e).split("\n")[0][:120])); pg.goto(url); until(pg, READY)
    pg.evaluate("scrGo('%s')" % scr); until(pg, "!!eqData()&&!!CN.data&&!!SK.data"); pg.wait_for_timeout(250)
    return pg, errs


def data(check):
    d = json.loads((ROOT / "data/socket_ids.json").read_text()); it = d["items"]; ns = [i["n"] for i in it]
    kinds = {k: sum(1 for i in it if i["kind"] == k) for k in ("rune", "glyph")}
    check("sockets: data/socket_ids.json holds 61 entries: 32 runes and 29 glyphs (%s)" % kinds, len(it) == 61 and kinds == {"rune": 32, "glyph": 29}, kinds)
    check("sockets: numbers are 1 to 61, each once; ids are unique; 'Rune ' ids are runes and 'Glyph ' ids are glyphs", sorted(ns) == list(range(1, 62)) and len({i["id"] for i in it}) == 61
          and all((i["id"].startswith("Rune ") and i["kind"] == "rune") or (i["id"].startswith("Glyph ") and i["kind"] == "glyph") for i in it))
    check("sockets: each entry has a name, a tier 1 to 3 and effect values ('fx' for the first playthrough, 'fxp' only where New Game Plus differs: none does today)",
          all(i["name"] and i["tier"] in (1, 2, 3) and isinstance(i["fx"], list) for i in it) and not any("fxp" in i for i in it) and not any("only" in i for i in it))
    # no game text beyond names and stat labels: nothing long in the file apart from the one generator note
    long = [i["id"] for i in it if len(i["name"]) > 40]; labels = d["labels"]
    check("sockets: no game text beyond names and the stat labels (every name under 40 characters, %d labels, none over 40)" % len(labels), not long and all(len(v) < 40 for v in labels.values()), long)
    # append-only against main: the numbers of main's file are the same here
    ref = next((r for r in ("origin/main", "main") if subprocess.run(["git", "rev-parse", "--verify", "-q", r], cwd=ROOT, capture_output=True).returncode == 0), None)
    old = subprocess.run(["git", "show", "%s:data/socket_ids.json" % ref], cwd=ROOT, capture_output=True, text=True) if ref else None
    if old is None or old.returncode != 0: check("sockets: registry append-only against main (main has no socket registry yet: nothing to compare with)", True, "skipped")
    else:
        was = {i["id"]: i["n"] for i in json.loads(old.stdout)["items"]}; now = {i["id"]: i["n"] for i in it}
        check("sockets: registry is append-only: every id on main keeps its number (%d ids)" % len(was), all(now.get(k) == v for k, v in was.items()), [k for k, v in was.items() if now.get(k) != v][:5])


def run(b, base, check, label):
    pg, errs = page(b, base); E = pg.evaluate
    R = E("""(()=>{const k=SK.data.items;return{n:k.length,runes:k.filter(r=>r.kind==='rune').length,glyphs:k.filter(r=>r.kind==='glyph').length,
      swordFits:k.filter(r=>skFits('silver',r)).length,steelFits:k.filter(r=>skFits('steel',r)).length,armFits:['chest','gloves','trousers','boots'].map(s=>k.filter(r=>skFits(s,r)).length),
      none:[skFits('crossbow',k[0]),skFits('mask',k[40]),skFits('bolts',k[0]),skFits('silver',null)]}})()""")
    check("%s: the slot rule: every sword takes the 32 runes and no glyph, every armour piece the 29 glyphs and no rune, the crossbow, bolts and mask take nothing (%s)" % (label, R),
          R["n"] == 61 and R["swordFits"] == 32 and R["steelFits"] == 32 and R["armFits"] == [29, 29, 29, 29] and R["none"] == [False, False, False, False], R)
    # ---- capacity per ruleset ----
    E("eqLoad('ng_plus')"); until(pg, "!!EQ.rs.ng_plus")
    cap = E("""(()=>{const f=(rs,id)=>skCap(EQ.rs[rs].byId.get(id));return{gs:[f('ng','Gryphon School silver sword'),f('ng_plus','Gryphon School silver sword')],ga:[f('ng','Gryphon Armor'),f('ng_plus','Gryphon Armor')],
      lynx:[f('ng','Lynx School steel sword 4'),f('ng_plus','Lynx School steel sword 4'),f('ng','Lynx Gloves 5'),f('ng_plus','Lynx Gloves 5')],wolf4:f('ng_plus','NGP Wolf Pants 4'),
      xb:skCap(EQ.rs.ng.byId.get('Crossbow')),mask:skCap(EQ.rs.ng.bySlot.mask[0]),bolts:skCap(EQ.rs.ng.bySlot.bolts[0]),maxAll:Math.max(...['ng','ng_plus'].flatMap(r=>EQ.rs[r].items.map(skCap)))}})()""")
    check("%s: capacity is the item's enhancement_slots of the chosen ruleset: Griffin sword and armor 1 in the first playthrough, 3 in New Game Plus; Lynx sword 3 and gloves 2 in both; Wolven trousers 4; crossbow, bolts and mask 0 (%s)" % (label, cap),
          cap["gs"] == [1, 3] and cap["ga"] == [1, 3] and cap["lynx"] == [3, 3, 2, 2] and cap["wolf4"] == 4 and cap["xb"] == 0 and cap["mask"] == 0 and cap["bolts"] == 0 and cap["maxAll"] == 4, cap)
    # ---- build: Griffin sword and armor, one rune, one glyph; the discs sit in the top-left corner of the tile ----
    SETUP = """(rs=>{document.getElementById('lvl').value=100;S.rs=rs;S.gear.fill(0);S.sock.fill(0);const d=eqData();S.gear[1]=d.byId.get('Gryphon School silver sword').n;S.gear[4]=d.byId.get('Gryphon Armor').n;S.gear[0]=d.byId.get('Lynx School steel sword 4').n;
      S.sock[4]=SK.byId.get('Rune dazhbog').n;S.sock[8]=SK.byId.get('Glyph igni lesser').n;save();eqRender(true)})"""
    E(SETUP, "ng"); pg.wait_for_timeout(200)
    geo = E("""(()=>{const g=u=>{const t=document.querySelector('.eqslot[data-i="'+u+'"] .eqtile').getBoundingClientRect(),ss=[...document.querySelectorAll('.eqslot[data-i="'+u+'"] .sock')].map(x=>x.getBoundingClientRect());
        return{n:ss.length,cls:[...document.querySelectorAll('.eqslot[data-i="'+u+'"] .sock')].map(x=>x.className.replace('sock ','')),
          topleft:ss.length>0&&ss.every(r=>r.left>=t.left-1&&r.top>=t.top-1&&r.right<=t.left+t.width*0.6&&r.bottom<=t.top+t.height*0.3),under:ss.some(r=>r.top>t.bottom)}};
      return{steel:g(0),silver:g(1),chest:g(4),gloves:g(5),crossbow:g(2),empty:g(7)}})()""")
    check("%s: discs sit in the top-left corner of each weapon and armour tile: filled orange = rune, filled blue = glyph, hollow = empty; the count is the item's capacity (steel 3 hollow, silver 1 rune, chest 1 glyph) (%s)" % (label, json.dumps(geo)[:200]),
          geo["steel"]["n"] == 3 and geo["steel"]["cls"] == ["empty"] * 3 and geo["silver"]["cls"] == ["rune"] and geo["chest"]["cls"] == ["glyph"] and all(geo[k]["topleft"] and not geo[k]["under"] for k in ("steel", "silver", "chest")), geo)
    check("%s: no discs on an empty slot, on the crossbow, bolts or mask (gloves slot empty: %d, crossbow: %d)" % (label, geo["gloves"]["n"], geo["crossbow"]["n"]), geo["gloves"]["n"] == 0 and geo["crossbow"]["n"] == 0 and geo["empty"]["n"] == 0, geo)
    col = E("""(()=>{const c=s=>getComputedStyle(document.querySelector(s)).backgroundColor;return{rune:c('.eqslot[data-i="1"] .sock.rune'),glyph:c('.eqslot[data-i="4"] .sock.glyph'),empty:c('.eqslot[data-i="0"] .sock.empty')}})()""")
    check("%s: filled rune disc is orange, filled glyph disc is blue, an empty one is hollow-dark (%s)" % (label, col), col["rune"] == "rgb(224, 138, 42)" and col["glyph"] == "rgb(79, 155, 224)" and col["empty"] != col["rune"] and col["empty"] != col["glyph"], col)
    # ---- the item card ----
    card = E("""(()=>{const c=[...document.querySelectorAll('.eqitem')].map(x=>({h:x.querySelector('h4').textContent,sock:(x.querySelector('.eqsocks')||{textContent:''}).textContent.replace(/\\s+/g,' ').trim(),fx:[...x.querySelectorAll('.sockfx')].map(y=>[...y.children].map(c=>c.textContent).join(' ')),nb:x.querySelectorAll('.eqsocks .sock').length,
        green:[...x.querySelectorAll('.sockfx')].map(y=>getComputedStyle(y).color)}));return c})()""")
    byh = {c["h"]: c for c in card}
    sw, ar = byh.get("Griffin silver sword"), byh.get("Griffin armor")
    lynx = byh.get("Grandmaster Feline steel sword")
    check("%s: the item card says 'Sockets 1 of 1' and shows each rune's or glyph's bonus as a green line under the base stats, with its name in brackets; an empty-socket sword says 'Sockets 0 of 3' (%s)" % (label, [sw and sw["sock"], sw and sw["fx"], ar and ar["fx"]]),
          bool(sw and ar and lynx) and sw["sock"].startswith("Sockets 1 of 1") and sw["fx"] == ["Chance to cause burning +3 % [Dazhbog runestone]"] and ar["fx"] == ["Igni Sign intensity +2 % [Lesser Glyph of Igni]"] and ar["sock"].startswith("Sockets 1 of 1")
          and all(c == "rgb(127, 193, 107)" for c in sw["green"] + ar["green"]) and lynx["sock"].startswith("Sockets 0 of 3"), card)
    # ---- the picker: opens from a disc or the card's row, filters by kind, tabs, search, current marked, Remove ----
    pg.click('.eqslot[data-i="1"] .sock'); until(pg, "!!document.querySelector('#skov .skmodal')")
    P = E("""(()=>{const rows=[...document.querySelectorAll('#skov .skrow')];return{title:document.getElementById('sktitle').textContent,kinds:[...new Set(rows.map(r=>r.classList.contains('rune')?'rune':'glyph'))],
      tabs:[...document.querySelectorAll('#skov .sktab')].map(t=>t.textContent.replace(/\\s+/g,' ').trim()),cur:rows.filter(r=>r.classList.contains('cur')).map(r=>[...r.querySelector('.skname').childNodes].map(c=>c.textContent).join(' ')),count:document.getElementById('skcount').textContent,
      first:rows[0]&&rows[0].textContent,focus:document.activeElement.id,remove:document.getElementById('skremove').disabled,modal:document.querySelector('#skov [role=dialog]').getAttribute('aria-modal')}})()""")
    check("%s: clicking a disc opens the rune picker for that socket: tabs Lesser / Normal / Greater / Other with counts, the search box focused, the current rune marked (opens on its tab), Remove enabled, runes only (%s)" % (label, P),
          P["title"] == "Rune picker · Silver sword" and P["kinds"] == ["rune"] and P["tabs"] == ["Lesser 10", "Normal 10", "Greater 10", "Other 2"] and P["cur"] == ["Dazhbog runestone in this socket"] and P["focus"] == "skq" and not P["remove"] and P["modal"] == "true", P)
    tot = {}
    for t in ("lesser", "normal", "greater", "other"):
        pg.click('#sktabs [data-t="%s"]' % t); tot[t] = E("[...document.querySelectorAll('#skov .skrow')].map(r=>r.querySelector('.skname').firstChild.textContent)")
    check("%s: the weapon picker lists 32 runes over its four tabs (10 + 10 + 10 + 2: Pyerog and Tvarog have no stat bonus and are under Other); every row has an icon (or lettered disc), a name and its effect (%s)" % (label, [len(v) for v in tot.values()]),
          [len(v) for v in tot.values()] == [10, 10, 10, 2] and sorted(tot["other"]) == ["Pyerog runestone", "Tvarog runestone"], tot)
    pg.click('#sktabs [data-t="normal"]'); pg.fill("#skq", "bleed")
    S1 = E("[...document.querySelectorAll('#skov .skrow')].map(r=>r.textContent)"); pg.fill("#skq", "zzz"); S2 = E("document.querySelector('#skov .skempty')&&document.querySelector('#skov .skempty').textContent"); pg.fill("#skq", "")
    check("%s: search finds by name or effect (bleed: %s) and says so when nothing matches (%s)" % (label, S1, S2), len(S1) == 1 and "Devana" in S1[0] and S2 and "Nothing matches" in S2, [S1, S2])
    rows = E("[...document.querySelectorAll('#skov .skrow')].map(r=>({fx:r.querySelector('.skfx').textContent,ic:!!r.querySelector('.skic'),img:!!r.querySelector('img.skic')}))")
    check("%s: every row shows an icon and an effect" % label, all(r["ic"] and r["fx"] for r in rows), rows[:3])
    pg.click('#skov .skrow[data-n="%d"]' % E("SK.byId.get('Rune perun').n")); pg.wait_for_timeout(150)
    after = E("[S.sock[4],SK.byN.get(S.sock[4]).name,document.getElementById('skov').hidden,document.activeElement.className,document.getElementById('toastMsg').textContent,location.hash.includes('.r1')]")
    check("%s: choosing a rune sockets it, closes the picker, puts focus back on the disc, says so, and the link has r1 (%s)" % (label, after), after[1] == "Perun runestone" and after[2] and "sock" in after[3] and "Perun runestone socketed" in after[4] and after[5], after)
    pg.click('.eqslot[data-i="1"] .sock'); until(pg, "!!document.querySelector('#skov .skmodal')"); pg.click("#skremove"); pg.wait_for_timeout(150)
    rm = E("[S.sock[4],document.getElementById('skov').hidden,document.getElementById('toastMsg').textContent]")
    check("%s: Remove empties the socket and closes the picker (%s)" % (label, rm), rm[0] == 0 and rm[1] and "removed" in rm[2], rm)
    pg.click('.eqslot[data-i="4"] .sock'); until(pg, "!!document.querySelector('#skov .skmodal')")
    G = E("""(()=>{const rows=[...document.querySelectorAll('#skov .skrow')];const tabs=[...document.querySelectorAll('#skov .sktab')].map(t=>t.textContent.replace(/\\s+/g,' ').trim());return{title:document.getElementById('sktitle').textContent,kinds:[...new Set(rows.map(r=>r.classList.contains('rune')?'rune':'glyph'))],tabs}})()""")
    check("%s: the armor picker lists glyphs only: 29 over Lesser 9 / Normal 9 / Greater 9 / Other 2 (the two Glyphs of Infusion have no stat bonus) (%s)" % (label, G), G["title"] == "Glyph picker · Chest armor" and G["kinds"] == ["glyph"] and G["tabs"] == ["Lesser 9", "Normal 9", "Greater 9", "Other 2"], G)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(100)
    esc = E("[document.getElementById('skov').hidden,document.activeElement.className,document.activeElement.dataset.u]")
    check("%s: Escape closes the picker and returns focus to the disc that opened it (%s)" % (label, esc), esc[0] and "sock" in esc[1] and esc[2] == "4", esc)
    pg.click('.eqitem:has(h4:text("Griffin silver sword")) .sockrow .sock'); until(pg, "!!document.querySelector('#skov .skmodal')")
    check("%s: the item card's socket row opens the same picker" % label, E("document.getElementById('sktitle').textContent") == "Rune picker · Silver sword")
    pg.keyboard.press("Escape")
    # ---- Tab stays inside the picker; the key C does not open Player Stats behind it ----
    pg.click('.eqslot[data-i="1"] .sock'); until(pg, "!!document.querySelector('#skov .skmodal')")
    for _ in range(30): pg.keyboard.press("Tab")
    inside = E("document.getElementById('skov').contains(document.activeElement)"); pg.focus('#skov .skrow'); pg.keyboard.press("c"); pg.wait_for_timeout(100)
    check("%s: Tab stays inside the open picker, and the key C does not open Player Stats behind it" % label, inside and E("!PS.open"), inside)
    pg.keyboard.press("Escape")
    # ---- NG / NG+ and item swaps: keep what fits, list what was removed ----
    E(SETUP, "ng_plus"); E("""(()=>{S.sock[4]=SK.byId.get('Rune dazhbog').n;S.sock[5]=SK.byId.get('Rune veles greater').n;S.sock[6]=SK.byId.get('Rune zoria lesser').n;S.sock[8]=SK.byId.get('Glyph igni lesser').n;S.sock[9]=SK.byId.get('Glyph quen').n;save();eqRender(true)})()""")
    pg.wait_for_timeout(200)
    caps = E("[...document.querySelectorAll('.eqslot[data-i=\"1\"] .sock')].length+','+[...document.querySelectorAll('.eqslot[data-i=\"4\"] .sock')].length")
    pg.click('#topbar [data-rs="ng"]'); pg.wait_for_timeout(1200)
    sw = E("[S.rs,S.sock.slice(4,8).join(),S.sock.slice(8,12).join(),document.getElementById('toastMsg').textContent]")
    check("%s: NG+ to NG: the Griffin sword (3 sockets, now 1) keeps its first rune and loses the other two, the armor keeps its glyph; the notice lists exactly what was removed (%s)" % (label, sw),
          caps == "3,3" and sw[0] == "ng" and sw[1] == "%d,0,0,0" % E("SK.byId.get('Rune dazhbog').n") and sw[2] == "%d,0,0,0" % E("SK.byId.get('Glyph igni lesser').n") and "Removed from sockets" in sw[3] and "Greater Veles runestone" in sw[3] and "Lesser Zoria runestone" in sw[3] and "Dazhbog" not in sw[3] and "Quen" in sw[3], [caps, sw])
    pg.click('#topbar [data-rs="ng_plus"]'); pg.wait_for_timeout(800); back = E("S.sock.slice(4,8).join()")
    check("%s: switching back to NG+ does not bring removed sockets back (the build is what the link says)" % label, back == "%d,0,0,0" % E("SK.byId.get('Rune dazhbog').n"), back)
    # an item swap: Lynx steel sword (3) with three runes -> Griffin steel sword in NG (1)
    sw2 = E("""(()=>{S.rs='ng';const d=eqData();S.gear.fill(0);S.sock.fill(0);S.gear[0]=d.byId.get('Lynx School steel sword 4').n;S.sock[0]=SK.byId.get('Rune perun').n;S.sock[1]=SK.byId.get('Rune morana').n;S.sock[2]=SK.byId.get('Rune triglav').n;save();eqRender(true);
        const g=d.byId.get('Gryphon School steel sword');return !!g})()""")
    pg.click('.eqslot[data-i="0"] .eqtile'); until(pg, "!!EQ.pick"); pg.fill("#pkq", "griffin"); pg.wait_for_timeout(200)
    ids = E("[...document.querySelectorAll('#pkgrid .pktile')].map(b=>b.dataset.id)")
    pick = next((i for i in ids if i.startswith("Gryphon School steel sword")), None)
    if pick:
        pg.click('#pkgrid [data-id="%s"]' % pick); pg.click("#pkequip"); pg.wait_for_timeout(250)
        sw3 = E("[S.sock.slice(0,4).join(),document.getElementById('toastMsg').textContent]")
        check("%s: equipping a Griffin sword (1 socket) in place of a Lynx sword with 3 runes keeps the first rune, removes the other two and says which (%s)" % (label, sw3),
              sw3[0] == "%d,0,0,0" % E("SK.byId.get('Rune perun').n") and "Removed from sockets" in sw3[1] and "Morana" in sw3[1] and "Triglav" in sw3[1] and "Perun" not in sw3[1].split("Removed from sockets")[1], sw3)
    else: check("%s: item swap (no Griffin steel sword found)" % label, False, ids[:5])
    E("(()=>{S.sock.fill(0);S.gear.fill(0);S.rs='ng';save()})()")
    # unequipping an item removes its sockets
    E("""(()=>{const d=eqData();S.gear[1]=d.byId.get('Gryphon School silver sword').n;S.sock[4]=SK.byId.get('Rune dazhbog').n;save();eqRender(true)})()"""); pg.wait_for_timeout(150)
    pg.click('.eqslot[data-i="1"] .eqx'); pg.wait_for_timeout(200)
    un = E("[S.sock[4],document.getElementById('toastMsg').textContent]")
    check("%s: unequipping a sword removes its runes and says so (%s)" % (label, un), un[0] == 0 and "Removed from sockets" in un[1] and "Dazhbog" in un[1], un)
    # ---- Player Stats: the model's numbers with and without the sockets ----
    E(SETUP, "ng"); E("(()=>{document.getElementById('lvl').value=40;S.gear[0]=0;S.sock[0]=0;S.sock[1]=0;S.sock[2]=0;save();eqRender(true)})()")   # level 40: inside the stats table, above the Griffin items's level 11
    ps = E("""(()=>{const a=psCalc();const keep=S.sock.slice();S.sock.fill(0);const b=psCalc();S.sock=keep;const diff=[];
      Object.keys(a.det).forEach(k=>a.det[k].forEach((blk,i)=>blk.forEach((l,j)=>{const o=b.det[k][i][j];if(l[0]!==o[0]||l[2]!==o[2])diff.push([k,o[0],l[0],l[1],l[2]])})));
      Object.keys(a.rows).forEach(k=>{if(JSON.stringify(a.rows[k])!==JSON.stringify(b.rows[k]))diff.push(['row '+k,b.rows[k].v,a.rows[k].v])});return diff})()""")
    names = {d[0] + ":" + str(d[3]) for d in ps if len(d) > 3}
    check("%s: Player Stats adds the sockets with the source in brackets: Dazhbog runestone gives the silver sword +3 %% Chance to cause burning (0 %% to 3 %%), the lesser Glyph of Igni raises the Igni numbers (%s)" % (label, ps),
          any(d[0] == "silver" and d[1] == "0 %" and d[2] == "3 %" and d[4] == "[Dazhbog runestone]" for d in ps) and any(d[0] == "sign" and d[4] == "[Lesser Glyph of Igni]" for d in ps) and any(d[0] == "sign" and d[3] == "Fire damage" for d in ps)
          and not any(d[0] in ("steel", "armor", "crossbow", "stamina", "toxicity") for d in ps), ps)
    # the Igni number follows the game's formula: Fire damage = FireDamage x (1 + (Igni power - 1)); +0.02 power gives +0.02 x the base: checked against the model without the glyph
    ig = E("""(()=>{const f=()=>{const R=psCalc();return R.det.sign[3][0][0]};const w=+f();const keep=S.sock.slice();S.sock[8]=0;const wo=+f();S.sock=keep;return[w,wo]})()""")
    check("%s: the Igni Fire damage is higher with the lesser Glyph of Igni (%s without, %s with)" % (label, ig[1], ig[0]), ig[0] > ig[1], ig)
    E("(()=>{S.sock.fill(0);S.gear[5]=eqData().byId.get('Gryphon Gloves 5').n;save()})()")
    mend = E("""(()=>{S.sock[12]=SK.byId.get('Glyph mending').n;const R=psCalc();const out=R.det.vitality[0].map(x=>[x[0],x[2]]);const W0=psCalc().det.armor[0][4][0];S.sock[12]=SK.byId.get('Glyph warding').n;const W=psCalc().det.armor[0][4];S.sock[12]=0;return{out,W,W0}})()""")
    check("%s: a Glyph of Mending changes a regeneration the screen does not model, so those two lines show — (not computed) with the glyph named; a Glyph of Warding adds to the elemental resistance line (%s)" % (label, mend),
          all(x[0] is None and x[1] == "[Glyph of Mending]" for x in mend["out"]) and mend["W"][2] == "[Glyph of Warding]" and int(mend["W"][0][:-2]) - int(mend["W0"][:-2]) == 2, mend)
    # ---- r1: write, read, order, absence ----
    link = E("""(()=>{const d=eqData();S.rs='ng_plus';S.gear.fill(0);S.sock.fill(0);S.gear[0]=d.byId.get('Lynx School steel sword 4').n;S.gear[4]=d.byId.get('Lynx Armor 4').n;S.cons[0]=CN.byId.get('Swallow 3').n;S.scr='inv';
      S.sock[0]=SK.byId.get('Rune perun').n;S.sock[2]=SK.byId.get('Rune zoria lesser').n;S.sock[8]=SK.byId.get('Glyph igni lesser').n;S.sock[9]=SK.byId.get('Glyph yrden lesser').n;S.sock[10]=SK.byId.get('Glyph quen').n;return enc()})()""")
    seg = link.split(".")[8:]
    t = E("(c=>{const s=dec(c);return s&&s.sock.join()})", link); want = E("S.sock.join()")
    check("%s: r1 round trip: one r1 segment of 50 characters (r1 + 6 slots x 4 sockets x 2), the same 24 numbers come back; order g1, c1, r1, s1 (%s)" % (label, [x[:2] for x in seg]),
          [x[:2] for x in seg] == ["g1", "c1", "r1", "s1"] and len(seg[2]) == 50 and t == want, [seg, t, want])
    plain = E("(()=>{S.sock.fill(0);return enc()})()")
    check("%s: nothing socketed: no r1 segment" % label, "r1" not in plain and [x[:2] for x in plain.split(".")[8:]] == ["g1", "c1", "s1"], plain[-40:])
    import linkcheck
    fixtures, _ = linkcheck.load_fixtures(); same, diff = 0, []
    for fx in fixtures:
        if fx["kind"] == "legacy" or len(fx["code"].split(".")[2]) != 32 or fx["version"] >= "v36": continue
        r = E("(c)=>{const s=dec(c);if(!s)return null;S=s;enforceLocks();return enc()}", fx["code"])
        if r == fx["code"] and ".r1" not in r: same += 1
        else: diff.append((fx["name"][:30], fx["code"][-30:], (r or "")[-30:]))
    check("%s: old links stay byte-identical: every link made before v36 re-encodes to itself, with no r1 (%d links)" % (label, same), not diff and same > 60, diff[:3])
    # ---- hostile and edge links ----
    base_code = E("(()=>{S=blank();return enc()})()")
    g = lambda ng: E("(rs=>{const d=eqData();S.rs=rs;S.gear.fill(0);S.gear[1]=d.byId.get('Gryphon School silver sword').n;S.gear[4]=d.byId.get('Gryphon Armor').n;S.gear[0]=d.byId.get('Lynx School steel sword 4').n;S.gear[7]=d.byId.get('Lynx Boots 5').n;return enc()})", ng)
    def n(i): return E("SK.byId.get('%s').n" % i)
    def seg(vals): return "r1" + "".join(A64[v >> 6] + A64[v & 63] for v in vals)
    def link_with(ng, vals): return g(ng) + "." + seg(vals + [0] * (24 - len(vals)))
    OK = link_with("ng", [0, 0, 0, 0, n("Rune dazhbog"), 0, 0, 0])
    bad = {"47": OK[:-3], "49": OK + "A", "twice": OK + "." + seg([0] * 24), "chars": OK[:-1] + "!", "short tag": OK.replace(".r1", ".r1") + ".r1AA"}
    res = {k: E("(c)=>dec(c)", v) for k, v in bad.items()}
    check("%s: a malformed or repeated r1 is rejected as a whole link (%s)" % (label, {k: v is None for k, v in res.items()}), all(v is None for v in res.values()), list(res))
    tol = E("(c)=>{const s=dec(c+'.z9ABC');return !!s&&s.sock.every(x=>x===0)}", base_code)
    check("%s: a link with no r1 opens with every socket empty; an unknown well-formed segment next to r1 is ignored" % label, tol and E("(c)=>dec(c+'.z9ABC').sock.every(x=>x===0)", base_code))
    # what decode drops once the item data is known: past capacity, a glyph in a weapon, a rune in armour, unknown number, capacity of the other ruleset
    cases = {"rune in armour": ("ng", [0, 0, 0, 0, 0, 0, 0, 0, n("Rune dazhbog")]), "glyph in a sword": ("ng", [n("Glyph igni")]),
             "past capacity": ("ng", [0, 0, 0, 0, n("Rune dazhbog"), n("Rune perun")]), "unknown number": ("ng", [0, 0, 0, 0, 4095]), "number 62": ("ng", [0, 0, 0, 0, 62]),
             "ng+ capacity in ng": ("ng", [0, 0, 0, 0, n("Rune dazhbog"), n("Rune perun"), n("Rune morana")]), "empty slot": ("ng", [0] * 12 + [n("Glyph igni")]), "valid": ("ng", [0, 0, 0, 0, n("Rune dazhbog")])}
    out = {}
    for k, (rs, vals) in cases.items():
        q = b.new_page(viewport={"width": 1400, "height": 950}); q.goto(base + "#" + link_with(rs, vals)); until(q, READY); until(q, "typeof SK!=='undefined'&&!!SK.data&&!!eqData()"); q.wait_for_timeout(300)
        out[k] = q.evaluate("[S.sock.join(),document.getElementById('toastMsg').textContent,location.hash.slice(1).includes('.r1')]"); q.close()
    z = lambda *idx: ",".join(str(i) for i in idx)
    keep = n("Rune dazhbog")
    check("%s: on decode a rune in armour, a glyph in a sword, a number past the item's capacity, an unknown number (4095, 62) and sockets on an empty slot are dropped, with the dropped-from-link notice naming them; what fits stays (%s)" % (label, {k: v[0] for k, v in out.items()}),
          out["valid"][0].split(",")[4] == str(keep) and "Removed from sockets" not in out["valid"][1]
          and all(set(out[k][0].split(",")) == {"0"} and "Removed from sockets" in out[k][1] for k in ("rune in armour", "glyph in a sword", "unknown number", "number 62", "empty slot"))
          and out["past capacity"][0].split(",")[4:6] == [str(keep), "0"] and "Perun" in out["past capacity"][1] and out["ng+ capacity in ng"][0].split(",")[4:7] == [str(keep), "0", "0"] and "Perun" in out["ng+ capacity in ng"][1] and "Morana" in out["ng+ capacity in ng"][1], out)
    pg.close()
    # ---- a phone: no sideways scroll, the picker is a full-screen sheet with 44 px rows, the card's disc row opens it ----
    m, errs2 = page(b, base, 390, 844, True); m.evaluate(SETUP, "ng"); m.wait_for_timeout(200)
    ph = m.evaluate("""(()=>({sw:document.documentElement.scrollWidth<=innerWidth+1,discs:document.querySelectorAll('.eqslot .sock').length}))()""")
    m.evaluate("document.querySelector('.eqitem:has(h4)') && document.querySelector('.eqsocks .sock').click()"); until(m, "!!document.querySelector('#skov .skmodal')")
    sheet = m.evaluate("""(()=>{const r=document.querySelector('#skov .skmodal').getBoundingClientRect(),row=document.querySelector('#skov .skrow').getBoundingClientRect(),t=document.querySelector('#skov .sktab').getBoundingClientRect();return{w:r.width,h:r.height,row:row.height,tab:t.height,sw:document.documentElement.scrollWidth<=innerWidth+1}})()""")
    check("%s: on a phone the page does not scroll sideways, the picker is a full-screen sheet and its rows and tabs are 44 px high (%s)" % (label, sheet), ph["sw"] and sheet["w"] >= 388 and sheet["h"] >= 840 and sheet["row"] >= 44 and sheet["tab"] >= 44 and sheet["sw"] and ph["discs"] > 0, [ph, sheet])
    m.close()
    check("%s: no script errors" % label, not errs and not errs2, (errs + errs2)[:2])


def imported(b, base, check, label):
    sav = sorted((FIXD / "sockets-1").glob("*.sav")) if (FIXD / "sockets-1").is_dir() else []
    if not sav:
        check("%s: sockets-1 import (fixture absent: skipped)" % label, True, "skipped"); return
    pg, errs = page(b, base, scr="char"); E = pg.evaluate
    pg.click("#savebtn"); pg.set_input_files("#impfile", [str(sav[0])]); ok = until(pg, "!document.getElementById('impStep2').hidden", 30000)
    sec = E("""(()=>{const s=[...document.querySelectorAll('.impsec')].find(x=>x.querySelector('b').textContent==='Sockets in your save');return s?{lines:[...s.querySelectorAll('.impline')].map(x=>x.textContent.trim()),on:s.querySelector('input').checked}:null})()""")
    check("%s: the import review of sockets-1 has 'Sockets in your save': silver sword = Dazhbog runestone (1 socket), chest = Lesser Glyph of Igni, ticked (%s)" % (label, sec),
          ok and sec and sec["on"] and sec["lines"] == ["Silver sword · Griffin silver sword (1 socket in First playthrough)", "Dazhbog runestone", "Chest armor · Griffin armor (1 socket in First playthrough)", "Lesser Glyph of Igni"], sec)
    pg.click("#impApply"); pg.wait_for_timeout(1200)
    r = E("""(()=>{const n=(slot,j)=>{const x=S.sock[SK_SLOTS.indexOf(slot)*SK_MAX+j];return x?SK.byN.get(x).id:null};return{sock:S.sock.map(x=>x?SK.byN.get(x).id:0).filter(Boolean),silver:n('silver',0),chest:n('chest',0),steel:[0,1,2].map(j=>n('steel',j)),
        others:['gloves','trousers','boots'].map(s=>[0,1,2,3].map(j=>n(s,j))),rolled:PS.imp.rolled,link:location.hash.includes('.r1')}})()""")
    check("%s: applying sockets-1 puts the silver sword = Rune dazhbog and chest = Glyph igni lesser in the build, everything else empty, nothing counted as rolled, and the link has r1 (%s)" % (label, r),
          r["silver"] == "Rune dazhbog" and r["chest"] == "Glyph igni lesser" and len(r["sock"]) == 2 and r["steel"] == [None] * 3 and all(x is None for o in r["others"] for x in o) and r["rolled"] == {} and r["link"], r)
    ps = E("""(()=>{const R=psCalc();return{silver:R.det.silver[2].map(x=>[x[0],x[1],x[2]]).filter(x=>x[2]),sign:R.det.sign[2][0],sig:R.rows.sign.v}})()""")
    check("%s: after the import Player Stats names its sources: the silver sword's burning chance is 3 %% [Dazhbog runestone] and the Igni block carries [Lesser Glyph of Igni] (%s)" % (label, ps),
          ps["silver"] == [["3 %", "Chance to cause burning", "[Dazhbog runestone]"]] and ps["sign"][2] == "[Lesser Glyph of Igni]", ps)
    pg.close()
    # the other saves hold no sockets: they import as before (the numbers themselves are checked by importcheck and statscheck)
    for d in ("refsave", "save-l9", "stats-l9", "stats-l9b"):
        f = sorted((FIXD / d).glob("*.sav")) if (FIXD / d).is_dir() else []
        if not f: check("%s: %s imports with no sockets (fixture absent: skipped)" % (label, d), True, "skipped"); continue
        q, e2 = page(b, base, scr="char"); q.click("#savebtn"); side = sorted((FIXD / d).glob("*.json")); q.set_input_files("#impfile", [str(f[0])] + [str(side[0])] if side else [str(f[0])])
        until(q, "!document.getElementById('impStep2').hidden", 30000); line = q.evaluate("[...document.querySelectorAll('.impsec b')].map(x=>x.textContent).includes('Sockets in your save')")
        q.click("#impApply"); q.wait_for_timeout(1000); sk = q.evaluate("[S.sock.some(Boolean),location.hash.includes('.r1')]"); q.close()
        check("%s: %s has no 'Sockets in your save' section (nothing is socketed), imports with no sockets and no r1 (%s)" % (label, d, line), line is False and sk == [False, False] and not e2, [line, sk, e2])
