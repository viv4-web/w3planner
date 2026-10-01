// ---- Equipment panel (always visible, right of the skills): slots, chooser, tooltip, set bonuses, ruleset switch, Equip set. The data (data/items.json and data/items_<ruleset>.json) is loaded by script tags right after the page has loaded, never inside index.html. ----
const EQ_URL={meta:/*@file:items*/,ng:/*@file:items_ng*/,ng_plus:/*@file:items_ng_plus*/};
const EQ_SLOTS=['steel','silver','crossbow','bolts','chest','gloves','trousers','boots','mask']; // the order of the g1 link segment: never change it, only append
const EQ_NAME={steel:'Steel sword',silver:'Silver sword',crossbow:'Crossbow',bolts:'Bolts',chest:'Armor',gloves:'Gauntlets',trousers:'Trousers',boots:'Boots',mask:'Mask'};
const EQ_WEAPONS=['steel','silver','bolts','crossbow'],EQ_ARMOUR=['chest','gloves','trousers','boots','mask'];
const EQ_QUAL={1:['Common','#a2a2a2'],2:['Masterwork','#2b7bff'],3:['Magic','#e1d401'],4:['Relic','#ca610c'],5:['Witcher gear','#01b701']}; // GetItemRarityDescription
const EQ_RS={ng:'First playthrough',ng_plus:'New Game Plus'};
let EQ={meta:null,rs:{},err:null,pick:null,sig:''};
const eqEsc=t=>String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function eqScript(url){return new Promise((ok,no)=>{const e=document.createElement('script');e.src=url;e.onload=ok;e.onerror=()=>no(new Error('Could not load '+url));document.head.appendChild(e)})}
async function eqLoad(rs){
 if(!EQ.meta){if(!(window.W3DATA&&W3DATA.items))await eqScript(EQ_URL.meta);EQ.meta=W3DATA.items;EQ.disp=new Map(EQ.meta.stat_display.map(t=>[t.stat.toLowerCase(),t]))}
 if(!EQ.rs[rs]){const key='items_'+rs;if(!(window.W3DATA&&W3DATA[key]))await eqScript(EQ_URL[rs]);
  const items=W3DATA[key].items,byN=new Map(),byId=new Map(),bySlot={},chains=new Map();
  items.forEach(it=>{byN.set(it.n,it);byId.set(it.id,it);(bySlot[it.slot]=bySlot[it.slot]||[]).push(it);
   const k=it.set?it.set+'|'+it.slot+'|'+it.id.replace(/\s*\d+$/,''):it.id;(chains.get(k)||chains.set(k,[]).get(k)).push(it)});
  chains.forEach(c=>{c.sort((a,b)=>(a.tier||0)-(b.tier||0)||(a.id<b.id?-1:1));c.forEach(it=>{it.ch=c})});
  EQ.rs[rs]={items,byN,byId,bySlot,chains:[...chains.values()]}}
 return EQ.rs[rs]}
const eqData=()=>EQ.rs[S.rs]||null;
const eqCur=i=>{const d=eqData();return d&&S.gear[i]?d.byN.get(S.gear[i])||null:null};
function eqValidate(){const d=eqData();let bad=0;EQ_SLOTS.forEach((s,i)=>{const n=S.gear[i];if(!n)return;const it=d.byN.get(n);if(!it||it.slot!==s){S.gear[i]=0;bad++}});return bad}

// ---- what the game shows: primary stat, stat lines (gameplay/globals/tooltip_settings.csv), level, rarity ----
function eqPrimary(it){const b=(it.base||[]),f=n=>b.find(e=>e.stat===n&&e.type==='base')||b.find(e=>e.stat===n); // the game takes the base value, else the multiplicative, else the additive one (GetItemPrimaryStat)
 if(it.slot==='steel')return{label:'Damage',e:f('SlashingDamage')};
 if(it.slot==='silver')return{label:'Damage',e:f('SilverDamage')};
 if(['chest','gloves','trousers','boots'].includes(it.slot))return{label:'Armor',e:f('armor')};
 if(it.slot==='bolts'){const e=['FireDamage','PiercingDamage','PoisonDamage','BludgeoningDamage','PhysicalDamage'].map(f).find(Boolean);return{label:e?(e.label||'Damage'):'Damage',e}}
 if(it.slot==='crossbow'){const m=(it.bonuses||[]).find(e=>e.stat==='attack_power'&&e.type==='mult'),d=eqData(),bolt=eqCur(3)||(d&&d.byId.get('Bodkin Bolt')),be=bolt&&eqPrimary(bolt).e;
  return{label:'Damage',e:m&&be?{min:be.min*m.min,max:be.max!==undefined?be.max*m.min:undefined,stat:'x'}:null,note:bolt?'with '+bolt.name:''}}
 return{label:'',e:null}}
