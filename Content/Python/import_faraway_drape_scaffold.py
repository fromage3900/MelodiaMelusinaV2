"""Import scaffold for SK_FarawayMother_Drape (P2 Copernicus cloth).
Run in editor after Houdini bake exports SM_FabricRidge_Hero.fbx:
  unreal.EditorAssetLibrary.import_asset /Game/Melodia/P2_FarawayMother/Meshes/SK_FarawayMother_Drape
  Assign M_Cymatic_Faraway* + wire TensionMask -> MF_ClothWindDrape
  Validate with CymaticsAmount>0 in PIE
"""
import unreal, pathlib, json

FBX = pathlib.Path("Exports/Houdini/FarawayMother/SM_FabricRidge_Hero.fbx")
OUT = "/Game/Melodia/P2_FarawayMother/Meshes/SK_FarawayMother_Drape"

def main():
    if not FBX.exists():
        unreal.log_warning(f"[P2 Drape] FBX not yet baked: {FBX} - run Houdini GUI bake first")
        return {"status": "awaiting_bake", "fbx": str(FBX)}
    # Import via Interchange (skeleton, cloth)
    print(f"[P2 Drape] Import {FBX} -> {OUT} - wire to M_Cymatic_Faraway*")
    # TODO: call Interchange import, set skel, materials, save
    return {"status": "import_ready"}

if __name__ == "__main__":
    print(main())
