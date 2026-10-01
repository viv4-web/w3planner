
const APP_VERSION="v27";
const CFG=Object.assign({mode:"online",shareBase:""},window.PLANNER_CONFIG||{});
const DATA=/*@data:DATA*/;

// ---- skill tooltip engine: ported from the game's own menu scripts ----
const TIPDATA=/*@data:TIPDATA*/;
// Skill tooltip formulas, ported from the game scripts and compiled ahead of time (no eval at runtime).
const TIPFN=/*@data:TIPFN*/;
function tipText(ti,i,L){const id=TREES[ti].sk[i].id,D=TIPDATA.desc[id]||[];L=Math.max(1,Math.min(3,L));
 const base=D[L-1]||D[0]||TREES[ti].sk[i].desc||'';if(!TIPFN[id])return base;
 try{  const V=o=>({b:o?o.b:0,a:o?o.a:0,m:o?o.m:0});
  const enumId=e=>{const m=e.match(/S_(Sword|Magic|Alchemy|Perk)_(s?)(\d+)/);return ({Sword:'sword',Magic:'magic',Alchemy:'alchemy',Perk:'perk'})[m[1]]+'_'+m[2]+(+m[3])};
  const NTZ=x=>String(+(+x).toFixed(2));
  const fill=(s,a,f,t)=>{let i=0,j=0,k=0;return (s||'').replace(/\$I\$/g,()=>{const v=a&&a[i++];return v===undefined||isNaN(v)?'?':v}).replace(/\$F\$/g,()=>{const v=f&&f[j++];return v===undefined||isNaN(v)?'?':NTZ(v)}).replace(/\$S\$/g,()=>t&&t[k]!==undefined?t[k++]:'?')};
  const txt=k=>k==='__desc__'?base:(TIPDATA.locs[k]||'');
  const H={SA:(e,a)=>V((TIPDATA.ab[enumId(e)]||{})[a]),AA:(n,a)=>V((TIPDATA.ab[n]||{})[a]),MUL:(v,k)=>({b:v.b*k,a:v.a*k,m:v.m*k}),CALC:v=>v.b*(1+v.m)+v.a,
   NTZ,FTS:NTZ,FTSP:(x,p)=>(+x).toFixed(p),LOC:txt,LOCP:(k,a,f,t)=>fill(txt(k),a,f,t),
   GetWitcherPlayer:()=>({GetStatMax:()=>100,GetAlchemyS03Threshold:()=>NaN}),theGame:{GetDefinitionsManager:()=>({GetAbilityAttributeValue:()=>{}})},
   EffectTypeToName:()=>'',StatEnumToName:()=>'',BCS_Stamina:0,BCS_Vitality:0,EET_IgnorePain:0};
  const r=TIPFN[id](H,L,id);return (r||base).replace(/<br\s*\/?>/g,'\n').replace(/<[^>]+>/g,'')}catch(e){return base.replace(/\$[IFS]\$/g,"?")}}
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');
function tipHTML(ti,i){const K=TREES[ti].sk[i],L=S.lv[ti][i];let s=`<div class="tt-h"><b>${K.name.toUpperCase()}</b><span>${L}/${K.max}</span></div><div class="tt-b">`;
 if(L>0)s+=`<div class="cur">Current level:</div>${esc(tipText(ti,i,L))}`;
 if(L<K.max)s+=`${L>0?'<div class="gap"></div>':''}<div class="nxt">Next level:</div><span class="dimt">${esc(tipText(ti,i,L+1))}</span>`;
 return s+'</div>'}

const EXTRA=/*@data:EXTRA*/;
const MUTIMG=/*@data:MUTIMG*/;const LOCK=/*@data:LOCK*/;
const ART=/*@data:ART*/;
const META=[{id:'c',name:'Combat',color:'#9b1a14',glow:'#e0473a',wash:'#5a0a08'},{id:'s',name:'Signs',color:'#1c58d0',glow:'#5b95ff',wash:'#0c2a6e'},{id:'a',name:'Alchemy',color:'#2f7322',glow:'#7cc95a',wash:'#173d10'},{id:'g',name:'General',color:'#9c6212',glow:'#f0b050',wash:'#4a2e08'}];
const TREES=META.map((m,ti)=>{const d=DATA[ti];const t={...m,sk:d.map((r,j)=>({id:r[0],name:EXTRA[ti][j][0],desc:EXTRA[ti][j][1],icon:EXTRA[ti][j][2],max:r[4],pts:r[5],req:r[6],alt:!!r[7],rew:!!r[8],sub:r[9]})),
 nodes:d.map(r=>[246+r[3]*48.92,344+r[2]*32.04]),edges:[]};t.sk.forEach((s,i)=>s.req.forEach(p=>t.edges.push([p,i])));
 if(ti===3)t.core=t.sk.map((s,i)=>s.req.length?-1:i).filter(i=>i>=0);return t});
const MAXL=3;const mx=(ti,i)=>TREES[ti].sk[i].max;
const MUTS=/*@data:MUTS*/.map((m,k)=>({...m,tier:k%3}));
const SPECIAL_MUT=/*@data:SPECIAL_MUT*/;
{const base={red:0,blue:3,green:6},ico={red:9,blue:10,green:11};SPECIAL_MUT.forEach(([lb,c])=>MUTS.push({...MUTS[base[c]],name:lb+' mutagen',label:lb,special:true,tier:0,icon:ico[c]}))}
const STATN={"vitality": "Vitality", "attack_power": "Attack power", "spell_power": "Sign intensity"};
const MUTCOL={red:'#b33b3b',blue:'#3d74d4',green:'#4f9a3e'};
// parents: connected node above
TREES.forEach(t=>{t.parents=t.sk.map(s=>s.req);t.children=t.sk.map(()=>[]);t.edges.forEach(([p,c])=>t.children[p].push(c));});

let S; // state
function blank(){return{lv:TREES.map(t=>t.nodes.map(()=>0)),slots:Array(16).fill(null),muts:Array(4).fill(null),mres:Array(12).fill(0),mact:-1,gear:Array(9).fill(0),rs:'ng'}}
function demo(){const s=blank();const T=TREES[1],ix=id=>T.sk.findIndex(k=>k.id===id);
 ['magic_s42','magic_s3','magic_s11','magic_s35','magic_s37','magic_s40'].forEach(id=>s.lv[1][ix(id)]=1);s.lv[1][ix('magic_s11')]=3;
 ['magic_s11','magic_s3','magic_s35','magic_s37','magic_s40'].forEach((id,k)=>s.slots[k]=[1,ix(id)]);s.muts[0]=6;return s}
let tab=1, sel=null, selMut=null;

// ---- encoding ----
const A='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
// ---- gear segment (g1): the 9th segment of a link, only when gear is equipped or the mode is New Game Plus: g1 + A (First playthrough) or B (New Game Plus) + 2 characters per slot (CLAUDE.md, "Gear link format") ----
function gearSeg(){if(!S.gear.some(Boolean)&&S.rs!=='ng_plus')return'';return'.g1'+(S.rs==='ng_plus'?'B':'A')+S.gear.map(v=>A[v>>6]+A[v&63]).join('')}
function enc(){const d=S.lv.flat();let o='';for(let i=0;i<d.length;i+=3)o+=A[(d[i]||0)*16+(d[i+1]||0)*4+(d[i+2]||0)];
 o+='.';S.slots.forEach(x=>{const v=x?x[0]*20+x[1]+1:0;o+=A[v>>6]+A[v&63]});
 o+='.';S.muts.forEach(m=>o+=m==null?'-':m.toString(36));o+='.'+lvl()+'.'+bonusPts();o+='.'+parseInt(S.mres.map(x=>x?1:0).reverse().join(''),2).toString(36)+'.'+(S.mact+1);return'v1.'+o+gearSeg()}
