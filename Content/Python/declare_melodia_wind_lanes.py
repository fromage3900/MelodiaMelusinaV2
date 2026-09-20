"""Declare the canonical Melodia wind lanes on the MPC pair (idempotent).

Authority (owner brief 2026-09-16, corrected 09316fa9):
  MPC_Melodia_Palette  -- SOURCE lane. Wind enters here.
  MPC_Cymatics_Driver  -- DERIVED lane. Sole writer is
                          UMelodiaCymaticsWriterSubsystem; this script only
                          declares the parameters it publishes.

Lane-level ownership inside MPC_Melodia_Palette: the audio-reactive subsystem
is the sole writer of the beat/band lanes (GlobalReactivity, Bass, Mid, Treble,
BeatPhase, BeatPulse, BeatIntensity + the Bass/Mid aliases). Wind uses DISJOINT
names, so neither writer can stomp the other:

  WindDirX / WindDirY / WindStrength        <- OSC / TD / game (this contract)
  GlobalReactivity, Bass, Mid, Treble, ...  <- UMelodiaAudioReactivePresentationSubsystem

Verified live 2026-09-16: MPC_Melodia_Palette declares 51 scalars and already
carries WindStrength; WindDirX/WindDirY are new. MPC_Cymatics_Driver declares
10 scalars, none of them wind.

Declaring a parameter that a runtime write targets matters: writing to an
undeclared collection parameter is a silent no-op (see
converge_landscape_authority_nikki.py stage 0, which had to fix exactly that).

Run: Monolith editor.run_python (execute_file) on this path, or
     import declare_melodia_wind_lanes as d; d.main()
"""
from __future__ import annotations

import json
import time as _time
from datetime import datetime, timezone
from pathlib import Path

import unreal

PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
DRIVER = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"


def _report_path() -> Path:
    """Resolve Saved/Audit under the real project dir.

    Monolith's run_python execs this source without a __file__ binding, so
    Path(__file__) is not available there -- unreal.Paths is the authority.
    """
    try:
        return Path(unreal.Paths.project_dir()) / "Saved" / "Audit" \
            / "melodia_wind_lanes_declaration.json"
    except Exception:
        return (Path(__file__).resolve().parents[2] / "Saved" / "Audit"
                / "melodia_wind_lanes_declaration.json")


REPORT = _report_path()

# (name, default) -- WindStrength already exists on the palette and is left
# untouched so no existing consumer's default shifts. Direction defaults to +X
# so a strength-only sender still produces a defined direction; strength
# defaults to 0.0, which is the zero-delta state (no hue reveal, no bend).
PALETTE_WIND_LANES = [
    ("WindDirX", 1.0),
    ("WindDirY", 0.0),
    ("WindStrength", 0.0),
]

DRIVER_WIND_LANES = [
    ("Cymatic_WindDirX", 1.0),
    ("Cymatic_WindDirY", 0.0),
    ("Cymatic_WindStrength", 0.0),
]


def _load(path: str):
    mpc = unreal.EditorAssetLibrary.load_asset(path)
    if not mpc:
        raise RuntimeError(f"MPC missing on disk: {path}")
    return mpc


def _new_id_hex(seed: int) -> str:
    """A unique non-zero FGuid formatted as UE Digits (AABBCCDD...)."""
    a = (seed * 2654435761) & 0xFFFFFFFF
    b = (seed * 40503 + 0x9E3779B9) & 0xFFFFFFFF
    c = (seed * 2246822519 + 0x85EBCA6B) & 0xFFFFFFFF
    d = (seed * 3266489917 + 0xC2B2AE35) & 0xFFFFFFFF
    a |= 0x10000000  # never all-zero on any component
    b |= 0x00001000
    c |= 0x00100000
    d |= 0x10000000
    return f"{a:08X}{b:08X}{c:08X}{d:08X}"


def _make_entry(name: str, default: float, id_hex: str):
    """Build a CollectionScalarParameter carrying an explicit Id.

    UE 5.8's Python binding exposes only default_value/parameter_name on this
    struct -- Id is protected and set_editor_property('parameter_id'|'id')
    raises. The struct's text form does carry it, so round-trip through
    import_text is the supported path (export_text on a live entry reads
    `(DefaultValue=...,ParameterName="...",Id=<32 hex>)`).
    """
    entry = unreal.CollectionScalarParameter()
    entry.import_text(
        f'(DefaultValue={float(default):f},ParameterName="{name}",Id={id_hex})'
    )
    got = _entry_text(entry)
    if f"Id={id_hex}" not in got:
        raise RuntimeError(f"Id did not round-trip for {name}: {got}")
    if str(entry.get_editor_property("parameter_name")) != name:
        raise RuntimeError(f"name did not round-trip for {name}: {got}")
    return entry


def _entry_text(entry) -> str:
    try:
        return str(entry.export_text())
    except Exception:
        return ""


def declare(mpc_path: str, lanes: list) -> dict:
    """Add any missing scalar lanes. Never mutates or removes existing ones."""
    mpc = _load(mpc_path)
    params = list(mpc.get_editor_property("scalar_parameters"))
    existing = {str(p.get_editor_property("parameter_name")) for p in params}
    added, kept, ids = [], [], {}
    for idx, (name, default) in enumerate(lanes):
        if name in existing:
            kept.append(name)
            continue
        seed = int(_time.time() * 1000) + (len(params) + idx) * 7919
        id_hex = _new_id_hex(seed)
        params.append(_make_entry(name, default, id_hex))
        added.append(name)
        ids[name] = id_hex

    saved = None
    if added:
        mpc.set_editor_property("scalar_parameters", params)
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(mpc))

    # Verify by re-reading reflection, not by trusting set/save return values.
    reread = _load(mpc_path)
    entries = list(reread.get_editor_property("scalar_parameters"))
    present = sorted(str(p.get_editor_property("parameter_name")) for p in entries)
    persisted = {str(p.get_editor_property("parameter_name")): _entry_text(p)
                 for p in entries}
    id_ok = {n: (h in persisted.get(n, "")) for n, h in ids.items()}
    return {
        "mpc": mpc_path,
        "added": added,
        "kept": kept,
        "saved": saved,
        "scalar_count": len(present),
        "all_declared": all(n in present for n, _ in lanes),
        "ids_persisted": id_ok,
        "scalars": present,
    }


def main() -> dict:
    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "authority": "MPC_Melodia_Palette (source) -> UMelodiaCymaticsWriterSubsystem"
                     " -> MPC_Cymatics_Driver (derived)",
        "palette": declare(PALETTE, PALETTE_WIND_LANES),
        "driver": declare(DRIVER, DRIVER_WIND_LANES),
    }
    report["ok"] = bool(report["palette"]["all_declared"]
                        and report["driver"]["all_declared"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[WindLanes] palette +{report['palette']['added']} "
               f"driver +{report['driver']['added']} ok={report['ok']}")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
