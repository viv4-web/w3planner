// ---- Equipment panel (always visible, right of the skills): slots, chooser, tooltip, set bonuses, ruleset switch, Equip set. The data (data/items.json and data/items_<ruleset>.json) is loaded by script tags right after the page has loaded, never inside index.html. ----
const EQ_URL={meta:/*@file:items*/,ng:/*@file:items_ng*/,ng_plus:/*@file:items_ng_plus*/};
const EQ_SLOTS=['steel','silver','crossbow','bolts','chest','gloves','trousers','boots','mask']; // the order of the g1 link segment: never change it, only append
// labels follow the game's inventory (panel_inventory_paperdoll_slotname_* where it has one; item_category_* otherwise)
const EQ_NAME={steel:'Steel sword',silver:'Silver sword',crossbow:'Crossbow',bolts:'Bolts',chest:'Chest armor',gloves:'Gloves',trousers:'Trousers',boots:'Boots',mask:'Mask'};
const EQ_WEAPONS=['steel','silver','crossbow','bolts'],EQ_ARMOUR=['chest','gloves','trousers','boots','mask'];
const EQ_QUAL={1:['Common','#a2a2a2'],2:['Masterwork','#2b7bff'],3:['Magic','#e1d401'],4:['Relic','#ca610c'],5:['Witcher gear','#01b701']}; // GetItemRarityDescription
const EQ_RS={ng:'First playthrough',ng_plus:'New Game Plus'};
let EQ={meta:null,rs:{},err:null,pick:null,sig:''};
const eqEsc=t=>String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function eqScript(url){return new Promise((ok,no)=>{const e=document.createElement('script');e.src=url;e.onload=ok;e.onerror=()=>no(new Error('Could not load '+url));document.head.appendChild(e)})}
async function eqLoad(rs){
 if(!EQ.meta){if(!(window.W3DATA&&W3DATA.items))await eqScript(EQ_URL.meta);EQ.meta=W3DATA.items;EQ.disp=new Map(EQ.meta.stat_display.map(t=>[t.stat.toLowerCase(),t]))}
 if(!EQ.rs[rs]){const key='items_'+rs;if(!(window.W3DATA&&W3DATA[key]))await eqScript(EQ_URL[rs]);
  const items=W3DATA[key].items,byN=new Map(),byId=new Map(),bySlot={},first=new Map();
  items.forEach((it,k)=>{byN.set(it.n,it);byId.set(it.id,it);(bySlot[it.slot]=bySlot[it.slot]||[]).push(it);
   it.fk=it.set?it.set+'|'+it.slot+'|'+it.id.replace(/^NGP /,'').replace(/\s*\d+$/,'')+'|'+(it.legendary?'L':''):it.id;   // a family = one set, slot and variant (normal or Legendary): Wolven's normal tiers 1-4 are 'Wolf X', its Grandmaster 'NGP Wolf X 4'
   if(!first.has(it.fk))first.set(it.fk,k)});
  Object.values(bySlot).forEach(l=>l.sort((x,y)=>first.get(x.fk)-first.get(y.fk)||(x.tier||0)-(y.tier||0)||(x.id<y.id?-1:1)));   // the picker lists a family together, Basic to Grandmaster; families in the order of the data
  EQ.rs[rs]={items,byN,byId,bySlot}}
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
// The game blocks an item when GetItemLevel(item) > GetLevel() (HasRequiredLevelToEquipItem, r4Player.ws:11723). Only the Level field counts: bonus points, skill points and places of power never enter it.
const eqReq=it=>it.level_varies||it.required_level==null?null:it.required_level;
const eqLow=it=>{const r=eqReq(it);return r!=null&&r>lvl()};
function eqRange(it){const g=n=>{const e=(it.bonuses||[]).find(b=>b.stat===n);return e?e.min:null},a=g('item_level_min'),b=g('item_level_max');return S.rs==='ng'&&a!=null&&b!=null?' ('+a+' to '+b+')':''}   // autogen relics: the level is rolled when the item drops; only some carry the XML range, and in NG+ it moves with the NG+ level
function eqLevel(it){if(it.level_varies)return{t:'Level varies'+eqRange(it),bad:false};if(it.slot==='mask'||it.required_level==null)return null;return{t:'Requires level '+it.required_level,bad:eqLow(it)}}   // masks: the game's tooltip shows no level for them (guiTooltipComponent.ws:505)
function eqSetOf(it){return it.set&&EQ.meta?EQ.meta.sets[it.set]:null}
function eqTip(it){const q=EQ_QUAL[it.quality]||['',''],p=eqPrimary(it),lv=eqLevel(it),st=eqSetOf(it),lines=eqLines(it);
 let h=`<div class="eqt"><div class="eqt-name" style="color:${q[1]||'#e6dcc8'}">${eqEsc(it.name)}</div><div class="eqt-rar">${[q[0],it.armor_class?it.armor_class[0].toUpperCase()+it.armor_class.slice(1)+' armor':EQ_NAME[it.slot],it.quest?'Quest item':''].filter(Boolean).map(eqEsc).join(' · ')}</div>`;
 if(lv)h+=`<div class="eqt-lvl${lv.bad?' bad':''}">${lv.t}</div>`;
 if(p.label){const e=p.e;h+=`<div class="eqt-prim">${e?`<b>${eqVal({...e,percent:false})}</b> ${eqEsc(p.label)}${p.note?` <small>${eqEsc(p.note)}</small>`:''}`:it.autogen?`<span class="dim">${eqEsc(p.label)} varies with the item's level</span>`:''}</div>`}
 lines.forEach(e=>{h+=`<div class="eqt-line" style="color:${eqColor(e)}"><span>${eqEsc(e.label||e.stat)}</span><b>${eqEsc(eqVal(e))}</b></div>`});
 const meta=[];if(it.enhancement_slots)meta.push(it.enhancement_slots+' '+(it.enhancement_kind||'upgrade')+' slot'+(it.enhancement_slots>1?'s':''));if(it.weight)meta.push('Weight '+(Math.round(it.weight*100)/100));
 if(meta.length)h+=`<div class="eqt-meta">${eqEsc(meta.join(' · '))}</div>`;
 if(st){h+=`<div class="eqt-set"><b>${eqEsc(st.name)}</b>${st.bonuses.length?(it.set_bonus_piece?' · counts toward the set bonus':' · does not count toward the set bonus'+(it.slot==='crossbow'||it.slot==='bolts'?': '+eqWhy(it):' in '+EQ_RS[S.rs]+' (no set bonus tag in the game data)')):' · no set bonus'}</div>`}
 return h+'</div>'}

// ---- sets: pieces counted by the SetBonusPiece rule, bonuses at 3 and 6 ----
// The game counts every equipped item that carries the SetBonusPiece tag, whatever its slot (UpdateItemSetBonuses, playerWitcher.ws:10972-10987; tag name gameParams.ws:345). So the reason an item is not
// counted is read from the data: no tag on any item of its kind (the set crossbows), none on any piece of its slot, or only some tiers carry it (NG: Grandmaster only).
function eqWhy(it){const d=eqData(),sib=((d&&d.bySlot[it.slot])||[]).filter(x=>x.set===it.set),tagged=sib.filter(x=>x.set_bonus_piece);
 if(it.slot==='crossbow'||it.slot==='bolts')return'crossbows and bolts carry no set bonus tag in the game data, so they never count';
 if(!tagged.length)return'no '+EQ_NAME[it.slot].toLowerCase()+' of this set carries the set bonus tag';
 const tiers=[...new Set(tagged.map(x=>x.tier_name||'Basic'))];return'in '+EQ_RS[S.rs]+' only the '+tiers.join(', ')+(tiers.length>1?' tiers carry':' tier carries')+' the set bonus tag'}
function eqSets(){const d=eqData(),out=[];if(!d||!EQ.meta)return out;
 Object.keys(EQ.meta.sets).forEach(sid=>{const st=EQ.meta.sets[sid],mine=EQ_SLOTS.map((s,i)=>eqCur(i)).filter(it=>it&&it.set===sid);if(!mine.length)return;
  out.push({sid,st,n:mine.length,counted:mine.filter(it=>it.set_bonus_piece).length,skipped:mine.filter(it=>!it.set_bonus_piece)})});return out}
function eqSetHtml(x){const cur=b=>b.per_piece?String(Math.round(+b.per_piece*x.counted*100)/100):'';
 return`<section class="eqset"><h3>${eqEsc(x.st.name)} <small>${x.counted} counted, ${x.n} worn</small></h3>`+(x.st.bonuses.length?`<ul>`+x.st.bonuses.map(b=>{const on=x.counted>=b.pieces;return`<li class="${on?'lit':'dim'}"><b>${b.pieces} pieces${on?'':' (not active)'}</b> ${eqEsc(b.text.replace('{current}',cur(b)))}</li>`}).join('')+`</ul>`:`<p class="dim">This set has no set bonus.</p>`)+
  x.skipped.map(it=>`<p class="dim">${eqEsc(it.name)} is not counted: ${eqEsc(eqWhy(it))}.</p>`).join('')+`</section>`}

// ---- the equipment screen ----
function eqSlotHtml(slot){const i=EQ_SLOTS.indexOf(slot),it=eqCur(i),low=it&&eqLow(it),q=it&&EQ_QUAL[it.quality]?EQ_QUAL[it.quality][1]:'#6b5a42',sq=['bolts','mask'].includes(slot);
 return`<div class="eqslot${it?' on':''}${sq?' sq':''}${low?' low':''}" data-i="${i}"><button type="button" class="eqtile" data-i="${i}" style="--q:${q}" aria-haspopup="dialog" aria-label="${EQ_NAME[slot]}: ${it?eqEsc(it.name):'empty'}${low?'. Level too low, requires level '+eqReq(it):''}. Open the chooser${it?'. Press Delete to unequip':''}">${it&&it.icon?`<img src="${it.icon}" alt="">`:`<span class="eqempty">${EQ_NAME[slot]}</span>`}${low?'<i class="eqbadge">Level too low</i>':''}</button>
  <div class="eqsl"><b>${EQ_NAME[slot]}</b><span>${it?eqEsc(it.name):'Empty'}</span></div>${it?`<button type="button" class="eqx" data-i="${i}" aria-label="Unequip ${eqEsc(it.name)}">×</button>`:''}</div>`}
const eqLater='<div class="eqstrip" aria-disabled="true">Consumables &amp; bombs, coming later</div>';
function eqItemStats(it){const q=EQ_QUAL[it.quality]||['',''],p=eqPrimary(it),lv=eqLevel(it);
 return`<section class="eqitem"><h4 style="color:${q[1]||'#e6dcc8'}">${eqEsc(it.name)}</h4><div class="eqim">${eqEsc(EQ_NAME[it.slot])}${it.tier_name&&it.set?' · '+eqEsc(it.tier_name):''}${lv?` · <span class="${lv.bad?'bad':''}">${lv.t}</span>`:''}</div>
  <div class="eqgrid">${p.label&&p.e?`<span>${eqEsc(p.label)}</span><b>${eqVal({...p.e,percent:false})}</b>`:''}${eqLines(it).map(e=>`<span style="color:${eqColor(e)}">${eqEsc(e.label||e.stat)}</span><b style="color:${eqColor(e)}">${eqEsc(eqVal(e))}</b>`).join('')}</div></section>`}
function eqRender(force){const body=document.getElementById('eqbody');if(!body)return;
 const sig=[S.rs,S.gear.join(),lvl(),!!eqData(),EQ.err].join('|');if(!force&&sig===EQ.sig)return;EQ.sig=sig;document.getElementById('eqlvl').textContent=lvl();
 document.querySelectorAll('#eqpanel .eqrs [data-rs]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.rs===S.rs)));
 const keep=document.activeElement&&body.contains(document.activeElement)?document.activeElement.dataset.i:null,had=!!(document.activeElement&&document.activeElement.classList&&document.activeElement.classList.contains('eqtile'));
 const weapons=`<section class="eqsec eqw"><h3>Weapons</h3><div class="eqslots">${EQ_WEAPONS.map(eqSlotHtml).join('')}</div>${eqLater}</section>`,armour=`<section class="eqsec eqarm"><h3>Armor</h3><div class="eqslots">${EQ_ARMOUR.map(eqSlotHtml).join('')}</div></section>`;
 let rest;
 if(EQ.err)rest=`<p class="eqmsg">Could not load the equipment data: ${eqEsc(EQ.err)}. <button class="btn" id="eqretry" type="button">Try again</button></p>`;
 else if(!eqData())rest='<p class="eqmsg">Loading equipment data…</p>';
 else{const sets=eqSets(),items=EQ_SLOTS.map((s,i)=>eqCur(i)).filter(Boolean);
  rest=`<section class="eqsec"><h3>Sets</h3>${sets.length?sets.map(eqSetHtml).join(''):'<p class="dim">No set pieces equipped. Pieces of one witcher school or other set unlock bonuses at 3 and 6 pieces.</p>'}</section>
   <section class="eqsec"><h3>Item stats <small>listed, not added up</small></h3>${items.length?items.map(eqItemStats).join(''):'<p class="dim">Equip an item to see its numbers here.</p>'}</section>`}
 const lows=eqData()?EQ_SLOTS.map((s,i)=>[s,eqCur(i)]).filter(x=>x[1]&&eqLow(x[1])):[],warn=lows.length?`<p class="eqwarn" role="status"><b>Level too low</b> for ${lows.map(x=>EQ_NAME[x[0]].toLowerCase()+' (level '+eqReq(x[1])+')').join(', ')}. The gear stays in the link; raise Level to use it.</p>`:'';
 body.innerHTML=warn+`<div class="eqcols"><div class="eqc1">${weapons}</div><div class="eqc2">${armour}</div><div class="eqc3">${rest}</div></div>`;
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
function eqCands(slot){const d=eqData();return d?d.bySlot[slot]||[]:[]}
function eqFilterOpts(slot){const sets=new Map();let relic=0,other=0;
 eqCands(slot).forEach(it=>{if(it.set)sets.set(it.set,EQ.meta.sets[it.set].name);else if(it.group==='relic')relic++;else other++});
 const o=[['all','All items']];Object.keys(EQ.meta.sets).forEach(s=>{if(sets.has(s))o.push(['set:'+s,sets.get(s)+' set'])});if(relic)o.push(['relic','Relics']);if(other)o.push(['other',slot==='mask'?'Masks':slot==='bolts'?'Bolts':slot==='crossbow'?'Crossbows':'Other']);return o}
const EQ_TIERS=['Basic','Enhanced','Superior','Mastercrafted','Grandmaster'];
// Search: every word must be found in the item's name, tier name or id ("enhanced griffin" finds the Enhanced Griffin card only).
const eqHit=(it,w)=>{const t=(it.name+' '+(it.tier_name||'')+' '+it.id).toLowerCase();return w.every(k=>t.includes(k))};
function eqShown(){const p=EQ.pick,w=p.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
 return eqCands(p.slot).filter(it=>(p.filter==='all'||(p.filter==='relic'?it.group==='relic'&&!it.set:p.filter==='other'?!it.set&&it.group!=='relic':p.filter==='set:'+it.set))&&(p.tier==='all'||it.tier_name===p.tier)&&eqHit(it,w))}   // the tier filter applies to tiered items (those of a set); a relic has no tier
function eqPick(i){const slot=EQ_SLOTS[i],cur=eqCur(i);EQ.pick={i,slot,filter:'all',tier:'all',q:'',sel:cur,opener:document.activeElement,scroll:true};   // the worn item is selected (and scrolled into view); with nothing worn nothing is
 const ov=document.getElementById('eqpick');
 ov.innerHTML=`<div class="mmodal eqpmodal"><div class="mh"><h2 id="pktitle">${eqEsc(EQ_NAME[slot])}</h2><label>Show <select id="pkset"></select></label><label>Tier <select id="pktier"><option value="all">All tiers</option>${EQ_TIERS.map(t=>`<option>${t}</option>`).join('')}</select></label><input id="pkq" type="search" placeholder="Search by name" aria-label="Search by name" autocomplete="off"><span class="dim" id="pkcount" aria-live="polite"></span><button class="btn" id="pkclose" type="button">Close</button></div>
  <div class="pkbody"><div class="pkgrid" id="pkgrid" role="listbox" aria-label="${eqEsc(EQ_NAME[slot])} items"></div><div class="pkside" id="pkside"></div></div></div>`;
 ov.hidden=false;const sel=document.getElementById('pkset');sel.innerHTML=eqFilterOpts(slot).map(o=>`<option value="${eqEsc(o[0])}">${eqEsc(o[1])}</option>`).join('');
 sel.onchange=()=>{EQ.pick.filter=sel.value;eqPickRender()};document.getElementById('pktier').onchange=e=>{EQ.pick.tier=e.target.value;eqPickRender()};document.getElementById('pkq').oninput=e=>{EQ.pick.q=e.target.value;eqPickRender()};document.getElementById('pkclose').onclick=()=>eqClosePick();
 ov.onclick=e=>{if(e.target===ov)eqClosePick()};eqPickRender();document.getElementById('pkq').focus()}
function eqPickRender(){const p=EQ.pick;if(!p)return;const list=eqShown(),grid=document.getElementById('pkgrid');
 if(p.sel&&!list.includes(p.sel))p.sel=null;   // a filter or search that hides the selected card clears the selection; nothing else is picked for you
 document.getElementById('pkcount').textContent=list.length+' item'+(list.length===1?'':'s');
 grid.innerHTML=list.length?list.map(it=>{const q=EQ_QUAL[it.quality]?EQ_QUAL[it.quality][1]:'#6b5a42',on=it===p.sel,eq=it===eqCur(p.i);
  return`<button type="button" class="pktile${on?' sel':''}${eq?' worn':''}${eqLow(it)?' low':''}" role="option" aria-selected="${on}" data-id="${eqEsc(it.id)}" style="--q:${q}" title="${eqEsc(it.name)}">${it.icon?`<img src="${it.icon}" alt="" loading="lazy">`:''}<span>${eqEsc(it.name)}</span>${it.set&&it.tier_name?`<small class="pktr">${eqEsc(it.tier_name)}</small>`:''}${eqLow(it)?`<small class="pkreq">Level ${eqReq(it)}</small>`:''}${eq?'<em>worn</em>':''}</button>`}).join(''):'<p class="eqmsg">Nothing matches.</p>';
 const side=document.getElementById('pkside'),d=eqData(),it=p.sel;
 const lock=it&&eqLow(it),pl=it&&it.set?eqSetPlan(it):null,noset=pl&&!pl.pieces.length;
 side.innerHTML=it?`${eqTip(it)}<div class="pkact"><button class="btn" id="pkequip" type="button"${lock?' disabled aria-describedby="pkwhy"':''}>${eqCur(p.i)===it?'Equipped':'Equip'}</button>${it.set?`<button class="btn" id="pkequipset" type="button"${noset?' disabled aria-describedby="pkwhy"':''}>Equip set</button>`:''}${eqCur(p.i)?'<button class="btn" id="pkunequip" type="button">Unequip</button>':''}</div>${lock||noset?`<p class="pknote bad" id="pkwhy">${lock?'Requires level '+eqReq(it):'No piece of this set can be equipped at level '+lvl()}</p>`:''}${it.set?eqSetNote(it):''}`:'<p class="eqmsg">Select an item to see it here.</p>';
 grid.querySelectorAll('.pktile').forEach(b=>{b.onclick=()=>{p.sel=d.byId.get(b.dataset.id);eqPickRender();const n=document.querySelector('#pkgrid [data-id="'+p.sel.id+'"]');if(n)n.focus()};b.ondblclick=()=>eqEquip(d.byId.get(b.dataset.id));
  b.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();const x=d.byId.get(b.dataset.id);if(e.shiftKey&&x.set)eqEquipSet(x);else eqEquip(x)}else eqGridKey(e,b)}});   // Shift+Enter equips the whole set, like the Equip set button
 if(p.scroll){p.scroll=false;const n=grid.querySelector('.pktile.sel');if(n)n.scrollIntoView({block:'center'})}
 const eb=document.getElementById('pkequip');if(eb)eb.onclick=()=>eqEquip(it);const sb=document.getElementById('pkequipset');if(sb)sb.onclick=()=>eqEquipSet(it);const ub=document.getElementById('pkunequip');if(ub)ub.onclick=()=>{const i=p.i;eqClosePick(true);eqUnequip(i)}}
function eqGridKey(e,b){const t=[...document.querySelectorAll('#pkgrid .pktile')],k=t.indexOf(b);let n=-1;
 if(e.key==='ArrowRight')n=k+1;else if(e.key==='ArrowLeft')n=k-1;else if(e.key==='ArrowDown'||e.key==='ArrowUp'){const dir=e.key==='ArrowDown'?1:-1;const x=b.offsetLeft;n=k;for(let j=k+dir;j>=0&&j<t.length;j+=dir){if(t[j].offsetTop!==b.offsetTop&&Math.abs(t[j].offsetLeft-x)<4){n=j;break}}}
 if(n>=0&&n<t.length&&n!==k){e.preventDefault();t[n].focus();t[n].click();t[n].focus()}}
function eqEquip(it){const p=EQ.pick;if(!p||!it)return;if(eqLow(it)){notify('Requires level '+eqReq(it)+'.');return}S.gear[p.i]=it.n;const i=p.i;save();eqClosePick(true);eqRender(true);notify(it.name+' equipped.');const b=document.querySelector('#eqbody .eqtile[data-i="'+i+'"]');if(b)b.focus()}
// ---- Equip set: every piece of the selected item's set at the same tier and variant (NGP or not), into its slot ----
const eqWords=t=>t.toLowerCase().split(/[\s_]+/);
function eqSetPlan(it){const d=eqData();if(!d||!it||!it.set)return null;const ngp=x=>!!x.legendary,pieces=[],notes=[],skipped=[];   // the variant: normal or Legendary (in New Game Plus Wolven's lower tiers are the 'NGP' ids, its Grandmaster the plain id)
 const common=(a,b)=>{const A=eqWords(a),B=eqWords(b);let k=0;while(k<A.length&&k<B.length&&A[k]===B[k])k++;return k};
 EQ_SLOTS.forEach((slot,i)=>{const all=(d.bySlot[slot]||[]).filter(x=>x.set===it.set),same=all.filter(x=>ngp(x)===ngp(it)),c=same.length?same:all;if(!c.length)return;   // a slot with no piece of the same variant (the set crossbows) takes what the set has
  
  let best=null,bs=1e12;c.forEach(x=>{const sc=(x===it?-1e9:0)+Math.abs((x.tier||1)-(it.tier||1))*1000+(((x.tier||1)>(it.tier||1))?1:0)-common(x.id,it.id)*10;if(sc<bs){bs=sc;best=x}});   // exact item first, then the nearest tier (lower on a tie), then the same family of ids (q702 vs q704, EP1 vs base)
  if(eqLow(best)){skipped.push({slot,item:best});return}   // only what the current Level allows; the slot keeps what it has
  if((best.tier||1)!==(it.tier||1))notes.push(EQ_NAME[slot]+': '+(best.tier_name||'Basic')+' (there is no '+(it.tier_name||'Basic')+' one)');
  pieces.push({slot,i,item:best})});
 const sb=EQ.meta.sets[it.set],tagged=EQ_SLOTS.map(sl=>(d.bySlot[sl]||[]).filter(x=>x.set===it.set&&ngp(x)===ngp(it)&&x.set_bonus_piece&&x.slot!=='crossbow')).flat(),
  countTiers=[...new Set(tagged.sort((a,b)=>(a.tier||0)-(b.tier||0)).map(x=>x.tier_name||'Basic'))],
  uncounted=sb&&sb.bonuses.length?pieces.filter(x=>!x.item.set_bonus_piece&&x.slot!=='crossbow'&&x.slot!=='bolts'):[];   // what the set bonus would not count in this ruleset (the script counts only SetBonusPiece)
 return{pieces,notes,skipped,uncounted,countTiers}}
function eqNoCount(pl){if(!pl.uncounted.length)return'';return pl.uncounted.map(x=>EQ_NAME[x.slot].toLowerCase()).join(', ')+' will not count toward the set bonus in '+EQ_RS[S.rs]+' (no set bonus tag in the game data); '+(pl.countTiers.length?'only the '+pl.countTiers.join(', ')+(pl.countTiers.length>1?' tiers count':' tier counts')+'.':'no tier of this set counts there.')}
function eqSetNote(it){const pl=eqSetPlan(it);if(!pl)return'';const sk=pl.skipped.length?`<p class="pknote"><b>Skipped, level too low:</b> ${eqEsc(pl.skipped.map(x=>EQ_NAME[x.slot]+' (requires level '+eqReq(x.item)+')').join('; '))}.</p>`:'';if(!pl.pieces.length)return sk;return`<p class="pknote"><b>Equip set</b> puts ${pl.pieces.length} piece${pl.pieces.length===1?'':'s'} of ${eqEsc(EQ.meta.sets[it.set].name)} (${eqEsc(it.tier_name||'Basic')}) in ${pl.pieces.map(x=>EQ_NAME[x.slot].toLowerCase()).join(', ')}, replacing what is there.${pl.notes.length?` <b>Nearest tier used:</b> ${eqEsc(pl.notes.join('; '))}.`:''}</p>${pl.uncounted.length?`<p class="pknote"><b>Not counted:</b> ${eqEsc(eqNoCount(pl))}</p>`:''}${sk}`}
function eqEquipSet(it){const p=EQ.pick,pl=eqSetPlan(it);if(!p||!pl||!pl.pieces.length)return;pl.pieces.forEach(x=>{S.gear[x.i]=x.item.n});const i=p.i;save();eqClosePick(true);eqRender(true);   // one save(): the link changes once
 notify('Set equipped: '+pl.pieces.length+' pieces of '+EQ.meta.sets[it.set].name+'.'+(pl.notes.length?' Nearest tier used for '+pl.notes.join('; ')+'.':'')+(pl.uncounted.length?' '+eqNoCount(pl).replace(/^./,c=>c.toUpperCase())+(/\.$/.test(eqNoCount(pl))?'':'.'):'')+(pl.skipped.length?' Skipped, level too low: '+pl.skipped.map(x=>EQ_NAME[x.slot].toLowerCase()+' (level '+eqReq(x.item)+')').join(', ')+'.':''));const b=document.querySelector('#eqbody .eqtile[data-i="'+i+'"]');if(b)b.focus()}
function eqClosePick(quiet){const ov=document.getElementById('eqpick'),p=EQ.pick;EQ.pick=null;ov.hidden=true;ov.innerHTML='';if(!quiet&&p&&p.opener&&p.opener.focus)p.opener.focus()}
document.getElementById('eqbtn').onclick=eqFocusPanel;
document.querySelectorAll('#eqpanel .eqrs [data-rs]').forEach(b=>{b.onclick=()=>eqSwitch(b.dataset.rs);b.onkeydown=e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const o=b.dataset.rs==='ng'?'ng_plus':'ng';eqSwitch(o);const n=document.querySelector('#eqpanel .eqrs [data-rs="'+o+'"]');if(n)n.focus()}}});
document.addEventListener('keydown',e=>{if(!EQ.pick)return;
 if(e.key==='Escape'){e.preventDefault();eqClosePick();return}
 if(e.key==='Tab'){const f=[...document.getElementById('eqpick').querySelectorAll('button:not([disabled]),input,select,[tabindex="0"]')].filter(x=>x.offsetParent!==null);if(!f.length)return;
  if(e.shiftKey&&document.activeElement===f[0]){e.preventDefault();f[f.length-1].focus()}else if(!e.shiftKey&&document.activeElement===f[f.length-1]){e.preventDefault();f[0].focus()}}});
function eqRefresh(){if(eqData())eqValidate();eqRender(true)}
if(document.readyState==='complete')setTimeout(eqStart,0);else window.addEventListener('load',()=>setTimeout(eqStart,0));
