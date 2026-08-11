"""Topology-driven world composer — COLLECTION (default) or JOINED legacy mode."""

from __future__ import annotations

import math

import bpy

from . import instance, library, tags

_OS_COMPOSE_CACHE: dict | None = None


def _load_os_compose_styles() -> dict:
    global _OS_COMPOSE_CACHE
    if _OS_COMPOSE_CACHE is not None:
        return _OS_COMPOSE_CACHE
    try:
        import sys
        import os
        deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if deploy not in sys.path:
            sys.path.insert(0, deploy)
        from surreal_os.rules_engine import load_compose_styles
        _OS_COMPOSE_CACHE = load_compose_styles()
    except Exception:
        _OS_COMPOSE_CACHE = {}
    return _OS_COMPOSE_CACHE


def resolve_compose_style(monolith, style_key: str) -> dict | None:
    """Merge hardcoded COMPOSE_STYLES with surreal_os compose_roles + genome override."""
    base = dict(COMPOSE_STYLES.get(style_key) or {})
    os_styles = _load_os_compose_styles()
    if style_key in os_styles:
        base.update(os_styles[style_key])
    genome = getattr(monolith, "_active_style_genome", None)
    if genome and genome.get("compose_style") == style_key:
        role_map = genome.get("compose_roles")
        if isinstance(role_map, dict):
            base.update(role_map)
    return base if base else None


