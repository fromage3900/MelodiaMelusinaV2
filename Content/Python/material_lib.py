"""Shared helpers for BS_GodFile material Python builders."""
from __future__ import annotations

import unreal

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
FUNCTION_DIR = f"{MATERIALS_ROOT}/Functions"
PROFILE_DIR = f"{MATERIALS_ROOT}/ToonProfiles"
MASTER_DIR = f"{MATERIALS_ROOT}/Masters"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"
ENV_INST_DIR = f"{MATERIALS_ROOT}/Instances/Environment"
POST_DIR = f"{MATERIALS_ROOT}/PostProcess"

# Post-process materials must sample PPI_POST_PROCESS_INPUT0, not PPI_SCENE_COLOR.
PP_SCENE_TEXTURE = "PPI_POST_PROCESS_INPUT0"


def post_process_scene_texture_id():
    return getattr(unreal.SceneTextureId, PP_SCENE_TEXTURE)


def clear_material_graph(material) -> None:
    try:
        for expr in list(unreal.MaterialEditingLibrary.get_material_expressions(material) or []):
            unreal.MaterialEditingLibrary.delete_material_expression(material, expr)
    except Exception as exc:
        unreal.log_warning(f"[material_lib] clear graph: {exc}")


def mask_rgb(owner, from_expr, x: int, y: int):
    mask = create_expression(owner, unreal.MaterialExpressionComponentMask, x, y)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", True)
    mask.set_editor_property("b", True)
    mask.set_editor_property("a", False)
    connect(from_expr, "", mask, "")
    return mask
MPC_DIR = f"{MATERIALS_ROOT}/Functions"


def ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def asset_class_name(asset_data) -> str:
    """Short asset class from EditorAssetLibrary.find_asset_data (UE 5.8 safe)."""
    if not asset_data:
        return ""
    try:
        cls = asset_data.asset_class
        if cls is None:
            return ""
        if hasattr(cls, "get_asset_name"):
            name = cls.get_asset_name()
            if name:
                return str(name)
        text = str(cls)
        if "MaterialInstanceConstant" in text:
            return "MaterialInstanceConstant"
        if "MaterialFunction" in text:
            return "MaterialFunction"
        if "Material" in text:
            return "Material"
        if "." in text:
            return text.rsplit(".", 1)[-1].rstrip("'")
        return text
    except Exception:
        return ""


def list_path_stem(list_path: str) -> str:
    return list_path.rsplit("/", 1)[-1].split(".", 1)[0]


def load_asset_from_list_path(list_path: str):
    stem = list_path_stem(list_path)
    base = list_path.split(".", 1)[0]
    return unreal.load_asset(f"{base}.{stem}")


def asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def save_package(asset) -> None:
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)


def try_set_editor_property(obj, name: str, value) -> None:
    try:
        if hasattr(obj, "has_editor_property") and obj.has_editor_property(name):
            obj.set_editor_property(name, value)
    except Exception:
        pass


def create_expression(owner, expression_class, x: int, y: int):
    if isinstance(owner, unreal.MaterialFunction):
        return unreal.MaterialEditingLibrary.create_material_expression_in_function(
            owner, expression_class, x, y
        )
    return unreal.MaterialEditingLibrary.create_material_expression(
        owner, expression_class, x, y
    )


def _owner_material(expr):
    try:
        return expr.get_outer()
    except Exception:
        return None


def _modify_expression_owner(expr) -> None:
    try:
        outer = expr.get_outer()
        while outer:
            if isinstance(outer, (unreal.Material, unreal.MaterialFunction)):
                outer.modify()
                return
            outer = outer.get_outer() if hasattr(outer, "get_outer") else None
    except Exception:
        pass


def _param_name(expr) -> str | None:
    for prop in ("parameter_name", "ParameterName"):
        try:
            raw = expr.get_editor_property(prop)
            if raw is not None:
                return str(raw)
        except Exception:
            continue
    return None


