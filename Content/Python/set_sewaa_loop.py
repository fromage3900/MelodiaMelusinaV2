"""Set looping on the Sewaa BGM tracks and report durations."""
import unreal

for path in [
    "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Full",
    "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Inst",
]:
    sw = unreal.EditorAssetLibrary.load_asset(path)
    if sw:
        sw.set_editor_property("looping", True)
        dur = sw.get_editor_property("duration")
        sr = sw.get_editor_property("sample_rate")
        unreal.EditorAssetLibrary.save_loaded_asset(sw, only_if_is_dirty=False)
        print(f"LOOP_SET {path} dur={dur:.1f}s sr={sr}")
    else:
        print(f"LOAD_FAIL {path}")
