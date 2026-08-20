"""Proof: dump the CURRENT canonical grade shader (deliberate-error trick on a
throwaway duplicate) and show the custom-node call-site — grading inputs must
come from preshader buffer slots, not 0.0 literals. Scratch is deleted after.
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "grade_wiring_proof.json"
SRC = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
SCRATCH = "/Game/EnvSandbox/Materials/_Scratch/M_PP_GradeDumpLab"


def main() -> dict:
    results: dict = {}
    if unreal.EditorAssetLibrary.does_asset_exist(SCRATCH):
        unreal.EditorAssetLibrary.delete_asset(SCRATCH)
    unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        "M_PP_GradeDumpLab", "/Game/EnvSandbox/Materials/_Scratch", unreal.load_asset(SRC))
    mat = unreal.load_asset(SCRATCH)
    custom = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat)
              if type(e).__name__ == "MaterialExpressionCustom"][0]
    code = custom.get_editor_property("code")
    custom.set_editor_property("code", code + "\nfloat zz_broken = ZZ_FORCE_DUMP;\n")
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        results["recompile"] = str(exc)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
    time.sleep(20)
    dumps = glob.glob(
        r"C:\EnvironmentPortfolio\BS_GodFile\Saved\ShaderDebugInfo\PCD3D_SM6\M_PP_GradeDumpLab*\*\*\PostProcessMaterialShaders.usf")
    results["dump_count"] = len(dumps)
    if dumps:
        lines = open(dumps[-1], encoding="utf-8", errors="replace").read().splitlines()
        call = [l for l in lines if "CustomExpression0(" in l and "Local" in l]
        results["call_site"] = call[-1].strip() if call else None
        results["preshader_slots"] = sum(1 for l in lines
                                         if "Material_PreshaderBuffer[" in l and "CustomExpression0" in l)
    if unreal.EditorAssetLibrary.does_asset_exist(SCRATCH):
        unreal.EditorAssetLibrary.delete_asset(SCRATCH)
        results["scratch_deleted"] = True
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    main()