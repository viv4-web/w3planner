// ---- Quests (v33): status, list, level band, Next up, detail, progress. Data: data/QUESTS.json (tools/make_quests.py, docs/QUESTS.md); the journal text is game content and exists in the live build only ----
// The screen is S.scr 'q' and lives in the link as s1Q; nothing else is in the link. Progress is kept in this browser (localStorage 'w3p.quests.v1') and in an exported file, never in the link or anywhere else.
const QS_URL=/*@file:QUESTS*/, QS_DESC=/*@quests*/null;
const QS_KEY='w3p.quests.v1';
const QS_KINDS=[['main','Main'],['side','Secondary'],['contract','Contracts'],['treasure','Treasure hunts'],['gwent','Gwent'],['race','Races'],['fist','Fistfights']];
const QS_NAMES={none:'Not started',active:'Active',done:'Done',failed:'Failed',inactive:'Inactive'},QS_MARKS=['none','active','done','failed'];
const QS_SAVE={JS_Success:'done',JS_Active:'active',JS_Failed:'failed',JS_Inactive:'inactive'};
const QS_ICON={none:'<circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6"/>',active:'<circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="8" cy="8" r="2.6" fill="currentColor"/>',
 done:'<path d="M3 8.5l3.2 3.2L13 4.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',failed:'<path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
 inactive:'<circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="2.2 2.2"/>'};
const QS_VIEW_KEY='w3p.quests.view';   // 'list' | 'band': the view last chosen in this browser (v33b); the default is the List
const QS={data:null,byG:null,byObj:null,byDesc:null,load:null,err:false,region:'ve',view:'list',kind:'all',hide:false,q:'',sel:null,descP:null,desc:null,init:false,shown:false,lv:0,open:false,reveal:new Set(),cells:new Set(),
 store:{manual:{},save:null,changed:0},ok:true,confirm:false};
const qsEl=id=>document.getElementById(id);
const qsEsc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const qsIcon=st=>`<svg class="qsic qs-${st}" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">${QS_ICON[st]||QS_ICON.none}</svg>`;

// ---- storage: every read and write is in try/catch; without storage the screen works for this visit and the chip says so ----
const QS_GUID=/^[0-9a-f]{32}$/,QS_CODES={done:'d',active:'a',failed:'f',inactive:'i',none:'n'},QS_DECODE={d:'done',a:'active',f:'failed',i:'inactive',n:'none'};
function qsClean(o){   // untrusted (the file the user loads, or another version's storage): only known shapes and values survive; null when it is not progress at all
 if(!o||typeof o!=='object'||o.v!==1)return null;const out={manual:{},save:null,changed:Number.isFinite(o.changed)?Math.max(0,Math.floor(o.changed)):0};
 const take=(src,allowed,max)=>{const r={};if(src&&typeof src==='object')for(const k of Object.keys(src).slice(0,max)){const v=src[k];if(QS_GUID.test(k)&&allowed.includes(v))r[k]=v}return r};
 out.manual=take(o.manual,QS_MARKS,6000);
 if(o.save&&typeof o.save==='object')out.save={at:Number.isFinite(o.save.at)?Math.max(0,Math.floor(o.save.at)):0,file:typeof o.save.file==='string'?o.save.file.slice(0,120):'',
  q:take(o.save.q,['done','active','failed','inactive'],6000),o:take(o.save.o,['done','active','failed','inactive'],12000),e:take(o.save.e,['done','active','failed','inactive'],12000)};
 return out}
function qsStoreInit(){if(QS.read)return;QS.read=true;qsRead()}
function qsRead(){try{const raw=localStorage.getItem(QS_KEY);QS.ok=true;if(!raw)return;const c=qsClean(JSON.parse(raw));if(c)QS.store=c}catch(e){QS.ok=false}
 try{const v=localStorage.getItem(QS_VIEW_KEY);if(v==='list'||v==='band')QS.view=v}catch(e){}}
function qsSetView(v){QS.view=v;QS.open=false;try{localStorage.setItem(QS_VIEW_KEY,v)}catch(e){}}
function qsWrite(){try{localStorage.setItem(QS_KEY,JSON.stringify(Object.assign({v:1},QS.store)));QS.ok=true}catch(e){QS.ok=false}qsChip()}
function qsTouch(){QS.store.changed=Date.now();qsWrite()}
const qsSaveState=g=>QS.store.save&&QS.store.save.q[g]||'none';
const qsState=g=>QS.store.manual[g]||qsSaveState(g);
const qsMarked=()=>QS.data?QS.data.quests.filter(q=>qsState(q.g)!=='none').length:0;
const qsHand=()=>Object.keys(QS.store.manual).length;
const qsHasProgress=()=>!!(qsHand()||QS.store.save);

