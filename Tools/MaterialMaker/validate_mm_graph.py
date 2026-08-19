#!/usr/bin/env python3
"""Structural validation for MM_Master_SurrealAnimatedPBR *.ptex (no Material Maker required).

  py Tools/MaterialMaker/validate_mm_graph.py
  py Tools/MaterialMaker/validate_mm_graph.py --version v2
  py Tools/MaterialMaker/validate_mm_graph.py --json Saved/Audit/mm_graph_validation.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

GRAPH_SETS = {
    "v1": {
        "static": ROOT / "MM_Master_SurrealAnimatedPBR_Static.ptex",
        "dynamic": ROOT / "MM_Master_SurrealAnimatedPBR_Dynamic.ptex",
        "emissive": "Blend_EmissVeins",
        "min_exports": 4,
    },
    "v2": {
        "static": ROOT / "MM_Master_SurrealAnimatedPBR_v2_Static.ptex",
        "dynamic": ROOT / "MM_Master_SurrealAnimatedPBR_v2_Dynamic.ptex",
        "emissive": "Blend_EmissiveFinal",
        "min_exports": 8,
    },
}

REQUIRED_LANES = ["00", "01", "02", "05", "06", "07", "08", "14", "22", "23"]
REQUIRED_REMOTES = {
    "BakeTime", "AnimSpeed", "AnimOffset", "TileRepeat", "StyleNikki", "StyleMadoka",
    "StyleItto", "StyleCelestial", "ExportResolution", "HeightScale", "NormalStrength",
}
def material_ports(emissive_node: str) -> dict[str, int]:
    return {
        "Blend_Albedo": 0,
        "Tones_Metallic": 1,
        "Tones_RoughBias": 2,
        emissive_node: 3,
        "Normal_Map": 4,
        "Tones_AO": 5,
        "Buffer_Height": 6,
        "Tones_Opacity": 7,
        "Blend_SSS": 8,
    }
NASA_FILES = [
    "NASA_Refs/blue_marble_4k.jpg",
    "NASA_Refs/hubble_carina_4k.jpg",
    "NASA_Refs/moon_lro_elevation_2k.png",
    "NASA_Refs/mars_mola_2k.png",
    "NASA_Refs/star_mask.png",
    "NASA_Refs/star_bright.csv",
]
INVALID_TONES_KEYS = {"value", "contrast"}


def validate_ptex(path: Path, *, expect_dynamic: bool, emissive_node: str, min_exports: int) -> dict:
    issues: list[str] = []
    graph = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["name"]: n for n in graph.get("nodes", [])}
    conns = graph.get("connections", [])

    if graph.get("type") != "graph":
        issues.append("root type is not graph")

    comments = [n for n in graph["nodes"] if n.get("type") == "comment"]
    lane_ids = []
    for c in comments:
        text = c.get("text", "")
        if "[lane:" in text:
            lane_ids.append(text.split("[lane:")[1].split("]")[0])
    for lid in REQUIRED_LANES:
        if lid not in lane_ids:
            issues.append(f"missing comment lane {lid}")

    if "Remote_MasterParams" not in nodes:
        issues.append("missing Remote_MasterParams")
    else:
        remote = nodes["Remote_MasterParams"]
        widget_names = {w["name"] for w in remote.get("widgets", []) if w.get("type") == "named_parameter"}
        for r in REQUIRED_REMOTES:
            if r not in widget_names:
                issues.append(f"missing remote param ${r}")

    for node in graph.get("nodes", []):
        ntype = node.get("type")
        params = node.get("parameters", {})
        if ntype == "tones" and INVALID_TONES_KEYS & set(params):
            issues.append(
                f"{node.get('name')}: `tones` node uses value/contrast — use `tones_range` instead"
            )
        if ntype == "image":
            if "fix_ratio" in params:
                issues.append(f"{node.get('name')}: image param fix_ratio should be fix_ar")
            if "image" in params and params["image"].startswith("C:"):
                issues.append(f"{node.get('name')}: absolute image path breaks portability")

    if "Material" not in nodes:
        issues.append("missing Material node")
    else:
        mat = nodes["Material"]
        expected_type = "material_dynamic" if expect_dynamic else "material"
        if mat.get("type") != expected_type:
            issues.append(f"Material type {mat.get('type')} != {expected_type}")
        mat_wires = {(c["from"], c["to_port"]) for c in conns if c["to"] == "Material"}
        for src, port in material_ports(emissive_node).items():
            if src not in nodes:
                issues.append(f"missing map source node {src}")
            elif (src, port) not in mat_wires:
                issues.append(f"Material port {port} not wired from {src}")

    if "SourceImage" not in nodes:
        issues.append("missing SourceImage")

    export_nodes = [n for n in graph["nodes"] if n.get("type") == "export"]
    if not expect_dynamic and len(export_nodes) < min_exports:
        issues.append(f"expected >={min_exports} export nodes, got {len(export_nodes)}")

    for nasa in NASA_FILES:
        if not (ROOT / nasa).is_file():
            issues.append(f"missing NASA ref: {nasa}")

    return {
        "path": str(path),
        "nodes": len(graph.get("nodes", [])),
        "connections": len(conns),
        "export_nodes": len(export_nodes),
        "ok": len(issues) == 0,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", choices=sorted(GRAPH_SETS), default="v2")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    graph_set = GRAPH_SETS[args.version]
    static = graph_set["static"]
    dynamic = graph_set["dynamic"]
    emissive = graph_set["emissive"]
    min_exports = graph_set["min_exports"]

    results = []
    for path, expect_dynamic in ((static, False), (dynamic, True)):
        if not path.is_file():
            print(f"MISSING {path}")
            return 1
        r = validate_ptex(
            path,
            expect_dynamic=expect_dynamic,
            emissive_node=emissive,
            min_exports=min_exports,
        )
        results.append(r)
        status = "OK" if r["ok"] else "FAIL"
        print(f"[{status}] {path.name}: {r['nodes']} nodes, {r['connections']} wires")
        for issue in r["issues"]:
            print(f"  - {issue}")

    payload = {"version": args.version, "results": results, "all_ok": all(r["ok"] for r in results)}
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")

    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
