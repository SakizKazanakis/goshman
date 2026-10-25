"""Offline verification of non-destructive reconstruction-view preflight."""
import json
import hashlib
from PIL import Image
from goshman.project import create_project, import_reference
from goshman.reference_preflight import audit_multiview_inputs
from goshman.reference_views import prepare_turnaround


def make_project(tmp_path):
    folder=tmp_path/"project"
    p=create_project(folder,"Animatronic Crocodile Cowboy")
    src=tmp_path/"original.png"
    Image.new("RGB",(1491,1055),(80,95,105)).save(src)
    import_reference(folder,p,src,"full_turnaround")
    prepare_turnaround(folder)
    return folder


def test_four_views_and_source_unchanged(tmp_path):
    folder=make_project(tmp_path)
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (folder/"references").glob("*.png")}
    result=audit_multiview_inputs(folder)
    assert result["status"]=="PASS_PREFLIGHT"
    assert result["image_count"]==4
    assert list(result["views"])==["front","left","back","right"]
    assert not result["camera_calibration_verified"]
    assert not result["semantic_correspondence_verified"]
    assert all(not x["background_removed"] for x in result["views"].values())
    assert {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (folder/"references").glob("*.png")}==before
    saved=json.loads((folder/"derived"/"reconstruction_input_report.json").read_text())
    assert saved==result


def test_reject_corrupted_four_view(tmp_path):
    folder=make_project(tmp_path)
    (folder/"derived"/"turnaround"/"front.png").write_bytes(b"corrupted")
    from goshman.reconstruction import ReconstructionError
    import pytest
    with pytest.raises(ReconstructionError):
        audit_multiview_inputs(folder)
