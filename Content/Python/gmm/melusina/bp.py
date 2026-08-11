"""Melusina exploration Blueprint tools — create, component wire, verify.

Wraps setup_melusina_exploration.create_exploration_blueprint().
Extends with MCP-backed blueprint operations when available.
"""
from __future__ import annotations

from gmm.core.audit import GmmAudit
from gmm.core.mcp_client import MonolithClient, MCPConnectionError


def create_exploration_bp() -> dict:
    """Create BP_Melusina_Exploration via duplicate of BP_Melusina."""
    audit = GmmAudit(action="melusina.bp_setup")
    try:
        import setup_melusina_exploration
        result = setup_melusina_exploration.create_exploration_blueprint()
        audit.ok(
            created=result.get("created", False),
            already_existed=result.get("already_existed", False),
            steps_taken=result.get("steps_taken", []),
        )
        audit.save("gmm_melusina_bp.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_bp.json")
        return audit.to_dict()


def add_camera_springarm(bp_path: str) -> dict:
    """Add SpringArm + Camera components to the exploration BP."""
    audit = GmmAudit(action="melusina.bp_add_camera")
    try:
        import unreal
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            raise ValueError(f"BP not found: {bp_path}")
        blueprint = unreal.BlueprintEditorLibrary.get_blueprint_from_asset(bp)
        if not blueprint:
            raise ValueError("Not a valid Blueprint")
        arm = unreal.BlueprintEditorLibrary.add_member_variable(
            blueprint, "SpringArm", unreal.Class.find("SpringArmComponent"),
        )
        cam = unreal.BlueprintEditorLibrary.add_member_variable(
            blueprint, "Camera", unreal.Class.find("CameraComponent"),
        )
        unreal.EditorAssetLibrary.save_asset(bp_path)
        audit.ok(bp_path=bp_path, springarm_added=bool(arm), camera_added=bool(cam))
        audit.save("gmm_melusina_bp_camera.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_bp_camera.json")
        return audit.to_dict()


def create_exploration_bp_via_mcp(source_path: str, dest_path: str, dest_name: str) -> dict:
    """Create exploration BP via MCP blueprint actions.
    
    Preferred method when Unreal Editor is running with MCP.
    """
    audit = GmmAudit(action="melusina.bp_setup_mcp")
    try:
        mc = MonolithClient()
        result = mc.duplicate_blueprint(
            source=source_path,
            dest_path=dest_path,
            dest_name=dest_name,
        )
        audit.ok(**result)
        audit.save("gmm_melusina_bp_mcp.json")
        return audit.to_dict()
    except MCPConnectionError as e:
        audit.fail(f"MCP connection failed: {e}")
        audit.save("gmm_melusina_bp_mcp.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_bp_mcp.json")
        return audit.to_dict()


def add_camera_via_mcp(bp_path: str) -> dict:
    """Add SpringArm + Camera via MCP blueprint actions."""
    audit = GmmAudit(action="melusina.bp_add_camera_mcp")
    try:
        mc = MonolithClient()
        # Add SpringArm component
        result_arm = mc.add_actor_component(
            bp_path=bp_path,
            component_class="SpringArmComponent",
            component_name="SpringArm",
        )
        # Add Camera component
        result_cam = mc.add_actor_component(
            bp_path=bp_path,
            component_class="CameraComponent",
            component_name="Camera",
        )
        audit.ok(
            bp_path=bp_path,
            springarm_result=result_arm,
            camera_result=result_cam,
        )
        audit.save("gmm_melusina_bp_camera_mcp.json")
        return audit.to_dict()
    except MCPConnectionError as e:
        audit.fail(f"MCP connection failed: {e}")
        audit.save("gmm_melusina_bp_camera_mcp.json")
        return audit.to_dict()
    except Exception as e:
        audit.fail_from_exception(e)
        audit.save("gmm_melusina_bp_camera_mcp.json")
        return audit.to_dict()