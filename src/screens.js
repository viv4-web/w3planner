// ---- Screens (v28, v29): Glossary | Inventory | Character are live; Alchemy, World Map, Quests and Meditation are greyed ("in game only") and open a panel; swipe on a phone ----
// The open screen is S.scr ('char', 'inv' or 'glo') and lives in the link as the s1I / s1G segment (absent = Character). The level block, the ruleset switch and Copy link belong to every screen.
const SCR_ORDER=['glo','inv','char'];   // the live screens, left to right as in the bar: the arrows step through these and skip the greyed tabs
const SCR_IDS={glo:'screenGlo',inv:'screenInv',char:'screenChar'},SCR_TABS={glo:'tabGlo',inv:'tabInv',char:'tabChar'};
function scrGo(s){if(s===S.scr||!SCR_ORDER.includes(s))return;if(EQ.pick)eqClosePick(true);S.scr=s;save();window.scrollTo({top:0})}
function scrStep(d){const i=SCR_ORDER.indexOf(S.scr)+d;if(i>=0&&i<SCR_ORDER.length)scrGo(SCR_ORDER[i])}
function scrApply(){const inv=S.scr==='inv';
 Object.keys(SCR_IDS).forEach(k=>{document.getElementById(SCR_IDS[k]).hidden=S.scr!==k;document.body.classList.toggle('scr-'+k,S.scr===k)});
 Object.keys(SCR_TABS).forEach(k=>{const b=document.getElementById(SCR_TABS[k]);b.setAttribute('aria-selected',String(S.scr===k));b.classList.toggle('on',S.scr===k)});
 const i=SCR_ORDER.indexOf(S.scr),pv=document.getElementById('scrPrev'),nx=document.getElementById('scrNext');pv.disabled=i<=0;nx.disabled=i>=SCR_ORDER.length-1;
 pv.setAttribute('aria-disabled',String(pv.disabled));nx.setAttribute('aria-disabled',String(nx.disabled));
 const on=document.querySelector('#stabs .stab.on');if(on&&innerWidth<600)on.scrollIntoView({block:'nearest',inline:'center'});   // the phone's tab row scrolls sideways
 if(inv&&!stashDrawn)stashRender();if(S.scr==='glo'){if(typeof glOpen==='function')glOpen()}else if(typeof glClose==='function')glClose()}
// the greyed tabs: a centred panel (title, "In-game feature only.", the reason, and the two live places to go instead)
const IG_WHY={alchemy:['Alchemy','Crafting happens in the game; plan consumables in Inventory slots.'],map:['World Map','The world map is in-game only. For an interactive map, use witcher3map.com, a free, ad-free fan project (CC BY-NC-SA).'],quests:['Quests','Quest progress lives in the game.'],meditation:['Meditation','Meditation can only be done in the game.'],crafting:['Crafting','Crafting happens in the game; plan consumables in Inventory slots.']};
let igOpener=null;
function igOpen(k,opener){const w=IG_WHY[k];if(!w)return;igOpener=opener||document.activeElement;document.getElementById('igtitle').textContent=w[0];document.getElementById('igwhy').textContent=w[1];
 const o=document.getElementById('igov'),ext=document.getElementById('igMap');ext.hidden=k!=='map';o.hidden=false;(k==='map'?ext:document.getElementById('igInv')).focus()}   // World Map only: a plain link to witcher3map.com (another site; nothing of it is loaded or copied)
function igClose(go){document.getElementById('igov').hidden=true;if(go)scrGo(go);else if(igOpener&&igOpener.focus)igOpener.focus();igOpener=null}
document.querySelectorAll('[data-ig]').forEach(b=>{b.onclick=()=>igOpen(b.dataset.ig,b)});
document.getElementById('igInv').onclick=()=>igClose('inv');document.getElementById('igGlo').onclick=()=>igClose('glo');document.getElementById('igclose').onclick=()=>igClose();
document.getElementById('igov').onclick=e=>{if(e.target.id==='igov')igClose()};
document.addEventListener('keydown',e=>{const o=document.getElementById('igov');if(o.hidden)return;if(e.key==='Escape'){e.preventDefault();igClose()}
 else if(e.key==='Tab'){const f=[...o.querySelectorAll('button,a[href]:not([hidden])')],i=f.indexOf(document.activeElement);if(e.shiftKey&&i<=0){e.preventDefault();f[f.length-1].focus()}else if(!e.shiftKey&&i===f.length-1){e.preventDefault();f[0].focus()}}});
// Copy link: ONE control, in the top bar, for every screen. It copies the link of the build as it is now (enc(): skills, mutations, mutagens, level, gear, consumables, ruleset, and s1I / s1G when Inventory / Glossary is open).
let copyT=0;
function copyLink(){const b=document.getElementById('copy'),url=(CFG.shareBase||location.href.split('#')[0])+'#'+enc();
 const done=ok=>{b.textContent=ok?'Link copied':'Copy failed';notify(ok?'Link copied':'Could not copy: your browser blocked it. The full link is in the address bar.');clearTimeout(copyT);copyT=setTimeout(()=>{b.textContent='Copy link'},1500)};
 const old=()=>{const t=document.createElement('textarea');t.value=url;t.setAttribute('readonly','');t.style.cssText='position:fixed;left:-9999px;top:0';document.body.appendChild(t);t.select();let ok=false;try{ok=document.execCommand('copy')}catch(_){}t.remove();return ok};
 (navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(url).then(()=>true,old):Promise.resolve(old())).then(done)}
document.getElementById('copy').onclick=copyLink;
// phone: the full-screen slot sheet starts below the top bar, which stays on top of it (so Copy link, the tabs and Level stay reachable)
{const mq=matchMedia('(max-width:599px)'),il=document.getElementById('invLeft'),tb=document.getElementById('topbar');
 const sync=()=>{const open=mq.matches&&il.classList.contains('panelopen');if(open){window.scrollTo({top:0});document.documentElement.style.setProperty('--tbh',tb.offsetHeight+'px')}document.body.classList.toggle('sheet-open',open)};
 new MutationObserver(sync).observe(il,{attributes:true,attributeFilter:['class']});addEventListener('resize',sync)}
document.getElementById('tabGlo').onclick=()=>scrGo('glo');document.getElementById('tabInv').onclick=()=>scrGo('inv');document.getElementById('tabChar').onclick=()=>scrGo('char');
document.getElementById('scrPrev').onclick=()=>scrStep(-1);document.getElementById('scrNext').onclick=()=>scrStep(1);
document.querySelectorAll('#topbar .rsg [data-rs]').forEach(b=>{b.onclick=()=>eqSwitch(b.dataset.rs);b.onkeydown=e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();const o=b.dataset.rs==='ng'?'ng_plus':'ng';eqSwitch(o);const n=document.querySelector('#topbar .rsg [data-rs="'+o+'"]');if(n)n.focus()}}});
// swipe: on a narrow screen a horizontal swipe left goes to the next screen, right to the previous one. Not on the skill tree or mutation grid (they drag), not in fields and not inside the item grids.
{let x0=0,y0=0,t0=0,ok=false;const root=document.getElementById('screens');
 root.addEventListener('touchstart',e=>{const t=e.target;ok=innerWidth<1024&&e.touches.length===1&&!(t.closest&&t.closest('svg,input,select,textarea,.pkgrid,.oilgrid,#mutov,.glsubs,.glrows,.gltext,.stabs'));if(ok){x0=e.touches[0].clientX;y0=e.touches[0].clientY;t0=Date.now()}},{passive:true});
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
