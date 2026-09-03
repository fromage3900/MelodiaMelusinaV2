"""V6.2 polish: center depth blur + per-tap rejection + mean-biased blend.

Residual jitter comes from TSR depth noise at sub-pixel level. Even with frame-identical
tap positions, the depth values themselves jitter. Three fixes:

1. Blur dC across 5 taps (center + 4 cardinal) — reduces per-pixel depth noise by ~60%
2. Reject extreme deltas (> 5x threshold) — prevents far-off geometry from triggering edges
3. Bias mean blend to min 50% mean — reduces single-sample noise amplification
"""
import unreal

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"
MEL = unreal.MaterialEditingLibrary

m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError(f"Missing {MAT}")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")
changes = 0

# ── Replace 1: Center depth blur (replace single dC lookup with 5-tap blur) ──
old_dc = "float dC = SceneTextureLookup(uvC, PPI_SceneDepth, false).r;"
new_dc = (
    "// V6.2: center depth blur — average 5 taps to reduce TSR jitter\n"
    "float dC = SceneTextureLookup(uvC, PPI_SceneDepth, false).r;\n"
    "dC = (dC + SceneTextureLookup(clamp(uvC-float2(invBuffer.x,0),viewUVMin,viewUVMax),PPI_SceneDepth,false).r\n"
    "       + SceneTextureLookup(clamp(uvC+float2(invBuffer.x,0),viewUVMin,viewUVMax),PPI_SceneDepth,false).r\n"
    "       + SceneTextureLookup(clamp(uvC-float2(0,invBuffer.y),viewUVMin,viewUVMax),PPI_SceneDepth,false).r\n"
    "       + SceneTextureLookup(clamp(uvC+float2(0,invBuffer.y),viewUVMin,viewUVMax),PPI_SceneDepth,false).r) * 0.2;"
)

if old_dc in code:
    code = code.replace(old_dc, new_dc)
    changes += 1
    print("[OK] Center depth blur (5-tap average)")
else:
    # Try to find just the declaration
    for alt in ["float dC=SceneTextureLookup(uvC,PPI_SceneDepth,false).r;",
                "float dC=SceneTextureLookup(uvC, PPI_SceneDepth, false).r;"]:
        if alt in code:
            code = code.replace(alt, new_dc)
            changes += 1
            print(f"[OK] Center depth blur (matched alt format)")
            break

# ── Replace 2: Add rejection threshold before the radial loop ──
# Insert after "float taper = lerp(1.0, saturate(distRatio), saturate(TaperStrength));"
old_taper_end = "float taper = lerp(1.0, saturate(distRatio), saturate(TaperStrength));"
new_taper_end = (
    "float taper = lerp(1.0, saturate(distRatio), saturate(TaperStrength));\n"
    "// V6.2: rejection threshold for tap deltas\n"
    "float rejectThresh = max(dC * max(DepthRelativeThreshold,0.001), 1.0) * 5.0;"
)

if old_taper_end in code:
    code = code.replace(old_taper_end, new_taper_end)
    changes += 1
    print("[OK] Rejection threshold added")
else:
    print("[SKIP] taper line not found — rejection threshold not inserted")

# ── Replace 3: Per-tap rejection (inside the radial loop) ──
# Replace the delta calculation
old_dt = "float dt = SceneTextureLookup(tUv, PPI_SceneDepth, false).r - dC;"
new_dt = (
    "float dt = SceneTextureLookup(tUv, PPI_SceneDepth, false).r - dC;\n"
    "        // V6.2: reject extreme deltas (far geometry triggering false edges)\n"
    "        if (dt > rejectThresh) dt = 0.0;"
)

if old_dt in code:
    code = code.replace(old_dt, new_dt)
    changes += 1
    print("[OK] Per-tap rejection added")
else:
    # Try without spaces
    old_dt2 = "float dt=SceneTextureLookup(tUv,PPI_SceneDepth,false).r-dC;"
    if old_dt2 in code:
        code = code.replace(old_dt2, new_dt)
        changes += 1
        print("[OK] Per-tap rejection added (tight format)")

# ── Replace 4: Mean-biased blend (min 50% mean contribution) ──
old_blend = "float depthBlurred = lerp(dMax, depthMean, saturate(InkBlurStrength));"
new_blend = (
    "// V6.2: mean-biased blend — min 50% mean contribution for TSR stability\n"
    "float meanBias = 0.5 + saturate(InkBlurStrength) * 0.5;\n"
    "float depthBlurred = lerp(dMax, depthMean, meanBias);"
)

if old_blend in code:
    code = code.replace(old_blend, new_blend)
    changes += 1
    print("[OK] Mean-biased blend (50% min mean)")
else:
    # The current V6 code uses this slightly different version
    for alt in ["float depthBlurred = lerp(dMax, depthMean, saturate(InkBlurStrength));",
                "float depthBlurred=lerp(dMax,depthMean,saturate(InkBlurStrength));"]:
        if alt in code:
            code = code.replace(alt, new_blend)
            changes += 1
            print(f"[OK] Mean-biased blend matched alt")
            break

# ── Apply ──────────────────────────────────────────────────────────────────
if changes > 0:
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print(f"\n[DONE] V6.2 polish — {changes} changes, code length {len(code)}")
else:
    print("\n[NOOP] No changes — may already be V6.2")

# ── Verify ──────────────────────────────────────────────────────────────────
rb = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
rc = rb.get_editor_property("code")
print(f"Verification: blur5={'float2(invBuffer.x,0)' in rc} reject={'rejectThresh' in rc} meanBias={'meanBias' in rc} story={'paperHash' in rc}")
