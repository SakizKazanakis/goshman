"""Head tooth-row collision diagnostic for an existing GOSHMAN .blend scene.

Run: blender --background crocodile_cowboy.blend --python tests/blender_tooth_contact.py
This measures only BVH triangle intersections, not minimum clearance distances.
"""
import bpy
import json
from mathutils.bvhtree import BVHTree

rig = bpy.data.objects["GOSHMAN_Rig"]
if rig.animation_data:
    rig.animation_data.action = None
jaw = rig.pose.bones["jaw"]
upper = [bpy.data.objects[f"Upper_tooth_{i:02d}"] for i in range(9)]
lower = [bpy.data.objects[f"Lower_tooth_{i:02d}"] for i in range(9)]

def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        points = [tuple(evaluated.matrix_world @ v.co) for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        return BVHTree.FromPolygons(points, faces)
    finally:
        evaluated.to_mesh_clear()

poses = []
for angle in (0, 1, 3, 5, 10, 20, 35, 54.431):
    jaw.rotation_euler = (angle * 3.141592653589793 / 180, 0, 0)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    stationary = [world_bvh(obj, depsgraph) for obj in upper]
    moving = [world_bvh(obj, depsgraph) for obj in lower]
    collisions = [
        (i, j) for i in range(9) for j in range(9)
        if stationary[i].overlap(moving[j])
    ]
    poses.append({"angle_deg": angle, "colliding_tooth_pairs": collisions})
print("GOSHMAN_TOOTH_BVH=" + json.dumps(poses))
