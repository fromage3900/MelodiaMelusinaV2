"""Run inside the Unreal editor: re-apply the exterior kit HDA's true defaults BY NAME to STAGE_HouseExteriorKit_v1 (Houdini Engine
rebuild() keeps parameter values by position, so run this after every re-import + rebuild; see ue_reset_house_params.py)."""
import json
import unreal

REPORT = r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/HouseExterior_20261023/exterior_kit_gate.json"
LABEL = "STAGE_HouseExteriorKit_v1"


def run():
    controls = json.load(open(REPORT, encoding="utf-8"))["controls"]
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    act = [a for a in sub.get_all_level_actors() if a.get_actor_label() == LABEL][0]
    wr = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(world, act)
    tuples = wr.get_parameter_tuples()
    n = 0
    for name, val in controls.items():
        t = tuples.get(name)
        if t is None:
            continue
        if len(t.float_values) == 1:
            wr.set_float_parameter_value(name, float(val)); n += 1
        elif len(t.int32_values) == 1:
            wr.set_int_parameter_value(name, int(val)); n += 1
    print("%s: reset %d parameters by name, recook %s" % (LABEL, n, wr.recook()))


run()
