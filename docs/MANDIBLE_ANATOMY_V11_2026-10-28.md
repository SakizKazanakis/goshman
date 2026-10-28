# GOSHMAN — Mandible anatomy v11, 2026-10-28

## Confirmed implementation
- Source branch: feature/mandible-cheek-anatomy-v11-20261028; baseline v10.
- After voxel union and before bone parenting, smooth position weights taper the anterior mandibular wall, shift the fore-chin 0.165 units rearward and lower the underside by up to 0.185 units.
- Retains joint pivot at Y=-0.20, Z=4.70 and 0–54.431-degree jaw sweep.
- Repairs erroneous vertex-colour blend expression `-y/-y/snout` to `-y/snout`.
- Actual Blender 5.2.3 build: 185 objects, 39 bones, 26 actions.
- Restricted 33-pose BVH test: no intersections between specified skull/cheek and unified-mandible shells. This is **not** a full mouth/hardware collision test.

## Diagnostic silhouette IoU
Based on human-guided polygons over the reference sheet and isolated alpha render passes. Not a final per-pixel ground truth.

| Part/view | v10 | v11 |
|---|---:|---:|
| Mandible front | 0.19521 | 0.33690 |
| Mandible left | 0.18317 | 0.32599 |
| Mandible right | 0.32655 | 0.47063 |
| Skull front | 0.63849 | 0.63849 |
| Skull left | 0.80020 | 0.80020 |
| Skull right | 0.68054 | 0.68054 |

## Remaining deviations
- Front mandible overly broad in lower-middle areas and lacks anatomical subdivisions.
- Left jaw orientation still has 36 px centroid shift relative to manually marked outline.
- Transition to cheek, movable hinge caps, teeth and tongue are not included in this isolated-mandible IoU.
- Human sign-off on anatomical fidelity, final calibrated multi-view camera fitting and complete collision test have **not** passed.
