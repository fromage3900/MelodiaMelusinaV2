from __future__ import annotations


def _py_path_prefix() -> str:
    # Inject the project's Content/Python folder into sys.path and ensure LiveLink import still works.
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_python = os.path.abspath(os.path.join(script_dir, "..")).replace("\\", "/")
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
        + "\nexcept Exception as _envui_exc:\n "
        + " unreal.log_error('[EnvUI] Menu action failed: ' + str(_envui_exc))"
    )


def register_envui_menus(owner: str = "BSGodFile_LiveLink") -> None:
    import unreal

    menus = unreal.ToolMenus.get()
    main = menus.find_menu("LevelEditor.MainMenu")
    if not main:
        unreal.log_warning("[EnvUI] LevelEditor.MainMenu not found")
        return

    # Ensure a clean slate (avoid duplicates across hot reloads)
    for stale in (
        "LevelEditor.MainMenu.LiveLink.BlenderLiveLink",
        "LevelEditor.MainMenu.LiveLink",
    ):
        if menus.find_menu(stale):
            menus.remove_menu(stale)

    main.add_sub_menu(owner, "LiveLink", "LiveLink", "LiveLink", "Live Link")
    live = menus.extend_menu("LevelEditor.MainMenu.LiveLink")

    # Sections (keep stable ordering)
    live.add_section("Connection", "Connection", "None")
    live.add_section("PCG", "PCG", "None")
    live.add_section("Niagara", "Niagara", "None")
    live.add_section("Capture", "Capture", "None")
    live.add_section("Materials", "Materials", "None")
    live.add_section("Modifiers", "Modifiers", "None")
    live.add_section("MRQ", "MRQ", "None")
    live.add_section("Grandmaster", "Grandmaster", "None")
    live.add_section("Help", "Help", "None")

    def add_entry(menu, section, name, label, py_body):
        entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label(label)
        entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type_name="",
            string=_menu_command(py_body),
        )
        menu.add_menu_entry(section, entry)

    # --- Connection (LiveLink) ---
    add_entry(
        live,
        "Connection",
        "StartLL",
        "Start Live Link (connect to Blender)",
        "from envui import commands; commands.run('livelink.start');",
    )
    add_entry(live, "Connection", "StopLL", "Stop Live Link", "from envui import commands; commands.run('livelink.stop');")
    add_entry(
        live,
        "Connection",
        "StatusLL",
        "Show Status",
        "from envui import commands; commands.run('livelink.status');",
    )

    # --- PCG ---
    add_entry(
        live,
        "PCG",
        "RunSakuraPCG",
        "Run Sakura PCG (showcase wrapper)",
        "from envui import commands; commands.run('pcg.sakura_build');",
    )
    add_entry(
        live,
        "PCG",
        "RunUniversalPCG",
        "Run Universal PCG Build",
        "from envui import commands; commands.run('pcg.universal_build');",
    )
    add_entry(
        live,
        "PCG",
        "RunGreyboxPCG",
        "Apply Greybox PCG (Template minimal)",
        "from envui import commands; commands.run('pcg.greybox_apply');",
    )
    add_entry(
        live,
        "PCG",
        "AuditPCGPortfolio",
        "Audit PCG Portfolio",
        "from envui import commands; commands.run('pcg.audit');",
    )

    # --- Niagara ---
    add_entry(
        live,
        "Niagara",
        "RunSakuraNiagara",
        "Run Sakura Dream Niagara (full plan)",
        "from envui import commands; commands.run('niagara.sakura_plan');",
    )
    add_entry(
        live,
        "Niagara",
        "RunSakuraNiagaraRebuild",
        "Run Sakura Dream Niagara (--rebuild)",
        "from envui import commands; commands.run('niagara.sakura_plan_rebuild');",
    )

    # --- Capture ---
    add_entry(
        live,
        "Capture",
        "CapturePortfolioOutputs",
        "Capture Portfolio Outputs (screenshots + previews + metadata)",
        "from envui import commands; commands.run('capture.portfolio_outputs');",
    )
    add_entry(
        live,
        "Capture",
        "SetupHeroCameras",
        "Setup ZenForest Hero Cameras",
        "from envui import commands; commands.run('capture.setup_hero_cameras');",
    )
    add_entry(
        live,
        "Capture",
        "CaptureAllHeroCameras",
        "Capture All Hero Cameras",
        "from envui import commands; commands.run('capture.all_hero_cameras');",
    )
    add_entry(
        live,
        "Capture",
        "RunOrchestratorTick",
        "Portfolio Orchestrator Tick (10m loop step)",
        "from envui import commands; commands.run('portfolio.orchestrator_tick');",
    )

    # --- EnvUI registry-backed actions ---
    add_entry(
        live,
        "Materials",
        "MatCaptureThumbs",
        "Capture Material Thumbnails",
        "from envui import commands; commands.run('materials.capture_thumbnails');",
    )
    add_entry(
        live,
        "Materials",
        "MatRunAudits",
        "Run Material Audits (disk-only)",
        "from envui import commands; commands.run('materials.run_audits');",
    )
    add_entry(
        live,
        "Materials",
        "MatCaptureAndAudit",
        "Capture Thumbnails + Run Audits",
        "from envui import commands; commands.run('materials.capture_and_audit');",
    )
    add_entry(
        live,
        "Materials",
        "MatPrintPaths",
        "Print Material Output Paths",
        "from envui import commands; commands.run('materials.print_paths');",
    )
    add_entry(
        live,
        "Modifiers",
        "OpenModifierPanel",
        "Open Modifier Panel (Procedural Toolkit)",
        "from envui import commands; commands.run('modifiers.open_panel');",
    )

    # --- MRQ ---
    add_entry(
        live,
        "MRQ",
        "MRQSetupPresets",
        "Setup MRQ Presets (4K 16-bit EXR)",
        "from envui import commands; commands.run('mrq.setup_presets');",
    )
    add_entry(
        live,
        "MRQ",
        "MRQSetupSequence",
        "Setup Sakura Cinematic Sequence (10s orbit)",
        "from envui import commands; commands.run('mrq.setup_sequence');",
    )
    add_entry(
        live,
        "MRQ",
        "MRQQueueRender",
        "Queue Sakura Cinematic MRQ Render",
        "from envui import commands; commands.run('mrq.queue_render');",
    )

    # --- Grandmaster ---
    add_entry(
        live,
        "Grandmaster",
        "GmmAbout",
        "About Grandmaster",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.about', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmAgentStatus",
        "Agent Status",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.agent.status', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmBlessingEvolution",
        "Generate Blessings (Ollama)",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.agent.blessing_evolution', {'target_count': 5});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmDelegateGeometry",
        "Delegate: Geometry (list genomes)",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.agent.delegate', {'intent': 'geometry', 'action': 'list_genomes'});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMcpStatus",
        "MCP Status",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.mcp_status', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMcpDiscover",
        "MCP Discover Actions",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.mcp_discover', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmRunPython",
        "Run Python via MCP",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.run_python', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmKycVerify",
        "MKC: Verify All Systems",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.mkc.verify_all', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmPcgPreflight",
        "PCG: Run Production Preflight",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.pcg.preflight', {});",
    )

    add_entry(
        live,
        "Grandmaster",
        "GmmPcgRepairQuarantine",
        "PCG: Repair Quarantined References",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.pcg.repair_quarantine', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMelusinaAssess",
        "Assess Melusina Rig",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.melusina.rig_assess', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMelusinaBlend",
        "Setup Melusina Blend Spaces",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.melusina.blend_setup', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMelusinaBp",
        "Setup Melusina Blueprints",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.melusina.bp_setup', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMelodiaEnemies",
        "Melodia: List Enemies",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.melodia.enemies', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmMelodiaSkills",
        "Melodia: List Skills",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.melodia.skills', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmSurrealEscher",
        "Surreal: Escher Geometry",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.surreal.escher', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmSurrealProcArch",
        "Surreal: Procedural Architecture",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.surreal.proc_arch', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmBattleTestEncounter",
        "Battle: Spawn Test Encounter",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.battle.test_encounter', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmBattleState",
        "Battle: Poll State",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.battle.state', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmBattleCommand",
        "Battle: Issue Command (basic_attack)",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.battle.command', {'command': 'basic_attack'});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmUiBattleMenu",
        "UI: Create Battle Menu Widget",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.ui.battle_menu', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmUiVictoryScreen",
        "UI: Create Victory Screen Widget",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.ui.victory_screen', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmUiBattleGui",
        "Battle: Open Test Harness GUI",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.ui.battle_gui', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmGameRun",
        "Game: Launch CLI Battle Runner",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.game.run', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmGameConfig",
        "Game: View Config",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.game.config', {});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmGameSave",
        "Game: Save Progress",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.game.save', {'action': 'save'});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmGameLoad",
        "Game: Load Progress",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.game.save', {'action': 'load'});",
    )
    add_entry(
        live,
        "Grandmaster",
        "GmmGamePlayerStatus",
        "Game: Player Status",
        "from gmm.ui.commands import run_gmm; run_gmm('gmm.game.player_status', {});",
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

    menus.refresh_all_widgets()
    unreal.log("[EnvUI] LiveLink menu ready — organized sections + EnvUI registry actions")
