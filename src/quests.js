// ---- Quests (v33): status, list, level band, Next up, detail, progress. Data: data/QUESTS.json (tools/make_quests.py, docs/QUESTS.md); the journal text is game content and exists in the live build only ----
// The screen is S.scr 'q' and lives in the link as s1Q; nothing else is in the link. Progress is kept in this browser (localStorage 'w3p.quests.v1') and in an exported file, never in the link or anywhere else.
const QS_URL=/*@file:QUESTS*/, QS_RULES_URL=/*@file:QUEST-RULES*/, QS_DESC=/*@quests*/null;
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
function qsRead(){try{const v=localStorage.getItem(QS_VIEW_KEY);if(v==='list'||v==='band'||v==='time')QS.view=v;QS.showDone=localStorage.getItem(QS_DONE_KEY)==='1';QS.timeDone=localStorage.getItem(QS_TDONE_KEY)==='1';const sc=localStorage.getItem(QS_TSCOPE_KEY);if(sc==='base'||sc==='hos'||sc==='bob')QS.tscope=sc}catch(e){}   // the view first: it must win on load whether or not any progress is stored (v33c; v33b skipped it when nothing was stored)
 try{const raw=localStorage.getItem(QS_KEY);QS.ok=true;if(!raw)return;const c=qsClean(JSON.parse(raw));if(c)QS.store=c}catch(e){QS.ok=false}}
function qsSetDone(on){QS.showDone=on;try{localStorage.setItem(QS_DONE_KEY,on?'1':'0')}catch(e){}}
function qsSetTimeDone(on){QS.timeDone=on;try{localStorage.setItem(QS_TDONE_KEY,on?'1':'0')}catch(e){}}
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
  QS.data=d;QS.byG=new Map(d.quests.map(q=>[q.g,q]));QS.byObj=new Map();QS.byDesc=new Set();d.quests.forEach(q=>{q.o.forEach((g,i)=>QS.byObj.set(g,[q,i]));q.d.forEach(g=>QS.byDesc.add(g))});QS.regions=new Map(d.regions);
  try{if(!(window.W3DATA&&W3DATA.QUEST_RULES))await eqScript(QS_RULES_URL);const R=W3DATA.QUEST_RULES;if(R&&R.quests){R.gmap=new Map(R.gates.map(x=>[x.id,x]));R.pts=new Map(R.points);QS.R=R}}catch(e){QS.R=null}   // the timeline data is optional: without it the other views work
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
function qsFailsAt(q){const c=qsCuts(q).find(x=>x.whole&&!qsPassed(x.gate));return c?c.gate:null}   // the gate a quest that is still open fails at
function qsMissLists(){   // per lane in use: the next gate not passed, the open quests that fail there, and the ones that only lose an objective
 const out=[];if(!QS.R||!QS.store.save)return out;const lanes=['b'];if(QS.data.quests.some(q=>q.p==='bob'&&qsState(q.g)!=='none'))lanes.push('w');
 lanes.forEach(l=>{const gt=qsGates(l).find(x=>!qsPassed(x));if(!gt)return;const whole=[],obj=[];
  QS.data.quests.forEach(q=>{if(!qsOpenState(qsState(q.g)))return;const c=qsCuts(q).filter(x=>x.gate===gt);if(!c.length)return;if(c.some(x=>x.whole))whole.push(q);else obj.push(q)});
  const my=qsMy(),by=(a,b)=>Math.abs((a.lv==null?999:a.lv)-my)-Math.abs((b.lv==null?999:b.lv)-my)||a.n.localeCompare(b.n);out.push({gate:gt,whole:whole.sort(by),obj:obj.sort(by)})});return out}
