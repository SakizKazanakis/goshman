"""Objective validation of GOSHMAN export artifacts.

These are structural checks; passing does not certify visual fidelity to references
or successful import into Clickteam Fusion 2.5.
"""
from __future__ import annotations
import json
import struct
from pathlib import Path

from PIL import Image

from .project import load_project, verify_references


def inspect_glb(path: Path) -> dict:
    """Inspect actual glTF 2.0 JSON metadata inside a binary GLB without glTF deps."""
    size = path.stat().st_size
    if size < 20 or size > 1_000_000_000:
        raise ValueError("Invalid GLB length")
    with path.open("rb") as file:
        header = file.read(20)
        magic, version, declared, chunk_len, chunk_type = struct.unpack("<4sIIII", header)
        if magic != b"glTF" or version != 2 or declared != size:
            raise ValueError("Invalid GLB header")
        if chunk_type != 0x4E4F534A or chunk_len < 2 or chunk_len > size - 20:
            raise ValueError("GLB first chunk is not valid JSON")
        doc = json.loads(file.read(chunk_len))
    if doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("Not a glTF 2.0 asset")
    meshes = doc.get("meshes", [])
    skins = doc.get("skins", [])
    actions = doc.get("animations", [])
    return {
        "meshes": len(meshes),
        "skins": len(skins),
        "joints": sum(len(item.get("joints", [])) for item in skins),
        "animations": len(actions),
        "animation_names": [item.get("name", "") for item in actions],
        "textures": len(doc.get("textures", [])),
        "images": len(doc.get("images", [])),
        "normal_maps": sum("normalTexture" in m for m in doc.get("materials", [])),
        "base_color_maps": sum("baseColorTexture" in m.get("pbrMetallicRoughness",{})
                               for m in doc.get("materials",[])),
        "metallic_roughness_maps": sum("metallicRoughnessTexture" in m.get("pbrMetallicRoughness",{})
                                      for m in doc.get("materials",[])),
    }


def inspect_png(path: Path) -> dict:
    with Image.open(path) as image:
        image.load()
        if image.mode != "RGBA":
            raise ValueError("PNG render must use RGBA")
        if image.width <= 0 or image.height <= 0:
            raise ValueError("PNG render has invalid dimensions")
        bounds = image.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError("PNG render contains no visible pixels")
        touches_border = bounds[0] == 0 or bounds[1] == 0 or bounds[2] == image.width or bounds[3] == image.height
        return {
            "width": image.width, "height": image.height,
            "visible_bbox": list(bounds), "touches_border": touches_border,
        }


def audit_project(folder: Path) -> dict:
    """Generate a read-only technical QA report from an existing project directory."""
    folder = folder.resolve()
    project = load_project(folder)
    errors = verify_references(folder, project)
    warnings: list[str] = []
    output = folder / "output"
    artifacts = {}
    for file in ("crocodile_cowboy.blend", "crocodile_cowboy.glb",
                 "crocodile_cowboy.fbx", "preview_front.png", "build_report.json"):
        path = output / file
        if not path.is_file() or path.stat().st_size == 0:
            errors.append("Missing or empty required artifact: " + file)
        else:
            artifacts[file] = path.stat().st_size
    glb = None
    glb_path = output / "crocodile_cowboy.glb"
    if glb_path.is_file() and glb_path.stat().st_size:
        try:
            glb = inspect_glb(glb_path)
            if glb["meshes"] < 1:
                errors.append("GLB contains no polygon meshes")
            if glb["joints"] < 1:
                errors.append("GLB contains no skeleton joints")
            if glb["animations"] < 1:
                errors.append("GLB contains no animation clips")
        except (ValueError, KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append("GLB validation failed: " + str(exc))
    preview = None
    front = output / "preview_front.png"
    if front.is_file() and front.stat().st_size:
        try:
            preview = inspect_png(front)
            if preview["touches_border"]:
                warnings.append("Front-view render touches image edge; camera framing may crop geometry")
        except (ValueError, OSError) as exc:
            errors.append("Preview PNG validation failed: " + str(exc))
    report = None
    report_path = output / "build_report.json"
    if report_path.is_file() and report_path.stat().st_size:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(report, dict):
                raise ValueError("Build report is not an object")
            if report.get("mesh_objects", 0) < 1 or report.get("bones", 0) < 1:
                errors.append("Build report does not establish mesh and bone generation")
            if glb and report.get("mesh_objects", 0) != glb["meshes"]:
                warnings.append("Blender scene and glTF mesh counts differ")
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            errors.append("Build report validation failed: " + str(exc))
    pbr_summary = None
    manifest_path = output / "pbr_manifest.json"
    if manifest_path.is_file():
        try:
            pbr_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            resolution = pbr_manifest["resolution"]
            materials = pbr_manifest["materials"]
            checked = 0
            for name, channels in materials.items():
                if set(channels) != {"base_color", "normal", "roughness", "metallic"}:
                    errors.append("Incomplete UV PBR channels: " + name)
                for kind, filename in channels.items():
                    p = Path(filename)
                    # Manifest may contain absolute paths; forbid pointing outside project.
                    if not p.is_absolute():
                        p = output / p
                    p = p.resolve()
                    if not p.is_relative_to(folder):
                        errors.append("Unsafe PBR image path: " + str(filename))
                        continue
                    with Image.open(p) as im:
                        if im.size != (resolution,resolution):
                            errors.append("Wrong PBR resolution: " + str(p))
                    checked += 1
            pbr_summary={"resolution":resolution,"materials":len(materials),"maps_checked":checked}
            if glb is not None and (glb["images"] < 10 or glb["normal_maps"] < 1):
                errors.append("PBR images or normal maps missing from exported GLB")
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            errors.append("PBR manifest validation failed: " + str(exc))
    else:
        warnings.append("No UV PBR map manifest; legacy non-textured build")
    sprite_groups = {}
    sprites = output / "sprites"
    if sprites.is_dir():
        for directory in sorted(x for x in sprites.iterdir() if x.is_dir()):
            frames = sorted(directory.glob("*.png"))
            if not frames:
                continue
            try:
                checks = [inspect_png(p) for p in frames]
                sizes = {(f["width"], f["height"]) for f in checks}
                if len(sizes) != 1:
                    errors.append("Mismatched frame sizes: " + directory.name)
                if any(x["touches_border"] for x in checks):
                    warnings.append("Sprite clipping risk: " + directory.name)
                sprite_groups[directory.name] = len(checks)
            except (ValueError, OSError) as exc:
                errors.append("Invalid sprite group " + directory.name + ": " + str(exc))
    warnings.append("Visual resemblance to user references and Clickteam runtime compatibility are NOT established by structural QA")
    return {
        "status": "PASS_TECHNICAL" if not errors else "FAIL",
        "project": project.name,
        "references": len(project.references),
        "artifacts_bytes": artifacts,
        "glb": glb, "preview": preview,
        "blender_report": report, "pbr": pbr_summary,
        "sprite_groups": sprite_groups,
        "errors": errors, "warnings": warnings,
    }
