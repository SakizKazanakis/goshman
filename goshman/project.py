"""Safe persistent project representation and immutable reference import."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import tempfile
import uuid

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class Reference:
    id: str
    filename: str
    sha256: str
    width: int
    height: int
    role: str = "unclassified"


@dataclass
class CharacterSpec:
    name: str = "Animatronic Crocodile Cowboy"
    kind: str = "mechanical crocodile"
    height: float = 6.2
    head_scale: float = 1.0
    snout_length: float = 1.0
    tail_length: float = 2.4
    eye_scale: float = 1.0
    armor_detail: int = 2
    palette: dict = field(default_factory=lambda: {
        "scales": "#59892b", "belly": "#dab967", "leather": "#794026",
        "metal": "#869293", "gold": "#e9b324", "mouth": "#63212a",
    })

    def validate(self) -> None:
        for key in ("height", "head_scale", "snout_length", "tail_length", "eye_scale"):
            value = getattr(self, key)
            if not isinstance(value, (int, float)) or not (0.15 <= value <= 20):
                raise ValueError(f"{key} out of allowed range")
        if self.armor_detail not in (0, 1, 2, 3):
            raise ValueError("armor_detail must be 0..3")
        if not self.name.strip() or len(self.name) > 120:
            raise ValueError("Invalid character name")
        for color in self.palette.values():
            if not isinstance(color, str) or len(color) != 7 or color[0] != "#" or any(c not in "0123456789abcdefABCDEF" for c in color[1:]):
                raise ValueError("Palette colors must be #RRGGBB")


@dataclass
class Project:
    project_id: str
    name: str
    created_at: str
    references: list[Reference] = field(default_factory=list)
    spec: CharacterSpec = field(default_factory=CharacterSpec)
    version: int = 1


def atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as f:
            tmp = Path(f.name)
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()


def create_project(folder: Path, name: str) -> Project:
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / "project.json"
    if manifest.exists():
        raise FileExistsError("Project manifest already exists")
    p = Project(str(uuid.uuid4()), name, datetime.now(timezone.utc).isoformat())
    save_project(folder, p)
    return p


def save_project(folder: Path, project: Project) -> None:
    project.spec.validate()
    data = asdict(project)
    atomic_json(folder / "project.json", data)


def load_project(folder: Path) -> Project:
    d = json.loads((folder / "project.json").read_text(encoding="utf-8"))
    if d.get("version") != 1:
        raise ValueError("Unsupported project schema")
    spec = CharacterSpec(**d["spec"])
    spec.validate()
    return Project(d["project_id"], d["name"], d["created_at"],
                   [Reference(**r) for r in d.get("references", [])], spec, d["version"])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_reference(folder: Path, project: Project, original: Path, role: str = "unclassified") -> Reference:
    from PIL import Image
    original = original.resolve(strict=True)
    if original.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError("Unsupported reference file format")
    with Image.open(original) as im:
        im.verify()
    with Image.open(original) as im:
        width, height = im.size
    if width * height > 120_000_000:
        raise ValueError("Image dimensions exceed limit")
    digest = sha256_file(original)
    for item in project.references:
        if item.sha256 == digest:
            return item
    dest = folder / "references" / f"{digest[:16]}{original.suffix.lower()}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, dest)
    record = Reference(str(uuid.uuid4()), str(dest.relative_to(folder)), digest, width, height, role)
    project.references.append(record)
    save_project(folder, project)
    return record


def verify_references(folder: Path, project: Project) -> list[str]:
    problems = []
    for record in project.references:
        path = (folder / record.filename).resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file():
            problems.append(f"Missing or unsafe reference: {record.filename}")
        elif sha256_file(path) != record.sha256:
            problems.append(f"Changed reference: {record.filename}")
    return problems
