"""Integrated PCG pillar audit — scale, alignment, walkability, density heatmaps.

Run in-editor:
  py Content/Python/pcg_pillar_audit.py

Outputs:
  Saved/Audit/pcg_pillar_audit_{timestamp}.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_pillar_audit.json"


def audit_mesh_alignment(role: str, paths: list[str]) -> dict:
    """Check mesh bounds and pivot alignment for walkability."""
    if unreal is None:
        return {"role": role, "error": "unreal not available"}

    import pcg_scale_alignment as sa

    bounds_list = [sa.get_mesh_bounds(p) for p in paths if p]
    return sa.verify_role_scales(role, bounds_list)


def audit_volume_density(level_path: str) -> dict:
    """Check ISM counts and density bands for walkability."""
    import pcg_scale_alignment as sa

    return sa.generate_heatmap_data(level_path)


def run_pillar_audit(pillar_key: str) -> dict:
    """Full audit for a single pillar including architectural scale checks."""
    import pcg_portfolio_standards as std
    import pcg_scale_alignment as sa

    level_path = f"{std.LEVEL_WP_ROOT}/L_WP_{pillar_key}"

    report = {
        "pillar": pillar_key,
        "level": level_path,
        "mesh_alignment": {},
        "walkability": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Check key role scales for grand buildings
    key_roles = ["column", "arch", "floor", "stair", "grass", "rock", "flower", "moss"]
    for role in key_roles:
        paths = std.SCATTER_MESHES.get(role, [])
        report["mesh_alignment"][role] = audit_mesh_alignment(role, paths)

    # Check volume density
    report["walkability"] = audit_volume_density(level_path)

    # Instance density proves that generation produced output; it does not prove
    # capsule clearance, navmesh connectivity, route width, slope, or step limits.
    aligned = all(
        r.get("scales_consistent", False) or r.get("reason") == "no meshes"
        for r in report["mesh_alignment"].values()
    )
    density_output_ok = report["walkability"].get("total_ism", 0) > 10

    report["summary"] = {
        "mesh_alignment_ok": aligned,
        "density_output_ok": density_output_ok,
        "walkability_evaluated": False,
        "walkability_ok": False,
        "walkability_reason": (
            "Not evaluated: requires navmesh reachability and character-clearance queries; "
            "ISM count is only a generation-health metric."
        ),
        "total_ism": report["walkability"].get("total_ism", 0),
        "passed": False,
    }
    return report


def main() -> int:
    if unreal is None:
        print("ERROR: This script must run inside Unreal Editor")
        return 1

    import pcg_portfolio_standards as std

    pillars = ["SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery"]
    results = []

    for pillar in pillars:
        print(f"[PCGAudit] Auditing {pillar}...")
        result = run_pillar_audit(pillar)
        results.append(result)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    all_passed = all(r.get("summary", {}).get("passed", False) for r in results)
    print(f"[PCGAudit] Overall: {'PASSED' if all_passed else 'NEEDS WORK'} -> {REPORT}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())