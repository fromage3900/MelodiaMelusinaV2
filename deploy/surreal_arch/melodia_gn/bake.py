"""Bake all melodia_gn node groups to a .blend library file.

Run once to persist generated GN trees so they can be linked from any .blend.
Importing melodia_gn triggers all module-level register_builder() calls, so
GROUP_BUILDERS is fully populated by the time bake_all() runs.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

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


# ---------------------------------------------------------------------------
# Structural fingerprints (P2 regression baseline). Does NOT write a library.
# ---------------------------------------------------------------------------

HEAVY_TREES_51PLUS = (
    "MEL_escher_penrose_stairs",
    "MEL_nikki_quarter",
    "MEL_sky_observatory",
    "MEL_escher_waterfall",
    "MEL_escher_belvedere",
    "MEL_stepped_pyramid",
    "MEL_castle_siege_tower",
    "MEL_water_ripples",
    "MEL_water_gerstner",
    "MEL_castle_portcullis",
    "MEL_castle_barbican",
    "MEL_reed_body",
    "MEL_castle_gothic_window",
    "MEL_ornament_vine",
    "MEL_gazebo",
    "MEL_castle_assembler",
    "MEL_music_staff",
)


def _jsonable_default(value: Any) -> Any:
    """Normalize GN socket defaults so hashes are stable across runs."""
    if value is None:
        return None
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        try:
            return [_jsonable_default(x) for x in list(value)]
        except Exception:
            return str(value)
    return str(value)


def fingerprint_tree(ng) -> dict[str, Any]:
    """Stable structural fingerprint of one Geometry Node tree (no locations)."""
    nodes = []
    for node in sorted(ng.nodes, key=lambda n: n.name):
        nodes.append({
            "name": node.name,
            "type": getattr(node, "bl_idname", node.type),
            "inputs": [
                (s.identifier, s.name, s.type) for s in node.inputs
            ],
            "outputs": [
                (s.identifier, s.name, s.type) for s in node.outputs
            ],
        })
    links = sorted(
        (
            lnk.from_node.name,
            lnk.from_socket.identifier,
            lnk.to_node.name,
            lnk.to_socket.identifier,
        )
        for lnk in ng.links
    )
    iface: list[dict[str, Any]] = []
    try:
        for item in ng.interface.items_tree:
            if getattr(item, "item_type", "") != "SOCKET":
                continue
            default = None
            if hasattr(item, "default_value"):
                try:
                    default = _jsonable_default(item.default_value)
                except Exception:
                    default = None
            iface.append({
                "name": item.name,
                "in_out": getattr(item, "in_out", ""),
                "socket_type": getattr(item, "socket_type", ""),
                "default": default,
            })
    except Exception:
        pass
    payload = {
        "name": ng.name,
        "interface": iface,
        "links": links,
        "nodes": nodes,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return {
        "name": ng.name,
        "sha256": digest,
        "node_count": len(ng.nodes),
        "link_count": len(ng.links),
        "interface_count": len(iface),
    }


def fingerprint_builders(
    names: list[str] | tuple[str, ...] | None = None,
    *,
    construct: bool = True,
) -> dict[str, Any]:
    """Construct named trees via GROUP_BUILDERS (same loop as bake_all) and hash.

    Does not call save_library / libraries.write. Safe for factory-startup.
    """
    target = list(names) if names is not None else list(HEAVY_TREES_51PLUS)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for name in target:
        ng = bpy.data.node_groups.get(name)
        if ng is None and construct:
            builder = GROUP_BUILDERS.get(name)
            if builder is None:
                errors.append({"name": name, "error": "not in GROUP_BUILDERS"})
                continue
            try:
                built = builder(name)
                ng = built[0] if isinstance(built, (tuple, list)) else built
                if ng is None:
                    ng = bpy.data.node_groups.get(name)
            except Exception as exc:
                errors.append({"name": name, "error": str(exc)})
                continue
        if ng is None:
            errors.append({"name": name, "error": "tree missing after construct"})
            continue
        try:
            results.append(fingerprint_tree(ng))
        except Exception as exc:
            errors.append({"name": name, "error": f"fingerprint failed: {exc}"})
    return {
        "ok": not errors,
        "count": len(results),
        "trees": results,
        "errors": errors,
        "algorithm": "sha256 of canonical JSON (nodes+links+interface; no locations)",
    }
