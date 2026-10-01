"""Original placeholder artwork for the planner. Everything here is drawn from scratch in code."""
import io,base64,math,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import os
FONT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'font','BarlowCondensed-SemiBold.ttf')
TREE=[dict(main=(155,26,20),glow=(224,71,58),dark=(90,10,8)),dict(main=(28,88,208),glow=(91,149,255),dark=(12,42,110)),
      dict(main=(47,115,34),glow=(124,201,90),dark=(23,61,16)),dict(main=(156,98,18),glow=(240,176,80),dark=(74,46,8))]
MUTC={'red':(214,52,44),'blue':(52,128,230),'green':(76,190,60),'gold':(230,166,64),'grey':(150,150,150)}
def uri(im,fmt='PNG',q=86):
    b=io.BytesIO()
    if fmt=='JPEG':im.convert('RGB').save(b,'JPEG',quality=q,optimize=True)
    else:im.save(b,'PNG',optimize=True)
    return f'data:image/{"jpeg" if fmt=="JPEG" else "png"};base64,'+base64.b64encode(b.getvalue()).decode()
def smooth(e0,e1,x):
    t=np.clip((x-e0)/(e1-e0),0,1);return t*t*(3-2*t)
def canvas(w,h,ss=4):return Image.new('RGBA',(w*ss,h*ss),(0,0,0,0))
def down(im,w,h):return im.resize((w,h),Image.LANCZOS)
def poly_pts(cx,cy,r,n,rot=-90):return [(cx+r*math.cos(math.radians(rot+360*k/n)),cy+r*math.sin(math.radians(rot+360*k/n))) for k in range(n)]

