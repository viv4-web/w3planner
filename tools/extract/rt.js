const R=require('./rt.json');
const enumToId=e=>{const m=e.match(/S_(Sword|Magic|Alchemy|Perk)_(s?)(\d+)/);return ({Sword:'sword',Magic:'magic',Alchemy:'alchemy',Perk:'perk'})[m[1]]+'_'+m[2]+(+m[3])};
const V=o=>({b:o?o.b:0,a:o?o.a:0,m:o?o.m:0});
function SA(e,attr){const id=enumToId(e).replace('perk__','perk_');const a=(R.ab[id]||R.ab[id.replace('_s','_s')]||{})[attr];return V(a)}
function AA(ab,attr){return V((R.ab[ab]||{})[attr])}
function MUL(v,k){return {b:v.b*k,a:v.a*k,m:v.m*k}}
function CALC(v){return v.b*(1+v.m)+v.a}
const NTZ=x=>String(+(+x).toFixed(2)), FTS=x=>String(+(+x).toFixed(2)), FTSP=(x,p)=>(+x).toFixed(p);
function fill(str,ints,floats,strs){let i=0,f=0,s=0;return (str||'').replace(/\$I\$/g,()=>ints&&ints[i]!==undefined&&!isNaN(ints[i])?ints[i++]:(i++,'?')).replace(/\$F\$/g,()=>floats&&floats[f]!==undefined?NTZ(floats[f++]):'?').replace(/\$S\$/g,()=>strs&&strs[s]!==undefined?strs[s++]:'?')}
function run(id,L){const code=R.tips[id];const LOC=k=>k===locKey?R.desc[id][Math.min(L,3)-1]:(R.locs[k]||'');
 const LOCP=(k,ints,floats,strs)=>fill(k===locKey?R.desc[id][Math.min(L,3)-1]:(R.locs[k]||''),ints,floats,strs);
 const locKey='__desc__';const skillLevel=L;let out='',argsInt=[],argsFloat=[],argsString=[],arg=0,arg_focus=0,ability={b:0,a:0,m:0},mn={b:0,a:0,m:0},mx=mn,min=mn,max=mn;
 const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};
 const GetWitcherPlayer=()=>({GetStatMax:()=>100,GetAlchemyS03Threshold:()=>NaN});const theGame={GetDefinitionsManager:()=>({GetAbilityAttributeValue:()=>{arg=NaN}})};const EffectTypeToName=()=>'',StatEnumToName=()=>'',BCS_Stamina=0,BCS_Vitality=0,EET_IgnorePain=0;let penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp;
 eval(code.replace(/\blet\b/g,''));return out.replace(/<br>/g,'\n')}
module.exports={run};
if(require.main===module){let ok=0,err=[];for(const id in R.tips){for(const L of [1,3]){try{const s=run(id,L);if(!s||/\$[IFS]\$/.test(s)||/NaN|undefined/.test(s))err.push([id,L,(s||'').slice(0,90)]);else ok++}catch(e){err.push([id,L,e.message])}}}
 console.log('ok',ok,'problems',err.length);err.slice(0,25).forEach(x=>console.log(x.join(' | ')));console.log('\nSAMPLE s11 L3:',run('magic_s11',3));console.log('SAMPLE s42 L2:',run('magic_s42',2))}
