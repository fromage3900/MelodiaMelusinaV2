// Landscape Pro triplanar projection.
// Signature is deliberately UNCHANGED - this function is shared by
// M_Master_Toon_Landscape_HeightBlend, M_Master_Nikki_Landscape and M_Master_Nikki
// (10+ instances downstream), so the 11 input pins stay as they are.
//
// 2026-08-29 cost + correctness pass:
//   * sincos() instead of separate sin/cos calls
//   * one sine + two frac decorrelations instead of three sines for the breakup
//   * SampleGrad retains derivatives of continuous projected coordinates.
// 2026-09-04: Rotate geometric normal with projection; handle zero axis weights.

float3 p = WorldPosition + ProjectionOffset;

float3 sr, cr;
sincos(ProjectionRotation * (3.14159265359 / 180.0), sr, cr);

// XYZ Euler rotation, global to the projection so all three planes stay coherent.
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

// Derivatives taken once from the projected position, then masked per axis.
float3 ddxp = ddx(uvp);
float3 ddyp = ddy(uvp);

float3 geometricNormal = WorldNormal * rsqrt(max(dot(WorldNormal, WorldNormal), 1e-12));
float3 n = abs(mul(projection, geometricNormal));
float3 w = pow(n, max(BlendSharpness, 0.01));
w *= max(AxisWeights, float3(0.0, 0.0, 0.0));

// The three breakup values MUST stay decorrelated. A single shared value cancels
// exactly in the normalise below and the effect disappears entirely.
float bscale = max(abs(BreakupScale), 0.0001);
float b = 0.5 + 0.5 * sin(dot(uvp * bscale, float3(1.17, -0.41, 0.23)) * 6.2831853);
float3 bv = float3(b, frac(b * 1.6180339 + 0.33), frac(b * 2.4142136 + 0.66));
bv = pow(saturate(bv), max(BreakupContrast, 0.01));
w *= lerp(float3(1.0, 1.0, 1.0), bv, saturate(BreakupStrength));

float weightSum = w.x + w.y + w.z;
if (weightSum < 1e-6)
{
    // Disabled axes or maximal breakup cannot erase the surface.
    w = n;
    weightSum = w.x + w.y + w.z;
    if (weightSum < 1e-6) { w = float3(0, 0, 1); weightSum = 1; }
}
w /= weightSum;


// Surface-gradient composition, using UE's platform-aware normal decoder.
// Reference: Mikkelsen, JCGT 9(3), 2020. UV axes match the colour projections.
float3 nx = UnpackNormalMap(Texture2DSampleGrad(NormalTex,NormalTexSampler,uvX,ddxp.yz,ddyp.yz)).xyz;
float3 ny = UnpackNormalMap(Texture2DSampleGrad(NormalTex,NormalTexSampler,uvY,ddxp.xz,ddyp.xz)).xyz;
float3 nz = UnpackNormalMap(Texture2DSampleGrad(NormalTex,NormalTexSampler,uvZ,ddxp.xy,ddyp.xy)).xyz;
float2 sx=nx.xy/max(nx.z,0.05), sy=ny.xy/max(ny.z,0.05), sz=nz.xy/max(nz.z,0.05);
float3 N=mul(projection,geometricNormal);
// Convert the three 2D slopes to the common projection frame before blending.
float3 perturb=w.x*float3(0,sx.x,sx.y)+w.y*float3(sy.x,0,sy.y)+w.z*float3(sz.x,sz.y,0);
perturb-=N*dot(N,perturb);
float3 result=normalize(N+max(NormalStrength,0.0)*perturb);
return normalize(mul(transpose(projection),result));