// ---- data ----
function qsLoad(){if(QS.data)return Promise.resolve(QS.data);
 return QS.load||(QS.load=(async()=>{if(!(window.W3DATA&&W3DATA.QUESTS))await eqScript(QS_URL);const d=W3DATA.QUESTS;if(!d||!d.quests)throw new Error('empty');
  QS.data=d;QS.byG=new Map(d.quests.map(q=>[q.g,q]));QS.byObj=new Map();QS.byDesc=new Set();d.quests.forEach(q=>{q.o.forEach((g,i)=>QS.byObj.set(g,[q,i]));q.d.forEach(g=>QS.byDesc.add(g))});QS.regions=new Map(d.regions);return d})().catch(e=>{QS.load=null;QS.err=true;throw e}))}
function qsDescLoad(){if(QS.desc)return Promise.resolve(QS.desc);if(!QS_DESC)return Promise.reject(new Error('none'));
 return QS.descP||(QS.descP=new Promise((ok,bad)=>{const s=document.createElement('script');s.src=QS_DESC.desc;s.onload=()=>{const d=(window.W3DATA||{}).quests_desc;if(d){QS.desc=d;ok(d)}else{QS.descP=null;bad(new Error('empty'))}};
  s.onerror=()=>{QS.descP=null;s.remove();bad(new Error('load'))};document.head.appendChild(s)}))}

// ---- the XP rule (r4Game.ws OnGiveReward, lines 1020-1078): a quest 10 or more levels under yours gives 5 %; only rewards whose name contains "q60" (q.hs, set by tools/make_quests.py) also scale by 16 % per level, at most 150 % ----
function qsXp(q,my){if(q.lv==null)return null;const d=q.lv-my;if(d<=-10)return .05;if(!q.hs)return 1;let m=1;if(d<10){m=Math.max(0,Math.min(1.5,1+d*.16))}return m>0?m:.05}
const qsPct=m=>Math.round(m*100)+'%';
const qsXpText=(q,my)=>{const m=qsXp(q,my);if(m==null)return'XP at your level: not computed yet (no level for this quest)';
 return q.hs?'This Hearts of Stone reward scales XP by level: '+qsPct(m)+' of the usual XP at level '+my:m<1?'5% XP: this quest is 10 or more levels under level '+my:'Full XP at level '+my}
const qsLevelText=q=>q.lv==null?'—':String(q.lv);
const qsMy=()=>lvl();
function qsLvSpan(q){return q.lv==null?'<span class="qslv na" title="not computed yet">—</span>':`<span class="qslv">${q.lv}</span>`}

// ---- regions ----
const qsInRegion=r=>QS.data.quests.filter(q=>q.r===r);
function qsPercent(r){const l=qsInRegion(r);return l.length?Math.round(100*l.filter(q=>qsState(q.g)==='done').length/l.length):0}
function qsRenderRegs(){const el=qsEl('qsRegs');
 el.innerHTML=QS.data.regions.map(([k,n])=>{const c=qsInRegion(k).length;return`<button type="button" class="qsreg${k===QS.region?' on':''}" role="tab" data-r="${k}" aria-selected="${k===QS.region}" title="${qsEsc(n)}: ${qsPercent(k)}% done of ${c} quests"><span class="qsrn">${qsEsc(n)}</span><small>${qsPercent(k)}% done</small></button>`}).join('');
 el.querySelectorAll('.qsreg').forEach(b=>{b.onclick=()=>{QS.region=b.dataset.r;qsRenderAll()};b.onkeydown=e=>{if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;e.preventDefault();const ks=QS.data.regions.map(r=>r[0]),i=ks.indexOf(QS.region)+(e.key==='ArrowRight'?1:-1);
  if(i<0||i>=ks.length)return;QS.region=ks[i];qsRenderAll();const n=el.querySelector('.qsreg.on');if(n)n.focus()}});
 const on=el.querySelector('.qsreg.on');if(on&&innerWidth<760)on.scrollIntoView({block:'nearest',inline:'center'})}

