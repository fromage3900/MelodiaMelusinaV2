"""UE editor startup: load Blender Live Link client and register menus."""
import importlib.util
import os
import sys

import unreal

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_OWNER = "BSGodFile_LiveLink"


def _py_path_prefix():
    project_python = _SCRIPT_DIR.replace("\\", "/")
    return (
        f"import sys; import unreal; p=r'{project_python}'; "
        f"sys.path.insert(0,p) if p not in sys.path else None; "
        f"import livelink_unreal; "
    )


def _menu_command(py_body: str) -> str:
    return (
        _py_path_prefix()
        + "try:\n "
        + py_body
        + "\nexcept Exception as _ll_exc:\n "
        + " unreal.log_error('[LiveLink] Menu action failed: ' + str(_ll_exc))"
    )


def register_livelink_menus():
    menus = unreal.ToolMenus.get()
    main = menus.find_menu("LevelEditor.MainMenu")
    if not main:
        unreal.log_warning("[LiveLink] LevelEditor.MainMenu not found")
        return

    for stale in (
        "LevelEditor.MainMenu.LiveLink.BlenderLiveLink",
        "LevelEditor.MainMenu.LiveLink",
    ):
        if menus.find_menu(stale):
            menus.remove_menu(stale)

    main.add_sub_menu(_OWNER, "LiveLink", "LiveLink", "LiveLink", "Live Link")
    live = menus.extend_menu("LevelEditor.MainMenu.LiveLink")
    live.add_section("Connection", "Connection")
    live.add_section("Portfolio", "Portfolio")
    live.add_section("Help", "Help")

    def add_entry(menu, section, name, label, py_body):
        entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label(label)
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            unreal.Name(""),
            _menu_command(py_body),
        )
        menu.add_menu_entry(section, entry)

    # Primary actions on LiveLink (one click fewer than nested submenu)
    add_entry(
        live,
        "Connection",
        "StartLL",
        "Start Live Link (connect to Blender)",
        "livelink_unreal.start_connection(); "
        "unreal.log('[LiveLink] Start requested — check Output Log for Connected/Error')",
    )
    add_entry(live, "Connection", "StopLL", "Stop Live Link", "livelink_unreal.stop_connection()")
    add_entry(
        live,
        "Connection",
        "StatusLL",
        "Show Status",
        "unreal.log('[LiveLink] ' + livelink_unreal.get_status())",
    )
    add_entry(
        live,
        "Portfolio",
        "RunSakuraPCG",
        "Run Sakura PCG (showcase wrapper)",
        "import setup_pcg_sakura; "
        "report = setup_pcg_sakura.build_all(rebuild=True, spawn=True); "
        "unreal.log('[Portfolio] Sakura PCG passed=' + str(report.get('passed')))",
    )
    add_entry(
        live,
        "Portfolio",
        "RunUniversalPCG",
        "Run Universal PCG Build",
        "import setup_pcg_universal; "
        "report = setup_pcg_universal.build_all(force=True); "
        "unreal.log('[Portfolio] Universal PCG passed=' + str(report.get('passed')))",
    )
    add_entry(
        live,
        "Portfolio",
        "RunGreyboxPCG",
        "Apply Greybox PCG (Template minimal)",
        "import setup_pcg_greybox; "
        "import pcg_portfolio_standards as s; "
        "r = setup_pcg_greybox.apply_greybox_pcg(s.LEVEL_TEMPLATE, preset='minimal'); "
        "unreal.log('[Portfolio] Greybox PCG passed=' + str(r.get('passed')))",
    )
    add_entry(
        live,
        "Portfolio",
        "AuditPCGPortfolio",
        "Audit PCG Portfolio",
        "import audit_pcg_portfolio; "
        "r = audit_pcg_portfolio._audit_in_ue(); "
        "unreal.log('[Portfolio] PCG audit clean=' + str(r.get('clean')))",
    )
    add_entry(
        live,
        "Portfolio",
        "RunSakuraNiagara",
        "Run Sakura Dream Niagara (full plan)",
        "import run_sakura_niagara_plan; "
        "report = run_sakura_niagara_plan.run_plan(rebuild=False); "
        "unreal.log('[Portfolio] Sakura Niagara all_ok=' + str(report.get('all_ok')))",
    )
    add_entry(
        live,
        "Portfolio",
        "RunOrchestratorTick",
        "Portfolio Orchestrator Tick (10m loop step)",
        "import run_portfolio_orchestrator_loop_tick; "
        "code = run_portfolio_orchestrator_loop_tick.main(); "
        "unreal.log('[Portfolio] Orchestrator exit=' + str(code))",
    )
    add_entry(
        live,
        "Portfolio",
        "CapturePortfolioOutputs",
        "Capture Portfolio Outputs (screenshots + previews + metadata)",
        "import export_screenshot, capture_material_previews, capture_scene_metadata; "
        "ss = export_screenshot.capture_screenshot(); "
        "mp = capture_material_previews.capture_material_previews(); "
        "md = capture_scene_metadata.capture_scene_metadata(); "
        "unreal.log('[Portfolio] Capture complete: ' + str({'screenshot': ss.get('ok'), 'materials': mp.get('count'), 'metadata': md.get('ok')}))",
    )
    add_entry(
        live,
        "Portfolio",
        "RunSakuraNiagaraRebuild",
        "Run Sakura Dream Niagara (--rebuild)",
        "import run_sakura_niagara_plan; "
        "report = run_sakura_niagara_plan.run_plan(rebuild=True); "
        "unreal.log('[Portfolio] Sakura Niagara all_ok=' + str(report.get('all_ok')))",
    )
    add_entry(
        live,
        "Help",
        "HelpLL",
        "How to use (no UE panel)",
        "unreal.log_warning("
        "'[LiveLink] No UE window opens. Order: Blender N-panel > Start Live Link, "
        "then UE LiveLink > Start Live Link, then Blender > Send Full Scene. "
        "Imports: /Game/LiveLink/')",
    )
    # Agent Bridge Commands
    add_entry(
        live,
        "Portfolio",
        "AgentStatus",
        "Agent Status (🏛️🎨📍🔗🛡️)",
        "import gmm.ui.commands as cmds; "
        "r = cmds.run_gmm('gmm.agent.status', {}); "
        "unreal.log('[AgentBridge] ' + r.message)",
    )
    add_entry(
        live,
        "Portfolio",
        "RunBlessingEvolution",
        "Generate Blessings (Ollama)",
        "import gmm.ui.commands as cmds; "
        "r = cmds.run_gmm('gmm.agent.blessing_evolution', {'target_count': 5}); "
        "unreal.log('[AgentBridge] ' + r.message)",
    )
    add_entry(
        live,
        "Portfolio",
        "DelegateToGeometry",
        "Delegate: Geometry (list genomes)",
        "import gmm.ui.commands as cmds; "
        "r = cmds.run_gmm('gmm.agent.delegate', {'intent': 'geometry', 'action': 'list_genomes'}); "
        "unreal.log('[AgentBridge] ' + r.message)",
    )
    add_entry(
        live,
        "Portfolio",
        "DelegateToMaterial",
        "Delegate: Material (build universal)",
        "import gmm.ui.commands as cmds; "
        "r = cmds.run_gmm('gmm.agent.delegate', {'intent': 'material', 'action': 'build_universal'}); "
        "unreal.log('[AgentBridge] ' + r.message)",
    )

    menus.refresh_all_widgets()
    unreal.log(
        "[LiveLink] Menu ready — LiveLink > Start Live Link "
        "(dropdown only; no floating panel)"
    )


