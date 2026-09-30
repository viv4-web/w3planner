"""Extract textures from a Witcher 3 texture.cache to PNG.
Usage: python w3tex.py <texture.cache> <output_folder> [filter ...]
Filters are case-insensitive substrings of the internal path (e.g. icons\\skills gui).
Requires: pip install pillow
"""
import struct, sys, os, zlib, io
from PIL import Image

FMT = {0x07:b'DXT1',0x08:b'DXT5',0x0D:b'DXT3',0x0A:'BC7',0x0E:'BC4',0x0F:'BC5',0x00:'RGBA',0xFD:'RGBA'}

def read_index(path):
    f = open(path,'rb'); f.seek(-32,2)
    crc,used,count,strsize,mipcount,magic,ver = struct.unpack('<QIIIIII', f.read(32))
    if magic != 1415070536: raise SystemExit('Not a texture.cache (bad magic)')
    f.seek(-(32 + count*52 + strsize + mipcount*4), 2)
    f.read(mipcount*4)
    names = f.read(strsize).split(b'\0')[:count]
    f.seek(-(32 + count*52), 2)
    entries = []
    for i in range(count):
        e = struct.unpack('<IiIIIIHHHHiiqBBBB', f.read(52))
        entries.append(dict(name=names[i].decode('utf-8','replace'), page=e[2], align=e[5], w=e[6], h=e[7],
                            mips=e[8], slices=e[9], nmipoff=e[11], t1=e[13], cube=e[15]))
    return f, entries

def dds_header(w,h,fourcc,dx10fmt=None,rgba=False,linear=0):
    flags=0x1|0x2|0x4|0x1000
    if rgba:
        pf=struct.pack('<II4sIIIII',32,0x41,b'\0\0\0\0',32,0xff,0xff00,0xff0000,0xff000000)
    elif dx10fmt:
        pf=struct.pack('<II4sIIIII',32,0x4,b'DX10',0,0,0,0,0)
    else:
        pf=struct.pack('<II4sIIIII',32,0x4,fourcc,0,0,0,0,0)
    hdr=b'DDS '+struct.pack('<IIIIIII',124,flags,h,w,linear,0,1)+b'\0'*44+pf+struct.pack('<IIIII',0x1000,0,0,0,0)
    if dx10fmt: hdr+=struct.pack('<IIIII',dx10fmt,3,0,1,0)
    return hdr

def extract(f, e):
    f.seek(e['page']*4096); zsize,size,idx = struct.unpack('<IIB', f.read(9))
    data = zlib.decompress(f.read(zsize))      # top mip is enough
    fmt = FMT.get(e['t1'])
    w,h = e['w'],e['h']
    if fmt=='RGBA': return Image.frombytes('RGBA',(w,h),data[:w*h*4])
    if isinstance(fmt,bytes): hdr=dds_header(w,h,fmt)
    elif fmt=='BC7': hdr=dds_header(w,h,None,dx10fmt=98)
    elif fmt=='BC4': hdr=dds_header(w,h,b'ATI1')
    elif fmt=='BC5': hdr=dds_header(w,h,b'ATI2')
    else: raise ValueError('unknown format %x'%e['t1'])
    return Image.open(io.BytesIO(hdr+data)).convert('RGBA')

if __name__=='__main__':
    src,out=sys.argv[1],sys.argv[2]; filt=[s.lower() for s in sys.argv[3:]]
    f,entries=read_index(src)
    sel=[e for e in entries if not filt or any(s in e['name'].lower() for s in filt)]
    print(f'{len(entries)} textures in cache, {len(sel)} match')
    ok=bad=0
    for e in sel:
        if e['cube']: continue
        dst=os.path.join(out, os.path.splitext(e['name'].replace('\\','/'))[0]+'.png')
        os.makedirs(os.path.dirname(dst),exist_ok=True)
        try: extract(f,e).save(dst); ok+=1
        except Exception as ex: bad+=1; print('skip',e['name'],ex)
    print(f'saved {ok} PNGs to {out}' + (f', {bad} skipped' if bad else ''))
