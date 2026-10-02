// ---- Witcher 3 Next-Gen save reader (v31). Own code, MIT. Runs in the browser (a File's bytes, no network) and in Node (tests/test_saveread.js).
// Format notes: docs/IMPORT.md. Loaded on demand when the Import dialog opens (a separate hashed script, never inside index.html): window.W3SAVE = {readSave, parseSidecar, lz4Block, decompress, TESTED}.
(function(root){'use strict';
const TESTED={save:66,game:29,code3:164};   // the save version, game version and third header code of the saves this reader was checked with
class SaveError extends Error{constructor(code,msg){super(msg);this.code=code}}
const dv=(d)=>new DataView(d.buffer,d.byteOffset,d.byteLength);
const u16=(d,o)=>d[o]|(d[o+1]<<8),u32=(d,o)=>(d[o]|(d[o+1]<<8)|(d[o+2]<<16)|(d[o+3]<<24))>>>0,i32=(d,o)=>d[o]|(d[o+1]<<8)|(d[o+2]<<16)|(d[o+3]<<24);
const str=(d,o,n)=>{let s='';for(let i=0;i<n;i++)s+=String.fromCharCode(d[o+i]);return s};

// LZ4 block (no frame): the container stores each 1 MiB chunk as one block
function lz4Block(src,sp,send,dst,dp){
 while(sp<send){const t=src[sp++];let lit=t>>4;if(lit===15){let b;do{b=src[sp++];lit+=b}while(b===255)}
  for(let i=0;i<lit;i++)dst[dp++]=src[sp++];
  if(sp>=send)break;
  const off=src[sp]|(src[sp+1]<<8);sp+=2;if(off===0||off>dp)throw new SaveError('PARSE','bad LZ4 offset');
  let ml=t&15;if(ml===15){let b;do{b=src[sp++];ml+=b}while(b===255)}ml+=4;
  let m=dp-off;for(let i=0;i<ml;i++)dst[dp++]=dst[m++]}
 return dp}
// "SNFH" "FZLC", i32 chunk count, i32 header size, then count x (i32 compressed, i32 decompressed, i32 end offset); the chunks follow the header
function decompress(buf){
 if(buf.length<16||str(buf,0,8)!=='SNFHFZLC')throw new SaveError('NOT_SAVE',"This isn't a Witcher 3 save.");
 const n=i32(buf,8),hs=i32(buf,12);if(n<1||n>4096||hs<16+12*n||hs>buf.length)throw new SaveError('PARSE','the chunk table is damaged');
 let total=0;const tab=[];for(let i=0;i<n;i++){const cs=i32(buf,16+12*i),ds=i32(buf,20+12*i);if(cs<0||ds<0||ds>(1<<22))throw new SaveError('PARSE','a chunk size is wrong');tab.push([cs,ds]);total+=ds}
 if(total>(1<<28))throw new SaveError('PARSE','the save is larger than expected');
 const out=new Uint8Array(hs+total);out.set(buf.subarray(0,hs));let sp=hs,dp=hs;
 for(const[cs,ds]of tab){if(sp+cs>buf.length)throw new SaveError('PARSE','the file is cut short');const e=lz4Block(buf,sp,sp+cs,out,dp);if(e-dp!==ds)throw new SaveError('PARSE','a chunk did not unpack to its size');sp+=cs;dp+=ds}
 return out}

// ---- names and variable table ----
function readTables(d,hs){
 if(str(d,hs,4)!=='SAV3')throw new SaveError('PARSE','the save header is missing');
 const codes=[i32(d,hs+4),i32(d,hs+8),i32(d,hs+12)];
 if(str(d,d.length-2,2)!=='SE')throw new SaveError('PARSE','the end marker is missing');
 const vt=i32(d,d.length-6),sf=vt-10,nm=i32(d,sf);if(vt<=0||vt>=d.length||nm<=0||nm>=d.length||str(d,nm,2)!=='NM')throw new SaveError('PARSE','the name table is missing');
 const so=nm+2;if(str(d,so,4)!=='MANU')throw new SaveError('PARSE','the name table is damaged');
 const n=i32(d,so+4);let o=so+12;const names=[];for(let i=0;i<n;i++){const l=d[o];names.push(str(d,o+1,l));o+=1+l}
 const cnt=i32(d,vt),ents=[];for(let i=0;i<cnt;i++)ents.push([i32(d,vt+4+8*i),i32(d,vt+8+8*i)]);ents.sort((a,b)=>a[0]-b[0]);
 return{codes,names,ents}}
function find(d,pat,from,to){const n=pat.length;outer:for(let i=from;i<=to-n;i++){for(let k=0;k<n;k++)if(d[i+k]!==pat[k])continue outer;return i}return -1}

// ---- values: the engine's property serialisation (u16 name index, u16 type index, u32 size) ----
function propsPos(d,o,end,N){const out=[];if(d[o]===0)o++;
 while(o+2<=end){const n=u16(d,o);if(n===0)return{list:out,pos:o+2};const ty=u16(d,o+2),sz=u32(d,o+4);if(sz<4||o+4+sz>end)break;out.push([N[n-1],N[ty-1],d.subarray(o+8,o+4+sz)]);o+=4+sz}
 return{list:out,pos:o}}
const props=(d,o,end,N)=>propsPos(d,o,end,N).list;
const PW={Bool:1,Int8:1,Uint8:1,Int16:2,Uint16:2,CName:2,Int32:4,Uint32:4,Float:4,Int64:8,Uint64:8,Double:8,CGUID:16};
const isEnum=t=>t.length>2&&t[0]==='E'&&t[1]>='A'&&t[1]<='Z';
function prim(t,r,N){
 if(isEnum(t)&&r.length===2){const i=u16(r,0);return i>0&&i<=N.length?N[i-1]:null}
 switch(t){case'Bool':return !!r[0];case'Uint8':return r[0];case'Int8':return r[0]<<24>>24;case'Uint16':return u16(r,0);case'Int16':return u16(r,0)<<16>>16;case'Uint32':return u32(r,0);case'Int32':return i32(r,0);
  case'Uint64':return Number(dv(r).getBigUint64(0,true));case'Int64':return Number(dv(r).getBigInt64(0,true));case'Float':return dv(r).getFloat32(0,true);case'Double':return dv(r).getFloat64(0,true);
  case'CName':{const i=u16(r,0);return i>0&&i<=N.length?N[i-1]:null}
  case'String':{const h=r[0];return h&128?str(r,1,h&127):null}
  case'StringAnsi':return str(r,1,r[0]).replace(/\0+$/,'')}
 return undefined}
function struct(p,N){const o={};for(const[a,b,c]of p){try{o[a]=value(b,c,N)}catch(e){o[a]=null}}return o}
function value(t,r,N){
 const v=prim(t,r,N);if(v!==undefined)return v;
 if(t.startsWith('array:')){const et=t.split(',').slice(2).join(','),n=u32(r,0);
  if(isEnum(et))return Array.from({length:n},(_,i)=>prim(et,r.subarray(4+i*2,6+i*2),N));
  if(PW[et]){const w=PW[et];return Array.from({length:n},(_,i)=>prim(et,r.subarray(4+i*w,4+(i+1)*w),N))}
  if(et==='String'||et==='StringAnsi'){let o=4;const out=[];for(let i=0;i<n;i++){const l=r[o]&127;out.push(str(r,o+1,l));o+=1+l}return out}
  let o=4;const out=[];for(let i=0;i<n;i++){const r2=propsPos(r,o,r.length,N);out.push(struct(r2.list,N));o=r2.pos}   // a struct element = a property list that ends with name 0
  return out}
 if(t.startsWith('handle:')||t.startsWith('ptr:')){if(r.length<12)return{cls:null,empty:true};return Object.assign(struct(props(r,8,r.length,N),N),{cls:N[u16(r,6)-1]})}
 return struct(props(r,0,r.length,N),N)}

// ---- the player's inline blob: SXAP, BLCK Entity (its PORPs), more BLCKs, then the inventory as a raw binary list ----
function playerBlob(d,tb){
 const N=tb.names,idx=N.indexOf('levelManager')+1;if(idx<1)throw new SaveError('PARSE','the player data was not found');
 const pat=[0x50,0x4f,0x52,0x50,idx&255,idx>>8];
 for(let i=0;i<tb.ents.length;i++){const o=tb.ents[i][0];if(d[o]!==0x53||d[o+1]!==0x53)continue;
  const ts=(i+1<tb.ents.length?tb.ents[i+1][0]:o+tb.ents[i][1])-o;if(find(d,pat,o,o+ts)<0)continue;
  // top-level tokens of the blob
  let p=o+6;const end=o+ts;let entity=null;
  while(p<end){const m=str(d,p,4);
   if(m==='SXAP')p+=16;
   else if(m==='BLCK'){const nm=N[u16(d,p+4)-1],sz=u32(d,p+6),st=p+10;if(nm==='Entity')entity=[st,st+sz];p=st+sz}
   else if(m==='PORP'||m==='AVAL')p+=12+u32(d,p+8);
   else if(m==='SBDF')p+=8+u32(d,p+4);
   else break}
  if(!entity)continue;
  const P={};let q=entity[0];
  while(q<entity[1]){const m=str(d,q,4);
   if(m==='PORP'||m==='AVAL'){const nm=N[u16(d,q+4)-1],ty=N[u16(d,q+6)-1],sz=u32(d,q+8);if(m==='PORP')P[nm]={type:ty,val:d.subarray(q+12,q+12+sz)};q+=12+sz}
   else if(m==='BLCK')q+=10+u32(d,q+6);
   else break}
  return{P,inv:p<end?d.subarray(p,end):null}}
 throw new SaveError('PARSE','the player data was not found')}

// ---- the inventory (CInventoryComponent) binary: u16 item count at byte 11, then variable records. Records are found by their fixed middle:
// [name u16][4][7][dye u16 u16 = 43 00 44 00 for the default dye][quantity u16][float: -1.0 or the durability][u8 extras n][n x (u16 name, u32 value, u8)][u16 id][u16 quality/level] ----
function inventory(raw,N){
 if(!raw||raw.length<30)return{count:0,items:[]};const header=u16(raw,11),starts=new Set();
 for(let i=13;i<raw.length-6;i++){
  if(raw[i]===0x43&&raw[i+1]===0&&raw[i+2]===0x44&&raw[i+3]===0&&raw[i+4]===1&&raw[i+5]===0)starts.add(i-13);
  if(raw[i]===0&&raw[i+1]===0&&raw[i+2]===0x80&&raw[i+3]===0xbf)starts.add(i-19)}
 const items=[],sorted=Array.from(starts).sort((a,b)=>a-b);
 sorted.forEach((st,k)=>{
  if(st<13||st+30>raw.length)return;const name=u16(raw,st);if(name<1||name>N.length)return;const ne=raw[st+23];if(ne>6)return;
  let o=st+24;const ex={};let ok=true;
  for(let j=0;j<ne;j++){if(o+7>raw.length){ok=false;break}const en=u16(raw,o);ex[N[en-1]||'?']=u32(raw,o+2);o+=7}
  if(!ok||o+4>raw.length)return;
  // after the extras: [u16 id][u16 count x 256][count x u16 ability name]...; items made by the game's random generator (autogen_*, MA_* magic abilities, quality_*) list their rolled abilities there,
  // the fixed relics and set pieces list none (docs/IMPORT.md, "Rolled values and sockets")
  const end=k+1<sorted.length?sorted[k+1]:raw.length,cnt=Math.min(raw[o+3],Math.max(0,Math.floor((end-(o+4))/2))),abilities=[];
  for(let j=0;j<cnt;j++){const an=u16(raw,o+4+2*j);if(an>=1&&an<=N.length)abilities.push(N[an-1])}
  items.push({id:N[name-1],qty:u16(raw,st+17),ref:u16(raw,o),extras:ex,abilities})});
 return{count:header,items}}

const SLOT_NAMES=['invalid','SilverSword','SteelSword','Armor','Boots','Pants','Gloves','Petard1','Petard2','RangedWeapon','Quickslot1','Quickslot2','Unused','Hair','Potion1','Potion2','Mask','Bolt','PotMut1','PotMut2','PotMut3','PotMut4','SkillMut1','SkillMut2','SkillMut3','SkillMut4','HorseBlinders','HorseSaddle','HorseBag','HorseTrophy','Potion3','Potion4'];
// bytes of a save (Uint8Array) -> what the importer needs. Throws SaveError('NOT_SAVE' | 'PARSE', message).
function readSave(bytes){
 const d=decompress(bytes),hs=i32(bytes,12),tb=readTables(d,hs),N=tb.names,{P,inv}=playerBlob(d,tb);
 const get=k=>{if(!P[k])throw new SaveError('PARSE','"'+k+'" was not found in the player data');return value(P[k].type,P[k].val,N)};
 const lm=get('levelManager'),am=get('abilityManager'),slots=get('itemSlots');
 const pts=lm.points||[],sp=pts[0]||{},xp=pts[1]||{},total=(xp.used||0)+(xp.free||0),defs=lm.levelDefinitions||[];
 const need=n=>{const e=defs.find(x=>x.number===n);return e&&e.requiredTotalExp!=null?e.requiredTotalExp:null};
 const lo=need(lm.level),hi=need(lm.level+1);
 const character={level:lm.level,xpTotal:total,xpInLevel:lo!=null?total-lo:null,xpForLevel:lo!=null&&hi!=null?hi-lo:null,pointsUsed:sp.used||0,pointsFree:sp.free||0};
 const skills=(am.skills||[]).filter(x=>x.abilityName).map(x=>({id:x.abilityName,level:x.level||0,max:x.maxLevel||0,core:!!x.isCoreSkill}));
 const skillSlots=(am.skillSlots||[]).map(s=>({id:s.id,skill:s.socketedSkill?((am.skills||[]).find(x=>x.skillType===s.socketedSkill)||{}).abilityName||null:null,unlocked:!!s.unlocked}));
 const invr=inventory(inv,N),byRef=new Map();invr.items.forEach(r=>{if(!byRef.has(r.ref))byRef.set(r.ref,r)});
 const equipped={};slots.forEach((s,i)=>{const v=s&&s.value;if(v&&SLOT_NAMES[i]){const r=byRef.get(v);equipped[SLOT_NAMES[i]]=r?{id:r.id,qty:r.qty,extras:r.extras,abilities:r.abilities}:{id:null,ref:v}}});
 const mutagenSlots=(am.mutagenSlots||[]).map(m=>{const v=m.item&&m.item.value;const r=v?byRef.get(v):null;return{slot:m.equipmentSlot,unlockedAt:m.unlockedAtLevel,item:r?r.id:null}});
 const crowns=(invr.items.find(r=>r.id==='Crowns')||{}).qty||0;
 return{codes:tb.codes,character,skills,skillSlots,mutagenSlots,equipped,inventory:invr.items,inventoryHeader:invr.count,crowns,playTimeSec:playTime(d,N),effects:effects(P.effectManager,N)}}
// The player's active effects (potions, whetstones, Places of Power ...): the effectManager property lists W3Effect_* objects, each a property list with abilityName, duration and timeLeft (seconds).
function effects(pr,N){const out=[];if(!pr)return out;const v=pr.val;
 for(let i=0;i+1<v.length;i++){const n=u16(v,i);if(n>=1&&n<=N.length&&N[n-1].indexOf('W3Effect_')===0){
  try{const L=propsPos(v,i+2,v.length,N).list,o={cls:N[n-1]};
   L.forEach(([a,t,x])=>{if(a==='abilityName'&&t==='CName'){const k=u16(x,0);o.ability=k>0&&k<=N.length?N[k-1]:null}else if((a==='timeLeft'||a==='duration')&&t==='Float')o[a]=dv(x).getFloat32(0,true)});
   out.push(o)}catch(e){}}}
 return out}
// Time played: the one property "GameTime" of type Double in the save (seconds, e.g. 37522.0632893 = 10 h 25 min; read from two saves of one run, it grows by the minutes played). null when not found.
function playTime(d,N){const g=N.indexOf('GameTime')+1,t=N.indexOf('Double')+1;if(g<1||t<1)return null;const dv=new DataView(d.buffer,d.byteOffset,d.length);
 for(let i=0;i+12<=d.length;i++)if(d[i]===(g&255)&&d[i+1]===(g>>8)&&d[i+2]===(t&255)&&d[i+3]===(t>>8)){const x=dv.getFloat64(i+4,true);if(x>=0&&x<1e8)return x}
 return null}

// the JSON next to a save: {saveMetadata:{initial buildID, current buildID, gameVersion, saveVersion, platform, modsMetadata:{numMods, modsList:{mod...}}}}
function parseSidecar(text){
 let j;try{j=JSON.parse(text)}catch(e){return null}const m=j&&j.saveMetadata;if(!m)return null;
 // the same key "mod" repeats in modsList, so a parsed object keeps only the last: take the names from the text too
 const names=[];const re=/"modName"\s*:\s*"((?:[^"\\]|\\.)*)"/g;let x;while((x=re.exec(text)))names.push(x[1].replace(/^modio_/,''));
 return{gameVersion:m.gameVersion,saveVersion:m.saveVersion,platform:m.platform||null,build:String(m['current buildID']||'').trim().split(/\s+/)[0]||null,mods:names,numMods:+(m.modsMetadata&&m.modsMetadata.numMods)||names.length}}

root.W3SAVE={readSave,parseSidecar,lz4Block,decompress,TESTED,SaveError,SLOT_NAMES};
if(typeof module!=='undefined'&&module.exports)module.exports=root.W3SAVE;
})(typeof window!=='undefined'?window:globalThis);
