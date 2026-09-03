"""List engine NiagaraSystem assets under /Niagara/."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.search_all_assets(True)
filter = unreal.ARFilter(
    class_names=["NiagaraSystem"],
    package_paths=["/Niagara"],
    recursive_paths=True,
)
assets = ar.get_assets(filter)
out = []
for ad in assets[:80]:
    out.append(
        {
            "path": str(ad.package_name),
            "asset": str(ad.asset_name),
        }
    )

report = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "niagara_engine_systems.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps({"count": len(assets), "samples": out}, indent=2), encoding="utf-8")
print(f"found {len(assets)} systems, wrote {len(out)} samples")
