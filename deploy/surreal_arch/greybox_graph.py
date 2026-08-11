"""Room graph presets — spawn and auto-snap module chains."""

from __future__ import annotations

import bpy
from mathutils import Vector


GRAPH_CLOISTER = [
    ("GREYBOX_CORRIDOR", {"gb_length": 8.0, "gb_corridor_profile": "DOUBLE"}),
    ("GB_CORRIDOR_BEND", {"gb_length": 6.0}),
    ("GREYBOX_CORRIDOR", {"gb_length": 8.0}),
    ("GB_GOTHIC_PORTAL", {}),
]

GRAPH_SCI_FI_DECK = [
    ("GREYBOX_CORRIDOR", {"gb_length": 12.0, "gb_corridor_profile": "DOUBLE"}),
    ("GB_CORRIDOR_T", {"gb_length": 6.0}),
    ("GREYBOX_ROOM", {"gb_width": 8.0, "gb_depth": 6.0}),
]

GRAPH_ROMANESQUE_CLOISTER = [
    ("GB_ROMANESQUE_ARCADE", {"gb_width": 3.2, "gb_height": 4.2, "unit_size": 3.2, "gb_trim_mode": "RECESS"}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 8.0, "gb_trim_mode": "RECESS", "unit_size": 3.2}),
    ("GB_ROMANESQUE_ARCADE", {"gb_width": 3.2, "gb_height": 4.2}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 8.0, "gb_trim_mode": "RECESS"}),
    ("GB_ROMANESQUE_ARCADE", {}),
]

GRAPH_SCIFI_AIRLOCK = [
    ("GREYBOX_CORRIDOR", {"gb_length": 6.0, "gb_corridor_profile": "DOUBLE", "material_choice": "METAL"}),
    ("GB_SCIFI_PRESSURE_DOOR", {"gb_length": 3.5, "gb_door_width": 1.2, "gb_trim_mode": "RECESS", "gb_trim_recess": 0.1}),
    ("GREYBOX_ROOM", {"gb_width": 3.5, "gb_depth": 3.5, "gb_height": 3.2, "gb_ceiling": True, "material_choice": "METAL"}),
    ("GB_SCIFI_PRESSURE_DOOR", {"gb_length": 3.5, "gb_door_width": 1.2, "gb_trim_mode": "RECESS"}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 6.0, "gb_trim_mode": "RECESS", "material_choice": "METAL"}),
]

GRAPH_ROMANESQUE_APSE = [
    ("GB_ROMANESQUE_ARCADE", {"gb_width": 3.2, "gb_height": 4.2, "gb_trim_mode": "RECESS", "unit_size": 3.2}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 10.0, "gb_trim_mode": "RECESS", "unit_size": 3.2}),
    ("GB_ROMANESQUE_ARCADE", {"gb_width": 3.2, "gb_height": 4.2}),
    ("GB_ROMANESQUE_APSE", {"gb_width": 4.0, "gb_depth": 3.5, "gb_height": 4.5, "gb_trim_mode": "RECESS"}),
]

GRAPH_VENETIAN_CANAL = [
    ("GB_VENETIAN_LOGGIA", {"gothic_width": 2.8, "gb_height": 4.0, "gb_trim_mode": "RECESS"}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 8.0, "gb_trim_mode": "RECESS", "gb_wainscot_height": 0.35}),
    ("GB_VENETIAN_LOGGIA", {"gothic_width": 2.8, "gb_height": 4.0}),
    ("GREYBOX_CORRIDOR", {"gb_length": 6.0, "gb_corridor_profile": "SINGLE", "gb_trim_mode": "RECESS"}),
    ("GB_VENETIAN_LOGGIA", {}),
]

