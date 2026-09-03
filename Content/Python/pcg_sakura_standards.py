"""Sakura PCG style constants — thin layer over pcg_portfolio_standards."""
from __future__ import annotations

from pcg_portfolio_standards import (  # noqa: F401
    ACTOR_EXCLUDE_PREFIX,
    ACTOR_SAKURA_VOLUME,
    DIR_STYLES,
    GRAPH_FOLIAGE,
    GRASS_SCALE_MAX,
    GRASS_SCALE_MIN,
    ISM_BAND_SAKURA,
    LEVEL_SAKURA,
    MI_SAKURA_GRASS,
    MI_SAKURA_PETALS,
    PCG_VOLUME_CENTER,
    PCG_VOLUME_SCALE,
    SCATTER_MESHES,
    SMC_SAKURA,
    TAG_EXCLUDE,
    TAG_GROUND,
    resolve_mesh,
)
from pcg_graph_builder import apply_transform, configure_spawner

PCG_ROOT = f"{DIR_STYLES}/Sakura"
COLLECTION_PATH = SMC_SAKURA
GRAPH_GROUND_COVER = GRAPH_FOLIAGE
LEVEL = LEVEL_SAKURA
ACTOR_PCG_VOLUME = ACTOR_SAKURA_VOLUME

MI_GRASS = MI_SAKURA_GRASS
MI_PETALS = MI_SAKURA_PETALS

GROUND_COVER_ISM_MIN = ISM_BAND_SAKURA[0]
GROUND_COVER_ISM_MAX = ISM_BAND_SAKURA[1]


def configure_grass_spawner(spawner_settings, material_path: str | None = None) -> bool:
    return configure_spawner(spawner_settings, "grass", material_path or MI_GRASS)


def apply_grass_transform(settings) -> None:
    apply_transform(settings, scale_min=GRASS_SCALE_MIN, scale_max=GRASS_SCALE_MAX)
