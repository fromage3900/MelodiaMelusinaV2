"""GMM command registry — EnvUI-compatible commands for all subsystems.

Each command is a callable with signature:
    (params: dict) -> CommandResult

Usage from envui:
    from gmm.ui.commands import GMM_COMMANDS
    registry.update(GMM_COMMANDS)
"""
from __future__ import annotations

import json
import sys
from typing import Any, Callable

from gmm import VERSION, VERSION_NAME, VERSION_TAG
from gmm.core import MonolithClient, write_audit, GmmAudit


class CommandResult:
    """Standardised return envelope for EnvUI commands."""
    def __init__(self, ok: bool, message: str = "",
                 outputs: dict | None = None, error: str | None = None):
        self.ok = ok
        self.message = message
        self.outputs = outputs or {}
        self.error = error


GMM_SECTION = "Grandmaster"


# ------------------------------------------------------------------
# Core Commands
# ------------------------------------------------------------------

def _cmd_about(_: dict) -> CommandResult:
    msg = (
        f"{VERSION_NAME} v{VERSION} ({VERSION_TAG})\n"
        f"Monolith MCP + MelodiaCore + Melusina rig + Surreal/Escher geometry\n"
        f"Audit reports: Saved/Audit/gmm_*.json"
    )
    return CommandResult(ok=True, message=msg, outputs={
        "version": VERSION,
        "name": VERSION_NAME,
        "tag": VERSION_TAG,
        "subsystems": ["melodia", "melusina", "surreal", "pcg", "mkc"],
    })


def _cmd_mcp_status(params: dict) -> CommandResult:
    mc = MonolithClient()
    try:
        status = mc.status()
        return CommandResult(ok=True, message=f"MCP: {status.get('version', 'unknown')}",
                             outputs=status)
    except Exception as e:
        return CommandResult(ok=False, message=f"MCP unreachable: {e}", error=str(e))


def _cmd_mcp_discover(params: dict) -> CommandResult:
    ns = params.get("namespace", "")
    mc = MonolithClient()
    try:
        result = mc.discover(ns or None)
        count = len(result) if isinstance(result, list) else result.get("total_actions", 0)
        return CommandResult(ok=True, message=f"Discovered {count} actions in '{ns or 'all'}'",
                             outputs={"namespace": ns, "actions": result})
    except Exception as e:
        return CommandResult(ok=False, message=f"Discover failed: {e}", error=str(e))


def _cmd_run_python(params: dict) -> CommandResult:
    command = params.get("command", "")
    mode = params.get("mode", "execute_statement")
    if not command:
        return CommandResult(ok=False, message="No command provided", error="missing_command")
    mc = MonolithClient()
    try:
        result = mc.run_python(command, mode=mode)
        success = result.get("success", False)
        msg = "Python executed OK" if success else "Python execution failed"
        return CommandResult(ok=success, message=msg, outputs=result)
    except Exception as e:
        return CommandResult(ok=False, message=f"run_python failed: {e}", error=str(e))


# ------------------------------------------------------------------
# Melodia Commands
# ------------------------------------------------------------------

def _cmd_melodia_enemies(_: dict) -> CommandResult:
    from gmm.melodia.enemies import list_enemies, audit_enemy_summary
    enemies = list_enemies()
    summary = audit_enemy_summary()
    audit = GmmAudit(action="melodia.enemy_list", **summary)
    audit.save("gmm_melodia_enemies.json")
    return CommandResult(ok=True,
                         message=f"{summary['count']} enemies, elements: {summary['elements']}",
                         outputs=audit.to_dict())


def _cmd_melodia_skills(_: dict) -> CommandResult:
    from gmm.melodia.skills import list_skills, audit_skill_summary
    skills = list_skills()
    summary = audit_skill_summary()
    audit = GmmAudit(action="melodia.skill_list", **summary)
    audit.save("gmm_melodia_skills.json")
    return CommandResult(ok=True,
                         message=f"{summary['count']} skills, instruments: {summary['instruments']}",
                         outputs=audit.to_dict())


# ------------------------------------------------------------------
# Melusina Commands
# ------------------------------------------------------------------

def _cmd_melusina_rig_assess(params: dict) -> CommandResult:
    audit = GmmAudit(action="melusina.rig_assess")
    try:
        import assess_melusina_rig
        report = assess_melusina_rig.build_full_report()
        audit.ok(**report)
        audit.save("gmm_melusina_rig.json")
        msg = f"Rig assessed: {report.get('skeletal_mesh', {}).get('bone_count', '?')} bones"
        return CommandResult(ok=True, message=msg, outputs=audit.to_dict())
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save()
        return CommandResult(ok=False, message=f"Rig assessment failed: {e}", error=str(e))


def _cmd_melusina_blend_setup(params: dict) -> CommandResult:
    audit = GmmAudit(action="melusina.blend_setup")
    try:
        import setup_melusina_exploration
        result = setup_melusina_exploration.create_blend_space()
        audit.ok(**result)
        audit.save("gmm_melusina_blend.json")
        return CommandResult(ok=result.get("created", False),
                             message=result.get("error", "Blend space OK"),
                             outputs=audit.to_dict())
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save()
        return CommandResult(ok=False, message=f"Blend setup failed: {e}", error=str(e))


def _cmd_melusina_bp_setup(params: dict) -> CommandResult:
    audit = GmmAudit(action="melusina.bp_setup")
    try:
        import setup_melusina_exploration
        result = setup_melusina_exploration.create_exploration_blueprint()
        audit.ok(**result)
        audit.save("gmm_melusina_bp.json")
        return CommandResult(ok=result.get("created", False),
                             message="BP created" if result.get("created") else "BP existed",
                             outputs=audit.to_dict())
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save()
        return CommandResult(ok=False, message=f"BP setup failed: {e}", error=str(e))


