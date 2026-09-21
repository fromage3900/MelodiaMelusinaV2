# Resonance Loom - operators (beatgrid import, paint groups, bake, validate, export).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# melodia_utils import follows the sibling-addon pattern (guarded, path-fixed)
# so the addon finds its repo without assuming a drive letter.

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

from .loom_core import lanes
from .loom_core import naming
from .loom_core.midi_grid import MidiParseError, load_beatgrid
from .loom_core.sidecar import build_sidecar, pattern_density, write_sidecar

try:
    import melodia_utils as _mu  # type: ignore
except Exception:
    _ADDONS_ROOT = str(Path(__file__).resolve().parents[2])
    if _ADDONS_ROOT not in sys.path:
        sys.path.insert(0, _ADDONS_ROOT)
    try:
        import melodia_utils as _mu  # type: ignore
    except Exception:
        _mu = None  # type: ignore

_MAX_MARKERS = 512  # keep the timeline sane on dense charts
_TOOLS_DIR = Path(__file__).resolve().parents[3]  # addon -> BlenderAddons -> Tools -> root


def default_beatgrid_path() -> str:
    """Project beatgrid via melodia_utils discovery; empty when unavailable."""
    if _mu is None:
        return ""
    try:
        for candidate in _mu.discover_midi():
            if "beatgrid" in candidate.name.lower():
                return str(candidate)
    except Exception:
        pass
    return ""


def default_export_dir() -> str:
    if _mu is None:
        return ""
    try:
        return str(Path(_mu.repo_root()) / "Imports" / "Meshes" / "Loom")
    except Exception:
        return ""


def _validation_findings(context) -> list[tuple[str, str]]:
    """(severity, message) checks for the current garment authoring state."""
    loom = context.scene.loom
    findings: list[tuple[str, str]] = []
    if not loom.beatgrid_loaded:
        findings.append(("ERROR", "No beatgrid imported. Run Import Beatgrid first."))
    if not naming.is_valid_cosmetic_id(loom.cosmetic_id):
        findings.append(("ERROR", f"Cosmetic id {loom.cosmetic_id!r} must be Cos_<Name>."))
    mesh = context.active_object
    if mesh is not None and mesh.type == "MESH" and mesh.data.shape_keys:
        key_blocks = mesh.data.shape_keys.key_blocks
        for key in (naming.ACCENT_SHAPE_KEY, naming.HIT_SHAPE_KEY):
            if key not in key_blocks:
                findings.append(("WARNING", f"Shape key {key} not baked yet."))
        all_names = [kb.name for kb in key_blocks]
        collisions = naming.short_name_collisions(all_names)
        if collisions:
            findings.append(("ERROR", f"Case-insensitive name collisions: {collisions}"))
    return findings


class LOOM_OT_import_beatgrid(bpy.types.Operator):
    """Parse the project beatgrid MIDI and place downbeat/accent markers on the timeline"""

    bl_idname = "melodia_loom.import_beatgrid"
    bl_label = "Import Beatgrid"
    bl_options = {"REGISTER", "UNDO"}

    midi_path: bpy.props.StringProperty(name="MIDI", subtype="FILE_PATH")

    def execute(self, context):
        path = self.midi_path or context.scene.loom.midi_path or default_beatgrid_path()
        if not path:
            self.report({"ERROR"}, "No beatgrid MIDI set. Pick 128BPMarpeggiomelody_beatgrid.mid")
            return {"CANCELLED"}
        try:
            grid = load_beatgrid(path)
        except (MidiParseError, OSError) as exc:
            self.report({"ERROR"}, f"Beatgrid parse failed: {exc}")
            return {"CANCELLED"}

        loom = context.scene.loom
        loom.midi_path = path
        loom.bpm = round(grid.bpm, 2)
        loom.duration_sec = round(grid.duration_sec, 4)
        loom.pattern_density = pattern_density(grid)
        loom.beatgrid_loaded = True

        skill = loom.skill_id if loom.skill_id in lanes.SKILL_IDS else sorted(lanes.SKILL_IDS)[0]
        cosmetic = loom.cosmetic_id or "Cos_Dress_Authoring"
        sidecar = build_sidecar(grid, cosmetic, skill, midi_file=path,
                                lane_strategy=loom.lane_strategy)
        loom.lane_hits_json = json.dumps(sidecar.lane_hits)

        fps = context.scene.render.fps
        for marker in [m for m in context.scene.timeline_markers if m.name.startswith("LOOM_")]:
            context.scene.timeline_markers.remove(marker)
        for count, beat_idx in enumerate(grid.downbeat_indices()):
            if count >= _MAX_MARKERS:
                break
            frame = round(beat_idx * grid.seconds_per_beat * fps) + 1
            context.scene.timeline_markers.new(f"LOOM_DOWN_{count + 1:03d}", frame=frame)
        for count, note in enumerate([n for n in grid.notes if n.velocity >= 96]):
            if count >= _MAX_MARKERS:
                break
            frame = round(note.start_sec * fps) + 1
            context.scene.timeline_markers.new(f"LOOM_ACC_{count + 1:03d}", frame=frame)

        self.report(
            {"INFO"},
            f"{grid.bpm:.0f} BPM, {len(grid.notes)} notes, "
            f"{len(grid.downbeat_indices())} bars, density {loom.pattern_density:.2f}",
        )
        return {"FINISHED"}


