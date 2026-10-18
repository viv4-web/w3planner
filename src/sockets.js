// ---- Runes and glyphs in sockets (v36): data/socket_ids.json (61 entries, loaded with the equipment lists by a script tag, never inside index.html) ----
// Which gear takes which: swords take runes, the four armour pieces take glyphs (enhancement_kind in items_<ruleset>.json, from the item XML). How many: the item's enhancement_slots in the chosen ruleset
// (1 on a Griffin sword in the first playthrough, 3 in New Game Plus). The crossbow, bolts and mask have none. S.sock holds 6 slots x 4 sockets of registry numbers (0 = empty), written to the link as r1.
// What the game does with a socketed item: the rune's or glyph's ability (<name> _Stats) is added to the sword or armour piece (the save keeps it in the item's socket list, docs/IMPORT.md "Sockets").
const SK_URL=/*@file:socket_ids*/;
const SK_SLOTS=['steel','silver','chest','gloves','trousers','boots'];   // the order of the r1 link segment: never change it, only append
const SK_MAX=4,SK_COL={rune:'#e08a2a',glyph:'#4f9be0'},SK_TABS=[['lesser','Lesser'],['normal','Normal'],['greater','Greater'],['other','Other']];
let SK={data:null,byN:new Map(),byId:new Map(),pick:null};
async function skLoad(){if(SK.data)return SK;
 if(!(window.W3DATA&&W3DATA.socket_ids))await eqScript(SK_URL);
 const d=W3DATA.socket_ids;SK.data=d;SK.byN=new Map();SK.byId=new Map();d.items.forEach(r=>{SK.byN.set(r.n,r);SK.byId.set(r.id,r)});return SK}
const skKind=slot=>slot==='steel'||slot==='silver'?'rune':'glyph';
const skCap=it=>it&&SK_SLOTS.includes(it.slot)?Math.min(SK_MAX,it.enhancement_slots||0):0;
const skCur=slot=>eqCur(EQ_SLOTS.indexOf(slot));
const skAt=(slot,j)=>{const n=S.sock[SK_SLOTS.indexOf(slot)*SK_MAX+j];return n&&SK.data?SK.byN.get(n)||null:null};
// the one rule that says whether a rune or glyph fits a slot (a unit test calls it directly)
const skFits=(slot,r)=>!!r&&SK_SLOTS.includes(slot)&&r.kind===skKind(slot)&&(!r.only||r.only===S.rs);
// Keeps what fits: a rune or glyph stays when its slot holds an item with room for it and it is the right kind; the rest is removed. While every filled socket is still inside the item's room, nothing moves
// (an open socket between two filled ones stays open); when the item has fewer sockets than before, the filled ones move up and the last ones that do not fit are removed.
// Returns [{slot, name, why}] for what was removed (the caller says so with notify); nothing happens until both data files are loaded.
function skFit(){const out=[];if(!SK.data||!eqData())return out;
 SK_SLOTS.forEach((slot,si)=>{const it=skCur(slot),cap=skCap(it),base=si*SK_MAX,valid=[];
  for(let j=0;j<SK_MAX;j++){const n=S.sock[base+j];if(!n)continue;const r=SK.byN.get(n);
   if(!r){out.push({slot,name:'an unknown rune or glyph',why:'not in this version'});continue}
   if(!skFits(slot,r)){out.push({slot,name:r.name,why:r.kind==='rune'?'runes only fit swords':'glyphs only fit armor'});continue}
   valid.push([j,n,r])}
  const room=valid.every(v=>v[0]<cap),kept=room?valid:valid.slice(0,cap);
  valid.slice(room?valid.length:cap).forEach(v=>out.push({slot,name:v[2].name,why:it?(it.name+' has '+(cap===0?'no sockets':cap+' socket'+(cap>1?'s':''))+' in '+EQ_RS[S.rs]):'no '+EQ_NAME[slot].toLowerCase()+' is equipped'}));
  for(let j=0;j<SK_MAX;j++)S.sock[base+j]=0;kept.forEach((v,k)=>{S.sock[base+(room?v[0]:k)]=v[1]})});
 return out}
const skRemovedText=rm=>rm.length?'Removed from sockets: '+rm.map(x=>x.name+' ('+x.why+')').join('; ')+'.':'';

