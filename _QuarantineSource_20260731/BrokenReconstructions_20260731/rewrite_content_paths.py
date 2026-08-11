"""One-shot literal-path rewrite for the 2026-07-09 2-root consolidation.

Rewrites /Game/<old-root> literals in Python/PowerShell tooling to their new
homes (see Content/Python/paths.py). Idempotent; prints a per-file change map.
Run AFTER the corresponding asset batches have moved in-editor.

Usage: python Tools/rewrite_content_paths.py [--dry-run] [--batch 3|4]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ["Content/Python", "deploy", "learner", "Tools"]
EXTS = {".py", ".ps1"}

BATCH3 = {
    "/Game/Textures": "/Game/EnvSandbox/Textures_Shared",
    "/Game/Greybox_Kit": "/Game/EnvSandbox/Greybox_Kit",
    "/Game/Library": "/Game/EnvSandbox/Library",
    "/Game/MaterialFunctions": "/Game/EnvSandbox/MaterialFunctions_Legacy",
    "/Game/MaterialLayers": "/Game/EnvSandbox/MaterialLayers_Legacy",
    "/Game/Alphas_Sparkles": "/Game/EnvSandbox/Alphas_Sparkles",
    "/Game/Stylization": "/Game/EnvSandbox/Stylization",
    "/Game/Sakura": "/Game/EnvSandbox/Sakura",
    "/Game/Assets": "/Game/EnvSandbox/Assets_Legacy",
}

BATCH4 = {
    "/Game/_PROJECT/Meshes/WPTerrains": "/Game/EnvSandbox/Meshes/WPTerrains",
    "/Game/_PROJECT": "/Game/Melodia/_PROJECT",
    "/Game/Game_BP": "/Game/Melodia/Game_BP",
    "/Game/Actor_BP": "/Game/Melodia/Actor_BP",
    "/Game/Blueprints": "/Game/Melodia/Blueprints",
    "/Game/Characters": "/Game/Melodia/Characters",
    "/Game/DataStuctures": "/Game/Melodia/DataStuctures",
    "/Game/Magical": "/Game/Melodia/Magical",
}


def main() -> int:
    """Rewrite content paths."""
    dry = "--dry-run" in sys.argv
    batch = sys.argv[sys.argv.index("--batch") + 1] if "--batch" in sys.argv else "3"

    mapping = dict(BATCH3) if batch == "3" else dict(BATCH4)
    keys = sorted(mapping, key=len, reverse=True)
    changed = {}

    for d in SCAN_DIRS:
        base = ROOT / d

        if not base.is_dir():
            continue

        for f in base.rglob("*"):
            if f.suffix not in EXTS or "__pycache__" in f.parts:
                continue

            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                text = f.read_text(encoding="utf-8-sig")

            out = text
            hits = 0

            for k in keys:
                n = out.count(k)
                if n:
                    out = out.replace(k, mapping[k])
                    hits += n

            out = out.replace("/Game/EnvSandbox/EnvSandbox/", "/Game/EnvSandbox/")
            out = out.replace("/Game/Melodia/Melodia/", "/Game/Melodia/")

            if hits and out != text:
                changed[str(f.relative_to(ROOT))] = hits
                if not dry:
                    f.write_text(out, encoding="utf-8")

    for k, v in sorted(changed.items()):
        print(f"{v:3d}  {k}")

    print(f"total files: {len(changed)}  (batch {batch}{'  DRY' if dry else ''})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
