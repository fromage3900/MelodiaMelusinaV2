"""Create a cinematic LevelSequence for L_SakuraPath with a 10s orbit.

Run in-editor with L_SakuraPath loaded:
  py Content/Python/setup_sakura_sequence.py

Outputs:
  /Game/EnvSandbox/MRQ/Sequences/Sakura_Path_Cinematic
"""
from __future__ import annotations

import sys

SEQUENCE_PATH = "/Game/EnvSandbox/MRQ/Sequences/Sakura_Path_Cinematic"
DURATION_FRAMES = 600  # 10s at 60fps
FRAME_RATE = 60


def _find_sequence_class():
    import unreal

    cand = getattr(unreal, "LevelSequence", None)
    if cand:
        return cand
    for name in ["LevelSequence", "MovieSceneSequence"]:
        c = getattr(unreal, name, None)
        if c:
            return c
    raise RuntimeError("LevelSequence class not found")


def _find_subsystem():
    import unreal

    cand = getattr(unreal, "LevelSequenceEditorSubsystem", None)
    if cand:
        return unreal.get_editor_subsystem(cand)
    raise RuntimeError("LevelSequenceEditorSubsystem not found")


def _find_camera_in_world() -> object | None:
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors() or []:
        cls = actor.get_class()
        cine_cls = unreal.CineCameraActor.static_class()
        if cls == cine_cls or getattr(cls, "get_name", lambda: "")() == "CineCameraActor":
            return actor
    return None


def find_or_create_sakura_sequence() -> dict:
    import unreal

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()

    existing = asset_reg.get_asset_by_object_path(SEQUENCE_PATH)
    if existing and existing.is_valid():
        unreal.log(f"[SakuraSequence] Sequence already exists at {SEQUENCE_PATH}")
        return {"ok": True, "sequence_path": SEQUENCE_PATH, "created": False}

    unreal.EditorAssetLibrary.make_directory("/Game/EnvSandbox/MRQ/Sequences")

    SeqClass = _find_sequence_class()
    sequence = asset_tools.create_asset("Sakura_Path_Cinematic", "/Game/EnvSandbox/MRQ/Sequences", SeqClass, None)
    if not sequence:
        return {"ok": False, "error": "failed to create sequence asset"}

    sequence.set_display_rate(unreal.FrameRate(FRAME_RATE, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(DURATION_FRAMES)

    subsys = _find_subsystem()
    if hasattr(subsys, "on_level_sequence_created"):
        subsys.on_level_sequence_created(sequence)

    unreal.log(f"[SakuraSequence] Created empty sequence: {SEQUENCE_PATH}")
    return {"ok": True, "sequence_path": SEQUENCE_PATH, "created": True}


def bind_camera_to_sequence(sequence_path: str = SEQUENCE_PATH) -> dict:
    import unreal

    asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
    seq_data = asset_reg.get_asset_by_object_path(sequence_path)
    if not seq_data or not seq_data.is_valid():
        return {"ok": False, "error": f"sequence not found: {sequence_path}"}

    sequence = seq_data.get_asset()
    camera = _find_camera_in_world()
    if not camera:
        return {"ok": False, "error": "no CineCameraActor found in current level"}

    binding = sequence.add_possessable(camera)
    if not binding:
        return {"ok": False, "error": "failed to add camera binding to sequence"}

    binding_id = binding.get_id()
    unreal.log(f"[SakuraSequence] Bound camera '{camera.get_actor_label()}' to sequence (id={binding_id})")

    track = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)
    if not track:
        return {"ok": False, "error": "failed to add camera cut track"}

    section = track.add_section()
    section.set_start_frame(0)
    section.set_end_frame(DURATION_FRAMES)
    section.set_parameters(unreal.SectionEvaluationData(binding_id))
    section.set_editor_property("start_frame", 0)
    section.set_editor_property("end_frame", DURATION_FRAMES)

    transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)
    if transform_track:
        xform_section = transform_track.add_section()
        xform_section.set_start_frame(0)
        xform_section.set_end_frame(DURATION_FRAMES)

        import math

        orbit_radius = 400.0
        for frame in [0, DURATION_FRAMES // 2, DURATION_FRAMES]:
            angle = 2.0 * math.pi * (frame / DURATION_FRAMES)
            x = orbit_radius * math.cos(angle)
            y = orbit_radius * math.sin(angle)
            z = 50.0
            xform_section.add_key(unreal.FrameNumber(frame), unreal.Name("Location.X"), x)
            xform_section.add_key(unreal.FrameNumber(frame), unreal.Name("Location.Y"), y)
            xform_section.add_key(unreal.FrameNumber(frame), unreal.Name("Location.Z"), z)

    unreal.EditorAssetLibrary.save_asset(sequence_path)
    unreal.log(f"[SakuraSequence] Camera orbit complete for {sequence_path}")
    return {"ok": True, "sequence_path": sequence_path, "camera": camera.get_actor_label()}


def setup_complete() -> dict:
    seq_result = find_or_create_sakura_sequence()
    if not seq_result.get("ok"):
        return seq_result
    bind_result = bind_camera_to_sequence()
    return bind_result


def main() -> int:
    result = setup_complete()
    if "json" in sys.argv:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
