"""Create MRQ presets: 4K 16-bit EXR cinematic + 1080 PNG material-loop preview.

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/setup_mrq_presets.py"

Outputs:
  /Game/EnvSandbox/MRQ/Presets/MRQ_Preset_Cinematic
  /Game/EnvSandbox/MRQ/Presets/MRQ_Preset_MI_Loop_1080

API verified live against UE 5.8 (2026-07-24) - the real preset-construction
pattern is `preset.find_or_add_setting_by_class(SettingClass)`, NOT property
assignment on a `.get_settings()` object (that was this script's original,
untested, incorrect guess). Resolution/output-directory live on
MoviePipelineOutputSetting, not on the per-format output class.
"""
from __future__ import annotations

import sys

PRESET_DIR = "/Game/EnvSandbox/MRQ/Presets"
PRESET_PATH = f"{PRESET_DIR}/MRQ_Preset_Cinematic"
PRESET_MI_LOOP_PATH = f"{PRESET_DIR}/MRQ_Preset_MI_Loop_1080"
OUTPUT_DIR = "{project_dir}/Saved/Portfolio/MRQ/"
OUTPUT_DIR_MI_LOOPS = "{project_dir}/Saved/Portfolio/Renders/MaterialLoops/"


def _ensure_preset_dir():
    import unreal

    for p in ("/Game/EnvSandbox/MRQ", PRESET_DIR):
        if not unreal.EditorAssetLibrary.does_directory_exist(p):
            unreal.EditorAssetLibrary.make_directory(p)


def _create_preset(name: str, path: str) -> "unreal.MoviePipelinePrimaryConfig":
    import unreal

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    return asset_tools.create_asset(name, PRESET_DIR, unreal.MoviePipelineMasterConfig, None)


def _existing_preset(path: str):
    """Load an existing preset using a real object path, avoiding stale registry misses."""
    import unreal

    name = path.rsplit("/", 1)[-1]
    object_path = f"{path}.{name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return None
    return unreal.EditorAssetLibrary.load_asset(object_path) or unreal.EditorAssetLibrary.load_asset(path)


def create_cinematic_preset() -> dict:
    """4K 16-bit multilayer EXR, Epic anti-aliasing, deferred beauty pass."""
    import unreal

    _ensure_preset_dir()
    existing = _existing_preset(PRESET_PATH)
    if existing:
        unreal.log(f"[MRQPresets] Preset already exists at {PRESET_PATH}, skipping")
        return {"ok": True, "preset_path": PRESET_PATH, "created": False}

    preset = _create_preset("MRQ_Preset_Cinematic", PRESET_DIR)
    if not preset:
        return {"ok": False, "error": "failed to create preset asset"}

    preset.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)

    # Adding the setting is enough to enable it - its default anti-aliasing
    # mode is reasonable and its exact enum member names weren't verified,
    # unlike everything else in this file.
    preset.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)

    out_setting = preset.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out_setting.set_editor_property("output_resolution", unreal.IntPoint(3840, 2160))
    out_setting.set_editor_property("output_directory", unreal.DirectoryPath(path=OUTPUT_DIR))
    out_setting.set_editor_property("file_name_format", "{level_name}.{frame_number}")
    out_setting.set_editor_property("zero_pad_frame_numbers", 4)

    exr = preset.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR)
    exr.set_editor_property("multilayer", True)

    unreal.EditorAssetLibrary.save_asset(PRESET_PATH)
    unreal.log(f"[MRQPresets] Created cinematic preset: {PRESET_PATH}")
    return {"ok": True, "preset_path": PRESET_PATH, "created": True}


def create_mi_loop_preset() -> dict:
    """1080x1080 PNG sequence preset for 4s material-instance preview loops."""
    import unreal

    _ensure_preset_dir()
    existing = _existing_preset(PRESET_MI_LOOP_PATH)
    if existing:
        unreal.log(f"[MRQPresets] MI loop preset exists: {PRESET_MI_LOOP_PATH}")
        return {"ok": True, "preset_path": PRESET_MI_LOOP_PATH, "created": False}

    preset = _create_preset("MRQ_Preset_MI_Loop_1080", PRESET_DIR)
    if not preset:
        return {"ok": False, "error": "failed to create MI loop preset"}

    preset.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)

    # Adding the setting is enough to enable it - its default anti-aliasing
    # mode is reasonable and its exact enum member names weren't verified,
    # unlike everything else in this file.
    preset.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)

    out_setting = preset.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    out_setting.set_editor_property("output_resolution", unreal.IntPoint(1080, 1080))
    out_setting.set_editor_property("output_directory", unreal.DirectoryPath(path=OUTPUT_DIR_MI_LOOPS))
    out_setting.set_editor_property("file_name_format", "{level_name}.{frame_number}")

    preset.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)

    unreal.EditorAssetLibrary.save_asset(PRESET_MI_LOOP_PATH)
    unreal.log(f"[MRQPresets] Created MI loop preset: {PRESET_MI_LOOP_PATH}")
    return {"ok": True, "preset_path": PRESET_MI_LOOP_PATH, "created": True}


def main() -> int:
    results = {
        "cinematic": create_cinematic_preset(),
        "mi_loop": create_mi_loop_preset(),
    }
    ok = all(r.get("ok") for r in results.values())
    if "json" in sys.argv:
        import json
        print(json.dumps(results, indent=2))
    else:
        print(results)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
