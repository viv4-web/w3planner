// ---- Quests (v33): status, list, level band, Next up, detail, progress. Data: data/QUESTS.json (tools/make_quests.py, docs/QUESTS.md); the journal text is game content and exists in the live build only ----
// The screen is S.scr 'q' and lives in the link as s1Q; nothing else is in the link. Progress is kept in this browser (localStorage 'w3p.quests.v1') and in an exported file, never in the link or anywhere else.
const QS_URL=/*@file:QUESTS*/, QS_RULES_URL=/*@file:QUEST-RULES*/, QS_FAILS_URL=/*@file:QUEST_FAILS*/, QS_QF_URL=/*@lazyjs:questfails*/, QS_DESC=/*@quests*/null;
const QS_KEY='w3p.quests.v1';
const QS_KINDS=[['main','Main'],['side','Secondary'],['contract','Contracts'],['treasure','Treasure hunts'],['gwent','Gwent'],['race','Races'],['fist','Fistfights']];
const QS_NAMES={none:'Not started',active:'Active',done:'Done',failed:'Failed',inactive:'Inactive'},QS_MARKS=['none','active','done','failed'];
const QS_SAVE={JS_Success:'done',JS_Active:'active',JS_Failed:'failed',JS_Inactive:'inactive'};
const QS_ICON={none:'<circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6"/>',active:'<circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="8" cy="8" r="2.6" fill="currentColor"/>',
 done:'<path d="M3 8.5l3.2 3.2L13 4.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',failed:'<path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
 inactive:'<circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="2.2 2.2"/>'};
const QS_DONE_KEY='w3p.quests.banddone';   // '1' | '0': the Level band's own "Show done" toggle, off by default (v33d)
const QS_TDONE_KEY='w3p.quests.timedone';   // '1' | '0': the Timeline's own "Show done" toggle, off by default (v34)
const QS_TSCOPE_KEY='w3p.quests.timescope';   // 'base' | 'hos' | 'bob': the Timeline's scope last chosen in this browser (v34.1); the default is the base game
const QS_VIEW_KEY='w3p.quests.view';   // 'list' | 'band': the view last chosen in this browser (v33b); the default is the List
const QS={showDone:false,timeDone:false,tscope:'base',R:null,data:null,byG:null,byObj:null,byDesc:null,load:null,err:false,region:'ve',view:'list',kind:'all',hide:false,q:'',sel:null,descP:null,desc:null,init:false,shown:false,lv:0,open:false,reveal:new Set(),cells:new Set(),
 store:{manual:{},save:null,changed:0},ok:true,confirm:false};
// the Level band's dot shapes, one per type (14 px, inline SVG; status = fill: outline for not started, filled for active, outline with a small x for failed, dashed for inactive); the colours are CSS tokens (--t-main ...) in quests.css
const QS_STAR=Array.from({length:10},(_,i)=>{const a=-Math.PI/2+i*Math.PI/5,r=i%2?2.9:6.6;return(7+r*Math.cos(a)).toFixed(2)+','+(7+r*Math.sin(a)).toFixed(2)}).join(' ');
const QS_SHAPE={main:'<polygon points="7,0.8 13.2,7 7,13.2 0.8,7"/>',side:'<circle cx="7" cy="7" r="5.8"/>',contract:'<polygon points="7,1 13.2,12.4 0.8,12.4"/>',treasure:'<rect x="1.4" y="1.4" width="11.2" height="11.2"/>',
 gwent:'<polygon points="7,0.9 12.6,4 12.6,10 7,13.1 1.4,10 1.4,4"/>',race:'<polygon points="'+QS_STAR+'"/>',fist:'<polygon points="5.4,1 8.6,1 8.6,5.4 13,5.4 13,8.6 8.6,8.6 8.6,13 5.4,13 5.4,8.6 1,8.6 1,5.4 5.4,5.4"/>'};
const qsShape=(kind,st,legend)=>`<svg class="qsshape qs-${st}" viewBox="0 0 14 14" width="14" height="14" aria-hidden="true" focusable="false">${QS_SHAPE[kind]}${st==='failed'&&!legend?'<path class="x" d="M4.6 4.6l4.8 4.8M9.4 4.6l-4.8 4.8"/>':''}${st==='done'&&!legend?'<path class="ck" d="M4.2 7.2l2 2 3.6-4"/>':''}</svg>`;
const qsEl=id=>document.getElementById(id);
const qsEsc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const qsIcon=(st,kind)=>`<svg class="qsic qs-${st}${kind?' t-'+kind:''}" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">${QS_ICON[st]||QS_ICON.none}</svg>`;

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
function qsRead(){try{const v=localStorage.getItem(QS_VIEW_KEY);if(v==='list'||v==='band'||v==='time'||v==='fails')QS.view=v;QS.showDone=localStorage.getItem(QS_DONE_KEY)==='1';QS.timeDone=localStorage.getItem(QS_TDONE_KEY)==='1';const sc=localStorage.getItem(QS_TSCOPE_KEY);if(sc==='base'||sc==='hos'||sc==='bob')QS.tscope=sc}catch(e){}   // the view first: it must win on load whether or not any progress is stored (v33c; v33b skipped it when nothing was stored)
 QS.ok=qsProbe();   // v39.3: storage is "blocked" only when a probe key cannot be written, read back and removed right now; reading or parsing our own data says nothing about it
 let raw=null;try{raw=localStorage.getItem(QS_KEY)}catch(e){}
 if(!raw)return;try{const c=qsClean(JSON.parse(raw));if(c)QS.store=c}catch(e){QS.bad=true}}   // unreadable data (not JSON, damaged): start empty, the next save replaces it
function qsProbe(){try{const k=QS_KEY+'.probe';localStorage.setItem(k,'1');const ok=localStorage.getItem(k)==='1';localStorage.removeItem(k);return ok}catch(e){return false}}
function qsSetDone(on){QS.showDone=on;try{localStorage.setItem(QS_DONE_KEY,on?'1':'0')}catch(e){}}
function qsSetTimeDone(on){QS.timeDone=on;try{localStorage.setItem(QS_TDONE_KEY,on?'1':'0')}catch(e){}}
function qsSetView(v){QS.view=v;QS.open=false;try{localStorage.setItem(QS_VIEW_KEY,v)}catch(e){}}
function qsWrite(){try{localStorage.setItem(QS_KEY,JSON.stringify(Object.assign({v:1},QS.store)));QS.ok=true;QS.bad=false}catch(e){QS.ok=qsProbe()}qsChip()}   // a real save clears a stuck 'blocked'; a failed one asks the probe (a one-off failure, a full quota: storage still works)
function qsTouch(){QS.store.changed=Date.now();qsWrite()}
const qsSaveState=g=>QS.store.save&&QS.store.save.q[g]||'none';
const qsState=g=>QS.store.manual[g]||qsSaveState(g);
const qsMarked=()=>QS.data?QS.data.quests.filter(q=>qsState(q.g)!=='none').length:0;
const qsHand=()=>Object.keys(QS.store.manual).length;
const qsHasProgress=()=>!!(qsHand()||QS.store.save);

