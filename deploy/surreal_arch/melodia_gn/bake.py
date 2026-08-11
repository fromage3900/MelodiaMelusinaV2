"""Bake all melodia_gn node groups to a .blend library file.

Run once to persist generated GN trees so they can be linked from any .blend.
Importing melodia_gn triggers all module-level register_builder() calls, so
GROUP_BUILDERS is fully populated by the time bake_all() runs.
"""

from __future__ import annotations

import os
from pathlib import Path

import bpy

from .core import GROUP_BUILDERS
from .logging import log


DEFAULT_LIBRARY_NAME = "melodia_gn_library.blend"
LIBRARY_SUBDIR = "GN_Library"


def get_library_path(blend_path: str | None = None) -> str:
    """Resolve the library .blend path relative to the addon directory."""
    if blend_path:
        base = Path(blend_path).parent
    else:
        base = Path(__file__).parent.parent
    lib_dir = base / LIBRARY_SUBDIR
    lib_dir.mkdir(parents=True, exist_ok=True)
    return str(lib_dir / DEFAULT_LIBRARY_NAME)


def bake_all(blend_path: str | None = None, overwrite: bool = False) -> str:
    """Generate all melodia_gn node groups and save to a library .blend.

    Args:
        blend_path: Path to the .blend file to use as reference (optional).
        overwrite: Whether to regenerate existing trees.

    Returns:
        Path to the saved library file.
    """
    lib_path = get_library_path(blend_path)

    if not overwrite and os.path.exists(lib_path):
        # Append existing trees instead of rebuilding
        log.info("Library exists, appending trees from %s", lib_path)
        append_trees(lib_path)
        return lib_path

    log.info("Building %d node groups...", len(GROUP_BUILDERS))
    created = []
    for name, builder in sorted(GROUP_BUILDERS.items()):
        if name in bpy.data.node_groups and not overwrite:
            log.debug("Skipping '%s' (already exists)", name)
            continue
        try:
            builder(name)
            created.append(name)
            log.debug("Built '%s'", name)
        except Exception as e:
            log.error("Failed to build '%s'", name, exc=e)

    # Save after batch build
    if created:
        result = save_library(lib_path)
        log.info("Built %d/%d node groups", len(created), len(GROUP_BUILDERS))
        return result

    log.warning("No node groups were built")
    return lib_path


def append_trees(lib_path: str) -> list[str]:
    """Append node groups from an existing library .blend."""
    if not os.path.exists(lib_path):
        return []

    with bpy.data.libraries.load(lib_path) as (data_from, data_to):
        for nt in data_from.node_groups:
            if nt not in bpy.data.node_groups:
                data_to.node_groups.append(nt)

    return list(data_to.node_groups)


def save_library(lib_path: str | None = None) -> str:
    """Save all melodia_gn groups to library .blend."""
    lib_path = lib_path or get_library_path()

    # Collect our groups
    groups_to_save = [
        g for g in bpy.data.node_groups
        if g.name.startswith("MEL_")
    ]

    # Save to library (sets of datablocks, not dict)
    bpy.data.libraries.write(
        lib_path,
        set(groups_to_save),
        fake_user=True,
        compress=True,
    )
    log.info("Saved %d groups to %s", len(groups_to_save), lib_path)
    return lib_path


def load_library(lib_path: str | None = None) -> list[str]:
    """Load all groups from library into current .blend."""
    lib_path = lib_path or get_library_path()
    return append_trees(lib_path)
