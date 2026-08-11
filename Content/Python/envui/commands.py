from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import importlib


def _log(msg: str) -> None:
    try:
        import unreal

        unreal.log(f"[EnvUI] {msg}")
    except Exception:
        print(f"[EnvUI] {msg}")


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    message: str = ""
    outputs: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "outputs": self.outputs or {},
            "stats": self.stats or {},
            "error": self.error,
        }


CommandFn = Callable[[Dict[str, Any]], CommandResult]


@dataclass(frozen=True)
class EnvUICommand:
    id: str
    label: str
    section: str
    fn: CommandFn


def _cmd_livelink_start(_: Dict[str, Any]) -> CommandResult:
    import livelink_unreal

    livelink_unreal.start_connection()
    return CommandResult(ok=True, message="Live Link start requested.")


def _cmd_livelink_stop(_: Dict[str, Any]) -> CommandResult:
    import livelink_unreal

    livelink_unreal.stop_connection()
    return CommandResult(ok=True, message="Live Link stop requested.")


def _cmd_livelink_status(_: Dict[str, Any]) -> CommandResult:
    import livelink_unreal

    status = livelink_unreal.get_status()
    _log(f"[LiveLink] {status}")
    return CommandResult(ok=True, message="Live Link status.", outputs={"status": status})


def _cmd_pcg_run_sakura(_: Dict[str, Any]) -> CommandResult:
    import setup_pcg_sakura

    report = setup_pcg_sakura.build_all(rebuild=True, spawn=True)
    return CommandResult(ok=True, message="Sakura PCG complete.", outputs={"report": report})


def _cmd_pcg_run_universal(_: Dict[str, Any]) -> CommandResult:
    import setup_pcg_universal

    report = setup_pcg_universal.build_all(force=True)
    return CommandResult(ok=True, message="Universal PCG build complete.", outputs={"report": report})


def _cmd_pcg_apply_greybox(_: Dict[str, Any]) -> CommandResult:
    import setup_pcg_greybox
    import pcg_portfolio_standards as s

    r = setup_pcg_greybox.apply_greybox_pcg(s.LEVEL_TEMPLATE, preset="minimal")
    return CommandResult(ok=True, message="Greybox PCG applied.", outputs={"report": r})


def _cmd_pcg_audit(_: Dict[str, Any]) -> CommandResult:
    import audit_pcg_portfolio

    r = audit_pcg_portfolio._audit_in_ue()
    return CommandResult(ok=True, message="PCG audit complete.", outputs={"report": r})


def _cmd_niagara_run_sakura(_: Dict[str, Any]) -> CommandResult:
    import run_sakura_niagara_plan

    report = run_sakura_niagara_plan.run_plan(rebuild=False)
    return CommandResult(ok=True, message="Sakura Niagara plan complete.", outputs={"report": report})


def _cmd_niagara_run_sakura_rebuild(_: Dict[str, Any]) -> CommandResult:
    import run_sakura_niagara_plan

    report = run_sakura_niagara_plan.run_plan(rebuild=True)
    return CommandResult(ok=True, message="Sakura Niagara plan complete (rebuild).", outputs={"report": report})


def _cmd_orchestrator_tick(_: Dict[str, Any]) -> CommandResult:
    import run_portfolio_orchestrator_loop_tick

    code = run_portfolio_orchestrator_loop_tick.main()
    return CommandResult(ok=True, message="Orchestrator tick complete.", outputs={"exit_code": code})


def _cmd_capture_all_hero_cameras(_: Dict[str, Any]) -> CommandResult:
    import render_exporter

    result = render_exporter.capture_all_hero_renders()
    ok = bool(result.get("ok"))
    count = int(result.get("count") or 0)
    return CommandResult(
        ok=ok,
        message=f"Captured {count} hero camera plate(s).",
        outputs={"result": result},
        error=None if ok else str(result.get("error") or "capture_failed"),
    )


def _cmd_setup_hero_cameras(_: Dict[str, Any]) -> CommandResult:
    import setup_zenforest_hero_cameras as hero_cams

    report = hero_cams.setup_hero_cameras()
    count = len(report.get("cameras") or [])
    return CommandResult(
        ok=True,
        message=f"Placed {count} portfolio cameras in ZenForestTest.",
        outputs={"report": report},
    )