// ---- what a socketed item gives ----
const skFx=r=>(S.rs==='ng_plus'&&r.fxp)||r.fx;
const skShown=r=>skFx(r).filter(e=>SK.data.labels[e[0]]);   // a stat the game does not list (tooltip_settings.csv has no row; no attribute_name_ label) is kept in the data and not shown
const skNum=(e,v)=>{const d=EQ.disp&&EQ.disp.get(e[0].toLowerCase()),pct=e[1]==='mult'||(d?d.percent:/chance|resist|power|indestructible|focus/.test(e[0]));   // a multiplicative value is a percentage (the game's tooltip rule, CLAUDE.md)
 return(v<0?'':'+')+(pct?Math.round(v*100)+' %':String(Math.round(v)))};
const skVal=e=>Array.isArray(e[2])?skNum(e,e[2][0])+' to '+skNum(e,e[2][1]).replace(/^\+/,''):skNum(e,e[2]);
const skLab=e=>SK.data.labels[e[0]];
// sum of one stat over the sockets of one worn sword or armour piece: {v: lowest, hi: highest}; src lists the rune and glyph names that contribute
function skStat(slot,name){let v=0,hi=0;if(!SK.data||!SK_SLOTS.includes(slot))return{v,hi,src:[]};const src=[];
 for(let j=0;j<SK_MAX;j++){const r=skAt(slot,j);if(!r)continue;skFx(r).forEach(e=>{if(e[0]===name){v+=Array.isArray(e[2])?e[2][0]:e[2];hi+=Array.isArray(e[2])?e[2][1]:e[2];src.push(r.name)}})}
 return{v,hi,src}}
const skCount=slot=>{let n=0;for(let j=0;j<SK_MAX;j++)if(S.sock[SK_SLOTS.indexOf(slot)*SK_MAX+j])n++;return n};

// ---- icons: the game's picture, or a plain lettered disc where the server has none (the 12 Hearts of Stone glyphs, Pyerog, Tvarog) ----
const skDisc=r=>r.icon?`<img class="skic" src="${r.icon}" alt="">`:`<span class="skic skletter ${r.kind}" aria-hidden="true">${eqEsc(r.fam[0].toUpperCase())}</span>`;

// ---- the discs: top-left of a slot tile, and the Sockets row of the item card. filled orange = rune, filled blue = glyph, hollow = empty ----
function skDiscs(slot,u,cls){const it=skCur(slot),cap=skCap(it);if(!cap)return'';const name=EQ_NAME[slot];let h='';
 for(let j=0;j<cap;j++){const r=skAt(slot,j);
  h+=`<button type="button" class="sock ${r?r.kind:'empty'}" data-u="${u}" data-j="${j}" aria-label="${eqEsc(name)} socket ${j+1} of ${cap}: ${r?eqEsc(r.name):'empty'}. Open the ${skKind(slot)} picker" title="${r?eqEsc(r.name):'Empty socket'}"></button>`}
 return`<div class="${cls}" role="group" aria-label="${eqEsc(name)} sockets">${h}</div>`}
const skTile=u=>{const slot=EQ_SLOTS[u];return SK_SLOTS.includes(slot)&&eqCur(u)?skDiscs(slot,u,'socks'):''};
// the item card's row: "Sockets X of Y" and a bonus line for each rune or glyph
function skCard(it){if(!SK_SLOTS.includes(it.slot))return'';const slot=it.slot,u=EQ_SLOTS.indexOf(slot),cap=skCap(it),n=Math.min(skCount(slot),cap);
 let h=`<div class="eqsocks"><span>Sockets <b>${n} of ${cap}</b></span>${cap?skDiscs(slot,u,'sockrow'):''}</div>`;
 for(let j=0;j<cap;j++){const r=skAt(slot,j);if(r)h+=skLines(r)}
 return h}
function skLines(r){const sh=skShown(r);return sh.length?sh.map(e=>`<div class="sockfx"><span>${eqEsc(skLab(e))}</span><b>${eqEsc(skVal(e))}</b><i>[${eqEsc(r.name)}]</i></div>`).join(''):`<div class="sockfx none"><span>No stat bonus</span><i>[${eqEsc(r.name)}]</i></div>`}
// the hover tooltip's lines
function skTip(it){if(!SK_SLOTS.includes(it.slot))return'';const slot=it.slot,cap=skCap(it);if(!cap)return'';let h='';
 for(let j=0;j<cap;j++){const r=skAt(slot,j);if(r)h+=skLines(r)}
 return`<div class="eqt-meta">Sockets ${Math.min(skCount(slot),cap)} of ${cap}</div>`+h}

