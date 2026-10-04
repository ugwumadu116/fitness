# atlas = [front | back], body colours bled into the background so silhouette edges never sample grey
import sys, json, numpy as np
sys.path.insert(0,'..'); from joints2d import silhouette
from PIL import Image, ImageFilter
def bleed(a,m):
    m=np.asarray(Image.fromarray((m*255).astype('uint8')).filter(ImageFilter.MinFilter(5))).astype(float)/255
    out=a.astype(float).copy(); known=m.copy()
    for r in (4,8,16,32,64,128,256):
        num=np.stack([np.asarray(Image.fromarray(np.clip(out[...,c]*known,0,255).astype('uint8')).filter(ImageFilter.BoxBlur(r))).astype(float) for c in range(3)],-1)
        den=np.asarray(Image.fromarray((known*255).astype('uint8')).filter(ImageFilter.BoxBlur(r))).astype(float)/255
        newk=(den>0.02)&(known<0.5); out[newk]=(num/np.maximum(den,1e-3)[...,None])[newk]; known=np.maximum(known,newk.astype(float))
    return np.clip(out*1.08,0,255).astype('uint8')
n=sys.argv[1]; meta={}
halves=[]
for tag,f in (('front',f'{n}.png'),('back',f'{n}b.png')):
    a,m=silhouette(f); H,W=m.shape
    rows=m.sum(1); ys=[y for y in range(H) if rows[y]>W*0.02]; y0,y1=ys[0],ys[-1]
    xs=np.where(m[y0:int(y0+0.7*(y1-y0))].any(0))[0]   # fingertips are the widest point in an A-pose
    meta[tag]=dict(W=W,H=H,x0=int(xs.min()),x1=int(xs.max()),y0=int(y0),y1=int(y1))
    halves.append(Image.fromarray(bleed(a,m)))
W,H=halves[0].size
atlas=Image.new('RGB',(W*2,H)); atlas.paste(halves[0],(0,0)); atlas.paste(halves[1].resize((W,H)),(W,0))
atlas.resize((2048,int(2048*H/(2*W))),Image.LANCZOS).save(f'{n}-atlas.jpg',quality=86)
json.dump(meta,open(f'{n}-atlas.json','w')); print(n,meta)