def _cmd_capture_portfolio_outputs(_: Dict[str, Any]) -> CommandResult:
    import capture_material_previews
    import capture_scene_metadata
    import export_screenshot

    ss = export_screenshot.capture_screenshot()
    mp = capture_material_previews.capture_material_previews()
    md = capture_scene_metadata.capture_scene_metadata()
    return CommandResult(
        ok=True,
        message="Capture complete.",
        outputs={"screenshot": ss, "materials": mp, "metadata": md},
    )


def _cmd_capture_material_thumbnails(_: Dict[str, Any]) -> CommandResult:
    import capture_material_previews as previews

    path = previews.write_previews_manifest()
    _log(f"OK captured previews -> {path}")
    return CommandResult(ok=True, message="Captured material thumbnails.", outputs={"previews_manifest": str(path)})


def _cmd_run_material_audits(_: Dict[str, Any]) -> CommandResult:
    import material_family_manifest_full as fam
    import material_instance_audit as audit
    from envui.paths import get_paths

    fam.main()
    audit.main()
    out = get_paths().material_audit_json
    _log(f"OK wrote audit -> {out}")
    return CommandResult(ok=True, message="Ran disk-only material audits.", outputs={"material_audit_json": str(out)})


def _cmd_capture_and_audit(_: Dict[str, Any]) -> CommandResult:
    a = _cmd_capture_material_thumbnails({})
    if not a.ok:
        return a
    b = _cmd_run_material_audits({})
    if not b.ok:
        return b
    outputs = {}
    outputs.update(a.outputs or {})
    outputs.update(b.outputs or {})
    return CommandResult(ok=True, message="Captured thumbnails + ran audits.", outputs=outputs)


def _cmd_print_material_paths(_: Dict[str, Any]) -> CommandResult:
    from envui.paths import get_paths

    p = get_paths()
    _log(f"previews_manifest: {p.previews_manifest}")
    _log(f"material_audit_json: {p.material_audit_json}")
    return CommandResult(
        ok=True,
        message="Printed output paths.",
        outputs={"previews_manifest": str(p.previews_manifest), "material_audit_json": str(p.material_audit_json)},
    )


def _cmd_open_modifier_panel(_: Dict[str, Any]) -> CommandResult:
    # Existing dockable panel registered by the ProceduralModelingToolkit editor module.
    # C++: TabName("ProceduralModelingToolkit") + TryInvokeTab(TabName)
    tab_name = "ProceduralModelingToolkit"
    try:
        import unreal

        tab_id = unreal.Name(tab_name)

        gtm = None
        if hasattr(unreal, "GlobalTabmanager"):
            gtm = unreal.GlobalTabmanager.get()
        elif hasattr(unreal, "GlobalTabManager"):
            gtm = unreal.GlobalTabManager.get()

        if gtm is not None and hasattr(gtm, "try_invoke_tab"):
            gtm.try_invoke_tab(tab_id)
            _log(f"OK opened tab '{tab_name}'")
            return CommandResult(ok=True, message=f"Opened '{tab_name}' tab.", outputs={"tab": tab_name})

        _log(
            f"WARN cannot open '{tab_name}' via Python (tab manager not exposed). "
            f"Open it via Window menu: 'Procedural Modeling Toolkit'."
        )
        return CommandResult(
            ok=False,
            message=f"Tab manager not exposed to Python in this build.",
            outputs={"tab": tab_name},
            error="GlobalTabmanager not available",
        )
    except Exception as e:
        _log(f"ERROR opening modifier panel: {e}")
        return CommandResult(ok=False, message="Failed to open modifier panel.", error=str(e), outputs={"tab": tab_name})


def _cmd_mrq_setup_presets(_: Dict[str, Any]) -> CommandResult:
    import setup_mrq_presets

    result = setup_mrq_presets.create_cinematic_preset()
    ok = bool(result.get("ok"))
    return CommandResult(
        ok=ok,
        message="MRQ preset created." if ok else f"MRQ preset failed: {result.get('error', 'unknown')}",
        outputs={"result": result},
        error=None if ok else result.get("error"),
    )


def _cmd_mrq_setup_sequence(_: Dict[str, Any]) -> CommandResult:
    import setup_sakura_sequence

    result = setup_sakura_sequence.setup_complete()
    ok = bool(result.get("ok"))
    return CommandResult(
        ok=ok,
        message="Sakura sequence ready." if ok else f"Sequence setup failed: {result.get('error', 'unknown')}",
        outputs={"result": result},
        error=None if ok else result.get("error"),
    )


