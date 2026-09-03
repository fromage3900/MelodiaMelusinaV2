#!/usr/bin/env python3
"""Batch convert images via Material Maker Surreal Animated PBR master graphs.

Static export (UE5):
  py Content/Python/batch_mm_surreal_convert.py --input-dir D:/Art/Refs --output-dir Saved/MM_Export --dry-run

Animated frame bake (Static graph, patches $BakeTime per frame):
  py Content/Python/batch_mm_surreal_convert.py --input-dir D:/Art/Refs --output-dir Saved/MM_Export --animate --frames 16 --dry-run

Options:
  --mm-exe          Path to material_maker executable (auto-detect if omitted)
  --template        Static .ptex template path (default: v2 Static master)
  --preset          Sets Remote style weights in cloned graph
  --copy-to-ue      Copy exports to Content/EnvSandbox/Textures/Source/MM_Batch/
  --spritesheet     Pack animated frames into row spritesheets per map suffix
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MM_DIR = PROJECT_ROOT / "Tools" / "MaterialMaker"
DEFAULT_TEMPLATE = MM_DIR / "MM_Master_SurrealAnimatedPBR_v2_Static.ptex"
MANIFEST_DIR = PROJECT_ROOT / "Saved" / "Audit"
UE_TEXTURE_ROOT = PROJECT_ROOT / "Content" / "EnvSandbox" / "Textures" / "Source" / "MM_Batch"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tga", ".webp", ".bmp", ".exr"}

PRESETS: dict[str, dict[str, float]] = {
    "NeutralBatch": {"StyleNikki": 0, "StyleMadoka": 0, "StyleItto": 0, "StyleCelestial": 0},
    "NikkiHero": {"StyleNikki": 1.0, "StyleMadoka": 0, "StyleItto": 0, "StyleCelestial": 0.2, "SparkleDriftSpeed": 0.45},
    "MadokaNeon": {"StyleNikki": 0.2, "StyleMadoka": 0.85, "StyleItto": 0, "StyleCelestial": 0, "MadokaVeinEmissive": 0.5},
    "IttoBold": {"StyleNikki": 0, "StyleMadoka": 0, "StyleItto": 0.9, "StyleCelestial": 0, "IttoInkStrength": 0.75},
    "CelestialDeep": {"StyleNikki": 0.15, "StyleMadoka": 0, "StyleItto": 0, "StyleCelestial": 0.8, "CelestialTwinkle": 0.7},
    "SakuraDream": {"StyleNikki": 0.85, "StyleMadoka": 0.35, "StyleItto": 0, "StyleCelestial": 0.25, "NikkiPastelLift": 0.3},
}


def find_mm_exe(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    for candidate in [
        Path(os.environ.get("MATERIAL_MAKER_EXE", "")),
        Path(r"C:\Program Files\Material Maker\material_maker.exe"),
        Path(r"C:\scoop\apps\material-maker\current\material_maker.exe"),
        Path.home() / "scoop/apps/material-maker/current/material_maker.exe",
    ]:
        if candidate and candidate.is_file():
            return candidate
    which = shutil.which("material_maker") or shutil.which("material-maker")
    return Path(which) if which else None


def load_graph(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_graph(path: Path, graph: dict) -> None:
    path.write_text(json.dumps(graph, indent="\t") + "\n", encoding="utf-8")


def patch_source_image(graph: dict, image_path: Path, *, ptex_dir: Path) -> None:
    rel = os.path.relpath(image_path.resolve(), ptex_dir.resolve()).replace("\\", "/")
    for node in graph.get("nodes", []):
        if node.get("type") == "image" and node.get("name") == "SourceImage":
            node.setdefault("parameters", {})["image"] = rel


def patch_remote_params(graph: dict, updates: dict[str, float]) -> None:
    for node in graph.get("nodes", []):
        if node.get("type") != "remote" or node.get("name") != "Remote_MasterParams":
            continue
        params = node.setdefault("parameters", {})
        for key, val in updates.items():
            params[key] = val


def patch_bake_time(graph: dict, t: float) -> None:
    patch_remote_params(graph, {"BakeTime": t})


def iter_images(input_dir: Path) -> list[Path]:
    return [p for p in sorted(input_dir.iterdir()) if p.suffix.lower() in IMAGE_EXTS and p.is_file()]


def safe_name(path: Path) -> str:
    return re.sub(r"[^\w\-]+", "_", path.stem).strip("_") or "image"


def run_mm_export(mm_exe: Path, ptex: Path, out_dir: Path, *, target: str = "Unreal") -> subprocess.CompletedProcess:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(mm_exe),
        "--export-material",
        "--target",
        target,
        "-o",
        str(out_dir),
        str(ptex),
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def pack_spritesheet(frame_paths: list[Path], out_path: Path, *, columns: int = 8) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    if not frame_paths:
        return
    frames = [Image.open(p).convert("RGBA") for p in frame_paths]
    w, h = frames[0].size
    rows = (len(frames) + columns - 1) // columns
    sheet = Image.new("RGBA", (w * columns, h * rows), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        c, r = i % columns, i // columns
        sheet.paste(fr, (c * w, r * h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    for fr in frames:
        fr.close()


def collect_exported_maps(out_dir: Path) -> list[str]:
    if not out_dir.is_dir():
        return []
    return sorted(p.name for p in out_dir.iterdir() if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch MM surreal PBR convert")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--mm-exe", type=str, default=None)
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), default="NeutralBatch")
    parser.add_argument("--animate", action="store_true")
    parser.add_argument("--frames", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--copy-to-ue", action="store_true")
    parser.add_argument("--spritesheet", action="store_true")
    parser.add_argument("--work-dir", type=Path, default=None, help="Temp cloned ptex folder")
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        print(f"Missing input dir: {args.input_dir}", file=sys.stderr)
        return 1
    if not args.template.is_file():
        print(f"Missing template: {args.template}", file=sys.stderr)
        return 1

    mm_exe = find_mm_exe(args.mm_exe)
    if mm_exe is None and not args.dry_run:
        print("material_maker not found. Install MM or pass --mm-exe PATH", file=sys.stderr)
        return 1

    work_dir = args.work_dir or (args.output_dir / "_ptex_clones")
    work_dir.mkdir(parents=True, exist_ok=True)
    ptex_dir = work_dir

    manifest: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "template": str(args.template),
        "preset": args.preset,
        "animate": args.animate,
        "frames": args.frames if args.animate else 1,
        "mm_exe": str(mm_exe) if mm_exe else None,
        "jobs": [],
    }

    images = iter_images(args.input_dir)
    if not images:
        print(f"No images in {args.input_dir}")
        return 1

    preset_vals = PRESETS[args.preset]

    for image in images:
        name = safe_name(image)
        job: dict = {"image": str(image), "name": name, "exports": []}
        base_out = args.output_dir / name

        frame_count = args.frames if args.animate else 1
        for frame in range(frame_count):
            graph = load_graph(args.template)
            patch_source_image(graph, image, ptex_dir=ptex_dir)
            patch_remote_params(graph, preset_vals)
            if args.animate:
                patch_bake_time(graph, frame / max(1, frame_count))

            suffix = f"_{frame:03d}" if args.animate else ""
            clone_path = work_dir / f"{name}{suffix}.ptex"
            save_graph(clone_path, graph)

            out_dir = base_out / f"frame_{frame:03d}" if args.animate else base_out
            if args.dry_run:
                job["exports"].append({"ptex": str(clone_path), "out_dir": str(out_dir), "dry_run": True})
                continue

            assert mm_exe is not None
            proc = run_mm_export(mm_exe, clone_path, out_dir)
            entry = {
                "ptex": str(clone_path),
                "out_dir": str(out_dir),
                "returncode": proc.returncode,
                "stdout": proc.stdout[-2000:] if proc.stdout else "",
                "stderr": proc.stderr[-2000:] if proc.stderr else "",
                "files": collect_exported_maps(out_dir),
            }
            job["exports"].append(entry)
            if proc.returncode != 0:
                print(f"Export failed for {name} frame {frame}: {proc.stderr}", file=sys.stderr)

        if args.copy_to_ue and not args.dry_run:
            dest = UE_TEXTURE_ROOT / name
            if base_out.is_dir():
                shutil.copytree(base_out, dest, dirs_exist_ok=True)
                job["ue_copy"] = str(dest)

        if args.spritesheet and args.animate and not args.dry_run:
            sheets: dict[str, str] = {}
            for pattern in ("albedo", "emission", "normal", "orm", "height", "opacity", "sss"):
                frames = sorted(base_out.glob(f"frame_*/*_{pattern}.png"))
                if frames:
                    sheet_path = base_out / f"{name}_{pattern}_spritesheet.png"
                    pack_spritesheet(frames, sheet_path)
                    sheets[pattern] = str(sheet_path)
            job["spritesheets"] = sheets

        manifest["jobs"].append(job)

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFEST_DIR / "mm_batch_convert.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Processed {len(images)} image(s). Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
