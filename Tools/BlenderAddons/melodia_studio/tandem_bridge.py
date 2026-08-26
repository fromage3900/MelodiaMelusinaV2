"""Tandem bridge - Melodia Studio terrain <-> Surreal Architecture city.

No edits to deploy/surreal_architecture_gen.py (the GN baby). This module
is the ONLY place that touches both systems. It runs in-Blender (bpy) but
its height helpers are testable offline.

Field-wins: terrain height dictates building Z. We snap the 2D surreal plan
(XY flat at Z=0) onto the musical heightfield via surface_height_at() and
pad/level 1-cell around walls/gates so props and feet don't float.

Consumer-only: calls surreal_world/plans, compose, instance, export via
importlib (deploy is on sys.path like elsewhere) and never mutates the
monolith's registries.
"""

from __future__ import annotations

import os
import sys
import math
import json
from pathlib import Path
from datetime import datetime, timezone

try:
    import bpy  # type: ignore
    import mathutils  # type: ignore
except Exception:
    bpy = None  # type: ignore
    mathutils = None  # type: ignore

_HERE = Path(__file__).resolve().parent
_ADDONS_ROOT = _HERE.parent
_REPO_FALLBACK = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
_DEPLOY = _REPO_FALLBACK / "deploy"

# Ensure melodia_utils is reachable when run outside Blender
if str(_ADDONS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ADDONS_ROOT))
try:
    import melodia_utils as _mu  # type: ignore
except Exception:
    _mu = None  # type: ignore

try:
    from . import terrain_dressing as _td  # type: ignore
except Exception:
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("terrain_dressing", str(_HERE / "terrain_dressing.py"))
        _td = _ilu.module_from_spec(_spec)  # type: ignore
        assert _spec.loader is not None
        _spec.loader.exec_module(_td)  # type: ignore
    except Exception:
        _td = None  # type: ignore

# ---------------------------------------------------------------- pairing table
# Like _batch_remaining_presets STYLE_FOR_PRESET but melodia_preset -> surreal COMPOSE_STYLE
# plus a sensible plan kind per melodia family. User can override style in UI.
MELODIA_TO_SURREAL = {
    # melodia_studio walkable preset -> (surreal COMPOSE_STYLE, plan_kind, dressing_hint)
    "walkable_valley":     ("WESTERN_CASTLE",      "castle",      "verdant"),
    "walkable_highlands":  ("GOTHIC_NAVE_CROSSING","castle",      "crystalline"),
    "walkable_plaza":      ("RENAISSANCE_PIAZZA",  "grid_city",   "ballad_plaza"),
    "walkable_canyon":     ("BRUTALIST_PLAZA",     "motte_bailey","cathedral"),
    "walkable_spiral_arena": ("ZEN_SHRINE",        "zen_temple",  "crystalline"),
    # midi_bridge voxel presets (legacy) -> surreal
    "resonant_default":    ("WESTERN_VILLAGE",     "village",     "verdant"),
    "cathedral_wide":      ("GOTHIC_CLOISTER",     "castle",      "cathedral"),
    "dense_spire":         ("BRUTALIST_PLAZA",     "grid_city",   "toccata_surface"),
    "surface_only":        ("RENAISSANCE_PIAZZA",  "grid_city",   "bare"),
    "abyss_caves":         ("ROMANESQUE_CLOISTER", "motte_bailey","pavane_grotto"),
    "waltz_corridors":     ("ZEN_SHRINE",          "zen_roji",    "waltz_garden"),
    "ballad_broadstage":   ("RENAISSANCE_PIAZZA",  "grid_city",   "ballad_plaza"),
    "toccata_spires":      ("SCIFI_DECK",          "grid_city",   "toccata_surface"),
    "lullaby_undergrowth": ("ROMANESQUE_APSE",     "zen_roji",    "lullaby_cave"),
    "fugue_labyrinth":     ("GOTHIC_CHAPTER_HOUSE","village",     "fugue_maze"),
    "nocturne_ribbon":     ("VENETIAN_CANAL",      "zen_roji",    "nocturne_reflection"),
    "tarantella_bounce":   ("ART_DECO",            "grid_city",   "saltarello_ledges"),
    "canon_echo":          ("BYZANTINE_BASILICA",  "village",     "aria_mist"),
    "gavotte_hedges":      ("ART_NOUVEAU",         "village",     "verdant"),
    "rhapsody_fold":       ("BAROQUE_CHURCH",      "castle",      "chaconne_weave"),
    "berceuse_overhang":   ("ZEN_SHRINE",          "zen_roji",    "madrigal_canopy"),
    "ritornello_rings":    ("GOTHIC_NAVE_CROSSING","castle",      "crystalline"),
}

