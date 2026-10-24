"""Contract tests for standalone structural audit, no Blender/GPU/network needed."""
from pathlib import Path
import json
import struct

from PIL import Image, ImageDraw
import pytest

from goshman.project import create_project
from goshman.quality import inspect_glb, inspect_png, audit_project


def make_glb(path: Path, *, animations=1):
    document = {"asset": {"version": "2.0"},
                "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
                "skins": [{"joints": [0]}],
                "animations": [{"name": "GOSHMAN_idle"}] * animations}
    data = json.dumps(document).encode("utf-8")
    data += b" " * (-len(data) % 4)
    path.write_bytes(struct.pack("<4sIIII", b"glTF", 2, 20 + len(data),
                                 len(data), 0x4E4F534A) + data)


def make_valid_sample(folder: Path):
    create_project(folder, "Crocodile")
    out = folder / "output"
    out.mkdir()
    (out / "crocodile_cowboy.blend").write_bytes(b"BLENDER")
    (out / "crocodile_cowboy.fbx").write_bytes(b"FBX")
    make_glb(out / "crocodile_cowboy.glb")
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((8, 6, 56, 58), fill=(30, 130, 30, 255))
    image.save(out / "preview_front.png")
    (out / "build_report.json").write_text(json.dumps({"mesh_objects": 1, "bones": 1}), encoding="utf-8")


def test_structural_audit_valid_sample(tmp_path):
    folder = tmp_path / "p"
    make_valid_sample(folder)
    report = audit_project(folder)
    assert report["status"] == "PASS_TECHNICAL"
    assert report["errors"] == []
    assert report["glb"]["meshes"] == 1
    assert report["glb"]["animations"] == 1
    assert report["preview"]["touches_border"] is False
    assert "NOT established" in report["warnings"][-1]


def test_audit_missing_artifact_not_false_pass(tmp_path):
    folder = tmp_path / "p"
    make_valid_sample(folder)
    (folder / "output" / "crocodile_cowboy.fbx").unlink()
    report = audit_project(folder)
    assert report["status"] == "FAIL"
    assert any("fbx" in message for message in report["errors"])


def test_reject_corrupted_glb_and_transparent_preview(tmp_path):
    folder = tmp_path / "p"
    make_valid_sample(folder)
    output = folder / "output"
    (output / "crocodile_cowboy.glb").write_bytes(b"bad")
    Image.new("RGBA", (64,64), (0,0,0,0)).save(output / "preview_front.png")
    report = audit_project(folder)
    assert report["status"] == "FAIL"
    assert any("GLB validation" in x for x in report["errors"])
    assert any("PNG validation" in x for x in report["errors"])


def test_reject_wrong_version(tmp_path):
    dest = tmp_path / "bad.glb"
    make_glb(dest)
    data = bytearray(dest.read_bytes())
    struct.pack_into("<I", data, 4, 1)
    dest.write_bytes(data)
    with pytest.raises(ValueError, match="GLB header"):
        inspect_glb(dest)


def test_alpha_cropping_warning(tmp_path):
    dest = tmp_path / "edge.png"
    Image.new("RGBA", (12,12), (255,255,255,255)).save(dest)
    assert inspect_png(dest)["touches_border"] is True
