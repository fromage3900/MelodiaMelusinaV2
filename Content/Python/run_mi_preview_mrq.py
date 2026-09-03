"""Queue MRQ renders for MI preview loops from mi_preview_manifest.json.

Run in-editor:
  py Content/Python/run_mi_preview_mrq.py
  py Content/Python/run_mi_preview_mrq.py --only MI_ZenTrim_FlowersLots
  py Content/Python/run_mi_preview_mrq.py --proof

Requires:
  setup_material_preview_studio.py
  setup_mrq_presets.py
  setup_mi_preview_sequences.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mi_preview_manifest as manifest_mod
import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "run_mi_preview_mrq.json"


def _parse_only_arg() -> str | None:
    if "--proof" in sys.argv:
        return "MI_ZenTrim_FlowersLots"
    for index, arg in enumerate(sys.argv):
        if arg == "--only" and index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return None


def _load_level(level_path: str) -> bool:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les:
        return False
    les.load_level(level_path)
    return True


def _get_asset(asset_path: str):
    import unreal

    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    data = reg.get_asset_by_object_path(asset_path)
    if not data or not data.is_valid():
        return None
    return data.get_asset()


def _find_queue_subsystem():
    import unreal

    cls = getattr(unreal, "MoviePipelineQueueSubsystem", None)
    if not cls:
        raise RuntimeError("MoviePipelineQueueSubsystem not found")
    return unreal.get_editor_subsystem(cls)


def _find_executor_class():
    import unreal

    for name in ("MoviePipelineExecutorBase", "MoviePipelineQueueEngine"):
        cls = getattr(unreal, name, None)
        if cls:
            return cls
    raise RuntimeError("MRQ executor class not found")


def _configure_job_output(job, entry: dict) -> None:
    import unreal

    mi_id = entry["id"]
    out_dir = studio.output_dir_for_mi(mi_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = job.get_configuration().get_settings()
    output_setting = settings.find_settings_by_class(unreal.MoviePipelineOutputSetting)
    if output_setting:
        output_setting.output_resolution = unreal.IntPoint(studio.LOOP_RESOLUTION, studio.LOOP_RESOLUTION)
        output_setting.output_directory = unreal.DirectoryPath(str(out_dir))
        output_setting.file_name_format = f"{mi_id}_{{frame_number}}"
        output_setting.output_frame_rate = unreal.FrameRate(studio.FRAME_RATE, 1)
        output_setting.use_custom_frame_rate = True
        output_setting.custom_start_frame = 0
        output_setting.custom_end_frame = studio.LOOP_FRAMES
        output_setting.zero_pad_frame_numbers = 4


def queue_mi_loop(entry: dict, *, preset_path: str = studio.MRQ_PRESET_MI_LOOP) -> dict:
    import unreal
    import mi_preview_apply as apply_mod

    seq_path = str(entry.get("sequence_path") or studio.sequence_path_for_mi(entry["id"]))
    seq_package = f"{seq_path}.{seq_path.rsplit('/', 1)[-1]}"

    preset = _get_asset(f"{preset_path}.{preset_path.rsplit('/', 1)[-1]}")
    sequence = _get_asset(seq_package)
    if not preset:
        return {"ok": False, "id": entry["id"], "error": f"preset_missing:{preset_path}"}
    if not sequence:
        return {"ok": False, "id": entry["id"], "error": f"sequence_missing:{seq_package}"}

    apply_mod.apply_preview_entry(entry)

    queue_subsys = _find_queue_subsystem()
    queue = queue_subsys.get_queue()
    while queue.get_num_jobs() > 0:
        queue.delete_job(queue.get_jobs()[0])

    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_sequence(sequence)
    job.set_configuration(preset)
    job.set_job_name(f"MI_Loop_{entry['id']}")
    job.set_author("EnvPortfolio")
    job.map = unreal.SoftObjectPath(studio.LEVEL)

    _configure_job_output(job, entry)

    executor = _find_executor_class()()
    queue_subsys.render_queue_with_executor_instance(executor)

    return {
        "ok": True,
        "id": entry["id"],
        "sequence": seq_package,
        "preset": preset_path,
        "output_dir": str(studio.output_dir_for_mi(entry["id"])),
        "frames": studio.LOOP_FRAMES,
    }


def prepare_pipeline(*, only: str | None = None) -> dict:
    import setup_material_preview_studio as studio_setup
    import setup_mrq_presets as mrq_presets
    import setup_mi_preview_sequences as seq_setup

    manifest_mod.write_manifest()
    studio_setup.build_studio()
    mrq_presets.create_mi_loop_preset()
    return seq_setup.build_sequences(only=only)


def run_batch(*, only: str | None = None, prepare: bool = True) -> dict:
    if prepare:
        prep = prepare_pipeline(only=only)
        if not prep.get("ok"):
            return {"ok": False, "stage": "prepare", "result": prep}

    if not _load_level(studio.LEVEL):
        return {"ok": False, "error": f"failed_to_load:{studio.LEVEL}"}

    manifest = manifest_mod.load_manifest()
    entries = manifest_mod.filter_entries(manifest, only=only)
    if not entries:
        return {"ok": False, "error": "no_entries", "only": only}

    jobs: list[dict] = []
    for entry in entries:
        jobs.append(queue_mi_loop(entry))

    report = {
        "ok": all(j.get("ok") for j in jobs),
        "count": len(jobs),
        "only": only,
        "jobs": jobs,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    only = _parse_only_arg()
    result = run_batch(only=only)
    if "json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
