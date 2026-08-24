"""♪ Melodia Score — musical interface, BPM/scale orchestrator, waveform overlay.

The music-first UI layer for Melodia Studio:
- Scene-level Score props (BPM, key, mode, bars) on ``scene.melodia_score``
- BPM → genome DNA mapping (rhythm dungeon table from the MCP adapter)
- Scale-degree-driven room orchestration (chord tones get arch windows)
- Live waveform overlay drawn across the viewport top (gpu POST_PIXEL)
- ♪ Score N-panel under the genome carousel
"""

from __future__ import annotations

import math
import time

import bpy

from .branding import N_PANEL_CATEGORY

# ── State ───────────────────────────────────────────────────────────────

_wave_handler = None
_score_classes = []
_addon_keymaps = []

_KEYS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_SEMITONE = {
    "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
    "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
}
_MODES = {
    # semitone steps per degree (7 notes)
    "MAJOR":      (0, 2, 4, 5, 7, 9, 11),
    "MINOR":      (0, 2, 3, 5, 7, 8, 10),
    "PENTATONIC": (0, 2, 4, 7, 9),          # 5 degrees
    "BLUES":      (0, 3, 5, 6, 7, 10),      # 6 degrees
    "DORIAN":     (0, 2, 3, 5, 7, 9, 10),
    "PHRYGIAN":   (0, 1, 3, 5, 7, 8, 10),
    "LYDIAN":     (0, 2, 4, 6, 7, 9, 11),
    "MIXOLYDIAN": (0, 2, 4, 5, 7, 9, 10),
}
_CHORD_DEGREES = {0, 2, 4}  # triad members within a mode


def _score(context=None):
    context = context or bpy.context
    return getattr(context.scene, "melodia_score", None)


def _props_of_active(context):
    obj = context.active_object
    if obj and hasattr(obj, "surreal_arch_props"):
        return obj.surreal_arch_props
    return None


# ── Props ───────────────────────────────────────────────────────────────

class MelodiaScoreProps(bpy.types.PropertyGroup):
    bpm: bpy.props.IntProperty(
        name="BPM", description="Tempo in beats per minute — drives spacing + DNA",
        default=120, min=40, max=240)
    key_root: bpy.props.EnumProperty(
        name="Key", description="Tonic note",
        items=[(k, k, f"Semitone {_SEMITONE[k]}") for k in _KEYS],
        default="C")
    mode: bpy.props.EnumProperty(
        name="Mode", description="Scale/mode shaping ornament brightness",
        items=[(m, m.title(), f"{len(v)}-degree scale") for m, v in _MODES.items()],
        default="MAJOR")
    bars: bpy.props.IntProperty(
        name="Bars", description="Measures → room count / window count",
        default=4, min=1, max=16)
    drive_genomes: bpy.props.BoolProperty(
        name="Drive Genome DNA", description="Apply BPM/scale mapping to genome_* factors",
        default=True)
    overlay_alpha: bpy.props.FloatProperty(
        name="Overlay Opacity", default=0.55, min=0.05, max=1.0)


def register_score_props():
    try:
        bpy.utils.register_class(MelodiaScoreProps)
    except RuntimeError:
        pass
    if not hasattr(bpy.types.Scene, "melodia_score"):
        bpy.types.Scene.melodia_score = bpy.props.PointerProperty(type=MelodiaScoreProps)


def unregister_score_props():
    if hasattr(bpy.types.Scene, "melodia_score"):
        del bpy.types.Scene.melodia_score
    try:
        bpy.utils.unregister_class(MelodiaScoreProps)
    except Exception:
        pass


# ── Music theory helpers ────────────────────────────────────────────────

def _mode_degrees(mode):
    return list(_MODES.get(mode or "MAJOR", _MODES["MAJOR"]))


def _degree_brightness(mode):
    """0..1 brightness proxy: major/lydian bright, phrygian/locrian dark."""
    degs = _mode_degrees(mode)
    third = degs[2] if len(degs) > 2 else 4
    seventh = degs[-1]
    base = {"MAJOR": 0.85, "LYDIAN": 0.95, "MIXOLYDIAN": 0.8,
            "DORIAN": 0.6, "MINOR": 0.45, "PENTATONIC": 0.7,
            "BLUES": 0.35, "PHRYGIAN": 0.25}.get(mode or "MAJOR", 0.6)
    if third >= 4:
        base += 0.05
    else:
        base -= 0.08
    if seventh >= 10:
        base += 0.03
    return max(0.1, min(1.0, base))


