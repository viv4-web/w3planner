{
"sword_s2":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		
				
				
				ability = SA("S_Sword_s02",'adrenaline_damage_bonus');
				argsInt.push(Math.round(ability.m * skillLevel * 100));
				
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s16":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				arg = CALC(SA("S_Sword_s16",'focus_drain_reduction')) * skillLevel;
				argsInt.push(Math.round(arg*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s18":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				if (skillLevel > 1)
				{
					arg = CALC(SA("S_Sword_s18",'healing_bonus')) * (skillLevel-1);
					argsInt.push(Math.round(arg*100));
					out = LOCP(locKey, argsInt);
				}
				else
					out = LOC(targetSkill.localisationDescriptionKey);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s20":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s20",'focus_gain'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s19":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s19",'spell_power'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"magic_s20":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				arg = CALC(SA("S_Magic_s20",'range')) * skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s1":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				penaltyReduction = 1 - (skillLevel + 1) * CALC(SA("S_Magic_s01",'spell_power_penalty_reduction'));
				penalty = SA("S_Magic_s01","CPS_SpellPower");
				arg = -penalty.m * penaltyReduction;
			
				argsInt.push(Math.round(arg*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s8":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s08",'burn_chance_bonus'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
					
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s3":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				argsInt.push(25*(skillLevel-1));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s11":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				arg = CALC(SA("S_Magic_s11",'direct_damage_per_sec')) * skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
					
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s13":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				out = LOCP(locKey);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s4":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				if (skillLevel == 1 || skillLevel == 2)
					argsInt.push(100/skillLevel);
				
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s17":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				out = LOCP(locKey);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s19":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				if (skillLevel == 1 || skillLevel == 2)
					argsInt.push(50/skillLevel);
				
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"alchemy_s2":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Alchemy_s02",'vitality_gain_perc')) * skillLevel;
				argsInt.push(Math.round(arg*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s3":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = GetWitcherPlayer().GetAlchemyS03Threshold(skillLevel);
				argsInt.push(Math.max(0, Math.round(arg*100)));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s4":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Alchemy_s04",'apply_chance')) * skillLevel;
				argsInt.push(Math.min(100, Math.round(arg*100)));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s12":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		
			
				arg = CALC(SA("S_Alchemy_s12",'skill_chance')) * skillLevel;
				argsInt.push(Math.round(arg * 100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s5":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = 5 * skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s10":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Alchemy_s10",'PhysicalDamage')) * skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s8":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Alchemy_s08",'item_count')) * skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s11":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = 1 + skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s18":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				argsInt.push(skillLevel);
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s13":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Alchemy_s13",'vitality')) * skillLevel;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s14":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				ability = MUL(SA("S_Alchemy_s14",'duration'),skillLevel);				
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s16":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				argsInt.push(5*skillLevel);
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s20":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				theGame.GetDefinitionsManager().GetAbilityAttributeValue(EffectTypeToName(EET_IgnorePain), StatEnumToName(BCS_Vitality), min, max);
				ability = mn;
				arg = ability.m * skillLevel;				
				argsInt.push(Math.round(arg*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s15":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Alchemy_s15",'toxicityRegen')) * skillLevel;
				if(arg < 0) arg = -arg;
				argsInt.push(Math.round(arg));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"sword_s22":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s22",'trigger_at_attack_count'),skillLevel);
				argsInt.push(Math.round(ability.b));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s23":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s23",'damage_increase'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s24":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s24",'trigger_chance'),skillLevel);
				argsInt.push(Math.round(ability.b*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s25":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s25",'trigger_chance'),skillLevel);
				argsInt.push(Math.round(ability.b*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s26":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s26",'damage_increase'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s27":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s27",'duration'),skillLevel);
				argsInt.push(Math.round(ability.a));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s28":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s28",'stacking'),skillLevel);
				argsInt.push(Math.round(ability.b));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s29":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s29",'damage_increase'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s30":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s30",'adrenaline_gain'),skillLevel);
				argsFloat.push(ability.a);
				out = LOCP(locKey, undefined, argsFloat);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s31":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s31",'attack_power'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = SA("S_Sword_s31",'crossbow_multiplier');
				argsFloat.push(ability.a);
				out = LOCP(locKey, argsInt, argsFloat);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s32":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				ability = MUL(SA("S_Sword_s32",'slowdown_mod'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				ability = SA("S_Sword_s32",'damage_increase');
				argsInt.push(Math.round((ability.a+1)*100));
				ability = MUL(SA("S_Sword_s32",'instant_kill_chance'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s33":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				if (skillLevel > 1)
				{
					ability = MUL(SA("S_Sword_s33",'damage_increase'),(skillLevel - 1));
					argsInt.push(Math.round(ability.a*100));
				}
				ability = MUL(SA("S_Sword_s33",'instant_kill_chance'),(skillLevel));
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s34":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				if (skillLevel == 1)
					ability = SA("S_Sword_s34",'focus_gain_lvl1');
				else if (skillLevel == 2)
					ability = SA("S_Sword_s34",'focus_gain_lvl2');
				else if (skillLevel == 3)
					ability = SA("S_Sword_s34",'focus_gain_lvl3');
				
				argsFloat.push(ability.a);
				out = LOCP(locKey, undefined, argsFloat);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s35":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				if (skillLevel == 2)
					ability = SA("S_Sword_s35",'cost_reduction_desc_lvl2');
				else if (skillLevel == 3)
					ability = SA("S_Sword_s35",'cost_reduction_desc_lvl3');

				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"sword_s36":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("sword_adrenalinegain",'focus_gain');mx=mn;
		ability =  mn;
		arg_focus = ability.a;

		

				arg = CALC(SA("S_Sword_s36",'damage_reduction')) * skillLevel;
				argsInt.push(Math.round(arg*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("focus_gain") + ": +" + Math.round((arg_focus * 100) * skillLevel) + "%";
;return out;},
"magic_s42":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		
				
				arg = CALC(SA("S_Magic_s42",'trap_duration')) * skillLevel;
				argsInt.push(Math.round(arg));
				ability = MUL(SA("S_Magic_s42",'range'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				arg = CALC(SA("S_Magic_s42",'charge_count')) * skillLevel;
				argsInt.push(Math.round(arg));
				arg = CALC(SA("S_Magic_s42",'trap_count')) * skillLevel;
				argsInt.push(Math.round(arg));

				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s28":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s28",'stamina_cost_reduction_after_1'),(skillLevel-1));
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s31":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s31",'attack_power'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s33":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s33",'damage_vitality_percent'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s35":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s35",'spell_power_aard_igni'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s36":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s36",'duration'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s37":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				if (skillLevel == 1)
					ability = SA("S_Magic_s37",'damage_level1');
				else if (skillLevel == 2)
					ability = SA("S_Magic_s37",'damage_level2');
				else if (skillLevel == 3)
					ability = SA("S_Magic_s37",'damage_level3');
				
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s38":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s38",'spell_power'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s39":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				ability = MUL(SA("S_Magic_s39",'stamina_cost_reduction'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"magic_s40":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		 
		
		
		
		mn=AA("magic_staminaregen",'staminaRegen');mx=mn;
		ability =  mn;
		arg_stamina = ability.m;

		

				out = LOCP(locKey, argsInt);
				
out = out + "<br>" + LOC("attribute_name_staminaregen") + ": +" + NTZ((arg_stamina * 100) * skillLevel) + "/" + LOC("per_second");
;return out;},
"alchemy_s22":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				ability = MUL(SA("S_Alchemy_s22",'defence_bonus'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s23":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				if (skillLevel == 1)
					ability = SA("S_Alchemy_s23",'poison_dmg_level_1');
				else if (skillLevel == 2)
					ability = SA("S_Alchemy_s23",'poison_dmg_level_2');
				else if (skillLevel == 3)
					ability = SA("S_Alchemy_s23",'poison_dmg_level_3');
				
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s24":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				ability = MUL(SA("S_Alchemy_s24",'critical_hit_damage_bonus'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s25":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				ability = MUL(SA("S_Alchemy_s25",'bomb_damage_bonus'),skillLevel);
				argsFloat.push(ability.a*100);
				out = LOCP(locKey, undefined, argsFloat);
				
out = out;
;return out;},
"alchemy_s26":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				ability = MUL(SA("S_Alchemy_s26",'damage_bonus'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				ability = MUL(SA("S_Alchemy_s26",'damage_bonus_immune'),skillLevel);
				argsInt.push(Math.round(ability.a*100));

				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"alchemy_s27":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				ability = MUL(SA("S_Alchemy_s27",'critical_hit_damage_bonus'),skillLevel);
				argsInt.push(Math.round(ability.a*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_23":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_23",'critical_hit_damage_bonus'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = MUL(SA("S_Perk_23",'attack_power_fast_style'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_24":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_24",'spell_power'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = MUL(SA("S_Perk_24",'staminaRegen'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_25":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_25",'vitality'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = MUL(SA("S_Perk_25",'attack_power_heavy_style'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_26":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_26",'attack_power'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = MUL(SA("S_Perk_26",'spell_power'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_27":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_27",'attack_power_fast_style'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = MUL(SA("S_Perk_27",'bomb_dmg_multiplier'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_28":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_28",'poison_dmg_multiplier'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				ability = MUL(SA("S_Perk_28",'vitality'),skillLevel);
				argsInt.push(Math.round(ability.m*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_43":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		
		
		
		
		
		mn=AA("alchemy_potionduration",'potion_duration');mx=mn;
		ability =  mn;
		arg_duration = CALC(ability);
		
		

				arg = CALC(SA("S_Perk_43",'synergy_bonus')) * skillLevel;
				argsInt.push(Math.round(arg*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_30":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_30",'vitality');
				argsInt.push( Math.round( skillLevel * ability.m * 100 ) );
				out = LOCP( locKey, argsInt );
				
out = out;
;return out;},
"perk_31":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				out = LOCP( locKey );
				
out = out;
;return out;},
"perk_32":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_32",'cost_reduction');
				argsInt.push( Math.round( skillLevel * ability.m * 100 ) );
				out = LOCP( locKey, argsInt );
				
out = out;
;return out;},
"perk_33":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_33",'toxicity');
				argsInt.push( Math.round( skillLevel * ability.b ) );
				out = LOCP( locKey, argsInt );
				
out = out;
;return out;},
"perk_34":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_34",'adrenaline_cost');
				argsFloat.push( ability.b - skillLevel * 0.5 );
				out = LOCP( locKey, undefined, argsFloat );
				
out = out;
;return out;},
"perk_35":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_35",'encumbrance');
				argsInt.push( Math.round( skillLevel * ability.b ) );
				out = LOCP( locKey, argsInt );
				
out = out;
;return out;},
"perk_44":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_44",'melee_damage_increase');
				argsInt.push( Math.round( skillLevel * ability.m * 100 ) );
				out = LOCP( locKey, argsInt );
				
out = out;
;return out;},
"perk_37":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_37",'damage_multiplier'),skillLevel);
				argsInt.push(Math.round(ability.a * 100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_38":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = SA("S_Perk_38",'vitalityRegen_tooltip');
				argsInt.push( Math.round( skillLevel * CALC( ability ) ) );
				ability = SA("S_Perk_38",'staminaRegen_tooltip');
				argsInt.push( Math.round( skillLevel * ability.m * GetWitcherPlayer().GetStatMax(BCS_Stamina) ) );
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_39":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_39",'free_bomb'),skillLevel);
				argsInt.push(Math.round(ability.a * 100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_40":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_40",'critical_hit_chance'),skillLevel);
				argsInt.push(Math.round(100 * ability.a));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;},
"perk_41":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_41",'duration'),skillLevel);
				argsInt.push( Math.round( ability.a/60 ) );
				out = LOCP( locKey, argsInt );
				
out = out;
;return out;},
"perk_42":function(H,L,id){const {SA,AA,MUL,CALC,NTZ,FTS,FTSP,LOC,LOCP,GetWitcherPlayer,theGame,EffectTypeToName,StatEnumToName,BCS_Stamina,BCS_Vitality,EET_IgnorePain}=H;const skillLevel=L,locKey="__desc__";
let out="",argsInt=[],argsFloat=[],argsString=[],arg=NaN,arg_focus=0,arg_stamina=0,ability={b:0,a:0,m:0},mn=ability,mx=ability,min=ability,max=ability,penalty,penaltyReduction,arg2,arg3,value,val,dmg,amount,percent,tmp,sp;
const targetSkill={localisationDescriptionKey:locKey,localisationDescriptionLevel2Key:locKey,localisationDescriptionLevel3Key:locKey};

		
		
		
		
		
		
		
		
		

		
		
		mn=AA("survival_vitality",'vitality');mx=mn;
		ability =  mn;
		arg_vit = ability.m;

		

				ability = MUL(SA("S_Perk_42",'focus_gain'),skillLevel);
				argsInt.push(Math.round(ability.b*100));
				out = LOCP(locKey, argsInt);
				
out = out;
;return out;}
}