# GOSHMAN v16 — gum collars and mouth checks

- Blender 5.2.3 on authorized Windows device: saved .blend, 203 mesh objects, 39 bones, 26 actions.
- Added 18 annular open gum collars at upper/lower dental arc roots, individually parented to head or jaw. These are **not Boolean-cut sockets or integrated gingival tissue**; they are preliminary 3D collars.
- Restricted head/mandible shell sweep: 33 poses through 54.431°, no selected shell-shell BVH overlaps.
- Upper vs lower teeth at 0,1,3,5,10,20,35,54.431°: no BVH triangle overlaps.
- Lower teeth vs tongue, upper gum, upper snout and both cheeks; upper teeth vs tongue, mandible and both cheeks: no BVH triangle overlaps at the same eight angles.
- Added collars themselves are not yet included in the full pairwise collision matrix. No proof of root seating or high-poly anatomical reconstruction.
- **Profile shape unmodified from v15**: no evidence of reduced left/right mismatch in this iteration; bilateral profile adjustment is still open.
- Art acceptance and clickteam export untested. No VPS or main change.
