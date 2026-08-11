"""Scaffold Melodia WBP_* widgets from the Melusina atom map.

Maps Figma Game/* atoms → /Game/Melodia/UI/WBP_* per Docs/MELODIA_MELUSINA_GAME_UX.md.

Offline (no Unreal):
  python Content/Python/scaffold_melodia_wbp_atoms.py
  → Saved/Audit/melodia_wbp_atom_scaffold.json

In-editor (when Unreal idle):
  py Content/Python/scaffold_melodia_wbp_atoms.py --create
  # Prefer parent class for mobile:
  py Content/Python/scaffold_melodia_wbp_atoms.py --create --mobile-first
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "melodia_wbp_atom_scaffold.json"
UI_PATH = "/Game/Melodia/UI"
MOBILE_PARENT = "/Script/MelodiaCore.MelodiaMobileHUD"
RHYTHM_PARENT = "/Script/MelodiaCore.MelodiaRhythmHUDWidget"

# Screen + atom widgets from MELODIA_MELUSINA_GAME_UX.md
WBP_ATOMS: list[tuple[str, str]] = [
    ("WBP_MainMenu", "Game/MainMenu"),
    ("WBP_SaveLoad", "Game/SaveLoad"),
    ("WBP_Settings", "Game/Settings"),
    ("WBP_ComicOrrery", "Game/ComicOrrery"),
    ("WBP_QuestJournal", "Game/QuestJournal"),
    ("WBP_NPCInfo", "Game/NPCInfo"),
    ("WBP_Inventory", "Game/Inventory"),
    ("WBP_Title", "Game/Title"),
    ("WBP_PartyLoadout", "Game/PartyLoadout"),
    ("WBP_FieldHUD", "Game/FieldHUD"),
    ("WBP_Battle_Command", "Game/BattleCommand"),
    ("WBP_Battle_Rhythm", "Game/BattleRhythm"),
    ("WBP_Battle_Enemy", "Game/BattleEnemy"),
    ("WBP_Battle_Results", "Game/BattleResults"),
    ("WBP_SkillCodex", "Game/SkillCodex"),
    ("WBP_Battle_Mobile", "Game/BattleMobile"),
    ("WBP_GradePop", "Game/GradePop"),
    ("WBP_SheetMusicRoll", "Game/SheetMusicRoll"),
    ("WBP_NoteGlyph", "Game/NoteGlyph"),
    ("WBP_MeasureMarker", "Game/MeasureMarker"),
    ("WBP_PlaybackHead", "Game/PlaybackHead"),
    ("WBP_ElementWheel", "Game/ElementWheel"),
    ("WBP_SPBar", "Game/SPMeter"),
    ("WBP_ULTCharge", "Game/ULTMeter"),
    ("WBP_DialogueBubble", "Game/DialogueOverlay"),
    # Row F — First-Slice Essentials (desktop) — 20-min vertical slice
    ("WBP_MenuButton", "Ctrl/MenuButton"),
    ("WBP_BlessingBurden", "Game/BlessingBurden"),
    ("WBP_IntensityWarning", "Game/IntensityWarning"),
    ("WBP_DissonanceBanner", "Game/DissonanceBanner"),
    ("WBP_ResonanceBond", "Game/ResonanceBond"),
]

PARENT_OVERRIDES: dict[str, str] = {
    "WBP_Battle_Mobile": MOBILE_PARENT,
    "WBP_Battle_Rhythm": RHYTHM_PARENT,
}

# BindWidgetOptional names on UMelodiaMobileHUD — author these in the WBP.
MOBILE_BIND_WIDGETS = [
    "HighwayCanvas",
    "ComboText",
    "HPBar",
    "SPBar",
    "UltBar",
    "EnemyNameText",
    "EnemyHPBar",
    "EnemyToughnessBar",
    "GradePopupCanvas",
    "GradeText",
]

MOBILE_AUTHORING = {
    "orientation": "portrait",
    "frames": ["390x844", "430x932"],
    "parent_class": MOBILE_PARENT,
    "zones": {
        "top_bar": "combo + enemy toughness — T_Melodia_MobileTopBar",
        "highway": "vertical lanes A–D — T_Melodia_HighwayBG + LanePress",
        "skills": "4 chips ≥48pt — T_Melodia_SkillChipBG",
        "safe_area": "dev overlay T_Melodia_SafeAreaMask",
    },
    "bind_widgets": MOBILE_BIND_WIDGETS,
    "lane_buttons": "Assign LaneButtons[0..3] (EditAnywhere array) → ForwardLaneTap",
    "input": "LaneButtons[i] → MelodiaMobileHUD::ForwardLaneTap → HandleLaneTap",
    "brushes": [
        "T_Melodia_LanePress",
        "T_Melodia_SkillChipBG",
        "T_Melodia_MobileTopBar",
        "T_Melodia_HighwayBG",
        "T_Melodia_GradePerfect",
        "T_Melodia_GradeGreat",
        "T_Melodia_GradeGood",
        "T_Melodia_GradeMiss",
    ],
    "figma": "https://www.figma.com/design/Yx8ud7n39NdWZvnNvo4Xlf/Untitled?node-id=10-73",
    "web_ssot": "my-site-clean/wix/melodia-melusina.html?mode=ios#ios-battle",
}


def _disk_presence() -> dict[str, bool]:
    ui_dir = PROJECT_ROOT / "Content" / "Melodia" / "UI"
    return {name: (ui_dir / f"{name}.uasset").is_file() for name, _ in WBP_ATOMS}


def write_plan(created: list[dict] | None = None, editor: bool = False) -> dict:
    on_disk = _disk_presence()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "batch": "PassB-C",
        "editor_available": editor,
        "ui_path": UI_PATH,
        "atoms": [
            {
                "wbp": n,
                "figma": f,
                "path": f"{UI_PATH}/{n}",
                "parent": PARENT_OVERRIDES.get(n, "/Script/UMG.UserWidget"),
                "on_disk": on_disk.get(n, False),
            }
            for n, f in WBP_ATOMS
        ],
        "created": created or [],
        "on_disk_summary": {
            "present": [n for n, ok in on_disk.items() if ok],
            "missing": [n for n, ok in on_disk.items() if not ok],
        },
        "notes": [
            "MelodiaCore is the only battle authority — do not parent to JRPG template controllers.",
            "Keep smoke pawn until BP_Melusina compiles.",
            "Web SSOT: my-site-clean/wix/melodia-melusina.html phase panels.",
            "iOS SSOT: Docs/MELODIA_IOS_MOBILE_GAME_UI.md — portrait primary, vertical 4-lane.",
            "Figma AAA board: page 12 · AAA / Systems Board · Pass B",
            "WBP_Battle_Mobile: parent MelodiaMobileHUD; 4 LaneButtons; thumb zone bottom 35–45%.",
            "Mobile brushes: T_Melodia_LanePress, SkillChipBG, MobileTopBar, HighwayBG, Grade*.",
            "Rhythm windows: Plugins/MelodiaCore/Rules/melodia_rules.json",
        ],
        "wbp_battle_mobile": MOBILE_AUTHORING,
        "next_steps": [
            "Open Unreal with MelodiaCore enabled",
            "py Content/Python/scaffold_melodia_wbp_atoms.py --create --mobile-first",
            "Open WBP_Battle_Mobile → confirm parent MelodiaMobileHUD",
            "Author portrait layout; name BindWidgets; assign LaneButtons[0..3]",
            "Brush Batch N atlas from /Game/EnvSandbox/Textures/Melodia/GameUI",
            "Wire WBP_Battle_* to MelodiaBattleSession phase events",
            "Smoke CoreRules / Zen when editor free",
        ],
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _resolve_parent_class(unreal, class_path: str):
    cls = unreal.load_class(None, class_path)
    if cls:
        return cls
    # Fallback soft path forms
    soft = class_path.replace("/Script/", "")
    return unreal.load_class(None, soft)


def _reparent_widget_bp(unreal, asset, parent_class) -> bool:
    """Best-effort reparent; UE version APIs differ."""
    if not asset or not parent_class:
        return False
    try:
        if hasattr(unreal, "BlueprintEditorLibrary"):
            unreal.BlueprintEditorLibrary.reparent_blueprint(asset, parent_class)
            return True
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[WBPAtoms] BlueprintEditorLibrary.reparent failed: {exc}")
    try:
        # Older / alternate path
        asset.set_editor_property("parent_class", parent_class)
        return True
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[WBPAtoms] parent_class set failed: {exc}")
    return False


def create_in_editor(mobile_first: bool = False) -> list[dict]:
    import unreal

    created: list[dict] = []
    if not unreal.EditorAssetLibrary.does_directory_exist(UI_PATH):
        unreal.EditorAssetLibrary.make_directory(UI_PATH)

    atoms = list(WBP_ATOMS)
    if mobile_first:
        atoms.sort(key=lambda pair: 0 if pair[0] == "WBP_Battle_Mobile" else 1)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for name, figma in atoms:
        full = f"{UI_PATH}/{name}"
        parent_path = PARENT_OVERRIDES.get(name)
        if unreal.EditorAssetLibrary.does_asset_exist(f"{full}.{name}"):
            entry = {"name": name, "figma": figma, "status": "exists"}
            if parent_path and name == "WBP_Battle_Mobile":
                bp = unreal.EditorAssetLibrary.load_asset(full)
                parent = _resolve_parent_class(unreal, parent_path)
                if bp and parent and _reparent_widget_bp(unreal, bp, parent):
                    unreal.EditorAssetLibrary.save_asset(full)
                    entry["parent"] = parent_path
                    entry["reparent"] = "applied"
            created.append(entry)
            continue

        factory = unreal.WidgetBlueprintFactory()
        if parent_path:
            parent = _resolve_parent_class(unreal, parent_path)
            if parent and hasattr(factory, "set_editor_property"):
                try:
                    factory.set_editor_property("parent_class", parent)
                except Exception:  # noqa: BLE001
                    pass

        asset = asset_tools.create_asset(name, UI_PATH, unreal.WidgetBlueprint, factory)
        if asset:
            if parent_path:
                parent = _resolve_parent_class(unreal, parent_path)
                _reparent_widget_bp(unreal, asset, parent)
            unreal.EditorAssetLibrary.save_asset(full)
            unreal.log(f"[WBPAtoms] Created {full} ← {figma}")
            created.append({
                "name": name,
                "figma": figma,
                "status": "created",
                "parent": parent_path or "/Script/UMG.UserWidget",
            })
        else:
            created.append({"name": name, "figma": figma, "status": "failed"})
    return created


def main() -> int:
    do_create = "--create" in sys.argv
    mobile_first = "--mobile-first" in sys.argv
    try:
        import unreal  # noqa: F401

        editor = True
    except ImportError:
        editor = False

    created: list[dict] = []
    if do_create and editor:
        created = create_in_editor(mobile_first=mobile_first)
    elif do_create and not editor:
        print("[WBPAtoms] --create requires Unreal Editor Python. Wrote plan only.")

    report = write_plan(created=created, editor=editor)
    print(f"[WBPAtoms] Report -> {AUDIT}")
    print(
        f"[WBPAtoms] atoms={len(WBP_ATOMS)} editor={editor} "
        f"created={len(created)} missing={len(report['on_disk_summary']['missing'])}"
    )
    if "WBP_Battle_Mobile" in report["on_disk_summary"]["missing"]:
        print("[WBPAtoms] P0 missing: WBP_Battle_Mobile — run --create --mobile-first in editor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