GRAPH_SCI_FI_DECK_EXPANSION = [
    ("GREYBOX_CORRIDOR", {"gb_length": 14.0, "gb_corridor_profile": "DOUBLE", "material_choice": "METAL"}),
    ("GB_CORRIDOR_T", {"gb_length": 8.0, "material_choice": "METAL"}),
    ("GB_SCIFI_PRESSURE_DOOR", {"gb_length": 3.5, "gb_door_width": 1.4, "gb_trim_mode": "RECESS"}),
    ("GREYBOX_ROOM", {"gb_width": 10.0, "gb_depth": 8.0, "gb_height": 3.6, "material_choice": "METAL"}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 10.0, "gb_trim_mode": "RECESS", "material_choice": "METAL"}),
    ("GB_SCIFI_PRESSURE_DOOR", {"gb_length": 3.5, "gb_trim_mode": "RECESS"}),
]

GRAPH_SCI_FI_INDUSTRIAL_YARD = [
    ("GREYBOX_PILLAR_HALL", {"gb_cols_x": 4, "gb_cols_y": 3, "gb_spacing": 4.0, "gb_height": 4.2, "gb_trim_mode": "RECESS", "material_choice": "AUTO", "unit_size": 4.0}),
    ("GREYBOX_CATWALK", {"gb_length": 12.0, "gb_width": 1.6, "gb_rail_height": 1.0, "material_choice": "AUTO"}),
    ("GB_SCIFI_PRESSURE_DOOR", {"gb_length": 3.5, "gb_door_width": 1.6, "gb_trim_mode": "RECESS", "material_choice": "AUTO"}),
    ("GREYBOX_CORRIDOR", {"gb_length": 10.0, "gb_corridor_profile": "DOUBLE", "gb_trim_mode": "RECESS", "material_choice": "AUTO"}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 8.0, "gb_trim_mode": "RECESS", "material_choice": "AUTO"}),
    ("GREYBOX_CATWALK", {"gb_length": 8.0, "gb_width": 1.4, "material_choice": "AUTO"}),
]

