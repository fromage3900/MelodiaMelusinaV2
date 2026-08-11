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
    live.add_section("Connection", "Connection", 0)
    live.add_section("Portfolio", "Portfolio", 1)
    live.add_section("Help", "Help", 2)

    def add_entry(menu, section, name, label, py_body):
        entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label(label)
        entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type_name="",
            string=_menu_command(py_body),
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


def startup():
    if m is None:
        print("[init_unreal] LiveLink module not found, skipping startup", flush=True)
        return
    if hasattr(m, "startup"):
        m.startup()
    register_livelink_menus()
    _register_gmm()
    _register_osc_bridge()
    _register_agent_bridge()
    unreal.log(
        "[LiveLink] v3.1 loaded — LiveLink menu has Start/Stop/Status "
        "(no floating panel; start Blender server first)"
    )


def shutdown():
    if m is not None and hasattr(m, "shutdown"):
        m.shutdown()
