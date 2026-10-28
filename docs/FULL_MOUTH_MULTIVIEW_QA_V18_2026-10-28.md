# GOSHMAN v18 — multiview parameter sensitivity and full contact matrix
Date: 2026-10-28. Base v17 (`0315a224704aeda528e73a1b1b3a533a47ad42cd`).

## Verified Windows Blender 5.2.3 experiments
A new isolated worktree was created on authorized `hp_elitebook`; nothing was run on VPS or merged into main.

### Lateral ramus width sensitivity
Using original v17 .blend, five trial values for lateral width modification (-0.08, -0.04, 0, +0.04, +0.08) were rendered from fixed left/right profile cameras. All yielded exactly the same silhouette metrics on the 128/projection mask method: left IoU=0.4058883, right IoU=0.4486508. No width candidate was accepted. These results demonstrate local parameter insensitivity, not geometric correctness.

### Expanded interpenetration audit
Added `tests/blender_full_mouth_pairwise_bvh.py`, evaluating world-space triangle BVH overlaps at 0°,1°,3°,5°,10°,20°,35°,54.431°, over gums, tongue, jaw, upper snout, cheeks, hinge sockets/moving caps and 18 teeth.
- The same 22 overlapping object pairs were observed at every tested angle.
- These include expected/integrated intersections (`Upper_gum/Upper_snout`, `Lower_gum/Mandible_integrated`, `Tongue/Mandible_integrated`), and **unresolved contacts requiring dedicated classification and possible repair** (`Mandible_integrated/Jaw_hinge_socket_L`, `Mandible_integrated/Jaw_hinge_socket_R`; associated moving caps and hinge sockets).
- Upper teeth also intersect `Upper_snout` (their root-seat geometry); these need explicit verification for intended embed vs incorrect placement.
- Result is **not a pass of full collision-free assembly**. Triangle intersection detection alone cannot determine intentional embedment, pressure or mechanical clearance.
- Previous limited v17 test only checked skull/cheek shells vs mandible, and thus cannot replace this full matrix.

## Status
- No new sculpt geometry accepted on this branch. The working Blender scene remains v17.
- Profile mismatch **not fixed**.
- Full-head collision-clearance **not passed**; specific contact pairs documented for repair.
- v17 continuous Boolean-cut gum meshes remain the best verified gum baseline.
