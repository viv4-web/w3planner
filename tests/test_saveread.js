// Save import, unit tests without a browser: node tests/test_saveread.js
// Synthetic data only; the reference-save acceptance runs from tests/importcheck.py (and here, if ~/work/w3planner-art/save-spike/fixtures/refsave/ exists).
const fs=require('fs'),path=require('path'),os=require('os');
const W=require('../src/saveread.js');
let n=0;const ok=(name,c,d)=>{n++;if(!c){console.error('FAIL: '+name,d===undefined?'':JSON.stringify(d));process.exit(1)}};
const throws=(f)=>{try{f()}catch(e){return e}return null};
// LZ4 block: literals only, a match with an overlapping copy, and a long literal run (15 + 255 + extra)
const dec=(bytes,size)=>{const out=new Uint8Array(size);const e=W.lz4Block(Uint8Array.from(bytes),0,bytes.length,out,0);return[e,out]};
let [e1,o1]=dec([0x50,...'hello'.split('').map(c=>c.charCodeAt(0))],5);ok('lz4: literals only',e1===5&&Buffer.from(o1).toString()==='hello');
[e1,o1]=dec([0x32,0x61,0x62,0x63,0x03,0x00],9);ok('lz4: a match copies from 3 back (abcabcabc)',Buffer.from(o1).toString()==='abcabcabc',Buffer.from(o1).toString());
[e1,o1]=dec([0x11,0x61,0x01,0x00],6);ok('lz4: an overlapping match repeats a byte (aaaaaa)',Buffer.from(o1).toString()==='aaaaaa');
const [e2,o2]=dec([0xf0,255,0,...Array(270).fill(0x7a)],270);ok('lz4: a literal length of 15 + 255 + 0 bytes',e2===270&&o2.every(x=>x===0x7a),e2);
ok('lz4: a zero offset is refused',!!throws(()=>dec([0x10,0x61,0x00,0x00],5)));
// the container header
ok('not a save: wrong magic',(throws(()=>W.readSave(new Uint8Array(40).fill(65)))||{}).code==='NOT_SAVE');
ok('not a save: too short',(throws(()=>W.readSave(new Uint8Array(3)))||{}).code==='NOT_SAVE');
const hdr=(cnt,hs)=>{const b=new Uint8Array(64);b.set(Buffer.from('SNFHFZLC'));new DataView(b.buffer).setInt32(8,cnt,true);new DataView(b.buffer).setInt32(12,hs,true);return b};
ok('a damaged chunk table is a parse error, not a crash',(throws(()=>W.readSave(hdr(100000,16)))||{}).code==='PARSE');
ok('a file cut short is a parse error',(throws(()=>{const b=hdr(1,28);new DataView(b.buffer).setInt32(16,1000,true);new DataView(b.buffer).setInt32(20,10,true);return W.readSave(b)})||{}).code==='PARSE');
// the sidecar, including the repeated "mod" key that JSON.parse would collapse
const side=W.parseSidecar('{"saveMetadata":{"current buildID":"5.0.1044392  P4CL: 1","gameVersion":29,"saveVersion":66,"platform":"PC","modsMetadata":{"numMods":2,"modsList":{"mod":{"modName":"modio_A","modID":1},"mod":{"modName":"modio_B","modID":2}}}}}');
ok('sidecar: version, build, platform and BOTH mod names',side&&side.gameVersion===29&&side.saveVersion===66&&side.build==='5.0.1044392'&&side.platform==='PC'&&side.mods.join()==='A,B'&&side.numMods===2,side);
ok('sidecar: no mods, and junk, are fine',W.parseSidecar('{"saveMetadata":{"gameVersion":29,"saveVersion":66}}').mods.length===0&&W.parseSidecar('nope')===null);
// the mutagen table: one save id per planner mutagen, spot cases
const root=path.join(__dirname,'..','data'),A=JSON.parse(fs.readFileSync(path.join(root,'SAVEMUT.json'))),base=JSON.parse(fs.readFileSync(path.join(root,'MUTS.json'))),spec=JSON.parse(fs.readFileSync(path.join(root,'SPECIAL_MUT.json')));
const names=[...base.map(m=>m.name),...spec.map(s=>s[0]+' mutagen')];
ok('mutagen table: 36 ids, each planner mutagen exactly once',Object.keys(A).length===36&&[...Object.values(A)].sort((a,b)=>a-b).every((v,i)=>v===i));
const want={'Wraith mutagen':'Wraith mutagen','Gryphon mutagen':'Griffin mutagen','Fogling 1 mutagen':'Foglet mutagen','Fogling 2 mutagen':'Greater Foglet mutagen','Czart mutagen':'Chort mutagen','Dao mutagen':'Earth Elemental mutagen','Lamia mutagen':'Ekhidna mutagen','Volcanic Gryphon mutagen':'Archgriffin mutagen','Ekimma mutagen':'Ekimmara mutagen','Leshy mutagen':'Leshen mutagen','Lesser mutagen green':'Lesser green mutagen','Mutagen blue':'Blue mutagen','Greater mutagen red':'Greater red mutagen'};
for(const[k,v]of Object.entries(want))ok('mutagen table: '+k+' -> '+v,names[A[k]]===v,names[A[k]]);
// the names of items a quick slot can hold that the planner does not plan
const N=JSON.parse(fs.readFileSync(path.join(root,'savenames.json')));ok('savenames: Cows milk -> Cow\'s milk, Bottled water -> Water, Torch',N['Cows milk']==="Cow's milk"&&N['Bottled water']==='Water'&&N['Torch']==='Torch');
// the journal of the two stats saves (v33): the entries the save lists, by the GUID of the last path element (checked against data/QUESTS.json: 29 / 15 / 1 / 1 and 28 / 13 / 1 / 1)
{const Q=JSON.parse(fs.readFileSync(path.join(root,'QUESTS.json'))).quests,byG=new Map(Q.map(q=>[q.g,q])),fx=path.join(os.homedir(),'work/w3planner-art/save-spike/fixtures');
 for(const[sub,want,total]of[['stats-l9b',{JS_Success:29,JS_Active:15,JS_Failed:1,JS_Inactive:1},927],['stats-l9',{JS_Success:28,JS_Active:13,JS_Failed:1,JS_Inactive:1},898]]){
  const d=path.join(fx,sub),f=fs.existsSync(d)?fs.readdirSync(d).find(x=>x.endsWith('.sav')):null;if(!f){console.log('journal '+sub+': fixture not present, skipped');continue}
  const j=W.readSave(new Uint8Array(fs.readFileSync(path.join(d,f)))).journal,c={};j.forEach(([g,s])=>{if(byG.has(g))c[s]=(c[s]||0)+1});
  ok('journal '+sub+': '+total+' entries, every guid 32 hex digits, quest states '+JSON.stringify(want),j.length===total&&j.every(e=>/^[0-9a-f]{32}$/.test(e[0]))&&Object.keys(want).every(k=>c[k]===want[k])&&Object.keys(c).length===4,c)}}
