"""Real Blender/Cycles CPU integration test: two different geometries, four bake maps."""
import json
import math
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from goshman.blender_bake import bake_pair

bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,radius=1.0)
low=bpy.context.object
low.name="LOW_character_panel"
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=.975)
high=bpy.context.object
high.name="HIGH_detailed_panel"
for vertex in high.data.vertices:
    pos=vertex.co
    amplitude=.019*math.sin(21*pos.x)*math.sin(19*pos.z)
    pos += pos.normalized()*amplitude
material=bpy.data.materials.new("HighPoly_LeatherSource")
material.use_nodes=True
bsdf=material.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value=(.32,.09,.035,1)
bsdf.inputs["Roughness"].default_value=.72
bsdf.inputs["Metallic"].default_value=.05
high.data.materials.append(material)
folder=Path(sys.argv[-1])
report=bake_pair(high,low,folder,resolution=64,max_ray_distance=.25,
                 cage_extrusion=.08)
assert report["source_faces"]>report["target_faces"]*5
assert set(report["channels"])=={"normal","base_color","roughness","metallic"}
for filename in (folder/"normal.png",folder/"base_color.png",folder/"roughness.png",folder/"metallic.png"):
    image=bpy.data.images.load(str(filename),check_existing=False)
    assert tuple(image.size)==(64,64)
bpy.ops.object.select_all(action="DESELECT")
low.select_set(True)
bpy.context.view_layer.objects.active=low
asset=folder/"baked_lowpoly.glb"
bpy.ops.export_scene.gltf(filepath=str(asset),export_format="GLB",use_selection=True)
import struct
blob=asset.read_bytes()
assert blob[:4]==b"glTF"
chunk_size=struct.unpack_from("<I",blob,12)[0]
glb=json.loads(blob[20:20+chunk_size])
assert glb.get("meshes"), "No mesh exported after bake"
assert any("normalTexture" in material for material in glb.get("materials",[])), "Baked normal not exported"
assert any("baseColorTexture" in mat.get("pbrMetallicRoughness",{})
           for mat in glb.get("materials",[])), "Baked base colour not exported"
print("BAKE_RUNTIME_PASS",json.dumps({"high":report["source_faces"],
  "low":report["target_faces"],"glb_bytes":len(blob),"images":len(glb.get("images",[]))}))
