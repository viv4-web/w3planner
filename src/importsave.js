// ---- Import save (v31): fill the planner from a Witcher 3 Next-Gen .sav. The file is read in this browser (File API) and never sent anywhere (connect-src 'none'). Notes: docs/IMPORT.md ----
// The reader (src/saveread.js) is a separate hashed script loaded when the dialog first opens. It matches by SAVE ID = OUR ITEM/SKILL ID (never by name or icon) and the dialog shows our localised names.
const SAVEMUT=/*@data:SAVEMUT*/;   // save item id of a skill mutagen -> index in MUTS (tools/make_save_data.py)
const SAVEREAD_URL=/*@lazyjs:saveread*/, SAVENAMES_URL=/*@file:savenames*/;
const IMP={R:null,side:null,file:null,plan:null,opener:null,sel:{}};
const impEl=id=>document.getElementById(id);
const impNum=n=>Number(n).toLocaleString('en-US');
function impNode(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e}
function impOpen(opener){IMP.opener=opener||document.activeElement;impReset();impEl('impov').hidden=false;IMP.pre=impLoad().catch(()=>{});   // the reader loads when the dialog opens
 document.body.classList.add('imp-open');impEl('impfile').focus({preventScroll:true})}
function impClose(){impEl('impov').hidden=true;document.body.classList.remove('imp-open');IMP.R=IMP.plan=null;if(IMP.opener&&IMP.opener.focus)IMP.opener.focus()}
function impReset(){IMP.R=IMP.plan=IMP.side=IMP.file=null;impEl('impStep1').hidden=false;impEl('impStep2').hidden=true;impErr('');impEl('impfile').value='';impEl('impdrop').classList.remove('over')}
function impErr(msg,why){const e=impEl('imperr');e.hidden=!msg;e.textContent='';if(msg){e.appendChild(impNode('b',null,msg));if(why)e.appendChild(impNode('span',null,' '+why))}}
async function impLoad(){   // the reader, the names of items the planner does not plan, and the planner's own item lists (to match and to name)
 if(!window.W3SAVE)await eqScript(SAVEREAD_URL);if(!(window.W3DATA&&W3DATA.savenames))await eqScript(SAVENAMES_URL);await eqLoad(S.rs);await cnLoad()}
async function impHandle(files){
 const list=[...files],sav=list.filter(f=>/\.sav$/i.test(f.name)),js=list.find(f=>/\.json$/i.test(f.name));
 if(!sav.length){impErr(list.length?"This isn't a Witcher 3 save.":'Choose a .sav file.',list.length?'The file must end in .sav.':'');return}
 if(sav.length>1){impErr('One file at a time.','Drop a single .sav (and, if you like, its .json).');return}
 const f=sav[0];if(f.size>(64<<20)){impErr("Couldn't read this save.",'The file is larger than expected.');return}
 impErr('');impEl('impdrop').classList.add('busy');
 try{
  await impLoad();const bytes=new Uint8Array(await f.arrayBuffer());let R;
  try{R=W3SAVE.readSave(bytes)}catch(e){impEl('impdrop').classList.remove('busy');if(e&&e.code==='NOT_SAVE')impErr(e.message);else impErr("Couldn't read this save.",(e&&e.message?e.message:'unknown error')+'.');return}
  let side=null;if(js){try{side=W3SAVE.parseSidecar(await js.text())}catch(e){side=null}}
  IMP.R=R;IMP.side=side;IMP.file=f;IMP.plan=impPlan(R);impReview()
 }catch(e){impErr("Couldn't read this save.",(e&&e.message?e.message:'unknown error')+'.')}
 impEl('impdrop').classList.remove('busy')}

