# GOSHMAN v20 — Coaxial hinge assembly, measured collision changes, bilateral reconstruction attempt

Date: 2026-10-28; authorized Windows hp_elitebook, Blender 5.2.3; parent v19. VPS and main untouched.

## Implemented in source and verified in real Blender
- A new annular mesh generator `_coaxial_sleeve`: 48 radial sectors, two axial stations and inner bore; mesh is capped annularly.
- Symmetric fixed pin and head-mounted bearing cylinders, moving jaw-parented bushing and thin annular moving cap, stationary outer retainer and protective ring. All are centered on Y=-0.20, Z=4.70.
- Model builds: 190 mesh objects, 39 bones, 26 actions, .blend saved, jaw runs 0–54.431°. Restricted skull/cheeks vs mandible shell sweep: no detected intersections in 33 poses.
- Extended 8-angle full mouth BVH contact test: 14 overlapping mesh pairs/pose versus 16 for v19 and 22 for v18. Elimination of the two `Mandible_integrated/Jaw_hinge_moving_cap_L/R` intersections.
- This is a **kinematically organized visual 3D assembly**, not certified mechanical support: a bearing load path, axial retention/clearance, pressure and manufacturability are not validated.

## Unresolved overlaps
14 detected overlaps per sampled pose among gums, tongue, snout, cheeks and upper teeth. Some intended mesh embedment, but not yet made a watertight unified sculpt.

## Bilateral jaw-profile sweep and failed rebuild
A smooth Y-extension trial using 0,+0.025,+0.050,+0.075,+0.100 and negative controls showed diagnostic IoU gains in both views **within the in-memory sweep**, e.g. +0.05: left .408724 right .455179 vs baseline left .405888 right .448651.
However after fully regenerating the scene with an analogous shape edit, **the result did not reproduce**: Blender isolated pass left IoU .39865 (WORSE), right .46319 (BETTER). The edit also introduced 7 extra `Mandible_integrated/Lower_tooth_01..07` triangle contacts: full BVH matrix grew from 14 to 21.
Therefore that geometric adjustment was **rejected and reverted**, and the scene has been rebuilt without it (confirmed original chin_drop .426771). GitHub source contains only hinge improvements.
Baseline shape acceptance remains left .40589, right .44865. Do not cite sweep IoU as final results.

## Pending next work
- Anchoring bushing to an actual jaw load-bearing fork, verifying continuous swept clearance and robust mechanical seating.
- A new bilateral profile optimization that uses full regeneration and holds tooth-to-jaw seating fixed; apply topology regularization and multi-view QA simultaneously.
- Formal classification/welding of intentionally embedded parts.
- Final high-poly/PBR/Clickteam runtime testing not complete.
