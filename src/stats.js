// ---- Player Stats (v32): the game's Statistics screen, opened from Inventory (button, key C). Every value is worked out from the planner's state the way the game's scripts do, or shows "—" ("not computed yet"): never a guess.
// Sources: the screen itself is CharacterStatsPopup.ws (GetPlayerStatsGFxData, AddCharacterStat*, 50-730), the offence numbers playerWitcher.ws GetOffenseStatsList (8750-9010), the crossbow GetEquippedCrossbowDamage (CharacterStatsPopup.ws 880-934),
// armour GetTotalArmor (playerWitcher.ws 5842), mutagen abilities PlayerAbilityManager.ws 851-1020 and the Lvl / ConGeralt / survival_vitality abilities (data/STATS.json, tools/make_stats.py). Weapons only count while held (nothing is held on this screen).
const STATS=/*@data:STATS*/;
const PS={open:false,sel:0,play:null,opener:null};   // play = seconds played of the last imported save (kept in memory only, never in the link)
const PS_ROWS=[['silver','red','DPS - Silver sword'],['steel','red','DPS - Steel sword'],['armor','red','Armor'],['crossbow','red','Crossbow'],['vitality','green','Vitality'],['toxicity','green','Toxicity'],['sign','blue','Sign intensity'],['stamina','blue','Stamina'],['additional','orange','Additional']];
const PS_ICON={silver:'<path d="M12 3 L14 4 L14 16 L10 16 L10 4 Z M7 16 H17 M12 16 V21"/>',steel:'<path d="M12 2 L14 4 L14 15 L10 15 L10 4 Z M6 15 H18 M12 15 V21"/>',armor:'<path d="M12 3 L20 6 V12 C20 17 16 20 12 21 C8 20 4 17 4 12 V6 Z"/>',crossbow:'<path d="M3 8 C9 4 15 4 21 8 M12 6 V20 M8 12 H16"/>',vitality:'<path d="M12 20 C4 14 3 9 6.5 6.5 C9 5 11 6.5 12 8 C13 6.5 15 5 17.5 6.5 C21 9 20 14 12 20 Z"/>',toxicity:'<path d="M9 3 H15 M10 3 V9 L5 19 C4.5 20.5 5.5 21 7 21 H17 C18.5 21 19.5 20.5 19 19 L14 9 V3"/>',sign:'<path d="M12 3 L20 18 H4 Z M12 8 L16 16 H8 Z"/>',stamina:'<path d="M13 2 L5 13 H11 L10 22 L19 10 H13 Z"/>',additional:'<circle cx="6" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18" cy="12" r="1.6"/>'};
const psL=k=>STATS.labels[k];
const psRound=Math.round;

// the numbers of one equipped item for a stat name: {v, ex} (ex = false when the item rolls it between a minimum and a maximum, so no single value is known)
function psItem(it,name){if(!it)return{v:0,ex:true};let v=0,ex=true;[...(it.base||[]),...(it.bonuses||[])].forEach(b=>{if(b.stat===name){v+=b.min;if(b.max!=null&&b.max!==b.min)ex=false}});return{v,ex}}
const psSum=(it,names)=>names.reduce((a,n)=>{const x=psItem(it,n);return{v:a.v+x.v,ex:a.ex&&x.ex}},{v:0,ex:true});
// a mutagen's real stat (PlayerAbilityManager.ws OnSkillMutagenEquipped, MutagensSyngergyBonusUpdateSingle): its ability's number plus the synergy ability times Synergy level x (matching skills in its group + 1).
// The extra "x" abilities the Character screen adds while it builds its panel (characterMenu.ws 1337-1420) are not part of a saved game's stats, so a mutagen with a matching skill in its group makes the stat unknown.
function psMut(stat){let sum=0,unknown=false;S.muts.forEach((m,g)=>{if(m==null)return;const M=MUTS[m];if(M.stat!==stat)return;let n=0;for(let k=g*3;k<g*3+3;k++)if(slotMatch(k))n++;if(n>0)unknown=true;sum+=M.v+M.syn*synergyLv()*(n+1)});return{sum,unknown}}