# ------------------------------------------------------------------
# Surreal Geometry Commands
# ------------------------------------------------------------------

def _cmd_surreal_escher(params: dict) -> CommandResult:
    from gmm.surreal.escher import build_escher_graphs, ESCHER_STATUS
    build = params.get("build", False)
    if build:
        audit = build_escher_graphs(force=params.get("force", False))
    else:
        audit = ESCHER_STATUS()
    msg = "Escher graphs check OK" if audit.get("ok") else "Escher graphs incomplete"
    return CommandResult(ok=bool(audit.get("ok")), message=msg, outputs=audit)


def _cmd_surreal_proc_arch(params: dict) -> CommandResult:
    from gmm.surreal.proc_arch import build_cathedral_nave, CATHEDRAL_STATUS
    build = params.get("build", False)
    if build:
        audit = build_cathedral_nave(
            bay_count=params.get("bay_count", 4),
            buttress_depth=params.get("buttress_depth", 3),
        )
    else:
        audit = CATHEDRAL_STATUS()
    msg = "Cathedral grammar OK" if audit.get("ok") else "Cathedral grammar incomplete"
    return CommandResult(ok=bool(audit.get("ok")), message=msg, outputs=audit)


# ------------------------------------------------------------------
# PCG Governance Commands
# ------------------------------------------------------------------


def _cmd_pcg_preflight(params: dict) -> CommandResult:
    from gmm.pcg import preflight

    report = preflight(include_pillars=params.get("include_pillars", True))
    ok = report.get("status") == "ok" and bool(report.get("data", {}).get("all_ok"))
    return CommandResult(
        ok=ok,
        message="PCG preflight passed" if ok else "PCG preflight failed; inspect gmm_pcg_preflight.json",
        outputs=report,
        error=None if ok else "pcg_preflight_failed",
    )


def _cmd_pcg_manifest(params: dict) -> CommandResult:
    manifest_path = params.get("path") or params.get("manifest")
    if not manifest_path:
        return CommandResult(False, "Manifest path is required", error="missing_manifest_path")
    apply = bool(params.get("apply", False))
    replace = bool(params.get("replace", True))
    try:
        if apply:
            from pathlib import Path
            import import_world_manifest

            result = import_world_manifest.import_manifest(Path(manifest_path), apply=True, replace=replace)
        else:
            from gmm.pcg import validate_manifest_file

            result = validate_manifest_file(manifest_path, for_apply=bool(params.get("for_apply", False)))
    except Exception as exc:
        return CommandResult(False, f"World manifest command failed: {exc}", error=str(exc))
    ok = bool(result.get("ok"))
    action = "applied" if apply and result.get("applied") else "validated"
    return CommandResult(
        ok=ok,
        message=f"World manifest {action}" if ok else "World manifest failed validation/application",
        outputs=result,
        error=None if ok else "world_manifest_failed",
    )


def _cmd_pcg_repair_quarantine(params: dict) -> CommandResult:
    from gmm.pcg import repair_quarantined_references

    report = repair_quarantined_references(save=params.get("save", True))
    ok = report.get("status") == "ok"
    count = report.get("data", {}).get("replacement_count", 0)
    return CommandResult(
        ok=ok,
        message=f"Repaired {count} quarantined PCG reference(s)" if ok else "PCG quarantine repair failed",
        outputs=report,
        error=None if ok else "pcg_quarantine_repair_failed",
    )


def _cmd_pcg_release_gate(params: dict) -> CommandResult:
    from gmm.pcg import release_gate

    report = release_gate(params.get("path") or params.get("manifest"))
    ok = report.get("status") == "ok" and bool(report.get("data", {}).get("all_ok"))
    return CommandResult(
        ok=ok,
        message="PCG release gate passed" if ok else "PCG release gate failed",
        outputs=report,
        error=None if ok else "pcg_release_gate_failed",
    )


# ------------------------------------------------------------------
# MKC Commands
# ------------------------------------------------------------------

def _cmd_mkc_verify_all(params: dict) -> CommandResult:
    audit = GmmAudit(action="mkc.verify_all")
    results = {}
    mc = MonolithClient()
    try:
        status = mc.status()
        results["mcp"] = {"ok": True, "version": status.get("version")}
    except Exception as e:
        results["mcp"] = {"ok": False, "error": str(e)}
    try:
        import assess_melusina_rig
        rig = assess_melusina_rig.build_full_report()
        results["melusina_rig"] = {"ok": True, "bones": rig.get("skeletal_mesh", {}).get("bone_count")}
    except Exception as e:
        results["melusina_rig"] = {"ok": False, "error": str(e)}
    if params.get("include_pcg", True):
        try:
            from gmm.pcg import preflight

            pcg = preflight(include_pillars=params.get("include_pillars", True))
            results["pcg"] = {
                "ok": pcg.get("status") == "ok" and bool(pcg.get("data", {}).get("all_ok")),
                "report": pcg,
            }
        except Exception as e:
            results["pcg"] = {"ok": False, "error": str(e)}
    all_ok = bool(results) and all(r.get("ok") for r in results.values())
    if all_ok:
        audit.ok(subsystem_results=results, all_ok=True)
    else:
        audit.fail("One or more system checks failed")
        audit.data.update(subsystem_results=results, all_ok=False)
    audit.save("gmm_verify_all.json")
    return CommandResult(ok=all_ok,
                         message="All systems OK" if all_ok else "Some checks failed",
                         outputs=audit.to_dict())