// ---- Next up: active quests first (with the current objective), then quests not started that still give full XP, nearest to my level, then the region of the first active quest ----
const qsTitles=q=>QS.desc&&QS.desc[q.id]?QS.desc[q.id].o:null;   // objective titles are game text: in the lazy file, live build only
function qsCurrent(q){const out=[];if(!QS.store.save)return out;const T=qsTitles(q);q.o.forEach((g,i)=>{if(QS.store.save.o[g]==='active')out.push(T?T[i]:null)});return out}   // null = an active objective whose title is not in this build
function qsNextUp(){const my=qsMy(),all=QS.data.quests,act=all.filter(q=>qsState(q.g)==='active').sort((a,b)=>Math.abs((a.lv==null?999:a.lv)-my)-Math.abs((b.lv==null?999:b.lv)-my)||a.n.localeCompare(b.n));
 const home=act.length?act[0].r:QS.region,fresh=all.filter(q=>qsState(q.g)==='none'&&q.lv!=null&&qsXp(q,my)>=1).sort((a,b)=>Math.abs(a.lv-my)-Math.abs(b.lv-my)||(a.r===home?0:1)-(b.r===home?0:1)||a.lv-b.lv||a.n.localeCompare(b.n));
 return act.concat(fresh).slice(0,4)}
function qsRenderNext(){const el=qsEl('qsNext'),list=qsNextUp(),my=qsMy();
 el.innerHTML=`<h3>Next up</h3><div class="qscards">${list.map(q=>{const st=qsState(q.g),cur=st==='active'?qsCurrent(q):[];
  return`<button type="button" class="qscard${QS.sel===q.g?' on':''}" data-g="${q.g}">${qsIcon(st)}<span class="qscn"><b>${qsEsc(q.n)}</b><small>${qsEsc(QS.regions.get(q.r))} · level ${qsLevelText(q)} · ${QS_NAMES[st]}</small><em>${st==='active'?(cur.length?(cur[0]===null?cur.length+' active objective'+(cur.length>1?'s':'')+' (text not in this build)':qsEsc(cur[0])+(cur.length>1?' (+'+(cur.length-1)+')':'')):'Current objective: not known'):qsEsc(qsXp(q,my)>=1?'Full XP at your level':'')}</em></span></button>`}).join('')||'<p class="qshint">Nothing left to suggest.</p>'}</div>`;
 el.querySelectorAll('.qscard').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true)})}

// ---- the views ----
function qsKindName(k){return(QS_KINDS.find(x=>x[0]===k)||[0,k])[1]}
function qsRows(){   // the list: ordered by level; a search looks in every region
 const w=glWords(QS.q),all=w.length;let l=(all?QS.data.quests:qsInRegion(QS.region)).slice();
 if(QS.kind!=='all')l=l.filter(q=>q.t===QS.kind);if(QS.hide)l=l.filter(q=>qsState(q.g)!=='done');if(all)l=l.filter(q=>w.every(x=>glN(q.n).includes(x)));
 return l.sort((a,b)=>(a.lv==null)-(b.lv==null)||a.lv-b.lv||a.n.localeCompare(b.n))}
function qsRenderList(host){const reg=qsInRegion(QS.region),cnt=k=>reg.filter(q=>k==='all'||q.t===k).length,old=host.querySelector('#qsRows'),top=old?old.scrollTop:0;
 host.innerHTML=`<div class="qsfilters"><div class="qschips" role="group" aria-label="Quest type">${[['all','All']].concat(QS_KINDS).map(([k,n])=>`<button type="button" class="qschip${QS.kind===k?' on':''}" data-k="${k}" aria-pressed="${QS.kind===k}"${cnt(k)?'':' disabled'}>${n}</button>`).join('')}<button type="button" class="qschip hide${QS.hide?' on':''}" id="qsHide" aria-pressed="${QS.hide}">Hide done</button></div>
  <input id="qsQ" class="qssearch" type="search" placeholder="Search all quests" aria-label="Search all quests" autocomplete="off" spellcheck="false" value="${qsEsc(QS.q)}"></div><div class="qsrows" id="qsRows"></div>`;
 const rows=qsEl('qsRows'),l=qsRows(),all=glWords(QS.q).length;
 rows.innerHTML=l.map(q=>{const st=qsState(q.g);return`<button type="button" class="qsrow${QS.sel===q.g?' on':''}" data-g="${q.g}" aria-label="${qsEsc(q.n)}, ${QS_NAMES[st]}, level ${qsLevelText(q)}">${qsIcon(st)}<span class="qsrn2"><b>${qsEsc(q.n)}</b>${all?`<small>${qsEsc(QS.regions.get(q.r))}</small>`:''}</span>${qsLvSpan(q)}</button>`}).join('')||`<p class="qshint">${QS.q.trim()?'Nothing matches '+qsEsc(QS.q.trim())+'.':'No quests here.'}</p>`;
 rows.scrollTop=top;host.querySelectorAll('.qschip[data-k]').forEach(b=>{b.onclick=()=>{QS.kind=b.dataset.k;qsRenderView()}});qsEl('qsHide').onclick=()=>{QS.hide=!QS.hide;qsRenderView()};
 const inp=qsEl('qsQ');inp.oninput=()=>{QS.q=inp.value;const p=inp.selectionStart;qsRenderView();const n=qsEl('qsQ');n.focus();n.setSelectionRange(p,p)};
 rows.querySelectorAll('.qsrow').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true);b.onkeydown=e=>{if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;const rs=[...rows.querySelectorAll('.qsrow')],i=rs.indexOf(b)+(e.key==='ArrowDown'?1:-1);if(i>=0&&i<rs.length){e.preventDefault();rs[i].focus()}}})}