function dec(h){try{
 // Link data is untrusted: it is only ever read as numbers, and anything malformed is rejected.
 if(typeof h!=='string'||h.length>400)return null;
 const P=h.split('.');if(P[0]!=='v1'||P.length<4||P.length>9)return null;
 const [,l,sl,m,L,B,MR,MA,G]=P,ALPHA=[...A],inA=s=>[...s].every(c=>ALPHA.includes(c));
 if(G!==undefined&&!/^g1[AB][A-Za-z0-9_-]{18}$/.test(G))return null;
 const NSK=TREES.reduce((a,t)=>a+t.sk.length,0);
 if(l.length!==Math.ceil(NSK/3)||!inA(l))return null;
 if(!(sl.length===24||sl.length===32)||!inA(sl))return null;
 if(!/^[-0-9a-z]{4}$/.test(m)||[...m].some(c=>c!=='-'&&parseInt(c,36)>=MUTS.length))return null;
 const num=(x,lo,hi)=>{if(x===undefined||x==='')return null;if(!/^[0-9]{1,3}$/.test(x))return NaN;return Math.max(lo,Math.min(hi,+x))};
 const lv=num(L,1,100),bo=num(B,0,100);if(Number.isNaN(lv)||Number.isNaN(bo))return null;
 if(MR!==undefined&&!/^[0-9a-z]{1,3}$/.test(MR))return null;
 if(MA!==undefined&&!/^[0-9]{1,2}$/.test(MA))return null;
 const s=blank(),d=[];
 for(const ch of l){const n=A.indexOf(ch);d.push(n>>4,(n>>2)&3,n&3)}
 let k=0;TREES.forEach((t,ti)=>t.sk.forEach((sk,i)=>{s.lv[ti][i]=Math.min(sk.max,d[k++]||0)}));
 const used=new Set();
 for(let i=0;i<sl.length/2;i++){const v=A.indexOf(sl[i*2])*64+A.indexOf(sl[i*2+1]);if(v<1||v>80)continue;
  const ti=Math.floor((v-1)/20),ix=(v-1)%20;
  if(ti>=TREES.length||ix>=TREES[ti].sk.length||!s.lv[ti][ix]||used.has(ti+'.'+ix))continue;
  used.add(ti+'.'+ix);s.slots[i]=[ti,ix]}
 [...m].forEach((c,i)=>{s.muts[i]=c==='-'?null:parseInt(c,36)});
 if(MR){const bits=parseInt(MR,36)&4095;for(let i=0;i<12;i++)s.mres[i]=(bits>>i)&1}
 if(MA!==undefined){const a=+MA-1;s.mact=(a>=0&&a<12&&s.mres[a])?a:-1}
 if(lv!==null){document.getElementById('lvl').value=lv;document.getElementById('bonuspts').value=bo===null?0:bo}
 if(G!==undefined){s.rs=G[2]==='B'?'ng_plus':'ng';for(let i=0;i<9;i++)s.gear[i]=A.indexOf(G[3+2*i])*64+A.indexOf(G[4+2*i])}
 return s}catch(e){return null}}
// ---- rules ----
const spent=()=>S.lv.flat().reduce((a,b)=>a+b,0)+MUT.reduce((a,m,i)=>a+(S.mres[i]?m.sp:0),0);
const lvl=()=>Math.max(1,Math.min(100,+document.getElementById('lvl').value||1)),bonusPts=()=>Math.max(0,+document.getElementById('bonuspts').value||0);const budget=()=>lvl()-1+bonusPts();
const GA=/*@data:GA*/;
const MUT=/*@data:MUT*/,MASTER=/*@data:MASTER*/,MSLOT_UNLOCK=[2,4,8,12];
const SLOT_UNLOCK=[0,2,4,6,8,10,12,15,18,22,26,30],MUT_UNLOCK=[2,9,16,28];
const mCount=()=>S.mres.reduce((a,b)=>a+b,0);
const slotOpen=k=>k<12?budget()>=SLOT_UNLOCK[k]:mCount()>=MSLOT_UNLOCK[k-12],sockOpen=g=>budget()>=MUT_UNLOCK[g];
const TREECOL=['red','blue','green',null];
const accepts=(k,v)=>k<12||(S.mact>=0&&v&&TREECOL[v[0]]&&MUT[S.mact].cols.includes(TREECOL[v[0]]));
const mCanResearch=i=>!S.mres[i]&&MUT[i].req.every(j=>S.mres[j])&&budget()-spent()>=MUT[i].sp;
const mCanUndo=i=>S.mres[i]&&!MUT.some((m,j)=>S.mres[j]&&m.req.includes(i));
function enforceLocks(){S.slots=S.slots.map((x,k)=>slotOpen(k)&&accepts(k,x)?x:null);S.muts=S.muts.map((m,g)=>sockOpen(g)?m:null);if(S.mact>=0&&!S.mres[S.mact])S.mact=-1}
function available(ti,i){const t=TREES[ti],r=t.parents[i];if(!r.length)return true;return t.sk[i].alt?r.some(p=>S.lv[ti][p]>0):r.every(p=>S.lv[ti][p]>0)}
function canRemove(ti,i){if(S.lv[ti][i]>1)return true;const t=TREES[ti];S.lv[ti][i]=0;const ok=t.children[i].every(c=>S.lv[ti][c]===0||available(ti,c));S.lv[ti][i]=1;return ok}
function add(ti,i){if(S.lv[ti][i]<mx(ti,i)&&available(ti,i)&&spent()<budget()){S.lv[ti][i]++;save()}}
function rem(ti,i){if(S.lv[ti][i]>0&&canRemove(ti,i)){S.lv[ti][i]--;if(!S.lv[ti][i])S.slots=S.slots.map(x=>x&&x[0]===ti&&x[1]===i?null:x);save()}}
function equip(ti,i){if(!S.lv[ti][i]||S.slots.some(x=>x&&x[0]===ti&&x[1]===i))return;const f=S.slots.findIndex((x,k)=>k<12&&x==null&&slotOpen(k));if(f>=0){S.slots[f]=[ti,i];save()}}
function save(){history.replaceState(null,'','#'+enc());const tt=document.getElementById('toast');if(tt)tt.hidden=true;render()}

// ---- original glyphs ----
function glyph(ti,i,cx,cy,c){const k=(i*7+ti*3)%8,s=18;const P=`stroke="${c}" stroke-width="3" fill="none" stroke-linecap="round"`;
 switch(k){case 0:return`<path d="M${cx-s},${cy+s} L${cx+s},${cy-s} M${cx-s+6},${cy-s+6} L${cx+s-6},${cy+s-6}" ${P}/>`;
 case 1:return`<path d="M${cx},${cy-s} L${cx+s},${cy+s-4} L${cx-s},${cy+s-4} Z" ${P}/><circle cx="${cx}" cy="${cy+3}" r="4" fill="${c}"/>`;
 case 2:return`<circle cx="${cx}" cy="${cy}" r="${s}" ${P}/><path d="M${cx-s},${cy} L${cx+s},${cy}" ${P}/>`;
 case 3:return`<path d="M${cx},${cy-s} L${cx+s},${cy} L${cx},${cy+s} L${cx-s},${cy} Z" ${P}/><path d="M${cx},${cy-8} L${cx},${cy+8}" ${P}/>`;
 case 4:return`<path d="M${cx-s},${cy+6} L${cx},${cy-10} L${cx+s},${cy+6} M${cx-s},${cy+16} L${cx},${cy} L${cx+s},${cy+16}" ${P}/>`;
 case 5:return`<path d="M${cx},${cy-s} L${cx+5},${cy-5} L${cx+s},${cy} L${cx+5},${cy+5} L${cx},${cy+s} L${cx-5},${cy+5} L${cx-s},${cy} L${cx-5},${cy-5} Z" ${P}/>`;
 case 6:return`<path d="M${cx-12},${cy-s} L${cx+12},${cy-s} L${cx-12},${cy+s} L${cx+12},${cy+s} Z" ${P}/>`;
 default:return`<circle cx="${cx}" cy="${cy}" r="7" ${P}/><circle cx="${cx}" cy="${cy}" r="${s}" ${P} stroke-dasharray="6 5"/>`}}

