"""Melodia Studio - Audio Terrain (Blender 5.2 native GN) panel.

Surfaces the three ``deploy/surreal_arch/melodia_gn/audio_terrain.py`` builders
(MEL_audio_spectrum_terrain / MEL_audio_spectrum_towers / MEL_audio_radial_field)
inside the Melodia Studio N-panel so the audio-reactive terrain lane is
discoverable without digging through ``deploy/``.

Import origin is fail-closed: builders are loaded from the checkout's
``deploy/surreal_arch/melodia_gn`` via ``Tools/melodia_studio_pathbind.py``
(checkout bind + ``__file__`` proof), never from a stray AppData copy.

Offline-safe: importable without bpy (panels/operators only defined when bpy
is present), matching the rest of this addon.
"""

import os
import sys

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_bridge


# ------------------------------------------------------------- builder catalog
# Mirrors deploy/surreal_arch/melodia_gn/audio_terrain.py builder ids, labels
# and interface defaults. Sampling is driven by the scene timeline
# (use_scene_time=True in the builders), so there is no per-build "Time"
# control - scrub/play the timeline to animate the displacement.

BUILDERS = {
    "MEL_audio_spectrum_terrain": {
        "label": "Spectrum Terrain",
        "description": "Walkable terrain displaced by sampled frequency energy (X maps to band)",
        "params": [
            ("Size X M", 80.0, 2.0, 2000.0, "FLOAT"),
            ("Size Y M", 48.0, 2.0, 2000.0, "FLOAT"),
            ("Resolution X", 192, 8, 1024, "INT"),
            ("Resolution Y", 96, 8, 1024, "INT"),
            ("Height M", 18.0, 0.0, 500.0, "FLOAT"),
        ],
    },
    "MEL_audio_spectrum_towers": {
        "label": "Spectrum Towers",
        "description": "Frequency-bin tower field for cities, walls and reefs",
        "params": [
            ("Size X M", 120.0, 2.0, 4000.0, "FLOAT"),
            ("Frequency Bins", 128, 8, 2048, "INT"),
            ("Tower Width M", 0.7, 0.02, 40.0, "FLOAT"),
            ("Tower Depth M", 3.0, 0.02, 200.0, "FLOAT"),
            ("Height M", 32.0, 0.0, 1000.0, "FLOAT"),
        ],
    },
    "MEL_audio_radial_field": {
        "label": "Radial Field",
        "description": "Concentric audio-reactive membrane (radius maps low->high)",
        "params": [
            ("Size X M", 100.0, 2.0, 4000.0, "FLOAT"),
            ("Radial Segments", 256, 16, 2048, "INT"),
            ("Height M", 24.0, 0.0, 1000.0, "FLOAT"),
            ("Radius M", 50.0, 1.0, 2000.0, "FLOAT"),
        ],
    },
}

COMMON_DEFAULTS = {
    # (default, min, max)
    "Low Hz": (30.0, 0.0, 20000.0),
    "High Hz": (12000.0, 1.0, 24000.0),
    "Band Width": (0.08, 0.001, 1.0),
    "Audio Gain": (8.0, 0.0, 100.0),
}

AUDIO_BUILDER_IDS = tuple(BUILDERS.keys())


def _checkout_root():
    try:
        return midi_bridge.repo_root()
    except Exception:
        return None


