"""Upgrade premium outline to V6 — radial sampling, MeshBlend techniques, blue noise rotation.

Run in-editor (or via Monolith exec):
    exec(open("Content/Python/upgrade_premium_outline_v6.py").read())
"""
from __future__ import annotations
import unreal

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"
MEL = unreal.MaterialEditingLibrary

m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError(f"Missing {MAT}")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")

changes = 0

# ── Replace 1: Dead jitterPx calculation (immediately overridden by snap) ─────
old_jitter = (
    "float2 jitterPx = View.TemporalAAJitter.xy * float2(0.5,-0.5) * View.ViewSizeAndInvSize.xy;\n"
    "uvC = uvC - jitterPx * invBuffer * JitterCompensation;"
)
new_no_jitter = "// V6: jitterPx removed — tap-grid snap at line 20 makes compensation redundant"
if old_jitter in code:
    code = code.replace(old_jitter, new_no_jitter)
    changes += 1
    print("[OK] Dead jitter code removed")
else:
    print("[SKIP] Jitter pattern not matched exactly")

# ── Replace 2: 8-tap cross + depthDelta/normalMax → radial 16-tap + mean blend ──
old_taps = (
    "float2 ox = float2(invBuffer.x*widthPx, 0.0);\n"
    "float2 oy = float2(0.0, invBuffer.y*widthPx);\n"
    "float2 od1 = (ox+oy)*0.70710678;\n"
    "float2 od2 = (ox-oy)*0.70710678;\n"
    "float2 uvL=clamp(uvC-ox,viewUVMin,viewUVMax); float2 uvR=clamp(uvC+ox,viewUVMin,viewUVMax);\n"
    "float2 uvU=clamp(uvC-oy,viewUVMin,viewUVMax); float2 uvD=clamp(uvC+oy,viewUVMin,viewUVMax);\n"
    "float2 uvUL=clamp(uvC-od1,viewUVMin,viewUVMax); float2 uvDR=clamp(uvC+od1,viewUVMin,viewUVMax);\n"
    "float2 uvUR=clamp(uvC-od2,viewUVMin,viewUVMax); float2 uvDL=clamp(uvC+od2,viewUVMin,viewUVMax);\n"
    "float dL=SceneTextureLookup(uvL,PPI_SceneDepth,false).r; float dR=SceneTextureLookup(uvR,PPI_SceneDepth,false).r;\n"
    "float dU=SceneTextureLookup(uvU,PPI_SceneDepth,false).r; float dD=SceneTextureLookup(uvD,PPI_SceneDepth,false).r;\n"
    "float dUL=SceneTextureLookup(uvUL,PPI_SceneDepth,false).r; float dDR=SceneTextureLookup(uvDR,PPI_SceneDepth,false).r;\n"
    "float dUR=SceneTextureLookup(uvUR,PPI_SceneDepth,false).r; float dDL=SceneTextureLookup(uvDL,PPI_SceneDepth,false).r;\n"
    "float depthDelta = max(max(max(dL-dC,dR-dC),max(dU-dC,dD-dC)), max(max(dUL-dC,dDR-dC),max(dUR-dC,dDL-dC)));"
)