def _bpm_dna(bpm):
    """Rhythm-dungeon BPM→DNA table (mirrors blender_5.2_mcp mapping)."""
    if bpm < 100:
        return dict(verticality=0.30, ornament=0.70, organic=0.75, cosmic=0.20, spacing=0.70)
    if bpm < 120:
        return dict(verticality=0.40, ornament=0.50, organic=0.55, cosmic=0.15, spacing=0.50)
    if bpm < 140:
        return dict(verticality=0.70, ornament=0.50, organic=0.35, cosmic=0.25, spacing=0.50)
    if bpm < 160:
        return dict(verticality=0.80, ornament=0.85, organic=0.25, cosmic=0.30, spacing=0.30)
    if bpm < 180:
        return dict(verticality=0.90, ornament=0.65, organic=0.20, cosmic=0.45, spacing=0.20)
    return dict(verticality=0.95, ornament=0.90, organic=0.80, cosmic=0.85, spacing=0.10)


# ── Operators ───────────────────────────────────────────────────────────

class SURREAL_ARCH_OT_apply_bpm_genome(bpy.types.Operator):
    bl_idname = "surreal_arch.apply_bpm_genome"
    bl_label = "♩ Apply BPM Genome"
    bl_description = "Map tempo to architecture DNA: fast = dense/tall/cosmic, slow = organic/spread"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _props_of_active(context) is not None and _score(context) is not None

    def execute(self, context):
        props = _props_of_active(context)
        score = _score(context)
        if not props:
            self.report({"ERROR"}, "No Melodia mesh active")
            return {"CANCELLED"}
        dna = _bpm_dna(score.bpm)
        bright = _degree_brightness(score.mode)
        props.genome_verticality = dna["verticality"]
        props.genome_ornament_density = min(1.0, dna["ornament"] * (0.6 + bright * 0.6))
        props.genome_organic_growth = dna["organic"]
        props.genome_cosmic_influence = dna["cosmic"]
        props.genome_symmetry = 0.9 - dna["cosmic"] * 0.4
        props.graph_spawn_spacing = max(2.0, 14.0 * dna["spacing"])
        if score.drive_genomes:
            bpy.ops.surreal_arch.generate()
        self.report({"INFO"},
                    f"DNA set: {score.bpm} BPM {score.key_root} {score.mode} "
                    f"(brightness {bright:.2f})")
        return {"FINISHED"}


