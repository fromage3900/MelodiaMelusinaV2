"""
GMM NPC Pipeline — Main Entry Point

Unified pipeline for procedural NPC generation using VRM4U + MelodiaCore.
Inspired by Infinity Nikki's outfit-as-gameplay architecture.

Usage (Unreal Editor Python Console):
    import gmm.npc as npc
    npc.generate_npc_batch(count=10)           # Full pipeline
    npc.import_vrms()                          # Step 1: Import VRMs
    npc.setup_materials()                      # Step 2: Create MToon materials
    npc.generate_lods()                        # Step 3: Generate LODs
    npc.integrate_battle()                     # Step 4: Battle data
    npc.populate_level("L_PCGTest_Forest")     # Step 5: Spawn in level
    npc.audit_all()                            # Step 6: Full audit

Or run individual steps via GMM EnvUI menu: Grandmaster > NPC Pipeline > ...
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import unreal
except ImportError:
    unreal = None

# Import all pipeline modules
from . import vrm_source
from . import palette_mapper
from . import vrm4u_import
from . import material_factory
from . import archetype_library
from . import cloth_setup
from . import lod_generator
from . import battle_integration
from . import level_populator
from . import audit_npc


# ──────────────────────────────────────────────────────────────────────
# Pipeline State & Configuration
# ──────────────────────────────────────────────────────────────────────

PIPELINE_VERSION = "1.0.0"
PIPELINE_NAME = "GMM NPC Pipeline"

OUTPUT_DIR = Path("Saved/NPCPipeline")
AUDIT_DIR = Path("Saved/Audit")


# ──────────────────────────────────────────────────────────────────────
# Main Pipeline Functions
# ──────────────────────────────────────────────────────────────────────

def generate_npc_batch(
    count: int = 10,
    level: str = "L_PCGTest_Forest",
    archetypes: list[str] = None,
    seed: int = None,
) -> dict[str, Any]:
    """
    Full NPC generation pipeline.

    Args:
        count: Total NPCs to generate (distributed across archetypes)
        level: Target level for population
        archetypes: Specific archetypes to use (default: all 3)
        seed: Random seed for deterministic generation

    Returns:
        Pipeline report with all generated assets and audit results
    """
    if seed is not None:
        import random
        random.seed(seed)

    if archetypes is None:
        archetypes = ["SakuraDreamer", "CosmicWeaver", "MirageDancer"]

    report = {
        "pipeline": PIPELINE_NAME,
        "version": PIPELINE_VERSION,
        "config": {
            "count": count,
            "level": level,
            "archetypes": archetypes,
            "seed": seed,
        },
        "steps": {},
    }

    try:
        # Step 1: Ensure VRM sources exist
        unreal.log("Step 1/6: Checking VRM sources...")
        report["steps"]["vrm_sources"] = _ensure_vrm_sources(archetypes)

        # Step 2: Import VRMs via VRM4U
        unreal.log("Step 2/6: Importing VRMs...")
        report["steps"]["vrm_import"] = import_vrms()

        # Step 3: Setup materials
        unreal.log("Step 3/6: Setting up materials...")
        report["steps"]["materials"] = setup_materials()

        # Step 4: Generate LODs
        unreal.log("Step 4/6: Generating LODs...")
        report["steps"]["lods"] = generate_lods()

        # Step 5: Battle integration
        unreal.log("Step 5/6: Integrating battle data...")
        report["steps"]["battle"] = integrate_battle()

        # Step 6: Populate level
        unreal.log("Step 6/6: Populating level...")
        report["steps"]["population"] = populate_level(level)

        # Step 7: Full audit
        unreal.log("Running final audit...")
        report["steps"]["audit"] = audit_all()

        report["success"] = True
        unreal.log("✓ NPC Pipeline completed successfully!")

    except Exception as e:
        report["success"] = False
        report["error"] = str(e)
        unreal.log_error(f"NPC Pipeline failed: {e}")

    # Save report
    _save_pipeline_report(report)
    return report


def _ensure_vrm_sources(archetypes: list[str]) -> dict:
    """Verify VRM source files exist for required archetypes."""
    from .vrm_source import get_sources_by_archetype, validate_licenses

    sources = {}
    missing = []

    for arch in archetypes:
        arch_sources = get_sources_by_archetype(arch)
        sources[arch] = len(arch_sources)
        for src in arch_sources:
            vrm_path = Path(src.local_path)
            if not vrm_path.exists():
                missing.append(f"{src.source_id}: {vrm_path}")

    validation = validate_licenses()

    return {
        "sources_per_archetype": sources,
        "missing_files": missing,
        "license_validation": validation,
    }


def import_vrms() -> dict:
    """Import all VRMs from registry using VRM4U."""
    results = vrm4u_import.import_all_vrms()
    return {
        "imported": len([r for r in results if r.success]),
        "failed": len([r for r in results if not r.success]),
        "details": [asdict(r) for r in results],
    }


def setup_materials() -> dict:
    """Create master material, MPCs, and material instances for all archetypes."""
    return material_factory.setup_all_materials()


def generate_lods() -> dict:
    """Generate LOD configurations for all NPCs."""
    output_path = lod_generator.export_lod_configs()
    return {
        "config_exported": str(output_path),
        "presets": list(lod_generator.LOD_PRESETS.keys()),
    }


def integrate_battle() -> dict:
    """Generate battle enemy definitions and C++ code."""
    json_path = battle_integration.export_data_asset_json()
    cpp_path = battle_integration.export_cpp_initialization_code()
    validation = battle_integration.validate_against_gmm_config()

    return {
        "json_export": str(json_path),
        "cpp_export": str(cpp_path),
        "validation": validation,
        "archetypes": len(battle_integration.BATTLE_ARCHETYPES),
        "npc_variants": len(battle_integration.NPC_VARIANTS),
    }


def populate_level(level_name: str = "L_PCGTest_Forest") -> dict:
    """Spawn NPCs in the target level."""
    zone = level_populator.create_test_population(level_name)
    result = level_populator.populate_zone(zone)

    return {
        "level": level_name,
        "zone": zone.zone_name,
        "spawned": len(result.get("spawned", [])),
        "failed": len(result.get("failed", [])),
        "details": result,
    }


def audit_all() -> dict:
    """Run full audit on all generated NPCs."""
    return audit_npc.audit_all_npcs()


# ──────────────────────────────────────────────────────────────────────
# Utility Functions
# ──────────────────────────────────────────────────────────────────────

def _save_pipeline_report(report: dict):
    """Save pipeline report to disk."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"pipeline_report_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return str(path)


