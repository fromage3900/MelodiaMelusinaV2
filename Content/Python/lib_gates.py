"""Honest validation gates — shared pass/fail helpers for every loop and script.

A step "ran" is not a step "worked": every gate here asserts the TARGET state.
Import these instead of hand-rolling pass criteria (the 07-09 WP audit reported
passed=true on four failing levels because a script asserted completion, not
targets). Named lib_gates (flat) until the Content/Python package reorg lands.

All gates return {'passed': bool, 'detail': {...}} and never raise on
missing/None — a gate that crashes is a gate that gets try/except-ed away.
"""
from __future__ import annotations


def gate_pillar(pillar_key: str) -> dict:
    """WP + ISM>0 for one pillar. Editor-side, count in a SEPARATE call after generate."""
    import setup_wp_pillar_levels as wp

    try:
        r = wp.verify(pillar_key, save_report=False)
        return {"passed": bool(r.get("passed")), "detail": r}
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "detail": {"error": str(exc)[:200]}}


def gate_material_compiles(asset_path: str, *, max_ps: int | None = None) -> dict:
    """Material loads, has statistics, and (optionally) PS instructions under cap."""
    import unreal

    try:
        m = unreal.load_asset(asset_path)
        if not m:
            return {"passed": False, "detail": {"error": "load failed"}}
        s = unreal.MaterialEditingLibrary.get_statistics(m)
        ps = int(s.num_pixel_shader_instructions)
        ok = ps > 0 and (max_ps is None or ps <= max_ps)
        return {"passed": ok, "detail": {"ps": ps, "vs": int(s.num_vertex_shader_instructions)}}
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "detail": {"error": str(exc)[:200]}}


def gate_graph_health(graph_path: str, *, max_nodes: int = 40) -> dict:
    """PCG graph exists, node count sane (duplicate-chain rot check), every spawner has a mesh."""
    import unreal

    try:
        g = unreal.load_asset(graph_path)
        if not g:
            return {"passed": False, "detail": {"error": "load failed"}}
        nodes = list(g.nodes or [])
        spawners_ok, spawners = True, 0
        for n in nodes:
            s = n.get_settings()
            if s and isinstance(s, unreal.PCGStaticMeshSpawnerSettings):
                spawners += 1
                try:
                    sel = s.get_editor_property("mesh_selector_parameters")
                    entries = sel.get_editor_property("mesh_entries")
                    if not entries:
                        spawners_ok = False
                except Exception:  # noqa: BLE001
                    spawners_ok = False
        ok = 0 < len(nodes) <= max_nodes and spawners_ok
        return {"passed": ok, "detail": {"nodes": len(nodes), "spawners": spawners, "spawners_have_meshes": spawners_ok}}
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "detail": {"error": str(exc)[:200]}}


def gate_no_redirectors(scope: str) -> dict:
    import unreal

    eal = unreal.EditorAssetLibrary
    try:
        reds = [
            a for a in eal.list_assets(scope, recursive=True, include_folder=False)
            if "ObjectRedirector" in str(eal.find_asset_data(a).asset_class_path)
        ]
        return {"passed": len(reds) == 0, "detail": {"scope": scope, "redirectors": len(reds)}}
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "detail": {"error": str(exc)[:200]}}
