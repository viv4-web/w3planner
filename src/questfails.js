// ---- v39: the quest fail safeguard (docs/QUESTS.md). A separate lazy script (/*@lazyjs:questfails*/), loaded by qsLoad() together with data/QUEST_FAILS.json, so index.html stays small. ----
// A link says: quest A (the failer) reaches a step that fails quest B (the failed one); the game files show it (tools/build_quest_fails.py ships verified links only).
// Nothing here changes a state by itself. It paints the views quests.js has drawn (a MutationObserver repaints after every redraw) and offers two buttons when A is done and B is still open.
(function(){
// the rules live here, not in quests.css, so index.html stays small (the CSP allows inline styles); the colour tokens --qf-* are in quests.css
const css=`
.qfrow{margin:4px 0;border:2px solid transparent;border-radius:6px}.qfrow.qf-fail{background:var(--qf-red-bg);border-color:var(--qf-red)}.qfrow.qf-risk{background:var(--qf-amber-bg);border-color:var(--qf-amber)}.qfrow .qsrow{border-bottom:0;min-height:44px}.qfrow.qf-fail .qsrn2 b{color:#fff2ef}.qfrow.qf-fail .qsrow:hover{background:#4a1b17}.qfrow.qf-risk .qsrow:hover{background:#38291a}
.qfextra{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;padding:0 10px 8px 36px;font-size:16px;line-height:1.3}.qf-fail>.qfextra{color:var(--qf-ink-red)}.qf-risk>.qfextra{color:var(--qf-ink-amber)}.qfstep{flex:1 1 220px;min-width:0}
.qfchip{display:inline-flex;align-items:center;font-size:14px;font-weight:600;line-height:1.2;border-radius:999px;padding:3px 10px;color:var(--qf-chip-ink);white-space:nowrap}.qfchip.red{background:var(--qf-red-chip);color:#1a0907}.qfchip.amber{background:var(--qf-amber)}
.qfby{margin:0;font-size:15px;color:#e8998f}
.qfwhy{flex:1 1 100%}.qfwhy summary,.qfev summary{display:flex;align-items:center;min-height:44px;cursor:pointer;color:#e3c27a}.qfwhy summary:focus-visible,.qfev summary:focus-visible,.qfprompt .btn:focus-visible,.qfx2:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.qfwhy ol,.qfev ul{margin:0 0 6px;padding-left:22px}.qfwhy code{font-size:14px;color:inherit;background:#0006;padding:0 4px}.qfev{margin:0 0 6px}.qfev li{margin:3px 0;font-size:14px;word-break:break-word}.qfsrc{margin:0 0 6px;font-size:14px;opacity:.85}
.qfcaution{display:block;margin-top:5px;padding:4px 8px;background:var(--qf-red-bg);border:1px solid var(--qf-red);border-radius:4px;color:var(--qf-ink-red);font-size:15px!important;font-style:normal!important;line-height:1.25}
.qscard.qf-fail{border-color:var(--qf-red)}.qscard.qf-risk{border-color:var(--qf-amber)}.qscard .qfchip{margin-top:5px;align-self:flex-start;font-size:13px}
.qfrow.qf-fail.qf-risk{background:var(--qf-red-bg);border-color:var(--qf-red);box-shadow:0 0 0 2px var(--qf-amber)}.qfrow.qf-fail.qf-risk>.qfextra{color:var(--qf-ink-red)}.qscard.qf-fail.qf-risk{box-shadow:0 0 0 2px var(--qf-amber)}.qsdot.qf-fail{box-shadow:0 0 0 2px var(--qf-red);border-radius:50%}.qsdot.qf-risk{outline:2px dashed var(--qf-amber);outline-offset:2px;border-radius:50%}
.qfsub{display:block;font-size:15px}.qfsub.red{color:var(--qf-red-chip)}.qfsub.amber{color:var(--qf-amber)}
.qfdet{display:flex;flex-direction:column;gap:8px;margin:8px 0}.qfbox{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;padding:8px 12px;border:2px solid;border-radius:6px;font-size:16px;line-height:1.3}.qfbox.red{background:var(--qf-red-bg);border-color:var(--qf-red);color:var(--qf-ink-red)}.qfbox.amber{background:var(--qf-amber-bg);border-color:var(--qf-amber);color:var(--qf-ink-amber)}
.qfprompts:empty{display:none}.qfprompts{display:flex;flex-direction:column;gap:8px;margin:0 0 10px}
.qfprompt{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;padding:8px 8px 8px 14px;background:#0d0c0bf7;border:1px solid #8a6a36;font-size:17px;line-height:1.3;color:#f1e8d6}.qfprompt p{margin:0;flex:1 1 280px}.qfbtns{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.qfprompt .btn{min-height:44px;font-size:16px;cursor:pointer}
.qfinl{margin:8px 0}.qfinl .qfprompt{margin:0 0 8px}.qfrow>.qfinl{margin:0;padding:0 10px 8px}.qfrowx>.qfinl{margin:0;padding:10px 16px;background:#1b1410;border-top:1px solid #3a3226}.qfcan b,.qfcan .qslink{overflow-wrap:anywhere}
.qfx2{flex:none;width:44px;height:44px;padding:0;background:none;border:1px solid transparent;color:inherit;font:inherit;font-size:24px;line-height:1;cursor:pointer}.qfx2:hover{border-color:#8a6a36}

.qfbbox:empty{display:none}.qfbbox{margin:0 0 10px}.qfbanner{background:var(--qf-red-bg);border:1px solid var(--qf-red);border-radius:6px}
.qfbrow{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;padding:8px 14px}.qfbrow svg{flex:none;color:var(--qf-red-chip)}.qfbrow p{margin:0;overflow-wrap:anywhere;flex:1 1 360px;color:var(--qf-ink-red);font-size:17px;line-height:1.35}
.qfn{font-weight:600}.qfn.red{color:var(--qf-red-chip)}.qfn.amber{color:var(--qf-amber)}.qfreg{color:#d9b4ad}
.qfmore{min-height:44px;padding:0 16px;background:none;color:#ffd6cf;border:1px solid var(--qf-red);border-radius:4px;font:inherit;font-size:16px;font-weight:600;cursor:pointer}.qfmore:hover{background:#4a1b17}
.qfpanel{border-top:1px solid #7a2f29;background:#1b1410;padding:14px 16px;border-radius:0 0 6px 6px;display:flex;flex-direction:column;gap:16px}.qfpanel[hidden]{display:none}
.qflab{font-size:13px;font-weight:600;letter-spacing:.06em;color:#a8987a}.qfdep{display:flex;flex-direction:column;gap:10px}.qfdep+.qfdep{border-top:1px solid #3a3226;padding-top:16px}
.qfcards{display:flex;flex-wrap:wrap;gap:12px;align-items:stretch}.qfcard{flex:1 1 260px;display:flex;flex-direction:column;gap:5px;padding:12px 14px;border:2px solid;border-radius:6px}
.qfcard.red{background:var(--qf-red-bg);border-color:var(--qf-red);color:#f0b8b0}.qfcard.red .qflab{color:var(--qf-red-chip)}.qfcard.red .qfbig{color:#fff2ef}
.qfcard.amber{background:var(--qf-amber-bg);border-color:var(--qf-amber);color:#c9b48c}.qfcard.amber .qflab{color:var(--qf-amber)}.qfcard.amber .qfbig{color:#f3e8d2}
.qfbig{font-size:24px;font-weight:600;line-height:1.1}.qfmeta{font-size:15px}.qfgo{align-self:flex-start;min-height:44px;padding:0;background:none;border:0;font:inherit;font-size:16px;text-decoration:underline;cursor:pointer;color:inherit}
.qfmid{flex:1 1 220px;display:flex;flex-direction:column;justify-content:center;gap:5px;padding:4px}.qfstepn{color:#fff2ef;font-weight:600}.qfarrow{color:var(--qf-red);font-size:22px;line-height:1}
.qfsafe{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}.qfsafe p{margin:0;flex:1 1 360px;font-size:16px;color:#d9cbad}.qffin{min-height:44px;font-size:16px;cursor:pointer}
.qfdata{background:#15110c;border:1px solid #3a3226;border-radius:4px;padding:2px 12px}.qfdata summary{display:flex;align-items:center;min-height:44px;cursor:pointer;color:#c9bba0}.qfdata ul{margin:0 0 6px;padding-left:20px}.qfdata li{margin:3px 0;font-size:14px;color:#c9bba0;word-break:break-word}.qfdata p{margin:0 0 8px;font-size:14px;color:#c9bba0}
.qfmore:focus-visible,.qfgo:focus-visible,.qffin:focus-visible,.qfdata summary:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.qsreg{position:relative}.qfdots{position:absolute;top:3px;right:4px;display:flex;gap:3px}.qfd{display:block;width:9px;height:9px;box-sizing:border-box;border-radius:50%;box-shadow:0 0 0 1.5px #0d0c0a}.qfd.red{background:var(--qf-red-chip)}.qfd.amber{background:#0d0c0a;border:2.5px solid var(--qf-amber)}
@keyframes qfpulse{0%,100%{box-shadow:0 0 0 0 #fff0}50%{box-shadow:0 0 0 7px #fffc}}.qf-pulse{animation:qfpulse .7s ease-in-out 3;border-radius:6px}@media (prefers-reduced-motion:reduce){.qf-pulse{animation:none;outline:3px solid #fff;outline-offset:3px}}

#qsVFails{background:none;border-color:var(--qf-red);color:var(--qf-red-chip)}#qsVFails:not(.on):hover{border-color:var(--qf-red-chip);color:#fff2ef}#qsVFails.on{background:var(--qf-btn);border-color:var(--qf-red-chip);color:#fff4f2;font-weight:600}.qsviews{flex-wrap:wrap}
.qs-fails .qsregnav,.qs-fails #qsNext,.qs-fails #qsMiss,.qs-fails #qfBanner{display:none}
.qfhead{display:flex;flex-wrap:wrap;gap:12px;align-items:center;border:1px solid #5a2e28;background:#1d1310;border-radius:4px;padding:14px 16px;margin:0 0 12px}.qfht{flex:1 1 480px}.qfht h2{margin:0 0 4px;font-size:24px;font-weight:600;color:#fff2ef}.qfht p{margin:0;font-size:16px;color:#d9c2bb}
.qfhide{display:flex;align-items:center;gap:8px;min-height:44px;color:#c9bba0;cursor:pointer}.qfhide input{width:20px;height:20px}
.qfrowx{border:1px solid #3a3226;border-radius:6px;overflow:hidden;margin:0 0 10px}.qfr1{display:flex;flex-wrap:wrap}.qfblk{flex:1 1 260px;display:flex;flex-direction:column;justify-content:center;gap:4px;padding:14px 16px;background:#1b1410;min-width:0}
.qfblk.red{background:var(--qf-red-bg);color:#f0b8b0}.qfblk.red .qflab{color:var(--qf-red-chip)}.qfblk.red .qfbig{color:#fff2ef}.qfblk.amber{background:var(--qf-amber-bg);color:#c9b48c}.qfblk.amber .qflab{color:var(--qf-amber)}.qfblk.amber .qfbig{color:#f3e8d2}.qfblk.st{flex:1 1 200px;gap:8px}
.qfst{align-self:flex-start;font-size:14px;font-weight:600;border-radius:999px;padding:4px 10px;color:#15120e}.qfst.open{background:var(--qf-amber)}.qfst.safe{background:#9fc59a}.qfst.failed{background:#e0877c}.qfst.missed{background:#c9bba0}
.qfdetb{align-self:flex-start;min-height:44px;padding:0 12px;background:none;color:#e3c27a;border:1px solid #4a4031;border-radius:4px;font:inherit;font-size:16px;cursor:pointer}.qfdetb:focus-visible,.qfhide input:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.qfrdep{padding:14px 16px;background:#1b1410;border-top:1px solid #3a3226}.qfrdep[hidden]{display:none}.qfnote{margin:8px 0;font-size:15px;color:#a8987a}.qfnote b.s-open{color:var(--qf-amber)}.qfnote b.s-safe{color:#9fc59a}.qfnote b.s-failed{color:#e0877c}.qfnote b.s-missed{color:#c9bba0}
.qfgrp{border:1px solid #3a3226;border-radius:6px;overflow:hidden;margin:0 0 12px}.qfgh{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding:12px 16px;background:#2a1511;border-bottom:1px solid #5a2e28}.qfgt{flex:1 1 220px;display:flex;flex-direction:column;gap:3px}.qfgs{flex:2 1 260px;display:flex;flex-direction:column;gap:3px}.qfgh .qflab{color:var(--qf-red-chip)}.qfgh .qfbig{font-size:22px;color:#fff2ef}.qfgh .qfmeta{color:#f0b8b0}.qfgh .qfstepn{font-size:17px}.qfgn{flex:none;font-size:15px;font-weight:600;border-radius:999px;padding:4px 12px;background:var(--qf-red-chip);color:#1a0907}
.qfgrp .qfrowx{border:0;border-top:1px solid #3a3226;border-radius:0;margin:0}.qfgrp .qfblk{padding:10px 16px}.qfunl{font-size:15px;color:#d9cbad}
.qfsubh{margin-top:6px;font-size:15px!important;letter-spacing:0!important;color:#e3c27a!important}.qfgsub{padding:8px 16px;background:#1b1410;border-top:1px solid #5a2e28;font-size:15px;font-weight:600;color:#e3c27a}\n.qfgl{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}.qfgl li{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:center;padding:8px 12px;border:1px solid var(--qf-amber);border-radius:6px;background:var(--qf-amber-bg);color:#c9b48c}.qfgl li b{color:#f3e8d2;font-size:18px}.qfgl .qfunl{flex:1 1 100%}
`,st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
const OPEN=s=>qsOpenState(s),nm=g=>qsEsc(QS.byG.get(g).n),A={links:[],gone:new Set(),open:false,pulse:0,hide:false,det:new Set(),cand:0};   // open = the details panel under the banner (this visit only, no storage)
const GROUP_MIN=3;                                                  // this many links with the same failer and the same trigger are shown as one (banner, panel, tab): the Isle of Mists prompt has 16
const op=l=>l.op.func.replace('CF_','').replace('GreaterEqual','≥').replace('Greater','>').replace('Equal','=')+' '+l.op.value;
const isC=l=>l.kind==='choice',isU=l=>l.kind==='fails_unless_set',wd=l=>l.effect==='Deactivate'?'closes':'fails',lc=s=>s.charAt(0).toLowerCase()+s.slice(1),cap=s=>s.charAt(0).toUpperCase()+s.slice(1);   // a label is a lowercase noun phrase that reads after "at"; cap() for headings where it stands alone
const live=()=>A.links.filter(l=>OPEN(qsState(l.failed))&&OPEN(qsState(l.failer)));           // both quests still open: red + amber
const due=()=>{const seen=new Set();return A.links.filter(l=>!isC(l)&&qsState(l.failer)==='done'&&OPEN(qsState(l.failed))&&!A.gone.has(l.failer+l.failed)&&!seen.has(l.failer+l.failed)&&seen.add(l.failer+l.failed))};   // A is done, B was left open: ask (a choice cannot be asked: the save does not say which way it went)
const fails=g=>live().filter(l=>l.failer===g),risks=g=>live().filter(l=>l.failed===g&&!isC(l));   // a choice never puts the failed quest "at risk: do before": there is no order that avoids it
const say=(f,k)=>(f.length?', fails '+new Set(f.map(l=>l.failed)).size+' open quest'+(new Set(f.map(l=>l.failed)).size>1?'s':''):'')+(k.length?', at risk: do before '+[...new Set(k.map(l=>QS.byG.get(l.failer).n))].join(', '):'');   // a quest can be both: it fails one quest and is at risk from another
const by=g=>A.links.find(l=>l.failed===g&&qsState(g)==='failed'&&qsState(l.failer)==='done');   // B is failed and A is done: say who did it
const qq=g=>QS.byG.get(g),rg=g=>qsEsc(QS.regions.get(qq(g).r)),cn=(g,c)=>`<b class="qfn ${c}">${nm(g)}</b>`;
// groups: links that share a failer and a trigger (3 or more) are one entry; the rest are single
function groups(L){const m=new Map();L.forEach(l=>{const k=l.failer+'|'+l.trigger_label;if(!m.has(k))m.set(k,[]);m.get(k).push(l)});const out=[];m.forEach(v=>{if(v.length>=GROUP_MIN)out.push(v);else v.forEach(l=>out.push([l]))});return out}
const nf=ls=>new Set(ls.map(l=>l.failed)).size,plural=(n,w)=>n+' '+w+(n>1?'s':'');
// a group is split in the quests that fail at the step and the ones that fail only unless you did something first (Brothers In Arms): [main, unless]
const sp=ls=>[ls.filter(l=>!isU(l)),ls.filter(isU)],ug=ls=>ls[0].unless_group||ls[0].condition;
const cnt=ls=>{const[m,u]=sp(ls);return(m.length?plural(nf(m),'open quest')+' fail'+(nf(m)>1?'':'s')+' here':'')+(m.length&&u.length?', and ':'')+(u.length?nf(u)+(m.length?' more':' open quest'+(nf(u)>1?'s':''))+' unless you\'ve '+qsEsc(ug(u))+(m.length?'':' fail here'):'')};
// one line per link, by kind (the failer's row, Next up, the tooltip, the detail panel)
const unl=l=>l.kind==='fails_unless_set'?` unless you've ${qsEsc(l.condition)}`:'';
const uS=l=>`${nm(l.failed)} fails at ${qsEsc(l.trigger_label)} unless you've ${qsEsc(l.condition)} first.`;   // Brothers In Arms: the sentence starts with the full quest name
const step=l=>isC(l)?`› Choosing ${qsEsc(l.choice)} — ${nm(l.failed)} fails`:`› ${qsEsc(cap(l.trigger_label))} — ${nm(l.failed)} ${wd(l)} here${unl(l)}`;
const stepG=ls=>ls.length>=GROUP_MIN?`› ${qsEsc(ls[0].trigger_gerund||cap(ls[0].trigger_label))} — ${cnt(ls)}`:ls.map(step).join('</span><span class="qfstep">');
const steps=f=>groups(f).map(g=>`<span class="qfstep">${stepG(g)}</span>`).join('');
const inF=l=>l.trigger_label.includes(qq(l.failer).n)?'':' in '+nm(l.failer);
const riskLine=l=>`Fails at › ${qsEsc(cap(l.trigger_label))}${inF(l)}${unl(l)}.`;
const chipF=n=>`<span class="qfchip red">Fails ${n} quest${n>1?'s':''}</span>`,chipR=ls=>`<span class="qfchip amber">Do before ${[...new Set(ls.map(l=>nm(l.failer)))].join(', ')}</span>`;
const nq=f=>new Set(f.map(l=>l.failed)).size;
const dd=t=>t.replace(/\.{4,}/g,'...');                          // a name that ends in "..." followed by a full stop keeps three dots
const evData=l=>`<details class="qfev"><summary>Game data (remaster files, full trace)</summary><p>Where this happens in the quest files: ${qsEsc(l.trigger_phase)}</p><ul>${evList(l.evidence)}</ul>${l.fact?`<p>Story fact: <code>${qsEsc(l.fact)}</code>${l.op?' '+op(l):''}</p>`:''}${l.premise?`<p>Reading used: ${qsEsc(l.premise)}.</p>`:''}<p>Whether the game ${wd(l)} a quest you have not started yet is unconfirmed.</p></details>`;
const why=l=>{const t=l.trigger_label,F=nm(l.failed),R=nm(l.failer);
 const body=l.kind==='journal_status'?`<li>In ${R}, at ${t}.</li><li>${qsEsc(cap(l.journal))}.</li><li>The game then ${wd(l)} ${F}.</li>`
  :l.kind==='flow'?`<li>In ${R}, at ${t}.</li><li>${qsEsc(cap(l.flow))}.</li>`
  :l.kind==='fails_unless_set'?`<li>In ${R}, at ${t}.</li><li>${F} is checked once, at that moment.</li><li>It ${wd(l)} unless you've ${qsEsc(l.condition)} first.</li>`
  :l.kind==='choice'?`<li>In ${R}, choosing ${qsEsc(l.choice)}.</li><li>The game then fails ${F} as soon as it notices.</li>`
  :`<li>In ${R}, at ${t}.</li><li>The game then ${wd(l)} ${F} as soon as it notices.</li>`;
 return dd(`<details class="qfwhy"><summary>Why?</summary><ol>${body}</ol>${evData(l)}<p class="qfsrc">Source: remaster game files</p></details>`)};
const regs=l=>rg(l.failer)===rg(l.failed)?['','']:[` <span class="qfreg">(${rg(l.failer)})</span>`,` <span class="qfreg">(${rg(l.failed)})</span>`];   // no region after a name when both quests are in the same one
const tk=(t,l,c)=>t.replace(/\{failed\}/g,c?cn(l.failed,'amber'):nm(l.failed)).replace(/\{failer\}/g,c?cn(l.failer,'red'):nm(l.failer));
const bline=l=>{const none=qsState(l.failed)==='none',[a,b]=regs(l);
 if(l.banner_text)return dd(tk(qsEsc(l.banner_text),l,true));
 if(isC(l))return dd(`Choosing ${qsEsc(l.choice)} in ${cn(l.failer,'red')}${a} fails ${cn(l.failed,'amber')}${b}. To keep ${nm(l.failed)}, ${qsEsc(l.safe)}.`);
 if(isU(l))return dd(`${cn(l.failed,'amber')} fails at ${qsEsc(l.trigger_label)} unless you've ${qsEsc(l.condition)} first.`);
 return dd(`${cn(l.failer,'red')}${a} ${l.effect==='Deactivate'?'closes':'fails'+(none?' or closes':'')} ${cn(l.failed,'amber')}${b} at ${qsEsc(l.trigger_label)}. ${l.advice?qsEsc(l.advice):'Do '+nm(l.failed)+' first.'}`)};
const meta=g=>`${qsEsc(qsKindName(qq(g).t))} · ${rg(g)} · level ${qsLevelText(qq(g))} · ${QS_NAMES[qsState(g)]}`;
const stepTxt=l=>qsEsc(isC(l)?'Choosing '+l.choice:cap(l.trigger_label));   // only the trigger; the phase path is in the Game data section
const evList=ev=>ev.map(e=>`<li><code>${qsEsc(e.file.split('/').pop())}${e.block==null?'':' #'+e.block}</code> ${qsEsc(e.note)}</li>`).join('');
const gdata=(l,extra)=>`<details class="qfdata"><summary>Game data (remaster files, full trace)</summary>${extra||''}<p>Where this happens in the quest files: ${qsEsc(l.trigger_phase)}</p><ul>${evList(l.evidence)}</ul>${l.fact?`<p>Story fact: <code>${qsEsc(l.fact)}</code>${l.op?' '+op(l):''}</p>`:''}${l.premise?`<p>Reading used: ${qsEsc(l.premise)}.</p>`:''}<p>Whether the game ${wd(l)} a quest you have not started yet is unconfirmed.</p></details>`;
const safeOf=l=>l.safe_text?tk(qsEsc(l.safe_text),l):isC(l)?`This is a choice, not an order: no quest can be done first to avoid it. To keep ${nm(l.failed)}, ${qsEsc(l.safe)}.`:isU(l)?`${uS(l)} To keep it, do this before ${qsEsc(l.trigger_label)}.`:`Safe order: finish ${nm(l.failed)}, then continue ${nm(l.failer)}.${qsState(l.failed)==='none'?' If you haven\'t started it, the game may close it at this step instead.':''}`;
const dep=l=>dd(`<section class="qfdep" aria-label="${isC(l)?'Choosing '+qsEsc(l.choice)+' in '+nm(l.failer):nm(l.failer)} fails ${nm(l.failed)}">
  <div class="qfcards"><div class="qfcard red"><div class="qflab">${isC(l)?'IF YOU CHOOSE':'IF YOU DO THIS'}</div><div class="qfbig">${isC(l)?qsEsc(cap(l.choice)):nm(l.failer)}</div><div class="qfmeta">${isC(l)?'in '+nm(l.failer)+' · ':''}${meta(l.failer)}</div><button type="button" class="qfgo" data-go="${l.failer}">Go to quest ›</button></div>
  <div class="qfmid"><div class="qflab">AT THIS STEP</div><div class="qfstepn">${stepTxt(l)}</div><div class="qfarrow" aria-hidden="true">→</div></div>
  <div class="qfcard amber"><div class="qflab">THIS QUEST ${l.effect==='Deactivate'?'CLOSES':'FAILS'}</div><div class="qfbig">${nm(l.failed)}</div><div class="qfmeta">${meta(l.failed)}</div><button type="button" class="qfgo" data-go="${l.failed}">Go to quest ›</button></div></div>
  <div class="qfsafe"><p>${safeOf(l)}</p>${l.window?`<p class="qfwin">${qsEsc(l.window)}</p>`:''}${isC(l)?'':`<button type="button" class="btn qffin" data-fin="${l.failed}">I finished it already</button>`}</div>
  ${gdata(l)}</section>`);
// a group: the failer and the step once, the failed quests as a list
function depG(ls){const l0=ls[0],sh=l0.evidence.filter(e=>e.s!=null),[m,u]=sp(ls),li=l=>`<li><b>${nm(l.failed)}</b><span class="qfmeta">${meta(l.failed)}</span>${isU(l)?`<span class="qfunl">${uS(l)}</span>`:''}<button type="button" class="qfgo" data-go="${l.failed}">Go to quest ›</button><button type="button" class="btn qffin" data-fin="${l.failed}">I finished it already</button></li>`;
 return`<section class="qfdep qfdepg" aria-label="${qsEsc(cap(l0.trigger_label))} fails ${plural(nf(ls),'open quest')}">
  <div class="qfcards"><div class="qfcard red"><div class="qflab">IF YOU DO THIS</div><div class="qfbig">${nm(l0.failer)}</div><div class="qfmeta">${meta(l0.failer)}</div><button type="button" class="qfgo" data-go="${l0.failer}">Go to quest ›</button></div>
  <div class="qfmid"><div class="qflab">AT THIS STEP</div><div class="qfstepn">${stepTxt(l0)}</div><div class="qfarrow" aria-hidden="true">→</div></div></div>
  ${m.length?`<div class="qflab">THESE ${nf(m)} QUESTS ${m.some(l=>l.effect==='Deactivate')?'FAIL OR CLOSE':'FAIL'}</div><ul class="qfgl">${m.slice().sort(byLv).map(li).join('')}</ul>`:''}
  ${u.length?`<div class="qflab qfsubh">Fail unless done first (${nf(u)})</div><ul class="qfgl qfgu">${u.slice().sort(byLv).map(li).join('')}</ul>`:''}
  <div class="qfsafe"><p>Safe order: finish these quests, then continue ${nm(l0.failer)}.</p></div>
  <details class="qfdata"><summary>Game data (remaster files, full trace)</summary><p>Where this happens in the quest files: ${qsEsc(l0.trigger_phase)}</p><p>The step itself (shared by every quest above):</p><ul>${evList(sh)}</ul>${ls.map(l=>`<p><b>${nm(l.failed)}</b></p><ul>${evList(l.evidence.filter(e=>e.s==null))}</ul>`).join('')}${l0.premise?`<p>Reading used by some links: ${qsEsc(l0.premise)}.</p>`:''}<p>Whether the game fails a quest you have not started yet is unconfirmed.</p></details></section>`}
const lvk=q=>q.lv==null?1e9:q.lv,spx=g=>{const R=QS.R,r=R&&R.quests[g],i=r&&r.s?R.points.findIndex(p=>p[0]===r.s):-1;return i<0?null:i},   // v39.9: the story point of a quest in the game's order (QUEST-RULES.json `s`, the order of `points`); null when unknown
 byLv=(a,b)=>lvk(qq(a.failed))-lvk(qq(b.failed))||qq(a.failed).n.localeCompare(qq(b.failed).n);
// v39.9: from two links on, the banner names each failer and the quests at risk, one sentence per failer; more than 3 quests at risk: the first 2 by level, then "and N more"
const nlist=ns=>ns.length>3?ns.slice(0,2).join(', ')+' and '+(ns.length-2)+' more':ns.length>1?ns.slice(0,-1).join(', ')+' and '+ns[ns.length-1]:ns[0];
const uq=ls=>[...new Set(ls.slice().sort(byLv).map(l=>l.failed))],vb=ls=>{const v=new Set(ls.map(l=>l.effect==='Deactivate'?'closes':qsState(l.failed)==='none'?'fails or closes':'fails'));return v.size===1?[...v][0]:'fails or closes'};   // "fails or closes" where the game's effect on a quest not started is unconfirmed, as in bline
function bsent(F,ls){const[m,u]=sp(ls.filter(l=>!isC(l))),who=`${cn(F,'red')} <span class="qfreg">(${rg(F)})</span>`,nms=x=>nlist(uq(x).map(g=>cn(g,'amber'))),out=[];
 if(m.length||u.length)out.push(`Continuing ${who} ${vb(m.length?m:u)} ${m.length?nms(m)+(u.length?`, and ${nf(u)} more unless you've ${qsEsc(ug(u))}`:''):nms(u)+` unless you've ${qsEsc(ug(u))}`}.`);
 const by=new Map();ls.filter(isC).forEach(l=>{if(!by.has(l.failed))by.set(l.failed,new Set());by.get(l.failed).add(qsEsc(l.choice))});   // two choices that fail the same quest are one sentence
 by.forEach((cs,f)=>out.push(`Choosing ${[...cs].join(' or ')} in ${who} fails ${cn(f,'amber')}.`));return out}
function bsents(Lb){const m=new Map();Lb.forEach(l=>{if(!m.has(l.failer))m.set(l.failer,[]);m.get(l.failer).push(l)});
 return dd([...m].sort((a,b)=>lvk(qq(a[0]))-lvk(qq(b[0]))||qq(a[0]).n.localeCompare(qq(b[0]).n)).flatMap(([F,ls])=>bsent(F,ls)).join(' '))}
function banner(L){const Lb=L.filter(l=>!isC(l)||qsState(l.failer)==='active'),E=groups(Lb);if(!E.length)return'';   // a choice shows on the banner only while its failer is active
 const msg=Lb.length>1?bsents(Lb):bline(Lb[0]);
 return`<div class="qfbanner" role="note"><div class="qfbrow"><svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 2 21h20L12 3z"/><path d="M12 10v5M12 18h.01"/></svg><p>${msg}</p>
 <button type="button" class="qfmore" aria-expanded="false" aria-controls="qfPanel">More details</button></div>
 <div class="qfpanel" id="qfPanel" hidden><div class="qflab">QUEST DEPENDENCY</div>${groups(L).map(g=>g.length>=GROUP_MIN?depG(g):dep(g[0])).join('')}</div></div>`}
function wireDeps(box){box.querySelectorAll('[data-go]').forEach(x=>{x.onclick=()=>goTo(x.dataset.go)});box.querySelectorAll('[data-fin]').forEach(x=>{x.onclick=()=>qsMark(x.dataset.fin,'done')})}
function wireBanner(box){const b=box.querySelector('.qfmore'),pn=box.querySelector('.qfpanel');if(!b)return;
 const set=()=>{pn.hidden=!A.open;b.setAttribute('aria-expanded',String(A.open));b.textContent=A.open?'Hide details':'More details'};set();b.onclick=()=>{A.open=!A.open;set()};
 wireDeps(box)}
// "Go to quest": its region tab, the same view, then the row or marker (scrolled to, focused, its ring pulses for about 2 s; reduced motion: a plain outline for as long)
async function goTo(g){const q=qq(g);if(!q)return;const lv=QS.view==='fails';if(lv){qsSetView('list');qsEl('screenQ').classList.remove('qs-detail')}if(lv||q.r!==QS.region){QS.region=q.r;qsRenderAll()}   // the failures view has no markers: go on in the List
 const sel=()=>document.querySelector((QS.view==='list'?'.qsrow':'.qsdot')+'[data-g="'+g+'"]'),frame=()=>new Promise(r=>requestAnimationFrame(r));await frame();let el=sel();
 if(!el&&QS.view==='list'&&(QS.kind!=='all'||QS.q||QS.hide)){QS.kind='all';QS.q='';QS.hide=false;qsRenderAll();await frame();el=sel()}   // a filter was hiding it
 if(!el){qsSelect(g,true);return}                                  // not drawn in this view (done and hidden, or in a closed cell): open its detail instead
 el.scrollIntoView({block:'center',inline:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});el.focus({preventScroll:true});
 const t=el.closest('.qfrow')||el,id=++A.pulse;t.classList.add('qf-pulse');setTimeout(()=>{if(A.pulse===id)t.classList.remove('qf-pulse')},2000)}
// ---- the Quest failures view: every verified link, whatever the region tab or the level; sorted by the level of the quest that causes the fail, then by name; links with a shared trigger sit under one header, sorted by the level of the failed quest ----
const stat=l=>{const f=qsState(l.failed),r=qsState(l.failer);return f==='done'?['safe','Safe · you finished it']:f==='failed'?['failed','Failed']:isC(l)?(r==='done'?['missed','Missed · the choice is made']:r==='failed'?['safe','Safe · the causing quest failed']:['open','Open · decided in the quest']):r==='done'?['missed','Missed · the causing quest is done']:r==='failed'?['safe','Safe · the causing quest failed']:['open','Open · plan for it']};
const meta2=g=>`${qsEsc(qsKindName(qq(g).t))} · ${rg(g)}`+(qq(g).npc?' · '+qsEsc(qq(g).npc):'');
function rowx(l,grp){const k=l.id,[c,t]=stat(l),o=A.det.has(k),amber=`<div class="qfblk amber"><div class="qflab">THIS ${l.effect==='Deactivate'?'CLOSES':'FAILS'}</div><div class="qfbig">${nm(l.failed)}</div><div class="qfmeta">${meta2(l.failed)}${grp?' · level '+qsLevelText(qq(l.failed)):''}</div></div>`,
  st=`<div class="qfblk st"><span class="qfst ${c}">${t}</span><button type="button" class="qfdetb" aria-expanded="${o}">Details ›</button></div>`;
 const head=grp?`${amber}${l.kind==='fails_unless_set'?`<div class="qfblk mid"><div class="qflab">THE CONDITION</div><div class="qfunl">${uS(l)}</div></div>`:''}`
  :`<div class="qfblk red"><div class="qflab">${isC(l)?'IF YOU CHOOSE':'IF YOU DO'}</div><div class="qfbig">${isC(l)?qsEsc(l.choice.charAt(0).toUpperCase()+l.choice.slice(1)):nm(l.failer)}</div><div class="qfmeta">${isC(l)?'in '+nm(l.failer)+' · ':''}${meta2(l.failer)} · level ${qsLevelText(qq(l.failer))}</div></div>
  <div class="qfblk mid"><div class="qflab">${isC(l)?'THE CHOICE':'AT THIS STEP'}</div><div class="qfstepn">${stepTxt(l)}</div>${l.kind==='fails_unless_set'?`<div class="qfunl">${uS(l)}</div>`:''}</div>${amber}`;
 return`<div class="qfrowx" data-k="${k}"><div class="qfr1">${head}${st}</div>${A.dueNow.has(l)?`<div class="qfinl">${prompt(l,1)}</div>`:''}<div class="qfrdep"${o?'':' hidden'}>${dep(l)}</div></div>`}
function listAll(host){A.dueNow=new Set(due());const vis=l=>!(A.hide&&stat(l)[0]!=='open'),items=groups(A.links.filter(vis)).map(g=>g.slice().sort(g.length>=GROUP_MIN?byLv:(a,b)=>qq(a.failed).n.localeCompare(qq(b.failed).n))).sort((a,b)=>{const x=qq(a[0].failer),y=qq(b[0].failer);const sa=spx(x.g),sb=spx(y.g);return lvk(x)-lvk(y)||(sa!=null&&sb!=null?sa-sb:0)||x.n.localeCompare(y.n)||qq(a[0].failed).n.localeCompare(qq(b[0].failed).n)});
 const html=items.map(g=>g.length>=GROUP_MIN?`<section class="qfgrp" aria-label="${qsEsc(cap(g[0].trigger_label))}"><div class="qfgh"><div class="qfgt"><div class="qflab">IF YOU DO</div><b class="qfbig">${nm(g[0].failer)}</b><span class="qfmeta">${meta2(g[0].failer)} · level ${qsLevelText(qq(g[0].failer))}</span></div>
  <div class="qfgs"><div class="qflab">AT THIS STEP</div><div class="qfstepn">${stepTxt(g[0])}</div></div><span class="qfgn">${(()=>{const[m,u]=sp(g);return(m.length?plural(nf(m),'quest')+' fail'+(nf(m)>1?'':'s')+' here':'')+(m.length&&u.length?', ':'')+(u.length?nf(u)+(m.length?' more':' quest'+(nf(u)>1?'s':''))+' unless done first':'')})()}</span></div>${(()=>{const[m,u]=sp(g);return m.map(l=>rowx(l,true)).join('')+(u.length?`<div class="qfgsub">Fail unless done first</div>`+u.map(l=>rowx(l,true)).join(''):'')})()}</section>`:rowx(g[0],false)).join('');
 host.innerHTML=`<section class="qfall" aria-label="Quest failures"><div class="qfhead"><div class="qfht"><h2>Every quest that fails another</h2><p>All regions, whatever your level or progress, sorted by the level of the quest that causes the fail. Only links confirmed from the remaster's game files.</p></div>
 <label class="qfhide"><input type="checkbox" id="qfHide"${A.hide?' checked':''}> Hide ones I've dealt with</label></div>
 <div class="qfrowsx">${html||'<p class="qfnote">Nothing open: every link is dealt with. Turn the filter off to see them.</p>'}</div>
 <p class="qfnote">Status per row: <b class="s-open">Open</b> (both quests still open) · <b class="s-safe">Safe</b> (you finished the at-risk quest) · <b class="s-failed">Failed</b> · <b class="s-missed">Missed</b> (the causing quest is done, the other not).</p>
 ${A.cand>0?`<p class="qfnote qfcand">${A.cand} more possible fail links found in the game files are still being checked.</p>`:''}</section>`;
 host.querySelector('#qfHide').onchange=e=>{A.hide=e.target.checked;listAll(host);host.querySelector('#qfHide').focus()};
 host.querySelectorAll('.qfdetb').forEach(b=>{b.onclick=()=>{const r=b.closest('.qfrowx'),p=r.querySelector('.qfrdep'),k=r.dataset.k;p.hidden=!p.hidden;b.setAttribute('aria-expanded',String(!p.hidden));if(p.hidden)A.det.delete(k);else A.det.add(k)}});wireDeps(host);wire(host)}
function prompt(l,inl){return`<div class="qfprompt" role="${inl?'group':'status'}"${inl?` aria-label="${nm(l.failed)}: mark it failed or finished"`:''} data-k="${l.failer}${l.failed}" data-f="${l.failer}"><p><b>${nm(l.failer)}</b> is done. <b>${nm(l.failed)}</b> would have ${l.effect==='Deactivate'?'closed':'failed'} along the way.</p>
 <div class="qfbtns"><button type="button" class="btn" data-a="failed" data-g="${l.failed}">Mark it failed</button><button type="button" class="btn" data-a="done" data-g="${l.failed}">I finished it first</button><button type="button" class="qfx2" data-a="close" aria-label="Close this notice">×</button></div></div>`}
function wire(el){el.querySelectorAll('.qfprompt [data-a]').forEach(b=>{b.onclick=()=>{const k=b.closest('.qfprompt').dataset.k,a=b.dataset.a;
 const f=b.closest('.qfprompt').dataset.f,inD=!!b.closest('#qsDetail');
 if(a==='close'){A.gone.add(k);qsRenderAll()}else qsMark(b.dataset.g,a);   // one state for every copy of the prompt (the strip, the detail panel, the List row, the failures row): redraw them all
 const t=inD?document.querySelector('#qsDetail .qsmark.on'):document.querySelector('.qsrow[data-g="'+f+'"]');if(t)t.focus({preventScroll:true})}})}
function mk(tag,cls,html){const e=document.createElement(tag);e.className=cls;e.innerHTML=html;return e}
function paint(){if(!A.links.length||!QS.data)return;obs.disconnect();try{
 const view=qsEl('qsView'),L=live();
 // the prompt(s) above Next up: every link whose failer is done and whose failed quest is still open
 let box=qsEl('qfPrompts'),bn=qsEl('qfBanner');if(!bn){bn=mk('div','qfbbox','');bn.id='qfBanner';qsEl('qsMiss').before(bn)}if(!box){box=mk('div','qfprompts','');box.id='qfPrompts';qsEl('qsMiss').before(box)}
 box.innerHTML=due().map(prompt).join('');wire(box);
 // the banner above Next up (so on every region tab and every view): one line, or a summary, and the details panel
 const nu=new Set(qsNextUp().filter(q=>q.t==='main').map(q=>q.g)),LB=L.filter(l=>qsState(l.failer)==='active'||nu.has(l.failer)),bh=LB.length?banner(LB):'';/* v39.8: the banner and its panel only for a failer that is active or a main quest shown in Next up; every link stays in the tab and the rows */
 if(bn.dataset.h!==bh){bn.dataset.h=bh;bn.innerHTML=bh;wireBanner(bn)}
 // region tabs: a red dot when the tab holds a quest that fails another, an amber one when it holds a quest at risk
 qsEl('qsRegs').querySelectorAll('.qsreg[data-r]').forEach(t=>{t.querySelectorAll('.qfdots').forEach(e=>e.remove());const k=t.dataset.r,r=L.some(l=>qq(l.failer).r===k),a=L.some(l=>qq(l.failed).r===k&&!isC(l));if(!r&&!a)return;
  const w=(r?'has a quest that fails another':'')+(r&&a?' and ':'')+(a?'has a quest at risk of failing':''),n=t.querySelector('.qsrn').textContent;
  t.append(mk('span','qfdots',(r?'<i class="qfd red"></i>':'')+(a?'<i class="qfd amber"></i>':'')));const o=t.dataset.t||(t.dataset.t=t.title);t.setAttribute('aria-label',n+', '+w.replace(' and has',' and')+', '+t.querySelector('small').textContent);t.title=o+' · '+w});
 // List rows: a card around the row with the chip, the step and the Why? disclosure
 const D=due();view.querySelectorAll('.qsrow[data-g]').forEach(r=>{if(r.parentNode.classList.contains('qfrow'))return;const g=r.dataset.g,f=fails(g),k=risks(g),b=by(g),pd=D.filter(l=>l.failer===g);if(!f.length&&!k.length&&!b&&!pd.length)return;
  const w=mk('div','qfrow'+(f.length?' qf-fail':'')+(k.length?' qf-risk':''),'');r.before(w);w.append(r);
  const x=mk('div','qfextra',(f.length?chipF(nq(f))+steps(f):'')+(k.length?chipR(k)+k.map(l=>`<span class="qfstep">${riskLine(l)}</span>`).join('')+k.map(why).join(''):'')+(!f.length&&!k.length&&b?`<span class="qfby">by ${nm(b.failer)} (${qsEsc(b.trigger_short)})</span>`:''));
  if(x.innerHTML)w.append(x);if(pd.length){const e=mk('div','qfinl',pd.map(l=>prompt(l,1)).join(''));w.append(e);wire(e)}   // v39.9: the prompt also sits on the row of the quest that was marked done
  if(f.length||k.length)r.setAttribute('aria-label',r.getAttribute('aria-label')+say(f,k))});
 // dots (Level band, Timeline): a ring and the words in the label and the tooltip
 view.querySelectorAll('.qsdot[data-g]').forEach(d=>{const g=d.dataset.g,f=fails(g),k=risks(g);if(!f.length&&!k.length)return;
  if(f.length)d.classList.add('qf-fail');if(k.length)d.classList.add('qf-risk');d.setAttribute('aria-label',d.getAttribute('aria-label')+say(f,k))});
 // Next up cards
 qsEl('qsNext').querySelectorAll('.qscard[data-g]').forEach(c=>{const g=c.dataset.g,f=fails(g),k=risks(g),s=c.querySelector('.qscn');if(!s||(!f.length&&!k.length))return;
  if(f.length)c.classList.add('qf-fail');if(k.length)c.classList.add('qf-risk');
  if(f.length)s.append(mk('span','qfcaution',groups(f).map(g=>g.length>=GROUP_MIN?`Careful: ${qsEsc(g[0].trigger_label)} fails ${plural(nf(sp(g)[0].length?sp(g)[0]:g),'open quest')}${sp(g)[0].length&&sp(g)[1].length?', and '+nf(sp(g)[1])+' more unless you\'ve '+qsEsc(ug(sp(g)[1])):''}.`:g.map(l=>isC(l)?`Careful: choosing ${qsEsc(l.choice)} fails ${nm(l.failed)}.`:`Careful: ${qsEsc(l.trigger_label)} ${wd(l)} ${nm(l.failed)}${unl(l)}.`).join(' ')).join(' ')));if(k.length)s.append(mk('span','qfchip amber','Do before '+[...new Set(k.map(l=>nm(l.failer)))].join(', ')))});
 // the detail panel of the selected quest
 const dt=qsEl('qsDetail'),g=QS.sel,m=dt.querySelector('.qsmeta');
 dt.querySelectorAll('.qfdet,.qfinl').forEach(e=>e.remove());   // a repaint without a redraw must not stack copies
 if(g&&m){const f=fails(g),k=risks(g),b=by(g),p=due().filter(l=>l.failed===g);
  const h=(f.length?groups(f).map(gr=>`<div class="qfbox red">${chipF(nq(gr))}${gr.length>=GROUP_MIN?`<span class="qfstep">${stepG(gr)}</span>`:gr.map(l=>`<span class="qfstep">${step(l)}</span>`).join('')}</div>`).join(''):'')+(k.length?k.map(l=>`<div class="qfbox amber">${chipR([l])}<span class="qfstep">${riskLine(l)}</span>${why(l)}</div>`).join(''):'')+(b?`<p class="qfby">Failed by ${nm(b.failer)} (${qsEsc(b.trigger_short)})</p>`:'')+p.map(prompt).join('');
  if(h){const e=mk('div','qfdet',h);m.after(e);wire(e)}
  const pd=due().filter(l=>l.failer===g),pg=dt.querySelector('.qsprog');if(pd.length&&pg){const e=mk('div','qfinl',pd.map(l=>prompt(l,1)).join(''));pg.after(e);wire(e)}}   // v39.9: under MY PROGRESS of the quest that was marked done
 }finally{watch()}}
const obs=new MutationObserver(()=>paint());
function watch(){['qsView','qsNext','qsDetail','qsRegs'].forEach(id=>{const e=qsEl(id);if(e)obs.observe(e,{childList:true,subtree:true})})}
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;const p=document.activeElement&&document.activeElement.closest&&document.activeElement.closest('.qfprompt');
 if(p){e.preventDefault();e.stopPropagation();A.gone.add(p.dataset.k);qsRenderAll()}},true);   // Esc closes the notice the focus is in (before the drawer's own Esc)
