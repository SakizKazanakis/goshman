# GOSHMAN v10 — part-specific reference fitting (2026-10-28)

## Method
Human-guided visible-part polygon masks from original head sheet, not a pixel-perfect ground truth. Independent transparent alpha renders of cranium+cheeks, upper muzzle, unified mandible, eyes with recesses from real Blender 5.2.3. Fixes earlier reversed profile camera directions: left reference = +X viewpoint, right reference = -X. Orthographic scales front 145.04, left 136.47, right 140.17 px/unit; remaining registration provisional.

## Diagnostic per-part IoU (not final reference acceptance)
| View/part | v9 | v10 |
| --- | ---: | ---: |
| Front cranium+cheeks | 0.63849 | 0.63849 |
| Front muzzle | 0.71959 | 0.71959 |
| Front mandible | 0.19521 | 0.19521 |
| Front left eye | 0.58941 | 0.64793 |
| Front right eye | 0.59119 | 0.70970 |
| Left cranium+cheeks | 0.80020 | 0.80020 |
| Left muzzle | 0.54336 | 0.57982 |
| Left mandible | 0.18317 | 0.18317 |
| Left eye | 0.71362 | 0.74805 |
| Right cranium+cheeks | 0.68054 | 0.68054 |
| Right muzzle (cropped reference) | 0.46412 | 0.47514 |
| Right mandible | 0.32655 | 0.32655 |
| Right eye | 0.33110 | 0.30931 |

## Construction
Move five axial upper-muzzle stations 0.07–0.13 units forward; reduce globe radii and associated eye recess/iris/pupil. Existing rig and mechanical jaw unchanged. Real Blender build passed (185 objects, 39 bones, 26 actions). Previous restricted BVH comparison 33 jaw poses (0–54.431°) returned no contacts among selected cranium/cheek vs mandible meshes; this is not full component clearance.

## Decision
Not accepted for global reference fidelity. Changes improve some parts and worsen the right profile eye. Next major geometric corrections: jaw anterior mass/sidewall, lower cheek/skull extent and right eye depth. Source artwork and manually traced masks remain outside public GitHub.
