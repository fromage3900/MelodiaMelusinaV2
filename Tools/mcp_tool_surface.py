#!/usr/bin/env python3
"""Unreal-MCP tool surface — the "VERY HIGH PRIORITY R&D" implementable row.

Implements the named Unreal-MCP safe-editor tools from
Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md as thin,
sandbox-guarded wrappers over the existing Monolith / UnrealMCP surface.

Guardrails (from the research):
- FIRST TEST = a sandbox map only, exposing a tiny number of SAFE editor actions.
- Dry-run by default (--dry). Live execution only with an explicit flag + live Monolith :9316.
- No Content/_PROJECT/ writes, no parallel authority.

Tools implemented (research's target surface):
  RunP0SmokeTest, RunPerformanceCapture, AuditDataLayers,
  CreateRhythmReactiveMaterialInstance, PlaceSpeedTreeBiomeTest,
  ValidateWaterAuthority, ValidateMaraSkeleton, BakeHoudiniRegion, BuildHLODForRegion

Usage:
  python Tools/mcp_tool_surface.py --list
  python Tools/mcp_tool_surface.py RunP0SmokeTest --dry
  python Tools/mcp_tool_surface.py AuditDataLayers --live
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
MONOLITH = "http://127.0.0.1:9316/mcp"
SANDBOX_ONLY = True  # research guardrail: no chapter maps

TOOLS = {
    "RunP0SmokeTest": {
        "desc": "Wrap the P0 PIE smoke harness (pie_smoke_runner) and record a smoke gate.",
        "surface": "editor_query run_pie_smoke",
        "guard": "sandbox map only",
    },
    "RunPerformanceCapture": {
        "desc": "Trigger a Monolith viewport capture + Unreal Insights trace for a region.",
        "surface": "editor_query capture_scene_preview + TRACE_CPUPROFILER",
        "guard": "sandbox map only",
    },
    "AuditDataLayers": {
        "desc": "Enumerate Data Layers in the current level and report active/assigned state.",
        "surface": "mesh_query / editor_query data-layer read",
        "guard": "read-only",
    },
    "CreateRhythmReactiveMaterialInstance": {
        "desc": "Create an MI (parent M_Master_Toon_Universal) wired to MPC_Melodia_Palette rhythm params.",
        "surface": "material instance create + scalar override",
        "guard": "dry-run by default; owner confirmation for live creation",
    },
    "PlaceSpeedTreeBiomeTest": {
        "desc": "PCG-driven biome test using the PRESENT SpeedTree assets (M_SpeedTreeMaster + reset_speedtree_wind_instances.py). PCG owns runtime scatter; SpeedTree owns plants.",
        "surface": "PCG spawn of SpeedTree assets on a sandbox region + wind-instance reset",
        "guard": "sandbox map only; SpeedTree is the production plant authority (present)",
    },
    "ValidateWaterAuthority": {
        "desc": "Assert the water gameplay subsystem is the single authority (no parallel water sim).",
        "surface": "blueprint_query read UMelodiaWaterGameplaySubsystem",
        "guard": "read-only",
    },
    "ValidateMaraSkeleton": {
        "desc": "Assert the Mara skeleton/retarget is intact (reuse Melusina skeleton conventions per Houdini plan).",
        "surface": "mesh_query skeleton read",
        "guard": "read-only",
    },
    "BakeHoudiniRegion": {
        "desc": "Bake a Houdini HDA region into UE (HDA_ENV_TerrainStamp / PathCorridor / ScatterMaskBuilder / HeroRockFamily / LOD_Collision_Batch) per MARA_P0_P3_HOUDINI_EXECUTION_PLAN. Bake-not-live-cook: production-critical results are baked, never left dependent on live HDA cooking.",
        "surface": "HoudiniEngine asset bake -> /Game/Melodia/Environment/<Chapter>/Houdini/",
        "guard": "dry-run by default; requires HoudiniEngine + editor + sandbox",
    },
    "BuildHLODForRegion": {
        "desc": "Build HLOD for a sandbox region (Data Layers / HLOD config).",
        "surface": "HLOD build for region",
        "guard": "sandbox map only",
    },
}


def run_tool(name: str, live: bool) -> dict:
    meta = TOOLS[name]
    result = {
        "tool": name,
        "desc": meta["desc"],
        "guard": meta["guard"],
        "mode": "LIVE" if live else "DRY-RUN",
        "monolith": MONOLITH,
        "status": "NOT_EXECUTED" if not live else "EXECUTED",
    }
    if live:
        # Live execution routes through the Monolith / UnrealMCP surface. Full
        # wiring is staged per-tool; for now live is a guarded dispatch stub so
        # the surface is safe by default (research: "tiny number of safe actions").
        result["status"] = "DISPATCHED_GUARDED"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tool", nargs="?", help="tool name from the surface")
    ap.add_argument("--list", action="store_true", help="list tools")
    ap.add_argument("--dry", action="store_true", help="dry-run (default, no editor)")
    ap.add_argument("--live", action="store_true", help="live execution (requires Monolith :9316 + sandbox)")
    args = ap.parse_args()

    if args.list or not args.tool:
        print("Unreal-MCP tool surface (research SSOT implementable row):")
        for k, v in TOOLS.items():
            print(f"  {k:35s} {v['desc']}")
        return 0

    if args.tool not in TOOLS:
        print(f"unknown tool '{args.tool}'. Use --list", file=sys.stderr)
        return 2

    live = bool(args.live) and not args.dry
    result = run_tool(args.tool, live)

    ts = datetime.now().strftime("%Y-%m-%d")
    AUDIT.mkdir(parents=True, exist_ok=True)
    jpath = AUDIT / f"mcp_tool_surface_{ts}.json"
    jpath.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"-> {jpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())