// ---- render ----
function renderTabs(){const el=document.getElementById('tabs');
 const items=[...TREES.map((t,ti)=>({name:t.name,color:t.color,n:S.lv[ti].filter(x=>x>0).length})),{name:'Mutagens',color:'#6d665c',n:S.muts.filter(m=>m!=null).length}];
 el.innerHTML=items.map((it,k)=>`<button class="tab" role="tab" aria-selected="${k===tab}" data-k="${k}" title="${it.name}"><img src="${GA.tab[k]}" alt="" class="ti">${it.name}<span class="n">${it.n}</span><i style="background:${it.color}"></i></button>`).join('')+`<span class="treeTitle">${items[tab].name}</span>`;
 el.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{tab=+b.dataset.k;sel=null;render()})}



const DEFS=(t)=>`<defs>
 <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
 <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .45  0 0 0 0 .38  0 0 0 .22 0"/></filter>
 <filter id="grey"><feColorMatrix type="saturate" values="0"/></filter>
 ${TREES.map(T=>`<linearGradient id="tile${T.id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${T.glow}"/><stop offset=".18" stop-color="${T.color}"/><stop offset="1" stop-color="${T.wash}"/></linearGradient>`).join('')}
 <linearGradient id="dark" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a2620"/><stop offset="1" stop-color="#15130f"/></linearGradient>
 ${t?`<radialGradient id="wash${t.id}" cx="50%" cy="0%" r="110%"><stop offset="0" stop-color="${t.color}" stop-opacity=".85"/><stop offset=".45" stop-color="${t.wash}" stop-opacity=".9"/><stop offset="1" stop-color="#0a0908"/></radialGradient>`:''}
</defs>`;
const pip=(x,y,on)=>`<path d="M${x},${y-4.5} L${x+4.5},${y} L${x},${y+4.5} L${x-4.5},${y} Z" fill="${on?'#fff':'#0008'}" stroke="#fff" stroke-width="1"/>`;
function tile(t,ti,i,x,y,L,av,opt={}){const h=opt.h||42,sel=opt.sel,core=t.core&&t.core.includes(i),K=t.sk[i],sz=h*2;
 const on=L>0, lit=on||(core&&!opt.slot);
 let s=`<rect x="${x-h}" y="${y-h}" width="${sz}" height="${sz}" fill="#0b0a09"/>
 ${lit?`<image href="${GA.tilebg[ti]}" x="${x-h}" y="${y-h}" width="${sz}" height="${sz}" preserveAspectRatio="none" ${on?'':'opacity=".55"'}/>`:`<rect x="${x-h}" y="${y-h}" width="${sz}" height="${sz}" fill="url(#dark)"/>`}
 <image href="${K.icon}" x="${x-h*.86}" y="${y-h*.9}" width="${h*1.72}" height="${h*1.72}" ${lit||av?'':'filter="url(#grey)" opacity=".45"'} ${lit?'':av?'opacity=".92"':''}/>
 <image href="${lit?GA.tilefr[ti]:av?GA.fravail:GA.frlock}" x="${x-h}" y="${y-h}" width="${sz}" height="${sz}" preserveAspectRatio="none" ${lit||av?'':'opacity=".6"'}/>
 <rect class="frame" x="${x-h+.5}" y="${y-h+.5}" width="${sz-1}" height="${sz-1}" fill="none" stroke="${sel?'#fff':'none'}" stroke-width="1.5"/>
 ${sel?`<image href="${GA.frsel}" x="${x-h*1.2}" y="${y-h*1.2}" width="${sz*1.2}" height="${sz*1.2}" preserveAspectRatio="none"/>`:''}`;
 if(on||(av&&!opt.slot)&&!core)for(let d=0;d<K.max;d++)s+=pip(x-14+d*14,y+h-7,d<L);
 return s}

function renderTree(){const p=document.getElementById('treePanel');
 if(tab===4){renderMutagens(p);return}
 const t=TREES[tab],ti=tab,lv=S.lv[ti];
 let s=`<svg viewBox="190 290 700 910" role="group" aria-label="${t.name} skill tree">${DEFS(t)}
 <rect x="190" y="290" width="700" height="910" fill="#080706"/><image href="${GA.treebg[ti]}" x="190" y="290" width="700" height="910" preserveAspectRatio="xMidYMid slice"/>
 <rect x="194" y="294" width="692" height="902" fill="none" stroke="${t.glow}" stroke-opacity=".35"/>`;
 t.edges.forEach(([a,b])=>{const on=lv[a]>0&&lv[b]>0;const[x1,y1]=t.nodes[a],[x2,y2]=t.nodes[b];
  s+=on?`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${t.glow}" stroke-width="6" opacity=".55" filter="url(#glow)"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#fff" stroke-width="2.4"/>`
       :`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#b9ab94" stroke-width="1.4" opacity=".45"/>`});
 t.nodes.forEach(([x,y],i)=>{const L=lv[i],av=available(ti,i),isSel=sel&&sel[0]===ti&&sel[1]===i;
  s+=`<g class="node" tabindex="0" data-i="${i}" style="cursor:${L?'grab':'pointer'}" aria-label="${t.sk[i].name}, level ${L} of ${t.sk[i].max}${av?'':', locked'}">${tile(t,ti,i,x,y,L,av,{sel:isSel})}</g>`});
 p.innerHTML=s+'</svg>';
 p.querySelectorAll('.node').forEach(g=>{const i=+g.dataset.i;
  g.onclick=()=>{if(noClick)return;if(sel&&sel[0]===ti&&sel[1]===i)tryAdd(ti,i);else{sel=[ti,i];render()}};
  g.oncontextmenu=e=>{e.preventDefault();sel=[ti,i];rem(ti,i)};
  g.onpointerdown=e=>{if(e.button===0&&e.pointerType!=='touch'&&S.lv[ti][i])press(e,{kind:'skill',v:[ti,i]})};
  g.onpointerenter=e=>showTip(e,ti,i);g.onpointermove=moveTip;g.onpointerleave=hideTip;
  g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();g.onclick()}if(e.key==='Backspace'||e.key==='Delete')rem(ti,i)}});
 document.getElementById('treeHint').textContent=(budget()===0?'You have no skill points yet: raise Level or Bonus points below to start. ':'')+(matchMedia('(pointer:coarse)').matches?'Tap to select, tap again to add a point. To equip, select a skill then tap an open slot. Use Remove point below to take points back.':'Click to select, click again to add a point, right-click to remove. Drag an invested skill onto a slot.')}