# ------------------------------------------------------------------
# Battle Test Harness Commands
# ------------------------------------------------------------------

_BATTLE_HARNESS = None


def _get_harness():
    global _BATTLE_HARNESS
    if _BATTLE_HARNESS is None:
        from gmm.melodia.battle import BattleTestHarness
        _BATTLE_HARNESS = BattleTestHarness()
    return _BATTLE_HARNESS


def _cmd_battle_test_encounter(params: dict) -> CommandResult:
    harness = _get_harness()
    enemy_id = params.get("enemy_id", "CrystalShard")
    result = harness.spawn_encounter(enemy_id)
    if result.get("ok"):
        msg = f"Encounter started: {result['enemy']['display_name']} ({result['phase']})"
    else:
        msg = result.get("error", "Spawn failed")
    return CommandResult(ok=result.get("ok", False), message=msg, outputs=result)


def _cmd_battle_state(_: dict) -> CommandResult:
    harness = _get_harness()
    state = harness.poll_state()
    phase = state.get("phase", "None")
    enemy = state.get("enemy", {})
    player = state.get("player", {})
    msg = f"Phase: {phase} | Enemy HP: {enemy.get('hp', 0):.0f}/{enemy.get('max_hp', 0):.0f}"
    return CommandResult(ok=True, message=msg, outputs=state)


def _cmd_battle_command(params: dict) -> CommandResult:
    harness = _get_harness()
    command = params.get("command", "basic_attack")
    skill_id = params.get("skill_id", "")
    grade = params.get("grade", "perfect")

    result = harness.issue_command(command, skill_id)
    if not result.get("ok"):
        return CommandResult(ok=False, message=result.get("error", "Command failed"), outputs=result)

    rhythm = harness.resolve_rhythm(grade)
    if rhythm.get("phase") in ("Victory", "Defeat"):
        msg = f"{rhythm['phase']}! Damage: {rhythm.get('damage', 0):.0f} | Combo: {rhythm.get('combo', 0)}"
    elif rhythm.get("phase") == "EnemyTurn":
        enemy_result = harness.enemy_attack()
        msg = (
            f"Resolved {grade} | Enemy HP: {rhythm.get('enemy_hp', 0):.0f} | "
            f"Took {enemy_result.get('damage', 0):.0f} damage"
        )
    else:
        msg = f"Resolved {grade} | Phase: {rhythm.get('phase')}"

    return CommandResult(ok=True, message=msg, outputs=rhythm)


# ------------------------------------------------------------------
# UI Widget Commands
# ------------------------------------------------------------------

def _cmd_ui_create_battle_menu(_: dict) -> CommandResult:
    try:
        from gmm.ui.battle_menu import create_battle_menu_widget
        result = create_battle_menu_widget()
        if result.ok:
            return CommandResult(
                ok=True,
                message=f"Created battle menu widget: {result.path}",
                outputs={"path": result.path},
            )
        return CommandResult(ok=False, message=f"Failed: {result.error}", error=result.error)
    except Exception as e:
        return CommandResult(ok=False, message=f"Error: {e}", error=str(e))


def _cmd_ui_battle_gui(_: dict) -> CommandResult:
    try:
        from gmm.ui.battle_gui import launch_battle_gui_nonblocking
        launch_battle_gui_nonblocking()
        return CommandResult(ok=True, message="Battle Test Harness GUI launched in new window.")
    except Exception as e:
        return CommandResult(ok=False, message=f"Failed to launch GUI: {e}", error=str(e))


def _cmd_ui_title_menu(_: dict) -> CommandResult:
    """Create the title menu widget blueprint."""
    try:
        from gmm.ui.title_menu import create_title_menu_widget
        result = create_title_menu_widget()
        if result.ok:
            return CommandResult(
                ok=True,
                message=f"Created title menu widget: {result.path}",
                outputs={"path": result.path},
            )
        return CommandResult(ok=False, message=f"Failed: {result.error}", error=result.error)
    except Exception as e:
        return CommandResult(ok=False, message=f"Error: {e}", error=str(e))


def _cmd_ui_save_slots(_: dict) -> CommandResult:
    """Create the save slot menu widget blueprint."""
    try:
        from gmm.ui.save_slots import create_save_slot_menu_widget
        result = create_save_slot_menu_widget()
        if result.ok:
            return CommandResult(
                ok=True,
                message=f"Created save slot menu widget: {result.path}",
                outputs={"path": result.path},
            )
        return CommandResult(ok=False, message=f"Failed: {result.error}", error=result.error)
    except Exception as e:
        return CommandResult(ok=False, message=f"Error: {e}", error=str(e))


def _cmd_ui_create_victory_screen(_: dict) -> CommandResult:
    try:
        from gmm.ui.victory_screen import create_victory_screen_widget
        result = create_victory_screen_widget()
        if result.ok:
            return CommandResult(
                ok=True,
                message=f"Created victory screen widget: {result.path}",
                outputs={"path": result.path},
            )
        return CommandResult(ok=False, message=f"Failed: {result.error}", error=result.error)
    except Exception as e:
        return CommandResult(ok=False, message=f"Error: {e}", error=str(e))


def _cmd_battle_end(_: dict) -> CommandResult:
    global _BATTLE_HARNESS
    harness = _get_harness()
    result = harness.end_encounter()
    _BATTLE_HARNESS = None
    return CommandResult(ok=True, message="Encounter ended. Harness reset.", outputs=result)


# ------------------------------------------------------------------
# Game Runtime Commands
# ------------------------------------------------------------------