function psCalc(){const d=eqData();if(!d||!EQ.meta||!CN.data)return null;
 const L=lvl(),tbl=STATS.lvl[S.rs]||STATS.lvl.ng,con=STATS.con[S.rs]||STATS.con.ng,lv=tbl.slice(0,Math.max(0,L-1));
 const g={};EQ_SLOTS.forEach((s,i)=>g[s]=eqCur(i));
 const worn=['chest','gloves','trousers','boots','mask'].map(s=>g[s]).filter(Boolean),low=EQ_SLOTS.some(s=>g[s]&&eqLow(g[s]));
 const eq=[];S.slots.forEach(v=>{if(v){const t=TREES[v[0]],s=t.sk[v[1]],l=S.lv[v[0]][v[1]];if(l>0)eq.push({id:s.id,l})}});
 const touch=(re,skip)=>eq.some(e=>e.id!==skip&&(STATS.touch[e.id]||[]).some(a=>re.test(a)));
 const mutOn=S.mact>=0&&!!S.mres[S.mact];
 const setTxt=eqSets().flatMap(x=>x.st.bonuses.filter(b=>x.counted>=b.pieces).map(b=>b.text)).join(' ').toLowerCase(),setHit=re=>re.test(setTxt);
 const wornHas=names=>worn.some(it=>!psSum(it,names).ex||psSum(it,names).v!==0);   // a worn piece that changes a stat the screen does not add up: that stat is unknown
 const out={rows:{},det:{}},U=null;
 // ---- resources
 const mv=psMut('vitality'),surv=eq.filter(e=>STATS.surv.includes(e.id)).reduce((a,e)=>a+e.l,0);
 const vitUnk=mutOn||mv.unknown||touch(/^vitality$/)||wornHas(['vitality'])||setHit(/vitality/)||L>tbl.length+1&&S.rs==='ng';
 const vit=vitUnk?U:psRound((con.vitality+lv.reduce((a,r)=>a+r[0],0)+mv.sum)*(1+STATS.surv_mult*surv));
 const stam=touch(/^stamina$/)||wornHas(['stamina'])||setHit(/stamina/)?U:psRound(con.stamina);
 const tox=touch(/^toxicity$/)||wornHas(['toxicity'])||setHit(/toxicity/)?U:psRound(con.toxicity);
 out.rows.vitality={v:vit,max:vit};out.rows.stamina={v:stam,max:stam};out.rows.toxicity={v:tox==null?U:0,max:tox};
 // ---- armour: the four armour pieces' Armor (GetItemArmorTotal), plus the player's own armor ability (no skill the planner has gives any; Melt Armor's armor is the target's, shown as 127 against the game)
 const arm=['chest','gloves','trousers','boots'].map(s=>psItem(g[s],'armor')),armUnk=low||!arm.every(a=>a.ex)||touch(/^armor$/,'magic_s8')||setHit(/armor/);
 const armor=armUnk?U:psRound(arm.reduce((a,x)=>a+x.v,0));
 out.rows.armor={v:armor};
 // ---- offence (GetOffenseStatsList)
 const ma=psMut('attack_power'),ap={mult:1+ma.sum,add:lv.reduce((a,r)=>a+r[1],0)},offUnk=low||mutOn||ma.unknown||touch(/^(attack_power|critical_hit)/)||wornHas(['attack_power','critical_hit_chance','critical_hit_damage_bonus'])||setHit(/attack|damage|critical|sword/);
 const sword=(it,names)=>{if(!it)return{dmg:0,none:true};const dm=psSum(it,names),el=psSum(it,['FireDamage','FrostDamage']),cc=psItem(it,'critical_hit_chance'),cd=psItem(it,'critical_hit_damage_bonus');
  const ex=dm.ex&&el.ex&&cc.ex&&cd.ex;if(offUnk||!ex)return null;
  const crit=con.crit_chance+cc.v,cdm=con.crit_damage+cd.v,dmg=dm.v,e=el.v,fast=(dmg)*ap.mult+ap.add+e,fastC=dmg*(ap.mult+cdm)+ap.add+e,strong=(dmg*ap.mult+ap.add+e)*1.833,strongC=(dmg*(ap.mult+cdm)+ap.add+e)*1.833;
  const dps=(a,c,t)=>(a*(100-crit*100)+c*crit*100)/100/t;
  return{fast,fastC,strong,strongC,crit:crit*100,fdps:dps(fast,fastC,0.6),sdps:dps(strong,strongC,1.1)}};
 const swords={silver:sword(g.silver,['SilverDamage']),steel:sword(g.steel,['SlashingDamage','PiercingDamage','BludgeoningDamage'])};
 const chance=(it,n)=>{if(!it)return psRound(0)+' %';const x=psItem(it,n);return x.ex?psRound(x.v*100)+' %':U};
 ['silver','steel'].forEach(k=>{const s=swords[k],it=g[k],none=s&&s.none;
  out.rows[k]={v:s===null?U:none?0:psRound((s.fdps+s.sdps)/2)};
  const f=x=>s===null?U:none?0:psRound(x),c=x=>s===null?U:none?'0 %':psRound(x)+' %';
  const nm=k==='silver'?'silver':'steel';
  out.det[k]=[[[s===null?U:f(s.fast),psL('panel_common_statistics_tooltip_'+nm+'_fast_dps')],[c(s&&s.crit),psL('panel_common_statistics_tooltip_'+nm+'_fast_crit_chance')],[f(s&&s.fastC),psL('panel_common_statistics_tooltip_'+nm+'_fast_crit_dmg')]],
   [[f(s&&s.strong),psL('panel_common_statistics_tooltip_'+nm+'_strong_dps')],[c(s&&s.crit),psL('panel_common_statistics_tooltip_'+nm+'_strong_crit_chance')],[f(s&&s.strongC),psL('panel_common_statistics_tooltip_'+nm+'_strong_crit_dmg')]],
   ['poinsonchance','bleedingchance','burningchance','confusionchance','freezingchance','staggerchance'].map(n=>[chance(it,'desc_'+n+'_mult'),psL('attribute_name_desc_'+n+'_mult')])]});
 // ---- crossbow (GetEquippedCrossbowDamage): ((bolt piercing + 0) x mult + add + (bolt silver + 0) x mult + add) / 2, mult = the crossbow's attack_power + the player's
 const xb=g.crossbow,bolt=g.bolts,bp=psItem(bolt,'PiercingDamage'),bs=psItem(bolt,'SilverDamage'),bb=psItem(bolt,'BludgeoningDamage'),bf=psItem(bolt,'FireDamage'),xa=psItem(xb,'attack_power');
 const xbUnk=offUnk||!xa.ex||!bp.ex||!bs.ex||touch(/^attack_power/);
 let steelD,silverD,steelKey='attribute_name_piercingdamage';if(!bolt){steelD=5;silverD=4}else if(bf.v>0){steelD=silverD=bf.v;steelKey='attribute_name_firedamage'}else{silverD=bs.v;if(bp.v>0)steelD=bp.v;else{steelD=bb.v;steelKey='attribute_name_bludgeoningdamage'}}
 const xm=xa.v+ap.mult,xv=!xb?0:xbUnk?U:psRound(((steelD)*xm+ap.add+(silverD)*xm+ap.add)/2);
 out.rows.crossbow={v:xv};
 out.det.crossbow=[[[xbUnk&&!!xb?U:psRound((con.crit_chance)*100)+' %',psL('panel_common_statistics_tooltip_crossbow_crit_chance')],[psRound(steelD),psL(steelKey)],[psRound(silverD),psL('attribute_name_silverdamage')]]];
 // ---- the rest
 const res=n=>{const a=['chest','gloves','trousers','boots'].map(s=>psItem(g[s],n));return low||!a.every(x=>x.ex)?U:psRound(a.reduce((q,x)=>q+x.v,0)*100)+' %'};
 out.det.armor=[[[res('slashing_resistance_perc'),psL('slashing_resistance_perc')],[res('piercing_resistance_perc'),psL('attribute_name_piercing_resistance_perc')],[res('bludgeoning_resistance_perc'),psL('bludgeoning_resistance_perc')],[res('rending_resistance_perc'),psL('attribute_name_rending_resistance_perc')],[res('elemental_resistance_perc'),psL('attribute_name_elemental_resistance_perc')]],
  [['poison_resistance_perc',con.poison_resist],['bleeding_resistance_perc',con.bleeding_resist],['burning_resistance_perc',0]].map(([n,b])=>{const a=['chest','gloves','trousers','boots'].map(s=>psItem(g[s],n));return[low||!a.every(x=>x.ex)?U:psRound((b+a.reduce((q,x)=>q+x.v,0))*100)+' %',psL('attribute_name_'+n)]})];
 out.det.vitality=[[[U,psL('panel_common_statistics_tooltip_outofcombat_regen')],[U,psL('panel_common_statistics_tooltip_incombat_regen')]]];
 out.det.toxicity=[[[tox==null?U:0,psL('toxicity_offset')],[tox==null?U:0,psL('toxicity')]]];
 out.rows.sign={v:U};out.det.sign=[[[U,psL('Aard')]],[[U,psL('attribute_name_knockdown')],[U,psL('attribute_name_forcedamage')]],[[U,psL('Igni')]],[[U,psL('attribute_name_firedamage')],[U,psL('effect_burning')]],[[U,psL('Quen')]],[[U,psL('physical_resistance')]],[[U,psL('Yrden')]],[[U,psL('SlowdownEffect')],[U,psL('ShockDamage')],[U,psL('duration')]],[[U,psL('Axii')]],[[U,psL('duration')]]];
 out.det.stamina=[[[U,psL('attribute_name_staminaregen_out_of_combat')],[U,psL('attribute_name_staminaregen')]]];
 const kill=['steel','silver'].map(s=>psItem(g[s],'instant_kill_chance_mult')),kd=!kill.every(x=>x.ex)||touch(/^instant_kill/)?U:psRound(kill.reduce((q,x)=>q+x.v,0)*100)+' %';
 const wp=n=>{const a=worn.map(it=>psItem(it,n));return a.every(x=>x.ex)?psRound(a.reduce((q,x)=>q+x.v,0)*100)+' %':U};
 out.rows.additional={v:''};out.det.additional=[[[wp('bonus_herb_chance'),psL('bonus_herb_chance')],[kd,psL('instant_kill_chance')],[wp('human_exp_bonus_when_fatal'),psL('human_exp_bonus_when_fatal')],[wp('nonhuman_exp_bonus_when_fatal'),psL('nonhuman_exp_bonus_when_fatal')]]];
 return out}

