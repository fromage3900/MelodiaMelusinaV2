"""Melodia Studio panel - MIDI-driven Resonant World generation.

QOL pass (2026-08-24, C-authority):
 - Unified N-panel category "Melodia" so all Melodia tools sit together
 - Search/filter for MIDI, preview line (notes + beatgrid), last-run stats
 - Cleanup of stale Terrain objects on re-generate
 - dress_terrain receives midi_path so the placement plan uses real terrain
 - Management subpanel: health, folders, reload, docs
 - Icon fallback via addon_utils, offline-safe (no bpy on import)
 - Cached MIDI discovery (avoids rescanning every draw)
"""

import os
import shutil
import sys
import time
from pathlib import Path

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_bridge

# Optional QOL helpers - offline-safe
try:
    from . import addon_utils  # type: ignore
except Exception:
    addon_utils = None  # type: ignore

try:
    from . import melodia_chrome as _chrome  # type: ignore
except Exception:
    _chrome = None  # type: ignore

try:
    import melodia_utils as _mu  # type: ignore
except Exception:
    # Fallback: parent of addons root is on sys.path when loaded as Script Directory
    try:
        _ADDONS_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        if _ADDONS_ROOT not in sys.path:
            sys.path.insert(0, _ADDONS_ROOT)
        import melodia_utils as _mu  # type: ignore
    except Exception:
        _mu = None  # type: ignore


# ------------------------------------------------------------- caching

_MIDI_CACHE: list[str] = []
_MIDI_CACHE_TIME: float = 0.0
_MIDI_CACHE_TTL = 4.0  # seconds - avoids scanning on every draw, still live


def _discover_cached() -> list[str]:
    global _MIDI_CACHE, _MIDI_CACHE_TIME
    now = time.time()
    if _MIDI_CACHE and (now - _MIDI_CACHE_TIME) < _MIDI_CACHE_TTL:
        return _MIDI_CACHE
    # honour AddonPreferences midi_extra_dirs (semicolon-separated)
    extra = None
    if bpy is not None:
        try:
            prefs = bpy.context.preferences.addons.get("melodia_studio")
            if prefs and hasattr(prefs, "preferences"):
                raw = getattr(prefs.preferences, "midi_extra_dirs", "") or ""
                if raw.strip():
                    extra = [p.strip() for p in raw.split(";") if p.strip()]
        except Exception:
            extra = None
    found = midi_bridge.discover_midi(extra_dirs=extra)
    _MIDI_CACHE = found
    _MIDI_CACHE_TIME = now
    return found


# ------------------------------------------------------------- enum helpers

def _preset_enum(self, context):
    items = midi_bridge.preset_items()
    return items if items else [("resonant_default", "Resonant Default", "")]


def _midi_enum(self, context):
    # Allow filtering by search string
    filt = ""
    try:
        filt = (context.scene.melodia_studio.midi_filter or "").strip().lower()
    except Exception:
        pass
    found = _discover_cached()
    if filt:
        found = [p for p in found if filt in os.path.basename(p).lower() or filt in p.lower()]
    if not found:
        # Keep operator reachable even with no results
        if filt:
            return [("", f"No match for '{filt}'", "")]
        return [("", "No MIDI found", "")]
    root = midi_bridge.repo_root()
    items = []
    for path in found[:64]:
        try:
            label = os.path.relpath(path, root)
        except ValueError:
            label = os.path.basename(path)
        # label shown in dropdown; path is the value
        items.append((path, os.path.basename(path), label))
    return items


def _dressing_items():
    """Dressing styles - single source of truth from terrain_dressing.
    Falls back to a minimal list if terrain_dressing is unavailable."""
    try:
        from . import terrain_dressing as td
        items = []
        for key, val in sorted(td.DRESSING_STYLES.items()):
            items.append((key, val.get("label", key), val.get("description", "")))
        return items if items else [("bare", "Bare", "")]
    except Exception:
        return [
            ("bare", "Bare", "Control case"),
            ("verdant", "Verdant Resonance", "Lush walkable ground, soft magic"),
            ("crystalline", "Crystalline Choir", "Hard glowing mineral world"),
            ("cathedral", "Sunken Cathedral", "Flooded basin, tall pillars"),
            ("full_bloom", "Full Bloom", "Everything on"),
        ]


def _tandem_preset_items(self, context):
    """Merged preset list for tandem: walkable + voxel. Indicates walkable vs voxel."""
    items = []
    try:
        from . import walkable_world as ww
        for key, val in sorted(ww.WALKABLE_PRESETS.items()):
            items.append((key, val.get("label", key) + " [Walkable]", val.get("description", "")))
    except Exception:
        pass
    try:
        mid = midi_bridge.preset_items()
        for key, label, desc in mid:
            # avoid dup if same key as walkable
            if not any(k == key for k, _, _ in items):
                items.append((key, label + " [Voxel]", desc))
    except Exception:
        pass
    return items if items else [("walkable_valley", "Walkable Valley [Walkable]", "")]


def _tandem_style_items(self, context):
    try:
        deploy = os.path.join(midi_bridge.repo_root(), "deploy")
        if deploy not in sys.path:
            sys.path.insert(0, deploy)
        from surreal_world import compose as _comp  # type: ignore
        return [(k, k.replace("_", " ").title(), "") for k in sorted(_comp.COMPOSE_STYLES.keys())]
    except Exception:
        # fallback to pairing keys
        try:
            from . import tandem_bridge as _tb  # type: ignore
            return [(k, k.replace("_", " ").title(), "") for k in sorted(set(v[0] for v in _tb.MELODIA_TO_SURREAL.values()))]
        except Exception:
            return [("WESTERN_CASTLE", "Western Castle", "")]


