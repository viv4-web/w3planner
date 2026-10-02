// ---- Player Stats (v32): the game's Statistics screen, opened from the top bar (button, key C) over whatever tab is open. Every value is worked out from the planner's state the way the game's scripts do, or shows "—" ("not computed yet"): never a guess.
// Sources: the screen itself is CharacterStatsPopup.ws (GetPlayerStatsGFxData, AddCharacterStat*, 50-730), the offence numbers playerWitcher.ws GetOffenseStatsList (8750-9010), the crossbow GetEquippedCrossbowDamage (CharacterStatsPopup.ws 880-934),
// armour GetTotalArmor (playerWitcher.ws 5842), mutagen abilities PlayerAbilityManager.ws 851-1020, the regeneration lines AddCharacterStat (CharacterStatsPopup.ws 290-330) and the Lvl / ConGeralt / survival_vitality abilities (data/STATS.json, tools/make_stats.py).
// Weapons only count while held (nothing is held on this screen). A stat an item gives within a range is shown as "min–max" (never a midpoint). What an imported save adds that the link cannot hold (active effects such as a whetstone or a Place of Power,
// items with rolled abilities, play time) is kept in memory in PS.imp (never in the link).
const STATS=/*@data:STATS*/;
const PS={open:false,sel:0,play:null,imp:{effects:[],rolled:{}},opener:null};
const PS_ROWS=[['silver','red','DPS - Silver sword'],['steel','red','DPS - Steel sword'],['armor','red','Armor'],['crossbow','red','Crossbow'],['vitality','green','Vitality'],['toxicity','green','Toxicity'],['sign','blue','Sign intensity'],['stamina','blue','Stamina'],['additional','orange','Additional']];
const PS_ICON={silver:'<path d="M12 3 L14 4 L14 16 L10 16 L10 4 Z M7 16 H17 M12 16 V21"/>',steel:'<path d="M12 2 L14 4 L14 15 L10 15 L10 4 Z M6 15 H18 M12 15 V21"/>',armor:'<path d="M12 3 L20 6 V12 C20 17 16 20 12 21 C8 20 4 17 4 12 V6 Z"/>',crossbow:'<path d="M3 8 C9 4 15 4 21 8 M12 6 V20 M8 12 H16"/>',vitality:'<path d="M12 20 C4 14 3 9 6.5 6.5 C9 5 11 6.5 12 8 C13 6.5 15 5 17.5 6.5 C21 9 20 14 12 20 Z"/>',toxicity:'<path d="M9 3 H15 M10 3 V9 L5 19 C4.5 20.5 5.5 21 7 21 H17 C18.5 21 19.5 20.5 19 19 L14 9 V3"/>',sign:'<path d="M12 3 L20 18 H4 Z M12 8 L16 16 H8 Z"/>',stamina:'<path d="M13 2 L5 13 H11 L10 22 L19 10 H13 Z"/>',additional:'<circle cx="6" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18" cy="12" r="1.6"/>'};
const psL=k=>STATS.labels[k];
const psRound=Math.round;

// an equipped item's numbers for a stat name: v = the lowest, hi = the highest (the same unless the item gives the stat within a range, XML min and max)
function psItem(it,name){if(!it)return{v:0,hi:0};let v=0,hi=0;[...(it.base||[]),...(it.bonuses||[])].forEach(b=>{if(b.stat===name){v+=b.min;hi+=b.max!=null?b.max:b.min}});return{v,hi}}
const psSum=(it,names)=>names.reduce((a,n)=>{const x=psItem(it,n);return{v:a.v+x.v,hi:a.hi+x.hi}},{v:0,hi:0});
// a mutagen's real stat (PlayerAbilityManager.ws OnSkillMutagenEquipped, MutagensSyngergyBonusUpdateSingle): its ability's number plus the synergy ability times Synergy level x (matching skills in its group + 1).
// The extra "x" abilities the Character screen adds while it builds its panel (characterMenu.ws 1337-1420) are not part of a saved game's stats, so a mutagen with a matching skill in its group makes the stat unknown.
function psMut(stat){let sum=0,unknown=false;S.muts.forEach((m,g)=>{if(m==null)return;const M=MUTS[m];if(M.stat!==stat)return;let n=0;for(let k=g*3;k<g*3+3;k++)if(slotMatch(k))n++;if(n>0)unknown=true;sum+=M.v+M.syn*synergyLv()*(n+1)});return{sum,unknown}}