new_radial = (
    "// V6: radial 16-tap (8 dir x 2 rings) + frame-varying blue noise + mean blend\n"
    "float radStep = 360.0 / 8.0;\n"
    "float radOff = radStep * BlueNoiseVec2(trunc(uvC * bufPx), View.StateFrameIndexMod8 % 4).x;\n"
    "float dSum = 0.0; float dMax = 0.0; float nrmSum = 0.0; float nrmMax = 0.0;\n"
    "float3 nCnt = normalize(SceneTextureLookup(uvC,PPI_WorldNormal,false).rgb*2.0-1.0);\n"
    "for (int di = 0; di < 8; di++) {\n"
    "    float a = radians(radOff + radStep * di);\n"
    "    float2 d = float2(cos(a), sin(a));\n"
    "    for (int ri = 1; ri <= 2; ri++) {\n"
    "        float t = float(ri) / 2.0;\n"
    "        float sp = max(ceil(t * t * widthPx * 2.2), 1.0);\n"
    "        float2 tUv = clamp(uvC + d * sp * invBuffer, viewUVMin, viewUVMax);\n"
    "        float dt = SceneTextureLookup(tUv, PPI_SceneDepth, false).r - dC;\n"
    "        if (dt > 0.0) dSum += dt;\n"
    "        dMax = max(dMax, dt);\n"
    "        float3 nT = normalize(SceneTextureLookup(tUv,PPI_WorldNormal,false).rgb*2.0-1.0);\n"
    "        float nd = 1.0 - saturate(dot(nCnt, nT));\n"
    "        nrmSum += nd; nrmMax = max(nrmMax, nd);\n"
    "    }\n"
    "}\n"
    "float depthMean = dSum * (1.0/16.0);\n"
    "float depthBlurred = lerp(dMax, depthMean, saturate(InkBlurStrength));\n"
    "float depthThreshold = max(dC * max(DepthRelativeThreshold,0.0001), 1.0);\n"
    "float silResponse = (depthBlurred/depthThreshold) * DepthWeight * EdgeStrength;\n"
    "float normalMean = nrmSum * (1.0/16.0);\n"
    "float normalBlurred = lerp(nrmMax, normalMean, saturate(InkBlurStrength));\n"
    "float creaseResponse = (normalBlurred/max(CreaseThreshold,0.001)) * NormalWeight * EdgeStrength;"
)

if old_taps in code:
    code = code.replace(old_taps, new_radial)
    changes += 1
    print("[OK] Radial 16-tap sampling inserted")
else:
    print("[WARN] Old tap pattern not found — trying degraded match")
    # Try finding the key landmarks
    if "uvL=clamp" in code and "dL=SceneTextureLookup" in code:
        print("  Found partial match — individual var names present")
    else:
        print("  No match — code structure may have changed")
        print(f"  Code around where taps should be: ...{code[code.find('float2 ox'):code.find('float2 ox')+200] if 'float2 ox' in code else 'NOT FOUND'}...")

# ── Replace 3: Redundant old depthMean/normalMean/creaseResponse calc ──
# The radial block above already computes these, so remove the old versions
old_post = (
    "float depthThreshold = max(dC * max(DepthRelativeThreshold,0.0001), 1.0);\n"
    "float depthMean = (max(dL-dC,0.0)+max(dR-dC,0.0)+max(dU-dC,0.0)+max(dD-dC,0.0)+max(dUL-dC,0.0)+max(dDR-dC,0.0)+max(dUR-dC,0.0)+max(dDL-dC,0.0))*0.125;\n"
    "float depthBlurred = lerp(max(depthDelta,0.0), depthMean, saturate(InkBlurStrength));\n"
    "float silResponse = (depthBlurred/depthThreshold) * DepthWeight * EdgeStrength;\n"
    "float normalMean = ((1.0-saturate(dot(nC,nL)))+(1.0-saturate(dot(nC,nR)))+(1.0-saturate(dot(nC,nU)))+(1.0-saturate(dot(nC,nD)))+(1.0-saturate(dot(nC,nUL)))+(1.0-saturate(dot(nC,nDR)))+(1.0-saturate(dot(nC,nUR)))+(1.0-saturate(dot(nC,nDL))))*0.125;\n"
    "float normalBlurred = lerp(normalDiverge, normalMean, saturate(InkBlurStrength));\n"
    "float creaseResponse = (normalBlurred/max(CreaseThreshold,0.001)) * NormalWeight * EdgeStrength;"
)

if old_post in code and changes > 0:
    code = code.replace(old_post, "")
    changes += 1
    print("[OK] Redundant old normal/crease block removed")
else:
    print("[SKIP] Old post block not found — maybe already removed by radial replacement")

# ── Write back ──────────────────────────────────────────────────────────────
if changes > 0:
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print(f"\n[DONE] V6 applied — {changes} changes, code length {len(code)}")
else:
    print("\n[NOOP] No changes made — code may already be V6")

# ── Verify ──────────────────────────────────────────────────────────────────
rb = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
rc = rb.get_editor_property("code")
v6_ok = "BlueNoiseVec2" in rc and "jitterPx" not in rc and "paperHash" in rc
print(f"\nVerification: radial={'BlueNoiseVec2' in rc} noJitter={'jitterPx' not in rc} story={'paperHash' in rc}")
print(f"  Code length: {len(rc)}")
if v6_ok:
    print("  STATUS: V6 LIVE")
else:
    print("  STATUS: WARNING — verification failed")
