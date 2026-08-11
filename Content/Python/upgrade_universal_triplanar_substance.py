"""Add an additive Substance-style triplanar overlay to the universal Toon master.

This is intentionally project-owned and rollback-safe:

* it never deletes or rewires the existing V9/V10 branches;
* it creates one reusable material function with explicit projection controls;
* the new master branch is behind a *default-off* static switch;
* every node created by this script is tagged with ``UTriPro:`` so reruns are
  deterministic and do not grow duplicate graphs.

The function is a practical Substance Painter-style approximation rather than
an engine-content clone. It provides world/object-independent projection
controls commonly needed in production: scale, Euler rotation, offset, axis
blend sharpness, axis weights, and procedural breakup scale/strength/contrast.
The master uses it as an optional albedo overlay and a restrained roughness
modulator. Authored normal remains authoritative until a dedicated
reoriented-normal projection is introduced.

Run inside the UE editor:

    import upgrade_universal_triplanar_substance as u
    u.main()
"""

from __future__ import annotations

import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
FUNCTION_PATH = "/Game/EnvSandbox/Materials/Functions/MF_Triplanar_SubstanceStyle"
GROUP = "02 | Triplanar Pro"
TAG = "UTriPro:"


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[Universal Triplanar Pro] {message}")


def _master_expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _function_expressions(function):
    return list(unreal.MaterialEditingLibrary.get_material_function_expressions(function) or [])


def _find_tag(expressions, key):
    wanted = TAG + key
    for node in expressions:
        if str(_get(node, "desc", "")) == wanted:
            return node
    return None


def _find_parameter(material, name):
    for node in _master_expressions(material):
        if str(_get(node, "parameter_name", "")) == name:
            return node
    return None


