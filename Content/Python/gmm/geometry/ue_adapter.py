"""Lazy Unreal adapter for GMM geometry modifier previews.

This module is safe to import outside Unreal. Unreal-specific imports and calls
are isolated inside functions so the contract and unit-test layers remain pure.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class UnrealGeometryError(RuntimeError):
    """Raised when an Unreal geometry operation cannot be completed safely."""


def unreal_available() -> bool:
    try:
        import unreal  # type: ignore[import-not-found]
    except ImportError:
        return False
    return hasattr(unreal, "DynamicMeshComponent") or hasattr(unreal, "GeometryScriptLibrary")


def _safe_engine_version(unreal_module: Any) -> str:
    try:
        system_library = getattr(unreal_module, "SystemLibrary", None)
        getter = getattr(system_library, "get_engine_version", None)
        value = getter() if callable(getter) else "unknown"
        return str(value)
    except Exception:
        return "unknown"


def _available_names(unreal_module: Any, keywords: tuple[str, ...]) -> list[str]:
    """Return stable, JSON-safe names matching capability keywords."""
    try:
        names = dir(unreal_module)
    except Exception:
        return []
    lowered = tuple(keyword.lower() for keyword in keywords)
    return sorted(
        name for name in names
        if any(keyword in name.lower() for keyword in lowered)
    )


def capabilities() -> dict[str, object]:
    """Report the live UE Python/API surface without making project changes.

    This intentionally discovers names instead of assuming a particular UE 5.x
    Geometry Script binding. The report is useful for selecting an adapter path
    in-editor and remains safe to call from standalone Python.
    """
    try:
        import unreal  # type: ignore[import-not-found]
    except ImportError:
        return {
            "ok": False,
            "state": "unavailable",
            "error": "Unreal Python API is unavailable outside UE",
            "engine_version": "unknown",
            "plugins": {"geometry_script": False, "modeling_tools": False},
            "classes": {"dynamic_mesh": [], "geometry_script": [], "mesh_components": []},
            "functions": {"conversion": [], "bevel": []},
        }

    names = {
        "dynamic_mesh": _available_names(unreal, ("dynamicmesh", "dynamic_mesh")),
        "geometry_script": _available_names(unreal, ("geometry", "meshdescription")),
        "mesh_components": _available_names(unreal, ("staticmeshcomponent", "dynamicmeshcomponent", "proceduralmesh")),
    }
    function_names = {
        "conversion": _available_names(unreal, ("copy", "convert", "mesh")),
        "bevel": _available_names(unreal, ("bevel",)),
    }
    geometry_script = bool(names["geometry_script"] or hasattr(unreal, "GeometryScriptLibrary"))
    dynamic_mesh = bool(names["dynamic_mesh"] or hasattr(unreal, "DynamicMesh"))
    modeling_tools = any("modeling" in name.lower() for name in dir(unreal))
    return {
        "ok": True,
        "state": "discovered",
        "engine_version": _safe_engine_version(unreal),
        "plugins": {
            "geometry_script": geometry_script,
            "modeling_tools": modeling_tools,
        },
        "classes": names,
        "functions": function_names,
        "selected_path": "dynamic_mesh_geometry_script" if geometry_script and dynamic_mesh else "unverified",
    }


def describe_actor(actor_path: str = "") -> dict[str, object]:
    """Describe a selected/ named actor without changing the level.

    The standalone response is deliberately structured so EnvUI callers can
    distinguish an unavailable editor from an invalid actor path.
    """
    if not actor_path.strip():
        return {"ok": False, "state": "invalid_request", "error": "actor_path is required"}
    if not unreal_available():
        return {
            "ok": False,
            "state": "unavailable",
            "actor_path": actor_path,
            "error": "Unreal editor is required for actor inspection",
        }
    return {
        "ok": False,
        "state": "adapter_pending",
        "actor_path": actor_path,
        "error": "Live actor inspection requires UE API verification",
    }


def describe_target(asset_path: str) -> dict[str, object]:
    """Inspect an Unreal asset without mutating it.

    The exact Dynamic Mesh API varies by UE/plugin build, so this function
    deliberately reports capability and asset identity first. Live mutation is
    enabled only after the editor-side adapter confirms its API surface.
    """
    if not asset_path.strip():
        return {"ok": False, "error": "asset_path is required"}
    if not unreal_available():
        return {
            "ok": False,
            "state": "unavailable",
            "asset_path": asset_path,
            "error": "Unreal Geometry Script API is unavailable outside UE",
        }

    import unreal  # type: ignore[import-not-found]

    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not asset:
        return {"ok": False, "asset_path": asset_path, "error": "asset not found"}
    return {
        "ok": True,
        "state": "inspected",
        "asset_path": asset_path,
        "class": asset.get_class().get_name(),
        "name": asset.get_name(),
    }


def preview_bevel(
    asset_path: str,
    parameters: Mapping[str, object],
    *,
    preview_actor: str = "",
) -> dict[str, object]:
    """Request a non-destructive bevel preview in Unreal.

    This is intentionally fail-closed until a live UE adapter is selected and
    verified. It prevents a command from silently baking or mutating assets.
    """
    if not unreal_available():
        return {
            "ok": False,
            "state": "unavailable",
            "asset_path": asset_path,
            "error": "UE editor is required for bevel preview",
        }
    return {
        "ok": False,
        "state": "adapter_pending",
        "asset_path": asset_path,
        "preview_actor": preview_actor,
        "parameters": dict(parameters),
        "error": "Geometry Script bevel backend requires live UE API verification",
    }


def reset_preview(preview_actor: str) -> dict[str, object]:
    if not preview_actor.strip():
        return {"ok": False, "error": "preview_actor is required"}
    return {
        "ok": False,
        "state": "adapter_pending",
        "preview_actor": preview_actor,
        "error": "Preview reset requires a live UE preview actor",
    }


def preview_boolean(
    asset_path: str,
    parameters: Mapping[str, object],
    *,
    preview_actor: str = "",
) -> dict[str, object]:
    """Request a non-destructive boolean preview in Unreal.

    This is intentionally fail-closed until a live UE adapter is selected and
    verified. It prevents a command from silently baking or mutating assets.
    """
    if not unreal_available():
        return {
            "ok": False,
            "state": "unavailable",
            "asset_path": asset_path,
            "error": "UE editor is required for boolean preview",
        }
    return {
        "ok": False,
        "state": "adapter_pending",
        "asset_path": asset_path,
        "preview_actor": preview_actor,
        "parameters": dict(parameters),
        "error": "Geometry Script boolean backend requires live UE API verification",
    }


def apply_boolean(asset_path: str, parameters: Mapping[str, object]) -> dict[str, object]:
    """Apply a boolean modifier to an asset in Unreal.

    Like preview_boolean, this is fail-closed outside the editor and will only
    be wired to live Geometry Script calls after the adapter path is verified.
    """
    if not unreal_available():
        return {
            "ok": False,
            "state": "unavailable",
            "asset_path": asset_path,
            "error": "UE editor is required for boolean application",
        }
    return {
        "ok": False,
        "state": "adapter_pending",
        "asset_path": asset_path,
        "parameters": dict(parameters),
        "error": "Geometry Script boolean backend requires live UE API verification",
    }
