import struct,zlib,sys,os,io
from PIL import Image
def load(p):
  d=open(p,'rb').read()
  i=d.find(b'FWS');j=d.find(b'CWS');k=d.find(b'ZWS')
  cands=[x for x in (i,j,k) if x>=0];s=min(cands);d=d[s:]
  sig=d[:3];ver=d[3];ln=struct.unpack('<I',d[4:8])[0]
  if sig==b'CWS':body=zlib.decompress(d[8:])
  elif sig==b'ZWS':
    import lzma;body=lzma.LZMADecompressor(lzma.FORMAT_ALONE).decompress(d[12:17]+struct.pack('<Q',ln-8)+d[17:])
  else:body=d[8:]
  return s,sig,ver,body
def tags(body):
  nb=body[0]>>3;rb=(5+nb*4+7)//8;p=rb+4
  while p<len(body):
    h=struct.unpack('<H',body[p:p+2])[0];p+=2;code=h>>6;l=h&63
    if l==63:l=struct.unpack('<I',body[p:p+4])[0];p+=4
    yield code,body[p:p+l];p+=l
    if code==0:break
def extract(p,out):
  off,sig,ver,body=load(p);os.makedirs(out,exist_ok=True)
  names={};imgs={};jt=None;cnt={}
  for code,t in tags(body):
    cnt[code]=cnt.get(code,0)+1
    if code in (56,76):
      n=struct.unpack('<H',t[:2])[0];q=2
      for _ in range(n):
        cid=struct.unpack('<H',t[q:q+2])[0];q+=2;e=t.index(b'\0',q);names[cid]=t[q:e].decode('utf8','replace');q=e+1
    elif code==8:jt=t
    elif code in (6,21,35,90):
      cid=struct.unpack('<H',t[:2])[0]
      if code==6:data=(jt or b'')+t[2:];alpha=None
      elif code==21:data=t[2:];alpha=None
      else:
        al=struct.unpack('<I',t[2:6])[0];q=6+(2 if code==90 else 0);data=t[q:q+al];alpha=t[q+al:]
      data=data.replace(b'\xff\xd9\xff\xd8',b'')
      try:
        im=Image.open(io.BytesIO(data));im.load();im=im.convert('RGBA')
        if alpha:
          try:
            a=zlib.decompress(alpha);im.putalpha(Image.frombytes('L',im.size,a[:im.size[0]*im.size[1]]))
          except Exception:pass
        imgs[cid]=im
      except Exception as e:pass
    elif code in (20,36):
      cid,fmt,w,h=struct.unpack('<HBHH',t[:7]);q=7
      if fmt==3:ct=t[q]+1;q+=1
      raw=zlib.decompress(t[q:])
      try:
        if fmt==5:
          px=bytearray(w*h*4)
          for i in range(w*h):
            a,r,g,b=raw[i*4:i*4+4]
            if code==36 and a: r,g,b=min(255,r*255//a),min(255,g*255//a),min(255,b*255//a)
            px[i*4:i*4+4]=bytes((r,g,b,a if code==36 else 255))
          imgs[cid]=Image.frombytes('RGBA',(w,h),bytes(px))
        elif fmt==3:
          cs=4 if code==36 else 3;pal=raw[:ct*cs];pw=(w+3)&~3;idx=raw[ct*cs:]
          im=Image.new('RGBA',(w,h))
          P=[tuple(pal[i*cs:i*cs+cs])+((255,) if cs==3 else ()) for i in range(ct)]
          im.putdata([P[idx[y*pw+x]] if idx[y*pw+x]<ct else (0,0,0,0) for y in range(h) for x in range(w)]);imgs[cid]=im
      except Exception as e:pass
  for cid,im in imgs.items():
    nm=names.get(cid,'');fn=f'{cid:05d}'+('_'+''.join(c if c.isalnum() or c in '_-' else '_' for c in nm) if nm else '')+'.png'
    im.save(os.path.join(out,fn))
  print(p,'sig',sig,'ver',ver,'offset',off,'images',len(imgs),'named',sum(1 for c in imgs if c in names),'tagcounts',{k:v for k,v in sorted(cnt.items()) if k in (6,8,20,21,35,36,90,56,76,87)})
if __name__=='__main__':extract(sys.argv[1],sys.argv[2])