function mutIcon(m,cx,cy,r){return`<image href="${MUTIMG[MUTS[m].icon!==undefined?MUTS[m].icon:m]}" x="${cx-r*1.15}" y="${cy-r*1.15}" width="${r*2.3}" height="${r*2.3}"/>`}
function renderMutagens(p){let s=`<svg viewBox="0 0 700 910" role="group" aria-label="Mutagen collection">${DEFS()}<rect width="700" height="910" fill="#080706"/><image href="${GA.treebg[4]}" width="700" height="910" preserveAspectRatio="xMidYMid slice"/>`;
 const cell=(k,x,y,sp)=>{const m=MUTS[k],isSel=selMut===k;
  return `<g class="mut" tabindex="0" data-k="${k}" style="cursor:grab" aria-label="${m.name}"><title>${m.name}</title><rect class="frame" x="${x}" y="${y}" width="90" height="92" fill="#16130f" stroke="${isSel?'#fff':sp?'#8a7440':'#6b5a42'}" stroke-width="${isSel?2.5:1.5}"/>${mutIcon(k,x+45,y+(sp?36:46),sp?24:30)}${sp?`<text x="${x+45}" y="${y+84}" text-anchor="middle" fill="#cfc5b3" font-size="${m.label.length>12?10.5:12}">${m.label}</text>`:''}</g>`};
 for(let gx=0;gx<7;gx++)for(let gy=0;gy<9;gy++)s+=`<rect x="${20+gx*95}" y="${34+gy*97}" width="90" height="92" fill="none" stroke="#2a241d"/>`;
 s+=`<text x="20" y="24" fill="#c9a86a" font-size="15" letter-spacing="1.2">REGULAR</text><text x="400" y="24" fill="#c9a86a" font-size="15" letter-spacing="1.2">SPECIAL (LESSER BONUS)</text>`;
 for(let k=0;k<9;k++)s+=cell(k,20+(k%3)*95,34+Math.floor(k/3)*97,false);
 for(let k=9;k<MUTS.length;k++){const j=k-9;s+=cell(k,20+(4+Math.floor(j/9))*95,34+(j%9)*97,true)}
 p.innerHTML=s+'</svg>';
 p.querySelectorAll('.mut').forEach(g=>{const k=+g.dataset.k;g.onclick=()=>{if(noClick)return;selMut=k;sel=null;render()};g.onpointerdown=e=>{if(e.button===0&&e.pointerType!=='touch')press(e,{kind:'mut',v:k})};g.onkeydown=e=>{if(e.key==='Enter')g.onclick()}});
 document.getElementById('treeHint').textContent='Drag a mutagen onto a diamond socket, or select it and click the socket. Special mutagens give the same bonus as the Lesser mutagen of their colour.'}
const SLOTPOS=(()=>{const a=[];[[67,201,334],[567,698,830]].forEach(rows=>[281,517].forEach(x=>rows.forEach(y=>a.push([x,y]))));a.push([196,451],[292,451],[506,451],[602,451]);return a})();
const DIAM=[[92,201],[704,201],[92,700],[704,700]];
const MUTTREE={red:'c',blue:'s',green:'a'};
function synergyLv(){const t=TREES[3],i=t.sk.findIndex(s=>s.id==='perk_43');return i<0?0:S.lv[3][i]}
function slotMatch(k){const m=S.muts[Math.floor(k/3)],v=S.slots[k];return synergyLv()>0&&m!=null&&v&&TREES[v[0]].id===MUTTREE[MUTS[m].c]}
function mutBonus(g){const m=S.muts[g];if(m==null)return null;const M=MUTS[m];let v=M.v;const L=synergyLv();
 if(L>0){let n=0;for(let k=g*3;k<g*3+3;k++){const x=S.slots[k];if(x&&TREES[x[0]].id===MUTTREE[M.c])n++}v+=M.syn*L*(n+1)}return {stat:M.stat,pct:M.pct,v}}
const fmtStat=(pct,v)=>pct?'+'+Math.round(v*1000)/10+'%':'+'+Math.round(v);
function renderSlots(){const svg=document.getElementById('slots');
 let s=DEFS()+`<g stroke="#5a4a36" stroke-width="1.2"><line x1="399" y1="10" x2="399" y2="400"/><line x1="399" y1="502" x2="399" y2="890"/><line x1="20" y1="451" x2="150" y2="451"/><line x1="648" y1="451" x2="800" y2="451"/></g>
 <g class="mcentre" tabindex="0" role="button" aria-label="Open mutations${S.mact>=0?': active '+MUT[S.mact].name:''}" style="cursor:pointer"><title>Mutations</title>
 ${S.mact>=0?`<circle cx="399" cy="451" r="44" fill="${mColHex(S.mact)}" opacity=".45" filter="url(#glow)"/>`:''}
 ${S.mact>=0?`<circle cx="399" cy="451" r="44" fill="${mColHex(S.mact)}" opacity=".35" filter="url(#glow)"/><image href="${GA.cell[mCellKey(S.mact)]}" x="347" y="399" width="104" height="104"/><circle cx="399" cy="451" r="41" fill="none" stroke="#fff" stroke-width="2.5" opacity=".9"/><circle cx="399" cy="480" r="17" fill="#0b0b0b" stroke="${mColHex(S.mact)}" stroke-width="1.2"/><image href="${MUT[S.mact].icon}" x="384" y="465" width="30" height="30"/>`:`<image href="${GA.master}" x="351" y="403" width="96" height="96"/>`}
 <text x="399" y="518" text-anchor="middle" fill="#c9a86a" font-size="15" letter-spacing="1">${S.mact>=0?MUT[S.mact].name.toUpperCase():"MUTATIONS"}</text></g>`;
 SLOTPOS.forEach(([x,y],k)=>{const v=S.slots[k],q=k<12?1:.62,ok=k<12||S.mact>=0;
  if(v){const t=TREES[v[0]],m=slotMatch(k);
   s+=`<g class="node" tabindex="0" data-k="${k}" style="cursor:grab" aria-label="Slot ${k+1}: ${t.sk[v[1]].name}">${m?`<rect x="${x-54*q}" y="${y-54*q}" width="${108*q}" height="${108*q}" fill="${t.glow}" opacity=".5" filter="url(#glow)"/>`:''}${tile(t,v[0],v[1],x,y,S.lv[v[0]][v[1]],true,{h:48*q,slot:1})}</g>`}
  else if(!slotOpen(k))s+=`<g class="node locked" tabindex="0" role="button" data-k="${k}" aria-label="${lockMsg(k)}"><title>${lockMsg(k)}</title><rect x="${x-50*q}" y="${y-50*q}" width="${100*q}" height="${100*q}" fill="#0b0a09cc"/><rect class="frame" x="${x-48*q}" y="${y-48*q}" width="${96*q}" height="${96*q}" fill="none" stroke="#3d342a" stroke-width="1.5"/><image href="${LOCK.slot}" x="${x-24*q}" y="${y-24*q}" width="${48*q}" height="${48*q}" opacity=".8"/></g>`;
  else s+=`<g class="node" tabindex="0" data-k="${k}" aria-label="${k<12?"Empty slot "+(k+1):mSlotMsg()}"><title>${k<12?"":mSlotMsg()}</title><rect x="${x-50*q}" y="${y-50*q}" width="${100*q}" height="${100*q}" fill="#0b0a09cc"/><rect class="frame" x="${x-48*q}" y="${y-48*q}" width="${96*q}" height="${96*q}" fill="none" stroke="${k<12?"#6b5a42":ok?mColHex(S.mact):"#4a3a2a"}" stroke-width="1.5"/><image href="${ART.skill_slot_empty}" x="${x-26*q}" y="${y-26*q}" width="${52*q}" height="${52*q}" opacity=".85"/></g>`});
 DIAM.forEach(([x,y],g)=>{const m=S.muts[g],c=m!=null?MUTCOL[MUTS[m].c]:'#7a5a3a';if(!sockOpen(g)){s+=`<g class="mut locked" tabindex="0" role="button" data-g="${g}" aria-label="Mutagen socket locked: unlocks at ${MUT_UNLOCK[g]} skill points"><title>Unlocks at ${MUT_UNLOCK[g]} skill points</title><path d="M${x},${y-70} L${x+70},${y} L${x},${y+70} L${x-70},${y} Z" fill="#0b0a09cc" stroke="#4a3a2a" stroke-width="2"/><image href="${LOCK.sock}" x="${x-24}" y="${y-24}" width="48" height="48" opacity=".8"/></g>`;return}
  s+=`<g class="mut" tabindex="0" data-g="${g}" style="cursor:${m!=null?'grab':'default'}" aria-label="Mutagen slot ${g+1}${m!=null?': '+MUTS[m].name:''}"><path d="M${x},${y-72} L${x+72},${y} L${x},${y+72} L${x-72},${y} Z" fill="${m!=null?({red:'#3a1410',blue:'#10233d',green:'#123a10'})[MUTS[m].c]:'#0b0a09cc'}" stroke="#000" stroke-width="4"/><path class="frame" d="M${x},${y-70} L${x+70},${y} L${x},${y+70} L${x-70},${y} Z" fill="none" stroke="${c}" stroke-width="2"/>${m!=null?mutIcon(m,x,y,32):`<image href="${ART.mutagen_slot_empty}" x="${x-24}" y="${y-24}" width="48" height="48" opacity=".8"/>`}</g>`});
 svg.innerHTML=s;
 {const c=svg.querySelector('.mcentre');c.onclick=openMut;c.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openMut()}}}
 svg.querySelectorAll('g.node').forEach(g=>{const k=+g.dataset.k;
  g.onclick=()=>{if(noClick)return;if(!slotOpen(k)){slotNote(k);return}if(S.slots[k]){sel=[...S.slots[k]];tab=sel[0];render()}else if(sel&&S.lv[sel[0]][sel[1]]&&accepts(k,sel)){S.slots=S.slots.map(x=>x&&x[0]===sel[0]&&x[1]===sel[1]?null:x);S.slots[k]=[...sel];save()}else emptySlotNote(k)};
  g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();g.onclick()}};
  g.onpointerdown=e=>{if(e.button===0&&S.slots[k])press(e,{kind:'skill',v:[...S.slots[k]],from:k})};
  g.onpointerenter=e=>{if(S.slots[k])showTip(e,S.slots[k][0],S.slots[k][1])};g.onpointermove=moveTip;g.onpointerleave=hideTip});
 svg.querySelectorAll('g.mut').forEach(g=>{const k=+g.dataset.g;
  g.onclick=()=>{if(noClick)return;if(!sockOpen(k)){sockNote(k);return}if(S.muts[k]==null&&selMut!=null){S.muts[k]=selMut;save()}else if(S.muts[k]==null)notify('Open the Mutagens tab, pick a mutagen, then click a socket (or drag it onto one).')};
  g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();g.onclick()}};
  g.onpointerdown=e=>{if(e.button===0&&S.muts[k]!=null)press(e,{kind:'mut',v:S.muts[k],from:k})}})}