def iter_parameter_expressions(root):
    """Yield parameter expressions under a material graph (incl. nested functions)."""
    visited: set[str] = set()
    pending = [root]

    while pending:
        owner = pending.pop()
        if isinstance(owner, unreal.Material):
            exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(owner) or [])
        elif isinstance(owner, unreal.MaterialFunction):
            key = owner.get_path_name().split(".", 1)[0]
            if key in visited:
                continue
            visited.add(key)
            try:
                exprs = list(unreal.MaterialEditingLibrary.get_material_function_expressions(owner) or [])
            except Exception:
                exprs = []
        else:
            continue

        for expr in exprs:
            if not expr:
                continue
            tname = type(expr).__name__
            if "Parameter" in tname and "Function" not in tname:
                yield expr, owner
            elif tname == "MaterialExpressionMaterialFunctionCall":
                mf = None
                try:
                    mf = expr.get_editor_property("material_function")
                except Exception:
                    pass
                if mf:
                    pending.append(mf)


def iter_texture_parameter_expressions(root):
    """Yield (expression, owner) for texture parameter nodes under a material graph."""
    visited: set[str] = set()
    pending = [root]

    while pending:
        owner = pending.pop()
        if isinstance(owner, unreal.Material):
            exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(owner) or [])
        elif isinstance(owner, unreal.MaterialFunction):
            key = owner.get_path_name().split(".", 1)[0]
            if key in visited:
                continue
            visited.add(key)
            try:
                exprs = list(unreal.MaterialEditingLibrary.get_material_function_expressions(owner) or [])
            except Exception:
                exprs = []
        else:
            continue

        for expr in exprs:
            if not expr:
                continue
            tname = type(expr).__name__
            if "Texture" in tname and "Parameter" in tname:
                yield expr, owner
            elif tname == "MaterialExpressionMaterialFunctionCall":
                mf = None
                try:
                    mf = expr.get_editor_property("material_function")
                except Exception:
                    pass
                if mf:
                    pending.append(mf)


def texture_parameter_names(material) -> list[str]:
    """Texture parameter names exposed by a material (graph + layers)."""
    names: list[str] = []
    me = unreal.MaterialEditingLibrary
    if hasattr(me, "get_texture_parameter_names"):
        try:
            for raw in me.get_texture_parameter_names(material) or []:
                names.append(str(raw))
        except Exception:
            pass
    if names:
        return names
    seen: set[str] = set()
    for expr, _owner in iter_texture_parameter_expressions(material):
        pname = None
        for prop in ("parameter_name", "ParameterName"):
            try:
                raw = expr.get_editor_property(prop)
                if raw is not None:
                    pname = str(raw)
                    break
            except Exception:
                continue
        if pname:
            seen.add(pname)
    return sorted(seen)


def connect(from_expr, from_output: str, to_expr, to_input: str) -> bool:
    try:
        result = unreal.MaterialEditingLibrary.connect_material_expressions(
            from_expr, from_output, to_expr, to_input
        )
        # UE Python often returns None on success; only explicit False is failure.
        return result is not False
    except Exception:
        return False


def _verify_input(to_expr, from_expr, pin: str) -> bool:
    material = _owner_material(to_expr)
    if not material:
        return True
    try:
        pin_names = list(
            unreal.MaterialEditingLibrary.get_material_expression_input_names(to_expr)
        )
        if pin in pin_names:
            idx = pin_names.index(pin)
        elif pin in ("", "None"):
            idx = 0
        else:
            return True
        wired = list(
            unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
                material, to_expr
            )
        )
        if idx < len(wired):
            return wired[idx] == from_expr
    except Exception:
        pass
    return True


def connect_any(from_expr, to_expr, pin_names: tuple[str, ...], from_output: str = "") -> bool:
    seen: set[str] = set()
    for pin in pin_names:
        if pin in seen:
            continue
        seen.add(pin)
        if connect(from_expr, from_output, to_expr, pin) and _verify_input(
            to_expr, from_expr, pin
        ):
            return True
    return False


