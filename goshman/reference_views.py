"""Extract the five views from GOSHMAN's supplied 1491x1055 turnaround sheet.

This is provenance-preserving cropping, NOT 3D reconstruction, calibration or
background segmentation. The original reference remains unmodified.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from PIL import Image
from .project import load_project, verify_references, atomic_json

PANEL_BOXES = {
    "front": (8, 50, 305, 622),
    "left_profile": (307, 50, 608, 622),
    "back": (611, 50, 902, 622),
    "right_profile": (904, 50, 1193, 622),
    "three_quarter": (1195, 50, 1486, 622),
}
SOURCE_SIZE=(1491,1055)

def prepare_turnaround(folder: Path) -> dict:
    """Crop only the known supplied reference design; never guess sheet layout."""
    folder=Path(folder).resolve(strict=True)
    project=load_project(folder)
    errors=verify_references(folder,project)
    if errors:
        raise ValueError("Reference integrity failed: "+"; ".join(errors))
    candidates=[r for r in project.references if r.role=="full_turnaround"]
    if len(candidates)!=1:
        raise ValueError("Exactly one full_turnaround reference is required")
    source=candidates[0]
    original=folder/source.filename
    out=folder/"derived"/"turnaround"
    with Image.open(original) as img:
        if img.size!=SOURCE_SIZE:
            raise ValueError("Turnaround layout calibration only supports 1491x1055 supplied sheet")
        out.mkdir(parents=True,exist_ok=True)
        views={}
        for name,coords in PANEL_BOXES.items():
            path=out/(name+".png")
            img.crop(coords).save(path)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            views[name]={"file":str(path.relative_to(folder)),
                "source_sha256":source.sha256,"bbox_px":list(coords),
                "sha256":digest}
    record={"format":"goshman-reference-views-1","source":source.filename,
            "provenance":"pixel-exact crops from supplied reference",
            "not_calibrated_3d":True,"views":views}
    atomic_json(folder/"derived"/"turnaround_manifest.json",record)
    return record
