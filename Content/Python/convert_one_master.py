"""Convert ONE material master to Substrate Toon (crash-isolated runner).

Use via Monolith run_python (execute_file) with the target as first arg:
  C:/.../convert_one_master.py /Game/MSPresets/M_MS_Default_Material_VT/M_MS_Default_Material_VT

Converts via convert_masters_to_substrate_toon.main() with an explicit one-path
--paths list, then writes Saved/Audit/convert_one_result.json for the caller.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    if not target:
        unreal.log_error("[one] no target path given")
        return 2

    sys.argv = ["convert_one_master.py", "--paths", target]
    import convert_masters_to_substrate_toon as conv

    rc = conv.main()
    report = ROOT / "Saved" / "Audit" / "convert_one_result.json"
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
        unreal.log(f"[one] done {target} -> {data.get('summary', {})}")
    except Exception:
        unreal.log_warning("[one] result report missing after run")
    return rc


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