// ---- the screen ----
const psEl=id=>document.getElementById(id);
const psVal=v=>v==null?`<b class="psu" title="not computed yet" aria-label="not computed yet">—</b>`:`<b>${psEsc(String(v))}</b>`;
const psEsc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function psRender(){const R=psCalc(),list=psEl('psrows'),panel=psEl('pspanel');if(!list)return;
 if(panel.parentNode===list)psEl('pswrap').appendChild(panel);   // the phone layout keeps the detail inside the list: take it out before the rows are drawn again
 list.innerHTML=PS_ROWS.map(([id,col,name],i)=>{const r=R?R.rows[id]:{v:null},sel=i===PS.sel,big=id==='sign'?(r.v==null?psVal(null):`<b>+${r.v} %</b>`):id==='additional'?'':psVal(r.v),
  sub=id==='vitality'||id==='stamina'||id==='toxicity'?`<small>${r.max==null?'—':psEsc(String(r.max))}</small>`:'';
  return`<button type="button" role="tab" class="psrow ${col}${sel?' sel':''}" id="pstab${i}" aria-selected="${sel}" aria-controls="pspanel" tabindex="${sel?0:-1}" data-i="${i}"><svg class="psicon" viewBox="0 0 24 24" aria-hidden="true">${PS_ICON[id]}</svg><span class="psnum">${big}${sub}</span><span class="psname">${psEsc(name)}</span></button>`}).join('');
 const [id,col,name]=PS_ROWS[PS.sel];panel.className='pspanel '+col;panel.setAttribute('aria-labelledby','pstab'+PS.sel);
 panel.innerHTML=`<h3 class="pshead">${psEsc(name)}</h3>`+(R?R.det[id].map(b=>`<div class="psblock">${b.map(([v,l])=>`<div class="psline">${psVal(v)}<span>${psEsc(l)}</span></div>`).join('')}</div>`).join(''):'<p class="dim">Loading…</p>');
 const pt=psEl('pstime');if(PS.play!=null){pt.hidden=false;pt.innerHTML=`<span>TOTAL PLAY TIME</span><b>${Math.floor(PS.play/3600)}</b> Hours <b>${Math.floor(PS.play%3600/60)}</b> Minutes`}else pt.hidden=true;
 psPlace();
 list.querySelectorAll('.psrow').forEach(b=>{b.onclick=()=>psSelect(+b.dataset.i)})}
