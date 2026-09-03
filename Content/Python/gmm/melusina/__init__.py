"""Melusina character rig tools — assessment, blend space, BP setup, MPC bridge.

Phase 2 deliverable — wraps existing assess_melusina_rig, setup_melusina_exploration,
bridge_melusina_to_mpc into a unified API. Also provides MCP-backed variants.
"""
from __future__ import annotations

# Direct API wrappers
from gmm.melusina.rig import assess_rig
from gmm.melusina.blend import create_blend_space, add_sample
from gmm.melusina.bp import create_exploration_bp, add_camera_springarm
from gmm.melusina.mpc import get_mpc_params, bridge_catalog

# MCP-backed variants
from gmm.melusina.blend import create_blend_space_via_mcp, add_sample
from gmm.melusina.bp import create_exploration_bp_via_mcp, add_camera_via_mcp

__all__ = [
    # Direct API
    "assess_rig",
    "create_blend_space",
    "add_sample",
    "create_exploration_bp",
    "add_camera_springarm",
    "get_mpc_params",
    "bridge_catalog",
    # MCP-backed
    "create_blend_space_via_mcp",
    "create_exploration_bp_via_mcp",
    "add_camera_via_mcp",
]