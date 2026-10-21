"""Melodia Studio - STUDIO_OT_* operators.

Split out of studio_panel.py on 2026-10-04 (monolith split, no logic change).
All bl_idnames are unchanged (melodia_studio.*). Registration happens in the
studio_panel facade, in the original order.
"""

import os
import shutil
import sys
from pathlib import Path

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_bridge
from . import midi_picker
from . import terrain_build

# Optional QOL helpers - offline-safe
try:
    from . import addon_utils  # type: ignore
except Exception:
    addon_utils = None  # type: ignore

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


# ------------------------------------------------------------- operators

if bpy is not None:

    class STUDIO_OT_generate_from_midi(bpy.types.Operator):
        """Generate Resonant World terrain from the selected MIDI"""
        bl_idname = "melodia_studio.generate_from_midi"
        bl_label = "Generate Terrain"
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):
            props = context.scene.melodia_studio
            midi = midi_picker._selected_midi(props)
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

            obj = terrain_build.build_terrain_mesh(report["obj"], "Terrain")
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
                    instanced = terrain_build._instance_dressing(midi, props.dressing_style,
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
            midi = midi_picker._selected_midi(props)
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
            midi = midi_picker._selected_midi(props)
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
            midi_picker._MIDI_CACHE_TIME = 0
            midi_picker._discover_cached()
            self.report({'INFO'}, f"Found {len(midi_picker._MIDI_CACHE)} MIDI file(s)")
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

    OPERATOR_CLASSES = [
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
    ]

else:
    STUDIO_OT_generate_from_midi = STUDIO_OT_frame_terrain = STUDIO_OT_write_presets = STUDIO_OT_save_scene = object  # type: ignore
    STUDIO_OT_cleanup_scene = STUDIO_OT_setup_script_directory = STUDIO_OT_open_folder = STUDIO_OT_refresh_midi = STUDIO_OT_validate_health = object  # type: ignore
    OPERATOR_CLASSES = []  # type: ignore
