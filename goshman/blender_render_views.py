"""Render a real 3D mesh from five controlled orthographic camera directions.

Deterministic external visual inspection; NOT photogrammetric fitting and NOT
proof of resemblance to artistic reference sheets.
Blender CLI:
blender --background --factory-startup --python-exit-code 31 --python goshman/blender_render_views.py -- --model file.glb --output views
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


CAMERAS = {
    "front": (0.0, -1.0, 0.0),
    "left": (-1.0, 0.0, 0.0),
    "back": (0.0, 1.0, 0.0),
    "right": (1.0, 0.0, 0.0),
    "three_quarter": (-0.8, -1.0, 0.2),
}


def render_views(model: Path, output: Path, *, width: int = 320,
                 height: int = 640, samples: int = 4) -> dict:
    model=Path(model).resolve(strict=True)
    output=Path(output).resolve()
    if model.suffix.lower() not in (".glb", ".blend"):
        raise ValueError("Only validated GLB or Blender model files may be rendered")
    if not (128<=width<=2048 and 128<=height<=4096 and 1<=samples<=128):
        raise ValueError("Invalid resolution or sample limit")
    if model.suffix.lower()==".blend":
        bpy.ops.wm.open_mainfile(filepath=str(model))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(model))
    parts=[obj for obj in bpy.context.scene.objects if obj.type=="MESH" and obj.visible_get()]
    if not parts:
        raise RuntimeError("No visible geometry for the controlled view render")
    corners=[]
    graph=bpy.context.evaluated_depsgraph_get()
    for part in parts:
        evaluated=part.evaluated_get(graph)
        corners.extend(evaluated.matrix_world @ Vector(p) for p in evaluated.bound_box)
    if not corners:
        raise RuntimeError("Model has no bounding geometry")
    mins=Vector([min(p[i] for p in corners) for i in range(3)])
    maxs=Vector([max(p[i] for p in corners) for i in range(3)])
    sizes=maxs-mins
    center=(mins+maxs)*0.5
    if min(sizes)<0 or not all(math.isfinite(v) for v in sizes):
        raise RuntimeError("Geometry contains invalid coordinates")
    scene=bpy.context.scene
    for cam in [obj for obj in scene.objects if obj.type=="CAMERA"]:
        bpy.data.objects.remove(cam,do_unlink=True)
    camera_data=bpy.data.cameras.new("GOSHMAN_QA_ORTHOGRAPHIC")
    camera=bpy.data.objects.new("GOSHMAN_QA_ORTHOGRAPHIC",camera_data)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera_data.type="ORTHO"
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=samples
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.film_transparent=True
    # Render-time linear lighting; images stay reference-independent.
    world=bpy.data.worlds.new("GOSHMAN_QA_LIGHT") if not scene.world else scene.world
    scene.world=world
    world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value=(.4,.4,.4,1)
        bg.inputs["Strength"].default_value=.85
    for name,pos,energy in (("GOSHMAN_QA_KEY",(3,-4,7),850),
                            ("GOSHMAN_QA_FILL",(-4,-2,5),600)):
        light=bpy.data.lights.new(name,"AREA")
        light.energy=energy
        light.shape="DISK"
        light.size=6.0
        obj=bpy.data.objects.new(name,light)
        scene.collection.objects.link(obj)
        obj.location=center+Vector(pos)
    output.mkdir(parents=True,exist_ok=True)
    radius=max(float(sizes.length)*2,4)
    result={}
    for name,unit in CAMERAS.items():
        direction=Vector(unit).normalized()
        camera.location=center+direction*radius
        camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
        # Fit each projected camera silhouette independently; the long tail
        # must not make front/back views unnecessarily tiny.
        local_rotation=camera.rotation_euler.to_matrix().inverted()
        projected=[local_rotation @ (corner-center) for corner in corners]
        projected_width=max(v.x for v in projected)-min(v.x for v in projected)
        projected_height=max(v.y for v in projected)-min(v.y for v in projected)
        camera_data.ortho_scale=max(projected_height*1.16,
                                    projected_width*height/width*1.16,1.0)
        target=output/(name+".png")
        scene.render.filepath=str(target)
        bpy.ops.render.render(write_still=True)
        if not target.exists() or target.stat().st_size<100:
            raise RuntimeError("Blender rendered empty view "+name)
        result[name]={"image":target.name,
                      "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                      "bytes":target.stat().st_size}
    manifest={
        "status":"PASS_RENDER_TECHNICAL",
        "source_model":model.name,
        "source_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),
        "camera_type":"ORTHO",
        "camera_axis_convention":"+Z up, front=-Y, left=-X, back=+Y, right=+X",
        "views":result,
        "resolution":[width,height],
        "object_count":len(parts),
        "bounds":[list(mins),list(maxs)],
        "visual_fidelity_verified":False,
        "artist_reference_cameras_calibrated":False,
    }
    (output/"render_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest


def main():
    arguments=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--width",type=int,default=320)
    parser.add_argument("--height",type=int,default=640)
    parser.add_argument("--samples",type=int,default=4)
    args=parser.parse_args(arguments)
    print(json.dumps(render_views(args.model,args.output,
          width=args.width,height=args.height,samples=args.samples),indent=2))


if __name__=="__main__":
    main()
