# Four-view image-derived geometry — experimental control asset

**Date:** 2026-10-25

The existing procedural character blockout is NOT used by this path.

The local CPU fallback uses the user's original four authenticated turnaround crops, estimates the character silhouette in each crop (GrabCut), constructs a 3D occupancy volume by orthographic silhouette constraints, runs marching cubes and samples coarse vertex colours from the source images. The output is a real editable GLB polygon mesh.

**Important:** This is **NOT neural inference**. The source images are artistic reference renders from inconsistent perspectives, not calibrated photographs. The OR-union between front/back and left/right mask pairs compensates for incompatible silhouettes at the cost of inaccurate volume. No mechanical joints, hidden parts, facial animation, rig, true PBR materials, or precise likeness can be inferred from it.

## Local command

Install CPU extras separately:

`python -m pip install -e '.[vision]'`

Prepare and verify the private 12-sheet project first:

`python -m goshman.cli check crocodile_project`

`python -m goshman.cli prepare-views crocodile_project`

Create real image-derived geometry without uploading references:

`python -m goshman.cli visual-hull crocodile_project crocodile_project/output/visual_hull`

The output includes:

- `crocodile_multiview_silhouette_seed.glb` — an actual mesh with vertex colours.
- `reconstruction_report.json` — SHA-256 provenance, polygon counts, method limitations, no false AI claim.
- `front_mask.png`, `back_mask.png`, `left_mask.png`, `right_mask.png`.

Tests run on synthetic input in GitHub CI; the actual user sheets **must stay out of public GitHub**. A generated private real-reference GLB can be imported into Blender using the existing `import-ai` command, although its source is **not AI**.

## Still blocked

Real four-view AI inference on the crocodile requires an accessible licensed backend (e.g. Meshy or Tripo), provider credentials and explicit permission to transmit the private images and incur provider credits, or a compatible local GPU and model checkpoint. Neither private uploads nor paid requests have been authorized for this execution environment. Do not present the control GLB as final character geometry or as a pretrained-model result.
