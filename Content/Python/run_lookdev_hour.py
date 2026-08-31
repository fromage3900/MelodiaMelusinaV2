"""Lookdev hour orchestrator (2026-08-29) — run all four material workstreams
in one editor session with per-step isolation and a single manifest.

Steps (order matters):
  1. expand_glitter_pile   — MF_MelodiaGlitterPile + master splice + MPC wiring
  2. repair_melodia_ink    — 42-input Custom node repair (diagnose -> fix -> verify)
  3. fix_ppv_stack         — PPV silent-dropper removal + canonical grade weight
  4. build_sdf_architecture_instances — 5 niche SDF MIs + catalog

Each step is wrapped: a failure logs and continues; the manifest records every
step's ok/error and the audit JSON path it wrote. Run inside the UE editor:

    import sys; sys.path.append(r"C:\\EnvironmentPortfolio\\BS_GodFile\\Content\\Python")
    import run_lookdev_hour; run_lookdev_hour.main()

Writes: Saved/Audit/lookdev_hour_2026-08-29.json
"""
from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "lookdev_hour_2026-08-29.json"


def _log(message):
    unreal.log(f"[LookDevHour] {message}")


def main():
    steps = []

    def run(name, fn):
        entry = {"step": name, "started": datetime.now(timezone.utc).isoformat()}
        try:
            result = fn()
            entry["ok"] = True
            entry["result_keys"] = sorted(result.keys()) if isinstance(result, dict) else str(type(result))
            entry["result"] = result if isinstance(result, dict) else None
            _log(f"{name}: OK")
        except Exception as exc:
            entry["ok"] = False
            entry["error"] = str(exc)
            entry["traceback"] = traceback.format_exc(limit=6)
            unreal.log_warning(f"[LookDevHour] {name} FAILED: {exc}")
        entry["finished"] = datetime.now(timezone.utc).isoformat()
        steps.append(entry)

    import expand_glitter_pile
    run("glitter_pile", expand_glitter_pile.main)

    import repair_melodia_ink
    run("melodia_ink_repair", repair_melodia_ink.main)

    import fix_ppv_stack
    run("ppv_stack_fix", fix_ppv_stack.main)

    import build_sdf_architecture_instances
    run("sdf_architecture_instances", build_sdf_architecture_instances.main)

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "ok": all(s["ok"] for s in steps),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _log(f"manifest -> {OUT}  (ok={payload['ok']})")
    return payload


if __name__ == "__main__":
    main()