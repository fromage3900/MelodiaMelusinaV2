"""Inspect landscape material candidates for ZenForestTest's Landscape2."""
from __future__ import annotations

import unreal

for path in ("/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_NikkiDream",
             "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SakuraGarden"):
    obj = unreal.load_asset(path)
    if not obj:
        print(path, "MISSING")
        continue
    parent = obj.get_editor_property("parent")
    pp = str(parent.get_path_name()) if parent else None
    layers = 0
    layer_blend = False
    if parent:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(parent) or []:
            cn = type(e).__name__
            if cn in ("MaterialExpressionLandscapeLayerBlend", "MaterialExpressionLandscapeLayerWeight",
                      "MaterialExpressionLandscapeLayerCoords"):
                layer_blend = True
            if cn.startswith("MaterialExpressionLandscapeLayer"):
                layers += 1
    overrides = 0
    try:
        overrides = len(obj.get_editor_property("scalar_parameter_values") or [])
    except Exception:
        pass
    print(f"{path.split('/')[-1]}: parent={pp} layer_exprs={layers} layer_blend={layer_blend} scalar_overrides={overrides}")