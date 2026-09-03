"""V6.1 hotfix — remove frame-varying rotation. The outline needs pixel-STABLE rotation,
identical every frame. MeshBlend's frame dither works for soft blending, but the
outline's hard max() amplifies rotation changes into visible shaking."""
import unreal

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"
MEL = unreal.MaterialEditingLibrary

m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError(f"Missing {MAT}")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")

changes = 0

# Fix: Replace InterleavedGradientNoise with pixel-hash-only rotation (no frame index)
# Using the same hash as the storybook paper grain — deterministic per pixel, same every frame
old = "InterleavedGradientNoise(trunc(uvC * bufPx), View.StateFrameIndexMod8 % 4)"
new = "frac(sin(dot(trunc(uvC * bufPx), float2(12.9898, 78.233))) * 43758.5453)"

if old in code:
    code = code.replace(old, new)
    changes += 1
    print("[OK] Frame-varying rotation -> pixel-stable hash rotation")
else:
    print("[SKIP] Pattern not found")
    # Try the BlueNoiseVec2 variation in case
    old2 = "BlueNoiseVec2(trunc(uvC * bufPx), View.StateFrameIndexMod8 % 4).x"
    if old2 in code:
        code = code.replace(old2, new)
        changes += 1
        print("[OK] BlueNoiseVec2 variant fixed")

# Also verify the state frame index is NOT used anywhere else
if "StateFrameIndexMod8" in code:
    # Remove any remaining reference — we don't want frame-varying ANYTHING in the outline
    old_sfi = "View.StateFrameIndexMod8 % 4"
    if old_sfi in code:
        code = code.replace(old_sfi, "0")
        changes += 1
        print("[OK] Removed remaining StateFrameIndexMod8 reference")
    else:
        # Different occurrence
        import re
        code = re.sub(r'View\.StateFrameIndexMod8[^,\s)]*', '0', code)
        changes += 1
        print("[OK] Stripped remaining StateFrameIndexMod8 via regex")

if changes > 0:
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print(f"\n[DONE] V6.1 hotfix applied — {changes} changes, code length {len(code)}")
else:
    print("\n[NOOP] No changes — code may already use pixel-stable rotation")