// ---- mutations ----
const MHEX={red:'#c0443a',blue:'#4f86e0',green:'#6cbc4a'},MDARK={red:'#5a120e',blue:'#10295a',green:'#173d10'};
const mCellKey=i=>MUT[i].cols.length>1?'gold':MUT[i].cols[0];
const mColHex=i=>MUT[i].cols.length>1?'#e6a640':MHEX[MUT[i].cols[0]];
function mRing(i,x,y,r,w=3){const cs=MUT[i].cols,C=2*Math.PI*r,seg=C/cs.length;return cs.map((c,k)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="none" stroke="${MHEX[c]}" stroke-width="${w}" stroke-dasharray="${seg} ${C-seg}" stroke-dashoffset="${-k*seg}" transform="rotate(-90 ${x} ${y})"/>`).join('')}
const lockMsg=k=>k<12?`Unlocks at ${SLOT_UNLOCK[k]} skill points`:`Unlocks after researching ${MSLOT_UNLOCK[k-12]} mutations`;
const mSlotMsg=()=>S.mact<0?'Mutation slot: activate a mutation first':`Mutation slot: accepts ${MUT[S.mact].cols.join(', ')} skills`;
let mutOpen=false,msel=-1;
function openMut(){mutOpen=true;hideTip();document.getElementById('mutov').hidden=false;document.body.style.overflow='hidden';document.getElementById('mhint').innerHTML=matchMedia('(pointer:coarse)').matches?'Tap a mutation for details · <b>Tap again</b> to research, then activate':'Hover a mutation for details · <b>Click</b> to research, then activate · <b>Right-click</b> to undo research';renderMut();document.getElementById('mclose').focus()}
function closeMut(){mutOpen=false;document.getElementById('mutov').hidden=true;document.body.style.overflow=''}
function mNeeds(){return MUT.reduce((a,m,i)=>{if(S.mres[i]){a.r+=m.r;a.b+=m.b;a.g+=m.g}return a},{r:0,b:0,g:0})}
function mState(i){if(S.mres[i])return S.mact===i?'Active':'Researched';return MUT[i].req.every(j=>S.mres[j])?'Available':'Locked'}
function mResearch(i){if(!mCanResearch(i)){renderMut();return}S.mres[i]=1;enforceLocks();save()}
let mNote='';
function mWhy(i){const m=MUT[i],miss=m.req.filter(j=>!S.mres[j]),need=m.sp-(budget()-spent());
 if(S.mres[i])mNote='';else if(miss.length)mNote=`Research ${miss.map(j=>MUT[j].name).join(' and ')} first.`;
 else if(need>0)mNote=`Not enough skill points: ${m.sp} needed, ${budget()-spent()} available. <button class="btn" onclick="addPts(${need})">Add ${need} bonus point${need>1?'s':''}</button>`}
function addPts(n){const b=document.getElementById('bonuspts');b.value=(+b.value||0)+n;mNote='';enforceLocks();save()}
function mUndo(i){if(!mCanUndo(i))return;S.mres[i]=0;if(S.mact===i)S.mact=-1;enforceLocks();save()}
function mActivate(i){if(!S.mres[i])return;S.mact=S.mact===i?-1:i;enforceLocks();save()}
function renderMut(){if(!mutOpen)return;const avail=budget()-spent(),n=mCount(),nd=mNeeds();
 {const a=document.getElementById('mlvl'),b=document.getElementById('mbonus');if(document.activeElement!==a)a.value=document.getElementById('lvl').value;if(document.activeElement!==b)b.value=document.getElementById('bonuspts').value}
 document.getElementById('mhead').innerHTML=`<span class="pav${avail<0?' neg':''}" ${avail<0?`title="Over budget by ${-avail}: raise Level or Bonus points, or undo something"`:''}>Points available <b>${avail}</b></span><span>Researched <b>${n}</b>/12</span><span title="Mutagens this build needs">Needs <i class="dot" style="background:${MHEX.red}"></i><b>${nd.r}</b> <i class="dot" style="background:${MHEX.blue}"></i><b>${nd.b}</b> <i class="dot" style="background:${MHEX.green}"></i><b>${nd.g}</b></span>`;
 const MC=[495,345],stage=MSLOT_UNLOCK.filter(t=>n>=t).length;
 let s=`<defs>
 <filter id="mg" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="9"/></filter>
 <filter id="mgr"><feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .8 0 0 0 0 .8 0 0 0 0 .8 0 0 0 .35 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
 <radialGradient id="cellg" cx="42%" cy="36%" r="70%"><stop offset="0" stop-color="#bdbdbd"/><stop offset=".45" stop-color="#6d6d6d"/><stop offset=".85" stop-color="#2c2c2c"/><stop offset="1" stop-color="#151515"/></radialGradient>
 ${Object.entries(MHEX).map(([c,x])=>`<radialGradient id="cell_${c}" cx="42%" cy="36%" r="70%"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".18" stop-color="${x}"/><stop offset=".75" stop-color="${MDARK[c]}"/><stop offset="1" stop-color="#0a0a0a"/></radialGradient>`).join('')}
 <radialGradient id="cell_gold" cx="42%" cy="36%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset=".2" stop-color="#e6c47a"/><stop offset=".8" stop-color="#5a4318"/><stop offset="1" stop-color="#0a0a0a"/></radialGradient>
 <radialGradient id="masterg" cx="45%" cy="40%" r="65%"><stop offset="0" stop-color="#e8eef2"/><stop offset=".5" stop-color="#8a98a4"/><stop offset=".9" stop-color="#2a3036"/><stop offset="1" stop-color="#101214"/></radialGradient>
 <radialGradient id="blob"><stop offset=".6" stop-color="#fff" stop-opacity="0"/><stop offset=".9" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
 </defs><rect x="0" y="-40" width="1000" height="600" fill="#101010"/><image href="${GA.mutbg}" x="0" y="-40" width="1000" height="533" preserveAspectRatio="xMidYMid slice"/>`;
 const link=(a,b,on,col)=>{const[x1,y1]=a,[x2,y2]=b,mx=(x1+x2)/2,my=(y1+y2)/2,dx=x2-x1,dy=y2-y1,L=Math.hypot(dx,dy)||1,nx=-dy/L*3,ny=dx/L*3;
  s+=`<path d="M${x1},${y1} Q${mx+nx},${my+ny} ${x2},${y2} Q${mx-nx},${my-ny} ${x1},${y1} Z" fill="${on?col:'#8c8c8c'}" opacity="${on?.95:.45}"/>${on?`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="5" opacity=".35" filter="url(#mg)"/>`:''}`};
 MUT.forEach((m,i)=>m.req.forEach(j=>link(MUT[j].pos,m.pos,S.mres[i]&&S.mres[j],mColHex(i))));
 [1,3,7].forEach(i=>link(MUT[i].pos,MC,S.mres[i],MHEX[MUT[i].cols[0]]));
 // master cell
 s+=`<g class="mn" tabindex="0" data-i="-2" aria-label="${MASTER.name}, stage ${stage} of 4">
  ${stage?`<circle cx="${MC[0]}" cy="${MC[1]}" r="66" fill="#6fb4ff" opacity="${.18+stage*.08}" filter="url(#mg)"/>`:''}
  <image href="${GA.master}" x="${MC[0]-60}" y="${MC[1]-60}" width="120" height="120" opacity="${stage?1:.8}"/>
  ${[0,1,2,3].map(k=>{const a=(-135+k*90)*Math.PI/180,r=52,on=k<stage;return`<circle cx="${MC[0]+r*Math.cos(a)}" cy="${MC[1]+r*Math.sin(a)}" r="5" fill="${on?'#e6c47a':'#222'}" stroke="#fff" stroke-width="1"/>`}).join('')}
  
  <circle cx="${MC[0]}" cy="${MC[1]+54}" r="15" fill="#0c0c0c" stroke="#777"/>
  ${stage?`<text x="${MC[0]}" y="${MC[1]+59}" text-anchor="middle" fill="#fff" font-size="15" font-weight="500">${["","I","II","III","IV"][stage]}</text>`:`<image href="${LOCK.slot}" x="${MC[0]-10}" y="${MC[1]+44}" width="20" height="20"/>`}</g>`;
 MUT.forEach((m,i)=>{const [x,y]=m.pos,St=mState(i),lk=St==='Locked',res=S.mres[i],r=28,act=S.mact===i;
  const fill=res?(m.cols.length>2?'url(#cell_gold)':`url(#cell_${m.cols[0]})`):'url(#cellg)';
  s+=`<g class="mn" tabindex="0" data-i="${i}" aria-label="${m.name}, ${St}">
  ${res?`<circle cx="${x}" cy="${y}" r="${act?54:40}" fill="${act?'#dff4ff':m.cols.length>1?'#e6a640':mColHex(i)}" opacity="${act?.75:.35}" filter="url(#mg)"/>`:''}${act?`<circle cx="${x}" cy="${y}" r="${r+6}" fill="none" stroke="#fff" stroke-width="2.5" opacity=".9"/>`:''}
  <circle cx="${x}" cy="${y}" r="${r+3}" fill="#000" opacity=".6"/>
  <image href="${res?GA.cell[mCellKey(i)]:GA.cell.grey}" x="${x-r*1.45}" y="${y-r*1.45}" width="${r*2.9}" height="${r*2.9}" opacity="${lk?.55:1}"/>
  ${m.cols.length>1?`<g opacity="${res?1:.55}">${mRing(i,x,y,r+1,2)}</g>`:''}
  ${mHover===i?`<image href="${GA.msel}" x="${x-r*1.5}" y="${y-r*1.5}" width="${r*3}" height="${r*3}"/>`:''}
  <circle cx="${x}" cy="${y+r-2}" r="17" fill="#0b0b0b" stroke="${res?mColHex(i):'#6a6a6a'}" stroke-width="1.2"/>
  <image href="${m.icon}" x="${x-15}" y="${y+r-17}" width="30" height="30" opacity="${lk?.45:1}"/>
  </g>`});
 const web=document.getElementById('mweb');web.innerHTML=s;
 if(!web.dataset.wired){web.dataset.wired=1;
  const nodeOf=e=>{const g=e.target.closest&&e.target.closest('.mn');return g?+g.dataset.i:null};
  let touchSel=null,lastType='mouse';
  web.addEventListener('pointerover',e=>{if(e.pointerType==='touch')return;const i=nodeOf(e);if(i!==null&&mHover!==i){mHover=i;mTip()}});
  web.addEventListener('pointerout',e=>{if(e.pointerType==='touch')return;const to=e.relatedTarget&&e.relatedTarget.closest&&e.relatedTarget.closest('.mn');if(!to&&!(e.relatedTarget&&e.relatedTarget.closest&&e.relatedTarget.closest('#mtip'))){mHover=null;mTip()}});
  web.addEventListener('click',e=>{const i=nodeOf(e);if(i===null){touchSel=null;mHover=null;mTip();return}
   if(lastType==='touch'){if(touchSel!==i){touchSel=i;mHover=i;mTip();return}}
   mHover=i;mAct(i)});
  web.addEventListener('pointerdown',e=>{lastType=e.pointerType});
  web.addEventListener('contextmenu',e=>{const i=nodeOf(e);if(i===null)return;e.preventDefault();mHover=i;if(i>=0)mUndoWhy(i)});
  web.addEventListener('focusin',e=>{const i=nodeOf(e);if(i!==null){mHover=i;mTip()}});
  web.addEventListener('keydown',e=>{const i=nodeOf(e);if(i===null)return;if(e.key==='Enter'||e.key===' '){e.preventDefault();mAct(i)}if((e.key==='Delete'||e.key==='Backspace')&&i>=0){e.preventDefault();mUndoWhy(i)}});}
 mTip();
 {const f=web.querySelector(`.mn[data-i="${mHover}"]`);if(f&&document.activeElement&&document.activeElement.closest&&document.activeElement.closest('#mweb'))f.focus()}
}
let mHover=null,mMsg={i:null,t:''},mLast=null;
const COLNAME={red:'Combat',blue:'Signs',green:'Alchemy'};
function mAction(i){if(i<0)return null;const m=MUT[i];if(S.mres[i])return S.mact===i?{k:'deact',label:'Deactivate Mutation',ok:true,cls:'red'}:{k:'act',label:'Activate Mutation',ok:true,cls:'green'};
 const miss=m.req.filter(j=>!S.mres[j]);if(miss.length)return{k:'lock',label:'Requires '+miss.map(j=>MUT[j].name).join(' and '),ok:false,cls:'red'};
 const av=budget()-spent();if(av<m.sp)return{k:'pts',label:`Needs ${m.sp} skill points (${av} available). Raise Level or Bonus points.`,ok:false,cls:'red'};
 return{k:'res',label:`Research (${m.sp} skill points)`,ok:true,cls:'green'}}
