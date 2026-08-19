"""Run the project's existing Monolith PIE smoke harness for a MUAL clip.

The result is an evidence file consumed by ``mual_ue_source_pilot.py``.  This
uses the established MelodiaIntegrationMap and the existing asynchronous
``run_pie_smoke``/``poll_pie_smoke`` actions; it does not create a new test map
or alter runtime assets.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT = PIPELINE_DIR.parents[1]
TOOLS_DIR = PROJECT / "Tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
from mcp_client import monolith  # noqa: E402


DEFAULT_MAP = "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"
DEFAULT_ANIM_CLASS = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
DEFAULT_OUTPUT = PROJECT / "Saved/Audit/mual_pie_smoke.json"


def editor(action: str, **params) -> dict:
    raw = monolith("editor_query", {"action": action, **params}, timeout=120)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        raise RuntimeError(raw)
    try:
        result = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"editor_query:{action} returned invalid JSON: {raw!r}") from exc
    if not isinstance(result, dict):
        raise RuntimeError(f"editor_query:{action} returned a non-object")
    return result


def run(clip_name: str, *, map_path: str = DEFAULT_MAP, expected_anim_class: str = DEFAULT_ANIM_CLASS, duration: float = 5.0, timeout: float = 180.0, output: Path = DEFAULT_OUTPUT) -> int:
    marker = f"MUAL_PIE_{clip_name}_{int(time.time())}"
    report = {
        "schema": "melodia.mual_pie_smoke.v1",
        "clip_name": clip_name,
        "map": map_path,
        "expected_anim_class": expected_anim_class,
        "marker": marker,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "errors": [],
    }
    try:
        started = editor(
            "run_pie_smoke",
            map=map_path,
            duration=duration,
            marker=marker,
            sample_vars=["GroundSpeed", "bShouldMove", "bIsMoving", "DesiredYawDelta"],
            expected_anim_class=expected_anim_class,
            on_compile_errors="refuse",
            teardown_allowed=True,
        )
        session_id = started.get("session_id")
        if not session_id:
            raise RuntimeError(f"PIE smoke did not return a session_id: {started}")
        report["session_id"] = session_id
        deadline = time.time() + timeout
        final = {}
        while time.time() < deadline:
            final = editor("poll_pie_smoke", session_id=session_id, include_samples=True)
            if final.get("status") in {"complete", "stopped", "error"}:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(f"PIE smoke timed out: {session_id}")
        report["result"] = final
        report["ok"] = final.get("status") == "complete" and final.get("ok") is True
        if not report["ok"]:
            report["errors"].append("PIE smoke result did not satisfy status=complete and ok=true")
    except Exception as exc:
        report["errors"].append(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(output), "errors": report["errors"]}, indent=2))
    return 0 if report["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clip_name")
    parser.add_argument("--map", dest="map_path", default=DEFAULT_MAP)
    parser.add_argument("--expected-anim-class", default=DEFAULT_ANIM_CLASS)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    return run(args.clip_name, map_path=args.map_path, expected_anim_class=args.expected_anim_class, duration=args.duration, timeout=args.timeout, output=args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
