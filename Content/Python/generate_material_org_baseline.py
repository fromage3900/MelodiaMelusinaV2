"""Material Organization Baseline Census Generator.

Produces Saved/Audit/material_org_baseline.json per BRIEF_material_organization_2026-08-25.md:
  - Scans canonical material directories on disk
  - Identifies asset class (Material, MaterialInstanceConstant, MaterialFunction, MPC, NPC)
  - Identifies parent master relationships via binary uasset inspection
  - Flags duplicate asset names across distinct paths
  - Maps proposed target taxonomies and groups consistent with master_column_scheme.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_BASELINE = PROJECT_ROOT / "Saved" / "Audit" / "material_org_baseline.json"

ROOT_SPECS = [
    ("/Game/EnvSandbox/Materials", PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials"),
    ("/Game/Melodia/_PROJECT/04_Materials", PROJECT_ROOT / "Content" / "Melodia" / "_PROJECT" / "04_Materials"),
    ("/Game/ZenForestTest_MusicalGlam", PROJECT_ROOT / "Content" / "ZenForestTest_MusicalGlam"),
    ("/Game/_PROJECT/04_Materials", PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials"),
    ("/Game/_PROJECT/UPDATEDINSTANCES", PROJECT_ROOT / "Content" / "_PROJECT" / "UPDATEDINSTANCES"),
]

SKIP_SUBSTRINGS = {"_Archive", "_Scratch", "_Quarantine", "_Recovery", "Candidates"}

CLASS_PREFIX_MAP = {
    "M_": "Material",
    "MI_": "MaterialInstanceConstant",
    "MF_": "MaterialFunction",
    "MPC_": "MaterialParameterCollection",
    "NPC_": "NiagaraParameterCollection",
    "T_": "Texture2D",
}


def classify_asset(stem: str) -> str:
    for prefix, cls in CLASS_PREFIX_MAP.items():
        if stem.startswith(prefix):
            return cls
    return "Unknown"


def extract_parent_master(file_path: Path, asset_class: str) -> Optional[str]:
    if asset_class != "MaterialInstanceConstant":
        return None
    try:
        data = file_path.read_bytes()
        # Look for referenced master material names in uasset string table
        matches = set(re.findall(rb'M_[A-Za-z0-9_]+', data))
        decoded = [m.decode("ascii", errors="ignore") for m in matches]
        # Prioritize known master materials
        known_masters = [
            "M_Master_Toon_Universal",
            "M_Master_Toon_Landscape_HeightBlend",
            "M_Master_Nikki",
            "M_Master_Nikki_Landscape",
            "M_Master_SDF_Toon",
            "M_Toon_SDF",
            "M_Master_Gemstone",
            "M_Master_Toon_Character",
            "M_Water_Master_Grand_v6",
            "M_ToonFoliage",
            "M_MelodiaPlant_Wind_NikkiToon",
        ]
        for km in known_masters:
            if km in decoded:
                return km
        # Fallback to any string containing Master
        for m in decoded:
            if "Master" in m and not m.endswith("_Inst") and not m.endswith("_Inst1"):
                return m
        # Fallback to the first M_ that isn't the asset itself
        for m in decoded:
            if m != file_path.stem and not m.startswith("MF_") and not m.startswith("MPC_"):
                return m
    except Exception:
        pass
    return None


def determine_taxonomy_group(name: str, parent_master: Optional[str]) -> str:
    if parent_master == "M_Master_Toon_Universal":
        return "Universal"
    elif parent_master == "M_Master_Toon_Landscape_HeightBlend":
        return "Landscape"
    elif parent_master in ("M_Master_Nikki", "M_Master_Nikki_Landscape"):
        return "Nikki"
    elif parent_master in ("M_Master_SDF_Toon", "M_Toon_SDF"):
        return "SDF"
    elif parent_master == "M_Master_Gemstone":
        return "Gemstone"
    
    # By name
    if "Landscape" in name or "HeightBlend" in name:
        return "Landscape"
    if "Nikki" in name or "Sakura" in name:
        return "Nikki"
    if "SDF" in name or "Cosmic" in name:
        return "SDF"
    if "Water" in name:
        return "Water"
    if "Zen" in name:
        return "ZenForest"
    if "Character" in name or "Melusina" in name:
        return "Character"
    if name.startswith("MF_"):
        return "Function"
    return "Environment"


def run_baseline_census() -> Dict[str, Any]:
    assets: List[Dict[str, Any]] = []
    seen_names: Dict[str, List[str]] = defaultdict(list)
    master_instances: Dict[str, List[str]] = defaultdict(list)

    for reg_prefix, disk_dir in ROOT_SPECS:
        if not disk_dir.exists():
            continue
        for uasset in sorted(disk_dir.rglob("*.uasset")):
            if any(s in uasset.parts for s in SKIP_SUBSTRINGS):
                continue
            stem = uasset.stem
            rel_disk = uasset.relative_to(disk_dir).as_posix()
            asset_reg = f"{reg_prefix}/{rel_disk.rsplit('.', 1)[0]}"
            cls = classify_asset(stem)
            parent = extract_parent_master(uasset, cls)
            tax_group = determine_taxonomy_group(stem, parent)

            entry = {
                "name": stem,
                "path": asset_reg,
                "disk_path": str(uasset.resolve()).replace("\\", "/"),
                "class": cls,
                "parent_master": parent,
                "taxonomy_group": tax_group,
                "size_bytes": uasset.stat().st_size,
            }
            assets.append(entry)
            seen_names[stem].append(asset_reg)
            if parent:
                master_instances[parent].append(asset_reg)

    duplicates = {k: v for k, v in seen_names.items() if len(v) > 1}

    # Identify orphans
    orphans = []
    all_known_material_stems = {a["name"] for a in assets}
    for a in assets:
        if a["class"] == "MaterialInstanceConstant":
            parent = a.get("parent_master")
            if not parent:
                orphans.append({
                    "asset": a["path"],
                    "reason": "Missing detectable parent master"
                })
            elif parent not in all_known_material_stems:
                orphans.append({
                    "asset": a["path"],
                    "parent_master": parent,
                    "reason": "Parent master not present in scanned material roots"
                })

    # Summary by class
    class_counts = defaultdict(int)
    for a in assets:
        class_counts[a["class"]] += 1

    # Masters with instance counts
    master_summary = {}
    for a in assets:
        if a["class"] == "Material":
            insts = master_instances.get(a["name"], [])
            master_summary[a["name"]] = {
                "path": a["path"],
                "instance_count": len(insts),
                "is_zero_instance_candidate": len(insts) == 0,
            }

    report = {
        "schema": "melodia.material_org_baseline.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_assets": len(assets),
        "class_breakdown": dict(class_counts),
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "orphan_count": len(orphans),
        "orphan_sample": orphans[:50],
        "master_census": master_summary,
        "assets": assets,
    }

    OUT_BASELINE.parent.mkdir(parents=True, exist_ok=True)
    OUT_BASELINE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Generated {OUT_BASELINE.resolve()} ({len(assets)} assets cataloged)")
    return report


if __name__ == "__main__":
    run_baseline_census()