function mFlash(){const els=[document.getElementById('mbonus'),document.querySelector('#mhead .pav')];els.forEach(e=>{if(e){e.classList.remove('flash');void e.offsetWidth;e.classList.add('flash')}})}
function mAct(i){if(i<0){mTip();return}const a=mAction(i);mMsg={i:null,t:''};
 if(a.k==='res')mResearch(i);else if(a.k==='act'||a.k==='deact')mActivate(i);
 else{mMsg={i,t:a.k==='pts'?'Not enough skill points. Raise Level or Bonus points at the top of this screen.':''};renderMut();if(a.k==='pts')mFlash()}}
function mUndoWhy(i){if(!S.mres[i]){mTip();return}if(!mCanUndo(i)){const dep=MUT.map((m,j)=>S.mres[j]&&m.req.includes(i)?m.name:null).filter(Boolean);mMsg={i,t:'Undo '+dep.join(' and ')+' first.'};mTip();return}mMsg={i:null,t:''};mUndo(i)}
function mUndoBtn(){const u=document.getElementById('mundo');if(!u)return;const ok=mLast!==null&&mLast>=0&&S.mres[mLast];u.disabled=!ok;u.textContent=ok?'Undo research: '+MUT[mLast].name:'Undo research'}
function mTip(){if(mHover!==null&&mHover>=0)mLast=mHover;mUndoBtn();const tip=document.getElementById('mtip'),web=document.getElementById('mweb');if(!tip||!web)return;const i=mHover;
 if(i===null||!mutOpen){tip.hidden=true;return}
 const g=web.querySelector(`.mn[data-i="${i}"]`);if(!g){tip.hidden=true;return}
 let html;
 if(i===-2){const n=mCount(),st=MSLOT_UNLOCK.filter(t=>n>=t).length;html=`<b class="tn">${MASTER.name.toUpperCase()}</b><p>${MASTER.desc}</p><div class="tu">STAGE ${st} OF 4</div><div class="tc">${MSLOT_UNLOCK.map((t,k)=>`<span class="${n>=t?'on':''}">Slot ${k+1}: ${t} researched</span>`).join('')}</div>`}
 else{const m=MUT[i],a=mAction(i);
  html=`<b class="tn">${m.name.toUpperCase()}</b><p>${m.desc}</p><div class="tu">ALLOWS USE OF:</div><div class="tc">${['red','blue','green'].map(c=>`<span class="${m.cols.includes(c)?'on '+c:''}">${COLNAME[c]}</span>`).join('')}</div>
  ${S.mres[i]?'':`<div class="tcost">Cost: ${m.sp} skill points${[['r','red'],['b','blue'],['g','green']].filter(([k])=>m[k]).map(([k,c])=>` · <i class="dot" style="background:${MHEX[c]}"></i>${m[k]} ${c}`).join('')}</div>`}
  ${mMsg.i===i&&mMsg.t?`<div class="tbar red">${mMsg.t}</div>`:''}
  <div class="tbar ${a.cls}"><kbd>${a.ok?'Click':'—'}</kbd>${a.label}</div>${S.mres[i]?'<div class="tr">Right-click: undo research</div>':''}`}
 tip.innerHTML=html;tip.hidden=false;
 const wr=document.querySelector('.mweb').getBoundingClientRect(),r=g.getBoundingClientRect(),tw=tip.offsetWidth,th=tip.offsetHeight;
 let x=r.right-wr.left+8,y=r.top-wr.top-8;if(x+tw>wr.width-6)x=r.left-wr.left-tw-8;if(x<6)x=6;if(y+th>wr.height-6)y=wr.height-th-6;if(y<6)y=6;
 tip.style.left=x+'px';tip.style.top=y+'px'}
