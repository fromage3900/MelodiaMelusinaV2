"""
Gaea terrain file utilities.

Reads `.terrain` JSON graphs, extracts build metadata, and exposes node
parameters for offline reproduction or validation. Does not execute Gaea.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class GaeaTerrainGraph:
    """Parsed Gaea terrain graph."""

    def __init__(self, data: dict[str, Any]):
        self._data = data
        self.assets = data.get("Assets", {}).get("$values", [])
        self.build = {}
        self.state = {}
        for asset in self.assets:
            if isinstance(asset, dict):
                if "BuildDefinition" in asset:
                    self.build = asset["BuildDefinition"]
                if "State" in asset:
                    self.state = asset["State"]

    @property
    def resolution(self) -> int:
        return int(self.build.get("Resolution", 0))

    @property
    def bake_resolution(self: int) -> int:
        return int(self.build.get("BakeResolution", 0))

    @property
    def tile_resolution(self) -> int:
        return int(self.build.get("TileResolution", 0))

    @property
    def tiles(self) -> tuple[int, int]:
        n = int(self.build.get("NumberOfTiles", 1))
        return (n, n)

    @property
    def edge_blending(self) -> float:
        return float(self.build.get("EdgeBlending", 0.0))

    @property
    def width_m(self) -> float:
        for asset in self.assets:
            terrain = asset.get("Terrain")
            if terrain and "Width" in terrain:
                return float(terrain["Width"])
        return 0.0

    @property
    def height_m(self) -> float:
        for asset in self.assets:
            terrain = asset.get("Terrain")
            if terrain and "Height" in terrain:
                return float(terrain["Height"])
        return 0.0

    @property
    def preview_resolution(self) -> int:
        return int(self.state.get("PreviewResolution", 0))

    def nodes(self) -> dict[str, Any]:
        """Return node id -> node dict for the first terrain asset."""
        for asset in self.assets:
            terrain = asset.get("Terrain")
            if terrain and "Nodes" in terrain:
                return terrain["Nodes"]
        return {}

    def node_types(self) -> dict[str, str]:
        """Return node id -> type name."""
        return {nid: node.get("$type", "") for nid, node in self.nodes().items()}

    def find_nodes_by_type(self, type_name: str) -> list[dict[str, Any]]:
        """Return nodes whose type contains `type_name`."""
        return [node for node in self.nodes().values() if type_name in node.get("$type", "")]

    def summary(self) -> dict[str, Any]:
        nodes = self.nodes()
        type_counts: dict[str, int] = {}
        for node in nodes.values():
            if not isinstance(node, dict):
                continue
            t = node.get("$type", "Unknown")
            if isinstance(t, str):
                t = t.split(",")[0].strip()
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "resolution": self.resolution,
            "bake_resolution": self.bake_resolution,
            "width_m": self.width_m,
            "height_m": self.height_m,
            "node_count": len(nodes),
            "type_counts": type_counts,
            "preview_resolution": self.preview_resolution,
        }


def load_terrain(path: str | Path) -> GaeaTerrainGraph:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return GaeaTerrainGraph(data)


def validate_terrain(path: str | Path) -> dict[str, Any]:
    """Basic sanity checks on a `.terrain` file."""
    graph = load_terrain(path)
    s = graph.summary()
    issues: list[str] = []
    if s["resolution"] <= 0:
        issues.append("Resolution missing or zero")
    if s["width_m"] <= 0 or s["height_m"] <= 0:
        issues.append("World size missing or zero")
    if s["node_count"] == 0:
        issues.append("No nodes found")
    return {"path": str(path), "summary": s, "issues": issues, "ok": len(issues) == 0}
