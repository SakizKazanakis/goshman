# GOSHMAN fixed-camera comparison — 2026-10-28

Experimental branch: `feature/head-fixed-camera-qa-v9-20261028`, built from `feature/head-multiview-section-mesh-v8-20261028`.

## Camera calibration

Provisional orthographic camera parameters using coarse manually-seeded landmarks and a robust least-squares projection fit. They are not photogrammetrically certified.

| View | Image dimensions | Pixels/unit | Ortho scale | Reprojection RMS |
|---|---|---:|---:|---:|
| front | 293×346 | 145.04 | 2.386 | 19.10 px |
| left | 315×348 | 136.47 | 2.550 | 25.24 px |
| right | 290×349 | 140.17 | 2.490 | 32.80 px |

Identical camera parameters were used to render v7, v8, and v9 with Blender 5.2.3 on an authorized Windows machine.

## Geometry changes in v9

- Eye lateral placement reduced from ±0.35 to ±0.285 units (multiplied by `scale`).
- Nostril spacing reduced from ±0.30 to ±0.205 units.
- Forward muzzle cross-section widths modified: 0.78→0.86, 0.79→0.89, 0.73→0.79.
- Build report: 185 meshes, 39 rig bones, 26 animation actions.
- BVH: 33 sampled jaw angles (0–54.431°) with zero intersections among the tested skull shell / mandible shell pairs, **not** among every head component.

## Preliminary diagnostic IoU — not final fidelity QA

The masks use HSV/GrabCut and manual foreground seeds; exported Blender images were compared by a heuristic head-colour classifier on a 128×128 sample grid. These masks include occlusion and colour ambiguities. They are **not** human-approved silhouettes.

| View | v7 | v8 | v9 |
|---|---:|---:|---:|
| front | 0.57576 | 0.57135 | 0.57378 |
| left | 0.55517 | 0.55817 | 0.55866 |
| right | 0.35944 | 0.38008 | 0.37983 |

The metrics **do not demonstrate a consistent improvement** in reference fidelity from v8 to v9. The eye-spacing correction is directionally supported by approximate landmarks, but the shape update remains experimental.

## Acceptance

- Blender build, fixed-camera comparative rendering, and constrained jaw collision QA: **completed**.
- Accurate registered camera calibration, human-verified masks, reliable full-reference IoU/NME, all-part collision tests, source-specific PBR baking, and Clickteam Fusion: **not yet accepted**.
- Private source art and render files are kept off public GitHub.