// ---- the Level band: x = quest levels from the lowest to the highest in this region (at least 24 px per level), one row per type; dots of one level side by side in the level's slot, three lines at most ("+n" opens the rest) ----
const QS_DOT=14,QS_STEP=16,QS_SLOT=24,QS_LABEL=112;
function qsRenderBand(host){const my=qsMy(),reg=qsInRegion(QS.region),vis=reg.filter(q=>q.lv!=null&&qsState(q.g)!=='done'),nol=reg.filter(q=>q.lv==null&&qsState(q.g)!=='done').length;
 const note=`<p class="qsbnote">Done quests are hidden. Hollow = not started, filled = active. ${nol?nol+' quest'+(nol===1?' has':'s have')+' no level yet and '+(nol===1?'is':'are')+' only in the List. ':''}The hatched zone is where a quest gives only 5% XP (the game's rule, r4Game.ws OnGiveReward, normal difficulty, first playthrough).</p>`;
 if(!vis.length){host.innerHTML='<p class="qshint">No quests to show here: every quest of this region is done or has no level.</p>'+note;QS.place=null;return}
 const lo=Math.min(...vis.map(q=>q.lv)),hi=Math.max(...vis.map(q=>q.lv)),span=hi-lo+1,kinds=QS_KINDS.filter(([k])=>vis.some(q=>q.t===k));
 const avail=(host.clientWidth||900)-QS_LABEL-22,slot=Math.max(QS_SLOT,avail/span),W=Math.round(slot*span),per=Math.max(1,Math.floor(slot/QS_STEP)),cap=per*3;
 const lx=lv=>(Math.max(lo,Math.min(hi,lv))-lo+.5)*slot,zoneLv=my-10,zw=zoneLv>=lo?(Math.min(zoneLv,hi)-lo+1)*slot:0,flip=lx(my)>W-90;
 const zone=zw?`<i class="qsz5" style="width:${zw}px"></i>`:'',line=`<i class="qsme" style="left:${lx(my)}px"></i>`;
 let rows='';
 kinds.forEach(([k,n])=>{const byLv=new Map();vis.filter(q=>q.t===k).sort((a,b)=>(qsState(b.g)==='active')-(qsState(a.g)==='active')||a.n.localeCompare(b.n)).forEach(q=>{if(!byLv.has(q.lv))byLv.set(q.lv,[]);byLv.get(q.lv).push(q)});
  let lines=1,dots='';
  byLv.forEach((list,lv)=>{const key=k+':'+lv,open=QS.cells.has(key),over=list.length>cap,shown=over&&!open?list.slice(0,cap-1):list,total=shown.length+(over?1:0),nl=Math.ceil(total/per);lines=Math.max(lines,nl);
   const x0=(lv-lo)*slot;
   const place=(i,n)=>{const ln=Math.floor(i/per),inLine=Math.min(per,total-ln*per);return'left:'+(x0+(slot-inLine*QS_STEP)/2+(i%per)*QS_STEP+1).toFixed(1)+'px;top:'+(8+ln*QS_STEP)+'px'};
   shown.forEach((q,i)=>{const st=qsState(q.g);dots+=`<button type="button" class="qsdot ${st}${QS.sel===q.g?' on':''}${q.hs?' hos':''}" data-g="${q.g}" style="${place(i)}" aria-label="${qsEsc(q.n)}, ${QS_NAMES[st]}, level ${q.lv}"></button>`});
   if(over)dots+=`<button type="button" class="qsmore" data-cell="${key}" style="${place(shown.length)}" aria-expanded="${open}" aria-label="${open?'Show fewer quests':(list.length-shown.length)+' more quests at level '+lv}">${open?'−':'+'+(list.length-shown.length)}</button>`});
  rows+=`<div class="qsbrow" style="min-height:${Math.max(56,lines*QS_STEP+16)}px"><div class="qsblabel">${n}</div><div class="qsbplot" style="width:${W}px">${zone}${line}${dots}</div></div>`});
 const axis=Array.from({length:span},(_,i)=>`<span style="left:${((i+.5)*slot).toFixed(1)}px">${lo+i}</span>`).join('');
 host.innerHTML=`<div class="qsband" id="qsBand"><div class="qsbinner" style="width:${QS_LABEL+W}px"><div class="qsbhead"><span></span><div class="qsbplot head" style="width:${W}px">${zone}${zw?`<b class="qszl" style="left:6px">${zw>=56?'5% XP':'5%'}</b><b class="qszl full" style="left:${zw+6}px">full XP</b>`:''}${line}<b class="qsml${flip?' flip':''}" style="left:${lx(my)}px">You · ${my}</b></div></div>${rows}<div class="qsbaxis"><span></span><div class="qsbplot axis" style="width:${W}px">${axis}</div></div></div></div>`+note;
 host.querySelectorAll('.qsdot').forEach(d=>{d.onclick=()=>qsSelect(d.dataset.g,true);d.onmouseenter=d.onfocus=()=>qsTip(d);d.onmouseleave=d.onblur=()=>qsTipHide()});
 host.querySelectorAll('.qsmore').forEach(b=>{b.onclick=()=>{const k=b.dataset.cell;if(QS.cells.has(k))QS.cells.delete(k);else QS.cells.add(k);qsRenderBand(host);const n=host.querySelector('.qsmore[data-cell="'+k+'"]');if(n)n.focus()}});
 QS.place=null}