// the data file stores evidence items that several links share once (`ev`); a link holds their index: here every link gets the items themselves (s = the index of a shared one)
function norm(d){const ev=(d&&d.ev)||[];return((d&&d.links)||[]).filter(l=>l&&QS.byG.has(l.failer_guid)&&QS.byG.has(l.failed_guid)).map(l=>Object.assign({},l,{failer:l.failer_guid,failed:l.failed_guid,evidence:(l.evidence||[]).map(e=>typeof e==='number'?Object.assign({s:e},ev[e]):e)}))}
window.QF={
 init(d){A.links=norm(d);A.links.forEach((l,i)=>{if(A.links.filter(x=>x.failer+x.failed===l.failer+l.failed).length>1)l.id=l.failer+l.failed+':'+(l.fact||i);else l.id=l.failer+l.failed});A.cand=Math.max(0,Math.floor(Number(d&&d.candidates))||0);
  const v=qsEl('qsVFails');if(v){v.hidden=!A.links.length;v.textContent='Quest failures · '+A.links.length}watch()},
 fails:listAll,
 rank:g=>risks(g).length?-1:0,                                   // the Level band puts the at-risk quest above its failer inside one cell
 risk:()=>[...new Set(live().filter(l=>!isC(l)&&qsState(l.failer)==='active').map(l=>l.failed))].map(g=>QS.byG.get(g)),   // Next up: the amber quests come first, but only once the failer is active (a quest not started yet does not push another quest forward)
 tip:q=>{const f=fails(q.g),k=risks(q.g);return groups(f).map(gr=>`<span class="qfsub red">${gr.length>=GROUP_MIN?stepG(gr):gr.map(step).join('</span><span class="qfsub red">')}</span>`).join('')+k.map(l=>`<span class="qfsub amber">Do before ${nm(l.failer)}: ${riskLine(l)}</span>`).join('')},
 // v39.9: the detail panel's rule lines for a quest with a shipped fail link: null (no link, keep the panel's own line), '' (it only causes fails: no line) or one "Can fail" line per failer and kind
 line:g=>{const as=A.links.filter(l=>l.failed===g);if(!as.length)return A.links.some(l=>l.failer===g)?'':null;
  const ln=a=>{const f=`<button type="button" class="qslink t-${qq(a.failer).t}" data-g="${a.failer}">${nm(a.failer)}</button>`;return isC(a)?`Can fail by a choice in ${f}`:isU(a)?`Can fail at ${f} unless you've ${qsEsc(a.condition)} first`:`Can fail: do it before ${f}`};
  return[...new Set(as.slice().sort((a,b)=>lvk(qq(a.failer))-lvk(qq(b.failer))||qq(a.failer).n.localeCompare(qq(b.failer).n)).map(ln))].map(t=>`<p class="qsrule qfcan">${t}</p>`).join('')},
 live,due,paint};
})();
