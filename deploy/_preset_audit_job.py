"""Thin Blender job: audit melodia_gn presets vs registry."""
import sys
import os
import json

DEPLOY = os.path.dirname(os.path.abspath(__file__))
if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)

import surreal_architecture_gen
surreal_architecture_gen.register()

from surreal_arch.melodia_gn.presets import audit_presets

report = audit_presets()
print(json.dumps(report, indent=2))
orphans = report.get("orphan_preset_builders") or []
out = os.path.join(os.path.dirname(DEPLOY), "Saved", "Audit", "preset_audit_last.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"Wrote {out}")
if orphans:
    print(f"ORPHAN PRESET BUILDERS: {orphans}")
    sys.exit(1)
print("preset_audit: OK")