// one pass of the numbers; hi=false takes every ranged item stat at its lowest, hi=true at its highest
function psPass(hi){const d=eqData();if(!d||!EQ.meta||!CN.data)return null;
 const L=lvl(),tbl=STATS.lvl[S.rs]||STATS.lvl.ng,con=STATS.con[S.rs]||STATS.con.ng,lv=tbl.slice(0,Math.max(0,L-1));
 const g={};EQ_SLOTS.forEach((s,i)=>g[s]=eqCur(i));
 const I=(it,n)=>{const x=psItem(it,n);return hi?x.hi:x.v},IS=(it,ns)=>{const x=psSum(it,ns);return hi?x.hi:x.v};
 const rolled=s=>!!(g[s]&&PS.imp.rolled[s]===g[s].id);   // an imported item with rolled abilities in the save: their values are not read, so what it gives is unknown
 const worn=['chest','gloves','trousers','boots','mask'].map(s=>g[s]).filter(Boolean),low=EQ_SLOTS.some(s=>g[s]&&eqLow(g[s]));
 const eq=[];S.slots.forEach(v=>{if(v){const t=TREES[v[0]],s=t.sk[v[1]],l=S.lv[v[0]][v[1]];if(l>0)eq.push({id:s.id,l})}});
 const touch=(re,skip)=>eq.some(e=>e.id!==skip&&(STATS.touch[e.id]||[]).some(a=>re.test(a)));
 const effs=(PS.imp.effects||[]).map(e=>({e,x:STATS.eff[e.ability]})).filter(o=>o.x);
 const effTouch=re=>effs.some(o=>o.x.touch.some(a=>re.test(a))),effNum=(k,t)=>effs.reduce((a,o)=>a+(o.x[k]?o.x[k][t]:0),0);
 const mutOn=S.mact>=0&&!!S.mres[S.mact];
 const setTxt=eqSets().flatMap(x=>x.st.bonuses.filter(b=>x.counted>=b.pieces).map(b=>b.text)).join(' ').toLowerCase(),setHit=re=>re.test(setTxt);
 const wornHas=names=>worn.some(it=>psSum(it,names).hi!==0||psSum(it,names).v!==0)||worn.some(it=>!!PS.imp.rolled[EQ_SLOTS.find(s=>g[s]===it)]&&PS.imp.rolled[EQ_SLOTS.find(s=>g[s]===it)]===it.id);
 const out={rows:{},det:{}},U=null;
 // ---- resources
 const mv=psMut('vitality'),surv=eq.filter(e=>STATS.surv.includes(e.id)).reduce((a,e)=>a+e.l,0);
 const vitUnk=mutOn||mv.unknown||touch(/^vitality$/)||effTouch(/^vitality$/)||wornHas(['vitality'])||setHit(/vitality/)||L>tbl.length+1&&S.rs==='ng';
 const vit=vitUnk?U:psRound((con.vitality+lv.reduce((a,r)=>a+r[0],0)+mv.sum)*(1+STATS.surv_mult*surv));
 const stam=touch(/^stamina$/)||effTouch(/^stamina$/)||wornHas(['stamina'])||setHit(/stamina/)?U:psRound(con.stamina);
 const tox=touch(/^toxicity$/)||effTouch(/^toxicity$/)||wornHas(['toxicity'])||setHit(/toxicity/)?U:psRound(con.toxicity);
 out.rows.vitality={v:vit,max:vit};out.rows.stamina={v:stam,max:stam};out.rows.toxicity={v:tox==null?U:0,max:tox};
 // ---- armour: the four armour pieces' Armor (GetItemArmorTotal), plus the player's own armor ability (Melt Armor's armor is the target's: Armor 127 against the game with it equipped)
 const ARM=['chest','gloves','trousers','boots'],armUnk=low||ARM.some(rolled)||touch(/^armor$/,'magic_s8')||effTouch(/^armor$/)||setHit(/armor/);
 out.rows.armor={v:armUnk?U:psRound(ARM.reduce((a,s)=>a+I(g[s],'armor'),0))};
 // ---- offence (GetOffenseStatsList)
 const ma=psMut('attack_power'),ap={mult:1+ma.sum+effNum('attack_power','mult'),add:lv.reduce((a,r)=>a+r[1],0)+effNum('attack_power','add')};
 const offUnk=low||mutOn||ma.unknown||touch(/^(attack_power|critical_hit)/)||effTouch(/^critical_hit/)||wornHas(['attack_power','critical_hit_chance','critical_hit_damage_bonus'])||setHit(/attack|damage|critical|sword/);
 const sword=(k,names)=>{const it=g[k];if(!it)return{none:true};if(offUnk||rolled(k))return null;
  if(!(IS(it,names)>0))return null;   // an item whose damage is not in the data (generated by the game from its level) has no number here
  const dmg=IS(it,names),e=IS(it,['FireDamage','FrostDamage']),crit=con.crit_chance+I(it,'critical_hit_chance'),cdm=con.crit_damage+I(it,'critical_hit_damage_bonus');
  const fast=dmg*ap.mult+ap.add+e,fastC=dmg*(ap.mult+cdm)+ap.add+e,strong=fast*1.833,strongC=fastC*1.833,dps=(a,c,t)=>(a*(100-crit*100)+c*crit*100)/100/t;
  return{fast,fastC,strong,strongC,crit:crit*100,fdps:dps(fast,fastC,0.6),sdps:dps(strong,strongC,1.1)}};
 const swords={silver:sword('silver',['SilverDamage']),steel:sword('steel',['SlashingDamage','PiercingDamage','BludgeoningDamage'])};
 const chance=(it,n)=>it?psRound(I(it,n)*100)+' %':'0 %';
 ['silver','steel'].forEach(k=>{const s=swords[k],it=g[k],none=s&&s.none,unk=s===null,nm=k;
  out.rows[k]={v:unk?U:none?0:psRound((s.fdps+s.sdps)/2)};
  const f=x=>unk?U:none?0:psRound(x),c=x=>unk?U:none?'0 %':psRound(x)+' %';
  out.det[k]=[[[f(s&&s.fast),psL('panel_common_statistics_tooltip_'+nm+'_fast_dps')],[c(s&&s.crit),psL('panel_common_statistics_tooltip_'+nm+'_fast_crit_chance')],[f(s&&s.fastC),psL('panel_common_statistics_tooltip_'+nm+'_fast_crit_dmg')]],
   [[f(s&&s.strong),psL('panel_common_statistics_tooltip_'+nm+'_strong_dps')],[c(s&&s.crit),psL('panel_common_statistics_tooltip_'+nm+'_strong_crit_chance')],[f(s&&s.strongC),psL('panel_common_statistics_tooltip_'+nm+'_strong_crit_dmg')]],
   ['poinsonchance','bleedingchance','burningchance','confusionchance','freezingchance','staggerchance'].map(n=>[rolled(k)?U:chance(it,'desc_'+n+'_mult'),psL('attribute_name_desc_'+n+'_mult')])]});
 // ---- crossbow (GetEquippedCrossbowDamage): ((bolt piercing + 0) x mult + add + (bolt silver + 0) x mult + add) / 2, mult = the crossbow's attack_power + the player's
 const xb=g.crossbow,bolt=g.bolts,bp=I(bolt,'PiercingDamage'),bs=I(bolt,'SilverDamage'),bb=I(bolt,'BludgeoningDamage'),bf=I(bolt,'FireDamage'),xa=I(xb,'attack_power');
 const xbUnk=offUnk||rolled('crossbow')||rolled('bolts')||touch(/^attack_power/);
 let steelD,silverD,steelKey='attribute_name_piercingdamage';if(!bolt){steelD=5;silverD=4}else if(bf>0){steelD=silverD=bf;steelKey='attribute_name_firedamage'}else{silverD=bs;if(bp>0)steelD=bp;else{steelD=bb;steelKey='attribute_name_bludgeoningdamage'}}
 const xm=xa+ap.mult;out.rows.crossbow={v:!xb?0:xbUnk?U:psRound((steelD*xm+ap.add+silverD*xm+ap.add)/2)};
 out.det.crossbow=[[[xbUnk&&!!xb?U:psRound(con.crit_chance*100)+' %',psL('panel_common_statistics_tooltip_crossbow_crit_chance')],[rolled('bolts')?U:psRound(steelD),psL(steelKey)],[rolled('bolts')?U:psRound(silverD),psL('attribute_name_silverdamage')]]];
 // ---- resistances, regeneration, additional
 const res=n=>ARM.some(rolled)||low?U:psRound(ARM.reduce((q,s)=>q+I(g[s],n),0)*100)+' %';
 out.det.armor=[[[res('slashing_resistance_perc'),psL('slashing_resistance_perc')],[res('piercing_resistance_perc'),psL('attribute_name_piercing_resistance_perc')],[res('bludgeoning_resistance_perc'),psL('bludgeoning_resistance_perc')],[res('rending_resistance_perc'),psL('attribute_name_rending_resistance_perc')],[res('elemental_resistance_perc'),psL('attribute_name_elemental_resistance_perc')]],
  [['poison_resistance_perc',con.poison_resist],['bleeding_resistance_perc',con.bleeding_resist],['burning_resistance_perc',0]].map(([n,b])=>[ARM.some(rolled)||low?U:psRound((b+ARM.reduce((q,s)=>q+I(g[s],n),0))*100)+' %',psL('attribute_name_'+n)])];
 // Vitality regeneration: GetAttributeValue(vitalityRegen / vitalityCombatRegen) = ConGeralt add 1 (mult 0), shown "N/s" (CharacterStatsPopup.ws 297-302); Stamina out of combat = max Stamina x staminaOutOfCombatRegen mult (1) + add (0) (312-317)
 const rg=re=>touch(re)||effTouch(re)||wornHas(['vitalityRegen','vitalityCombatRegen','staminaOutOfCombatRegen'])||mutOn;
 const vr=rg(/^vitalityRegen$/)?U:psRound(con.vit_regen)+'/s',vc=rg(/^vitalityCombatRegen$/)?U:psRound(con.vit_combat_regen)+'/s',so=stam==null||rg(/^staminaOutOfCombatRegen$/)?U:psRound(stam*con.stamina_ooc_mult)+'/s';
 out.det.vitality=[[[vr,psL('panel_common_statistics_tooltip_outofcombat_regen')],[vc,psL('panel_common_statistics_tooltip_incombat_regen')]]];
 out.det.toxicity=[[[tox==null?U:0,psL('toxicity_offset')],[tox==null?U:0,psL('toxicity')]]];
 out.rows.sign={v:U};out.det.sign=[[[U,psL('Aard')]],[[U,psL('attribute_name_knockdown')],[U,psL('attribute_name_forcedamage')]],[[U,psL('Igni')]],[[U,psL('attribute_name_firedamage')],[U,psL('effect_burning')]],[[U,psL('Quen')]],[[U,psL('physical_resistance')]],[[U,psL('Yrden')]],[[U,psL('SlowdownEffect')],[U,psL('ShockDamage')],[U,psL('duration')]],[[U,psL('Axii')]],[[U,psL('duration')]]];
 out.det.stamina=[[[so,psL('attribute_name_staminaregen_out_of_combat')],[U,psL('attribute_name_staminaregen')]]];   // in combat: the game shows 20/s where the abilities add up to 18; not matched, so not shown
 const kill=['steel','silver'].map(s=>rolled(s)?null:I(g[s],'instant_kill_chance_mult')),kd=kill.includes(null)||touch(/^instant_kill/)?U:psRound(kill.reduce((q,x)=>q+x,0)*100)+' %';
 const wp=n=>wornHas([n])&&worn.some(it=>PS.imp.rolled[EQ_SLOTS.find(s=>g[s]===it)]===it.id)?U:psRound(worn.reduce((q,it)=>q+I(it,n),0)*100)+' %';
 out.rows.additional={v:''};out.det.additional=[[[wp('bonus_herb_chance'),psL('bonus_herb_chance')],[kd,psL('instant_kill_chance')],[wp('human_exp_bonus_when_fatal'),psL('human_exp_bonus_when_fatal')],[wp('nonhuman_exp_bonus_when_fatal'),psL('nonhuman_exp_bonus_when_fatal')]]];
 return out}

