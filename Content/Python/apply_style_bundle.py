"""Biome/style orchestrator (Phase N): one entry point that applies a style's
material + PCG scatter preset + Niagara VFX subset onto a target actor in one action.

Each style bundle is self-contained (its own material/PCG-graph/Niagara references) --
no cross-style wiring. Adding a 5th style later just means adding one new dict entry.

Editor (validate only, no level touched):
  py Content/Python/apply_style_bundle.py

Editor (apply to a placed actor):
  import apply_style_bundle as asb
  asb.apply_style_bundle("Sakura", target_actor=some_actor)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "style_bundle_validation.json"

# Each bundle's PCG graph and material are real, verified-existing assets as of
# 2026-06-28. Niagara lists are intentionally short/empty where no bespoke VFX
# exists yet for that style -- this orchestrator wires what's real, it doesn't
# fabricate placeholders.
STYLE_BUNDLES = {
    "Sakura": {
        "pcg_graph": "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Sakura_Showcase",
        "material": "/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Petals",
        "niagara_systems": [
            "/Game/EnvSandbox/VFX/Systems/Sakura/NS_WindRibbonGust",
            "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle",
        ],
    },
    "Baroque": {
        "pcg_graph": "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_M1_GrammarNave_BS",
        "material": "/Game/EnvSandbox/Materials/Instances/Environment/Baroque/MI_Baroque_GildedFiligree",
        "niagara_systems": [],
    },
    "Escher": {
        "pcg_graph": "/Game/EnvSandbox/PCG/Styles/Escher/PCG_DreamWalls",
        "material": "/Game/EnvSandbox/Materials/Instances/Environment/Escher/MI_Escher_ImpossibleTile",
        "niagara_systems": [],
    },
    "Zen": {
        "pcg_graph": "/Game/EnvSandbox/PCG/Styles/Zen/PCG_Zen_Garden",
        "material": "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_MossGarden",
        "niagara_systems": [
            "/Game/EnvSandbox/VFX/Systems/Ambient/NS_ConstellationTwinkle",
        ],
    },
    "Grotto": {
        "pcg_graph": "/Game/EnvSandbox/PCG/Styles/Grotto/PCG_Grotto_Scatter",
        "material": "/Game/EnvSandbox/Materials/SDF/M_SDF_Bioluminescence",
        "niagara_systems": [],
    },
}


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def validate_bundle(style_name: str) -> dict:
    """Confirm every asset reference in a bundle actually loads. No level touched."""
    import unreal

    bundle = STYLE_BUNDLES[style_name]
    result = {"style": style_name, "ok": True, "checks": []}

    for key in ("pcg_graph", "material"):
        asset_path = bundle[key]
        loaded = unreal.EditorAssetLibrary.load_asset(asset_path)
        ok = loaded is not None
        result["checks"].append({"field": key, "path": asset_path, "loaded": ok})
        result["ok"] = result["ok"] and ok

    for ns_path in bundle["niagara_systems"]:
        loaded = unreal.EditorAssetLibrary.load_asset(ns_path)
        ok = loaded is not None
        result["checks"].append({"field": "niagara_systems", "path": ns_path, "loaded": ok})
        result["ok"] = result["ok"] and ok

    return result


def apply_style_bundle(style_name: str, target_actor=None) -> dict:
    """Apply one style's material + PCG graph + Niagara subset onto target_actor
    in a single action. If target_actor is None, only validates the bundle
    (asset existence) and returns a report -- no level/actor is touched.
    """
    import unreal

    if style_name not in STYLE_BUNDLES:
        raise ValueError(f"Unknown style '{style_name}'. Known: {list(STYLE_BUNDLES)}")

    if target_actor is None:
        return validate_bundle(style_name)

    bundle = STYLE_BUNDLES[style_name]
    applied = {"style": style_name, "actor": target_actor.get_name(), "steps": []}

    pcg_graph = unreal.EditorAssetLibrary.load_asset(bundle["pcg_graph"])
    pcg_comp = target_actor.get_component_by_class(unreal.PCGComponent)
    if pcg_comp is not None and pcg_graph is not None:
        pcg_comp.set_editor_property("graph", pcg_graph)
        pcg_comp.generate(True)
        applied["steps"].append({"set_pcg_graph": bundle["pcg_graph"]})

    material = unreal.EditorAssetLibrary.load_asset(bundle["material"])
    mesh_comp = target_actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp is not None and material is not None:
        num_slots = mesh_comp.get_num_materials()
        for slot in range(num_slots):
            mesh_comp.set_material(slot, material)
        applied["steps"].append({"set_material": bundle["material"], "slots": num_slots})

    spawned = []
    for ns_path in bundle["niagara_systems"]:
        ns_asset = unreal.EditorAssetLibrary.load_asset(ns_path)
        if ns_asset is None:
            continue
        niagara_comp = unreal.NiagaraFunctionLibrary.spawn_system_attached(
            ns_asset,
            target_actor.root_component,
            "",
            unreal.Vector(0, 0, 0),
            unreal.Rotator(0, 0, 0),
            unreal.AttachLocation.KEEP_RELATIVE_OFFSET,
            True,
        )
        spawned.append(ns_path)
    if spawned:
        applied["steps"].append({"spawned_niagara": spawned})

    return applied


def main() -> int:
    if not _in_ue():
        print("This script must be run inside the Unreal Editor (py Content/Python/apply_style_bundle.py).")
        return 1

    results = [validate_bundle(name) for name in STYLE_BUNDLES]
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    all_ok = all(r["ok"] for r in results)
    for r in results:
        status = "OK" if r["ok"] else "MISSING ASSETS"
        print(f"[{r['style']}] {status}")
        for c in r["checks"]:
            if not c["loaded"]:
                print(f"    MISSING: {c['field']} -> {c['path']}")

    print(f"STYLE_BUNDLE_VALIDATION_{'OK' if all_ok else 'FAILED'} -> {REPORT}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