// v35.2: the item records are found by the name-table indices of the default dye (67/68 in saves 66, 147/150 in save 67), looked up by name. The four version-66 saves must read exactly as before the change
// (sha1 of the whole readSave result, taken from the old reader and checked equal), and save 67 (a rune in a sword, a glyph in an armour) must find every record and its gear.
{const crypto=require('crypto'),fx=path.join(os.homedir(),'work/w3planner-art/save-spike/fixtures'),first=d=>{const p=path.join(fx,d),f=fs.existsSync(p)?fs.readdirSync(p).find(x=>x.endsWith('.sav')):null;return f?new Uint8Array(fs.readFileSync(path.join(p,f))):null};
 const SHA={refsave:'945f086a900ce12cc5648ba72afd81504d591a13','save-l9':'2dbc873bf5a2c6e2849005582f2df5a638910e3d','stats-l9':'7e3a22725cfeec14766d194b06334a7ca1603f8a','stats-l9b':'a88eaccbad0248d5e3d4e59fff65599c33742106'};
 for(const[d,h]of Object.entries(SHA)){const b=first(d);if(!b){console.log('v35.2 '+d+': fixture not present, skipped');continue}const R=W.readSave(b);ok('v35.2 '+d+': the whole read result is what it was before the dye lookup (sha1 '+h.slice(0,8)+')',crypto.createHash('sha1').update(JSON.stringify(R)).digest('hex')===h&&R.inventory.length===R.inventoryHeader)}
 const b=first('sockets-1');if(b){const R=W.readSave(b),E=R.equipped;ok('v35.2 sockets-1: save version 67, 722 records = the header (the old reader found 706)',R.codes[0]===67&&R.inventory.length===722&&R.inventoryHeader===722,[R.codes,R.inventory.length]);
  ok('v35.2 sockets-1: the gear is found by id (Gryphon School silver and steel swords, Gryphon Armor, Gloves 1, Boots 1, Pants 1, Crossbow 5)',E.SilverSword.id==='Gryphon School silver sword'&&E.SteelSword.id==='Gryphon School steel sword'&&E.Armor.id==='Gryphon Armor'&&E.Gloves.id==='Gryphon Gloves 1'&&E.Boots.id==='Gryphon Boots 1'&&E.Pants.id==='Gryphon Pants 1'&&E.RangedWeapon.id==='Crossbow 5',Object.fromEntries(Object.entries(E).map(([k,v])=>[k,v.id])));
  ok('v35.2 sockets-1: the socketed rune and glyph are not imported, but their ability names keep those two items out of the stats numbers; the plain gear lists none',E.SilverSword.abilities.join()==='Rune dazhbog _Stats'&&E.Armor.abilities.join()==='Glyph igni lesser _Stats'&&E.SteelSword.abilities.length===0&&E.Gloves.abilities.length===0,[E.SilverSword.abilities,E.Armor.abilities])}
 else console.log('v35.2 sockets-1: fixture not present, skipped')}