def _tandem_plan_items(self, context):
    try:
        from . import tandem_bridge as _tb  # type: ignore
        return [(k, k.replace("_", " ").title(), "") for k in _tb.PLAN_KINDS]
    except Exception:
        return [("castle", "Castle", ""), ("zen_roji", "Zen Roji", ""), ("village", "Village", "")]


# ------------------------------------------------------------- addon preferences (v1.5 +)

if bpy is not None:
    class MelodiaStudioPreferences(bpy.types.AddonPreferences):
        """Addon Preferences — C: authority root + extra MIDI dirs. Surface in Edit > Preferences > Add-ons > Melodia Studio."""
        bl_idname = "melodia_studio"

        project_root: bpy.props.StringProperty(
            name="Project Root",
            description="Override BS_GodFile root (default: auto-detect C:\\EnvironmentPortfolio\\BS_GodFile via $MELODIA_PROJECT_ROOT or walk-up). Leave empty for auto.",
            subtype='DIR_PATH',
            default="",
        )
        midi_extra_dirs: bpy.props.StringProperty(
            name="Extra MIDI Dirs",
            description="Semicolon-separated extra MIDI search dirs (e.g., G:\\MyMIDIs;D:\\Songs). Appended to Content/MelodiaIntegration/MIDI and Imports/Audio.",
            default="",
        )

        def draw(self, context):
            layout = self.layout
            layout.label(text="C Authority — empty = auto-detect (env $MELODIA_PROJECT_ROOT preferred)", icon='INFO')
            layout.prop(self, "project_root")
            layout.prop(self, "midi_extra_dirs")
            # hint
            row = layout.row()
            row.label(text="Extra dirs are appended to discover_midi()", icon='FILE_SOUND')


    class StudioProps(bpy.types.PropertyGroup):
        midi_file: bpy.props.EnumProperty(
            name="MIDI",
            description="Project MIDI to build terrain from (filtered by Search)",
            items=_midi_enum,
        )
        midi_filter: bpy.props.StringProperty(
            name="Search",
            description="Filter MIDI list (substring, case-insensitive)",
            default="",
            options={'TEXTEDIT_UPDATE'},
        )
        preset: bpy.props.EnumProperty(
            name="Preset",
            description="Musical to spatial mapping preset",
            items=_preset_enum,
        )
        custom_midi: bpy.props.StringProperty(
            name="Custom MIDI",
            description="Override with a MIDI file outside the project",
            subtype='FILE_PATH',
            default="",
        )
        dressing_style: bpy.props.EnumProperty(
            name="Dressing",
            description="Musical expansion preset applied to the terrain mesh",
            items=_dressing_items(),
            default="verdant",
        )
        auto_cleanup: bpy.props.BoolProperty(
            name="Auto-cleanup old Terrain",
            description="Remove previous Terrain / MS_* objects before generating",
            default=True,
        )
        last_report: bpy.props.StringProperty(name="Last Report", default="")
        last_midi: bpy.props.StringProperty(name="Last MIDI", default="")
        show_advanced: bpy.props.BoolProperty(
            name="Advanced",
            description="Show advanced/debug options",
            default=False,
        )
        # Tandem (terrain -> surreal city) - field-wins, snap plan to terrain height
        tandem_preset: bpy.props.EnumProperty(
            name="Tandem Preset",
            description="Preset that drives both terrain shape and city pairing (walkable preferred for clean ground)",
            items=_tandem_preset_items,
            default=0,
        )
        tandem_style: bpy.props.EnumProperty(
            name="Style",
            description="Surreal COMPOSE_STYLE override (empty = auto from preset pairing)",
            items=_tandem_style_items,
        )
        tandem_plan: bpy.props.EnumProperty(
            name="Plan",
            description="Surreal plan kind (castle/zen_roji/village etc). Empty = auto from preset",
            items=_tandem_plan_items,
        )
        dress_instance: bpy.props.BoolProperty(
            name="Instance Dressing",
            description="Actually instance dressing props as linked objects (not just count string)",
            default=True,
        )
        dress_seed: bpy.props.IntProperty(
            name="Seed",
            description="Deterministic seed for dressing placement",
            default=11,
            min=0, max=9999,
        )
        dress_budget: bpy.props.IntProperty(
            name="Budget",
            description="Max props to instance",
            default=400,
            min=0, max=5000,
        )

else:
    StudioProps = object  # type: ignore


# ------------------------------------------------------------- mesh build

