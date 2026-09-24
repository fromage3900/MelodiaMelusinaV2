"""Jev PCG convergence audit — isolated prototype (2026-09-24).

ISOLATION: everything lives in Prototypes/JevPCGConvergenceAudit/. No .uasset/.umap writes,
no editor mutation. Jev only picks among the closed option sets below.
Provenance: prints the live model string; source="jev-live" or "classical-fallback"
(fallback is NOT Jev evidence). SDK typesafe_sdk 0.7.0: resp.answers[k].choice/.probabilities.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).parent / "audit_log.json"

# Live facts gathered 2026-09-24 (Saved/Audit/massive_morning_20260924/pcg_inventory.json).
STATE = {
    "project_pcg_graphs": 191,
    "graphs_using_pcgex": 42,
    "graphs_placed_in_levels": 36,
    "graphs_unreferenced": 114,
    "style_graph_folders": {"Baroque": 35, "Escher": 19, "WP": 16, "Sakura": 9, "SeaAbove": 9},
    "pcgex_mesh_collections": 12,
    "pcg_graph_instances": 1,
    "graph_user_params_scriptable": False,
    "bp_pcg_hosts": ["BP_Morning_GoldenSpiral", "BP_MelusinaRoomShell", "BP_PCG_LargeAssembly (engine demo)", "BP_PCG_SmallAssembly (engine demo)"],
    "massive_biome_core_live": {"volumes": 3, "instances": [992, 205, 25], "density_in_wrapper_data": True},
    "biome_da_has_material_field": False,
    "curve_system": "WC_Corridor_* Actor+SplineComponent spines (3, 20-33 m, hub at Dell) consumed by PCGExSampleNearestSpline (WestRim) and PCG_SplinePath",
    "room_system": "NONE working: PCG_MelusinaRoomShell_PCGex has 0 nodes and BP_MelusinaRoomShell is an empty Actor with one PCGComponent (SalonA generates nothing)",
    "plugins_enabled": ["PCG", "PCGExtendedToolkit", "PCGPrimitives (Grammar, Buildings, City examples)", "PCGBiomeCore", "PCGGeometryScriptInterop", "PCGWaterInterop"],
    "morning_has_landscape": False,
    "dead_or_broken_in_morning": ["EastBank/NorthDress hero corners 0 output", "Penrose/Escher 0x0x0 volumes", "MemoryDressing deactivated", "NorthDress companion over empty space", "WestRim main 160 greybox rocks", "coral/kelp point field"],
    "owner_goal": "Reusable corridor/passageway framework; PCGEx builds houses and diorama scenery; defined curves carve pathways; BP PCG hosts staged and updated project-wide",
}

QUESTIONS = {
    "structure_engine": {"type": "choice", "instructions": "Which engine should own houses/rooms/corridor STRUCTURE (walls, floors, openings)?",
        "criteria": {
            "PCGEX_CLUSTERS": "PCGEx clusters/graphs: rooms = cluster nodes, doorways/corridors = edges; build walls/floors from cluster geometry.",
            "PCG_PRIMITIVES_GRAMMAR": "Engine PCGPrimitives Grammar/Buildings (shape grammar on volumes and splines), PCGEx only for paths.",
            "EXTEND_ROOMSHELL": "Build the house kit inside the existing (empty) PCG_MelusinaRoomShell_PCGex + BP_MelusinaRoomShell names.",
            "HYBRID_GRAMMAR_ON_PCGEX": "PCGEx cluster layout decides rooms/doors/corridors; PCGPrimitives grammar skins each room/facade.",
        }},
    "path_authority": {"type": "choice", "instructions": "What should be the single authority for carving pathways/passages?",
        "criteria": {
            "SPLINE_SPINES": "Hand/placed Actor+SplineComponent spines (the WC_Corridor_* pattern), everything samples them.",
            "PCGEX_PATHS": "PCGEx path/cluster outputs (pathfinding between tagged anchors) are the authority; splines are derived.",
            "MANIFEST_CURVES": "World Compiler world.json manifest defines curves; splines are generated from it.",
            "SPLINE_PLUS_PCGEX_REFINE": "Placed spline spines are the authority; PCGEx refines/relaxes/offsets them into walkable passages and exclusion corridors.",
        }},
    "mesh_authority": {"type": "choice", "instructions": "Single mesh-list authority for all scatter and structure spawning?",
        "criteria": {
            "PCGEX_COLLECTIONS": "PCGExMeshCollection everywhere (per-entry material overrides, weights).",
            "BIOME_DA": "Massive PDA_Vegetation biome data assets (no material field).",
            "DA_POINTS_TO_COLLECTIONS": "Biome DA keeps category + transform ranges and points each category at a PCGExMeshCollection.",
        }},
    "bp_host_pattern": {"type": "choice", "instructions": "Standard pattern for Blueprint PCG hosts project-wide?",
        "criteria": {
            "GRAPH_INSTANCE_PARAMS": "BP owns PCGComponent + PCGGraphInstance; inputs flow as graph parameters (authored once by hand).",
            "BP_ATTRIBUTE_PIN": "BP passes an attribute set / actor data via input pins (the BiomeData-pin pattern), no graph params.",
            "DATA_ASSET_PER_BP": "Each BP references a data asset recipe; graph reads it via object path.",
        }},
    "first_step": {"type": "choice", "instructions": "What should be executed FIRST?",
        "criteria": {
            "C1_EXTRACT_PRIMITIVES": "Extract shared L0 subgraphs (ground project, density, transform, spawn, exclude) from the biome core.",
            "CORRIDOR_SCHEMA_PROTOTYPE": "Lock the corridor/room/path schema and prove one house + one carved corridor in a sandbox map.",
            "FIX_MORNING_DEAD_VOLUMES": "Fix Morning's dead/broken PCG volumes before adding frameworks.",
            "ARCHIVE_DEAD_GRAPHS": "Archive the 114 unreferenced graphs first to shrink the surface.",
        }},
    "riskiest": {"type": "choice", "instructions": "Riskiest assumption in converging PCG + PCGEx + BP hosts?",
        "criteria": {
            "NO_LANDSCAPE_GROUND": "Morning has no landscape; surface-sampler graphs and grammar-on-terrain assume one.",
            "SCRIPTING_GAPS": "Graph params / pins can't be created from script; convergence needs manual editor steps.",
            "PCGEX_VERSION_DRIFT": "PCGEx node API changes break the 42 PCGEx graphs during refactor.",
            "STYLE_GRAPH_COUPLING": "Style graphs have private spawn tails; swapping them changes look in art levels.",
            "SCOPE": "Project-wide scope is too big; converge a vertical slice first.",
        }},
    "needs_owner": {"type": "noul", "instructions": "Does an owner decision gate execution of the first step?",
        "criteria": {"true": "An owner art/architecture decision is required before agents execute.", "false": "Agents can execute the first step now."}},
    "readiness": {"type": "score", "instructions": "How ready is the project for a unified corridor/house/path PCG schema?",
        "criteria": ["Nothing reusable exists.", "Pieces exist but disconnected.", "Shared core exists for scatter; structure/paths ad hoc.", "Scatter + paths share primitives; structure ad hoc.", "Scatter, paths, structure and BP hosts all share one schema."]},
}


def main() -> None:
    key = os.environ.get("TYPESAFE_API_KEY")
    log = {"schema": "melodia.jev_pcg_convergence_audit.v1", "date": datetime.now().isoformat(timespec="seconds"), "state": STATE}
    if not key:
        log.update(source="classical-fallback", reason="TYPESAFE_API_KEY missing — NO Jev ruling")
    else:
        from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
        q = {}
        for k, v in QUESTIONS.items():
            cls = {"choice": Choice, "noul": Noul, "score": Score}[v["type"]]
            q[k] = cls(instructions=v["instructions"], criteria=v["criteria"])
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(state=STATE, questions=q)
        ans = {}
        for k, a in resp.answers.items():
            d = a.model_dump() if hasattr(a, "model_dump") else dict(a)
            ans[k] = d
        log.update(source="jev-live", model=resp.model, answers=ans)
    OUT.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    print("model:", log.get("model"), "| source:", log["source"])
    for k, a in log.get("answers", {}).items():
        if a.get("type") == "choice":
            top = sorted(a["probabilities"].items(), key=lambda i: -i[1])[:3]
            print(f"{k}: {a['choice']} (conf {a['confidence']:.2f}) {[(n, round(p, 3)) for n, p in top]}")
        elif a.get("type") == "noul":
            print(f"{k}: noul {a['noul']:.2f}")
        else:
            print(f"{k}: score {a['score']:.2f} (conf {a['confidence']:.2f})")


if __name__ == "__main__":
    main()
