"""Transparent animation frames and deterministic Clickteam Fusion metadata."""
from __future__ import annotations
from pathlib import Path
import json
import math
from PIL import Image
from .project import atomic_json


def pack_frames(files: list[Path], destination: Path, cols: int = 6, padding: int = 0) -> dict:
    if not files or cols < 1 or cols > 128 or padding < 0 or padding > 100:
        raise ValueError("Invalid frame count or atlas parameters")
    frames = []
    for f in files:
        with Image.open(f) as image:
            frames.append(image.convert("RGBA"))
    sizes = {(img.width, img.height) for img in frames}
    if len(sizes) != 1:
        raise ValueError("Frame dimensions must be identical")
    w, h = next(iter(sizes))
    rows = math.ceil(len(frames) / cols)
    if (w + padding) * cols * (h + padding) * rows > 350_000_000:
        raise ValueError("Atlas too large")
    atlas = Image.new("RGBA", (w * cols + padding * (cols - 1), h * rows + padding * (rows - 1)))
    regions = []
    for index, frame in enumerate(frames):
        x = (index % cols) * (w + padding)
        y = (index // cols) * (h + padding)
        atlas.alpha_composite(frame, (x, y))
        regions.append({"file": files[index].name, "x": x, "y": y, "w": w, "h": h})
    destination.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(destination)
    return {"texture": destination.name, "frame_width": w, "frame_height": h,
            "columns": cols, "rows": rows, "frame_count": len(frames), "regions": regions}


def make_fusion_manifest(animation: str, atlas: dict, fps: int = 12, anchor: str = "feet") -> dict:
    if not 1 <= fps <= 120:
        raise ValueError("FPS out of range")
    if anchor not in ("feet", "center"):
        raise ValueError("Unknown anchor")
    w, h = atlas["frame_width"], atlas["frame_height"]
    hotspot = {"x": w // 2, "y": round(h * .9)} if anchor == "feet" else {"x": w // 2, "y": h // 2}
    return {"format": "goshman-fusion-sprites-1", "name": animation, "fps": fps,
            "frames": atlas["frame_count"], "texture": atlas["texture"],
            "hotspot": hotspot, "action_point": {"x": w // 2, "y": h // 2},
            "atlas": atlas, "note": "Hotspots are metadata: Fusion import/editor requires manual assignment."}


def export_atlas(input_dir: Path, output: Path, name: str, fps: int = 12, cols: int = 6) -> dict:
    files = sorted(input_dir.glob("*.png"))
    atlas = pack_frames(files, output, cols=cols)
    manifest = make_fusion_manifest(name, atlas, fps)
    atomic_json(output.with_suffix(".json"), manifest)
    return manifest