// one tooltip for dots: name, type · region · level, status (on hover and on keyboard focus)
function qsTip(d){const q=QS.byG.get(d.dataset.g),t=qsEl('qsTip');if(!q)return;const st=qsState(q.g),m=qsXp(q,qsMy());
 t.innerHTML=`<b>${qsEsc(q.n)}</b><span>${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · level ${qsLevelText(q)}</span><span>${QS_NAMES[st]}${q.hs?' · Hearts of Stone XP '+qsPct(m):m<1?' · 5% XP':''}</span>`;t.hidden=false;
 const r=d.getBoundingClientRect(),w=t.offsetWidth,h=t.offsetHeight;t.style.left=Math.max(6,Math.min(innerWidth-w-6,r.left+r.width/2-w/2))+'px';t.style.top=(r.top-h-8>6?r.top-h-8:r.bottom+8)+'px'}
function qsTipHide(){const t=qsEl('qsTip');if(t)t.hidden=true}
function qsRenderView(){const host=qsEl('qsView'),sc=qsEl('screenQ');qsTipHide();
 qsEl('qsVBand').classList.toggle('on',QS.view==='band');qsEl('qsVList').classList.toggle('on',QS.view==='list');qsEl('qsVBand').setAttribute('aria-pressed',String(QS.view==='band'));qsEl('qsVList').setAttribute('aria-pressed',String(QS.view==='list'));
 sc.classList.toggle('qs-band',QS.view==='band');sc.classList.toggle('qs-open',QS.view==='band'&&QS.open);
 if(QS.view==='band')qsRenderBand(host);else qsRenderList(host)}

// ---- the detail panel (a column beside the list; in the Level band a drawer from the right) ----
function qsJournal(q,el){   // the spoiler gate: with a save only the entries the save has shown, otherwise nothing, until the player asks for the whole journal
 const T=QS.desc&&QS.desc[q.id],full=QS.reveal.has(q.id),sv=QS.store.save,seen=g=>sv&&sv.e&&sv.e[g]&&sv.e[g]!=='inactive';
 const idx=q.d.map((g,i)=>i).filter(i=>full||seen(q.d[i])),want=q.g;el.textContent='';
 const fill=()=>{if(QS.sel!==want)return;el.textContent='';
  const msg=t=>{const p=document.createElement('p');p.className='dim';p.textContent=t;el.appendChild(p)};
  if(!T||!T.d.length){msg(QS_DESC?'This quest has no journal text.':'Journal text is not included in this build.');return}
  if(!idx.length)msg(sv?'Your save has not shown any journal text for this quest yet.':'The journal is hidden so it does not spoil the story. Import a save to see what you have read, or show all of it.');
  idx.forEach(i=>{const p=document.createElement('p');glMarkup(p,T.d[i],[]);el.appendChild(p)});
  const b=document.createElement('button');b.type='button';b.className='btn qsspoil';b.textContent=full?'Hide full journal':'Show full journal (spoilers)';b.setAttribute('aria-expanded',String(full));
  b.onclick=()=>{if(full)QS.reveal.delete(q.id);else QS.reveal.add(q.id);qsJournal(q,el)};if(T.d.length>idx.length||full)el.appendChild(b)};
 if(T){fill();return}
 const l=document.createElement('p');l.className='dim';l.textContent='Loading…';el.appendChild(l);
 qsDescLoad().then(D=>{QS.desc=D;fill()},()=>{if(QS.sel!==want)return;el.textContent='';msg2(el,QS_DESC?'The journal text could not be loaded. Check your connection and try again.':'Journal text is not included in this build.')})}
