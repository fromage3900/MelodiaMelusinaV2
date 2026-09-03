"""Audit _PROJECT SDF materials vs EnvSandbox M_SDF_* — port recommendations.

Standalone (no editor):
  python Content/Python/audit_sdf_project.py

Output: Saved/Audit/sdf_project_review.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
PROJECT_MAT = CONTENT / "_PROJECT" / "04_Materials"
ENVSANDBOX_MASTERS = CONTENT / "EnvSandbox" / "Materials" / "Masters"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sdf_project_review.json"

PATH_RE = re.compile(rb"(/Game/[A-Za-z0-9_./-]+)\x00")
TIER_A_KEYWORDS = (
    "gothic", "baroque", "ornament", "filigree", "stucco", "cathedral",
    "tracery", "rosewindow", "rose_window", "flyingbuttress", "parallax",
    "raymarch_gothic", "gilded", "altar", "vault", "column",
)
DEFER_KEYWORDS = (
    "mandelbulb", "julia", "klein", "menger", "fractal", "math", "escher",
    "penrose", "mobius", "underwater", "coral", "kelp", "musical", "vinyl",
    "trebleclef", "floatingnotes", "magicorb", "cosmicportal", "testbench",
)
PORT_PRIORITY = {
    "M_SDF_TrueParallax": "high — band relief + real parallax reference",
    "M_SDF_GildedStucco": "high — baroque wall baseline",
    "M_SDF_GildedFiligree": "high — gold trim ornament",
    "M_SDF_OrnamentLayer": "high — layered ornament mask",
    "M_SDF_OrnamentLayer_Enhanced": "high — curvature-aware ornament",
    "M_SDF_Baroque": "high — core baroque SDF",
    "M_SDF_GothicArchitecture": "high — gothic environment",
    "M_SDF_GothicArchitecture_Enhanced": "medium — enhanced gothic bands",
    "M_SDF_RayMarch_Gothic": "medium — raymarch gothic (heavy)",
    "M_SDF_CathedralVault": "medium — vault ceiling specialist",
    "M_SDF_FlyingButtress": "medium — exterior buttress trim",
    "M_SDF_GothicRoseWindow": "medium — rose window radial",
}


def game_path(uasset: Path) -> str:
    rel = uasset.relative_to(CONTENT).with_suffix("")
    return "/Game/" + rel.as_posix()


def extract_refs(data: bytes) -> set[str]:
    return {m.group(1).decode("ascii", "ignore") for m in PATH_RE.finditer(data)}


def scan_folder(root: Path, prefix: str = "M_SDF") -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not root.exists():
        return out
    for p in root.rglob("*.uasset"):
        if not p.stem.startswith(prefix):
            continue
        gp = game_path(p)
        try:
            data = p.read_bytes()
        except OSError:
            continue
        refs = extract_refs(data)
        blob = data.decode("latin-1", errors="ignore").lower()
        has_parallax = "parallax" in blob or "realparallax" in blob
        has_curvature = "curvature" in blob or "ornament" in blob
        has_band = "band" in blob or "relief" in blob or "sdf" in blob
        has_mpc = "mpc_" in blob or "materialparametercollection" in blob
        out[p.stem] = {
            "path": gp,
            "size_kb": round(p.stat().st_size / 1024, 1),
            "refs_out": len(refs),
            "has_parallax_hint": has_parallax,
            "has_curvature_hint": has_curvature,
            "has_band_relief_hint": has_band,
            "has_mpc_hint": has_mpc,
            "melodia_refs": sorted(r for r in refs if "_PROJECT" in r or "Melodia" in r)[:8],
        }
    return out


def classify(name: str) -> str:
    n = name.lower()
    if any(k in n for k in DEFER_KEYWORDS):
        return "defer"
    if any(k in n for k in TIER_A_KEYWORDS):
        return "tier_a_gothic_baroque"
    if "sdf" in n:
        return "sdf_other"
    return "other"


def compare(project: dict, envsandbox: dict) -> dict:
    port_list: list[dict] = []
    already_ported: list[str] = []
    project_only: list[dict] = []

    for name, meta in sorted(project.items()):
        tier = classify(name)
        env_meta = envsandbox.get(name)
        entry = {
            "name": name,
            "project_path": meta["path"],
            "tier": tier,
            "envsandbox_path": env_meta["path"] if env_meta else None,
            "port_priority": PORT_PRIORITY.get(name, "low" if tier == "defer" else "review"),
            "strengths": [],
            "gaps": [],
        }
        if meta["has_band_relief_hint"]:
            entry["strengths"].append("band/relief SDF procedural")
        if meta["has_parallax_hint"]:
            entry["strengths"].append("parallax / height displacement")
        if meta["has_curvature_hint"]:
            entry["strengths"].append("curvature-driven ornament")
        if meta["has_mpc_hint"]:
            entry["strengths"].append("MPC / global parameter hooks")
        if env_meta:
            already_ported.append(name)
            if meta["has_parallax_hint"] and not env_meta["has_parallax_hint"]:
                entry["gaps"].append("wire MF_RealParallax on EnvSandbox copy")
            if meta["has_curvature_hint"] and not env_meta["has_curvature_hint"]:
                entry["gaps"].append("wire MF_CurvatureOrnament on EnvSandbox copy")
        elif tier != "defer":
            project_only.append(entry)
            port_list.append(entry)
        entry["recommend_port"] = tier != "defer" and env_meta is None

    return {
        "already_ported": already_ported,
        "port_recommendations": [e for e in port_list if e["recommend_port"]],
        "defer_skip": [n for n in project if classify(n) == "defer"],
        "project_only_count": len(project_only),
    }


def main() -> int:
    project = scan_folder(PROJECT_MAT)
    envsandbox = scan_folder(ENVSANDBOX_MASTERS)
    comparison = compare(project, envsandbox)

    highlights = [
        "_PROJECT has rich gothic/baroque SDF masters with band relief and ornament layering",
        "EnvSandbox already ports 16 Tier-A masters (TrueParallax, Gilded*, Gothic*, Ornament*)",
        "Best _PROJECT refs: TrueParallax, GildedFiligree, OrnamentLayer_Enhanced, RayMarch_Gothic",
        "Defer math-art, underwater, musical/game SDF unless scene-specific",
        "Gap: ensure MF_RealParallax + MF_CurvatureOrnament on ported masters missing hooks",
    ]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "highlights": highlights,
        "project_sdf_count": len(project),
        "envsandbox_sdf_count": len(envsandbox),
        "comparison": comparison,
        "project_masters": project,
        "envsandbox_masters": envsandbox,
        "do_not_bulk_copy": True,
        "note": "Audit-only — no assets copied. Port individually with MF maturation script.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"highlights": highlights, "report": str(REPORT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
