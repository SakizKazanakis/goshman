# GOSHMAN development status — 2026-10-24

**Not a complete, reference-faithful 3D character generator.** All statuses below distinguish real runtime verification from unimplemented or untested requirements.

## Verification evidence

- Latest verified Linux Blender + Windows build: https://github.com/SakizKazanakis/goshman/actions/runs/40080425782 — both jobs **SUCCESS**.
- Actual Blender 5.2.3 LTS build: **at least 170 mesh objects, 39 bones, 26 Actions**, exported .blend, .fbx, .glb, actual RGBA front-view render.
- CI included nondefault `height = 7.44` (1.2x overall scale) and `tail_length = 3.6` (1.5x segment offset). Build report and exported glTF animation count passed assertions.
- Linux and Windows Python tests pass, Qt offscreen launch passes, PyInstaller folder EXE builds and passes headless self-test.
- Structural validation now checks references' SHA-256, GLB header/meshes/skins/animations, output files, PNG alpha and sprite dimensions. `python -m goshman.cli audit <project-directory>` reports `PASS_TECHNICAL` or `FAIL`; it never equates structural validity with visual fidelity.
- 12 private user-provided reference sheets were packaged as a local GOSHMAN project for conversation delivery; **none was committed to this public repository**.

## Phase matrix

| Phase | Status | Verified progress / still missing |
| --- | --- | --- |
| 00 Audit of code and tools | PASS for known environment | User's Windows GPU, VRAM and real local Clickteam setup remain unknown |
| 01 Repository & CI | PASS | Reproducible branch CI and tests |
| 02 Windows GUI | PARTIAL | Qt/PyInstaller smoke PASS, GUI works in CI; real-user interaction and final UX QA absent |
| 03 Procedural geometry | PARTIAL | Real meshes and control of height, head, snout and tail; exact geometry reconstruction from reference views NOT achieved |
| 04 Surface/mechanical detailing | PARTIAL | Curved hat brim, pointed teeth, node-based procedural relief; UV/PBR baked textures, refined topology, scale sculpt and stitch details missing |
| 05 Rigging/animation | PARTIAL | 39 mechanical bones and 26 named Actions, brows/lids/eyes/jaw/tail controls; full independent finger phalanges, animation realism and visual acceptance missing |
| 06 Fusion export & QA | PARTIAL | BLEND/FBX/GLB exports and PNG sprite packing plus QA work; direct Clickteam 2.5 engine integration not runtime-tested |
| 07 GPT analysis | PARTIAL | Opt-in reference roles, strict parameter schema, secure credential UI, user approval prior to application; live request not verified |
| 08 Neural Image-to-3D | ADAPTER ONLY | ComfyUI workflow queue exists, no compatible GPU/image-to-3D model installed or tested |
| 09 Windows executable | PARTIAL | Automated packaged EXE smoke PASS on GitHub Windows runner; consumer PC deployment/Blender availability not tested |
| 10 Final acceptance | NOT COMPLETE | Reference-accurate character, visual multi-view QA, all motion clips, Clickteam import, AI reconstruction missing |

## Engineering caveats

- `overall_scale` changes armature object transform and the meshes parented to its bones; `tail_length` alters seven mechanical tail bones and all seven associated geometry segments.
- The material noise/bump improves Blender renders but **is not baked into glTF/FBX texture maps**. Game-engine fidelity therefore remains limited.
- New facial Actions are keyframed control-test approximations, not image-to-3D reconstruction or facial motion capture.
- Windows executable is unsigned alpha. Blender is installed separately. User project artwork and OpenAI API keys are not bundled.
- The Windows VPS from earlier work is **not used**. GitHub Actions performs isolated test execution.

## Next blocking requirements

1. Accurate multi-view geometry fitting or a validated AI image-to-mesh reconstruction with editable topology.
2. Mechanical detail refinement, rig completeness, actual UV texture baking and PBR export parity.
3. End-to-end visual acceptance against the 12 original reference sheets.
4. Clickteam Fusion runtime import and real Windows end-user functional tests.
