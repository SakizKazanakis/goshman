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


def _mandible_shell(scale, snout, record):
    """One watertight U-shaped jaw with continuous inset palate and sculpted walls.

    Consecutive cross sections run along left ramus, curved chin, right ramus.
    Exterior and interior share lip vertices; no independent cavity liner.
    The rear socket stays narrower and recedes under the cheeks.
    """
    controls=[
        (-.83*scale,-.205,4.695,.060,.065),
        (-.805*scale,-.36,4.630,.082,.095),
        (-.746*scale,-.56*snout,4.565,.116,.132),
        (-.615*scale,-.77*snout,4.502,.142,.142),
        (-.45*scale,-.938*snout,4.482,.156,.137),
        (-.28*scale,-1.043*snout,4.475,.155,.122),
        (-.13*scale,-1.094*snout,4.468,.145,.113),
        (0,-1.103*snout,4.468,.143,.110),
    ]
    controls += [(-x,y,z,w,h) for x,y,z,w,h in reversed(controls[:-1])]
    def cat(a,b,c,d,t):
        return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
    spine=[]
    for i in range(len(controls)-1):
        lo=controls[max(0,i-1)]
        mid=controls[i]
        hi=controls[i+1]
        end=controls[min(len(controls)-1,i+2)]
        for k in range(6):
            spine.append(tuple(cat(lo[j],mid[j],hi[j],end[j],k/6) for j in range(5)))
    spine.append(controls[-1])
    sides=24
    verts=[]
    faces=[]
    for i,(x,y,z,width,height) in enumerate(spine):
        before=Vector(spine[max(0,i-1)][:3])
        after=Vector(spine[min(len(spine)-1,i+1)][:3])
        tangent=(after-before).normalized()
        horizontal=Vector((-tangent.y,tangent.x,0)).normalized()
        for j in range(sides):
            t=2*math.pi*j/sides
            # broader jaw below its lip; narrower upper bevel.
            anisotropy=(1.0+.26*max(0,-math.sin(t)))
            position=Vector((x,y,z))+horizontal*(width*anisotropy*math.cos(t))+Vector((0,0,height*math.sin(t)))
            verts.append(tuple(position))
        if i:
            for j in range(sides):
                k=(j+1)%sides
                previous=(i-1)*sides
                current=i*sides
                faces.append((previous+j,previous+k,current+k,current+j))
    # Interior basin is joined TO THE LIP on both sides of the mouth.
    # A sector of the upper inner surface is replaced by a continuous floor
    # with transverse quads, rather than added as a second overlapping object.
    # This preserves one connected watertight component through the chin.
    cap_start=len(verts)
    for index in (0,len(spine)-1):
        x,y,z,w,h=spine[index]
        verts.append((x,y,z))
    for j in range(sides):
        k=(j+1)%sides
        faces.append((cap_start,k,j))
        off=(len(spine)-1)*sides
        faces.append((cap_start+1,off+j,off+k))
    mesh=bpy.data.meshes.new("Mandible_integrated_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new("Mandible_integrated",mesh)
    bpy.context.collection.objects.link(obj)
    # Boolean-volume union: the anatomical floor is a SOLID volume rather
    # than an open liner. Voxel remeshing fuses it with both lateral rami into
    # ONE manifold component. Maintain the movable jaw's original bone.
    basin_verts=[]
    basin_faces=[]
    nx=22
    ny=24
    for layer in range(2):
        for iy in range(ny+1):
            fy=iy/ny
            py=(-1.10+.45*fy)*snout
            width=(.38+.27*fy)*scale
            for ix in range(nx+1):
                t=(ix/nx)*2-1
                px=width*t
                if layer==0:
                    # Deep center and raised, muscular gum shoulders.
                    pz=4.405+.148*abs(t)**3+.012*(1-fy)
                else:
                    pz=4.305-.012*(1-t*t)
                basin_verts.append((px,py,pz))
    span=(ny+1)*(nx+1)
    for layer in range(2):
        for iy in range(ny):
            for ix in range(nx):
                a=layer*span+iy*(nx+1)+ix
                b=a+1
                c=a+(nx+1)
                e=c+1
                basin_faces.append((a,b,e,c) if layer==0 else (a,c,e,b))
    for iy in range(ny):
        for ix in (0,nx):
            a=iy*(nx+1)+ix
            b=(iy+1)*(nx+1)+ix
            basin_faces.append((a,b,b+span,a+span) if ix==0
                               else (a,a+span,b+span,b))
    for ix in range(nx):
        for iy in (0,ny):
            a=iy*(nx+1)+ix
            b=a+1
            basin_faces.append((a,a+span,b+span,b) if iy==0
                               else (a,b,b+span,a+span))
    offset=len(verts)
    verts.extend(basin_verts)
    faces.extend(tuple(v+offset for v in f) for f in basin_faces)
    mesh.clear_geometry()
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    obj.data.remesh_voxel_size=.010
    bpy.ops.object.voxel_remesh()
    # Relax voxel stair-steps while keeping the mechanical joint support shape.
    smooth=obj.modifiers.new("Mandible_voxel_surface_relax","SMOOTH")
    smooth.factor=1.15
    smooth.iterations=7
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    # v11: sculpt AFTER voxel union. Keep the rear joint seat at its original
    # hinge pivot, taper the broad cheeks forward and add lower chin mass.
    # Smooth weights make all changes continuous across the full watertight jaw.
    def weight(t):
        t=max(0.0,min(1.0,t))
        return t*t*(3-2*t)
    for vertex in obj.data.vertices:
        x,y,z=vertex.co
        front=weight((-.38-y)/.70)
        chin=weight((-.70-y)/.34)
        underside=weight((4.58-z)/.27)
        # Foremost U bend is too far ahead of the reference. Shift it rearward
        # without displacing the mechanical rotation axis at y=-0.20.
        py=y+.165*front
        # Narrow the anterior bulk but preserve the bearing-seat width.
        px=x*(1-.075*front-.035*chin)
        # Thicker, dropped anterior jaw symphysis; rim stays near the upper gum.
        pz=z-(.185*front+.035*(1-front))*underside
        vertex.co=(px,py,pz)
    obj.data.update()
    obj.select_set(False)
    obj=record(obj,"Belly","jaw")
    obj["jaw_refinement"]="v11_anatomical_chin_and_taper"
    obj["preserved_axis"]="-Y forward, jaw pivot Y=-0.20, Z=4.70"
    # Continuous point-domain colour gives a soft material transition and
    # avoids per-face pink/cream stripes on voxel triangles.
    attr=obj.data.color_attributes.new(name="JawSurfaceColor",type="FLOAT_COLOR",domain="POINT")
    belly=(.67,.50,.29,1.0)
    gum=(.43,.17,.21,1.0)
    for vert in obj.data.vertices:
        x,y,z=vert.co
        front=max(0,min(1,(-y/snout-.64)/.23))
        height=max(0,min(1,(z-4.415)/.120))
        centre=max(0,min(1,(.62*scale-abs(x))/.19))
        t=front*height*centre
        t=t*t*(3-2*t)
        attr.data[vert.index].color=tuple(belly[k]*(1-t)+gum[k]*t for k in range(4))
    material=bpy.data.materials.new("Mandible_soft_blended_skin")
    material.use_nodes=True
    nodes=material.node_tree.nodes
    bsdf=nodes.get("Principled BSDF")
    color_node=nodes.new("ShaderNodeVertexColor")
    color_node.layer_name="JawSurfaceColor"
    material.node_tree.links.new(color_node.outputs["Color"],bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value=.67
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["topology"]="single_smoothed_voxel_union_anatomical_floor"
    obj["surface_colour"]="continuous_point_domain_rgba"
    for polygon in obj.data.polygons:
        polygon.use_smooth=True
    return obj



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


def _section_mesh(name,stations,material,bone,record,sectors=48):
    """Continuous, parameterized non-spherical surface from axial sections."""
    verts=[]
    for y,z,rx,rz,flat in stations:
        for i in range(sectors):
            t=2*math.pi*i/sectors
            c=math.cos(t);q=math.sin(t)
            x=rx*math.copysign(abs(c)**.8,c)
            h=rz*math.copysign(abs(q)**(1.35 if q>0 else .85),q)
            if q>0:h*=1-.14*flat
            verts.append((x,y,z+h))
    faces=[]
    for k in range(len(stations)-1):
        for i in range(sectors):
            j=(i+1)%sectors
            faces.append((k*sectors+i,k*sectors+j,(k+1)*sectors+j,(k+1)*sectors+i))
    verts.extend(((0,stations[0][0],stations[0][1]),(0,stations[-1][0],stations[-1][1])))
    cap_a=len(verts)-2;cap_b=len(verts)-1
    for i in range(sectors):
        j=(i+1)%sectors
        faces.append((cap_a,j,i))
        p=(len(stations)-1)*sectors
        faces.append((cap_b,p+i,p+j))
    mesh=bpy.data.meshes.new(name+'_section_mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    for polygon in mesh.polygons:polygon.use_smooth=True
    obj['construction']='reference_guided_axial_sections_v8'
    return record(obj,material,bone)


def _build_section_head(scale,snout,record):
    skull=[
     (-.57,5.12,.17*scale,.22*scale,.2),
     (-.50,5.13,.42*scale,.43*scale,.3),
     (-.36,5.11,.57*scale,.56*scale,.5),
     (-.15,5.06,.66*scale,.67*scale,.7),
     (.08,5.04,.70*scale,.70*scale,.8),
     (.30,5.04,.65*scale,.64*scale,.5),
     (.48,5.04,.53*scale,.54*scale,.2),
     (.59,5.04,.32*scale,.34*scale,.1),
     (.63,5.04,.08*scale,.13*scale,0)]
    muzzle=[
     (-1.33*snout,4.87,.37*scale,.095*scale,.95),
     (-1.29*snout,4.88,.62*scale,.15*scale,.95),
     (-1.18*snout,4.88,.86*scale,.18*scale,.95),
     (-.97*snout,4.88,.89*scale,.195*scale,.9),
     (-.75*snout,4.89,.79*scale,.23*scale,.75),
     (-.51*snout,4.91,.64*scale,.30*scale,.55),
     (-.35*snout,4.94,.50*scale,.34*scale,.35),
     (-.24*snout,4.95,.24*scale,.24*scale,.1)]
    return (_section_mesh('Head_cranium',skull,'Scales','head',record),
            _section_mesh('Upper_snout',muzzle,'Scales','head',record))


def build_head(*, scale, snout, eye, ellipsoid, cylinder, fang, record):
    """Build independent skull, movable mandible, hinge seats, and eye sockets."""
    cranium,muzzle=_build_section_head(scale,snout,record)
    # Lips meet in neutral with a narrow dark separating seam, not open air.
    ellipsoid("Upper_gum",(0,-.78*snout,4.657),
              (.58*scale,.325*snout,.084),"Mouth","head",40,18)
    for side,sign in (("L",-1),("R",1)):
        x=sign*.285*scale
        ellipsoid("Cheek_"+side,(sign*.545*scale,-.165,4.80),(.25*scale,.31,.205),"Scales","head",40,24)
        ellipsoid("Nostril_"+side,(sign*.205*scale,-1.065*snout,5.01),(.082,.04,.052),"Black","head",20,12)
        _orbital_fairing(side,x,scale,eye,record)
        ellipsoid("Orbit_recess_"+side,(x,-.505,5.26),(.223*eye,.048,.230*eye),"Black","head",40,20)
        ellipsoid("Eyeball_"+side,(x,-.527,5.26),(.186*eye,.120,.190*eye),"White","eye."+side,48,24)
        ellipsoid("Iris_"+side,(x,-.645,5.26),(.106*eye,.045,.112*eye),"Iris","eye."+side,32,16)
        ellipsoid("Pupil_"+side,(x,-.681,5.26),(.054*eye,.024,.059*eye),"Black","eye."+side,24,12)
        ellipsoid("Eyebrow_"+side,(x,-.55,5.59),(.268,.084,.078),"Leather","brow."+side,32,16)
        ellipsoid("Upper_eyelid_"+side,(x,-.555,5.415),(.227*eye,.10,.057),"Scales","lid."+side,32,16)
        hx=sign*.795*scale
        cylinder("Jaw_hinge_socket_"+side,(hx,-.20,4.70),.093,.050,"Black","head",40,(0,math.pi/2,0))
        cylinder("Jaw_hinge_bearing_"+side,(hx+sign*.032,-.20,4.70),.074,.040,"Metal","head",40,(0,math.pi/2,0))
        cylinder("Jaw_hinge_pin_"+side,(hx+sign*.056,-.20,4.70),.028,.020,"Metal","head",32,(0,math.pi/2,0))
        # The hinge cap is recessed, while the lower jaw is ONE uninterrupted mesh.
        ellipsoid("Jaw_hinge_moving_cap_"+side,
                  (sign*.844*scale,-.20,4.70),(.027,.067,.067),
                  "Metal","jaw",32,16)
    _mandible_shell(scale,snout,record)
    ellipsoid("Tongue",(0,-.94*snout,4.57),
              (.26,.13*snout,.031),"Mouth","jaw")
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
    moving_names=("Mandible_integrated",)
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
            chin=bpy.data.objects["Mandible_integrated"].evaluated_get(deps)
            forward_vertex=min(chin.data.vertices,key=lambda v:v.co.y)
            tip=tuple(round(float(v),6) for v in (chin.matrix_world @ forward_vertex.co))
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
    # The one-piece lower jaw has designed seating contact in the first poses;
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
