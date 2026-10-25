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
                    render: bool = False, export: bool = True, size: int = 512,
                    pbr_resolution: int = 256) -> list[str]:
    project_folder = project_folder.resolve(strict=True)
    project = load_project(project_folder)
    project.spec.validate()
    problems = verify_references(project_folder, project)
    if problems:
        raise ValueError("; ".join(problems))
    if pbr_resolution not in (0, 256, 512, 1024, 2048):
        raise ValueError("PBR resolution must be 0, 256, 512, 1024, or 2048")
    if not 128 <= size <= 4096:
        raise ValueError("Invalid render size")
    script = Path(__file__).with_name("blender_generate.py").resolve()
    return [str(find_blender(blender_path)), "--background", "--factory-startup", "--python-exit-code", "31", "--python", str(script), "--",
            "--project", str(project_folder), "--size", str(size),
            "--render", "1" if render else "0", "--export", "1" if export else "0",
            "--pbr-resolution", str(pbr_resolution)]


def run_blender(project_folder: Path, blender_path: str | None = None, render: bool = False,
                export: bool = True, size: int = 512, timeout: int = 1800,
                pbr_resolution: int = 256) -> subprocess.CompletedProcess:
    cmd = blender_command(project_folder, blender_path, render, export, size, pbr_resolution)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False, check=False)


def import_external_glb(source: Path, destination: Path, *,
                        blender_path: str | None = None, height: float = 6.2,
                        timeout: int = 900) -> subprocess.CompletedProcess:
    """Convert an actually existing external AI GLB to editable .blend via Blender."""
    source = Path(source).resolve(strict=True)
    from .quality import inspect_glb
    if inspect_glb(source)["meshes"] < 1:
        raise ValueError("External asset has no meshes")
    destination = Path(destination).resolve()
    if destination.suffix.lower() != ".blend":
        raise ValueError("Destination must be a .blend file")
    script = Path(__file__).with_name("blender_import_ai.py")
    cmd = [str(find_blender(blender_path)), "--background", "--factory-startup",
           "--python-exit-code", "31", "--python", str(script), "--",
           "--source", str(source), "--destination", str(destination),
           "--height", str(height)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          shell=False, check=False)



def run_cycles_bake(scene: Path, high: str, low: str, output: Path, *,
                    blender_path: str | None = None, resolution: int = 1024,
                    timeout: int = 3600) -> subprocess.CompletedProcess:
    """Real source high-poly -> target low-poly Cycles bake (not synthetic PBR)."""
    scene=Path(scene).resolve(strict=True)
    if scene.suffix.lower()!=".blend":
        raise ValueError("High/low source scene must be a Blender .blend file")
    output=Path(output).resolve()
    if resolution not in (64,128,256,512,1024,2048,4096):
        raise ValueError("Bake resolution unsupported")
    if not high or not low or high==low or len(high)>128 or len(low)>128:
        raise ValueError("Two distinct Blender mesh object names are required")
    script=Path(__file__).with_name("blender_bake.py")
    cmd=[str(find_blender(blender_path)),"--background","--factory-startup",
         "--python-exit-code","31","--python",str(script),"--",
         "--scene",str(scene),"--high",high,"--low",low,
         "--output",str(output),"--resolution",str(resolution)]
    return subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,
                          shell=False,check=False)



def render_reference_views(model: Path, output: Path, *,
                           blender_path: str | None = None,
                           width: int = 320, height: int = 640,
                           samples: int = 4,
                           timeout: int = 1800) -> subprocess.CompletedProcess:
    """Render 5 orthographic Blender images for independent reference QA."""
    model=Path(model).resolve(strict=True)
    output=Path(output).resolve()
    if model.suffix.lower() not in (".glb",".blend"):
        raise ValueError("Render target must be actual GLB or Blender scene")
    if not(128<=width<=2048 and 128<=height<=4096 and 1<=samples<=128):
        raise ValueError("Invalid render size or samples")
    script=Path(__file__).with_name("blender_render_views.py").resolve()
    cmd=[str(find_blender(blender_path)),"--background","--factory-startup",
         "--python-exit-code","31","--python",str(script),"--",
         "--model",str(model),"--output",str(output),
         "--width",str(width),"--height",str(height),"--samples",str(samples)]
    return subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,
                          shell=False,check=False)
