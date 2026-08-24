"""🔔 Tubular chime row — real free-free-beam tuning, ET degrees from the ♪ Score.

Math (see Docs/MelodiaStudio/MUSIC_KIT_LEDGER_20260823.md):
    f(d)  = A4 * 2^((semitone(d) - 9) / 12)          equal temperament
    L(f)  = L_ref * sqrt(f_ref / f)                   free-free hollow beam
    hang node at 22.4% of L; shimmer bands at 1/2.756 and 1/5.404 of L.

Builds one joined IMM-ready mesh: beam + cords + tubes + nodal rings.
"""

from __future__ import annotations

import math

import bmesh
import bpy
import math
import mathutils

_A4 = 440.0
_MODE_STEPS = {
    "MAJOR": (0, 2, 4, 5, 7, 9, 11),
    "MINOR": (0, 2, 3, 5, 7, 8, 10),
    "PENTATONIC": (0, 2, 4, 7, 9),
    "BLUES": (0, 3, 5, 6, 7, 10),
    "DORIAN": (0, 2, 3, 5, 7, 9, 10),
    "PHRYGIAN": (0, 1, 3, 5, 7, 8, 10),
    "LYDIAN": (0, 2, 4, 6, 7, 9, 11),
    "MIXOLYDIAN": (0, 2, 4, 5, 7, 9, 10),
}
_KEY_SEMITONE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
                 "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def _degree_freqs(key_root: str, mode: str, count: int):
    """Return list of Hz for count ascending scale degrees."""
    steps = _MODE_STEPS.get((mode or "MAJOR").upper(), _MODE_STEPS["MAJOR"])
    tonic = _KEY_SEMITONE.get(key_root, 0)
    freqs = []
    for i in range(count):
        octave, deg = divmod(i, len(steps))
        semitone = tonic + steps[deg] + 12 * octave
        freqs.append(_A4 * 2.0 ** ((semitone - 9) / 12.0))
    return freqs


def _bm_cylinder(bm, radius, depth, segments, x, z_top, rot_y=0.0):
    """Append an open-ended tube wall (two circle rings + side faces)."""
    ring_a = []
    ring_b = []
    segs = max(12, segments)
    ca, sa = math.cos(rot_y), math.sin(rot_y)
    for i in range(segs):
        ang = 2 * math.pi * i / segs
        y = radius * math.sin(ang)
        zz = radius * math.cos(ang)
        # rotate around X so tube axis lies along Z (vertical hanging)
        ya = y * ca - zz * sa
        za = y * sa + zz * ca
        ring_a.append(bm.verts.new((x, ya, z_top + za)))
        ring_b.append(bm.verts.new((x, ya, z_top - depth + za)))
    bm.faces.new(ring_a)
    bm.faces.new(list(reversed(ring_b)))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((ring_a[i], ring_a[j], ring_b[j], ring_b[i]))


def _bm_torus(bm, major_r, minor_r, seg_major, seg_minor, x, z, axis="x"):
    """Thin ring (nodal cord / shimmer band), axis along X by default."""
    verts = {}
    for i in range(seg_major):
        a = 2 * math.pi * i / seg_major
        for j in range(seg_minor):
            b = 2 * math.pi * j / seg_minor
            r = major_r + minor_r * math.cos(b)
            h = minor_r * math.sin(b)
            if axis == "x":
                verts[(i, j)] = bm.verts.new((x + h, r * math.cos(a), r * math.sin(a) + z))
            else:
                verts[(i, j)] = bm.verts.new((r * math.cos(a) + x, h, r * math.sin(a) + z))
    for i in range(seg_major):
        i2 = (i + 1) % seg_major
        for j in range(seg_minor):
            j2 = (j + 1) % seg_minor
            bm.faces.new((verts[(i, j)], verts[(i2, j)], verts[(i2, j2)], verts[(i, j2)]))


