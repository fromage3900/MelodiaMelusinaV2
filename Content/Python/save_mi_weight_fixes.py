"""Save the TextureWeight fixes applied to Universal instances (persist dirty MIs)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "mi_texture_weight_fix.json"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    targets = [p for p in report.get("fixed_texture_weight", [])]
    saved, failed = [], []
    for path in targets:
        try:
            inst = unreal.load_asset(path)
            if inst and isinstance(inst, unreal.MaterialInstanceConstant):
                unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
                saved.append(path)
            else:
                failed.append(path)
        except Exception as exc:
            failed.append(f"{path} ({exc})")
    unreal.log(f"[mi_save] saved={len(saved)} failed={len(failed)}")
    print(f"saved: {len(saved)} | failed: {len(failed)}")
    for f in failed:
        print("  ", f)
    return 0


if __name__ == "__main__":
    time.sleep(3)
    sys.exit(main())
