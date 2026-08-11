"""Disk MI parent / master integrity for EnvSandbox Materials (no editor).

Extracts /Game/... refs from MI_*.uasset under EnvSandbox/Materials and flags:
  - missing parent-like material refs (M_/MI_/MF_)
  - missing texture refs
  - blessed-master presence under Materials/Masters/

Companion to audit_material_library.py / audit_universal_instance_overrides.py
(editor-only). Writes Saved/Audit/mi_master_integrity_disk.json.

Run:
  python Content/Python/audit_mi_master_integrity_disk.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "Content"
MATERIALS_ROOT = CONTENT_ROOT / "EnvSandbox" / "Materials"
MASTERS_ROOT = MATERIALS_ROOT / "Masters"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "mi_master_integrity_disk.json"

BLESSED_MASTERS = (
    "M_Master_Toon_Universal",
    "M_Master_Toon_Landscape_HeightBlend",
    "M_Master_Toon_Cosmic",
    "M_Master_SDF_Toon",
    "M_Toon_SDF",
    "M_ToonFoliage",
    "M_Water_Master_Grand_v6",
)

PATH_RE = re.compile(rb"(/Game/[A-Za-z0-9_./-]+)\x00")
MATERIAL_PREFIX = re.compile(r"^(M_|MI_|MF_|TP_)", re.I)


def asset_game_path(uasset: Path) -> str:
    rel = uasset.relative_to(CONTENT_ROOT).with_suffix("")
    return "/Game/" + rel.as_posix()


def extract_paths(data: bytes) -> set[str]:
    return {m.group(1).decode("ascii", "ignore") for m in PATH_RE.finditer(data)}


def resolve_on_disk(game_path: str) -> Path | None:
    if not game_path.startswith("/Game/"):
        return None
    candidate = CONTENT_ROOT / (game_path.removeprefix("/Game/") + ".uasset")
    return candidate if candidate.exists() else None


def is_texture_ref(ref: str) -> bool:
    name = ref.rsplit("/", 1)[-1]
    return (
        "/Textures/" in ref
        or name.startswith("T_")
        or any(name.startswith(p) for p in ("Marble_", "Perlin_", "Voronoi_", "Noise_", "SDF_"))
    )


def scan_masters() -> dict:
    on_disk = sorted(p.stem for p in MASTERS_ROOT.glob("*.uasset")) if MASTERS_ROOT.exists() else []
    blessed = {
        name: (MASTERS_ROOT / f"{name}.uasset").exists() for name in BLESSED_MASTERS
    }
    extras = [n for n in on_disk if n not in BLESSED_MASTERS]
    return {
        "masters_dir": str(MASTERS_ROOT),
        "blessed_present": blessed,
        "blessed_all_present": all(blessed.values()),
        "blessed_missing": [n for n, ok in blessed.items() if not ok],
        "on_disk_count": len(on_disk),
        "on_disk": on_disk,
        "extras_beyond_blessed_7": extras,
    }


def scan_mi_integrity() -> dict:
    instances: list[str] = []
    missing_parent_like: list[dict[str, str]] = []
    missing_textures: list[dict[str, str]] = []
    parent_hits: dict[str, list[str]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()

    if not MATERIALS_ROOT.exists():
        return {"error": f"missing {MATERIALS_ROOT}"}

    for p in MATERIALS_ROOT.rglob("MI_*.uasset"):
        ap = asset_game_path(p)
        instances.append(ap)
        try:
            data = p.read_bytes()
        except OSError:
            continue
        for ref in extract_paths(data):
            if ref == ap:
                continue
            name = ref.rsplit("/", 1)[-1]
            if MATERIAL_PREFIX.match(name):
                parent_hits[ap].append(ref)
                if resolve_on_disk(ref) is None:
                    key = (ap, ref)
                    if key not in seen:
                        seen.add(key)
                        missing_parent_like.append({"source": ap, "target": ref})
            elif is_texture_ref(ref) and resolve_on_disk(ref) is None:
                key = (ap, ref)
                if key not in seen:
                    seen.add(key)
                    missing_textures.append({"source": ap, "target": ref})

    # Unique missing targets
    missing_parent_targets = sorted({r["target"] for r in missing_parent_like})
    missing_texture_targets = sorted({r["target"] for r in missing_textures})

    return {
        "mi_count": len(instances),
        "missing_parent_like_refs": missing_parent_like,
        "missing_parent_like_count": len(missing_parent_like),
        "missing_parent_targets": missing_parent_targets,
        "missing_texture_refs": missing_textures,
        "missing_texture_ref_count": len(missing_textures),
        "missing_texture_targets": missing_texture_targets,
        "instances_with_no_material_ref": [
            ap for ap in instances if not parent_hits.get(ap)
        ],
    }


def print_report(report: dict) -> None:
    masters = report["masters"]
    mi = report["mi"]
    print("=" * 60)
    print("MI <-> Master Integrity (disk)")
    print("=" * 60)
    print(f"Blessed 7 all present: {masters['blessed_all_present']}")
    if masters["blessed_missing"]:
        print(f"  MISSING: {masters['blessed_missing']}")
    print(f"Masters on disk: {masters['on_disk_count']} (extras beyond 7: {len(masters['extras_beyond_blessed_7'])})")
    print(f"MI_ scanned: {mi.get('mi_count', 0)}")
    print(f"Missing parent-like refs: {mi.get('missing_parent_like_count', 0)}")
    for t in (mi.get("missing_parent_targets") or [])[:15]:
        print(f"  parent-like: {t}")
    print(f"Missing texture refs from MIs: {mi.get('missing_texture_ref_count', 0)}")
    for t in (mi.get("missing_texture_targets") or [])[:15]:
        print(f"  texture: {t}")
    print(f"\nReport: {REPORT_PATH}")


def main() -> int:
    report = {
        "masters": scan_masters(),
        "mi": scan_mi_integrity(),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
