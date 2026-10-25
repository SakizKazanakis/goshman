"""Blender UV map synthesizer and exporter for GOSHMAN materials.

Creates real PNG material maps and embeds them in .blend and .glb. NOT
a high-poly Cycles normal bake or photograph-driven texture reconstruction.
"""
from __future__ import annotations
from pathlib import Path
import struct
import zlib
import bpy
import numpy as np
from pbr_maps import make_maps


def _save_rgba_png(path: Path, pixels: np.ndarray) -> None:
    """Write the actual deterministic RGBA data; never rely on Blender's generated image buffer.

    Blender 5.2.3 was observed exporting fully black PNGs from Image.pixels
    foreach_set followed by save. A direct PNG writer and reload avoids it.
    """
    if pixels.ndim != 3 or pixels.shape[2] != 4:
        raise ValueError("Expected four-channel RGBA image")
    h, w, _ = pixels.shape
    if not (32 <= w <= 8192 and 32 <= h <= 8192):
        raise ValueError("Invalid PBR dimensions")
    data = np.rint(np.clip(pixels, 0, 1) * 255).astype(np.uint8)
    raw = b"".join(b"\x00" + data[y].tobytes() for y in range(h - 1, -1, -1))
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(
            ">I", zlib.crc32(kind + body) & 0xffffffff)
    header = b"\x89PNG\r\n\x1a\n"
    header += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    path.write_bytes(header + chunk(b"IDAT", zlib.compress(raw, level=6)) + chunk(b"IEND", b""))


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
            path=texture_dir/f"{name.lower()}_{kind}.png"
            _save_rgba_png(path,pixels)
            if not path.is_file() or path.stat().st_size < 100:
                raise RuntimeError(f"Failed writing texture map: {path}")
            # Load verified file pixels into nodes so Blender and GLB see the same data.
            image=bpy.data.images.load(str(path),check_existing=False)
            image.name=f"GOSHMAN_{name}_{kind}"
            image.colorspace_settings.name="sRGB" if kind=="base_color" else "Non-Color"
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
