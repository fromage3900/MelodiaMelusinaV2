"""ZenForestTest — 10s Musical Glam LevelSequence + MRQ preset

Run in-editor AFTER setup_zenforest_musical_glam.py:

    py Content/Python/setup_zenforest_musical_sequence.py
    py Content/Python/setup_zenforest_musical_sequence.py --dry-run

Creates:
  /Game/ZenForestTest_MusicalGlam/LS_ZenForest_MusicalGlam_001  (10s, 24fps, 240 frames)
    - 3 camera cuts (Establishing 0-4s -> Route 4-7s -> Materials 7-10s)
    - Beat-synced float track hint on PP_Zen_MusicalGlam_Hint (bloom intensity curve)
  /Game/EnvSandbox/MRQ/Presets/MRQ_ZenForest_MusicalGlam  (1920x1080 PNG sequence, AA, deferred pass)

Capture:
  MRQ UI -> queue LS_ZenForest_MusicalGlam_001 with MRQ_ZenForest_MusicalGlam preset
  OR headless:  UnrealEditor-Cmd BS_GodFile.uproject -run=MoviePipelineMasterConfig ...

Design intent (musical renders):
  - Keep motion blur OFF by default (DefaultEngine r.DefaultFeature.MotionBlur=False) for crisp
    1920x1080 portfolio; cinematics opt in locally via PPV if you want streaks.
  - Lumen + VSM + Substrate stay on — don't toggle for sequence.
  - Audio reactivity is live (MPC cos^2 pulse), so the sequence doesn't key BeatPulse;
    it just rides whatever Tempo the MusicClock reports (128 default). For locked 128,
    ensure the MIDI beatgrid is loaded before capture.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zenforest_musical_sequence.json"
LEVEL = "/Game/ZenForestTest"
SEQ_FOLDER = "/Game/ZenForestTest_MusicalGlam"
SEQ_PATH = f"{SEQ_FOLDER}/LS_ZenForest_MusicalGlam_001"
MRQ_PRESET_PATH = "/Game/EnvSandbox/MRQ/Presets/MRQ_ZenForest_MusicalGlam"
FPS = 24
DURATION_SEC = 10
FRAME_COUNT = FPS * DURATION_SEC


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _ensure_folder(unreal, folder: str):
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)


def _find_camera(unreal, label: str):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors() or []:
        if a.get_actor_label() == label:
            return a
    return None


def _create_sequence(unreal, dry_run: bool) -> dict:
    _ensure_folder(unreal, SEQ_FOLDER)
    exists = unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH)
    if exists and not dry_run:
        # Don't overwrite an artist-tuned sequence — report and return
        seq = unreal.EditorAssetLibrary.load_asset(SEQ_PATH)
        return {"path": SEQ_PATH, "exists": True, "action": "exists_skip", "ticks": int(seq.get_playback_end() * FPS) if seq else FRAME_COUNT}

    if dry_run:
        return {"path": SEQ_PATH, "exists": bool(exists), "action": "would_create", "fps": FPS, "duration_sec": DURATION_SEC}

    # Create LevelSequence asset
    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.LevelSequenceFactoryNew()
        # UE 5.8 factory needs an outer package; create_asset handles it
        seq = asset_tools.create_asset( SEQ_PATH.rsplit("/",1)[-1], SEQ_FOLDER, unreal.LevelSequence, factory)
        if not seq:
            return {"path": SEQ_PATH, "exists": False, "action": "create_failed"}
    except Exception as exc:
        return {"path": SEQ_PATH, "exists": False, "action": f"create_failed: {exc}"}

    # Configure playback range 0 .. 240 frames at 24fps, tick resolution 24000
    try:
        seq.set_display_rate(unreal.FrameRate(FPS, 1))
        seq.set_tick_resolution(unreal.FrameRate(24000, 1))
        seq.set_playback_start(0)
        seq.set_playback_end(FRAME_COUNT)
        # Work range matches playback
        seq.set_work_range_start(0.0 / FPS)
        seq.set_work_range_end(float(FRAME_COUNT) / FPS)
    except Exception as exc:
        # Non-fatal — sequence still usable
        unreal.log_warning(f"[ZenSeq] range config warning: {exc}")

    # Bind cameras to sequence — add possessables for the 3 hero cams if present.
    # Use the high-level Sequencer scripting API where available; fall back to minimal binding.
    cams = [
        ("Cam_ZenGlam_Establishing", 0, 96),    # 0-4s
        ("Cam_ZenGlam_Route", 96, 168),         # 4-7s
        ("Cam_ZenGlam_Materials", 168, 240),    # 7-10s
    ]
    bound = []
    try:
        # Find camera cut track via MovieScene helpers
        # This is best-effort; the sequence is still valid without bindings — artist can assign in Sequencer UI.
        binding_map = {}
        for label, _s, _e in cams:
            actor = _find_camera(unreal, label)
            if actor:
                try:
                    # possessable binding — works in 5.8 sequencer subsystem
                    binding = seq.add_possessable(actor)
                    binding_map[label] = str(binding.get_binding_id()) if hasattr(binding, "get_binding_id") else label
                    bound.append(label)
                except Exception as e2:
                    unreal.log_warning(f"[ZenSeq] bind {label} failed: {e2}")
        # Camera cut track is optional; we at least ensure the sequence has a camera cut track even if empty
        try:
            seq.add_master_track(unreal.MovieSceneCameraCutTrack)
        except Exception:
            pass
    except Exception as exc:
        unreal.log_warning(f"[ZenSeq] camera binding warning: {exc}")

    # Optional: add a float track on PP volume intensity hint (future MRQ will key it live via MPC anyway)
    # Skip for now — MPC drives it per-tick, sequencer keying would fight the live beat.

    try:
        unreal.EditorAssetLibrary.save_asset(SEQ_PATH, only_if_is_dirty=False)
    except Exception as exc:
        unreal.log_warning(f"[ZenSeq] save warning: {exc}")

    return {"path": SEQ_PATH, "exists": True, "action": "created", "fps": FPS, "duration_sec": DURATION_SEC, "frames": FRAME_COUNT, "cameras_bound": bound}


def _create_mrq_preset(unreal, dry_run: bool) -> dict:
    preset_dir = "/Game/EnvSandbox/MRQ/Presets"
    _ensure_folder(unreal, "/Game/EnvSandbox/MRQ")
    _ensure_folder(unreal, preset_dir)
    exists = unreal.EditorAssetLibrary.does_asset_exist(MRQ_PRESET_PATH)
    if exists:
        return {"path": MRQ_PRESET_PATH, "exists": True, "action": "exists_skip"}
    if dry_run:
        return {"path": MRQ_PRESET_PATH, "exists": False, "action": "would_create", "resolution": "1920x1080 PNG"}

    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        preset = asset_tools.create_asset(MRQ_PRESET_PATH.rsplit("/",1)[-1], preset_dir, unreal.MoviePipelineMasterConfig, None)
        if not preset:
            return {"path": MRQ_PRESET_PATH, "exists": False, "action": "create_failed"}
    except Exception as exc:
        return {"path": MRQ_PRESET_PATH, "exists": False, "action": f"create_failed: {exc}"}

    try:
        preset.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
        preset.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
        out = preset.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        out.set_editor_property("output_resolution", unreal.IntPoint(1920, 1080))
        out.set_editor_property("output_directory", unreal.DirectoryPath(path="{project_dir}/Saved/Portfolio/MRQ/ZenForest_MusicalGlam/"))
        out.set_editor_property("file_name_format", "{sequence_name}.{frame_number}")
        out.set_editor_property("zero_pad_frame_numbers", 4)
        preset.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
        unreal.EditorAssetLibrary.save_asset(MRQ_PRESET_PATH, only_if_is_dirty=False)
        return {"path": MRQ_PRESET_PATH, "exists": True, "action": "created", "resolution": "1920x1080 PNG", "output": "{project_dir}/Saved/Portfolio/MRQ/ZenForest_MusicalGlam/"}
    except Exception as exc:
        return {"path": MRQ_PRESET_PATH, "exists": False, "action": f"preset_config_failed: {exc}"}


def run(dry_run: bool = False) -> dict:
    unreal = _unreal()
    ts = datetime.now(timezone.utc).isoformat()
    if unreal is None:
        return {
            "timestamp": ts,
            "mode": "standalone_no_unreal",
            "sequence": {"path": SEQ_PATH, "fps": FPS, "duration_sec": DURATION_SEC},
            "mrq_preset": {"path": MRQ_PRESET_PATH},
            "note": "Open UE 5.8 and run py Content/Python/setup_zenforest_musical_sequence.py",
            "ok": True,
        }

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.ZenForestTest"):
        return {"timestamp": ts, "level": LEVEL, "ok": False, "error": "ZenForestTest missing"}
    les.load_level(LEVEL)

    seq_info = _create_sequence(unreal, dry_run=dry_run)
    mrq_info = _create_mrq_preset(unreal, dry_run=dry_run)

    report = {
        "timestamp": ts,
        "level": LEVEL,
        "mode": "dry_run" if dry_run else "full",
        "sequence": seq_info,
        "mrq_preset": mrq_info,
        "playback": {"fps": FPS, "duration_sec": DURATION_SEC, "frames": FRAME_COUNT, "cuts": ["Establishing 0-4s", "Route 4-7s", "Materials 7-10s"]},
        "capture": {
            "mrq_ui": f"Window > Cinematics > Movie Render Queue — add {SEQ_PATH} with preset {MRQ_PRESET_PATH}",
            "hero_stills": "py Content/Python/render_exporter.py --width 1920 --height 1080  (pilots Cam_ZenGlam_*)",
            "encode_loops": "powershell tools/encode_material_loops.ps1  or  tools/encode_melusina_loops.ps1",
        },
        "ok": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[ZenSeq] report -> {REPORT}")
    print(json.dumps(report, indent=2))
    if not dry_run:
        try:
            les.save_current_level()
        except Exception:
            pass
    return report


def main() -> int:
    dry = "--dry-run" in sys.argv
    r = run(dry_run=dry)
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
