"""Offline contract tests for real Meshy/Tripo integrations.

No network calls, private image uploads or billable provider jobs are made.
"""
from __future__ import annotations
import io
import json
import struct

from PIL import Image
import pytest

from goshman.project import create_project, import_reference
from goshman.reconstruction import (
    MultiViewProvider, ReconstructionError, load_views, run_multiview_job,
    _approved_host,
)


class FakeResponse:
    def __init__(self, payload=None, data=b"", status_code=200):
        self.payload = payload or {}
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("Test HTTP failure")

    def json(self):
        return self.payload

    def iter_content(self, size):
        for i in range(0, len(self.data), size):
            yield self.data[i:i+size]


def make_glb():
    doc = json.dumps({
        "asset": {"version": "2.0"},
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "skins": [], "animations": []
    }).encode()
    doc += b" " * (-len(doc) % 4)
    return struct.pack("<4sIIII", b"glTF", 2, 20+len(doc),
                       len(doc), 0x4E4F534A) + doc


class MeshySession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST",url,kwargs))
        return FakeResponse({"result":"01-task"})

    def get(self, url, **kwargs):
        self.calls.append(("GET",url,kwargs))
        if "multi-image-to-3d" in url:
            return FakeResponse({"status":"SUCCEEDED",
                 "model_urls":{"glb":"https://assets.meshy.ai/model.glb"},
                 "consumed_credits":30})
        return FakeResponse(data=make_glb())


class TripoSession:
    def __init__(self):
        self.calls=[]
        self.uploads=0

    def post(self,url,**kwargs):
        self.calls.append(("POST",url,kwargs))
        if url.endswith("/files"):
            self.uploads+=1
            return FakeResponse({"code":0,"data":{"file_token":f"file_{self.uploads}"}})
        return FakeResponse({"code":0,"data":{"task_id":"task_123"}})

    def get(self,url,**kwargs):
        self.calls.append(("GET",url,kwargs))
        if url.endswith("/tasks/task_123"):
            return FakeResponse({"code":0,"data":{"status":"success",
                 "output":{"model_url":"https://cdn.tripo3d.ai/assets/abc.glb"},
                 "credits_consumed":40}})
        return FakeResponse(data=make_glb())


@pytest.fixture
def refs(tmp_path):
    folder=tmp_path/"character"
    project=create_project(folder,"Crocodile")
    original=tmp_path/"original.png"
    Image.new("RGB",(1491,1055),(44,64,75)).save(original)
    source=import_reference(folder,project,original,role="full_turnaround")
    out=folder/"derived"/"turnaround"
    out.mkdir(parents=True)
    import hashlib
    views={}
    for name in ("front","left_profile","back","right_profile","three_quarter"):
        path=out/(name+".png")
        Image.new("RGB",(320,640),(17,44,78)).save(path)
        views[name]={"file":str(path.relative_to(folder)),
                     "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (folder/"derived"/"turnaround_manifest.json").write_text(
        json.dumps({"views":views}),encoding="utf-8")
    return folder


def test_no_private_upload_or_billing_without_both_approvals(refs):
    session=MeshySession()
    views=load_views(refs)
    p=MultiViewProvider("meshy",api_key="test-only",session=session)
    with pytest.raises(PermissionError):
        p.submit(views,allow_image_upload=True,allow_paid_generation=False)
    assert session.calls==[]
    state=run_multiview_job(refs,"meshy",session=session)
    assert state["status"]=="BLOCKED"
    assert session.calls==[]


def test_meshy_real_contract_mock(refs,tmp_path):
    session=MeshySession()
    client=MultiViewProvider("meshy",api_key="test-only",session=session)
    task=client.submit(load_views(refs),allow_image_upload=True,allow_paid_generation=True)
    assert task=="01-task"
    payload=session.calls[0][2]["json"]
    assert payload["ai_model"]=="meshy-7.1"
    assert len(payload["image_urls"])==4
    assert payload["image_urls"][0].startswith("data:image/png;base64,")
    result=client.poll(task)
    assert result["status"]=="SUCCESS"
    output=client.download_model(result["download_url"],tmp_path/"model.glb")
    assert output["glb"]["meshes"]==1
    assert (tmp_path/"model.glb").is_file()


def test_tripo_real_contract_mock(refs,tmp_path):
    session=TripoSession()
    client=MultiViewProvider("tripo",api_key="test-only",session=session)
    task=client.submit(load_views(refs),allow_image_upload=True,allow_paid_generation=True)
    assert task=="task_123"
    assert session.uploads==4
    request=session.calls[4][2]["json"]
    assert [next(iter(x)) for x in request["inputs"]]==["front","left","back","right"]
    assert request["model"]=="v3.1-20260211"
    out=client.poll(task)
    assert out["status"]=="SUCCESS"
    result=client.download_model(out["download_url"],tmp_path/"model.glb")
    assert result["glb"]["meshes"]==1


def test_reject_untrusted_model_artifact(tmp_path):
    for url in ("http://assets.meshy.ai/model.glb",
                "https://127.0.0.1/internal",
                "https://assets.meshy.ai.evil.example/steal.glb"):
        with pytest.raises(ReconstructionError):
            _approved_host(url)


def test_reference_mutation_refused(refs):
    folder=refs
    entry=folder/"derived"/"turnaround"/"front.png"
    entry.write_bytes(b"tampered")
    with pytest.raises(ReconstructionError):
        load_views(folder)