GRAPH_ZEN_ROJI_PATH = [
    ("GB_ZEN_TORII_GATE", {"torii_width": 3.6, "torii_height": 4.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_TOBIISHI", {"gb_length": 4.5, "gb_width": 1.6, "gb_trim_mode": "RECESS", "unit_size": 2.0}),
    ("GB_ZEN_ROJI_STEP", {"gb_length": 5.0, "gb_width": 1.8, "gb_trim_mode": "RECESS", "unit_size": 2.0}),
    ("GB_ZEN_ROJI_STEP", {"gb_length": 4.0, "gb_width": 1.8}),
    ("GB_ZEN_TSUKUBAI", {"gb_width": 1.6, "gb_depth": 1.6, "gb_height": 0.45, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_LANTERN", {"zen_lantern_height": 1.4, "zen_lantern_style": "KASUGA", "gb_trim_mode": "RECESS"}),
]

GRAPH_ZEN_SHRINE_COURTYARD = [
    ("GB_ZEN_TORII_GATE", {"torii_width": 4.0, "torii_height": 4.5}),
    ("GB_ZEN_BAMBOO_FENCE", {"gb_length": 8.0, "zen_fence_height": 1.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_KARESANSUI", {"gb_width": 8.0, "gb_depth": 6.0, "gb_trim_mode": "RECESS"}),
    ("ZEN_BRIDGE", {"zen_bridge_span": 5.0, "zen_bridge_rise": 0.6}),
    ("GB_ZEN_ENGAWA", {"gb_width": 5.5, "gb_depth": 2.5, "gb_height": 0.35, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_MACHIAI", {"gb_width": 3.2, "gb_depth": 2.4, "gb_height": 2.2, "gb_trim_mode": "RECESS"}),
    ("ZEN_TEAHOUSE", {"teahouse_depth": 4.5, "teahouse_width": 5.0}),
    ("GB_ZEN_LANTERN", {}),
]

GRAPH_ZEN_KARESANSHUI_WALK = [
    ("GB_ZEN_TORII_GATE", {"torii_width": 3.4, "torii_height": 4.0, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_ROJI_STEP", {"gb_length": 5.0, "gb_width": 1.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_KARESANSUI", {"gb_width": 8.0, "gb_depth": 6.0, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_MACHIAI", {"gb_width": 3.2, "gb_depth": 2.4, "gb_height": 2.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_LANTERN", {"zen_lantern_height": 1.4}),
]

GRAPH_ZEN_SAKURA_WALK = [
    ("GB_ZEN_SAKURA_TORII", {"torii_width": 3.4, "torii_height": 4.0, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_ROJI_STEP", {"gb_length": 5.0, "gb_width": 1.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_CHERRY_ALLEE", {"gb_length": 6.0, "gb_width": 2.6, "gb_height": 0.32, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_WATER_EDGE", {"gb_length": 2.8, "gb_width": 2.4, "zen_stream_depth": 0.35, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_STONE_BRIDGE", {"zen_bridge_span": 5.0, "zen_bridge_rise": 0.55, "gb_width": 1.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_KARESANSUI", {"gb_width": 8.0, "gb_depth": 6.0, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_MACHIAI", {"gb_width": 3.2, "gb_depth": 2.4, "gb_height": 2.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_ENGAWA", {"gb_width": 5.0, "gb_depth": 2.3, "gb_height": 0.35, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_LANTERN", {"zen_lantern_height": 1.5}),
]

GRAPH_ZEN_TEA_GARDEN = [
    ("GB_ZEN_TORII_GATE", {"torii_width": 3.2, "torii_height": 3.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_TOBIISHI", {"gb_length": 6.0, "gb_width": 1.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_BAMBOO_FENCE", {"gb_length": 6.0, "zen_fence_height": 1.1}),
    ("GB_ZEN_TSUKUBAI", {"gb_width": 1.4, "gb_depth": 1.4, "gb_height": 0.4, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_ENGAWA", {"gb_width": 4.5, "gb_depth": 2.2, "gb_trim_mode": "RECESS"}),
    ("ZEN_TEAHOUSE", {"teahouse_depth": 4.0, "teahouse_width": 4.5}),
    ("GB_ZEN_LANTERN", {"zen_lantern_height": 1.2, "gb_trim_mode": "RECESS"}),
]

def _preview_chain(spec):
    return " \u203a ".join(at.replace("GREYBOX_", "").replace("GB_", "") for at, _ in spec)


GRAPH_REGISTRY = {
    "CLOISTER": {
        "label": "Cloister Walk",
        "description": "Gothic monastery walk — corridor bend into portal bay",
        "preview": _preview_chain(GRAPH_CLOISTER),
        "style": "gothic",
        "module_count": len(GRAPH_CLOISTER),
        "spec": GRAPH_CLOISTER,
    },
    "SCI_FI_DECK": {
        "label": "Sci-Fi Deck Spine",
        "description": "Industrial spine — long hall, T-junction, command room",
        "preview": _preview_chain(GRAPH_SCI_FI_DECK),
        "style": "scifi",
        "module_count": len(GRAPH_SCI_FI_DECK),
        "spec": GRAPH_SCI_FI_DECK,
    },
    "ROMANESQUE_CLOISTER": {
        "label": "Romanesque Cloister Loop",
        "description": "Arcade bay and offset corridor rhythm — bay-end snaps",
        "preview": _preview_chain(GRAPH_ROMANESQUE_CLOISTER),
        "style": "romanesque",
        "module_count": len(GRAPH_ROMANESQUE_CLOISTER),
        "spec": GRAPH_ROMANESQUE_CLOISTER,
    },
    "SCI_FI_AIRLOCK": {
        "label": "Sci-Fi Double-Door Airlock",
        "description": "Pressure doors with gasket trim flanking sealed chamber",
        "preview": _preview_chain(GRAPH_SCIFI_AIRLOCK),
        "style": "scifi",
        "module_count": len(GRAPH_SCIFI_AIRLOCK),
        "spec": GRAPH_SCIFI_AIRLOCK,
    },
    "ROMANESQUE_APSE": {
        "label": "Romanesque Choir + Apse",
        "description": "Arcade walk terminating in semicircular apse — Cistercian choir layout",
        "preview": _preview_chain(GRAPH_ROMANESQUE_APSE),
        "style": "romanesque",
        "module_count": len(GRAPH_ROMANESQUE_APSE),
        "spec": GRAPH_ROMANESQUE_APSE,
    },
    "VENETIAN_CANAL": {
        "label": "Venetian Canal Block",
        "description": "Loggia rhythm along offset corridor — sottoportego + waterfront facade",
        "preview": _preview_chain(GRAPH_VENETIAN_CANAL),
        "style": "venetian",
        "module_count": len(GRAPH_VENETIAN_CANAL),
        "spec": GRAPH_VENETIAN_CANAL,
    },
    "SCI_FI_DECK_EXPANSION": {
        "label": "Sci-Fi Command Deck",
        "description": "Expanded deck spine — T-junction, airlock, command room, return corridor",
        "preview": _preview_chain(GRAPH_SCI_FI_DECK_EXPANSION),
        "style": "scifi",
        "module_count": len(GRAPH_SCI_FI_DECK_EXPANSION),
        "spec": GRAPH_SCI_FI_DECK_EXPANSION,
    },
    "SCI_FI_INDUSTRIAL_YARD": {
        "label": "Sci-Fi Industrial Yard",
        "description": "Hypostyle atrium, catwalk spine, bulkhead, service corridor return",
        "preview": _preview_chain(GRAPH_SCI_FI_INDUSTRIAL_YARD),
        "style": "scifi",
        "module_count": len(GRAPH_SCI_FI_INDUSTRIAL_YARD),
        "spec": GRAPH_SCI_FI_INDUSTRIAL_YARD,
    },
    "ZEN_ROJI_PATH": {
        "label": "Zen Roji Approach",
        "description": "Torii gate, dew-path steps, tsukubai basin, stone lantern — tea garden entry",
        "preview": _preview_chain(GRAPH_ZEN_ROJI_PATH),
        "style": "zen",
        "module_count": len(GRAPH_ZEN_ROJI_PATH),
        "spec": GRAPH_ZEN_ROJI_PATH,
    },
    "ZEN_SHRINE_COURTYARD": {
        "label": "Zen Shrine Courtyard",
        "description": "Torii, bamboo fence, karesansui, bridge, engawa veranda, teahouse, lantern",
        "preview": _preview_chain(GRAPH_ZEN_SHRINE_COURTYARD),
        "style": "zen",
        "module_count": len(GRAPH_ZEN_SHRINE_COURTYARD),
        "spec": GRAPH_ZEN_SHRINE_COURTYARD,
    },
    "ZEN_TEA_GARDEN": {
        "label": "Zen Tea Garden",
        "description": "Compact roji — torii, tobi-ishi, bamboo screen, tsukubai, engawa, teahouse",
        "preview": _preview_chain(GRAPH_ZEN_TEA_GARDEN),
        "style": "zen",
        "module_count": len(GRAPH_ZEN_TEA_GARDEN),
        "spec": GRAPH_ZEN_TEA_GARDEN,
    },
    "ZEN_KARESANSHUI_WALK": {
        "label": "Zen Karesansui Walk",
        "description": "Torii → roji path → dry garden → machiai waiting pavilion",
        "preview": _preview_chain(GRAPH_ZEN_KARESANSHUI_WALK),
        "style": "zen",
        "module_count": len(GRAPH_ZEN_KARESANSHUI_WALK),
        "spec": GRAPH_ZEN_KARESANSHUI_WALK,
    },
    "ZEN_SAKURA_WALK": {
        "label": "Zen Sakura Walk",
        "description": "Cherry blossom garden route — allee, stream edge, stone bridge, karesansui",
        "preview": _preview_chain(GRAPH_ZEN_SAKURA_WALK),
        "style": "zen",
        "module_count": len(GRAPH_ZEN_SAKURA_WALK),
        "spec": GRAPH_ZEN_SAKURA_WALK,
    },
}


def best_snap_pair(monolith, obj_a, obj_b):
    """Prefer opposing MUST_CONNECT snaps when chaining graph modules."""
    pts_a = monolith._gb_load_snap_points(obj_a)
    pts_b = monolith._gb_load_snap_points(obj_b)
    if not pts_a or not pts_b:
        return None
    compatible = {
        ("DOOR", "DOOR"), ("WALL", "WALL"),
        ("WALL", "DOOR"), ("DOOR", "WALL"),
        ("CORNER", "WALL"), ("WALL", "CORNER"),
    }
    best = None
    best_score = -1e9
    must_bonus = 6.0
    for pa in pts_a:
        for pb in pts_b:
            key = (pa.get("type"), pb.get("type"))
            if key not in compatible and pa.get("type") != pb.get("type"):
                continue
            da = monolith._gb_snap_world_dir(obj_a, pa)
            db = monolith._gb_snap_world_dir(obj_b, pb)
            align = da.dot(db)
            if align > -0.35:
                continue
            wa = monolith._gb_snap_world_point(obj_a, pa)
            wb = monolith._gb_snap_world_point(obj_b, pb)
            dist = (wa - wb).length
            score = -dist + abs(align) * 3.0
            if pa.get("rule") == "MUST_CONNECT":
                score += must_bonus
            if pb.get("rule") == "MUST_CONNECT":
                score += must_bonus
            if score > best_score:
                best_score = score
                best = (pa, pb, wa, wb)
    return best


def resolve_graph_spacing(context, default=10.0):
    obj = context.active_object
    if obj and hasattr(obj, "surreal_arch_props"):
        return float(getattr(obj.surreal_arch_props, "graph_spawn_spacing", default))
    return default


def spawn_graph(context, monolith, graph_spec, spacing=None, graph_id=None):
    if spacing is None:
        spacing = resolve_graph_spacing(context)
    col = context.collection
    objs = []
    x = 0.0
    for arch_type, overrides in graph_spec:
        mesh = bpy.data.meshes.new(f"Graph_{arch_type}")
        obj = bpy.data.objects.new(f"Graph_{arch_type}", mesh)
        col.objects.link(obj)
        props = obj.surreal_arch_props
        props.arch_type = arch_type
        for k, v in overrides.items():
            if hasattr(props, k):
                setattr(props, k, v)
        obj.location = Vector((x, 0.0, 0.0))
        context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.surreal_arch.generate()
        objs.append(obj)
        x += spacing
    snap_fn = best_snap_pair
    try:
        import sys
        import os
        deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if deploy not in sys.path:
            sys.path.insert(0, deploy)
        from surreal_os import rules_engine as os_rules
        snap_fn = os_rules.best_snap_pair
    except Exception:
        pass
    for i in range(1, len(objs)):
        pair = snap_fn(monolith, objs[i], objs[i - 1])
        if pair:
            monolith._gb_apply_snap_pair(objs[i], objs[i - 1], pair)
    genome = getattr(monolith, "_active_style_genome", None)
    transform_id = None
    if genome:
        transform_id = genome.get("surreal_transform")
        if not transform_id and graph_id:
            transform_id = None
    if transform_id:
        try:
            from surreal_os import rules_engine as os_rules
            os_rules.apply_surreal_transform(objs, transform_id, genome, graph_id=graph_id)
        except Exception:
            pass
    return objs


def register_graph_operators(monolith):
    for graph_id, meta in GRAPH_REGISTRY.items():
        label = meta["label"]
        spec = meta["spec"]

        def _make_op(gid=graph_id, gspec=spec, glabel=label):
            class OT_Graph(bpy.types.Operator):
                bl_idname = f"surreal_arch.spawn_graph_{gid.lower()}"
                bl_label = f"Spawn {glabel}"
                bl_description = meta.get("description", "")
                bl_options = {"REGISTER", "UNDO"}

                def execute(self, context):
                    spacing = resolve_graph_spacing(context)
                    objs = spawn_graph(context, monolith, gspec, spacing=spacing, graph_id=gid)
                    self.report({"INFO"}, f"Spawned {len(objs)} modules ({gid}) @ {spacing:.1f}m")
                    return {"FINISHED"}

            return OT_Graph

        yield _make_op(graph_id, spec, label)
