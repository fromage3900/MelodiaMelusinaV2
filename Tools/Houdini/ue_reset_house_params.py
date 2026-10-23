"""Run inside the Unreal editor. Re-applies the HDA's true defaults (from Saved/Audit/HouseTerrain_20261023/terrain_gate.json,
written by build_house_terrain_hda.py) to STAGE_HouseTerrain_v2 and STAGE_HouseCaves_v1 by NAME.

Why: Houdini Engine's rebuild() keeps parameter values by POSITION, so after the HDA definition gains parameters the stored
values land on the wrong names (cave_min_slope became 75, rock thresholds landed in the cave search radii). Run this after
every re-import + rebuild, then ue_sync_house_caves.py is optional."""
import json
import unreal

REPORT = r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/HouseTerrain_20261023/terrain_gate.json"
LABELS = ("STAGE_HouseTerrain_v2", "STAGE_HouseCaves_v1")


def run():
    controls = json.load(open(REPORT, encoding="utf-8"))["controls"]
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    by = {a.get_actor_label(): a for a in sub.get_all_level_actors()}
    for label in LABELS:
        wr = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(world, by[label])
        tuples = wr.get_parameter_tuples()
        n = 0
        for name, val in controls.items():
            t = tuples.get(name)
            if t is None:
                continue
            if isinstance(val, str):
                wr.set_string_parameter_value(name, val)
            elif len(t.float_values) == 1:
                wr.set_float_parameter_value(name, float(val))
            elif len(t.int32_values) == 1:
                wr.set_int_parameter_value(name, int(val))
            else:
                continue
            n += 1
        print("%s: reset %d parameters by name, recook %s" % (label, n, wr.recook()))


run()