if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def _load_livelink_module():
    for name in ("livelink_unreal.py", "livelink_unreal.pyc"):
        path = os.path.join(_SCRIPT_DIR, name)
        if not os.path.isfile(path):
            continue
        spec = importlib.util.spec_from_file_location("livelink_unreal", path)
        if not spec or not spec.loader:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules["livelink_unreal"] = mod
        spec.loader.exec_module(mod)
        mod.register_menus = register_livelink_menus
        return mod
    unreal.log_error(
        "[LiveLink] Missing Content/Python/livelink_unreal.py or .pyc — "
        "copy from your 3DRedbox purchase, restart UE"
    )
    return None


m = _load_livelink_module()


def _register_osc_bridge() -> None:
    """Start the TD-UE OSC bridge on editor startup."""
    print("[TD-Bridge] Attempting OSC bridge start...", flush=True)
    try:
        from osc_server import start_bridge
        if start_bridge(port=8000):
            print("[TD-Bridge] OSC bridge STARTED on port 8000 (raw socket)", flush=True)
            unreal.log("[TD-Bridge] OSC bridge started on port 8000 (raw socket)")
    except Exception as e:
        print(f"[TD-Bridge] OSC bridge FAILED: {e}", flush=True)
        unreal.log_error(f"[TD-Bridge] OSC bridge failed: {e}")


def _register_gmm() -> None:
    """Register GMM menus on editor startup."""
    print("[GMM] Attempting GMM menu registration...", flush=True)
    try:
        from gmm.ui.register import register_gmm_menus
        register_gmm_menus()
        print("[GMM] Menus REGISTERED", flush=True)
        unreal.log("[GMM] Grandmaster Melodia Melusina menus registered")
    except Exception as e:
        print(f"[GMM] Registration FAILED: {e}", flush=True)
        unreal.log_error(f"[GMM] Registration failed: {e}")


