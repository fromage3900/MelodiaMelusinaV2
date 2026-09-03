"""Fix potential causes: revert TP on universal, check MPC node placement."""
import unreal
MEL = unreal.MaterialEditingLibrary

# 1. Reset Toon Profile on universal master to None (restore original behavior)
mat = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
if mat:
    for expr in MEL.get_material_expressions(mat) or []:
        if type(expr).__name__ == "MaterialExpressionSubstrateToonBSDF":
            try:
                expr.set_editor_property("toon_profile", None)
                print("[OK] Reset universal master Toon Profile to None")
            except Exception as ex:
                print(f"[FAIL] Could not reset: {str(ex)[:80]}")
    unreal.EditorAssetLibrary.save_asset(mat.get_path_name())
    print("[OK] Saved")

# 2. Check Nikki master TP — should be TP_NikkiDream (that's correct)
mat2 = unreal.load_asset("/Game/EnvSandbox/Materials/_Scratch/M_Master_Nikki")
if mat2:
    for expr in MEL.get_material_expressions(mat2) or []:
        if type(expr).__name__ == "MaterialExpressionSubstrateToonBSDF":
            try:
                tp = expr.get_editor_property("toon_profile")
                tp_name = tp.get_name() if tp else "None"
                print(f"Nikki TP: {tp_name}")
            except:
                print("Nikki TP: could not read")