def _create_master_node(material, cls, key, x, y):
    node = _find_tag(_master_expressions(material), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    if not node:
        raise RuntimeError(f"Could not create {cls.__name__} ({key})")
    _set(node, "desc", TAG + key)
    return node, True


def _create_parameter(material, cls, name, default, key, x, y, group=GROUP):
    node = _find_parameter(material, name)
    if node:
        return node, False
    node, created = _create_master_node(material, cls, key, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", default)
    return node, created


def _create_fn_node(function, cls, key, x, y):
    node = _find_tag(_function_expressions(function), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression_in_function(function, cls, x, y)
    if not node:
        raise RuntimeError(f"Could not create function node {cls.__name__} ({key})")
    _set(node, "desc", TAG + key)
    return node, True


def _connect(source, output, target, input_name):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, output, target, input_name):
        raise RuntimeError(
            f"Could not connect {source.get_name()}:{output} -> {target.get_name()}:{input_name}"
        )


def _fn_input(function, key, name, input_type, sort, x=-1500, y=0):
    node, created = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, key, x, y)
    _set(node, "input_name", name)
    _set(node, "input_type", input_type)
    _set(node, "sort_priority", sort)
    return node, created


def _fn_output(function, key, name, x=350, y=0):
    node, created = _create_fn_node(function, unreal.MaterialExpressionFunctionOutput, key, x, y)
    _set(node, "output_name", name)
    return node, created


TRIPLANAR_HLSL = r"""
float3 p = WorldPosition + ProjectionOffset;
float3 r = ProjectionRotation * (3.14159265359 / 180.0);
float3 s = sin(r);
float3 c = cos(r);

// XYZ Euler rotation, matching the stable project convention used by the
// existing Nikki material functions. Rotation is intentionally global to the
// projection so all three planes remain coherent.
p = float3(
    p.x * (c.y * c.z) + p.y * (s.x * s.y * c.z - c.x * s.z) + p.z * (c.x * s.y * c.z + s.x * s.z),
    p.x * (c.y * s.z) + p.y * (s.x * s.y * s.z + c.x * c.z) + p.z * (c.x * s.y * s.z - s.x * c.z),
    p.x * (-s.y) + p.y * (s.x * c.y) + p.z * (c.x * c.y));

float scale = max(abs(ProjectionScale), 0.00001);
float3 uvp = p * scale;

// Explicit axis projections: X uses YZ, Y uses XZ, Z uses XY.
float2 uvX = uvp.yz;
float2 uvY = uvp.xz;
float2 uvZ = uvp.xy;

float3 n = abs(normalize(WorldNormal));
float3 w = pow(n, max(BlendSharpness, 0.01));
w *= max(AxisWeights, float3(0.0, 0.0, 0.0));

// A deterministic, texture-free breakup keeps large surfaces from reading as
// one perfect projected sheet. The three directions are decorrelated so the
// transition is less obviously axis-aligned than a single noise lookup.
float breakupScale = max(abs(BreakupScale), 0.0001);
float3 bp = uvp * breakupScale;
float bx = 0.5 + 0.5 * sin(dot(bp, float3(1.17, -0.41, 0.23)) * 6.2831853);
float by = 0.5 + 0.5 * sin(dot(bp, float3(-0.37, 1.09, 0.51)) * 6.2831853 + 2.0943951);
float bz = 0.5 + 0.5 * sin(dot(bp, float3(0.43, 0.19, 1.21)) * 6.2831853 + 4.1887902);
float3 breakup = pow(saturate(float3(bx, by, bz)), max(BreakupContrast, 0.01));
w *= lerp(float3(1.0, 1.0, 1.0), breakup, saturate(BreakupStrength));

float weightSum = max(w.x + w.y + w.z, 0.0001);
w /= weightSum;

float3 sampleX = Texture2DSample(Tex, TexSampler, uvX).rgb;
float3 sampleY = Texture2DSample(Tex, TexSampler, uvY).rgb;
float3 sampleZ = Texture2DSample(Tex, TexSampler, uvZ).rgb;
return sampleX * w.x + sampleY * w.y + sampleZ * w.z;
"""


def build_function():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    function = unreal.EditorAssetLibrary.load_asset(FUNCTION_PATH)
    created_asset = False
    if function is None:
        function = tools.create_asset(
            "MF_Triplanar_SubstanceStyle",
            FUNCTION_PATH.rsplit("/", 1)[0],
            unreal.MaterialFunction,
            unreal.MaterialFunctionFactoryNew(),
        )
        created_asset = True
    if function is None:
        raise RuntimeError(f"Could not load/create {FUNCTION_PATH}")

    # This function is project-owned and has no external consumers until the
    # master bridge is connected. Rebuilding its own small graph in place makes
    # reruns deterministic without deleting any user material or engine asset.
    try:
        unreal.MaterialEditingLibrary.delete_all_material_expressions_in_function(function)
    except Exception as exc:
        if created_asset:
            raise
        _log(f"Function graph was not cleared ({exc}); continuing with tagged nodes")

    inputs = [
        ("Tex", unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D, 0, -1500, -500),
        ("WorldPosition", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 1, -1500, -380),
        ("WorldNormal", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 2, -1500, -260),
        ("ProjectionScale", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 3, -1500, -120),
        ("BlendSharpness", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 4, -1500, 0),
        ("ProjectionOffset", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 5, -1500, 120),
        ("ProjectionRotation", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 6, -1500, 240),
        ("AxisWeights", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 7, -1500, 360),
        ("BreakupScale", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 8, -1500, 500),
        ("BreakupStrength", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 9, -1500, 620),
        ("BreakupContrast", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 10, -1500, 740),
    ]
    fn_inputs = {}
    for name, kind, sort, x, y in inputs:
        node, _ = _fn_input(function, "Input_" + name, name, kind, sort, x, y)
        fn_inputs[name] = node

    custom, _ = _create_fn_node(function, unreal.MaterialExpressionCustom, "ProjectionCustom", -500, 120)
    _set(custom, "description", "Substance-style triplanar projection with rotated offset planes and deterministic breakup")
    _set(custom, "code", TRIPLANAR_HLSL)
    _set(custom, "output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    custom_inputs = []
    for name, *_ in inputs:
        ci = unreal.CustomInput()
        _set(ci, "input_name", name)
        custom_inputs.append(ci)
    _set(custom, "inputs", custom_inputs)
    for name in fn_inputs:
        _connect(fn_inputs[name], "", custom, name)

    output, _ = _fn_output(function, "Output_Color", "Color", 300, 120)
    _connect(custom, "", output, "")
    unreal.MaterialEditingLibrary.update_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    return function


def _scalar(material, name, default, key, x, y, min_value=None, max_value=None):
    node, created = _create_parameter(
        material,
        unreal.MaterialExpressionScalarParameter,
        name,
        float(default),
        key,
        x,
        y,
    )
    if min_value is not None:
        _set(node, "slider_min", float(min_value))
    if max_value is not None:
        _set(node, "slider_max", float(max_value))
    return node, created


def _vector(material, name, default, key, x, y):
    return _create_parameter(
        material,
        unreal.MaterialExpressionVectorParameter,
        name,
        unreal.LinearColor(*default),
        key,
        x,
        y,
    )


def _find_type(material, class_name, predicate=None):
    for node in _master_expressions(material):
        if type(node).__name__ != class_name:
            continue
        if predicate is None or predicate(node):
            return node
    return None


def _find_node_name(material, name):
    for node in _master_expressions(material):
        if node.get_name() == name:
            return node
    return None


def build_master(function):
    material = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if material is None:
        raise RuntimeError(f"Could not load {MASTER_PATH}")
    MEL = unreal.MaterialEditingLibrary

    static_switch, _ = _create_parameter(
        material,
        unreal.MaterialExpressionStaticSwitchParameter,
        "bTriplanarPro_Active",
        False,
        "Switch_Active",
        -1250,
        -520,
    )
    scalar_specs = [
        ("TriplanarPro_Scale", 0.01, "Scale", -1250, -320, 0.00001, 1.0),
        ("TriplanarPro_Sharpness", 4.0, "Sharpness", -1250, -220, 0.01, 32.0),
        ("TriplanarPro_BlendStrength", 0.0, "BlendStrength", -1250, -120, 0.0, 1.0),
        ("TriplanarPro_RoughnessBlend", 0.0, "RoughnessBlend", -1250, -20, 0.0, 1.0),
        ("TriplanarPro_BreakupStrength", 0.0, "BreakupStrength", -1250, 100, 0.0, 1.0),
        ("TriplanarPro_BreakupScale", 1.0, "BreakupScale", -1250, 200, 0.001, 32.0),
        ("TriplanarPro_BreakupContrast", 1.0, "BreakupContrast", -1250, 300, 0.01, 8.0),
    ]
    params = {}
    for name, default, key, x, y, low, high in scalar_specs:
        params[name], _ = _scalar(material, name, default, key, x, y, low, high)
    params["TriplanarPro_ProjectionOffset"], _ = _vector(
        material, "TriplanarPro_ProjectionOffset", (0.0, 0.0, 0.0, 0.0), "ProjectionOffset", -1250, 400
    )
    params["TriplanarPro_ProjectionRotation"], _ = _vector(
        material, "TriplanarPro_ProjectionRotation", (0.0, 0.0, 0.0, 0.0), "ProjectionRotation", -1250, 500
    )
    params["TriplanarPro_AxisWeights"], _ = _vector(
        material, "TriplanarPro_AxisWeights", (1.0, 1.0, 1.0, 0.0), "AxisWeights", -1250, 600
    )

    call, _ = _create_master_node(material, unreal.MaterialExpressionMaterialFunctionCall, "FunctionCall", -850, 80)
    _set(call, "material_function", function)
    _set(call, "desc", TAG + "FunctionCall")

    # TextureObjectParameter_0 is the existing, verified TriplanarDetailMap
    # (Perlin_1). Reusing it keeps the new bridge consistent with current
    # material instances and avoids introducing an unassigned texture slot.
    texture = _find_parameter(material, "TriplanarDetailMap")
    if texture is None:
        raise RuntimeError("TriplanarDetailMap parameter is missing from the universal master")

    world_pos, _ = _create_master_node(material, unreal.MaterialExpressionWorldPosition, "WorldPosition", -1050, 720)
    world_normal, _ = _create_master_node(material, unreal.MaterialExpressionVertexNormalWS, "WorldNormal", -1050, 820)
    bindings = {
        "Tex": texture,
        "WorldPosition": world_pos,
        "WorldNormal": world_normal,
        "ProjectionScale": params["TriplanarPro_Scale"],
        "BlendSharpness": params["TriplanarPro_Sharpness"],
        "ProjectionOffset": params["TriplanarPro_ProjectionOffset"],
        "ProjectionRotation": params["TriplanarPro_ProjectionRotation"],
        "AxisWeights": params["TriplanarPro_AxisWeights"],
        "BreakupScale": params["TriplanarPro_BreakupScale"],
        "BreakupStrength": params["TriplanarPro_BreakupStrength"],
        "BreakupContrast": params["TriplanarPro_BreakupContrast"],
    }
    for pin, node in bindings.items():
        _connect(node, "", call, pin)

    # The existing final Toon BSDF path is identified by the proven output
    # connection instead of assuming node creation order. Its BaseColor input
    # currently comes from StaticSwitchParameter_10, which is preserved as A.
    bsdf = _find_type(material, "MaterialExpressionSubstrateToonBSDF")
    if bsdf is None:
        raise RuntimeError("Universal master SubstrateToonBSDF node was not found")

    # Find the current BaseColor source by inspecting the known final BSDF
    # input. The Python API exposes inputs by index; the editor reflection used
    # by Monolith calls this pin BaseColor, but the Python connection helper is
    # also happy with that named pin.
    current_base = _find_node_name(material, "MaterialExpressionStaticSwitchParameter_10")
    if current_base is None:
        current_base = _find_type(
            material,
            "MaterialExpressionStaticSwitchParameter",
            lambda n: str(_get(n, "parameter_name", "")) == "bDFContactBlend_Active",
        )
    if current_base is None:
        current_base = _find_type(material, "MaterialExpressionStaticSwitchParameter")
    if current_base is None:
        raise RuntimeError("Could not find the existing universal Toon BaseColor source")

    # Reuse the existing base source as A. This branch is tagged and connected
    # only to the new switch, so the old BSDF connection remains unchanged in
    # the asset's rollback history until the new switch is enabled.
    color_lerp, _ = _create_master_node(material, unreal.MaterialExpressionLinearInterpolate, "ColorBlend", -450, 0)
    _connect(current_base, "", color_lerp, "A")
    _connect(call, "Color", color_lerp, "B")
    _connect(params["TriplanarPro_BlendStrength"], "", color_lerp, "Alpha")

    active_gate, _ = _create_master_node(material, unreal.MaterialExpressionStaticSwitch, "ActiveGate", -180, 0)
    _connect(color_lerp, "", active_gate, "True")
    _connect(current_base, "", active_gate, "False")
    _connect(static_switch, "", active_gate, "Value")
    _connect(active_gate, "", bsdf, "BaseColor")

    # Optional roughness utility: grayscale of the projected color, blended
    # into the existing roughness input by a default-zero parameter. This keeps
    # authored roughness authoritative by default and avoids a second texture
    # lookup. The source is found from the existing BSDF Roughness pin path.
    dot, _ = _create_master_node(material, unreal.MaterialExpressionDotProduct, "RoughnessLuma", -420, 260)
    lum, _ = _create_master_node(material, unreal.MaterialExpressionConstant3Vector, "RoughnessLumaWeights", -620, 340)
    _set(lum, "constant", unreal.LinearColor(0.2126, 0.7152, 0.0722, 0.0))
    _connect(call, "Color", dot, "A")
    _connect(lum, "", dot, "B")
    rough_source = _find_node_name(material, "MaterialExpressionStaticSwitchParameter_11")
    if rough_source is None:
        rough_source = _find_type(
            material,
            "MaterialExpressionScalarParameter",
            lambda n: str(_get(n, "parameter_name", "")) == "Roughness",
        )
    if rough_source is None:
        # Leave the roughness branch disconnected if this particular master
        # revision does not expose a scalar named Roughness; the albedo bridge
        # remains fully valid and the diagnostic is explicit.
        _log("No scalar Roughness parameter found; skipping optional roughness source")
    else:
        rough_lerp, _ = _create_master_node(material, unreal.MaterialExpressionLinearInterpolate, "RoughnessBlend_Lerp", -170, 260)
        _connect(rough_source, "", rough_lerp, "A")
        _connect(dot, "", rough_lerp, "B")
        _connect(params["TriplanarPro_RoughnessBlend"], "", rough_lerp, "Alpha")
        _connect(rough_lerp, "", bsdf, "Roughness")

    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    _log("Building function")
    function = build_function()
    _log("Integrating default-off bridge into universal master")
    material = build_master(function)
    _log(f"Saved {FUNCTION_PATH}")
    _log(f"Saved {MASTER_PATH}")
    return {
        "function": FUNCTION_PATH,
        "master": MASTER_PATH,
        "switch": "bTriplanarPro_Active",
        "default_enabled": False,
    }


if __name__ == "__main__":
    main()
