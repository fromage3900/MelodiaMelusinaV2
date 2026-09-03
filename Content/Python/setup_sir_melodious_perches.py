"""Spawn SirMelodiousPerch actors in shipping levels.

This tool spawns AMelodiaExplorationInteractionVolume actors configured as
perch landing spots for Sir Melodious's flight mode. Each perch:

- InteractionId = "perch.sirmelodious.landing"
- bRequireMelusina = False (Sir lands here, not Melusina)
- bOneShot = False (reusable)
- A placeholder static mesh (can be swapped to environment-specific meshes later)

Perch placement philosophy:
  - High points (cathedral arches, cliff edges, rooftop ridges)
  - Exploration junctions (where flight paths branch)
  - At intervals along long flight paths (~every 3.5s of flight)
  - Visual landmarks that read as "Sir was here" from a distance

Usage:
  python Content/Python/setup_sir_melodious_perches.py            # dry-run (report only)
  python Content/Python/setup_sir_melodious_perches.py --apply     # spawn in editor
  python Content/Python/setup_sir_melodious_perches.py --level ZenForestTest --apply

Requires the editor to be running with Monolith on port 9316 for --apply.
Dry-run mode reads the filesystem only and reports what would be spawned.
"""

import argparse
import json
import os
import sys

# ─── Perch definitions per level ──────────────────────────────────────────────

# Each perch is (x, y, z, label) — world-space coordinates in the level.
# These are starting points; the level designer should adjust them visually.
# Z is up; perches should be placed at elevated positions (high points).

PERCHES = {
    # ZenForestTest — the hero reference level
    "/Game/ZenForestTest": [
        (320.0, 180.0, 450.0, "perch_zen_arch_west"),
        (680.0, 420.0, 520.0, "perch_zen_cliff_east"),
        (150.0, 600.0, 380.0, "perch_zen_forest_south"),
        (900.0, 200.0, 600.0, "perch_zen_tower_north"),
    ],

    # L_KaleidoNave — the kaleidoscope nave level
    "/Game/EnvSandbox/Environments/L_KaleidoNave": [
        (400.0, 300.0, 500.0, "perch_nave_arch"),
        (200.0, 700.0, 450.0, "perch_nave_balcony"),
        (800.0, 400.0, 550.0, "perch_nave_column"),
    ],

    # L_FallenMoon — the fallen moon level
    "/Game/EnvSandbox/Environments/L_FallenMoon": [
        (300.0, 200.0, 400.0, "perch_moon_crater_edge"),
        (600.0, 500.0, 480.0, "perch_moon_ridge"),
        (150.0, 800.0, 360.0, "perch_moon_shore"),
    ],

    # L_MelusinaMorning — the morning/bedroom level
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning": [
        (160.0, 130.0, 220.0, "perch_morning_window"),  # near the existing perch_location
        (400.0, 300.0, 350.0, "perch_morning_rooftop"),
    ],

    # L_Template — the template test level
    "/Game/EnvSandbox/_Template/L_Template": [
        (200.0, 200.0, 300.0, "perch_template_test_01"),
        (600.0, 600.0, 350.0, "perch_template_test_02"),
    ],

    # LV_SeaAbove_Prototype — the Sea Above prototype
    "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype": [
        (500.0, 300.0, 800.0, "perch_sea_above_cathedral_arch"),
        (300.0, 600.0, 750.0, "perch_sea_above_bell_proxy"),
        (700.0, 200.0, 900.0, "perch_sea_above_high_ledge"),
    ],
}

# ─── Perch actor configuration ─────────────────────────────────────────────────

PERCH_INTERACTION_ID = "perch.sirmelodious.landing"
PERCH_LABEL_PREFIX = "SirMelodiousPerch_"

# Placeholder mesh — a simple cylinder that reads as a perch from a distance
PLACEHOLDER_MESH_PATH = "/Engine/BasicShapes/Cylinder"
PLACEHOLDER_SCALE = (0.35, 0.35, 0.8)  # narrow, tall-ish — like a perch post

# The existing perch proxy from setup_melodia_opening_levels.py uses (0.35, 0.35, 1.4)
# We use a slightly shorter scale for exploration perches


def dry_run():
    """Report what would be spawned — no editor required."""
    print("=== SirMelodiousPerch Dry Run ===")
    print(f"  Interaction ID: {PERCH_INTERACTION_ID}")
    print(f"  Placeholder mesh: {PLACEHOLDER_MESH_PATH}")
    print(f"  Scale: {PLACEHOLDER_SCALE}")
    print()

    total = 0
    for level_path, perches in PERCHES.items():
        print(f"  Level: {level_path}")
        for x, y, z, label in perches:
            actor_name = f"{PERCH_LABEL_PREFIX}{label}"
            print(f"    {actor_name}")
            print(f"      Location: ({x}, {y}, {z})")
            print(f"      InteractionId: {PERCH_INTERACTION_ID}")
            print(f"      bRequireMelusina: False")
            print(f"      bOneShot: False")
            total += 1
        print()

    print(f"  Total perches: {total}")
    print(f"  Levels: {len(PERCHES)}")
    print()
    print("  Run with --apply to spawn in the editor (requires Monolith on 9316).")


def spawn_in_editor(level_path_filter=None):
    """Spawn perches in the editor via Monolith. Requires the editor running."""
    print("ERROR: Editor spawning is not yet implemented.")
    print("The Perch BP must be created first (BP_SirMelodiousPerch),")
    print("then this script can spawn instances via Monolith.")
    print()
    print("To create BP_SirMelodiousPerch in the editor:")
    print("  1. Create a new Blueprint based on AMelodiaExplorationInteractionVolume")
    print(f"  2. Set InteractionId = '{PERCH_INTERACTION_ID}'")
    print("  3. Set bRequireMelusina = False")
    print("  4. Set bOneShot = False")
    print("  5. Add a static mesh component with a placeholder shape")
    print(f"  6. Save as /Game/Melodia/Characters/SirMelodious/BP_SirMelodiousPerch")
    print()
    print("After the BP exists, re-run this script with --apply to place instances.")

    # Write the spawn manifest for later use
    manifest = {
        "interaction_id": PERCH_INTERACTION_ID,
        "placeholder_mesh": PLACEHOLDER_MESH_PATH,
        "scale": list(PLACEHOLDER_SCALE),
        "levels": {},
    }
    for level_path, perches in PERCHES.items():
        if level_path_filter and level_path_filter not in level_path:
            continue
        manifest["levels"][level_path] = [
            {
                "name": f"{PERCH_LABEL_PREFIX}{label}",
                "location": [x, y, z],
                "label": label,
            }
            for x, y, z, label in perches
        ]

    manifest_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "Saved", "Audit", "sir_melodious_perch_manifest.json"
    )
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written to: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Spawn SirMelodiousPerch actors in shipping levels."
    )
    parser.add_argument("--apply", action="store_true", help="Spawn in editor (requires Monolith)")
    parser.add_argument("--level", type=str, default=None, help="Filter to a specific level path")
    args = parser.parse_args()

    if args.apply:
        spawn_in_editor(level_path_filter=args.level)
    else:
        dry_run()


if __name__ == "__main__":
    main()
