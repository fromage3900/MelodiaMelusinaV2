"""Apply production-safe UI texture settings to the verified Figma universal assets."""
import unreal

ROOT = "/Game/Melodia/UI/Textures/Universal"
NAMES = (
    "T_Melodia_Universal_ParchmentFrame",
    "T_Melodia_Universal_SealSP",
    "T_Melodia_Universal_SealULT",
    "T_Melodia_Universal_RhythmLaneInk",
    "T_Melodia_Universal_Hitline",
    "T_Melodia_Universal_CornerBaroque",
    "T_Melodia_Universal_DividerScroll",
    "T_Melodia_Universal_CrestBaroque",
    "T_Melodia_Universal_MedallionRosette",
    "T_Melodia_Universal_BraceVolute",
)

configured = []
for name in NAMES:
    path = f"{ROOT}/{name}"
    texture = unreal.load_asset(path)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError(f"Missing universal UI texture: {path}")
    texture.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("srgb", True)
    texture.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    configured.append(path)

print(f"Configured {len(configured)} universal UI textures")
for path in configured:
    print(path)
