"""Monolith MCP HTTP client — wraps all editor.animation.mesh.blueprint actions.

Usage:
    from gmm.core import MonolithClient
    mc = MonolithClient()
    status = mc.status()
    result = mc.run_python("print('hello')", mode="execute_statement")
    tools = mc.discover("editor")
"""
from __future__ import annotations

import json
import sys
from typing import Any


class McpError(Exception):
    """Raised when an MCP call returns an error payload."""

    def __init__(self, message: str, code: int | None = None, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class MonolithClient:
    """Stateless HTTP client for the Monolith MCP server (default port 9316)."""

    def __init__(self, host: str = "localhost", port: int = 9316, timeout: int = 60):
        self.base_url = f"http://{host}:{port}"
        self.mcp_url = f"{self.base_url}/mcp"
        self.health_url = f"{self.base_url}/health"
        self.timeout = timeout
        self._request_id = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(self, namespace: str | None = None, **kwargs) -> dict:
        """List available tools in a namespace.

        Args:
            namespace: Filter to a specific namespace (e.g. "editor", "animation").
            **kwargs: Pass detail=True for full schemas, filter/offset/limit.

        Returns:
            Per-action param schemas (or terse names+descriptions).
        """
        params = kwargs.copy()
        if namespace:
            params["namespace"] = namespace
        return self.call_action("monolith", "discover", params)

    def status(self) -> dict:
        """Monolith server health: version, uptime, action count, engine."""
        try:
            return self._get_json(self.health_url)
        except MCPConnectionError:
            return self.call_action("monolith", "status")

    def call_action(self, namespace: str, action: str, params: dict | None = None) -> dict:
        """Execute an MCP action.

        POST to http://host:port with
        {"namespace": ns, "action": action, "params": {...}}
        """
        params = params or {}
        special_tools = {
            ("monolith", "discover"): "monolith_discover",
            ("monolith", "status"): "monolith_status",
            ("monolith", "guide"): "monolith_guide",
        }
        tool_name = special_tools.get((namespace, action))
        if tool_name:
            arguments = params
        else:
            tool_name = f"{namespace}_query"
            arguments = {"action": action, "params": params}
        return self._call_tool(tool_name, arguments)

    def run_python(
        self,
        command: str,
        mode: str = "execute_statement",
        unattended: bool = True,
        file_scope: str = "private",
    ) -> dict:
        """Execute Python in the editor via editor.run_python.

        Args:
            command: Inline code or file path.
            mode: execute_file, execute_statement, or evaluate_statement.
            unattended: Suppress UI dialogs.
            file_scope: private (isolated) or public (shared with REPL).

        Returns:
            {"success": bool, "output": [...], "evaluated_result": ...}
        """
        return self.call_action("editor", "run_python", {
            "command": command,
            "mode": mode,
            "unattended": unattended,
            "file_scope": file_scope,
        })

    def run_python_file(self, file_path: str) -> dict:
        """Convenience: run a Python script file via editor.run_python."""
        return self.run_python(file_path, mode="execute_file")

    def describe_action(self, namespace: str, action: str) -> dict:
        """Get the full param schema for a single action."""
        return self.call_action("describe", "action_schema", {
            "target_namespace": namespace,
            "target_action": action,
        })

    def bulk_fill(self, target_namespace: str, target: str, tree: dict) -> dict:
        """Reflection-walker bulk property fill."""
        return self.call_action("bulk_fill", "apply", {
            "target_namespace": target_namespace,
            "target": target,
            "tree": tree,
        })

    def guide(self, section: str | None = None) -> dict:
        """Monolith onboarding guide sections."""
        params = {}
        if section:
            params["section"] = section
        return self.call_action("monolith", "guide", params)

    # ------------------------------------------------------------------
    # Convenience: Melodia/Melusina/Surreal helpers
    # ------------------------------------------------------------------

    def create_blend_space_1d(self, path: str, skeleton_path: str,
                               axis_name: str = "Speed",
                               axis_min: float = 0.0, axis_max: float = 600.0) -> dict:
        """Create a 1D blend space via MCP animation actions."""
        return self.call_action("animation", "create_blend_space_1d", {
            "path": path,
            "skeleton": skeleton_path,
            "axis_name": axis_name,
            "axis_min": axis_min,
            "axis_max": axis_max,
        })

    def add_blend_sample(self, blend_space_path: str,
                          animation_path: str, sample_value: float) -> dict:
        """Add an animation sample to a blend space."""
        return self.call_action("animation", "add_blendspace_sample", {
            "blend_space_path": blend_space_path,
            "animation_path": animation_path,
            "sample_value": sample_value,
        })

    def create_blueprint(self, path: str, parent_class: str = "Actor") -> dict:
        """Create a Blueprint asset."""
        return self.call_action("blueprint", "create_blueprint", {
            "path": path,
            "parent_class": parent_class,
        })

    def duplicate_blueprint(self, source: str, dest_path: str, dest_name: str) -> dict:
        """Duplicate a Blueprint asset."""
        return self.call_action("blueprint", "duplicate_blueprint", {
            "source_path": source,
            "destination_path": dest_path,
            "destination_name": dest_name,
        })

    def add_actor_component(self, bp_path: str, component_class: str,
                             component_name: str) -> dict:
        """Add a component to a Blueprint."""
        return self.call_action("blueprint", "add_component", {
            "asset_path": bp_path,
            "component_class": component_class,
            "component_name": component_name,
        })

    def load_level(self, path: str) -> dict:
        """Load a level via editor.load_level."""
        return self.call_action("editor", "load_level", {"path": path})

    def get_scene_info(self) -> dict:
        """Get current scene/level information."""
        return self.call_action("mesh", "get_scene_statistics")

    def spawn_actor(self, mesh_path: str, location: list | None = None) -> dict:
        """Spawn a mesh actor in the current level."""
        params = {"mesh_path": mesh_path}
        if location:
            params["location"] = location
        return self.call_action("mesh", "spawn_actor", params)

    def create_parametric_mesh(self, params: dict) -> dict:
        """Create a parametric mesh (building shell, maze, pipe, etc.)."""
        return self.call_action("mesh", "create_parametric_mesh", params)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_json(self, url: str) -> dict:
        try:
            import urllib.error
            import urllib.request

            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MCPConnectionError(f"Cannot read MCP endpoint {url}: {exc}") from exc

    def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        self._request_id += 1
        body = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        response = self._post_json(self.mcp_url, body)
        if "error" in response:
            error = response["error"]
            raise McpError(
                message=str(error.get("message", error)),
                code=error.get("code"),
                data=error.get("data"),
            )
        result = response.get("result", {})
        if result.get("isError"):
            content = result.get("content", [])
            message = content[0].get("text", "MCP tool failed") if content else "MCP tool failed"
            raise McpError(message)
        content = result.get("content", [])
        if content and isinstance(content[0], dict):
            text = content[0].get("text")
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                    return parsed if isinstance(parsed, dict) else {"result": parsed}
                except json.JSONDecodeError:
                    return {"success": True, "output": [text]}
        return result if isinstance(result, dict) else {"result": result}

    def _post_json(self, url: str, body: dict) -> dict:
        try:
            import urllib.error
            import urllib.request

            request = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise MCPConnectionError(f"Cannot connect to MCP at {url}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise MCPConnectionError(f"Invalid JSON response from MCP: {exc}") from exc


class MCPConnectionError(McpError):
    """Raised when the MCP server cannot be reached."""
