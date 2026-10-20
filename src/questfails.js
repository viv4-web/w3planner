// ---- v39: the quest fail safeguard (docs/QUESTS.md). A separate lazy script (/*@lazyjs:questfails*/), loaded by qsLoad() together with data/QUEST_FAILS.json, so index.html stays small. ----
// A link says: quest A (the failer) reaches a step that fails quest B (the failed one); the game files show it (tools/build_quest_fails.py ships verified links only).
// Nothing here changes a state by itself. It paints the views quests.js has drawn (a MutationObserver repaints after every redraw) and offers two buttons when A is done and B is still open.
(function(){
const OPEN=s=>qsOpenState(s),nm=g=>qsEsc(QS.byG.get(g).n),A={links:[],gone:new Set()};
const op=l=>l.op.func.replace('CF_','').replace('GreaterEqual','≥').replace('Greater','>').replace('Equal','=')+' '+l.op.value;
const live=()=>A.links.filter(l=>OPEN(qsState(l.failed))&&OPEN(qsState(l.failer)));           // both quests still open: red + amber
const due=()=>A.links.filter(l=>qsState(l.failer)==='done'&&OPEN(qsState(l.failed))&&!A.gone.has(l.failer+l.failed));   // A is done, B was left open: ask
const fails=g=>live().filter(l=>l.failer===g),risks=g=>live().filter(l=>l.failed===g);
const by=g=>A.links.find(l=>l.failed===g&&qsState(g)==='failed'&&qsState(l.failer)==='done');   // B is failed and A is done: say who did it
const step=l=>`› ${qsEsc(l.trigger_label)} — ${nm(l.failed)} fails here`;
const chipF=n=>`<span class="qfchip red">Fails ${n} quest${n>1?'s':''}</span>`,chipR=ls=>`<span class="qfchip amber">Do before ${ls.map(l=>nm(l.failer)).join(', ')}</span>`;
const why=l=>`<details class="qfwhy"><summary>Why?</summary><ol><li>In ${nm(l.failer)} (${qsEsc(l.trigger_phase)}): ${qsEsc(l.trigger_label.charAt(0).toLowerCase()+l.trigger_label.slice(1))}.</li><li>That sets the story fact <code>${qsEsc(l.fact)}</code>.</li>
 <li>${nm(l.failed)} waits for <code>${qsEsc(l.fact)} ${op(l)}</code> and fails as soon as it is true.</li></ol>
 <details class="qfev"><summary>Evidence in the game files</summary><ul>${l.evidence.map(e=>`<li><code>${qsEsc(e.file.split('/').pop())}${e.block==null?'':' #'+e.block}</code> ${qsEsc(e.note)}</li>`).join('')}</ul>
 <p>Whether the game fails a quest you have not started yet is unconfirmed.</p></details><p class="qfsrc">Source: remaster game files</p></details>`;
function prompt(l){return`<div class="qfprompt" role="status" data-k="${l.failer}${l.failed}"><p><b>${nm(l.failer)}</b> is done. <b>${nm(l.failed)}</b> would have failed along the way.</p>
 <div class="qfbtns"><button type="button" class="btn" data-a="failed" data-g="${l.failed}">Mark it failed</button><button type="button" class="btn" data-a="done" data-g="${l.failed}">I finished it first</button><button type="button" class="qfx2" data-a="close" aria-label="Close this notice">×</button></div></div>`}
function wire(el){el.querySelectorAll('.qfprompt [data-a]').forEach(b=>{b.onclick=()=>{const k=b.closest('.qfprompt').dataset.k,a=b.dataset.a;
 if(a==='close'){A.gone.add(k);paint();return}qsMark(b.dataset.g,a)}})}
function mk(tag,cls,html){const e=document.createElement(tag);e.className=cls;e.innerHTML=html;return e}
function paint(){if(!A.links.length||!QS.data)return;obs.disconnect();try{
 const view=qsEl('qsView'),L=live();
 // the prompt(s) above Next up: every link whose failer is done and whose failed quest is still open
 let box=qsEl('qfPrompts');if(!box){box=mk('div','qfprompts','');box.id='qfPrompts';qsEl('qsMiss').before(box)}
 box.innerHTML=due().map(prompt).join('');wire(box);
 // the banner, on every view: one line per failer
 view.querySelectorAll('.qfbanner').forEach(e=>e.remove());
 const fl=[...new Set(L.map(l=>l.failer))];
 if(fl.length)view.prepend(mk('div','qfbanner',fl.map(g=>{const n=fails(g).length;return`<p role="note"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 2 21h20L12 3z"/><path d="M12 10v5M12 18h.01"/></svg><span>Continuing <b>${nm(g)}</b> fails ${n} open quest${n>1?'s':''}. Do the amber one${n>1?'s':''} first.</span></p>`}).join('')));
 // List rows: a card around the row with the chip, the step and the Why? disclosure
 view.querySelectorAll('.qsrow[data-g]').forEach(r=>{const g=r.dataset.g,f=fails(g),k=risks(g),b=by(g);if(!f.length&&!k.length&&!b)return;
  const w=mk('div','qfrow'+(f.length?' qf-fail':k.length?' qf-risk':''),'');r.before(w);w.append(r);
  const x=mk('div','qfextra',f.length?chipF(f.length)+f.map(l=>`<span class="qfstep">${step(l)}</span>`).join(''):k.length?chipR(k)+k.map(l=>`<span class="qfstep">Fails at › ${qsEsc(l.trigger_label)} in ${nm(l.failer)}.</span>`).join('')+k.map(why).join(''):`<span class="qfby">by ${nm(b.failer)} (${qsEsc(b.trigger_short)})</span>`);
  w.append(x);if(f.length||k.length)r.setAttribute('aria-label',r.getAttribute('aria-label')+(f.length?', fails '+f.length+' open quest':', at risk: do before '+k.map(l=>QS.byG.get(l.failer).n).join(', ')))});
 // dots (Level band, Timeline): a ring and the words in the label and the tooltip
 view.querySelectorAll('.qsdot[data-g]').forEach(d=>{const g=d.dataset.g,f=fails(g),k=risks(g);if(!f.length&&!k.length)return;
  d.classList.add(f.length?'qf-fail':'qf-risk');d.setAttribute('aria-label',d.getAttribute('aria-label')+(f.length?', fails '+f.length+' open quest':', at risk: do before '+k.map(l=>QS.byG.get(l.failer).n).join(', ')))});
 // Next up cards
 qsEl('qsNext').querySelectorAll('.qscard[data-g]').forEach(c=>{const g=c.dataset.g,f=fails(g),k=risks(g),s=c.querySelector('.qscn');if(!s||(!f.length&&!k.length))return;
  c.classList.add(f.length?'qf-fail':'qf-risk');s.append(mk('span',f.length?'qfcaution':'qfchip amber',f.length?f.map(l=>`Careful: ${qsEsc(l.trigger_label)} fails ${nm(l.failed)}.`).join(' '):'Do before '+k.map(l=>nm(l.failer)).join(', ')))});
 // the detail panel of the selected quest
 const dt=qsEl('qsDetail'),g=QS.sel,m=dt.querySelector('.qsmeta');
 if(g&&m){const f=fails(g),k=risks(g),b=by(g),p=due().filter(l=>l.failed===g);
  const h=(f.length?f.map(l=>`<div class="qfbox red">${chipF(f.length)}<span class="qfstep">${step(l)}</span></div>`).join(''):'')+(k.length?k.map(l=>`<div class="qfbox amber">${chipR([l])}<span class="qfstep">Fails at › ${qsEsc(l.trigger_label)} in ${nm(l.failer)}.</span>${why(l)}</div>`).join(''):'')+(b?`<p class="qfby">Failed by ${nm(b.failer)} (${qsEsc(b.trigger_short)})</p>`:'')+p.map(prompt).join('');
  if(h){const e=mk('div','qfdet',h);m.after(e);wire(e)}}
 }finally{watch()}}
const obs=new MutationObserver(()=>paint());
function watch(){['qsView','qsNext','qsDetail'].forEach(id=>{const e=qsEl(id);if(e)obs.observe(e,{childList:true,subtree:true})})}
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;const p=document.activeElement&&document.activeElement.closest&&document.activeElement.closest('.qfprompt');
 if(p){e.preventDefault();e.stopPropagation();A.gone.add(p.dataset.k);paint()}},true);   // Esc closes the notice the focus is in (before the drawer's own Esc)
window.QF={
 init(d){A.links=((d&&d.links)||[]).filter(l=>l&&QS.byG.has(l.failer_guid)&&QS.byG.has(l.failed_guid)).map(l=>Object.assign({},l,{failer:l.failer_guid,failed:l.failed_guid}));watch()},
 rank:g=>risks(g).length?-1:0,                                   // the Level band puts the at-risk quest above its failer inside one cell
 risk:()=>[...new Set(live().filter(l=>qsState(l.failer)==='active').map(l=>l.failed))].map(g=>QS.byG.get(g)),   // Next up: the amber quests come first, but only once the failer is active (a quest not started yet does not push another quest forward)
 tip:q=>{const f=fails(q.g),k=risks(q.g);return f.map(l=>`<span class="qfsub red">${step(l)}</span>`).join('')+k.map(l=>`<span class="qfsub amber">Do before ${nm(l.failer)}: fails at › ${qsEsc(l.trigger_label)}</span>`).join('')},
 live,due,paint};
})();
