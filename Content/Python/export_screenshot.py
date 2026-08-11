"""Export screenshot from current editor viewport to Saved/Portfolio/Screenshots/.

Run (editor):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/export_screenshot.py"
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/export_screenshot.py" --width 1920 --height 1080
"""
from __future__ import annotations

import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "Screenshots"


def _parse_res() -> tuple[int, int]:
    w, h = 1920, 1080
    for i, arg in enumerate(sys.argv):
        if arg == "--width" and i + 1 < len(sys.argv):
            try:
                w = int(sys.argv[i + 1])
            except ValueError:
                pass
        if arg == "--height" and i + 1 < len(sys.argv):
            try:
                h = int(sys.argv[i + 1])
            except ValueError:
                pass
    return w, h


def capture_screenshot(width: int = 1920, height: int = 1080) -> dict:
    import unreal

    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{ts}_{width}x{height}.png"
    out_path = out_dir / filename
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(
            width, height, str(out_path), show_dialog=False, override_override=True
        )
    except Exception:
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(
                width, height, str(out_path), show_dialog=False
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
    return {"ok": True, "path": str(out_path), "width": width, "height": height, "filename": filename}


def main() -> int:
    w, h = _parse_res()
    result = capture_screenshot(w, h)
    print(json.dumps(result, indent=2) if "json" in sys.argv else str(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
