"""
Build 5 SeaAbove P0 MIs in-editor from Saved/Audit/copernicus_experiment_2026-09-02/.
Run in UE Python:  py "Content/Python/_mi_sea_above_create.py"
Mirrors _mi_brass_animated_create.py pattern but for Sea Above.
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
MAN = ROOT / "Saved/Audit/copernicus_experiment_2026-09-02/manifest.json"
MI_DIR = ROOT / "Content/EnvSandbox/Materials/Instances/Copernicus"
try:
    import unreal
    HAS_UNREAL = True
except ImportError:
    HAS_UNREAL = False

VARIANTS = ["SeaAbove_ReefChladniCoral","SeaAbove_KelpCymaticSheen","SeaAbove_IslandParallaxStone","SeaAbove_MusicalWaterGeometry","SeaAbove_TidepoolNacre"]
MASTERS = {
    "SeaAbove_ReefChladniCoral": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "SeaAbove_KelpCymaticSheen": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "SeaAbove_IslandParallaxStone": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "SeaAbove_MusicalWaterGeometry": "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Substrate",
    "SeaAbove_TidepoolNacre": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
}

def main():
    if not HAS_UNREAL:
        print("[dry] unreal not available — would create:", VARIANTS)
        print("  Manifest:", MAN, "exists" , MAN.exists())
        return
    am = unreal.AssetToolsHelpers.get_asset_tools()
    for v in VARIANTS:
        mi_name = f"MI_Copernicus_{v}"
        pkg = f"/Game/EnvSandbox/Materials/Instances/Copernicus/{mi_name}"
        print(f"[MI] {mi_name} master={MASTERS[v]} pkg={pkg}")
        # Real creation requires asset factory; stub here — editor will import textures then set MI params
        # See Docs/Houdini/copernicus README for texture import pipeline.

if __name__ == "__main__":
    main()