def _cmd_mrq_queue_render(_: Dict[str, Any]) -> CommandResult:
    import run_mrq_capture

    result = run_mrq_capture.queue_sakura_render()
    ok = bool(result.get("ok"))
    return CommandResult(
        ok=ok,
        message="Render queued." if ok else f"Render queue failed: {result.get('error', 'unknown')}",
        outputs={"result": result},
        error=None if ok else result.get("error"),
    )


def _cmd_mi_loop_preview_frame(_: Dict[str, Any]) -> CommandResult:
    import mi_preview_viewport_frame as preview

    result = preview.capture_preview_frame()
    ok = bool(result.get("ok"))
    return CommandResult(
        ok=ok,
        message=f"Preview frame -> {result.get('output_path')}" if ok else result.get("error", "preview failed"),
        outputs={"result": result},
        error=None if ok else result.get("error"),
    )


def _cmd_mi_loop_capture_selected(_: Dict[str, Any]) -> CommandResult:
    import mi_preview_viewport_frame as preview
    import run_mi_preview_mrq as mrq

    mi_path = preview._selected_mi_path()
    if not mi_path:
        return CommandResult(ok=False, message="Select a material instance in the Content Browser.", error="no_selection")
    name = mi_path.rsplit("/", 1)[-1].split(".")[0]
    result = mrq.run_batch(only=name, prepare=True)
    ok = bool(result.get("ok"))
    return CommandResult(
        ok=ok,
        message=f"Loop capture queued for {name}." if ok else "Loop capture failed.",
        outputs={"result": result, "mi": name},
        error=None if ok else str(result.get("error") or result),
    )


