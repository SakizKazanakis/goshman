"""Constrained ComfyUI local adapter. No claim of ready-made TRELLIS workflow."""
from __future__ import annotations
import ipaddress
import json
from urllib.parse import urlparse
import uuid
import requests


def validate_local_endpoint(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password or parsed.path not in ("", "/"):
        raise ValueError("Only base URL of local ComfyUI is accepted")
    if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("ComfyUI endpoint must be localhost")
    return url.rstrip("/")


def ping(endpoint: str = "http://127.0.0.1:8188") -> dict:
    base = validate_local_endpoint(endpoint)
    response = requests.get(base + "/system_stats", timeout=4)
    response.raise_for_status()
    return response.json()


def queue_verified_workflow(workflow: dict, endpoint: str = "http://127.0.0.1:8188") -> dict:
    """Submit a user-imported ComfyUI API workflow, never invent model node IDs."""
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("Nonempty ComfyUI API-format workflow required")
    for id, node in workflow.items():
        if not isinstance(node, dict) or "class_type" not in node or "inputs" not in node:
            raise ValueError(f"Invalid ComfyUI API workflow node: {id}")
    base = validate_local_endpoint(endpoint)
    response = requests.post(base + "/prompt", json={"prompt": workflow, "client_id": str(uuid.uuid4())}, timeout=15)
    response.raise_for_status()
    return response.json()
