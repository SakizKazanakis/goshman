from pathlib import Path
import json
from PIL import Image
import pytest
from goshman.project import (create_project, load_project, save_project, CharacterSpec,
                             import_reference, verify_references)


def test_round_trip(tmp_path):
    folder = tmp_path / 'demo'
    p = create_project(folder, 'Crocodile')
    assert p.name == load_project(folder).name
    p.spec.head_scale = 1.25
    save_project(folder, p)
    assert load_project(folder).spec.head_scale == 1.25
    assert (folder/'project.json').exists()


def test_create_does_not_overwrite(tmp_path):
    create_project(tmp_path,'One')
    with pytest.raises(FileExistsError):
        create_project(tmp_path,'Two')


def test_reference_copy_and_tamper(tmp_path):
    folder = tmp_path / 'p'
    p = create_project(folder, 'Croc')
    original = tmp_path / 'my reference.png'
    Image.new('RGBA',(32,64),(0,220,60,255)).save(original)
    ref = import_reference(folder,p,original,'head')
    assert ref.width == 32 and ref.height == 64
    assert import_reference(folder,p,original).id == ref.id
    assert len(p.references)==1
    assert verify_references(folder,p)==[]
    (folder/ref.filename).write_bytes(b'tampered')
    assert 'Changed reference' in verify_references(folder,p)[0]
    assert original.exists()


def test_reference_path_traversal(tmp_path):
    folder=tmp_path/'p';p=create_project(folder,'Croc')
    from goshman.project import Reference
    p.references.append(Reference('id','../secrets.txt','0'*64,0,0))
    assert len(verify_references(folder,p)) == 1


def test_validation():
    for attr, invalid in [('height',-3),('snout_length',999),('armor_detail',5)]:
        spec=CharacterSpec()
        setattr(spec, attr, invalid)
        with pytest.raises(ValueError):
            spec.validate()
