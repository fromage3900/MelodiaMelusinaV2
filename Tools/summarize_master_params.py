"""Summarize live parameter inventory of the four masters (read-only, repo-side).

Reads Saved/Audit/master_graphs_<latest>/ exports and prints name lists grouped
by kind, so the canonical column (group) schemes can be built data-driven.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

OUT_ROOT = Path(__file__).resolve().parents[1] / "Saved" / "Audit"


def latest_dir() -> Path:
    dirs = sorted(OUT_ROOT.glob("master_graphs_*"))
    return dirs[-1] if dirs else sys.exit("no master_graphs export dir found")


def load(stem: str) -> dict:
    f = sorted((latest_dir()).glob(f"{stem}.json"))
    return json.loads(f[-1].read_text(encoding="utf-8"))


def dump(stem: str) -> None:
    d = load(stem)
    p = d["get_material_parameters"]
    sc = [s["name"] for s in (p.get("scalar_parameters") or [])]
    vc = [v["name"] for v in (p.get("vector_parameters") or [])]
    tc = [t["name"] for t in (p.get("texture_parameters") or [])]
    sw = [s["name"] for s in (p.get("static_switch_parameters") or [])]
    print(f"=== {stem} === scalars={len(sc)} vectors={len(vc)} textures={len(tc)} switches={len(sw)}")
    print("SWITCHES:", ", ".join(sw))
    print("TEXTURES:", ", ".join(tc))
    print("VECTORS:", ", ".join(vc))
    print()


if __name__ == "__main__":
    stems = sys.argv[1:] or [
        "M_Master_Toon_Universal",
        "M_Master_Toon_Landscape_HeightBlend",
        "M_Master_Nikki",
        "M_Master_Nikki_Landscape",
    ]
    for s in stems:
        dump(s)