// the lowest and the highest pass, merged: equal numbers stay one number, different ones become "min–max" (a percentage "10–12 %"), never a midpoint
function psMerge(a,b){if(a==null||b==null)return null;if(a===b)return a;const num=x=>typeof x==='string'?parseFloat(x):x,sx=x=>typeof x==='string'?x.replace(/^-?[\d.]+/,''):'';if(isNaN(num(a))||isNaN(num(b)))return null;return typeof a==='string'?num(a)+'–'+num(b)+sx(b):a+'–'+b}
function psCalc(){const a=psPass(false);if(!a)return null;const b=psPass(true),o={rows:{},det:{}};
 Object.keys(a.rows).forEach(k=>{const r=a.rows[k],q=b.rows[k];o.rows[k]={v:psMerge(r.v,q.v),max:r.max==null?r.max:psMerge(r.max,q.max)};if(r.v===''){o.rows[k].v=''}});
 Object.keys(a.det).forEach(k=>{o.det[k]=a.det[k].map((blk,i)=>blk.map(([v,l],j)=>[psMerge(v,b.det[k][i][j][0]),l]))});return o}

// ---- the screen ----
const psEl=id=>document.getElementById(id);
const psEsc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const psVal=v=>v==null?`<b class="psu" title="not computed yet" aria-label="not computed yet">—</b>`:`<b>${psEsc(String(v))}</b>`;
function psEffects(){const e=(PS.imp.effects||[]).filter(x=>x.ability&&STATS.eff_names[x.ability]);if(!e.length)return'';
 return'Active effects in the imported save: '+e.map(x=>{const mod=STATS.eff[x.ability],bits=[];if(x.timeLeft>0)bits.push(Math.max(1,psRound(x.timeLeft/60))+' min left');
  if(mod&&mod.attack_power&&mod.attack_power.mult)bits.push('+'+psRound(mod.attack_power.mult*100)+'% attack power, included');else if(mod&&mod.touch.some(a=>/^spell_power/.test(a)))bits.push('Sign intensity, not computed');
  return psEsc(STATS.eff_names[x.ability])+(bits.length?' ('+bits.join(', ')+')':'')}).join('; ')+'.'}
