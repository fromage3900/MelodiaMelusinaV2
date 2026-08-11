"""Inventory static meshes and flag bad/duplicate names.

Run standalone:
  python Content/Python/audit_static_mesh_inventory.py

Writes:
  Saved/Audit/static_mesh_inventory.json
"""
from __future__ import annotations

import json
import re
import struct
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "static_mesh_inventory.json"

BAD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"SM_SM_", re.I), "double_SM_prefix"),
    (re.compile(r"wallhi\d*", re.I), "wallhi_placeholder"),
    (re.compile(r"wallmid\d*", re.I), "wallmid_placeholder"),
    (re.compile(r"wallshort\d*", re.I), "wallshort_placeholder"),
    (re.compile(r"wallwindow", re.I), "wallwindow_placeholder"),
    (re.compile(r"PolySphere\d+", re.I), "engine_primitive"),
    (re.compile(r"Shape_\w+", re.I), "engine_primitive"),
    (re.compile(r"Cube_\d+", re.I), "engine_primitive"),
    (re.compile(r"SM_Block_", re.I), "greybox_block"),
    (re.compile(r"Deco\d+$", re.I), "generic_deco_number"),
    (re.compile(r"UMesh_", re.I), "procedural_placeholder"),
    (re.compile(r"^SM_[A-Za-z]{1,2}\d+$"), "cryptic_short"),
]


def game_path(p: Path) -> str:
    rel = p.relative_to(CONTENT).with_suffix("")
    return "/Game/" + rel.as_posix()


def _read_bounds_hint(data: bytes) -> dict[str, float] | None:
    """Best-effort AABB from StaticMesh export data in uasset (approximate)."""
    idx = data.find(b"BoundingBox")
    if idx < 0:
        return None
    # Heuristic: scan for plausible float triplets near bbox marker
    window = data[idx : idx + 512]
    floats: list[float] = []
    for off in range(0, len(window) - 12, 4):
        try:
            v = struct.unpack("<f", window[off : off + 4])[0]
        except struct.error:
            continue
        if 0.01 < abs(v) < 50000:
            floats.append(v)
    if len(floats) < 6:
        return None
    xs, ys, zs = floats[0::3][:4], floats[1::3][:4], floats[2::3][:4]
    if not xs or not ys or not zs:
        return None
    return {
        "extent_x": round(max(xs) - min(xs), 2),
        "extent_y": round(max(ys) - min(ys), 2),
        "extent_z": round(max(zs) - min(zs), 2),
    }


def _suggest_name(stem: str, folder: str, bounds: dict[str, float] | None) -> str | None:
    """Suggest rename from folder context + silhouette proportions."""
    if bounds:
        x, y, z = bounds["extent_x"], bounds["extent_y"], bounds["extent_z"]
        dims = sorted([x, y, z], reverse=True)
        tall = dims[0]
        mid, small = dims[1], dims[2]
        aspect = tall / max(small, 0.01)
        flat = mid / max(small, 0.01)

        if aspect > 4 and tall > 200:
            kind = "Column" if small < 80 else "Tower"
        elif aspect > 2.5 and z < max(x, y) * 0.4:
            kind = "Wall"
        elif flat > 3 and small < 50:
            kind = "Floor" if "floor" in folder.lower() else "Slab"
        elif tall < 120 and mid < 120 and small < 120:
            kind = "Rock" if "rock" in folder.lower() or "greybox" in folder.lower() else "Prop"
        elif tall > 80 and mid > 40:
            kind = "Tree" if "sakura" in folder.lower() or "foliage" in folder.lower() else "Monolith"
        else:
            kind = None

        if kind:
            folder_tag = ""
            if "Greybox_Kit" in folder:
                folder_tag = "Greybox"
            elif "Sakura" in folder:
                folder_tag = "Sakura"
            elif "MagiciansLibrary" in folder or "Library" in folder:
                folder_tag = "Kit"
            elif "WPTerrains" in folder or "Terrain" in folder:
                folder_tag = "Terrain"
            prefix = f"SM_{folder_tag}_" if folder_tag else "SM_"
            return f"{prefix}{kind}_{stem.split('_')[-1]}"

    # Name-based fixes without bounds
    fixes = {
        "SM_SM_Rock_1": "SM_Greybox_Rock_A",
        "SM_SM_Rock_2": "SM_Greybox_Rock_B",
        "SM_SM_Rock_3": "SM_Greybox_Rock_C",
        "SM_UMesh_PolySphere5": "SM_Sakura_PetalProxy_Sphere",
    }
    return fixes.get(stem)


def main() -> int:
    meshes = sorted(CONTENT.rglob("SM_*.uasset"))
    by_folder: dict[str, list[str]] = defaultdict(list)
    flagged: list[dict] = []
    stem_locs: dict[str, list[str]] = defaultdict(list)

    for p in meshes:
        gp = game_path(p)
        stem = p.stem
        folder = p.parent.relative_to(CONTENT).as_posix()
        by_folder[folder].append(stem)
        stem_locs[stem].append(gp)
        issues = [label for rx, label in BAD_PATTERNS if rx.search(stem)]
        if not issues:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            data = b""
        bounds = _read_bounds_hint(data)
        suggested = _suggest_name(stem, folder, bounds)
        flagged.append(
            {
                "path": gp,
                "name": stem,
                "folder": folder,
                "issues": issues,
                "size_kb": round(p.stat().st_size / 1024, 1),
                "bounds_hint": bounds,
                "suggested_name": suggested,
            }
        )

    dupes = {k: v for k, v in stem_locs.items() if len(v) > 1}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(meshes),
        "folder_count": len(by_folder),
        "flagged_count": len(flagged),
        "duplicate_stem_count": len(dupes),
        "by_folder": {k: sorted(v) for k, v in sorted(by_folder.items(), key=lambda x: -len(x[1]))},
        "flagged": flagged,
        "duplicate_stems": dupes,
        "rename_candidates": [f for f in flagged if f.get("suggested_name") and f["suggested_name"] != f["name"]],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"total": len(meshes), "flagged": len(flagged), "rename_candidates": len(report["rename_candidates"]), "out": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
