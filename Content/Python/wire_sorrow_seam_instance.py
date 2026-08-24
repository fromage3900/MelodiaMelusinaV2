#!/usr/bin/env python3
"""
Wire MI_Fabric_Melusina_SorrowSeam instance spec (no editor mutation until probe green).
Validates m_fabric_melusina.v1.json contract + sorrow_seam.v1.json — read-only.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = json.loads((ROOT / "specs" / "melusina_sorrow_seam.v1.json").read_text())
fabric = json.loads((ROOT / "specs" / "materials" / "m_fabric_melusina.v1.json").read_text())
assert spec["parent_spec"] == "specs/materials/m_fabric_melusina.v1.json"
assert spec["parent_material"] == fabric["asset"]["parent_path"]
assert "presentation consumes only" in spec["signals"]["write"]
print("Sorrow Seam spec OK — parent", fabric["asset"]["parent_path"], "slots", spec["slots"], "instance", spec["cosmetic"]["instance"])
print("Next: when editor live, create MI_Fabric_Melusina_SorrowSeam on M_Fabric_Melusina, set SheenIridescence 0.18 default, wire MPC scalars.")
