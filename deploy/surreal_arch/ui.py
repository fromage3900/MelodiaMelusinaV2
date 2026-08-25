"""UI search, filtered picker, and VIEW_3D panels."""

from __future__ import annotations

import bpy

from .accessory_visibility import ACCESSORY_VECTOR_SIZE


def workflow_mode(props):
    return getattr(props, "ui_workflow_mode", "FULL")


def workflow_allows_style(style_id, mode):
    if mode == "FULL":
        return True
    if mode == "BLOCKOUT":
        return style_id in ("GREYBOX", "EXPERIMENTAL", "ALL")
    if mode == "ARCHITECTURE":
        return style_id in ("GOTHIC", "CIVIC", "CASTLE", "ASIAN", "EXPERIMENTAL", "ALL")
    return True


def workflow_allows_panel(panel_kind, props):
    mode = workflow_mode(props)
    if mode == "FULL":
        return True
    hidden = {
        "effects", "integration", "music", "magic", "scifi", "escher",
        "aesthetic", "kepler", "sverchok", "higgsas", "compose", "layer3",
        "advanced_gn", "auto_building",
    }
    if panel_kind in hidden:
        return False
    if mode == "BLOCKOUT":
        if panel_kind in ("level_design", "style_greybox"):
            return True
        if panel_kind.startswith("style_") and panel_kind != "style_greybox":
            return False
    if mode == "ARCHITECTURE":
        if panel_kind in ("level_design", "style_greybox"):
            return False
    return True


def filter_type_ids(monolith, query, style_filter, wf_mode):
    from .catalog import search_index
    q = (query or "").strip().lower()
    allowed = None
    if wf_mode == "BLOCKOUT":
        allowed = {"greybox", "experimental"}
    elif wf_mode == "ARCHITECTURE":
        allowed = {"gothic", "civic", "castle", "asian", "experimental"}
    out = set()
    for ent in search_index(monolith):
        if style_filter != "ALL" and ent["style"].upper() != style_filter:
            continue
        if allowed is not None and ent["style"] not in allowed:
            continue
        if q:
            tokens = [t for t in q.split() if t]
            if tokens and not all(tok in ent["search_text"] for tok in tokens):
                continue
        out.add(ent["id"])
    return out


def _rank(ent, query):
    q = (query or "").strip().lower()
    if not q:
        return 0
    if q == ent["id"].lower() or q in ent["label"].lower():
        return 100
    if q in ent["search_text"]:
        return 50
    return 10


def draw_picker_search_header(layout, props):
    from .melodia_gn.core import STUDIO_LABELS
    box = layout.box()
    info = STUDIO_LABELS.get(props.arch_type, {})
    active_label = info.get("ui_label", props.arch_type)
    hint = info.get("panel_hint", props.arch_type)
    box.label(text=f"Active: {active_label}", icon="OUTLINER_OB_MESH")
    if hint and hint != props.arch_type:
        box.label(text=hint, icon="INFO")
    row = box.row(align=True)
    row.prop(props, "arch_search_query", text="", icon="VIEWZOOM")
    row.prop(props, "ui_picker_style_filter", text="")
    row.prop(props, "ui_workflow_mode", text="")
    q = (props.arch_search_query or "").strip()
    if q and hasattr(props, "id_data"):
        pass


