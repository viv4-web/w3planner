// ---- Consumables (v28): potions, decoctions, bombs and oils from data/consumables.json, loaded with the equipment lists (a script tag, never inside index.html) ----
// Slots (the game's EEquipmentSlots, itemsTypes.ws:25-39 and 32-33,48-49): Potion1-4 take potions, decoctions AND food and drink (GetSlotForItem, itemsTypes.ws:357-374: the 'Potion' tag, and 'Edibles'/'Drinks' -> EES_Potion1),
// Petard1 takes bombs, the second of the two slots the planner had is the Pocket (EES_Quickslot1: tag 'QuickSlot', itemsTypes.ws:364). The remaster has one bomb slot and one Pocket slot.
// Oils are not slots: one oil per sword (the Fixative skill, which allows several, is not in the new skill tree), an oil only on a sword it fits (SteelOil / SilverOil tag, r4Player.ws:1378-1385).
const CN_URL=/*@file:consumables*/;
const CN_SLOTS=['potion1','potion2','potion3','potion4','petard1','pocket','oil_steel','oil_silver'];   // the order of the c1 link segment: never change it, only append
const CN_NAME={potion1:'Potion 1',potion2:'Potion 2',potion3:'Potion 3',potion4:'Potion 4',petard1:'Bomb',pocket:'Pocket',oil_steel:'Steel sword oil',oil_silver:'Silver sword oil'};
const CN_CAT={potion:'Potion',decoction:'Decoction',bomb:'Bomb',oil:'Oil',food:'Food & drink',pocket:'Pocket'},CN_COL={potion:'#b8423a',decoction:'#5b9a43',bomb:'#c8892f',oil:'#d9a640',food:'#a98b5a',pocket:'#c9a24a'};
let CN={data:null,byN:new Map(),byId:new Map(),bySlot:{},err:null};
// the one rule that says what a slot accepts (a unit test calls it directly)
function cnAccepts(slotKey,it){if(!it)return false;
 if(slotKey.startsWith('potion'))return it.cat==='potion'||it.cat==='decoction'||it.cat==='food';
 if(slotKey==='petard1')return it.cat==='bomb';
 if(slotKey==='pocket')return it.cat==='pocket';
 if(slotKey==='oil_steel')return it.cat==='oil'&&!!it.steel;
 if(slotKey==='oil_silver')return it.cat==='oil'&&!!it.silver;
 return false}
async function cnLoad(){if(CN.data)return CN;
 if(!(window.W3DATA&&W3DATA.consumables))await eqScript(CN_URL);
 const d=W3DATA.consumables;CN.data=d;CN.byN=new Map();CN.byId=new Map();d.items.forEach(it=>{CN.byN.set(it.n,it);CN.byId.set(it.id,it)});
 CN.bySlot={};CN_SLOTS.forEach(k=>{CN.bySlot[k]=d.items.filter(it=>cnAccepts(k,it))});return CN}
const cnCur=k=>CN.data&&S.cons[k]?CN.byN.get(S.cons[k])||null:null;   // k = position in the c1 segment (0-7)
// numbers that are not a valid item for their slot (a hand-made link) are dropped, like gear that does not exist in the ruleset
// An old link (v28 to v31) can hold a bomb in the second bomb slot, which is now the Pocket: the bomb moves to the Bomb slot when that is empty, otherwise it is dropped; CN.moved says which (shown by the caller).
// The link text is not rewritten until the build changes; the numbers decode as before.
function cnValidate(){let bad=0;CN.moved=[];CN_SLOTS.forEach((k,i)=>{const n=S.cons[i];if(!n)return;const it=CN.byN.get(n);if(!cnAccepts(k,it)){
  if(k==='pocket'&&it&&it.cat==='bomb'){if(!S.cons[4]){S.cons[4]=n;CN.moved.push(it.name+' moved to the Bomb slot (the second bomb slot is now the Pocket)')}else{CN.moved.push(it.name+' was in the second bomb slot, which is now the Pocket; the Bomb slot already holds a bomb, so it was removed')}S.cons[i]=0;return}
  S.cons[i]=0;bad++}});return bad}
// the NG+ bomb numbers differ (the data says which): the item as the current ruleset shows it
function cnView(it){const g=S.rs==='ng_plus'&&it.ngp?it.ngp:null;return{stats:(g&&g.stats)||it.stats||[],dur:g&&g.dur!=null?g.dur:it.dur,ch:g&&g.ch!=null?g.ch:it.ch}}

