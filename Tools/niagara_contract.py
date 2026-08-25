"""niagara_contract.py - canonical machine-readable Niagara User.* contract.

Single source of truth for the project-wide 20-parameter ecosystem contract.
Both the authoring tools (Tools/author_*.py) and the audit tool
(Tools/niagara_ecosystem_audit.py) import this module, so the contract cannot
drift between writers and verifiers.

Accounting: 16 floats + 3 vec3 (WindVector, ImpactPosition, TargetPosition) +
1 LinearColor (ReactionColor) = 20 parameters. The verbal shorthand
"17 floats + WindVector + ReactionColor + DreamVisibility" used in some dated
docs is WRONG and superseded by this module.

Bus sources follow Docs/NIAGARA_ECOSYSTEM_2026-08-09.md and the
BP_MelodiaNiagaraDriver push table. The master driver is the only writer;
systems consume what their graph uses.

Conformance (what niagara_ecosystem_audit.py --contract enforces):
fixed bounds, zero warmup, zero compile errors/warnings, contract params
declared. This module is importable from outside the editor (no Monolith
dependency) so both Tools and docs-side checks share one definition.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical parameter table (ordered - this order is the contract's identity).
#
#   key:  name        -> audit type (float / vec3 / vec4)
#   "ty": niagara authoring type name (NiagaraFloat / Vector3f / LinearColor)
#   "src": live bus source that writes the parameter
#   "note": purpose
# ---------------------------------------------------------------------------
_CONTRACT_TABLE = [
    {"key": "Intensity", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.GlobalReactivity",
     "note": "overall authored strength 0-1"},
    {"key": "Seed", "ty": "NiagaraFloat", "type": "float", "src": "driver: 0 (deterministic variation)",
     "note": "deterministic variation"},
    {"key": "WindVector", "ty": "Vector3f", "type": "vec3", "src": "driver: (WindStrength, 0, 0)",
     "note": "external wind direction/speed"},
    {"key": "Reaction01", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.BeatIntensity",
     "note": "short response envelope"},
    {"key": "ReactionColor", "ty": "LinearColor", "type": "vec4", "src": "MPC QuantumReactionColor (winner tint); driver white neutral",
     "note": "palette lift - the quantum draw colors every system"},
    {"key": "ImpactPosition", "ty": "Vector3f", "type": "vec3", "src": "driver: player location",
     "note": "optional impact location"},
    {"key": "TargetPosition", "ty": "Vector3f", "type": "vec3", "src": "reserved (neutral 0)",
     "note": "optional attraction/destination"},
    {"key": "AudioLow", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.Bass (TD /audio/band/sub,low)",
     "note": "presentation-only audio band"},
    {"key": "AudioMid", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.Mid (TD /audio/band/mid)",
     "note": "presentation-only audio band"},
    {"key": "AudioHigh", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.Treble (TD /audio/band/high,air)",
     "note": "presentation-only audio band"},
    {"key": "BeatPulse", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.BeatPulse (reactivity C++)",
     "note": "per-beat pulse"},
    {"key": "RhythmPulse", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.RhythmPulse (player hit)",
     "note": "player rhythm-hit pulse"},
    {"key": "GlobalReactivity", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.GlobalReactivity",
     "note": "master reactivity gain"},
    {"key": "PlayerProximity", "ty": "NiagaraFloat", "type": "float", "src": "driver-computed clamp(1 - dist/range) per component",
     "note": "player proximity 0..1"},
    {"key": "QuantumChoice", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.QuantumChoice (draw winner 0..1)",
     "note": "quantum decision-service winner"},
    {"key": "QuantumSeed", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.QuantumSeed (normalized draw seed)",
     "note": "quantum draw seed"},
    {"key": "QuantumBackend", "ty": "NiagaraFloat", "type": "float", "src": "MPC_Melodia_Palette.QuantumBackend (provider id 0..1)",
     "note": "quantum provider identity"},
    {"key": "QuantumChoiceInv", "ty": "NiagaraFloat", "type": "float", "src": "driver-computed 1 - QuantumChoice (collapse loser)",
     "note": "inverse of the draw winner"},
    {"key": "QuantumPulse", "ty": "NiagaraFloat", "type": "float", "src": "MPC QuantumPulse (1.0 per draw, driver-decayed ~5/s)",
     "note": "quantum draw pulse"},
    {"key": "DreamVisibility", "ty": "NiagaraFloat", "type": "float", "src": "MPC_SakuraDream.DreamVisibility",
     "note": "global quality/capture visibility"},
]

# audit-side view: name -> "float"|"vec3"|"vec4" (ordered dict)
CONTRACT_PARAMS: dict[str, str] = {row["key"]: row["type"] for row in _CONTRACT_TABLE}

# authoring-side view: list of (name, niagara type name) in contract order
CONTRACT_AUTHOR: list[tuple[str, str]] = [(row["key"], row["ty"]) for row in _CONTRACT_TABLE]

# canonical human-readable accounting (used by docs that cite the contract)
CONTRACT_COUNTS = {
    "total": len(_CONTRACT_TABLE),
    "floats": sum(1 for r in _CONTRACT_TABLE if r["type"] == "float"),
    "vec3": sum(1 for r in _CONTRACT_TABLE if r["type"] == "vec3"),
    "vec4": sum(1 for r in _CONTRACT_TABLE if r["type"] == "vec4"),
}


def contract_info() -> list[dict]:
    """Full per-parameter metadata (key, ty, type, src, note) in contract order."""
    return [dict(row) for row in _CONTRACT_TABLE]


if __name__ == "__main__":
    print(f"contract: {CONTRACT_COUNTS['total']} params "
          f"({CONTRACT_COUNTS['floats']} floats, {CONTRACT_COUNTS['vec3']} vec3, "
          f"{CONTRACT_COUNTS['vec4']} vec4)")
    for row in _CONTRACT_TABLE:
        print(f"  User.{row['key']:16s} {row['type']:6s} <- {row['src']}")
