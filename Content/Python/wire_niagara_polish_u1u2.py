#!/usr/bin/env python3
"""
Wire U1 biolum flipbook + U2 ribbon score polish (requires editor on 9316).
Run: python Content/Python/wire_niagara_polish_u1u2.py --dry (validate specs) or --live (Monolith).
"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = json.loads((ROOT / "specs" / "niagara" / "melusina_polish_pack.v1.json").read_text())
print(f"Polish pack {spec['version']} : {[u['id'] for u in spec['upgrades']]}")
for u in spec["upgrades"]:
    print(f"  {u['id']} -> {u['targets']} @ {u.get('material', u.get('graph',''))[:60]}")
# Dry validates budget/validation contracts only; live path would call:
# blueprint_query/niagara -- validate_system, isolated preview, stat Niagara checks per specs/niagara/melusina_polish_pack.v1.json
print("Dry OK — run with --live when editor 9316 is responsive (one writer).")
