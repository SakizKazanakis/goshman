# GOSHMAN — Animatronic 3D Character Studio (development alpha)

**GOSHMAN** is an experimental Windows x64 desktop application for producing a real procedural 3D robot-crocodile cowboy and exporting assets for Clickteam Fusion 2.5. The working model is a **geometric blockout**. This repository is not a finished, reference-accurate fan-game character generator.

## Proven functionality

- Project JSON, validated parameter specification, atomic saves, and copy-on-import user references with SHA-256 integrity checks.
- PySide6 graphical Windows desktop shell (project/reference management, adjustable proportions, Blender subprocess, logging, cancellation, export UI and opt-in GPT reference analysis). Basic interactive GLB polygon viewport supports orbit and zoom (software shading, not Blender-grade display).
- Blender 5.2.3 LTS actual headless execution: **at least 170 mesh objects, 39 bones, 26 animation Actions and 10 node-based materials**; successful `.blend`, `.glb` and `.fbx` export.
- `Pillow` sprite sequence packing to PNG atlas with Clickteam Fusion JSON metadata; verified by unit tests. A true PNG front-view preview is rendered automatically by the generator in the latest codebase; see GitHub Actions for test status.
- Unit tests pass in Linux and Windows CI; real Linux Blender generation and Windows Qt / packaged EXE smoke tests pass. Updated run: https://github.com/SakizKazanakis/goshman/actions/runs/40080425782.
- Optional OpenAI Responses API JSON-schema image analysis with explicit per-session user consent; ComfyUI localhost workflow queue adapter. Live AI inference is not tested or included.

## Not yet completed

- Reconstruction of user-supplied reference detail is **not achieved**: the current geometry is parametric and simplified, not an accurate crocodile sculpt.
- Texture-image baking and reference-accurate scales, leather, stitching, complete articulated finger mechanics and quality-validated facial acting. The new 26 Actions remain procedural test poses.
- High-quality PBR/texture mapping in the interactive viewport and direct Fusion project injection. The initial mesh viewer is software-projected, with flat material colors and approximate visibility; PNG import into Clickteam still manual and JSON hotspot metadata is not applied automatically.
- Frame-by-frame visual QA for all 26 Actions, consumer-PC Windows installation, live GPT requests and end-to-end ComfyUI TRELLIS.2 output.
- No bundled Blender binary, no neural model weights, no API keys and no 12 copyrighted/user-supplied PNG images committed into the public repo.

See [docs/STATUS.md](docs/STATUS.md) for an evidence-based phase status matrix.

## Download / launch

For an automatically produced Windows build, open [GitHub Actions](https://github.com/SakizKazanakis/goshman/actions), select a successful recent `GOSHMAN CI` workflow, and download its **goshman-windows-2022** artifact. Extract all archive contents (do not remove `_internal/`) and launch `GOSHMAN.exe`. This is an **unsigned alpha binary**. Blender is still required separately for 3D geometry generation.

Alternatively install official Blender 5.2.3 LTS and Python 3.12 x64, then in Windows PowerShell from a cloned repository:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[gui,ai,test]"
.venv\Scripts\python.exe -m goshman.gui
```

Create or open a GOSHMAN project, import private local images, select `blender.exe`, and click "СОЗДАТЬ 3D-МОДЕЛЬ В BLENDER". Or use CLI:

```powershell
.venv\Scripts\python.exe -m goshman.cli new projects\crocodile
.venv\Scripts\python.exe -m goshman.cli generate projects\crocodile --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --render
.venv\Scripts\python.exe -m goshman.cli check projects\crocodile
```

Generated output lives in `projects\crocodile\output\`. A complete `.blend`, `.glb` and `.fbx` can be examined in Blender or another compatible 3D viewer. Optional PNG sprite sequences can be packed using the desktop interface or:

```powershell
.venv\Scripts\python.exe -m goshman.cli atlas projects\crocodile\output\sprites\idle projects\crocodile\output\sprites\idle_sheet.png --name idle --fps 24
```

## Modules

| File | Role |
| --- | --- |
| `goshman/project.py` | Project JSON, hash/integrity verification of references |
| `goshman/blender_generate.py` | Blender geometry, skeleton, Actions, export, PNG preview/render |
| `goshman/backend.py` | Controlled Blender subprocess without shell interpolation |
| `goshman/gui.py` | PySide6 desktop UI |
| `goshman/preview.py` | Simple interactive Qt software 3D GLB mesh viewer |
| `goshman_app.py` | PyInstaller-safe Windows `.exe` launcher and smoke mode |
| `goshman/ai.py` | Strict opt-in GPT / OpenAI Responses analysis |
| `goshman/comfy.py` | Local ComfyUI custom API-workflow connector |
| `goshman/export.py` | Deterministic PNG atlas and Clickteam metadata |
| `goshman/quality.py` | Read-only Blender/GLB/PNG structural export validation |
| `.github/workflows/ci.yml` | Linux Blender 5.2.3 and Windows packaged app tests |

## UV PBR maps and multi-view reference preparation

The Blender generator now synthesizes four real UV texture channels (base colour,
roughness, metallic and tangent-space normal) for its ten procedural materials.
Select **256, 512, 1024 or 2048 px** in the Windows interface, or use
`python -m goshman.cli generate crocodile_project --pbr-resolution 2048`.
Material maps are saved under `output/pbr/`, included in `.blend` and
linked inside the exported `.glb`. These maps are generated from a
deterministic recipe, **not** a high-poly-to-low-poly Cycles bake, and do not
copy texture pixels or precise shape from the provided character reference.

For the private 1491×1055 full-body turnaround sheet included with the
crocodile project, `python -m goshman.cli prepare-views crocodile_project`
creates cropped front, left, back, right and three-quarter source panels under
`derived/turnaround/` and records image hashes. This cropping does not imply
calibrated orthographic photographs or complete 3D reconstruction.

Full acceptance status and unverified Clickteam/AI stages:
[docs/ACCEPTANCE_2026-10-24.md](docs/ACCEPTANCE_2026-10-24.md).

## Structural export audit

Run `python -m goshman.cli audit projects\\crocodile` after generation, or use the GUI's
**Проверить экспорт** control. It validates reference hashes, nonempty native exports,
binary glTF 2.0 meshes/skins/animations, preview alpha and sprite sequences. It reports
`PASS_TECHNICAL` only for structural correctness; it does not assert reference fidelity,
successful import into Clickteam Fusion or accurate PBR textures in other renderers.

Character height and segmented tail length now affect actual Blender geometry rather
than merely stored UI parameters. The hat has curved brim geometry and fangs are conical;
procedural material bump remains Blender-specific until texture baking is implemented.
GPT reference requests include reference roles; returned parameters require user approval
before overwriting the existing character specification. Keys can be saved through the
system keyring.

## Key safety / redistribution notes

Never commit OpenAI API keys or private/user-licensed reference images. External AI endpoints require consent, and AI provider/network access may cost money. GOSHMAN does not silently download neural weights. Keep all extracted PyInstaller files together; never execute unsigned untrusted binaries. Third-party dependencies have separate licenses. **This repository has no project software license assigned.**

Relevant sources: [Blender](https://www.blender.org/), [OpenAI API](https://developers.openai.com/api/docs/guides/structured-outputs), [ComfyUI](https://github.com/Comfy-Org/ComfyUI), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), [Clickteam](https://www.clickteam.com/clickteam-fusion-2-5).