document.addEventListener('keydown',e=>{if(mutOpen&&e.key==='Escape')closeMut()});

// ---- hover tooltip ----
const fmtDesc=d=>d.replace(/\$[A-Za-z]+\$/g,'<span class="num">?</span>');
function showTip(e,ti,i){if(drag)return;const el=document.getElementById('tip');
 el.innerHTML=tipHTML(ti,i);el.style.display='block';moveTip(e)}
function moveTip(e){const el=document.getElementById('tip');if(el.style.display!=='block')return;const w=el.offsetWidth,h=el.offsetHeight;
 let x=e.clientX+18,y=e.clientY+18;if(x+w>innerWidth-8)x=e.clientX-w-18;if(y+h>innerHeight-8)y=innerHeight-h-8;el.style.left=x+'px';el.style.top=y+'px'}
function hideTip(){document.getElementById('tip').style.display='none'}

// ---- drag & drop (pointer events: mouse + touch) ----
let drag=null,noClick=false,hot=null;
function press(e,info){hideTip();drag={...info,sx:e.clientX,sy:e.clientY,started:false}}
function ghostSVG(d){if(d.kind==='skill'){const[ti,i]=d.v,t=TREES[ti];return`<svg viewBox="-50 -50 100 100" width="72" height="72">${DEFS(t)}${tile(t,ti,i,0,0,S.lv[ti][i],true,{h:44})}</svg>`}
 return`<svg viewBox="-50 -50 100 100" width="72" height="72">${DEFS()}${mutIcon(d.v,0,0,34)}</svg>`}
function targetAt(x,y,kind){const el=document.elementFromPoint(x,y);if(!el)return null;
 return el.closest(kind==='skill'?'#slots g.node[data-k]:not(.locked)':'#slots g.mut[data-g]:not(.locked)')}
function setHot(g){if(hot===g)return;if(hot){const f=hot.querySelector('.frame');f&&f.setAttribute('stroke',f.dataset.o);}hot=g;if(g){const f=g.querySelector('.frame');if(f){f.dataset.o=f.getAttribute('stroke');f.setAttribute('stroke','#e8d3a4')}}}
document.addEventListener('pointermove',e=>{if(!drag)return;
 if(!drag.started){if(Math.hypot(e.clientX-drag.sx,e.clientY-drag.sy)<7)return;drag.started=true;
  const gh=document.createElement('div');gh.className='ghost';gh.innerHTML=ghostSVG(drag);document.body.appendChild(gh);drag.gh=gh;document.body.classList.add('dragging')}
 drag.gh.style.left=e.clientX+'px';drag.gh.style.top=e.clientY+'px';setHot(targetAt(e.clientX,e.clientY,drag.kind))});
function endDrag(e){if(!drag)return;const d=drag;drag=null;if(!d.started)return;
 d.gh.remove();document.body.classList.remove('dragging');setHot(null);noClick=true;setTimeout(()=>noClick=false,0);
 const tg=e&&targetAt(e.clientX,e.clientY,d.kind);
 if(d.kind==='skill'){if(tg&&!accepts(+tg.dataset.k,d.v)){}else if(tg){const k=+tg.dataset.k;if(d.from!=null&&S.slots[k]&&!accepts(d.from,S.slots[k])){save();return}if(d.from!=null){const tmp=S.slots[k];S.slots[k]=S.slots[d.from];S.slots[d.from]=tmp}else{S.slots=S.slots.map(x=>x&&x[0]===d.v[0]&&x[1]===d.v[1]?null:x);S.slots[k]=d.v}}else if(d.from!=null)S.slots[d.from]=null}
 else{if(tg){const g=+tg.dataset.g;if(d.from!=null){const tmp=S.muts[g];S.muts[g]=S.muts[d.from];S.muts[d.from]=tmp}else S.muts[g]=d.v}else if(d.from!=null)S.muts[d.from]=null}
 save()}
document.addEventListener('pointerup',endDrag);document.addEventListener('pointercancel',()=>{if(drag&&drag.gh){drag.gh.remove();document.body.classList.remove('dragging');setHot(null)}drag=null});

function renderBonus(){const tot={};S.muts.forEach((m,g)=>{const b=mutBonus(g);if(!b)return;const k=b.stat;tot[k]=tot[k]||{pct:b.pct,v:0,c:MUTS[m].c};tot[k].v+=b.v});
 document.getElementById('bonus').innerHTML=Object.entries(tot).map(([k,t])=>`<div class="${t.c}">+ ${STATN[k]} <span style="margin-left:40px">${fmtStat(t.pct,t.v).replace('+','+')}</span></div>`).join('')}

