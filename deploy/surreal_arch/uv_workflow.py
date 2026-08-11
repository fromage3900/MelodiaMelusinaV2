"""UV + trimsheet workflow — evaluated proxy for MioUV / UVPackmaster without losing GN source."""

from __future__ import annotations

import bpy


PROXY_TAG = "surreal_uv_proxy_for"
SOURCE_TAG = "surreal_uv_proxy_source"
BAKED_TAG = "surreal_arch_mesh_baked"


def evaluated_mesh_object(context, obj):
    """Return depsgraph-evaluated mesh (modifiers applied virtually)."""
    if obj is None or obj.type != "MESH":
        return None
    depsgraph = context.evaluated_depsgraph_get()
    return obj.evaluated_get(depsgraph)


def mesh_from_evaluated(context, obj):
    ev = evaluated_mesh_object(context, obj)
    if ev is None:
        return None
    depsgraph = context.evaluated_depsgraph_get()
    try:
        return bpy.data.meshes.new_from_object(ev, depsgraph=depsgraph)
    except TypeError:
        return bpy.data.meshes.new_from_object(ev)


def find_proxy_for_source(source):
    name = source.get(PROXY_TAG) if source else None
    if name:
        proxy = bpy.data.objects.get(name)
        if proxy and proxy.type == "MESH":
            return proxy
    for o in bpy.data.objects:
        if o.get(SOURCE_TAG) == source.name:
            return o
    return None


def find_source_for_proxy(proxy):
    if proxy is None:
        return None
    src_name = proxy.get(SOURCE_TAG)
    if src_name:
        return bpy.data.objects.get(src_name)
    return None


def _purge_surreal_gn_modifiers(obj):
    for mod in list(obj.modifiers):
        if mod.name.startswith("SurrealArch"):
            obj.modifiers.remove(mod)
            continue
        if mod.type == "NODES" and mod.node_group and "SurrealArch" in mod.node_group.name:
            obj.modifiers.remove(mod)


def _copy_uv_layer_by_loop_index(src_mesh, dst_mesh, uv_name):
    if uv_name not in src_mesh.uv_layers:
        return False
    src_uv = src_mesh.uv_layers[uv_name]
    if uv_name not in dst_mesh.uv_layers:
        dst_mesh.uv_layers.new(name=uv_name)
    dst_uv = dst_mesh.uv_layers[uv_name]
    if len(src_mesh.loops) != len(dst_mesh.loops):
        return False
    for i in range(len(dst_mesh.loops)):
        dst_uv.data[i].uv = src_uv.data[i].uv
    return True


def ensure_mesh_uv_layer(obj, uv_name):
    """Promote a corner-domain UV attribute to a classic UV layer if needed."""
    mesh = obj.data if obj and obj.type == "MESH" else None
    if mesh is None:
        return False
    if uv_name in mesh.uv_layers and len(mesh.uv_layers[uv_name].data) == len(mesh.loops):
        return True

    attr = mesh.attributes.get(uv_name)
    if attr is None or attr.domain != "CORNER":
        return False

    if uv_name not in mesh.uv_layers:
        layer = mesh.uv_layers.new(name=uv_name)
    else:
        layer = mesh.uv_layers.get(uv_name)
    if layer is None:
        return False

    try:
        if attr.data_type == "FLOAT2":
            for i, item in enumerate(attr.data):
                layer.data[i].uv = (item[0], item[1])
        elif attr.data_type == "FLOAT_VECTOR":
            for i, item in enumerate(attr.data):
                layer.data[i].uv = (item.vector[0], item.vector[1])
        else:
            return False
    except Exception:
        return False

    mesh.uv_layers.active = layer
    mesh.update()
    return True


