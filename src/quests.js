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
const QS={data:null,byG:null,byObj:null,load:null,err:false,region:'ve',view:'band',kind:'all',hide:false,q:'',sel:null,descP:null,desc:null,init:false,shown:false,lv:0,
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
  q:take(o.save.q,['done','active','failed','inactive'],6000),o:take(o.save.o,['done','active','failed','inactive'],12000)};
 return out}
function qsStoreInit(){if(QS.read)return;QS.read=true;qsRead()}
function qsRead(){try{const raw=localStorage.getItem(QS_KEY);QS.ok=true;if(!raw)return;const c=qsClean(JSON.parse(raw));if(c)QS.store=c}catch(e){QS.ok=false}}
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
  QS.data=d;QS.byG=new Map(d.quests.map(q=>[q.g,q]));QS.byObj=new Map();d.quests.forEach(q=>q.o.forEach((o,i)=>QS.byObj.set(o[0],[q,i])));QS.regions=new Map(d.regions);return d})().catch(e=>{QS.load=null;QS.err=true;throw e}))}
function qsDescLoad(){if(QS.desc)return Promise.resolve(QS.desc);if(!QS_DESC)return Promise.reject(new Error('none'));
 return QS.descP||(QS.descP=new Promise((ok,bad)=>{const s=document.createElement('script');s.src=QS_DESC.desc;s.onload=()=>{const d=(window.W3DATA||{}).quests_desc;if(d){QS.desc=d;ok(d)}else{QS.descP=null;bad(new Error('empty'))}};
  s.onerror=()=>{QS.descP=null;s.remove();bad(new Error('load'))};document.head.appendChild(s)}))}

// ---- the XP rule (r4Game.ws OnGiveReward, lines 1020-1078): a quest 10 or more levels under yours gives 5 %; Hearts of Stone rewards (named q60...) also scale by 16 % per level, from 150 % down ----
function qsXp(q,my){if(q.lv==null)return null;const d=q.lv-my;if(d<=-10)return .05;if(q.p!=='ep1')return 1;let m=1;if(d<10){m=Math.max(0,Math.min(1.5,1+d*.16))}return m>0?m:.05}
const qsPct=m=>Math.round(m*100)+'%';
const qsXpText=(q,my)=>{const m=qsXp(q,my);if(m==null)return'XP at your level: not computed yet (no level for this quest)';
 return q.p==='ep1'?'Hearts of Stone scales XP by level: '+qsPct(m)+' of the usual XP at level '+my:m<1?'5% XP: this quest is 10 or more levels under level '+my:'Full XP at level '+my}
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
function qsCurrent(q){const out=[];if(!QS.store.save)return out;q.o.forEach(([g,t])=>{if(QS.store.save.o[g]==='active')out.push(t)});return out}
function qsNextUp(){const my=qsMy(),all=QS.data.quests,act=all.filter(q=>qsState(q.g)==='active').sort((a,b)=>Math.abs((a.lv==null?999:a.lv)-my)-Math.abs((b.lv==null?999:b.lv)-my)||a.n.localeCompare(b.n));
 const home=act.length?act[0].r:QS.region,fresh=all.filter(q=>qsState(q.g)==='none'&&q.lv!=null&&qsXp(q,my)>=1).sort((a,b)=>Math.abs(a.lv-my)-Math.abs(b.lv-my)||(a.r===home?0:1)-(b.r===home?0:1)||a.lv-b.lv||a.n.localeCompare(b.n));
 return act.concat(fresh).slice(0,4)}