def _cmd_mi_loop_publish(params: Dict[str, Any]) -> CommandResult:
    import subprocess
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "Tools" / "publish_material_loops.ps1"
    if not script.is_file():
        return CommandResult(ok=False, message="publish_material_loops.ps1 missing.", error="script_missing")
    args = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script), "-NoPush"]
    if params.get("with_push"):
        args = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script)]
    proc = subprocess.run(args, cwd=str(project_root), capture_output=True, text=True)
    ok = proc.returncode == 0
    return CommandResult(
        ok=ok,
        message="Publish pipeline finished (see logs)." if ok else "Publish pipeline failed.",
        outputs={"stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:]},
        error=None if ok else proc.stderr or proc.stdout,
    )


def get_registry() -> Dict[str, EnvUICommand]:
    # Keep this deterministic and side-effect free.
    return {
        "livelink.start": EnvUICommand(
            id="livelink.start",
            label="Start Live Link (connect to Blender)",
            section="Connection",
            fn=_cmd_livelink_start,
        ),
        "livelink.stop": EnvUICommand(
            id="livelink.stop",
            label="Stop Live Link",
            section="Connection",
            fn=_cmd_livelink_stop,
        ),
        "livelink.status": EnvUICommand(
            id="livelink.status",
            label="Show Status",
            section="Connection",
            fn=_cmd_livelink_status,
        ),
        "pcg.sakura_build": EnvUICommand(
            id="pcg.sakura_build",
            label="Run Sakura PCG (showcase wrapper)",
            section="PCG",
            fn=_cmd_pcg_run_sakura,
        ),
        "pcg.universal_build": EnvUICommand(
            id="pcg.universal_build",
            label="Run Universal PCG Build",
            section="PCG",
            fn=_cmd_pcg_run_universal,
        ),
        "pcg.greybox_apply": EnvUICommand(
            id="pcg.greybox_apply",
            label="Apply Greybox PCG (Template minimal)",
            section="PCG",
            fn=_cmd_pcg_apply_greybox,
        ),
        "pcg.audit": EnvUICommand(
            id="pcg.audit",
            label="Audit PCG Portfolio",
            section="PCG",
            fn=_cmd_pcg_audit,
        ),
        "niagara.sakura_plan": EnvUICommand(
            id="niagara.sakura_plan",
            label="Run Sakura Dream Niagara (full plan)",
            section="Niagara",
            fn=_cmd_niagara_run_sakura,
        ),
        "niagara.sakura_plan_rebuild": EnvUICommand(
            id="niagara.sakura_plan_rebuild",
            label="Run Sakura Dream Niagara (--rebuild)",
            section="Niagara",
            fn=_cmd_niagara_run_sakura_rebuild,
        ),
        "portfolio.orchestrator_tick": EnvUICommand(
            id="portfolio.orchestrator_tick",
            label="Portfolio Orchestrator Tick (10m loop step)",
            section="Portfolio",
            fn=_cmd_orchestrator_tick,
        ),
        "capture.portfolio_outputs": EnvUICommand(
            id="capture.portfolio_outputs",
            label="Capture Portfolio Outputs (screenshots + previews + metadata)",
            section="Capture",
            fn=_cmd_capture_portfolio_outputs,
        ),
        "capture.setup_hero_cameras": EnvUICommand(
            id="capture.setup_hero_cameras",
            label="Setup ZenForest Hero Cameras",
            section="Capture",
            fn=_cmd_setup_hero_cameras,
        ),
        "capture.all_hero_cameras": EnvUICommand(
            id="capture.all_hero_cameras",
            label="Capture All Hero Cameras",
            section="Capture",
            fn=_cmd_capture_all_hero_cameras,
        ),
        "materials.capture_thumbnails": EnvUICommand(
            id="materials.capture_thumbnails",
            label="Capture Material Thumbnails",
            section="Materials",
            fn=_cmd_capture_material_thumbnails,
        ),
        "materials.run_audits": EnvUICommand(
            id="materials.run_audits",
            label="Run Material Audits (disk-only)",
            section="Materials",
            fn=_cmd_run_material_audits,
        ),
        "materials.capture_and_audit": EnvUICommand(
            id="materials.capture_and_audit",
            label="Capture Thumbnails + Run Audits",
            section="Materials",
            fn=_cmd_capture_and_audit,
        ),
        "materials.print_paths": EnvUICommand(
            id="materials.print_paths",
            label="Print Material Output Paths",
            section="Materials",
            fn=_cmd_print_material_paths,
        ),
        "modifiers.open_panel": EnvUICommand(
            id="modifiers.open_panel",
            label="Open Modifier Panel (Procedural Toolkit)",
            section="Modifiers",
            fn=_cmd_open_modifier_panel,
        ),
        "mrq.setup_presets": EnvUICommand(
            id="mrq.setup_presets",
            label="Setup MRQ Presets (4K 16-bit EXR)",
            section="MRQ",
            fn=_cmd_mrq_setup_presets,
        ),
        "mrq.setup_sequence": EnvUICommand(
            id="mrq.setup_sequence",
            label="Setup Sakura Cinematic Sequence (10s orbit)",
            section="MRQ",
            fn=_cmd_mrq_setup_sequence,
        ),
        "mrq.queue_render": EnvUICommand(
            id="mrq.queue_render",
            label="Queue Sakura Cinematic MRQ Render",
            section="MRQ",
            fn=_cmd_mrq_queue_render,
        ),
        "loops.preview_frame": EnvUICommand(
            id="loops.preview_frame",
            label="Preview active MI (1 frame)",
            section="Material Loops",
            fn=_cmd_mi_loop_preview_frame,
        ),
        "loops.capture_selected": EnvUICommand(
            id="loops.capture_selected",
            label="Capture selected MI loop",
            section="Material Loops",
            fn=_cmd_mi_loop_capture_selected,
        ),
        "loops.publish": EnvUICommand(
            id="loops.publish",
            label="Publish loops (encode + ingest, no push)",
            section="Material Loops",
            fn=_cmd_mi_loop_publish,
        ),
    }

    # Inject GMM (Grandmaster Melodia Melusina) commands
    _inject_gmm_commands(reg)

    return reg


def _inject_gmm_commands(reg: dict) -> None:
    """Dynamically import and register GMM commands if package is available."""
    try:
        from gmm.ui.commands import GMM_COMMANDS, GMM_SECTION

        for cmd_id, (section, fn) in GMM_COMMANDS.items():
            if cmd_id not in reg:
                reg[cmd_id] = EnvUICommand(
                    id=cmd_id,
                    label=cmd_id.replace("gmm.", "").replace(".", " ").title(),
                    section=section,
                    fn=fn,
                )
    except ImportError:
        pass
    except Exception:
        pass


def run(command_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = params or {}
    reg = get_registry()
    cmd = reg.get(command_id)
    if not cmd:
        res = CommandResult(ok=False, message="Unknown command.", error=f"Unknown command_id '{command_id}'")
        _log(res.error or res.message)
        return res.to_dict()

    try:
        result = cmd.fn(params)
        if result.ok:
            _log(f"OK {command_id}: {result.message}")
        else:
            _log(f"FAIL {command_id}: {result.error or result.message}")
        return result.to_dict()
    except Exception as e:
        res = CommandResult(ok=False, message="Command crashed.", error=str(e))
        _log(f"ERROR {command_id}: {e}")
        return res.to_dict()

