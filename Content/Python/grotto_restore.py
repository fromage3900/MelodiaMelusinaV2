"""Copy the 4 Grotto SDF masters into EnvSandbox/Materials/SDF/ so the orphaned MIs resolve."""
import unreal

SRC = "/Game/_PROJECT/04_Materials/SDF"
DST = "/Game/EnvSandbox/Materials/SDF"

MASTERS = [
    "M_SDF_Bioluminescence",
    "M_SDF_BubbleColumn",
    "M_SDF_CoralBranching",
    "M_SDF_FloatingNotes",
]

for name in MASTERS:
    src_path = f"{SRC}/{name}"
    dst_path = f"{DST}/{name}"
    src_exists = unreal.EditorAssetLibrary.does_asset_exist(src_path)
    dst_exists = unreal.EditorAssetLibrary.does_asset_exist(dst_path)
    if not src_exists:
        # try Underwater subfolder
        src_path = f"{SRC}/Underwater/{name}"
        src_exists = unreal.EditorAssetLibrary.does_asset_exist(src_path)
    if src_exists and not dst_exists:
        ok = unreal.EditorAssetLibrary.duplicate_asset(src_path, dst_path)
        unreal.log(f"[GrottoRestore] {name}: duplicated -> {ok}")
    elif dst_exists:
        unreal.log(f"[GrottoRestore] {name}: already at dst")
    else:
        unreal.log(f"[GrottoRestore] {name}: SOURCE MISSING")

# Verify the 5 MIs now resolve
MIS = [
    "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_Bioluminescence",
    "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_BubbleColumn",
    "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_CoralBranching",
    "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_FloatingNotes",
    "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_CrystallineSpire",
]
for mi in MIS:
    obj = unreal.load_asset(mi)
    par = obj.get_editor_property("parent") if obj else None
    unreal.log(f"[GrottoVerify] {mi.split('/')[-1]}: parent={par.get_path_name() if par else 'NONE'}")