function msg2(el,t){const p=document.createElement('p');p.className='dim';p.textContent=t;el.appendChild(p)}
function qsRenderDetail(){const el=qsEl('qsDetail'),q=QS.sel&&QS.byG.get(QS.sel);
 if(!q){el.innerHTML='<button type="button" class="btn qsclose" id="qsClose" aria-label="Close">×</button><div class="qsempty"><p>Choose a quest to see its objectives and journal text.</p></div>';qsEl('qsClose').onclick=()=>qsCloseDrawer(true);el.classList.remove('has');return}
 el.classList.add('has');const hadFocus=document.activeElement&&document.activeElement.id==='qsClose';   // a re-draw (the text arriving) must not drop the focus
 const st=qsState(q.g),sv=qsSaveState(q.g),hand=QS.store.manual[q.g],haveSave=!!QS.store.save,cur=qsCurrent(q),my=qsMy(),T=qsTitles(q);
 const saveLine=!haveSave?'No save imported: use <b>My progress</b> below, or import a save.':`In your save: <b>${QS_NAMES[sv]}</b>${sv==='none'?' (no journal entry)':''}`+(hand?` · you marked it <b>${QS_NAMES[hand]}</b>`:'');
 const curHtml=cur.length?`<ul>${cur.map(t=>`<li>${t===null?'An active objective (its text is not included in this build)':qsEsc(t)}</li>`).join('')}</ul>`:'<p class="dim">Not known: the save has no active objective for it.</p>';
 el.innerHTML=`<button type="button" class="btn qsclose" id="qsClose" aria-label="Close">×</button><button type="button" class="btn qsback" id="qsBack" aria-label="Back to the list">◀ Back</button><h2 class="qstitle">${qsIcon(st)}<span>${qsEsc(q.n)}</span></h2>
  <p class="qsmeta">${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · ${q.lv==null?'<span title="not computed yet">level —</span>':'level '+q.lv}</p>
  <p class="qsxp">${qsEsc(qsXpText(q,my))}</p><p class="qssave">${saveLine}</p>
  ${st==='active'?`<div class="qscur"><h3>Current objective${cur.length>1?'s':''}</h3>${curHtml}</div>`:''}
  <div class="qsprog" role="radiogroup" aria-label="My progress"><span class="qsplabel">My progress</span>${QS_MARKS.map(s=>`<button type="button" class="btn qsmark${st===s?' on':''}" role="radio" aria-checked="${st===s}" data-s="${s}">${qsIcon(s)}${QS_NAMES[s]}</button>`).join('')}${hand?'<button type="button" class="qsclear" id="qsClear">Follow my save</button>':''}</div>
  <h3 class="qsh3">Journal</h3><div class="qsdesc" id="qsDesc" tabindex="0"></div>
  <h3 class="qsh3">Objectives</h3>${q.o.length?(T?`<ul class="qsobjs">${q.o.map((g,i)=>{const s=QS.store.save&&QS.store.save.o[g]||'none';return`<li class="${s}">${qsIcon(s)}<span>${qsEsc(T[i]||'')}</span></li>`}).join('')}</ul>`:`<p class="dim">${QS_DESC?'Loading…':q.o.length+' objectives (their text is not included in this build).'}</p>`):'<p class="dim">No objectives listed.</p>'}`;
 el.querySelectorAll('.qsmark').forEach(b=>{b.onclick=()=>qsMark(q.g,b.dataset.s)});const c=qsEl('qsClear');if(c)c.onclick=()=>qsMark(q.g,null);
 qsEl('qsBack').onclick=()=>{qsEl('screenQ').classList.remove('qs-detail');const r=document.querySelector('.qsrow.on');if(r)r.focus()};qsEl('qsClose').onclick=()=>qsCloseDrawer(true);
 qsJournal(q,qsEl('qsDesc'));if(hadFocus)qsEl('qsClose').focus({preventScroll:true});
 if(!T&&QS_DESC)qsDescLoad().then(D=>{QS.desc=D;if(QS.sel===q.g)qsRenderDetail();qsRenderNext()},()=>{})}
