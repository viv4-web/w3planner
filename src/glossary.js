// ---- Glossary (v29): Bestiary, Tutorial, Characters, Books, as the game's Glossary screen. Game text and pictures: built into the live site only ----
// GL_FILES is replaced by tools/build.py with {files:{key:url}, counts} when the build has Glossary content (the live build); the public and offline builds keep null and show
// "Glossary content is not included in this build." Nothing is requested until the Glossary screen opens; every data file is a script (W3DATA.glossary_<key>), the CSP forbids fetch.
// State is not in the link (only the open screen is: s1G). Data: docs/GLOSSARY.md.
const GL_FILES=/*@glossary*/null;
const GL_TABS=[{k:'bestiary',n:['creature','creatures']},{k:'tutorial',n:['tutorial','tutorials']},{k:'characters',n:['character','characters']},{k:'books',n:['entry','entries']}];
const GL_NAME={bestiary:'Bestiary',tutorial:'Tutorial',characters:'Characters',books:'Books'};
const GL={tab:'bestiary',q:'',all:false,sel:{},data:{},p:{},init:false,allCap:{},timer:0,col:{}};   // col[tab][group]=true: that group is folded (not in the link, kept while the page is open)
const glN=s=>String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();   // case- and accent-insensitive
const glWords=q=>glN(q).split(/\s+/).filter(Boolean);
const glEl=id=>document.getElementById(id);
const glPhone=()=>innerWidth<=760;   // the phone layout: list or entry, one at a time (glossary.css, same breakpoint)
function glScript(key){if(GL.data[key])return Promise.resolve(GL.data[key]);
 return GL.p[key]||(GL.p[key]=new Promise((ok,bad)=>{const url=GL_FILES&&GL_FILES.files[key];if(!url){bad(new Error('no file'));return}
  const s=document.createElement('script');s.src=url;s.onload=()=>{const d=(window.W3DATA||{})['glossary_'+key];if(d){GL.data[key]=d;ok(d)}else{delete GL.p[key];bad(new Error('empty'))}};s.onerror=()=>{delete GL.p[key];s.remove();bad(new Error('load'))};document.head.appendChild(s)}))}
const glKinds=()=>Object.keys(GL_FILES.files).filter(k=>k.startsWith('books_')&&k!=='books_index');
function glLoadTab(tab,bodies){return glScript(tab==='books'?'books_index':tab).then(d=>bodies&&tab==='books'?Promise.all(glKinds().map(glScript)).then(()=>d):d)}
const glEntries=tab=>{const d=GL.data[tab==='books'?'books_index':tab];return d?d.entries:[]};
const glGroups=tab=>{const d=GL.data[tab==='books'?'books_index':tab];return d&&d.groups?d.groups:null};
function glBodyText(tab,e){if(tab==='books'){const d=GL.data['books_'+e.kind];return d&&d.text[e.id]!==undefined?d.text[e.id]:null}return e.stages.join(' ')}
const glHaveBodies=()=>glKinds().every(k=>GL.data[k]);

// ---- text: the game's few tags (<br>, <i>, <b>, <s>, <font color>) and button placeholders become DOM nodes (never innerHTML); search words are highlighted ----
function glSegs(str,words){if(!words.length)return[{t:str}];let n='',map=[];for(let i=0;i<str.length;i++){const c=glN(str[i]);for(let j=0;j<c.length;j++){n+=c[j];map.push(i)}}
 const hits=[];words.forEach(w=>{let p=0;while((p=n.indexOf(w,p))>=0){hits.push([map[p],map[p+w.length-1]+1]);p+=w.length}});if(!hits.length)return[{t:str}];
 hits.sort((a,b)=>a[0]-b[0]);const m=[];hits.forEach(h=>{const l=m[m.length-1];if(l&&h[0]<=l[1])l[1]=Math.max(l[1],h[1]);else m.push(h.slice())});
 const out=[];let p=0;m.forEach(([a,b])=>{if(a>p)out.push({t:str.slice(p,a)});out.push({t:str.slice(a,b),hl:1});p=b});if(p<str.length)out.push({t:str.slice(p)});return out}
