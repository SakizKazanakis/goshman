from pathlib import Path
from PIL import Image
import pytest
from goshman.project import create_project,import_reference
from goshman.reference_views import prepare_turnaround,PANEL_BOXES

def test_prepare_exact_crops_and_sha(tmp_path):
    folder=tmp_path/"croc"
    project=create_project(folder,"Crocodile")
    source=tmp_path/"turnaround.png"
    Image.new("RGB",(1491,1055),(12,150,70)).save(source)
    import_reference(folder,project,source,"full_turnaround")
    data=prepare_turnaround(folder)
    assert set(data["views"])==set(PANEL_BOXES)
    assert data["not_calibrated_3d"] is True
    for name,item in data["views"].items():
        path=folder/item["file"]
        assert path.is_file()
        with Image.open(path) as im:
            box=PANEL_BOXES[name]
            assert im.size==(box[2]-box[0],box[3]-box[1])
    assert (folder/"derived"/"turnaround_manifest.json").exists()

def test_unknown_sheet_shape_not_assumed(tmp_path):
    folder=tmp_path/"croc"
    project=create_project(folder,"Crocodile")
    source=tmp_path/"random.png"
    Image.new("RGB",(640,640)).save(source)
    import_reference(folder,project,source,"full_turnaround")
    with pytest.raises(ValueError,match="1491x1055"):
        prepare_turnaround(folder)

def test_tampered_reference_is_rejected(tmp_path):
    folder=tmp_path/"croc"
    project=create_project(folder,"Crocodile")
    source=tmp_path/"turnaround.png"
    Image.new("RGB",(1491,1055)).save(source)
    r=import_reference(folder,project,source,"full_turnaround")
    (folder/r.filename).write_bytes(b"altered")
    with pytest.raises(ValueError,match="integrity"):
        prepare_turnaround(folder)