def build_terrain_mesh(obj_path, mesh_name="Terrain"):
    """Build a mesh from the generator's OBJ (v x y z r g b) format."""
    if bpy is None:
        return None
    if not os.path.exists(obj_path):
        return None

    verts, faces, colors = [], [], []
    with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                if len(parts) >= 7:
                    colors.append((float(parts[4]), float(parts[5]), float(parts[6]), 1.0))
                else:
                    colors.append((0.5, 0.5, 0.5, 1.0))
            elif parts[0] == "f":
                faces.append([int(p.split("/")[0]) - 1 for p in parts[1:]])

    if not verts:
        return None

    mesh = bpy.data.meshes.new(mesh_name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    if colors:
        attr = mesh.color_attributes.new(name="AuraColor", type='FLOAT_COLOR', domain='CORNER')
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                vidx = mesh.loops[loop_idx].vertex_index
                if vidx < len(colors):
                    attr.data[loop_idx].color = colors[vidx]

    if len(mesh.uv_layers) == 0:
        mesh.uv_layers.new(name="UVMap")

    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(build_aura_material())
    return obj


def build_aura_material(name="M_ResonantAura"):
    """Material that actually samples AuraColor for base colour + emission."""
    if bpy is None:
        return None
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    col = nt.nodes.new('ShaderNodeVertexColor')
    col.layer_name = "AuraColor"
    col.location = (-300, 0)
    lum = nt.nodes.new('ShaderNodeRGBToBW')
    lum.location = (-100, -200)
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (60, -200)
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.95
    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(col.outputs['Color'], lum.inputs['Color'])
    nt.links.new(lum.outputs['Val'], ramp.inputs['Fac'])
    if 'Emission Color' in bsdf.inputs:
        nt.links.new(col.outputs['Color'], bsdf.inputs['Emission Color'])
    if 'Emission Strength' in bsdf.inputs:
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Emission Strength'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


# ---------------------------------------------------------------- dressing instancing (linked, low memory)
# Reuses the proven pattern from resonant_world_studio/build.py:176 but
# lives here so the primary Melodia Studio panel can instance without
# depending on that sibling addon.

_DRESS_COLL = "MS_Dressing"
_PROP_SHAPE = {
    "resonance_crystal": ("cone", 5.0, 0.12),
    "chime_pillar": ("cylinder", 3.5, 0.30),
    "moss_cluster": ("ico", 0.0, 0.85),
    "songstone": ("cube", 0.0, 0.70),
    "note_bloom": ("circle", 4.0, 0.40),
}

def _dress_collection():
    if bpy is None:
        return None
    coll = bpy.data.collections.get(_DRESS_COLL)
    if coll is None:
        coll = bpy.data.collections.new(_DRESS_COLL)
        bpy.context.scene.collection.children.link(coll)
    return coll

def _clear_dressing():
    if bpy is None:
        return 0
    coll = bpy.data.collections.get(_DRESS_COLL)
    if coll is None:
        # also clear legacy loose objects with MS_Dress prefix
        removed = 0
        for obj in list(bpy.data.objects):
            if obj.name.startswith("MS_Dress_"):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed += 1
                except Exception:
                    pass
        return removed
    for obj in list(coll.all_objects):
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            pass
    try:
        # keep the collection for next run
        pass
    except Exception:
        pass
    return 1

def _prop_material(name, colour, emission, roughness):
    if bpy is None:
        return None
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (300, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (0, 0)
    b.inputs['Base Color'].default_value = (*colour, 1.0)
    b.inputs['Roughness'].default_value = roughness
    if emission > 0:
        if 'Emission Color' in b.inputs:
            b.inputs['Emission Color'].default_value = (*colour, 1.0)
        if 'Emission Strength' in b.inputs:
            b.inputs['Emission Strength'].default_value = emission
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return mat

def _template_object(kind, colour):
    if bpy is None:
        return None
    name = f"MS_TPL_{kind}"
    existing = bpy.data.objects.get(name)
    if existing is not None:
        return existing
    shape, emit, rough = _PROP_SHAPE.get(kind, ("cube", 0.0, 0.6))
    try:
        if shape == "cone":
            bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.32, depth=1.1)
        elif shape == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.18, depth=2.0)
        elif shape == "ico":
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34)
        elif shape == "circle":
            bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.26, fill_type='NGON')
        else:
            bpy.ops.mesh.primitive_cube_add(size=0.42)
    except Exception:
        return None
    obj = bpy.context.active_object
    if obj is None:
        return None
    obj.name = name
    try:
        obj.data.materials.append(_prop_material(f"M_MS_{kind}", colour, emit, rough))
    except Exception:
        pass
    obj.hide_render = True
    obj.hide_viewport = True
    # move template far away so it never renders in view
    try:
        obj.location = (0, 0, -9999)
        obj.hide_set(True)
    except Exception:
        pass
    return obj

def _instance_dressing(midi_path: str, style_id: str, seed: int, budget: int) -> int:
    """Build field deterministically and instance dressing props. Returns count."""
    if bpy is None:
        return 0
    _clear_dressing()
    if style_id == "bare":
        return 0
    # Build field using shared core.field.build_field() pipeline
    try:
        from . import terrain_dressing as td
        from .core.field import build_field
        result = build_field(midi_path, "walkable_valley", source="walkable")
        if not result["ok"]:
            return 0
        field = result["field"]
        plan, _stats = td.plan_dressing(field, style_id=style_id, seed=seed, budget=budget)
    except Exception:
        return 0
    if not plan:
        return 0
    coll = _dress_collection()
    templates: dict = {}
    made = 0
    for spec in plan:
        kind = spec["kind"]
        if kind not in templates:
            tpl = _template_object(kind, tuple(spec["colour"]))
            if tpl is None:
                continue
            templates[kind] = tpl
        tpl = templates.get(kind)
        if tpl is None or tpl.data is None:
            continue
        try:
            inst = bpy.data.objects.new(f"MS_Dress_{kind}_{made}", tpl.data)
            coll.objects.link(inst)
            x, y, z = spec["location"]
            s = spec["scale"]
            inst.location = (float(x), float(y), float(z))
            inst.scale = (float(s), float(s), float(s))
            inst.rotation_euler = (0, 0, float(spec["rotation_z"]))
            made += 1
        except Exception:
            continue
    return made


def _selected_midi(props):
    if props.custom_midi:
        try:
            path = bpy.path.abspath(props.custom_midi)
        except Exception:
            path = props.custom_midi
        if os.path.exists(path):
            return path
    # Enum may be "" when filtered to no match
    val = getattr(props, "midi_file", "") or ""
    if val and os.path.exists(val):
        return val
    # Fallback: first discovered file so the button still works with a filter
    disc = _discover_cached()
    if disc:
        return disc[0]
    return None


