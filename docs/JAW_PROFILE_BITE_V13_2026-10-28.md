# GOSHMAN v13 — jaw profile / tooth-row reconstruction (2026-10-28)

Branch: `feature/jaw-profile-bite-v13-20261028`. Base v12, unchanged core rig pivot (Y=-0.20 Z=4.70).

## Parameter sweep in real Blender 5.2.3

Fore-mandible +Y displacement with smooth weight, zero at the posterior hinge. Fixed three orthographic cameras and part-isolated alpha passes. IoU is diagnostic using hand-traced approximate outlines, not final ground truth.

| Shift | Front IoU | Left IoU | Right IoU | Mean | collision poses in 33 tests |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.33690 | 0.32599 | 0.47063 | 0.37784 | 0 |
| 0.06 | 0.33690 | 0.34656 | 0.46941 | 0.38429 | 0 |
| 0.12 | 0.33690 | 0.36473 | 0.46842 | 0.39002 | 0 |
| **0.18** | **0.33690** | **0.37570** | **0.46482** | **0.39247** | **0** |
| 0.24 | 0.33690 | 0.37526 | 0.44973 | 0.38730 | 0 |
| 0.30 | 0.33690 | 0.36289 | 0.41948 | 0.37309 | 0 |

Selected candidate: 0.18. This improves average diagnostic IoU but marginally worsens right profile, so not fully art-accepted.

## Tooth adjustments

- Upper x offsets alternate ±0.008, lower x ±0.012 (scaled). Individual radii adjust for index 1,7 upper and 2,6 lower.
- Lower tooth z: 4.55 → 4.57; actual height still 0.10. Individual positions remain simplified. 
- Real BVH triangle-overlap testing at 0°,1°,3°,5°,10°,20°,35°,54.431° found **0** intersecting upper/lower tooth pairs.
- Sampled minimum separation: 0°=0.038562, 1°=0.045044, 3°=0.057434, 5°=0.071795 model units; previous closed gap 0.045933. Nearer but NOT touching / interdigitating correctly.

## Technical validation and open defects

- Blender build: 185 mesh objects, 39 bones, 26 actions, animation range 0–54.431°.
- Restricted skull/cheek vs mandible BVH in 33 poses: no triangle intersections; NOT full mouth/hardware validation.
- Left jaw profile IoU 0.32599 → 0.37570, right 0.47063 → 0.46482, front stable 0.33690. Main residual: bilateral view asymmetry / registration, cheek joint realism and tooth tip interdigitation.
- No claim of exact photogrammetric ground truth, physical contact, production game readiness or complete reference fidelity.
- No changes to main or VPS.