// ---- data ----
function qsLoad(){if(QS.data)return Promise.resolve(QS.data);
 return QS.load||(QS.load=(async()=>{if(!(window.W3DATA&&W3DATA.QUESTS))await eqScript(QS_URL);const d=W3DATA.QUESTS;if(!d||!d.quests)throw new Error('empty');
  QS.data=d;QS.byG=new Map(d.quests.map(q=>[q.g,q]));QS.byObj=new Map();QS.byDesc=new Set();d.quests.forEach(q=>{q.o.forEach((g,i)=>QS.byObj.set(g,[q,i]));q.d.forEach(g=>QS.byDesc.add(g))});QS.regions=new Map(d.regions);
  try{if(!(window.W3DATA&&W3DATA.QUEST_RULES))await eqScript(QS_RULES_URL);const R=W3DATA.QUEST_RULES;if(R&&R.quests){R.gmap=new Map(R.gates.map(x=>[x.id,x]));R.pts=new Map(R.points);QS.R=R}}catch(e){QS.R=null}   // the timeline data is optional: without it the other views work
  try{if(!(window.W3DATA&&W3DATA.QUEST_FAILS))await eqScript(QS_FAILS_URL);if(!window.QF)await eqScript(QS_QF_URL);QF.init(W3DATA.QUEST_FAILS)}catch(e){}   // v39: the fail safeguard (questfails.js) is optional too
  return d})().catch(e=>{QS.load=null;QS.err=true;throw e}))}
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
// ---- story rules (v34: data/QUEST-RULES.json from the game's quest graphs): story point, gates ("fails at"), predecessors ----
// A gate is a story point of no return. A save has PASSED a gate when a quest the gate names as "done" is Done or a quest it names as "next" exists (any state): docs/QUESTS.md.
const qsRule=g=>QS.R&&QS.R.quests[g]||null;
const qsGates=lane=>QS.R?QS.R.gates.filter(x=>x.lane===lane).sort((a,b)=>a.x-b.x):[];
const qsPassed=gt=>gt.done.some(g=>qsState(g)==='done')||gt.next.some(g=>qsState(g)!=='none');
const qsOpenState=s=>s==='none'||s==='active'||s==='inactive';
const QS_SECTIONS=['p','a','i','b','3','e'];
function qsSection(){if(!QS.R)return -1;let best=-1;QS_SECTIONS.forEach((k,i)=>{if((QS.R.enter[k]||[]).some(g=>qsState(g)!=='none'))best=i});return best}   // the highest story section with a quest in the save
function qsCuts(q){const r=qsRule(q.g);return r&&r.c?r.c.map(([id,lv,how])=>({gate:QS.R.gmap.get(id),whole:lv==='q',how:how==='f'?'Failure':'Deactivate'})).filter(x=>x.gate):[]}
function qsFailsAt(q){const c=qsCuts(q).filter(x=>x.whole&&!qsPassed(x.gate)).sort((a,b)=>a.gate.x-b.gate.x)[0];return c?c.gate:null}   // the gate a quest that is still open fails at: the earliest in the story (the one the panel and the brackets use)
function qsMissLists(){   // per lane in use: the next gate not passed, the open quests that fail there, and the ones that only lose an objective
 const out=[];if(!QS.R||!QS.store.save)return out;const lanes=['b'];if(QS.data.quests.some(q=>q.p==='bob'&&qsState(q.g)!=='none'))lanes.push('w');
 lanes.forEach(l=>{const gt=qsGates(l).find(x=>!qsPassed(x));if(!gt)return;const whole=[],obj=[];
  QS.data.quests.forEach(q=>{if(!qsOpenState(qsState(q.g)))return;const c=qsCuts(q).filter(x=>x.gate===gt);if(!c.length)return;if(c.some(x=>x.whole))whole.push(q);else obj.push(q)});
  const my=qsMy(),by=(a,b)=>Math.abs((a.lv==null?999:a.lv)-my)-Math.abs((b.lv==null?999:b.lv)-my)||a.n.localeCompare(b.n);out.push({gate:gt,whole:whole.sort(by),obj:obj.sort(by)})});return out}
const qsRank=q=>window.QF?QF.rank(q.g):0;   // v39: -1 for a quest that another quest would fail (shown first)
function qsNextUp(){const my=qsMy(),all=QS.data.quests;QS.nextFail=new Map();
 const miss=[];qsMissLists().forEach(m=>m.whole.forEach(q=>{QS.nextFail.set(q.g,m.gate.name);miss.push(q)}));
 const act=all.filter(q=>qsState(q.g)==='active'&&!QS.nextFail.has(q.g)).sort((a,b)=>Math.abs((a.lv==null?999:a.lv)-my)-Math.abs((b.lv==null?999:b.lv)-my)||a.n.localeCompare(b.n));
 const home=(miss[0]||act[0]||{r:QS.region}).r,fresh=all.filter(q=>qsState(q.g)==='none'&&q.lv!=null&&qsXp(q,my)>=1&&!QS.nextFail.has(q.g)).sort((a,b)=>Math.abs(a.lv-my)-Math.abs(b.lv-my)||(a.r===home?0:1)-(b.r===home?0:1)||a.lv-b.lv||a.n.localeCompare(b.n));
 const risk=(window.QF?QF.risk():[]).filter(q=>!QS.nextFail.has(q.g)),rk=new Set(risk.map(q=>q.g));   // v39: a quest another open quest would fail comes first
 return miss.concat(risk,act.filter(q=>!rk.has(q.g)),fresh.filter(q=>!rk.has(q.g))).slice(0,4)}
function qsRenderNext(){const el=qsEl('qsNext'),list=qsNextUp(),my=qsMy();
 el.innerHTML=`<h3>Next up</h3><div class="qscards">${list.map(q=>{const st=qsState(q.g),cur=st==='active'?qsCurrent(q):[],fg=QS.nextFail.get(q.g);
  return`<button type="button" class="qscard t-${q.t}${fg?' fails':''}${QS.sel===q.g?' on':''}" data-g="${q.g}">${qsIcon(st,q.t)}<span class="qscn"><b>${qsEsc(q.n)}</b><small>${qsEsc(QS.regions.get(q.r))} · level ${qsLevelText(q)} · ${QS_NAMES[st]}</small><em${fg?' class="qsfail"':''}>${fg?'Fails at '+qsEsc(fg):st==='active'?(cur.length?(cur[0]===null?cur.length+' active objective'+(cur.length>1?'s':'')+' (text not in this build)':qsEsc(cur[0])+(cur.length>1?' (+'+(cur.length-1)+')':'')):'Current objective: not known'):qsEsc(qsXp(q,my)>=1?'Full XP at your level':'')}</em></span></button>`}).join('')||'<p class="qshint">Nothing left to suggest.</p>'}</div>`;
 el.querySelectorAll('.qscard').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true)})}
// the Missable panel (above Next up, only with a save): open quests that fail at the next gate the save has not passed
function qsRenderMiss(){const el=qsEl('qsMiss'),L=qsMissLists().filter(m=>m.whole.length||m.obj.length);el.hidden=!L.length;if(!L.length){el.textContent='';return}
 const chip=q=>{const st=qsState(q.g);return`<button type="button" class="qsmi t-${q.t}${QS.sel===q.g?' on':''}" data-g="${q.g}">${qsIcon(st,q.t)}<b>${qsEsc(q.n)}</b><small>${qsEsc(QS.regions.get(q.r))} · ${qsLevelText(q)}</small></button>`};
 el.innerHTML=L.map(m=>`<section class="qsmissec" aria-label="Missable before ${qsEsc(m.gate.name)}"><h3>Missable before <b>${qsEsc(m.gate.name)}</b> <span class="qsmn">${m.whole.length}</span></h3>
  ${m.whole.length?`<div class="qsmis">${m.whole.map(chip).join('')}</div>`:'<p class="qshint">No open quest fails there.</p>'}
  ${m.obj.length?`<details class="qsmobj"><summary>Also lose an objective there (${m.obj.length})</summary><div class="qsmis">${m.obj.map(chip).join('')}</div></details>`:''}</section>`).join('')+'<small class="qsmfoot">From the game\'s quest graphs</small>';
 el.querySelectorAll('.qsmi').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true)})}

// ---- the views ----
function qsKindName(k){return(QS_KINDS.find(x=>x[0]===k)||[0,k])[1]}
function qsRows(){   // the list: ordered by level; a search looks in every region
 const w=glWords(QS.q),all=w.length;let l=(all?QS.data.quests:qsInRegion(QS.region)).slice();
 if(QS.kind!=='all')l=l.filter(q=>q.t===QS.kind);if(QS.hide)l=l.filter(q=>qsState(q.g)!=='done');if(all)l=l.filter(q=>w.every(x=>glN(q.n).includes(x)));
 return l.sort((a,b)=>(a.lv==null)-(b.lv==null)||a.lv-b.lv||a.n.localeCompare(b.n))}
function qsRenderList(host){const reg=qsInRegion(QS.region),cnt=k=>reg.filter(q=>k==='all'||q.t===k).length,old=host.querySelector('#qsRows'),top=old?old.scrollTop:0;
 host.innerHTML=`<div class="qsfilters"><div class="qschips" role="group" aria-label="Quest type">${[['all','All']].concat(QS_KINDS).map(([k,n])=>`<button type="button" class="qschip${k==='all'?'':' t-'+k}${QS.kind===k?' on':''}" data-k="${k}" aria-pressed="${QS.kind===k}"${cnt(k)?'':' disabled'}>${n}</button>`).join('')}<button type="button" class="qschip hide${QS.hide?' on':''}" id="qsHide" aria-pressed="${QS.hide}">Hide done</button></div>
  <input id="qsQ" class="qssearch" type="search" placeholder="Search all quests" aria-label="Search all quests" autocomplete="off" spellcheck="false" value="${qsEsc(QS.q)}"></div><div class="qsrows" id="qsRows"></div>`;
 const rows=qsEl('qsRows'),l=qsRows(),all=glWords(QS.q).length;
 rows.innerHTML=l.map(q=>{const st=qsState(q.g),ch=qsByChoice(q);return`<button type="button" class="qsrow t-${q.t} st-${st}${ch?' choice':''}${QS.sel===q.g?' on':''}" data-g="${q.g}" aria-label="${qsEsc(q.n)}, ${qsKindName(q.t)}, ${QS_NAMES[st]}, level ${qsLevelText(q)}${ch?', can fail by a choice':''}">${qsIcon(st,q.t)}<span class="qsrn2"><b>${qsEsc(q.n)}</b>${all?`<small>${qsEsc(QS.regions.get(q.r))}</small>`:''}</span>${ch?'<span class="qsbych">by choice</span>':''}${qsLvSpan(q)}</button>`}).join('')||`<p class="qshint">${QS.q.trim()?'Nothing matches '+qsEsc(QS.q.trim())+'.':'No quests here.'}</p>`;
 rows.scrollTop=top;host.querySelectorAll('.qschip[data-k]').forEach(b=>{b.onclick=()=>{QS.kind=b.dataset.k;qsRenderView()}});qsEl('qsHide').onclick=()=>{QS.hide=!QS.hide;qsRenderView()};
 const inp=qsEl('qsQ');inp.oninput=()=>{QS.q=inp.value;const p=inp.selectionStart;qsRenderView();const n=qsEl('qsQ');n.focus();n.setSelectionRange(p,p)};
 rows.querySelectorAll('.qsrow').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true);b.onkeydown=e=>{if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;const rs=[...rows.querySelectorAll('.qsrow')],i=rs.indexOf(b)+(e.key==='ArrowDown'?1:-1);if(i>=0&&i<rs.length){e.preventDefault();rs[i].focus()}}})}