// ---- the picker ----
const skTabOf=r=>skShown(r).length?['lesser','normal','greater'][r.tier-1]:'other';
const skEffect=r=>{const sh=skShown(r);return sh.length?sh.map(e=>skLab(e)+' '+skVal(e)).join(', '):'No stat bonus'};
function skOv(){let o=document.getElementById('skov');if(o)return o;o=document.createElement('div');o.id='skov';o.className='skov';o.hidden=true;document.body.appendChild(o);return o}
function skOpen(u,j,opener){if(!SK.data||!eqData()){notify('The item data is still loading.');return}
 const slot=EQ_SLOTS[u],it=skCur(slot);if(!it||!SK_SLOTS.includes(slot)){notify('Equip a '+(EQ_NAME[slot]||'item').toLowerCase()+' first.');return}
 if(!skCap(it)){notify(it.name+' has no sockets in '+EQ_RS[S.rs]+'.');return}
 if(typeof eqClosePick==='function'&&EQ.pick)eqClosePick(true);
 const cur=skAt(slot,Math.min(j,skCap(it)-1));
 SK.pick={u,slot,j:Math.min(j,skCap(it)-1),q:'',tab:cur?skTabOf(cur):'normal',opener:opener||document.activeElement};
 const ov=skOv();ov.hidden=false;document.body.classList.add('skopen');skRender(true)}
function skClose(quiet){const p=SK.pick;if(!p)return;SK.pick=null;const ov=skOv();ov.hidden=true;ov.innerHTML='';document.body.classList.remove('skopen');
 if(!quiet){const b=document.querySelector('#eqbody .sock[data-u="'+p.u+'"][data-j="'+p.j+'"]')||p.opener;if(b&&b.focus)b.focus()}}
function skPick(r){const p=SK.pick;if(!p)return;const it=skCur(p.slot);if(!it||!skFits(p.slot,r)||p.j>=skCap(it))return;
 S.sock[SK_SLOTS.indexOf(p.slot)*SK_MAX+p.j]=r?r.n:0;const u=p.u,j=p.j;save();skClose(true);eqRender(true);
 notify((r?r.name+' socketed in the '+EQ_NAME[p.slot].toLowerCase()+'.':'Socket emptied.'));const b=document.querySelector('#eqbody .sock[data-u="'+u+'"][data-j="'+j+'"]');if(b)b.focus()}
function skRemove(){const p=SK.pick;if(!p)return;const r=skAt(p.slot,p.j);if(!r)return;S.sock[SK_SLOTS.indexOf(p.slot)*SK_MAX+p.j]=0;const u=p.u,j=p.j;save();skClose(true);eqRender(true);
 notify(r.name+' removed from the '+EQ_NAME[p.slot].toLowerCase()+'.');const b=document.querySelector('#eqbody .sock[data-u="'+u+'"][data-j="'+j+'"]');if(b)b.focus()}
function skList(){const p=SK.pick,w=p.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
 return SK.data.items.filter(r=>skFits(p.slot,r)).filter(r=>{const t=(r.name+' '+r.id+' '+skEffect(r)).toLowerCase();return w.every(k=>t.includes(k))})}