function renderInfo(){const el=document.getElementById('info');
 if(tab===4&&selMut!=null){const m=MUTS[selMut];el.innerHTML=`<h2>${m.name}</h2><p>${STATN[m.stat]} ${fmtStat(m.pct,m.v)}. ${m.special?'A special mutagen: it gives the same bonus as the Lesser '+m.c+' mutagen. ':''}With the Synergy skill, matching-colour skills in the same group add more.</p>`;return}
 if(!sel){el.innerHTML=`<h2>No skill selected</h2><p>Select a skill in a tree to see its details and equip it. Hover any skill for its description.</p>`;return}
 const[ti,i]=sel,t=TREES[ti],L=S.lv[ti][i],av=available(ti,i),eq=S.slots.some(x=>x&&x[0]===ti&&x[1]===i);
 const K=t.sk[i],req=K.req.map(p=>t.sk[p].name);el.innerHTML=`<h2>${K.name}${t.core&&t.core.includes(i)?' (school)':''}${K.rew?' <small style="color:var(--gold);font-size:16px">Reworked</small>':''}</h2><p>Level ${L} of ${K.max}.${req.length?' Requires '+(K.alt&&req.length>1?'one of: ':'')+req.join(', ')+'.':' No prerequisites.'}${K.pts?' Tree investment listed: '+K.pts+' points.':''}</p><p>Full description loads from the game's text file next.</p>
 <div class="actions"><button class="btn" id="aAdd" ${L<K.max&&av&&spent()<budget()?'':'disabled'}>Add point</button><button class="btn" id="aRem" ${L&&canRemove(ti,i)?'':'disabled'}>Remove point</button><button class="btn" id="aEq" ${L&&!eq?'':'disabled'}>${eq?'Equipped':'Equip'}</button></div>`;
 document.getElementById('aAdd').onclick=()=>add(ti,i);document.getElementById('aRem').onclick=()=>rem(ti,i);document.getElementById('aEq').onclick=()=>equip(ti,i)}

function render(){document.getElementById('total').textContent=budget();document.getElementById('avail').textContent=budget()-spent();{const v=budget()-spent(),e=document.getElementById('avail2');e.textContent=v;e.style.color=v<0?'#ff6a5a':'';e.title=v<0?'Over budget: raise Level or Bonus points, or remove something':''}renderTabs();renderTree();renderSlots();renderBonus();renderInfo();renderMut();
 document.getElementById('link').value=(CFG.shareBase||location.href.split('#')[0])+'#'+enc()}

S=dec(location.hash.slice(1))||blank();enforceLocks();
function pointsChanged(){enforceLocks();save()}
// ---- friendly notices (these replace silent failures) ----
let toastT=null;
function notify(msg,go){const t=document.getElementById('toast');document.getElementById('toastMsg').textContent=msg;document.getElementById('toastGo').hidden=!go;t.hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>{t.hidden=true},go?9000:6500)}
function flashPoints(){['lvl','bonuspts'].forEach(id=>{const e=document.getElementById(id);e.classList.remove('flash');void e.offsetWidth;e.classList.add('flash')})}
document.getElementById('toastGo').onclick=()=>{const e=document.getElementById('lvl');e.scrollIntoView({block:'center',behavior:'smooth'});e.focus();flashPoints()};
function slotNote(k){if(k<12){notify('Slot '+(k+1)+' unlocks at '+SLOT_UNLOCK[k]+' skill points, and you have '+budget()+' in total. Raise Level or Bonus points (from Places of Power) to open it.',true);flashPoints()}
 else notify('Mutation slot '+(k-11)+' unlocks after researching '+MSLOT_UNLOCK[k-12]+' mutations (you have '+mCount()+'). Open Mutations to research them.')}
function sockNote(g){notify('Mutagen socket '+(g+1)+' unlocks at '+MUT_UNLOCK[g]+' skill points, and you have '+budget()+' in total. Raise Level or Bonus points (from Places of Power) to open it.',true);flashPoints()}
function emptySlotNote(k){
 if(k>=12&&S.mact<0){notify(mSlotMsg());return}
 if(!sel||!S.lv[sel[0]][sel[1]]){notify('Select a skill that has points in it, then click a slot (or drag the skill onto it).');return}
 if(!accepts(k,sel))notify('While '+MUT[S.mact].name+' is active, this slot accepts only '+MUT[S.mact].cols.map(c=>({red:'Combat',blue:'Signs',green:'Alchemy'})[c]).join(', ')+' skills.')}
function tryAdd(ti,i){const K=TREES[ti].sk[i];
 if(S.lv[ti][i]>=K.max){notify(K.name+' is already at its highest level.');return}
 if(!available(ti,i)){notify('Locked: needs '+K.req.map(p=>TREES[ti].sk[p].name).join(K.alt?' or ':' and ')+' first.');return}
 if(spent()>=budget()){notify('No skill points left. Raise Level or Bonus points (from Places of Power) to spend more.',true);flashPoints();return}
 add(ti,i)}
document.getElementById('lvl').oninput=document.getElementById('bonuspts').oninput=pointsChanged;
document.getElementById('mlvl').oninput=e=>{document.getElementById('lvl').value=e.target.value;pointsChanged()};
document.getElementById('mbonus').oninput=e=>{document.getElementById('bonuspts').value=e.target.value;pointsChanged()};
document.getElementById('mutbtn').onclick=openMut;document.getElementById('mclose').onclick=closeMut;document.getElementById('mundo').onclick=()=>{if(mLast!==null&&mLast>=0){mHover=mLast;mUndoWhy(mLast)}};document.getElementById('mutov').onclick=e=>{if(e.target.id==='mutov')closeMut()};
document.getElementById('reset').onclick=()=>{S=blank();sel=null;save()};
document.getElementById('copy').onclick=async()=>{const b=document.getElementById('copy');try{await navigator.clipboard.writeText(document.getElementById('link').value);b.textContent='Link copied'}catch(e){const l=document.getElementById('link');l.select();let ok=false;try{ok=document.execCommand('copy')}catch(_){}b.textContent=ok?'Link copied':'Press Ctrl+C'}setTimeout(()=>b.textContent='Copy link',1500)};
{const row=document.getElementById('importRow');
 if(CFG.mode==='offline'){row.hidden=false;
  const msg=t=>{document.getElementById('impmsg').textContent=t};
  const open=()=>{const el=document.getElementById('imp'),m=String(el.value||'').match(/(?:#|^|\/)(v1\.[A-Za-z0-9_.\-]+)\s*$/);
   if(!m){msg('That does not look like a build link.');return}
   const s=dec(m[1]);if(!s){msg('That build link could not be read.');return}
   S=s;sel=null;selMut=null;enforceLocks();save();el.value='';msg('Build opened.')};
  document.getElementById('impbtn').onclick=open;
  document.getElementById('imp').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();open()}}}}
{const sr=document.getElementById('shareRow');if(sr&&CFG.share===false)sr.hidden=true}
{const ft=document.querySelector('footer'),su=CFG.siteUrl||CFG.shareBase;if(ft){const link=(su&&/^https?:\/\//.test(su))?' · <a href="'+encodeURI(su)+'" style="color:inherit">Latest version online</a>':'';ft.insertAdjacentHTML('beforeend',' · '+(CFG.mode==='offline'?'Offline '+APP_VERSION+link:APP_VERSION))}}
window.onhashchange=()=>{const s=dec(location.hash.slice(1));if(s){S=s;enforceLocks();render();if(typeof eqRefresh==='function')eqRefresh()}};
save();