class LOOM_OT_ensure_paint_groups(bpy.types.Operator):
    """Create the three LOOM vertex groups on the active mesh (paint targets)"""

    bl_idname = "melodia_loom.ensure_paint_groups"
    bl_label = "Ensure Paint Groups"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        mesh = context.active_object
        created = []
        for group in naming.LOOM_VGROUPS:
            if group not in mesh.vertex_groups:
                mesh.vertex_groups.new(name=group)
                created.append(group)
        if created:
            self.report({"INFO"}, f"Created: {', '.join(created)}")
        else:
            self.report({"INFO"}, "All LOOM paint groups already present")
        return {"FINISHED"}


class LOOM_OT_bake_rhythm_keys(bpy.types.Operator):
    """Bake the LOOM paint groups into rhythm shape keys (Tier A authored motion)"""

    bl_idname = "melodia_loom.bake_rhythm_keys"
    bl_label = "Bake Rhythm Keys"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        mesh = context.active_object
        scale = context.scene.loom.bake_scale
        missing = [g for g in (naming.ACCENT_GROUP, naming.HIT_GROUP)
                   if g not in mesh.vertex_groups]
        if missing:
            self.report({"ERROR"}, f"Paint groups missing: {', '.join(missing)}.")
            return {"CANCELLED"}

        if not mesh.data.shape_keys:
            mesh.shape_key_add(name="Basis", from_mix=False)
        targets = [
            (naming.ACCENT_SHAPE_KEY, naming.ACCENT_GROUP, 1.0),
            (naming.HIT_SHAPE_KEY, naming.HIT_GROUP, 1.6),  # downbeat impulse reads larger
        ]
        try:
            key_blocks = mesh.data.shape_keys.key_blocks
            for key_name, group_name, multiplier in targets:
                key = key_blocks.get(key_name)
                if key is None:
                    key = mesh.shape_key_add(name=key_name, from_mix=False)
                key.value = 0.0
                group = mesh.vertex_groups[group_name]
                for v in mesh.data.vertices:
                    try:
                        w = group.weight(v.index)
                    except RuntimeError:
                        continue
                    if w <= 0.0:
                        continue
                    key.data[v.index].co = v.co + (v.normal * (w * scale * multiplier))
        except (AttributeError, KeyError, RuntimeError) as exc:
            self.report({"ERROR"}, f"Bake failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Baked {len(targets)} rhythm keys at scale {scale} m")
        return {"FINISHED"}


class LOOM_OT_validate_garment(bpy.types.Operator):
    """Check naming, baked keys, beatgrid state and the wardrobe draft contract"""

    bl_idname = "melodia_loom.validate_garment"
    bl_label = "Validate Garment"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        try:
            return self._validate(context)
        except Exception as exc:  # never let an exception kill the editor
            self.report({"ERROR"}, f"Validation crashed: {exc}")
            return {"CANCELLED"}

    def _validate(self, context):
        findings = _validation_findings(context)

        # Reuse the existing draft linter (reads the C++ headers at runtime --
        # the anti-drift pattern). A zero finding here is NOT proof by itself;
        # the linter returns 2 when it could not read the contract.
        try:
            if str(_TOOLS_DIR) not in sys.path:
                sys.path.insert(0, str(_TOOLS_DIR))
            import wardrobe_draft_lint  # type: ignore
            report, code = wardrobe_draft_lint.lint()
            findings.append((
                "INFO" if code == 0 else "ERROR" if code == 1 else "WARNING",
                f"wardrobe_draft_lint: {report.get('blocking_count', '?')} blocking, "
                f"{report.get('owner_decision_count', '?')} owner decisions, "
                f"exit code {code} ({report.get('drafts_checked', '?')} drafts)",
            ))
        except Exception as exc:  # unreadable contract = HOLD, never a clean pass
            findings.append(("WARNING", f"wardrobe_draft_lint unavailable: {exc}"))

        text = bpy.data.texts.get("LOOM_Validation_Report")
        if text is None:
            text = bpy.data.texts.new("LOOM_Validation_Report")
        text.clear()
        for sev, msg in findings:
            text.write(f"[{sev}] {msg}\n")
        errors = [f for f in findings if f[0] == "ERROR"]
        self.report({"ERROR" if errors else "INFO"},
                    f"{len(findings)} finding(s), {len(errors)} error(s). "
                    f"Full report in text datablock LOOM_Validation_Report.")
        return {"FINISHED"}