function skRender(first){const p=SK.pick;if(!p)return;const ov=skOv(),it=skCur(p.slot),cap=skCap(it);if(!it||p.j>=cap){skClose(true);return}
 const kind=skKind(p.slot),all=skList(),cnt={};SK_TABS.forEach(t=>cnt[t[0]]=0);all.forEach(r=>cnt[skTabOf(r)]++);
 const shown=all.filter(r=>skTabOf(r)===p.tab),curR=skAt(p.slot,p.j);
 if(first){ov.innerHTML=`<div class="skmodal" role="dialog" aria-modal="true" aria-labelledby="sktitle"><div class="skhead"><h2 id="sktitle"></h2><button type="button" class="btn" id="skclose">Close</button></div>
  <div class="sksocks" id="sksocks" role="group" aria-label="Sockets of this item"></div>
  <div class="skfilters"><input id="skq" type="search" placeholder="Search by name or effect" aria-label="Search by name or effect" autocomplete="off"></div>
  <div class="sktabs" id="sktabs" role="tablist" aria-label="Tier"></div>
  <div class="sklist" id="sklist" role="list"></div>
  <div class="skfoot"><button type="button" class="btn" id="skremove">Remove</button><span class="dim" id="skcount" aria-live="polite"></span></div></div>`;
  ov.onclick=e=>{if(e.target===ov)skClose()};document.getElementById('skclose').onclick=()=>skClose();document.getElementById('skremove').onclick=skRemove;
  const q=document.getElementById('skq');q.oninput=()=>{SK.pick.q=q.value;skRender()};
  if(innerWidth>=600)q.focus({preventScroll:true});else document.getElementById('skclose').focus({preventScroll:true})}
 document.getElementById('sktitle').textContent=(kind==='rune'?'Rune':'Glyph')+' picker · '+EQ_NAME[p.slot];
 const sks=document.getElementById('sksocks');
 sks.innerHTML=`<span class="dim">${eqEsc(it.name)}</span>`+Array.from({length:cap},(_,j)=>{const r=skAt(p.slot,j);return`<button type="button" class="sksock${j===p.j?' on':''}" data-j="${j}" aria-pressed="${j===p.j}" aria-label="Socket ${j+1} of ${cap}: ${r?eqEsc(r.name):'empty'}"><i class="sock ${r?r.kind:'empty'}" aria-hidden="true"></i>${j+1}</button>`}).join('');
 sks.querySelectorAll('.sksock').forEach(b=>{b.onclick=()=>{const j=+b.dataset.j;p.j=j;const c=skAt(p.slot,j);if(c)p.tab=skTabOf(c);skRender();const n=sks.querySelector('.sksock.on');if(n)n.focus()}});
 const tabs=document.getElementById('sktabs');
 tabs.innerHTML=SK_TABS.map(t=>`<button type="button" role="tab" class="sktab${t[0]===p.tab?' on':''}" data-t="${t[0]}" aria-selected="${t[0]===p.tab}" tabindex="${t[0]===p.tab?0:-1}">${t[1]} <small>${cnt[t[0]]}</small></button>`).join('');
 tabs.querySelectorAll('.sktab').forEach(b=>{b.onclick=()=>{p.tab=b.dataset.t;skRender();const n=tabs.querySelector('.sktab.on');if(n)n.focus()};
  b.onkeydown=e=>{const k=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;if(!k)return;e.preventDefault();const i=(SK_TABS.findIndex(t=>t[0]===p.tab)+k+SK_TABS.length)%SK_TABS.length;p.tab=SK_TABS[i][0];skRender();tabs.querySelector('.sktab.on').focus()}});
 const list=document.getElementById('sklist');
 list.innerHTML=shown.length?shown.map(r=>`<button type="button" class="skrow ${r.kind}${curR===r?' cur':''}" role="listitem" data-n="${r.n}" aria-pressed="${curR===r}">${skDisc(r)}<span class="skname">${eqEsc(r.name)}${curR===r?'<em>in this socket</em>':''}</span><span class="skfx">${eqEsc(skEffect(r))}</span></button>`).join(''):`<p class="dim skempty">${p.q.trim()?'Nothing matches that search in this tab.':'Nothing in this tab.'}</p>`;
 list.querySelectorAll('.skrow').forEach(b=>{b.onclick=()=>skPick(SK.byN.get(+b.dataset.n))});
 document.getElementById('skremove').disabled=!curR;
 document.getElementById('skcount').textContent=shown.length+' of '+all.length+' '+kind+'s'}
document.addEventListener('keydown',e=>{if(!SK.pick)return;
 if(e.key==='Escape'){e.preventDefault();e.stopPropagation();skClose();return}
 if(e.key==='Tab'){const f=[...document.querySelectorAll('#skov button:not(:disabled),#skov input')].filter(x=>x.offsetParent!==null);if(!f.length)return;const a=document.activeElement,i=f.indexOf(a);
  if(e.shiftKey&&(i<=0)){e.preventDefault();f[f.length-1].focus()}else if(!e.shiftKey&&(i===f.length-1)){e.preventDefault();f[0].focus()}}},true);
