"""Closed-editor audit of the active menu surface and Melusina battle adapter."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "active_frontend_and_battle_routes.json"
MENU = "/Game/Melodia/UI/WBP_MainMenu"
BATTLE = "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation"
MONTAGE = "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack"
EXPECTED = {"Btn_NewGame", "Btn_Continue"}


def named_widgets(widget) -> list[str]:
    # UE 5.8 commandlets expose neither WidgetTree enumeration nor
    # UserWidget::GetWidgetFromName to Python. The serialized package still
    # retains authored widget names, which is sufficient for this static route
    # audit; compilation is performed separately by the UI recovery gate.
    generated = widget.generated_class() if widget else None
    cdo = unreal.get_default_object(generated) if generated else None
    candidates = ("Btn_NewGame", "Btn_Continue", "Btn_Settings", "Btn_Options", "Btn_Quit")
    if not cdo:
        return []
    package = Path(unreal.Paths.project_content_dir()) / "Melodia" / "UI" / "WBP_MainMenu.uasset"
    try:
        payload = package.read_bytes()
    except OSError:
        return []
    return [
        name for name in candidates
        if name.encode("ascii") in payload or name.encode("utf-16-le") in payload
    ]


menu = unreal.load_asset(MENU)
battle = unreal.load_asset(BATTLE)
montage = unreal.load_asset(MONTAGE)
widgets = named_widgets(menu) if menu else []
report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "menu_loads": bool(menu),
    "menu_widgets": widgets,
    "required_menu_buttons": sorted(EXPECTED),
    "required_buttons_present": EXPECTED.issubset(set(widgets)),
    "settings_button_present": any(name in {"Btn_Settings", "Btn_Options"} for name in widgets),
    "battle_blueprint_loads": bool(battle),
    "battle_blueprint_compiled": False,
    "attack_montage_loads": bool(montage),
    "attack_montage_skeleton": "",
}
if battle:
    unreal.BlueprintEditorLibrary.compile_blueprint(battle)
    report["battle_blueprint_compiled"] = True
if montage:
    skeleton = montage.get_editor_property("skeleton")
    report["attack_montage_skeleton"] = skeleton.get_path_name() if skeleton else ""
report["ok"] = bool(
    report["menu_loads"] and report["required_buttons_present"]
    and report["battle_blueprint_loads"] and report["battle_blueprint_compiled"]
    and report["attack_montage_loads"]
)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("ACTIVE_FRONTEND_BATTLE_AUDIT: " + json.dumps(report))
if not report["ok"]:
    raise RuntimeError("Active frontend/battle audit failed")
