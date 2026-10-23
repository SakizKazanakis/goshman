"""Isolated Blender subprocess adapter: never pass unchecked paths to a shell."""
from __future__ import annotations
from pathlib import Path
import subprocess
import sys
import json
import shutil
from .project import load_project, verify_references


def find_blender(user_path: str | None = None) -> Path:
    candidates = [user_path, shutil.which("blender")]
    if sys.platform == "win32":
        root = Path(r"C:\Program Files\Blender Foundation")
        candidates.extend(str(p) for p in sorted(root.glob("Blender */blender.exe"), reverse=True))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError("Blender executable not detected; specify --blender")


def blender_command(project_folder: Path, blender_path: str | None = None,
                    render: bool = False, export: bool = True, size: int = 512) -> list[str]:
    project_folder = project_folder.resolve(strict=True)
    project = load_project(project_folder)
    project.spec.validate()
    problems = verify_references(project_folder, project)
    if problems:
        raise ValueError("; ".join(problems))
    if not 128 <= size <= 4096:
        raise ValueError("Invalid render size")
    script = Path(__file__).with_name("blender_generate.py").resolve()
    return [str(find_blender(blender_path)), "--background", "--factory-startup", "--python-exit-code", "31", "--python", str(script), "--",
            "--project", str(project_folder), "--size", str(size),
            "--render", "1" if render else "0", "--export", "1" if export else "0"]


def run_blender(project_folder: Path, blender_path: str | None = None, render: bool = False,
                export: bool = True, size: int = 512, timeout: int = 1800) -> subprocess.CompletedProcess:
    cmd = blender_command(project_folder, blender_path, render, export, size)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False, check=False)
