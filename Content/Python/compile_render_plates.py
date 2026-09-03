"""Compile UE render outputs into a structured renders manifest.

This converts existing PNG outputs (from viewport captures and Monolith captures)
into a canonical JSON manifest consumed by `portfolio_aggregator.py`.

Output:
  Saved/Portfolio/Renders/renders_manifest.json

Design goals:
- Always write a valid manifest, even if no inputs exist
- Never modify exporter logic; this is a read-only compiler over existing files
- Figma-oriented presentation metadata for technical director readability
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import portfolio_output_layout as portfolio_fs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RENDERS_ROOT = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders"
MANIFEST_PATH = RENDERS_ROOT / "renders_manifest.json"


@dataclass(frozen=True)
class PlatePresentation:
    figma_component: str
    grid_columns: tuple[int, int] | None = None
    frame_width_px: int | None = None
    frame_height_px: int | None = None
    fill_mode: str | None = None
    plate_role: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"figma_component": self.figma_component}
        if self.grid_columns:
            out["grid_columns"] = [self.grid_columns[0], self.grid_columns[1]]
        if self.frame_width_px is not None:
            out["frame_width_px"] = int(self.frame_width_px)
        if self.frame_height_px is not None:
            out["frame_height_px"] = int(self.frame_height_px)
        if self.fill_mode is not None:
            out["fill_mode"] = str(self.fill_mode)
        if self.plate_role is not None:
            out["plate_role"] = str(self.plate_role)
        return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root_str() -> str:
    # Use forward slashes per Export Standardization Notes.
    return PROJECT_ROOT.as_posix()


def _warn(warnings: list[str], message: str) -> None:
    warnings.append(message)
    print(f"[compile_render_plates] WARNING: {message}", file=sys.stderr)


_RES_RE = re.compile(r"(?P<w>\d{2,5})x(?P<h>\d{2,5})", re.IGNORECASE)


def _parse_resolution_from_name(name: str) -> tuple[int | None, int | None]:
    m = _RES_RE.search(name)
    if not m:
        return None, None
    try:
        return int(m.group("w")), int(m.group("h"))
    except Exception:
        return None, None


def _aspect_ratio_string(width: int | None, height: int | None) -> str | None:
    if not width or not height or width <= 0 or height <= 0:
        return None
    # Keep a small set of common labels.
    if width * 9 == height * 16:
        return "16:9"
    if width * 5 == height * 4:
        return "4:5"
    if width == height:
        return "1:1"
    return f"{width}:{height}"


def _presentation_defaults(kind: str) -> PlatePresentation:
    # Mirrors PORTFOLIO_PIPELINE.md §2.3 defaults (TD readability, not visual design).
    if kind == "hero":
        return PlatePresentation(
            figma_component="HeroShowcase",
            grid_columns=(1, 12),
            frame_width_px=1280,
            frame_height_px=720,
            fill_mode="aspect_crop",
            plate_role="hero_showcase",
        )
    if kind == "breakdown":
        return PlatePresentation(
            figma_component="BreakdownGrid",
            grid_columns=(1, 6),
            frame_width_px=628,
            frame_height_px=628,
            fill_mode="fit",
            plate_role="breakdown_sheet",
        )
    if kind == "materials":
        return PlatePresentation(
            figma_component="MaterialSwatchCard",
            grid_columns=(7, 9),
            frame_width_px=302,
            frame_height_px=302,
            fill_mode="fit",
            plate_role="material_swatch",
        )
    if kind == "pcg":
        return PlatePresentation(
            figma_component="SpecCardTable",
            grid_columns=(10, 12),
            frame_width_px=302,
            frame_height_px=302,
            fill_mode="fit",
            plate_role="pcg_visualization",
        )
    # Fallback for future kinds (trims, etc.)
    return PlatePresentation(figma_component="UnknownPlate")


def build_plate_entry(path: Path | str, kind: str, *, metadata: dict | None = None) -> dict:
    """Build a canonical plate entry for a single image.

    - `path`: filesystem path to the PNG/JPG
    - `kind`: one of: hero, breakdown, materials, pcg (others allowed but treated as unknown)
    - `metadata`: optional capture metadata to include under `capture`
    """
    p = Path(path)
    name = p.name
    width, height = _parse_resolution_from_name(name)
    pres = _presentation_defaults(kind)

    capture = {
        "mode": None,
        "camera": None,
        "asset_path": None,
        "material_paths": [],
    }
    if isinstance(metadata, dict):
        # Shallow merge, but keep known keys stable.
        for k, v in metadata.items():
            if k in capture:
                capture[k] = v
            else:
                capture[k] = v

    entry: dict[str, Any] = {
        "path": p.as_posix(),
        "filename": name,
        "kind": kind,
        "width": width,
        "height": height,
        "aspect_ratio": _aspect_ratio_string(width, height),
        "level": None,
        "source": None,
        "presentation": pres.to_dict(),
        "capture": capture,
    }
    return entry


def scan_disk_plates(*, project_root: Path | None = None) -> dict[str, list[dict]]:
    """Scan the Saved/Portfolio/Renders tree for existing plates.

    Returns dict keyed by manifest groups: hero, breakdown, materials, pcg.
    """
    root = project_root or PROJECT_ROOT
    renders_root = root / "Saved" / "Portfolio" / "Renders"
    paths = portfolio_fs.portfolio_paths(project_root=root)

    hero_dir = Path(paths["hero_dir"])
    breakdown_dir = Path(paths["breakdown_dir"])
    materials_dir = renders_root / "Materials"
    trims_dir = renders_root / "Trims"  # scanned but placed under `materials` for now

    groups: dict[str, list[dict]] = {"hero": [], "breakdown": [], "materials": [], "pcg": []}

    def scan_dir(directory: Path, kind: str, pattern: str = "*.png") -> None:
        if not directory.is_dir():
            return
        for file in sorted(directory.glob(pattern)):
            if not file.is_file():
                continue
            groups[kind].append(build_plate_entry(file, kind, metadata={"source": "disk_scan"}))

    scan_dir(hero_dir, "hero", "hero_*.png")
    scan_dir(breakdown_dir, "breakdown", "breakdown_*.png")
    scan_dir(materials_dir, "materials", "*.png")
    scan_dir(trims_dir, "materials", "*.png")
    # pcg group reserved for future (heatmaps, density plates, etc.)
    return groups


def merge_capture_results(*results: dict | None) -> dict[str, list[dict]]:
    """Normalize results from viewport exporter / Monolith calls into plate lists."""
    groups: dict[str, list[dict]] = {"hero": [], "breakdown": [], "materials": [], "pcg": []}

    for result in results:
        if not isinstance(result, dict):
            continue

        # render_exporter.export_renders() shape:
        # { timestamp, hero:{ok, path, ...}, breakdown:{ok|skipped, path?, ...} }
        if "hero" in result and isinstance(result.get("hero"), dict):
            hero = result["hero"]
            path = hero.get("path")
            if path:
                groups["hero"].append(
                    build_plate_entry(
                        path,
                        "hero",
                        metadata={
                            "source": hero.get("source") or "viewport",
                            "camera": hero.get("camera"),
                        },
                    )
                )

        if "breakdown" in result and isinstance(result.get("breakdown"), dict):
            bd = result["breakdown"]
            path = bd.get("path")
            if path:
                groups["breakdown"].append(
                    build_plate_entry(
                        path,
                        "breakdown",
                        metadata={
                            "source": bd.get("source") or "viewport",
                            "camera": bd.get("camera"),
                            "mode": bd.get("mode"),
                        },
                    )
                )

        # Monolith return shapes are not yet standardized in this repo.
        # We accept a minimal `{"kind": "...", "path": "...", ...}` entry.
        if "plates" in result and isinstance(result.get("plates"), list):
            for plate in result["plates"]:
                if not isinstance(plate, dict):
                    continue
                kind = str(plate.get("kind") or "")
                if kind not in groups:
                    continue
                path = plate.get("path")
                if not path:
                    continue
                groups[kind].append(build_plate_entry(path, kind, metadata=plate.get("capture") or {}))

    return groups


def compile_renders_manifest(*, export_result: dict | None = None, scan_disk: bool = True) -> dict:
    """Compile the final renders_manifest.json payload.

    - `export_result`: optional dict from `render_exporter.export_renders()`
    - `scan_disk`: include disk scan plates (recommended; makes compiler resilient)
    """
    warnings: list[str] = []

    # Ensure canonical folder layout exists.
    try:
        portfolio_fs.ensure_portfolio_layout()
    except Exception as exc:
        _warn(warnings, f"ensure_portfolio_layout failed: {exc}")

    merged = merge_capture_results(export_result or {})

    if scan_disk:
        disk = scan_disk_plates()
        # Combine and de-dupe by absolute path string.
        for key in ("hero", "breakdown", "materials", "pcg"):
            seen: set[str] = set()
            combined: list[dict] = []
            for item in merged.get(key, []) + disk.get(key, []):
                p = str(item.get("path") or "")
                if not p or p in seen:
                    continue
                seen.add(p)
                combined.append(item)
            merged[key] = combined

    # Null-safe outputs: always arrays for groups.
    for key in ("hero", "breakdown", "materials", "pcg"):
        if key not in merged or not isinstance(merged[key], list):
            merged[key] = []

    ok = True  # writing a manifest is always "ok"; missing plates are warnings, not failure.
    if not merged["hero"]:
        _warn(warnings, "hero: no plates found")
    if not merged["breakdown"]:
        _warn(warnings, "breakdown: no plates found")

    manifest = {
        "generated_at": _now_iso(),
        "generated_by": "compile_render_plates.py",
        "ok": ok,
        "project_root": _project_root_str(),
        "warnings": warnings,
        "hero": merged["hero"],
        "breakdown": merged["breakdown"],
        "materials": merged["materials"],
        "pcg": merged["pcg"],
    }
    return manifest


def write_renders_manifest(manifest: dict, *, path: Path | None = None) -> Path:
    out = path or MANIFEST_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return out


def main() -> int:
    payload = compile_renders_manifest(export_result=None, scan_disk=True)
    out = write_renders_manifest(payload)
    print(
        f"RENDERS_MANIFEST ok={payload.get('ok')} "
        f"hero={len(payload.get('hero') or [])} "
        f"breakdown={len(payload.get('breakdown') or [])} "
        f"materials={len(payload.get('materials') or [])} "
        f"pcg={len(payload.get('pcg') or [])} -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

