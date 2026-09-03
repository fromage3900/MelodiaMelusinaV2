"""Text-injection entry point for the official UE Level-to-PCG Data Asset export.

The source level is intentionally supplied by the caller so this helper never
silently edits a production map. Populate the source level with the authored
classic architecture library, then run this against a proof/staging level.
"""
from __future__ import annotations

from typing import Any


DEFAULT_DESTINATION = "/Game/EnvSandbox/PCG/Musical/Hero/Library"
DEFAULT_ASSET_NAME = "DA_ClassicArchitectureLibrary"


def export_classic_library(
    unreal: Any,
    source_level_path: str,
    destination_path: str = DEFAULT_DESTINATION,
    asset_name: str = DEFAULT_ASSET_NAME,
) -> dict[str, Any]:
    """Export a staging level through UPCGLevelToAsset via the project bridge."""
    library = getattr(unreal, "PCGScaleWorldEditorLibrary", None)
    if library is None:
        return {
            "success": False,
            "error": "PCGScaleWorldEditorLibrary is unavailable; rebuild/restart the editor first",
        }

    export = getattr(library, "export_level_to_pcg_data_asset", None)
    if export is None:
        return {
            "success": False,
            "error": "export_level_to_pcg_data_asset is unavailable in the reflected module",
        }

    result = str(export(source_level_path, destination_path, asset_name))
    success = not result.startswith("ERROR:") and bool(result)
    return {
        "success": success,
        "source_level": source_level_path,
        "destination_path": destination_path,
        "asset_name": asset_name,
        "package": result if success else None,
        "error": None if success else result,
        "production_maps_touched": False,
    }


def run(unreal: Any) -> dict[str, Any]:
    """Conservative default: require an explicit staging level from injection."""
    return {
        "success": False,
        "error": "Pass an explicit authored staging level to export_classic_library(unreal, source_level_path)",
        "production_maps_touched": False,
    }


if __name__ == "__main__":
    print("Use export_classic_library(unreal, source_level_path) from UE text injection.")
