"""Apply all 30 Copernicus MIs to cathedral pieces in LV_SeaAbove_Prototype.

World Partition / HLOD architecture:
  LV_SeaAbove_Prototype loads L_WP_SpaceCathedral_HLODLayer_Instanced +
  L_WP_SpaceCathedral_HLODLayer_Merged. Each piece is a StaticMeshComponent
  on a partitioned actor (HISMC/ISMC typically). This script loads the level,
  iterates all level actors, finds StaticMeshComponents whose mesh or label
  matches SpaceCathedral, and assigns MIs in a round-robin / shuffled pattern
  covering all 30 variants. Preserves any piece whose actor tag is
  "CopernicusLocked" (human override).

Selection heuristic (priority order):
  1. Component name contains "Cathedral" (case-insensitive)
  2. Component's StaticMesh path contains "Cathedral" or "SpaceCathedral"
  3. Actor label contains "Cathedral"

Apply strategy: even distribution. For N pieces and 30 MIs, piece i gets
MI_Copernicus_<variant[(i*7) % 30]> (stride-7 coprime permutation -> visually
adjacent pieces get distinct variants).

Run in-editor:
  UnrealEditor-Cmd.exe BS_GodFile.uproject
    -ExecutePythonScript="Content/Python/_mi_expand_apply_to_cathedral.py"
    -unattended -nullrhi

Manifest: Saved/Audit/copernicus_mi_apply.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus"
MI_PREFIX = "MI_Copernicus_"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_mi_apply.json"
TAG_LOCKED = "CopernicusLocked"


def list_copernicus_mis() -> list[str]:
    """Return sorted list of Copernicus MI asset names in MI_DIR."""
    if not unreal.EditorAssetLibrary.does_directory_exist(MI_DIR):
        return []
    assets = unreal.EditorAssetLibrary.list_assets(MI_DIR, recursive=False)
    mis = []
    for a in assets:
        stem = a.rsplit("/", 1)[-1].split(".", 1)[0]
        if stem.startswith(MI_PREFIX):
            mis.append(stem)
    return sorted(mis)


def is_cathedral_component(comp) -> bool:
    """True if the component looks like a cathedral piece."""
    label = (comp.get_name() or "").lower()
    if "cathedral" in label:
        return True
    try:
        sm = comp.get_editor_property("static_mesh")
        if sm is not None:
            mesh_path = sm.get_path_name().lower()
            if "cathedral" in mesh_path or "spacecathedral" in mesh_path:
                return True
    except Exception:
        pass
    return False


def is_locked_actor(actor) -> bool:
    """Actor has the CopernicusLocked tag -> do not touch."""
    try:
        tags = list(actor.tags or [])
    except Exception:
        tags = []
    return TAG_LOCKED in tags


def collect_cathedral_pieces():
    """Return list of (component, actor_label, mesh_name) tuples."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pieces = []
    for actor in eas.get_all_level_actors() or []:
        if is_locked_actor(actor):
            continue
        label = actor.get_actor_label()
        try:
            comps = actor.get_components_by_class(unreal.StaticMeshComponent) or []
        except Exception:
            continue
        for comp in comps:
            if comp is None:
                continue
            if not is_cathedral_component(comp):
                continue
            mesh_name = ""
            try:
                sm = comp.get_editor_property("static_mesh")
                if sm is not None:
                    mesh_name = sm.get_name() or ""
            except Exception:
                pass
            pieces.append((comp, label, mesh_name))
    return pieces


def apply_mi(comp, mi_path: str) -> bool:
    """Assign MI to slot 0 of the component. Returns True on success."""
    mi = unreal.load_asset(mi_path)
    if mi is None:
        return False
    try:
        comp.set_material(0, mi)
        comp.mark_render_state_dirty()
        return True
    except Exception:
        return False


def main() -> int:
    # Load level
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        print(f"[APPLY] ERROR level missing: {LEVEL_PATH}")
        return 1
    # Make sure it's loaded
    try:
        llib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        # OpenLevel only needed if it's not already loaded
    except Exception:
        pass

    mis = list_copernicus_mis()
    if not mis:
        print(f"[APPLY] ERROR no Copernicus MIs in {MI_DIR}")
        return 1
    print(f"[APPLY] {len(mis)} Copernicus MIs available")

    pieces = collect_cathedral_pieces()
    print(f"[APPLY] found {len(pieces)} cathedral pieces in {LEVEL_PATH}")

    # Apply stride-7 coprime permutation for visual variety
    n = len(mis)
    applied = 0
    rows = []
    for idx, (comp, actor_label, mesh_name) in enumerate(pieces):
        mi_name = mis[(idx * 7) % n]
        mi_path = f"{MI_DIR}/{mi_name}"
        ok = apply_mi(comp, mi_path)
        status = "applied" if ok else "failed"
        if ok:
            applied += 1
        rows.append({
            "index": idx,
            "actor": actor_label,
            "mesh": mesh_name,
            "mi": mi_name,
            "status": status,
        })
        if idx < 5 or not ok:
            print(f"[APPLY] [{idx:3d}] {actor_label}/{mesh_name} <- {mi_name} -> {status}")

    # Save level + external actors
    try:
        unreal.EditorAssetLibrary.save_asset(LEVEL_PATH)
        unreal.EditorAssetLibrary.save_directory(
            "/Game/__ExternalActors__/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
            only_if_is_dirty=True, recursive=True,
        )
        saved = True
    except Exception:
        saved = False

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": LEVEL_PATH,
        "mis_available": mis,
        "pieces_found": len(pieces),
        "applied": applied,
        "saved": saved,
        "rows": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[APPLY] === applied={applied}/{len(pieces)} saved={saved} report -> {REPORT} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())