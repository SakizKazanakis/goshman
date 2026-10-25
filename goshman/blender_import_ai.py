"""Blender headless bridge: a REAL externally generated GLB -> editable BLEND.

Run with: blender -b -t 2 --python goshman/blender_import_ai.py --
  --source model.glb --destination imported_character.blend --height 6.2

Does not invent a skeleton, material bake or claim fidelity to references.
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


def import_glb(source: Path, destination: Path, character_height: float) -> dict:
    if not source.is_file() or source.stat().st_size < 100:
        raise ValueError("Input must be a nonempty GLB asset")
    if source.suffix.lower() != ".glb":
        raise ValueError("Input must be a .glb file")
    if not (0.1 <= character_height <= 100.0):
        raise ValueError("Character height outside allowed range")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objects:
        raise ValueError("Imported GLB contains no polygon mesh")
    for obj in objects:
        if not len(obj.data.vertices) or not len(obj.data.polygons):
            raise ValueError("Imported GLB contains an empty mesh")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners=[]
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        for vertex in evaluated.bound_box:
            corners.append(evaluated.matrix_world @ Vector(vertex))
    min_z=min(v.z for v in corners)
    max_z=max(v.z for v in corners)
    height=max_z-min_z
    if height <= 0 or not math.isfinite(height):
        raise ValueError("Invalid vertical dimensions of imported mesh")
    original_roots=[obj for obj in bpy.context.scene.objects if obj.parent is None]
    root=bpy.data.objects.new("GOSHMAN_AI_Character_ROOT",None)
    bpy.context.collection.objects.link(root)
    for obj in original_roots:
        if obj == root:
            continue
        matrix=obj.matrix_world.copy()
        obj.parent=root
        obj.matrix_world=matrix
    factor=character_height/height
    root.scale=(factor,)*3
    root.location=(0,0,-factor*min_z)
    mesh_count=len(objects)
    face_count=sum(len(obj.data.polygons) for obj in objects)
    vert_count=sum(len(obj.data.vertices) for obj in objects)
    materials={mat.name for obj in objects for mat in obj.data.materials if mat}
    rig_objects=[obj for obj in bpy.context.scene.objects if obj.type=="ARMATURE"]
    destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    if not destination.is_file() or destination.stat().st_size < 100:
        raise RuntimeError("Blender failed to save output scene")
    report={
        "status":"PASS_TECHNICAL",
        "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "file":str(destination),
        "mesh_objects":mesh_count,
        "vertices":vert_count,
        "faces":face_count,
        "materials":len(materials),
        "imported_armatures":len(rig_objects),
        "applied_character_scale":factor,
        "requested_height":character_height,
        "blender_version":bpy.app.version_string,
        "visual_fidelity_verified":False,
        "mechanical_rig_verified":False,
        "cycles_bake_verified":False,
    }
    destination.with_suffix(".json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--destination",type=Path,required=True)
    parser.add_argument("--height",type=float,default=6.2)
    x=parser.parse_args(args)
    print(json.dumps(import_glb(x.source.resolve(strict=True),
                                x.destination.resolve(),x.height),indent=2))


if __name__=="__main__":
    main()