# ---------- skill icon: faint emblem outline + initials ----------
def emblem(d,cx,cy,r,v,col,wd):
    k=v%8
    if k==0:d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=col,width=wd)
    elif k==1:d.polygon(poly_pts(cx,cy,r*1.1,4),outline=col,width=wd)
    elif k==2:d.polygon(poly_pts(cx,cy,r,6,0),outline=col,width=wd)
    elif k==3:d.polygon(poly_pts(cx,cy,r*1.1,3),outline=col,width=wd)
    elif k==4:d.polygon(poly_pts(cx,cy,r*1.1,3,90),outline=col,width=wd)
    elif k==5:d.polygon(poly_pts(cx,cy,r,5),outline=col,width=wd)
    elif k==6:d.polygon(poly_pts(cx,cy,r,8,22.5),outline=col,width=wd)
    else:
        d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=col,width=wd);rr=r*.68;d.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],outline=col,width=max(1,wd//2))
def initials(name):
    stop={'of','the','and','a','an','to','in'}
    words=[w for w in name.replace('-',' ').replace("'",' ').split() if w.lower() not in stop]
    if not words:return name[:2].upper()
    if len(words)==1:return words[0][:2].capitalize().upper() if len(words[0])>1 else words[0].upper()
    return (words[0][0]+words[1][0]).upper()
def skill_icon(name,ti,idx,S=128,ss=4):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2
    emblem(d,c,c*0.98,S*ss*.36,idx*3+ti,(255,255,255,105),int(S*ss*.032))
    txt=initials(name);f=ImageFont.truetype(FONT,int(S*ss*.5))
    sh=Image.new('RGBA',im.size,(0,0,0,0));sd=ImageDraw.Draw(sh);bb=sd.textbbox((0,0),txt,font=f)
    x=c-(bb[0]+bb[2])/2;y=c*0.98-(bb[1]+bb[3])/2
    sd.text((x+S*ss*.012,y+S*ss*.02),txt,font=f,fill=(0,0,0,200));sh=sh.filter(ImageFilter.GaussianBlur(S*ss*.014))
    im.alpha_composite(sh);ImageDraw.Draw(im).text((x,y),txt,font=f,fill=(250,246,236,255))
    return down(im,S,S)

# ---------- sphere shading ----------
def orb(S,rgb,alpha=1.0,tex=0.05,seed=1,ss=2):
    N=S*ss;yy,xx=np.mgrid[0:N,0:N].astype(np.float32);u=(xx-N/2+.5)/(N/2);v=(yy-N/2+.5)/(N/2);r=np.hypot(u,v)
    z=np.sqrt(np.clip(1-r*r,0,1));L=np.array([-.4,-.5,.77],np.float32);L/=np.linalg.norm(L)
    diff=np.clip(u*L[0]+v*L[1]+z*L[2],0,1);H=L+np.array([0,0,1],np.float32);H/=np.linalg.norm(H)
    spec=np.clip(u*H[0]+v*H[1]+z*H[2],0,1)**60
    rng=np.random.default_rng(seed);tx=np.zeros_like(u)
    for _ in range(6):
        a,b,c1,c2=rng.uniform(4,14,4);tx+=np.sin(u*a+c1)*np.sin(v*b+c2)
    tx=tx/6*tex
    base=np.array(rgb,np.float32)[None,None,:]
    col=base*(0.28+0.85*diff[...,None]+tx[...,None])*(0.62+0.38*z[...,None])+spec[...,None]*150
    col=np.clip(col+ (1-z[...,None])**3*40,0,255)
    a=smooth(1.0,0.965,r)*alpha
    out=np.dstack([col,a*255]).astype(np.uint8);return Image.fromarray(out,'RGBA').resize((S,S),Image.LANCZOS)
def ring(im,cx,cy,r,col,wd,ss):
    d=ImageDraw.Draw(im);d.ellipse([(cx-r)*ss,(cy-r)*ss,(cx+r)*ss,(cy+r)*ss],outline=col,width=int(wd*ss))
def cell_img(kind,W=150,H=149):
    im=Image.new('RGBA',(W,H),(0,0,0,0));R=int(W*.34)*2
    o=orb(R,MUTC[kind],1.0,0.09 if kind!='grey' else 0.14,seed=sum(map(ord,kind))%97)
    if kind=='grey':
        arr=np.array(o).astype(np.float32);g=arr[...,:3].mean(-1,keepdims=True);arr[...,:3]=np.clip(g*0.9+12,0,255);o=Image.fromarray(arr.astype(np.uint8),'RGBA')
    im.alpha_composite(o,(W//2-R//2,H//2-R//2))
    big=im.resize((W*3,H*3),Image.LANCZOS);ring(big,W/2,H/2,W*.385,(255,255,255,70 if kind!='grey' else 46),1.4,3)
    ring(big,W/2,H/2,W*.31,(255,255,255,40),1.0,3);return big.resize((W,H),Image.LANCZOS)
def master_img(W=280,H=282):
    ss=2;im=Image.new('RGBA',(W*ss,H*ss),(0,0,0,0))
    g=orb(int(W*.78)*ss,(175,182,190),0.55,0.12,seed=5,ss=1);im.alpha_composite(g,((W*ss-g.width)//2,(H*ss-g.height)//2))
    for (c,dx,dy,rr) in [((104,80,214),-.13,-.08,.17),((52,160,232),.12,-.05,.17),((76,190,60),-.01,.13,.17)]:
        b=orb(int(W*rr*2)*ss,c,0.88,0.1,seed=abs(int(dx*100))+9,ss=1);im.alpha_composite(b,(int(W*ss/2+dx*W*ss-b.width/2),int(H*ss/2+dy*H*ss-b.height/2)))
    ring(im,W/2,H/2,W*.47,(255,255,255,80),2.2,ss);ring(im,W/2,H/2,W*.385,(255,255,255,55),1.6,ss)
    return im.resize((W,H),Image.LANCZOS)
def mutagen_img(color,tier,S=128):
    im=Image.new('RGBA',(S,S),(0,0,0,0));rgb=MUTC[color];sizes=[.46,.6,.74][tier]
    o=orb(int(S*sizes),rgb,1.0,.1,seed=tier+3);im.alpha_composite(o,((S-o.width)//2,(S-o.height)//2))
    big=im.resize((S*3,S*3),Image.LANCZOS)
    for k in range(tier):ring(big,S/2,S/2,S*(sizes/2+.05+.06*k),tuple(rgb)+(150-k*45,),1.6,3)
    return big.resize((S,S),Image.LANCZOS)
def mutation_icon(n,S=128,ss=4):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2
    f=ImageFont.truetype(FONT,int(S*ss*(.62 if n<10 else .5)));txt=str(n);bb=d.textbbox((0,0),txt,font=f)
    d.text((c-(bb[0]+bb[2])/2,c-(bb[1]+bb[3])/2-S*ss*.02),txt,font=f,fill=(238,234,224,255));return down(im,S,S)

# ---------- panels / frames / backgrounds ----------
def noise(h,w,amp,seed):return np.random.default_rng(seed).normal(0,amp,(h,w,1)).astype(np.float32)
def tree_bg(idx,W=808,H=937):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32);u=(xx/W-.5)*2;v=yy/H
    if idx<4:m=np.array(TREE[idx]['main'],np.float32);dk=np.array(TREE[idx]['dark'],np.float32)*.45
    else:m=np.array((90,90,92),np.float32);dk=np.array((26,26,28),np.float32)
    t=np.clip(v*1.15,0,1)[...,None];base=m[None,None]*(1-t)*.62+dk[None,None]*t+8
    rad=np.hypot(u*.9,(v-.42)*1.5);base=base*(1-.5*smooth(.2,1.25,rad)[...,None])
    cx,cy=0,.5;rr=np.hypot(u*W/H,(v-cy))
    for k,r0 in enumerate((.16,.27,.38)):base+=(np.exp(-((rr-r0)/.004)**2)*(16-3*k))[...,None]
    base+=noise(H,W,3.2,idx+11);return Image.fromarray(np.clip(base,0,255).astype(np.uint8),'RGB').filter(ImageFilter.GaussianBlur(.6))
def tile_bg(idx,S=128):
    yy,xx=np.mgrid[0:S,0:S].astype(np.float32);v=yy/S;g=np.array(TREE[idx]['glow'],np.float32);m=np.array(TREE[idx]['main'],np.float32);dk=np.array(TREE[idx]['dark'],np.float32)
    t=v[...,None];base=np.where(t<.22,g*(1-t/.22)+m*(t/.22),m*(1-(t-.22)/.78)+dk*((t-.22)/.78))
    sheen=np.clip(1-np.hypot(xx/S-.3,yy/S-.15)*2.2,0,1)[...,None]*38;return Image.fromarray(np.clip(base+sheen,0,255).astype(np.uint8),'RGB').convert('RGBA')
def frame(S,col,wd,notch=True,ss=4):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);W=S*ss;w=int(wd*ss);d.rectangle([0,0,W-1,W-1],outline=col,width=w)
    if notch:
        n=int(S*ss*.09)
        for x,y in ((0,0),(W-n,0),(0,W-n),(W-n,W-n)):d.rectangle([x,y,x+n,y+n],fill=col)
    return down(im,S,S)
def sel_frame(S=152,ss=4):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);W=S*ss;t=int(5*ss);L=int(S*ss*.24);m=int(S*ss*.06);c=(255,255,255,255)
    for sx in (0,1):
        for sy in (0,1):
            x=m if sx==0 else W-m;y=m if sy==0 else W-m;dx=1 if sx==0 else -1;dy=1 if sy==0 else -1
            d.rectangle([min(x,x+dx*L),min(y,y+dy*t),max(x,x+dx*L),max(y,y+dy*t)],fill=c);d.rectangle([min(x,x+dx*t),min(y,y+dy*L),max(x,x+dx*t),max(y,y+dy*L)],fill=c)
    gl=im.filter(ImageFilter.GaussianBlur(8*ss));gl.putalpha(gl.getchannel('A').point(lambda a:int(a*.5)));gl.alpha_composite(im);return down(gl,S,S)
def sel_ring(S=152,ss=4):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2;r=S*ss*.46
    d.ellipse([c-r,c-r,c+r,c+r],outline=(255,255,255,255),width=int(4*ss))
    for a in (0,90,180,270):
        x=c+r*math.cos(math.radians(a));y=c+r*math.sin(math.radians(a));d.ellipse([x-9*ss,y-9*ss,x+9*ss,y+9*ss],fill=(0,0,0,0))
    cut=Image.new('RGBA',im.size,(0,0,0,0));cd=ImageDraw.Draw(cut)
    for a in (0,90,180,270):
        x=c+r*math.cos(math.radians(a));y=c+r*math.sin(math.radians(a));cd.ellipse([x-9*ss,y-9*ss,x+9*ss,y+9*ss],fill=(255,255,255,255))
    a=np.array(im);m=np.array(cut)[...,3]>0;a[m]=(0,0,0,0);im=Image.fromarray(a,'RGBA');return down(im,S,S)
def bar(color,W=560,H=128):
    xx=np.tile(np.linspace(0,1,W,dtype=np.float32),(H,1));yy=np.tile(np.linspace(0,1,H,dtype=np.float32)[:,None],(1,W))
    a=(1-smooth(.55,1.0,xx))*(.94-.12*yy);edge=np.exp(-((xx*W)/2.2)**2)
    m=np.array(color,np.float32);col=m*(.85-.35*yy)[...,None]+edge[...,None]*80
    top=(yy*H<2.2)|(yy*H>H-2.2);line=(top*(1-smooth(.2,.9,xx)))[...,None]*70
    out=np.dstack([np.clip(col+line,0,255),np.clip(a*255+edge*60,0,255)]).astype(np.uint8);return Image.fromarray(out,'RGBA')
def tab_icon(k,S=64,ss=6):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2;col=(236,224,196,255);w=int(4*ss);R=S*ss
    if k==0:
        d.line([R*.2,R*.22,R*.8,R*.82],fill=col,width=w);d.line([R*.8,R*.22,R*.2,R*.82],fill=col,width=w)
        d.line([R*.33,R*.6,R*.47,R*.74],fill=col,width=w);d.line([R*.67,R*.6,R*.53,R*.74],fill=col,width=w)
    elif k==1:
        d.polygon(poly_pts(c,c*1.06,R*.36,3),outline=col,width=w);d.ellipse([c-R*.05,c*1.15-R*.05,c+R*.05,c*1.15+R*.05],fill=col)
    elif k==2:
        d.ellipse([R*.24,R*.4,R*.76,R*.9],outline=col,width=w);d.line([R*.43,R*.42,R*.43,R*.16],fill=col,width=w);d.line([R*.57,R*.42,R*.57,R*.16],fill=col,width=w);d.line([R*.36,R*.14,R*.64,R*.14],fill=col,width=w)
    elif k==3:
        pts=[]
        for i in range(8):
            r=R*.4 if i%2==0 else R*.14;a=math.radians(-90+45*i);pts.append((c+r*math.cos(a),c+r*math.sin(a)))
        d.polygon(pts,outline=col,width=w)
    else:
        d.ellipse([R*.12,R*.28,R*.6,R*.76],outline=col,width=w);d.ellipse([R*.4,R*.24,R*.88,R*.72],outline=col,width=w)
    return down(im,S,S)
def ornament(S=128,ss=4):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2;col=(201,168,106,255)
    for r,w in ((.42,3),(.3,2)):d.polygon(poly_pts(c,c,S*ss*r,4),outline=col,width=int(w*ss))
    d.ellipse([c-5*ss,c-5*ss,c+5*ss,c+5*ss],fill=col);return down(im,S,S)
def slot_empty(S=64,ss=6):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2;R=S*ss;col=(176,140,92,255)
    d.polygon(poly_pts(c,c,R*.36,4),outline=col,width=int(2.4*ss));d.line([c-R*.12,c,c+R*.12,c],fill=col,width=int(2.4*ss));d.line([c,c-R*.12,c,c+R*.12],fill=col,width=int(2.4*ss));return down(im,S,S)
def mut_slot_empty(S=64,ss=6):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2;R=S*ss;col=(176,140,92,255)
    d.ellipse([c-R*.32,c-R*.32,c+R*.32,c+R*.32],outline=col,width=int(2.4*ss));d.ellipse([c-R*.07,c-R*.07,c+R*.07,c+R*.07],fill=col);return down(im,S,S)
def padlock(S=64,ss=6):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);R=S*ss;col=(150,124,92,255)
    d.rounded_rectangle([R*.28,R*.44,R*.72,R*.8],radius=R*.05,fill=col);d.arc([R*.34,R*.16,R*.66,R*.62],180,360,fill=col,width=int(3.4*ss))
    d.ellipse([R*.47,R*.55,R*.53,R*.61],fill=(30,26,20,255));d.rectangle([R*.485,R*.58,R*.515,R*.7],fill=(30,26,20,255));return down(im,S,S)
def skill_point(S=64,ss=6):
    im=canvas(S,S,ss);d=ImageDraw.Draw(im);c=S*ss/2;pts=[]
    for i in range(8):
        r=S*ss*.42 if i%2==0 else S*ss*.13;a=math.radians(-90+45*i);pts.append((c+r*math.cos(a),c+r*math.sin(a)))
    gl=Image.new('RGBA',im.size,(0,0,0,0));ImageDraw.Draw(gl).polygon(pts,fill=(255,255,255,200));gl=gl.filter(ImageFilter.GaussianBlur(S*ss*.05))
    im.alpha_composite(gl);d.polygon(pts,fill=(255,255,255,255));return down(im,S,S)
def mut_bg(W=1280,H=682):
    w,h=W//2,H//2;rng=np.random.default_rng(7);pts=rng.uniform([0,0],[w,h],(34,2)).astype(np.float32)
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32);d=np.stack([np.hypot(xx-p[0],yy-p[1]) for p in pts]);d.sort(0);edge=1-smooth(0,5.5,d[1]-d[0])
    rad=np.hypot((xx/w-.5)*1.4,(yy/h-.5)*1.6);base=16+22*(1-smooth(.1,.9,rad))+edge*20+rng.normal(0,1.6,(h,w))
    im=Image.fromarray(np.clip(base,0,255).astype(np.uint8),'L').resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1));return im.convert('RGB')
