"""World Compiler editor apply console.

Compile stays CLI (Tools/world_compiler.py + Tools/world_compiler_ue_driver.py).
This module is Apply / Cleanup / Capture / status only, invoked from EUW_WorldCompiler
or:  world_compiler_ue.py <bundle> <step>
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = ROOT / "Saved" / "WorldCompiler" / "morning_rainbow_bloom_3900"
COMPILE_HINT = (
    "Compile is CLI only: python Tools/world_compiler.py compile recipes/morning_rainbow_bloom.v1.json "
    "&& python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/morning_rainbow_bloom_3900 --lookdev"
)


def _ue():
    import world_compiler_ue as wc

    return wc


def _bundle(path: str | None = None) -> Path:
    p = Path(path) if path else DEFAULT_BUNDLE
    return p if p.is_absolute() else (ROOT / p)


def status(bundle: str | None = None) -> dict:
    bdir = _bundle(bundle)
    ue_dir = bdir / "ue"
    last = {}
    if ue_dir.is_dir():
        files = sorted(ue_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            last = {"step": files[0].stem, "payload": json.loads(files[0].read_text(encoding="utf-8"))}
    return {"compile_stays_cli": COMPILE_HINT, "bundle": str(bdir).replace("\\", "/"), "last_step": last}


def cleanup(bundle: str | None = None) -> dict:
    wc = _ue()
    bdir = _bundle(bundle)
    payload = wc.STEPS["cleanup"](wc._load_bundle(bdir))
    wc._write(bdir, "cleanup", payload)
    return payload


def apply_field(bundle: str | None = None) -> dict:
    """Place/generate the PCG field from an existing bundle. Does not compile."""
    wc = _ue()
    bdir = _bundle(bundle)
    b = wc._load_bundle(bdir)
    out = {}
    for step in ("materials", "table", "volume", "generate"):
        payload = wc.STEPS[step](b)
        wc._write(bdir, step, payload)
        out[step] = payload
    return out


def capture(bundle: str | None = None) -> dict:
    wc = _ue()
    bdir = _bundle(bundle)
    b = wc._load_bundle(bdir)
    out = {}
    for step in ("lookdev_cameras", "lookdev_capture", "ensure_euw", "save"):
        payload = wc.STEPS[step](b)
        wc._write(bdir, step, payload)
        out[step] = payload
    proof = {
        "schema": "melodia.world_compiler_lookdev.v1",
        "recorded_at": date.today().isoformat(),
        "compile_stays_cli": COMPILE_HINT,
        "steps": {k: {"ok": "error" not in (v or {})} for k, v in out.items()},
        "shots": (out.get("lookdev_capture") or {}).get("shots"),
        "hidden_houdini": (out.get("lookdev_capture") or {}).get("hidden_houdini"),
    }
    dest = ROOT / "Saved" / "Audit" / f"world_compiler_morning_rainbow_bloom_lookdev_{date.today().isoformat()}.json"
    dest.write_text(json.dumps(proof, indent=2, default=str), encoding="utf-8")
    out["proof"] = str(dest).replace("\\", "/")
    return out


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = {"status": status, "cleanup": cleanup, "apply": apply_field, "capture": capture}[cmd]
    print(json.dumps(fn(), indent=2, default=str))