def apply_export_uv(context, baked, src, props):
    """Choose UV strategy for UE export duplicate — respect lock + procedural modes."""
    if baked is None or baked.type != "MESH":
        return False

    if props is None:
        try:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=0.872665, island_margin=0.02)
            bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            if context.active_object and context.active_object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
        return True

    uv_name = getattr(props, "uv_map_name", "UVMap") or "UVMap"
    mode = getattr(props, "uv_unwrap_mode", "TRIPLANAR")
    locked = getattr(props, "uv_lock_external", False)

    ensure_mesh_uv_layer(baked, uv_name)

    if locked and ensure_mesh_uv_layer(baked, uv_name):
        return True
    if locked and src and src.type == "MESH":
        if _copy_uv_layer_by_loop_index(src.data, baked.data, uv_name):
            return True

    if mode == "SMART":
        import surreal_architecture_gen as monolith

        old_mode = props.uv_unwrap_mode
        props.uv_unwrap_mode = "SMART"
        try:
            monolith.apply_smart_uv_unwrap(baked, props, context)
        finally:
            props.uv_unwrap_mode = old_mode
        return True

    if mode in ("TRIPLANAR", "BOX", "TRIM_SHEET"):
        if ensure_mesh_uv_layer(baked, uv_name):
            return True
        if getattr(props, "auto_uv_unwrap", True):
            ensure_mesh_uv_layer(baked, uv_name)
        return True

    return ensure_mesh_uv_layer(baked, uv_name)


