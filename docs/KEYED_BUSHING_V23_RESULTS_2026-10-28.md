# GOSHMAN v23 — keyed bushing experiment and contact QA (2026-10-28)

## Implementation and actual build

Working on authorized Windows hp_elitebook, Blender 5.2.3, derived from v22/v21. Two keyed-slot cutouts were added to each mandibular lug using Boolean Difference, and two movable radial key cylinders per side were added under the jaw bone. New Blender scene saved successfully: 194 mesh objects, 39 rig bones, 26 actions. Restricted skull-vs-jaw BVH returned zero overlaps through 33 sampled positions (0–54.431 degrees). 

## Measured outcome
- Extended v18-style 8-angle mouth-component audit: 14 overlapping pairs at each angle, unchanged from v21. **Important:** this older audit does not include the newly added keys; alone it cannot certify key safety.
- Dedicated `tests/blender_keyed_joint_contact_v23.py` at angles 0,1,5,15,30,54.431 degrees: every added key overlaps the moving bushing (10 BVH triangle overlaps) and its mandibular slot wall (4 overlaps). No key-to-stationary-pin overlaps were detected. **This is a failed precise-fit test**: the keyed parts are currently interpenetrating geometry, not a designed tolerance-verified fastening.
- Blender part-isolated reference mask QA: right jaw IoU .47668 vs baseline v21 .47708 (slight decline). Other parts largely unchanged. No claim of reference-fidelity improvement.
- The v22 dense 109-angle clearance check was for v21 geometry, **not** repeated for the newly modified keyed system. The v22 results must not be attributed to v23.
- No physical simulation, load transfer test, CNC/print tolerance stack, or actual game export has been performed.

## Acceptance decision
Branch retained as **experimental, not accepted for final mechanical assembly**. Required correction: generate keyed protrusions integral with the bushing, cut matching clearance-fit female slots in the lug, test zero unwanted triangle penetration with 109+ pose sweep, and verify axial retention, torque transmission, and both reference profiles together. Do not merge to main. VPS untouched.
