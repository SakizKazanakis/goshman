"""Opt-in multi-view to real mesh adapters (Meshy 7.1 and Tripo v3).

Never transmits private reference images or spends API credits unless BOTH
the image-transfer and paid-operation gates are explicitly acknowledged.
Task metadata and actual GLB mesh artifacts are persisted separately.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests
from PIL import Image

from .project import atomic_json, load_project, verify_references
from .quality import inspect_glb

VIEWS = ("front", "left", "back", "right")
MESHY_BASE = "https://api.meshy.ai/openapi/v1/multi-image-to-3d"
TRIPO_BASE = "https://openapi.tripo3d.com/v3"
ALLOWED_DOWNLOAD_HOSTS = ("assets.meshy.ai", "cdn.tripo3d.ai", "tripo3d.ai",
                          "meshy.ai", "meshycdn.com")
MAX_MODEL_BYTES = 250 * 1024 * 1024


class ReconstructionError(RuntimeError):
    pass


def load_views(folder: Path) -> dict[str, Path]:
    """Only use verified private files created from the supplied turnaround."""
    folder = folder.resolve(strict=True)
    project = load_project(folder)
    errors = verify_references(folder, project)
    if errors:
        raise ReconstructionError("Reference integrity mismatch: " + "; ".join(errors))
    manifest = folder / "derived" / "turnaround_manifest.json"
    if not manifest.is_file():
        raise ReconstructionError("Prepare the five turnaround views first")
    record = json.loads(manifest.read_text(encoding="utf-8"))
    items = record.get("views") or record.get("panels")
    if not isinstance(items, dict):
        raise ReconstructionError("Invalid multiview manifest")
    result: dict[str, Path] = {}
    for role, input_role in (("front", "front"), ("left", "left_profile"),
                             ("back", "back"), ("right", "right_profile")):
        entry = items.get(input_role)
        if not isinstance(entry, dict):
            raise ReconstructionError(f"Missing multiview angle: {role}")
        rel = entry.get("file", f"derived/turnaround/{input_role}.png")
        full = (folder / rel).resolve(strict=True)
        if not full.is_relative_to(folder) or full.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ReconstructionError("Unsafe or invalid image path")
        digest = hashlib.sha256(full.read_bytes()).hexdigest()
        expected = entry.get("sha256")
        if expected and expected != digest:
            raise ReconstructionError(f"Reference crop was modified: {role}")
        if full.stat().st_size > 20_000_000:
            raise ReconstructionError(f"Reference image too large: {role}")
        with Image.open(full) as image:
            image.verify()
        result[role] = full
    return result


def _json_response(response, provider: str) -> dict:
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ReconstructionError(provider + ": invalid API response")
    if provider == "tripo":
        if result.get("code") != 0:
            raise ReconstructionError("Tripo API error: " + str(result.get("message", "unknown")))
        if not isinstance(result.get("data"), dict):
            raise ReconstructionError("Tripo API response is missing data")
        return result["data"]
    return result


def _approved_host(url: str) -> str:
    target = urlsplit(url)
    if target.scheme != "https" or target.username or target.password or not target.hostname:
        raise ReconstructionError("Model download must use an HTTPS provider asset URL")
    host = target.hostname.lower()
    if not any(host == h or host.endswith("." + h) for h in ALLOWED_DOWNLOAD_HOSTS):
        raise ReconstructionError("Untrusted model artifact host: " + host)
    return host


class MultiViewProvider:
    def __init__(self, provider: str, api_key: str | None = None, session=None):
        if provider not in ("meshy", "tripo"):
            raise ValueError("Supported providers: meshy and tripo")
        self.provider = provider
        env = "MESHY_API_KEY" if provider == "meshy" else "TRIPO_API_KEY"
        self.key = api_key or os.getenv(env)
        self.session = session or requests.Session()

    @property
    def headers(self) -> dict:
        if not self.key:
            raise ReconstructionError("API key is not configured for " + self.provider)
        return {"Authorization": "Bearer " + self.key}

    def submit(self, views: dict[str, Path], *, allow_image_upload: bool = False,
               allow_paid_generation: bool = False) -> str:
        if not allow_image_upload or not allow_paid_generation:
            raise PermissionError("Both private-image upload and paid-generation approval are mandatory")
        if set(views) != set(VIEWS):
            raise ValueError("Exactly four named views are required: " + ", ".join(VIEWS))
        if self.provider == "meshy":
            data_uris = []
            for role in VIEWS:
                path = Path(views[role])
                if path.stat().st_size > 20_000_000:
                    raise ReconstructionError("Meshy image too large")
                suffix = path.suffix.lower()
                mime = {"png": "image/png", "jpg": "image/jpeg",
                        "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix.lstrip("."))
                if not mime:
                    raise ValueError("Unsupported source image type")
                data_uris.append(f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}")
            payload = {"image_urls": data_uris, "ai_model": "meshy-7.1",
                       "geometry_resolution": "2k", "should_texture": True,
                       "enable_pbr": True, "target_formats": ["glb"]}
            response = self.session.post(MESHY_BASE, headers=self.headers,
                                         json=payload, timeout=45)
            value = _json_response(response, "meshy").get("result")
        else:
            tokens = {}
            for role in VIEWS:
                path = Path(views[role])
                if path.stat().st_size > 20_000_000:
                    raise ReconstructionError("Tripo image too large")
                with path.open("rb") as handle:
                    answer = self.session.post(TRIPO_BASE + "/files", headers=self.headers,
                           files={"file": (path.name, handle, "image/png")}, timeout=45)
                token = _json_response(answer, "tripo").get("file_token")
                if not isinstance(token, str) or not token:
                    raise ReconstructionError("Tripo did not return file_token")
                tokens[role] = token
            payload = {"inputs": [{role: tokens[role]} for role in VIEWS],
                       "model": "v3.1-20260211", "texture": True,
                       "pbr": True, "geometry_quality": "detailed"}
            response = self.session.post(TRIPO_BASE + "/generation/multiview-to-model",
                                         headers=self.headers, json=payload, timeout=45)
            value = _json_response(response, "tripo").get("task_id")
        if not isinstance(value, str) or not value or len(value) > 160 or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ReconstructionError("Provider returned invalid task identifier")
        return value

    def poll(self, task_id: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", task_id):
            raise ValueError("Invalid task identifier")
        url = (MESHY_BASE + "/" + task_id if self.provider == "meshy"
               else TRIPO_BASE + "/tasks/" + task_id)
        response = self.session.get(url, headers=self.headers, timeout=30)
        state = _json_response(response, self.provider)
        status = str(state.get("status", "")).lower()
        if status in ("succeeded", "success"):
            return {"status": "SUCCESS", "download_url": (
                (state.get("model_urls") or {}).get("glb") if self.provider == "meshy"
                else (state.get("output") or {}).get("model_url")),
                    "provider_status": status,
                    "credits_consumed": state.get("consumed_credits", state.get("credits_consumed"))}
        if status in ("failed", "cancelled", "canceled"):
            return {"status": "FAIL", "provider_status": status,
                    "error": str(state.get("task_error", state.get("error_message", "")))[:500]}
        if status in ("pending", "in_progress", "queued", "running"):
            return {"status": "RUNNING", "provider_status": status,
                    "progress": state.get("progress")}
        raise ReconstructionError("Unrecognized provider task status: " + status)

    def download_model(self, url: str, destination: Path) -> dict:
        _approved_host(url)
        destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_suffix(".glb.part")
        # Never pass bearer token to artifact CDN. Never silently follow a redirect.
        response = self.session.get(url, stream=True, timeout=(10, 90),
                                    allow_redirects=False)
        response.raise_for_status()
        if 300 <= response.status_code < 400:
            raise ReconstructionError("Unexpected model URL redirect")
        sha = hashlib.sha256()
        total = 0
        try:
            with temp.open("wb") as fp:
                for chunk in response.iter_content(1 << 20):
                    total += len(chunk)
                    if total > MAX_MODEL_BYTES:
                        raise ReconstructionError("Model artifact exceeds size limit")
                    fp.write(chunk)
                    sha.update(chunk)
            if total < 20:
                raise ReconstructionError("Provider did not return a GLB mesh")
            mesh = inspect_glb(temp)
            if mesh["meshes"] < 1:
                raise ReconstructionError("Downloaded glTF contains no meshes")
            temp.replace(destination)
            return {"sha256": sha.hexdigest(), "bytes": total, "glb": mesh,
                    "file": destination.name}
        finally:
            temp.unlink(missing_ok=True)


def run_multiview_job(folder: Path, provider: str, *, approve_upload: bool = False,
                      approve_billing: bool = False, api_key: str | None = None,
                      timeout_seconds: int = 900, poll_interval: int = 15,
                      session=None, sleep=time.sleep) -> dict:
    """One opt-in production job with immutable task ID and explicit blocking states."""
    folder = folder.resolve(strict=True)
    views = load_views(folder)
    client = MultiViewProvider(provider, api_key, session)
    digest = hashlib.sha256((provider + "|" + "|".join(
        hashlib.sha256(views[v].read_bytes()).hexdigest() for v in VIEWS)).encode()).hexdigest()
    result_dir = folder / "output" / "reconstruction" / provider / digest[:16]
    result_dir.mkdir(parents=True, exist_ok=True)
    state_path = result_dir / "job.json"
    state = {"provider": provider, "input_sha256": digest, "status": "PREFLIGHT",
             "view_roles": list(VIEWS), "actual_api_test": False}
    atomic_json(state_path, state)
    if not approve_upload or not approve_billing:
        state["status"] = "BLOCKED"
        state["reason"] = "Private image upload and paid generation require explicit authorization"
        atomic_json(state_path, state)
        return state
    if not client.key:
        state["status"] = "BLOCKED"
        state["reason"] = "No authorized provider API credential"
        atomic_json(state_path, state)
        return state
    previous = json.loads(state_path.read_text(encoding="utf-8"))
    task_id = previous.get("task_id")
    if task_id is None:
        task_id = client.submit(views, allow_image_upload=True, allow_paid_generation=True)
        state.update({"status": "RUNNING", "task_id": task_id, "actual_api_test": True})
        atomic_json(state_path, state)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() <= deadline:
        progress = client.poll(task_id)
        state.update(progress)
        atomic_json(state_path, state)
        if progress["status"] == "SUCCESS":
            url = progress.get("download_url")
            if not isinstance(url, str):
                state["status"] = "FAIL"
                state["reason"] = "Provider reports success but no GLB asset is available"
                atomic_json(state_path, state)
                return state
            artifact = client.download_model(url, result_dir / "model.glb")
            state.pop("download_url", None)  # Never persist signed provider URLs.
            state["artifact"] = artifact
            state["status"] = "PASS_TECHNICAL"
            atomic_json(state_path, state)
            return state
        if progress["status"] == "FAIL":
            state["status"] = "FAIL"
            return state
        sleep(poll_interval)
    state["status"] = "BLOCKED"
    state["reason"] = "Polling time budget exhausted; task may still be running remotely"
    atomic_json(state_path, state)
    return state
