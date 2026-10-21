"""Melodia Studio — one editor pie over the tool registries that already exist.

View only. envui.commands (GMM included), world_compiler_panel, foundry_converged_panel,
and the Melodia *_panel modules stay the owners. This module does not compile, cook,
write MPCs, or load a level.

Colours resolve from melodia-design-system/tokens.json (Figma variable export).
The docked tab uses the existing parchment and filigree textures when they are loaded.

Offline:
  python Content/Python/melodia_studio_panel.py
Editor:
  import melodia_studio_panel as studio; studio.open_studio()
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

PYTHON_DIR = Path(__file__).resolve().parent
ROOT = PYTHON_DIR.parents[1]
TOKENS_PATH = ROOT / "melodia-design-system" / "tokens.json"

EUW_PATH = "/Game/Melodia/Tools/EUW_MelodiaStudio"
EUW_DIR = "/Game/Melodia/Tools"

PARCHMENT = "/Game/Melodia/UI/Textures/T_Melodia_Parchment_Field"
FILIGREE_CORNER = "/Game/Melodia/UI/Textures/T_Melodia_FiligreeCorner_Ornate"
FILIGREE_DIVIDER = "/Game/Melodia/UI/Textures/T_Melodia_FiligreeDivider_Wave"
FONT_UI = "/Game/Melodia/UI/Fonts/F_Melodia_UI"
FONT_SERIF = "/Game/Melodia/UI/Fonts/F_InstrumentSerif"

SECTION_ORDER = (
    "Connection",
    "World",
    "PIE",
    "Wardrobe",
    "Sir",
    "Dressing",
    "Look",
    "Flora",
    "PCG",
    "Niagara",
    "Capture",
    "Materials",
    "Modifiers",
    "MRQ",
    "Portfolio",
    "Material Loops",
    "Grandmaster",
    "Help",
)

GMM_FIRST = ("gmm.about", "gmm.mcp_status")

READ_ONLY_IDS = frozenset({
    "world.status",
    "foundry.status",
    "foundry.validate",
    "foundry.plan",
    "pie.status",
    "wardrobe.equipped",
    "sir.list",
    "dress.platforms",
    "look.inspect",
    "flora.readout",
    "help.livelink",
    "livelink.status",
    "pcg.audit",
    "materials.run_audits",
    "materials.print_paths",
    "gmm.about",
    "gmm.mcp_status",
    "gmm.mcp_discover",
    "gmm.settings.get",
    "gmm.modifiers.summary",
    "gmm.geometry.capabilities",
    "gmm.geometry.describe_actor",
    "gmm.geometry.describe_target",
    "gmm.melodia.enemies",
    "gmm.melodia.skills",
    "gmm.melusina.rig_assess",
    "gmm.pcg.preflight",
    "gmm.pcg.manifest",
    "gmm.pcg.release_gate",
    "gmm.mkc.verify_all",
    "gmm.battle.state",
    "gmm.game.config",
    "gmm.game.player_status",
    "gmm.agent.status",
    "gmm.npc.vrm4u_capabilities",
    "gmm.npc.audit",
    "gmm.npc.status",
    "gmm.roguelike.room_templates",
    "gmm.roguelike.artifacts",
    "gmm.roguelike.blessings",
})

READ_ONLY_TAILS = frozenset({
    "status", "about", "summary", "list", "inspect", "validate", "plan",
    "audit", "preflight", "capabilities", "manifest", "config",
})

PALETTE_MPC = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
DRIVER_MPC = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"
ASK_FIRST_LEVELS = ("L_MelusinaMorning", "L_SakuraPath")
PLATE_GRID = 9
_PLATE: dict[str, Any] = {"widget": None, "cells": [], "label": None, "handle": None}


def modes_from_bands(bass: float, beat: float) -> tuple[int, int]:
    """Same clamp as UMelodiaCymaticsSubsystem::Tick and the cymatics writer."""
    mode_n = max(1, min(8, 2 + int(math.floor(float(bass) * 6.0))))
    mode_m = max(1, min(8, 3 + int(math.floor(float(beat) * 5.0))))
    return mode_n, mode_m


def chladni01(mode_n: int, mode_m: int, u: float, v: float) -> float:
    """MelodiaCymaticFieldComponent::Chladni01. Absolute standing wave in 0..1."""
    pi_u = math.pi * u
    pi_v = math.pi * v
    amp_a = math.cos(mode_n * pi_u) * math.cos(mode_m * pi_v)
    amp_b = math.cos(mode_m * pi_u) * math.cos(mode_n * pi_v)
    return abs(amp_a - amp_b) * 0.5


def sample_cymatic_amplitude(mode_n: int, mode_m: int, u: float, v: float, beat: float) -> float:
    """UMelodiaCymaticsSubsystem::SampleCymaticAmplitude. Signed, beat-scaled."""
    pi_u = math.pi * u
    pi_v = math.pi * v
    amp_a = math.cos(mode_n * pi_u) * math.cos(mode_m * pi_v)
    amp_b = math.cos(mode_m * pi_u) * math.cos(mode_n * pi_v)
    return (amp_a - amp_b) * max(float(beat), 0.15)


def bus_tension(bass: float, beat: float) -> float:
    """Third argument of UWorldFieldBus::PublishResonance."""
    return max(0.0, min(1.0, max(float(bass), float(beat))))


def pin_chladni() -> list[str]:
    """Offline pins. These numbers are the C++ formula evaluated at fixed cells."""
    problems: list[str] = []
    if modes_from_bands(0.0, 0.0) != (2, 3):
        problems.append("rest modes")
    if modes_from_bands(1.0, 1.0) != (8, 8):
        problems.append("full modes")
    if modes_from_bands(0.2, 0.0) != (3, 3):
        problems.append("bass 0.2 mode")
    # N=2,M=3,u=0,v=0.25 -> |cos(3*pi/4)|/2
    expected = math.sqrt(2) / 4.0
    got = chladni01(2, 3, 0.0, 0.25)
    if abs(got - expected) > 1e-6:
        problems.append(f"chladni01 corner {got} != {expected}")
    if chladni01(2, 3, 0.5, 0.5) > 1e-6:
        problems.append("center node should be silent")
    signed = sample_cymatic_amplitude(2, 3, 0.0, 0.25, 0.0)
    if abs(signed - (-math.sqrt(2) / 2.0 * 0.15)) > 1e-6:
        problems.append(f"signed sample {signed}")
    if abs(bus_tension(0.2, 0.7) - 0.7) > 1e-6:
        problems.append("tension")
    return problems


def plate_state(bass: float, beat: float) -> dict[str, Any]:
    mode_n, mode_m = modes_from_bands(bass, beat)
    return {
        "bass": float(bass),
        "beat": float(beat),
        "mode_n": mode_n,
        "mode_m": mode_m,
        "tension": bus_tension(bass, beat),
    }


HELP_TEXT = (
    "[Melodia Studio] Open this pie from the Level Editor menu Melodia Studio.\n"
    "Blender: N-panel > Start Live Link, then Connection > Start Live Link, "
    "then Blender > Send Full Scene. Imports land in /Game/LiveLink/.\n"
    "Compile stays CLI: python Tools/world_compiler.py and "
    "python Tools/world_compiler_ue_driver.py. This pie does not load a level."
)


@dataclass(frozen=True)
class StudioAction:
    id: str
    section: str
    label: str
    read_only: bool
    run: Callable[[], str]


def _resolve_color(doc: dict, value: str, seen: set[str] | None = None) -> str:
    if not isinstance(value, str) or not value.startswith("{"):
        return value
    seen = seen or set()
    if value in seen:
        return "#241B2E"
    seen.add(value)
    node: Any = doc
    for part in value.strip("{}").split("."):
        node = node[part]
    inner = node["value"] if isinstance(node, dict) else node
    return _resolve_color(doc, inner, seen)


def palette() -> dict[str, str]:
    """Semantic light colours from the Figma-backed token file."""
    doc = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    light = doc["semantic-light"]["color"]

    def pick(*path: str) -> str:
        node: Any = light
        for part in path:
            node = node[part]
        return _resolve_color(doc, node["value"])

    return {
        "surface": pick("surface", "base"),
        "raised": pick("surface", "raised"),
        "sunken": pick("surface", "sunken"),
        "inverse": pick("surface", "inverse"),
        "text": pick("text", "primary"),
        "text_soft": pick("text", "secondary"),
        "inverse_text": pick("text", "inverse"),
        "accent_text": pick("text", "accent"),
        "gold": pick("accent", "primary"),
        "lavender": pick("accent", "secondary"),
        "sakura": pick("accent", "tertiary"),
        "astral": pick("accent", "astral"),
        "iris": pick("accent", "iris"),
    }


def slice_colors() -> list[str]:
    tones = palette()
    return [
        tones["gold"],
        tones["lavender"],
        tones["sakura"],
        tones["astral"],
        tones["iris"],
        tones["raised"],
        tones["sunken"],
    ]


def _read_only(action_id: str) -> bool:
    if action_id in READ_ONLY_IDS:
        return True
    return action_id.rsplit(".", 1)[-1] in READ_ONLY_TAILS


def _forbidden(action_id: str, label: str) -> bool:
    blob = f"{action_id} {label}".lower()
    return "compile" in blob or "load_level" in blob or "load level" in blob


def _envui_run(command_id: str) -> str:
    from envui import commands

    result = commands.run(command_id)
    if result.get("ok"):
        return f"OK {command_id}: {result.get('message', '')}"
    return f"FAIL {command_id}: {result.get('error') or result.get('message')}"


def _local_actions() -> list[StudioAction]:
    def world_status() -> str:
        import world_compiler_panel as wcp
        return str(wcp.status())

    def world_cleanup() -> str:
        import world_compiler_panel as wcp
        return str(wcp.cleanup())

    def world_apply() -> str:
        import world_compiler_panel as wcp
        return str(wcp.apply_field())

    def world_capture() -> str:
        import world_compiler_panel as wcp
        return str(wcp.capture())

    def foundry_status() -> str:
        import foundry_converged_panel as fcp
        return fcp.menu_status_summary()

    def foundry_validate() -> str:
        import foundry_converged_panel as fcp
        return fcp.menu_foundry_validate_summary()

    def foundry_plan() -> str:
        import foundry_converged_panel as fcp
        return fcp.menu_foundry_plan_summary()

    def pie_status() -> str:
        import melodia_pie_panel as ptp
        return ptp.menu_status_summary()

    def pie_play() -> str:
        import melodia_pie_panel as ptp
        return str(ptp.pie_play())

    def pie_stop() -> str:
        import melodia_pie_panel as ptp
        return str(ptp.pie_stop())

    def wardrobe() -> str:
        import wardrobe_live_panel as wlp
        return wlp.menu_equipped_summary()

    def sir_list() -> str:
        import sir_perch_panel as spp
        return spp.menu_list_summary()

    def sir_spawn() -> str:
        import sir_perch_panel as spp
        return str(spp.spawn_missing())

    def sir_snap() -> str:
        import sir_perch_panel as spp
        return str(spp.snap_selected())

    def sir_save() -> str:
        import sir_perch_panel as spp
        return str(spp.save_level())

    def platforms() -> str:
        import platform_speed_panel as psp
        return psp.menu_list_summary()

    def slower() -> str:
        import platform_speed_panel as psp
        return psp.menu_nudge_summary(1.5)

    def faster() -> str:
        import platform_speed_panel as psp
        return psp.menu_nudge_summary(0.67)

    def platform_save() -> str:
        import platform_speed_panel as psp
        return str(psp.save_level())

    def snap() -> str:
        import snap_place_panel as snp
        return snp.menu_snap_summary()

    def snap_save() -> str:
        import snap_place_panel as snp
        return str(snp.save_level())

    def look() -> str:
        import foundry_converged_panel as fcp
        return fcp.menu_mi_summary()

    def look_web() -> str:
        import material_instance_widget_panel as mi
        return str(mi.MaterialInstanceWidgetPanel.launch_web_panel())

    def look_webm() -> str:
        import foundry_converged_panel as fcp
        return fcp.menu_webm_summary()

    def flora_readout() -> str:
        return format_flora(read_flora_lanes())

    def place_field() -> str:
        return json.dumps(place_one_field(), default=str)

    def prove_lift() -> str:
        return json.dumps(prove_field(), default=str)

    rows = (
        ("world.status", "World", "World Compiler status", world_status),
        ("world.cleanup", "World", "Cleanup tagged field actors", world_cleanup),
        ("world.apply", "World", "Apply field from existing bundle", world_apply),
        ("world.capture", "World", "Capture lookdev stills", world_capture),
        ("foundry.status", "World", "Foundry status (MI + WC + recipe)", foundry_status),
        ("foundry.validate", "World", "Validate staged Foundry recipes", foundry_validate),
        ("foundry.plan", "World", "Plan Sea Above test tile", foundry_plan),
        ("pie.status", "PIE", "PIE status", pie_status),
        ("pie.play", "PIE", "Play (Simulate, current level)", pie_play),
        ("pie.stop", "PIE", "Stop PIE", pie_stop),
        ("wardrobe.equipped", "Wardrobe", "Show live equipped slots", wardrobe),
        ("sir.list", "Sir", "List authored vs placed perches", sir_list),
        ("sir.spawn", "Sir", "Spawn missing perches", sir_spawn),
        ("sir.snap", "Sir", "Snap selected perches to ground", sir_snap),
        ("sir.save", "Sir", "Save current level", sir_save),
        ("dress.platforms", "Dressing", "List platforms in current level", platforms),
        ("dress.slower", "Dressing", "Selected platform: slower", slower),
        ("dress.faster", "Dressing", "Selected platform: faster", faster),
        ("dress.save", "Dressing", "Save current level", platform_save),
        ("place.snap", "Dressing", "Snap selected meshes to ground", snap),
        ("place.save", "Dressing", "Save current level (placement)", snap_save),
        ("look.inspect", "Look", "Inspect material instance", look),
        ("look.web", "Look", "Open lookdev page", look_web),
        ("look.webm", "Look", "Encode MI-loop PNGs to .webm", look_webm),
        ("flora.readout", "Flora", "Plant wind lanes (read only)", flora_readout),
        ("field.place", "World", "Place one Chladni field on a World Compiler cluster", place_field),
        ("field.prove", "World", "Simulate and record one instance lift", prove_lift),
        ("help.livelink", "Help", "How to use", lambda: HELP_TEXT),
    )
    return [
        StudioAction(id=i, section=section, label=label, read_only=_read_only(i), run=fn)
        for i, section, label, fn in rows
        if not _forbidden(i, label)
    ]


def _gmm_actions() -> list[StudioAction]:
    """GMM_COMMANDS is the Grandmaster owner. Read it directly so a swallowed envui inject cannot hide it."""
    try:
        from gmm.ui.commands import GMM_COMMANDS
    except Exception:
        return []
    out: list[StudioAction] = []
    for cmd_id, (section, fn) in GMM_COMMANDS.items():
        label = cmd_id.replace("gmm.", "").replace(".", " ").title()
        if _forbidden(cmd_id, label):
            continue

        def _run(func=fn, cid=cmd_id) -> str:
            result = func({})
            message = getattr(result, "message", "")
            if getattr(result, "ok", False):
                return f"OK {cid}: {message}"
            return f"FAIL {cid}: {getattr(result, 'error', None) or message}"

        out.append(StudioAction(
            id=cmd_id,
            section=section or "Grandmaster",
            label=label,
            read_only=_read_only(cmd_id),
            run=_run,
        ))
    return out


def _envui_actions() -> list[StudioAction]:
    from envui import commands

    reg = commands.get_registry()
    out: list[StudioAction] = []
    for cmd in reg.values():
        if cmd.section in {"World", "PIE", "Wardrobe", "Sir", "Dressing", "Look", "Help"}:
            continue
        if _forbidden(cmd.id, cmd.label):
            continue
        command_id = cmd.id
        out.append(StudioAction(
            id=command_id,
            section=cmd.section or "Grandmaster",
            label=cmd.label,
            read_only=_read_only(command_id),
            run=lambda cid=command_id: _envui_run(cid),
        ))
    return out


def actions() -> list[StudioAction]:
    merged: dict[str, StudioAction] = {}
    for row in _local_actions() + _envui_actions() + _gmm_actions():
        merged.setdefault(row.id, row)
    return list(merged.values())


def sections() -> list[tuple[str, list[StudioAction]]]:
    grouped: dict[str, list[StudioAction]] = {name: [] for name in SECTION_ORDER}
    extras: dict[str, list[StudioAction]] = {}
    for row in actions():
        if row.section in grouped:
            grouped[row.section].append(row)
        else:
            extras.setdefault(row.section, []).append(row)
    for name, rows in grouped.items():
        if name == "Grandmaster":
            rank = {action_id: i for i, action_id in enumerate(GMM_FIRST)}
            rows.sort(key=lambda row: (rank.get(row.id, 50), row.label.lower()))
    ordered = [(name, grouped[name]) for name in SECTION_ORDER if grouped[name]]
    ordered.extend((name, rows) for name, rows in sorted(extras.items()))
    return ordered


def display_label(row: StudioAction) -> str:
    mark = "read" if row.read_only else "writes"
    return f"{row.label}  ·  {mark}"


def run_action(action_id: str) -> str:
    found = next((row for row in actions() if row.id == action_id), None)
    if found is None:
        return f"[Melodia Studio] unknown action {action_id}"
    try:
        text = found.run()
    except Exception as exc:
        text = f"[Melodia Studio] HOLD ({exc})"
    return text if isinstance(text, str) else str(text)


def audit_catalog() -> dict[str, Any]:
    """Offline check: palette, required slices, no compile or load-level control."""
    tones = palette()
    grouped = sections()
    names = [name for name, _ in grouped]
    flat = [row for _, rows in grouped for row in rows]
    grand = next(rows for name, rows in grouped if name == "Grandmaster")
    problems = []
    required = (
        "Connection", "World", "PIE", "Wardrobe", "Sir", "Dressing",
        "Look", "Flora", "PCG", "Grandmaster", "Help",
    )
    for name in required:
        if name not in names:
            problems.append(f"missing section {name}")
    if grand[0].id != "gmm.about" or grand[1].id != "gmm.mcp_status":
        problems.append(f"grandmaster order {[row.id for row in grand[:2]]}")
    for row in flat:
        if _forbidden(row.id, row.label):
            problems.append(f"forbidden {row.id}")
    if tones["text"].upper() != "#241B2E" or tones["gold"].upper() != "#C9A86A":
        problems.append(f"palette drifted {tones['text']} {tones['gold']}")
    if tones["surface"].upper() != "#F8ECD6":
        problems.append(f"surface drifted {tones['surface']}")
    problems.extend(pin_chladni())
    return {
        "ok": not problems,
        "problems": problems,
        "sections": names,
        "actions": len(flat),
        "palette": tones,
        "grandmaster_first": [row.id for row in grand[:2]],
    }


def _ue():
    import unreal
    return unreal


def _hex(value: str) -> tuple[float, float, float, float]:
    raw = value.lstrip("#")
    return (
        int(raw[0:2], 16) / 255.0,
        int(raw[2:4], 16) / 255.0,
        int(raw[4:6], 16) / 255.0,
        1.0,
    )


def _color(unreal, value: str):
    r, g, b, a = _hex(value)
    return unreal.LinearColor(r, g, b, a)


def _asset_widget_tree(asset):
    """UE 5.8 hides WidgetBlueprint.WidgetTree from Python properties. Find the object."""
    unreal = _ue()
    for read in (
        lambda: asset.get_widget_tree(),
        lambda: getattr(asset, "widget_tree", None),
        lambda: getattr(asset, "WidgetTree", None),
    ):
        try:
            tree = read()
        except Exception:
            tree = None
        if tree is not None:
            return tree
    asset_path = ""
    try:
        asset_path = asset.get_path_name()
    except Exception:
        asset_path = EUW_PATH
    found = None
    for obj in unreal.ObjectIterator():
        try:
            if obj.get_class().get_name() != "WidgetTree":
                continue
            path = obj.get_path_name()
        except Exception:
            continue
        if "EUW_MelodiaStudio" not in path or "WidgetTree_0" in path:
            continue
        found = obj
        if asset_path and asset_path in path:
            return obj
    return found


_CLICKS: list = []


def _bind_click(button, fn) -> None:
    """Keep the Python callable alive and attach it to the button, not its label."""
    _CLICKS.append(fn)
    delegate = getattr(button, "on_clicked", None)
    if delegate is None:
        raise AttributeError(f"{button.get_class().get_name()} has no on_clicked")
    delegate.add_callable(fn)


def _find_named(host, name: str, class_name: str | None = None):
    """EditorUtilityWidget in this build has no get_widget_from_name.

    Match the widget name exactly. Slice_Connection_Label is the caption, not the button.
    Prefer the live WidgetTree_0 instance over the saved template.
    """
    unreal = _ue()
    if host is not None:
        getter = getattr(host, "get_widget_from_name", None)
        if callable(getter):
            try:
                found = getter(name)
                if found is not None and (class_name is None or found.get_class().get_name() == class_name):
                    return found
            except Exception:
                pass
    token = ""
    try:
        token = host.get_name() if host is not None else ""
    except Exception:
        token = ""
    live = None
    template = None
    for obj in unreal.ObjectIterator():
        try:
            path = obj.get_path_name()
            leaf = path.rsplit(".", 1)[-1]
            kind = obj.get_class().get_name()
        except Exception:
            continue
        if "EUW_MelodiaStudio" not in path or leaf != name:
            continue
        if class_name is not None and kind != class_name:
            continue
        if "WidgetTree_0" in path:
            if token and token in path:
                return obj
            live = obj
        else:
            template = obj
    return live or template


def _tree_has(tree, name: str) -> bool:
    if tree is None:
        return False
    try:
        tree_path = tree.get_path_name()
    except Exception:
        return False
    unreal = _ue()
    for obj in unreal.ObjectIterator():
        try:
            path = obj.get_path_name()
        except Exception:
            continue
        if not path.startswith(tree_path):
            continue
        leaf = path.rsplit(".", 1)[-1]
        if leaf == name:
            return True
    return False


def _construct(tree, unreal, cls, name):
    """UWidgetTree.ConstructWidget is C++-only in UE 5.8. Create the widget on the tree."""
    widget = None
    try:
        widget = unreal.new_object(cls, outer=tree, name=name)
    except Exception as exc:
        unreal.log_warning(f"[Melodia Studio] new {name} failed: {exc}")
        try:
            widget = unreal.new_object(cls, tree)
        except Exception as exc2:
            unreal.log_error(f"[Melodia Studio] could not create {name}: {exc2}")
            return None
        try:
            widget.rename(name)
        except Exception:
            pass
    if widget is None:
        return None
    try:
        widget.set_editor_property("bIsVariable", True)
    except Exception:
        try:
            widget.set_editor_property("is_variable", True)
        except Exception:
            pass
    return widget


def _font(unreal, asset_path: str, size: int):
    font = unreal.SlateFontInfo()
    loaded = unreal.EditorAssetLibrary.load_asset(asset_path)
    if loaded is not None:
        try:
            font.set_editor_property("font_object", loaded)
        except Exception:
            pass
        try:
            font.set_editor_property("typeface_font_name", "Regular")
        except Exception:
            pass
    font.set_editor_property("size", size)
    return font


def _paint_text(unreal, block, text: str, color: str, font_path: str, size: int) -> None:
    try:
        block.set_text(text)
    except Exception:
        block.set_editor_property("text", text)
    try:
        block.set_color_and_opacity(_color(unreal, color))
    except Exception:
        pass
    try:
        block.set_font(_font(unreal, font_path, size))
    except Exception:
        pass


def _brush_texture(unreal, image, asset_path: str) -> bool:
    tex = unreal.EditorAssetLibrary.load_asset(asset_path)
    if tex is None:
        return False
    try:
        image.set_brush_from_texture(tex, True)
        return True
    except Exception:
        return False


def ensure_shell():
    """Create the Editor Utility Widget shell. Buttons are filled when the tab opens."""
    unreal = _ue()
    if unreal.EditorAssetLibrary.does_asset_exist(EUW_PATH):
        asset = unreal.EditorAssetLibrary.load_asset(EUW_PATH)
    else:
        if not unreal.EditorAssetLibrary.does_directory_exist(EUW_DIR):
            unreal.EditorAssetLibrary.make_directory(EUW_DIR)
        factory = unreal.EditorUtilityWidgetBlueprintFactory()
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "EUW_MelodiaStudio", EUW_DIR, unreal.EditorUtilityWidgetBlueprint, factory,
        )
    if asset is None:
        raise RuntimeError("EditorUtilityWidgetBlueprintFactory returned nothing")
    tree = _asset_widget_tree(asset)
    if tree is None:
        raise RuntimeError("Melodia Studio widget tree is not visible to Python")
    if _tree_has(tree, "StudioPie"):
        return asset
    tones = palette()
    root = _construct(tree, unreal, unreal.VerticalBox, "StudioRoot")
    if root is None:
        raise RuntimeError("could not create the Melodia Studio root")
    try:
        tree.root_widget = root
    except Exception:
        tree.set_editor_property("root_widget", root)

    frame = _construct(tree, unreal, unreal.Border, "StudioFrame")
    parchment = unreal.EditorAssetLibrary.load_asset(PARCHMENT)
    if parchment is not None:
        try:
            brush = unreal.SlateBrush()
            brush.set_editor_property("resource_object", parchment)
            frame.set_editor_property("brush", brush)
        except Exception:
            pass
    try:
        frame.set_brush_color(_color(unreal, tones["raised"]))
    except Exception:
        pass
    root.add_child(frame)

    pie_size = _construct(tree, unreal, unreal.SizeBox, "StudioPieSize")
    try:
        pie_size.set_editor_property("height_override", 560.0)
        pie_size.set_editor_property("width_override", 720.0)
    except Exception:
        pass
    pie = _construct(tree, unreal, unreal.CanvasPanel, "StudioPie")
    pie_size.add_child(pie) if hasattr(pie_size, "add_child") else pie_size.set_content(pie)
    frame.set_content(pie_size) if hasattr(frame, "set_content") else frame.add_child(pie_size)

    slice_label = _construct(tree, unreal, unreal.TextBlock, "StudioSliceLabel")
    _paint_text(unreal, slice_label, "Choose a slice", tones["text"], FONT_SERIF, 18)
    root.add_child(slice_label)

    scroller = _construct(tree, unreal, unreal.ScrollBox, "StudioActionScroll")
    host = _construct(tree, unreal, unreal.VerticalBox, "StudioActions")
    scroller.add_child(host)
    root.add_child(scroller)

    result = _construct(tree, unreal, unreal.MultiLineEditableTextBox, "StudioResult")
    try:
        result.set_editor_property("is_read_only", True)
    except Exception:
        pass
    _paint_text(unreal, result, HELP_TEXT, tones["text"], FONT_UI, 13)
    root.add_child(result)

    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(asset)
    except Exception:
        try:
            unreal.KismetEditorUtilities.compile_blueprint(asset)
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def _clear(panel) -> None:
    try:
        panel.clear_children()
        return
    except Exception:
        pass
    try:
        for child in list(panel.get_all_children()):
            panel.remove_child(child)
    except Exception:
        pass


def _button(unreal, parent, name: str, text: str, fill: str, ink: str):
    button = unreal.new_object(unreal.Button, parent)
    try:
        button.set_background_color(_color(unreal, fill))
    except Exception:
        pass
    label = unreal.new_object(unreal.TextBlock, button)
    _paint_text(unreal, label, text, ink, FONT_UI, 12)
    try:
        button.add_child(label)
    except Exception:
        pass
    slot = parent.add_child(button)
    return button, slot


def _place(slot, x: float, y: float, w: float, h: float) -> None:
    try:
        slot.set_position(_ue().Vector2D(x, y))
        slot.set_size(_ue().Vector2D(w, h))
        slot.set_anchors(_ue().Anchors(0, 0, 0, 0))
        slot.set_alignment(_ue().Vector2D(0.5, 0.5))
    except Exception:
        pass


def _decorate_pie(unreal, canvas) -> None:
    corners = ((28, 28, 0), (690, 28, 90), (28, 520, -90), (690, 520, 180))
    for index, (x, y, _angle) in enumerate(corners):
        image = unreal.new_object(unreal.Image, canvas)
        if not _brush_texture(unreal, image, FILIGREE_CORNER):
            continue
        try:
            image.set_visibility(unreal.SlateVisibility.HIT_TEST_INVISIBLE)
        except Exception:
            pass
        slot = canvas.add_child(image)
        _place(slot, x, y, 72, 72)
        _ = index
    rule = unreal.new_object(unreal.Image, canvas)
    if _brush_texture(unreal, rule, FILIGREE_DIVIDER):
        try:
            rule.set_visibility(unreal.SlateVisibility.HIT_TEST_INVISIBLE)
        except Exception:
            pass
        slot = canvas.add_child(rule)
        _place(slot, 360, 300, 280, 28)


def _show_slice(widget, section: str, rows: list[StudioAction]) -> None:
    unreal = _ue()
    tones = palette()
    label = _find_named(widget, "StudioSliceLabel")
    if label is not None:
        _paint_text(unreal, label, section, tones["text"], FONT_SERIF, 18)
    host = _find_named(widget, "StudioActions")
    if host is None:
        return
    _clear(host)
    colors = slice_colors()
    for index, row in enumerate(rows):
        fill = tones["raised"] if row.read_only else colors[index % len(colors)]
        button, _slot = _button(
            unreal, host, f"Act_{row.id.replace('.', '_')}", display_label(row), fill, tones["text"],
        )

        def _click(action_id: str = row.id, live=widget):
            text = run_action(action_id)
            box = _find_named(live, "StudioResult")
            if box is not None:
                try:
                    box.set_text(text)
                except Exception:
                    pass
            unreal.log(text)

        try:
            _bind_click(button, _click)
        except Exception as exc:
            unreal.log_error(f"[Melodia Studio] bind {row.id}: {exc}")


def _editor_worlds(unreal) -> list:
    worlds = []
    try:
        sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    except Exception:
        return worlds
    for getter in ("get_game_world", "get_editor_world"):
        try:
            world = getattr(sub, getter)()
        except Exception:
            world = None
        if world is not None:
            worlds.append(world)
    return worlds


def _mpc_scalar(path: str, name: str) -> float | None:
    try:
        unreal = _ue()
    except Exception:
        return None
    mpc = unreal.EditorAssetLibrary.load_asset(path)
    if mpc is None:
        return None
    for world in _editor_worlds(unreal):
        try:
            value = unreal.MaterialLibrary.get_scalar_parameter_value(world, mpc, name)
            return float(value)
        except Exception:
            continue
    return None


def read_live_bands() -> dict[str, Any]:
    """Read palette bands. Does not write a collection."""
    bass = _mpc_scalar(PALETTE_MPC, "BassIntensity")
    beat = _mpc_scalar(PALETTE_MPC, "BeatPulse")
    bass = 0.0 if bass is None else bass
    beat = 0.0 if beat is None else beat
    state = plate_state(bass, beat)
    state["driver_mode_n"] = _mpc_scalar(DRIVER_MPC, "Cymatic_ModeN")
    state["driver_mode_m"] = _mpc_scalar(DRIVER_MPC, "Cymatic_ModeM")
    state["source"] = "mpc" if _mpc_scalar(PALETTE_MPC, "BassIntensity") is not None else "rest"
    return state


def read_flora_lanes() -> dict[str, float | None]:
    """Lanes M_MelodiaPlant_Wind already samples. Read only."""
    names = (
        "Cymatic_BeatPulse",
        "Cymatic_EmissiveScale",
        "Cymatic_WindDirX",
        "Cymatic_WindDirY",
        "Cymatic_WindStrength",
    )
    return {name: _mpc_scalar(DRIVER_MPC, name) for name in names}


def format_flora(lanes: dict[str, float | None]) -> str:
    lines = ["[Flora] M_MelodiaPlant_Wind reads these driver lanes. No master write."]
    for name, value in lanes.items():
        shown = "HOLD (collection unread)" if value is None else f"{value:.4f}"
        lines.append(f"  {name}: {shown}")
    return "\n".join(lines)


def _mix_linear(unreal, amount: float):
    amount = max(0.0, min(1.0, amount))
    plum = (0x24 / 255.0, 0x1B / 255.0, 0x2E / 255.0)
    gold = (0xC9 / 255.0, 0xA8 / 255.0, 0x6A / 255.0)
    return unreal.LinearColor(
        plum[0] * (1.0 - amount) + gold[0] * amount,
        plum[1] * (1.0 - amount) + gold[1] * amount,
        plum[2] * (1.0 - amount) + gold[2] * amount,
        1.0,
    )


def _draw_plate(unreal, canvas, cx: float, cy: float, tones: dict[str, str]):
    """Coarse Chladni grid in the pie center. Cells are views, not writers."""
    _PLATE["cells"] = []
    span = PLATE_GRID * 9.0
    origin_x = cx - span * 0.5
    origin_y = cy - span * 0.5
    for row in range(PLATE_GRID):
        for col in range(PLATE_GRID):
            u = col / (PLATE_GRID - 1)
            v = row / (PLATE_GRID - 1)
            image = unreal.new_object(unreal.Image, canvas)
            try:
                image.set_visibility(unreal.SlateVisibility.HIT_TEST_INVISIBLE)
            except Exception:
                pass
            slot = canvas.add_child(image)
            _place(slot, origin_x + col * 9.0 + 4.0, origin_y + row * 9.0 + 4.0, 8.0, 8.0)
            _PLATE["cells"].append((image, u, v))
    label = unreal.new_object(unreal.TextBlock, canvas)
    _paint_text(unreal, label, "N2 M3", tones["text"], FONT_SERIF, 14)
    slot = canvas.add_child(label)
    _place(slot, cx, cy - span * 0.5 - 16.0, 120.0, 22.0)
    _PLATE["label"] = label
    _refresh_plate()
    return _button(unreal, canvas, "Slice_Center", "Plate", tones["inverse"], tones["gold"])


def _refresh_plate() -> None:
    if not _PLATE["cells"]:
        return
    try:
        unreal = _ue()
    except Exception:
        return
    state = read_live_bands()
    _PLATE["state"] = state
    for image, u, v in _PLATE["cells"]:
        wave = chladni01(state["mode_n"], state["mode_m"], u, v) * max(state["tension"], 0.15)
        try:
            image.set_color_and_opacity(_mix_linear(unreal, wave))
        except Exception:
            pass
    label = _PLATE.get("label")
    if label is not None:
        driver_n = state.get("driver_mode_n")
        driver_m = state.get("driver_mode_m")
        extra = ""
        if driver_n is not None and driver_m is not None:
            extra = f"  driver {int(driver_n)},{int(driver_m)}"
        text = f"N{state['mode_n']} M{state['mode_m']}{extra}"
        try:
            label.set_text(text)
        except Exception:
            pass


def _ensure_plate_tick() -> None:
    if _PLATE.get("handle") is not None:
        return
    unreal = _ue()

    def _tick(_delta):
        _refresh_plate()
        return True

    try:
        _PLATE["handle"] = unreal.register_slate_post_tick_callback(_tick)
    except Exception as exc:
        unreal.log_error(f"[Melodia Studio] plate tick: {exc}")


def _level_name(unreal) -> str:
    worlds = _editor_worlds(unreal)
    if not worlds:
        return ""
    try:
        return str(worlds[-1].get_name())
    except Exception:
        return ""


def _is_ask_first(level_name: str) -> bool:
    return any(name in level_name for name in ASK_FIRST_LEVELS)


def _tag_component(comp) -> bool:
    unreal = _ue()
    try:
        tags = list(comp.get_editor_property("component_tags"))
    except Exception:
        tags = []
    if any(str(tag) == "MelodiaCymatic" for tag in tags):
        return False
    tags.append(unreal.Name("MelodiaCymatic"))
    comp.set_editor_property("component_tags", tags)
    return True


def place_one_field() -> dict[str, Any]:
    """Tag one World Compiler ISM cluster and drop the existing field component beside it."""
    try:
        unreal = _ue()
    except Exception as exc:
        return {"ok": False, "status": "HOLD", "error": f"Unreal not running: {exc}"}
    level = _level_name(unreal)
    if not level:
        return {"ok": False, "status": "HOLD", "error": "no editor world"}
    if _is_ask_first(level):
        return {"ok": False, "status": "HOLD", "level": level, "error": "ask-first level"}
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    host = None
    for actor in actors:
        label = ""
        try:
            label = actor.get_actor_label()
        except Exception:
            label = actor.get_name()
        tag_text = " ".join(str(tag) for tag in getattr(actor, "tags", []))
        if not (label.startswith("WC_") or "WorldCompiler" in tag_text or "WorldCompiler" in label):
            continue
        comps = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
        if any(comp.get_instance_count() > 0 for comp in comps):
            host = actor
            break
    if host is None:
        return {"ok": False, "status": "HOLD", "level": level, "error": "no World Compiler ISM cluster in this level"}
    tagged = 0
    for comp in host.get_components_by_class(unreal.InstancedStaticMeshComponent):
        if comp.get_instance_count() <= 0:
            continue
        _tag_component(comp)
        tagged += 1
    location = host.get_actor_location()
    existing = None
    for actor in actors:
        try:
            if actor.get_actor_label() == "MelodiaStudio_ChladniField":
                existing = actor
                break
        except Exception:
            continue
    if existing is None:
        field_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.TriggerBox, location, unreal.Rotator(0.0, 0.0, 0.0)
        )
        field_actor.set_actor_label("MelodiaStudio_ChladniField")
        comp_class = unreal.load_class(None, "/Script/BS_GodFile.MelodiaCymaticFieldComponent")
        field_actor.add_component_by_class(comp_class, False, unreal.Transform(), False)
    else:
        field_actor = existing
        field_actor.set_actor_location(location, False, False)
    return {
        "ok": True,
        "level": level,
        "host": host.get_actor_label(),
        "tagged_components": tagged,
        "field": field_actor.get_actor_label(),
        "location": [location.x, location.y, location.z],
    }


def _write_receipt(payload: dict[str, Any]) -> str:
    dest = ROOT / "Saved" / "Audit" / "chladni_plate_afternoon.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(dest).replace("\\", "/")


def prove_field() -> dict[str, Any]:
    """Simulate the current level and record plate modes against one instance lift."""
    try:
        unreal = _ue()
    except Exception as exc:
        receipt = {"ok": False, "status": "HOLD", "error": f"Unreal not running: {exc}"}
        receipt["receipt"] = _write_receipt(receipt)
        return receipt
    placed = place_one_field()
    if not placed.get("ok"):
        receipt = {"ok": False, "placed": placed}
        placed["receipt"] = _write_receipt(receipt)
        return placed
    host = None
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        try:
            if actor.get_actor_label() == placed["host"]:
                host = actor
                break
        except Exception:
            continue
    rest_z = None
    if host is not None:
        for comp in host.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if comp.get_instance_count() > 0:
                transform = comp.get_instance_transform(0, True)
                rest_z = transform.translation.z
                break
    import melodia_pie_panel as pie

    play = pie.pie_play()
    state = plate_state(
        _mpc_scalar(PALETTE_MPC, "BassIntensity") or 0.0,
        _mpc_scalar(PALETTE_MPC, "BeatPulse") or 0.0,
    )
    receipt = {
        "ok": True,
        "placed": placed,
        "play": play,
        "plate": state,
        "rest_z": rest_z,
        "note": "Lift is sampled on the next editor tick after simulate starts.",
    }
    ticks = {"n": 0}

    def _sample(_delta):
        ticks["n"] += 1
        if ticks["n"] < 90:
            return True
        lifted = None
        if host is not None:
            for comp in host.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if comp.get_instance_count() > 0:
                    transform = comp.get_instance_transform(0, True)
                    lifted = transform.translation.z
                    break
        bus = None
        try:
            bus_cls = unreal.load_class(None, "/Script/BS_GodFile.WorldFieldBus")
            sample = bus_cls.sample_resonance_tension(unreal.Vector(0.0, 0.0, 0.0))
            bus = {
                "n": sample.get_editor_property("resonance_n"),
                "m": sample.get_editor_property("resonance_m"),
                "tension": sample.get_editor_property("tension"),
            }
        except Exception as exc:
            bus = {"error": str(exc)}
        receipt["lifted_z"] = lifted
        receipt["delta_z"] = None if lifted is None or rest_z is None else lifted - rest_z
        receipt["bus"] = bus
        receipt["plate_matches_bus"] = (
            isinstance(bus, dict)
            and bus.get("n") == state["mode_n"]
            and bus.get("m") == state["mode_m"]
        )
        receipt["receipt"] = _write_receipt(receipt)
        unreal.log("[Melodia Studio] field proof " + json.dumps({
            "delta_z": receipt["delta_z"],
            "plate_matches_bus": receipt["plate_matches_bus"],
            "bus": bus,
        }, default=str))
        return False

    try:
        unreal.register_slate_post_tick_callback(_sample)
    except Exception as exc:
        receipt["tick_error"] = str(exc)
        receipt["receipt"] = _write_receipt(receipt)
    return receipt


def populate_pie(widget) -> None:
    unreal = _ue()
    tones = palette()
    canvas = _find_named(widget, "StudioPie")
    if canvas is None:
        unreal.log_error("[Melodia Studio] StudioPie is missing from the tab")
        return
    _clear(canvas)
    _decorate_pie(unreal, canvas)
    grouped = [(name, rows) for name, rows in sections() if rows]
    count = max(len(grouped), 1)
    colors = slice_colors()
    cx, cy, radius = 360.0, 270.0, 210.0
    for index, (name, rows) in enumerate(grouped):
        angle = -math.pi / 2.0 + (2.0 * math.pi * index / count)
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        fill = colors[index % len(colors)]
        button, slot = _button(unreal, canvas, f"Slice_{name.replace(' ', '_')}", name, fill, tones["text"])
        _place(slot, x, y, 132, 36)

        def _open(section: str = name, items: list[StudioAction] = rows, live=widget):
            _show_slice(live, section, items)

        try:
            _bind_click(button, _open)
        except Exception as exc:
            unreal.log_error(f"[Melodia Studio] slice {name}: {exc}")

    center, slot = _draw_plate(unreal, canvas, cx, cy, tones)
    _place(slot, cx, cy + 78, 88, 28)

    def _home(live=widget):
        box = _find_named(live, "StudioResult")
        if box is not None:
            try:
                box.set_text(HELP_TEXT)
            except Exception:
                pass
        host = _find_named(live, "StudioActions")
        if host is not None:
            _clear(host)
        label = _find_named(live, "StudioSliceLabel")
        if label is not None:
            _paint_text(unreal, label, "Choose a slice", tones["text"], FONT_SERIF, 18)

    try:
        _bind_click(center, _home)
    except Exception:
        pass


def _let_clicks_through(widget) -> None:
    """The ivory frame covers the pie. It must not take the click."""
    unreal = _ue()
    for name, kind in (("StudioFrame", "Border"), ("StudioTitle", "TextBlock"), ("StudioSliceLabel", "TextBlock")):
        widget_obj = _find_named(widget, name, kind)
        if widget_obj is None:
            continue
        try:
            widget_obj.set_visibility(unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE)
        except Exception:
            pass


def _bind_designed_slices(widget) -> int:
    """The saved Editor Utility Widget already has the pie. Bind the slice buttons."""
    unreal = _ue()
    _let_clicks_through(widget)
    bound = 0
    grouped = [(name, rows) for name, rows in sections() if rows]
    for name, rows in grouped:
        button = _find_named(widget, f"Slice_{name.replace(' ', '_')}", "Button")
        if button is None:
            unreal.log_error(f"[Melodia Studio] slice button missing: {name}")
            continue

        def _open(section: str = name, items: list[StudioAction] = rows, live=widget):
            _show_slice(live, section, items)

        try:
            _bind_click(button, _open)
            bound += 1
        except Exception as exc:
            unreal.log_error(f"[Melodia Studio] slice {name}: {exc}")
    unreal.log(f"[Melodia Studio] bound {bound} slice buttons")
    return bound


def open_studio():
    """Open the saved Melodia Studio Editor Utility Widget. Python does not build the tree."""
    unreal = _ue()
    asset = unreal.EditorAssetLibrary.load_asset(EUW_PATH)
    if asset is None:
        unreal.log_error("[Melodia Studio] designed widget is missing at " + EUW_PATH)
        return None
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget = subsystem.spawn_and_register_tab(asset)
    if widget is None:
        unreal.log_error("[Melodia Studio] spawn_and_register_tab returned nothing")
        return None
    bound = _bind_designed_slices(widget)
    unreal.log(f"[Melodia Studio] designed pie open. {bound} slices bound. Compile stays CLI. No load level.")
    return widget


def verify_open() -> dict[str, Any]:
    """Editor check: tab spawned, catalog clean, wardrobe HOLD, read-only text matches owners."""
    report = audit_catalog()
    unreal = _ue()
    widget = open_studio()
    report["spawned"] = widget is not None
    report["pie"] = _find_named(widget, "StudioPie") is not None if widget else False
    report["result_box"] = _find_named(widget, "StudioResult") is not None if widget else False
    samples = {}
    for action_id in (
        "foundry.status", "pie.status", "sir.list", "dress.platforms",
        "wardrobe.equipped", "gmm.about", "livelink.status",
    ):
        samples[action_id] = run_action(action_id)
    report["samples"] = samples
    report["wardrobe_hold"] = "HOLD" in samples["wardrobe.equipped"]
    report["ok"] = bool(report["ok"] and report["spawned"] and report["pie"] and report["wardrobe_hold"])
    unreal.log("[Melodia Studio] verify " + json.dumps({
        "ok": report["ok"],
        "spawned": report["spawned"],
        "wardrobe_hold": report["wardrobe_hold"],
        "sections": report["sections"],
    }))
    return report


if __name__ == "__main__":
    print(json.dumps(audit_catalog(), indent=2))
