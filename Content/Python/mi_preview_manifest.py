"""Aggregate full MI catalog with profile-based preview routing.

Writes:
  Saved/Portfolio/MaterialLoops/mi_preview_manifest.json

Run standalone (no editor):
  python Content/Python/mi_preview_manifest.py
  py Content/Python/mi_preview_manifest.py --write
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mi_preview_studio as studio

PROJECT_ROOT = studio.PROJECT_ROOT
OUT_PATH = studio.MANIFEST_JSON

SHOWCASE_DIR = "/Game/EnvSandbox/Materials/Instances/Showcase"
STYLIZED_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/Stylized"
SDF_INST_DIR = "/Game/EnvSandbox/Materials/SDF/Instances"
WATER_V10_DIR = "/Game/EnvSandbox/Materials/Instances/Water/v10"
WATER_V10_INSTANCES = (
    "MI_Water_v10_CalmPond",
    "MI_Water_v10_BiolumGrotto",
    "MI_Water_v10_HeroFLIP",
)
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "material_instance_audit.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _is_cosmic_sdf(name: str) -> bool:
    lower = name.lower()
    return name.startswith("MI_SDF_") and any(k in lower for k in studio.COSMIC_SDF_KEYWORDS)


def _is_trimsheet(name: str) -> bool:
    return name.startswith("MI_ZenTrim_") or name.startswith("MI_ClothTrim_")


def route_preview(
    *,
    name: str,
    profile: str = "TP_Default",
    source: str = "unknown",
    folder: str | None = None,
) -> dict[str, Any]:
    preview_mesh = "sphere"
    # Melodia void tint keys — never UE HQ sky / UDS
    backdrop = studio.DEFAULT_BACKDROP
    priority = "catalog"
    mesh_scale = studio.default_mesh_scale(preview_mesh)
    uv_tiling = (1.0, 1.0)

    if name in studio.NIKKI_PRIORITY:
        priority = "hero"

    if _is_trimsheet(name):
        preview_mesh = "plane_vertical"
        backdrop = "Sakura_SoftVoid"
        mesh_scale = studio.default_mesh_scale(preview_mesh)
    elif name in studio.WATER_LANDSCAPE_NAMES or "Water" in name or "Hydro" in name or "Landscape" in name:
        preview_mesh = "plane_horizontal"
        backdrop = "Studio_Neutral"
        mesh_scale = studio.default_mesh_scale(preview_mesh)
    elif name.startswith("MI_NikkiHero_Sakura") or name in (
        "MI_Show_CherryBlossom",
        "MI_Show_FairyHearts",
        "MI_Show_SkinSoft",
        "MI_Show_NikkiHero",
    ):
        preview_mesh = "sphere"
        backdrop = "Sakura_SoftVoid"
    elif name.startswith("MI_NikkiHero_Cosmic") or name.startswith("MI_NikkiHero_Space") or "Nebula" in name or "Celestial" in name:
        preview_mesh = "sphere"
        backdrop = "Cosmic_DeepField"
    elif name.startswith("MI_NikkiHero_Baroque") or (_is_cosmic_sdf(name) is False and name.startswith("MI_SDF_") and profile in studio.BAROQUE_PROFILES):
        preview_mesh = "sphere"
        backdrop = "Baroque_WarmVault"
    elif _is_cosmic_sdf(name) or name == "MI_SDF_RosyQuartz":
        preview_mesh = "sphere"
        backdrop = "Cosmic_DeepField" if _is_cosmic_sdf(name) else "Sakura_SoftVoid"
    elif name.startswith("MI_SDF_"):
        preview_mesh = "sphere"
        backdrop = "Baroque_WarmVault"
    elif name.startswith("MI_Show_"):
        preview_mesh = "sphere"
        backdrop = "Studio_Neutral"

    if name == "MI_ZenTrim_FlowersLots":
        priority = "hero"
        mesh_scale = (1.2, 1.2, 0.08)
        uv_tiling = (1.0, 1.0)
        backdrop = "Sakura_SoftVoid"

    asset_folder = folder or SHOWCASE_DIR
    if name.startswith("MI_SDF_"):
        asset_folder = SDF_INST_DIR
    elif name.startswith("MI_NikkiHero_"):
        asset_folder = studio.NIKKI_HERO_DIR
    elif _is_trimsheet(name):
        asset_folder = STYLIZED_DIR

    return {
        "id": name,
        "asset_path": _asset_path(asset_folder, name),
        "profile": profile,
        "preview_mesh": preview_mesh,
        "backdrop": backdrop,
        "orbit_speed": 1.0,
        "mesh_scale": list(mesh_scale),
        "uv_tiling": list(uv_tiling),
        "priority": priority,
        "source": source,
        "sequence_path": studio.sequence_path_for_mi(name),
        "output_dir": str(studio.output_dir_for_mi(name).relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }


def _stub_material_lib() -> None:
    """Allow starter_instances import outside the Unreal Python environment."""
    import sys
    import types

    if "material_lib" in sys.modules:
        return
    stub = types.ModuleType("material_lib")
    stub.MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
    stub.MASTER_DIR = f"{stub.MATERIALS_ROOT}/Masters"
    stub.ENV_INST_DIR = f"{stub.MATERIALS_ROOT}/Instances/Environment"
    sys.modules["material_lib"] = stub


def _entries_from_starters() -> list[dict[str, Any]]:
    _stub_material_lib()
    from starter_instances import STARTER_INSTANCES

    rows: list[dict[str, Any]] = []
    for spec in STARTER_INSTANCES:
        name = spec["name"]
        rows.append(
            route_preview(
                name=name,
                profile=str(spec.get("profile", "TP_Default")),
                source="starter_instances",
                folder=SHOWCASE_DIR,
            )
        )
    return rows


def _entries_from_trimsheets() -> list[dict[str, Any]]:
    from setup_trimsheet_instances import all_trimsheet_specs

    rows: list[dict[str, Any]] = []
    for spec in all_trimsheet_specs():
        name = spec["name"]
        folder = spec.get("folder", STYLIZED_DIR)
        rows.append(
            route_preview(
                name=name,
                profile=str(spec.get("profile", "TP_Default")),
                source="trimsheet_instances",
                folder=folder,
            )
        )
    return rows


def _entries_from_sdf_batch() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        from build_melodia_sdf_batch import WAVE1_CATHEDRAL, WAVE2_COSMO, WAVE3_LANDSCAPE

        for wave in (WAVE1_CATHEDRAL, WAVE2_COSMO, WAVE3_LANDSCAPE):
            for spec in wave:
                name = spec["name"]
                tags = spec.get("tags") or []
                tag_text = " ".join(str(t) for t in tags).lower()
                profile = "TP_Gold" if "gold" in tag_text or "gilded" in tag_text else "TP_Default"
                rows.append(route_preview(name=name, profile=profile, source="sdf_batch", folder=SDF_INST_DIR))
        return rows
    except Exception:
        pass

    batch_path = PROJECT_ROOT / "Content" / "Python" / "build_melodia_sdf_batch.py"
    if not batch_path.is_file():
        return rows
    import re

    for match in re.finditer(r'"name":\s*"(MI_SDF_[^"]+)"', batch_path.read_text(encoding="utf-8")):
        name = match.group(1)
        rows.append(route_preview(name=name, profile="TP_Default", source="sdf_batch_parsed", folder=SDF_INST_DIR))
    return rows


def _entries_from_audit() -> list[dict[str, Any]]:
    audit = _read_json(AUDIT_PATH)
    if not isinstance(audit, dict):
        return []
    materials = audit.get("materials")
    if not isinstance(materials, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in materials:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("material_name") or "").strip()
        if not name or not name.startswith("MI_"):
            continue
        path = item.get("path") or item.get("asset_path")
        folder = None
        if isinstance(path, str) and "/Game/" in path:
            folder = path.rsplit("/", 1)[0]
        rows.append(
            route_preview(
                name=name,
                profile=str(item.get("profile") or item.get("shader_family") or "TP_Default"),
                source="material_instance_audit",
                folder=folder,
            )
        )
    return rows


def _dedupe(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    priority_rank = {"hero": 0, "catalog": 1}
    for entry in entries:
        mi_id = entry["id"]
        existing = by_id.get(mi_id)
        if not existing:
            by_id[mi_id] = entry
            continue
        if priority_rank.get(entry.get("priority", "catalog"), 9) < priority_rank.get(
            existing.get("priority", "catalog"), 9
        ):
            by_id[mi_id] = entry
    return sorted(by_id.values(), key=lambda e: (e.get("priority") != "hero", e["id"]))


def _entries_from_nikki_priority() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in studio.NIKKI_PRIORITY:
        folder = SHOWCASE_DIR
        if name.startswith("MI_NikkiHero_"):
            folder = studio.NIKKI_HERO_DIR
        elif name.startswith("MI_SDF_"):
            folder = SDF_INST_DIR
        rows.append(
            route_preview(
                name=name,
                profile="TP_Default",
                source="nikki_priority",
                folder=folder,
            )
        )
    return rows


def _entries_from_water_v10() -> list[dict[str, Any]]:
    return [
        route_preview(
            name=name,
            profile="WaterV10",
            source="water_v10_material_family",
            folder=WATER_V10_DIR,
        )
        for name in WATER_V10_INSTANCES
    ]


def build_manifest() -> dict[str, Any]:
    entries = _dedupe(
        _entries_from_nikki_priority()
        + _entries_from_starters()
        + _entries_from_trimsheets()
        + _entries_from_sdf_batch()
        + _entries_from_audit()
        + _entries_from_water_v10()
    )
    return {
        "generated_at": _now_iso(),
        "generated_by": "mi_preview_manifest.py",
        "studio_display_name": studio.STUDIO_DISPLAY_NAME,
        "level": studio.LEVEL,
        "doctrine": "melodia_void_nikki_lens",
        "nikki_priority": list(studio.NIKKI_PRIORITY),
        "frame_rate": studio.FRAME_RATE,
        "loop_frames": studio.LOOP_FRAMES,
        "resolution": studio.LOOP_RESOLUTION,
        "count": len(entries),
        "entries": entries,
    }


def write_manifest() -> Path:
    manifest = build_manifest()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    web_path = PROJECT_ROOT / "my-site-clean" / "generated" / "mi_preview_manifest.json"
    web_path.parent.mkdir(parents=True, exist_ok=True)
    web_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return OUT_PATH


def load_manifest() -> dict[str, Any]:
    data = _read_json(OUT_PATH)
    if isinstance(data, dict) and data.get("entries"):
        return data
    return build_manifest()


def filter_entries(manifest: dict[str, Any], *, only: str | None = None) -> list[dict[str, Any]]:
    entries = list(manifest.get("entries") or [])
    if only:
        only_lower = only.lower()
        entries = [e for e in entries if e.get("id", "").lower() == only_lower or only_lower in e.get("id", "").lower()]
    return entries


def main() -> int:
    path = write_manifest()
    manifest = build_manifest()
    print(f"OK wrote {path} ({manifest['count']} entries)")
    if "json" in sys.argv:
        print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
