# GOSHMAN v19 — hinged socket clearance and contact classification

2026-10-28. Isolated branch based on v18. Verified on authorized Windows hp_elitebook using Blender 5.2.3. No main/VPS changes.

## Construction
Replaced two solid `Jaw_hinge_socket_L/R` cylinders with two head-parented toroidal rings, 48×12 segments, major radius 0.107, minor radius 0.020, X-axis. Retained the jaw bone axis at Y=-0.20 Z=4.70 and existing moving caps. Axial sweep tested six outward offsets 0, .04, .08, .12, .16, .20 from the first ring position. Smallest tested candidate with no jaw/socket and cap/socket triangle intersections at seven sampled poses was outboard +0.12 each side.

## Real Blender results
Built and saved real v19 .blend. Mesh objects 186, bones 39, actions 26. Restricted head shell / jaw BVH over 33 poses (0–54.431°): no intersections (same as v18).

Extended pairwise BVH matrix, 8 jaw poses: **22 intersecting pairs in v18 → 16 pairs in final v19**, at each test pose. Eliminated:
- Two moving caps against stationary hinge sockets.
- Two jaw surface vs stationary hinge sockets.
- Two stationary cheek vs hinge socket intersections.

## Clearance (approximate sampled vertex-to-triangle minimum distance)
At 0°,1°,3°,5°,10°,20°,35°,54.431°:
- Left ring to mandible: minimum ~0.018447 model units (0°).
- Right ring to mandible: minimum ~0.018420 (0°).
- Both rings to moving caps: minimum ~0.065812.
These are sampled geometric separations rather than analytically exact continuous-sweep minimum distances. Not a physical tolerance or manufacturability certification.

## Remaining 16 intersections / classification
- `Upper_gum/Upper_snout`: intentional embedded tissue **candidate**; must be joined/welded for production sculpt.
- `Lower_gum/Mandible_integrated`, `Tongue/Mandible_integrated`: intended embedded components, not evidence of undesired kinematic interference.
- `Mandible_integrated/Jaw_hinge_moving_cap_L/R`: attached moving-shell contact, intended attachment **candidate**, but should be joined or clearance designed.
- `Upper_snout/Cheek_L/R`: static sculpt overlap requiring topology union.
- `Upper_snout/Upper_tooth_00...08`: nine tooth bases inserted into upper snout; requires design verification and a unified alveolar seat before claiming production readiness.
No collisions remain between jaw and toroidal sockets in tested poses.

## Unresolved physical-design concern
Moving rings outboard by 0.12 creates visible spatial gaps relative to existing bearing/pin hardware. Although there is no mesh contact, it **does not prove a mechanically supported bearing assembly**. Must redesign bearing, pins, socket and movable jaw as one kinematically constrained joint and check support/contact, axial travel and tolerances. Do not claim hinge mechanical acceptance.

## References
No new jaw/sculpt silhouette fit in v19. Original bilateral IoU discrepancies remain, with diagnostic v16/v17 left=0.4059, right=0.4487. GOSHMAN exact reference fidelity remains unaccepted.
