# find 2D joints for a front A-pose image from its silhouette
import numpy as np, json, sys
from PIL import Image, ImageDraw, ImageFilter
def silhouette(path):
    a=np.asarray(Image.open(path).convert('RGB')).astype(int); H,W,_=a.shape
    d=np.zeros((H,W))
    for y in range(H):
        bg=(a[y,:12].mean(0)+a[y,-12:].mean(0))/2; d[y]=np.abs(a[y]-bg).sum(1)
    m=d>38
    m=np.asarray(Image.fromarray((m*255).astype('uint8')).filter(ImageFilter.MedianFilter(7))).astype(bool)
    # keep only the body: the largest connected blob, holes filled
    from scipy import ndimage
    lab,n=ndimage.label(m)
    if n: m=lab==(np.bincount(lab.ravel())[1:].argmax()+1)

    return a,m
def runs(row):
    r=[];x=0;n=len(row)
    while x<n:
        if row[x]:
            s=x
            while x<n and row[x]: x+=1
            r.append((s,x-1))
        else: x+=1
    return r
def find(path):
    a,m=silhouette(path); H,W=m.shape
    ys,xs=np.where(m)
    y0=ys.min()
    # feet: lowest rows with substantial mass near the centre (ignore shadow speckle)
    rowsum=m.sum(1); y1=max(y for y in range(H) if rowsum[y]>W*0.02)
    h=y1-y0
    cols=xs[(ys>y0+0.3*h)&(ys<y0+0.5*h)]; cx=int(np.median(cols))
    # crotch: going up the centre column from the feet, first body pixel
    cy=next(y for y in range(int(y0+0.75*h),y0,-1) if m[y,cx-3:cx+4].all())
    J={}
    def legs_at(y):
        rr=[r for r in runs(m[y]) if r[1]-r[0]>8]
        L=[r for r in rr if (r[0]+r[1])/2>cx]; R=[r for r in rr if (r[0]+r[1])/2<cx]
        pick=lambda s,side: min(s,key=lambda r: abs((r[0]+r[1])/2-cx)) if s else None
        return pick(L,1),pick(R,-1)
    for name,frac in (('UpLeg',None),('Leg',0.47),('Foot',None)):
        pass
    ky=int(cy+0.47*(y1-cy)); ay=int(y1-0.05*h); hy=int(cy+0.02*h)
    for tag,y in (('Leg',ky),('Foot',ay),('UpLeg',hy)):
        l,r=legs_at(y)
        J['Left'+tag]=[(l[0]+l[1])/2,y]; J['Right'+tag]=[(r[0]+r[1])/2,y]
    J['LeftUpLeg'][1]=J['RightUpLeg'][1]=cy-0.035*h
    for s in ('Left','Right'):
        f=J[s+'Foot']; J[s+'ToeBase']=[f[0],y1-0.01*h]
    J['Hips']=[cx,cy-0.05*h]; J['Spine']=[cx,cy-0.11*h]; J['Spine1']=[cx,cy-0.19*h]; J['Spine2']=[cx,cy-0.27*h]
    J['Neck']=[cx,y0+0.165*h]; J['Head']=[cx,y0+0.13*h]; J['HeadTop_End']=[cx,y0]
    # arms: outermost run per row below the armpit; fit a line through their centres
    shy=y0+0.19*h
    for s,sgn in (('Left',1),('Right',-1)):
        pts=[]
        for y in range(int(y0+0.3*h), int(y0+0.62*h)):
            rr=[r for r in runs(m[y]) if r[1]-r[0]>4]
            if len(rr)<2: continue
            r=max(rr,key=lambda r:(r[0]+r[1])/2*sgn)
            if (r[0]+r[1])/2*sgn > cx*sgn+0.12*h: pts.append(((r[0]+r[1])/2,y,r[1]-r[0]))
        pts=np.array(pts)
        # fingertip = lowest outer point; wrist where the arm run is narrowest above the hand
        tip=pts[pts[:,1].argmax()]
        A=np.polyfit(pts[:,1],pts[:,0],1)
        wy=tip[1]-0.085*h; wx=np.polyval(A,wy)
        # shoulder: torso edge at shoulder height, inset by a quarter of the upper-arm width
        rr=runs(m[int(shy+0.03*h)]); edge=max(r[1] for r in rr) if sgn>0 else min(r[0] for r in rr)
        sx=edge-sgn*0.045*h
        J[s+'Arm']=[sx,shy+0.02*h]; J[s+'Shoulder']=[cx+sgn*0.04*h,shy-0.005*h]
        J[s+'Hand']=[wx,wy]; J[s+'HandEnd']=[tip[0],tip[1]]
        ey=(J[s+'Arm'][1]+wy)/2; J[s+'ForeArm']=[np.polyval(A,ey)-sgn*0.008*h if ey>pts[:,1].min() else (sx+wx)/2, ey]
    return a,m,J,(y0,y1,cx,cy)
if __name__=='__main__':
    out={}
    for n in sys.argv[1:]:
        a,m,J,meta=find(f'{n}.png'); out[n]={'J':{k:[float(v[0]),float(v[1])] for k,v in J.items()},'meta':[int(x) for x in meta]}
        im=Image.fromarray(a.astype('uint8')); d=ImageDraw.Draw(im)
        for k,(x,y) in J.items(): d.ellipse((x-9,y-9,x+9,y+9),fill=(255,60,0)); 
        im.resize((im.width//3,im.height//3)).save(f'{n}-joints.jpg')
    json.dump(out,open('joints2d.json','w'))
    print('ok')
