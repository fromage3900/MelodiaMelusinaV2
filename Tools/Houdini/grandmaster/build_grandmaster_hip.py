#!/usr/bin/env python3
"""Create the Melodia Grandmaster authoring HIP in a clean Hython process.

This is a scene/workspace scaffold, not a world generator or a new compiler.
It links the current Universe Foundry, Houdini Foundry and World Compiler inputs
without mutating Unreal. A real Houdini 22 GUI/Engine proof is still required.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HIP = ROOT / "Saved/HoudiniFoundry/Grandmaster/Melodia_Grandmaster.hip"
HDA = "hda/CrystalCathedralV3.hda"
PROCEDURAL_RECIPE = "recipes/houdini_foundry/crystal_cathedral_6bay_harmony.v1.json"
WORLD_RECIPE = "recipes/kaleido_archipelago.v1.json"
GENOME = "specs/universe/faraway_mother.world_genome.v1.json"
DELTA = "specs/universe/faraway_mother.resolved_demo.world_delta.v1.json"
SOURCES = (
    HDA, PROCEDURAL_RECIPE, WORLD_RECIPE, GENOME, DELTA,
    "Tools/universe_foundry.py", "Tools/world_compiler.py",
    "Tools/Houdini/foundry/houdini_foundry.py",
)
LANES = (
    ("A0_FOUNDRY_MISSION", (-7, 3), (0.31, 0.46, 0.72), "World Zero genome + delta / Universe Foundry; reference only"),
    ("B0_WORLD_COMPILER", (-3, 3), (0.26, 0.61, 0.55), "Kaleido archipelago world recipe / existing compiler; reference only"),
    ("C0_FIELDS_ECOLOGY", (1, 3), (0.31, 0.61, 0.40), "FieldAtlas/PCG and ecology bakes; add validated outputs here"),
    ("D0_COPERNICUS_LOOKDEV", (5, 3), (0.75, 0.49, 0.64), "Non-authoritative material and resonance lookdev"),
    ("E0_BAKE_EVIDENCE", (9, 3), (0.76, 0.56, 0.29), "Bakes, manifests, hashes; no direct Unreal mutation"),
)


def preflight(root: Path, use_cathedral: bool) -> list[str]:
    needed = [x for x in SOURCES if use_cathedral or x != HDA]
    return [x for x in needed if not (root / x).is_file()]


def invoke(root: Path, *args: str) -> None:
    """Run the canonical CLI; never copy its compile/validation code."""
    proc = subprocess.run([sys.executable, *args], cwd=str(root), check=False)
    if proc.returncode:
        raise RuntimeError(f"Existing authority tool failed ({proc.returncode}): {' '.join(args)}")


def refresh_offline(root: Path) -> None:
    """Explicitly requested offline validation/compile, no UE/editor operations."""
    invoke(root, "Tools/universe_foundry.py", "validate", "--genome", GENOME, "--delta", DELTA)
    invoke(root, "Tools/universe_foundry.py", "compile", "--genome", GENOME, "--delta", DELTA)
    invoke(root, "Tools/world_compiler.py", "validate", WORLD_RECIPE)
    invoke(root, "Tools/world_compiler.py", "compile", WORLD_RECIPE)
    invoke(root, "Tools/Houdini/foundry/houdini_foundry.py", "validate", PROCEDURAL_RECIPE)


def annotate(node, caption: str, color) -> None:
    import hou
    node.setColor(hou.Color(color))
    node.setComment(caption)
    try:
        node.setGenericFlag(hou.nodeFlag.DisplayComment, True)
    except (AttributeError, hou.Error):
        pass


def build(root: Path, output: Path, use_cathedral: bool) -> dict:
    import hou
    # Always run in an isolated Hython process. Do not clear an artist's open GUI HIP.
    if hou.isUIAvailable():
        raise RuntimeError("Refusing to reset an interactive Houdini session: run with hython.exe")
    hou.hipFile.clear(suppress_save_prompt=True)
    if use_cathedral:
        hou.hda.installFile(str(root / HDA))
    obj = hou.node("/obj")
    master = obj.createNode("subnet", "MELODIA_GRANDMASTER")
    annotate(master, "Grandmaster Studio | Authoring only | World truth stays in UE", (0.48, 0.37, 0.70))
    master.setUserData("melodia.authority", "authoring_only")
    master.setUserData("melodia.foundry.genome", GENOME)
    master.setUserData("melodia.foundry.delta", DELTA)
    master.setUserData("melodia.world_compiler.recipe", WORLD_RECIPE)
    master.setUserData("melodia.houdini_foundry.recipe", PROCEDURAL_RECIPE)
    master.setUserData("melodia.cook_policy", "explicit_manual_only")

    for name, pos, color, caption in LANES:
        marker = master.createNode("null", name)
        marker.setPosition(hou.Vector2(*pos))
        annotate(marker, caption, color)
        marker.setUserData("melodia.status", "reference_only")

    if use_cathedral:
        cathedral = master.createNode("CrystalCathedralV3", "C1_CRYSTAL_CATHEDRAL_V3")
        cathedral.setPosition(hou.Vector2(1, -1))
        annotate(cathedral, "Existing 18-control HDA | four outputs | no automatic bake", (0.65, 0.58, 0.91))
        cathedral.setUserData("melodia.recipe", PROCEDURAL_RECIPE)
    else:
        marker = master.createNode("null", "C1_CATHEDRAL_HDA_NOT_LOADED")
        marker.setPosition(hou.Vector2(1, -1))
        annotate(marker, "Optional Cathedral HDA not loaded", (0.66, 0.56, 0.53))

    master.moveToGoodPosition()
    output.parent.mkdir(parents=True, exist_ok=True)
    hou.hipFile.save(file_name=str(output))
    return {
        "schema": "melodia.grandmaster.scene_scaffold.v1",
        "status": "SCENE_SCAFFOLD_ONLY",
        "hip": str(output),
        "houdini_version": hou.applicationVersionString(),
        "root_node": master.path(),
        "hda_instantiated": use_cathedral,
        "universe_foundry_inputs": [GENOME, DELTA],
        "world_compiler_recipe": WORLD_RECIPE,
        "houdini_foundry_recipe": PROCEDURAL_RECIPE,
        "runtime_or_ue_proof": False,
        "mission_ref_attached": False,
        "integration_note": "Mission/World Compiler references only: explicitly compile and validate via existing CLIs; do not call this an end-to-end bridge proof.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="stdlib-only preflight; no Houdini import")
    parser.add_argument("--refresh-offline", action="store_true", help="explicitly run canonical offline compilers before HIP creation")
    parser.add_argument("--no-cathedral", action="store_true", help="omit Cathedral V3 instance (useful for lightweight authoring)")
    parser.add_argument("--out", type=Path, default=DEFAULT_HIP)
    parser.add_argument("--force", action="store_true", help="overwrite only the specified HIP output, never backups or sources")
    args = parser.parse_args(argv)
    root = ROOT
    missing = preflight(root, not args.no_cathedral)
    if missing:
        print("ERROR: missing canonical inputs:\n" + "\n".join("  " + p for p in missing), file=sys.stderr)
        return 2
    if args.check:
        print("PASS: all Grandmaster source paths exist (Houdini cook not tested)")
        return 0
    output = args.out.expanduser().resolve()
    if output.exists() and not args.force:
        parser.error(f"Refusing to overwrite existing HIP: {output} (use --out or --force)")
    if args.refresh_offline:
        refresh_offline(root)
    report = build(root, output, not args.no_cathedral)
    receipt = output.with_suffix(".scaffold.json")
    receipt.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CREATED", output)
    print("RECEIPT", receipt)
    print("NEXT: inspect in Houdini GUI; World Compiler/UE write and save/reload proof are NOT performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
