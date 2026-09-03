"""Small contract fixture used by tests and dry-run tooling."""
from __future__ import annotations


def musical_ornament_manifest() -> dict:
    return {
        "format": "melodia_project_manifest_v1",
        "project_id": "BS_GodFile",
        "asset_id": "ornament_vault_ribs",
        "source": {
            "application": "blender",
            "generator": "melodia_gn",
            "generator_version": "0.1.0",
            "git_revision": "fixture",
        },
        "style_id": "MELODIA_STAGE",
        "units": "meters",
        "coordinate_system": "blender_z_up",
        "roles": ["musical_ornament", "hero"],
        "instances": [{
            "role": "musical_ornament",
            "transform": [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
        }],
        "material_hints": [{"role": "ornament", "ue_material_hint": "gilded"}],
        "validation": {"status": "passed", "errors": [], "warnings": []},
    }
