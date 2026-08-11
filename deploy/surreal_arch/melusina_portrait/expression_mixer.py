"""Expression mixer ΓÇö keyframe blendshapes on the Melusina armature from a viseme track.

Pipeline:
  1. Parse voice file ΓåÆ VoiceTrack (phoneme_reader)
  2. Detect viseme bindings on armature (viseme_mapper)
  3. For each animation frame:
       a. Compute viseme weights from active phoneme(s)
       b. Add idle animation overlay (blink, breath, subtle sway)
       c. Set keyframes on shape keys of the armature's mesh children
  4. Output: keyframed Blender animation ready to play or export
"""

from __future__ import annotations

import bpy
from mathutils import Vector

from .phoneme_reader import VoiceTrack, PhonemeEvent
from .viseme_mapper import (
    VISEMES,
    VisemeBinding,
    VisemeDef,
    detect_rig_blendshapes,
    get_bound_viseme_map,
    get_rig_mesh_targets,
    phoneme_to_viseme_code,
    get_viseme_weights,
)


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Settings container (stored on the armature or scene)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

@dataclass
class PortraitSettings:
    """Config for portrait generation."""
    fps: int = 24
    blend_strength: float = 1.0      # overall blendshape intensity 0-1
    idle_amplitude: float = 0.15     # breathing / sway amount
    eye_blink_rate: float = 4.0      # blinks per second (average)
    eye_blink_duration: float = 0.1  # seconds per blink
    smooth_frames: int = 2           # interpolation window for viseme transitions


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Core keyframe engine
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def generate_portrait_animation(
    armature_obj,
    track: VoiceTrack,
    settings: PortraitSettings | None = None,
) -> dict:
    """Generate lip-sync + idle animation from a voice track onto the rig.

    Returns a status dict with frame_count, visemes_used, any errors.
    """
    if settings is None:
        settings = PortraitSettings()

    if armature_obj is None or armature_obj.type != "ARMATURE":
        return {"error": "No armature selected", "frame_count": 0}

    # Detect viseme bindings
    viseme_map = get_bound_viseme_map(armature_obj)
    mesh_targets = get_rig_mesh_targets(armature_obj)

    if not viseme_map:
        return {"error": "No viseme blendshapes detected on rig", "frame_count": 0,
                "hint": "Run viseme detection first"}

    # Compute frame range
    total_duration = max(track.total_duration_sec, 0.5)
    start_frame = 1
    end_frame = int(total_duration * settings.fps) + 2  # pad 2 frames for decay

    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame
    scene.render.fps = settings.fps

    # Clear existing animation on shape keys
    _clear_shape_key_animation(armature_obj, viseme_map, mesh_targets)

    # Generate keyframes per frame
    for frame in range(start_frame, end_frame + 1):
        time_sec = (frame - 1) / settings.fps

        # 1. Compute viseme weights from active phoneme(s)
        viseme_weights = _compute_frame_viseme_weights(
            track, time_sec, settings
        )

        # 2. Add idle animation overlay
        idle_overlay = _compute_idle_overlay(
            time_sec, settings, total_duration
        )

        # 3. Merge and apply to shape keys
        _apply_shape_keys(
            armature_obj, frame,
            viseme_weights, idle_overlay,
            viseme_map, mesh_targets,
            settings,
        )

    # Set timeline
    scene.frame_current = start_frame

    visemes_used = sorted(set(viseme_map.keys()))

    return {
        "frame_count": end_frame - start_frame + 1,
        "duration_sec": total_duration,
        "visemes_used": visemes_used,
        "viseme_count": len(visemes_used),
        "start_frame": start_frame,
        "end_frame": end_frame,
        "track_name": track.name,
    }


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Internal helpers
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def _compute_frame_viseme_weights(
    track: VoiceTrack,
    time_sec: float,
    settings: PortraitSettings,
) -> dict[str, float]:
    """Compute viseme weight for a single frame from the voice track.

    Uses smooth blending: when near a phoneme boundary,
    blends evenly between the outgoing and incoming viseme.
    """
    # Find the active phoneme at this time
    active: PhonemeEvent | None = None
    next_event: PhonemeEvent | None = None

    for ev in track.events:
        if ev.start_sec <= time_sec < ev.end_sec:
            active = ev
            # Find the next event (for transition blending)
            for nev in track.events:
                if nev.start_sec >= ev.end_sec:
                    next_event = nev
                    break
            break

    if active is None:
        return {"rest": 1.0}

    code = phoneme_to_viseme_code(active.phoneme)

    # Check if we're near a boundary for smooth transition
    transition = 0.0
    if next_event:
        remaining = active.end_sec - time_sec
        half_window = (1.0 / settings.fps) * settings.smooth_frames
        if remaining < half_window and next_event:
            # Blend toward next viseme
            transition = 1.0 - (remaining / half_window) if half_window > 0 else 0.0
            transition = max(0.0, min(1.0, transition))

    weights = {v.code: 0.0 for v in VISEMES}
    weights[code] = 1.0 - transition

    if transition > 0.0 and next_event:
        next_code = phoneme_to_viseme_code(next_event.phoneme)
        weights[next_code] = transition

    return weights