// ---- the Level band: x = quest levels from the lowest to the highest in this region (at least 24 px per level), one row per type; dots of one level side by side in the level's slot, three lines at most ("+n" opens the rest) ----
const QS_DOT=14,QS_STEP=16,QS_SLOT=24,QS_LABEL=112;
function qsBandTools(){return`<div class="qsbtools"><button type="button" class="qschip${QS.showDone?' on':''}" id="qsShowDone" aria-pressed="${QS.showDone}" title="Show the quests you have done as faint dots with a check">Show done</button></div>`}
function qsRenderBand(host){const my=qsMy(),reg=qsInRegion(QS.region),vis=reg.filter(q=>q.lv!=null&&(QS.showDone||qsState(q.g)!=='done')),nol=reg.filter(q=>q.lv==null&&(QS.showDone||qsState(q.g)!=='done')).length;
 const tools=qsBandTools(),bind=()=>{qsEl('qsShowDone').onclick=()=>{qsSetDone(!QS.showDone);qsRenderView();const n=qsEl('qsShowDone');if(n)n.focus()}};
 const note=`<p class="qsbnote">${QS.showDone?'Done quests are shown faintly, with a check.':'Done quests are hidden: turn on Show done to see them.'} Each type has its own shape and colour; outline = not started, filled = active, outline with × = failed. ${nol?nol+' quest'+(nol===1?' has':' have')+' no level yet and '+(nol===1?'is':'are')+' only in the List. ':''}The hatched zone is where a quest gives only 5% XP (the game's rule, r4Game.ws OnGiveReward, normal difficulty, first playthrough).</p>`;
 if(!vis.length){host.innerHTML=tools+'<p class="qshint">No quests to show here: every quest of this region is done or has no level.</p>'+note;bind();QS.place=null;return}
 const lo=Math.min(my,...vis.map(q=>q.lv)),hi=Math.max(my,...vis.map(q=>q.lv)),span=hi-lo+1,   // the axis always holds the player's level (v33d)
  kinds=QS_KINDS.filter(([k])=>vis.some(q=>q.t===k));
 const avail=(host.clientWidth||900)-QS_LABEL-22,slot=Math.max(QS_SLOT,avail/span),W=Math.round(slot*span),per=Math.max(1,Math.floor(slot/QS_STEP)),cap=per*3;
 const lx=lv=>(Math.max(lo,Math.min(hi,lv))-lo+.5)*slot,zoneLv=my-10,zw=zoneLv>=lo?(Math.min(zoneLv,hi)-lo+1)*slot:0,flip=lx(my)>W-90;
 const zone=zw?`<i class="qsz5" style="width:${zw}px"></i>`:'',line=`<i class="qsme" style="left:${lx(my)}px"></i>`;
 let rows='';
 kinds.forEach(([k,n])=>{const byLv=new Map();vis.filter(q=>q.t===k).sort((a,b)=>qsRank(a)-qsRank(b)||(qsState(a.g)==='done')-(qsState(b.g)==='done')||(qsState(b.g)==='active')-(qsState(a.g)==='active')||a.n.localeCompare(b.n)).forEach(q=>{if(!byLv.has(q.lv))byLv.set(q.lv,[]);byLv.get(q.lv).push(q)});
  let lines=1,dots='';
  byLv.forEach((list,lv)=>{const key=k+':'+lv,open=QS.cells.has(key),over=list.length>cap,shown=over&&!open?list.slice(0,cap-1):list,total=shown.length+(over?1:0),nl=Math.ceil(total/per);lines=Math.max(lines,nl);
   const x0=(lv-lo)*slot;
   const place=(i,n)=>{const ln=Math.floor(i/per),inLine=Math.min(per,total-ln*per);return'left:'+(x0+(slot-inLine*QS_STEP)/2+(i%per)*QS_STEP+1).toFixed(1)+'px;top:'+(8+ln*QS_STEP)+'px'};
   shown.forEach((q,i)=>{const st=qsState(q.g);dots+=`<button type="button" class="qsdot t-${q.t} ${st}${QS.sel===q.g?' on':''}" data-g="${q.g}" style="${place(i)}" aria-label="${qsEsc(q.n)}, ${qsKindName(q.t)}, ${QS_NAMES[st]}, level ${q.lv}">${qsShape(q.t,st)}</button>`});
   if(over)dots+=`<button type="button" class="qsmore" data-cell="${key}" style="${place(shown.length)}" aria-expanded="${open}" aria-label="${open?'Show fewer quests':(list.length-shown.length)+' more quests at level '+lv}">${open?'−':'+'+(list.length-shown.length)}</button>`});
  rows+=`<div class="qsbrow t-${k}" style="min-height:${Math.max(56,lines*QS_STEP+16)}px"><div class="qsblabel">${n}</div><div class="qsbplot" style="width:${W}px">${zone}${line}${dots}</div></div>`});
 const axis=Array.from({length:span},(_,i)=>`<span style="left:${((i+.5)*slot).toFixed(1)}px">${lo+i}</span>`).join('');
 host.innerHTML=tools+`<div class="qsband" id="qsBand"><div class="qsbinner" style="width:${QS_LABEL+W}px"><div class="qsbhead"><span></span><div class="qsbplot head" style="width:${W}px">${zone}${zw?`<b class="qszl" style="left:6px">${zw>=56?'5% XP':'5%'}</b><b class="qszl full" style="left:${zw+6}px">full XP</b>`:''}${line}<b class="qsml${flip?' flip':''}" style="left:${lx(my)}px">You · ${my}</b></div></div>${rows}<div class="qsbaxis"><span></span><div class="qsbplot axis" style="width:${W}px">${axis}</div></div></div></div><ul class="qslegend" aria-label="Quest types">${QS_KINDS.map(([k,n])=>`<li class="t-${k}">${qsShape(k,'none',true)}<span>${n}</span></li>`).join('')}</ul>`+note;
 bind();host.querySelectorAll('.qsdot').forEach(d=>{d.onclick=()=>qsSelect(d.dataset.g,true);d.onmouseenter=d.onfocus=()=>qsTip(d);d.onmouseleave=d.onblur=()=>qsTipHide()});
 host.querySelectorAll('.qsmore').forEach(b=>{b.onclick=()=>{const k=b.dataset.cell;if(QS.cells.has(k))QS.cells.delete(k);else QS.cells.add(k);qsRenderBand(host);const n=host.querySelector('.qsmore[data-cell="'+k+'"]');if(n)n.focus()}});
 QS.place=null}
// ---- the Timeline (v34, decluttered in v34.1 and v34.2): columns = the story sections, rows = regions; three scopes (Base game, Hearts of Stone, Blood and Wine: a single lane laid out by quest level); the points of no return are numbered, bars only on column edges ----
const QS_TCOLS=[['p','Prologue'],['a','Act I'],['i','Isle of Mists'],['b','Battle of Kaer Morhen'],['3','Act III'],['e','Epilogue']],QS_TROWS=['wo','vz','ve','no','sk','km','oth'];
const QS_TSCOPES=[['base','Base game',null],['hos','Hearts of Stone','h'],['bob','Blood and Wine','w']];   // [scope, tab, lane key]
// v34.2 measures (px): a marker is 20, the gap 6, a cell has 10 px at the sides and 8 above and below, at most 10 markers a line and 2 lines a cell; a column is 100 px at least; a badge in the header is 24
const QS_TM=20,QS_TGAP=6,QS_TSTEP=QS_TM+QS_TGAP,QS_TPADX=10,QS_TPADY=8,QS_TPER=10,QS_TLINES=2,QS_TMIN=100,QS_TBADGE=24,QS_TGROUP=19;
// the width of a column from the marker count of its fullest cell (across the regions): the markers of its longer line (two lines, 10 at most), the cell padding, 100 px at least (min: what its header badges need)
const qsColW=(n,min)=>Math.max(min||QS_TMIN,QS_TMIN,Math.min(QS_TPER,Math.ceil(n/QS_TLINES))*QS_TSTEP-QS_TGAP+2*QS_TPADX);
// the leftover width of the box is shared among the columns in proportion to their content width: -> new widths (the same when there is no leftover: a phone scrolls)
function qsShare(ws,avail){const sum=ws.reduce((a,b)=>a+b,0),left=avail-sum;return left>0&&sum>0?ws.map(w=>w+left*w/sum):ws.slice()}
// how a cell of nF markers that fail at the next gate (their own group, first) and nR others lays out in a column w px wide: markers per line, two lines at most over both groups; over that the last place is a "+N" chip ("−" once expanded)
function qsCellPlace(nF,nR,w,open){const per=Math.max(1,Math.min(QS_TPER,Math.floor((w-2*QS_TPADX+QS_TGAP)/QS_TSTEP))),cap=(f,r,b)=>{const fs=Math.min(f,per*b),rem=b-Math.ceil(fs/per);return[fs,Math.min(r,per*rem),rem]};
 const[f0,r0]=cap(nF,nR,QS_TLINES),over=nF+nR>f0+r0;let fS,rS,rem;if(open||!over){fS=nF;rS=nR;rem=1}else{[fS,rS,rem]=cap(nF,nR,QS_TLINES);if(rS>0)rS--;else fS--}
 const chipR=nR>0&&rem>0,chip=!over?null:chipR?{blk:'r',idx:rS}:{blk:'f',idx:fS},fLines=Math.ceil((fS+(chip&&chip.blk==='f'?1:0))/per),rLines=Math.ceil((rS+(chip&&chip.blk==='r'?1:0))/per);   // the chip is the next place after the last marker shown, in the group it follows
 return{per,over,fS,rS,chip,fLines,rLines,lines:fLines+rLines,more:nF+nR-fS-rS}}
