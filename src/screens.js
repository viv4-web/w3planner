// ---- Screens (v28): Character | Inventory, switched like the game's top bar; the stash (empty until a save is imported); swipe on a phone ----
// The open screen is S.scr ('char' or 'inv') and lives in the link as the s1I segment (absent = Character). The level block, the ruleset switch and Copy link belong to both screens.
const SCR_ORDER=['inv','char'];   // the bar, left to right (Alchemy before them is "coming later" and not a screen yet)
function scrGo(s){if(s===S.scr||!SCR_ORDER.includes(s))return;if(EQ.pick)eqClosePick(true);S.scr=s;save();window.scrollTo({top:0})}
function scrStep(d){const i=SCR_ORDER.indexOf(S.scr)+d;if(i>=0&&i<SCR_ORDER.length)scrGo(SCR_ORDER[i])}
function scrApply(){const inv=S.scr==='inv';
 document.getElementById('screenChar').hidden=inv;document.getElementById('screenInv').hidden=!inv;document.body.classList.toggle('scr-inv',inv);
 [['tabInv','inv'],['tabChar','char']].forEach(([id,k])=>{const b=document.getElementById(id);b.setAttribute('aria-selected',String(S.scr===k));b.classList.toggle('on',S.scr===k)});
 const i=SCR_ORDER.indexOf(S.scr),pv=document.getElementById('scrPrev'),nx=document.getElementById('scrNext');pv.disabled=i<=0;nx.disabled=i>=SCR_ORDER.length-1;
 pv.setAttribute('aria-disabled',String(pv.disabled));nx.setAttribute('aria-disabled',String(nx.disabled));
 if(inv&&!stashDrawn)stashRender()}
document.getElementById('tabInv').onclick=()=>scrGo('inv');document.getElementById('tabChar').onclick=()=>scrGo('char');
document.getElementById('scrPrev').onclick=()=>scrStep(-1);document.getElementById('scrNext').onclick=()=>scrStep(1);
document.querySelectorAll('#topbar .rsg [data-rs]').forEach(b=>{b.onclick=()=>eqSwitch(b.dataset.rs);b.onkeydown=e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const o=b.dataset.rs==='ng'?'ng_plus':'ng';eqSwitch(o);const n=document.querySelector('#topbar .rsg [data-rs="'+o+'"]');if(n)n.focus()}}});
// swipe: on a narrow screen a horizontal swipe left goes to the next screen, right to the previous one. Not on the skill tree or mutation grid (they drag), not in fields and not inside the item grids.
{let x0=0,y0=0,t0=0,ok=false;const root=document.getElementById('screens');
 root.addEventListener('touchstart',e=>{const t=e.target;ok=innerWidth<1024&&e.touches.length===1&&!(t.closest&&t.closest('svg,input,select,textarea,.pkgrid,.oilgrid,#mutov'));if(ok){x0=e.touches[0].clientX;y0=e.touches[0].clientY;t0=Date.now()}},{passive:true});
 root.addEventListener('touchend',e=>{if(!ok||!e.changedTouches.length)return;ok=false;const dx=e.changedTouches[0].clientX-x0,dy=e.changedTouches[0].clientY-y0;
  if(Date.now()-t0<800&&Math.abs(dx)>=70&&Math.abs(dy)<Math.abs(dx)*.6)scrStep(dx<0?1:-1)},{passive:true})}

