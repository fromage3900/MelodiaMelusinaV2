"""Fix V6 compile errors: replace BlueNoiseVec2 + remove remaining old var refs."""
import unreal

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate"
MEL = unreal.MaterialEditingLibrary

m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError(f"Missing {MAT}")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")
changes = 0

# Fix 1: Replace BlueNoiseVec2 with InterleavedGradientNoise (available in PP context)
# InterleavedGradientNoise takes (pixelPos, frameId) returns a float
old_noise = "BlueNoiseVec2(trunc(uvC * bufPx), View.StateFrameIndexMod8 % 4).x"
new_noise = "InterleavedGradientNoise(trunc(uvC * bufPx), View.StateFrameIndexMod8 % 4)"

if old_noise in code:
    code = code.replace(old_noise, new_noise)
    changes += 1
    print("[OK] BlueNoiseVec2 -> InterleavedGradientNoise")
else:
    print("[SKIP] BlueNoiseVec2 not found (may already be fixed)")

# Fix 2: Remove old normal lookup lines that reference uvL/uvR/uvU/uvD etc
# These were from V5 and reference vars that no longer exist
old_normals = (
    "float3 nL=SceneTextureLookup(uvL,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nR=SceneTextureLookup(uvR,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nU=SceneTextureLookup(uvU,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nD=SceneTextureLookup(uvD,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nUL=SceneTextureLookup(uvUL,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nDR=SceneTextureLookup(uvDR,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nUR=SceneTextureLookup(uvUR,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float3 nDL=SceneTextureLookup(uvDL,PPI_WorldNormal,false).rgb*2.0-1.0;\n"
    "float normalDiverge = max(max(max(1.0-saturate(dot(nC,nL)),1.0-saturate(dot(nC,nR))),max(1.0-saturate(dot(nC,nU)),1.0-saturate(dot(nC,nD)))), max(max(1.0-saturate(dot(nC,nUL)),1.0-saturate(dot(nC,nDR))),max(1.0-saturate(dot(nC,nUR)),1.0-saturate(dot(nC,nDL)))));"
)

if old_normals in code:
    code = code.replace(old_normals, "")
    changes += 1
    print("[OK] Old normal lookup lines removed")
else:
    # Try individual lines
    count = 0
    for old_line in [
        "float3 nL=SceneTextureLookup(uvL,PPI_WorldNormal,false).rgb*2.0-1.0;",
        "float3 nR=SceneTextureLookup(uvR,PPI_WorldNormal,false).rgb*2.0-1.0;",
        "float3 nU=SceneTextureLookup(uvU,PPI_WorldNormal,false).rgb*2.0-1.0;",
        "float3 nD=SceneTextureLookup(uvD,PPI_WorldNormal,false).rgb*2.0-1.0;",
    ]:
        if old_line in code:
            code = code.replace(old_line, "")
            count += 1
    if count > 0:
        changes += 1
        print(f"[OK] Removed {count} old normal lookup lines (partial)")
    else:
        print("[SKIP] Old normal lookups not found — may already be removed")

# Also remove normalDiverge if still present
if "normalDiverge" in code and "float normalDiverge" in code:
    # Find and remove the normalDiverge line
    import re
    code = re.sub(r'float normalDiverge = [^;]+;', '', code)
    changes += 1
    print("[OK] normalDiverge removed")

# Fix 3: Also remove nC declaration if it's duplicated (we declare it inside the loop now)
old_nc = "float3 nC=normalize(SceneTextureLookup(uvC,PPI_WorldNormal,false).rgb*2.0-1.0);"
if old_nc in code:
    # Check if there's already a declaration inside the radial block
    # The radial block has: float3 nCnt = normalize...
    # But the old code also has: float3 nC = normalize...
    # Count occurrences
    if code.count(old_nc) > 1:
        # Remove all but the first or handle duplicates
        code = code.replace(old_nc, "", 1)  # remove first occurrence
        changes += 1
        print("[OK] Duplicate nC declaration removed")

if changes > 0:
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print(f"\n[DONE] Fix applied — {changes} changes, code length {len(code)}")

    # Quick verification
    rb = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
    rc = rb.get_editor_property("code")
    print(f"Verification: interleaved={'InterleavedGradientNoise' in rc} noUvL={'uvL' not in rc} story={'paperHash' in rc}")
else:
    print("\n[NOOP] No changes needed")
