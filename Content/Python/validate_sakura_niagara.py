"""PIE-ready validation checklist for Sakura Dream Niagara kit."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sakura_niagara_validation.json"

SYSTEMS_SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"
VFX_MAT_DIR = "/Game/EnvSandbox/VFX/Materials"
MPC_PATH = "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream.MPC_SakuraDream"
LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"

EXPECTED_ACTORS = (
    "VFX_SakuraCanopy",
    "VFX_SakuraSparkle",
    "VFX_SakuraGround",
    "VFX_LanternMotes",
    "VFX_PondShimmer",
    "VFX_PetalGust",
)

EXPECTED_SYSTEMS = (
    "NS_SakuraPetals",
    "NS_SakuraPetals_v2",
    "NS_SakuraGroundPetals",
    "NS_SakuraDreamSparkle",
    "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer",
    "NS_SakuraPetalGust",
)

SPRITE_MIS = (
    "MI_Niagara_Petal",
    "MI_Niagara_Sparkle",
    "MI_Niagara_Mote",
    "MI_Niagara_Pond",
    "MI_Niagara_Gust",
)

PETAL_SYSTEMS = ("NS_SakuraPetals_v2", "NS_SakuraGroundPetals", "NS_SakuraPetalGust")


def _is_null_rhi() -> bool:
    for arg in sys.argv:
        if "nullrhi" in arg.lower():
            return True
    try:
        import unreal

        rhi = str(unreal.SystemLibrary.get_console_variable_string("r.RHI.Name") or "").lower()
        return rhi == "null" or "null" in rhi
    except Exception:
        return False


def run_validation() -> dict:
    import unreal

    import setup_sakura_niagara as setup

    checks: list[dict] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": label, "ok": ok, "detail": detail})
        flag = "PASS" if ok else "FAIL"
        unreal.log(f"[SakuraValidate] {flag}: {label} {detail}")

    for name in EXPECTED_SYSTEMS:
        path = f"{SYSTEMS_SAKURA}/{name}.{name}"
        check(f"system {name}", unreal.EditorAssetLibrary.does_asset_exist(path), path)

    canopy = setup.canonical_canopy_system()
    check("canonical canopy resolves to v2", canopy == setup.CANOPY_SYSTEM_V2, canopy)

    check("MPC_SakuraDream", unreal.EditorAssetLibrary.does_asset_exist(MPC_PATH), MPC_PATH)
    check(
        "M_Niagara_SakuraSprite",
        unreal.EditorAssetLibrary.does_asset_exist(
            f"{VFX_MAT_DIR}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite"
        ),
    )
    mpc_bindings = setup._probe_mpc_material_bindings()
    for param in ("WindStrength", "SparklePulse", "PetalDensity"):
        check(f"MPC material {param}", mpc_bindings.get(param, False), "M_Niagara_SakuraSprite")

    for mi in SPRITE_MIS:
        p = f"{VFX_MAT_DIR}/{mi}.{mi}"
        check(f"sprite {mi}", unreal.EditorAssetLibrary.does_asset_exist(p), p)

    for name in PETAL_SYSTEMS:
        path = f"{SYSTEMS_SAKURA}/{name}.{name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        system = unreal.load_asset(path)
        if system:
            spec = next((s for s in setup.SAKURA_SYSTEMS if s.name == name), None)
            if spec:
                mat_path = f"{VFX_MAT_DIR}/{spec.sprite_material}.{spec.sprite_material}"
                assigned = setup._assign_sprite_material(system, mat_path)
                check(f"petal material {name}", assigned, spec.sprite_material)

    level_ok = unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.L_SakuraPath")
    check("level L_SakuraPath", level_ok)

    actors_found: list[str] = []
    gust_inactive = False
    if level_ok:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        les.load_level(LEVEL)
        labels = {a.get_actor_label() for a in eas.get_all_level_actors()}
        for label in EXPECTED_ACTORS:
            present = label in labels
            check(f"actor {label}", present)
            if present:
                actors_found.append(label)

        for actor in eas.get_all_level_actors():
            if actor.get_actor_label() != "VFX_PetalGust":
                continue
            comp = actor.get_component_by_class(unreal.NiagaraComponent)
            if comp:
                gust_inactive = not bool(comp.get_auto_activate())
            break
        check("gust actor auto_activate=False", gust_inactive)

        canopy_spawn = next(s for s in setup._resolve_level_spawns(eas) if s["label"] == "VFX_SakuraCanopy")
        check(
            "canopy spawn uses v2",
            canopy_spawn["system"] == setup.CANOPY_SYSTEM_V2,
            canopy_spawn["system"],
        )

    particle_gate = "skipped (nullrhi)" if _is_null_rhi() else "PIE manual — see audit particle_count_gate"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "total": len(checks),
        "all_ok": all(c["ok"] for c in checks),
        "actors_found": actors_found,
        "canonical_canopy": canopy,
        "mpc_material_bindings": mpc_bindings,
        "particle_count_gate": particle_gate,
        "hand_tune_notes": setup.SAKURA_TUNING_NOTES,
        "pie_notes": [
            "No Niagara compile errors in Output Log",
            "Petals read pink/cream at dusk exposure (bias 11)",
            "Bloom picks up sparkle emissive without clipping",
            "Ground petals visible on path; canopy frames torii",
            "Canopy v2: 400-1200 visible; ground: 30-80 visible",
            "Lantern motes visible in detail shot",
            "Gust reads as storybook wind (trigger VFX_PetalGust or MPC GustTrigger)",
        ],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SakuraValidate] report -> {REPORT_PATH}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        print("Run inside Unreal Editor")
        return 1
    report = run_validation()
    return 0 if report.get("all_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