COMPOSE_STYLES = {
    "WESTERN_CASTLE": {
        "large": "_lib_KEEP",
        "medium": "_lib_TOWN_HOUSE",
        "small": "_lib_MARKET_STALL",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_WATCHTOWER",
        "gate": "_lib_GATEHOUSE",
        "monument": "_lib_OBELISK",
        "sacred": "_lib_CHAPEL",
    },
    "WESTERN_VILLAGE": {
        "large": "_lib_TOWN_HALL",
        "medium": "_lib_TAVERN",
        "small": "_lib_BLACKSMITH",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_GATEHOUSE",
        "monument": "_lib_VILLAGE_WELL",
        "sacred": "_lib_CHAPEL",
    },
    "ASIAN_CITY": {
        "large": "_lib_KR_HANOK",
        "medium": "_lib_CN_TING_PAVILION",
        "small": "_lib_JP_KURA_STOREHOUSE",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_CN_TIERED_PAGODA",
        "gate": "_lib_CN_PAILOU",
        "monument": "_lib_CN_MOON_GATE",
        "sacred": "_lib_CN_TIERED_PAGODA",
    },
    "ASIAN_CITY_RECURSIVE": {
        "large": "_lib_KR_HANOK",
        "medium": "_lib_JP_KURA_STOREHOUSE",
        "small": "_lib_CN_TING_PAVILION",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_CN_TIERED_PAGODA",
        "gate": "_lib_CN_PAILOU",
        "monument": "_lib_CN_MOON_GATE",
        "sacred": "_lib_CN_TIERED_PAGODA",
    },
    "ZEN_SHRINE": {
        "large": "_lib_GB_ZEN_MACHIAI",
        "medium": "_lib_GB_ZEN_KARESANSUI",
        "small": "_lib_GB_ZEN_LANTERN",
        "wall": "_lib_GB_ZEN_CHERRY_ALLEE",
        "corner_tower": "_lib_GB_ZEN_GOJU_PAGODA",
        "gate": "_lib_GB_ZEN_TORII_GATE",
        "monument": "_lib_GB_ZEN_TAHOTO",
        "sacred": "_lib_GB_ZEN_HONDEN",
    },
    "ART_NOUVEAU": {
        "large": "_lib_BAROQUE_FACADE",
        "medium": "_lib_BALCONY",
        "small": "_lib_FILIGREE_PANEL",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_OGEE_ARCH",
        "monument": "_lib_PUBLIC_FOUNTAIN",
        "sacred": "_lib_CHAPEL",
    },
    "ART_DECO": {
        "large": "_lib_TESSELLATION_TOWER",
        "medium": "_lib_GB_BRUTALIST_PANEL_WALL",
        "small": "_lib_FILIGREE_PANEL",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_TESSELLATION_TOWER",
        "gate": "_lib_CUSPED_ARCH",
        "monument": "_lib_OBELISK",
        "sacred": "_lib_PUBLIC_FOUNTAIN",
    },
    "MOORISH_COURTYARD": {
        "large": "_lib_PALAZZO",
        "medium": "_lib_GB_ROMANESQUE_ARCADE",
        "small": "_lib_FILIGREE_PANEL",
        "wall": "_lib_CURVED_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_ARCHWAY_ADV",
        "monument": "_lib_PUBLIC_FOUNTAIN",
        "sacred": "_lib_CHAPEL",
    },
    "RENAISSANCE_PIAZZA": {
        "large": "_lib_BAROQUE_FACADE",
        "medium": "_lib_GB_ROMANESQUE_ARCADE",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_ARCHWAY_ADV",
        "monument": "_lib_PUBLIC_FOUNTAIN",
        "sacred": "_lib_DOME",
    },
    "VENETIAN_CANAL": {
        "large": "_lib_PALAZZO",
        "medium": "_lib_GB_VENETIAN_LOGGIA",
        "small": "_lib_BIFORA",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_BRIDGE",
        "monument": "_lib_PUBLIC_FOUNTAIN",
        "sacred": "_lib_CHAPEL",
    },
    "GOTHIC_CLOISTER": {
        "large": "_lib_CHAPEL",
        "medium": "_lib_GREYBOX_CORRIDOR",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_GB_GOTHIC_PORTAL",
        "monument": "_lib_BELL_TOWER",
        "sacred": "_lib_CHAPEL",
    },
    "GOTHIC_CHAPTER_HOUSE": {
        "large": "_lib_CHAPEL",
        "medium": "_lib_GREYBOX_CORRIDOR",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_GB_GOTHIC_PORTAL",
        "monument": "_lib_BELL_TOWER",
        "sacred": "_lib_CHAPEL",
    },
    "GOTHIC_NAVE_CROSSING": {
        "large": "_lib_CHAPEL",
        "medium": "_lib_GREYBOX_CORRIDOR",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_GB_GOTHIC_PORTAL",
        "monument": "_lib_ROSE_WINDOW",
        "sacred": "_lib_CHAPEL",
    },
    "ROMANESQUE_CLOISTER": {
        "large": "_lib_CHAPEL",
        "medium": "_lib_GB_ROMANESQUE_ARCADE",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_GATEHOUSE",
        "monument": "_lib_BELL_TOWER",
        "sacred": "_lib_CHAPEL",
    },
    "ROMANESQUE_APSE": {
        "large": "_lib_BELL_TOWER",
        "medium": "_lib_GB_ROMANESQUE_ARCADE",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_GATEHOUSE",
        "monument": "_lib_BELL_TOWER",
        "sacred": "_lib_GB_ROMANESQUE_APSE",
    },
    "SCIFI_DECK": {
        "large": "_lib_GREYBOX_PILLAR_HALL",
        "medium": "_lib_GREYBOX_CORRIDOR",
        "small": "_lib_GREYBOX_CATWALK",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_WATCHTOWER",
        "gate": "_lib_GB_SCIFI_PRESSURE_DOOR",
        "monument": "_lib_GREYBOX_ROOM",
        "sacred": "_lib_GREYBOX_ROOM",
    },
    "BYZANTINE_BASILICA": {
        "large": "_lib_BAROQUE_VAULT",
        "medium": "_lib_GB_ROMANESQUE_ARCADE",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_CUSPED_ARCH",
        "monument": "_lib_ROSE_WINDOW",
        "sacred": "_lib_DOME",
    },
    "BAROQUE_CHURCH": {
        "large": "_lib_BAROQUE_FACADE",
        "medium": "_lib_BAROQUE_VAULT",
        "small": "_lib_BAROQUE_BALUSTRADE",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_BELL_TOWER",
        "gate": "_lib_OGEE_ARCH",
        "monument": "_lib_BAROQUE_NICHE",
        "sacred": "_lib_DOME",
    },
    "BRUTALIST_PLAZA": {
        "large": "_lib_GREYBOX_PILLAR_HALL",
        "medium": "_lib_GB_BRUTALIST_PANEL_WALL",
        "small": "_lib_PILLAR",
        "wall": "_lib_CURTAIN_WALL",
        "corner_tower": "_lib_WATCHTOWER",
        "gate": "_lib_GATEHOUSE",
        "monument": "_lib_PUBLIC_FOUNTAIN",
        "sacred": "_lib_CHAPEL",
    },
}

