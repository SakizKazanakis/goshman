"""Faithful side-by-side comparison sheets for real Blender renders and 2D sources.

No invented similarity score: five views are artistic and not calibrated
photographic cameras. Kept as an explicit human visual acceptance stage.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
from .project import atomic_json
from .reconstruction import load_views

VIEW_NAMES=("front","left","back","right","three_quarter")


def create_view_comparison(folder: Path, renders: Path, output: Path,
                           *, cell_width: int=400, cell_height: int=640) -> dict:
    if not (256<=cell_width<=2048 and 256<=cell_height<=2048):
        raise ValueError("Comparison canvas dimensions out of safe bounds")
    folder=Path(folder).resolve(strict=True)
    renders=Path(renders).resolve(strict=True)
    output=Path(output).resolve()
    verified=load_views(folder)
    data=json.loads((folder/"derived"/"turnaround_manifest.json").read_text(encoding="utf-8"))
    extra=data["views"]["three_quarter"]
    last=(folder/extra["file"]).resolve(strict=True)
    if not last.is_relative_to(folder) or hashlib.sha256(last.read_bytes()).hexdigest()!=extra["sha256"]:
        raise ValueError("Invalid three-quarter reference provenance")
    verified["three_quarter"]=last
    manifest=json.loads((renders/"render_manifest.json").read_text(encoding="utf-8"))
    if set(manifest.get("views",{}))!=set(VIEW_NAMES):
        raise ValueError("Blender render manifest requires the five named camera directions")
    if manifest.get("status")!="PASS_RENDER_TECHNICAL":
        raise ValueError("Blender rendering was not verified")
    width=cell_width*2
    header=36
    row_height=cell_height+header
    sheet=Image.new("RGB",(width,row_height*5),(229,230,231))
    draw=ImageDraw.Draw(sheet)
    assets={}
    for i,name in enumerate(VIEW_NAMES):
        entry=manifest["views"][name]
        png=(renders/(name+".png")).resolve(strict=True)
        if not png.is_relative_to(renders) or entry.get("image")!=name+".png":
            raise ValueError("Untrusted render path for "+name)
        sha=hashlib.sha256(png.read_bytes()).hexdigest()
        if sha!=entry.get("sha256"):
            raise ValueError("Modified rendered view: "+name)
        with Image.open(verified[name]) as orig:
            reference=ImageOps.contain(orig.convert("RGB"),(cell_width-16,cell_height-16))
        with Image.open(png) as im:
            image=im.convert("RGBA")
            if image.getbbox() is None:
                raise ValueError("Rendered image is fully transparent: "+name)
            # Explicit white background for comparability; original is unchanged.
            white=Image.new("RGBA",image.size,(245,245,245,255))
            rendered=Image.alpha_composite(white,image).convert("RGB")
            render_thumb=ImageOps.contain(rendered,(cell_width-16,cell_height-16))
        top=i*row_height
        draw.rectangle((0,top,width-1,top+row_height-1),outline=(130,130,130))
        draw.text((12,top+8),f"{name}: ORIGINAL REFERENCE",fill=(20,20,20))
        draw.text((cell_width+12,top+8),f"{name}: ACTUAL 3D RENDER",fill=(20,20,20))
        sheet.paste(reference,((cell_width-reference.width)//2,
                              top+header+(cell_height-reference.height)//2))
        sheet.paste(render_thumb,(cell_width+(cell_width-render_thumb.width)//2,
                                  top+header+(cell_height-render_thumb.height)//2))
        assets[name]={"source_sha256":hashlib.sha256(verified[name].read_bytes()).hexdigest(),
                      "render_sha256":sha}
    output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output)
    report={"status":"PASS_CONTACT_SHEET_TECHNICAL",
            "comparison_image":str(output),
            "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
            "five_views":assets,
            "reference_fidelity_verified":False,
            "note":"Human review required: original artistic view cameras not calibrated; no IoU or fake similarity percentage"}
    atomic_json(output.with_suffix(".json"),report)
    return report