class LOOM_OT_export_garment(bpy.types.Operator):
    """Export the garment FBX plus its .melodia_rhythm.json sidecar to Imports/Meshes/Loom"""

    bl_idname = "melodia_loom.export_garment"
    bl_label = "Export Garment"
    bl_options = {"REGISTER"}

    output_dir: bpy.props.StringProperty(
        name="Output", subtype="DIR_PATH", default="")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        try:
            return self._export(context)
        except Exception as exc:  # never let an exception kill the editor
            self.report({"ERROR"}, f"Export crashed: {exc}")
            return {"CANCELLED"}

    def _export(self, context):
        loom = context.scene.loom
        blocking = [msg for sev, msg in _validation_findings(context) if sev == "ERROR"]
        if blocking:
            self.report({"ERROR"}, f"Validation blocked export: {blocking[0]}")
            return {"CANCELLED"}

        out_dir = Path(self.output_dir or loom.output_dir or default_export_dir())
        fbx_path = out_dir / f"{loom.cosmetic_id}.fbx"
        out_dir.mkdir(parents=True, exist_ok=True)

        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path),
            use_selection=True,
            object_types={"MESH"},
            path_mode="AUTO",
            add_leaf_bones=False,
        )

        grid = load_beatgrid(loom.midi_path)
        skill = loom.skill_id if loom.skill_id in lanes.SKILL_IDS else sorted(lanes.SKILL_IDS)[0]
        sidecar = build_sidecar(grid, loom.cosmetic_id, skill, midi_file=loom.midi_path,
                                lane_strategy=loom.lane_strategy)
        sidecar_path = write_sidecar(sidecar, out_dir / f"{loom.cosmetic_id}.melodia_rhythm.json")

        self.report({"INFO"}, f"Exported {fbx_path.name} + {sidecar_path.name} -> {out_dir}")
        return {"FINISHED"}


class LOOM_OT_bake_secondary_action(bpy.types.Operator):
    """Keyframe the baked rhythm keys onto the beat grid (ACT_LoomSecondary sway)"""

    bl_idname = "melodia_loom.bake_secondary_action"
    bl_label = "Bake Secondary Sway"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        loom = context.scene.loom
        mesh = context.active_object
        return (
            loom.beatgrid_loaded
            and mesh is not None
            and mesh.type == "MESH"
            and mesh.data.shape_keys is not None
        )

    def execute(self, context):
        try:
            return self._bake(context)
        except Exception as exc:  # never let an exception kill the editor
            self.report({"ERROR"}, f"Secondary sway crashed: {exc}")
            return {"CANCELLED"}

    def _bake(self, context):
        loom = context.scene.loom
        mesh = context.active_object
        keys = mesh.data.shape_keys
        for required in (naming.HIT_SHAPE_KEY, naming.ACCENT_SHAPE_KEY):
            if required not in keys.key_blocks:
                self.report({"ERROR"}, f"{required} not baked. Run Bake Rhythm Keys first.")
                return {"CANCELLED"}

        grid = load_beatgrid(loom.midi_path)
        fps = context.scene.render.fps
        beat_frames = grid.seconds_per_beat * fps

        hit = keys.key_blocks[naming.HIT_SHAPE_KEY]
        accent = keys.key_blocks[naming.ACCENT_SHAPE_KEY]
        hit.value = 0.0
        accent.value = 0.0

        pulses = 0
        # Downbeat impulses on the Hit key: pop, hold ~30% of a beat, release.
        for beat_idx in grid.downbeat_indices():
            f = round(beat_idx * beat_frames) + 1
            hit.value = 1.0
            hit.keyframe_insert("value", frame=f)
            hit.value = 0.35
            hit.keyframe_insert("value", frame=f + max(1, round(0.3 * beat_frames)))
            hit.value = 0.0
            hit.keyframe_insert("value", frame=f + max(1, round(beat_frames)))
            pulses += 1
        # Accent flourishes on the Accent key, scaled by note velocity.
        for note in [n for n in grid.notes if n.velocity >= 96]:
            f = round(note.start_sec * fps) + 1
            accent.value = note.velocity / 127.0
            accent.keyframe_insert("value", frame=f)
            accent.value = 0.0
            accent.keyframe_insert("value", frame=f + max(1, round(0.5 * beat_frames)))
            pulses += 1

        if keys.animation_data is None:
            keys.animation_data_create()
        action = keys.animation_data.action
        if action is None:
            action = bpy.data.actions.new(naming.SECONDARY_ACTION)
            keys.animation_data.action = action
        action.name = naming.SECONDARY_ACTION

        self.report({"INFO"}, f"{naming.SECONDARY_ACTION}: {pulses} pulses keyed")
        return {"FINISHED"}


classes = (
    LOOM_OT_import_beatgrid,
    LOOM_OT_ensure_paint_groups,
    LOOM_OT_bake_rhythm_keys,
    LOOM_OT_bake_secondary_action,
    LOOM_OT_validate_garment,
    LOOM_OT_export_garment,
)


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