class SURREAL_ARCH_OT_generate_scale_room(bpy.types.Operator):
    bl_idname = "surreal_arch.generate_scale_room"
    bl_label = "♬ Generate Scale Room"
    bl_description = ("Orchestrate room shell from key+mode+bars: chord tones become "
                      "arch windows, passing tones stay rect; bar count = window count; "
                      "spacing follows beat length")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _props_of_active(context) is not None and _score(context) is not None

    def execute(self, context):
        props = _props_of_active(context)
        score = _score(context)
        if not props:
            self.report({"ERROR"}, "No Melodia mesh active")
            return {"CANCELLED"}

        degs = _mode_degrees(score.mode)
        tonic = _SEMITONE[score.key_root]
        n = len(degs)

        # Room footprint from mode character
        bright = _degree_brightness(score.mode)
        shape_by_mode = {
            "MAJOR": "OCTAGON", "LYDIAN": "ELLIPSE", "MIXOLYDIAN": "HEX",
            "DORIAN": "APSIDAL", "MINOR": "RECTANGLE", "PENTATONIC": "OCTAGON",
            "BLUES": "L_SHAPE", "PHRYGIAN": "SUPERELLIPSE",
        }
        props.arch_type = "GREYBOX_ROOM"
        props.gb_room_shape = shape_by_mode.get(score.mode, "RECTANGLE")
        if props.gb_room_shape not in ("RECTANGLE", "L_SHAPE", "T_SHAPE", "U_SHAPE"):
            props.gb_room_radius = max(2.0, 60.0 / score.bpm)

        # Windows = bars; arch height follows degree interval size
        props.gb_windows_enabled = True
        props.gb_window_count_ns = max(1, score.bars)
        props.gb_window_count_ew = max(1, max(1, score.bars // 2))
        chord_bars = sum(1 for b in range(max(1, score.bars)) if (b % n) in _CHORD_DEGREES)
        passing = max(1, score.bars) - chord_bars
        avg_arch = 0.18 + 0.22 * (chord_bars / max(1, score.bars)) * (1.4 - bright * 0.5)
        props.gb_window_shape = "GOTHIC" if bright > 0.55 else "ARCH_ROUND"
        props.gb_window_arch_height = round(avg_arch, 3)
        props.gb_window_has_mullion = bool(chord_bars >= passing)
        props.gb_window_sill = 1.0 + (tonic % 5) * 0.06

        # Beat-length spacing
        beat_len = 60.0 / max(40, score.bpm)
        props.unit_size = max(1.0, round(beat_len * 4.0, 2))

        # Genome nudges from mode brightness
        props.genome_ornament_density = min(1.0, 0.35 + bright * 0.55)
        props.genome_structural_logic = 0.9 - bright * 0.3
        if score.drive_genomes:
            bpy.ops.surreal_arch.generate()
        self.report({"INFO"},
                    f"Scale room: {n}-degree {score.mode}, {score.bars} bars, "
                    f"{props.gb_room_shape}, arch={avg_arch:.2f}")
        return {"FINISHED"}


# ── Waveform overlay ────────────────────────────────────────────────────

def _draw_wave_overlay():
    global _wave_handler
    context = bpy.context
    wm = context.window_manager
    if wm is None:
        return
    win = context.window
    if win is None:
        return
    import gpu
    from gpu_extras.batch import batch_for_shader

    score = _score(context)
    bpm = float(getattr(score, "bpm", 120)) if score else 120.0
    alpha = float(getattr(score, "overlay_alpha", 0.55)) if score else 0.55
    t = time.monotonic()
    beat_hz = bpm / 60.0
    pulse = 0.5 + 0.5 * math.sin(t * beat_hz * math.tau)

    region = context.region
    if region is None:
        return
    w, h = region.width, region.height
    top = h - 46
    amp = 12.0 + pulse * 16.0
    mid_y = top - 26.0

    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    gpu.state.blend_set("ALPHA")

    coords = []
    step = 8.0
    x = 24.0
    while x <= w - 24.0:
        phase = (x - 24.0) / max(1.0, (w - 48.0))
        yv = (math.sin(phase * math.tau * 2.0 + t * beat_hz * math.tau)
              * (0.35 + 0.65 * math.sin(phase * math.pi)))
        coords.append((x, mid_y + yv * amp))
        x += step
    batch = batch_for_shader(shader, "LINE_STRIP", {"pos": coords})
    shader.uniform_float("color", (0.28, 0.85, 1.0, alpha * (0.55 + 0.45 * pulse)))
    batch.draw(shader)

    # beat dots
    dot_shader_coords = []
    for i in range(4):
        lit = int(t * beat_hz) % 4 == i
        r = 5.0 if lit else 3.0
        cx = w - 130 + i * 26
        cy = top - 8
        for k in range(10):
            a0 = math.tau * k / 10
            dot_shader_coords.append((cx + r * math.cos(a0), cy + r * math.sin(a0)))
    if dot_shader_coords:
        dbatch = batch_for_shader(shader, "POINTS", {"pos": dot_shader_coords})
        shader.uniform_float("color", (1.0, 0.82, 0.25, alpha))
        dbatch.draw(shader)
    gpu.state.blend_set("NONE")


class SURREAL_ARCH_OT_toggle_wave_overlay(bpy.types.Operator):
    bl_idname = "surreal_arch.toggle_wave_overlay"
    bl_label = "Waveform Overlay"
    bl_description = "Draw a live BPM-synced sine waveform strip along the viewport top"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global _wave_handler
        if _wave_handler is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(_wave_handler, "POST_PIXEL")
            except Exception:
                pass
            _wave_handler = None
            self.report({"INFO"}, "Waveform overlay OFF")
        else:
            _wave_handler = bpy.types.SpaceView3D.draw_handler_add(
                _draw_wave_overlay, (), "WINDOW", "POST_PIXEL")
            self.report({"INFO"}, "Waveform overlay ON — ♪ synced to Score BPM")
        return {"FINISHED"}


# ── IMM kit export (ZBrush Insert Multi Mesh) ───────────────────────────

_IMM_KIT = (
    "MEL_music_waveform_wall",
    "MEL_music_vinyl_disc",
    "MEL_music_lissajous_harp",
    "MEL_imm_piano_keys",
    "MEL_music_frequency_ribcage",
    "MEL_music_tuning_fork",
    "MEL_music_metronome_pillar",
    "MEL_music_soundhole_rosette",
)

_IMM_GLYPHS = (
    "MEL_music_treble_clef", "MEL_music_bass_clef", "MEL_music_note_head",
    "MEL_music_staff", "MEL_music_fermata", "MEL_music_time_signature",
    "MEL_decorative_rosette", "MEL_bell_chime",
)


def _ensure_tree(tree_name):
    """Build a GN tree on demand via GROUP_BUILDERS."""
    if tree_name in bpy.data.node_groups:
        return bpy.data.node_groups[tree_name]
    from .melodia_gn.core import GROUP_BUILDERS
    fn = GROUP_BUILDERS.get(tree_name)
    if fn is None:
        return None
    try:
        result = fn(tree_name)
        return bpy.data.node_groups.get(tree_name)
    except Exception as exc:
        print(f"[Melodia IMM] builder '{tree_name}' failed: {exc}")
        return None


class SURREAL_ARCH_OT_export_imm_kit(bpy.types.Operator):
    bl_idname = "surreal_arch.export_imm_kit"
    bl_label = "Export ZBrush IMM Kit"
    bl_description = ("Batch-export musical builders as base-pivoted OBJ meshes into a folder — "
                      "import in ZBrush and create an InsertMultiMesh brush per piece")
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(subtype="DIR_PATH", name="Output Folder")
    include_glyphs: bpy.props.BoolProperty(name="Include Notation Glyphs", default=True)
    decimate_ratio: bpy.props.FloatProperty(name="Decimate Ratio (0=off)",
                                            default=0.0, min=0.0, max=1.0)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        import os
        out_dir = bpy.path.abspath(self.filepath) if self.filepath else os.path.join(
            bpy.path.abspath("//"), "IMM_Kit")
        os.makedirs(out_dir, exist_ok=True)

        names = list(_IMM_KIT)
        if self.include_glyphs:
            names.extend(_IMM_GLYPHS)

        exported, failed = [], []
        view_layer = context.view_layer
        old_active = view_layer.objects.active
        old_sel = {o for o in context.selected_objects}

        for tree_name in names:
            tree = _ensure_tree(tree_name)
            if tree is None:
                failed.append((tree_name, "tree build failed"))
                continue
            tmp_mesh = bpy.data.meshes.new(f"_tmp_{tree_name}")
            tmp_obj = bpy.data.objects.new(f"_tmp_{tree_name}", tmp_mesh)
            context.collection.objects.link(tmp_obj)
            try:
                mod = tmp_obj.modifiers.new(name="melodia_imm", type="NODES")
                mod.node_group = tree
                deps = context.evaluated_depsgraph_get()
                eval_obj = tmp_obj.evaluated_get(deps)
                final_mesh = bpy.data.meshes.new_from_object(eval_obj)
                if final_mesh is None or len(final_mesh.vertices) == 0:
                    failed.append((tree_name, "empty evaluation"))
                    continue
                # Base-pivot: min-Z → 0, centroid XY → origin
                xs = [v.co.x for v in final_mesh.vertices]
                ys = [v.co.y for v in final_mesh.vertices]
                zs = [v.co.z for v in final_mesh.vertices]
                cx, cy, mz = (min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, min(zs)
                for v in final_mesh.vertices:
                    v.co.x -= cx
                    v.co.y -= cy
                    v.co.z -= mz
                export_obj = bpy.data.objects.new(tree_name, final_mesh)
                context.collection.objects.link(export_obj)
                if self.decimate_ratio > 0.01:
                    dm = export_obj.modifiers.new("decimate", type="DECIMATE")
                    dm.ratio = self.decimate_ratio
                    deps2 = context.evaluated_depsgraph_get()
                    eval2 = export_obj.evaluated_get(deps2)
                    dm_mesh = bpy.data.meshes.new_from_object(eval2)
                    bpy.data.objects.remove(export_obj, do_unlink=True)
                    export_obj = bpy.data.objects.new(tree_name, dm_mesh)
                    context.collection.objects.link(export_obj)
                bpy.ops.object.select_all(action="DESELECT")
                export_obj.select_set(True)
                view_layer.objects.active = export_obj
                obj_path = os.path.join(out_dir, f"{tree_name}.obj")
                bpy.ops.wm.obj_export(filepath=obj_path, export_selected_objects=True,
                                      export_materials=False, export_uv=False,
                                      forward_axis="NEGATIVE_Z", up_axis="Y")
                exported.append(obj_path)
                bpy.data.objects.remove(export_obj, do_unlink=True)
            except Exception as exc:
                failed.append((tree_name, str(exc)[:120]))
            finally:
                bpy.data.objects.remove(tmp_obj, do_unlink=True)
                try:
                    bpy.data.meshes.remove(tmp_mesh)
                except Exception:
                    pass

        readme = os.path.join(out_dir, "_IMM_README.txt")
        with open(readme, "w", encoding="utf-8") as f:
            f.write("Melodia Studio — Musical Geometry IMM Kit\n")
            f.write("=" * 44 + "\n\n")
            f.write("ZBrush workflow:\n")
            f.write("1. Import > OBJ — pick any MEL_*.obj (becomes a Tool).\n")
            f.write("2. Tool > Make PolyMesh3D.\n")
            f.write("3. Brush > Create > Create Insert Multi Mesh Brush.\n")
            f.write("4. Repeat per piece; save brushes under ZStartup/ZPlugs/Imm/\n")
            f.write("   or drag into Brush palette.\n\n")
            f.write("Pieces are base-pivoted (origin at footprint centre, floor z=0)\n")
            f.write("and Y-up so they plant correctly with IMM drag-out.\n\n")
            f.write(f"Exported ({len(exported)}):\n")
            for p in exported:
                f.write(f"  {os.path.basename(p)}\n")
            if failed:
                f.write(f"\nFailed ({len(failed)}):\n")
                for name, err in failed:
                    f.write(f"  {name}: {err}\n")

        # restore selection
        bpy.ops.object.select_all(action="DESELECT")
        for o in old_sel:
            try:
                o.select_set(True)
            except Exception:
                pass
        if old_active:
            view_layer.objects.active = old_active

        msg = f"IMM kit: {len(exported)} exported to {out_dir}"
        if failed:
            msg += f"; {len(failed)} failed (see _IMM_README.txt)"
        self.report({"WARNING" if failed else "INFO"}, msg)
        return {"FINISHED"}


# ── Panel ♪ Score ───────────────────────────────────────────────────────

class SURREAL_ARCH_PT_music_score(bpy.types.Panel):
    bl_label = "♪ Score — Tempo & Key"
    bl_idname = "SURREAL_ARCH_PT_music_score"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_order = 9
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        score = _score(context)
        props = _props_of_active(context)
        if score is None:
            layout.label(text="Score unavailable", icon="ERROR")
            return

        box = layout.box()
        box.label(text="Tempo & Key", icon="PLAY")
        col = box.column(align=True)
        col.prop(score, "bpm")
        row = box.row(align=True)
        row.prop(score, "key_root")
        row.prop(score, "mode")
        col2 = box.column(align=True)
        col2.prop(score, "bars")
        col2.prop(score, "drive_genomes")

        ops_box = layout.box()
        ops_box.label(text="Musical Geometry", icon="MOD_WAVE")
        c1 = ops_box.column(align=True)
        c1.scale_y = 1.15
        c1.operator("surreal_arch.apply_bpm_genome", icon="TIME")
        c1.operator("surreal_arch.generate_scale_room", icon="MESH_CIRCLE")
        ops_box.prop(score, "overlay_alpha")
        ops_box.operator("surreal_arch.toggle_wave_overlay", icon="ANIM")

        kit = layout.box()
        kit.label(text="Musical Kit (GN Stack)", icon="IPO_BEZIER")
        grid = kit.grid_flow(row_major=True, columns=2, align=True)
        for tree_name, label in (
            ("MEL_music_waveform_wall", "♪ Waveform Wall"),
            ("MEL_music_vinyl_disc", "◎ Vinyl Disc"),
            ("MEL_music_lissajous_harp", "∿ Lissajous Harp"),
            ("MEL_imm_piano_keys", "▤ Piano Keys"),
            ("MEL_music_frequency_ribcage", "⌒ Freq Ribcage"),
            ("MEL_music_tuning_fork", "Ψ Tuning Fork"),
            ("MEL_music_metronome_pillar", "▲ Metronome"),
            ("MEL_music_soundhole_rosette", "✿ Rosette"),
        ):
            op = grid.operator("mel_gn.stack_add", text=label)
            op.tree_name = tree_name
        kit.operator("surreal_arch.generate_chime_row", icon="NLA_PUSHDOWN")

        imm = layout.box()
        imm.label(text="ZBrush IMM Kit", icon="PACKAGE")
        imm.operator("surreal_arch.export_imm_kit", icon="EXPORT")


class SURREAL_ARCH_MT_pie_score(bpy.types.Menu):
    bl_label = "♪ Score"
    bl_idname = "SURREAL_ARCH_MT_pie_score"

    def draw(self, context):
        pie = self.layout.menu_pie()
        pie.operator("surreal_arch.apply_bpm_genome", text="BPM → Genome", icon="TIME")
        pie.operator("surreal_arch.generate_scale_room", text="Scale Room", icon="MESH_CIRCLE")
        pie.operator("surreal_arch.toggle_wave_overlay", text="Wave Overlay", icon="ANIM")
        pie.operator("surreal_arch.export_imm_kit", text="IMM Kit Export", icon="EXPORT")
        col = pie.column(align=True)
        for tree_name, label in (
            ("MEL_music_waveform_wall", "Waveform Wall"),
            ("MEL_music_vinyl_disc", "Vinyl Disc"),
            ("MEL_imm_piano_keys", "Piano Keys"),
            ("MEL_music_soundhole_rosette", "Rosette"),
        ):
            op = col.operator("mel_gn.stack_add", text=label, icon="IPO_BEZIER")
            op.tree_name = tree_name
        col2 = pie.column(align=True)
        col2.operator("mel_gn.stack_add", text="Freq Ribcage").tree_name = "MEL_music_frequency_ribcage"
        col2.operator("mel_gn.stack_add", text="Metronome").tree_name = "MEL_music_metronome_pillar"


class SURREAL_ARCH_OT_pie_score(bpy.types.Operator):
    bl_idname = "surreal_arch.pie_score"
    bl_label = "Score Pie"

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=SURREAL_ARCH_MT_pie_score.bl_idname)
        return {"FINISHED"}


# ── Registration ────────────────────────────────────────────────────────

def register_music_ui():
    global _score_classes
    register_score_props()
    try:
        from .chime_row import register_chime_row
        register_chime_row()
    except Exception as exc:
        print(f"[Melodia Studio] chime_row register skipped: {exc}")
    _score_classes = [
        SURREAL_ARCH_OT_apply_bpm_genome,
        SURREAL_ARCH_OT_generate_scale_room,
        SURREAL_ARCH_OT_toggle_wave_overlay,
        SURREAL_ARCH_OT_export_imm_kit,
        SURREAL_ARCH_PT_music_score,
        SURREAL_ARCH_MT_pie_score,
        SURREAL_ARCH_OT_pie_score,
    ]
    from .integration import _register_class_once
    ok = []
    for cls in _score_classes:
        if _register_class_once(cls):
            ok.append(cls)
    # Shift+M hotkey for the score pie
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon if wm else None
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("surreal_arch.pie_score", "M", "PRESS", shift=True)
        _addon_keymaps.append((km, kmi))
    return _score_classes


def unregister_music_ui():
    global _wave_handler
    if _wave_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_wave_handler, "POST_PIXEL")
        except Exception:
            pass
        _wave_handler = None
    try:
        from .chime_row import unregister_chime_row
        unregister_chime_row()
    except Exception:
        pass
    for km, kmi in list(_addon_keymaps):
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    _addon_keymaps.clear()
    for cls in reversed(_score_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    _score_classes = []
    unregister_score_props()