def draw_arch_picker_filtered(layout, context, monolith, *, compact=False):
    obj = context.active_object
    props = obj.surreal_arch_props if obj else None
    if not props:
        layout.label(text="Select a mesh with Melodia Studio", icon="ERROR")
        return
    current_at = props.arch_type
    draw_picker_search_header(layout, props)
    q = (props.arch_search_query or "").strip()
    mode = workflow_mode(props)
    filtered = filter_type_ids(
        monolith, props.arch_search_query, props.ui_picker_style_filter, mode
    )
    if q:
        from .catalog import search_index
        hits = [e for e in search_index(monolith) if e["id"] in filtered]
        hits.sort(key=lambda e: -_rank(e, q))
        box = layout.box()
        box.label(text=f"{len(hits)} result(s)", icon="SORTALPHA")
        grid = box.grid_flow(row_major=True, columns=3 if compact else 4, align=True)
        for ent in hits[:48]:
            op = grid.operator("surreal_arch.set_arch_type", text=ent["label"],
                               depress=(current_at == ent["id"]))
            op.arch_type = ent["id"]
            op.auto_generate = False
        return
    for style_id, style_label, cat_ids in monolith._ARCH_PICKER_STYLE_GROUPS:
        if not workflow_allows_style(style_id, mode):
            continue
        if props.ui_picker_style_filter != "ALL" and props.ui_picker_style_filter != style_id:
            continue
        style_box = layout.box()
        style_box.label(text=style_label, icon="DOWNARROW_HLT")
        for cat_id in cat_ids:
            cat = monolith._ARCH_CATEGORIES_BY_ID.get(cat_id)
            if not cat:
                continue
            cat_label, cat_icon, items = cat
            visible = [(a, l) for a, l in items if a in filtered]
            if not visible:
                continue
            box = style_box.box()
            box.label(text=cat_label, icon=monolith._sanitize_ui_icon(cat_icon))
            grid = box.grid_flow(row_major=True, columns=2 if compact else 3, align=True)
            for at_id, at_label in visible:
                op = grid.operator("surreal_arch.set_arch_type", text=at_label,
                                   depress=(current_at == at_id))
                op.arch_type = at_id
                op.auto_generate = False
    if not compact:
        power = layout.box()
        power.label(text="Power user", icon="SETTINGS")
        power.prop(props, "arch_type", text="Full enum")
    layout.separator()
    row = layout.row(align=True)
    row.scale_y = 1.3
    row.operator("surreal_arch.generate", text="Generate", icon="SHADERFX")
    draw_bagapie_ivy_row(layout, context)


def draw_bagapie_ivy_row(layout, context):
    box = layout.box()
    row = box.row(align=True)
    row.scale_y = 1.15
    row.operator("surreal_arch.nikki_mat_apply", text="Nikki Mat (props)", icon="MATERIAL_DATA")
    row.operator("surreal_arch.ivy_scatter", text="Ivy (Bagapie)", icon="OUTLINER_OB_CURVE")
    batch = box.row(align=True)
    batch.operator("surreal_arch.ivy_scatter_review_queue", text="RQ Ivy Batch", icon="OUTLINER_COLLECTION")

    obj = context.active_object
    if obj is None or obj.type != "MESH":
        box.label(text="Select a mesh for Nikki material or ivy scattering", icon="INFO")
        return

    try:
        from .bagapie_bridge import bagapie_available
        ready = bagapie_available()
    except Exception:
        ready = False
    if ready:
        box.label(text=f"Target: {obj.name}", icon="CHECKBOX_HLT")
    else:
        box.label(text="Enable Bagapie extension to scatter ivy", icon="ERROR")


def draw_graph_library(layout, context):
    from .greybox_graph import GRAPH_REGISTRY
    box = layout.box()
    box.label(text="Graph library", icon="NODETREE")
    obj = context.active_object
    if obj and hasattr(obj, "surreal_arch_props"):
        box.prop(obj.surreal_arch_props, "graph_spawn_spacing", text="Module spacing (m)")
    styles = sorted({m.get("style", "all") for m in GRAPH_REGISTRY.values()})
    for style in styles:
        style_box = box.box()
        style_box.label(text=style.replace("_", " ").title(), icon="OUTLINER_COLLECTION")
        for gid, meta in GRAPH_REGISTRY.items():
            if meta.get("style") != style:
                continue
            card = style_box.box()
            header = card.row(align=True)
            header.label(text=f"{meta['label']} ({meta['module_count']} mods)", icon="LINKED")
            header.operator(f"surreal_arch.spawn_graph_{gid.lower()}", text="Spawn", icon="PLAY")
            card.label(text=meta["preview"], icon="FORWARD")
            card.label(text=meta["description"], icon="INFO")


