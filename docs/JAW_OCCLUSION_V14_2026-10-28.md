# GOSHMAN v14 — mirrored dentition and closed-bite audit

Date: 2026-10-28
Branch: `feature/jaw-bilateral-occlusion-v14-20261028`. Based on v13.

## Implemented
- Replaced alternating semi-random tooth offsets with mirrored per-index upper/lower X placements, radii and heights.
- Nine upper and nine lower teeth retain individually addressable object names.
- Symmetric tooth ranks around central index 4: tooth pairs i/8-i have equal radii, equal heights, opposite lateral offsets and matching Y/Z.
- Changed Y positions slightly per pair; lower tooth Z from 4.57 to 4.584 in the local generator.
- No modification of the mandibular outer shell or hinge pivot in v14.

## Real Blender 5.2.3 results
- Build: 185 mesh objects, 39 bones, 26 actions; restricted jaw sweep 33 positions 0–54.431° finds no upper-shell/mandible-shell intersections.
- World-space BVH upper/lower tooth triangles: 0 overlapping pairs at angles 0,1,3,5,10,20,35,54.431°.
- Sampled minimum tooth surface separation: 0° 0.005808; 1° 0.011560; 3° 0.022296; 5° 0.033028 units.
- Previous v13 closed-bite sampled gap 0.038562. New near-contact is closer and nonpenetrating at sampled poses, but exact surface-to-surface clearance and physically natural tooth interdigitation remain unverified.
- Jaw/muzzle/cheek silhouette was not changed; v13 jaw diagnostic IoU remains the valid prior baseline (front 0.33690; left 0.37570; right 0.46482). No claim of improved multiview skull profile.

## Outstanding constraints
- Need per-tooth mapping to reference shapes and dental arc, and collision checks against tongue, gums, cheeks, face and hinge caps. 
- Side-profile jaw v13 tradeoff persists (right view slightly worse than v12).
- Test is surface-vertex sampled; it is not a true analytic minimum distance test.
- No Clickteam Fusion test, PBR bake, full high-poly reconstruction or visual art sign-off.
- VPS and main branch untouched.
