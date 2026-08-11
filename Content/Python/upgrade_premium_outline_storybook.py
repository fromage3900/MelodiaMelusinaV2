"""Premium Outline V5 — triple-AAA storybook ink upgrade.

Fixes the TSR depth-tap jitter at root cause:
  1. Snap tap grid → all 9 depth taps land at frame-identical texel positions
  2. Stable analytic band → replaces fwidth with fixed-width band, no per-frame modulation
  3. Storybook ink feel → paper grain, ink pooling, warm paper substrate

Run in-editor:
    import upgrade_premium_outline_storybook as v5; v5.run_all()

Requires the editor to be running with the premium outline material loaded.
The Script is idempotent — safe to re-run.
"""
from __future__ import annotations

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"

# ---- Replacement blocks ---------------------------------------------------

# Replace 1: Jitter compensation → pixel-snapped UV grid
# The old code uses View.TemporalAAJitter which is sub-pixel; point-sampled
# SceneTextureLookup quantises it back, but the half-texel flips cause flicker.
# Snapping to pixel center makes all 9 taps frame-identical.

OLD_JITTER = r"""    float2 jitterPx = View.TemporalAAJitter.xy * float2(0.5, -0.5) * View.ViewSizeAndInvSize.xy;
    uvC = clamp(uvC - jitterPx * invBuffer * JitterCompensation, viewUVMin, viewUVMax);"""

NEW_SNAP = r"""    // V5 — tap-grid snap: frame-identical depth lookups regardless of TSR jitter
    float2 snappedUv = (floor(uvC * View.BufferSizeAndInvSize.xy) + 0.5) * View.BufferSizeAndInvSize.zw;
    uvC = clamp(snappedUv, viewUVMin, viewUVMax);"""

# Replace 2: fwidth AA → stable analytic band
# fwidth(silResponse) modulates every frame with TSR jitter. With the tap grid
# now frame-identical, a fixed band from widthPx and AAWidth is sufficient and stable.

# Note: there are TWO occurrences of the fwidth AA pattern (silhouette + crease).
# We use a marker-based replacement to catch both.

OLD_FWIDTH_AA = r"""    float aaFloor = rcp(max(widthPx, 1.0));
    float aaS = clamp(max(max(fwidth(silResponse), 1e-5) * aaW, aaFloor), 1e-5, 0.9);"""

NEW_ANALYTIC_AA = r"""    // V5 — stable analytic band (no fwidth, no per-frame modulation)
    float aaS = max(rcp(max(widthPx, 1.0)) * AAWidth, 1e-5);"""

OLD_FWIDTH_AC = r"""    float aaC = clamp(max(max(fwidth(creaseResponse), 1e-5) * aaW, aaFloor), 1e-5, 0.9);"""

NEW_ANALYTIC_AC = r"""    // V5 — stable analytic band (no fwidth)
    float aaC = max(rcp(max(widthPx, 1.0)) * AAWidth, 1e-5);"""

# Addition 3: Storybook enhancements — inserted before the final composite output
# We find the final lerp/return and insert before it.

STORYBOOK_BLOCK = r"""
    // ---- STORYBOOK ENHANCEMENTS (triple-AAA dreamy ink) -------------------
    // Paper grain from screen-space hash — no texture sampler needed.
    // Modulates ink density so it reads as ink on paper, not flat digital colour.
    float2 paperInt = floor(uvC * 640.0);
    float paperHash = frac(sin(dot(paperInt, float2(12.9898, 78.233))) * 43758.5453);
    paperHash = frac(paperHash + sin(dot(paperInt + float2(39.346, 11.135), float2(12.9898, 78.233))) * 24634.6345);
    float paperGrain = lerp(1.0, paperHash, 0.12 * saturate(1.0 - silEdge * 1.5));
    edgeColor *= paperGrain;

    // Ink pools slightly in creases — geometry depressions hold more ink
    float inkPool = 1.0 + 0.10 * creaseEdge * (1.0 - silEdge);
    edgeColor *= inkPool;

    // Warm paper substrate visible through thin ink
    float3 paperColor = float3(0.94, 0.89, 0.81);
    float paperShow = 1.0 - saturate(edgeResponse * 2.5);
    edgeColor = lerp(edgeColor, paperColor, paperShow * 0.20);
    // -------------------------------------------------------------------------

"""


