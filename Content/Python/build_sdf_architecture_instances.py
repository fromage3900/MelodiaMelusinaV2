"""Create MI_SDF_Architecture_* instances (Phase 3 — niche SDF catalog).

Creates 5 Material Instances under Instances/SDFArchitecture/, each parenting
an existing SDF architecture master, with defensively-set common scalar
parameters (only parameters that actually exist on the parent are written —
every skip is logged, never silent).

Masters catalogued (from the live Masters/ directory, 2026-08-29):
  M_SDF_EscherGeometry_Enhanced   — optical-illusion tessellation
  M_SDF_Penrose_Staircase         — endless looped stairs
  M_SDF_GothicArchitecture_Enhanced — tracery arches/vaults
  M_SDF_CathedralVault            — ribbed vault ceilings
  M_SDF_TrueParallax              — deep-window parallax SDF

Run in the UE editor (Monolith run_python): build_sdf_architecture_instances.main()
Writes: Saved/Audit/sdf_architecture_instances_2026-08-29.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

MASTER_DIR = "/Game/EnvSandbox/Materials/Masters/SDF"  # registry-verified 2026-08-29
OUT_DIR = "/Game/EnvSandbox/Materials/Instances/SDFArchitecture"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "sdf_architecture_instances_2026-08-29.json"

INSTANCES = {
    # param names below are registry/reflection-verified 2026-08-29; params that
    # don't exist on a given master are skipped and logged (never silent).
    "MI_SDF_Escher_Enhanced": {
        "parent": f"{MASTER_DIR}/M_SDF_EscherGeometry_Enhanced",
        "params": {"UVScale": 3.0, "EdgeStrength": 0.8, "GildingAmount": 0.35,
                   "InkDensity": 0.6, "OilPaintMix": 0.4, "AudioReactivity": 0.5},
    },
    "MI_SDF_Penrose_Stairs": {
        "parent": f"{MASTER_DIR}/M_SDF_Penrose_Staircase",
        "params": {"StairHeight": 1.0, "StairWidth": 1.0, "BallSize": 0.5, "AnimSpeed": 0.5},
    },
    "MI_SDF_Gothic_Arc": {
        "parent": f"{MASTER_DIR}/M_SDF_GothicArchitecture_Enhanced",
        "params": {"UVScale": 2.0, "EdgeStrength": 0.7, "GildingAmount": 0.4},
    },
    "MI_SDF_Cathedral_Vault": {
        "parent": f"{MASTER_DIR}/M_SDF_CathedralVault",
        "params": {"VaultHeight": 1.2, "VaultWidth": 1.0, "RibCount": 8.0,
                   "RibThickness": 0.5, "KeystoneSize": 0.5},
    },
    "MI_SDF_Parallax_Window": {
        "parent": f"{MASTER_DIR}/M_SDF_TrueParallax",
        "params": {"Displacement": 0.1, "BevelRadius": 0.05, "GildingAmount": 0.3},
    },
    # ---- wave 2 (2026-08-29, reflection-verified params) ----
    "MI_SDF_ParallaxPulse": {
        "parent": "/Game/EnvSandbox/Materials/Masters/M_SDF_ParallaxPulse",
        "params": {"BandScale": 8.0, "GlowStrength": 0.6, "PulseSpeed": 1.5},
    },
    "MI_SDF_Musical": {
        "parent": "/Game/_PROJECT/04_Materials/SDF/M_SDF_Musical",
        "params": {"Amplitude": 0.6, "AudioReactivity": 0.8, "BarWidth": 0.4, "Speed": 1.0},
    },
    "MI_SDF_RoseWindow": {
        "parent": "/Game/_PROJECT/04_Materials/baroque/M_SDF_RoseWindow",
        "params": {"RingFreq": 6.0, "Scale": 1.0, "GlowAmount": 0.5, "WorldUVScale": 1.0},
    },
    "MI_SDF_StarburstGem": {
        "parent": "/Game/_PROJECT/04_Materials/SDF/M_SDF_StarburstGem",
        "params": {"UVScale": 1.0},
    },
    "MI_SDF_CrystallineSpire": {
        "parent": "/Game/_PROJECT/04_Materials/SDF/M_SDF_CrystallineSpire",
        "params": {"FacetSharpness": 32.0, "SpireCount": 5.0},
    },
    "MI_SDF_GothicRose": {
        "parent": "/Game/_PROJECT/04_Materials/SDF/M_SDF_GothicRoseWindow",
        "params": {"PetalCount": 8.0, "TraceryWidth": 0.4, "GlowIntensity": 0.6},
    },
}


def _log(message):
    unreal.log(f"[SDFArch] {message}")


def _master_scalar_params(master):
    """Names of scalar parameters exposed by the master (best-effort reflection)."""
    names = set()
    try:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(master) or []:
            if type(e).__name__ in ("MaterialExpressionScalarParameter",
                                    "MaterialExpressionCollectionParameter"):
                n = e.get_editor_property("parameter_name")
                if n:
                    names.add(str(n))
    except Exception as exc:
        _log(f"reflection failed on {master.get_name()}: {exc}")
    return names


def main():
    results = []
    unreal.EditorAssetLibrary.make_directory(OUT_DIR.replace("/Game/", "", 1))
    for name, spec in INSTANCES.items():
        parent = unreal.EditorAssetLibrary.load_asset(spec["parent"])
        if parent is None:
            _log(f"master missing, skipped: {spec['parent']}")
            results.append({"instance": name, "status": "skipped_parent_missing",
                            "parent": spec["parent"]})
            continue
        existing = unreal.EditorAssetLibrary.load_asset(f"{OUT_DIR}/{name}")
        mid = existing
        if mid is None:
            tools = unreal.AssetToolsHelpers.get_asset_tools()
            mid = tools.create_asset(name, OUT_DIR, unreal.MaterialInstanceConstant, None)
            if mid is None:
                results.append({"instance": name, "status": "create_failed"})
                continue
        mid.set_editor_property("parent", parent)
        available = _master_scalar_params(parent)
        applied, skipped = [], []
        for pname, value in spec["params"].items():
            if pname not in available:
                skipped.append(pname)
                continue
            try:
                # NOTE (this build's slim API): set_material_instance_scalar_
                # parameter_value returns False even on success — verify via
                # read-back instead of trusting the boolean (proven 2026-08-29:
                # SET returned False while GET read back the written value).
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mid, pname, float(value))
                got = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mid, pname)
                if got is not None and abs(float(got) - float(value)) < 1e-4:
                    applied.append(pname)
                else:
                    skipped.append(pname)
            except Exception as exc:
                _log(f"{name}: set {pname} failed: {exc}")
                skipped.append(pname)
        unreal.EditorAssetLibrary.save_loaded_asset(mid, only_if_is_dirty=False)
        results.append({
            "instance": f"{OUT_DIR}/{name}", "parent": spec["parent"],
            "status": "ok", "params_applied": applied, "params_skipped": skipped,
        })
        _log(f"{name}: applied={applied} skipped={skipped}")

    payload = {"generated": "2026-08-29", "out_dir": OUT_DIR, "instances": results, "ok": True}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _log(f"audit -> {OUT}")
    return payload


if __name__ == "__main__":
    main()