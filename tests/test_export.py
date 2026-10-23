from pathlib import Path
from PIL import Image
import pytest
from goshman.export import pack_frames, export_atlas


def test_atlas_manifest(tmp_path):
    frames=tmp_path/'frames'; frames.mkdir()
    for i in range(4):
        Image.new('RGBA',(16,32),(i,0,255-i,130)).save(frames/f'frame_{i:02d}.png')
    manifest=export_atlas(frames,tmp_path/'atlas.png','walk',12,2)
    assert manifest['frames']==4
    assert manifest['hotspot']=={'x':8,'y':29}
    assert (tmp_path/'atlas.json').exists()
    with Image.open(tmp_path/'atlas.png') as atlas:
        assert atlas.size == (32,64)
        assert atlas.mode=='RGBA'
        assert atlas.getpixel((0,0))[3]==130


def test_atlas_rejects_unequal_frame_size(tmp_path):
    files=[]
    for i, width in enumerate((12,14)):
        p=tmp_path/f'{i}.png';Image.new('RGBA',(width,20)).save(p);files.append(p)
    with pytest.raises(ValueError,match='identical'):
        pack_frames(files,tmp_path/'atlas.png')
