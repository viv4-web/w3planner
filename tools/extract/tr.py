import re,json
new=open('characterMenuDupe.ws',encoding='utf-8',errors='replace').read()
old=open('characterMenu.ws',encoding='utf-8',errors='replace').read()
S=json.load(open('/home/claude/skills.json'))
def enum(id):
  m=re.match(r'(sword|magic|alchemy|perk)_?(s?)(\d+)',id);k,s,n=m.groups()
  return {'sword':'S_Sword_','magic':'S_Magic_','alchemy':'S_Alchemy_','perk':'S_Perk_'}[k]+('s' if s else '')+(n.zfill(2) if s else n)
def funcs(src):
  out={}
  for m in re.finditer(r'private function (Get\w+TooltipDescription)\(targetSkill.*?\n\t\{(.*?)\n\t\}\r?\n',src,re.S):
    body=m.group(2)
    if 'switch' not in body: continue
    sw=body.index('switch');pre=body[:sw];cases={}
    for c in re.finditer(r'case (S_\w+):(.*?)(?=\n\t\t\tcase S_|\n\t\t\tdefault:)',body,re.S):cases.setdefault(c.group(1),c.group(2))
    post=''
    r=body.rfind('return ')
    if r>0 and 'baseString' in body[r:r+200]:
      post=body[r:].split(';')[0].replace('return baseString','baseString = baseString')+';'
    out[m.group(1)]=(pre,cases,post)
  return out
F=[funcs(new),funcs(old)]
def find(e):
  for fs in F:
    for fn,(pre,cases,post) in fs.items():
      if e in cases: return pre,cases[e]+'\n'+post
  return None,None
def tr(code):
  c=re.sub(r'//.*','',code)
  c=re.sub(r'\bvar\b[^;]*;','',c)
  c=re.sub(r"(?:GetWitcherPlayer\(\)|thePlayer)\.GetSkillAttributeValue\(\s*(S_\w+)\s*,\s*('[^']*'|[\w()\"]+)[^;]*?\)(?=\s*[*;)\s])",r'SA("\1",\2)',c)
  c=re.sub(r"PowerStatEnumToName\((\w+)\)",r'"\1"',c)
  c=re.sub(r"(?:dm|theGame\.GetDefinitionsManager\(\))\.GetAbilityAttributeValue\(\s*'([^']+)'\s*,\s*('[^']*'|[\w\"]+)\s*,\s*min\s*,\s*max\s*\)",r'mn=AA("\1",\2);mx=mn',c)
  c=re.sub(r'dm\s*=\s*theGame\.GetDefinitionsManager\(\);','',c)
  c=re.sub(r'GetAttributeRandomizedValue\(\s*min\s*,\s*max\s*\)','mn',c)
  c=re.sub(r'(\bSA\("[^"]+",[^)]*\)|\bability\b|\bmn\b)\s*\*\s*\(([^()]*)\)',r'MUL(\1,(\2))',c)
  c=re.sub(r'(\bSA\("[^"]+",[^)]*\)|\bAA\("[^"]+",[^)]*\)|\bability\b|\bmn\b)\s*\*\s*(skillLevel|\d+(?:\.\d+)?f?)',r'MUL(\1,\2)',c)
  c=re.sub(r'(\d+(?:\.\d+)?)f\b',r'\1',c)
  for a,b in [('CalculateAttributeValue','CALC'),('RoundMath','Math.round'),('RoundF','Math.round'),('FloorF','Math.floor'),('CeilF','Math.ceil'),('AbsF','Math.abs'),('FloatToStringPrec','FTSP'),('FloatToString','FTS'),('NoTrailZeros','NTZ'),('IntToString','String'),
              ('valueMultiplicative','m'),('valueAdditive','a'),('valueBase','b'),('.PushBack(','.push('),
              ('GetLocStringByKeyExtWithParams','LOCP'),(', ,',', undefined,'),('GetLocStringByKeyExt','LOC'),('GetLocStringByKey','LOC'),('baseString','out')]:c=c.replace(a,b)
  c=re.sub(r'\bMin\(','Math.min(',c);c=re.sub(r'\bMax\(','Math.max(',c)
  c=re.sub(r'\bbreak;','',c)
  return c
out={};bad=[]
for s in S:
  pre,case=find(enum(s['id']))
  if case is None: bad.append(s['id']);continue
  out[s['id']]=tr(pre)+'\n'+tr(case)
json.dump(out,open('/home/claude/tipjs.json','w'))
print('translated',len(out),'none',bad)
