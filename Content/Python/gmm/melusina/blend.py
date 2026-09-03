"""Melusina blend space tools — create, edit, add samples, verify.

Wraps setup_melusina_exploration.create_blend_space().
Extends with MCP-backed blend space operations when available.
"""
from __future__ import annotations

from gmm.core.audit import GmmAudit
from gmm.core.mcp_client import MonolithClient, MCPConnectionError


def create_blend_space_via_mcp(
    asset_path: str,
    skeleton_path: str,
    samples: list[dict] | None = None,
    axis_name: str = "Speed",
    axis_min: float = 0.0,
    axis_max: float = 600.0,
) -> dict:
    """Create a 1D blend space via MCP animation actions (create_blend_space_1d +
    add_blendspace_sample). Preferred method when Unreal Editor is running with MCP.

    `samples` is a list of {"anim_path": str, "x": float} dicts.
    """
    audit = GmmAudit(action="melusina.blend_setup_mcp")
    try:
        mc = MonolithClient()
        created = mc.call_action("animation", "create_blend_space_1d", {
            "asset_path": asset_path,
            "skeleton_path": skeleton_path,
            "axis_name": axis_name,
            "axis_min": axis_min,
            "axis_max": axis_max,
        })
        added = []
        for s in (samples or []):
            r = mc.call_action("animation", "add_blendspace_sample", {
                "asset_path": asset_path,
                "anim_path": s["anim_path"],
                "x": s["x"],
                "y": s.get("y", 0.0),
            })
            added.append(r)
        audit.ok(asset_path=asset_path, created=created, samples_added=len(added), sample_results=added)
        audit.save("gmm_melusina_blend_mcp.json")
        return audit.to_dict()
    except MCPConnectionError as e:
        audit.fail(f"MCP connection failed: {e}")
        audit.save("gmm_melusina_blend_mcp.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_blend_mcp.json")
        return audit.to_dict()


def create_blend_space() -> dict:
    """Create BS_Locomotion blend space for Melusina.

    Falls back to direct API (setup_melusina_exploration) when MCP unavailable.
    """
    audit = GmmAudit(action="melusina.blend_setup")
    try:
        import setup_melusina_exploration
        result = setup_melusina_exploration.create_blend_space()
        if result.get("created"):
            audit.ok(
                path=result.get("path"),
                samples_added=result.get("samples_added", 0),
                sample_details=result.get("sample_details", []),
                method_used=result.get("method_used"),
            )
        else:
            audit.warn(result.get("error", "unknown"))
            audit.ok(**result)
        path = audit.save("gmm_melusina_blend.json")
        audit.data["audit_path"] = path
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_blend.json")
        return audit.to_dict()


def add_sample(blend_space_path: str, animation_path: str, speed: float) -> dict:
    """Add a single animation sample to a blend space (via direct API)."""
    audit = GmmAudit(action="melusina.blend_add_sample")
    try:
        import unreal
        bs = unreal.EditorAssetLibrary.load_asset(blend_space_path)
        anim = unreal.EditorAssetLibrary.load_asset(animation_path)
        if not bs or not anim:
            raise ValueError("Asset not found")
        bs.add_sample(anim, speed)
        unreal.EditorAssetLibrary.save_asset(blend_space_path)
        audit.ok(blend_space=blend_space_path, animation=animation_path, sample_value=speed)
        audit.save("gmm_melusina_blend_sample.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_blend_sample.json")
        return audit.to_dict()
