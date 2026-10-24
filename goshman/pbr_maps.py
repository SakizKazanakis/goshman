"""Deterministic tileable UV PBR texture recipes for the animatronic blockout.

This is texture synthesis, not Cycles high-poly-to-low-poly baking nor 3D
reconstruction from reference photographs.
"""
from __future__ import annotations
import hashlib
import numpy as np

PROFILES = {
    "Scales": (.52, 0.0), "Belly": (.68, 0.0), "Leather": (.73, 0.0),
    "Metal": (.27, .9), "Gold": (.26, .75), "Mouth": (.8, 0.0),
    "Black": (.28, 0.0), "White": (.35, 0.0), "Iris": (.3, 0.0),
    "Sole": (.88, 0.0),
}

def _noise(n: int, rng: np.random.Generator, scale: int) -> np.ndarray:
    lattice = rng.random((scale, scale), dtype=np.float32)
    pos = np.arange(n, dtype=np.float32) * scale / n
    lo = np.floor(pos).astype(np.int32) % scale
    hi = (lo+1) % scale
    t = pos - np.floor(pos)
    t = t*t*(3-2*t)
    a = lattice[lo[:,None],lo[None,:]]
    b = lattice[hi[:,None],lo[None,:]]
    c = lattice[lo[:,None],hi[None,:]]
    d = lattice[hi[:,None],hi[None,:]]
    yy,xx = t[:,None],t[None,:]
    return (a*(1-yy)*(1-xx)+b*yy*(1-xx)+c*(1-yy)*xx+d*yy*xx).astype(np.float32)

def make_maps(material: str, hex_color: str, resolution: int = 512) -> dict[str,np.ndarray]:
    if material not in PROFILES:
        raise ValueError("Unknown PBR material: " + material)
    if not isinstance(resolution,int) or resolution < 64 or resolution > 2048 or resolution % 16:
        raise ValueError("PBR resolution must be divisible by 16 and in 64..2048")
    if len(hex_color) != 7 or not hex_color.startswith("#"):
        raise ValueError("Expected #RRGGBB")
    rgb = np.array([int(hex_color[j:j+2],16)/255.0 for j in (1,3,5)], dtype=np.float32)
    seed = int.from_bytes(hashlib.sha256((material+hex_color).encode()).digest()[:8],"little")
    rng = np.random.default_rng(seed)
    n=resolution
    coarse=_noise(n,rng,12)
    fine=_noise(n,rng,53)
    micro=rng.random((n,n),dtype=np.float32)
    height=0.3*coarse+0.25*fine+0.08*micro
    if material in ("Scales","Belly"):
        columns=8 if material=="Scales" else 3
        rows=11 if material=="Scales" else 12
        y,x=np.mgrid[0:n,0:n]
        row=np.floor(y*rows/n)
        xf=np.mod(x*columns/n+0.5*np.mod(row,2),1.0)
        yf=np.mod(y*rows/n,1.0)
        border=np.minimum.reduce([xf,1-xf,yf,1-yf])
        height+=np.clip(border*13.0,0.0,1.0)*(0.42 if material=="Scales" else 0.34)
    elif material=="Leather":
        height+=0.18*_noise(n,rng,94)
    elif material in ("Metal","Gold"):
        height+=0.12*_noise(n,rng,125)
    elif material=="Sole":
        yy,xx=np.mgrid[0:n,0:n]
        grooves=((xx%max(8,n//13))<max(2,n//150))|((yy%max(8,n//17))<max(2,n//150))
        height-=grooves.astype(np.float32)*0.30
    factor=np.clip(0.83+0.32*(height-height.mean())+0.12*(fine-0.5),0.64,1.2)
    base=np.clip(rgb[None,None,:]*factor[:,:,None],0,1)
    rough_base,metal_base=PROFILES[material]
    rough=np.clip(rough_base+0.16*(fine-0.5)+0.09*(micro-0.5),0.07,0.98)
    metal=np.full((n,n),metal_base,dtype=np.float32)
    dx=np.roll(height,-1,axis=1)-np.roll(height,1,axis=1)
    dy=np.roll(height,-1,axis=0)-np.roll(height,1,axis=0)
    strength=2.6 if material in ("Scales","Belly") else 0.9
    nx,ny,nz=-dx*strength,-dy*strength,np.ones_like(dx)
    norm=np.sqrt(nx*nx+ny*ny+nz*nz)
    normal=np.stack(((nx/norm+1)*0.5,(ny/norm+1)*0.5,(nz/norm+1)*0.5),axis=-1)
    def rgba(rgb_img):
        result=np.empty((n,n,4),dtype=np.float32)
        result[:,:,:3]=rgb_img
        result[:,:,3]=1.0
        return result
    def gray(v):
        return rgba(np.repeat(v[:,:,None],3,axis=2))
    return {"base_color":rgba(base),"roughness":gray(rough),
            "metallic":gray(metal),"normal":rgba(normal)}
