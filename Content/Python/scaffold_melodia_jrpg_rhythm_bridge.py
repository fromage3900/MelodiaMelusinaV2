"""Scaffold Melodia ↔ TurnBasedJRPGTemplate rhythm battle bridge.

Creates bridge folders, verifies template assets, scaffolds Melodia BPs,
exports registry JSON, writes audit report.

Run in Unreal Editor:
  py Content/Python/scaffold_melodia_jrpg_rhythm_bridge.py
  py Content/Python/scaffold_melodia_jrpg_rhythm_bridge.py --verify-only
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "melodia_jrpg_rhythm_scaffold.json"
REGISTRY_JSON = PROJECT_ROOT / "Content" / "Data" / "Melodia" / "melodia_registry_seed.json"

from jrpg_template_catalog import (
    BATTLE_ASSETS,
    BRIDGE_SCAFFOLD,
    MELODIA_CPP_BRIDGE,
    STRUCT_ASSETS,
    TPL_BATTLE,
)
from paths import JRPG_TEMPLATE, MELODIA


def _ensure_dir(path: str) -> bool:
    import unreal
    if unreal.EditorAssetLibrary.does_directory_exist(path):
        return False
    unreal.EditorAssetLibrary.make_directory(path)
    return True


def _create_bp(path: str, name: str, parent_class) -> str | None:
    import unreal
    full = f"{path}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(f"{full}.{name}"):
        return full
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(name, path, unreal.Blueprint, factory)
    if asset:
        unreal.EditorAssetLibrary.save_asset(full)
        unreal.log(f"[JRPGBridge] Created BP {full}")
        return full
    return None


def verify_template_assets() -> list[dict]:
    import unreal
    checks = []
    for asset in list(BATTLE_ASSETS) + list(STRUCT_ASSETS):
        game_path = f"{asset.ue_path}.{asset.name}"
        ok = unreal.EditorAssetLibrary.does_asset_exist(game_path)
        checks.append({"name": asset.name, "path": asset.ue_path, "exists": ok})
    return checks


def verify_melodia_cpp() -> list[dict]:
    import unreal
    checks = []
    for asset in MELODIA_CPP_BRIDGE:
        cls = unreal.load_class(None, asset.ue_path)
        checks.append({"name": asset.name, "path": asset.ue_path, "exists": cls is not None})
    return checks


def scaffold_bridge_blueprints() -> list[dict]:
    import unreal
    created = []

    dirs = [
        f"{MELODIA}/Bridge/JRPG",
        f"{MELODIA}/Bridge/JRPG/RhythmBattle",
        f"{MELODIA}/Blueprints/Battle",
        f"{MELODIA}/Core",
        "/Game/Data/Melodia",
        f"{MELODIA}/UI",
        f"{MELODIA}/Levels",
    ]
    for d in dirs:
        _ensure_dir(d)

    # Bridge actor — hooks template battle controller events
    bridge = _create_bp(f"{MELODIA}/Bridge/JRPG", "BP_Melodia_JRPG_Bridge", unreal.Actor)
    if bridge:
        created.append(bridge)

    # Rhythm battle arena stub
    battle_parent = unreal.load_class(None, f"{TPL_BATTLE}/BP_BattleBase.BP_BattleBase_C")
    if battle_parent:
        rb = _create_bp(f"{MELODIA}/Blueprints/Battle", "BP_Melodia_RhythmBattle", battle_parent)
        if rb:
            created.append(rb)

    # Game mode subclass
    gm_class = unreal.load_class(None, "/Script/MelodiaCore.MelodiaGameMode")
    if gm_class:
        gm = _create_bp(f"{MELODIA}/Blueprints/Battle", "BP_Melodia_GameMode", gm_class)
        if gm:
            created.append(gm)

    # Rhythm HUD widget
    hud_class = unreal.load_class(None, "/Script/MelodiaCore.MelodiaRhythmHUDWidget")
    if hud_class:
        hud = _create_bp(f"{MELODIA}/UI", "WBP_Battle_Rhythm", hud_class)
        if hud:
            created.append(hud)
        pop = _create_bp(f"{MELODIA}/UI", "WBP_GradePop", unreal.UserWidget)
        if pop:
            created.append(pop)

    # Quest hook
    quest = _create_bp(f"{MELODIA}/Core", "BP_QuestManager", unreal.Actor)
    if quest:
        created.append(quest)

    return [{"path": p} for p in created]


def export_registry_seed() -> dict:
    from gmm.game.data_registry import MelodiaDataRegistry
    reg = MelodiaDataRegistry()
    REGISTRY_JSON.parent.mkdir(parents=True, exist_ok=True)
    text = reg.export_json(str(REGISTRY_JSON))
    return {"path": str(REGISTRY_JSON), "bytes": len(text)}


def main() -> int:
    import unreal

    verify_only = "--verify-only" in sys.argv
    unreal.log("=== Melodia JRPG Rhythm Bridge Scaffold ===")

    template_checks = verify_template_assets()
    cpp_checks = verify_melodia_cpp()
    template_ok = all(c["exists"] for c in template_checks)
    cpp_ok = all(c["exists"] for c in cpp_checks)

    created = []
    registry = {}
    if not verify_only:
        created = scaffold_bridge_blueprints()
        registry = export_registry_seed()
        try:
            import scaffold_rhythm_assets as rhythm
            rhythm.main()
        except Exception as exc:
            unreal.log_warning(f"[JRPGBridge] rhythm scaffold skipped: {exc}")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jrpg_template_root": JRPG_TEMPLATE,
        "template_assets_ok": template_ok,
        "melodia_cpp_ok": cpp_ok,
        "template_checks": template_checks,
        "cpp_checks": cpp_checks,
        "bridge_created": created,
        "registry_seed": registry,
        "bridge_scaffold_plan": [{"name": n, "path": p} for n, p, _ in BRIDGE_SCAFFOLD],
        "next_steps": [
            "Parent BP_Melodia_JRPG_Bridge to BP_BattleController (manual — template BP class)",
            "Wire BP_Melodia_GameMode as default for L_Melodia_RhythmSlice",
            "On Skill command: MelodiaBattleSession -> RhythmExecution -> WBP_Battle_Rhythm",
            "Map S_UnitStats rows to DT_MelodiaEnemies",
            "Run gmm/game/battle_manager.py smoke in standalone Python",
        ],
    }

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[JRPGBridge] Report -> {AUDIT}")
    unreal.log(f"[JRPGBridge] template_ok={template_ok} cpp_ok={cpp_ok} created={len(created)}")
    return 0 if template_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