def _cmd_game_run(params: dict) -> CommandResult:
    """Launch the interactive CLI battle game."""
    enemy_id = params.get("enemy_id", "")
    if enemy_id:
        from gmm.main import run_quick_battle
        import sys
        old = sys.argv
        sys.argv = ["gmm", "--battle", enemy_id]
        try:
            exit_code = run_quick_battle(enemy_id)
            return CommandResult(ok=exit_code == 0,
                                 message=f"Battle vs {enemy_id} completed (exit {exit_code})")
        finally:
            sys.argv = old
    else:
        from gmm.main import run_game_loop
        import sys
        old = sys.argv
        sys.argv = ["gmm"]
        exit_code = run_game_loop()
        sys.argv = old
        return CommandResult(ok=True, message="Game loop exited")


def _cmd_game_config(_: dict) -> CommandResult:
    from gmm.game.config import GAME_CFG
    cfg = GAME_CFG.to_dict()
    return CommandResult(ok=True, message="Game config loaded", outputs=cfg)


def _cmd_game_save(params: dict) -> CommandResult:
    from gmm.game.player_state import MelodiaPlayerState
    from gmm.game.save_manager import SaveManager
    action = params.get("action", "save")
    sm = SaveManager()
    ps = MelodiaPlayerState()
    sm.load(ps)

    if action == "save":
        path = sm.save(ps)
        return CommandResult(ok=True, message=f"Saved to {path}", outputs={"path": path})
    elif action == "load":
        ok = sm.load(ps)
        desc = ps.describe()
        return CommandResult(ok=ok,
                             message=f"Loaded Lv.{ps.level} HP:{ps.hp:.0f}" if ok else "No save found",
                             outputs=desc)
    elif action == "list":
        slots = sm.list_slots()
        return CommandResult(ok=True,
                             message=f"{len(slots)} save slot(s)",
                             outputs={"slots": slots, "save_dir": sm.save_dir})
    elif action == "delete":
        slot = params.get("slot", sm.slot_name)
        ok = sm.delete_slot(slot)
        return CommandResult(ok=ok, message=f"Deleted '{slot}'" if ok else f"Slot '{slot}' not found")
    return CommandResult(ok=False, message=f"Unknown action '{action}'")


def _cmd_game_player_status(_: dict) -> CommandResult:
    from gmm.game.player_state import MelodiaPlayerState
    from gmm.game.save_manager import SaveManager
    ps = MelodiaPlayerState()
    sm = SaveManager()
    sm.load(ps)
    desc = ps.describe()
    return CommandResult(ok=True, message=f"Lv.{ps.level} {ps.hp:.0f}/{ps.max_hp:.0f}HP",
                         outputs=desc)


def _cmd_game_equipment(params: dict) -> CommandResult:
    from gmm.game.equipment_catalog import list_equipment, get_equipment, catalog_summary
    slot = params.get("slot", "")
    equip_id = params.get("item_id", "")
    if equip_id:
        item = get_equipment(equip_id)
        if not item:
            return CommandResult(ok=False, message=f"Unknown item '{equip_id}'")
        return CommandResult(ok=True, message=f"{item.display_name} ({item.slot})", outputs=item.to_dict())
    items = list_equipment(slot)
    summary = catalog_summary()
    return CommandResult(ok=True,
                         message=f"{summary['total']} items ({summary['by_slot']})",
                         outputs={"items": items, "summary": summary})


def _cmd_game_audio(params: dict) -> CommandResult:
    from gmm.game.audio_engine import AudioEngine
    ae = AudioEngine()
    action = params.get("action", "status")
    if action == "toggle":
        state = ae.toggle()
        return CommandResult(ok=True, message=f"Audio {'ON' if state else 'OFF'}")
    return CommandResult(ok=True, message=f"Audio {'ON' if ae.enabled else 'OFF'}",
                         outputs=ae.describe())


_ACTIVE_STACKS: dict[str, Any] = {}

def _cmd_settings_get(params: dict) -> CommandResult:
    from gmm.core.settings import GmmSettings
    settings = GmmSettings()
    key = params.get("key", "")
    if key:
        val = settings.get(key)
        return CommandResult(ok=True, message=f"{key} = {val}", outputs={key: val})
    return CommandResult(ok=True, message="All settings loaded", outputs=settings.data)


def _cmd_settings_set(params: dict) -> CommandResult:
    from gmm.core.settings import GmmSettings
    settings = GmmSettings()
    key = params.get("key", "")
    value = params.get("value", None)
    if not key or value is None:
        return CommandResult(ok=False, message="Missing key or value", error="missing_args")
    ok = settings.set(key, value)
    if ok:
        return CommandResult(ok=True, message=f"Set {key} to {value}", outputs={key: value})
    else:
        return CommandResult(ok=False, message=f"Failed to set {key}", error="set_failed")


def _cmd_modifiers_summary(_: dict) -> CommandResult:
    from gmm.game.modifiers import modifier_registry_summary
    summary = modifier_registry_summary()
    return CommandResult(ok=True, message=f"Registered modifiers: {', '.join(summary['ids'])}", outputs=summary)