function glAddText(parent,str,words){glSegs(str,words).forEach(s=>{if(s.hl){const m=document.createElement('mark');m.className='glhl';m.textContent=s.t;parent.appendChild(m)}else parent.appendChild(document.createTextNode(s.t))})}
// the game's <<...>> placeholders: input actions and icons become a small boxed word ([Cast Sign]), colour switches are dropped, an inline picture of a book is a [picture]
function glKeyLabel(r){if(/^(end_)?color/i.test(r))return null;if(/^[a-z]/.test(r))return'picture';return r.replace(/,.*$/,'').replace(/^(GUI_PC_|GUI_|ICO_|IK_|GI_)/,'').replace(/_mod$/i,'').replace(/_+/g,' ').replace(/([a-z])([A-Z])/g,'$1 $2').trim()}
function glMarkup(root,text,words){text=String(text).replace(/^(\s*<br\s*\/?>)+/i,'').replace(/(<br\s*\/?>\s*)+$/i,'');let cur=root;   // the game pads its paragraphs with <br>; the first and last are dropped
 const stack=[],re=/<<([^>]*)>>|<(\/?)([a-zA-Z]+)([^>]*)>|([^<]+|<)/g;let m;
 while((m=re.exec(text))){
  if(m[1]!==undefined){const l=glKeyLabel(m[1]);if(l){const k=document.createElement('span');k.className='glkey';k.textContent='['+l+']';cur.appendChild(k)}}
  else if(m[3]){const tag=m[3].toLowerCase();
   if(tag==='br'){cur.appendChild(document.createElement('br'))}
   else if(['i','b','s','font'].includes(tag)){
    if(m[2]){for(let i=stack.length-1;i>=0;i--)if(stack[i].tag===tag){cur=stack[i].parent;stack.length=i;break}}
    else{const n=document.createElement(tag==='font'?'span':tag),c=tag==='font'&&/color\s*=\s*["']?(#[0-9a-fA-F]{3,8})\b/.exec(m[4]);if(c)n.style.color=c[1];cur.appendChild(n);stack.push({tag,parent:cur});cur=n}}}
  else glAddText(cur,m[5],words)}}
function glPlain(text){return String(text).replace(/<<[^>]*>>/g,' ').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim()}

// ---- search ----
function glMatch(tab,e,words){   // {name:true} when every word is in the name, {snip} when the words are found in the name and text together; null otherwise
 if(!words.length)return{};if(e._n===undefined)e._n=glN(e.name);const body=glBodyText(tab,e);if(body!==null&&e._b===undefined)e._b=glN(glPlain(body));
 if(words.every(w=>e._n.includes(w)))return{name:true};const hay=e._n+' '+(e._b||'');if(!words.every(w=>hay.includes(w)))return null;
 const t=glPlain(body||''),n=glN(t),p=Math.max(0,n.indexOf(words.find(w=>n.includes(w))||'')),a=Math.max(0,p-40),s=t.slice(a,a+120);return{snip:(a?'… ':'')+s+(a+120<t.length?' …':'')}}
const glFilter=(tab,q)=>{const w=glWords(q);return glEntries(tab).filter(e=>glMatch(tab,e,w))};
const glCountText=(tab,n,total)=>{
 if(tab==='books'){const es=glEntries(tab),b=es.filter(e=>e.kind!=='painting').length,p=es.length-b;return total===undefined?`${b} books · ${p} paintings & maps`:`${n} of ${es.length} entries`}
 const nn=GL_TABS.find(t=>t.k===tab).n;return total===undefined?`${n} ${nn[1]}`:`${n} of ${total} ${nn[1]}`}

// ---- list ----
function glRow(tab,e,extra){const b=document.createElement('button');b.type='button';b.className='glrow';b.dataset.id=e.id;b.dataset.tab=tab;
 if(tab==='bestiary'||tab==='characters'||tab==='books'){const i=document.createElement('span');i.className='glth';if(e.thumb){const im=document.createElement('img');im.src=e.thumb;im.alt='';im.loading='lazy';im.decoding='async';i.appendChild(im)}b.appendChild(i)}
 const t=document.createElement('span');t.className='glname';const nm=document.createElement('b');nm.textContent=e.name;t.appendChild(nm);
 const note=e.note||(tab==='tutorial'&&e.group);if(note){const g=document.createElement('small');g.textContent=note;t.appendChild(g)}
 if(extra){const s=document.createElement('small');s.className='glsnip';if(extra.snip)glAddText(s,extra.snip,extra.words);else s.textContent='name match';t.appendChild(s)}
 b.appendChild(t);return b}
function glRenderList(){const rows=glEl('glRows'),tab=GL.tab;rows.textContent='';
 if(GL.all)return glRenderAll();
 const entries=GL.data[tab==='books'?'books_index':tab]?glFilter(tab,GL.q):null;
 if(!entries){const p=document.createElement('p');p.className='glhint';p.textContent=GL.err?'This section could not be loaded. Check your connection and try again.':'Loading…';rows.appendChild(p);return}
 glEl('glCount').textContent=GL.q.trim()?glCountText(tab,entries.length,glEntries(tab).length):glCountText(tab,entries.length);
 if(!entries.length){const p=document.createElement('p');p.className='glhint';p.textContent='Nothing matches '+GL.q.trim()+'.';rows.appendChild(p);return}
 const frag=document.createDocumentFragment(),groups=glGroups(tab);
 const q=GL.q.trim(),col=GL.col[tab]||(GL.col[tab]={});   // groups fold and unfold; while searching every group with a result stays open
 if(groups)groups.forEach(g=>{const es=entries.filter(e=>e.group===g);if(!es.length)return;const open=!!q||!col[g];
  const h=document.createElement('button');h.type='button';h.className='glgroup tog';h.dataset.g=g;h.setAttribute('aria-expanded',String(open));if(q)h.setAttribute('aria-disabled','true');
  const ch=document.createElement('span');ch.className='glchev';ch.setAttribute('aria-hidden','true');ch.textContent=open?'▾':'▸';const t=document.createElement('span');t.textContent=g+' ('+es.length+')';h.append(ch,t);frag.appendChild(h);
  const box=document.createElement('div');box.className='glgrp';box.hidden=!open;es.forEach(e=>box.appendChild(glRow(tab,e)));frag.appendChild(box)});
 else entries.forEach(e=>frag.appendChild(glRow(tab,e)));
 rows.appendChild(frag);glFoldBtn(tab,entries);glSyncView(entries)}
function glFoldBtn(tab,entries){const b=glEl('glFold'),groups=glGroups(tab),q=GL.q.trim();b.hidden=!groups||!!q||GL.all;if(b.hidden)return;
 const any=groups.some(g=>!(GL.col[tab]||{})[g]);b.textContent=any?'Collapse all':'Expand all';b.dataset.act=any?'collapse':'expand'}
function glToggleGroup(g){if(GL.q.trim())return;const col=GL.col[GL.tab]||(GL.col[GL.tab]={}),keep=glEl('glRows').scrollTop;col[g]=!col[g];glRenderList();glEl('glRows').scrollTop=keep;const h=glEl('glRows').querySelector('.glgroup.tog[data-g="'+CSS.escape(g)+'"]');if(h)h.focus({preventScroll:true})}
function glFoldAll(){const tab=GL.tab,col=GL.col[tab]||(GL.col[tab]={}),collapse=glEl('glFold').dataset.act==='collapse';(glGroups(tab)||[]).forEach(g=>{col[g]=collapse});glRenderList();glEl('glRows').scrollTop=0}
// the entry on the right follows the list: a search that hides it moves to the first result (desktop; a phone keeps its list or entry view), and the search words are highlighted
function glSyncView(es){if(GL.all||glPhone())return;const tab=GL.tab,cur=es.find(x=>x.id===GL.sel[tab])||es[0];if(!cur)return;GL.sel[tab]=cur.id;glMarkSel();glRenderView(tab,cur,glWords(GL.q))}
function glMarkSel(){const id=GL.sel[GL.tab];glEl('glRows').querySelectorAll('.glrow').forEach(r=>{const on=!GL.all&&r.dataset.id===id;r.classList.toggle('on',on);if(on)r.setAttribute('aria-current','true');else r.removeAttribute('aria-current')})}
function glRenderAll(){const rows=glEl('glRows'),words=glWords(GL.q);rows.textContent='';
 if(!words.length){glEl('glCount').textContent='Searching every tab';const p=document.createElement('p');p.className='glhint';p.textContent='Type to search names and text in Bestiary, Tutorial, Characters and Books.';rows.appendChild(p);return}
 if(!GL.allReady){glEl('glCount').textContent='Searching…';const p=document.createElement('p');p.className='glhint';p.textContent=GL.err?'Some sections could not be loaded.':'Loading every tab…';rows.appendChild(p);return}
 let total=0,tabs=0;const frag=document.createDocumentFragment();
 GL_TABS.forEach(({k})=>{const hits=[];glEntries(k).forEach(e=>{const m=glMatch(k,e,words);if(m)hits.push([e,m])});if(!hits.length)return;total+=hits.length;tabs++;
  const h=document.createElement('div');h.className='glgroup';h.textContent=GL_NAME[k]+' ('+hits.length+')';frag.appendChild(h);const cap=GL.allCap[k]||50;
  hits.slice(0,cap).forEach(([e,m])=>{const r=glRow(k,e,{snip:m.snip,words});r.dataset.all='1';frag.appendChild(r)});
  if(hits.length>cap){const b=document.createElement('button');b.type='button';b.className='btn glmore';b.textContent='Show all '+hits.length+' in '+GL_NAME[k];b.onclick=()=>{GL.allCap[k]=1e9;glRenderList()};frag.appendChild(b)}});
 glEl('glCount').textContent=total?total+' result'+(total===1?'':'s')+' in '+tabs+' tab'+(tabs===1?'':'s'):'No results';
 if(!total){const p=document.createElement('p');p.className='glhint';p.textContent='Nothing matches '+GL.q.trim()+' in any tab.';frag.appendChild(p)}
 rows.appendChild(frag)}

// ---- entry view ----
function glSelect(tab,id,words){const e=glEntries(tab).find(x=>x.id===id);if(!e)return;GL.sel[tab]=id;if(GL.col[tab]&&GL.col[tab][e.group]){GL.col[tab][e.group]=false;glRenderList()}glMarkSel();   // an entry opened from a search result or a link unfolds its group
 glRenderView(tab,e,words||[]);
 if(glPhone()){glEl('screenGlo').classList.add('gl-detail');window.scrollTo({top:0})}}
function glRenderView(tab,e,words){const view=glEl('glView'),pic=glEl('glPic'),title=glEl('glTitle'),text=glEl('glText'),weak=glEl('glWeak');
 title.textContent=e.name;pic.textContent='';view.classList.toggle('nopic',tab==='tutorial'&&!e.img);view.dataset.tab=tab;
 if(e.img){const im=document.createElement('img');im.src=e.img;im.alt=e.name;im.className=tab==='books'&&e.kind!=='painting'?'glicon':'';pic.appendChild(im)}else{const n=document.createElement('span');n.className='glnopic';n.textContent='No picture';pic.appendChild(n)}
 text.textContent='';text.scrollTop=0;weak.textContent='';weak.hidden=true;
 const put=body=>{text.textContent='';
  if(tab==='books'||tab==='tutorial'){const d=document.createElement('div');d.className='glstage';glMarkup(d,body||'',words);text.appendChild(d)}
  else e.stages.forEach((s,i)=>{if(e.stages.length>1||tab==='bestiary'){const l=document.createElement('div');l.className='glstlabel';l.textContent='Entry '+(i+1);text.appendChild(l)}const d=document.createElement('div');d.className='glstage';glMarkup(d,s,words);text.appendChild(d)});
  const m=text.querySelector('mark');if(m)text.scrollTop=Math.max(0,m.offsetTop-text.offsetTop-40)};
 if(tab==='books'){if(e.kind==='painting'){text.textContent='';const p=document.createElement('p');p.className='dim';p.textContent='A painting, map or sketch: the picture is the entry.';text.appendChild(p)}
  else{const b=glBodyText(tab,e);if(b!==null)put(b);else{text.textContent='Loading…';const kind=e.kind;glScript('books_'+kind).then(()=>{if(GL.sel.books===e.id)put(glBodyText(tab,e))},()=>{text.textContent='This text could not be loaded.'})}}}
 else put(tab==='tutorial'?e.stages[0]:null);
 if(tab==='bestiary'&&e.weak&&e.weak.length){weak.hidden=false;const h=document.createElement('h3');h.textContent='Susceptibility';weak.appendChild(h);const row=document.createElement('div');row.className='glchips';
  e.weak.forEach(w=>{if(w.k==='item'){const b=document.createElement('button');b.type='button';b.className='glchip';b.dataset.id=w.id;b.textContent=w.name;b.title='Open '+w.name+' in Inventory';b.onclick=()=>glGoItem(w.id);row.appendChild(b)}
   else{const s=document.createElement('span');s.className='glchip plain';s.textContent=w.name;row.appendChild(s)}});weak.appendChild(row)}}

// a susceptibility chip opens Inventory at that item: a potion or decoction in the Potion 1 panel, a bomb in the Bomb 1 panel (the card is selected), an oil in the Oil row of the sword it fits (highlighted)
function glGoItem(id){if(!CN.data||!eqData()){notify('The item data is still loading.');return}const it=CN.byId.get(id);if(!it){notify('That item is not in the planner.');return}
 const sword=it.cat==='oil'?((CN.bySlot[CN_SLOTS[6]]||[]).includes(it)?0:1):-1,u=it.cat==='oil'?sword:it.cat==='bomb'?13:9;
 scrGo('inv');setTimeout(()=>{eqPick(u);
  if(it.cat==='oil'){const t=document.querySelector('#oilrow .oiltile[data-n="'+it.n+'"]');if(t){t.classList.add('hl');t.scrollIntoView({block:'nearest'});t.focus({preventScroll:true})}notify(it.name+' fits the '+(sword===0?'steel':'silver')+' sword: it is in the Oil row.')}
  else{EQ.pick.sel=it;EQ.pick.scroll=true;eqPickRender()}},0)}

// ---- tabs ----
function glRenderSubs(){document.querySelectorAll('#glSubs .glst[data-t]').forEach(b=>{const on=b.dataset.t===GL.tab;b.setAttribute('aria-selected',String(on));b.classList.toggle('on',on);b.tabIndex=on?0:-1});
 const i=GL_TABS.findIndex(t=>t.k===GL.tab);glEl('glPrev').disabled=i<=0;glEl('glNext').disabled=i>=GL_TABS.length-1;
 const q=glEl('glQ');q.placeholder=GL.all?'Search all tabs':'Search this tab';q.setAttribute('aria-label',q.placeholder);glEl('glAll').setAttribute('aria-pressed',String(GL.all));glEl('glAll').classList.toggle('on',GL.all);
 const on=document.querySelector('#glSubs .glst.on');if(on&&innerWidth<600)on.scrollIntoView({block:'nearest',inline:'center'})}
function glShowTab(tab){GL.tab=tab;GL.err=false;glRenderSubs();glEl('screenGlo').classList.remove('gl-detail');glRenderList();
 glLoadTab(tab).then(()=>{if(GL.tab!==tab||GL.all)return;glRenderList();const es=glFilter(tab,GL.q),e=es.find(x=>x.id===GL.sel[tab])||(glPhone()?null:es[0]);   // the entry you had open, else the first on a desktop (a phone starts at the list)
  if(e){GL.sel[tab]=e.id;glRenderView(tab,e,glWords(GL.q));glMarkSel();glScrollSel()}},()=>{GL.err=true;if(GL.tab===tab)glRenderList()})}
function glStep(d){const i=GL_TABS.findIndex(t=>t.k===GL.tab)+d;if(i>=0&&i<GL_TABS.length){GL.all=false;glShowTab(GL_TABS[i].k)}}
function glSearchInput(){GL.q=glEl('glQ').value;clearTimeout(GL.timer);GL.timer=setTimeout(glSearch,120)}
function glSearch(){
 if(GL.all){const words=glWords(GL.q);GL.allReady=false;glRenderList();if(!words.length)return;
  Promise.all(GL_TABS.map(t=>glLoadTab(t.k,true))).then(()=>{GL.allReady=true;GL.err=false;if(GL.all)glRenderList()},()=>{GL.err=true;GL.allReady=false;if(GL.all)glRenderList()});return}
 if(GL.tab==='books'&&glWords(GL.q).length&&!glHaveBodies()){glRenderList();glLoadTab('books',true).then(()=>{if(!GL.all&&GL.tab==='books')glRenderList()},()=>{});return}
 glRenderList()}
function glToggleAll(){GL.all=!GL.all;GL.allReady=false;glRenderSubs();glSearch()}
function glScrollSel(){const r=glEl('glRows'),n=r.querySelector('.glrow.on');if(n)r.scrollTop=Math.max(0,n.offsetTop-(r.clientHeight-n.offsetHeight)/2)}   // the list only, never the page
function glGoResult(tab,id){const words=glWords(GL.q);GL.all=false;glEl('screenGlo').classList.remove('gl-detail');
 const go=()=>{GL.tab=tab;GL.sel[tab]=id;glRenderSubs();glRenderList();glSelect(tab,id,words);glScrollSel()};
 glLoadTab(tab,tab==='books').then(go,()=>{})}
function glBind(){
 glEl('glSubs').addEventListener('click',e=>{const b=e.target.closest('.glst');if(!b||!b.dataset.t)return;GL.all=false;glShowTab(b.dataset.t)});
 glEl('glSubs').addEventListener('keydown',e=>{if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;e.preventDefault();glStep(e.key==='ArrowRight'?1:-1);const b=document.querySelector('#glSubs .glst.on');if(b)b.focus()});
 glEl('glPrev').onclick=()=>glStep(-1);glEl('glNext').onclick=()=>glStep(1);glEl('glQ').addEventListener('input',glSearchInput);glEl('glAll').onclick=glToggleAll;
 glEl('glBack').onclick=()=>{glEl('screenGlo').classList.remove('gl-detail');const r=glEl('glRows').querySelector('.glrow.on');if(r)r.scrollIntoView({block:'center'})};
 glEl('glFold').onclick=glFoldAll;
 glEl('glRows').addEventListener('click',e=>{const h=e.target.closest('.glgroup.tog');if(h){glToggleGroup(h.dataset.g);return}const r=e.target.closest('.glrow');if(!r)return;if(r.dataset.all)glGoResult(r.dataset.tab,r.dataset.id);else glSelect(GL.tab,r.dataset.id,glWords(GL.q))});
 glEl('glRows').addEventListener('keydown',e=>{if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;const rs=[...glEl('glRows').querySelectorAll('.glrow')].filter(r=>!r.closest('[hidden]')),i=rs.indexOf(document.activeElement);if(i<0)return;const n=rs[i+(e.key==='ArrowDown'?1:-1)];if(!n)return;e.preventDefault();n.focus();if(!glPhone()&&!GL.all)n.click()});
 glEl('glQ').addEventListener('keydown',e=>{if(e.key==='ArrowDown'){const r=[...glEl('glRows').querySelectorAll('.glrow')].find(x=>!x.closest('[hidden]'));if(r){e.preventDefault();r.focus()}}})}
function glClose(){GL.shown=false}
function glOpen(){if(GL.shown)return;GL.shown=true;if(!GL.init){GL.init=true;glBind()}   // scrApply runs after every change of the build; the screen is set up once per visit
 const has=!!GL_FILES;glEl('glMsg').hidden=has;glEl('glBody').hidden=!has;document.querySelector('#screenGlo .glsub').hidden=!has;if(!has)return;
 glShowTab(GL.tab)}