function qsNextUp(){const my=qsMy(),all=QS.data.quests;QS.nextFail=new Map();
 const miss=[];qsMissLists().forEach(m=>m.whole.forEach(q=>{QS.nextFail.set(q.g,m.gate.name);miss.push(q)}));
 const act=all.filter(q=>qsState(q.g)==='active'&&!QS.nextFail.has(q.g)).sort((a,b)=>Math.abs((a.lv==null?999:a.lv)-my)-Math.abs((b.lv==null?999:b.lv)-my)||a.n.localeCompare(b.n));
 const home=(miss[0]||act[0]||{r:QS.region}).r,fresh=all.filter(q=>qsState(q.g)==='none'&&q.lv!=null&&qsXp(q,my)>=1&&!QS.nextFail.has(q.g)).sort((a,b)=>Math.abs(a.lv-my)-Math.abs(b.lv-my)||(a.r===home?0:1)-(b.r===home?0:1)||a.lv-b.lv||a.n.localeCompare(b.n));
 return miss.concat(act,fresh).slice(0,4)}
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
 rows.innerHTML=l.map(q=>{const st=qsState(q.g);return`<button type="button" class="qsrow t-${q.t} st-${st}${QS.sel===q.g?' on':''}" data-g="${q.g}" aria-label="${qsEsc(q.n)}, ${qsKindName(q.t)}, ${QS_NAMES[st]}, level ${qsLevelText(q)}">${qsIcon(st,q.t)}<span class="qsrn2"><b>${qsEsc(q.n)}</b>${all?`<small>${qsEsc(QS.regions.get(q.r))}</small>`:''}</span>${qsLvSpan(q)}</button>`}).join('')||`<p class="qshint">${QS.q.trim()?'Nothing matches '+qsEsc(QS.q.trim())+'.':'No quests here.'}</p>`;
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
 kinds.forEach(([k,n])=>{const byLv=new Map();vis.filter(q=>q.t===k).sort((a,b)=>(qsState(a.g)==='done')-(qsState(b.g)==='done')||(qsState(b.g)==='active')-(qsState(a.g)==='active')||a.n.localeCompare(b.n)).forEach(q=>{if(!byLv.has(q.lv))byLv.set(q.lv,[]);byLv.get(q.lv).push(q)});
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
// ---- the Timeline (v34, decluttered in v34.1): columns = the story sections, rows = regions; three scopes (Base game, Hearts of Stone, Blood and Wine: a single lane laid out by quest level); gates are vertical bars numbered like the key above ----
const QS_TCOLS=[['p','Prologue'],['a','Act I'],['i','Isle of Mists'],['b','Battle of Kaer Morhen'],['3','Act III'],['e','Epilogue']],QS_TROWS=['wo','vz','ve','no','sk','km','oth'];
const QS_TSCOPES=[['base','Base game',null],['hos','Hearts of Stone','h'],['bob','Blood and Wine','w']],QS_TSTEP=18,QS_TMIN=100,QS_TPX=9,QS_TLINES=2;   // [scope, tab, lane key]; a marker's footprint is 18 px; a column is 9 px per marker of its fullest cell (two lines of 18 px), 100 px at least; a cell wraps to two lines
// the width of a column from the marker count of its fullest cell (across the regions)
const qsColW=n=>Math.max(QS_TMIN,QS_TPX*n+8);
// how a cell of n markers in a column w px wide lays out: per line, two lines at most; over that the last place is a "+N" chip (all of them, and a "−" chip, when the cell is expanded)
function qsCellLay(n,w,open){const per=Math.max(1,Math.floor((w-8)/QS_TSTEP)),cap=per*QS_TLINES,over=n>cap,shown=over&&!open?cap-1:n;return{per,cap,over,shown,more:n-shown,lines:Math.max(n?1:0,Math.ceil((shown+(over?1:0))/per))}}
// a cell's order: quests that will fail at the next gate first, then Main, then the other types in the legend's order; then the open ones, active first, done last, by name
function qsCellOrder(list){const ty=q=>QS_KINDS.findIndex(k=>k[0]===q.t),fl=q=>qsOpenState(qsState(q.g))&&qsFailsAt(q)?0:1,
 ord=(a,b)=>(qsState(a.g)==='done')-(qsState(b.g)==='done')||(qsState(b.g)==='active')-(qsState(a.g)==='active')||a.n.localeCompare(b.n);
 return list.slice().sort((a,b)=>fl(a)-fl(b)||ty(a)-ty(b)||ord(a,b))}
// the gates of a lane in story order, numbered 1..n, with the name and the quest code the key shows and whether the save has passed each
function qsGateKey(lane){return qsGates(lane).map((g,i)=>({g,n:i+1,passed:qsPassed(g),name:g.name.replace(/\s*\(Q\d{3}\)$/,''),code:g.code||'',real:!!g.real}))}
function qsSetScope(s){if(QS_TSCOPES.some(x=>x[0]===s)){QS.tscope=s;try{localStorage.setItem(QS_TSCOPE_KEY,s)}catch(e){}}}
function qsDotHtml(q,pos){const st=qsState(q.g),fg=qsOpenState(st)?qsFailsAt(q):null;
 return`<button type="button" class="qsdot t-${q.t} ${st}${fg?' fails':''}${QS.sel===q.g?' on':''}" data-g="${q.g}" style="${pos}" aria-label="${qsEsc(q.n)}, ${qsKindName(q.t)}, ${QS_NAMES[st]}, level ${qsLevelText(q)}${fg?', fails at '+qsEsc(fg.name):''}">${qsShape(q.t,st)}${fg?'<i class="qsfd"></i>':''}</button>`}
function qsSwarm(list,x0,w,key,top0){   // markers side by side in a cell of width w, two lines at most, the rest behind a "+N" chip -> {html, lines}
 const L=qsCellLay(list.length,w,QS.cells.has(key)),open=QS.cells.has(key),pos=i=>'left:'+(x0+4+(i%L.per)*QS_TSTEP).toFixed(1)+'px;top:'+(top0+Math.floor(i/L.per)*QS_TSTEP)+'px';
 let h=list.slice(0,L.shown).map((q,i)=>qsDotHtml(q,pos(i))).join('');
 if(L.over)h+=`<button type="button" class="qsmore" data-cell="${key}" style="${pos(L.shown)}" aria-expanded="${open}" aria-label="${open?'Show fewer quests':L.more+' more quests'}">${open?'−':'+'+L.more}</button>`;
 return{html:h,lines:L.lines}}
// the key above the chart: a numbered badge, the name and quest code, "· passed" for a gate the save is past; the real cutoff has a gold outlined badge
const qsGateBadge=(k,style)=>`<b class="qsgb${k.passed?' passed':''}${k.real?' real':''}"${style?` style="${style}"`:''} title="${qsEsc(k.name+(k.code?' ('+k.code+')':''))}${k.passed?' · passed':''}${k.real?' · real cutoff':''}">${k.n}</b>`;
function qsGateKeyHtml(keys){return`<ol class="qsgkey" aria-label="Points of no return"><li class="qsgkh">Points of no return</li>${keys.map(k=>`<li class="qsgk${k.passed?' passed':''}${k.real?' real':''}">${qsGateBadge(k)}<span>${qsEsc(k.name)}${k.code?` <small>(${qsEsc(k.code)})</small>`:''}${k.real?' <em>real cutoff</em>':''}${k.passed?' <small>· passed</small>':''}</span></li>`).join('')}</ol>`}
function qsRenderTime(host){
 const scope=QS.tscope,lane=(QS_TSCOPES.find(x=>x[0]===scope)||[])[2]||null;
 const tools=`<div class="qsbtools"><button type="button" class="qschip${QS.timeDone?' on':''}" id="qsShowDoneT" aria-pressed="${QS.timeDone}" title="Show the quests you have done as faint dots with a check">Show done</button></div>`;
 if(!QS.R){host.innerHTML=tools+'<p class="qshint">The timeline data could not be loaded.</p>';qsEl('qsShowDoneT').onclick=()=>{qsSetTimeDone(!QS.timeDone);qsRenderView()};return}
 const R=QS.R,Qs=QS.data.quests,known=q=>qsRule(q.g)&&qsRule(q.g).s,drawn=q=>known(q)&&(QS.timeDone||qsState(q.g)!=='done'),sec=qsSection(),keys=qsGateKey(lane||'b');
 // columns: base game = the story sections, expansions = the quest levels; a column is as wide as the fullest cell in it
 let cols,cells=new Map(),lo=0,rows=[];   // cols: [{label,w,k}]; cells: row|col -> [quests]
 if(!lane){rows=QS_TROWS.map(r=>({k:r,name:QS.regions.get(r)}));cols=QS_TCOLS.map(([k,n])=>({k,n}));
  Qs.filter(q=>known(q)&&drawn(q)&&QS_TCOLS.some(c=>c[0]===qsRule(q.g).s)).forEach(q=>{const key=q.r+'|'+qsRule(q.g).s;if(!cells.has(key))cells.set(key,[]);cells.get(key).push(q)})}
 else{const all=Qs.filter(q=>known(q)&&qsRule(q.g).s===lane),lvs=all.map(q=>q.lv).filter(v=>v!=null).sort((a,b)=>a-b),gx=keys.map(k=>k.g.x);
  lo=Math.floor(Math.min(lvs[Math.min(3,lvs.length-1)],...gx));const hi=Math.ceil(Math.max(lvs[lvs.length-1],...gx));   // the axis starts at the 4th lowest level: a stray level-1 quest is drawn at the left edge, its level is in the tooltip
  cols=Array.from({length:hi-lo+1},(_,i)=>({k:lo+i,n:String(lo+i)}));rows=[{k:'lane',name:R.pts.get(lane)}];
  all.filter(drawn).forEach(q=>{const key='lane|'+(q.lv==null?lo:Math.max(lo,q.lv));if(!cells.has(key))cells.set(key,[]);cells.get(key).push(q)})}
 cols.forEach(c=>{c.max=Math.max(0,...rows.map(r=>(cells.get(r.k+'|'+c.k)||[]).length));c.w=qsColW(c.max)});
  let acc=0;cols.forEach(c=>{c.x=acc;acc+=c.w});const W=Math.round(acc),at=u=>{const i=Math.max(0,Math.min(cols.length-1,Math.floor(u)));return cols[i].x+(u-i)*cols[i].w};   // u in column units
 const gu=x=>lane?x-lo+.5:x,gx=k=>at(gu(k.g.x)).toFixed(1);   // base-game gates are in column units, expansion gates in levels (a level's marker stands at the middle of its column)
 // where "You" are: the middle of the current section (Act III follows the gates passed there); in an expansion, the highest level the save has started
 let youU=null;if(!lane&&sec>=0){youU=sec+.5;if(sec===4){const p=keys.filter(k=>k.g.x>=4&&k.g.x<5&&k.passed);youU=(p.length?p[p.length-1].g.x:4)+.12}}
 if(lane){const st=Qs.filter(q=>known(q)&&qsRule(q.g).s===lane&&qsState(q.g)!=='none'&&q.lv!=null).map(q=>Math.max(lo,q.lv));if(st.length)youU=Math.max(...st)-lo+.5}
 const youX=youU==null?null:at(youU),you=youX==null?'':`<i class="qsme" style="left:${youX.toFixed(1)}px"></i>`,
  bg=cols.map((c,i)=>(!lane&&i===sec?`<i class="qscolbg" style="left:${c.x.toFixed(1)}px;width:${c.w.toFixed(1)}px"></i>`:'')+(i?`<i class="qscol" style="left:${c.x.toFixed(1)}px"></i>`:'')).join(''),
  bars=keys.map(k=>`<i class="qsgate${k.passed?' passed':''}" style="left:${gx(k)}px"></i>`).join('');
 const head=`<div class="qsbhead qstlhead"><span></span><div class="qsbplot head" style="width:${W}px">${bg}${bars}${!lane?cols.map((c,i)=>`<b class="qstc${i===sec?' on':''}" style="left:${(c.x+6).toFixed(1)}px;width:${(c.w-12).toFixed(1)}px">${qsEsc(c.n)}</b>`).join(''):''}${keys.map(k=>qsGateBadge(k,'left:'+gx(k)+'px')).join('')}${you}</div></div>`;
 let body='';
 rows.forEach(r=>{let dots='',lines=1;cols.forEach(c=>{const l=cells.get(r.k+'|'+c.k);if(!l)return;const o=qsSwarm(qsCellOrder(l),c.x,c.w,'t:'+scope+':'+r.k+':'+c.k,8);dots+=o.html;lines=Math.max(lines,o.lines)});
  body+=`<div class="qsbrow${lane?' qslane':''}" style="min-height:${Math.max(lane?96:48,lines*QS_TSTEP+16)}px"><div class="qsblabel">${qsEsc(r.name)}</div><div class="qsbplot" style="width:${W}px">${bg}${bars}${you}${dots}</div></div>`});
 const axis=lane?cols.map(c=>`<span style="left:${(c.x+c.w/2).toFixed(1)}px">${c.n}</span>`).join(''):'',
  lab=youX==null?'':`<b class="qsyou${youX<64?' lft':youX>W-70?' rgt':''}" style="left:${youX.toFixed(1)}px;top:${lane?24:4}px">You are here</b>`;
 body+=`<div class="qsbaxis qstfoot"><span></span><div class="qsbplot axis" style="width:${W}px;height:${lane?46:28}px">${bg}${bars}${you}${axis}${lab}</div></div>`;
 const unk=Qs.filter(q=>!known(q)).sort((a,b)=>(a.lv==null)-(b.lv==null)||a.lv-b.lv||a.n.localeCompare(b.n));
 host.innerHTML=`<div class="qstbar">${tools}</div>
  ${qsGateKeyHtml(keys)}${lane?`<p class="qsbnote qsscnote">Laid out by quest level: every ${qsEsc(R.pts.get(lane))} quest shares one story point in the game's quest graphs.</p>`:''}
  <div class="qsband qstl" id="qsTL"><div class="qsbinner" style="width:${QS_LABEL+W}px">${head}${body}</div></div>
  <ul class="qslegend" aria-label="Quest types">${QS_KINDS.map(([k,n])=>`<li class="t-${k}">${qsShape(k,'none',true)}<span>${n}</span></li>`).join('')}<li class="qsl-fd"><i class="qsfd"></i><span>Orange dot: fails at the next gate you haven't passed</span></li><li class="qsl-more"><span class="qsmore">+N</span><span>More in this cell</span></li></ul>
  <details class="qsunk" id="qsUnk"${QS.unkOpen?' open':''}><summary>Placement not computed yet (${unk.length})</summary><p class="qsbnote">The game's graphs give no story point for these quests (nothing gates them before the first act); they are only in the List and the Level band.</p><div class="qsunkl">${unk.map(q=>{const st=qsState(q.g);return`<button type="button" class="qsrow t-${q.t} st-${st}" data-g="${q.g}">${qsIcon(st,q.t)}<span class="qsrn2"><b>${qsEsc(q.n)}</b><small>${qsEsc(QS.regions.get(q.r))}</small></span>${qsLvSpan(q)}</button>`}).join('')}</div></details>
  <p class="qsbnote">${QS.timeDone?'Done quests are shown faintly, with a check.':'Done quests are hidden: turn on Show done to see them.'} ${lane?'Quests are laid out by their level.':'Columns are the story sections the game\'s quest graphs place a quest in.'} The numbered bars are the points of no return, and an orange dot marks a quest that fails at a bar your save has not passed. From the game's quest graphs.</p>`;
 qsEl('qsShowDoneT').onclick=()=>{qsSetTimeDone(!QS.timeDone);qsRenderView();const n=qsEl('qsShowDoneT');if(n)n.focus()};
 qsEl('qsUnk').ontoggle=e=>{QS.unkOpen=e.target.open};
 host.querySelectorAll('.qsdot').forEach(d=>{d.onclick=()=>qsSelect(d.dataset.g,true);d.onmouseenter=d.onfocus=()=>qsTip(d);d.onmouseleave=d.onblur=()=>qsTipHide()});
 host.querySelectorAll('.qsunkl .qsrow').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true)});
 host.querySelectorAll('#qsTL .qsmore').forEach(b=>{b.onclick=()=>{const k=b.dataset.cell;if(QS.cells.has(k))QS.cells.delete(k);else QS.cells.add(k);qsRenderTime(host);const n=host.querySelector('.qsmore[data-cell="'+k+'"]');if(n)n.focus()}})}