// ---- the stash: five sub-tabs as in the game; empty in v28 (a later version fills it from a save import, kept in this browser only, never in the link) ----
const ST_TABS=[{k:'crafting',name:'Crafting components',ic:'<path d="M12 3l2 3 3-1 1 3 3 1-1 3 2 3-3 1-1 3-3-1-2 3-2-3-3 1-1-3-3-1 1-3-2-3 3-1 1-3 3 1z" /><circle cx="12" cy="12" r="3.2"/>'},
 {k:'quest',name:'Quest items',ic:'<path d="M7 3h10a2 2 0 0 1 2 2v14l-4-2-3 2-3-2-4 2V5a2 2 0 0 1 2-2z"/><path d="M9 8h6M9 12h6"/>'},
 {k:'food',name:'Food & drink, Roach',ic:'<path d="M5 9h12v3a6 6 0 0 1-12 0z"/><path d="M17 10h2a2 2 0 0 1 0 5h-2M8 4v2M11 3v3M14 4v2"/>'},
 {k:'alchemy',name:'Alchemy',ic:'<path d="M10 3h4M11 3v6L5 19a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-6-10V3"/><path d="M8 15h8"/>'},
 {k:'gear',name:'Weapons & Armor',ic:'<path d="M14 3l7 7-3 1-2-2-8 8 1 3-3 1-1-4-4-1 1-3 3 1 8-8-2-2z"/>'}];
let ST={tab:0},stashDrawn=false;
// the stash contents: a local object {crafting:[{id,qty}], quest:[...], food:[...], alchemy:{oils:[ids],potions:[ids],bombs:[ids]}, weapons:[ids], armor:[ids]}; nothing writes it in v28
function stashData(){try{const o=JSON.parse(localStorage.getItem('w3planner.stash')||'null');return o&&typeof o==='object'?o:null}catch(e){return null}}
const stashCount=o=>o?['crafting','quest','food','weapons','armor'].reduce((a,k)=>a+((o[k]||[]).length),0)+['oils','potions','bombs'].reduce((a,k)=>a+(((o.alchemy||{})[k])||[]).length,0):0;
function stashColumn(title,rows){return`<div class="stcol"><h3>${eqEsc(title)}</h3>${rows.length?`<ul>${rows.map(r=>`<li>${eqEsc(r)}</li>`).join('')}</ul>`:'<p class="dim">Nothing here.</p>'}</div>`}
function stashRender(){const el=document.getElementById('stash');if(!el)return;stashDrawn=true;const o=stashData(),n=stashCount(o),t=ST_TABS[ST.tab];
 const nm=id=>{const c=CN.data&&CN.byId.get(id),g=eqData()&&eqData().byId.get(id);return c?c.name:g?g.name:String(id)},rows=a=>(a||[]).map(x=>typeof x==='object'?nm(x.id)+(x.qty>1?' ×'+x.qty:''):nm(x));
 let body;
 if(!n)body=`<div class="stempty"><p>Your stash fills when you import a save. Click any slot to plan.</p><button class="btn" id="stimport" type="button" disabled aria-disabled="true">Import save (coming later)</button></div>`;
 else if(t.k==='alchemy')body=`<div class="stcols c3">${stashColumn('Oils',rows((o.alchemy||{}).oils))}${stashColumn('Potions',rows((o.alchemy||{}).potions))}${stashColumn('Bombs',rows((o.alchemy||{}).bombs))}</div>`;
 else if(t.k==='gear')body=`<div class="stcols c2">${stashColumn('Weapons',rows(o.weapons))}${stashColumn('Armor',rows(o.armor))}</div>`;
 else body=`<div class="stcols c1">${stashColumn(t.name,rows(o[t.k]))}</div>`;
 el.innerHTML=`<div class="sthead"><h2>Stash</h2><div class="sttabs" role="tablist" aria-label="Stash sections">${ST_TABS.map((s,i)=>`<button type="button" class="sttab${i===ST.tab?' on':''}" role="tab" aria-selected="${i===ST.tab}" data-t="${i}" title="${eqEsc(s.name)}" aria-label="${eqEsc(s.name)}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${s.ic}</svg></button>`).join('')}</div></div><div class="stname">${eqEsc(t.name)}</div>${body}`;
 el.querySelectorAll('.sttab').forEach(b=>{b.onclick=()=>{ST.tab=+b.dataset.t;stashRender()}})}