# Ancient Cultures instrument pairings (see ancient_cultures.py) merged at import
try:
    from .ancient_cultures import ANCIENT_TANDEM_PAIRS as _AC_PAIRS  # type: ignore
    for _k, _v in _AC_PAIRS.items():
        MELODIA_TO_SURREAL.setdefault(_k, tuple(_v))
except Exception:
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "ancient_cultures",
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "ancient_cultures.py"))
        if _spec is not None and _spec.loader is not None:
            _ac = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_ac)
            for _k, _v in getattr(_ac, "ANCIENT_TANDEM_PAIRS", {}).items():
                MELODIA_TO_SURREAL.setdefault(_k, tuple(_v))
    except Exception:
        pass

# Also expose plan spawner keys -> surreal_world.plans function names
PLAN_KINDS = ("castle", "zen_roji", "zen_temple", "village", "grid_city", "motte_bailey")

def resolve_tandem_pair(preset_id: str) -> tuple[str, str]:
    """(surreal_style, plan_kind) for a melodia preset, with safe default."""
    style, plan, _hint = MELODIA_TO_SURREAL.get(preset_id, ("WESTERN_CASTLE", "castle", "verdant"))
    return style, plan

def repo_root() -> Path:
    if _mu is not None:
        try:
            return _mu.repo_root()
        except Exception:
            pass
    return _REPO_FALLBACK

# ---------------------------------------------------------------- pure helpers (offline-safe)

def snap_plan_to_field(plan_obj, field: dict, base_z: float = 0.0) -> int:
    """Move a flat SurrealPlan so its vertices sit on the musical terrain.

    For each mesh vertex, Z = surface_height_at(field, world_x, world_y).
    Uses math.floor per terrain_dressing fix. Returns vertices snapped.
    """
    if plan_obj is None or not field:
        return 0
    if _td is None:
        return 0
    try:
        me = plan_obj.data
        mat = plan_obj.matrix_world
        # plan is at plan_obj.location; vertices are local
        count = 0
        for v in me.vertices:
            w = mat @ v.co if mathutils is not None else v.co
            h = _td.surface_height_at(field, float(w.x), float(w.y))
            # Convert back to local: local Z = world Z - object location Z
            # simpler: offset vertex local Z so world Z == h
            world_z = float(w.z)
            delta = float(h) - world_z + float(base_z)
            v.co.z += delta
            count += 1
        me.update()
        return count
    except Exception:
        return 0

def pad_and_level(plan_obj, field: dict, radius: int = 1) -> int:
    """Flatten a small pad around gate/corner verts so feet don't float.

    Very gentle: for each vertex in is_gate/is_corner_tower groups, force the
    surrounding field cells to that vertex's height within `radius`. Returns
    cells patched. Does NOT mutate the visual mesh beyond snap; it patches the
    dict so later surface_height_at queries are flat.
    """
    if not plan_obj or not field or radius <= 0:
        return 0
    try:
        me = plan_obj.data
        mat = plan_obj.matrix_world
        vgroups = {vg.name: vg.index for vg in plan_obj.vertex_groups}
        target_idxs: set[int] = set()
        for name in ("is_gate", "is_corner_tower", "is_keep"):
            idx = vgroups.get(name)
            if idx is None:
                continue
            for v in me.vertices:
                for g in v.groups:
                    if g.group == idx:
                        target_idxs.add(v.index)
                        break
        if not target_idxs:
            return 0
        patched = 0
        for vi in target_idxs:
            w = mat @ me.vertices[vi].co if mathutils is not None else me.vertices[vi].co
            h = _td.surface_height_at(field, float(w.x), float(w.y)) if _td else float(w.z)
            cx, cy = int(math.floor(float(w.x))), int(math.floor(float(w.y)))
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    key = (cx + dx, cy + dy)
                    if key in field:
                        # level to porch height, keep velocity
                        vel = field[key][1]
                        field[key] = (int(round(float(h))), vel)
                        patched += 1
        return patched
    except Exception:
        return 0

