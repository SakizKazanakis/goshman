from pathlib import Path
import ast
import pytest
from PIL import Image
from goshman.project import create_project, import_reference
from goshman.backend import blender_command
from goshman.ai import response_schema, analyze_references
from goshman.comfy import validate_local_endpoint,queue_verified_workflow


def test_blender_command_does_not_use_shell(tmp_path):
    fake=tmp_path/'blender.exe'; fake.write_text('not executable')
    folder=tmp_path/'project';create_project(folder,'Croc')
    args=blender_command(folder,str(fake))
    assert '--background' in args and '--factory-startup' in args
    assert '--python-exit-code' in args and '--project' in args
    assert 'shell' not in args


def test_tamper_prevents_generation(tmp_path):
    fake=tmp_path/'blender.exe';fake.touch()
    folder=tmp_path/'p';p=create_project(folder,'Croc')
    original=tmp_path/'a.png'; Image.new('RGB',(10,10)).save(original)
    r=import_reference(folder,p,original)
    (folder/r.filename).write_bytes(b'bad')
    with pytest.raises(ValueError,match='Changed reference'):
        blender_command(folder,str(fake))


def test_ai_requires_consent():
    with pytest.raises(PermissionError):
        analyze_references([],model='gpt-4.1',consent=False)
    assert response_schema()['additionalProperties'] is False


def test_comfy_local_only():
    assert validate_local_endpoint('http://127.0.0.1:8188')=='http://127.0.0.1:8188'
    for host in ('https://example.org','http://192.168.1.1:8188','file:///etc/passwd'):
        with pytest.raises(ValueError):validate_local_endpoint(host)
    with pytest.raises(ValueError,match='API workflow node'):
        queue_verified_workflow({'5': {'class_type':'NoInputs'}})


def test_blender_generator_syntax():
    script=Path(__file__).parents[1]/'goshman'/'blender_generate.py'
    tree=ast.parse(script.read_text(encoding='utf-8'))
    names={x.name for x in ast.walk(tree) if isinstance(x,ast.FunctionDef)}
    assert {'make_rig','build','animate','do_exports'}.issubset(names)
