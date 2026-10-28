# GOSHMAN v15 — curved dental arches and internal mouth clearance

Date: 2026-10-28. Branch: `feature/dental-arches-interior-clearance-v15-20261028`, based on v14.

## Geometry implemented

- Upper and lower 9-tooth arrays now have **curved horseshoe XY placement**, with individually assigned lateral positions, anterior/posterior positions, radii and heights.
- Mirrored left/right dental parameters are maintained.
- Upper gum moved backward/upward and reduced vertically; tongue moved back and narrowed to avoid tooth interference.
- The lower-jaw branch, cheek mesh and hinge remain unchanged from v14. This version does **not** claim to fix residual left/right silhouette inconsistency.

## Real Blender 5.2.3 tests

- Build successful: 185 mesh objects, 39 bones, 26 actions.
- Restricted main-shell BVH: zero observed jaw-to-head overlaps across 33 poses, 0–54.431 degrees.
- Upper/lower tooth-row BVH: zero observed overlaps in eight poses (0, 1, 3, 5, 10, 20, 35, 54.431 degrees).
- Before internal correction, lower teeth intersected the tongue and upper gum.
- After correction, no BVH triangle intersections observed in eight poses among the following tested pairs: lower teeth against tongue, upper gum, upper snout, and both cheeks; upper teeth against tongue, integrated mandible, and both cheeks.
- Surface-vertex sampled minimum upper/lower tooth clearance **before gum/tongue correction**, with unchanged tooth shapes afterwards: 0°=0.016883, 1°=0.020721, 3°=0.028709, 5°=0.039980 scene units. This is larger than v14 closed-bite minimum of 0.005808; do not claim closer occlusion.
- Contact testing is pairwise triangle intersection only, **not** exact surface-distance proof or full assembly collision testing. Tongue-gum, caps/bearings, and other cross-part collisions remain untested.

## Remaining defects / acceptance

- Exact anchoring of every tooth root to the actual jaw/gum surface is not established: root positions are procedural approximations.
- Final reference-derived dental-arc positions and photogrammetric camera alignment are unavailable.
- Left/right profile mismatch and jaw branch silhouette are inherited from v13/v14, not corrected here.
- Physically meaningful interdigitation, accurate croc dentition, high-poly organic sculpt, final PBR baking, Fusion 2.5 integration: not accepted.
- Main branch and VPS were not changed.