def _cmd_modifiers_stack(params: dict) -> CommandResult:
    from gmm.game.modifiers import ModifierStack
    unit = params.get("unit", "Player")
    action = params.get("action", "view")

    if unit not in _ACTIVE_STACKS:
        _ACTIVE_STACKS[unit] = ModifierStack()

    stack = _ACTIVE_STACKS[unit]

    if action == "view":
        snap = stack.snapshot()
        return CommandResult(ok=True, message=f"Unit '{unit}' has {len(snap)} active modifiers", outputs={"active": snap})
    elif action == "add":
        mod_id = params.get("modifier_id", "")
        if not mod_id:
            return CommandResult(ok=False, message="Missing modifier_id", error="missing_modifier_id")
        ok = stack.add(mod_id)
        snap = stack.snapshot()
        return CommandResult(ok=ok, message=f"Added '{mod_id}' to '{unit}'" if ok else f"Failed to add '{mod_id}' (limit reached or invalid)", outputs={"active": snap})
    elif action == "tick":
        stack.tick_turn()
        snap = stack.snapshot()
        return CommandResult(ok=True, message=f"Ticked modifiers for '{unit}'", outputs={"active": snap})
    elif action == "clear":
        stack.clear()
        return CommandResult(ok=True, message=f"Cleared modifiers for '{unit}'", outputs={"active": []})
    elif action == "evaluate":
        stat = params.get("stat", "")
        base_value = float(params.get("base_value", 100.0))
        if not stat:
            return CommandResult(ok=False, message="Missing stat to evaluate", error="missing_stat")
        res = stack.evaluate(stat, base_value)
        return CommandResult(ok=True, message=f"Evaluated {stat}: {base_value} -> {res}", outputs={"stat": stat, "base": base_value, "result": res})

    return CommandResult(ok=False, message=f"Unknown action '{action}'", error="invalid_action")


# Geometry Modifier Commands

def _cmd_geometry_modifier_stack(params: dict) -> CommandResult:
    """Validate/serialize a modifier stack without requiring Unreal."""
    from gmm.geometry.modifiers import GeometryModifier, ModifierStack

    stack = ModifierStack(str(params.get("target", "")))
    for raw in params.get("modifiers", []):
        if not isinstance(raw, dict):
            return CommandResult(False, "Each modifier must be an object", error="invalid_modifier")
        try:
            stack.add(GeometryModifier(
                modifier_id=str(raw.get("id", "")),
                modifier_type=str(raw.get("type", "")),
                enabled=bool(raw.get("enabled", True)),
                scope=str(raw.get("scope", "editor")),
                backend=str(raw.get("backend", "auto")),
                parameters=dict(raw.get("parameters", {})),
            ))
        except (TypeError, ValueError) as exc:
            return CommandResult(False, f"Modifier stack validation failed: {exc}", error="invalid_stack")
    errors = stack.validate()
    if errors:
        return CommandResult(False, "Modifier stack failed validation", outputs={"errors": errors}, error="invalid_stack")
    if params.get("preview", False):
        from gmm.geometry.sessions import SESSIONS
        session_id = str(params.get("session_id") or f"preview:{stack.target}")
        try:
            session = SESSIONS.create(stack, session_id)
        except (TypeError, ValueError) as exc:
            return CommandResult(False, "Preview session rejected", error=str(exc))
        return CommandResult(True, "Modifier stack preview session created", outputs=session.to_dict())
    return CommandResult(True, "Modifier stack validated", outputs=stack.to_dict())


def _cmd_geometry_commit_preview(params: dict) -> CommandResult:
    from gmm.geometry.sessions import SESSIONS
    try:
        session = SESSIONS.transition(str(params.get("session_id", "")), "committed")
        return CommandResult(True, "Preview committed", outputs=session.to_dict())
    except (KeyError, ValueError) as exc:
        return CommandResult(False, "Preview commit rejected", error=str(exc))


def _cmd_geometry_bake(params: dict) -> CommandResult:
    from gmm.geometry.sessions import SESSIONS
    if params.get("confirm") is not True:
        return CommandResult(False, "Bake requires explicit confirmation", error="bake_confirmation_required")
    try:
        session = SESSIONS.transition(str(params.get("session_id", "")), "baked")
        return CommandResult(True, "Preview baked", outputs=session.to_dict())
    except (KeyError, ValueError) as exc:
        return CommandResult(False, "Bake rejected", error=str(exc))


def _cmd_geometry_clear_preview(params: dict) -> CommandResult:
    from gmm.geometry.sessions import SESSIONS
    try:
        result = SESSIONS.clear(str(params.get("session_id", "")))
        return CommandResult(True, "Preview cleared", outputs=result)
    except (KeyError, ValueError) as exc:
        return CommandResult(False, "Preview clear rejected", error=str(exc))


def _cmd_geometry_capabilities(_: dict) -> CommandResult:
    from gmm.geometry.ue_adapter import capabilities
    result = capabilities()
    error = result.get("error")
    return CommandResult(
        bool(result.get("ok")),
        "Geometry capabilities discovered" if result.get("ok") else "Geometry capabilities unavailable",
        outputs=result,
        error=str(error) if error else None,
    )


def _cmd_geometry_describe_actor(params: dict) -> CommandResult:
    from gmm.geometry.ue_adapter import describe_actor
    result = describe_actor(str(params.get("actor_path", "")))
    error = result.get("error")
    return CommandResult(
        bool(result.get("ok")),
        "Actor inspected" if result.get("ok") else "Actor inspection unavailable",
        outputs=result,
        error=str(error) if error else None,
    )


def _cmd_geometry_describe_target(params: dict) -> CommandResult:
    from gmm.geometry.ue_adapter import describe_target
    result = describe_target(str(params.get("asset_path", "")))
    error = result.get("error")
    return CommandResult(bool(result.get("ok")), "Target inspected" if result.get("ok") else "Target inspection unavailable", outputs=result, error=str(error) if error else None)