function psRender(){const R=psCalc(),list=psEl('psrows'),panel=psEl('pspanel');if(!list)return;
 if(panel.parentNode===list)psEl('pswrap').appendChild(panel);   // the phone layout keeps the detail inside the list: take it out before the rows are drawn again
 list.innerHTML=PS_ROWS.map(([id,col,name],i)=>{const r=R?R.rows[id]:{v:null},sel=i===PS.sel,big=id==='sign'?psVal(r.v):id==='additional'?'':psVal(r.v),
  sub=id==='vitality'||id==='stamina'||id==='toxicity'?`<small>${r.max==null?'—':psEsc(String(r.max))}</small>`:'';
  return`<button type="button" role="tab" class="psrow ${col}${sel?' sel':''}" id="pstab${i}" aria-selected="${sel}" aria-controls="pspanel" tabindex="${sel?0:-1}" data-i="${i}"><svg class="psicon" viewBox="0 0 24 24" aria-hidden="true">${PS_ICON[id]}</svg><span class="psnum">${big}${sub}</span><span class="psname">${psEsc(name)}</span></button>`}).join('');
 const [id,col,name]=PS_ROWS[PS.sel];panel.className='pspanel '+col;panel.setAttribute('aria-labelledby','pstab'+PS.sel);
 panel.innerHTML=`<h3 class="pshead">${psEsc(name)}</h3>`+(R?R.det[id].map(b=>`<div class="psblock">${b.map(([v,l])=>`<div class="psline">${psVal(v)}<span>${psEsc(l)}</span></div>`).join('')}</div>`).join(''):'<p class="dim">Loading…</p>');
 const pt=psEl('pstime');if(PS.play!=null){pt.hidden=false;pt.innerHTML=`<span>TOTAL PLAY TIME</span><b>${Math.floor(PS.play/3600)}</b> Hours <b>${Math.floor(PS.play%3600/60)}</b> Minutes`}else pt.hidden=true;
 const fe=psEl('pseff'),et=psEffects();fe.hidden=!et;fe.textContent=et;
 psPlace();
 list.querySelectorAll('.psrow').forEach(b=>{b.onclick=()=>psSelect(+b.dataset.i)})}