def _compute_idle_overlay(
    time_sec: float,
    settings: PortraitSettings,
    total_duration: float,
) -> dict[str, float]:
    """Compute subtle idle animation weights.

    Returns a dict of shape_key_name ΓåÆ value for:
      - Eye blink (periodic)
      - Breath (sinusoidal chest rise)
      - Subtle head sway (sinusoidal)
    """
    overlay: dict[str, float] = {}

    # Periodic eye blink
    blink_period = 1.0 / max(settings.eye_blink_rate, 0.1)
    blink_phase = (time_sec % blink_period) / blink_period
    blink_dur_ratio = settings.eye_blink_duration / blink_period
    if blink_phase < blink_dur_ratio:
        # Triangular blink: 0ΓåÆ1ΓåÆ0
        t = blink_phase / blink_dur_ratio
        blink_val = 1.0 - abs(2.0 * t - 1.0)  # peak at t=0.5
        overlay["_idle_blink"] = blink_val * settings.idle_amplitude
    else:
        overlay["_idle_blink"] = 0.0

    # Subtle breathing ΓÇö smooth sinusoidal chest motion
    import math
    breath_val = math.sin(time_sec * 1.2) * 0.5 + 0.5  # 0-1 range, ~5s cycle
    overlay["_idle_breath"] = breath_val * settings.idle_amplitude * 0.3

    # Gaze direction subtle sway
    sway = math.sin(time_sec * 0.7) * settings.idle_amplitude * 0.2
    overlay["_idle_sway"] = sway

    return overlay


def _apply_shape_keys(
    armature_obj,
    frame: int,
    viseme_weights: dict[str, float],
    idle_overlay: dict[str, float],
    viseme_map: dict[str, str],
    mesh_targets: dict[str, str],
    settings: PortraitSettings,
):
    """Set keyframes on shape keys for a single frame."""
    for viseme_code, weight in viseme_weights.items():
        if weight <= 0.001 and viseme_code != "rest":
            continue
        key_name = viseme_map.get(viseme_code)
        if key_name is None:
            continue

        # Find the mesh data that owns this shape key
        mesh_name = mesh_targets.get(key_name)
        mesh_obj = _find_mesh_child(armature_obj, mesh_name) if mesh_name else None
        if mesh_obj is None:
            # Fallback: search all children
            mesh_obj = _find_shape_key_owner(armature_obj, key_name)
        if mesh_obj is None:
            continue

        kb = mesh_obj.data.shape_keys.key_blocks.get(key_name)
        if kb is None:
            continue

        val = weight * settings.blend_strength
        kb.value = val
        kb.keyframe_insert("value", frame=frame)

    # Apply idle overlays to compatible shape keys
    for idle_key, idle_val in idle_overlay.items():
        if idle_val < 0.001:
            continue
        _apply_idle_to_best_match(
            armature_obj, frame, idle_key, idle_val, mesh_targets, settings
        )


def _apply_idle_to_best_match(
    armature_obj,
    frame: int,
    idle_key: str,
    value: float,
    mesh_targets: dict[str, str],
    settings: PortraitSettings,
):
    """Try to apply an idle overlay to a compatible shape key on the rig."""
    # Map idle keys to common blendshape name patterns
    patterns = {
        "_idle_blink": ["blink", "eye_close", "eyeClosed", "eyes_closed", "Eyelid_Close"],
        "_idle_breath": ["breath", "chest_breathe", "torso_breath", "Breath"],
        "_idle_sway": ["head_sway", "neck_sway", "Head_Sway"],
    }
    candidates = patterns.get(idle_key, [])
    for child in armature_obj.children_recursive:
        if child.type != "MESH":
            continue
        data = child.data
        if not hasattr(data, "shape_keys") or data.shape_keys is None:
            continue
        for pat in candidates:
            for kb in data.shape_keys.key_blocks:
                if pat.lower() in kb.name.lower():
                    kb.value = value
                    kb.keyframe_insert("value", frame=frame)
                    return


def _find_mesh_child(armature_obj, name: str):
    """Find a mesh child by name."""
    if name is None:
        return None
    for child in armature_obj.children_recursive:
        if child.type == "MESH" and child.name == name:
            return child
    return None


def _find_shape_key_owner(armature_obj, key_name: str):
    """Walk armature children to find the mesh owning a shape key."""
    for child in armature_obj.children_recursive:
        if child.type != "MESH":
            continue
        data = child.data
        if not hasattr(data, "shape_keys") or data.shape_keys is None:
            continue
        if key_name in data.shape_keys.key_blocks:
            return child
    return None


def _clear_shape_key_animation(
    armature_obj,
    viseme_map: dict[str, str],
    mesh_targets: dict[str, str],
):
    """Remove all existing keyframes from shape keys used by visemes."""
    for key_name in viseme_map.values():
        for child in armature_obj.children_recursive:
            if child.type != "MESH":
                continue
            data = child.data
            if not hasattr(data, "shape_keys") or data.shape_keys is None:
                continue
            if key_name in data.shape_keys.key_blocks:
                kb = data.shape_keys.key_blocks[key_name]
                if kb.animation_data and kb.animation_data.action:
                    kb.animation_data_clear()
                kb.value = 0.0


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# High-level convenience
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def clear_all_portrait_animation(armature_obj) -> int:
    """Remove all keyframed shape key animation from the rig. Returns count cleared."""
    count = 0
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return 0
    for child in armature_obj.children_recursive:
        if child.type != "MESH":
            continue
        data = child.data
        if not hasattr(data, "shape_keys") or data.shape_keys is None:
            continue
        for kb in data.shape_keys.key_blocks:
            if kb.animation_data and kb.animation_data.action:
                kb.animation_data_clear()
                kb.value = 0.0
                count += 1
    return count