def _cmd_geometry_bevel_preview(params: dict) -> CommandResult:
    from gmm.geometry.schemas import BEVEL_DEFAULTS, validate_bevel_parameters
    from gmm.geometry.ue_adapter import preview_bevel

    values = dict(BEVEL_DEFAULTS)
    values.update(params.get("parameters", {}))
    errors = validate_bevel_parameters(values)
    if errors:
        return CommandResult(False, "Invalid bevel parameters", outputs={"errors": errors}, error="invalid_bevel")
    result = preview_bevel(
        str(params.get("asset_path", "")),
        values,
        preview_actor=str(params.get("preview_actor", "")),
    )
    error = result.get("error")
    return CommandResult(bool(result.get("ok")), "Bevel preview applied" if result.get("ok") else "Bevel preview unavailable", outputs=result, error=str(error) if error else None)


def _cmd_geometry_reset_preview(params: dict) -> CommandResult:
    from gmm.geometry.ue_adapter import reset_preview
    result = reset_preview(str(params.get("preview_actor", "")))
    error = result.get("error")
    return CommandResult(bool(result.get("ok")), "Preview reset" if result.get("ok") else "Preview reset unavailable", outputs=result, error=str(error) if error else None)


# NPC Pipeline Commands

def _cmd_npc_vrm4u_capabilities(_: dict) -> CommandResult:
    from gmm.npc.vrm4u_import import vrm4u_capabilities
    result = vrm4u_capabilities()
    error = result.get("error")
    return CommandResult(
        bool(result.get("ok")),
        "VRM4U is ready" if result.get("ok") else "VRM4U is unavailable",
        outputs=result,
        error=str(error) if error else None,
    )