function eqNum(e,v){return e.percent?Math.round(v*100)+' %':String(Math.round(v))}
function eqVal(e){if(e.effect)return'';const r=e.max!==undefined&&e.max!==e.min;return r?eqNum(e,e.min)+' to '+eqNum(e,e.max):eqNum(e,e.min)}
function eqLines(it){const skip=it.slot==='steel'?'SilverDamage':it.slot==='silver'?'SlashingDamage':'',p=eqPrimary(it).e;
 return[...(it.base||[]),...(it.bonuses||[])].filter(e=>e.line!==undefined&&e.stat!==skip&&e!==p).sort((a,b)=>a.line-b.line)}
const eqColor=e=>{const t=EQ.disp&&EQ.disp.get(String(e.stat).toLowerCase());return t&&t.color?'#'+t.color:'#BAADA0'};
function eqLevel(it){if(it.level_varies)return{t:'Level varies',bad:false};if(it.required_level==null)return null;return{t:'Requires level '+it.required_level,bad:it.required_level>lvl()}}
function eqSetOf(it){return it.set&&EQ.meta?EQ.meta.sets[it.set]:null}
function eqTip(it,withTiers){const q=EQ_QUAL[it.quality]||['',''],p=eqPrimary(it),lv=eqLevel(it),st=eqSetOf(it),lines=eqLines(it);
 let h=`<div class="eqt"><div class="eqt-name" style="color:${q[1]||'#e6dcc8'}">${eqEsc(it.name)}</div><div class="eqt-rar">${[q[0],it.armor_class?it.armor_class[0].toUpperCase()+it.armor_class.slice(1)+' armor':EQ_NAME[it.slot],it.quest?'Quest item':''].filter(Boolean).map(eqEsc).join(' · ')}</div>`;
 if(withTiers&&it.ch&&it.ch.length>1)h+=`<div class="eqt-tiers" role="group" aria-label="Tier">${it.ch.map(x=>`<button type="button" class="btn eqchip" data-id="${eqEsc(x.id)}" aria-pressed="${x===it}">${eqEsc(x.tier_name||'Basic')}</button>`).join('')}</div>`;
 if(lv)h+=`<div class="eqt-lvl${lv.bad?' bad':''}">${lv.t}</div>`;
 if(p.label){const e=p.e;h+=`<div class="eqt-prim">${e?`<b>${eqVal({...e,percent:false})}</b> ${eqEsc(p.label)}${p.note?` <small>${eqEsc(p.note)}</small>`:''}`:it.autogen?`<span class="dim">${eqEsc(p.label)} varies with the item's level</span>`:''}</div>`}
 lines.forEach(e=>{h+=`<div class="eqt-line" style="color:${eqColor(e)}"><span>${eqEsc(e.label||e.stat)}</span><b>${eqEsc(eqVal(e))}</b></div>`});
 const meta=[];if(it.enhancement_slots)meta.push(it.enhancement_slots+' '+(it.enhancement_kind||'upgrade')+' slot'+(it.enhancement_slots>1?'s':''));if(it.weight)meta.push('Weight '+(Math.round(it.weight*100)/100));
 if(meta.length)h+=`<div class="eqt-meta">${eqEsc(meta.join(' · '))}</div>`;
 if(st){h+=`<div class="eqt-set"><b>${eqEsc(st.name)}</b>${st.bonuses.length?(it.set_bonus_piece?' · counts toward the set bonus':' · does not count toward the set bonus in this mode'):' · no set bonus'}</div>`}
 return h+'</div>'}

// ---- sets: pieces counted by the SetBonusPiece rule, bonuses at 3 and 6 ----
function eqSets(){const d=eqData(),out=[];if(!d||!EQ.meta)return out;
 Object.keys(EQ.meta.sets).forEach(sid=>{const st=EQ.meta.sets[sid],mine=EQ_SLOTS.map((s,i)=>eqCur(i)).filter(it=>it&&it.set===sid);if(!mine.length)return;
  out.push({sid,st,n:mine.length,counted:mine.filter(it=>it.set_bonus_piece).length})});return out}
function eqSetHtml(x){const cur=b=>b.per_piece?String(Math.round(+b.per_piece*x.counted*100)/100):'';
 return`<section class="eqset"><h3>${eqEsc(x.st.name)} <small>${x.counted} counted, ${x.n} worn</small></h3>`+(x.st.bonuses.length?`<ul>`+x.st.bonuses.map(b=>{const on=x.counted>=b.pieces;return`<li class="${on?'lit':'dim'}"><b>${b.pieces} pieces${on?'':' (not active)'}</b> ${eqEsc(b.text.replace('{current}',cur(b)))}</li>`}).join('')+`</ul>`:`<p class="dim">This set has no set bonus.</p>`)+
  (x.counted<x.n?`<p class="dim">${x.n-x.counted} worn piece${x.n-x.counted>1?'s do':' does'} not count: in this mode only some tiers carry the set bonus tag.</p>`:'')+`</section>`}

// ---- the equipment screen ----
function eqSlotHtml(slot){const i=EQ_SLOTS.indexOf(slot),it=eqCur(i),q=it&&EQ_QUAL[it.quality]?EQ_QUAL[it.quality][1]:'#6b5a42',sq=['bolts','mask'].includes(slot);
 return`<div class="eqslot${it?' on':''}${sq?' sq':''}" data-i="${i}"><button type="button" class="eqtile" data-i="${i}" style="--q:${q}" aria-haspopup="dialog" aria-label="${EQ_NAME[slot]}: ${it?eqEsc(it.name):'empty'}. Open the chooser${it?'. Press Delete to unequip':''}">${it&&it.icon?`<img src="${it.icon}" alt="">`:`<span class="eqempty">${EQ_NAME[slot]}</span>`}</button>
  <div class="eqsl"><b>${EQ_NAME[slot]}</b><span>${it?eqEsc(it.name):'Empty'}</span></div>${it?`<button type="button" class="eqx" data-i="${i}" aria-label="Unequip ${eqEsc(it.name)}">×</button>`:''}</div>`}
const eqLater=n=>`<div class="eqslot later" aria-disabled="true"><div class="eqtile" aria-hidden="true"><span class="eqempty">${n}</span></div><div class="eqsl"><b>${n}</b><span>Later phase</span></div></div>`;
function eqItemStats(it){const q=EQ_QUAL[it.quality]||['',''],p=eqPrimary(it),lv=eqLevel(it);
 return`<section class="eqitem"><h4 style="color:${q[1]||'#e6dcc8'}">${eqEsc(it.name)}</h4><div class="eqim">${eqEsc(EQ_NAME[it.slot])}${it.tier_name&&it.set?' · '+eqEsc(it.tier_name):''}${lv?` · <span class="${lv.bad?'bad':''}">${lv.t}</span>`:''}</div>
  <div class="eqgrid">${p.label&&p.e?`<span>${eqEsc(p.label)}</span><b>${eqVal({...p.e,percent:false})}</b>`:''}${eqLines(it).map(e=>`<span style="color:${eqColor(e)}">${eqEsc(e.label||e.stat)}</span><b style="color:${eqColor(e)}">${eqEsc(eqVal(e))}</b>`).join('')}</div></section>`}
function eqRender(force){const body=document.getElementById('eqbody');if(!body)return;
 const sig=[S.rs,S.gear.join(),lvl(),!!eqData(),EQ.err].join('|');if(!force&&sig===EQ.sig)return;EQ.sig=sig;document.getElementById('eqlvl').textContent=lvl();
 document.querySelectorAll('#eqpanel .eqrs [data-rs]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.rs===S.rs)));
 const keep=document.activeElement&&body.contains(document.activeElement)?document.activeElement.dataset.i:null,had=!!(document.activeElement&&document.activeElement.classList&&document.activeElement.classList.contains('eqtile'));
 const weapons=`<section class="eqsec"><h3>Weapons</h3><div class="eqslots">${EQ_WEAPONS.map(eqSlotHtml).join('')}${eqLater('Consumables')}${eqLater('Bombs')}</div></section>`,armour=`<section class="eqsec"><h3>Armor</h3><div class="eqslots">${EQ_ARMOUR.map(eqSlotHtml).join('')}</div></section>`;
 let rest;
 if(EQ.err)rest=`<p class="eqmsg">Could not load the equipment data: ${eqEsc(EQ.err)}. <button class="btn" id="eqretry" type="button">Try again</button></p>`;
 else if(!eqData())rest='<p class="eqmsg">Loading equipment data…</p>';
 else{const sets=eqSets(),items=EQ_SLOTS.map((s,i)=>eqCur(i)).filter(Boolean);
  rest=`<section class="eqsec"><h3>Sets</h3>${sets.length?sets.map(eqSetHtml).join(''):'<p class="dim">No set pieces equipped. Pieces of one witcher school or other set unlock bonuses at 3 and 6 pieces.</p>'}</section>
   <section class="eqsec"><h3>Item stats <small>listed, not added up</small></h3>${items.length?items.map(eqItemStats).join(''):'<p class="dim">Equip an item to see its numbers here.</p>'}</section>`}
 body.innerHTML=weapons+armour+rest;
 body.querySelectorAll('.eqtile[data-i]').forEach(b=>{const i=+b.dataset.i;b.onclick=()=>eqPick(i);b.oncontextmenu=e=>{e.preventDefault();eqUnequip(i)};
  b.onkeydown=e=>{if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();eqUnequip(i)}};
  const it=eqCur(i);if(it){b.onmouseenter=()=>eqHoverTip(it,b);b.onmouseleave=eqHideTip;b.onfocus=()=>eqHoverTip(it,b);b.onblur=eqHideTip}});
 body.querySelectorAll('.eqx').forEach(b=>{b.onclick=()=>eqUnequip(+b.dataset.i)});const rt=document.getElementById('eqretry');if(rt)rt.onclick=eqStart;
 if(had&&keep!=null){const n=body.querySelector('.eqtile[data-i="'+keep+'"]');if(n)n.focus({preventScroll:true})}}
function eqHoverTip(it,el){let t=document.getElementById('eqtip');if(!t){t=document.createElement('div');t.id='eqtip';t.className='eqtip';t.setAttribute('role','tooltip');document.body.appendChild(t)}
 t.innerHTML=eqTip(it,false);t.hidden=false;const r=el.getBoundingClientRect(),w=t.offsetWidth,h=t.offsetHeight;let x=r.right+10;if(x+w>innerWidth-8)x=Math.max(8,r.left-w-10);t.style.left=x+'px';t.style.top=Math.max(8,Math.min(r.top,innerHeight-h-8))+'px'}
function eqHideTip(){const t=document.getElementById('eqtip');if(t)t.hidden=true}
function eqUnequip(i){const it=eqCur(i);if(!it)return;S.gear[i]=0;save();eqRender(true);notify(it.name+' unequipped.');const b=document.querySelector('#eqbody .eqtile[data-i="'+i+'"]');if(b)b.focus()}
// load the data right after the page has loaded (never inside index.html, and not before the skill tree is up)
async function eqStart(){EQ.err=null;eqRender(true);
 try{await eqLoad(S.rs);const bad=eqValidate();if(bad){save();notify(bad+' equipped item'+(bad>1?'s':'')+' in this build '+(bad>1?'are':'is')+' not available in '+EQ_RS[S.rs]+' and '+(bad>1?'were':'was')+' removed.')}}catch(e){EQ.err=e.message}
 eqRender(true)}
function eqFocusPanel(){const p=document.getElementById('eqpanel');p.scrollIntoView({behavior:'smooth',block:'start'});const f=p.querySelector('.eqtile[data-i]');if(f)f.focus({preventScroll:true})}   // the Equipment button (shown only on narrow screens, where the panel is below the skills)
async function eqSwitch(rs){if(rs===S.rs)return;
 try{await eqLoad(rs)}catch(e){notify('Could not load the '+EQ_RS[rs]+' data: '+e.message);return}
 const nu=EQ.rs[rs],old=eqData(),dropped=[];let kept=0;
 EQ_SLOTS.forEach((s,i)=>{const n=S.gear[i];if(!n)return;const it=nu.byN.get(n);if(!it||it.slot!==s){dropped.push(old&&old.byN.get(n)?old.byN.get(n).name:'an item');S.gear[i]=0}else kept++});
 S.rs=rs;save();eqRender(true);
 notify('Switched to '+EQ_RS[rs]+'. '+(dropped.length?'Removed because they do not exist in this mode: '+dropped.join(', ')+'.':'')+(kept?(dropped.length?' ':'')+kept+' item'+(kept>1?'s':'')+' kept (same item in both modes; its numbers are the new mode\'s).':(dropped.length?'':'Nothing was equipped.')))}

// ---- the chooser ----
function eqCands(slot){const d=eqData();return d?d.chains.filter(c=>c[0].slot===slot):[]}
function eqFilterOpts(slot){const ch=eqCands(slot),sets=new Map();let relic=0,other=0;
 ch.forEach(c=>{const it=c[0];if(it.set)sets.set(it.set,EQ.meta.sets[it.set].name);else if(it.group==='relic')relic++;else other++});
 const o=[['all','All items']];Object.keys(EQ.meta.sets).forEach(s=>{if(sets.has(s))o.push(['set:'+s,sets.get(s)+' set'])});if(relic)o.push(['relic','Relics']);if(other)o.push(['other',slot==='mask'?'Masks':slot==='bolts'?'Bolts':slot==='crossbow'?'Crossbows':'Other']);return o}
function eqShown(){const p=EQ.pick;const q=p.q.trim().toLowerCase();
 return eqCands(p.slot).filter(c=>{const it=c[0];return p.filter==='all'||(p.filter==='relic'?it.group==='relic'&&!it.set:p.filter==='other'?!it.set&&it.group!=='relic':p.filter==='set:'+it.set)}).filter(c=>!q||c.some(x=>x.name.toLowerCase().includes(q)||x.id.toLowerCase().includes(q)))}
function eqPick(i){const slot=EQ_SLOTS[i],cur=eqCur(i);EQ.pick={i,slot,filter:'all',q:'',sel:cur,opener:document.activeElement};
 const ov=document.getElementById('eqpick');
 ov.innerHTML=`<div class="mmodal eqpmodal"><div class="mh"><h2 id="pktitle">${eqEsc(EQ_NAME[slot])}</h2><label>Show <select id="pkset"></select></label><input id="pkq" type="search" placeholder="Search by name" aria-label="Search by name" autocomplete="off"><span class="dim" id="pkcount" aria-live="polite"></span><button class="btn" id="pkclose" type="button">Close</button></div>
  <div class="pkbody"><div class="pkgrid" id="pkgrid" role="listbox" aria-label="${eqEsc(EQ_NAME[slot])} items"></div><div class="pkside" id="pkside"></div></div></div>`;
 ov.hidden=false;const sel=document.getElementById('pkset');sel.innerHTML=eqFilterOpts(slot).map(o=>`<option value="${eqEsc(o[0])}">${eqEsc(o[1])}</option>`).join('');
 sel.onchange=()=>{EQ.pick.filter=sel.value;eqPickRender()};document.getElementById('pkq').oninput=e=>{EQ.pick.q=e.target.value;eqPickRender()};document.getElementById('pkclose').onclick=()=>eqClosePick();
 ov.onclick=e=>{if(e.target===ov)eqClosePick()};eqPickRender();document.getElementById('pkq').focus()}
function eqPickRender(){const p=EQ.pick;if(!p)return;const list=eqShown(),grid=document.getElementById('pkgrid');
 if(p.sel&&!list.some(c=>c.includes(p.sel)))p.sel=null;if(!p.sel&&list.length)p.sel=eqCur(p.i)&&list.some(c=>c.includes(eqCur(p.i)))?eqCur(p.i):list[0][list[0].length-1];
 document.getElementById('pkcount').textContent=list.length+' item'+(list.length===1?'':'s');
 grid.innerHTML=list.length?list.map(c=>{const rep=p.sel&&c.includes(p.sel)?p.sel:c[c.length-1],q=EQ_QUAL[rep.quality]?EQ_QUAL[rep.quality][1]:'#6b5a42',on=c.includes(p.sel),eq=c.includes(eqCur(p.i));
  return`<button type="button" class="pktile${on?' sel':''}${eq?' worn':''}" role="option" aria-selected="${on}" data-id="${eqEsc(rep.id)}" style="--q:${q}" title="${eqEsc(rep.name)}">${rep.icon?`<img src="${rep.icon}" alt="" loading="lazy">`:''}<span>${eqEsc(rep.name)}</span>${c.length>1?`<i>${c.length} tiers</i>`:''}${eq?'<em>worn</em>':''}</button>`}).join(''):'<p class="eqmsg">Nothing matches.</p>';
 const side=document.getElementById('pkside'),d=eqData(),it=p.sel;
 side.innerHTML=it?`${eqTip(it,true)}<div class="pkact"><button class="btn" id="pkequip" type="button">${eqCur(p.i)===it?'Equipped':'Equip'}</button>${it.set?'<button class="btn" id="pkequipset" type="button">Equip set</button>':''}${eqCur(p.i)?'<button class="btn" id="pkunequip" type="button">Unequip</button>':''}</div>${it.set?eqSetNote(it):''}`:'<p class="eqmsg">Select an item to see it here.</p>';
 grid.querySelectorAll('.pktile').forEach(b=>{b.onclick=()=>{p.sel=d.byId.get(b.dataset.id);eqPickRender();const n=document.querySelector('#pkgrid [data-id="'+p.sel.id+'"]');if(n)n.focus()};b.ondblclick=()=>eqEquip(d.byId.get(b.dataset.id));
  b.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();const x=d.byId.get(b.dataset.id);if(e.shiftKey&&x.set)eqEquipSet(x);else eqEquip(x)}else eqGridKey(e,b)}});   // Shift+Enter equips the whole set, like the Equip set button
 side.querySelectorAll('.eqchip').forEach(b=>{b.onclick=()=>{p.sel=d.byId.get(b.dataset.id);eqPickRender();const n=document.querySelector('#pkside [data-id="'+p.sel.id+'"]');if(n)n.focus()}});
 const eb=document.getElementById('pkequip');if(eb)eb.onclick=()=>eqEquip(it);const sb=document.getElementById('pkequipset');if(sb)sb.onclick=()=>eqEquipSet(it);const ub=document.getElementById('pkunequip');if(ub)ub.onclick=()=>{const i=p.i;eqClosePick(true);eqUnequip(i)}}
