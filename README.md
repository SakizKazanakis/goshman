# GOSHMAN (development alpha)

**GOSHMAN is a Windows-oriented, reference-driven character production application.** It targets a robotic crocodile cowboy created for an independently developed Clickteam Fusion 2.5 fangame. This is an **alpha codebase**, not a finished character nor an already verified `.exe`.

## What is implemented in source code

- Project creation and versioned JSON specifications with atomic writes.
- Image reference import with hashing, copy-on-import, and alteration detection (no images committed to public GitHub).
- PySide6 desktop interface for project/reference management, adjustable geometry parameters and Blender invocation via `QProcess`.
- A procedural Blender Python scene builder covering body, head/snout, jaw, eyes, hat/stars, vest, metal joints, legs/boots, articulated arms/fingers and seven-segment tail. Uses real mesh objects, PBR node materials and named armature bones.
- Prototype transform-based Blender Actions for idle, jaw opening, jumpscare, look-left, angry, wave, tail sway, walk, attack, A-pose and T-pose.
- Optional FBX/GLB export, transparent PNG rendering, deterministic sprite atlas assembly and Clickteam import metadata.
- Explicitly opt-in OpenAI Responses API vision planner with structured JSON schema, and localhost ComfyUI API-workflow connector.
- Windows packaging script, command-line interface and pytest suite.

## What is NOT yet demonstrated

Blender is unavailable in the current build container; therefore Blender script execution, mesh quality, actual 3D rig motion, GLB/FBX export, GPU inference and the Windows .exe **have not been tested**. The Blender generator currently creates a procedural *first-pass* character, not a high-fidelity scan of supplied reference images. GPT and ComfyUI adapters are coded but untested with live keys/models. Local 3D preview is not yet implemented; view GLB in an external viewer. The JSON sprite hotspot/action point **must be manually applied in Clickteam**. Blender screenshot/render output is not part of CI.

## Windows quick start

Install Python 3.12 x64 and the official Blender version tested with your scene. Open PowerShell in a local checkout:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[gui,ai,test]"
.venv\Scripts\python.exe -m goshman.gui
```

Create a project in the GUI, import your reference images locally, set Blender executable and click **Create 3D model**. Alternatively:

```powershell
.venv\Scripts\python.exe -m goshman.cli new projects\crocodile
.venv\Scripts\python.exe -m goshman.cli reference projects\crocodile C:\Images\head.png --role head
.venv\Scripts\python.exe -m goshman.cli generate projects\crocodile --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --render
.venv\Scripts\python.exe -m goshman.cli check projects\crocodile
```

If Blender rendered PNG sequences, the application collects atlases after the Blender process finishes. To pack a sequence manually:

```powershell
.venv\Scripts\python.exe -m goshman.cli atlas projects\crocodile\output\sprites\idle projects\crocodile\output\sprites\idle_sheet.png --name idle --fps 24
```

The *project.json* and user references are kept local. **Never commit API credentials or unlicensed reference images.** For GPT set `OPENAI_API_KEY` in the current user's environment or store it securely in Windows Credential Manager using `goshman.ai.save_api_key()`.

### Tests and Windows artifact

```powershell
.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

`build_windows.ps1` produces an unpacked `dist/GOSHMAN/` folder **only when executed on a compatible Windows build machine**; it does not bundle Blender or independently prove Windows runtime success.

## Architecture and limitations

- `goshman/project.py` — project data, reference integrity.
- `goshman/blender_generate.py` — actual Blender geometry, rigging and animation action source.
- `goshman/backend.py` — controlled subprocess execution.
- `goshman/gui.py` — PySide6 desktop application.
- `goshman/ai.py` — OpenAI Responses vision planner; external sharing requires explicit checkbox.
- `goshman/comfy.py` — localhost-only ComfyUI workflow adapter. It requires user-provided compatible API-format graph and actual installed model nodes.
- `goshman/export.py` — atlas and manifest for Fusion.
- `docs/STATUS.md` — phase audit and evidence.

**Next gate:** Execute Blender 5.x locally, fix any version-specific API errors, verify generated scene and actions, inspect the renders against the 12 references, then test Windows packaging and Clickteam import.

## Upstream resources (not vendored)

- [Blender](https://www.blender.org/) — geometry/rigging/render (GPL).
- [OpenAI API](https://developers.openai.com/api/docs/guides/structured-outputs) — optional vision planning; API usage may incur charges.
- [Sprite Sheet Maker](https://github.com/ManasMakde/SpriteSheetMaker) — inspiration/optional integration; inspect bundled code license before redistributing.
- [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) — optional separate GPU backend, not bundled.
- [ComfyUI](https://github.com/Comfy-Org/ComfyUI) — optional external workflow server, not bundled.
- [Clickteam Fusion](https://www.clickteam.com/clickteam-fusion-2-5) — end target; no automatic project injection is claimed.

## Rights and redistribution

No license has yet been selected for this new repository. Do not presume permission to redistribute the source code or user reference images. External components and models have independent terms.
