"""Generate the SDF/Escher/baroque fold-in manifest for runtime specs.

Reads the live asset registry (via Monolith run_python) and classifies every
material under /Game/_PROJECT/04_Materials into runtime families with port +
conversion state. Writes specs/sdf_runtime_families.json.

Grounding rule: census from the live registry, never hand-typed names. The
MooaToon tree is classified DEAD (owner decision 2026-08-12) and excluded from
port targets; every non-MooaToon master in _PROJECT is folded onto the
EnvSandbox Substrate Toon spine.

Run in editor via Monolith editor_query run_python (path is the workspace root).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_MAT_ROOT = "/Game/_PROJECT/04_Materials"
ENV_MAT_ROOT = "/Game/EnvSandbox/Materials"

OUT_PATH = Path(__file__).resolve().parents[2] / "specs" / "sdf_runtime_families.json"

DEAD_FAMILIES = {"MooaToon"}  # owner decision 2026-08-12: dead, use Substrate Toon

# Family classification by path fragment -> (family, runtime role)
FAMILY_BY_FRAGMENT: list[tuple[str, str, str]] = [
    ("Underwater", "Aquatic", "environment"),
    ("Cathedral", "Cathedral", "environment"),
    ("baroque", "Baroque", "architecture"),
    ("Cosmo", "Cosmic", "skybox"),
    ("Glitter", "Glitter", "accent"),
    ("Impasto", "Impasto", "painterly"),
    ("Masters", "EnhancedMaster", "master"),
    ("Functions", "Function", "function"),
    ("PostProcess", "PostProcess", "postprocess"),
    ("Dev", "Dev", "dev"),
    ("MooaToon", "Dead", "dead"),
]

# Distinctive stems (suffixes after the family subfolder) that get their own
# family label when they live at the SDF root.
STEM_FAMILY_OVERRIDES: dict[str, tuple[str, str]] = {
    "Escher": ("Escher", "mathematical"),
    "Mandelbulb": ("MathArt", "mathematical"),
    "Menger": ("MathArt", "mathematical"),
    "Julia": ("MathArt", "mathematical"),
    "Klein": ("MathArt", "mathematical"),
    "Mobius": ("MathArt", "mathematical"),
    "Penrose": ("MathArt", "mathematical"),
    "Sierpinski": ("MathArt", "mathematical"),
    "SheetMusic": ("Musical", "musical"),
    "GrandStaff": ("Musical", "musical"),
    "TrebleClef": ("Musical", "musical"),
    "VinylRecord": ("Musical", "musical"),
    "FloatingNotes": ("Musical", "musical"),
    "Musical": ("Musical", "musical"),
    "RoseWindow": ("Cathedral", "architecture"),
    "StainedGlass": ("Cathedral", "architecture"),
    "FlyingButtress": ("Cathedral", "architecture"),
    "CathedralVault": ("Cathedral", "architecture"),
    "Gothic": ("Cathedral", "architecture"),
    "Baroque": ("Baroque", "architecture"),
    "GildedAltar": ("Baroque", "architecture"),
    "GildedFiligree": ("Baroque", "architecture"),
    "GildedStucco": ("Baroque", "architecture"),
    "OrnamentLayer": ("Baroque", "architecture"),
    "TrueParallax": ("Baroque", "architecture"),
    "HybridStone": ("Stone", "architecture"),
    "AbyssalVent": ("Aquatic", "environment"),
    "Anemone": ("Aquatic", "environment"),
    "Bioluminescence": ("Aquatic", "environment"),
    "BubbleColumn": ("Aquatic", "environment"),
    "Caustics": ("Aquatic", "environment"),
    "Coral": ("Aquatic", "environment"),
    "FishSchool": ("Aquatic", "environment"),
    "Kelp": ("Aquatic", "environment"),
    "ThermalGlow": ("Aquatic", "environment"),
    "CosmicPortal": ("Cosmic", "skybox"),
    "CrystallineSpire": ("Cosmic", "skybox"),
    "InfinityMirror": ("Cosmic", "skybox"),
    "MagicOrb": ("Cosmic", "skybox"),
    "MetalShards": ("Cosmic", "skybox"),
    "FloralMagic": ("Cosmic", "skybox"),
    "Grass": ("Nature", "environment"),
    "Foliage": ("Nature", "environment"),
    "Water": ("Water", "environment"),
}


def classify(asset_path: str) -> dict:
    rel = asset_path.replace(f"{PROJECT_MAT_ROOT}/", "")
    parts = rel.split("/")
    name = parts[-1].split(".")[0]
    folder = parts[0] if len(parts) > 1 else "SDF"
    family, role = "SDF", "procedural"
    for frag, fam, rl in FAMILY_BY_FRAGMENT:
        if folder.startswith(frag):
            family, role = fam, rl
            break
    if family == "SDF":
        for token, (fam, rl) in STEM_FAMILY_OVERRIDES.items():
            if token in name:
                family, role = fam, rl
                break
    is_dead = family == "Dead"
    is_master = name.startswith("M_") and not name.startswith("MI_")
    is_instance = name.startswith("MI_")
    kind = "master" if is_master else ("instance" if is_instance else "other")
    return {
        "name": name,
        "path": asset_path,
        "folder": folder,
        "family": family,
        "role": role,
        "kind": kind,
        "dead": is_dead,
        "port_target": None if (is_dead or not is_master) else f"{ENV_MAT_ROOT}/Masters/{name}",
    }


def main() -> int:
    eal = unreal.EditorAssetLibrary
    if not eal.does_directory_exist(PROJECT_MAT_ROOT):
        print("PROJECT_MAT_ROOT missing; aborting")
        return 1
    assets = eal.list_assets(PROJECT_MAT_ROOT, recursive=True, include_folder=False)
    entries = sorted((classify(a) for a in assets), key=lambda e: (e["family"], e["name"]))

    # EnvSandbox-side state: which masters/instances already exist
    env_assets = eal.list_assets(ENV_MAT_ROOT, recursive=True, include_folder=False)
    env_names = {a.rsplit("/", 1)[-1].split(".")[0] for a in env_assets}

    summary: dict = {}
    for e in entries:
        key = f"{e['family']}.{e['kind']}"
        summary[key] = summary.get(key, 0) + 1
        if e["kind"] == "master":
            e["port_state"] = "present" if e["name"] in env_names else "gap"
    total_gap = sum(1 for e in entries if e.get("port_state") == "gap")

    payload = {
        "schema": "sdf_runtime_families.v1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "project_material_root": PROJECT_MAT_ROOT,
        "env_sandbox_material_root": ENV_MAT_ROOT,
        "policy": {
            "mooatoon": "DEAD (owner 2026-08-12) - excluded from port; substrate toon only",
            "port_target_folder": f"{ENV_MAT_ROOT}/Masters",
            "conversion": "Strategy C: preserve graph, swap root to SubstrateToonBSDF -> MP_FRONT_MATERIAL",
        },
        "summary": summary,
        "master_gap_count": total_gap,
        "entries": entries,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(entries)} entries, {total_gap} master gaps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