function qsSelect(g,focus){QS.sel=g;const q=QS.byG.get(g);if(q&&q.r!==QS.region&&!(QS.view==='list'&&glWords(QS.q).length)){QS.region=q.r}
 if(QS.view==='band'){QS.open=true;QS.opener=g}qsRenderAll();qsEl('screenQ').classList.add('qs-detail');
 if(QS.view==='band'){qsDrawerPlace();const c=qsEl('qsClose');if(c)c.focus({preventScroll:true})}else if(innerWidth<=900&&focus)qsEl('qsDetail').scrollIntoView({block:'start'})}
function qsDrawerPlace(){const tb=qsEl('topbar'),el=qsEl('qsDetail');el.style.top=(innerWidth>=600?Math.max(0,tb.getBoundingClientRect().bottom):0)+'px'}
function qsCloseDrawer(focus){if(!QS.open)return;QS.open=false;qsEl('screenQ').classList.remove('qs-open');if(focus){const d=document.querySelector('.qsdot[data-g="'+QS.opener+'"]')||document.querySelector('.qscard.on');if(d)d.focus()}}

// ---- progress by hand ----
function qsMark(g,s){if(s===null)delete QS.store.manual[g];else QS.store.manual[g]=s;qsTouch();qsRenderAll()}
function qsRenderAll(){if(!QS.data)return;qsRenderRegs();qsRenderNext();qsRenderView();qsRenderDetail();qsChip();if(QS.open)qsDrawerPlace()}

// ---- the chip: Saved in this browser | export | load | reset ----
const qsWhen=t=>t?new Date(t).toLocaleString([],{dateStyle:'medium',timeStyle:'short'}):'never';
function qsChip(){const b=qsEl('qsChip');if(!b)return;b.textContent=(QS.ok?'Saved in this browser':'Not saved in this browser')+' ▾';b.classList.toggle('warn',!QS.ok);
 const m=qsEl('qsMenu');if(m.hidden)return;qsMenuFill()}
function qsMenuFill(){const m=qsEl('qsMenu'),n=QS.data?qsMarked():0,h=qsHand(),s=QS.store.save;
 m.innerHTML=`<p class="qsmeta2"><b>${n}</b> quest${n===1?'':'s'} marked${h?' · '+h+' by hand':''}${s?' · save: '+qsEsc(s.file||'imported')+' ('+qsEsc(qsWhen(s.at))+')':''}</p><p class="qsmeta2">Last change: ${qsEsc(qsWhen(QS.store.changed))}</p>
  ${QS.ok?'':'<p class="qsmeta2 bad">This browser blocks storage for the site: your marks work until you close the page. Export them to keep them.</p>'}
  <button type="button" class="btn" id="qsExport" role="menuitem">Export progress (.json)</button>
  <label class="btn" role="menuitem" tabindex="0" id="qsLoadLbl" for="qsLoadFile">Load progress file</label><input class="vh" id="qsLoadFile" type="file" accept=".json,application/json" aria-label="Load a progress file">
  ${QS.confirm?'<p class="qsmeta2 bad">Remove all your quest progress from this browser?</p><div class="qsrow2"><button type="button" class="btn qsdanger" id="qsResetYes">Reset</button><button type="button" class="btn" id="qsResetNo">Keep it</button></div>':'<button type="button" class="btn" id="qsReset" role="menuitem">Reset</button>'}
  <p class="qsmsg" id="qsMsg2" role="status"></p>`;
 qsEl('qsExport').onclick=qsExport;qsEl('qsLoadFile').onchange=e=>{if(e.target.files[0])qsLoadFile(e.target.files[0]);e.target.value=''};const lb=qsEl('qsLoadLbl');lb.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();qsEl('qsLoadFile').click()}};
 const r=qsEl('qsReset');if(r)r.onclick=()=>{QS.confirm=true;qsMenuFill();qsEl('qsResetNo').focus()};
 const y=qsEl('qsResetYes');if(y){y.onclick=()=>{QS.store={manual:{},save:null,changed:Date.now()};QS.confirm=false;try{localStorage.removeItem(QS_KEY)}catch(e){QS.ok=false}qsMenuFill();qsRenderAll();qsEl('qsMsg2').textContent='Your quest progress was removed.'};qsEl('qsResetNo').onclick=()=>{QS.confirm=false;qsMenuFill();qsEl('qsReset').focus()}}}