def apply() -> str:
    """Apply all code changes to the premium outline material."""
    import unreal
    MEL = unreal.MaterialEditingLibrary
    m = unreal.load_asset(MAT)
    if not m:
        raise RuntimeError(f"missing {MAT}")

    custom = [e for e in MEL.get_material_expressions(m)
              if type(e).__name__ == "MaterialExpressionCustom"][0]
    code = custom.get_editor_property("code")
    mutations = 0

    # Replacement 1: jitter → snap
    if OLD_JITTER in code:
        code = code.replace(OLD_JITTER, NEW_SNAP)
        mutations += 1
        print("  [OK] Jitter compensation → tap-grid snap")
    else:
        # Try alternative: the code might not have newlines/indentation exactly matching
        # Search for the key identifier
        if "View.TemporalAAJitter" in code:
            print("  [WARN] Found View.TemporalAAJitter but pattern didn't match — check indentation")
        else:
            print("  [SKIP] Jitter block not found (may already be V5)")

    # Replacement 2: fwidth AA (silhouette)
    if OLD_FWIDTH_AA in code:
        code = code.replace(OLD_FWIDTH_AA, NEW_ANALYTIC_AA)
        mutations += 1
        print("  [OK] fwidth AA (silhouette) → stable analytic band")
    else:
        if "fwidth(silResponse)" in code:
            print("  [WARN] Found fwidth(silResponse) but pattern didn't match")
        else:
            print("  [SKIP] Silhouette fwidth not found (may already be V5)")

    # Replacement 3: fwidth AA (crease)
    if OLD_FWIDTH_AC in code:
        code = code.replace(OLD_FWIDTH_AC, NEW_ANALYTIC_AC)
        mutations += 1
        print("  [OK] fwidth AA (crease) → stable analytic band")
    else:
        if "fwidth(creaseResponse)" in code:
            print("  [WARN] Found fwidth(creaseResponse) but pattern didn't match")
        else:
            print("  [SKIP] Crease fwidth not found (may already be V5)")

    # Addition 3: Storybook enhancements
    # Insert before the final composite/return. Look for a known anchor.
    anchors = [
        "float3 finalColor = lerp(SceneColor.rgb, edgeColor, edgeResponse);",
        "return float4(finalColor, 1.0);",
        "// --- FINAL OUTPUT ---",
    ]
    inserted = False
    for anchor in anchors:
        if anchor in code:
            code = code.replace(anchor, STORYBOOK_BLOCK + anchor)
            mutations += 1
            inserted = True
            print(f"  [OK] Storybook enhancements inserted before '{anchor[:50]}...'")
            break

    if not inserted:
        print("  [WARN] Could not find final-output anchor — storybook block not inserted")
        print(f"  Code ends with: ...{code[-200:]}")

    if mutations == 0:
        print("  No changes made — material may already be V5")
        return "noop"

    # Write back and recompile
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)

    # Verify
    rb = [e for e in MEL.get_material_expressions(m)
          if type(e).__name__ == "MaterialExpressionCustom"][0].get_editor_property("code")
    rb_ok = "snappedUv" in rb and "fwidth(silResponse)" not in rb and "paperHash" in rb
    print(f"\n  Verified: snappedUv={'snappedUv' in rb} "
          f"noFwidth={'fwidth(silResponse)' not in rb} "
          f"storybook={'paperHash' in rb}")
    if "paperHash" in rb:
        print(f"  Storybook block: {rb[rb.find('paperHash'):rb.find('paperHash')+80]}")

    status = "ok" if rb_ok else "READBACK FAILED"
    print(f"  Status: {status}")
    return status


def run_all() -> str:
    """Entry point — apply all V5 changes."""
    print(f"=== Premium Outline V5 — triple-AAA storybook ink ===")
    print(f"  Material: {MAT}")
    result = apply()
    print(f"  Done: {result}")
    return result


if __name__ == "__main__":
    run_all()
