# GOSHMAN v17 — integrated gum volume and Boolean tooth sockets

28 October 2026, Windows Blender 5.2.3 LTS. Branch: `feature/integrated-gingiva-bilateral-v17-20261028`, parent v16.

## Real implementation
- Replaced 18 independent open gum collars with two swept closed 3D gum bands: `Upper_gum` parented to head and `Lower_gum` parented to jaw.
- Nine Boolean Difference cylindrical cavities were applied to each band with Blender Exact solver. Real geometry contains socket bores, not merely surface overlay.
- Mesh objects: 186 (from 203). Rig: 39 bones; actions: 26.
- Current bores are procedural simple cylinders, **not yet individual anatomically sculpted sockets or validated gum-to-jaw fusion**. Topology audit reported 0 boundary edges on both gum bands; Blender boolean output: upper 990 vertices 562 faces; lower 923 vertices 575 faces.

## Failure caught and resolved
- Initial v17 upper bores were shallow: all nine upper teeth intersected upper gum at all eight tested poses.
- Deepening the upper cutter to depth 0.220 and changing its Z center to 4.745 removed these BVH triangle overlaps on eight sampled jaw angles.

## Collision verification (actual Blender)
- Angles: 0, 1, 3, 5, 10, 20, 35, 54.431 degrees.
- 0 BVH tooth-to-own-gum contacts for all 18 teeth, no upper tooth/lower gum crossings, lower tooth/upper gum crossings, upper gum/lower gum intersections or lower gum/tongue intersections in tested poses.
- Restricted mandibular shell / skull and cheeks: no overlaps at 33 sampled poses through 54.431 degrees.
- Collision test does NOT establish no self-contacts of tooth roots in boolean cavities, physical integration of gums into adjacent skin, or zero near-contacts at every intermediate angle.

## Bilateral silhouette fitting
Manual approximate reference polygon masks, fixed orthographic camera. Baseline v16: left mandibular IoU=0.405888, right=0.448651.
Tried symmetric lateral ramus Z shifts (0, ±0.035, ±0.070 units); all nonzero shifts traded one view for the other, so NONE accepted:
- +0.035: left=0.404320, right=0.450673.
- -0.035: left=0.405354, right=0.445041.
- +0.070: left=0.402404, right=0.451034.
- -0.070: left=0.403974, right=0.439974.
Therefore **profile mismatch remains unresolved**, no improvement claimed.

## Not accepted
Photogrammetric grade correspondence, anatomy-specific embedded sockets, unified gingiva-jaw sculpt and bilateral reference fidelity, full assembly collisions, PBR bake, and Clickteam Fusion runtime verification.
No VPS/main changes.
