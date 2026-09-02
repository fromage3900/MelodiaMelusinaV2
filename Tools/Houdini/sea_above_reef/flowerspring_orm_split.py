#!/usr/bin/env python
"""Split the packed ORM maps into per-channel maps for Substance Painter.

Painter's fill-layer API sets one bitmap per channel, so each variant gets
T_<V>_AO.png / T_<V>_Roughness.png / T_<V>_Metallic.png next to the packed
T_<V>_ORM.png (which is kept for UE import).

Run: python Tools/Houdini/sea_above_reef/flowerspring_orm_split.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

STAGE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/"
             "substance_staging/FlowerSpring/textures")

VARIANTS = ["FlowerSpring", "GildedLoom", "SilkWaterfall", "CherryBlossomWood", "StarlitAbyss"]

result = {}
for v in VARIANTS:
    vdir = STAGE / v
    orm_path = vdir / f"T_{v}_ORM.png"
    if not orm_path.exists():
        result[v] = "MISSING_ORM"
        continue
    arr = np.asarray(Image.open(orm_path).convert("RGB"), np.uint8)
    for name, ch in (("AO", 0), ("Roughness", 1), ("Metallic", 2)):
        Image.fromarray(arr[..., ch], mode="L").save(str(vdir / f"T_{v}_{name}.png"))
    result[v] = 3
    print(f"[split] {v}: AO/Roughness/Metallic written")

(STAGE.parent / "flowerspring_orm_split_manifest.json").write_text(
    json.dumps({"schema": "melodia.flowerspring_orm_split.v1",
                "channels": "R=AO G=Roughness B=Metallic", "result": result}, indent=1),
    encoding="utf-8")
print("ORM_SPLIT_DONE " + json.dumps(result))