def helix_bg(W=1307,H=951,ss=2):
    im=Image.new('RGBA',(W*ss,H*ss),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA')
    for (x0,y0,x1,y1,A,k,al) in ((60,930,1250,300,120,28,90),(500,960,1300,520,90,20,70),(760,420,1300,60,70,18,55)):
        P0=np.array([x0,y0],float)*ss;P1=np.array([x1,y1],float)*ss;u=(P1-P0);L=np.linalg.norm(u);u/=L;n=np.array([-u[1],u[0]]);N=int(L/ (3*ss))
        prev=[None,None]
        for i in range(N+1):
            t=i/N;P=P0+u*L*t;ph=t*k
            for s in (0,1):
                off=A*ss*math.sin(ph+s*math.pi);depth=math.cos(ph+s*math.pi);pt=P+n*off
                if prev[s] is not None:d.line([tuple(prev[s]),tuple(pt)],fill=(150,150,150,int(al*(.55+.45*depth))),width=int((4.2+1.8*depth)*ss))
                prev[s]=pt
            if i%3==0:
                a=P+n*A*ss*math.sin(ph);b=P+n*A*ss*math.sin(ph+math.pi);d.line([tuple(a),tuple(b)],fill=(150,150,150,int(al*.42)),width=int(2.4*ss))
    return im.resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(.7))


