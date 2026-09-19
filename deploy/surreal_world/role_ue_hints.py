"""ROLE_UE_HINTS — bpy-free SSOT shared by Blender export and the conductor.

Keep this file importable outside Blender. deploy/surreal_world/export.py is the
producer; Content/Python/import_world_manifest.py consumes the resulting
ue_material_hint strings. Do not invent a second hint table.

Default sacred slot is MI_Zen_Karesansui. ZEN_SHRINE style overrides remap
gate/sacred/large/monument onto the Zen MI set at export time.
"""
from __future__ import annotations

MATERIALS_ROOT = "/Game/EnvSandbox/Materials/Instances/Environment"

ROLE_UE_HINTS = {
    "large": f"{MATERIALS_ROOT}/Stylized/MI_Show_StoneCliff",
    "medium": f"{MATERIALS_ROOT}/Stylized/MI_Show_Default",
    "small": f"{MATERIALS_ROOT}/Stylized/MI_Show_Default",
    "wall": f"{MATERIALS_ROOT}/Stylized/MI_Trimsheet_HeavyWear",
    "corner_tower": f"{MATERIALS_ROOT}/Stylized/MI_Show_StoneCliff",
    "gate": f"{MATERIALS_ROOT}/Stylized/MI_Show_ContactRimHero",
    "monument": f"{MATERIALS_ROOT}/Stylized/MI_Show_StoneCliff",
    "sacred": f"{MATERIALS_ROOT}/Zen/MI_Zen_Karesansui",
    "joined_mesh": f"{MATERIALS_ROOT}/Stylized/MI_Show_Default",
}

STYLE_ROLE_OVERRIDES = {
    "ZEN_SHRINE": {
        "gate": f"{MATERIALS_ROOT}/Zen/MI_Zen_ToriiVermillion",
        "sacred": f"{MATERIALS_ROOT}/Zen/MI_Zen_HondenSanctum",
        "large": f"{MATERIALS_ROOT}/Zen/MI_Zen_MossGarden",
        "monument": f"{MATERIALS_ROOT}/Zen/MI_Zen_SakuraDrift",
    },
}

DEFAULT_HINT = f"{MATERIALS_ROOT}/Stylized/MI_Show_Default"


def material_hint(style: str | None, role: str | None) -> str:
    overrides = STYLE_ROLE_OVERRIDES.get(style or "", {})
    return overrides.get(role or "", ROLE_UE_HINTS.get(role or "", DEFAULT_HINT))
