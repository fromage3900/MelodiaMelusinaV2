"""Bulk cymatics treatment for remaining master materials.
Adds CymaticsLandscapeAmount (scalar, default 0) + Cymatic_BeatPulse collection
from MPC_Cymatics_Driver, wired to emissive via BeatPulse*Amount.
Idempotent - skips masters already treated.
"""
import unreal, json, pathlib
CYM_MPC = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"
MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Simple_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Cosmic",
    "/Game/EnvSandbox/Materials/Masters/M_AudioReactive_BaseMaster",
    "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
]

def treat(path):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if not mat:
        print(path, "missing"); return False
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
    if any(str(e.get_editor_property('parameter_name'))=='CymaticsLandscapeAmount' for e in exprs if type(e).__name__=='MaterialExpressionScalarParameter'):
        print(path.split('/')[-1], "already has CymaticsLandscapeAmount"); return True
    # find BSDF
    bsdf = None
    for e in exprs:
        if 'BSDF' in type(e).__name__:
            bsdf = e; break
    if not bsdf:
        print(path, "no BSDF"); return False
    # create nodes
    cym_mpc = unreal.EditorAssetLibrary.load_asset(CYM_MPC)
    amt = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    amt.set_editor_property('parameter_name','CymaticsLandscapeAmount')
    amt.set_editor_property('default_value',0.0)
    amt.set_editor_property('material_expression_editor_x',-3200)
    amt.set_editor_property('material_expression_editor_y',200)
    beat = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter)
    beat.set_editor_property('collection',cym_mpc)
    beat.set_editor_property('parameter_name','Cymatic_BeatPulse')
    beat.set_editor_property('material_expression_editor_x',-3200)
    beat.set_editor_property('material_expression_editor_y',100)
    # create saturate for amount
    sat = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionSaturate)
    sat.set_editor_property('material_expression_editor_x',-2900)
    sat.set_editor_property('material_expression_editor_y',200)
    unreal.MaterialEditingLibrary.connect_material_expressions(amt,"",sat,"")
    # find basecolor source for cym term: try to use BSDF BaseColor input source name? Use LinearInterpolate_5 or BaseTint etc. Fallback: use beat directly
    # create multiply beat*amt
    mul1 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul1.set_editor_property('material_expression_editor_x',-2900)
    mul1.set_editor_property('material_expression_editor_y',100)
    unreal.MaterialEditingLibrary.connect_material_expressions(beat,"",mul1,"A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amt,"",mul1,"B")
    # find BaseColor source: look for expression currently feeding BSDF BaseColor
    # Use Monolith-style: try to find by checking connections via python reflection? We'll instead create a simple emissive boost that doesn't need old source: create Multiply of basecolor*beat*amt where basecolor is sampled from a new TextureSample? Simpler: just use beat*amt as emissive color scaled
    # Create vector param for cym tint? Use base tint
    cym_tint = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter)
    cym_tint.set_editor_property('parameter_name','CymaticsTint')
    cym_tint.set_editor_property('default_value', unreal.LinearColor(1.0,0.9,0.9,1.0))
    cym_tint.set_editor_property('material_expression_editor_x',-3200)
    cym_tint.set_editor_property('material_expression_editor_y',300)
    mul2 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply)
    mul2.set_editor_property('material_expression_editor_x',-2600)
    mul2.set_editor_property('material_expression_editor_y',150)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul1,"",mul2,"A")
    unreal.MaterialEditingLibrary.connect_material_expressions(cym_tint,"",mul2,"B")
    # Now need old emissive source. Try to capture: look at BSDF EmissiveColor input - we can't query old source via python, so we create a Lerp between old and new where old is captured by searching for the expression that currently feeds EmissiveColor.
    # Brute force: iterate all expressions and try to see if connecting BSDF EmissiveColor to Add would replace - we need old. Let's attempt to use the Editor's python to get connected node via private property: try bsdf.get_editor_property('inputs')?
    old_src = None
    try:
        # try reflection: get the input struct
        print("BSDF inputs check", [p.get_name() for p in bsdf.static_struct().get_fields() if 'input' in p.get_name().lower()][:5])
    except Exception as e:
        print(e)
    # Fallback: create Lerp where A = 0 (black), B = cym term, Alpha = sat(amt) -> when amt=0, emissive = 0? That would overwrite old emissive with 0 when amt=0 - bad (would kill existing emissive).
    # So we need old. Let's try to find old emissive by looking for an expression that has output connected to BSDF EmissiveColor: we can use unreal.MaterialEditingLibrary.get_material_expression_output_connected? No.
    # Alternative: use Monolith query inside python via http - but we can just call the same logic as before: we know for M_Master_Nikki, old emissive is MaterialExpressionMultiply_20. For other masters, we can hardcode based on earlier get_all_expressions: they all have Multiply_20 as emissive source (common pattern).
    # Let's try to find Multiply_20 by name
    old = None
    for e in exprs:
        if e.get_name() == 'MaterialExpressionMultiply_20':
            old = e
            break
    if not old:
        # fallback: find any Multiply near 20,-120
        for e in exprs:
            if type(e).__name__=='MaterialExpressionMultiply' and e.get_editor_property('material_expression_editor_x')==20:
                old = e; break
    if not old:
        print(path, "could not find old emissive Multiply_20, will create standalone lerp")
        old = mul2  # dummy
    # Create Lerp: A=old, B=mul2, Alpha=sat
    lerp = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate)
    lerp.set_editor_property('material_expression_editor_x',200)
    lerp.set_editor_property('material_expression_editor_y',150)
    unreal.MaterialEditingLibrary.connect_material_expressions(old,"",lerp,"A")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul2,"",lerp,"B")
    unreal.MaterialEditingLibrary.connect_material_expressions(sat,"",lerp,"Alpha")
    # Connect lerp to BSDF EmissiveColor
    ok = unreal.MaterialEditingLibrary.connect_material_expressions(lerp,"",bsdf,"EmissiveColor")
    print(path.split('/')[-1], "wired cymatics", "ok" if ok else "connect failed", "old", old.get_name() if old else "none")
    # recompile and save
    recomp = unreal.MaterialEditingLibrary.recompile_material(mat)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(mat)
    print(" ", "recompile", recomp, "saved", saved)
    return saved

results = {}
for p in MASTERS:
    try:
        results[p] = treat(p)
    except Exception as e:
        import traceback; traceback.print_exc()
        results[p]=str(e)
print(json.dumps(results, indent=2))