def create_uv_edit_proxy(context, source, *, apply_modifiers=True, name_suffix="_UVEdit"):
    """Duplicate evaluated geometry for external UV tools (non-destructive on source)."""
    if source is None or source.type != "MESH":
        return None, "Select a mesh object"

    existing = find_proxy_for_source(source)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    me = mesh_from_evaluated(context, source)
    if me is None:
        return None, "Could not evaluate mesh"

    proxy_name = source.name + name_suffix
    if proxy_name in bpy.data.objects:
        i = 1
        while f"{proxy_name}.{i:03d}" in bpy.data.objects:
            i += 1
        proxy_name = f"{proxy_name}.{i:03d}"

    proxy = bpy.data.objects.new(proxy_name, me)
    context.collection.objects.link(proxy)
    proxy.matrix_world = source.matrix_world.copy()
    proxy[SOURCE_TAG] = source.name
    source[PROXY_TAG] = proxy.name

    props = getattr(source, "surreal_arch_props", None)
    if props:
        uv_name = getattr(props, "uv_map_name", "UVMap") or "UVMap"
        ensure_mesh_uv_layer(proxy, uv_name)
        layer = proxy.data.uv_layers.get(uv_name)
        if layer is None:
            layer = proxy.data.uv_layers.new(name=uv_name)
        proxy.data.uv_layers.active = layer

    if apply_modifiers:
        context.view_layer.objects.active = proxy
        proxy.select_set(True)
        for mod in list(proxy.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                try:
                    proxy.modifiers.remove(mod)
                except Exception:
                    pass

    return proxy, f"UV edit proxy: {proxy.name}"


def commit_uv_from_proxy(context, source, proxy, uv_name=None, bake_geometry=None):
    """
    Copy UV from proxy onto source.

    When topology differs (live GN on a cube base), bake proxy mesh onto source and
    remove the SurrealArch GN modifier so UV layers are valid for export.
    """
    if source is None or proxy is None:
        return False, "Missing source or proxy"
    if proxy.type != "MESH" or source.type != "MESH":
        return False, "Source and proxy must be meshes"

    props = getattr(source, "surreal_arch_props", None)
    if uv_name is None:
        uv_name = getattr(props, "uv_map_name", "UVMap") if props else "UVMap"
    uv_name = uv_name or "UVMap"

    topology_match = len(source.data.loops) == len(proxy.data.loops)
    if bake_geometry is None:
        bake_geometry = not topology_match

    if bake_geometry and not topology_match:
        new_me = proxy.data.copy()
        old_me = source.data
        source.data = new_me
        if old_me and old_me.users == 0:
            bpy.data.meshes.remove(old_me)

        _purge_surreal_gn_modifiers(source)

        if props is not None:
            props.uv_lock_external = True
            props.auto_uv_unwrap = False
            props.uv_unwrap_mode = "NONE"

        source[BAKED_TAG] = True
        if PROXY_TAG in source:
            del source[PROXY_TAG]
        bpy.data.objects.remove(proxy, do_unlink=True)
        source.data.update()
        return True, (
            f"Baked mesh + UV committed on '{source.name}' "
            "(GN removed — duplicate before Regenerate if you need parametric source)"
        )

    p_uv = proxy.data.uv_layers.get(uv_name) or proxy.data.uv_layers.active
    if p_uv is None:
        ensure_mesh_uv_layer(proxy, uv_name)
        p_uv = proxy.data.uv_layers.get(uv_name) or proxy.data.uv_layers.active
    if p_uv is None:
        return False, f"Proxy has no UV layer '{uv_name}'"

    if not topology_match:
        return False, (
            "Topology mismatch — regenerate proxy after changing Surreal parameters"
        )

    if uv_name not in source.data.uv_layers:
        source.data.uv_layers.new(name=uv_name)
    s_uv = source.data.uv_layers.get(uv_name)
    if s_uv is None:
        return False, f"Source has no UV layer '{uv_name}'"

    for i, _loop in enumerate(proxy.data.loops):
        s_uv.data[i].uv = p_uv.data[i].uv

    if props is not None:
        props.uv_lock_external = True
        props.uv_unwrap_mode = "NONE"

    source.data.update()
    return True, f"Committed '{uv_name}' from {proxy.name} (UV locked on source)"


def remove_uv_proxy(context, source):
    proxy = find_proxy_for_source(source)
    if proxy:
        bpy.data.objects.remove(proxy, do_unlink=True)
    if PROXY_TAG in source:
        del source[PROXY_TAG]
    return True


ZEN_WOOD_TYPES = frozenset({
    "GB_ZEN_ENGAWA", "GB_ZEN_BAMBOO_FENCE", "GB_ZEN_MACHIAI",
    "GB_ZEN_SHOIN", "GB_ZEN_KURI", "GB_ZEN_KYAKUDEN",
    "ZEN_SHOJI", "ZEN_TEAHOUSE",
})


def zen_module_uv_defaults(arch_type):
    """Trimsheet-friendly defaults for zen greybox modules."""
    if not (arch_type.startswith("GB_ZEN") or arch_type.startswith("ZEN_")):
        return {}
    base = dict(
        gb_trim_mode="RECESS",
        gb_bake_trim_colors=True,
        auto_uv_unwrap=True,
    )
    if arch_type in ZEN_WOOD_TYPES:
        return {
            **base,
            "uv_unwrap_mode": "BOX",
            "uv_scale": 0.5,
            "gb_trim_recess": 0.04,
        }
    return {
        **base,
        "uv_unwrap_mode": "TRIM_SHEET",
        "uv_scale": 1.0,
        "trim_sheet_atlas_cols": 4,
        "trim_sheet_body_scale": 0.88,
        "gb_trim_recess": 0.04,
    }


def apply_trim_preset(props, preset_id):
    """One-click trim + UV defaults for trimsheet-friendly greybox."""
    presets = {
        "ARCHITECTURAL": dict(
            gb_trim_mode="RECESS",
            gb_trim_recess=0.06,
            gb_wainscot_height=0.35,
            gb_baseboard_height=0.12,
            uv_unwrap_mode="TRIM_SHEET",
            uv_scale=1.0,
            trim_sheet_atlas_cols=4,
            gb_bake_trim_colors=True,
            unit_size=3.2,
        ),
        "MODULAR_TILE": dict(
            gb_trim_mode="RECESS",
            gb_trim_recess=0.04,
            gb_wainscot_height=0.0,
            gb_baseboard_height=0.1,
            uv_unwrap_mode="BOX",
            uv_scale=1.0,
            gb_bake_trim_colors=True,
            unit_size=2.0,
        ),
        "SCI_FI_PANEL": dict(
            gb_trim_mode="RECESS",
            gb_trim_recess=0.08,
            gb_wainscot_height=0.0,
            gb_baseboard_height=0.15,
            uv_unwrap_mode="TRIPLANAR",
            uv_scale=0.5,
            gb_bake_trim_colors=True,
            unit_size=4.0,
        ),
        "ZEN_WOOD": dict(
            gb_trim_mode="RECESS",
            gb_trim_recess=0.04,
            gb_wainscot_height=0.0,
            gb_baseboard_height=0.08,
            uv_unwrap_mode="BOX",
            uv_scale=0.5,
            gb_bake_trim_colors=True,
            unit_size=2.0,
            material_choice="WOOD",
        ),
        "ZEN_STONE": dict(
            gb_trim_mode="RECESS",
            gb_trim_recess=0.04,
            gb_wainscot_height=0.0,
            gb_baseboard_height=0.0,
            uv_unwrap_mode="TRIM_SHEET",
            uv_scale=1.0,
            trim_sheet_atlas_cols=4,
            trim_sheet_body_scale=0.9,
            gb_bake_trim_colors=True,
            unit_size=2.0,
            material_choice="STONE",
        ),
    }
    spec = presets.get(preset_id)
    if not spec:
        return False
    for k, v in spec.items():
        if hasattr(props, k):
            setattr(props, k, v)
    return True
