# GOSHMAN v22 — 109-pose bearing fit and tooth-to-jaw audit

2026-10-28. Authorized Windows `hp_elitebook`, Blender 5.2.3, based on confirmed v21. This is a **diagnostic QA iteration**, not a new geometry version. `main` and VPS unchanged.

## Tested in the actual .blend

`tests/blender_bearing_clearance_v22.py` sampled **109 angles** from 0° to 54.431° (~0.504° spacing), measuring surface-vertex-to-BVH triangle distances and triangle intersections separately for both hinge sides. Script and results also verified with 7-angle paired load-path tests (`tests/blender_joint_load_path_v22.py`).

| Measured pair | Minimum scene units | Maximum scene units | Triangle intersections over 109 poses |
| --- | ---: | ---: | --- |
| Left pin vs bushing | .005999 | .006123 | none |
| Right pin vs bushing | .005999 | .006123 | none |
| Left/Right bushing vs stationary support bearing | .036000 | .036000 | none |
| Left/Right bushing vs stationary socket/protective ring | ~.072131 | ~.072178 | none |
| Left/Right bushing vs moving cap | .008500 | .008500 | none |
| Left/Right stationary retainer vs moving cap | .020000 | .020000 | none |
| Left/Right jaw shell vs stationary socket | .064875 | .064892 | none |
| Left/Right jaw shell vs moving bushing (7-angle secondary audit) | .003904 | .003905 | none |
| Fixed pin vs fixed retainer (7-angle secondary audit) | sampled distance .006000 | .006000 | **BVH overlap** (likely deliberate fixed-part embed) |
| Fixed bearing vs fixed pin (7-angle secondary audit) | sampled distance .013970 | .013970 | **BVH overlap** (fixed-part embed) |

The distance metric is sampled, not an exact signed distance. BVH triangle overlaps and a nonzero vertex-to-surface distance can coexist. Manufacturing feasibility and force transfer are not established by these numbers.

## All nine lower teeth vs the changed jaw

Each lower tooth was tested against `Mandible_integrated` at 9 representative angles of the same sweep (0°, about .504°, 1.008°, 1.512°, 3.024°, 6.048°, 12.096°, 27.216°, 54.431°), **no BVH tooth-jaw triangle overlaps**.

Minimum sampled distances for teeth 00..08 were .042604, .024877, .028600, .024912, .034346, .024930, .028608, .024925, .042736 scene units respectively.

These finite distances **do not prove tooth roots are securely embedded**. They may be seated through a separate gum mesh but assembly integrity remains unverified.

## Mechanical design findings

- The free bushing-to-jaw radial clearance of ~.004 scene units is controlled and consistent with intended fit but needs a fastening or keyed connection if the bushing must rotate *with* the mandible rather than freely in it.
- A stationary load path across the fixed pin/bearing/retainer has intentional overlapping solids, but physical fixation (press-fit, snap-fit, fastener or manufactured unity) and axial retention are **not certified**.
- External ring geometry sits away from moving cap; ring is not shown as a functional stop. This must be redesigned if it is intended as the axial stop.
- These samples are dense, not a mathematical proof across the full continuous trajectory; no load, deflection, fatigue or tolerance stack-up simulated.

## Reference fidelity

No changes to jaw shape in v22, therefore the last confirmed diagnostic baseline remains v21: left IoU 0.43016, right IoU 0.47708. The project must not claim another multi-view fidelity gain. To improve both profiles, next stage must optimize the jaw surface **together with tooth-root placement**, constrain the actual hinge and mouth contacts, regenerate the scene for each candidate, and validate again.

## Acceptance

**QA improved and reproducible. Mechanical joint and final high-fidelity head are NOT accepted.** Blender scene unchanged from v21; no PBR bake or real Clickteam Fusion import verified.
