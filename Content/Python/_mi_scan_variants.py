"""Scan Saved/Audit/copernicus_cymatic and report texture suffixes per variant.

Run: python Content/Python/_mi_scan_variants.py
"""
from __future__ import annotations
from pathlib import Path

AUDIT = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/copernicus_cymatic")
HEADER = "T_Cymatic_"
EXISTING = {
    "CavernWeave", "ChoirStone", "CrystalCathedral", "FractalCathedral",
    "FrostBloom", "FrozenFracture", "GildedCoral", "MoltenCore",
    "PearlWeave", "SingingSilk", "StarlitLoom", "VoronoiSacredGeometry",
}

print(f"{'VARIANT':<28} {'#PNGS':>5} {'SUFFIXES'}")
print("-" * 90)
missing = []
for d in sorted(AUDIT.iterdir()):
    if not d.is_dir() or d.name.startswith("_"):
        continue
    files = list(d.glob("*.png"))
    suffixes = set()
    for f in files:
        s = f.stem
        if s.startswith(HEADER):
            suffixes.add(s[len(HEADER):])
    has_mi = d.name in EXISTING
    flag = "" if has_mi else " *** NO MI ***"
    if not has_mi:
        missing.append(d.name)
    print(f"{d.name:<28} {len(files):>5} {', '.join(sorted(suffixes))}{flag}")

print()
print(f"Total variants: {len(EXISTING) + len(missing)} (existing MIs: {len(EXISTING)}, missing: {len(missing)})")
print(f"Missing variants: {missing}")