def field_from_midi(midi_path: str, preset_id: str):
    """Build the same field Melodia Studio's Generate uses, for snapping.

    Returns (field, preset_dict, metrics) or (None, None, None).
    """
    try:
        # reuse walkable_world path (the real walkable field)
        walkable_dir = _HERE
        if str(walkable_dir) not in sys.path:
            sys.path.insert(0, str(walkable_dir))
        import walkable_world as ww  # type: ignore
        mv = ww.load_voxel_module()
        preset = ww.WALKABLE_PRESETS.get(preset_id)
        if preset is None:
            # fall back to midi_bridge preset families -> walkable_valley
            preset = ww.WALKABLE_PRESETS.get("walkable_valley")
            preset_id = "walkable_valley"
        tracks, tpb = mv.parse_midi(midi_path)
        if not tracks:
            return None, None, None
        notes = list(tracks[0])
        stem, ext = os.path.splitext(midi_path)
        bg = stem + "_beatgrid" + ext
        if os.path.exists(bg):
            try:
                b_tracks, b_tpb = mv.parse_midi(bg)
                if b_tracks and b_tpb:
                    s = float(tpb) / float(b_tpb)
                    notes.extend((int(n[0] * s), n[1] + 36, n[2]) for n in b_tracks[0])
                    notes.sort()
            except Exception:
                pass
        field, _gw = ww.build_heightfield(notes, preset["cells_per_beat"], preset["height_scale"],
                                          preset["plateau_radius"], tpb, preset.get("fold", "serpentine"))
        field = ww.fill_gaps(field)
        field = ww.limit_slope(field, preset["max_slope"], preset["smooth_passes"])
        metrics = ww.walkability(field, preset["max_slope"])
        metrics["largest_region"] = ww.largest_connected_region(field, preset["max_slope"])
        metrics["largest_region_fraction"] = round(metrics["largest_region"] / float(max(1, metrics["cells"])), 3)
        return field, preset, metrics
    except Exception as exc:
        print(f"[Tandem] field_from_midi failed: {exc}")
        return None, None, None

# ---------------------------------------------------------------- Blender operators / panel (only when bpy present)

try:
    from . import melodia_chrome as _chrome  # type: ignore
except Exception:
    _chrome = None  # type: ignore

