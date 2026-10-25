"""Actual Blender Cycles high-poly -> low-poly texture baking.

Unlike goshman.pbr_maps, this explicitly ray-bakes the selected high-poly
source geometry onto the UVs of a separate low-poly target. Normal, diffuse
albedo, roughness and metallic are extracted as separate image maps.
"""
from __future__ import annotations
from pathlib import Path
import json
import hashlib
import bpy


def bake_pair(high, low, output: Path, *, resolution: int = 1024,
              cage_extrusion: float = 0.03, max_ray_distance: float = 0.12) -> dict:
    if high == low or high.type != "MESH" or low.type != "MESH":
        raise ValueError("Bake requires two different polygon mesh objects")
    if resolution not in (64, 128, 256, 512, 1024, 2048, 4096):
        raise ValueError("Unsupported bake resolution")
    if not low.data.uv_layers:
        raise ValueError("Low-poly object needs nonoverlapping UV coordinates")
    if not high.data.materials:
        raise ValueError("High-poly object needs at least one source material")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.use_cage = False
    bake.cage_extrusion = cage_extrusion
    bake.max_ray_distance = max_ray_distance
    bake.normal_space = "TANGENT"
    bake.margin = max(2, int(resolution * .01))
    bake.target = "IMAGE_TEXTURES"
    high.hide_render = False
    low.hide_render = False
    if not low.data.materials:
        low.data.materials.append(bpy.data.materials.new("GOSHMAN_BakeTarget"))
    low_mat = low.data.materials[0]
    if not low_mat.use_nodes:
        low_mat.use_nodes = True
    nodes = low_mat.node_tree.nodes
    node = nodes.new("ShaderNodeTexImage")
    node.label = "GOSHMAN_ACTUAL_SELECTED_TO_ACTIVE_BAKE"
    for other in nodes:
        other.select = False
    node.select = True
    nodes.active = node
    # Operator requires high-poly source SELECTED and low-poly target ACTIVE.
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    # Emission signal routing for material scalar channels, restored after each bake.
    temporary = []
    outputs = {}
    try:
        for channel in ("normal", "base_color", "roughness", "metallic"):
            image = bpy.data.images.new(
                f"GOSHMAN_BAKED_{channel}",width=resolution,height=resolution,
                alpha=True,float_buffer=False)
            image.colorspace_settings.name = "sRGB" if channel == "base_color" else "Non-Color"
            node.image = image
            nodes.active = node
            if channel in ("roughness","metallic"):
                for material in high.data.materials:
                    if material is None:
                        continue
                    material.use_nodes = True
                    nt = material.node_tree
                    principled = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"),None)
                    output_node = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"),None)
                    if principled is None or output_node is None:
                        raise ValueError("Source PBR material needs Principled BSDF and Material Output")
                    surface = output_node.inputs["Surface"]
                    old_source = surface.links[0].from_socket if surface.is_linked else None
                    emission = nt.nodes.new("ShaderNodeEmission")
                    param = principled.inputs["Roughness" if channel == "roughness" else "Metallic"]
                    if param.is_linked:
                        nt.links.new(param.links[0].from_socket,emission.inputs["Color"])
                    else:
                        value = float(param.default_value)
                        emission.inputs["Color"].default_value = (value,value,value,1)
                    nt.links.new(emission.outputs["Emission"],surface)
                    temporary.append((nt,output_node,emission,old_source))
                bake_type = "EMIT"
                kwargs = {}
            elif channel == "base_color":
                bake_type = "DIFFUSE"
                kwargs = {"pass_filter":{"COLOR"}}
            else:
                bake_type = "NORMAL"
                kwargs = {"normal_space":"TANGENT"}
            bpy.ops.object.bake(type=bake_type,
                                use_selected_to_active=True,
                                cage_extrusion=cage_extrusion,
                                max_ray_distance=max_ray_distance,
                                margin=bake.margin,**kwargs)
            if temporary:
                for nt,output_node,emission,old_source in temporary:
                    nt.nodes.remove(emission)
                    if old_source:
                        nt.links.new(old_source,output_node.inputs["Surface"])
                temporary.clear()
            image.file_format = "PNG"
            path = output / f"{channel}.png"
            image.filepath_raw = str(path)
            image.save()
            if path.stat().st_size < 100:
                raise RuntimeError("Baked image is missing or empty: " + channel)
            image.pack()
            outputs[channel] = {"path":str(path),
                                "bytes":path.stat().st_size,
                                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        report = {"status":"PASS_BAKE_EXECUTED",
                  "engine":"CYCLES","method":"selected_to_active",
                  "source_high_poly":high.name,"target_low_poly":low.name,
                  "source_faces":len(high.data.polygons),
                  "target_faces":len(low.data.polygons),
                  "resolution":resolution,"channels":outputs,
                  "blender_version":bpy.app.version_string,
                  "reference_fidelity_tested":False}
        (output/"bake_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        return report
    finally:
        for nt,output_node,emission,old_source in temporary:
            nt.nodes.remove(emission)
            if old_source:
                nt.links.new(old_source,output_node.inputs["Surface"])
        high.select_set(False)
        low.select_set(False)
