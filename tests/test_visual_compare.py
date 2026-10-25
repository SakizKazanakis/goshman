"""No-model, non-network tests of 5-way visual QA assembly and tamper checks."""
import hashlib
import json
from pathlib import Path

from PIL import Image
import pytest

from goshman.project import create_project, import_reference
from goshman.reference_views import prepare_turnaround
from goshman.visual_compare import create_view_comparison, VIEW_NAMES


def build_project(tmp_path):
    folder=tmp_path/"character"
    project=create_project(folder,"Crocodile")
    original=tmp_path/"whole.png"
    Image.new("RGB",(1491,1055),(90,91,92)).save(original)
    import_reference(folder,project,original,"full_turnaround")
    prepare_turnaround(folder)
    renders=tmp_path/"renders"
    renders.mkdir()
    views={}
    for role in VIEW_NAMES:
        path=renders/(role+".png")
        Image.new("RGBA",(160,320),(63,130,49,255)).save(path)
        views[role]={"image":role+".png",
                     "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (renders/"render_manifest.json").write_text(json.dumps(
        {"status":"PASS_RENDER_TECHNICAL","views":views}),encoding="utf-8")
    return folder,renders


def test_original_vs_render_contact_sheet_five_views(tmp_path):
    folder,renders=build_project(tmp_path)
    out=tmp_path/"qa"/"comparison.png"
    report=create_view_comparison(folder,renders,out,cell_width=256,cell_height=256)
    assert report["status"]=="PASS_CONTACT_SHEET_TECHNICAL"
    assert not report["reference_fidelity_verified"]
    assert set(report["five_views"])==set(VIEW_NAMES)
    with Image.open(out) as image:
        assert image.size==(512,5*(256+36))
    assert out.with_suffix(".json").is_file()


def test_modified_render_is_rejected(tmp_path):
    folder,renders=build_project(tmp_path)
    (renders/"front.png").write_bytes(b"tampered")
    with pytest.raises(ValueError,match="Modified rendered view"):
        create_view_comparison(folder,renders,tmp_path/"c.png",cell_width=256,cell_height=256)


def test_unverified_render_manifest_rejected(tmp_path):
    folder,renders=build_project(tmp_path)
    file=renders/"render_manifest.json"
    data=json.loads(file.read_text())
    data["status"]="NOT_TESTED"
    file.write_text(json.dumps(data))
    with pytest.raises(ValueError,match="not verified"):
        create_view_comparison(folder,renders,tmp_path/"c.png")