// the reference save, when the local fixture exists
const ref=path.join(os.homedir(),'work/w3planner-art/save-spike/fixtures/refsave/ManualSave_52587_7ea48400_3d23fe3.sav');
if(fs.existsSync(ref)){const R=W.readSave(new Uint8Array(fs.readFileSync(ref)));
 ok('refsave: level 8, 610 of 1000 XP, 15 points used, 0 free',R.character.level===8&&R.character.xpInLevel===610&&R.character.xpForLevel===1000&&R.character.pointsUsed===15&&R.character.pointsFree===0,R.character);
 ok('refsave: header codes 66 / 29 / 164',R.codes.join()==='66,29,164');
 ok('refsave: 402 inventory records = the header, crowns 2890',R.inventory.length===402&&R.inventoryHeader===402&&R.crowns===2890);
 ok('refsave: gear ids, quantities, charges',R.equipped.SteelSword.id==='Dol Blathanna longsword'&&R.equipped.Potion1.qty===30&&R.equipped.Potion2.qty===66&&R.equipped.Petard1.extras.ammo_current===2&&R.equipped.Potion3.extras.ammo_current===3&&!R.equipped.Mask);
 console.log('refsave checks passed');}
else console.log('refsave not present: those checks were skipped');
const l9b=path.join(os.homedir(),'work/w3planner-art/save-spike/fixtures/stats-l9b/AutoSave_106591_7ea48400_52e9569.sav');
if(fs.existsSync(l9b)){const R=W.readSave(new Uint8Array(fs.readFileSync(l9b)));
 ok('stats-l9b: time played 39576.77 s (10 h 59 min)',Math.abs(R.playTimeSec-39576.7659)<0.01,R.playTimeSec);
 ok('stats-l9b: two active effects, ShrineQuenEffect 1800 s and EnhancedWeaponEffect 3600 s, with the time left',R.effects.length===2&&R.effects[0].ability==='ShrineQuenEffect'&&R.effects[0].duration===1800&&R.effects[1].ability==='EnhancedWeaponEffect'&&R.effects[1].timeLeft>3500&&R.effects[1].timeLeft<3600,R.effects);
 ok('stats-l9b: the equipped relics list no abilities, the carried random items list theirs (autogen_*, MA_*, quality_*)',R.equipped.SteelSword.abilities.length===0&&R.inventory.some(r=>r.id==='Boots 02'&&r.abilities.includes('MA_BurningResistance')&&r.abilities.includes('quality_masterwork_boots')),R.equipped.SteelSword);
 ok('stats-l9b: the player\'s ability list: 200 entries, perk_24 x 12 (4 medium pieces x level 3), magic_staminaregen x 12, synergy bonus x 30, <mutagen>_x x 7, Lvl2 to Lvl9, the two effects',
   (A=>A&&Object.values(A).reduce((a,b)=>a+b,0)===200&&A.perk_24===12&&A.magic_staminaregen===12&&A.greater_mutagen_color_blue_synergy_bonus===30&&A.greater_mutagen_color_blue_x===7&&A.Lvl2===1&&A.Lvl9===1&&!A.Lvl10&&A.ShrineQuenEffect===1&&A.EnhancedWeaponEffect===1&&A.all_PC_ability===1)(R.abilities),R.abilities);
 console.log('stats-l9b checks passed')}
console.log(n+' checks passed');
