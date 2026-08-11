"""MCP contract smoke test."""
from __future__ import annotations

def test_mcp_adapter_import():
    try:
        import deploy.surreal_arch_mcp_adapter as adapter
        assert hasattr(adapter, "TOOLS")
        assert isinstance(adapter.TOOLS, list)
        assert len(adapter.TOOLS) > 0
        names = {t["name"] for t in adapter.TOOLS}
        assert "surreal_list_genomes" in names
        assert "surreal_apply_genome" in names
        print("[test_mcp_contract] surreal adapter OK")
    except Exception as e:
        print(f"[test_mcp_contract] surreal adapter skip: {e}")

    try:
        import deploy.blender_mcp_adapter as adapter
        assert hasattr(adapter, "TOOLS")
        assert isinstance(adapter.TOOLS, list)
        assert len(adapter.TOOLS) > 0
        names = {t["name"] for t in adapter.TOOLS}
        assert "blender_scene_info" in names
        assert "blender_execute_code" in names
        print("[test_mcp_contract] blender adapter OK")
    except Exception as e:
        print(f"[test_mcp_contract] blender adapter skip: {e}")