"""Filesystem layout for Saved/Portfolio exporter outputs.

Ensures directory structure and moves misplaced artifacts from:
  scene_metadata_exporter.py
  render_exporter.py

Run standalone (no editor required):
  python Content/Python/portfolio_output_layout.py
  py Content/Python/portfolio_output_layout.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_ROOT = PROJECT_ROOT / "Saved" / "Portfolio"
METADATA_DIR = PORTFOLIO_ROOT / "Metadata"
RENDERS_DIR = PORTFOLIO_ROOT / "Renders"
HERO_DIR = RENDERS_DIR / "Hero"
BREAKDOWN_DIR = RENDERS_DIR / "Breakdown"
MATERIALS_DIR = RENDERS_DIR / "Materials"
TRIMS_DIR = RENDERS_DIR / "Trims"
SCENE_METADATA_PATH = METADATA_DIR / "scene_metadata.json"

_LAYOUT_DIRS = (
    PORTFOLIO_ROOT,
    METADATA_DIR,
    RENDERS_DIR,
    HERO_DIR,
    BREAKDOWN_DIR,
    MATERIALS_DIR,
    TRIMS_DIR,
)


def portfolio_paths(*, project_root: Path | None = None) -> dict[str, Path]:
    root = project_root or PROJECT_ROOT
    portfolio_root = root / "Saved" / "Portfolio"
    metadata_dir = portfolio_root / "Metadata"
    renders_dir = portfolio_root / "Renders"
    return {
        "project_root": root,
        "portfolio_root": portfolio_root,
        "metadata_dir": metadata_dir,
        "renders_dir": renders_dir,
        "hero_dir": renders_dir / "Hero",
        "breakdown_dir": renders_dir / "Breakdown",
        "materials_dir": renders_dir / "Materials",
        "trims_dir": renders_dir / "Trims",
        "scene_metadata": metadata_dir / "scene_metadata.json",
    }


def ensure_portfolio_layout(*, project_root: Path | None = None) -> dict[str, Path]:
    """Create Saved/Portfolio layout if missing. Returns canonical paths."""
    paths = portfolio_paths(project_root=project_root)
    created: list[str] = []
    for key in (
        "portfolio_root",
        "metadata_dir",
        "renders_dir",
        "hero_dir",
        "breakdown_dir",
        "materials_dir",
        "trims_dir",
    ):
        directory = paths[key]
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(paths["project_root"])))
    paths["created"] = created  # type: ignore[typeddict-item]
    return paths


def _move_file(source: Path, destination: Path, *, dry_run: bool) -> dict | None:
    if source.resolve() == destination.resolve():
        return None
    if destination.exists():
        return {
            "action": "skipped",
            "reason": "destination_exists",
            "source": str(source),
            "destination": str(destination),
        }
    if dry_run:
        return {
            "action": "would_move",
            "source": str(source),
            "destination": str(destination),
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return {
        "action": "moved",
        "source": str(source),
        "destination": str(destination),
    }


def organize_portfolio_outputs(*, project_root: Path | None = None, dry_run: bool = False) -> dict:
    """Place exporter artifacts into canonical folders under Saved/Portfolio."""
    paths = ensure_portfolio_layout(project_root=project_root)
    moves: list[dict] = []

    legacy_metadata = paths["portfolio_root"] / "scene_metadata.json"
    if legacy_metadata.is_file():
        entry = _move_file(legacy_metadata, paths["scene_metadata"], dry_run=dry_run)
        if entry:
            moves.append(entry)

    search_dirs: list[Path] = [paths["portfolio_root"], paths["renders_dir"]]
    patterns = (
        ("hero_*.png", paths["hero_dir"]),
        ("breakdown_*.png", paths["breakdown_dir"]),
        ("grid_*.png", paths["materials_dir"]),
        ("material_*.png", paths["materials_dir"]),
        ("trim_*.png", paths["trims_dir"]),
    )
    seen: set[Path] = set()
    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        for pattern, dest_dir in patterns:
            for source in sorted(search_dir.glob(pattern)):
                if not source.is_file():
                    continue
                resolved = source.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                if source.parent.resolve() == dest_dir.resolve():
                    continue
                entry = _move_file(source, dest_dir / source.name, dry_run=dry_run)
                if entry:
                    moves.append(entry)

    return {
        "portfolio_root": str(paths["portfolio_root"]),
        "paths": {key: str(value) for key, value in paths.items() if isinstance(value, Path)},
        "moves": moves,
        "dry_run": dry_run,
    }


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    paths = ensure_portfolio_layout()
    report = organize_portfolio_outputs(dry_run=dry_run)
    if "json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        created = paths.get("created") or []
        if created:
            print(f"created: {', '.join(created)}")
        else:
            print("layout ok")
        if report["moves"]:
            print(f"organized {len(report['moves'])} file(s)")
            for move in report["moves"]:
                print(f"  {move['action']}: {move.get('source')} -> {move.get('destination')}")
        else:
            print("nothing to reorganize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