function qsRenderNext(){const el=qsEl('qsNext'),list=qsNextUp(),my=qsMy();
 el.innerHTML=`<h3>Next up</h3><div class="qscards">${list.map(q=>{const st=qsState(q.g),cur=st==='active'?qsCurrent(q):[];
  return`<button type="button" class="qscard${QS.sel===q.g?' on':''}" data-g="${q.g}">${qsIcon(st)}<span class="qscn"><b>${qsEsc(q.n)}</b><small>${qsEsc(QS.regions.get(q.r))} · level ${qsLevelText(q)} · ${QS_NAMES[st]}</small><em>${st==='active'?(cur.length?qsEsc(cur[0])+(cur.length>1?' (+'+(cur.length-1)+')':''):'Current objective: not known'):qsEsc(qsXp(q,my)>=1?'Full XP at your level':'')}</em></span></button>`}).join('')||'<p class="qshint">Nothing left to suggest.</p>'}</div>`;
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
const QS_MAXLV=60,qsX=lv=>(Math.max(1,Math.min(QS_MAXLV,lv))-1)/(QS_MAXLV-1)*100;
function qsRenderBand(host){const my=qsMy(),reg=qsInRegion(QS.region),vis=reg.filter(q=>q.lv!=null&&qsState(q.g)!=='done'),nol=reg.filter(q=>q.lv==null&&qsState(q.g)!=='done').length;
 const kinds=QS_KINDS.filter(([k])=>reg.some(q=>q.t===k));
 host.innerHTML=`<div class="qsband" id="qsBand"><div class="qsbhead"><span></span><div class="qsbplot head"><i class="qsz5" style="width:${my-10>=1?(qsX(my-9.5)).toFixed(2):0}%"><b>${my-10>=1?'5% XP':''}</b></i><i class="qszfull" style="left:${my-10>=1?qsX(my-9.5).toFixed(2):0}%"><b>full XP</b></i><i class="qsme" style="left:${qsX(my).toFixed(2)}%"><b>You · ${my}</b></i></div></div>
  ${kinds.map(([k,n])=>`<div class="qsbrow" data-k="${k}"><div class="qsblabel">${n}</div><div class="qsbplot" data-k="${k}"><i class="qsz5" style="width:${my-10>=1?(qsX(my-9.5)).toFixed(2):0}%"></i><i class="qsme" style="left:${qsX(my).toFixed(2)}%"></i></div></div>`).join('')}
  <div class="qsbaxis"><span></span><div class="qsbplot axis">${[1,5,10,15,20,25,30,35,40,45,50,55,60].map(n=>`<span style="left:${qsX(n).toFixed(2)}%">${n}</span>`).join('')}</div></div></div>
  <p class="qsbnote">Done quests are hidden. Hollow = not started, filled = active. ${nol?nol+' quest'+(nol===1?' has':'s have')+' no level yet and '+(nol===1?'is':'are')+' only in the List. ':''}Zones follow the game's quest XP rule (r4Game.ws, OnGiveReward), on normal difficulty and a first playthrough.</p>`;
 const place=()=>{const band=qsEl('qsBand');if(!band)return;band.querySelectorAll('.qsbplot[data-k]').forEach(plot=>{const k=plot.dataset.k,px=plot.clientWidth||600,step=px/(QS_MAXLV-1),D=16,lanes=[];
  plot.querySelectorAll('.qsdot').forEach(d=>d.remove());
  vis.filter(q=>q.t===k).sort((a,b)=>a.lv-b.lv||a.n.localeCompare(b.n)).forEach(q=>{const x=(q.lv-1)*step;let ln=lanes.findIndex(e=>x-e>=D);if(ln<0){ln=lanes.length;lanes.push(-1e9)}lanes[ln]=x;
   const st=qsState(q.g),b=document.createElement('button');b.type='button';b.className='qsdot '+st+(QS.sel===q.g?' on':'')+(q.p==='ep1'?' hos':'');b.dataset.g=q.g;b.style.left='calc('+qsX(q.lv).toFixed(2)+'% - '+(D/2)+'px)';b.style.top=(6+ln*(D+2))+'px';
   const m=qsXp(q,my);b.title=q.n+' · level '+q.lv+' · '+QS_NAMES[st]+' · '+(q.p==='ep1'?'Hearts of Stone XP '+qsPct(m):m<1?'5% XP':'full XP');b.setAttribute('aria-label',b.title);b.onclick=()=>qsSelect(q.g,true);plot.appendChild(b)});
  plot.style.height=Math.max(1,lanes.length)*(D+2)+10+'px'})};
 place();QS.place=place}
function qsRenderView(){const host=qsEl('qsView');
 qsEl('qsVBand').classList.toggle('on',QS.view==='band');qsEl('qsVList').classList.toggle('on',QS.view==='list');qsEl('qsVBand').setAttribute('aria-pressed',String(QS.view==='band'));qsEl('qsVList').setAttribute('aria-pressed',String(QS.view==='list'));
 if(QS.view==='band')qsRenderBand(host);else qsRenderList(host)}

// ---- the detail panel ----
function qsRenderDetail(){const el=qsEl('qsDetail'),q=QS.sel&&QS.byG.get(QS.sel);
 if(!q){el.innerHTML='<div class="qsempty"><p>Choose a quest to see its objectives and journal text.</p></div>';el.classList.remove('has');return}
 el.classList.add('has');
 const st=qsState(q.g),sv=qsSaveState(q.g),hand=QS.store.manual[q.g],haveSave=!!QS.store.save,cur=qsCurrent(q),my=qsMy();
 const saveLine=!haveSave?'No save imported: use <b>My progress</b> below, or import a save.':`In your save: <b>${QS_NAMES[sv]}</b>${sv==='none'?' (no journal entry)':''}`+(hand?` · you marked it <b>${QS_NAMES[hand]}</b>`:'');
 el.innerHTML=`<button type="button" class="btn qsback" id="qsBack" aria-label="Back to the list">◀ Back</button><h2 class="qstitle">${qsIcon(st)}<span>${qsEsc(q.n)}</span></h2>
  <p class="qsmeta">${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · ${q.lv==null?'<span title="not computed yet">level —</span>':'level '+q.lv}</p>
  <p class="qsxp">${qsEsc(qsXpText(q,my))}</p><p class="qssave">${saveLine}</p>
  ${st==='active'?`<div class="qscur"><h3>Current objective${cur.length>1?'s':''}</h3>${cur.length?`<ul>${cur.map(t=>`<li>${qsEsc(t)}</li>`).join('')}</ul>`:'<p class="dim">Not known: the save has no active objective for it.</p>'}</div>`:''}
  <div class="qsprog" role="radiogroup" aria-label="My progress"><span class="qsplabel">My progress</span>${QS_MARKS.map(s=>`<button type="button" class="btn qsmark${st===s?' on':''}" role="radio" aria-checked="${st===s}" data-s="${s}">${qsIcon(s)}${QS_NAMES[s]}</button>`).join('')}${hand?'<button type="button" class="qsclear" id="qsClear">Follow my save</button>':''}</div>
  <h3 class="qsh3">Journal</h3><div class="qsdesc" id="qsDesc" tabindex="0"><p class="dim">Loading…</p></div>
  <h3 class="qsh3">Objectives</h3>${q.o.length?`<ul class="qsobjs">${q.o.map(([g,t])=>{const s=QS.store.save&&QS.store.save.o[g]||'none';return`<li class="${s}">${qsIcon(s)}<span>${qsEsc(t)}</span></li>`}).join('')}</ul>`:'<p class="dim">No objectives listed.</p>'}`;
 el.querySelectorAll('.qsmark').forEach(b=>{b.onclick=()=>qsMark(q.g,b.dataset.s)});const c=qsEl('qsClear');if(c)c.onclick=()=>qsMark(q.g,null);qsEl('qsBack').onclick=()=>{qsEl('screenQ').classList.remove('qs-detail');const r=document.querySelector('.qsrow.on,.qsdot.on');if(r)r.focus()};
 const d=qsEl('qsDesc'),want=q.g;
 qsDescLoad().then(D=>{if(QS.sel!==want)return;d.textContent='';const t=D[q.id];if(!t||!t.length){d.innerHTML='<p class="dim">This quest has no journal text.</p>';return}t.forEach(x=>{const p=document.createElement('p');glMarkup(p,x,[]);d.appendChild(p)})},
  e=>{if(QS.sel===want)d.innerHTML=`<p class="dim">${QS_DESC?'The journal text could not be loaded. Check your connection and try again.':'Journal text is not included in this build.'}</p>`})}
function qsSelect(g,focus){QS.sel=g;const q=QS.byG.get(g);if(q&&q.r!==QS.region&&!(QS.view==='list'&&glWords(QS.q).length)){QS.region=q.r}qsRenderAll();
 qsEl('screenQ').classList.add('qs-detail');if(innerWidth<=900&&focus)qsEl('qsDetail').scrollIntoView({block:'start'})}

// ---- progress by hand ----
function qsMark(g,s){if(s===null)delete QS.store.manual[g];else QS.store.manual[g]=s;qsTouch();qsRenderAll()}
function qsRenderAll(){if(!QS.data)return;qsRenderRegs();qsRenderNext();qsRenderView();qsRenderDetail();qsChip()}

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
function qsFromJournal(j){if(!j||!QS.data)return null;const q={},o={};
 j.forEach(([g,s])=>{const st=QS_SAVE[s];if(!st)return;if(QS.byG.has(g))q[g]=st;else if(QS.byObj.has(g))o[g]=st});return{q,o}}
function qsCounts(stateOf){const c={done:0,active:0,failed:0,inactive:0,none:0};QS.data.quests.forEach(q=>{c[stateOf(q.g)]++});return c}
// what importing would change: counts now and after, and the quests whose hand mark disagrees with the save
function qsCompare(J){const now=qsCounts(qsState),keep=qsCounts(g=>QS.store.manual[g]||J.q[g]||'none'),repl=qsCounts(g=>J.q[g]||'none');
 const diff=QS.data.quests.filter(q=>QS.store.manual[q.g]&&QS.store.manual[q.g]!==(J.q[q.g]||'none'));return{now,keep,repl,diff}}
function qsApplyJournal(J,name,mode){QS.store.save={at:Date.now(),file:String(name||'').slice(0,120),q:J.q,o:J.o};if(mode==='replace')QS.store.manual={};qsTouch()}

// ---- screen ----
function qsBind(){
 qsEl('qsVBand').onclick=()=>{QS.view='band';qsRenderView()};qsEl('qsVList').onclick=()=>{QS.view='list';qsRenderView()};
 const chip=qsEl('qsChip');chip.onclick=e=>{e.stopPropagation();qsMenu(qsEl('qsMenu').hidden)};
 document.addEventListener('click',e=>{const m=qsEl('qsMenu');if(!m.hidden&&!e.composedPath().includes(qsEl('qsChipWrap')))qsMenu(false)});   // composedPath: a click on a button the menu has just re-drawn is still inside it
 document.addEventListener('keydown',e=>{const m=qsEl('qsMenu');if(!m.hidden&&e.key==='Escape'){e.preventDefault();qsMenu(false);chip.focus()}});
 addEventListener('resize',()=>{if(QS.shown&&QS.view==='band'&&QS.place)QS.place()})}
function qsClose(){QS.shown=false;const w=qsEl('qsChipWrap');if(w){w.hidden=true;qsMenu(false)}}
function qsOpen(){if(QS.shown)return;QS.shown=true;if(!QS.init){QS.init=true;qsBind()}qsStoreInit();
 qsEl('qsChipWrap').hidden=false;qsChip();
 const body=qsEl('qsBody');qsEl('qsLoadMsg').hidden=true;qsEl('qsLoadMsg').textContent='';
 qsLoad().then(()=>{if(!QS.shown)return;body.hidden=false;QS.lv=qsMy();qsRenderAll()},()=>{body.hidden=true;qsEl('qsLoadMsg').hidden=false;qsEl('qsLoadMsg').textContent='The quest list could not be loaded. Check your connection and try again.'})}
function qsSync(){if(QS.shown&&QS.data&&QS.lv!==qsMy()){QS.lv=qsMy();qsRenderAll()}}   // the Level field changed: zones, Next up and tooltips follow it