def _connect_input_prop(to_expr, prop_name: str, from_expr) -> bool:
    try:
        prop = to_expr.get_editor_property(prop_name)
        prop.connect(0, from_expr)
        material = _owner_material(to_expr)
        if material:
            material.modify()
        return True
    except Exception:
        return False


def connect_unary(from_expr, to_expr) -> bool:
    """Wire single-input nodes (Sine/Abs/OneMinus/Frac/etc.) using UE 5.8 pin names."""
    pin_names: list[str] = []
    try:
        pin_names = list(
            unreal.MaterialEditingLibrary.get_material_expression_input_names(to_expr)
        )
    except Exception:
        pass
    if connect_any(
        from_expr, to_expr, tuple(pin_names) + ("None", "", "input", "Input")
    ):
        return True
    for prop in ("input", "Input"):
        if _connect_input_prop(to_expr, prop, from_expr):
            return True
    return False


def connect_append2(a_expr, b_expr, append_expr) -> bool:
    """Append two scalars or vectors (AppendVector A/B pins in UE 5.8)."""
    ok_a = connect_any(a_expr, append_expr, ("A", "a", "Input0", "R", "r"))
    ok_b = connect_any(b_expr, append_expr, ("B", "b", "Input1", "G", "g"))
    return ok_a and ok_b


def connect_append3_from_scalars(r_expr, g_expr, b_expr, owner, x: int, y: int):
    """Build float3 from three scalar expressions via nested AppendVector."""
    rg = create_expression(owner, unreal.MaterialExpressionAppendVector, x, y)
    connect_append2(r_expr, g_expr, rg)
    rgb = create_expression(owner, unreal.MaterialExpressionAppendVector, x + 160, y)
    connect_append2(rg, b_expr, rgb)
    return rgb


def connect_function_input(from_expr, call_expr, *pin_names: str) -> bool:
    """Wire an input on MaterialExpressionMaterialFunctionCall."""
    return connect_any(from_expr, call_expr, pin_names)


def connect_static_switch(switch_expr, true_expr, false_expr) -> bool:
    """Wire both branches of a MaterialExpressionStaticSwitchParameter."""
    # UE 5.8 exposes True/False — A/B are compile-time labels only, not connectable pins.
    ok_true = connect_any(true_expr, switch_expr, ("True", "Yes", "a", "A"))
    ok_false = connect_any(false_expr, switch_expr, ("False", "No", "b", "B"))
    if ok_true and ok_false:
        return True
    if not ok_true:
        ok_true = _connect_input_prop(switch_expr, "a", true_expr) or _connect_input_prop(
            switch_expr, "A", true_expr
        )
    if not ok_false:
        ok_false = _connect_input_prop(switch_expr, "b", false_expr) or _connect_input_prop(
            switch_expr, "B", false_expr
        )
    return ok_true and ok_false


def connect_front_material(material, from_expr, from_output: str = "") -> None:
    unreal.MaterialEditingLibrary.connect_material_property(
        from_expr,
        from_output,
        unreal.MaterialProperty.MP_FRONT_MATERIAL,
    )


def connect_toon_pin(toon_bsdf, expr, pin_names: tuple[str, ...]) -> bool:
    for pin in pin_names:
        if connect(expr, "", toon_bsdf, pin):
            return True
    return False


def _set_param_desc(expr, desc: str | None) -> None:
    if not desc:
        return
    for prop in ("desc", "Desc", "parameter_desc"):
        try:
            if hasattr(expr, "has_editor_property") and expr.has_editor_property(prop):
                expr.set_editor_property(prop, desc)
                return
        except Exception:
            continue


def scalar_param(
    owner,
    name: str,
    group: str,
    default: float,
    x: int,
    y: int,
    *,
    desc: str | None = None,
):
    expr = create_expression(owner, unreal.MaterialExpressionScalarParameter, x, y)
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("group", group)
    expr.set_editor_property("default_value", default)
    _set_param_desc(expr, desc)
    return expr