// on a phone the detail opens right under its row; on a desktop it sits at the right
function psPlace(){const panel=psEl('pspanel'),wrap=psEl('pswrap');if(innerWidth<=760){const b=psEl('pstab'+PS.sel);if(b&&b.nextSibling!==panel)b.after(panel)}else if(panel.parentNode!==wrap)wrap.appendChild(panel)}
function psSelect(i,focus){PS.sel=(i+PS_ROWS.length)%PS_ROWS.length;psRender();if(focus!==false){const b=psEl('pstab'+PS.sel);if(b)b.focus()}}
function psOpen(){if(S.scr!=='inv'||PS.open)return;if(EQ.pick)eqClosePick(true);PS.open=true;PS.sel=0;PS.opener=document.activeElement;psEl('eqbody').hidden=true;psEl('invhint').hidden=true;psEl('pstats').hidden=false;psRender();const b=psEl('pstab0');if(b&&innerWidth>760)b.focus({preventScroll:true});window.scrollTo({top:0})}
function psClose(quiet){if(!PS.open)return;PS.open=false;psEl('pstats').hidden=true;psEl('eqbody').hidden=false;psEl('invhint').hidden=false;if(!quiet){const o=psEl('pstatsbtn');if(o)o.focus()}}
function psSync(){if(PS.open){if(S.scr!=='inv')psClose(true);else psRender()}}   // called after every render (scrApply)
document.addEventListener('keydown',e=>{
 if(e.ctrlKey||e.metaKey||e.altKey)return;const t=e.target,typing=t&&(/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)||t.isContentEditable);
 if((e.key==='c'||e.key==='C')&&!typing&&S.scr==='inv'&&!document.querySelector('.igov:not([hidden]),.impov:not([hidden]),.mov:not([hidden])')&&!EQ.pick){e.preventDefault();PS.open?psClose():psOpen();return}
 if(PS.open&&e.key==='Escape'){e.preventDefault();psClose();return}
 if(PS.open&&t&&t.classList&&t.classList.contains('psrow')){if(e.key==='ArrowDown'){e.preventDefault();psSelect(PS.sel+1)}else if(e.key==='ArrowUp'){e.preventDefault();psSelect(PS.sel-1)}else if(e.key==='Home'){e.preventDefault();psSelect(0)}else if(e.key==='End'){e.preventDefault();psSelect(PS_ROWS.length-1)}}});
addEventListener('resize',()=>{if(PS.open)psPlace()});
psEl('pstatsbtn').onclick=psOpen;psEl('psclose').onclick=()=>psClose();
