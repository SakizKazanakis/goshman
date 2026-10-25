"""GOSHMAN command-line interface for offline operations and automation."""
import argparse
from pathlib import Path
import sys
import json
from .project import create_project, load_project, import_reference, save_project, verify_references
from .export import export_atlas
from .quality import audit_project
from .reference_views import prepare_turnaround
from .reconstruction import run_multiview_job
from .backend import run_blender


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="GOSHMAN: crocodile animatronic asset pipeline")
    sub = p.add_subparsers(dest="action", required=True)
    new = sub.add_parser("new", help="Initialize project folder")
    new.add_argument("folder", type=Path)
    new.add_argument("--name", default="Animatronic Crocodile Cowboy")
    ref = sub.add_parser("reference", help="Import image without modifying original")
    ref.add_argument("folder", type=Path)
    ref.add_argument("image", type=Path)
    ref.add_argument("--role", default="unclassified")
    info = sub.add_parser("check", help="Check reference integrity and configuration")
    info.add_argument("folder", type=Path)
    gen = sub.add_parser("generate", help="Run procedural Blender scene generator")
    gen.add_argument("folder", type=Path)
    gen.add_argument("--blender")
    gen.add_argument("--render", action="store_true")
    gen.add_argument("--no-export", action="store_true")
    gen.add_argument("--size", type=int, default=512)
    gen.add_argument("--pbr-resolution", type=int, choices=(0,256,512,1024,2048), default=256)
    extract = sub.add_parser("prepare-views", help="Crop the supplied five-view character reference")
    extract.add_argument("folder", type=Path)
    reconstruct = sub.add_parser("reconstruct", help="Opt-in neural multiview 3D mesh job")
    reconstruct.add_argument("folder", type=Path)
    reconstruct.add_argument("--provider", choices=("meshy","tripo"), required=True)
    reconstruct.add_argument("--approve-upload", action="store_true",
                             help="Explicitly approve transmitting the four private views to the provider")
    reconstruct.add_argument("--approve-billing", action="store_true",
                             help="Explicitly approve the provider's paid generation operation")
    reconstruct.add_argument("--timeout", type=int, default=900)
    audit = sub.add_parser("audit", help="Validate actual Blender/GLB/PNG outputs (not visual fidelity)")
    audit.add_argument("folder", type=Path)
    atlas = sub.add_parser("atlas", help="Create Fusion spritesheet from PNG sequence")
    atlas.add_argument("input_dir", type=Path)
    atlas.add_argument("output", type=Path)
    atlas.add_argument("--name", default="idle")
    atlas.add_argument("--fps", type=int, default=12)
    atlas.add_argument("--columns", type=int, default=6)
    args = p.parse_args(argv)
    try:
        if args.action == "new":
            x = create_project(args.folder, args.name)
            print(x.project_id)
        elif args.action == "reference":
            project = load_project(args.folder)
            r = import_reference(args.folder, project, args.image, args.role)
            print(json.dumps(vars(r), ensure_ascii=False))
        elif args.action == "check":
            pr = load_project(args.folder)
            errors = verify_references(args.folder, pr)
            print(json.dumps({"name": pr.name, "references": len(pr.references), "errors": errors}, ensure_ascii=False))
            return 2 if errors else 0
        elif args.action == "generate":
            result = run_blender(args.folder, args.blender, args.render, not args.no_export,
                                 args.size, pbr_resolution=args.pbr_resolution)
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return result.returncode
        elif args.action == "atlas":
            print(json.dumps(export_atlas(args.input_dir, args.output, args.name, args.fps, args.columns), ensure_ascii=False, indent=2))
        elif args.action == "prepare-views":
            print(json.dumps(prepare_turnaround(args.folder), ensure_ascii=False, indent=2))
        elif args.action == "reconstruct":
            state = run_multiview_job(args.folder, args.provider,
                 approve_upload=args.approve_upload,
                 approve_billing=args.approve_billing,
                 timeout_seconds=args.timeout)
            print(json.dumps(state, ensure_ascii=False, indent=2))
            return 0 if state["status"] == "PASS_TECHNICAL" else 2
        elif args.action == "audit":
            report = audit_project(args.folder)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["status"] == "PASS_TECHNICAL" else 2
        return 0
    except (OSError, ValueError, RuntimeError) as err:
        print(f"GOSHMAN ERROR: {err}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