// does a quest fail at this gate (a whole-quest cutoff on it) and is it still open
const qsFailsAtGate=(q,gt)=>!!gt&&qsOpenState(qsState(q.g))&&qsCuts(q).some(x=>x.whole&&x.gate===gt);
// v35: a quest with no story point is "ungated" (the game files show no story gate for it) or "unknown" (there is a gate we can't read yet): `u` in data/QUEST-RULES.json; null = placed.
// `k` = can fail by a choice: [["q"]] its own conversation, [["q", quest]] a choice in that other quest. Not part of the gates, the Missable panel or Next up.
const qsPlaceKind=q=>{const r=qsRule(q.g);return r&&r.s?null:(r&&r.u==='ungated'?'ungated':'unknown')};
const qsPack=q=>q.p==='ep1'?'hos':q.p==='bob'?'bob':'base';   // the Timeline scope a quest belongs to
const qsChoices=q=>{const r=qsRule(q.g);return r&&r.k?r.k:[]};
const qsByChoice=q=>qsChoices(q).length>0;
// v34.3 "Missable, story point unknown": the quests with a whole-quest cutoff in this lane and no story point (so no place in the grid), grouped by the gate they fail at. Only with a save, like the Missable panel.
// An open quest sits under the earliest gate it has not passed (for the next gate that is exactly qsFailsAtGate, the panel's and the brackets' test); a quest whose gates are all passed, or that is Done or Failed, under its earliest cutoff gate.
const qsLaneCuts=(q,lane)=>qsCuts(q).filter(x=>x.whole&&x.gate.lane===lane).sort((a,b)=>a.gate.x-b.gate.x);
function qsStripGate(q,lane){const c=qsLaneCuts(q,lane);if(!c.length)return null;const u=qsOpenState(qsState(q.g))?c.find(x=>!qsPassed(x.gate)):null;return(u||c[0]).gate}
function qsMissUnknown(lane,keys){   // -> [{k: the gate's key entry, list}], the next gate not passed first, then the other gates not passed, then the passed ones, each in story order
 if(!QS.R||!QS.store.save)return[];const by=new Map();
 QS.data.quests.forEach(q=>{if(qsRule(q.g)&&qsRule(q.g).s)return;const g=qsStripGate(q,lane);if(!g)return;if(!by.has(g))by.set(g,[]);by.get(g).push(q)});
 return keys.filter(k=>by.has(k.g)).map(k=>({k,list:by.get(k.g)})).sort((a,b)=>a.k.passed-b.k.passed||a.k.g.x-b.k.g.x)}
function qsMissUnknownHtml(groups,gt){const vis=groups.map(x=>({k:x.k,list:qsCellOrder(x.list.filter(q=>QS.timeDone||qsState(q.g)!=='done'),gt)})).filter(x=>x.list.length);if(!vis.length)return'';
 return`<section class="qsmu" id="qsMU" aria-labelledby="qsMUh"><h3 class="qsgkh" id="qsMUh">Missable, story point unknown</h3><p class="qsbnote">These can be missed, but the game files don't say where in the story they open.</p><div class="qsmugs">${vis.map(x=>`<div class="qsmug${x.k.passed?' passed':''}" data-gate="${x.k.g.id}" role="group" aria-label="Fails at ${qsEsc(x.k.name)}${x.k.passed?', passed':''}"><span class="qsfl">fails at <b class="qsgb mini${x.k.passed?' passed':''}" title="${qsEsc(x.k.name+(x.k.code?' ('+x.k.code+')':''))}${x.k.passed?' · passed':''}">${x.k.n}</b><em>${qsEsc(x.k.name)}</em></span><div class="qsmud">${x.list.map(q=>qsDotHtml(q,'')).join('')}</div></div>`).join('')}</div></section>`}
// a cell's order: quests that fail at the next gate first, then Main, then the other types in the legend's order; then active first, done last, by name
function qsCellOrder(list,gt){const ty=q=>QS_KINDS.findIndex(k=>k[0]===q.t),fl=q=>qsFailsAtGate(q,gt)?0:1,
 ord=(a,b)=>(qsState(a.g)==='done')-(qsState(b.g)==='done')||(qsState(b.g)==='active')-(qsState(a.g)==='active')||a.n.localeCompare(b.n);
 return list.slice().sort((a,b)=>fl(a)-fl(b)||ty(a)-ty(b)||ord(a,b))}
// the gates of a lane in story order, numbered 1..n, with the short name and the quest code (the badge's tooltip) and whether the save has passed each
function qsGateKey(lane){return qsGates(lane).map((g,i)=>({g,n:i+1,passed:qsPassed(g),name:g.name.replace(/\s*\(Q\d{3}\)$/,''),code:g.code||'',real:!!g.real}))}
// where a gate stands: on the edge between two columns (base game: a whole number; the expansions: the edge before its level's column), or inside a column (base game, a fraction)
function qsGatePlace(k,lane,lo,ncol){const x=k.g.x;if(lane)return{edge:Math.max(0,Math.min(ncol,Math.ceil(x-1e-9)-lo))};return Math.abs(x-Math.round(x))<1e-9?{edge:Math.round(x)}:{col:Math.floor(x)}}
function qsSetScope(s){if(QS_TSCOPES.some(x=>x[0]===s)){QS.tscope=s;try{localStorage.setItem(QS_TSCOPE_KEY,s)}catch(e){}}}
function qsDotHtml(q,pos){const st=qsState(q.g),fg=qsOpenState(st)?qsFailsAt(q):null,ch=qsByChoice(q);
 return`<button type="button" class="qsdot t-${q.t} ${st}${fg?' fails':''}${ch?' choice':''}${QS.sel===q.g?' on':''}" data-g="${q.g}" style="${pos}" aria-label="${qsEsc(q.n)}, ${qsKindName(q.t)}, ${QS_NAMES[st]}, level ${qsLevelText(q)}${fg?', fails at '+qsEsc(fg.name):''}${ch?', can fail by a choice':''}">${qsShape(q.t,st)}</button>`}
