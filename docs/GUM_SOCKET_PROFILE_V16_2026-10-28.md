# GOSHMAN v16 — dental gum collars and bilateral mandible profile

## Execution (2026-10-28)
Source: v15; isolated Windows worktree; branch `feature/jaw-gum-socket-profile-v16-20261028`. No VPS or main modifications.

## Delivered
- 18 procedural open annular gingival collars at tooth bases, bilaterally arranged and bone-parented (head/jaw). Construction uses 3 annular rings, 32 segments, no face capping the inner aperture.
- These are **separate open collars**, not actual Boolean negative tooth cavities in the integrated gum volume; tooth roots are not proven anatomically seated.
- Smooth symmetric Y-shift on lateral mandible regions, vanishing near center and rear hinge: max 0.07 scene units. Original joint axis preserved.

## Blender acceptance and limitations
Blender 5.2.3 real scene: 203 meshes, 39 bones, 26 actions, .blend saved. 33 sampled jaw positions through 54.431°: no selected skull/cheek shell vs jaw-shell BVH intersections.
Upper/lower dental pairs: 8 angles 0,1,3,5,10,20,35,54.431° with zero BVH triangle overlaps; tested teeth vs tongue, upper gum, upper snout, cheeks, mandible at these angles: no detected intersections.
**Collar-to-tooth/root, collar-to-gum, collar-to-mandible, collar-to-collar** full clearance and manifold attachment were not validated.

Reference diagnostic per-part IoU (manual approximate polygon masks; not calibrated ground-truth):
| View | v15 | v16 |
|---|---:|---:|
| Jaw left | 0.37570 | 0.40589 |
| Jaw right | 0.46482 | 0.44865 |
| Jaw front | 0.33690 | 0.33690 |
Bilateral mismatch difference reduced 0.08912 → 0.04276 while right-view fidelity declined. Thus **no global artistic acceptance**.

## Outstanding
- True recessed gum sockets cut into high-poly continuous gingival mesh and embedded tooth roots.
- Validate collar and tongue crossings, physical interdigitation, seam/fold normal integrity.
- Multi-view registered sculpt fitting of lateral jaw and cheek profile, improve both views simultaneously.
- Real game export / PBR baking not validated.
