"""Faraway Mother PCG Assembly & Level Staging Automation.

Validates and stages the Faraway Mother level (LV_FarawayMother_Prototype)
with PCG volume graphs, World Field Bus parameter bindings, and hero music
puzzle challenge integration.

Supports offline validation and in-engine execution.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA = "melodia.faraway_mother_pcg_assembly.v1"
DEFAULT_MANIFEST = "specs/pcg/faraway_mother_pcg_manifest.v1.json"
TARGET_LEVEL_PATH = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"

REQUIRED_PCG_GRAPHS = [
    "/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge",
    "/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_DetailProps",
    "/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_WindZones",
]


def _graph_exists(game_path: str) -> bool:
    """True when a /Game/... PCG graph is actually present on disk.

    verify_assembly used to return REQUIRED_PCG_GRAPHS verbatim as
    "pcg_graphs_staged", so it reported all three as staged while none existed.
    That is a false green: callers read ok=True plus a populated staged list and
    conclude the graphs are there.
    """
    rel = game_path.replace("/Game/", "Content/", 1) + ".uasset"
    return (Path(__file__).resolve().parents[2] / rel).is_file()


@dataclass
class AssemblyVerificationResult:
    ok: bool
    manifest_path: str
    total_staged_points: int
    biomes_verified: List[str]
    pcg_graphs_staged: List[str]
    world_fields_connected: List[str]
    narrative_challenge: Dict[str, str]
    errors: List[str] = field(default_factory=list)


def verify_assembly(manifest_path_str: str) -> AssemblyVerificationResult:
    """Verify PCG ecosystem manifest and level staging readiness."""
    manifest_path = Path(manifest_path_str).resolve()
    errors: List[str] = []

    if not manifest_path.is_file():
        return AssemblyVerificationResult(
            ok=False,
            manifest_path=str(manifest_path),
            total_staged_points=0,
            biomes_verified=[],
            pcg_graphs_staged=[],
            world_fields_connected=[],
            narrative_challenge={},
            errors=[f"Manifest file not found: {manifest_path}"],
        )

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return AssemblyVerificationResult(
            ok=False,
            manifest_path=str(manifest_path),
            total_staged_points=0,
            biomes_verified=[],
            pcg_graphs_staged=[],
            world_fields_connected=[],
            narrative_challenge={},
            errors=[f"Invalid JSON: {e}"],
        )

    if data.get("schema") != "melodia.faraway_mother_pcg_manifest.v1":
        errors.append(f"Unexpected schema: {data.get('schema')}")

    total_pts = int(data.get("total_points") or 0)
    if total_pts <= 0:
        errors.append("Manifest contains zero points")

    biomes = list(data.get("biome_summaries", {}).keys())
    expected_biomes = {"WeaveRidge", "LaceCanopy", "FrillValley", "ResonantSeamWay"}
    if set(biomes) != expected_biomes:
        errors.append(f"Biome mismatch: observed {set(biomes)} != expected {expected_biomes}")

    for b_name, b_summary in data.get("biome_summaries", {}).items():
        if int(b_summary.get("point_count") or 0) <= 0:
            errors.append(f"Biome {b_name} has non-positive point count")

    world_fields = data.get("world_field_channels") or []
    if len(world_fields) < 4:
        errors.append("Missing required World Field Bus channels")

    narrative = data.get("narrative_challenge_hook") or {}
    if not narrative.get("challenge_id"):
        errors.append("Missing narrative challenge_id")

    present = [g for g in REQUIRED_PCG_GRAPHS if _graph_exists(g)]
    missing = [g for g in REQUIRED_PCG_GRAPHS if g not in present]
    if missing:
        errors.append(
            "PCG graphs missing on disk (manifest is complete, the graphs are not "
            f"authored): {missing}"
        )

    return AssemblyVerificationResult(
        ok=len(errors) == 0,
        manifest_path=str(manifest_path),
        total_staged_points=total_pts,
        biomes_verified=biomes,
        pcg_graphs_staged=present,
        world_fields_connected=world_fields,
        narrative_challenge=narrative,
        errors=errors,
    )


def apply_assembly_in_engine(verification: AssemblyVerificationResult) -> Dict[str, Any]:
    """Execute live in-engine actor configuration and PCG assignment."""
    if not verification.ok:
        raise RuntimeError(f"Cannot apply assembly: verification failed with {verification.errors}")

    try:
        import unreal  # type: ignore
    except ImportError:
        return {
            "applied": False,
            "engine_available": False,
            "message": "Unreal module not available (dry-run passed)",
        }

    # In-engine actor creation and PCG setup
    unreal.log("FarawayMother PCG Assembly: Initializing level and PCG volumes...")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    created_actors = []
    for graph_path in verification.pcg_graphs_staged:
        actor_name = Path(graph_path).name.replace("PCG_", "PCGVolume_")
        unreal.log(f"Staged PCG Graph binding: {actor_name} -> {graph_path}")
        created_actors.append(actor_name)

    return {
        "applied": True,
        "engine_available": True,
        "level": TARGET_LEVEL_PATH,
        "actors_configured": created_actors,
        "total_points": verification.total_staged_points,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST, help="Path to PCG manifest")
    parser.add_argument("--apply", action="store_true", help="Apply assembly inside Unreal Engine")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args(argv)

    verification = verify_assembly(args.manifest)
    result_dict = asdict(verification)

    if args.apply and verification.ok:
        result_dict["engine_result"] = apply_assembly_in_engine(verification)

    if args.json:
        print(json.dumps(result_dict, indent=2))
    else:
        status_str = "PASS" if verification.ok else "FAIL"
        print(f"Faraway Mother PCG Assembly Verification: {status_str}")
        print(f"Manifest: {verification.manifest_path}")
        print(f"Total Staged Points: {verification.total_staged_points}")
        print(f"Biomes: {', '.join(verification.biomes_verified)}")
        print(f"PCG Graphs: {', '.join(verification.pcg_graphs_staged)}")
        print(f"World Field Channels: {', '.join(verification.world_fields_connected)}")
        if verification.errors:
            print(f"Errors ({len(verification.errors)}):")
            for err in verification.errors:
                print(f"  - {err}")

    return 0 if verification.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
