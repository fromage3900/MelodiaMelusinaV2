"""YAML/JSON grammar graphs → GRAPH_REGISTRY-compatible specs."""

from __future__ import annotations

import os

from ._io import load_data, package_path


def _grammar_filename(graph_id: str) -> str:
    if graph_id == "ZEN_SHRINE_AXIS":
        return "zen_shrine_axis.json"
    return f"{graph_id.lower()}.json"


def load_grammar_graph(graph_id: str) -> list[tuple[str, dict]]:
    """Return list of (arch_type, overrides) from grammar file."""
    data = load_data("grammar", _grammar_filename(graph_id))
    modules = data.get("modules", [])
    spec = []
    for row in modules:
        at = row.get("arch_type")
        if not at:
            continue
        spec.append((at, dict(row.get("overrides") or {})))
    return spec


def grammar_meta(graph_id: str) -> dict:
    data = load_data("grammar", _grammar_filename(graph_id))
    return {
        "label": data.get("label", graph_id),
        "description": data.get("description", ""),
        "style": data.get("style", "zen"),
    }


def merge_grammar_into_registry(graph_registry: dict) -> int:
    """Register or refresh OS grammar graphs in surreal_arch GRAPH_REGISTRY."""
    root = package_path("grammar")
    touched = 0
    for name in os.listdir(root):
        if not name.endswith(".json"):
            continue
        data = load_data("grammar", name)
        gid = data.get("id")
        if not gid:
            continue
        modules = data.get("modules", [])
        spec = [(m["arch_type"], dict(m.get("overrides") or {})) for m in modules if m.get("arch_type")]
        if not spec:
            continue
        preview = " › ".join(
            at.replace("GREYBOX_", "").replace("GB_", "") for at, _ in spec
        )
        entry = {
            "label": data.get("label", gid),
            "description": data.get("description", ""),
            "preview": preview,
            "style": data.get("style", "zen"),
            "module_count": len(spec),
            "spec": spec,
            "os_grammar": True,
        }
        graph_registry[gid] = entry
        touched += 1
    return touched
