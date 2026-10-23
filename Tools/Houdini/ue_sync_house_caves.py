"""Run inside the Unreal editor (Monolith editor_query run_python, or Output Log: py <path>).

Copies every numeric parameter from STAGE_HouseTerrain_v2 onto STAGE_HouseCaves_v1, so both Houdini assets see the same
window / pad / horizon / cave seeds, then recooks the caves asset once. Houdini Engine drops mesh parts that share a geo with
heightfield volumes, so the terrain and the caves are two assets built from one builder (build_house_terrain_hda.py --caves).
Strings are skipped on purpose (string tuples read back misaligned through the wrapper)."""
import unreal

SRC, DST = "STAGE_HouseTerrain_v2", "STAGE_HouseCaves_v1"
SKIP = {"window_cx", "window_cz"}


def run():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    by = {a.get_actor_label(): a for a in sub.get_all_level_actors()}
    src = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(world, by[SRC])
    dst = unreal.HoudiniPublicAPIAssetWrapper.create_wrapper(world, by[DST])
    dst_t = dst.get_parameter_tuples()
    n = 0
    for name, t in src.get_parameter_tuples().items():
        if name in SKIP or name not in dst_t:
            continue
        if len(t.float_values) == 1:
            dst.set_float_parameter_value(name, t.float_values[0]); n += 1
        elif len(t.int32_values) == 1:
            dst.set_int_parameter_value(name, t.int32_values[0]); n += 1
    dst.recook()
    print("synced %d numeric parameters %s -> %s, caves recooked" % (n, SRC, DST))


run()
