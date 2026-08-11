"""Create per-MI Level Sequences with camera orbit for loop captures.

Run in-editor with L_MaterialPreview_Studio loaded:
  py Content/Python/setup_mi_preview_sequences.py
  py Content/Python/setup_mi_preview_sequences.py --only MI_ZenTrim_FlowersLots
"""
from __future__ import annotations

import json
import math
import sys

import mi_preview_manifest as manifest_mod
import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "mi_preview_sequences.json"


def _parse_only_arg() -> str | None:
    for index, arg in enumerate(sys.argv):
        if arg == "--only" and index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return None


def _find_sequence_class():
    import unreal

    cls = getattr(unreal, "LevelSequence", None)
    if cls:
        return cls
    raise RuntimeError("LevelSequence class not found")


def _find_subsystem():
    import unreal

    cls = getattr(unreal, "LevelSequenceEditorSubsystem", None)
    if not cls:
        raise RuntimeError("LevelSequenceEditorSubsystem not found")
    return unreal.get_editor_subsystem(cls)


def _find_camera(eas):
    import unreal

    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == studio.TAG_CAMERA:
            return actor
        if isinstance(actor, unreal.CineCameraActor):
            return actor
    return None


def _ensure_sequence_asset(asset_tools, entry: dict) -> tuple[object, bool]:
    import unreal

    seq_path = str(entry.get("sequence_path") or studio.sequence_path_for_mi(entry["id"]))
    name = seq_path.rsplit("/", 1)[-1]
    package_path = f"{seq_path}.{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(seq_path):
        existing = unreal.EditorAssetLibrary.load_asset(package_path)
        if existing:
            return existing, False
    folder = seq_path.rsplit("/", 1)[0]
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

    SeqClass = _find_sequence_class()
    sequence = asset_tools.create_asset(name, folder, SeqClass, None)
    if not sequence:
        raise RuntimeError(f"failed to create sequence: {seq_path}")
    return sequence, True


def _bind_camera_orbit(sequence, camera, entry: dict) -> dict:
    import unreal

    mi_id = entry["id"]
    frames = studio.LOOP_FRAMES
    fps = studio.FRAME_RATE

    sequence.set_display_rate(unreal.FrameRate(fps, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(frames)

    # Do not notify LevelSequenceEditorSubsystem here. In UE 5.8 that callback
    # routes through SequencerScripting and can dereference a null editor
    # sequence context when the script is running unattended/headless. MRQ
    # only needs the saved asset and does not need a docked Sequencer tab.

    try:
        bindings = list(sequence.get_bindings() or [])
    except Exception:
        bindings = []
    for binding in bindings:
        try:
            sequence.remove_binding(binding)
        except Exception:
            pass

    try:
        for track in list(sequence.get_master_tracks() or []):
            sequence.remove_master_track(track)
    except Exception:
        pass

    binding = sequence.add_possessable(camera)
    if not binding:
        return {"ok": False, "error": "camera_bind_failed", "id": mi_id}

    binding_id = binding.get_id()

    cut_track = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)
    if cut_track:
        section = cut_track.add_section()
        section.set_range(0, frames)
        try:
            section.set_camera_binding_id(binding_id)
        except Exception:
            section.set_editor_property("camera_binding_id", binding_id)

    transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)
    if not transform_track:
        return {"ok": False, "error": "transform_track_failed", "id": mi_id}

    xform_section = transform_track.add_section()
    xform_section.set_range(0, frames)

    key_frames = [0, frames // 4, frames // 2, 3 * frames // 4, frames]
    for frame in key_frames:
        pos = studio.orbit_camera_position(frame, total_frames=frames)
        rot = studio.look_at_rotation(pos)
        fn = unreal.FrameNumber(frame)
        xform_section.add_key(fn, unreal.Name("Location.X"), float(pos[0]))
        xform_section.add_key(fn, unreal.Name("Location.Y"), float(pos[1]))
        xform_section.add_key(fn, unreal.Name("Location.Z"), float(pos[2]))
        xform_section.add_key(fn, unreal.Name("Rotation.Pitch"), float(rot[0]))
        xform_section.add_key(fn, unreal.Name("Rotation.Yaw"), float(rot[1]))
        xform_section.add_key(fn, unreal.Name("Rotation.Roll"), float(rot[2]))

    seq_path = str(entry.get("sequence_path") or studio.sequence_path_for_mi(mi_id))
    unreal.EditorAssetLibrary.save_asset(seq_path)
    return {"ok": True, "id": mi_id, "sequence_path": seq_path, "frames": frames}


def build_sequences(*, only: str | None = None) -> dict:
    import unreal
    import mi_preview_apply as apply_mod

    manifest = manifest_mod.load_manifest()
    entries = manifest_mod.filter_entries(manifest, only=only)
    if not entries:
        return {"ok": False, "error": "no_manifest_entries", "only": only}

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(studio.LEVEL)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    camera = _find_camera(eas)
    if not camera:
        return {"ok": False, "error": "camera_missing_in_studio"}

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    unreal.EditorAssetLibrary.make_directory(studio.MRQ_SEQUENCES_DIR)

    results: list[dict] = []
    for entry in entries:
        apply_mod.apply_preview_entry(entry)
        try:
            sequence, created = _ensure_sequence_asset(asset_tools, entry)
            bind = _bind_camera_orbit(sequence, camera, entry)
            bind["created"] = created
            results.append(bind)
        except Exception as exc:
            results.append({"ok": False, "id": entry.get("id"), "error": str(exc)})

    report = {
        "ok": all(r.get("ok") for r in results),
        "count": len(results),
        "only": only,
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    result = build_sequences(only=_parse_only_arg())
    if "json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