def _midi_preview_lines(midi_path: str) -> str:
    """One-line summary: notes, beatgrid, size. Never throws."""
    try:
        mv = midi_bridge.load_voxel_module()
        tracks, tpb = mv.parse_midi(midi_path)
        if not tracks:
            return "No notes parsed"
        n = len(tracks[0])
        bg = midi_bridge.beatgrid_for(midi_path)
        bg_txt = " + beatgrid" if bg else ""
        size = ""
        try:
            kb = os.path.getsize(midi_path) / 1024.0
            size = f" - {kb:.0f} KB"
        except Exception:
            pass
        return f"{n} notes - TPB {tpb}{bg_txt}{size}"
    except Exception as exc:
        return f"Preview unavailable: {exc}"


# ------------------------------------------------------------- operators

if bpy is not None:

    class STUDIO_OT_generate_from_midi(bpy.types.Operator):
        """Generate Resonant World terrain from the selected MIDI"""
        bl_idname = "melodia_studio.generate_from_midi"
        bl_label = "Generate Terrain"
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):
            props = context.scene.melodia_studio
            midi = _selected_midi(props)
            if not midi:
                self.report({'WARNING'}, "No MIDI selected - pick one or set Custom MIDI")
                return {'CANCELLED'}

            # Remove only exact tool-owned names. Prefix deletion can destroy
            # owner-renamed objects such as ``Terrain_Final``.
            if getattr(props, "auto_cleanup", True):
                for generated_name in (
                    "Terrain",
                    "Showroom_Terrain",
                    "MS_Camera",
                    "MS_Key",
                    "MS_Fill",
                    "MS_Rim",
                ):
                    generated = bpy.data.objects.get(generated_name)
                    if generated is not None:
                        bpy.data.objects.remove(generated, do_unlink=True)

            # Progress feedback
            wm = context.window_manager
            try:
                wm.progress_begin(0, 100)
                wm.progress_update(10)
            except Exception:
                pass

            try:
                report = midi_bridge.generate_world(midi, preset_id=props.preset)
            except Exception as exc:
                try:
                    wm.progress_end()
                except Exception:
                    pass
                self.report({'ERROR'}, "Generation failed: %s" % exc)
                return {'CANCELLED'}

            if not report.get("ok"):
                try:
                    wm.progress_end()
                except Exception:
                    pass
                self.report({'ERROR'}, report.get("reason", "unknown failure"))
                return {'CANCELLED'}

            try:
                wm.progress_update(60)
            except Exception:
                pass

            # Remove stale Terrain object before linking new one (extra guard)
            if getattr(props, "auto_cleanup", True):
                try:
                    old = bpy.data.objects.get("Terrain")
                    if old is not None:
                        bpy.data.objects.remove(old, do_unlink=True)
                except Exception:
                    pass

            obj = build_terrain_mesh(report["obj"], "Terrain")
            if obj is None:
                try:
                    wm.progress_end()
                except Exception:
                    pass
                self.report({'ERROR'}, "OBJ produced no geometry")
                return {'CANCELLED'}

            try:
                wm.progress_update(80)
            except Exception:
                pass

            # QOL fix: pass midi so dressing builds a real field instead of {}
            try:
                dressing = midi_bridge.dress_terrain(
                    obj, report.get("obj", ""), props.dressing_style,
                    midi_path=midi,
                    seed=getattr(props, "dress_seed", 11),
                    budget=getattr(props, "dress_budget", 400),
                )
            except Exception as exc:
                self.report({'WARNING'}, "Dressing failed: %s" % exc)
                dressing = None

            # ---- NEW: actual instancing (linked, not realized) ----
            instanced = 0
            if getattr(props, "dress_instance", True) and dressing:
                try:
                    instanced = _instance_dressing(midi, props.dressing_style,
                                                   getattr(props, "dress_seed", 11),
                                                   getattr(props, "dress_budget", 400))
                    dressing += f" | instanced {instanced}"
                except Exception as exc:
                    self.report({'WARNING'}, f"Instancing failed: {exc}")

            try:
                wm.progress_end()
            except Exception:
                pass

            summary = "%d voxels | %d verts | %d faces" % (report["voxels"], report["verts"], report["faces"])
            if dressing:
                summary += " | %s" % dressing
            if instanced:
                summary += f" | {instanced} instances"
            props.last_report = summary
            props.last_midi = midi
            self.report({'INFO'}, "%s from %s" % (summary, os.path.basename(midi)))
            return {'FINISHED'}

    class STUDIO_OT_frame_terrain(bpy.types.Operator):
        """Add camera and lights scaled to the terrain bounds"""
        bl_idname = "melodia_studio.frame_terrain"
        bl_label = "Frame + Light"
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):
            import math
            import mathutils
            meshes = [o for o in context.scene.objects if o.type == 'MESH' and o.data]
            if not meshes:
                self.report({'WARNING'}, "No mesh to frame - Generate Terrain first")
                return {'CANCELLED'}
            mn = [1e18] * 3
            mx = [-1e18] * 3
            for o in meshes:
                for corner in o.bound_box:
                    w = o.matrix_world @ mathutils.Vector(corner)
                    for i in range(3):
                        mn[i] = min(mn[i], w[i])
                        mx[i] = max(mx[i], w[i])
            centre = mathutils.Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
            size = mathutils.Vector([mx[i] - mn[i] for i in range(3)])
            span = max(size)
            if span < 1e-6:
                self.report({'WARNING'}, "Degenerate bounds")
                return {'CANCELLED'}
            for name in ("MS_Camera", "MS_Key", "MS_Fill", "MS_Rim"):
                existing = bpy.data.objects.get(name)
                if existing:
                    bpy.data.objects.remove(existing, do_unlink=True)
            cam_data = bpy.data.cameras.new("MS_Camera")
            cam_data.lens = 50
            cam_data.clip_end = span * 20
            cam = bpy.data.objects.new("MS_Camera", cam_data)
            context.collection.objects.link(cam)
            fov = 2 * math.atan((cam_data.sensor_width * 0.5) / cam_data.lens)
            dist = (max(size.x, size.z * 1.4) * 0.5) / math.tan(fov * 0.5) * 1.25
            cam.location = (centre.x - span * 0.28, centre.y - dist * 0.82, centre.z + span * 0.42)
            direction = centre - cam.location
            cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            context.scene.camera = cam
            unit = span * span
            for name, energy, colour, loc in (
                ("MS_Key", unit * 2.2, (1.0, 0.94, 0.86), (centre.x + span * 0.6, centre.y - span * 0.75, centre.z + span * 0.7)),
                ("MS_Fill", unit * 0.55, (0.62, 0.75, 1.0), (centre.x - span * 0.8, centre.y - span * 0.5, centre.z + span * 0.25)),
                ("MS_Rim", unit * 1.5, (1.0, 0.55, 0.85), (centre.x, centre.y + span * 0.85, centre.z + span * 0.55)),
            ):
                data = bpy.data.lights.new(name, type='AREA')
                data.energy = energy
                data.color = colour
                data.size = span * 0.55
                obj = bpy.data.objects.new(name, data)
                obj.location = loc
                context.collection.objects.link(obj)
                d = centre - mathutils.Vector(loc)
                obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            self.report({'INFO'}, "Framed span %.1f units" % span)
            return {'FINISHED'}

    class STUDIO_OT_write_presets(bpy.types.Operator):
        """Write the preset file so it can be edited outside Blender"""
        bl_idname = "melodia_studio.write_presets"
        bl_label = "Export Presets"
        def execute(self, context):
            path = midi_bridge.write_presets()
            self.report({'INFO'}, "Presets -> %s" % path)
            return {'FINISHED'}

    class STUDIO_OT_save_scene(bpy.types.Operator):
        """Save the current scene into GeneratedScenes"""
        bl_idname = "melodia_studio.save_scene"
        bl_label = "Save Scene"
        scene_name: bpy.props.StringProperty(name="Name", default="")
        def execute(self, context):
            import time as _time
            name = self.scene_name.strip() or _time.strftime("scene_%Y%m%d_%H%M%S")
            target = os.path.join(midi_bridge.scenes_dir(), name)
            os.makedirs(target, exist_ok=True)
            blend = os.path.join(target, "scene.blend")
            bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
            self.report({'INFO'}, "Saved %s" % blend)
            return {'FINISHED'}
        def invoke(self, context, event):
            return context.window_manager.invoke_props_dialog(self)

    class STUDIO_OT_cleanup_scene(bpy.types.Operator):
        """Remove generated Terrain / MS_* / SR_* objects to start fresh"""
        bl_idname = "melodia_studio.cleanup_scene"
        bl_label = "Clean Up"
        bl_options = {'REGISTER', 'UNDO'}
        def execute(self, context):
            removed = 0
            for generated_name in (
                "Terrain",
                "Showroom_Terrain",
                "MS_Camera",
                "MS_Key",
                "MS_Fill",
                "MS_Rim",
            ):
                generated = bpy.data.objects.get(generated_name)
                if generated is not None:
                    bpy.data.objects.remove(generated, do_unlink=True)
                    removed += 1
            # Dressing instances (MS_Dressing collection + MS_Dress_/MS_TPL_ objects)
            try:
                coll = bpy.data.collections.get("MS_Dressing")
                if coll is not None:
                    for obj in list(coll.all_objects):
                        bpy.data.objects.remove(obj, do_unlink=True)
                    bpy.data.collections.remove(coll)
                    removed += 1
                for obj in list(bpy.data.objects):
                    if obj.name.startswith(("MS_Dress_", "MS_TPL_")):
                        bpy.data.objects.remove(obj, do_unlink=True)
                        removed += 1
            except Exception:
                pass
            # Tandem city collections (SurrealPlan + _Composed)
            try:
                for coll in list(bpy.data.collections):
                    if coll.name.startswith(("SurrealPlan", "SurrealWorld", "RW_")):
                        for obj in list(coll.all_objects):
                            try:
                                bpy.data.objects.remove(obj, do_unlink=True)
                            except Exception:
                                pass
            except Exception:
                pass
            self.report({'INFO'}, f"Cleaned {removed} generated object(s)")
            return {'FINISHED'}

    class STUDIO_OT_setup_script_directory(bpy.types.Operator):  # type: ignore
        """Add Tools/BlenderAddons to Blender's script directories (so melodia_utils resolves)"""
        bl_idname = "melodia_studio.setup_script_directory"
        bl_label = "Setup Script Directory"
        def execute(self, context):
            if _mu is not None:
                try:
                    root = _mu.repo_root()
                    addons = str(root / "Tools" / "BlenderAddons")
                    # Use addon_utils if available, else just report
                    if addon_utils is not None and hasattr(addon_utils, "open_folder"):
                        self.report({'INFO'}, f"Script dir: {addons} -- add via Preferences > File Paths > Script Directories if needed")
                    else:
                        self.report({'INFO'}, f"Addons: {addons}")
                    return {'FINISHED'}
                except Exception as exc:
                    self.report({'ERROR'}, str(exc))
                    return {'CANCELLED'}
            self.report({'WARNING'}, "melodia_utils not available")
            return {'CANCELLED'}

    class STUDIO_OT_render_proof(bpy.types.Operator):
        """Render a proof image of the current terrain"""
        bl_idname = "melodia_studio.render_proof"
        bl_label = "Render Proof"
        bl_options = {'REGISTER'}

        def execute(self, context):
            props = context.scene.melodia_studio
            midi = _selected_midi(props)
            if not midi:
                self.report({'WARNING'}, "No MIDI selected")
                return {'CANCELLED'}

            # Find terrain mesh
            terrain = bpy.data.objects.get("Terrain")
            if terrain is None:
                self.report({'WARNING'}, "No Terrain object - Generate first")
                return {'CANCELLED'}

            # Render
            import math
            import mathutils
            mn = [1e18] * 3
            mx = [-1e18] * 3
            for o in [terrain]:
                for corner in o.bound_box:
                    w = o.matrix_world @ mathutils.Vector(corner)
                    for i in range(3):
                        mn[i] = min(mn[i], w[i])
                        mx[i] = max(mx[i], w[i])
            centre = mathutils.Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
            size = mathutils.Vector([mx[i] - mn[i] for i in range(3)])
            span = max(size)

            # Camera
            cam_data = bpy.data.cameras.get("MS_Camera") or bpy.data.cameras.new("MS_Camera")
            cam_data.lens = 50
            cam_data.clip_end = span * 20
            cam = bpy.data.objects.get("MS_Camera")
            if cam is None:
                cam = bpy.data.objects.new("MS_Camera", cam_data)
                context.collection.objects.link(cam)
            fov = 2 * math.atan((cam_data.sensor_width * 0.5) / cam_data.lens)
            dist = (max(size.x, size.z * 1.4) * 0.5) / math.tan(fov * 0.5) * 1.25
            cam.location = (centre.x - span * 0.28, centre.y - dist * 0.82, centre.z + span * 0.42)
            direction = centre - cam.location
            cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            context.scene.camera = cam

            # Output
            out = os.path.join(midi_bridge.repo_root(), "Saved", "Audit",
                               "melodia_studio_render.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            sc = context.scene
            sc.render.engine = 'BLENDER_EEVEE'
            sc.render.resolution_x = 1280
            sc.render.resolution_y = 720
            sc.render.image_settings.file_format = 'PNG'
            sc.render.filepath = out
            bpy.ops.render.render(write_still=True)
            self.report({'INFO'}, "Rendered %s" % out)
            return {'FINISHED'}

    class STUDIO_OT_batch_render(bpy.types.Operator):
        """Batch render all presets for the selected MIDI"""
        bl_idname = "melodia_studio.batch_render"
        bl_label = "Batch Render"
        bl_options = {'REGISTER'}

        def execute(self, context):
            props = context.scene.melodia_studio
            midi = _selected_midi(props)
            if not midi:
                self.report({'WARNING'}, "No MIDI selected")
                return {'CANCELLED'}

            # Run daemon
            import subprocess
            daemon = os.path.join(midi_bridge.repo_root(), "Tools",
                                  "midi_worldgen_daemon.py")
            if not os.path.exists(daemon):
                self.report({'WARNING'}, "Daemon not found: %s" % daemon)
                return {'CANCELLED'}

            python_exe = os.environ.get("MELODIA_PYTHON_EXE")
            if not python_exe:
                candidate = os.path.basename(sys.executable).lower()
                if candidate.startswith("python"):
                    python_exe = sys.executable
                else:
                    python_exe = shutil.which("python")
            if not python_exe:
                self.report({'ERROR'}, "Python not found; set MELODIA_PYTHON_EXE")
                return {'CANCELLED'}

            result = subprocess.run(
                [python_exe, "-B", daemon],
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                self.report({'INFO'}, "Batch render complete")
            else:
                self.report({'ERROR'}, "Batch failed: %s" % result.stderr[-200:])
                return {'CANCELLED'}
            return {'FINISHED'}

    class STUDIO_OT_open_folder(bpy.types.Operator):
        """Open a Melodia folder in the OS file browser"""
        bl_idname = "melodia_studio.open_folder"
        bl_label = "Open Folder"
        folder: bpy.props.EnumProperty(
            name="Folder",
            items=[
                ("scenes", "GeneratedScenes", "Tools/MelodiaProceduralStudio/GeneratedScenes"),
                ("midi", "MIDI", "Content/MelodiaIntegration/MIDI"),
                ("addons", "BlenderAddons", "Tools/BlenderAddons"),
                ("showroom", "Showroom", "Tools/MelodiaProceduralStudio/GeneratedScenes/showroom"),
            ],
            default="scenes",
        )
        def execute(self, context):
            key = self.folder
            if _mu is not None:
                root = _mu.repo_root()
                mapping = {
                    "scenes": _mu.scenes_dir(),
                    "midi": _mu.midi_content_dir(),
                    "addons": root / "Tools" / "BlenderAddons",
                    "showroom": _mu.scenes_dir() / "showroom",
                }
                target = mapping.get(key, root)
            else:
                base = midi_bridge.repo_root()
                mapping = {
                    "scenes": os.path.join(base, "Tools", "MelodiaProceduralStudio", "GeneratedScenes"),
                    "midi": os.path.join(base, "Content", "MelodiaIntegration", "MIDI"),
                    "addons": os.path.join(base, "Tools", "BlenderAddons"),
                    "showroom": os.path.join(base, "Tools", "MelodiaProceduralStudio", "GeneratedScenes", "showroom"),
                }
                target = mapping.get(key, base)
            if addon_utils is not None:
                p = addon_utils.open_folder(target)
            else:
                Path(target).mkdir(parents=True, exist_ok=True)
                p = str(target)
            self.report({'INFO'}, f"Opened {p}")
            return {'FINISHED'}

    class STUDIO_OT_refresh_midi(bpy.types.Operator):
        """Re-scan MIDI files"""
        bl_idname = "melodia_studio.refresh_midi"
        bl_label = "Refresh"
        bl_options = {'REGISTER'}
        def execute(self, context):
            global _MIDI_CACHE_TIME
            _MIDI_CACHE_TIME = 0
            _discover_cached()
            self.report({'INFO'}, f"Found {len(_MIDI_CACHE)} MIDI file(s)")
            # Force UI redraw
            for area in context.screen.areas:
                area.tag_redraw()
            return {'FINISHED'}

    class STUDIO_OT_validate_health(bpy.types.Operator):
        """Run offline health checks and write report to last_report"""
        bl_idname = "melodia_studio.validate_health"
        bl_label = "Validate"
        def execute(self, context):
            if _mu is None:
                self.report({'WARNING'}, "melodia_utils not importable - check Script Directories")
                return {'CANCELLED'}
            h = _mu.health_check()
            props = context.scene.melodia_studio
            if h["ok"]:
                props.last_report = f"Health OK - {h['midi_count']} MIDIs, {h['repo_root']}"
                self.report({'INFO'}, "Health OK - C: authority")
            else:
                props.last_report = "Health: " + "; ".join(h["issues"][:2])
                self.report({'WARNING'}, "; ".join(h["issues"][:2]))
            return {'FINISHED'}

else:
    STUDIO_OT_generate_from_midi = STUDIO_OT_frame_terrain = STUDIO_OT_write_presets = STUDIO_OT_save_scene = object  # type: ignore
    STUDIO_OT_cleanup_scene = STUDIO_OT_setup_script_directory = STUDIO_OT_open_folder = STUDIO_OT_refresh_midi = STUDIO_OT_validate_health = object  # type: ignore


# ------------------------------------------------------------- panels

if bpy is not None:

    def _icon(key, fallback):
        if addon_utils is not None:
            try:
                return addon_utils.icon_kwargs(key, fallback)
            except Exception:
                pass
        return {"icon": fallback}

    class STUDIO_PT_panel(bpy.types.Panel):
        bl_label = "Melodia Studio"
        bl_idname = "STUDIO_PT_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Melodia Studio"  # separate tab per owner
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            props = context.scene.melodia_studio

            # Gold-ivory luxury header with pink/rose-gold pillar (cathedral)
            if _chrome is not None:
                try:
                    _chrome.chrome_header(layout, "Studio", "MIDI  ->  Walkable Ground  |  Field-Wins", pillar="cathedral", icon_key="starlight")
                except Exception:
                    pass
            else:
                # fallback: health hint (one line, not noisy)
                if _mu is not None:
                    h = _mu.health_check()
                    if not h["ok"] and h["issues"]:
                        box = layout.box()
                        box.alert = True
                        box.label(text="Setup needed", icon='ERROR')
                        box.label(text=h["issues"][0])

            # Health status as single kicker line (luxury, not red box) when chrome present
            if _chrome is not None and _mu is not None:
                try:
                    h = _mu.health_check()
                    if not h["ok"] and h["issues"]:
                        _chrome.chrome_status(layout, False, "Setup needed", h["issues"][0])
                except Exception:
                    pass

            # Resonant World
            if _chrome is not None:
                try:
                    _chrome.chrome_kicker(layout, "Resonant World", icon='FILE_SOUND')
                except Exception:
                    pass
            box = layout.box()
            row = box.row()
            if _chrome is None:
                row.label(text="Resonant World", icon='FILE_SOUND')
            row.operator("melodia_studio.refresh_midi", text="", icon='FILE_REFRESH')
            # Search + MIDI picker
            box.prop(props, "midi_filter", text="", icon='VIEWZOOM')
            box.prop(props, "midi_file", text="")
            # Truncate hint (audit P0)
            try:
                _found_all = _discover_cached()
                if len(_found_all) > 64:
                    box.label(text=f"Showing 64 of {len(_found_all)} - use search", icon='INFO')
            except Exception:
                pass
            # Preview line for selected MIDI
            midi = _selected_midi(props)
            if midi and os.path.exists(midi):
                box.label(text=_midi_preview_lines(midi), icon='INFO')
            box.prop(props, "preset", text="Preset")
            box.prop(props, "custom_midi", text="Custom")

            # Dressing + options
            if _chrome is not None:
                try:
                    _chrome.chrome_kicker(box, "Dressing  |  Pink  &  Rose Gold", icon='BRUSH_DATA')
                except Exception:
                    pass
            box.prop(props, "dressing_style", text="Dressing")
            row = box.row()
            row.prop(props, "auto_cleanup")
            row.prop(props, "show_advanced", text="Advanced")
            # Instance controls (-visible always; advanced shows seed/budget)
            row2 = box.row(align=True)
            row2.prop(props, "dress_instance", text="Instance Props")
            if props.show_advanced:
                row3 = box.row(align=True)
                row3.prop(props, "dress_seed", text="Seed")
                row3.prop(props, "dress_budget", text="Budget")

            col = box.column(align=True)
            col.scale_y = 1.4
            col.operator("melodia_studio.generate_from_midi", **_icon("generate", 'MOD_BUILD'))  # type: ignore[arg-type]

            # Presentation
            if _chrome is not None:
                try:
                    _chrome.chrome_kicker(layout, "Presentation", icon='LIGHT')
                except Exception:
                    pass
            box2 = layout.box()
            if _chrome is None:
                box2.label(text="Presentation", icon='LIGHT')
            col = box2.column(align=True)
            col.operator("melodia_studio.frame_terrain", icon='CAMERA_DATA')
            row = col.row(align=True)
            row.operator("melodia_studio.render_proof", icon='RENDER_STILL')
            row.operator("melodia_studio.batch_render", icon='RENDER_ANIMATION')
            row = col.row(align=True)
            row.operator("melodia_studio.save_scene", icon='FILE_TICK')
            row.operator("melodia_studio.cleanup_scene", icon='TRASH')

            # Config
            if props.show_advanced:
                box3 = layout.box()
                box3.label(text="Config", icon='PREFERENCES')
                box3.operator("melodia_studio.write_presets", icon='EXPORT')
                row = box3.row(align=True)
                row.operator("melodia_studio.open_folder", text="MIDI").folder = "midi"  # type: ignore[attr-defined]
                row.operator("melodia_studio.open_folder", text="Scenes").folder = "scenes"  # type: ignore[attr-defined]
                row = box3.row(align=True)
                row.operator("melodia_studio.validate_health", icon='CHECKMARK')

            if props.last_report:
                layout.separator()
                box = layout.box()
                box.label(text="Last run", icon='CHECKMARK')
                # Wrap long report
                for line in str(props.last_report).split(" | "):
                    box.label(text=line)
                if props.last_midi:
                    box.label(text=os.path.basename(props.last_midi), icon='FILE_SOUND')

    class STUDIO_PT_management(bpy.types.Panel):
        bl_label = "Management"
        bl_idname = "STUDIO_PT_management"
        bl_parent_id = "STUDIO_PT_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Melodia Studio"
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            if _chrome is not None:
                try:
                    _chrome.chrome_header(layout, "Management", "C Authority  |  Autosync", pillar="grotto", icon_key="starlight")
                except Exception:
                    pass

            # 4-row health dashboard
            if _mu is not None:
                root = _mu.repo_root()
                h = _mu.health_check()

                box = layout.box()
                box.label(text="Health", icon='HEART')
                row = box.row()
                row.label(text="Repo: %s" % os.path.basename(root), icon='FILE_FOLDER')
                row.alignment = 'RIGHT'
                row.label(text="OK" if h["ok"] else "ISSUES",
                          icon='CHECKMARK' if h["ok"] else 'ERROR')

                row = box.row()
                row.label(text="MIDI: %d files" % h.get("midi_count", 0),
                          icon='FILE_SOUND')

                if h.get("issues"):
                    for iss in h["issues"][:3]:
                        row = box.row()
                        row.label(text=iss, icon='ERROR')
                    if len(h["issues"]) > 3:
                        row = box.row()
                        row.label(text=f"... +{len(h['issues'])-3} more", icon='INFO')
                else:
                    row = box.row()
                    row.label(text="All systems nominal", icon='CHECKMARK')

                vers = _mu.addon_versions()
                if vers:
                    row = box.row()
                    row.label(text="Addons: %d" % len(vers), icon='PACKAGE')
                # GN preset badge — live audit if surreal_arch on path
                try:
                    import importlib.util as _ilu
                    import pathlib as _pl
                    _gn_presets = _pl.Path(midi_bridge.repo_root()) / "deploy" / "surreal_arch" / "melodia_gn" / "presets.py"
                    if _gn_presets.exists():
                        spec = _ilu.spec_from_file_location("_gn_presets_tmp", str(_gn_presets))
                        if spec and spec.loader:
                            mod = _ilu.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            rep = mod.audit_presets() if hasattr(mod, "audit_presets") else {}
                            cov = rep.get("coverage_ratio", 0)
                            pb = rep.get("preset_builders", 0)
                            rb = rep.get("registered_builders") or rep.get("preset_builders", 0)
                            row = box.row()
                            row.label(text=f"GN: {pb}/{rb} presets {cov*100:.0f}%", icon='NODETREE')
                except Exception:
                    pass
                # AppData drift hint
                try:
                    if _mu is not None and hasattr(_mu, "addon_versions"):
                        av = _mu.addon_versions()
                        tools_ver = None
                        appdata_ver = None
                        for k, v in (av or {}).items():
                            if "melodia_studio" in k.lower():
                                tools_ver = v
                                break
                        if tools_ver:
                            row = box.row()
                            row.label(text=f"Melodia Studio {tools_ver}", icon='INFO')
                except Exception:
                    pass
            else:
                layout.label(text=midi_bridge.repo_root(), icon='FILE_FOLDER')
                layout.label(text="melodia_utils not available", icon='ERROR')

            col = layout.column(align=True)
            col.operator("melodia_studio.validate_health", icon='HEART')
            row = col.row(align=True)
            row.operator("melodia_studio.setup_script_directory",
                         icon='SCRIPTPLUGINS')
            row.operator("melodia_studio.open_folder",
                         text="Addons").folder = "addons"  # type: ignore[attr-defined]
            row = col.row(align=True)
            row.operator("melodia_studio.open_folder",
                         text="Showroom").folder = "showroom"  # type: ignore[attr-defined]

    classes = [
        MelodiaStudioPreferences,
        StudioProps,
        STUDIO_OT_generate_from_midi,
        STUDIO_OT_frame_terrain,
        STUDIO_OT_write_presets,
        STUDIO_OT_save_scene,
        STUDIO_OT_cleanup_scene,
        STUDIO_OT_setup_script_directory,
        STUDIO_OT_render_proof,
        STUDIO_OT_batch_render,
        STUDIO_OT_open_folder,
        STUDIO_OT_refresh_midi,
        STUDIO_OT_validate_health,
        STUDIO_PT_panel,
        STUDIO_PT_management,
    ]

else:
    classes = []  # type: ignore


def register():
    if bpy is None:
        return
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass
    try:
        bpy.types.Scene.melodia_studio = bpy.props.PointerProperty(type=StudioProps)  # type: ignore[attr-defined]
    except Exception:
        pass


def unregister():
    if bpy is None:
        return
    if hasattr(bpy.types.Scene, "melodia_studio"):
        try:
            del bpy.types.Scene.melodia_studio  # type: ignore[attr-defined]
        except Exception:
            pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
