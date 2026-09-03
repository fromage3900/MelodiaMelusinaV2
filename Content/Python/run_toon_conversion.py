"""UE entrypoint: convert all masters, fix MCP params, assign instance profiles."""
import sys
import time

import unreal as _unreal

time.sleep(20)

# Restore M_Toon_SDF if template graph was wiped; fix MeshBlend refs before conversion

_toon_sdf = "/Game/EnvSandbox/Materials/Masters/M_Toon_SDF"
if _unreal.EditorAssetLibrary.does_asset_exist(_toon_sdf):
    _mat = _unreal.load_asset(_toon_sdf)
    if _mat and len(list(_unreal.MaterialEditingLibrary.get_material_expressions(_mat))) == 0:
        _unreal.log_warning("[ToonConversion] M_Toon_SDF empty â€” rebuilding via setup_sdf_materials")
        import setup_sdf_materials

        setup_sdf_materials.build_all()


sys.argv = [
    "run_toon_conversion.py",
    "--batch",
    "all",
    "--fix-params",
    "--assign-profiles",
    "--finish",
]

from convert_masters_to_substrate_toon import main

raise SystemExit(main())