// the badge of a gate: its number (the key and the chart); grey once passed, a gold outline for the real cutoff; the tooltip has the name and the quest code
const qsGateBadge=(k,style,cls)=>`<b class="qsgb${k.passed?' passed':''}${k.real?' real':''}${cls?' '+cls:''}"${style?` style="${style}"`:''} title="${qsEsc(k.name+(k.code?' ('+k.code+')':''))}${k.passed?' · passed':''}${k.real?' · real cutoff':''}">${k.n}</b>`;
function qsGateKeyHtml(keys){return`<h3 class="qsgkh">Points of no return</h3><ol class="qsgkey" aria-label="Points of no return">${keys.map(k=>`<li class="qsgk${k.passed?' passed':''}${k.real?' real':''}" title="${qsEsc(k.name+(k.code?' ('+k.code+')':''))}">${qsGateBadge(k)}<span>${qsEsc(k.name)}${k.real?' <em>real cutoff</em>':''}${k.passed?' <small>· passed</small>':''}</span></li>`).join('')}</ol>`}
// the markers of a cell in a column starting at x0, w wide: the group that fails at the next gate (gt) under a thin orange bracket "fails at <n>", then the others; -> {html, h} (h: the height the cell needs)
function qsSwarm(list,x0,w,key,gt,gn){
 const open=QS.cells.has(key),F=list.filter(q=>qsFailsAtGate(q,gt)),R=list.filter(q=>!qsFailsAtGate(q,gt)),P=qsCellPlace(F.length,R.length,w,open),px=i=>x0+QS_TPADX+(i%P.per)*QS_TSTEP;
 const fy=QS_TPADY+(F.length?QS_TGROUP:0),ry=fy+P.fLines*QS_TSTEP+(F.length?2:0),fpos=i=>`left:${px(i).toFixed(1)}px;top:${fy+Math.floor(i/P.per)*QS_TSTEP}px`,rpos=i=>`left:${px(i).toFixed(1)}px;top:${ry+Math.floor(i/P.per)*QS_TSTEP}px`;
 let h='';
 if(F.length&&P.fS>0){const bw=Math.min(P.fS,P.per)*QS_TSTEP-QS_TGAP+8,gl=P.fLines*QS_TSTEP-QS_TGAP+4;
  h+=`<span class="qsfl" style="left:${(x0+QS_TPADX-4).toFixed(1)}px;top:${QS_TPADY-1}px" aria-hidden="true">fails at <b class="qsgb mini">${gn}</b></span><i class="qsfb" style="left:${(x0+QS_TPADX-4).toFixed(1)}px;top:${QS_TPADY+14}px;width:${bw}px;height:${gl+5}px" aria-hidden="true"></i>`}
 h+=F.slice(0,P.fS).map((q,i)=>qsDotHtml(q,fpos(i))).join('')+R.slice(0,P.rS).map((q,i)=>qsDotHtml(q,rpos(i))).join('');
 if(P.chip)h+=`<button type="button" class="qsmore" data-cell="${key}" style="${P.chip.blk==='f'?fpos(P.chip.idx):rpos(P.chip.idx)}" aria-expanded="${open}" aria-label="${open?'Show fewer quests':P.more+' more quests'}">${open?'−':'+'+P.more}</button>`;
 const bottom=P.rLines?ry+P.rLines*QS_TSTEP-QS_TGAP:(P.fLines?fy+P.fLines*QS_TSTEP-QS_TGAP:0);
 return{html:h,h:bottom?bottom+QS_TPADY:0}}
function qsRenderTime(host){
 const scope=QS.tscope,lane=(QS_TSCOPES.find(x=>x[0]===scope)||[])[2]||null;
 const tools=`<div class="qsbtools"><button type="button" class="qschip${QS.timeDone?' on':''}" id="qsShowDoneT" aria-pressed="${QS.timeDone}" title="Show the quests you have done as faint dots with a check">Show done</button></div>`;
 if(!QS.R){host.innerHTML=tools+'<p class="qshint">The timeline data could not be loaded.</p>';qsEl('qsShowDoneT').onclick=()=>{qsSetTimeDone(!QS.timeDone);qsRenderView()};return}
 const R=QS.R,Qs=QS.data.quests,known=q=>qsRule(q.g)&&qsRule(q.g).s,drawn=q=>known(q)&&(QS.timeDone||qsState(q.g)!=='done'),sec=qsSection(),keys=qsGateKey(lane||'b'),avail=(host.clientWidth||900)-QS_LABEL-22,
  next=keys.find(k=>!k.passed)||null;   // the next gate the save has not passed: the quests that fail there are grouped in their cells
 // columns: base game = the story sections, expansions = the quest levels; a column is as wide as the fullest cell in it (and its header badges), then the leftover width is shared
 let cols,cells=new Map(),lo=0,rows=[];   // cols: [{k,n}]; cells: row|col -> [quests]
 if(!lane){rows=QS_TROWS.map(r=>({k:r,name:QS.regions.get(r)}));cols=QS_TCOLS.map(([k,n])=>({k,n}));
  Qs.filter(q=>known(q)&&drawn(q)&&QS_TCOLS.some(c=>c[0]===qsRule(q.g).s)).forEach(q=>{const key=q.r+'|'+qsRule(q.g).s;if(!cells.has(key))cells.set(key,[]);cells.get(key).push(q)})}
 else{const all=Qs.filter(q=>known(q)&&qsRule(q.g).s===lane),lvs=all.map(q=>q.lv).filter(v=>v!=null).sort((a,b)=>a-b),gx=keys.map(k=>k.g.x);
  lo=Math.floor(Math.min(lvs[Math.min(3,lvs.length-1)],...gx));const hi=Math.ceil(Math.max(lvs[lvs.length-1],...gx));   // the axis starts at the 4th lowest level: a stray level-1 quest is drawn at the left edge, its level is in the tooltip
  cols=Array.from({length:hi-lo+1},(_,i)=>({k:lo+i,n:String(lo+i)}));rows=[{k:'lane',name:R.pts.get(lane)}];
  all.filter(drawn).forEach(q=>{const key='lane|'+(q.lv==null?lo:Math.max(lo,q.lv));if(!cells.has(key))cells.set(key,[]);cells.get(key).push(q)})}
 const place=keys.map(k=>qsGatePlace(k,lane,lo,cols.length)),inCol=cols.map(()=>0),onEdge=cols.map(()=>0).concat(0);   // badges inside a column, badges on the edge before a column
 place.forEach(p=>{if(p.col!=null)inCol[p.col]++;else onEdge[p.edge]++});
 cols.forEach((c,i)=>{c.max=Math.max(0,...rows.map(r=>(cells.get(r.k+'|'+c.k)||[]).length));c.w=qsColW(c.max,Math.max(inCol[i]*QS_TBADGE+12,onEdge[i]?onEdge[i]*QS_TBADGE+4:0))});
 qsShare(cols.map(c=>c.w),avail).forEach((w,i)=>{cols[i].w=w});
 let acc=0;cols.forEach(c=>{c.x=acc;acc+=c.w});const W=Math.round(acc),at=u=>{const i=Math.max(0,Math.min(cols.length-1,Math.floor(u)));return cols[i].x+(u-i)*cols[i].w},edgeX=e=>e>=cols.length?acc:cols[e].x;
 // where "You" are: the middle of the current section (Act III follows the gates passed there); in an expansion, the highest level the save has started
 let youU=null;if(!lane&&sec>=0){youU=sec+.5;if(sec===4){const p=keys.filter(k=>k.g.x>=4&&k.g.x<5&&k.passed);youU=(p.length?p[p.length-1].g.x:4)+.12}}
 if(lane){const st=Qs.filter(q=>known(q)&&qsRule(q.g).s===lane&&qsState(q.g)!=='none'&&q.lv!=null).map(q=>Math.max(lo,q.lv));if(st.length)youU=Math.max(...st)-lo+.5}
 const youX=youU==null?null:at(youU),you=youX==null?'':`<i class="qsme" style="left:${youX.toFixed(1)}px"></i>`,
  bg=cols.map((c,i)=>(!lane&&i===sec?`<i class="qscolbg" style="left:${c.x.toFixed(1)}px;width:${c.w.toFixed(1)}px"></i>`:'')+(i?`<i class="qscol" style="left:${c.x.toFixed(1)}px"></i>`:'')).join('');
 // bars: only on an edge (one bar for all the gates there, grey when every one of them is passed)
 const edges=new Map();keys.forEach((k,i)=>{const p=place[i];if(p.edge!=null){if(!edges.has(p.edge))edges.set(p.edge,[]);edges.get(p.edge).push(k)}});
 const bars=[...edges].map(([e,ks])=>`<i class="qsgate${ks.every(k=>k.passed)?' passed':''}" data-gates="${ks.map(k=>k.n).join(',')}" style="left:${edgeX(e).toFixed(1)}px"></i>`).join('');
 // badges in the header: on an edge, side by side from the bar; inside a column, side by side from its left
 const seen=new Map(),badges=keys.map((k,i)=>{const p=place[i],id=p.edge!=null?'e'+p.edge:'c'+p.col,j=seen.get(id)||0;seen.set(id,j+1);
  const left=p.edge!=null?edgeX(p.edge)+j*QS_TBADGE:cols[p.col].x+6+12+j*QS_TBADGE;return qsGateBadge(k,'left:'+left.toFixed(1)+'px')}).join('');
 const head=`<div class="qsbhead qstlhead"><span></span><div class="qsbplot head" style="width:${W}px">${bg}${bars}${!lane?cols.map((c,i)=>`<b class="qstc${i===sec?' on':''}" style="left:${(c.x+6).toFixed(1)}px;width:${(c.w-12).toFixed(1)}px">${qsEsc(c.n)}</b>`).join(''):''}${badges}${you}</div></div>`;
 let body='';
 rows.forEach(r=>{let dots='',hh=0;cols.forEach(c=>{const l=cells.get(r.k+'|'+c.k);if(!l)return;const o=qsSwarm(qsCellOrder(l,next&&next.g),c.x,c.w,'t:'+scope+':'+r.k+':'+c.k,next&&next.g,next?next.n:0);dots+=o.html;hh=Math.max(hh,o.h)});
  body+=`<div class="qsbrow${lane?' qslane':''}" style="min-height:${Math.max(56,hh)}px"><div class="qsblabel">${qsEsc(r.name)}</div><div class="qsbplot" style="width:${W}px">${bg}${bars}${you}${dots}</div></div>`});
 const axis=lane?cols.map(c=>`<span style="left:${(c.x+c.w/2).toFixed(1)}px">${c.n}</span>`).join(''):'',
  lab=youX==null?'':`<b class="qsyou${youX<64?' lft':youX>W-70?' rgt':''}" style="left:${youX.toFixed(1)}px;top:${lane?24:4}px">You are here</b>`;
 body+=`<div class="qsbaxis qstfoot"><span></span><div class="qsbplot axis" style="width:${W}px;height:${lane?46:28}px">${bg}${bars}${you}${axis}${lab}</div></div>`;
 const strip=qsMissUnknown(lane||'b',keys),inStrip=new Set(strip.flatMap(x=>x.list.map(q=>q.g)));   // the quests in the strip are not repeated in the two sections below
 const un=Qs.filter(q=>!known(q)&&!inStrip.has(q.g)&&qsPack(q)===scope&&(QS.timeDone||qsState(q.g)!=='done')),ungated=un.filter(q=>qsPlaceKind(q)==='ungated'),unknown=un.filter(q=>qsPlaceKind(q)==='unknown');
 host.innerHTML=`<div class="qstbar">${tools}</div>
  ${qsGateKeyHtml(keys)}${lane?`<p class="qsbnote qsscnote">Laid out by quest level: every ${qsEsc(R.pts.get(lane))} quest shares one story point in the game's quest graphs.</p>`:''}
  <div class="qsband qstl" id="qsTL"><div class="qsbinner" style="width:${QS_LABEL+W}px">${head}${body}</div></div>
  ${qsMissUnknownHtml(strip,next&&next.g)}
  <ul class="qslegend" aria-label="Quest types">${QS_KINDS.map(([k,n])=>`<li class="t-${k}">${qsShape(k,'none',true)}<span>${n}</span></li>`).join('')}<li class="qsl-fb"><i class="qsfb"></i><span>Fails at the next gate you haven't passed</span></li><li class="qsl-more"><span class="qsmore">+N</span><span>More in this cell</span></li><li class="qsl-ch"><i class="qsch" aria-hidden="true"></i><span>Can fail by a choice</span></li></ul>
  ${qsUnplacedHtml('ungated',ungated,scope,avail)}${qsUnplacedHtml('unknown',unknown,scope,avail)}
  <p class="qsbnote">${QS.timeDone?'Done quests are shown faintly, with a check.':'Done quests are hidden: turn on Show done to see them.'} ${lane?'Quests are laid out by their level.':'Columns are the story sections the game\'s quest graphs place a quest in.'} The numbered gates are the points of no return; quests that fail at the next one you have not passed are grouped first in their cell, under an orange bracket. From the game's quest graphs.</p>`;
 qsEl('qsShowDoneT').onclick=()=>{qsSetTimeDone(!QS.timeDone);qsRenderView();const n=qsEl('qsShowDoneT');if(n)n.focus()};
 [['qsNoGate','ungClosed',true],['qsNotComputed','unkOpen',false]].forEach(([id,k,inv])=>{const d=qsEl(id);if(d)d.ontoggle=e=>{QS[k]=inv?!e.target.open:e.target.open}});
 host.querySelectorAll('.qsdot').forEach(d=>{d.onclick=()=>qsSelect(d.dataset.g,true);d.onmouseenter=d.onfocus=()=>qsTip(d);d.onmouseleave=d.onblur=()=>qsTipHide()});
 host.querySelectorAll('#qsTL .qsmore,.qsug .qsmore').forEach(b=>{b.onclick=()=>{const k=b.dataset.cell;if(QS.cells.has(k))QS.cells.delete(k);else QS.cells.add(k);qsRenderTime(host);const n=host.querySelector('.qsmore[data-cell="'+k+'"]');if(n)n.focus()}})}
