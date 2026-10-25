"""Experimental image-derived 3D visual hull from private four-view project.

Not neural inference, photogrammetry, an accurate character, or an editable rig.
A real mesh is carved from source silhouette projections (no primitive blockout).
Dependencies are optional: pip install goshman[vision].
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from .project import atomic_json
from .reconstruction import load_views


def _mask(rgb):
    import numpy as np
    import cv2
    from scipy import ndimage
    image=np.ascontiguousarray(rgb,dtype=np.uint8)
    h,w,_=image.shape
    high=image.max(axis=2).astype(np.int16)
    low=image.min(axis=2).astype(np.int16)
    sat=high-low
    intensity=np.median(image.astype(np.int16),axis=2)
    foreground=(sat>17)|((intensity<150)&(sat>5))|(intensity<115)
    init=np.full((h,w),cv2.GC_PR_BGD,dtype=np.uint8)
    init[foreground]=cv2.GC_PR_FGD
    init[(sat>45)|((intensity<105)&(sat>12))]=cv2.GC_FGD
    init[(sat<8)&(intensity>166)]=cv2.GC_BGD
    init[:3,:]=cv2.GC_BGD
    init[-2:,:]=cv2.GC_BGD
    try:
        cv2.grabCut(cv2.cvtColor(image,cv2.COLOR_RGB2BGR),init,None,
                    np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),
                    4,cv2.GC_INIT_WITH_MASK)
        mask=np.isin(init,(cv2.GC_FGD,cv2.GC_PR_FGD))
    except cv2.error:
        mask=foreground
    mask=cv2.morphologyEx(mask.astype(np.uint8),cv2.MORPH_CLOSE,
                         np.ones((5,5),np.uint8),iterations=1)
    num,components,stats,centres=cv2.connectedComponentsWithStats(mask,8)
    if num>1:
        best=max(range(1,num),key=lambda j: stats[j,cv2.CC_STAT_AREA]-
                 .02*abs(centres[j,0]-w*.5)*h)
        mask=components==best
    return ndimage.binary_fill_holes(mask)


def build_visual_hull(folder:Path, output:Path, *,
                      grid_x:int=100,grid_y:int=110,grid_z:int=192)->dict:
    """Generate an experimental coloured GLB from verified private multiview files.

    Axis depth, absolute size and colours are illustrative. No AI service runs.
    """
    import numpy as np
    from scipy import ndimage
    from skimage.measure import marching_cubes
    import trimesh

    if not (40<=grid_x<=160 and 40<=grid_y<=160 and 60<=grid_z<=256):
        raise ValueError("Voxel resolution outside safe bounds")
    folder=Path(folder).resolve(strict=True)
    output=Path(output).resolve()
    sources=load_views(folder)
    names=("front","back","left","right")
    images={}; masks={}; source_info={}
    for name in names:
        path=sources[name]
        with Image.open(path) as image:
            rgb=np.array(image.convert("RGB"))
        images[name]=rgb
        masks[name]=_mask(rgb)
        if masks[name].sum()<300:
            raise ValueError("Unable to identify meaningful character silhouette: "+name)
        source_info[name]={"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                           "size":list(rgb.shape[:2][::-1]),
                           "foreground_pixels":int(masks[name].sum())}
    output.mkdir(parents=True,exist_ok=True)
    for name in names:
        Image.fromarray(masks[name].astype(np.uint8)*255).save(output/(name+"_mask.png"))
    xs=np.linspace(0,1,grid_x)
    ys=np.linspace(0,1,grid_y)
    zs=np.linspace(0,1,grid_z)
    def projection(mask,axes):
        h,w=mask.shape
        row=np.clip(np.rint((1-zs)*(h-1)).astype(np.int32),0,h-1)
        col=np.clip(np.rint(axes*(w-1)).astype(np.int32),0,w-1)
        return mask[row[:,None],col[None,:]].T
    front=projection(masks["front"],xs)
    back=projection(masks["back"],1-xs)
    left=projection(masks["left"],ys)
    right=projection(masks["right"],1-ys)
    # Artistic views are not calibrated or 1:1 aligned. OR combines alternate
    # silhouettes; AND carves orthogonal views. It is not accurate photo 3D.
    occupancy=(front|back)[:,None,:] & (left|right)[None,:,:]
    occupancy=ndimage.binary_closing(occupancy,np.ones((3,3,3),bool))
    if not occupancy.any():
        raise ValueError("Silhouette intersection is empty")
    verts,faces,_,_=marching_cubes(np.pad(occupancy.astype(np.uint8),1),level=.5)
    verts-=1
    verts[:,0]=(verts[:,0]/(grid_x-1)-.5)
    verts[:,1]=(verts[:,1]/(grid_y-1)-.5)*1.1
    verts[:,2]=verts[:,2]/(grid_z-1)*2.0
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
    trimesh.repair.fix_normals(mesh)
    colours=np.empty((len(verts),4),np.uint8)
    for i,(vertex,normal) in enumerate(zip(mesh.vertices,mesh.vertex_normals)):
        z=float(np.clip(1-vertex[2]/2,0,1))
        if abs(normal[1])>=abs(normal[0]):
            name="front" if normal[1]<0 else "back"
            pos=vertex[0]+.5
            if name=="back":
                pos=1-pos
        else:
            name="left" if normal[0]<0 else "right"
            pos=vertex[1]/1.1+.5
            if name=="right":
                pos=1-pos
        rgb=images[name];h,w,_=rgb.shape
        colours[i,:3]=rgb[int(np.clip(round(z*(h-1)),0,h-1)),
                           int(np.clip(round(pos*(w-1)),0,w-1))]
        colours[i,3]=255
    mesh.visual.vertex_colors=colours
    glb=output/"crocodile_multiview_silhouette_seed.glb"
    mesh.export(glb)
    actual=trimesh.load(glb,force="scene")
    if not actual.geometry:
        raise RuntimeError("GLB re-import found no polygon objects")
    report={
        "status":"PASS_IMAGE_DERIVED_GEOMETRY",
        "method":"non_neural_four_view_silhouette_visual_hull",
        "source_images":source_info,
        "model_name":glb.name,
        "model_sha256":hashlib.sha256(glb.read_bytes()).hexdigest(),
        "mesh":{"vertices":len(mesh.vertices),
                "triangles":len(mesh.faces),"watertight":bool(mesh.is_watertight)},
        "assumed_dimensions_m":[1.0,1.1,2.0],
        "ai_inference_executed":False,"privacy_upload_executed":False,
        "reference_fidelity_verified":False,
        "mechanical_rig_present":False,
        "limitations":["Artistic projections not camera calibrated",
                       "Hidden machinery not reconstructed",
                       "Colour is sampled from source pixels, not PBR baked",
                       "Not a neural 3D reconstruction or final character"]
    }
    atomic_json(output/"reconstruction_report.json",report)
    return report