function qsMenu(open){const m=qsEl('qsMenu'),b=qsEl('qsChip');m.hidden=!open;b.setAttribute('aria-expanded',String(open));QS.confirm=false;if(open)qsMenuFill()}
function qsExport(){const o=Object.assign({app:'w3planner',kind:'quest-progress',exported:new Date().toISOString()},{v:1,manual:QS.store.manual,save:QS.store.save,changed:QS.store.changed});
 const url=URL.createObjectURL(new Blob([JSON.stringify(o)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='w3planner-quests.json';qsEl('qsChipWrap').appendChild(a);a.click();a.remove();   // inside the chip's box, so its own click does not count as a click outside the menu
 setTimeout(()=>URL.revokeObjectURL(url),2000);
 qsEl('qsMsg2').textContent='Exported w3planner-quests.json.'}
async function qsLoadFile(f){const msg=qsEl('qsMsg2');if(f.size>(2<<20)){msg.textContent="This doesn't look like a progress file (too large).";return}
 let c=null;try{c=qsClean(JSON.parse(await f.text()))}catch(e){}if(!c){msg.textContent="This isn't a w3planner quest progress file.";return}
 try{await qsLoad()}catch(e){msg.textContent='The quest list could not be loaded.';return}
 QS.store=c;qsWrite();qsRenderAll();qsEl('qsMsg2')&&(qsEl('qsMsg2').textContent='Loaded '+f.name+': '+qsMarked()+' quests marked.')}

// ---- from a save (v33): saveread.js gives [[guid, status], ...]; the page keeps the quests and objectives it knows ----
function qsFromJournal(j){if(!j||!QS.data)return null;const q={},o={},e={};
 j.forEach(([g,s])=>{const st=QS_SAVE[s];if(!st)return;if(QS.byG.has(g))q[g]=st;else if(QS.byObj.has(g))o[g]=st;else if(QS.byDesc.has(g))e[g]=st});return{q,o,e}}   // e: the journal entries (text) the save has shown
function qsCounts(stateOf){const c={done:0,active:0,failed:0,inactive:0,none:0};QS.data.quests.forEach(q=>{c[stateOf(q.g)]++});return c}
// what importing would change: counts now and after, and the quests whose hand mark disagrees with the save
function qsCompare(J){const now=qsCounts(qsState),keep=qsCounts(g=>QS.store.manual[g]||J.q[g]||'none'),repl=qsCounts(g=>J.q[g]||'none');
 const diff=QS.data.quests.filter(q=>QS.store.manual[q.g]&&QS.store.manual[q.g]!==(J.q[q.g]||'none'));return{now,keep,repl,diff}}
function qsApplyJournal(J,name,mode){QS.store.save={at:Date.now(),file:String(name||'').slice(0,120),q:J.q,o:J.o,e:J.e};if(mode==='replace')QS.store.manual={};qsTouch()}

// ---- screen ----
function qsBind(){
 const sw=v=>{qsSetView(v);qsEl('screenQ').classList.remove('qs-detail');qsRenderView();qsRenderDetail()};qsEl('qsVBand').onclick=()=>sw('band');qsEl('qsVList').onclick=()=>sw('list');
 const chip=qsEl('qsChip');chip.onclick=e=>{e.stopPropagation();qsMenu(qsEl('qsMenu').hidden)};
 document.addEventListener('click',e=>{const m=qsEl('qsMenu');if(!m.hidden&&!e.composedPath().includes(qsEl('qsChipWrap')))qsMenu(false)});   // composedPath: a click on a button the menu has just re-drawn is still inside it
 document.addEventListener('keydown',e=>{const m=qsEl('qsMenu');if(!m.hidden&&e.key==='Escape'){e.preventDefault();qsMenu(false);chip.focus()}});
 let rt=0;addEventListener('resize',()=>{if(!QS.shown||!QS.data)return;clearTimeout(rt);rt=setTimeout(()=>{if(QS.view==='band')qsRenderView();if(QS.open)qsDrawerPlace()},120)});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&QS.shown&&QS.open&&qsEl('qsMenu').hidden){e.preventDefault();qsCloseDrawer(true)}})}
function qsClose(){QS.shown=false;const w=qsEl('qsChipWrap');if(w){w.hidden=true;qsMenu(false)}}
function qsOpen(){if(QS.shown)return;QS.shown=true;if(!QS.init){QS.init=true;qsBind()}qsStoreInit();
 qsEl('qsChipWrap').hidden=false;qsChip();
 const body=qsEl('qsBody');qsEl('qsLoadMsg').hidden=true;qsEl('qsLoadMsg').textContent='';
 qsLoad().then(()=>{if(!QS.shown)return;body.hidden=false;QS.lv=qsMy();qsRenderAll()},()=>{body.hidden=true;qsEl('qsLoadMsg').hidden=false;qsEl('qsLoadMsg').textContent='The quest list could not be loaded. Check your connection and try again.'})}
function qsSync(){if(QS.shown&&QS.data&&QS.lv!==qsMy()){QS.lv=qsMy();qsRenderAll()}}   // the Level field changed: zones, Next up and tooltips follow it