def vector_param(
    owner,
    name: str,
    group: str,
    default: tuple[float, float, float, float],
    x: int,
    y: int,
    *,
    desc: str | None = None,
):
    expr = create_expression(owner, unreal.MaterialExpressionVectorParameter, x, y)
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("group", group)
    expr.set_editor_property("default_value", unreal.LinearColor(*default))
    _set_param_desc(expr, desc)
    return expr


def collection_param(
    owner,
    collection_path: str,
    param_name: str,
    x: int,
    y: int,
    *,
    vector: bool = False,
):
    """MaterialExpressionCollectionParameter wired to an MPC asset."""
    # Accept either '/Game/Folder/MPC_Name' or the object form
    # '/Game/Folder/MPC_Name.MPC_Name'.  Normalizing before the load prevents a
    # duplicated object suffix from silently dropping a collection node.
    leaf = collection_path.rsplit("/", 1)[-1]
    package_path = collection_path.rsplit(".", 1)[0] if "." in leaf else collection_path
    asset_name = package_path.rsplit("/", 1)[-1]
    asset_path = f"{package_path}.{asset_name}"
    collection = unreal.load_asset(asset_path)
    if not collection:
        unreal.log_warning(f"[MaterialLib] Missing material parameter collection: {asset_path}")
        return None
    expr = create_expression(owner, unreal.MaterialExpressionCollectionParameter, x, y)
    expr.set_editor_property("collection", collection)
    expr.set_editor_property("parameter_name", param_name)
    return expr


def collection_scalar(owner, collection_path: str, param_name: str, x: int, y: int):
    return collection_param(owner, collection_path, param_name, x, y, vector=False)


def collection_vector(owner, collection_path: str, param_name: str, x: int, y: int):
    return collection_param(owner, collection_path, param_name, x, y, vector=True)


def texture_param(owner, name: str, group: str, x: int, y: int, *, desc: str | None = None):
    expr = create_expression(owner, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("group", group)
    _set_param_desc(expr, desc)
    return expr


PLACEHOLDER_TEXTURE_PATHS = {
    "/Engine/EngineResources/DefaultTexture",
    "/Engine/EngineResources/WhiteSquareTexture",
    "/Engine/EngineMaterials/DefaultNormal",
    "/Engine/EngineMaterials/DefaultDiffuse",
    "/Engine/EngineMaterials/DefaultWhiteGrid",
    "/Engine/EngineMaterials/DefaultWhiteTexture",
}

# Never assign these (or any /Engine/ path) on portfolio master/instance texture params.
BANNED_TEXTURE_PATHS = frozenset(PLACEHOLDER_TEXTURE_PATHS)


def texture_asset_path(tex) -> str | None:
    if not tex:
        return None
    try:
        return tex.get_path_name().split(".", 1)[0]
    except Exception:
        return None


def is_banned_texture_path(path: str | None) -> bool:
    if not path:
        return True
    base = path.split(".", 1)[0]
    return base in BANNED_TEXTURE_PATHS or base.startswith("/Engine/")


def is_banned_texture(tex) -> bool:
    return is_banned_texture_path(texture_asset_path(tex))


def sanitize_candidates(candidates: list[str] | str) -> list[str]:
    if isinstance(candidates, str):
        candidates = [candidates]
    clean = [p for p in candidates if p and not is_banned_texture_path(p.split(".", 1)[0])]
    if len(clean) < len(candidates):
        dropped = [p for p in candidates if p not in clean]
        unreal.log_warning(f"[material_lib] dropped banned/Engine texture candidates: {dropped[:4]}")
    return clean


def is_placeholder_texture(tex) -> bool:
    return is_banned_texture(tex) or not texture_asset_path(tex)


def resolve_texture_path(candidates: list[str] | str) -> str | None:
    for path in sanitize_candidates(candidates):
        pkg = path.split(".", 1)[0]
        if unreal.EditorAssetLibrary.does_asset_exist(path) or unreal.EditorAssetLibrary.does_asset_exist(pkg):
            return path if unreal.EditorAssetLibrary.does_asset_exist(path) else pkg
    return None


def load_texture(candidates: list[str] | str):
    path = resolve_texture_path(candidates)
    return unreal.load_asset(path) if path else None


def set_expression_texture(expr, candidates: list[str] | str) -> str | None:
    candidates = sanitize_candidates(candidates)
    if not candidates:
        unreal.log_error("[material_lib] set_expression_texture: no valid /Game candidates after ban filter")
        return None
    tex = load_texture(candidates)
    if not tex or not expr:
        return None
    path = resolve_texture_path(candidates)
    if path and is_banned_texture_path(path):
        unreal.log_error(f"[material_lib] refused banned texture assignment: {path}")
        return None
    for prop in ("texture", "Texture"):
        try:
            expr.set_editor_property(prop, tex)
            _modify_expression_owner(expr)
            return path
        except Exception as exc:
            unreal.log_warning(f"[material_lib] set_expression_texture {prop}: {exc}")
    return None


def set_instance_texture(instance, param_name: str, candidates: list[str] | str) -> str | None:
    candidates = sanitize_candidates(candidates)
    if not candidates:
        return None
    tex = load_texture(candidates)
    if not tex or not instance:
        return None
    path = resolve_texture_path(candidates)
    try:
        if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_texture_parameter_value"):
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                instance, param_name, tex
            )
        else:
            instance.set_texture_parameter_value_editor_only(param_name, tex)
        return path
    except Exception as exc:
        unreal.log_warning(f"[material_lib] texture {param_name}: {exc}")
        return None


