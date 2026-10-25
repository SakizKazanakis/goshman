"""Read-only checks for private artistic multiview inputs.

Preflight never removes backgrounds or repaints visible geometry: naive matting
loses small metallic finger joints in the supplied crocodile references.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from PIL import Image, ImageStat
from .project import atomic_json
from .reconstruction import load_views, VIEWS

def audit_multiview_inputs(folder: Path) -> dict:
    """Verify four view images and emit truthful warnings, no inference or upload."""
    folder = Path(folder).resolve(strict=True)
    views = load_views(folder)
    inputs = {}
    warnings = ["The supplied turnaround consists of artistic renders, not calibrated camera photographs."]
    failures = []
    for role in VIEWS:
        path = views[role]
        with Image.open(path) as opened:
            image = opened.convert("RGB")
            width, height = image.size
            if width < 256 or height < 256:
                failures.append(f"{role}: image shorter than recommended 256px minimum")
            if width < 512:
                warnings.append(f"{role}: {width}px source width; upscaling cannot add true detail")
            # Corners provide a rough background consistency indicator only.
            corners = (image.getpixel((2,2)), image.getpixel((width-3,2)),
                       image.getpixel((2,height-3)), image.getpixel((width-3,height-3)))
            spread = max(max(channel) - min(channel) for channel in zip(*corners))
            if spread > 50:
                warnings.append(f"{role}: background differs between corners; assess the crop visually")
            gray = ImageStat.Stat(image.convert("L"))
            inputs[role] = {
                "file": str(path.relative_to(folder)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "width": width, "height": height,
                "aspect_ratio": round(width/height, 5),
                "mean_luminance": round(gray.mean[0], 2),
                "background_corner_spread_max": spread,
                "background_removed": False
            }
    heights = [item["height"] for item in inputs.values()]
    if min(heights) and max(heights)/min(heights) > 1.15:
        warnings.append("Different image heights may bias multi-view reconstruction")
    result = {
        "status": "PASS_PREFLIGHT" if not failures else "FAIL_PREFLIGHT",
        "camera_calibration_verified": False,
        "semantic_correspondence_verified": False,
        "image_count": len(views),
        "views": inputs,
        "warnings": warnings,
        "errors": failures,
    }
    out = folder / "derived" / "reconstruction_input_report.json"
    atomic_json(out, result)
    return result