if bpy is not None:

    def _surreal_available() -> tuple[bool, str]:
        """Is the surreal monolith importable?"""
        try:
            deploy = str(_DEPLOY)
            if deploy not in sys.path:
                sys.path.insert(0, deploy)
            import importlib.util as _ilu
            spec = _ilu.find_spec("surreal_world.compose")
            if spec is None:
                return False, f"surreal_world not on sys.path ({deploy})"
            return True, "ok"
        except Exception as exc:
            return False, str(exc)

    def _compose_style_items(self, context):
        # COMPOSE_STYLES canonical list; keep sorted like surreal does
        try:
            deploy = str(_DEPLOY)
            if deploy not in sys.path:
                sys.path.insert(0, deploy)
            from surreal_world import compose as _comp  # type: ignore
            items = []
            for key in sorted(_comp.COMPOSE_STYLES.keys()):
                items.append((key, key.replace("_", " ").title(), ""))
            return items or [("WESTERN_CASTLE", "Western Castle", "")]
        except Exception:
            return [(k, k.replace("_", " ").title(), "") for k in ("WESTERN_CASTLE","ZEN_SHRINE","GOTHIC_CLOISTER")]

    def _plan_kind_items(self, context):
        return [(k, k.replace("_", " ").title(), "") for k in PLAN_KINDS]

    class STUDIO_OT_tandem_compose(bpy.types.Operator):  # type: ignore
        """Spawn Surreal plan, snap it to Melodia terrain, and compose instances"""
        bl_idname = "melodia_studio.tandem_compose"
        bl_label = "Compose City On Terrain"
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):
            props = getattr(context.scene, "melodia_studio", None)
            if props is None:
                self.report({'ERROR'}, "Melodia Studio props not found")
                return {'CANCELLED'}

            # Terrain must exist
            terrain = bpy.data.objects.get("Terrain")
            if terrain is None:
                terrain = bpy.data.objects.get("RW_Terrain")
            if terrain is None:
                self.report({'WARNING'}, "Generate Terrain first (no Terrain/RW_Terrain)")
                return {'CANCELLED'}

            # Resolve MIDI -> field (for snapping)
            midi_path = None
            try:
                from . import studio_panel as _sp
                midi_path = _sp._selected_midi(props)  # reuse panel's picker logic
            except Exception:
                pass
            if not midi_path or not os.path.exists(midi_path):
                # fallback: last_midi
                midi_path = getattr(props, "last_midi", "") or ""
                if not midi_path or not os.path.exists(midi_path):
                    self.report({'WARNING'}, "No MIDI selected - pick one in Resonant World")
                    return {'CANCELLED'}

            preset_id = getattr(props, "preset", "resonant_default")
            # Prefer walkable_tandem_preset if present, else panel preset
            tandem_preset = getattr(props, "tandem_preset", "") or preset_id
            if tandem_preset in ("", None):
                tandem_preset = preset_id

            field, _preset, metrics = field_from_midi(midi_path, tandem_preset)
            # If field_from_midi used walkable preset, ok; if it fell back to walkable_valley,
            # we still snap - better than flat.
            if field is None:
                self.report({'ERROR'}, "Could not rebuild field for snapping")
                return {'CANCELLED'}

            surreal_style = getattr(props, "tandem_style", "") or resolve_tandem_pair(tandem_preset)[0]
            plan_kind = getattr(props, "tandem_plan", "") or resolve_tandem_pair(tandem_preset)[1]

            # Import surreal_world as consumer (no monolith mutation)
            try:
                deploy = str(_DEPLOY)
                if deploy not in sys.path:
                    sys.path.insert(0, deploy)
                from surreal_world import plans as _plans  # type: ignore
                from surreal_world import compose as _compose  # type: ignore
            except Exception as exc:
                self.report({'ERROR'}, f"Surreal import failed: {exc}")
                return {'CANCELLED'}

            # Spawn plan at terrain centre so city sits on terrain, not at origin
            try:
                import mathutils as _mu2
                # centre from terrain bounds
                mn = [1e18]*3; mx = [-1e18]*3
                for corner in terrain.bound_box:
                    w = terrain.matrix_world @ _mu2.Vector(corner)
                    for i in range(3):
                        mn[i] = min(mn[i], float(w[i])); mx[i] = max(mx[i], float(w[i]))
                centre = _mu2.Vector([(mn[i]+mx[i])/2 for i in range(3)])
                location = (float(centre.x), float(centre.y), 0.0)
            except Exception:
                location = (0.0, 0.0, 0.0)

            spawner = getattr(_plans, f"spawn_{plan_kind}_plan", None)
            if spawner is None:
                spawner = _plans.spawn_castle_plan
            try:
                plan_obj = spawner(location=location)
            except Exception as exc:
                self.report({'ERROR'}, f"Plan spawn failed: {exc}")
                return {'CANCELLED'}

            snapped = snap_plan_to_field(plan_obj, field)
            padded = pad_and_level(plan_obj, field, radius=1)

            # Compose - COLLECTION mode is safe (no destructive JOIN)
            try:
                # Need monolith handle for style genome; we pass None and let compose resolve without it
                world_root, msg = _compose.compose_world(None, context, plan_obj, style_key=surreal_style, detail_scale=1.0, compose_mode="COLLECTION")
                if world_root is None:
                    self.report({'WARNING'}, msg or "Compose placed nothing")
                    return {'CANCELLED'}
                # Annotate with tandem provenance
                world_root["melodia_tandem_preset"] = tandem_preset
                world_root["melodia_tandem_style"] = surreal_style
                world_root["melodia_tandem_plan"] = plan_kind
                world_root["melodia_snapped_verts"] = snapped
                world_root["melodia_padded_cells"] = padded
            except Exception as exc:
                self.report({'ERROR'}, f"Compose failed: {exc}")
                return {'CANCELLED'}

            # Dressing cross-tag: instance a few props on wall tops? Leave to Generate's dressing.
            # We just ensure the plan is hidden after compose (world is what matters)
            try:
                plan_obj.hide_viewport = True
                plan_obj.hide_render = True
            except Exception:
                pass

            # Last report
            try:
                props.last_report = f"Tandem {tandem_preset} -> {surreal_style}/{plan_kind} | snap {snapped} verts | {msg}"
                props.last_midi = midi_path
            except Exception:
                pass
            self.report({'INFO'}, f"Tandem: {surreal_style}/{plan_kind} on {tandem_preset} ({snapped} verts snapped)")
            return {'FINISHED'}

    class STUDIO_OT_tandem_export(bpy.types.Operator):  # type: ignore
        """Write tandem export: melodia handoff + surreal world manifest"""
        bl_idname = "melodia_studio.tandem_export"
        bl_label = "Export Tandem"

        def execute(self, context):
            # Find a tandem world root (latest _Composed)
            world_root = None
            for obj in bpy.data.objects:
                if obj.get("melodia_tandem_preset"):
                    world_root = obj
            if world_root is None:
                # fallback to any surreal world root
                for obj in bpy.data.objects:
                    if obj.get("surreal_composed_from"):
                        world_root = obj
                        break
            if world_root is None:
                self.report({'WARNING'}, "Compose a tandem city first")
                return {'CANCELLED'}
            try:
                deploy = str(_DEPLOY)
                if deploy not in sys.path:
                    sys.path.insert(0, deploy)
                from surreal_world import export as _export  # type: ignore
                # Write .world.json next to blend or Saved/Audit
                blend_dir = bpy.path.abspath("//")
                if not blend_dir or blend_dir == "//":
                    blend_dir = str(repo_root() / "Saved" / "Audit")
                out_dir = os.path.join(blend_dir, "tandem_export")
                os.makedirs(out_dir, exist_ok=True)
                world_json = os.path.join(out_dir, f"{world_root.name}.world.json")
                path = _export.write_world_manifest(world_root, filepath=world_json, monolith=None)
                # Also try melodia handoff if heightfield exists
                msg = f"World -> {path}" if path else "World manifest failed"
                # Append melodia current_terrain.obj handoff if available
                try:
                    from . import midi_bridge as _mb
                    handoff_png = None
                    # look for Saved/Audit/world_build* heightfields
                    audit = repo_root() / "Saved" / "Audit"
                    if audit.is_dir():
                        cand = sorted(audit.rglob("heightfield*.png"))
                        if cand:
                            handoff_png = str(cand[-1])
                    if handoff_png:
                        msg += f" | handoff PNG: {handoff_png}"
                except Exception:
                    pass
                self.report({'INFO'}, msg)
                return {'FINISHED'}
            except Exception as exc:
                self.report({'ERROR'}, f"Tandem export failed: {exc}")
                return {'CANCELLED'}

    class STUDIO_PT_tandem(bpy.types.Panel):  # type: ignore
        bl_label = "Tandem City"
        bl_idname = "STUDIO_PT_tandem"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Melodia Studio"
        bl_parent_id = "STUDIO_PT_panel"
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            if _chrome is not None:
                try:
                    _chrome.chrome_header(layout, "Tandem City", "Terrain  |  Snapped  |  City", pillar="zen", icon_key="starlight")
                    _chrome.chrome_kicker(layout, "Pink  &  Rose Gold  |  Zen Shrine", icon='SHADERFX')
                except Exception:
                    pass
            props = getattr(context.scene, "melodia_studio", None)
            if props is None:
                layout.label(text="Melodia Studio not ready", icon='ERROR')
                return
            ok, detail = _surreal_available()
            if _chrome is not None:
                try:
                    _chrome.chrome_status(layout, ok, "Surreal GN  |  Ready" if ok else "Surreal not found", "" if ok else detail)
                except Exception:
                    pass
            else:
                box = layout.box()
                if ok:
                    box.label(text="S u r r e a l   G N   R e a d y", icon='CHECKMARK')
                else:
                    box.alert = True
                    box.label(text="Surreal not found", icon='ERROR')
                    box.label(text=detail)

            # Tandem preset/style/plan -- use icon grid when chrome available
            use_grid = False
            if _chrome is not None:
                try:
                    # Large thumbnail grid for preset (walkable valley etc)
                    grid_ok = _chrome.chrome_preset_grid(layout, context, "tandem_preset")
                    if grid_ok:
                        use_grid = True
                except Exception:
                    use_grid = False
            try:
                if not use_grid:
                    box = layout.box()
                    box.prop(props, "tandem_preset", text="Tandem Preset")
                # Style/plan stay as compact props (icons already give lux)
                row = layout.row(align=True)
                row.prop(props, "tandem_style", text="Style")
                row.prop(props, "tandem_plan", text="Plan")
            except Exception:
                layout.label(text="Tandem props not registered - restart Blender", icon='ERROR')
                return

            col = layout.column(align=True)
            col.scale_y = 1.25
            col.operator("melodia_studio.tandem_compose", icon='MOD_BUILD')
            row = col.row(align=True)
            row.operator("melodia_studio.tandem_export", icon='EXPORT')

            terrain = bpy.data.objects.get("Terrain") or bpy.data.objects.get("RW_Terrain")
            if terrain is None:
                layout.label(text="Generate Terrain first", icon='INFO')
            else:
                layout.label(text=f"Terrain: {terrain.name}", icon='MESH_DATA')

    classes = [
        STUDIO_OT_tandem_compose,
        STUDIO_OT_tandem_export,
        STUDIO_PT_tandem,
    ]

else:
    def resolve_tandem_pair(*a, **kw):  # type: ignore
        return ("WESTERN_CASTLE", "castle")
    classes = []  # type: ignore

def register():
    if bpy is None:
        return
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as exc:
            print(f"[Tandem] register {cls}: {exc}")

def unregister():
    if bpy is None:
        return
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
