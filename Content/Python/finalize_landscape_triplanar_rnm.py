"""Finalize the shared landscape triplanar normal lane with axis-correct RNM.

This is intentionally a surgical edit: it keeps the existing function inputs,
the colour custom node, and every downstream material call intact.  Only the
normal custom node is replaced, then the function and its known Nikki landscape
master are recompiled and saved by the editor.
"""

import unreal


FUNCTION_PATH = "/Game/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro"
CHECKPOINT_PATH = "/Game/EnvSandbox/Materials/Functions/Checkpoints/MF_Triplanar_LandscapePro_PRE_RNM_20260904"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"

RNM_CODE = r"""// Landscape Pro triplanar normal projection.
// Axis-aware reorientation follows the triplanar normal treatment in
// Mikkelsen, Surface Gradient-Based Bump Mapping Framework (JCGT 9(3), 2020).
// The function signature is kept stable for all downstream materials.

float3 p = WorldPosition + ProjectionOffset;
float3 sr, cr;
sincos(ProjectionRotation * (3.14159265359 / 180.0), sr, cr);
float3x3 projection = float3x3(
    cr.y * cr.z, sr.x * sr.y * cr.z - cr.x * sr.z, cr.x * sr.y * cr.z + sr.x * sr.z,
    cr.y * sr.z, sr.x * sr.y * sr.z + cr.x * cr.z, cr.x * sr.y * sr.z - sr.x * cr.z,
    -sr.y, sr.x * cr.y, cr.x * cr.y);
p = mul(projection, p);

float scale = max(abs(ProjectionScale), 0.00001);
float3 uvp = p * scale;
float2 uvX = uvp.yz;
float2 uvY = uvp.xz;
float2 uvZ = uvp.xy;
float3 ddxp = ddx(uvp);
float3 ddyp = ddy(uvp);

float3 geometricNormal = WorldNormal * rsqrt(max(dot(WorldNormal, WorldNormal), 1e-12));
float3 projectedNormal = normalize(mul(projection, geometricNormal));
float3 axisSign = step(0.0, projectedNormal) * 2.0 - 1.0;
float3 absNormal = abs(projectedNormal);
float3 w = pow(absNormal, max(BlendSharpness, 0.01));
w *= max(AxisWeights, float3(0.0, 0.0, 0.0));

float bscale = max(abs(BreakupScale), 0.0001);
float b = 0.5 + 0.5 * sin(dot(uvp * bscale, float3(1.17, -0.41, 0.23)) * 6.2831853);
float3 breakup = float3(b, frac(b * 1.6180339 + 0.33), frac(b * 2.4142136 + 0.66));
breakup = pow(saturate(breakup), max(BreakupContrast, 0.01));
w *= lerp(float3(1.0, 1.0, 1.0), breakup, saturate(BreakupStrength));
float weightSum = w.x + w.y + w.z;
if (weightSum < 1e-6)
{
    w = absNormal;
    weightSum = w.x + w.y + w.z;
    if (weightSum < 1e-6) { w = float3(0.0, 0.0, 1.0); weightSum = 1.0; }
}
w /= weightSum;

float3 nx = UnpackNormalMap(Texture2DSampleGrad(NormalTex, NormalTexSampler, uvX, ddxp.yz, ddyp.yz)).xyz;
float3 ny = UnpackNormalMap(Texture2DSampleGrad(NormalTex, NormalTexSampler, uvY, ddxp.xz, ddyp.xz)).xyz;
float3 nz = UnpackNormalMap(Texture2DSampleGrad(NormalTex, NormalTexSampler, uvZ, ddxp.xy, ddyp.xy)).xyz;

// Correct mirrored tangent axes for the three projected planes.
nx.x *= axisSign.x;
ny.x *= axisSign.y;
nz.x *= -axisSign.z;

// Reoriented Normal Mapping lifts each tangent sample into its plane's
// geometric frame before swizzling it into the common projected frame.
// Keep this inline: UE Material Custom expressions reject local function
// declarations, even though the same HLSL is valid in a standalone shader.
float3 rnx1 = float3(projectedNormal.zy, absNormal.x) + float3(0.0, 0.0, 1.0);
float3 rnx2 = nx * float3(-1.0, -1.0, 1.0);
nx = rnx1 * dot(rnx1, rnx2) / max(rnx1.z, 1e-4) - rnx2;
float3 rny1 = float3(projectedNormal.xz, absNormal.y) + float3(0.0, 0.0, 1.0);
float3 rny2 = ny * float3(-1.0, -1.0, 1.0);
ny = rny1 * dot(rny1, rny2) / max(rny1.z, 1e-4) - rny2;
float3 rnz1 = float3(projectedNormal.xy, absNormal.z) + float3(0.0, 0.0, 1.0);
float3 rnz2 = nz * float3(-1.0, -1.0, 1.0);
nz = rnz1 * dot(rnz1, rnz2) / max(rnz1.z, 1e-4) - rnz2;
nx.z *= axisSign.x;
ny.z *= axisSign.y;
nz.z *= axisSign.z;

float3 resultProjected = normalize(nx.zyx * w.x + ny.xzy * w.y + nz.xyz * w.z);
float3 resultWorld = mul(transpose(projection), resultProjected);
return normalize(resultWorld);"""


def run():
    fn = unreal.EditorAssetLibrary.load_asset(FUNCTION_PATH)
    if fn is None:
        raise RuntimeError("Missing triplanar function: %s" % FUNCTION_PATH)
    customs = [
        e for e in unreal.MaterialEditingLibrary.get_material_function_expressions(fn) or []
        if e.get_class().get_name() == "MaterialExpressionCustom"
    ]
    if not customs:
        raise RuntimeError("No custom nodes found in triplanar function")
    def pin_names(expr):
        return [str(i.get_editor_property("input_name")) for i in expr.get_editor_property("inputs")]
    # Resolve by declared pins, never by a comment or identifier in the HLSL.
    normal = next((e for e in customs if "NormalTex" in pin_names(e)), None)
    color = next((e for e in customs if "NormalTex" not in pin_names(e)), None)
    if normal is None or color is None:
        raise RuntimeError("Could not resolve colour/normal custom nodes by input pins")
    # The first run of this utility selected by a code comment. Restore the
    # colour node from the untouched checkpoint before applying RNM.
    backup = unreal.EditorAssetLibrary.load_asset(CHECKPOINT_PATH)
    if backup is not None:
        backup_customs = [
            e for e in unreal.MaterialEditingLibrary.get_material_function_expressions(backup) or []
            if e.get_class().get_name() == "MaterialExpressionCustom"
        ]
        backup_color = next((e for e in backup_customs if "NormalTex" not in pin_names(e)), None)
        if backup_color is not None:
            color.set_editor_property("code", backup_color.get_editor_property("code"))
            color.set_editor_property("description", backup_color.get_editor_property("description"))
    normal.set_editor_property("code", RNM_CODE)
    normal.set_editor_property("description", "Landscape Pro triplanar - axis-correct RNM normal blend with rotated projection")
    unreal.MaterialEditingLibrary.update_material_function(fn)
    unreal.EditorAssetLibrary.save_loaded_asset(fn, False)
    mat = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if mat is not None:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return {"function": FUNCTION_PATH, "master": MASTER_PATH, "custom_count": len(customs), "normal_node": normal.get_name()}


if __name__ == "__main__":
    print(run())