ROLE_MATERIALS = {
    "WESTERN_CASTLE": {
        "large": "Wood", "medium": "Wood", "small": "Wood",
        "wall": "Voronoi Shader (Flat)", "corner_tower": "Voronoi Shader (3 Tones)",
        "gate": "Tree Shader *", "monument": "Voronoi Shader (3 Tones)", "sacred": "Tree Shader *",
    },
    "ZEN_SHRINE": {
        "large": "Wood", "medium": "Wood", "small": "Wood",
        "wall": "Voronoi Shader (Flat)", "corner_tower": "Wood",
        "gate": "Wood", "monument": "Water (Basic)", "sacred": "Tree Shader *",
    },
}


def resolve_role_materials(monolith, style_key):
    spec = ROLE_MATERIALS.get(style_key, ROLE_MATERIALS.get("WESTERN_CASTLE", {}))
    out = {}
    komikaze = getattr(monolith, "_komikaze_link", None)
    for role, mat_name in spec.items():
        out[role] = komikaze(mat_name, link=False) if komikaze else None
    return out


def _meta(plan_obj, style_key, role, lib_name, plan_face=-1):
    return {
        "role": role,
        "style_key": style_key,
        "lib_name": lib_name,
        "plan_name": plan_obj.name,
        "plan_face": plan_face,
    }