// ---- what the save holds, matched to the planner by id ----
function impPlan(R){
 const d=eqData(),sk=new Map();TREES.forEach((t,ti)=>t.sk.forEach((s,i)=>sk.set(s.id,[ti,i])));
 const ch=R.character,total=ch.pointsUsed+ch.pointsFree,level=Math.max(1,Math.min(100,ch.level)),bonus=Math.max(0,Math.min(100,total-(level-1)));
 const learned=[],notSk=[];R.skills.forEach(s=>{if(s.level<=0||s.core)return;const k=sk.get(s.id);if(k)learned.push({ti:k[0],ix:k[1],level:Math.min(s.level,TREES[k[0]].sk[k[1]].max)});else notSk.push(s.id)});
 const has=(ti,ix)=>learned.some(x=>x.ti===ti&&x.ix===ix),slots=Array(16).fill(null),slotNames=[];let open=0,equipped=0;
 R.skillSlots.forEach(s=>{if(s.unlocked)open++;if(!s.skill)return;const k=sk.get(s.skill);if(k&&has(k[0],k[1])&&s.id>=1&&s.id<=16){slots[s.id-1]=[k[0],k[1]];equipped++;slotNames[s.id-1]=TREES[k[0]].sk[k[1]].name}else notSk.push(s.skill)});
 const muts=[null,null,null,null],mutRows=[],notMut=[];
 R.mutagenSlots.slice(0,4).forEach((m,g)=>{if(!m.item){mutRows.push({slot:g+1,name:null});return}const i=SAVEMUT[m.item];if(i==null){notMut.push(m.item);mutRows.push({slot:g+1,name:null,skip:true})}else{muts[g]=i;mutRows.push({slot:g+1,name:MUTS[i].name})}});
 const GEAR=[['steel','SteelSword'],['silver','SilverSword'],['crossbow','RangedWeapon'],['bolts','Bolt'],['chest','Armor'],['gloves','Gloves'],['trousers','Pants'],['boots','Boots'],['mask','Mask']];
 const gear=Array(9).fill(0),gearRows=[],notGear=[];
 GEAR.forEach(([slot,key],i)=>{const e=R.equipped[key];if(!e){gearRows.push({slot,name:null});return}const it=e.id&&d.byId.get(e.id);if(it&&it.slot===slot){gear[i]=it.n;gearRows.push({slot,name:it.name,set:it.set,item:it})}else{notGear.push(e.id||'?');gearRows.push({slot,name:null,skip:true})}});
 const setCount={};gearRows.forEach(r=>{if(r.set&&['steel','silver','chest','gloves','trousers','boots'].includes(r.slot))setCount[r.set]=(setCount[r.set]||0)+1});
 const topSet=Object.keys(setCount).sort((a,b)=>setCount[b]-setCount[a])[0]||null,setInfo=topSet?{name:EQ.meta.sets[topSet].name,n:setCount[topSet],of:EQ.meta.sets[topSet][S.rs].pieces.length}:null;
 const CONS=[['potion1','Potion1'],['potion2','Potion2'],['potion3','Potion3'],['potion4','Potion4'],['petard1','Petard1'],['petard2','Petard2']],cons=Array(8).fill(0),consRows=[];
 CONS.forEach(([slot,key],i)=>{const e=R.equipped[key];if(!e)return;const it=e.id&&CN.byId.get(e.id);
  if(it&&cnAccepts(slot,it)){cons[i]=it.n;consRows.push({slot,name:it.name,charges:e.extras&&e.extras.ammo_current!=null?e.extras.ammo_current:null})}
  else consRows.push({slot,food:true,name:impDisplay(e.id),qty:e.qty,known:!!(e.id&&W3DATA.savenames[e.id])})});
 ['Quickslot1','Quickslot2'].forEach((key,i)=>{const e=R.equipped[key];if(e)consRows.push({slot:'quick'+(i+1),other:true,name:impDisplay(e.id),qty:e.qty})});
 // the stash: what the save's inventory holds that the planner knows (gear and consumables); the rest is counted
 const stash={weapons:[],armor:[],alchemy:{oils:[],potions:[],bombs:[]}};let plannable=0;
 R.inventory.forEach(r=>{const g=d.byId.get(r.id),c=CN.byId.get(r.id);
  if(g){plannable++;(['steel','silver','crossbow','bolts'].includes(g.slot)?stash.weapons:stash.armor).push({id:g.id,qty:r.qty})}
  else if(c){plannable++;(c.cat==='oil'?stash.alchemy.oils:c.cat==='bomb'?stash.alchemy.bombs:stash.alchemy.potions).push({id:c.id,qty:r.qty})}});
 stash.crowns=R.crowns;
 return{level,bonus,total,learned,notSk,slots,slotNames,open,equipped,muts,mutRows,notMut,gear,gearRows,notGear,setInfo,cons,consRows,stash,plannable,records:R.inventory.length}}
function impDisplay(id){return id?((window.W3DATA&&W3DATA.savenames&&W3DATA.savenames[id])||id):'an unknown item'}

