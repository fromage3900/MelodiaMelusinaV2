# -*- coding: utf-8 -*-
"""Canonical Melodia Portfolio Stage path resolution.

SSOT: Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend
(falls back to PortfolioStages / KitbashExport older stages)

Agent / CLI rule: never save over the live stage without
MELODIA_ALLOW_STAGE_SAVE=1. Prefer Sidecar copies (Saved/Audit/*.blend).
See Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md
"""
from __future__ import annotations

import os
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
ROOT = _TOOLS.parent

# Live stage often lives on G: even when Tools/ are opened from C:
_G_BS = Path(r"G:\EnvironmentPortfolio\BS_GodFile")

STAGE_CANDIDATES: tuple[Path, ...] = (
    _G_BS / "Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend",
    ROOT / "Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend",
    ROOT / "Exports" / "PortfolioStages" / "Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend",
    ROOT / "Exports" / "PortfolioStages" / "Melodia_Portfolio_Stage_v17_SIR_VISIBLE.blend",
    ROOT / "Exports" / "PortfolioStages" / "Melodia_Portfolio_Stage_v16_SIR_VISIBLE.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v14.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v10.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v9.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v8.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v7.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v4.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v3.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v2.blend",
    ROOT / "KitbashExport" / "Melodia_Portfolio_Stage.blend",
)

MELUSINA_RIG_BLEND = Path(r"G:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend")
EXPORTS_CLOTHES = ROOT / "Exports" / "MelusinaClothes"
AUDIT_INVENTORY = ROOT / "Saved" / "Audit" / "melusina_stage_mesh_inventory.json"

BLENDER_EXE_CANDIDATES: tuple[Path, ...] = (
    Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"),
)


def resolve_blender_exe() -> Path:
    env = os.environ.get("MELODIA_BLENDER", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p
    for p in BLENDER_EXE_CANDIDATES:
        if p.is_file():
            return p
    return Path("blender")


def resolve_stage_blend() -> Path:
    """Return first existing stage candidate (v22 ZenRebuild preferred)."""
    for p in STAGE_CANDIDATES:
        if p.is_file():
            return p
    return STAGE_CANDIDATES[0]


def resolve_stage_blend_str() -> str:
    return str(resolve_stage_blend())


def stage_save_allowed() -> bool:
    """Explicit opt-in required before any tool may write the portfolio stage."""
    return os.environ.get("MELODIA_ALLOW_STAGE_SAVE", "").strip() in ("1", "true", "yes")


def is_portfolio_stage_path(path: str | Path | None) -> bool:
    if not path:
        return False
    name = Path(path).name.lower()
    return name.startswith("melodia_portfolio_stage") and name.endswith(".blend")