// v35: the quests with no story point, below the strip, in two sections grouped by region like the grid rows (same markers, status fill, "+N" chips; a click opens the drawer).
// "No story gate found": the v35 placement found no story point for them; "Not computed yet": there is a gate we can't read. The strip's quests are not repeated; counts follow the scope tab, Show done and the save.
const QS_UNPL={ungated:{id:'qsNoGate',title:'No story gate found',help:'They open when you reach the place, meet the person or find the item. The game files show no story point for them.'},
 unknown:{id:'qsNotComputed',title:'Not computed yet',help:"The game files have a story gate for these that we can't read yet."}};
function qsUnplacedHtml(kind,list,scope,avail){if(!list.length)return'';const m=QS_UNPL[kind],open=kind==='ungated'?!QS.ungClosed:!!QS.unkOpen,by=new Map();
 list.forEach(q=>{if(!by.has(q.r))by.set(q.r,[]);by.get(q.r).push(q)});
 const rows=QS.data.regions.map(r=>r[0]).filter(k=>by.has(k)).map(k=>{const o=qsSwarm(qsCellOrder(by.get(k),null),0,avail,'u:'+scope+':'+kind+':'+k,null,0);
  return`<div class="qsbrow qsugrow" data-r="${k}"><div class="qsblabel">${qsEsc(QS.regions.get(k))}</div><div class="qsbplot" style="width:${avail}px;height:${Math.max(36,o.h)}px">${o.html}</div></div>`}).join('');
 return`<details class="qsug" id="${m.id}"${open?' open':''}><summary>${m.title} (${list.length})</summary><p class="qsbnote">${qsEsc(m.help)}</p><div class="qsugl">${rows}</div></details>`}
// one tooltip for dots: name, type · region · level, status (on hover and on keyboard focus)
function qsTip(d){const q=QS.byG.get(d.dataset.g),t=qsEl('qsTip');if(!q)return;const st=qsState(q.g),m=qsXp(q,qsMy());
 t.innerHTML=`<b class="t-${q.t}">${qsEsc(q.n)}</b><span>${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · level ${qsLevelText(q)}</span><span>${QS_NAMES[st]}${q.hs?' · Hearts of Stone XP '+qsPct(m):m<1?' · 5% XP':''}</span>${(qsOpenState(st)&&qsFailsAt(q))?'<span class="qsfail">Fails at '+qsEsc(qsFailsAt(q).name)+'</span>':''}${qsByChoice(q)?'<span class="qschoicet">Can fail by a choice</span>':''}${window.QF?QF.tip(q):''}`;t.hidden=false;
 const r=d.getBoundingClientRect(),w=t.offsetWidth,h=t.offsetHeight;t.style.left=Math.max(6,Math.min(innerWidth-w-6,r.left+r.width/2-w/2))+'px';t.style.top=(r.top-h-8>6?r.top-h-8:r.bottom+8)+'px'}
function qsTipHide(){const t=qsEl('qsTip');if(t)t.hidden=true}
function qsRenderView(){const host=qsEl('qsView'),sc=qsEl('screenQ');qsTipHide();
 [['qsVTime','time'],['qsVBand','band'],['qsVList','list'],['qsVFails','fails']].forEach(([id,v])=>{qsEl(id).classList.toggle('on',QS.view===v);qsEl(id).setAttribute('aria-pressed',String(QS.view===v))});
 sc.classList.toggle('qs-band',QS.view!=='list');sc.classList.toggle('qs-fails',QS.view==='fails'&&!!window.QF);sc.classList.toggle('qs-time',QS.view==='time');qsEl('qsScope').hidden=QS.view!=='time';qsEl('qsScope').querySelectorAll('.qssc').forEach(b=>{const on=b.dataset.scope===QS.tscope;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on))});sc.classList.toggle('qs-open',QS.view!=='list'&&QS.open);   // Level band and Timeline: the detail is a drawer
 if(QS.view==='time')qsRenderTime(host);else if(QS.view==='band')qsRenderBand(host);else if(QS.view==='fails'&&window.QF)QF.fails(host);else qsRenderList(host)}

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
// v35 "Can fail by choice" in the drawer: only the player's wording, never a scene output or a fact name.
function qsChoiceFill(q,el){el.textContent='';const ch=qsChoices(q);if(!ch.length)return;
 const h=document.createElement('h3');h.className='qsh3';h.textContent='Can fail by choice';el.appendChild(h);
 ch.forEach(e=>{const p=document.createElement('p');p.className='qsrule qschrow';
  if(e.length===1)p.textContent="A choice in this quest's conversation ends it as failed.";
  else{const o=QS.byG.get(e[1]);p.appendChild(document.createTextNode('Fails through a choice in '));
   if(o){const b=document.createElement('button');b.type='button';b.className='qslink t-'+o.t;b.dataset.g=o.g;b.textContent=o.n;b.onclick=()=>qsSelect(o.g,true);p.appendChild(b)}else p.appendChild(document.createTextNode('another quest'))}
  el.appendChild(p)});
 const f=document.createElement('small');f.className='qsmfoot';f.textContent="From the game's quest graphs.";el.appendChild(f)}