def _register_agent_bridge() -> None:
    """Register agent bridge panel in UE editor."""
    print("[AgentBridge] Attempting agent bridge registration...", flush=True)
    try:
        from agent_status_panel import register_agent_panel, log_agent_status
        register_agent_panel()
        print("[AgentBridge] Agent bridge REGISTERED", flush=True)
        unreal.log("[AgentBridge] Agent bridge panel registered in LiveLink menu")
    except Exception as e:
        print(f"[AgentBridge] Registration FAILED: {e}", flush=True)
        unreal.log_error(f"[AgentBridge] Registration failed: {e}")


def _register_world_compiler() -> None:
    """Apply/Cleanup/Capture only. Compile stays CLI."""
    try:
        menus = unreal.ToolMenus.get()
        main = menus.find_menu("LevelEditor.MainMenu")
        if not main:
            return
        owner = "BSGodFile_WorldCompiler"
        if menus.find_menu("LevelEditor.MainMenu.WorldCompiler"):
            menus.remove_menu("LevelEditor.MainMenu.WorldCompiler")
        main.add_sub_menu(owner, "WorldCompiler", "WorldCompiler", "World Compiler", "World Compiler")
        menu = menus.extend_menu("LevelEditor.MainMenu.WorldCompiler")
        menu.add_section("Apply", "Apply")
        menu.add_section("Foundry", "Foundry")
        hint = (
            "unreal.log('[WorldCompiler] Compile is CLI: python Tools/world_compiler.py "
            "compile recipes/morning_rainbow_bloom.v1.json && python Tools/world_compiler_ue_driver.py "
            "Saved/WorldCompiler/morning_rainbow_bloom_3900 --lookdev')"
        )
        py_dir = _SCRIPT_DIR.replace("\\", "/")

        def add(name, label, body):
            entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
            entry.set_label(label)
            entry.set_string_command(
                unreal.ToolMenuStringCommandType.PYTHON,
                unreal.Name(""),
                f"import sys; p=r'{py_dir}'; sys.path.insert(0,p) if p not in sys.path else None; "
                f"import world_compiler_panel as wcp; {body}",
            )
            menu.add_menu_entry("Apply", entry)

        def add_foundry(name, label, body):
            entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
            entry.set_label(label)
            entry.set_string_command(
                unreal.ToolMenuStringCommandType.PYTHON,
                unreal.Name(""),
                f"import sys; p=r'{py_dir}'; sys.path.insert(0,p) if p not in sys.path else None; "
                f"import unreal; import foundry_converged_panel as fcp; {body}",
            )
            menu.add_menu_entry("Foundry", entry)

        add("WCHint", "Compile stays CLI (log hint)", hint)
        add("WCStatus", "Status (last ue/step.json)", "unreal.log(str(wcp.status()))")
        add("WCCleanup", "Cleanup tagged field actors", "unreal.log(str(wcp.cleanup()))")
        add("WCApply", "Apply field from existing bundle", "unreal.log(str(wcp.apply_field()))")
        add("WCCapture", "Capture lookdev stills", "unreal.log(str(wcp.capture()))")
        # Converged Foundry front door: MI inspect + WC status + Foundry validate/plan.
        # Each entry delegates to foundry_converged_panel (which delegates to the
        # existing MI / WC / Foundry owners). Results print to the Output Log.
        add_foundry("FoundryStatus", "Foundry status (MI + WC + recipe)",
                    "unreal.log(fcp.menu_status_summary())")
        add_foundry("FoundryMI", "Inspect material instance (selected or hero)",
                    "unreal.log(fcp.menu_mi_summary())")
        add_foundry("FoundryValidate", "Validate staged Foundry recipes",
                    "unreal.log(fcp.menu_foundry_validate_summary())")
        add_foundry("FoundryPlan", "Plan Sea Above test tile",
                    "unreal.log(fcp.menu_foundry_plan_summary())")
        add_foundry("FoundryWebm", "Encode MI-loop PNGs to .webm",
                    "unreal.log(fcp.menu_webm_summary())")
        menus.refresh_all_widgets()
        unreal.log("[WorldCompiler] menu registered (apply/cleanup/capture; compile stays CLI)")
    except Exception as exc:
        unreal.log_error(f"[WorldCompiler] menu failed: {exc}")


