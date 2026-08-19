"""Dry-run / run the Substrate Toon converter on the Electric Dreams master set
(MSPresets + Custom MS masters). Wraps convert_masters_to_substrate_toon.main()
with an explicit --paths list so the queue stays unchanged.

Usage via Monolith run_python (execute_file):
  dry_run:  --dry-run
  convert:  (no extra flag)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import unreal

ED_MASTERS = [
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CNR",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CR",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliage",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoOpacity",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoOpacityNoWPO",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoWPO",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/M_DefaultTextEmissive",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/M_MS_Default_Material_VT_DynamicLayering",
    "/Game/MSPresets/MS_Foliage_Material_LATEST/AssetZooMaterials/M_FloorGrid_Master",
    "/Game/MSPresets/MS_Foliage_Material_LATEST/GlobalFoliageActor/Materials/M_UI_Element",
    "/Game/MSPresets/MS_Foliage_Material_LATEST/MasterMaterials/M_Foliage",
    "/Game/MSPresets/M_MS_Billboard_Material/M_MS_Billboard_Material",
    "/Game/MSPresets/M_MS_Decal_Material_VT/M_MS_Decal_Material_VT",
    "/Game/MSPresets/M_MS_Decal_Material_VT/M_MS_Decal_Material_VT_NoNormalAlbedo1",
    "/Game/MSPresets/M_MS_Default_Material/M_MS_Default_Material",
    "/Game/MSPresets/M_MS_Default_Material_VT/M_MS_Default_Material_VT",
    "/Game/MSPresets/M_MS_Default_Material_VT/M_MS_Default_Material_VT_WaterTest",
    "/Game/MSPresets/M_MS_Foliage_Material/M_MS_Foliage_Material",
    "/Game/MSPresets/M_MS_Surface_Material/M_MS_Surface_Material",
    "/Game/MSPresets/M_MS_Surface_Material_VT/M_MS_Surface_Material_VT",
]


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    sys.argv = ["convert_ed_masters.py", "--paths", *ED_MASTERS] + (["--dry-run"] if dry else [])
    import convert_masters_to_substrate_toon as conv

    return conv.main()


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