// ---- "Affected by": the skills and mutations of THIS build that change the item (names only; no numbers are computed) ----
// kinds: what the skill touches. Sources: playerWitcher.ws (CalculatePotionDuration 7410-7445, GetToxicityDamageThreshold 7385, S_Alchemy_s03 7686), alchemyManager.ws:234, petard.ws:1092-1118, 1312,
// damageManagerProcessor.ws:751-763, 1899, 2504, 2553; mutations: playerWitcher.ws:4182 (Metamorphosis), PlayerAbilityManager.ws:4671 (Euphoria).
const CN_MODS=[
 {skill:'alchemy_s14',cats:['decoction'],what:'decoction duration'},
 {skill:'alchemy_s3',cats:['potion'],what:'potion duration'},
 {skill:'alchemy_s4',cats:['potion'],what:'a bonus potion effect'},
 {skill:'alchemy_s2',cats:['potion'],what:'Vitality healed per dose'},
 {skill:'alchemy_s13',cats:['decoction'],what:'Vitality while a decoction is active'},
 {skill:'alchemy_s18',cats:['potion','decoction'],what:'maximum Toxicity'},
 {skill:'alchemy_s15',cats:['potion','decoction'],what:'how fast Toxicity drops'},
 {skill:'alchemy_s24',cats:['potion','decoction'],what:'damage at high Toxicity'},
 {skill:'alchemy_s20',cats:['potion','decoction'],what:'Toxicity damage threshold'},
 {skill:'alchemy_s10',cats:['bomb'],what:'bomb damage'},
 {skill:'alchemy_s11',cats:['bomb'],what:'cluster bombs'},
 {skill:'alchemy_s25',cats:['bomb'],what:'bomb damage by Toxicity'},
 {skill:'alchemy_s8',cats:['bomb'],what:'bombs per slot',note:true},
 {skill:'alchemy_s12',cats:['oil'],what:'a poison chance from the oil'},
 {skill:'alchemy_s5',cats:['oil'],what:'protection against the oil\'s monster type'},
 {skill:'alchemy_s27',cats:['oil'],what:'critical damage against the oil\'s monster type'},
 {mut:12,cats:['decoction'],what:'random decoctions at no Toxicity'},
 {mut:10,cats:['potion','decoction'],what:'damage by Toxicity'},
 {mut:4,cats:['potion','decoction'],what:'damage by Toxicity'}];
const CN_EFF_NOTE='In-game text: +1 bomb per slot for each rank. The game\'s scripts only add it to the number of bombs a recipe makes (alchemyManager.ws:234).';
function cnEquippedSkill(id){let ti=-1,i=-1;TREES.forEach((t,a)=>t.sk.forEach((s,b)=>{if(s.id===id){ti=a;i=b}}));if(ti<0||!S.lv[ti][i])return null;
 return S.slots.some(x=>x&&x[0]===ti&&x[1]===i)?TREES[ti].sk[i]:null}   // a skill works when it has points and sits in a skill slot
const cnMutActive=n=>{const i=MUT.findIndex(m=>m.n===n);return i>=0&&S.mact===i&&!!S.mres[i]?MUT[i]:null};
function cnAffected(it){const out=[];
 CN_MODS.forEach(m=>{if(!m.cats.includes(it.cat))return;const s=m.skill?cnEquippedSkill(m.skill):cnMutActive(m.mut);if(s)out.push({name:s.name,what:m.what,note:m.note?CN_EFF_NOTE:'',mut:!!m.mut})});return out}

// ---- tooltip / stats text ----
const cnNum=(v,pct)=>pct?'+'+Math.round(v*100)+' %':(Array.isArray(v)?v[0]+' to '+v[1]:String(v));
function cnTipLines(it,withAff){const v=cnView(it),o=[];
 if(it.tox!=null)o.push(['Toxicity',String(it.tox)]);
 if(it.tox_offset!=null)o.push(['Toxicity offset',String(it.tox_offset)]);
 if(it.dur!=null||v.dur!=null)o.push([it.cat==='bomb'?'Effect duration':'Duration',v.dur+' s']);
 if(v.ch!=null)o.push(['Charges',String(v.ch)]);
 v.stats.forEach(s=>o.push([s.label,cnNum(s.v,s.pct)]));
 if(it.cat==='oil')o.push(['Works on',it.steel&&it.silver?'steel and silver sword':'silver sword only']);
 return o}
function cnTip(it,withAff=true){const aff=withAff?cnAffected(it):[],tier=it.tier_name?' · '+it.tier_name:'';
 let h=`<div class="eqt"><div class="eqt-name" style="color:${CN_COL[it.cat]||'#e6dcc8'}">${eqEsc(it.name)}</div><div class="eqt-rar">${eqEsc(CN_CAT[it.cat]+tier)}</div>`;
 cnTipLines(it).forEach(l=>{h+=`<div class="eqt-line"><span>${eqEsc(l[0])}</span><b>${eqEsc(l[1])}</b></div>`});
 if(it.desc)h+=`<div class="eqt-meta">${eqEsc(it.desc)}</div>`;
 if(withAff)h+=aff.length?`<div class="eqt-aff"><b>Affected by:</b> ${aff.map(a=>eqEsc(a.name)+(a.mut?' (mutation)':'')).join(', ')}${aff.some(a=>a.note)?`<small>${eqEsc(CN_EFF_NOTE)}</small>`:''}</div>`:'<div class="eqt-aff dim">Affected by: nothing in this build</div>';
 return h+'</div>'}
function cnStatsHtml(it,label){const aff=cnAffected(it);
 return`<section class="eqitem"><h4 style="color:${CN_COL[it.cat]}">${eqEsc(it.name)}</h4><div class="eqim">${eqEsc(label||CN_CAT[it.cat])}${it.tier_name?' · '+eqEsc(it.tier_name):''}</div>
  <div class="eqgrid">${cnTipLines(it).map(l=>`<span>${eqEsc(l[0])}</span><b>${eqEsc(l[1])}</b>`).join('')}</div>${it.desc?`<p class="eqdesc">${eqEsc(it.desc)}</p>`:''}
  <p class="eqaff">${aff.length?`<b>Affected by:</b> ${aff.map(a=>eqEsc(a.name)+(a.mut?' (mutation)':'')).join(', ')}`:'<span class="dim">Affected by: nothing in this build</span>'}${aff.some(a=>a.note)?`<small>${eqEsc(CN_EFF_NOTE)}</small>`:''}</p></section>`}