def _register_melodia_menu() -> None:
    """Melodia top-level menu: Platforms speed tuning + PIE Tools (later tooling)."""
    try:
        menus = unreal.ToolMenus.get()
        main = menus.find_menu("LevelEditor.MainMenu")
        if not main:
            return
        owner = "BSGodFile_Melodia"
        if menus.find_menu("LevelEditor.MainMenu.Melodia"):
            menus.remove_menu("LevelEditor.MainMenu.Melodia")
        main.add_sub_menu(owner, "Melodia", "Melodia", "Melodia", "Melodia")
        menu = menus.extend_menu("LevelEditor.MainMenu.Melodia")
        menu.add_section("Platforms", "Platforms")
        menu.add_section("PIETools", "PIE Tools")
        menu.add_section("SirPerches", "Sir Perches")
        menu.add_section("Placement", "Placement")
        menu.add_section("Wardrobe", "Wardrobe")
        py_dir = _SCRIPT_DIR.replace("\\", "/")

        def add(section, name, label, module, body):
            entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
            entry.set_label(label)
            entry.set_string_command(
                unreal.ToolMenuStringCommandType.PYTHON,
                unreal.Name(""),
                f"import sys; p=r'{py_dir}'; sys.path.insert(0,p) if p not in sys.path else None; "
                f"import unreal; import {module}; {body}",
            )
            menu.add_menu_entry(section, entry)

        # Platforms: list + set speed/duration on selected-or-indexed platform.
        # Sliders are not available to ToolMenu strings; these entries act on the
        # Content Browser / Outliner selection via platform_speed_panel.
        add("Platforms", "PlatList", "List platforms in current level",
            "platform_speed_panel as psp", "unreal.log(psp.menu_list_summary())")
        add("Platforms", "PlatSlower", "Selected platform: slower (+50% duration)",
            "platform_speed_panel as psp",
            "unreal.log(psp.menu_nudge_summary(1.5))")
        add("Platforms", "PlatFaster", "Selected platform: faster (-33% duration)",
            "platform_speed_panel as psp",
            "unreal.log(psp.menu_nudge_summary(0.67))")
        add("Platforms", "PlatSave", "Save current level",
            "platform_speed_panel as psp", "unreal.log(str(psp.save_level()))")
        # PIE Tools: extension point. New tools = function in melodia_pie_panel
        # + one add() line here. Never loads another level (see pie_play).
        add("PIETools", "PIEStatus", "PIE status",
            "melodia_pie_panel as ptp", "unreal.log(ptp.menu_status_summary())")
        add("PIETools", "PIEPlay", "Play (Simulate, current level)",
            "melodia_pie_panel as ptp", "unreal.log(str(ptp.pie_play()))")
        add("PIETools", "PIEStop", "Stop PIE",
            "melodia_pie_panel as ptp", "unreal.log(str(ptp.pie_stop()))")
        # Sir Perches: native ASirPerchPoint spots from setup_sir_melodious_perches
        # data, wisely snapped. Save is explicit (ask-first levels stay safe).
        add("SirPerches", "PerchList", "List authored vs placed perches",
            "sir_perch_panel as spp", "unreal.log(spp.menu_list_summary())")
        add("SirPerches", "PerchSpawn", "Spawn missing perches (wise Z)",
            "sir_perch_panel as spp", "unreal.log(str(spp.spawn_missing()))")
        add("SirPerches", "PerchSnap", "Snap selected perches to ground",
            "sir_perch_panel as spp", "unreal.log(str(spp.snap_selected()))")
        add("SirPerches", "PerchSave", "Save current level",
            "sir_perch_panel as spp", "unreal.log(str(spp.save_level()))")
        # Placement: trace-grounded snapping for selected meshes.
        add("Placement", "SnapSelected", "Snap selected meshes to ground",
            "snap_place_panel as snp", "unreal.log(snp.menu_snap_summary())")
        add("Placement", "SnapSave", "Save current level",
            "snap_place_panel as snp", "unreal.log(str(snp.save_level()))")
        # Wardrobe: in-game edits on the live PIE pawn (HOLDs outside PIE).
        add("Wardrobe", "WardEquipped", "Show live equipped slots",
            "wardrobe_live_panel as wlp", "unreal.log(wlp.menu_equipped_summary())")
        menus.refresh_all_widgets()
        unreal.log("[Melodia] menu registered (Platforms + PIE Tools)")
    except Exception as exc:
        unreal.log_error(f"[Melodia] menu failed: {exc}")


def startup():
    if m is None:
        print("[init_unreal] LiveLink module not found, skipping LiveLink only", flush=True)
    else:
        if hasattr(m, "startup"):
            m.startup()
        register_livelink_menus()
        unreal.log(
            "[LiveLink] v3.1 loaded — LiveLink menu has Start/Stop/Status "
            "(no floating panel; start Blender server first)"
        )
    _register_gmm()
    _register_osc_bridge()
    _register_agent_bridge()
    _register_world_compiler()
    _register_melodia_menu()


def shutdown():
    if m is not None and hasattr(m, "shutdown"):
        m.shutdown()


startup()
