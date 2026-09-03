"""Queue a cinematic MRQ render of L_SakuraPath via the Sakura_Path_Cinematic sequence.

Run in-editor:
  py Content/Python/run_mrq_capture.py

Requires:
  setup_mrq_presets.py  (create preset first)
  setup_sakura_sequence.py  (create sequence + bind camera first)
"""
from __future__ import annotations

import sys

LEVEL_PATH = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"
PRESET_PATH = "/Game/EnvSandbox/MRQ/Presets/MRQ_Preset_Cinematic"
SEQUENCE_PATH = "/Game/EnvSandbox/MRQ/Sequences/Sakura_Path_Cinematic"

OUTPUT_LOG = "Saved/Portfolio/MRQ/render_log.json"


def _load_level(level_path: str) -> bool:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les:
        unreal.log_warning("[MRQCapture] LevelEditorSubsystem not available")
        return False
    les.load_level(level_path)
    unreal.log(f"[MRQCapture] Loaded level: {level_path}")
    return True


def _get_preset(preset_path: str):
    import unreal

    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
    data = asset_reg.get_asset_by_object_path(preset_path)
    if not data or not data.is_valid():
        return None
    return data.get_asset()


def _get_sequence(sequence_path: str):
    import unreal

    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
    data = asset_reg.get_asset_by_object_path(sequence_path)
    if not data or not data.is_valid():
        return None
    return data.get_asset()


def _find_executor_class():
    import unreal

    cand = getattr(unreal, "MoviePipelineExecutorBase", None)
    if cand:
        return cand
    for name in ["MoviePipelineExecutorBase", "MoviePipelineQueueEngine"]:
        c = getattr(unreal, name, None)
        if c:
            return c
    raise RuntimeError("MRQ executor class not found")


def _find_queue_subsystem():
    import unreal

    cand = getattr(unreal, "MoviePipelineQueueSubsystem", None)
    if cand:
        return unreal.get_editor_subsystem(cand)
    raise RuntimeError("MoviePipelineQueueSubsystem not found")


def queue_sakura_render(
    level_path: str = LEVEL_PATH,
    preset_path: str = PRESET_PATH,
    sequence_path: str = SEQUENCE_PATH,
) -> dict:
    import unreal

    if level_path:
        loaded = _load_level(level_path)
        if not loaded:
            return {"ok": False, "error": f"failed to load level: {level_path}"}

    preset = _get_preset(preset_path)
    if not preset:
        return {"ok": False, "error": f"preset not found: {preset_path}"}

    sequence = _get_sequence(sequence_path)
    if not sequence:
        return {"ok": False, "error": f"sequence not found: {sequence_path}"}

    queue_subsys = _find_queue_subsystem()
    queue = queue_subsys.get_queue()
    job = queue.duplicate_job(None) if queue.get_num_jobs() > 0 else queue.allocate_new_job()

    job.set_sequence(sequence)
    job.set_configuration(preset)
    job.set_job_name("Sakura_Path_Cinematic")
    job.set_author("EnvPortfolio")

    output_setting = job.get_configuration().get_settings().find_settings_by_class(unreal.MoviePipelineOutputSetting)
    if output_setting:
        output_setting.output_resolution = unreal.IntPoint(3840, 2160)
        output_setting.output_directory = unreal.DirectoryPath(OUTPUT_LOG.rsplit("/", 1)[0])
        output_setting.file_name_format = "{sequence_name}_{frame_number}"

    executor_cls = _find_executor_class()
    executor = executor_cls()

    executor.on_executor_finished_delegate.add_callable_unique(
        lambda: unreal.log("[MRQCapture] Render job finished")
    )
    executor.on_executor_errored_delegate.add_callable_unique(
        lambda _, error: unreal.log_warning(f"[MRQCapture] Render error: {error}")
    )

    queue_subsys.render_queue_with_executor_instance(executor)

    unreal.log(f"[MRQCapture] Queued Sakura cinematic render")
    return {
        "ok": True,
        "preset": preset_path,
        "sequence": sequence_path,
        "level": level_path,
        "job_name": "Sakura_Path_Cinematic",
        "resolution": "3840x2160",
    }


def main() -> int:
    result = queue_sakura_render()
    if "json" in sys.argv:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