def compose_world(
    monolith,
    context,
    plan_obj,
    style_key="WESTERN_CASTLE",
    detail_scale=1.0,
    compose_mode="COLLECTION",
):
    style = resolve_compose_style(monolith, style_key)
    if style is None:
        return None, f"Unknown style: {style_key}"
    if library.library_collection(create=False) is None:
        return None, "Library not initialized — run library_init first"

    instance.clear_composed_world(plan_obj)
    out_coll_name = f"{plan_obj.name}_Composed"
    out_coll = bpy.data.collections.get(out_coll_name)
    if out_coll is None:
        out_coll = bpy.data.collections.new(out_coll_name)
        context.scene.collection.children.link(out_coll)
    else:
        for o in list(out_coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)

    world_root = instance.create_instance_root(plan_obj, style_key) if compose_mode == "COLLECTION" else None
    if world_root:
        genome = getattr(monolith, "_active_style_genome", None)
        if genome and genome.get("id"):
            world_root["surreal_style_genome_id"] = genome["id"]
        elif style_key == "ZEN_SHRINE":
            world_root["surreal_style_genome_id"] = "zen_shrine_v1"
        elif style_key == "ASIAN_CITY":
            world_root["surreal_style_genome_id"] = "asian_city_v1"
        elif style_key == "ASIAN_CITY_RECURSIVE":
            world_root["surreal_style_genome_id"] = "asian_city_recursive_v1"
        elif style_key == "WESTERN_CASTLE":
            world_root["surreal_style_genome_id"] = "western_castle_v1"
        elif style_key == "ART_DECO":
            world_root["surreal_style_genome_id"] = "art_deco_lobby_v1"
        elif style_key == "ART_NOUVEAU":
            world_root["surreal_style_genome_id"] = "art_nouveau_v1"
        elif style_key == "MOORISH_COURTYARD":
            world_root["surreal_style_genome_id"] = "moorish_courtyard_v1"
        elif style_key == "RENAISSANCE_PIAZZA":
            world_root["surreal_style_genome_id"] = "renaissance_piazza_v1"
        elif style_key == "VENETIAN_CANAL":
            world_root["surreal_style_genome_id"] = "venetian_canal_v1"
        elif style_key == "GOTHIC_CLOISTER":
            world_root["surreal_style_genome_id"] = "gothic_cloister_v1"
        elif style_key == "GOTHIC_CHAPTER_HOUSE":
            world_root["surreal_style_genome_id"] = "gothic_chapter_house_v1"
        elif style_key == "GOTHIC_NAVE_CROSSING":
            world_root["surreal_style_genome_id"] = "gothic_nave_crossing_v1"
        elif style_key == "ROMANESQUE_CLOISTER":
            world_root["surreal_style_genome_id"] = "romanesque_cloister_v1"
        elif style_key == "ROMANESQUE_APSE":
            world_root["surreal_style_genome_id"] = "romanesque_apse_v1"
        elif style_key == "SCIFI_DECK":
            world_root["surreal_style_genome_id"] = "scifi_deck_v1"
        elif style_key == "BYZANTINE_BASILICA":
            world_root["surreal_style_genome_id"] = "byzantine_basilica_v1"
        elif style_key == "BAROQUE_CHURCH":
            world_root["surreal_style_genome_id"] = "baroque_church_v1"
        elif style_key == "BRUTALIST_PLAZA":
            world_root["surreal_style_genome_id"] = "brutalist_plaza_v1"
        try:
            if world_root not in list(out_coll.objects):
                out_coll.objects.link(world_root)
        except Exception:
            pass
    libs = {role: bpy.data.objects.get(name) for role, name in style.items()}
    role_mats = resolve_role_materials(monolith, style_key)
    spawned = []
    me = plan_obj.data
    plan_mat = plan_obj.matrix_world

    if len(me.polygons) > 0:
        areas = [f.area for f in me.polygons]
        max_area = max(areas) if areas else 1.0

        def area_role(face):
            a = face.area
            if a > max_area * 0.7:
                return "large"
            if a > max_area * 0.35:
                return "medium"
            return "small"

        for fi, face in enumerate(me.polygons):
            world_center = plan_mat @ face.center
            role = tags.face_role_from_tags(plan_obj, face, area_role)
            lib = libs.get(role)
            if lib is None:
                continue
            face_radius = math.sqrt(face.area) / 4.0
            inst_scale = max(0.4, face_radius) * detail_scale
            rot_z = math.atan2(world_center.y, world_center.x) + math.pi / 2
            new_obj = instance.instance_library_piece(
                lib,
                world_center,
                rot_z,
                inst_scale,
                link_to_coll=out_coll,
                name_hint="bld",
                material=role_mats.get(role),
                parent=world_root,
                metadata=_meta(plan_obj, style_key, role, lib.name, fi),
            )
            if new_obj:
                spawned.append(new_obj)

    edge_face_count = {tuple(sorted(e.vertices)): 0 for e in me.edges}
    for f in me.polygons:
        for i in range(len(f.vertices)):
            a = f.vertices[i]
            b = f.vertices[(i + 1) % len(f.vertices)]
            key = tuple(sorted((a, b)))
            if key in edge_face_count:
                edge_face_count[key] += 1
    boundary = [k for k, n in edge_face_count.items() if n == 1]
    wall_lib = libs.get("wall")
    if wall_lib is not None and boundary:
        for (a, b) in boundary:
            wa = plan_mat @ me.vertices[a].co
            wb = plan_mat @ me.vertices[b].co
            mid = (wa + wb) * 0.5
            length = (wb - wa).length
            if length < 0.5:
                continue
            rot_z = math.atan2(wb.y - wa.y, wb.x - wa.x)
            sx = (length / 4.0) * detail_scale
            new_obj = instance.instance_library_piece(
                wall_lib,
                mid,
                rot_z,
                scale=1.0,
                scale_xyz=(sx, detail_scale, detail_scale),
                link_to_coll=out_coll,
                name_hint="wall",
                material=role_mats.get("wall"),
                parent=world_root,
                metadata=_meta(plan_obj, style_key, "wall", wall_lib.name),
            )
            if new_obj:
                spawned.append(new_obj)

    tower_lib = libs.get("corner_tower")
    gate_lib = libs.get("gate")
    if tower_lib is not None or gate_lib is not None:
        for vi, _v in enumerate(me.vertices):
            wpos = plan_mat @ me.vertices[vi].co
            if gate_lib and tags.vertex_in_group(plan_obj, vi, "is_gate"):
                new_obj = instance.instance_library_piece(
                    gate_lib,
                    wpos,
                    0.0,
                    detail_scale,
                    link_to_coll=out_coll,
                    name_hint="gate",
                    material=role_mats.get("gate"),
                    parent=world_root,
                    metadata=_meta(plan_obj, style_key, "gate", gate_lib.name),
                )
                if new_obj:
                    spawned.append(new_obj)
                continue
            if tower_lib and tags.vertex_in_group(plan_obj, vi, "is_corner_tower"):
                new_obj = instance.instance_library_piece(
                    tower_lib,
                    wpos,
                    0.0,
                    detail_scale,
                    link_to_coll=out_coll,
                    name_hint="twr",
                    material=role_mats.get("corner_tower"),
                    parent=world_root,
                    metadata=_meta(plan_obj, style_key, "corner_tower", tower_lib.name),
                )
                if new_obj:
                    spawned.append(new_obj)

    if not spawned:
        return None, "No instances placed — check plan faces and library init"

    if compose_mode == "COLLECTION":
        if world_root:
            world_root["surreal_instance_count"] = len(spawned)
        bpy.ops.object.select_all(action="DESELECT")
        if world_root:
            world_root.select_set(True)
            context.view_layer.objects.active = world_root
        return world_root, f"Composed {plan_obj.name} with {len(spawned)} instances (COLLECTION)"

    for o in context.view_layer.objects:
        try:
            o.select_set(False)
        except Exception:
            pass
    mesh_objs = []
    for root in spawned:
        for ch in root.children:
            if ch.type == "MESH":
                mesh_objs.append(ch)
    for o in mesh_objs:
        o.select_set(True)
    context.view_layer.objects.active = mesh_objs[0]
    try:
        with context.temp_override(
            active_object=mesh_objs[0],
            selected_objects=mesh_objs,
            selected_editable_objects=mesh_objs,
        ):
            bpy.ops.object.join()
    except Exception as e:
        return mesh_objs[0], f"Joined partially ({len(mesh_objs)} pieces, error: {e})"
    joined = context.view_layer.objects.active
    joined.name = f"{plan_obj.name}_World"
    joined["surreal_composed_from"] = plan_obj.name
    joined["surreal_compose_style"] = style_key
    joined["surreal_compose_mode"] = "JOINED"
    for c in list(joined.users_collection):
        c.objects.unlink(joined)
    context.scene.collection.objects.link(joined)
    return joined, f"Composed {plan_obj.name} with {len(spawned)} instances (JOINED)"


def recompose_world(monolith, context, obj, detail_scale=1.0, compose_mode="COLLECTION"):
    src_name = obj.get("surreal_composed_from")
    style = obj.get("surreal_compose_style", "WESTERN_CASTLE")
    mode = obj.get("surreal_compose_mode", compose_mode)
    if src_name:
        plan = bpy.data.objects.get(src_name)
        if plan is None:
            return None, f"Source plan '{src_name}' missing"
        if obj.type != "MESH" or obj.get("surreal_compose_mode") == "JOINED":
            if obj.name != plan.name:
                bpy.data.objects.remove(obj, do_unlink=True)
    else:
        plan = obj
    return compose_world(monolith, context, plan, style, detail_scale, compose_mode=mode)
