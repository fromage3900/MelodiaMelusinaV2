"""Wire overhaul package into surreal_architecture_gen monolith."""

from __future__ import annotations

import bpy
import json
import os
import sys
import time

_M = None
_EXTRA_CLASSES = []
_PATCHED = False
_REGISTERED_MONOLITH = None


def _register_class_once(cls):
    """Idempotent register - Blender 5.2 raises ValueError on a second spawn_polyhedron."""
    name = getattr(cls, "__name__", "")
    if name and getattr(bpy.types, name, None) is not None:
        return False
    try:
        bpy.utils.register_class(cls)
        return True
    except (RuntimeError, ValueError):
        return False


def _ensure_path():
    pkg = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(pkg)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    greybox_parent = os.path.dirname(parent)
    if greybox_parent not in sys.path:
        sys.path.insert(0, greybox_parent)


def _wire_trim_box_wrapper(monolith):
    """Re-apply after surreal_greybox.attach_all resets _gb_box each register."""
    from .trim_color_bake import resolve_trim_zone, tag_face_trim_attrs, tag_trim_geometry

    inner = getattr(monolith, "_gb_box_inner", None)
    current = monolith._gb_box
    if inner is None or current is inner:
        inner = current
        monolith._gb_box_inner = inner

    def _gb_box_trim_zones(tree, size, loc_xyz, x, y, label="level"):
        geom = inner(tree, size, loc_xyz, x, y, label)
        if geom is None:
            return None
        props = getattr(getattr(bpy.context, "active_object", None), "surreal_arch_props", None)
        zone = resolve_trim_zone(monolith, label, props)
        if zone is not None:
            return tag_trim_geometry(monolith, tree, geom, x, y, trim_value=zone)
        return tag_face_trim_attrs(monolith, tree, geom, x, y, zone_value=0.0, trim_flag=0.0)

    monolith._gb_box = _gb_box_trim_zones


def _legacy_modifier_panel_enabled(context) -> bool:
    addons = getattr(getattr(context, "preferences", None), "addons", None)
    if addons is None:
        return False
    for key in ("surreal_architecture_gen", "melodia_studio"):
        addon = addons.get(key)
        prefs = getattr(addon, "preferences", None) if addon else None
        if prefs is not None and hasattr(prefs, "show_legacy_modifier_panel"):
            return bool(prefs.show_legacy_modifier_panel)
    return False


def _demote_properties_panel(monolith):
    """Hide the Modifier-tab drawer unless Preferences enable the legacy panel."""
    panel = getattr(monolith, "SURREAL_ARCH_PT_panel", None)
    if panel is None or getattr(panel, "_melodia_legacy_demoted", False):
        return
    panel.bl_label = "Melodia Studio - Modifier (legacy)"
    opts = set(getattr(panel, "bl_options", set()) or set())
    opts.add("DEFAULT_CLOSED")
    panel.bl_options = opts

    @classmethod
    def _poll(cls, context):
        if not _legacy_modifier_panel_enabled(context):
            return False
        obj = getattr(context, "active_object", None)
        return bool(obj and getattr(obj, "type", None) == "MESH")

    panel.poll = _poll
    panel._melodia_legacy_demoted = True


