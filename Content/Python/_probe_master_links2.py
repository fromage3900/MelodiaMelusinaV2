"""Check SubstrateToon output wiring and ToonProfile refs on universal master."""
import unreal
import material_lib as lib

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
m = unreal.load_asset(MASTER)
exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(m) or [])

toon = [e for e in exprs if e and "SubstrateToonBSDF" in type(e).__name__]
unreal.log(f"[LinkProbe] toon_nodes={len(toon)}")

outputs = []
try:
    outputs = list(m.get_editor_property("material_outputs") or [])
except Exception:
    pass
unreal.log(f"[LinkProbe] material_outputs={outputs}")

for e in exprs:
    if e and "MaterialExpressionMaterialFunctionCall" in type(e).__name__:
        mf = e.get_editor_property("material_function")
        if mf:
            unreal.log(f"[LinkProbe] mf_call={mf.get_name()}")

profiles = lib.create_toon_profiles(["TP_Default"])
unreal.log(f"[LinkProbe] TP_Default exists={profiles.get('TP_Default') is not None}")

# Check if FrontMaterial connected
for e in exprs:
    tname = type(e).__name__
    if "SubstrateFrontMaterial" in tname or "MaterialExpressionSubstrate" in tname:
        unreal.log(f"[LinkProbe] substrate_expr={tname}")

unreal.log(f"[LinkProbe] path={m.get_path_name()}")