def _cmd_npc_import_vrms(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_generate_palettes(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_create_materials(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_setup_cloth(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_generate_lods(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_battle_integration(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_populate_level(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_audit(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


def _cmd_npc_registry_status(_: dict) -> CommandResult:
    return CommandResult(ok=True, data={"status": "NPC registry not initialized", "count": 0})


def _cmd_npc_full_pipeline(params: dict) -> CommandResult:
    return CommandResult(ok=False, error="Not implemented in standalone build")


# ------------------------------------------------------------------
# Roguelike Commands
# ------------------------------------------------------------------

def _cmd_roguelike_room_templates(_: dict) -> CommandResult:
    from gmm.game.roguelike import ROOM_TEMPLATES, run_roguelike_summary
    summary = run_roguelike_summary()
    templates = [{k: v.to_dict()} for k, v in ROOM_TEMPLATES.items()]
    return CommandResult(ok=True, message=f"Room templates: {summary['room_ids']}", outputs={"templates": templates, "summary": summary})


def _cmd_roguelike_artifacts(_: dict) -> CommandResult:
    from gmm.game.roguelike import ARTIFACTS
    artifacts = [a.to_dict() for a in ARTIFACTS.values()]
    return CommandResult(ok=True, message=f"Artifacts: {list(ARTIFACTS.keys())}", outputs={"artifacts": artifacts})


def _cmd_roguelike_blessings(_: dict) -> CommandResult:
    from gmm.game.roguelike import BLESSINGS
    blessings = [b.to_dict() for b in BLESSINGS.values()]
    total_cost = sum(b.token_cost for b in BLESSINGS.values())
    return CommandResult(ok=True, message=f"Blessings: {list(BLESSINGS.keys())} (total cost: {total_cost})", outputs={"blessings": blessings})


def _cmd_roguelike_generate_floor(params: dict) -> CommandResult:
    from gmm.game.roguelike import generate_floor
    floor = int(params.get("floor", 1))
    seed = int(params.get("seed", 0))
    rooms = generate_floor(floor, seed)
    return CommandResult(ok=True, message=f"Generated floor {floor}: {rooms}", outputs={"floor": floor, "rooms": rooms})


def _cmd_roguelike_setup(_: dict) -> CommandResult:
    from gmm.game.roguelike import run_roguelike_summary
    import setup_roguelike
    result = setup_roguelike.build_roguelike_setup()
    return CommandResult(ok=True, message=f"Roguelike setup complete. See next_steps.", outputs=result)


# ------------------------------------------------------------------
# Interaction Commands
# ------------------------------------------------------------------

def _cmd_interact_door(params: dict) -> CommandResult:
    """Test door interaction system."""
    from gmm.game.interaction import (
        InteractionManager, InteractableType, InteractionResult
    )
    door_id = params.get("door_id", "test_door")
    result = InteractionManager.interact("player", door_id)
    return CommandResult(
        ok=result.result == InteractionResult.SUCCESS,
        message=f"Door '{door_id}': {result.result.name}",
        outputs=result.interaction_data,
    )


def _cmd_interact_harvest(params: dict) -> CommandResult:
    """Test harvest node interaction system."""
    from gmm.game.interaction import (
        InteractionManager, InteractableType, HarvestNode, InteractionResult
    )
    node_id = params.get("node_id", "test_node")
    resource_type = params.get("resource_type", "golden_token")
    amount = int(params.get("amount", 1))
    
    InteractionManager.register_interactable(
        node_id, InteractableType.HARVEST_NODE,
        interaction_data={"node_id": node_id, "resource_type": resource_type, "amount": amount}
    )
    result = InteractionManager.interact("player", node_id)
    return CommandResult(
        ok=result.result == InteractionResult.SUCCESS,
        message=f"Harvest '{node_id}': {result.result.name} ({resource_type} x{amount})",
        outputs=result.interaction_data,
    )


def _cmd_interaction_summary(_: dict) -> CommandResult:
    """Get interaction system summary."""
    from gmm.game.interaction import interaction_system_summary, add_interact_binding_to_input_config
    summary = interaction_system_summary()
    summary["f_key_binding"] = add_interact_binding_to_input_config()
    return CommandResult(ok=True, message="Interaction system ready", outputs=summary)


# ------------------------------------------------------------------
# Party Commands
# ------------------------------------------------------------------

def _cmd_party_summary(_: dict) -> CommandResult:
    """Get party system summary."""
    from gmm.game.party import party_system_summary
    summary = party_system_summary()
    return CommandResult(ok=True, message="Party system ready", outputs=summary)


def _cmd_party_create_companion(params: dict) -> CommandResult:
    """Create a companion for testing."""
    from gmm.game.party import create_companion, Party
    companion_id = params.get("companion_id", "companion_01")
    archetype = params.get("archetype", "SakuraDreamer")
    level = int(params.get("level", 1))
    
    companion = create_companion(companion_id, archetype, level)
    if not companion:
        return CommandResult(ok=False, message=f"Unknown archetype: {archetype}")
    
    return CommandResult(
        ok=True,
        message=f"Created {archetype} (Lv.{level}): {companion_id}",
        outputs=companion.to_dict(),
    )


# ------------------------------------------------------------------
# Agent Bridge Commands
# ------------------------------------------------------------------

def _cmd_agent_status(_: dict) -> CommandResult:
    """Get status of all agents or specific agent."""
    from pathlib import Path
    project_root = Path(__file__).resolve().parents[3]
    
    agents = {
        "geometry": {"status": "ready", "icon": "🏛️"},
        "material": {"status": "ready", "icon": "🎨"},
        "placement": {"status": "ready", "icon": "📍"},
        "integration": {"status": "ready", "icon": "🔗"},
        "qa": {"status": "ready", "icon": "🛡️"},
    }
    
    # Check for loop stop files
    loop_stops = {
        "geometry": project_root / "deploy" / "SURREAL_ARCH_LOOP_STOP",
        "integration": project_root / "deploy" / "SURREAL_WORLD_LOOP_STOP",
    }
    
    for agent, stop_file in loop_stops.items():
        if stop_file.exists():
            agents[agent]["status"] = "stopped"
    
    msg = ", ".join(f"{v['icon']} {k}: {v['status']}" for k, v in agents.items())
    return CommandResult(ok=True, message=f"Agent Status: {msg}", outputs=agents)


def _cmd_agent_blessing_evolution(params: dict) -> CommandResult:
    """Queue blessing evolution request for processing."""
    from pathlib import Path
    from datetime import datetime
    
    project_root = Path(__file__).resolve().parents[3]
    agent_memory_dir = project_root / "Saved" / "AgentMemory"
    evolution_queue = agent_memory_dir / "blessing_evolution_queue.json"
    
    target_count = int(params.get("target_count", 5))
    element_focus = params.get("element_focus")
    
    evolution_context = {
        "target_count": target_count,
        "element_focus": element_focus,
        "timestamp": datetime.now().isoformat(),
    }
    
    agent_memory_dir.mkdir(parents=True, exist_ok=True)
    
    queue = []
    if evolution_queue.exists():
        try:
            queue = json.loads(evolution_queue.read_text())
        except Exception:
            pass
    
    queue.append(evolution_context)
    evolution_queue.write_text(json.dumps(queue, indent=2))
    
    return CommandResult(
        ok=True,
        message=f"Blessing evolution queued for {target_count} blessings (element: {element_focus or 'all'})",
        outputs={"queued": evolution_context}
    )


def _cmd_agent_delegate(params: dict) -> CommandResult:
    """Delegate to a specific agent by intent."""
    intent = params.get("intent", "")
    action = params.get("action", "")
    
    if not intent:
        return CommandResult(ok=False, message="Missing intent (geometry/material/placement/integration/audit/blessing)")
    
    # Map to appropriate subsystem
    intent_map = {
        "geometry": "surreal",
        "material": "material",
        "placement": "pcg",
        "integration": "integration",
        "audit": "audit",
        "blessing": "blessing",
    }
    
    subsystem = intent_map.get(intent, "unknown")
    msg = f"Delegated to {subsystem} agent: {action}"
    
    return CommandResult(ok=True, message=msg, outputs={"intent": intent, "action": action, "subsystem": subsystem})


def run_gmm(command_id: str, params: dict) -> CommandResult:
    """Dispatch function for envui.menu reference."""
    cmd_fn = GMM_COMMANDS.get(command_id)
    if not cmd_fn:
        return CommandResult(ok=False, message=f"Unknown GMM command: {command_id}", error="unknown_command")
    _, fn = cmd_fn
    return fn(params)


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------

GMM_COMMANDS: dict[str, tuple[str, Callable]] = {
    "gmm.interact.door": (GMM_SECTION, _cmd_interact_door),
    "gmm.interact.harvest": (GMM_SECTION, _cmd_interact_harvest),
    "gmm.interact.summary": (GMM_SECTION, _cmd_interaction_summary),
    "gmm.party.summary": (GMM_SECTION, _cmd_party_summary),
    "gmm.party.create": (GMM_SECTION, _cmd_party_create_companion),
    "gmm.about": (GMM_SECTION, _cmd_about),
    "gmm.mcp_status": (GMM_SECTION, _cmd_mcp_status),
    "gmm.mcp_discover": (GMM_SECTION, _cmd_mcp_discover),
    "gmm.run_python": (GMM_SECTION, _cmd_run_python),
    "gmm.settings.get": (GMM_SECTION, _cmd_settings_get),
    "gmm.settings.set": (GMM_SECTION, _cmd_settings_set),
    "gmm.modifiers.summary": (GMM_SECTION, _cmd_modifiers_summary),
    "gmm.modifiers.stack": (GMM_SECTION, _cmd_modifiers_stack),
    "gmm.geometry.modifier_stack": (GMM_SECTION, _cmd_geometry_modifier_stack),
    "gmm.geometry.commit_preview": (GMM_SECTION, _cmd_geometry_commit_preview),
    "gmm.geometry.bake": (GMM_SECTION, _cmd_geometry_bake),
    "gmm.geometry.clear_preview": (GMM_SECTION, _cmd_geometry_clear_preview),
    "gmm.geometry.capabilities": (GMM_SECTION, _cmd_geometry_capabilities),
    "gmm.geometry.describe_actor": (GMM_SECTION, _cmd_geometry_describe_actor),
    "gmm.geometry.describe_target": (GMM_SECTION, _cmd_geometry_describe_target),
    "gmm.geometry.bevel_preview": (GMM_SECTION, _cmd_geometry_bevel_preview),
    "gmm.geometry.reset_preview": (GMM_SECTION, _cmd_geometry_reset_preview),
    "gmm.melodia.enemies": (GMM_SECTION, _cmd_melodia_enemies),
    "gmm.melodia.skills": (GMM_SECTION, _cmd_melodia_skills),
    "gmm.melusina.rig_assess": (GMM_SECTION, _cmd_melusina_rig_assess),
    "gmm.melusina.blend_setup": (GMM_SECTION, _cmd_melusina_blend_setup),
    "gmm.melusina.bp_setup": (GMM_SECTION, _cmd_melusina_bp_setup),
    "gmm.surreal.escher": (GMM_SECTION, _cmd_surreal_escher),
    "gmm.surreal.proc_arch": (GMM_SECTION, _cmd_surreal_proc_arch),
    "gmm.pcg.preflight": (GMM_SECTION, _cmd_pcg_preflight),
    "gmm.pcg.repair_quarantine": (GMM_SECTION, _cmd_pcg_repair_quarantine),
    "gmm.pcg.manifest": (GMM_SECTION, _cmd_pcg_manifest),
    "gmm.pcg.release_gate": (GMM_SECTION, _cmd_pcg_release_gate),
    "gmm.mkc.verify_all": (GMM_SECTION, _cmd_mkc_verify_all),
    "gmm.battle.test_encounter": (GMM_SECTION, _cmd_battle_test_encounter),
    "gmm.battle.state": (GMM_SECTION, _cmd_battle_state),
    "gmm.battle.command": (GMM_SECTION, _cmd_battle_command),
    "gmm.battle.end": (GMM_SECTION, _cmd_battle_end),
    "gmm.ui.title_menu": (GMM_SECTION, _cmd_ui_title_menu),
    "gmm.ui.save_slots": (GMM_SECTION, _cmd_ui_save_slots),
    "gmm.ui.battle_menu": (GMM_SECTION, _cmd_ui_create_battle_menu),
    "gmm.ui.victory_screen": (GMM_SECTION, _cmd_ui_create_victory_screen),
    "gmm.ui.battle_gui": (GMM_SECTION, _cmd_ui_battle_gui),
    "gmm.game.run": (GMM_SECTION, _cmd_game_run),
    "gmm.game.config": (GMM_SECTION, _cmd_game_config),
    "gmm.game.save": (GMM_SECTION, _cmd_game_save),
    "gmm.game.player_status": (GMM_SECTION, _cmd_game_player_status),
    "gmm.game.equipment": (GMM_SECTION, _cmd_game_equipment),
    "gmm.game.audio": (GMM_SECTION, _cmd_game_audio),
    # Agent Bridge Commands
    "gmm.agent.status": (GMM_SECTION, _cmd_agent_status),
    "gmm.agent.blessing_evolution": (GMM_SECTION, _cmd_agent_blessing_evolution),
    "gmm.agent.delegate": (GMM_SECTION, _cmd_agent_delegate),
    # NPC Pipeline Commands
    "gmm.npc.vrm4u_capabilities": (GMM_SECTION, _cmd_npc_vrm4u_capabilities),
    "gmm.npc.import_vrms": (GMM_SECTION, _cmd_npc_import_vrms),
    "gmm.npc.palettes": (GMM_SECTION, _cmd_npc_generate_palettes),
    "gmm.npc.materials": (GMM_SECTION, _cmd_npc_create_materials),
    "gmm.npc.cloth": (GMM_SECTION, _cmd_npc_setup_cloth),
    "gmm.npc.lods": (GMM_SECTION, _cmd_npc_generate_lods),
    "gmm.npc.battle": (GMM_SECTION, _cmd_npc_battle_integration),
    "gmm.npc.populate": (GMM_SECTION, _cmd_npc_populate_level),
    "gmm.npc.audit": (GMM_SECTION, _cmd_npc_audit),
    "gmm.npc.status": (GMM_SECTION, _cmd_npc_registry_status),
    "gmm.npc.full_pipeline": (GMM_SECTION, _cmd_npc_full_pipeline),
    # Roguelike Commands
    "gmm.roguelike.room_templates": (GMM_SECTION, _cmd_roguelike_room_templates),
    "gmm.roguelike.artifacts": (GMM_SECTION, _cmd_roguelike_artifacts),
    "gmm.roguelike.blessings": (GMM_SECTION, _cmd_roguelike_blessings),
    "gmm.roguelike.generate_floor": (GMM_SECTION, _cmd_roguelike_generate_floor),
    "gmm.roguelike.setup": (GMM_SECTION, _cmd_roguelike_setup),
}