def _patch_genome_carousel_header(monolith):
    panel = getattr(monolith, "SURREAL_ARCH_PT_genome_carousel", None)
    if panel is None or getattr(panel, "_melodia_solo_object_patched", False):
        return

    original_draw = panel.draw

    def _draw_with_solo_object(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.scale_y = 1.25
        row.operator("surreal_arch.generate", text="Generate", icon="SHADERFX")
        if hasattr(bpy.types, "SURREAL_ARCH_OT_set_stage_visibility_preset"):
            op = row.operator(
                "surreal_arch.set_stage_visibility_preset",
                text="Starlight",
                icon="LIGHT_SUN",
            )
            op.preset = "starlight_on"
        row.operator("surreal_arch.solo_object", text="Solo Object", icon="SOLO_ON")
        layout.separator()
        original_draw(self, context)

    panel.draw = _draw_with_solo_object
    panel._melodia_solo_object_patched = True


def patch_monolith(monolith):
    global _M, _PATCHED
    if _M is not monolith:
        _PATCHED = False
    _M = monolith
    first_patch = not _PATCHED
    _PATCHED = True

    _ensure_path()
    try:
        import surreal_greybox
        surreal_greybox.attach_all(monolith)
    except Exception as _gb_err:
        print(f"[Surreal Architecture] surreal_greybox attach skipped: {_gb_err}")

    from . import gothic_kit, greybox_offset, romanesque_kit, brutalist_kit, venetian_kit, scifi_kit, zen_kit
    from .kit_registration import register_kit

    if first_patch:
        monolith.build_gothic_portal = lambda t, p, bx=-1400: gothic_kit.build_gothic_portal(t, monolith, p, bx)
        monolith.build_gothic_bay = lambda t, p, bx=-1400: gothic_kit.build_gothic_bay(t, monolith, p, bx)
        monolith.build_gothic_buttress_kit = lambda t, p, bx=-1400: gothic_kit.build_gothic_buttress(t, monolith, p, bx)
        monolith.build_gothic_tracery_panel = lambda t, p, bx=-1400: gothic_kit.build_gothic_tracery_panel(t, monolith, p, bx)

        def _build_greybox_room_with_reveals(tree, props, base_x=-1400):
            W = getattr(props, "gb_width", 8.0)
            D = getattr(props, "gb_depth", 6.0)
            H = getattr(props, "gb_height", 3.5)
            t = getattr(props, "gb_wall_thick", 0.3)
            parts = monolith._gb_rect_room_shell(tree, props, W, D, H, t, base_x, 0)
            from .greybox_trim import gb_rect_room_window_reveals
            parts.extend(gb_rect_room_window_reveals(tree, monolith, props, base_x, W, D, H, t))
            return monolith._gb_join(tree, parts, base_x + 1600, 0)

        monolith.build_greybox_room = _build_greybox_room_with_reveals

        orig_picker_draw = monolith.SURREAL_ARCH_PT_arch_picker.draw

        def _picker_draw(self, context):
            from .ui import draw_arch_picker_filtered
            draw_arch_picker_filtered(self.layout, context, monolith, compact=False)

        monolith.SURREAL_ARCH_PT_arch_picker.draw = _picker_draw
        monolith.SURREAL_ARCH_PT_arch_picker.bl_order = 1
        monolith.SURREAL_ARCH_PT_arch_picker.bl_label = "Architecture Picker"

        def _level_draw(self, context):
            from .ui import draw_level_design
            draw_level_design(self.layout, context, monolith)

        monolith.SURREAL_ARCH_PT_level_design.draw = _level_draw

        _orig_generate = monolith.SURREAL_ARCH_OT_generate.execute

        def _generate_with_trim_reset(self, context):
            from .trim_color_bake import reset_trim_zones
            props = getattr(getattr(context, "active_object", None), "surreal_arch_props", None)
            arch = getattr(props, "arch_type", "") if props else ""
            music_arch = {"NOTE_HEAD", "STAFF", "TREBLE_CLEF", "SHEET_MUSIC_RAIL"}
            now = time.monotonic()
            last = getattr(monolith, "_melodia_music_generate_last", 0.0)
            if arch in music_arch and now - last < 0.25:
                return {"CANCELLED"}
            if arch in music_arch:
                monolith._melodia_music_generate_last = now
            reset_trim_zones(monolith)
            return _orig_generate(self, context)

        monolith.SURREAL_ARCH_OT_generate.execute = _generate_with_trim_reset

    _wire_trim_box_wrapper(monolith)
    _patch_genome_carousel_header(monolith)
    _demote_properties_panel(monolith)

    monolith.build_greybox_corridor_offset = lambda t, p, bx=-1400: greybox_offset.build_greybox_corridor_offset(
        t, monolith, p, bx
    )
    monolith.build_romanesque_arcade_bay = lambda t, p, bx=-1400: romanesque_kit.build_romanesque_arcade_bay(
        t, monolith, p, bx
    )
    monolith.build_brutalist_panel_wall = lambda t, p, bx=-1400: brutalist_kit.build_brutalist_panel_wall(
        t, monolith, p, bx
    )
    monolith.build_venetian_loggia_bay = lambda t, p, bx=-1400: venetian_kit.build_venetian_loggia_bay(
        t, monolith, p, bx
    )

    register_kit(
        monolith,
        "GB_SCIFI_PRESSURE_DOOR",
        scifi_kit.build_scifi_pressure_door,
        snap_fn=scifi_kit.compute_scifi_pressure_door_snaps,
        builder_attr="build_scifi_pressure_door",
        material_key="METAL",
    )
    register_kit(
        monolith,
        "GB_ROMANESQUE_APSE",
        romanesque_kit.build_romanesque_apse,
        snap_fn=lambda M, props, t: romanesque_kit.compute_romanesque_snap_points(M, props, t),
        builder_attr="build_romanesque_apse",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_ROJI_STEP",
        zen_kit.build_zen_roji_step,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_roji_step",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_TORII_GATE",
        zen_kit.build_zen_torii_gate,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_torii_gate",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_SAKURA_TORII",
        zen_kit.build_zen_sakura_torii,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_sakura_torii",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_TSUKUBAI",
        zen_kit.build_zen_tsukubai,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_tsukubai",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_ENGAWA",
        zen_kit.build_zen_engawa,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_engawa",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_BAMBOO_FENCE",
        zen_kit.build_zen_bamboo_fence,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_bamboo_fence",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_TOBIISHI",
        zen_kit.build_zen_tobiishi,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_tobiishi",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_KARESANSUI",
        zen_kit.build_zen_karesansui,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_karesansui",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_MACHIAI",
        zen_kit.build_zen_machiai,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_machiai",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_STONE_BRIDGE",
        zen_kit.build_zen_stone_bridge,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_stone_bridge",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_CHERRY_ALLEE",
        zen_kit.build_zen_cherry_allee,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_cherry_allee",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_WATER_EDGE",
        zen_kit.build_zen_water_edge,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_water_edge",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_SANDO",
        zen_kit.build_zen_sando,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_sando",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_ZEN_KAIRO",
        zen_kit.build_zen_kairo,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_kairo",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_HAIDEN",
        zen_kit.build_zen_haiden,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_haiden",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_GOJU_PAGODA",
        zen_kit.build_zen_goju_pagoda,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_goju_pagoda",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_TAHOTO",
        zen_kit.build_zen_tahoto,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_tahoto",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_HONDEN",
        zen_kit.build_zen_honden,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_honden",
        material_key="WOOD",
    )
    register_kit(
        monolith,
        "GB_ZEN_LANTERN",
        zen_kit.build_zen_lantern,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_lantern_gb",
        material_key="STONE",
    )
    # v2.74 stub-fill: corridor bend/T exist in surreal_greybox but were never
    # registered, so the cloister graphs could not resolve them. ZEN_BRIDGE is
    # the garden-graph alias of the stone bridge; ZEN_TEAHOUSE is the new
    # zen_kit teahouse above. Adapters match register_kit (t, M, p, bx) shape;
    # shells builders take (tree, props, base_x) and are monolith-bound by
    # surreal_greybox.attach_all earlier in patch_monolith.
    def _build_corridor_bend(t, M, p, bx=-1400):
        return M.build_greybox_corridor_bend(t, p, bx)

    def _build_corridor_t(t, M, p, bx=-1400):
        return M.build_greybox_corridor_t(t, p, bx)

    register_kit(
        monolith,
        "GB_CORRIDOR_BEND",
        _build_corridor_bend,
        builder_attr="build_greybox_corridor_bend_kit",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "GB_CORRIDOR_T",
        _build_corridor_t,
        builder_attr="build_greybox_corridor_t_kit",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "ZEN_BRIDGE",
        zen_kit.build_zen_stone_bridge,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_stone_bridge",
        material_key="STONE",
    )
    register_kit(
        monolith,
        "ZEN_TEAHOUSE",
        zen_kit.build_zen_teahouse,
        snap_fn=zen_kit.compute_zen_kit_snaps,
        builder_attr="build_zen_teahouse",
        material_key="WOOD",
    )

    if not hasattr(monolith, "_gb_compute_snap_points_orig"):
        monolith._gb_compute_snap_points_orig = monolith._gb_compute_snap_points

    def _compute_snaps_extended(props):
        t = props.arch_type
        kit_snaps = getattr(monolith, "_KIT_SNAP_FN", {})
        if t in kit_snaps:
            fn = kit_snaps[t]
            try:
                return fn(monolith, props, t)
            except TypeError:
                return fn(monolith, props)
        if t.startswith("GB_GOTHIC_"):
            return gothic_kit.compute_gothic_snap_points(monolith, props, t)
        if t == "GB_CORRIDOR_OFFSET":
            return greybox_offset.compute_corridor_offset_snap_points(monolith, props)
        if t == "GB_ROMANESQUE_ARCADE":
            return romanesque_kit.compute_romanesque_snap_points(monolith, props, t)
        if t == "GB_ROMANESQUE_APSE":
            return romanesque_kit.compute_romanesque_snap_points(monolith, props, t)
        if t == "GB_BRUTALIST_PANEL_WALL":
            return brutalist_kit.compute_brutalist_snap_points(monolith, props)
        if t == "GB_VENETIAN_LOGGIA":
            return venetian_kit.compute_venetian_loggia_snap_points(monolith, props)
        if t.startswith("GB_ZEN_") or (t.startswith("ZEN_") and t not in ("ZEN_MOSS", "ZEN_RIPPLE", "ZEN_SAND", "ZEN_BAMBOO", "ZEN_PETALS", "ZEN_ORBIT", "ZEN_SMOKE", "ZEN_POND", "ZEN_TERRACE", "ZEN_GINKGO", "ZEN_RUNES", "ZEN_BONSAI")):
            return zen_kit.compute_zen_snaps(monolith, props, t)
        return monolith._gb_compute_snap_points_orig(props)

    monolith._gb_compute_snap_points = _compute_snaps_extended

    if not hasattr(monolith, "_gb_write_snap_points_orig"):
        monolith._gb_write_snap_points_orig = monolith._gb_write_snap_points

    def _write_snaps_extended(obj, props):
        monolith._gb_write_snap_points_orig(obj, props)
        from .snap_export import attach_trim_metadata
        attach_trim_metadata(obj, props, monolith)

    monolith._gb_write_snap_points = _write_snaps_extended

    from .catalog_dispatch import register_dispatch_entry, sync_catalog_dispatch

    register_dispatch_entry(
        monolith, "GB_CORRIDOR_OFFSET", "build_greybox_corridor_offset",
        snap_fn=greybox_offset.compute_corridor_offset_snap_points,
        material_key="STONE",
    )
    register_dispatch_entry(
        monolith, "GB_ROMANESQUE_ARCADE", "build_romanesque_arcade_bay",
        snap_fn=lambda M, props, t: romanesque_kit.compute_romanesque_snap_points(M, props, t),
        material_key="STONE",
    )
    register_dispatch_entry(
        monolith, "GB_BRUTALIST_PANEL_WALL", "build_brutalist_panel_wall",
        snap_fn=brutalist_kit.compute_brutalist_snap_points,
        material_key="STONE",
    )
    register_dispatch_entry(
        monolith, "GB_VENETIAN_LOGGIA", "build_venetian_loggia_bay",
        snap_fn=venetian_kit.compute_venetian_loggia_snap_points,
        material_key="MARBLE",
    )
    register_dispatch_entry(monolith, "GB_GOTHIC_PORTAL", "build_gothic_portal")
    register_dispatch_entry(monolith, "GB_GOTHIC_BAY", "build_gothic_bay")
    register_dispatch_entry(monolith, "GB_GOTHIC_BUTTRESS", "build_gothic_buttress_kit")
    register_dispatch_entry(monolith, "GB_GOTHIC_TRACERY_PANEL", "build_gothic_tracery_panel")

    sync_catalog_dispatch(monolith)

    try:
        from surreal_world.patch import patch_world

        patch_world(monolith)
    except Exception as _world_err:
        print(f"[Surreal Architecture] surreal_world patch skipped: {_world_err}")

    _wire_pipeline_and_bridges(monolith)
    register_os_layer(monolith)


def register_os_layer(monolith):
    """Wire Surreal Architecture OS - genomes, grammar graphs, rules."""
    try:
        import sys
        import os
        deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if deploy not in sys.path:
            sys.path.insert(0, deploy)
        from surreal_os.grammar_loader import merge_grammar_into_registry
        from surreal_os import genome as os_genome
        from surreal_arch.greybox_graph import GRAPH_REGISTRY

        n = merge_grammar_into_registry(GRAPH_REGISTRY)
        monolith._STYLE_GENOMES = os_genome.list_genomes()
        monolith._STYLE_GENOME_META = {}
        groups: dict[str, list[str]] = {}
        for gid in monolith._STYLE_GENOMES:
            try:
                g = os_genome.load_genome(gid)
                monolith._STYLE_GENOME_META[gid] = {
                    "graph": g.get("default_graph", ""),
                    "transform": g.get("surreal_transform") or "none",
                    "family": os_genome.genome_family(g),
                }
                fam = os_genome.genome_family(g)
            except Exception:
                fam = "Other"
            groups.setdefault(fam, []).append(gid)
        monolith._STYLE_GENOME_GROUPS = {k: sorted(v) for k, v in sorted(groups.items())}
        monolith._active_style_genome = None
        print(f"[SurrealOS] merged {n} grammar graph(s); genomes={len(monolith._STYLE_GENOMES)}")
    except Exception as err:
        print(f"[SurrealOS] register skipped: {err}")


def _wire_pipeline_and_bridges(monolith):
    """Beavel / Synthia / Higgsas pipeline hooks + monolith delegates."""
    from .bevel_bridge import apply_bevel
    from .pipeline import run_post_generate
    from .synthia_bridge import SYNTHIA_ARCH_MAP, materialize_arch_type

    monolith._surreal_patched = True

    if not hasattr(monolith, "_apply_geometry_nodes_orig"):
        monolith._apply_geometry_nodes_orig = monolith.apply_geometry_nodes_to_object

    def _apply_geometry_nodes_patched(obj, props):
        from .melodia_gn_route import try_apply_melodia_gn

        if try_apply_melodia_gn(obj, props, monolith):
            run_post_generate(obj, props, monolith, skip_bevel=True)
            return
        if props.arch_type in SYNTHIA_ARCH_MAP:
            materialize_arch_type(obj, props)
            if getattr(props, "auto_apply_material", True):
                fn = getattr(monolith, "apply_material_to_object", None)
                if fn:
                    try:
                        fn(obj, props)
                    except Exception:
                        pass
            write_snaps = getattr(monolith, "_gb_write_snap_points", None)
            if write_snaps:
                try:
                    write_snaps(obj, props)
                except Exception:
                    pass
            run_post_generate(obj, props, monolith)
            return
        monolith._apply_geometry_nodes_orig(obj, props)
        run_post_generate(obj, props, monolith, skip_bevel=True)

    monolith.apply_geometry_nodes_to_object = _apply_geometry_nodes_patched

    if not hasattr(monolith, "_apply_edge_bevel_orig"):
        monolith._apply_edge_bevel_orig = monolith.apply_edge_bevel_modifier

    def _apply_edge_bevel_patched(obj, props):
        apply_bevel(obj, props, backend="MODIFIER", monolith=monolith)

    monolith.apply_edge_bevel_modifier = _apply_edge_bevel_patched

    if hasattr(monolith, "_apply_bevel_addon"):
        if not hasattr(monolith, "_apply_bevel_addon_orig"):
            monolith._apply_bevel_addon_orig = monolith._apply_bevel_addon

        def _apply_bevel_addon_patched(obj, props):
            backend = getattr(props, "bevel_backend", "MODIFIER")
            if backend == "BEAVEL":
                apply_bevel(obj, props, backend="BEAVEL", monolith=monolith)
            else:
                monolith._apply_bevel_addon_orig(obj, props)

        monolith._apply_bevel_addon = _apply_bevel_addon_patched

    if hasattr(monolith, "SURREAL_ARCH_OT_spawn_synthia"):
        _orig_spawn_synthia = monolith.SURREAL_ARCH_OT_spawn_synthia.execute

        def _spawn_synthia_patched(self, context):
            from .capabilities import is_available
            from .synthia_bridge import apply_post_spawn, spawn

            if not is_available("synthia"):
                return _orig_spawn_synthia(self, context)

            props = None
            active = context.active_object
            if active and hasattr(active, "surreal_arch_props"):
                props = active.surreal_arch_props
            if not props:
                for o in bpy.data.objects:
                    if o.type == "MESH" and hasattr(o, "surreal_arch_props"):
                        props = o.surreal_arch_props
                        break
            if not props:
                self.report({"ERROR"}, "No mesh object with surreal_arch_props found")
                return {"CANCELLED"}

            before = {o.name for o in bpy.data.objects}
            try:
                if props.synthia_use_custom:
                    spawned = spawn("", "EQUATION", formula=props.synthia_custom_formula)
                else:
                    eq_ids = {p[0] for p in monolith.SYNTHIA_EQUATION_PRESETS}
                    preset_type = "EQUATION" if props.synthia_preset in eq_ids else "GEOMETRY"
                    spawned = spawn(props.synthia_preset, preset_type)
            except Exception as e:
                self.report({"ERROR"}, f"Synthia spawn failed: {e}")
                return {"CANCELLED"}

            if spawned is None:
                new_objs = [o for o in bpy.data.objects if o.name not in before]
                spawned = new_objs[-1] if new_objs else None
            if not spawned:
                self.report({"WARNING"}, "Synthia spawned but no new object detected")
                return {"CANCELLED"}

            apply_post_spawn(spawned, props, monolith)
            context.view_layer.objects.active = spawned
            bpy.ops.object.select_all(action="DESELECT")
            spawned.select_set(True)
            self.report({"INFO"}, f"Synthia: {spawned.name} spawned + pipeline applied")
            return {"FINISHED"}

        monolith.SURREAL_ARCH_OT_spawn_synthia.execute = _spawn_synthia_patched

    from .synthia_bridge import SYNTHIA_ARCH_MAP as _map
    from .catalog_dispatch import register_dispatch_entry

    def build_synthia_arch_stub(tree, props, base_x=-1400):
        """GN placeholder - SYNTHIA types materialize in apply_geometry_nodes patch."""
        safe = getattr(monolith, "_safe_node", None)
        if safe:
            node = safe(tree, "GeometryNodeMeshCube", (base_x, 0))
            if node:
                return node.outputs.get("Mesh") or node.outputs[0]
        return None

    monolith.build_synthia_arch_stub = build_synthia_arch_stub

    for arch_id in _map:
        register_dispatch_entry(monolith, arch_id, "build_synthia_arch_stub", material_key="IRIDESCENT")

    monolith._higgsas_available = lambda: __import__(
        "surreal_arch.higgsas_bridge", fromlist=["is_available"]
    ).is_available()
    monolith._higg_load = lambda name: __import__(
        "surreal_arch.higgsas_bridge", fromlist=["load_node"]
    ).load_node(name)

    if hasattr(monolith, "SURREAL_ARCH_PT_synthia"):
        _orig_synthia_draw = monolith.SURREAL_ARCH_PT_synthia.draw

        def _synthia_draw_patched(self, context):
            from .capabilities import status_line
            layout = self.layout
            box = layout.box()
            box.label(text="Optional Dependencies", icon="INFO")
            for dep in ("synthia", "beavel", "higgsas"):
                box.label(text=status_line(dep))
            layout.separator()
            _orig_synthia_draw(self, context)

        monolith.SURREAL_ARCH_PT_synthia.draw = _synthia_draw_patched


def register_overhaul(monolith):
    global _REGISTERED_MONOLITH
    _ensure_path()
    patch_monolith(monolith)
    from .bootstrap import register_preferences
    from .branding import unify_npanel_categories
    from .ui import make_view3d_panels
    from .greybox_graph import register_graph_operators
    from .greybox_overlay import enable_overlay
    from .research_presets import register_research_preset_operators
    from .asset_browser import register_asset_ops
    from .catalog_enum import register_catalog_enum_ops
    from .workflow_polls import patch_workflow_polls
    from .os_ops import register_os_operators
    from . import uv_ops
    from . import melodia_gn
    from .quality_props import register_quality_props
    from .stage_visibility import register_stage_visibility_classes
    from .accessory_visibility import register_accessory_classes, unregister_accessory_props
    from .stats_overlay import register_stats_overlay, unregister_stats_overlay
    from .solo_object import SOLO_OBJECT_CLASSES
    from .bagapie_bridge import BAGAPIE_BRIDGE_CLASSES
    from .nikki_materials import NIKKI_MATERIAL_CLASSES
    from .genome_carousel import CLASSES as GENOME_CAROUSEL_CLASSES
    from .live_bridge import CLASSES as LIVE_BRIDGE_CLASSES, register_props as register_live_bridge_props
    from .material_bridge import CLASSES as MATERIAL_BRIDGE_CLASSES, register_props as register_material_bridge_props
    from .melusina_portrait import CLASSES as MELUSINA_PORTRAIT_CLASSES, register_props as register_portrait_props
    from .pie_menu import (
        register_pie_menu,
        register_pie_menu_with_keymaps,
        unregister_pie_menu_with_keymaps,
    )
    from .stage_publish import CLASSES as STAGE_PUBLISH_CLASSES, register_props as register_stage_publish_props
    from .music_ui import register_music_ui, unregister_music_ui

    patch_workflow_polls(monolith)
    register_preferences()
    register_quality_props(monolith)
    _REGISTERED_MONOLITH = monolith

    global _EXTRA_CLASSES
    _EXTRA_CLASSES = list(GENOME_CAROUSEL_CLASSES)
    _EXTRA_CLASSES.extend(list(make_view3d_panels(monolith)))
    _EXTRA_CLASSES.extend(list(register_graph_operators(monolith)))
    _EXTRA_CLASSES.extend(register_research_preset_operators(monolith))
    _EXTRA_CLASSES.extend(register_asset_ops(monolith))
    _EXTRA_CLASSES.extend(register_catalog_enum_ops(monolith))
    _EXTRA_CLASSES.extend(register_os_operators(monolith))
    _EXTRA_CLASSES.extend(uv_ops.UV_OPERATOR_CLASSES)
    _EXTRA_CLASSES.extend(register_stage_visibility_classes())
    _EXTRA_CLASSES.extend(register_accessory_classes())
    _EXTRA_CLASSES.extend(register_stats_overlay())
    _EXTRA_CLASSES.extend(melodia_gn.CLASSES)
    _EXTRA_CLASSES.extend(SOLO_OBJECT_CLASSES)
    _EXTRA_CLASSES.extend(BAGAPIE_BRIDGE_CLASSES)
    _EXTRA_CLASSES.extend(NIKKI_MATERIAL_CLASSES)
    _EXTRA_CLASSES.extend(LIVE_BRIDGE_CLASSES)
    _EXTRA_CLASSES.extend(MATERIAL_BRIDGE_CLASSES)
    _EXTRA_CLASSES.extend(MELUSINA_PORTRAIT_CLASSES)
    _EXTRA_CLASSES.extend(list(register_pie_menu()))
    _EXTRA_CLASSES.extend(STAGE_PUBLISH_CLASSES)

    try:
        from surreal_world.patch import register_world_operators

        _EXTRA_CLASSES.extend(register_world_operators(monolith))
    except Exception as _wo_err:
        print(f"[Surreal Architecture] world operators skipped: {_wo_err}")

    from .polyhedra_ops import register_polyhedra_operators
    _EXTRA_CLASSES.extend(register_polyhedra_operators(monolith))

    class SURREAL_ARCH_OT_bake_beavel(bpy.types.Operator):
        bl_idname = "surreal_arch.bake_beavel"
        bl_label = "Bake Beavel Pro"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props")

        def execute(self, context):
            from .bevel_bridge import apply_bevel
            from .capabilities import is_available

            if not is_available("beavel"):
                self.report({"ERROR"}, "Beavel Pro addon not enabled")
                return {"CANCELLED"}
            obj = context.active_object
            props = obj.surreal_arch_props
            used = apply_bevel(obj, props, backend="BEAVEL", monolith=monolith)
            self.report({"INFO"}, f"Beavel bake applied ({used})")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_higgsas_load_arch_bridge(bpy.types.Operator):
        bl_idname = "surreal_arch.higgsas_load_arch_bridge"
        bl_label = "Load Higgsas Architecture Nodes"
        bl_options = {"REGISTER"}

        def execute(self, context):
            from .higgsas_bridge import load_arch_nodes, library_path
            import os
            if not os.path.exists(library_path()):
                self.report({"ERROR"}, f"Higgsas library not found:\n{library_path()}")
                return {"CANCELLED"}
            loaded, skipped = load_arch_nodes()
            msg = f"Loaded {len(loaded)} nodes"
            if skipped:
                msg += f" | missing: {', '.join(skipped[:3])}"
            self.report({"INFO"}, msg)
            return {"FINISHED"}

    class SURREAL_ARCH_OT_export_snap_json(bpy.types.Operator):
        bl_idname = "surreal_arch.export_snap_json"
        bl_label = "Export Snap JSON"
        bl_options = {"REGISTER"}

        filepath: bpy.props.StringProperty(subtype="FILE_PATH")

        def execute(self, context):
            obj = context.active_object
            if not obj or "surreal_snap_points" not in obj:
                self.report({"ERROR"}, "No snap metadata on active object")
                return {"CANCELLED"}
            props = getattr(obj, "surreal_arch_props", None)
            if props and getattr(props, "bevel_backend", "MODIFIER") in ("BEAVEL", "AUTO"):
                from .bevel_bridge import apply_bevel
                from .capabilities import is_available
                if is_available("beavel"):
                    apply_bevel(obj, props, backend="BEAVEL", monolith=monolith)
            path = self.filepath or bpy.path.abspath("//snap_points.json")
            from .snap_export import build_ue_export_payload
            payload = build_ue_export_payload(obj, monolith)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self.report({"INFO"}, f"Wrote UE snap JSON ({len(payload.get('trim_groups', []))} trim groups)")
            return {"FINISHED"}

        def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    class SURREAL_ARCH_OT_toggle_snap_overlay(bpy.types.Operator):
        bl_idname = "surreal_arch.toggle_snap_overlay"
        bl_label = "Toggle Snap Overlay"
        bl_options = {"REGISTER"}

        def execute(self, context):
            from .greybox_overlay import _handler, disable_overlay, enable_overlay
            if _handler is None:
                enable_overlay()
                self.report({"INFO"}, "Snap overlay ON")
            else:
                disable_overlay()
                self.report({"INFO"}, "Snap overlay OFF")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_bake_trim_attributes(bpy.types.Operator):
        bl_idname = "surreal_arch.bake_trim_attributes"
        bl_label = "Bake Trim Attributes"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props")

        def execute(self, context):
            obj = context.active_object
            from .trim_bake import apply_trim_bake
            if apply_trim_bake(obj, obj.surreal_arch_props, monolith):
                self.report({"INFO"}, "Trim vertex colors + face attribute written")
                return {"FINISHED"}
            self.report({"WARNING"}, "No trim groups for active arch type")
            return {"CANCELLED"}

    _EXTRA_CLASSES.extend([
        SURREAL_ARCH_OT_export_snap_json,
        SURREAL_ARCH_OT_toggle_snap_overlay,
        SURREAL_ARCH_OT_bake_trim_attributes,
        SURREAL_ARCH_OT_bake_beavel,
        SURREAL_ARCH_OT_higgsas_load_arch_bridge,
    ])
    for cls in _EXTRA_CLASSES:
        _register_class_once(cls)
    try:
        register_live_bridge_props()
    except Exception as exc:
        print(f"[Surreal Architecture] live_bridge props skipped: {exc}")
    try:
        register_material_bridge_props()
    except Exception as exc:
        print(f"[Surreal Architecture] material_bridge props skipped: {exc}")
    try:
        register_portrait_props()
    except Exception as exc:
        print(f"[Surreal Architecture] melusina_portrait props skipped: {exc}")
    try:
        register_stage_publish_props()
    except Exception as exc:
        print(f"[Surreal Architecture] stage_publish props skipped: {exc}")
    try:
        melodia_gn.register_props()
    except Exception as exc:
        print(f"[Surreal Architecture] mel_gn_stack props skipped: {exc}")
    enable_overlay()
    try:
        unify_npanel_categories()
    except Exception as exc:
        print(f"[Surreal Architecture] unify_npanel_categories skipped: {exc}")
    try:
        register_pie_menu_with_keymaps()
    except Exception as exc:
        print(f"[Surreal Architecture] pie keymaps skipped: {exc}")
    try:
        register_music_ui()
    except Exception as exc:
        print(f"[Melodia Studio] music score UI skipped: {exc}")


def unregister_overhaul():
    global _REGISTERED_MONOLITH
    try:
        from .pie_menu import unregister_pie_menu_with_keymaps
        unregister_pie_menu_with_keymaps()
    except Exception:
        pass
    try:
        from .music_ui import unregister_music_ui
        unregister_music_ui()
    except Exception:
        pass
    from .bootstrap import unregister_preferences
    from .greybox_overlay import disable_overlay
    from .quality_props import unregister_quality_props
    try:
        from . import melodia_gn
        melodia_gn.unregister_props()
    except Exception:
        pass
    try:
        if hasattr(bpy.types.Scene, "surreal_arch_review_queue_index"):
            del bpy.types.Scene.surreal_arch_review_queue_index
    except Exception:
        pass
    unregister_quality_props(_REGISTERED_MONOLITH)
    unregister_preferences()
    disable_overlay()
    try:
        unregister_stats_overlay()
    except Exception:
        pass
    try:
        unregister_accessory_props()
    except Exception:
        pass
    global _EXTRA_CLASSES
    for cls in reversed(_EXTRA_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    _EXTRA_CLASSES = []
    _REGISTERED_MONOLITH = None