// one tooltip for dots: name, type · region · level, status (on hover and on keyboard focus)
function qsTip(d){const q=QS.byG.get(d.dataset.g),t=qsEl('qsTip');if(!q)return;const st=qsState(q.g),m=qsXp(q,qsMy());
 t.innerHTML=`<b class="t-${q.t}">${qsEsc(q.n)}</b><span>${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · level ${qsLevelText(q)}</span><span>${QS_NAMES[st]}${q.hs?' · Hearts of Stone XP '+qsPct(m):m<1?' · 5% XP':''}</span>${(qsOpenState(st)&&qsFailsAt(q))?'<span class="qsfail">Fails at '+qsEsc(qsFailsAt(q).name)+'</span>':''}`;t.hidden=false;
 const r=d.getBoundingClientRect(),w=t.offsetWidth,h=t.offsetHeight;t.style.left=Math.max(6,Math.min(innerWidth-w-6,r.left+r.width/2-w/2))+'px';t.style.top=(r.top-h-8>6?r.top-h-8:r.bottom+8)+'px'}
function qsTipHide(){const t=qsEl('qsTip');if(t)t.hidden=true}
function qsRenderView(){const host=qsEl('qsView'),sc=qsEl('screenQ');qsTipHide();
 [['qsVTime','time'],['qsVBand','band'],['qsVList','list']].forEach(([id,v])=>{qsEl(id).classList.toggle('on',QS.view===v);qsEl(id).setAttribute('aria-pressed',String(QS.view===v))});
 sc.classList.toggle('qs-band',QS.view!=='list');sc.classList.toggle('qs-time',QS.view==='time');qsEl('qsScope').hidden=QS.view!=='time';qsEl('qsScope').querySelectorAll('.qssc').forEach(b=>{const on=b.dataset.scope===QS.tscope;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on))});sc.classList.toggle('qs-open',QS.view!=='list'&&QS.open);   // Level band and Timeline: the detail is a drawer
 if(QS.view==='time')qsRenderTime(host);else if(QS.view==='band')qsRenderBand(host);else qsRenderList(host)}

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
const rl=qsRule(q.g),cuts=qsCuts(q),afters=((rl&&rl.a)||[]).map(g=>QS.byG.get(g)).filter(Boolean),spn=rl&&rl.s?QS.R.pts.get(rl.s):null;
 const whole=cuts.filter(c=>c.whole),objs=cuts.filter(c=>!c.whole),gn=c=>`<b>${qsEsc(c.gate.name)}</b>${qsPassed(c.gate)?' <span class="dim">(passed in this save)</span>':''}`;
 const rulesHtml=!QS.R?'':`<div class="qsrules"><p class="qsrule">Story point: ${spn?'<b>'+qsEsc(spn)+'</b>':'<span title="not computed yet">placement not computed yet</span>'}</p>
  ${afters.length?`<p class="qsrule qsafter">Opens after: ${afters.map(a=>`<button type="button" class="qslink t-${a.t}" data-g="${a.g}">${qsEsc(a.n)}</button>`).join(', ')}</p>`:''}
  ${whole.length?`<p class="qsrule qsfailsat">Fails at ${whole.map(gn).join(', ')}</p>`:''}
  ${objs.length?`<p class="qsrule qsloses">Loses an objective at ${objs.map(gn).join(', ')}</p>`:''}
  ${!whole.length&&!objs.length?'<p class="qsrule qsnomiss">Not missable as far as computed</p>':''}</div>`;
 const curHtml=cur.length?`<ul>${cur.map(t=>`<li>${t===null?'An active objective (its text is not included in this build)':qsEsc(t)}</li>`).join('')}</ul>`:'<p class="dim">Not known: the save has no active objective for it.</p>';
 el.innerHTML=`<button type="button" class="btn qsclose" id="qsClose" aria-label="Close">×</button><button type="button" class="btn qsback" id="qsBack" aria-label="Back to the list">◀ Back</button><h2 class="qstitle t-${q.t}">${qsIcon(st,q.t)}<span>${qsEsc(q.n)}</span></h2>
  <p class="qsmeta">${qsEsc(qsKindName(q.t))} · ${qsEsc(QS.regions.get(q.r))} · ${q.lv==null?'<span title="not computed yet">level —</span>':'level '+q.lv}</p>
  <p class="qsxp">${qsEsc(qsXpText(q,my))}</p><p class="qssave">${saveLine}</p>
  ${rulesHtml}
  ${st==='active'?`<div class="qscur"><h3>Current objective${cur.length>1?'s':''}</h3>${curHtml}</div>`:''}
  <div class="qsprog t-${q.t}" role="radiogroup" aria-label="My progress"><span class="qsplabel">My progress</span>${QS_MARKS.map(s=>`<button type="button" class="btn qsmark${st===s?' on':''}" role="radio" aria-checked="${st===s}" data-s="${s}">${qsIcon(s)}${QS_NAMES[s]}</button>`).join('')}${hand?'<button type="button" class="qsclear" id="qsClear">Follow my save</button>':''}</div>
  <h3 class="qsh3">Journal</h3><div class="qsdesc" id="qsDesc" tabindex="0"></div>
  <h3 class="qsh3">Objectives</h3>${q.o.length?(T?`<ul class="qsobjs t-${q.t}">${q.o.map((g,i)=>{const s=QS.store.save&&QS.store.save.o[g]||'none';return`<li class="${s}">${qsIcon(s)}<span>${qsEsc(T[i]||'')}</span></li>`}).join('')}</ul>`:`<p class="dim">${QS_DESC?'Loading…':q.o.length+' objectives (their text is not included in this build).'}</p>`):'<p class="dim">No objectives listed.</p>'}`;
 el.querySelectorAll('.qsmark').forEach(b=>{b.onclick=()=>qsMark(q.g,b.dataset.s)});el.querySelectorAll('.qslink').forEach(b=>{b.onclick=()=>qsSelect(b.dataset.g,true)});const c=qsEl('qsClear');if(c)c.onclick=()=>qsMark(q.g,null);
 qsEl('qsBack').onclick=()=>{qsEl('screenQ').classList.remove('qs-detail');const r=document.querySelector('.qsrow.on');if(r)r.focus()};qsEl('qsClose').onclick=()=>qsCloseDrawer(true);
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
 const sw=v=>{qsSetView(v);qsEl('screenQ').classList.remove('qs-detail');qsRenderView();qsRenderDetail()};qsEl('qsVTime').onclick=()=>sw('time');qsEl('qsVBand').onclick=()=>sw('band');qsEl('qsVList').onclick=()=>sw('list');
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
