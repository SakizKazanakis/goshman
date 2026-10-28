# GOSHMAN v21 — Integrated hinge load path & profile verification (2026-10-28)

## Real implementation

Verified Blender 5.2.3 Windows hp_elitebook, isolated from v20. `Mandible_integrated` now includes two rear lateral load-bearing hinge lugs, fused during voxel remesh, with two cylindrical Boolean through-bores (radius 0.088). Stationary pin radius 0.058; jaw bushing outer radius 0.084, bore radius 0.064, sharing Y=-0.20 Z=4.70 axis. Other parts include fixed head-side bearing, external retainer, moving annular cap and protective ring. Final protective rings positioned outboard at X=±1.080 to avoid new collision regression. Rig remains 39 bones and 26 actions. 190 mesh objects, .blend saved.

## Actual Blender tests

- Restricted head-shell/jaw-shell BVH: zero detected intersections at 33 poses, 0–54.431°.
- Full mouth/contact matrix: 14 overlapping object pairs at eight sampled poses, unchanged from v20 **after fixing protective ring placement**. Initial v21 trial produced 18 pairs (including jaw vs both fixed rings, cheek vs both rings); corrected and rebuilt.
- Bilateral approximate silhouette IoU, isolated part alpha rendering and human-guided original reference polygons:
  - Left jaw v20 0.40589 -> v21 0.43016.
  - Right jaw v20 0.44865 -> v21 0.47708.
  These are preliminary diagnostic scores, not final photogrammetrically calibrated ground truth.
- 14 remaining overlaps are among intended embedded components and ununified sculpt surfaces: gums, tongue, snout, cheeks, upper tooth bases. Classifying them as harmless requires topology/assembly inspection, not just BVH counting.
- Full mechanically reliable bearing support, axial retention, manufacturing tolerances and minimum clearance over the **continuous** jaw trajectory have not been proved. Geometric radii alone do not constitute bearing qualification.
- Teeth and root geometry are inherited from v20; no simultaneous per-tooth fitting improvement claimed. Need full lower teeth vs modified mandible verification before acceptance.

## Status

**Engineering prototype progressed**, but not production/mechanical/art acceptance. Real 3D geometry and verified Blender build, source committed. `main` and VPS unchanged. No Clickteam integration or high-poly PBR qualification.
