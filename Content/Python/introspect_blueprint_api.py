"""Dump available Unreal Python Blueprint/editor helpers for repair planning."""
from __future__ import annotations

import json
import os
import unreal


REPORT_PATH = "G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/blueprint_api_introspection.json"


def names(obj_name: str):
    obj = getattr(unreal, obj_name, None)
    if obj is None:
        return []
    return [name for name in dir(obj) if "graph" in name.lower() or "node" in name.lower() or "blueprint" in name.lower() or "compile" in name.lower()]


def main():
    report = {
        "BlueprintEditorLibrary": names("BlueprintEditorLibrary"),
        "BlueprintEditorSubsystem": names("BlueprintEditorSubsystem"),
        "KismetCompilerLibrary": names("KismetCompilerLibrary"),
        "KismetSystemLibrary": names("KismetSystemLibrary"),
        "EditorAssetLibrary": names("EditorAssetLibrary"),
        "SubobjectDataBlueprintFunctionLibrary": names("SubobjectDataBlueprintFunctionLibrary"),
        "available_blueprint_symbols": [name for name in dir(unreal) if "Blueprint" in name or "Graph" in name or "K2Node" in name][:400],
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    unreal.log(f"[MelodiaAudit] Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