def post_process_blendable_location():
    """Match M_PP_ToonOutline stack point for UE 5.8 blendable ordering."""
    for name in ("BL_REPLACING_TONEMAPPER", "BL_SCENE_COLOR_AFTER_TONEMAP"):
        loc = getattr(unreal.BlendableLocation, name, None)
        if loc is not None:
            return loc
    return unreal.BlendableLocation.BL_REPLACING_TONEMAPPER


def create_toon_profiles(names: list[str]) -> dict[str, unreal.ToonProfile]:
    ensure_directory(PROFILE_DIR)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.ToonProfileFactory()
    profiles: dict[str, unreal.ToonProfile] = {}
    for profile_name in names:
        path = asset_path(PROFILE_DIR, profile_name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            profiles[profile_name] = unreal.load_asset(path)
            continue
        profile = asset_tools.create_asset(
            profile_name, PROFILE_DIR, unreal.ToonProfile, factory
        )
        if not profile:
            raise RuntimeError(f"Failed to create ToonProfile {profile_name}")
        profiles[profile_name] = profile
        save_package(profile)
    return profiles


def set_instance_vector(instance, name: str, rgba: tuple[float, float, float, float]) -> None:
    color = unreal.LinearColor(*rgba)
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_vector_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            instance, name, color
        )
    else:
        instance.set_vector_parameter_value_editor_only(name, color)


def set_instance_scalar(instance, name: str, value: float) -> None:
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_scalar_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            instance, name, value
        )
    else:
        instance.set_scalar_parameter_value_editor_only(name, value)


def set_instance_static_switch(instance, name: str, value: bool) -> None:
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_static_switch_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            instance, name, value
        )
    else:
        try_set_editor_property(instance, name, value)


def set_instance_toon_profile(instance, profile: unreal.ToonProfile) -> None:
    try_set_editor_property(instance, "toon_profile", profile)
    try_set_editor_property(instance, "override_toon_profile", True)


def create_material_instance(name: str, folder: str, parent_path: str) -> unreal.MaterialInstanceConstant:
    ensure_directory(folder)
    inst_path = asset_path(folder, name)
    if unreal.EditorAssetLibrary.does_asset_exist(inst_path):
        return unreal.load_asset(inst_path)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    parent = unreal.load_asset(parent_path)
    instance = asset_tools.create_asset(
        name, folder, unreal.MaterialInstanceConstant, factory
    )
    if not instance:
        raise RuntimeError(f"Failed to create instance {name}")
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
    return instance
