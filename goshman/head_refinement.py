"""Reference-guided mechanical head module for the GOSHMAN procedural crocodile.

Coordinates: X lateral, -Y forward, Z vertical. All values use the existing
6.2-unit character blockout, not physical millimetres. This module does not
claim photogrammetric reconstruction of the supplied artwork.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


JAW_PIVOT = (0.0, -0.20, 4.70)
JAW_MAX_OPEN = 0.95
JAW_SAMPLES = 33


def _tube(name, points, radii, material, bone, record, sides=16):
    """Smooth variable-radius closed tube between jaw hinge and chin."""
    centres = [Vector(p) for p in points]
    if len(centres) < 2 or len(centres) != len(radii):
        raise ValueError("Invalid mandibular rail")
    verts, faces = [], []
    for i, point in enumerate(centres):
        tangent = (centres[min(i+1,len(centres)-1)] -
                   centres[max(0,i-1)]).normalized()
        guide = Vector((0,0,1)) if abs(tangent.z)<.94 else Vector((1,0,0))
        u = tangent.cross(guide).normalized()
        v = tangent.cross(u).normalized()
        for j in range(sides):
            theta = 2*math.pi*j/sides
            verts.append(tuple(point + radii[i] *
                               (math.cos(theta)*u + math.sin(theta)*v)))
        if i:
            for j in range(sides):
                k = (j+1)%sides
                p = (i-1)*sides
                q = i*sides
                faces.append((p+j,p+k,q+k,q+j))
    verts.extend((tuple(centres[0]),tuple(centres[-1])))
    start_cap, end_cap = len(verts)-2,len(verts)-1
    for j in range(sides):
        k=(j+1)%sides
        faces.append((start_cap,k,j))
        p=(len(centres)-1)*sides
        faces.append((end_cap,p+j,p+k))
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    for face in obj.data.polygons:
        face.use_smooth=True
    return record(obj,material,bone)


def _orbital_fairing(side, x, scale, eye_scale, record):
    """Conforming quad-strip blending the visible socket rim into the cranium.

    Outer samples sit on the analytic cranium surface; the inner boundary
    advances to the globe. It remains stationary on the 'head' bone.
    """
    segments=64
    rings=(1.0,1.12,1.25,1.38)
    verts=[]
    cz=5.26
    for idx,r in enumerate(rings):
        for j in range(segments):
            theta=2*math.pi*j/segments
            px=x+(.246*eye_scale*r)*math.cos(theta)
            pz=cz+(.263*eye_scale*r)*math.sin(theta)
            radial=(px/(.68*scale))**2+((pz-5.03)/(.69*scale))**2
            surface_y=-.57*scale*math.sqrt(max(.025,1-radial))
            # Inner black reveal is recessed; outer lip follows the skin.
            alpha=idx/(len(rings)-1)
            py=(-.603*(1-alpha)+(.012+surface_y)*alpha)
            verts.append((px,py,pz))
    faces=[]
    for i in range(len(rings)-1):
        for j in range(segments):
            k=(j+1)%segments
            faces.append((i*segments+j,i*segments+k,
                          (i+1)*segments+k,(i+1)*segments+j))
    mesh=bpy.data.meshes.new("Eye_socket_skin_"+side+"_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new("Eye_socket_skin_"+side,mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth=True
    solid=obj.modifiers.new("Socket shell thickness","SOLIDIFY")
    solid.thickness=.018
    return record(obj,"Scales","head")


def build_head(*, scale, snout, eye, ellipsoid, cylinder, fang, record):
    """Build independent skull, movable mandible, hinge seats, and eye sockets."""
    ellipsoid("Head_cranium",(0,0,5.03),(.68*scale,.57*scale,.69*scale),
              "Scales","head",48,24)
    ellipsoid("Upper_snout",(0,-.57*snout,4.88),
              (.70*scale,.51*snout,.27*scale),"Scales","head",48,24)
    # Lips meet in neutral with a narrow dark separating seam, not open air.
    ellipsoid("Upper_gum",(0,-.78*snout,4.657),
              (.58*scale,.325*snout,.084),"Mouth","head",40,18)
    for side,sign in (("L",-1),("R",1)):
        x=sign*.35*scale
        ellipsoid("Cheek_"+side,(sign*.545*scale,-.165,4.80),(.25*scale,.31,.205),"Scales","head",40,24)
        ellipsoid("Nostril_"+side,(sign*.30*scale,-1.01*snout,5.01),(.082,.04,.052),"Black","head",20,12)
        _orbital_fairing(side,x,scale,eye,record)
        ellipsoid("Orbit_recess_"+side,(x,-.505,5.26),(.255*eye,.048,.260*eye),"Black","head",40,20)
        ellipsoid("Eyeball_"+side,(x,-.527,5.26),(.220*eye,.134,.225*eye),"White","eye."+side,48,24)
        ellipsoid("Iris_"+side,(x,-.645,5.26),(.118*eye,.049,.126*eye),"Iris","eye."+side,32,16)
        ellipsoid("Pupil_"+side,(x,-.681,5.26),(.060*eye,.025,.066*eye),"Black","eye."+side,24,12)
        ellipsoid("Eyebrow_"+side,(x,-.55,5.59),(.268,.084,.078),"Leather","brow."+side,32,16)
        ellipsoid("Upper_eyelid_"+side,(x,-.555,5.415),(.227*eye,.10,.057),"Scales","lid."+side,32,16)
        hx=sign*.795*scale
        cylinder("Jaw_hinge_socket_"+side,(hx,-.20,4.70),.093,.050,"Black","head",40,(0,math.pi/2,0))
        cylinder("Jaw_hinge_bearing_"+side,(hx+sign*.032,-.20,4.70),.074,.040,"Metal","head",40,(0,math.pi/2,0))
        cylinder("Jaw_hinge_pin_"+side,(hx+sign*.056,-.20,4.70),.028,.020,"Metal","head",32,(0,math.pi/2,0))
        rail=[
            (sign*.835*scale,-.205,4.695),
            (sign*.81*scale,-.34,4.622),
            (sign*.765*scale,-.54*snout,4.555),
            (sign*.635*scale,-.76*snout,4.49),
            (sign*.48*scale,-.92*snout,4.48),
            (sign*.32*scale,-1.015*snout,4.48),
            (sign*.16*scale,-1.055*snout,4.49),
        ]
        _tube("Jaw_ram_"+side,rail,(.054,.080,.112,.133,.137,.130,.120),"Belly","jaw",record,sides=24)
        ellipsoid("Jaw_hinge_moving_cap_"+side,(sign*.844*scale,-.20,4.70),(.027,.067,.067),"Metal","jaw",32,16)
    ellipsoid("Lower_jaw",(0,-.925*snout,4.41),(.49*scale,.188*snout,.090),"Belly","jaw",48,24)
    ellipsoid("Jaw_chin",(0,-1.037*snout,4.48),(.34*scale,.13*snout,.112),"Belly","jaw",48,24)
    ellipsoid("Lower_gum",(0,-.946*snout,4.541),(.43*scale,.175*snout,.045),"Mouth","jaw",40,18)
    ellipsoid("Tongue",(0,-.94*snout,4.56),(.27,.12*snout,.030),"Mouth","jaw")
    for i in range(9):
        x=(-.50+i*.125)*scale
        fang("Upper_tooth_%02d"%i,(x,-.94*snout,4.67),.052,.14,True,"head")
        fang("Lower_tooth_%02d"%i,(x,-.89*snout,4.55),.043,.10,False,"jaw")


def _world_bvh(obj, depsgraph):
    """Collision BVH in WORLD coordinates (not local coordinates of a bone child)."""
    evaluated=obj.evaluated_get(depsgraph)
    mesh=evaluated.to_mesh()
    try:
        coordinates=[tuple(evaluated.matrix_world@v.co) for v in mesh.vertices]
        faces=[tuple(poly.vertices) for poly in mesh.polygons]
        return BVHTree.FromPolygons(coordinates,faces,all_triangles=False)
    finally:
        evaluated.to_mesh_clear()


def jaw_sweep_audit(rig, *, output=None):
    """Check 33 poses across 0..0.95 rad with world-space triangle intersections.

    Excludes intentional pin-to-bearing contact and the explicitly joined
    mouth seam at closure. Reports all tested shell intersections rather than
    pretending zero-width art-directed seams are collision-free.
    """
    scene=bpy.context.scene
    data=rig.animation_data
    saved_action=data.action if data else None
    saved_frame=scene.frame_current
    jaw=rig.pose.bones["jaw"]
    saved_rotation=tuple(jaw.rotation_euler)
    skull_names=("Head_cranium","Upper_snout","Cheek_L","Cheek_R")
    moving_names=("Lower_jaw","Jaw_chin","Jaw_ram_L","Jaw_ram_R")
    poses=[]
    try:
        if data:
            data.action=None
        for step in range(JAW_SAMPLES):
            angle=JAW_MAX_OPEN*step/(JAW_SAMPLES-1)
            jaw.rotation_euler=(angle,0,0)
            bpy.context.view_layer.update()
            deps=bpy.context.evaluated_depsgraph_get()
            stationary={n:_world_bvh(bpy.data.objects[n],deps) for n in skull_names}
            mobile={n:_world_bvh(bpy.data.objects[n],deps) for n in moving_names}
            hits={}
            for a,static in stationary.items():
                for b,dynamic in mobile.items():
                    overlaps=static.overlap(dynamic)
                    if overlaps:
                        hits[a+"/"+b]=len(overlaps)
            # Ground-truth displacement of the chin's evaluated object origin.
            chin=bpy.data.objects["Jaw_chin"].evaluated_get(deps)
            tip=tuple(round(float(v),6) for v in chin.matrix_world.translation)
            poses.append({"angle_rad":round(angle,6),
                          "angle_deg":round(math.degrees(angle),3),
                          "chin_world":tip,
                          "surface_triangle_overlaps":hits})
    finally:
        jaw.rotation_euler=saved_rotation
        if data:
            data.action=saved_action
        scene.frame_set(saved_frame)
        bpy.context.view_layer.update()
    drop=poses[0]["chin_world"][2]-poses[-1]["chin_world"][2]
    # Lower jaw has designed seating contact in the first poses;
    # surface intersection counts are diagnostics requiring inspection.
    nonneutral=[p for p in poses[1:] if p["surface_triangle_overlaps"]]
    result={
        "samples":JAW_SAMPLES,
        "range_rad":[0,JAW_MAX_OPEN],
        "range_deg":[0,round(math.degrees(JAW_MAX_OPEN),3)],
        "chin_drop":round(drop,6),
        "skull_shells":list(skull_names),
        "jaw_shells":list(moving_names),
        "poses":poses,
        "collision_poses_beyond_neutral":len(nonneutral),
        "kinematically_opens_downward":drop>.20,
        "status":("PASS_NO_SHELL_INTERSECTION" if drop>.20 and not nonneutral
                  else "REVIEW_REQUIRED"),
        "note":"BVH triangle contacts include close seated surfaces; actual collisions "
               "must be assessed in the rendered hinge neighbourhood.",
    }
    if output:
        path=Path(output)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