def get_pipeline_status() -> dict:
    """Get current pipeline status without running."""
    from .vrm_source import get_all_sources, validate_licenses
    from .archetype_library import get_all_archetypes, get_total_npc_count

    return {
        "pipeline": PIPELINE_NAME,
        "version": PIPELINE_VERSION,
        "vrm_sources": len(get_all_sources()),
        "archetypes": len(get_all_archetypes()),
        "planned_npcs": get_total_npc_count(),
        "license_status": validate_licenses(),
        "output_dir": str(OUTPUT_DIR),
        "audit_dir": str(AUDIT_DIR),
    }


def list_available_commands() -> list[str]:
    """List all available pipeline commands."""
    return [
        "generate_npc_batch(count=10, level='L_PCGTest_Forest', seed=42)",
        "import_vrms()",
        "setup_materials()",
        "generate_lods()",
        "integrate_battle()",
        "populate_level(level='L_PCGTest_Forest')",
        "audit_all()",
        "get_pipeline_status()",
    ]


# ──────────────────────────────────────────────────────────────────────
# EnvUI / GMM Command Registration
# ──────────────────────────────────────────────────────────────────────

def register_gmm_commands():
    """Register NPC pipeline commands with GMM EnvUI system."""
    if unreal is None:
        return

    try:
        from gmm.core.audit import GmmAudit
        from gmm.ui.commands import GMM_COMMANDS
    except ImportError:
        unreal.log_warning("GMM core not available, skipping command registration")
        return

    # These will be injected into GMM_COMMANDS by the GMM initialization
    NPC_COMMANDS = {
        "gmm.npc.generate": {
            "label": "Generate NPC Batch",
            "description": "Run full NPC generation pipeline",
            "function": "gmm.npc.generate_npc_batch",
            "category": "NPC Pipeline",
        },
        "gmm.npc.import_vrms": {
            "label": "Import VRMs",
            "description": "Import VRM sources via VRM4U",
            "function": "gmm.npc.import_vrms",
            "category": "NPC Pipeline",
        },
        "gmm.npc.materials": {
            "label": "Setup Materials",
            "description": "Create MToon master material and archetype MPCs",
            "function": "gmm.npc.setup_materials",
            "category": "NPC Pipeline",
        },
        "gmm.npc.lods": {
            "label": "Generate LODs",
            "description": "Generate LOD configurations",
            "function": "gmm.npc.generate_lods",
            "category": "NPC Pipeline",
        },
        "gmm.npc.battle": {
            "label": "Integrate Battle",
            "description": "Generate Melodia enemy definitions",
            "function": "gmm.npc.integrate_battle",
            "category": "NPC Pipeline",
        },
        "gmm.npc.populate": {
            "label": "Populate Level",
            "description": "Spawn NPCs in test level",
            "function": "gmm.npc.populate_level",
            "category": "NPC Pipeline",
        },
        "gmm.npc.audit": {
            "label": "Audit All NPCs",
            "description": "Run full pipeline audit",
            "function": "gmm.npc.audit_all",
            "category": "NPC Pipeline",
        },
        "gmm.npc.status": {
            "label": "Pipeline Status",
            "description": "Show current pipeline status",
            "function": "gmm.npc.get_pipeline_status",
            "category": "NPC Pipeline",
        },
    }

    return NPC_COMMANDS


# ──────────────────────────────────────────────────────────────────────
# Module Exports
# ──────────────────────────────────────────────────────────────────────

__all__ = [
    "generate_npc_batch",
    "import_vrms",
    "setup_materials",
    "generate_lods",
    "integrate_battle",
    "populate_level",
    "audit_all",
    "get_pipeline_status",
    "register_gmm_commands",
    "PIPELINE_VERSION",
    "PIPELINE_NAME",
]

if __name__ == "__main__":
    if unreal:
        # Quick status check
        status = get_pipeline_status()
        print(json.dumps(status, indent=2))
    else:
        print(f"{PIPELINE_NAME} v{PIPELINE_VERSION}")
        print("Run in Unreal Editor Python Console")
        print("\nAvailable commands:")
        for cmd in list_available_commands():
            print(f"  {cmd}")