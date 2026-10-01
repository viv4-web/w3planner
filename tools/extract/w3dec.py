import struct,sys,csv
def bit6(f):
    res=0;shift=0;i=1
    while True:
        b=f.read(1)[0];s=6;mask=255
        if b>127:mask=127;s=7
        elif b>63 and i==1:mask=63
        if shift<32:res|=(b&mask)<<shift
        shift+=s
        if b<64 or (i>=3 and b<128):break
        i+=1
    return res
MAGIC={0x43975139:0x79321793}
def decode(path):
    f=open(path,'rb');data=f.read();import io;f=io.BytesIO(data)
    assert f.read(4)==b'RTSW';ver,=struct.unpack('<I',f.read(4));k1,=struct.unpack('<H',f.read(2))
    k2,=struct.unpack('<H',data[-2:]);magic=MAGIC[(k1<<16)|k2]
    n1=bit6(f);b1=[struct.unpack('<III',f.read(12)) for _ in range(n1)]
    n2=bit6(f);b2=[struct.unpack('<II',f.read(8)) for _ in range(n2)]
    n3=bit6(f);start=f.tell()
    ski=(magic>>8)&0xffff;strs={}
    bad=0
    utf8=ver>=164  # since the remaster (v164) strings are UTF-8: offset and length count bytes; before, UTF-16: they count 16-bit units
    for h,off,ln in b1:
        sid=h^magic;w=1 if utf8 else 2;p=start+off*w;k=ski
        if p+w*ln>len(data): bad+=1;continue
        out=bytearray()
        for j in range(ln):
            ck=((ln+1)*k)&0xffff
            if utf8: out.append(data[p+j]^(ck&0xff))
            else: out+=bytes([data[p+2*j]^(ck&0xff),data[p+2*j+1]^(ck>>8)])
            k=((k<<1)|(k>>15))&0xffff
        strs[sid]=out.decode('utf-8' if utf8 else 'utf-16-le',errors='replace')
    keys={kh:(sid^magic) for kh,sid in b2}
    end=start+n3*(1 if utf8 else 2)
    print('bad',bad,file=sys.stderr);print('version',ver,'strings',n1,'keys',n2,'string area ends',end,'file size',len(data),'extra bytes',len(data)-2-end,file=sys.stderr)
    return strs,keys
def h(key):
    x=0
    for c in key.lower().encode('utf-16-le')[::2]: x=(x*31+c)&0xffffffff
    return x
if __name__=="__main__":
    strs,keys=decode(sys.argv[1])
    import json
    json.dump({'strs':{str(k):v for k,v in strs.items()},'keys':{str(k):v for k,v in keys.items()}},open('strings.json','w'))
    for t in ['skill_rend_name','skill_rend_description','skill_far_reaching_aard_name','panel_character_skill_signs','skill_tree_name_survival']:
        sid=keys.get(h(t));print(t,'->',repr(strs.get(sid,'??'))[:300])