function qsRenderDetail(){const el=qsEl('qsDetail'),q=QS.sel&&QS.byG.get(QS.sel);
 if(!q){el.innerHTML='<button type="button" class="btn qsclose" id="qsClose" aria-label="Close">×</button><div class="qsempty"><p>Choose a quest to see its objectives and journal text.</p></div>';qsEl('qsClose').onclick=()=>qsCloseDrawer(true);el.classList.remove('has');return}
 el.classList.add('has');const hadFocus=document.activeElement&&document.activeElement.id==='qsClose';   // a re-draw (the text arriving) must not drop the focus
 const st=qsState(q.g),sv=qsSaveState(q.g),hand=QS.store.manual[q.g],haveSave=!!QS.store.save,cur=qsCurrent(q),my=qsMy(),T=qsTitles(q);
 const saveLine=!haveSave?'No save imported: use <b>My progress</b> below, or import a save.':`In your save: <b>${QS_NAMES[sv]}</b>${sv==='none'?' (no journal entry)':''}`+(hand?` · you marked it <b>${QS_NAMES[hand]}</b>`:'');
const rl=qsRule(q.g),cuts=qsCuts(q),afters=((rl&&rl.a)||[]).map(g=>QS.byG.get(g)).filter(Boolean),spn=rl&&rl.s?QS.R.pts.get(rl.s):null;
 const whole=cuts.filter(c=>c.whole),objs=cuts.filter(c=>!c.whole),gn=c=>`<b>${qsEsc(c.gate.name)}</b>${qsPassed(c.gate)?' <span class="dim">(passed in this save)</span>':''}`;
 const rulesHtml=!QS.R?'':`<div class="qsrules"><p class="qsrule">Story point: ${spn?'<b>'+qsEsc(spn)+'</b>':qsPlaceKind(q)==='ungated'?'<span class="qsnogate">no story gate found</span>':'<span title="not computed yet">— not computed yet</span>'}</p>
  ${afters.length?`<p class="qsrule qsafter">Opens after: ${afters.map(a=>`<button type="button" class="qslink t-${a.t}" data-g="${a.g}">${qsEsc(a.n)}</button>`).join(', ')}</p>`:''}
  ${whole.length?`<p class="qsrule qsfailsat">Fails at ${whole.map(gn).join(', ')}</p>`:''}
  ${objs.length?`<p class="qsrule qsloses">Loses an objective at ${objs.map(gn).join(', ')}</p>`:''}
  ${!whole.length&&!objs.length?`<p class="qsrule qsnomiss">${qsByChoice(q)?'No story gate fails this quest':'Not missable as far as computed'}</p>`:''}</div>`;
 const curHtml=cur.length?`<ul>${cur.map(t=>`<li>${t===null?'An active objective (its text is not included in this build)':qsEsc(t)}</li>`).join('')}</ul>`:'<p class="dim">Not known: the save has no active objective for it.</p>';
 el.innerHTML=`<button type="button" class="btn qsclose" id="qsClose" aria-label="Close">×</button><button type="button" class="btn qsback" id="qsBack" aria-label="Back to the list">◀ Back</button><h2 class="qstitle t-${q.t}">${qsIcon(st,q.t)}<span>${qsEsc(q.n)}</span></h2>
  <p class="qsmeta">${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · ${q.lv==null?'<span title="not computed yet">level —</span>':'level '+q.lv}</p>
  <p class="qsxp">${qsEsc(qsXpText(q,my))}</p><p class="qssave">${saveLine}</p>
  ${rulesHtml}${qsByChoice(q)?'<div class="qscfc" id="qsChoice"></div>':''}
  ${st==='active'?`<div class="qscur"><h3>Current objective${cur.length>1?'s':''}</h3>${curHtml}</div>`:''}
  <div class="qsprog t-${q.t}" role="radiogroup" aria-label="My progress"><span class="qsplabel">My progress</span>${QS_MARKS.map(s=>`<button type="button" class="btn qsmark${st===s?' on':''}" role="radio" aria-checked="${st===s}" data-s="${s}">${qsIcon(s)}${QS_NAMES[s]}</button>`).join('')}${hand?'<button type="button" class="qsclear" id="qsClear">Follow my save</button>':''}</div>
  <h3 class="qsh3">Journal</h3><div class="qsdesc" id="qsDesc" tabindex="0"></div>
  <h3 class="qsh3">Objectives</h3>${q.o.length?(T?`<ul class="qsobjs t-${q.t}">${q.o.map((g,i)=>{const s=QS.store.save&&QS.store.save.o[g]||'none';return`<li class="${s}">${qsIcon(s)}<span>${qsEsc(T[i]||'')}</span></li>`}).join('')}</ul>`:`<p class="dim">${QS_DESC?'Loading…':q.o.length+' objectives (their text is not included in this build).'}</p>`):'<p class="dim">No objectives listed.</p>'}`;
 el.querySelectorAll('.qsmark').forEach(b=>{b.onclick=()=>qsMark(q.g,b.dataset.s)});el.querySelectorAll('.qslink').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true)});const c=qsEl('qsClear');if(c)c.onclick=()=>qsMark(q.g,null);
 qsEl('qsBack').onclick=()=>{qsEl('screenQ').classList.remove('qs-detail');const r=document.querySelector('.qsrow.on');if(r)r.focus()};qsEl('qsClose').onclick=()=>qsCloseDrawer(true);
 const chb=qsEl('qsChoice');if(chb)qsChoiceFill(q,chb);
 qsJournal(q,qsEl('qsDesc'));if(hadFocus)qsEl('qsClose').focus({preventScroll:true});
 if(!T&&QS_DESC)qsDescLoad().then(D=>{QS.desc=D;if(QS.sel===q.g)qsRenderDetail();qsRenderNext()},()=>{})}
function qsSelect(g,focus){QS.sel=g;const q=QS.byG.get(g);if(q&&q.r!==QS.region&&!(QS.view==='list'&&glWords(QS.q).length)){QS.region=q.r}
 if(QS.view!=='list'){QS.open=true;QS.opener=g}qsRenderAll();qsEl('screenQ').classList.add('qs-detail');
 if(QS.view!=='list'){qsDrawerPlace();const c=qsEl('qsClose');if(c)c.focus({preventScroll:true})}else if(innerWidth<=900&&focus)qsEl('qsDetail').scrollIntoView({block:'start'})}
function qsDrawerPlace(){const tb=qsEl('topbar'),el=qsEl('qsDetail');el.style.top=(innerWidth>=600?Math.max(0,tb.getBoundingClientRect().bottom):0)+'px'}
function qsCloseDrawer(focus){if(!QS.open)return;QS.open=false;qsEl('screenQ').classList.remove('qs-open');if(focus){const d=document.querySelector('.qsdot[data-g="'+QS.opener+'"]')||document.querySelector('.qscard.on,.qsmi.on');if(d)d.focus()}}

// ---- progress by hand ----
function qsMark(g,s){if(s===null)delete QS.store.manual[g];else QS.store.manual[g]=s;qsTouch();qsRenderAll()}
function qsRenderAll(){if(!QS.data)return;qsRenderRegs();qsRenderMiss();qsRenderNext();qsRenderView();qsRenderDetail();qsChip();if(QS.open)qsDrawerPlace()}

// ---- the chip: Saved in this browser | export | load | reset ----
const qsWhen=t=>t?new Date(t).toLocaleString([],{dateStyle:'medium',timeStyle:'short'}):'never';
function qsChip(){const b=qsEl('qsChip');if(!b)return;if(!QS.ok)QS.ok=qsProbe();b.textContent=(QS.ok?(qsHasProgress()?'Saved in this browser':'No progress yet'):'Not saved in this browser')+' ▾';b.classList.toggle('warn',!QS.ok);
 const m=qsEl('qsMenu');if(m.hidden)return;qsMenuFill()}
function qsMenuFill(){const m=qsEl('qsMenu'),n=QS.data?qsMarked():0,h=qsHand(),s=QS.store.save;
 m.innerHTML=`<p class="qsmeta2"><b>${n}</b> quest${n===1?'':'s'} marked${h?' · '+h+' by hand':''}${s?' · save: '+qsEsc(s.file||'imported')+' ('+qsEsc(qsWhen(s.at))+')':''}</p><p class="qsmeta2">Last change: ${qsEsc(qsWhen(QS.store.changed))}</p>
  ${QS.ok?'':'<p class="qsmeta2 bad">This browser blocks storage for the site: your marks work until you close the page. Export them to keep them.</p>'}${QS.bad?'<p class="qsmeta2">The progress saved earlier could not be read. It is replaced when you mark a quest.</p>':''}
  <button type="button" class="btn" id="qsExport" role="menuitem">Export progress (.json)</button>
  <label class="btn" role="menuitem" tabindex="0" id="qsLoadLbl" for="qsLoadFile">Load progress file</label><input class="vh" id="qsLoadFile" type="file" accept=".json,application/json" aria-label="Load a progress file">
  ${QS.confirm?'<p class="qsmeta2 bad">Remove all your quest progress from this browser?</p><div class="qsrow2"><button type="button" class="btn qsdanger" id="qsResetYes">Reset</button><button type="button" class="btn" id="qsResetNo">Keep it</button></div>':'<button type="button" class="btn" id="qsReset" role="menuitem">Reset</button>'}
  <p class="qsmsg" id="qsMsg2" role="status"></p>`;
 qsEl('qsExport').onclick=qsExport;qsEl('qsLoadFile').onchange=e=>{if(e.target.files[0])qsLoadFile(e.target.files[0]);e.target.value=''};const lb=qsEl('qsLoadLbl');lb.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();qsEl('qsLoadFile').click()}};
 const r=qsEl('qsReset');if(r)r.onclick=()=>{QS.confirm=true;qsMenuFill();qsEl('qsResetNo').focus()};
 const y=qsEl('qsResetYes');if(y){y.onclick=()=>{QS.store={manual:{},save:null,changed:Date.now()};QS.confirm=false;try{localStorage.removeItem(QS_KEY)}catch(e){QS.ok=qsProbe()}qsMenuFill();qsRenderAll();qsEl('qsMsg2').textContent='Your quest progress was removed.'};qsEl('qsResetNo').onclick=()=>{QS.confirm=false;qsMenuFill();qsEl('qsReset').focus()}}}
