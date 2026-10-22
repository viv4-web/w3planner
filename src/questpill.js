// ---- v40: the quest status pill (docs/QUESTS.md). A separate lazy script (/*@lazyjs:questpill*/), loaded by qsLoad(); without it the old status icons are drawn. ----
// The pill replaces the bare status circle in the List, Next up and the Quest failures rows: a real button that shows the state in words and opens a menu with the four states of MY PROGRESS.
// Choosing one goes through qsMark(), the same code as the My progress buttons, so the fail prompt (Mark it failed / I finished it first) appears as it always did.
(function(){
const css=`
.qspill{display:inline-flex;align-items:center;justify-content:center;gap:5px;box-sizing:border-box;width:118px;min-height:32px;padding:0 8px;border:2px solid #7a6a4a;border-radius:999px;background:none;color:#d8ccb0;font:inherit;font-size:15px;font-weight:600;line-height:1;white-space:nowrap;cursor:pointer}
.qspill i{font-style:normal;flex:none}.qspill span{overflow:hidden;text-overflow:ellipsis}.qspill:hover{background:#2a2218}
.qspill.st-active{background:#d9a441;border-color:#d9a441;color:#1a1306}.qspill.st-done{background:#8fc58a;border-color:#8fc58a;color:#10200e}.qspill.st-failed{background:#e0877c;border-color:#e0877c;color:#2a0b07}
.qspill.st-active:hover,.qspill.st-done:hover,.qspill.st-failed:hover{filter:brightness(1.08)}
.qspill:focus-visible,.qspm button:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.qsrw{position:relative}.qsrw>.qspill{position:absolute;left:8px;top:50%;transform:translateY(-50%);z-index:1}.qsrw .qsrow{padding-left:136px}.qsrw .qsrow.choice::after{display:none}
.qscw{position:relative;display:block}.qscw .qscard{padding-bottom:50px;height:100%}.qscw>.qspill{position:absolute;left:10px;bottom:10px;z-index:1}
.qfblk .qspill,.qfgh .qspill{margin-top:6px;align-self:flex-start}
.qspm{position:fixed;z-index:60;min-width:200px;display:flex;flex-direction:column;padding:4px;background:#14100b;border:1px solid #8a6a36;border-radius:6px;box-shadow:0 8px 24px #000c}
.qspm button{display:flex;align-items:center;gap:10px;min-height:40px;padding:0 12px;background:none;border:0;border-radius:4px;color:#f1e8d6;font:inherit;font-size:17px;text-align:left;cursor:pointer}
.qspm button:hover,.qspm button:focus{background:#2d2417}.qspm button i{font-style:normal;width:16px;text-align:center;flex:none}.qspm button em{margin-left:auto;font-style:normal;font-size:14px;color:#b9a985}
.qspm button.st-active i{color:#d9a441}.qspm button.st-done i{color:#8fc58a}.qspm button.st-failed i{color:#e0877c}
@media (max-width:600px){.qspill{min-height:44px}.qspm button{min-height:44px}.qsrw .qsrow{min-height:56px}.qsrw .qsrn2 b{font-size:18px}}
`,st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
const GL={none:'○',inactive:'○',active:'◉',done:'✓',failed:'✕'};
let M=null;                                   // the open menu: {el, btn, g, ctx}
function pill(g){const q=QS.byG.get(g);if(!q)return'';const s=qsState(g),n=QS_NAMES[s];
 return`<button type="button" class="qspill st-${s}" data-pill="${g}" aria-haspopup="menu" aria-expanded="false" aria-label="${qsEsc(q.n)}: ${n}. Change status"><i aria-hidden="true">${GL[s]}</i> <span>${n}</span> <i aria-hidden="true">▾</i></button>`}
function close(back){if(!M)return;const{el,btn}=M;M=null;el.remove();btn.setAttribute('aria-expanded','false');if(back&&btn.isConnected)btn.focus({preventScroll:true})}
function place(){if(!M)return;const{el,btn}=M,r=btn.getBoundingClientRect(),w=el.offsetWidth,h=el.offsetHeight;let top=r.bottom+4;if(top+h>innerHeight-6&&r.top-h-4>6)top=r.top-h-4;
 el.style.left=Math.max(6,Math.min(r.left,innerWidth-w-6))+'px';el.style.top=top+'px'}   // under the pill, above it when there is no room; follows it when the page scrolls
function open(btn){if(M&&M.btn===btn){close(true);return}close(false);
 const g=btn.dataset.pill,q=QS.byG.get(g),cur=qsState(g),el=document.createElement('div');el.className='qspm';el.setAttribute('role','menu');el.setAttribute('aria-label','Set the status of '+q.n);
 el.innerHTML=QS_MARKS.map(s=>`<button type="button" role="menuitem" class="st-${s}" data-s="${s}"><i aria-hidden="true">${GL[s]}</i>${QS_NAMES[s]}${cur===s?'<em>(current)</em>':''}</button>`).join('');
 document.body.appendChild(el);btn.setAttribute('aria-expanded','true');
 M={el,btn,g,ctx:(btn.closest('#qsNext,#qsView,#qsDetail')||{}).id||''};place();
 const items=[...el.querySelectorAll('button')];(items.find(b=>b.dataset.s===cur)||items[0]).focus({preventScroll:true})}
function pick(s){const{g,ctx}=M;close(false);qsMark(g,s);const b=document.querySelector((ctx?'#'+ctx+' ':'')+'.qspill[data-pill="'+g+'"]')||document.querySelector('.qspill[data-pill="'+g+'"]');if(b)b.focus({preventScroll:true})}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.qspill');
 if(b){e.preventDefault();open(b);return}
 const it=e.target.closest&&e.target.closest('.qspm button');if(it&&M){pick(it.dataset.s);return}
 if(M&&!(e.target.closest&&e.target.closest('.qspm')))close(false)});   // a click anywhere else closes it
document.addEventListener('keydown',e=>{
 if(M){const items=[...M.el.querySelectorAll('button')],i=items.indexOf(document.activeElement);
  if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close(true);return}
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();items[(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length].focus({preventScroll:true});return}
  if(e.key==='Home'||e.key==='End'){e.preventDefault();items[e.key==='Home'?0:items.length-1].focus({preventScroll:true});return}
  if(e.key==='Tab'){close(false);return}
  return}
 const b=document.activeElement&&document.activeElement.closest&&document.activeElement.closest('.qspill');
 if(b&&e.key==='ArrowDown'){e.preventDefault();open(b)}},true);
addEventListener('resize',place);document.addEventListener('scroll',place,true);
window.QP={pill,close};
})();