// ---- the review ----
function impVersionNotes(R,side){const notes=[];const c=R.codes,T=W3SAVE.TESTED;
 const untested=c[0]!==T.save||c[1]!==T.game||(side&&(side.saveVersion!==T.save||side.gameVersion!==T.game));
 if(untested)notes.push("Saved with a game version we haven't tested. We'll try; check the results.");
 if(side&&side.mods&&side.mods.length)notes.push('This save lists '+side.mods.length+' mod'+(side.mods.length===1?'':'s')+' ('+side.mods.join(', ')+'). Items or skills added by mods are skipped.');
 return notes}
function impSec(key,title,dest,destGold){const s=impNode('section','impsec');const h=impNode('label','imphead');const cb=impNode('input');cb.type='checkbox';cb.checked=IMP.sel[key]!==false;cb.dataset.sec=key;cb.onchange=()=>{IMP.sel[key]=cb.checked;s.classList.toggle('off',!cb.checked)};
 h.append(cb,impNode('b',null,title),impNode('span','impdest'+(destGold?' gold':''),dest));s.append(h);const body=impNode('div','impbody');s.append(body);return[s,body]}
const impLine=(parent,text,cls)=>parent.appendChild(impNode('p','impline'+(cls?' '+cls:''),text));
function impReview(){
 const R=IMP.R,P=IMP.plan,side=IMP.side,ch=R.character;IMP.sel={character:true,mutagens:true,equipment:true,consumables:true,stash:true};
 impEl('impStep1').hidden=true;const root=impEl('impStep2');root.hidden=false;const main=impEl('impReviewBody');main.textContent='';
 const when=IMP.file.lastModified?new Date(IMP.file.lastModified):null,ver=side&&side.build?'game '+side.build:'save version '+R.codes[0]+' · game '+R.codes[1];
 impEl('impmeta').textContent=[IMP.file.name,when?when.toLocaleString([], {dateStyle:'medium',timeStyle:'short'}):null,ver].filter(Boolean).join(' · ');
 const nb=impEl('impnotes');nb.textContent='';impVersionNotes(R,side).forEach(t=>nb.appendChild(impNode('p','impnote',t)));nb.hidden=!nb.children.length;
 const colA=impNode('div','impcol'),colB=impNode('div','impcol');
 // Character
 let[s,b]=impSec('character','Character','Goes into the build link');colA.append(s);
 impLine(b,'Level '+ch.level+(ch.xpInLevel!=null?' · '+impNum(ch.xpInLevel)+' / '+impNum(ch.xpForLevel)+' XP':' · '+impNum(ch.xpTotal)+' XP'));
 impLine(b,ch.pointsUsed+' skill points used, '+ch.pointsFree+' unspent'+(P.bonus?' ('+(P.level-1)+' from level, '+P.bonus+' go into Bonus points)':''));
 const per=TREES.map((t,ti)=>({n:t.name,c:P.learned.filter(x=>x.ti===ti).length}));impLine(b,'Learned: '+per.map(x=>x.n+' '+x.c).join(' · '));
 TREES.forEach((t,ti)=>{const l=P.learned.filter(x=>x.ti===ti);if(l.length)impLine(b,t.name+': '+l.map(x=>t.sk[x.ix].name+(t.sk[x.ix].max>1?' '+x.level+'/'+t.sk[x.ix].max:'')).join(', '),'dim')});
 impLine(b,'Equipped: '+P.equipped+' of '+P.open+' open slots');if(P.slotNames.some(Boolean))impLine(b,P.slotNames.map((n,i)=>n?(i+1)+'. '+n:null).filter(Boolean).join(' · '),'dim');
 if(P.notSk.length)impLine(b,'Not imported: '+P.notSk.length+' skill'+(P.notSk.length===1?'':'s')+' from outside the planner ('+P.notSk.join(', ')+')','warn');
 // Mutagens
 [s,b]=impSec('mutagens','Mutagens','Goes into the build link');colA.append(s);
 P.mutRows.forEach(r=>impLine(b,'Slot '+r.slot+': '+(r.name||(r.skip?'not imported':'empty')),r.name?'':'dim'));
 if(P.notMut.length)impLine(b,'Not imported: '+P.notMut.join(', '),'warn');
 // Equipment
 [s,b]=impSec('equipment','Equipment','Goes into the build link');colB.append(s);
 P.gearRows.forEach(r=>impLine(b,EQ_NAME[r.slot]+': '+(r.name||(r.skip?'not imported':'empty')),r.name?'':'dim'));
 if(P.setInfo)impLine(b,'Set: '+P.setInfo.name+' '+P.setInfo.n+'/'+P.setInfo.of,'gold');if(P.notGear.length)impLine(b,'Not imported: '+P.notGear.join(', ')+' (not in the '+EQ_RS[S.rs]+' list)','warn');
 // Consumables
 [s,b]=impSec('consumables','Consumables','Goes into the build link');colB.append(s);
 P.consRows.forEach(r=>{const nm=CN_NAME[r.slot]||(r.slot==='quick1'?'Quick slot 1':'Quick slot 2');
  if(r.food)impLine(b,nm+': '+r.name+(r.qty>1?' ×'+r.qty:'')+' (food, not in planner) — slot left empty','dim');
  else if(r.other)impLine(b,nm+': '+r.name+' (not in planner)','dim');
  else impLine(b,nm+': '+r.name+(r.charges!=null?' ×'+r.charges:''))});
 if(!P.consRows.length)impLine(b,'Nothing in the potion or bomb slots','dim');
 // Stash
 [s,b]=impSec('stash','Stash','Stays on this computer',true);colB.append(s);
 impLine(b,impNum(P.records)+' items read · '+impNum(P.plannable)+' plannable');impLine(b,'Crowns: '+impNum(P.stash.crowns));impLine(b,'Kept in this browser only, never in the link.','gold');
 const nr=impNode('div','impnot');nr.append(impNode('b',null,'Not read in this version'),impNode('span',null,' · active mutation · oils on swords · NG+ — set these by hand after import.'));
 const cols=impNode('div','impcols');cols.append(colA,colB);main.append(cols,nr);
 impEl('impApply').focus({preventScroll:true})}

