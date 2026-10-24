# GOSHMAN acceptance evidence — 2026-10-24

## Definition of ready
A completed character must visually match all 12 supplied reference sheets, include editable geometry, independent mechanical joints, a facial and body rig, surface maps baked from approved detailed geometry, and successfully work within Clickteam Fusion 2.5. Export success alone does NOT constitute acceptance.

## Proven implementation
- Actual Blender procedural meshes, mechanical bones and Actions, with CI verified exports.
- Generated UV maps for 10 existing procedural materials: Base Color, Roughness, Metallic, Normal. Saved to output/pbr and embedded in Blender/GLB. CI tests 256px and offers up to 2048px.
- Cropping of the specific supplied 1491x1055 full-turnaround sheet into front/left/back/right/3-4 panels, with SHA-256 provenance; original reference unchanged and never published.
- Technical GLB validation of textured images and normal map links.

## Explicitly NOT completed
| Requirement | Status | Missing proof |
| --- | --- | --- |
| Accurate reconstruction from 12 supplied sheets | NOT ACHIEVED | Current geometry is a procedural approximation without registered cameras, measured 3D correspondence or full visual acceptance |
| Detailed high-poly -> low-poly Cycles baking | NOT IMPLEMENTED | UV textures are mathematically synthesized; not high-poly Cycles bake, not UV projection of original pixels |
| Image-to-3D inference on this crocodile | NOT TESTED | Compatible CUDA hardware, checkpoint inference, validated mesh and edited topology unavailable in session |
| Clickteam Fusion 2.5 runtime import | NOT TESTED | No accessible installed Fusion editor and test game project. Sprite manifests are not proof of engine integration |
| End-user Windows production release | NOT VERIFIED | CI smoke test does not establish functional operation on a consumer Windows PC |

## Reproducibility
- Prepare five cropped source views: python -m goshman.cli prepare-views crocodile_project
- Build maps and model: python -m goshman.cli generate crocodile_project --pbr-resolution 2048
- Inspect exports: python -m goshman.cli audit crocodile_project
- Review real CI checks in .github/workflows/ci.yml.
- Private user images and secret keys must not be uploaded to public CI.
- The user's VPS must not be used for GOSHMAN.

## Minimum future acceptance evidence
1. A reference-consistent editable model, plus evaluated matching across all body part sheets and poses.
2. Actual Cycles high-poly bake output with material texture maps and export parity checks.
3. Log of successful neural 3D inference on approved inputs with checkpoint/version, GPU, triangle counts and mesh artifact.
4. Clickteam Fusion 2.5 recording/log: imported sprite actions/directions, hotspots and running scene or exported game executable.
