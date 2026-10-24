"""Blender UV map synthesizer and exporter for GOSHMAN materials.

Creates real PNG material maps and embeds them in .blend and .glb. NOT
a high-poly Cycles normal bake or photograph-driven texture reconstruction.
"""
from __future__ import annotations
from pathlib import Path
import bpy
from pbr_maps import make_maps

def ensure_uv(obj):
    if obj.type != "MESH" or obj.data.uv_layers:
        return
    uv=obj.data.uv_layers.new(name="GOSHMAN_Procedural_UV")
    verts=[v.co for v in obj.data.vertices]
    minx=min(v.x for v in verts)
    minz=min(v.z for v in verts)
    dx=max(max(v.x for v in verts)-minx,0.0001)
    dz=max(max(v.z for v in verts)-minz,0.0001)
    for poly in obj.data.polygons:
        for loop_index in poly.loop_indices:
            v=obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=((v.x-minx)/dx,(v.z-minz)/dz)

def attach_maps(materials: dict, objects: list, output_dir: Path, resolution: int = 512) -> dict:
    output_dir=output_dir.resolve()
    texture_dir=output_dir/"pbr"
    texture_dir.mkdir(parents=True,exist_ok=True)
    result={}
    for obj in objects:
        ensure_uv(obj)
    for name,material in materials.items():
        bsdf=material.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            raise RuntimeError(f"Missing Principled BSDF for {name}")
        rgb=material.diffuse_color[:3]
        base="#"+"".join(f"{round(max(0,min(1,c))*255):02x}" for c in rgb)
        channels=make_maps(name,base,resolution)
        nodes=material.node_tree.nodes
        links=material.node_tree.links
        normal_node=nodes.new("ShaderNodeNormalMap")
        normal_node.name=f"GOSHMAN_{name}_Normal"
        normal_node.inputs["Strength"].default_value=1.0
        result[name]={}
        for kind,pixels in channels.items():
            image=bpy.data.images.new(f"GOSHMAN_{name}_{kind}",
                 width=resolution,height=resolution,alpha=True)
            image.pixels.foreach_set(pixels.ravel())
            image.colorspace_settings.name="sRGB" if kind=="base_color" else "Non-Color"
            image.file_format="PNG"
            path=texture_dir/f"{name.lower()}_{kind}.png"
            image.filepath_raw=str(path)
            image.save()
            if not path.is_file() or path.stat().st_size==0:
                raise RuntimeError(f"Failed writing texture map: {path}")
            image.pack()
            node=nodes.new("ShaderNodeTexImage")
            node.image=image
            node.label=f"GOSHMAN_{kind}"
            if kind=="normal":
                links.new(node.outputs["Color"],normal_node.inputs["Color"])
            else:
                socket={"base_color":"Base Color",
                        "roughness":"Roughness","metallic":"Metallic"}[kind]
                links.new(node.outputs["Color"],bsdf.inputs[socket])
            result[name][kind]=str(path.relative_to(output_dir))
        links.new(normal_node.outputs["Normal"],bsdf.inputs["Normal"])
    return result