function eqGridKey(e,b){const t=[...document.querySelectorAll('#pkgrid .pktile')],k=t.indexOf(b);let n=-1;
 if(e.key==='ArrowRight')n=k+1;else if(e.key==='ArrowLeft')n=k-1;else if(e.key==='ArrowDown'||e.key==='ArrowUp'){const dir=e.key==='ArrowDown'?1:-1;const x=b.offsetLeft;n=k;for(let j=k+dir;j>=0&&j<t.length;j+=dir){if(t[j].offsetTop!==b.offsetTop&&Math.abs(t[j].offsetLeft-x)<4){n=j;break}}}
 if(n>=0&&n<t.length&&n!==k){e.preventDefault();t[n].focus();t[n].click();t[n].focus()}}
function eqEquip(it){const p=EQ.pick;if(!p||!it)return;S.gear[p.i]=it.n;const i=p.i;save();eqClosePick(true);eqRender(true);notify(it.name+' equipped.');const b=document.querySelector('#eqbody .eqtile[data-i="'+i+'"]');if(b)b.focus()}
// ---- Equip set: every piece of the selected item's set at the same tier and variant (NGP or not), into its slot ----
const eqWords=t=>t.toLowerCase().split(/[\s_]+/);
function eqSetPlan(it){const d=eqData();if(!d||!it||!it.set)return null;const ngp=x=>x.id.startsWith('NGP '),pieces=[],notes=[];
 const common=(a,b)=>{const A=eqWords(a),B=eqWords(b);let k=0;while(k<A.length&&k<B.length&&A[k]===B[k])k++;return k};
 EQ_SLOTS.forEach((slot,i)=>{const c=(d.bySlot[slot]||[]).filter(x=>x.set===it.set&&ngp(x)===ngp(it));if(!c.length)return;
  let best=null,bs=1e12;c.forEach(x=>{const sc=(x===it?-1e9:0)+Math.abs((x.tier||1)-(it.tier||1))*1000+(((x.tier||1)>(it.tier||1))?1:0)-common(x.id,it.id)*10;if(sc<bs){bs=sc;best=x}});   // exact item first, then the nearest tier (lower on a tie), then the same family of ids (q702 vs q704, EP1 vs base)
  if((best.tier||1)!==(it.tier||1))notes.push(EQ_NAME[slot]+': '+(best.tier_name||'Basic')+' (there is no '+(it.tier_name||'Basic')+' one)');
  pieces.push({slot,i,item:best})});
 return{pieces,notes}}
