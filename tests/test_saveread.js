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
 console.log('stats-l9b checks passed')}
console.log(n+' checks passed');