def draw_level_design(layout, context, monolith):
    obj = context.active_object
    if not obj or not hasattr(obj, "surreal_arch_props"):
        layout.label(text="Select a mesh with Melodia Studio", icon="ERROR")
        return
    props = obj.surreal_arch_props
    grid = layout.box()
    grid.label(text="Modular grid", icon="GRID")
    col = grid.column(align=True)
    col.prop(props, "unit_size")
    col.prop(props, "auto_align_mode")
    trim = layout.box()
    trim.label(text="Trim mode", icon="MOD_BOOLEAN")
    tcol = trim.column(align=True)
    tcol.prop(props, "gb_trim_mode", text="Mode")
    if props.gb_trim_mode != "NONE":
        tcol.prop(props, "gb_trim_recess")
        tcol.prop(props, "gb_frame", text="Door frame")
        tcol.prop(props, "gb_bake_trim_colors", text="Bake trim colors")
    # ── Room shell: advanced shapes ──────────────────────────────
    if hasattr(props, "gb_room_shape"):
        is_room = props.arch_type in ("GREYBOX_ROOM", "GB_ROOM_COMPOSITE", "GB_ROOM_CIRCULAR", "GB_ROOM_APSIDAL", "GB_ROOM_CIRCULAR", "GB_ROOM_APSIDAL") or monolith._match_greybox_arch(props.arch_type)
        # Show for any greybox arch so advanced shapes are discoverable
        rbox = layout.box()
        rbox.label(text="Room Shell - shape & math", icon="MESH_CUBE")
        rcol = rbox.column(align=True)
        rcol.prop(props, "gb_room_shape", text="Shape")
        adv_shape = getattr(props, "gb_room_shape", "RECTANGLE") in ("CIRCULAR", "APSIDAL", "OCTAGON", "HEX", "ELLIPSE", "SUPERELLIPSE", "FREEFORM")
        if adv_shape:
            rcol.prop(props, "gb_room_radius", text="Radius")
            if getattr(props, "gb_room_shape", "") in ("OCTAGON", "HEX", "ELLIPSE", "SUPERELLIPSE", "CIRCULAR", "APSIDAL", "FREEFORM"):
                rcol.prop(props, "gb_room_sides", text="Sides")
            if getattr(props, "gb_room_shape", "") in ("ELLIPSE", "SUPERELLIPSE"):
                rcol.prop(props, "gb_room_ellipse_ratio", text="Ellipse Ratio")
            if getattr(props, "gb_room_shape", "") == "SUPERELLIPSE":
                rcol.prop(props, "gb_room_super_n", text="Super N")
            rcol.label(text="Tip: use Pie -> Room Shape (Alt+Q) for quick switch", icon="INFO")
        else:
            # Composite L/T/U hint
            if getattr(props, "gb_room_shape", "") in ("L_SHAPE", "T_SHAPE", "U_SHAPE"):
                rcol.label(text="L/T/U uses W/D as wing sizes - see composite builder", icon="INFO")

    # ── Window cutouts - detailed ────────────────────────────────
    if hasattr(props, "gb_window_shape"):
        wbox = layout.box()
        wbox.label(text="Window Cutouts - detailed", icon="WINDOW")
        wcol = wbox.column(align=True)
        wcol.prop(props, "gb_windows_enabled", text="Enable Windows")
        if getattr(props, "gb_windows_enabled", False):
            wcol.prop(props, "gb_window_shape", text="Window Shape")
            wcol.prop(props, "gb_window_arch_height", text="Arch Height")
            wrow = wbox.row(align=True)
            wrow.prop(props, "gb_window_width", text="W")
            wrow.prop(props, "gb_window_height", text="H")
            wrow.prop(props, "gb_window_sill", text="Sill")
            wcol.prop(props, "gb_window_frame_thickness", text="Frame Thick")
            brow = wbox.row(align=True)
            brow.prop(props, "gb_window_has_mullion", text="Mullion")
            brow.prop(props, "gb_window_has_transom", text="Transom")
            wcol.prop(props, "gb_window_glazing", text="Glazing (glass plane)")
            # Per-wall counts / toggles
            wbox.label(text="Placement", icon="UV")
            prow = wbox.row(align=True)
            prow.prop(props, "gb_window_count_ns", text="N/S")
            prow.prop(props, "gb_window_count_ew", text="E/W")
            fallback = wbox.column(align=True)
            fallback.label(text="Legacy per-wall fallback (when counts =0)", icon="DOT")
            frow = fallback.row(align=True)
            frow.prop(props, "gb_window_n", text="N")
            frow.prop(props, "gb_window_s", text="S")
            frow.prop(props, "gb_window_e", text="E")
            frow.prop(props, "gb_window_w", text="W")
            fallback.prop(props, "gb_window_count", text="Per Wall")
            wbox.label(text="Pie -> Window (Ctrl+Shift+Q) cycles shape", icon="INFO")
        else:
            wcol.label(text="Enable to expose shape / arch / frame / mullion / glazing", icon="INFO")
            wcol.prop(props, "gb_window_n", text="N")
            wcol.prop(props, "gb_window_e", text="E")
            wcol.prop(props, "gb_window_w", text="W")

    if monolith._match_greybox_arch(props.arch_type):
        kit = layout.box()
        kit.label(text="Corridor kit", icon="MOD_BUILD")
        kcol = kit.column(align=True)
        if hasattr(props, "gb_corridor_profile"):
            kcol.prop(props, "gb_corridor_profile")
            kcol.prop(props, "gb_corridor_ceiling")
            kcol.prop(props, "gb_corridor_rib_mode")
            kcol.prop(props, "gb_junction_column")
            kcol.prop(props, "gb_wainscot_height")
            kcol.prop(props, "gb_baseboard_height")
    monolith._draw_greybox_quick_launch(layout, context)
    snap = layout.box()
    snap.label(text="Place and snap", icon="SNAP_ON")
    srow = snap.row(align=True)
    srow.operator("surreal_arch.snap_to_selected", text="Snap to Selected", icon="SNAP_VERTEX")
    srow.operator("surreal_arch.auto_snap_chain", text="Auto Chain", icon="LINKED")
    n = len(monolith._gb_load_snap_points(obj))
    snap.label(text=f"{n} snap point(s)" if n else "Generate for snap metadata", icon="INFO")
    try:
        import json
        from .snap_export import build_trim_groups
        from .trim_color_bake import count_eval_trim_zone_faces

        raw = obj.get("surreal_trim_groups")
        trim_groups = json.loads(raw) if isinstance(raw, str) else (raw or [])
        if not trim_groups and props.gb_trim_mode != "NONE":
            trim_groups = build_trim_groups(props, monolith)
        if trim_groups:
            snap.label(text=f"{len(trim_groups)} trim group(s)", icon="MATERIAL")
        if props.gb_trim_mode != "NONE" and obj.data and len(obj.data.polygons):
            tz = count_eval_trim_zone_faces(obj)
            if tz:
                snap.label(text=f"{tz} GN trim-zone face(s)", icon="FACESEL")
    except Exception:
        pass
    qa = layout.box()
    qa.label(text="QA", icon="CHECKMARK")
    qa.operator("surreal_arch.validate_assembly", text="Check Assembly", icon="VIEWZOOM")
    for hint in monolith._gb_validate_assembly(context)[:3]:
        qa.label(text=hint, icon="INFO" if "passed" in hint.lower() else "ERROR")
    genome_box = layout.box()
    genome_box.label(text="Style Genome (OS)", icon="RNA")
    gcol = genome_box.column(align=True)
    gcol.prop(props, "style_genome_id", text="Active")
    genomes = sorted(getattr(monolith, "_STYLE_GENOMES", None) or [])
    genome_groups = getattr(monolith, "_STYLE_GENOME_GROUPS", None) or {}
    if genomes:
        catalog = genome_box.column(align=True)
        catalog.label(text=f"Catalog ({len(genomes)})", icon="PRESET")
        active_gid = getattr(props, "style_genome_id", "")
        genome_meta = getattr(monolith, "_STYLE_GENOME_META", {}) or {}

        def _draw_genome_button(gid):
            row = catalog.row(align=True)
            op = row.operator(
                "surreal_arch.select_style_genome",
                text=gid,
                depress=(gid == active_gid),
            )
            op.genome_id = gid
            meta = genome_meta.get(gid, {})
            graph = meta.get("graph", "")
            xf = meta.get("transform", "")
            if graph or xf:
                catalog.label(text=f"  {graph} - {xf}", icon="DOT")

        if genome_groups:
            for family, gids in genome_groups.items():
                catalog.label(text=f"{family} ({len(gids)})", icon="OUTLINER_COLLECTION")
                for gid in gids:
                    _draw_genome_button(gid)
        else:
            for gid in genomes:
                _draw_genome_button(gid)
    grow = genome_box.row(align=True)
    grow.operator("surreal_arch.apply_style_genome", text="Apply", icon="CHECKMARK")
    grow.operator("surreal_arch.spawn_genome_graph", text="Spawn Graph", icon="NODETREE")
    genome_box.operator("surreal_arch.spawn_zen_shrine_plan", text="Spawn Shrine Plan", icon="WORLD")
    if getattr(monolith, "_active_style_genome", None):
        g = monolith._active_style_genome
        genome_box.label(text=f"Active: {g.get('id', '?')} -> {g.get('default_graph', '')}", icon="INFO")
    draw_graph_library(layout, context)
    uvbox = layout.box()
    uvbox.label(text="UV / Trimsheet", icon="UV")
    ucol = uvbox.column(align=True)
    ucol.prop(props, "uv_unwrap_mode", text="Mode")
    if props.gb_trim_mode != "NONE":
        ucol.prop(props, "gb_bake_trim_colors", text="Bake trim colors")
    urow1 = uvbox.row(align=True)
    urow1.operator("surreal_arch.uv_create_edit_proxy", text="UV Proxy", icon="DUPLICATE")
    urow1.operator("surreal_arch.uv_commit_from_proxy", text="Commit UV", icon="IMPORT")
    urow2 = uvbox.row(align=True)
    urow2.operator("surreal_arch.uv_invoke_miouv", text="MioUV Pack", icon="UV_ISLANDSEL")
    urow2.operator("surreal_arch.uv_invoke_uvpackmaster", text="UVPM Pack", icon="UV")
    try:
        from .capabilities import status_line
        uvbox.label(text=status_line("miouv"), icon="PLUGIN")
        uvbox.label(text=status_line("uvpackmaster"), icon="PLUGIN")
    except Exception:
        pass
    assets = layout.box()
    assets.label(text="Asset Browser", icon="ASSET_MANAGER")
    assets.operator("surreal_arch.publish_greybox_assets", text="Publish Greybox Assets", icon="FILE_BLEND")
    assets.operator("surreal_arch.export_catalog_enum", text="Export Catalog Enum Stub", icon="TEXT")
    draw_bagapie_ivy_row(layout, context)
    research = layout.box()
    research.label(text="Research presets", icon="BOOKMARKS")
    r1 = research.row(align=True)
    r1.operator("surreal_arch.preset_research_romanesque_cloister_arcade", text="Cloister")
    r1.operator("surreal_arch.preset_research_brutalist_pilotis_hall", text="Pilotis")
    r2 = research.row(align=True)
    r2.operator("surreal_arch.preset_research_venetian_loggia_bay", text="Loggia")
    r2.operator("surreal_arch.preset_research_scifi_pressure_door_airlock", text="Airlock")
    tools = layout.box()
    tools.label(text="Export", icon="EXPORT")
    erow = tools.row(align=True)
    erow.operator("surreal_arch.export_ue5", text="Bake & Export UE5", icon="EXPORT")
    erow.operator("surreal_arch.export_snap_json", text="Snap JSON", icon="FILE_TICK")
    tools.operator("surreal_arch.bake_trim_attributes", text="Bake Trim Attributes")
    brow = tools.row(align=True)
    brow.operator("surreal_arch.bake_beavel", text="Bake Beavel Pro", icon="MOD_BEVEL")
    vrow = layout.box()
    vrow.label(text="Viewport", icon="HIDE_OFF")
    overlay_row = vrow.row(align=True)
    overlay_row.operator("surreal_arch.toggle_snap_overlay", text="Toggle Snap Overlay")
    overlay_row.operator("surreal_arch.stats_overlay_toggle", text="Stats Overlay", icon="INFO")
    acc = layout.box()
    acc.label(text="Accessories", icon="OUTLINER_COLLECTION")
    if hasattr(bpy.types.Scene, "surreal_arch_accessory_toggles"):
        grid = acc.grid_flow(row_major=True, columns=8, even_columns=True, align=True)
        for i in range(ACCESSORY_VECTOR_SIZE):
            grid.prop(
                context.scene,
                "surreal_arch_accessory_toggles",
                index=i,
                text="",
                toggle=True,
            )
        arow = acc.row(align=True)
        arow.operator("surreal_arch.apply_accessory_visibility", text="Apply", icon="CHECKMARK")
        arow.operator("surreal_arch.show_all_accessories", text="Show All", icon="HIDE_OFF")
    row = layout.row(align=True)
    row.scale_y = 1.25
    row.operator("surreal_arch.generate", text="Generate", icon="SHADERFX")


def make_view3d_panels(monolith):
    M = monolith

    class _V3DBase:
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Melodia Studio"
        bl_options = {"DEFAULT_CLOSED"}

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props")

    class SURREAL_ARCH_PT_view3d_picker(_V3DBase, bpy.types.Panel):
        bl_label = "Architecture Picker"
        bl_idname = "SURREAL_ARCH_PT_view3d_picker"

        def draw(self, context):
            draw_arch_picker_filtered(self.layout, context, M, compact=True)

    class SURREAL_ARCH_PT_view3d_level_design(_V3DBase, bpy.types.Panel):
        bl_label = "Level Design"
        bl_idname = "SURREAL_ARCH_PT_view3d_level_design"

        @classmethod
        def poll(cls, context):
            if not super().poll(context):
                return False
            props = context.active_object.surreal_arch_props
            return workflow_allows_panel("level_design", props)

        def draw(self, context):
            draw_level_design(self.layout, context, M)

    return SURREAL_ARCH_PT_view3d_picker, SURREAL_ARCH_PT_view3d_level_design