def bind_checkout_builders():
    """Fail-closed checkout import of melodia_gn; returns BoundMelodiaGn.

    Raises melodia_studio_pathbind.SourceBindError (or ImportError) when the
    checkout bind cannot be proven - callers surface that text, never a
    silently shadowed AppData copy.
    """
    root = _checkout_root()
    if not root or not os.path.isdir(root):
        raise RuntimeError(f"cannot resolve project checkout root (got {root!r})")
    tools_dir = os.path.join(root, "Tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import melodia_studio_pathbind as pathbind  # type: ignore

    bind = pathbind.bind_checkout_deploy(pathbind.Path(root))
    bound = pathbind.import_checkout_melodia_gn(bind)
    missing = [bid for bid in AUDIO_BUILDER_IDS if bid not in bound.builder_ids]
    if missing:
        raise RuntimeError(
            f"checkout melodia_gn is missing audio builders: {missing} "
            f"(bound from {bound.gn_init_file})"
        )
    return bound


def _set_tree_input(tree, socket_name, value):
    """Set a GN tree interface INPUT default by socket name. Returns True/False.

    Per-modifier input RNA is not exposed for these trees in Blender 5.2
    (verified headless: no Input_*/Socket_* props on NODES modifiers even
    after a depsgraph update), so tree interface defaults are the mechanism -
    the same one ``mel_gn.apply_preset`` uses. Values are shared by every
    object using the tree.
    """
    try:
        for item in list(tree.interface.items_tree):
            if getattr(item, "name", None) == socket_name and getattr(item, "in_out", "") == "INPUT":
                if hasattr(item, "default_value"):
                    item.default_value = value
                    return True
                return False
    except Exception:
        pass
    return False


def _load_sound(filepath):
    """Load (or reuse) a Sound datablock for filepath. Returns Sound or None."""
    if not filepath or not os.path.isfile(filepath):
        return None
    for snd in bpy.data.sounds:
        try:
            if os.path.normcase(os.path.abspath(bpy.path.abspath(snd.filepath))) == os.path.normcase(
                os.path.abspath(filepath)
            ):
                return snd
        except Exception:
            continue
    try:
        return bpy.data.sounds.load(filepath)
    except Exception:
        return None


def _ensure_target_object(builder_id):
    """Active mesh object wins; otherwise create MEL_AudioTerrain_<short> host."""
    obj = bpy.context.active_object
    if obj is not None and getattr(obj, "type", "") == "MESH":
        return obj, False
    short = builder_id.replace("MEL_audio_", "").replace("MEL_", "")
    name = f"MEL_AudioTerrain_{short}"
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    try:
        bpy.context.scene.collection.objects.link(obj)
    except Exception:
        bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj, True


def _get_or_build_tree(bound, builder_id):
    tree = bpy.data.node_groups.get(builder_id)
    if tree is not None and getattr(tree, "type", "") == "GEOMETRY":
        return tree, False
    builder = bound.builder_callables[builder_id]
    tree = builder(builder_id)
    if tree is None:
        raise RuntimeError(f"builder {builder_id} returned no node tree")
    return tree, True


if bpy is not None:

    def _audio_builder_items(self, context):
        return [
            (bid, spec["label"], spec["description"])
            for bid, spec in BUILDERS.items()
        ]

    def _on_builder_changed(self, context):
        # Reset the generic geometry slots to the newly selected builder's
        # defaults so stale values from another builder can't leak across.
        try:
            spec = BUILDERS.get(self.builder, {})
            for i, (_pname, dflt, _mn, _mx, _kind) in enumerate(spec.get("params", [])):
                setattr(self, f"p{i}", float(dflt))
        except Exception:
            pass

    class AudioTerrainProps(bpy.types.PropertyGroup):
        builder: bpy.props.EnumProperty(
            name="Builder",
            description="Audio-reactive GN builder to run",
            items=_audio_builder_items,
            update=_on_builder_changed,
        )
        sound_path: bpy.props.StringProperty(
            name="Sound",
            description="WAV/OGG/MP3 sampled by the Sample Sound Frequencies node (empty = build now, assign later in the modifier)",
            subtype="FILE_PATH",
            default="",
        )
        low_hz: bpy.props.FloatProperty(
            name="Low Hz", default=COMMON_DEFAULTS["Low Hz"][0],
            min=COMMON_DEFAULTS["Low Hz"][1], max=COMMON_DEFAULTS["Low Hz"][2],
        )
        high_hz: bpy.props.FloatProperty(
            name="High Hz", default=COMMON_DEFAULTS["High Hz"][0],
            min=COMMON_DEFAULTS["High Hz"][1], max=COMMON_DEFAULTS["High Hz"][2],
        )
        band_width: bpy.props.FloatProperty(
            name="Band Width", default=COMMON_DEFAULTS["Band Width"][0],
            min=COMMON_DEFAULTS["Band Width"][1], max=COMMON_DEFAULTS["Band Width"][2],
        )
        audio_gain: bpy.props.FloatProperty(
            name="Audio Gain", default=COMMON_DEFAULTS["Audio Gain"][0],
            min=COMMON_DEFAULTS["Audio Gain"][1], max=COMMON_DEFAULTS["Audio Gain"][2],
        )
        # Per-builder geometry params (only the active builder's row is drawn,
        # but all five slots exist so switching builders keeps values).
        p0: bpy.props.FloatProperty(name="P0", default=80.0)
        p1: bpy.props.FloatProperty(name="P1", default=48.0)
        p2: bpy.props.FloatProperty(name="P2", default=192.0)
        p3: bpy.props.FloatProperty(name="P3", default=96.0)
        p4: bpy.props.FloatProperty(name="P4", default=18.0)

    class MELODIA_OT_audio_terrain_build(bpy.types.Operator):  # type: ignore
        """Build the selected audio-reactive GN tree and attach it to a host object."""

        bl_idname = "melodia_studio.audio_terrain_build"
        bl_label = "Build Audio Terrain"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            props = getattr(context.scene, "melodia_audio_terrain", None)
            if props is None:
                self.report({"ERROR"}, "Audio Terrain props not registered")
                return {"CANCELLED"}
            builder_id = props.builder
            spec = BUILDERS.get(builder_id)
            if spec is None:
                self.report({"ERROR"}, f"Unknown builder {builder_id!r}")
                return {"CANCELLED"}

            try:
                bound = bind_checkout_builders()
            except Exception as exc:
                self.report({"ERROR"}, f"Checkout bind failed (refusing shadow import): {exc}")
                return {"CANCELLED"}

            try:
                tree, tree_built = _get_or_build_tree(bound, builder_id)
            except Exception as exc:
                self.report({"ERROR"}, f"Builder failed: {exc}")
                return {"CANCELLED"}

            try:
                obj, obj_created = _ensure_target_object(builder_id)
            except Exception as exc:
                self.report({"ERROR"}, f"Target object failed: {exc}")
                return {"CANCELLED"}

            mod = None
            for m in obj.modifiers:
                if getattr(m, "type", "") == "NODES" and getattr(m, "node_group", None) == tree:
                    mod = m
                    break
            if mod is None:
                try:
                    mod = obj.modifiers.new(name=tree.name, type="NODES")
                    mod.node_group = tree
                except Exception as exc:
                    self.report({"ERROR"}, f"GN modifier failed: {exc}")
                    return {"CANCELLED"}

            applied, skipped = 0, []
            values = {
                "Low Hz": (props.low_hz, "FLOAT"),
                "High Hz": (props.high_hz, "FLOAT"),
                "Band Width": (props.band_width, "FLOAT"),
                "Audio Gain": (props.audio_gain, "FLOAT"),
            }
            for i, (pname, _dflt, _mn, _mx, kind) in enumerate(spec["params"]):
                raw = getattr(props, f"p{i}")
                values[pname] = (int(round(raw)) if kind == "INT" else float(raw), kind)
            for pname, (pval, _kind) in values.items():
                if _set_tree_input(tree, pname, pval):
                    applied += 1
                else:
                    skipped.append(pname)

            sound_note = ""
            if props.sound_path:
                snd = _load_sound(props.sound_path)
                if snd is not None and _set_tree_input(tree, "Sound", snd):
                    applied += 1
                    sound_note = f" | sound={snd.name}"
                elif snd is None:
                    skipped.append("Sound")
                    sound_note = " | WARNING: sound file could not be loaded"
                else:
                    skipped.append("Sound")
                    sound_note = " | WARNING: Sound socket not found on tree"
            else:
                sound_note = " | no sound file (assign Sound in modifier)"

            msg = (
                f"{spec['label']}: tree={'built' if tree_built else 'reused'} "
                f"obj={obj.name}{' (new)' if obj_created else ''} "
                f"mod={mod.name} tree-inputs={applied}{sound_note}"
            )
            if skipped:
                msg += f" | skipped={','.join(skipped)}"
            self.report({"INFO"}, msg)
            try:
                studio = getattr(context.scene, "melodia_studio", None)
                if studio is not None:
                    studio.last_report = msg
                    studio.last_midi = ""
            except Exception:
                pass
            return {"FINISHED"}

    class MELODIA_PT_audio_terrain(bpy.types.Panel):  # type: ignore
        bl_label = "Audio Terrain (5.2)"
        bl_idname = "MELODIA_PT_audio_terrain"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Melodia Studio"
        bl_parent_id = "STUDIO_PT_panel"
        bl_options = {"DEFAULT_CLOSED"}

        def draw(self, context):
            layout = self.layout
            props = getattr(context.scene, "melodia_audio_terrain", None)
            if props is None:
                layout.label(text="Audio Terrain not ready", icon="ERROR")
                return
            box = layout.box()
            box.label(text="WAV -> spectrum -> GN terrain", icon="FILE_SOUND")
            box.prop(props, "builder", text="")
            spec = BUILDERS.get(props.builder, {})
            if spec.get("description"):
                box.label(text=spec["description"], icon="INFO")
            box.prop(props, "sound_path", text="Sound")
            box.label(text="Animation follows the timeline (Scene Time)", icon="TIME")

            adv = layout.box()
            adv.label(text="Frequency Bands", icon="MOD_WAVE")
            adv.prop(props, "low_hz")
            adv.prop(props, "high_hz")
            adv.prop(props, "band_width")
            adv.prop(props, "audio_gain")

            geo = layout.box()
            geo.label(text="Geometry", icon="MESH_GRID")
            for i, (pname, dflt, mn, mx, kind) in enumerate(spec.get("params", [])):
                row = geo.row()
                row.prop(props, f"p{i}", text=pname)

            col = layout.column(align=True)
            col.scale_y = 1.4
            col.operator("melodia_studio.audio_terrain_build", icon="MOD_BUILD")

            layout.separator()
            layout.label(text="Bake: Tools/audio_terrain_pipeline.py", icon="EXPORT")
            layout.label(text="UE: /Game/Melodia/World/AudioTerrain", icon="IMPORT")

    _AUDIO_TERRAIN_CLASSES = (
        AudioTerrainProps,
        MELODIA_OT_audio_terrain_build,
        MELODIA_PT_audio_terrain,
    )

    def register():
        for cls in _AUDIO_TERRAIN_CLASSES:
            try:
                bpy.utils.register_class(cls)
            except ValueError:
                pass  # already registered (addon refresh)
        if not hasattr(bpy.types.Scene, "melodia_audio_terrain"):
            bpy.types.Scene.melodia_audio_terrain = bpy.props.PointerProperty(type=AudioTerrainProps)

    def unregister():
        try:
            del bpy.types.Scene.melodia_audio_terrain
        except AttributeError:
            pass
        for cls in reversed(_AUDIO_TERRAIN_CLASSES):
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass

else:
    _AUDIO_TERRAIN_CLASSES = ()

    def register():
        pass

    def unregister():
        pass