// ---- apply: only the ticked sections, through the planner's own state ----
async function impDoApply(){
 const R=IMP.R,P=IMP.plan,sel=IMP.sel,f=IMP.file;if(!R||!P)return;
 await eqLoad(S.rs);await cnLoad();
 if(sel.character){S.lv=TREES.map(t=>t.nodes.map(()=>0));P.learned.forEach(x=>{S.lv[x.ti][x.ix]=x.level});
  impEl('lvl').value=P.level;impEl('bonuspts').value=P.bonus;S.slots=P.slots.map(x=>x?x.slice():null)}
 if(sel.mutagens)S.muts=P.muts.slice();
 if(sel.equipment)S.gear=P.gear.slice();
 if(sel.consumables){for(let i=0;i<6;i++)S.cons[i]=P.cons[i]}      // the sword oils (positions 6 and 7) are not read: left as they are
 if(sel.stash){try{localStorage.setItem('w3planner.stash',JSON.stringify(P.stash));stashDrawn=false}catch(e){notify('The stash could not be kept: this browser blocks storage for the site.')}}
 enforceLocks();eqValidate();cnValidate();S.scr='char';
 impClose();save();window.scrollTo({top:0});
 notify('Imported from '+f.name+(sel.character?': level '+P.level+', '+P.learned.length+' skills':'')+'. The link now holds this build; use Copy link to share it.')}
function impBind(){
 const b=impEl('savebtn');if(typeof CFG!=='undefined'&&CFG.share===false){b.hidden=true;return}
 b.onclick=()=>impOpen(b);impEl('impx').onclick=impClose;impEl('impback').onclick=impReset;impEl('impAnother').onclick=impReset;
 impEl('impApply').onclick=()=>impDoApply();
 impEl('impfile').onchange=e=>{if(e.target.files.length)impHandle(e.target.files)};
 const dz=impEl('impdrop');['dragenter','dragover'].forEach(t=>dz.addEventListener(t,e=>{e.preventDefault();dz.classList.add('over')}));
 ['dragleave','drop'].forEach(t=>dz.addEventListener(t,e=>{e.preventDefault();dz.classList.remove('over')}));
 dz.addEventListener('drop',e=>{if(e.dataTransfer&&e.dataTransfer.files.length)impHandle(e.dataTransfer.files)});
 impEl('impov').onclick=e=>{if(e.target.id==='impov')impClose()};
 document.addEventListener('keydown',e=>{const o=impEl('impov');if(o.hidden)return;if(e.key==='Escape'){e.preventDefault();impClose()}
  else if(e.key==='Tab'){const f=[...o.querySelectorAll('button,input:not([type=hidden])')].filter(x=>!x.closest('[hidden]')&&x.offsetParent!==null),i=f.indexOf(document.activeElement);
   if(!f.length)return;if(e.shiftKey&&(i<=0)){e.preventDefault();f[f.length-1].focus()}else if(!e.shiftKey&&i===f.length-1){e.preventDefault();f[0].focus()}}});
}
impBind();
