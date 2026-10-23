# GOSHMAN development status — 2026-10-23

Status is based on reproducible results from GitHub Actions, not solely on source-code presence. **This is an alpha development build, not a reference-faithful finished character.**

## Verified evidence

- Python unit tests: 12/12 PASS on Linux and Windows CI.
- Linux runner downloaded Blender 5.2.3 LTS from the official host and verified SHA-256.
- Actual headless Blender scene generation succeeded: 170 mesh objects, 35 armature bones, 11 animation Actions, 10 mesh materials. Files `.blend`, `.glb`, `.fbx` were exported and uploaded as GitHub Actions artifacts.
- GLB file parsed as a valid glTF 2.0 container and confirmed 170 meshes, 1 skin/35 joints, 11 animations.
- Windows Server 2022 runner assembled `dist/GOSHMAN/GOSHMAN.exe` with PyInstaller. Source GUI `QApplication`/`Window` offscreen smoke test passed.
- Additional CI gates: packaged `.exe` offscreen smoke test and actual Blender front PNG render. Their result must be read from the latest GitHub Actions run; implementation alone is NOT a PASS.
- Public repository does not contain user-supplied reference images, local projects, or private API keys.

## Phase matrix

| Phase | Verified status | Remaining work |
| --- | --- | --- |
| 00 source and environment audit | PASS | Windows end-user device and GPU profile not known |
| 01 repository, dependencies, unit tests | PASS | Expand coverage/quality checks |
| 02 PySide6 Windows GUI | PARTIAL | GUI source startup PASS; basic 3D viewport and Qt unit-test code present; final user's Windows UX/feature QA needed |
| 03 true procedural geometry | PARTIAL | 170 real meshes exported; visual fidelity not met |
| 04 detailed geometry and materials | PARTIAL | primitive solids, 10 plain PBR material nodes; no texture maps, detailed scales, correct topology |
| 05 animation and rigging | PARTIAL | 35 bones, 11 Actions exported; not all requested expressions and poses or quality checks |
| 06 Clickteam export | PARTIAL | FBX/GLB created, PNG atlas packer validated; real engine import not tested |
| 07 GPT structured analysis | SOURCE ONLY | real API key/permissioned vision request and user-confirmed analysis needed |
| 08 neural Image-to-3D | ADAPTER ONLY | ComfyUI workflow, model weights, compatible NVIDIA GPU and output validation absent |
| 09 Windows packaging | PARTIAL | PyInstaller artifact built, bundled .exe smoke verification pending latest CI |
| 10 acceptance | NOT COMPLETE | user-reviewed renders, Clickteam integration and scene visual accuracy required |

## Core limitation

The current model is a **blockout driven by hard-coded geometry formulas plus adjustable dimensions**. Reference sheets are securely imported and catalogued; they do not yet directly reconstruct topology or details. GPT can optionally generate a parameter specification but does not generate a detailed 3D mesh. At present, the Windows application requires Blender installed separately for 3D generation. A basic Qt software-rendered GLB orbit/zoom viewer is now implemented; textured PBR, precise depth buffer, and final UX acceptance are absent.

## GitHub Actions

- Most recent complete green run with generated Blender assets and Windows packaging: https://github.com/SakizKazanakis/goshman/actions/runs/40021230806
- Runs for packaged .exe smoke test and Blender PNG preview: https://github.com/SakizKazanakis/goshman/actions

All third-party runtimes/models remain separately installed and licensed. No Windows binary is signed. Windows executable execution on a consumer PC with installed Blender has not been tested.
