"""Explicit, opt-in OpenAI vision planner. The LLM never receives filesystem access."""
from __future__ import annotations
from pathlib import Path
import base64
import os
import mimetypes
import json
from .project import CharacterSpec

ALLOWED_FIELDS = ["name", "kind", "height", "head_scale", "snout_length", "tail_length", "eye_scale", "armor_detail"]


def response_schema() -> dict:
    return {"type": "object", "additionalProperties": False,
            "properties": {**{field: {"type": "string" if field in ("name", "kind") else "integer" if field == "armor_detail" else "number"} for field in ALLOWED_FIELDS},
                           "uncertainties": {"type": "array", "items": {"type": "string"}}},
            "required": ALLOWED_FIELDS + ["uncertainties"]}


def analyze_references(image_paths: list[Path], model: str, *, consent: bool = False, roles: list[str] | None = None) -> dict:
    if not consent:
        raise PermissionError("External image transmission needs explicit consent")
    if not image_paths or len(image_paths) > 12:
        raise ValueError("Provide 1..12 images")
    if roles is not None and len(roles) != len(image_paths):
        raise ValueError("Reference role count does not match image count")
    from openai import OpenAI
    content = [{"type": "input_text", "text": (
        "Analyze these multi-view references of ONE mechanical crocodile cowboy. "
        "Return one parameterized character description with consistent proportions. "
        "Do not invent unseen mechanisms; mention ambiguity in uncertainties. "
        "Geometry values: height 6.2 units, head scale 0.5..2, snout length 0.5..2, "
        "tail length 1..4, eye scale 0.5..2, armor detail 0..3.")}]
    for index, image in enumerate(image_paths):
        role = roles[index] if roles else "unclassified"
        if not isinstance(role, str) or len(role) > 80:
            raise ValueError("Invalid reference role")
        content.append({"type": "input_text", "text": f"Reference {index+1}, role: {role}. Treat panels and close-ups as one consistent character; never infer absolute measurements without scale."})
        if image.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ValueError("Unsupported image format")
        if image.stat().st_size > 15_000_000:
            raise ValueError("Image file too large")
        mime = mimetypes.guess_type(image.name)[0] or "image/png"
        data = base64.b64encode(image.read_bytes()).decode("ascii")
        content.append({"type": "input_image", "image_url": f"data:{mime};base64,{data}", "detail": "high"})
    response = OpenAI(api_key=get_api_key(), timeout=90).responses.create(model=model,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_schema", "name": "character_parameters", "strict": True, "schema": response_schema()}})
    parameters = json.loads(response.output_text)
    spec = CharacterSpec(**{k: parameters[k] for k in ALLOWED_FIELDS})
    spec.validate()
    return {"spec": spec, "uncertainties": parameters["uncertainties"], "model": model, "response_id": response.id}


def save_api_key(key: str) -> None:
    # Optional keyring delegates to the Windows Credential Manager on Windows.
    import keyring
    keyring.set_password("GOSHMAN", "OPENAI_API_KEY", key)


def get_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        import keyring
        return keyring.get_password("GOSHMAN", "OPENAI_API_KEY")
    except ImportError:
        return None
