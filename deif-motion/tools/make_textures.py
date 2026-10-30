"""Generates paper textures, film grain frames and halftone/sticker versions of the portraits."""
import sys, numpy as np, cv2
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
root=sys.argv[1]; A=root+'/assets/'; SRC=root+'/sources/'
rng=np.random.default_rng(7)

def noise(h,w,scale):
    n=rng.random((max(2,h//scale),max(2,w//scale)))
    return cv2.resize(n,(w,h),interpolation=cv2.INTER_CUBIC)

def paper(w,h,base,dark=False):
    n=0.5*noise(h,w,240)+0.3*noise(h,w,60)+0.2*noise(h,w,8)
    fib=np.zeros((h,w),np.float32)
    for _ in range(1400):
        x,y=rng.integers(0,w),rng.integers(0,h); a=rng.random()*np.pi; L=rng.integers(8,40)
        cv2.line(fib,(x,y),(int(x+L*np.cos(a)),int(y+L*np.sin(a))),float(rng.random()),1)
    fib=cv2.GaussianBlur(fib,(3,3),0)
    img=np.zeros((h,w,3),np.float32)+np.array(base,np.float32)
    amp=18 if not dark else 10
    img+=((n-0.5)*amp*2)[...,None]
    img+=(fib*(-10 if not dark else 8))[...,None]
    # stains / vignette
    yy,xx=np.mgrid[0:h,0:w]; d=np.sqrt(((xx-w/2)/(w/2))**2+((yy-h/2)/(h/2))**2)
    img*= (1-0.18*np.clip(d-0.6,0,1))[...,None]
    for _ in range(5 if not dark else 0):
        cx,cy,r=rng.integers(0,w),rng.integers(0,h),rng.integers(80,260)
        m=np.clip(1-np.sqrt((xx-cx)**2+(yy-cy)**2)/r,0,1)**2
        img-= (m*np.array([10,16,26]))[...,None].transpose(0,1,2)[:,:,0,:] if False else (m[...,None]*np.array([8,14,24]))
    return Image.fromarray(np.clip(img,0,255).astype(np.uint8))

paper(1080,1920,(232,226,213)).save(A+'paper.jpg',quality=90)
paper(1080,1920,(22,21,20),dark=True).save(A+'paper_dark.jpg',quality=90)
paper(900,1200,(240,236,226)).save(A+'paper_card.jpg',quality=88)
paper(900,1200,(214,204,184)).save(A+'paper_old.jpg',quality=88)

# grain frames (transparent PNG, used with mix-blend overlay)
for i in range(6):
    g=rng.normal(128,40,(960,540)).clip(0,255).astype(np.uint8)
    g=cv2.resize(g,(1080,1920),interpolation=cv2.INTER_NEAREST)
    a=np.full_like(g,46)
    # occasional scratches
    for _ in range(rng.integers(1,4)):
        x=rng.integers(0,1080); cv2.line(g,(x,0),(x+rng.integers(-30,30),1920),255 if rng.random()<.5 else 0,1); 
    for _ in range(30):
        x,y=rng.integers(0,1080),rng.integers(0,1920); cv2.circle(g,(x,y),int(rng.integers(1,3)),0,-1)
    Image.fromarray(np.dstack([g,g,g,a])).save(A+f'grain_{i}.png')

def halftone_sticker(name, border=14, contrast=1.5, dot=5):
    im=Image.open(A+f'{name}_rgba.png').convert('RGBA')
    alpha=np.array(im.split()[3])
    g=ImageOps.grayscale(im.convert('RGB'))
    g=ImageOps.autocontrast(g,cutoff=1); g=ImageEnhance.Contrast(g).enhance(contrast)
    ga=np.array(g,np.float32)/255
    h,w=ga.shape
    # rotated dot screen, blended softly with the photo (newspaper print look)
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32); c,s=np.cos(np.pi/4),np.sin(np.pi/4)
    u=(xx*c-yy*s)/dot; v=(xx*s+yy*c)/dot
    dist=np.sqrt((u-np.round(u))**2+(v-np.round(v))**2)
    r=np.sqrt(np.clip(1-ga,0,1))*0.62
    dots=np.where(dist<r,0.0,1.0)
    out=0.55*ga+0.45*dots*np.clip(ga*1.3,0,1)
    out=(np.clip(out,0,1)*255).astype(np.uint8)
    # white sticker border
    pad=border+6
    A2=np.pad(alpha,pad); O2=np.pad(out,pad,constant_values=255)
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(border*2+1,border*2+1))
    edge=cv2.dilate((A2>128).astype(np.uint8)*255,k)
    edge=cv2.GaussianBlur(edge,(3,3),0)
    m=(A2.astype(np.float32)/255)
    rgb=O2.astype(np.float32)*m+250*(1-m)
    res=np.dstack([rgb,rgb,rgb*0.97,edge]).clip(0,255).astype(np.uint8)
    # drop shadow baked in
    sh=cv2.GaussianBlur(edge,(31,31),0)//3
    H2,W2=edge.shape; canvas=np.zeros((H2+24,W2+24,4),np.uint8)
    canvas[18:18+H2,12:12+W2,3]=sh
    base=Image.fromarray(canvas); base.alpha_composite(Image.fromarray(res),(6,6))
    base.save(A+f'{name}_ht.png')
    # plain grayscale cutout (no sticker) for crossfades
    Image.fromarray(np.dstack([out,out,out,alpha])).save(A+f'{name}_bw.png')

for n in ['portrait_main','portrait_tree','portrait_interview']: halftone_sticker(n)

sil=ImageOps.grayscale(Image.open(SRC+'silhouette.jpg').crop((30,40,880,860)))  # drop the search-icon corner
sil=ImageEnhance.Contrast(sil).enhance(1.4); sil.save(A+'silhouette_bw.jpg',quality=90)
print('textures ok')
