# GOSHMAN v12 — jaw, cheek and teeth verification (2026-10-28)

## Actual implementation and regression
- Isolated branch `feature/jaw-cheek-tooth-clearance-v12-20261028`, baseline v11.
- Initial aggressive cheek seating changed centroid and forward jaw location but introduced shell collisions at 32 of 32 non-neutral poses: **rejected**.
- Conservative final variant shifts cheek center from (±0.545,-0.165,4.80) to (±0.545,-0.18,4.80), changes cheek radii from (0.25,0.31,0.205) to (0.245,0.305,0.195), and restores original v11 forward jaw displacement to +0.165 weighted units.
- Blender 5.2.3: 185 mesh objects, 39 bones, 26 animation actions; no shell collisions in restricted 33-pose BVH (0–54.431°).
- Isolated per-part silhouette IoU unchanged versus v11, including mandibular values front=0.33690, left=0.32599, right=0.47063. **No measurable reference-fidelity gain; variant NOT artistically accepted.**
- Left jaw centroid mismatch remains approximately -36.045 pixels.

## Real tooth-row test
- World-space BVH intersection test of 9 upper vs 9 lower teeth at 0, 1, 3, 5, 10, 20, 35 and 54.431 degrees: **zero interpenetrating tooth pairs** at all tested poses.
- Surface-sampled approximate minimum upper/lower tooth gap: 0°=0.045933, 1°=0.052541, 3°=0.066710, 5°=0.085636 model units.
- Thus closed teeth do **not** physically touch in this geometry. A nonintersecting gap is not evidence of natural tooth occlusion or correct bite. Need full mouth/teeth/hinge clearance and adjusted interdigitation.
- Tests exclude multiple other facial mechanisms; don't claim collision-free complete head.

## Decision
Work is mechanically validated in the restricted scope; the stated visual profile correction remains unsolved. v12 kept isolated for analysis and should not be merged into main without further reconstruction and approval.