class SURREAL_ARCH_OT_generate_chime_row(bpy.types.Operator):
    bl_idname = "surreal_arch.generate_chime_row"
    bl_label = "🔔 Generate Chime Row"
    bl_description = ("Free-free-beam tuned tubular chimes from the ♪ Score panel — "
                      "L ∝ √(f_ref/f); hang nodes at 22.4%; shimmer bands at overtone ratios")
    bl_options = {"REGISTER", "UNDO"}

    use_score: bpy.props.BoolProperty(name="Use ♪ Score key/mode", default=True)
    root_hz: bpy.props.FloatProperty(name="Root Hz (manual)", default=261.63, min=20, max=4000)
    count: bpy.props.IntProperty(name="Tube Count", default=8, min=3, max=16)
    longest_m: bpy.props.FloatProperty(name="Longest Tube (m)", default=1.25, min=0.2, max=6.0)
    od_mm: bpy.props.FloatProperty(name="Outer Ø (mm)", default=38.0, min=8.0, max=90.0)
    spacing: bpy.props.FloatProperty(name="Spacing (m)", default=0.16, min=0.05, max=1.0)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        score = getattr(context.scene, "melodia_score", None)
        if self.use_score and score is not None:
            key_root, mode, count = score.key_root, score.mode, max(3, score.bars + 1)
            f_low = None
        else:
            key_root, mode, count = "C", "MAJOR", self.count
            f_low = self.root_hz

        freqs = (_degree_freqs(key_root, mode, count) if self.use_score and score is not None
                 else [self.root_hz * 2.0 ** (i / 12.0) for i in range(self.count)])
        freqs.sort()  # ascending pitch

        # Beam law: longest tube at lowest frequency
        f_min = freqs[0]
        lengths = [self.longest_m * math.sqrt(f_min / f) for f in freqs]

        od = self.od_mm / 1000.0
        radius = od / 2.0
        seg_major, seg_minor = 28, 8
        spacing = max(self.spacing, od * 1.35)

        bm = bmesh.new()
        total_w = spacing * (len(lengths) - 1)
        x0 = -total_w / 2.0
        beam_z = self.longest_m + 0.06

        # Top beam
        bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=mathutils.Matrix.Translation((0.0, 0.0, beam_z + 0.02))
            @ mathutils.Matrix.Diagonal((total_w + spacing, 0.05, 0.05, 1.0)),
        )

        for i, L in enumerate(lengths):
            x = x0 + i * spacing
            z_top = beam_z - 0.03
            _bm_cylinder(bm, radius, L, seg_major, x, z_top)
            # nodal hang ring at 22.4%
            _bm_torus(bm, radius + 0.004, 0.004, 24, 6, x,
                      z_top - 0.224 * L, axis="y")
            # shimmer bands at overtone nodes (visual engraving): 1/2.756, 1/5.404
            for k in (2.756, 5.404):
                _bm_torus(bm, radius + 0.0025, 0.0016, 20, 5, x,
                          z_top - L / k, axis="y")
            # cord from beam to hang point
            cord_top = z_top
            cord_bot = z_top - 0.224 * L
            mid = (cord_top + cord_bot) / 2.0
            bmesh.ops.create_cube(
                bm, size=1.0,
                matrix=mathutils.Matrix.Translation((x, 0.0, mid))
                @ mathutils.Matrix.Diagonal((0.008, 0.008, abs(cord_top - cord_bot), 1.0)),
            )

        obj_name = "MEL_ChimeRow"
        mesh = bpy.data.meshes.new(obj_name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            obj = bpy.data.objects.new(obj_name, mesh)
            context.collection.objects.link(obj)
        else:
            old, obj.data = obj.data, mesh
            if old.users == 0:
                bpy.data.meshes.remove(old)
        obj.location = (0.0, 0.0, 0.0)

        # Komikaze first (monolith's own bridge), fallback principled brass
        mat = None
        try:
            import sys
            mon = sys.modules.get("surreal_architecture_gen")
            link = getattr(mon, "_komikaze_link", None)
            for name in ("Voronoi Shader (3 Tones)", "Wood"):
                if callable(link):
                    mat = link(name, link=False)
                    if mat is not None:
                        break
        except Exception:
            mat = None
        if mat is None:
            mat = bpy.data.materials.get("MEL_ChimeBrass")
            if mat is None:
                mat = bpy.data.materials.new("MEL_ChimeBrass")
                mat.use_nodes = True
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Metallic"].default_value = 1.0
                    bsdf.inputs["Roughness"].default_value = 0.25
                    base = bsdf.inputs.get("Base Color")
                    if base:
                        base.default_value = (0.72, 0.58, 0.28, 1.0)
        obj.data.materials.clear()
        obj.data.materials.append(mat)

        freq_txt = ", ".join(f"{f:.0f}" for f in freqs)
        self.report({"INFO"},
                    f"Chime row: {len(freqs)} tubes {key_root} {mode} "
                    f"[{freq_txt}] Hz · L {min(lengths):.2f}–{max(lengths):.2f} m")
        return {"FINISHED"}


def register_chime_row():
    try:
        bpy.utils.register_class(SURREAL_ARCH_OT_generate_chime_row)
    except (RuntimeError, ValueError):
        pass


def unregister_chime_row():
    try:
        bpy.utils.unregister_class(SURREAL_ARCH_OT_generate_chime_row)
    except Exception:
        pass