def mutagen_unique(color, S=128, ss=3):
    """Original placeholder icon for the special (monster) mutagens: an orb with a gold double ring and a small star."""
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); rgb = MUTC[color]
    o = orb(int(S * .56), rgb, 1.0, .1, seed=sum(map(ord, color)) % 89 + 5)
    im.alpha_composite(o, ((S - o.width) // 2, (S - o.height) // 2))
    big = im.resize((S * ss, S * ss), Image.LANCZOS); d = ImageDraw.Draw(big); c = S * ss / 2
    for r, w, a in ((S * .40, 2.2, 235), (S * .46, 1.4, 150)):
        d.ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], outline=(232, 196, 110, a), width=int(w * ss))
    sx, sy, sr = c + S * ss * .27, c - S * ss * .29, S * ss * .09
    d.polygon([(sx, sy - sr), (sx + sr * .28, sy - sr * .28), (sx + sr, sy), (sx + sr * .28, sy + sr * .28), (sx, sy + sr), (sx - sr * .28, sy + sr * .28), (sx - sr, sy), (sx - sr * .28, sy - sr * .28)], fill=(240, 214, 140, 255))
    return big.resize((S, S), Image.LANCZOS)


# ---------- equipment placeholders: one drawn silhouette per slot (the game's icons are used on the live site only) ----------
ITEM_SLOTS=['steel','silver','crossbow','bolts','chest','gloves','trousers','boots','mask']
ITEM_SIZE={'steel':(64,128),'silver':(64,128),'crossbow':(64,128),'bolts':(64,64),'chest':(64,128),'gloves':(64,128),'trousers':(64,128),'boots':(64,128),'mask':(64,64)}
def item_placeholder(slot,ss=6):
    W,H=ITEM_SIZE[slot];im=canvas(W,H,ss);d=ImageDraw.Draw(im);k=ss
    P=lambda pts:[(x*k,y*k) for x,y in pts]
    base=(34,31,28,255);d.rounded_rectangle([1*k,1*k,(W-1)*k,(H-1)*k],radius=4*k,fill=base,outline=(78,66,48,255),width=int(1.2*k))
    steel=(176,184,196,235);silver=(222,228,240,245);gold=(196,150,70,235);leather=(150,108,66,235);dark=(20,18,16,255)
    cx=W/2
    if slot in('steel','silver'):
        c=steel if slot=='steel' else silver
        d.polygon(P([(cx-4,14),(cx+4,14),(cx+3,84),(cx,92),(cx-3,84)]),fill=c);d.line(P([(cx,16),(cx,86)]),fill=(120,128,140,255),width=int(.8*k))
        d.rectangle(P([(cx-13,92),(cx+13,96)]),fill=gold);d.rectangle(P([(cx-2.5,96),(cx+2.5,112)]),fill=leather);d.ellipse(P([(cx-4,111),(cx+4,119)]),fill=gold)
        if slot=='silver':d.polygon(P([(cx,24),(cx+1.6,30),(cx,36),(cx-1.6,30)]),fill=(120,150,210,255))
    elif slot=='crossbow':
        d.rectangle(P([(cx-3,26),(cx+3,112)]),fill=leather);d.arc(P([(cx-26,18),(cx+26,58)]),200,340,fill=steel,width=int(3*k));d.line(P([(cx-26,38),(cx,30),(cx+26,38)]),fill=(210,200,180,255),width=int(.8*k))
        d.polygon(P([(cx-3,24),(cx+3,24),(cx,8)]),fill=silver)
    elif slot=='bolts':
        d.line(P([(14,50),(48,16)]),fill=leather,width=int(2.4*k));d.polygon(P([(52,12),(44,16),(48,20)]),fill=steel);d.polygon(P([(14,50),(10,42),(18,46)]),fill=(180,60,52,255));d.polygon(P([(14,50),(22,54),(18,46)]),fill=(180,60,52,255))
    elif slot=='chest':
        d.polygon(P([(16,22),(24,16),(cx-6,20),(cx,26),(cx+6,20),(W-24,16),(W-16,22),(W-10,48),(W-16,52),(W-20,44),(W-20,104),(20,104),(20,44),(16,52),(10,48)]),fill=leather,outline=gold)
        d.line(P([(cx,26),(cx,104)]),fill=gold,width=int(.9*k));d.line(P([(22,64),(W-22,64)]),fill=gold,width=int(.9*k))
    elif slot=='gloves':
        d.polygon(P([(18,60),(18,30),(24,30),(24,50),(28,24),(34,24),(34,48),(38,22),(44,22),(44,50),(48,30),(54,30),(52,70),(44,84),(26,84)]),fill=leather,outline=gold);d.rectangle(P([(22,84),(48,102)]),fill=steel)
    elif slot=='trousers':
        d.polygon(P([(16,20),(W-16,20),(W-14,110),(cx+3,110),(cx,48),(cx-3,110),(14,110)]),fill=leather,outline=gold);d.line(P([(16,28),(W-16,28)]),fill=gold,width=int(1.2*k))
    elif slot=='boots':
        d.polygon(P([(20,16),(40,16),(40,84),(54,96),(54,110),(14,110),(14,92),(20,86)]),fill=leather,outline=gold);d.rectangle(P([(14,104),(54,112)]),fill=dark)
    elif slot=='mask':
        d.ellipse(P([(14,10),(W-14,H-8)]),fill=(214,200,170,255),outline=gold);d.ellipse(P([(21,24),(29,32)]),fill=dark);d.ellipse(P([(W-29,24),(W-21,32)]),fill=dark);d.arc(P([(24,36),(W-24,52)]),20,160,fill=dark,width=int(1.4*k))
    return down(im,W,H)
