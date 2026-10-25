"""Real CPU four-view silhouette-to-GLB integration test. No AI or uploads."""
import json
from pathlib import Path
import pytest

pytest.importorskip("cv2")
pytest.importorskip("scipy")
pytest.importorskip("skimage")
trimesh=pytest.importorskip("trimesh")
from PIL import Image, ImageDraw
from goshman.project import create_project, import_reference
from goshman.reference_views import prepare_turnaround, PANEL_BOXES
from goshman.visual_hull import build_visual_hull


def test_synthetic_four_views_make_true_readable_glb(tmp_path):
    project=tmp_path/"project"
    created=create_project(project,"Synthetic test, not the actual crocodile")
    sheet=Image.new("RGB",(1491,1055),(195,195,195))
    draw=ImageDraw.Draw(sheet)
    for box in PANEL_BOXES.values():
        x0,y0,x1,y1=box
        centre=(x0+x1)//2
        draw.rectangle((centre-35,120,centre+35,560),fill=(28,142,39))
        draw.ellipse((centre-55,70,centre+55,185),fill=(49,169,60))
    path=tmp_path/"sheet.png";sheet.save(path)
    import_reference(project,created,path,"full_turnaround")
    prepare_turnaround(project)
    output=tmp_path/"result"
    result=build_visual_hull(project,output,grid_x=40,grid_y=40,grid_z=64)
    assert result["status"]=="PASS_IMAGE_DERIVED_GEOMETRY"
    assert not result["ai_inference_executed"]
    assert not result["reference_fidelity_verified"]
    assert result["mesh"]["vertices"]>200
    assert result["mesh"]["triangles"]>200
    glb=output/result["model_name"]
    assert glb.read_bytes().startswith(b"glTF")
    loaded=trimesh.load(glb,force="scene")
    assert len(loaded.geometry)>0
    for role in ("front","back","left","right"):
        assert (output/(role+"_mask.png")).exists()
    assert json.loads((output/"reconstruction_report.json").read_text())==result


def test_grid_size_limits_without_reading_private_sources(tmp_path):
    with pytest.raises(ValueError,match="Voxel resolution"):
        build_visual_hull(tmp_path,tmp_path/"result",grid_x=8)