function eqSetNote(it){const pl=eqSetPlan(it);if(!pl)return'';return`<p class="pknote"><b>Equip set</b> puts ${pl.pieces.length} piece${pl.pieces.length===1?'':'s'} of ${eqEsc(EQ.meta.sets[it.set].name)} (${eqEsc(it.tier_name||'Basic')}) in ${pl.pieces.map(x=>EQ_NAME[x.slot].toLowerCase()).join(', ')}, replacing what is there.${pl.notes.length?` <b>Nearest tier used:</b> ${eqEsc(pl.notes.join('; '))}.`:''}</p>`}
function eqEquipSet(it){const p=EQ.pick,pl=eqSetPlan(it);if(!p||!pl||!pl.pieces.length)return;pl.pieces.forEach(x=>{S.gear[x.i]=x.item.n});const i=p.i;save();eqClosePick(true);eqRender(true);   // one save(): the link changes once
 notify('Set equipped: '+pl.pieces.length+' pieces of '+EQ.meta.sets[it.set].name+'.'+(pl.notes.length?' Nearest tier used for '+pl.notes.join('; ')+'.':''));const b=document.querySelector('#eqbody .eqtile[data-i="'+i+'"]');if(b)b.focus()}
function eqClosePick(quiet){const ov=document.getElementById('eqpick'),p=EQ.pick;EQ.pick=null;ov.hidden=true;ov.innerHTML='';if(!quiet&&p&&p.opener&&p.opener.focus)p.opener.focus()}
document.getElementById('eqbtn').onclick=eqFocusPanel;
document.querySelectorAll('#eqpanel .eqrs [data-rs]').forEach(b=>{b.onclick=()=>eqSwitch(b.dataset.rs);b.onkeydown=e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const o=b.dataset.rs==='ng'?'ng_plus':'ng';eqSwitch(o);const n=document.querySelector('#eqpanel .eqrs [data-rs="'+o+'"]');if(n)n.focus()}}});
document.addEventListener('keydown',e=>{if(!EQ.pick)return;
 if(e.key==='Escape'){e.preventDefault();eqClosePick();return}
 if(e.key==='Tab'){const f=[...document.getElementById('eqpick').querySelectorAll('button:not([disabled]),input,select,[tabindex="0"]')].filter(x=>x.offsetParent!==null);if(!f.length)return;
  if(e.shiftKey&&document.activeElement===f[0]){e.preventDefault();f[f.length-1].focus()}else if(!e.shiftKey&&document.activeElement===f[f.length-1]){e.preventDefault();f[0].focus()}}});
function eqRefresh(){if(eqData())eqValidate();eqRender(true)}
if(document.readyState==='complete')setTimeout(eqStart,0);else window.addEventListener('load',()=>setTimeout(eqStart,0));