function qsMenu(open){const m=qsEl('qsMenu'),b=qsEl('qsChip');if(open){QS.ok=qsProbe();qsChip()}m.hidden=!open;b.setAttribute('aria-expanded',String(open));QS.confirm=false;if(open)qsMenuFill()}
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
 const sw=v=>{qsSetView(v);qsEl('screenQ').classList.remove('qs-detail');qsRenderView();qsRenderDetail()};qsEl('qsVTime').onclick=()=>sw('time');qsEl('qsVBand').onclick=()=>sw('band');qsEl('qsVList').onclick=()=>sw('list');qsEl('qsVFails').onclick=()=>sw('fails');
 qsEl('qsScope').querySelectorAll('.qssc').forEach(b=>{b.onclick=()=>{qsSetScope(b.dataset.scope);QS.open=false;qsEl('screenQ').classList.remove('qs-detail');qsRenderView();qsRenderDetail()}});
 const chip=qsEl('qsChip');chip.onclick=e=>{e.stopPropagation();qsMenu(qsEl('qsMenu').hidden)};
 document.addEventListener('click',e=>{const m=qsEl('qsMenu');if(!m.hidden&&!e.composedPath().includes(qsEl('qsChipWrap')))qsMenu(false)});   // composedPath: a click on a button the menu has just re-drawn is still inside it
 document.addEventListener('keydown',e=>{const m=qsEl('qsMenu');if(!m.hidden&&e.key==='Escape'){e.preventDefault();qsMenu(false);chip.focus()}});
 let rt=0;addEventListener('resize',()=>{if(!QS.shown||!QS.data)return;clearTimeout(rt);rt=setTimeout(()=>{if(QS.view!=='list')qsRenderView();if(QS.open)qsDrawerPlace()},120)});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&QS.shown&&QS.open&&qsEl('qsMenu').hidden){e.preventDefault();qsCloseDrawer(true)}})}
function qsClose(){QS.shown=false;const w=qsEl('qsChipWrap');if(w){w.hidden=true;qsMenu(false)}}
function qsOpen(){if(QS.shown)return;QS.shown=true;if(!QS.init){QS.init=true;qsBind()}qsStoreInit();
 qsEl('qsChipWrap').hidden=false;qsChip();
 const body=qsEl('qsBody');qsEl('qsLoadMsg').hidden=true;qsEl('qsLoadMsg').textContent='';
 qsLoad().then(()=>{if(!QS.shown)return;body.hidden=false;QS.lv=qsMy();qsRenderAll();   // the objective titles (Next up) come with the lazy text file
   if(QS_DESC&&!QS.desc)qsDescLoad().then(D=>{QS.desc=D;if(QS.shown){qsRenderNext();qsRenderDetail()}},()=>{})},
  ()=>{body.hidden=true;qsEl('qsLoadMsg').hidden=false;qsEl('qsLoadMsg').textContent='The quest list could not be loaded. Check your connection and try again.'})}
function qsSync(){if(QS.shown&&QS.data&&QS.lv!==qsMy()){QS.lv=qsMy();qsRenderAll()}}   // the Level field changed: zones, Next up and tooltips follow it

// ---- Handoff from the old address (v37): merge what it sent (HANDOFF, app.js) into localStorage. Only the five keys of this screen; every value is checked; nothing newer is overwritten ----
const HO_KEYS=[QS_KEY,QS_VIEW_KEY,QS_DONE_KEY,QS_TDONE_KEY,QS_TSCOPE_KEY],HO_PREF={[QS_VIEW_KEY]:/^(list|band|time|fails)$/,[QS_DONE_KEY]:/^[01]$/,[QS_TDONE_KEY]:/^[01]$/,[QS_TSCOPE_KEY]:/^(base|hos|bob)$/};
function hoParse(b64){const b=b64.replace(/-/g,'+').replace(/_/g,'/'),bin=atob(b+'='.repeat((4-b.length%4)%4)),o=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(bin,c=>c.charCodeAt(0))));
 if(!o||typeof o!=='object'||Array.isArray(o))return null;const out={};
 for(const k of HO_KEYS)if(Object.prototype.hasOwnProperty.call(o,k)&&typeof o[k]==='string'&&o[k].length<=800000)out[k]=o[k];return out}
function hoMerge(){const H=HANDOFF;if(!H.data&&!H.bad&&!H.big&&!H.stash)return;const msg=[];
 if(H.big)msg.push('Your quest progress was too large to bring over automatically from the old address.');
 if(H.data||H.bad){let ok=false,n=0;
  try{const o=H.data?hoParse(H.data):null;
   if(o){ok=true;
    for(const k of HO_KEYS){if(!(k in o))continue;const have=localStorage.getItem(k);
     if(k===QS_KEY){const c=qsClean(JSON.parse(o[k]));if(!c)continue;let m=c;
      if(have!==null){const cur=qsClean(JSON.parse(have));if(!cur)continue;   // data of a version we cannot read stays as it is
       const newer=cur.changed>=c.changed;m={manual:Object.assign({},newer?c.manual:cur.manual,newer?cur.manual:c.manual),
        save:!cur.save?c.save:!c.save?cur.save:(c.save.at>cur.save.at?c.save:cur.save),changed:Math.max(c.changed,cur.changed)}}
      localStorage.setItem(k,JSON.stringify(Object.assign({v:1},m)));n++}
     else if(have===null&&HO_PREF[k].test(o[k])){localStorage.setItem(k,o[k]);n++}}
    QS.read=false}}
  catch(e){ok=false}
  if(!ok)msg.push('Your quest progress could not be brought over from the old address ('+(qsProbe()?'the data was unreadable':'this browser blocks storage for the site')+').');
  else if(n)msg.push('Your quest progress was brought over from the old address.')}
 if(msg.length||H.stash)hoShow(msg,H.stash)}
// v38: the notices stay on screen until the user closes them (x, or Esc); an ordinary notify() toast is not touched and does not hide them. The stash sentence keeps its text; "Re-import your save" opens the Import save dialog
// (no button in the offline package, which hides Import save: the plain sentence is shown there).
function hoShow(msg,stash){const n=document.getElementById('hoNotice'),m=document.getElementById('hoMsg');m.textContent=msg.join(' ');
 if(stash){if(msg.length)m.append(' ');const sb=document.getElementById('savebtn');
  if(sb&&!sb.hidden&&CFG.share!==false&&typeof impOpen==='function'){const a=document.createElement('button');a.type='button';a.className='holink';a.textContent='Re-import your save';a.onclick=()=>impOpen(a);m.append(a,' to restore your stash.')}
  else m.append('Re-import your save to restore your stash.')}
 n.hidden=false;document.body.classList.add('ho-open');document.documentElement.style.setProperty('--hoh',n.offsetHeight+'px')}
function hoClose(){document.getElementById('hoNotice').hidden=true;document.body.classList.remove('ho-open')}
document.getElementById('hoX').onclick=hoClose;
document.addEventListener('keydown',e=>{const n=document.getElementById('hoNotice');if(e.key!=='Escape'||n.hidden)return;
 if(n.contains(document.activeElement)||!document.querySelector('.impov:not([hidden]),.igov:not([hidden]),.skov:not([hidden]),#mutov:not([hidden])'))hoClose()});   // an open dialog takes its own Esc first
hoMerge();
// v39.3: a file dropped anywhere but on the Import dialog's drop zone would make the browser try to open it (Firefox answers with a security error: content may not load or link to a local file). Stop that and say where files go.
['dragover','drop'].forEach(t=>document.addEventListener(t,e=>{const d=e.dataTransfer;if(!d||![...(d.types||[])].includes('Files')||(e.target.closest&&e.target.closest('#impdrop')))return;e.preventDefault();
 if(t==='drop')notify('Files are not opened here. Use Import save for a save, or the Saved in this browser menu on the Quests tab to load a progress file.')}));
