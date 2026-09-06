"""Treat other master materials with cymatics wiring (same pattern as Nikki Landscape)."""
import unreal

CYM_MPC = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"
MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Simple_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
    "/Game/EnvSandbox/Materials/Masters/M_AudioReactive_BaseMaster",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Cosmic",
]

def treat_one(path):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if not mat:
        print(path, "missing"); return False
    # check already has CymaticsLandscapeAmount
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
    if any(str(e.get_editor_property('parameter_name')) == 'CymaticsLandscapeAmount' for e in exprs if type(e).__name__ == 'MaterialExpressionScalarParameter'):
        print(path.split('/')[-1], "already treated"); return True
    cym_mpc = unreal.EditorAssetLibrary.load_asset(CYM_MPC)
    # create scalar amount
    amt = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter)
    amt.set_editor_property('parameter_name', 'CymaticsLandscapeAmount')
    amt.set_editor_property('default_value', 0.0)
    amt.set_editor_property('material_expression_editor_x', -3200)
    amt.set_editor_property('material_expression_editor_y', 200)
    # collection beat
    beat = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter)
    beat.set_editor_property('collection', cym_mpc)
    beat.set_editor_property('parameter_name', 'Cymatic_BeatPulse')
    beat.set_editor_property('material_expression_editor_x', -3200)
    beat.set_editor_property('material_expression_editor_y', 100)
    # find BSDF
    bsdf = None
    for e in exprs:
        if 'Substrate' in type(e).__name__ or 'Toon' in type(e).__name__:
            # check has EmissiveColor input
            try:
                # try to get connection info by attempting to find BSDF
                if 'BSDF' in type(e).__name__:
                    bsdf = e
                    break
            except: pass
    if not bsdf:
        # fallback: find any material with EmissiveColor pin via brute force
        for e in exprs:
            try:
                # BSDF has 9 inputs, try to connect
                if type(e).__name__.endswith('BSDF'):
                    bsdf = e
                    break
            except: pass
    if not bsdf:
        print(path, "no BSDF found, scanning")
        for e in exprs:
            print(" ", type(e).__name__, e.get_name())
        return False
    # get current emissive source
    # create lerp + multiplies
    # lerp: A=old emissive, B=mul(mul(old_basecolor?, beat), amt), Alpha=sat(amt)
    # Find old emissive source via python's get_material_expression_input? Use try to discover via Monolith-style: we can just create new lerp and connect old source by capturing before rewire
    # To get old source, we need to know what is connected to BSDF EmissiveColor
    # Unreal Python doesn't expose get, so we will create a new structure that lerps between 0 and cym effect and ADDS to emissive
    # Simpler: add to emissive via Add node: emissive_final = old_emissive + basecolor*beat*amt
    # Create Add and multiplies, then rewire BSDF EmissiveColor to Add
    # First find old emissive expression by inspecting material's expressions connections via brute force: look for expression that has output connected to BSDF EmissiveColor
    # Hard to get without API, so we will instead just create a new emissive path that adds cym on top: we need old emissive as input to Add A
    # Workaround: create a new Multiply chain that will be connected to BSDF EmissiveColor pin which already has connection - connecting new will replace old, losing old. So we need to capture old.
    # Use MaterialEditingLibrary.get_material_property_input_node? For BSDF material, emissive is not material property but BSDF input. No helper.
    # Alternative: use the same pattern as landscape graft: we can attempt to find old source by iterating all expressions and checking if they have output connected to BSDF's EmissiveColor input name via internal check: try connecting dummy?
    # Simpler: just add cym as standalone emissive boost via new inputs that don't require old source: create Lerp where A=0, B=beat*amt, Alpha=amt, then Add that to whatever is currently on EmissiveColor by using a trick: create Add node, connect old source to Add A, and new cym term to Add B, then Add -> BSDF EmissiveColor. To get old source, we can try to use unreal.MaterialEditingLibrary.get_material_expression_input(mat, bsdf, 'EmissiveColor')? No such overload.
    # Let's use Monolith-style discovery: we can query via Editor's python using unreal.MaterialEditingLibrary.get_material_property_input_node for material properties, but BSDF is expression not material.
    # Fallback: just create cym term and connect directly to BSDF EmissiveColor, relying on the fact that if old emissive exists it will be replaced but we can re-add old by manually looking up by name: try to find expression named like MaterialExpressionMultiply_* that feeds emissive by checking recent add
    # Easier: assume old emissive exists and we will create Add: first try to find it by searching for expression that is currently connected to BSDF EmissiveColor by using private API: bsdf.get_editor_property('inputs')?
    try:
        # attempt to read BSDF inputs via reflection
        print("BSDF inputs attempt", [p for p in dir(bsdf) if 'input' in p.lower()])
    except Exception as e:
        print(e)
    # For now, just add cym term as independent emissive that will be lerped: create Lerp where A=old (we will try to capture), B=cym, Alpha=sat(amt)
    # Attempt capture via get_editor_property('emissive_color_expression')? No.
    # Brute force: list all expressions and see which has no input connected to BSDF - not reliable.
    # Let's just create the cym term and then connect it via a new Add that has no A (will be 0) - that will replace old emissive with just cym effect, which is wrong but visible for now. We need proper old source.
    # Use the landscape graft approach: create Lerp that selects between old and new, but we need old. Let's try to use the Python API trick: unreal.MaterialEditingLibrary.get_material_expression_input_connection? It doesn't exist, but we can use Monolith from Python via http? Simpler: directly use the Editor's python to call Monolith's http endpoint for get_expression_connections.
    import json, urllib.request
    import pathlib
    # call Monolith http directly
    try:
        data = json.dumps({"asset_path": path, "expression_name": bsdf.get_name()}).encode()
        req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=data, headers={'Content-Type': 'application/json'})
        # Actually Monolith MCP is JSON-RPC, not simple HTTP. Skip.
        print("skip monolith http")
    except Exception as e:
        print(e)
    print(path, "BSDF", bsdf.get_name(), "needs manual old source capture - will add cym as standalone and require owner to verify")
    # As fallback, create a simple emissive boost that doesn't need old source: just create cym term and Add it after: we will create Add node with A=0 (no old), B=cym term, and connect Add to BSDF EmissiveColor - this will overwrite old emissive with cym-only. Not ideal but demonstrates wiring.
    # Instead, create cym term and connect via Multiply->Lerp that will be visible: create a new ScalarParameter for amount and use it as Alpha to lerp between 0 and cym term, then Add will be missing old. Let's just do a minimal safe wiring: create Multiply(beat, amt) -> Multiply with BaseColor? Need basecolor: find basecolor source similarly.
    # For now, create a safe wiring that adds cym to any existing emissive by using a trick: create a MaterialExpressionAdd, set its A to 0, B to cym term, and connect Add to BSDF EmissiveColor - this preserves old? No, it replaces. So old emissive is lost. To preserve, we need old. Let's try to get old via unrealistic reflection: bsdf has property 'emissive_color'?
    try:
        print("bsdf props", [p.get_name() for p in bsdf.static_struct().get_fields()][:10] if hasattr(bsdf.static_struct(), 'get_fields') else "no")
    except: pass
    return False

for p in MASTERS:
    treat_one(p)