// on a phone the detail opens right under its row; on a desktop it sits at the right
function psPlace(){const panel=psEl('pspanel'),wrap=psEl('pswrap');if(innerWidth<=760){const b=psEl('pstab'+PS.sel);if(b&&b.nextSibling!==panel)b.after(panel)}else if(panel.parentNode!==wrap)wrap.appendChild(panel)}
function psSelect(i){PS.sel=(i+PS_ROWS.length)%PS_ROWS.length;psRender();const b=psEl('pstab'+PS.sel);if(b)b.focus()}
// opens over the tab that is open: the tabs' content steps aside, the top bar stays
function psOpen(){if(PS.open)return;if(typeof EQ!=='undefined'&&EQ.pick)eqClosePick(true);PS.open=true;PS.sel=0;psEl('screens').hidden=true;psEl('pstats').hidden=false;psEl('pstatsbtn').setAttribute('aria-pressed','true');psRender();const b=psEl('pstab0');if(b&&innerWidth>760)b.focus({preventScroll:true});window.scrollTo({top:0})}
function psClose(quiet){if(!PS.open)return;PS.open=false;psEl('pstats').hidden=true;psEl('screens').hidden=false;psEl('pstatsbtn').setAttribute('aria-pressed','false');if(!quiet){psEl('pstatsbtn').focus()}}
function psSync(){if(PS.open)psRender()}   // called after every render (scrApply)
document.addEventListener('keydown',e=>{
 if(e.ctrlKey||e.metaKey||e.altKey)return;const t=e.target,typing=t&&(/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)||t.isContentEditable);
 if((e.key==='c'||e.key==='C')&&!typing&&!document.querySelector('.igov:not([hidden]),.impov:not([hidden]),.mov:not([hidden])')&&!(typeof EQ!=='undefined'&&EQ.pick)){e.preventDefault();PS.open?psClose():psOpen();return}
 if(PS.open&&e.key==='Escape'){e.preventDefault();psClose();return}
 if(PS.open&&t&&t.classList&&t.classList.contains('psrow')){if(e.key==='ArrowDown'){e.preventDefault();psSelect(PS.sel+1)}else if(e.key==='ArrowUp'){e.preventDefault();psSelect(PS.sel-1)}else if(e.key==='Home'){e.preventDefault();psSelect(0)}else if(e.key==='End'){e.preventDefault();psSelect(PS_ROWS.length-1)}}});
addEventListener('resize',()=>{if(PS.open)psPlace()});
psEl('pstatsbtn').onclick=()=>PS.open?psClose():psOpen();psEl('psclose').onclick=()=>psClose();
