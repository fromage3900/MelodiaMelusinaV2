"""
Probe the UE 5.8 MetaSound node surface BEFORE authoring the rhythm-hit graph.

Rationale (AGENTS.md rule 20 / "never invent APIs"): a synth graph needs exact
node class names and exact input/output pin names. Writing "Oscillator" from
memory produces a graph that fails at build time with an unhelpful error, or
worse, a graph that silently omits a block. This probe lists what actually
exists, with its real pins, so the builder is written against facts.

Read-only. Creates no assets. Run inside the editor via Monolith run_python.

Skill: melodia-audio-architecture
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(
    __file__.resolve().parents[2] / "Saved" / "Audit" / "metasound_node_probe.json"
) if "__file__" in dir() else Path(
    "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/metasound_node_probe.json"
)

# The blocks a struck-metal hit voice needs. Matched case-insensitively
# against the registry, so "osc" finds "Oscillator" or "SineOscillator".
WANTED = [
    "osc", "sine", "tone", "fm",
    "envelope", "adsr", "decay",
    "noise", "random",
    "filter", "biquad", "lowpass",
    "gain", "volume", "mix",
    "delay", "reverb",
    "clamp", "compare", "select", "branch", "switch",
]


def _registry_entries():
    """Best-effort: the registry is reachable a few different ways in 5.8."""
    out = []
    for getter in ("get_all_registered_classes", "get_node_classes"):
        fn = getattr(unreal.MetasoundFrontendRegistry, getter, None)
        if fn is None:
            continue
        try:
            for c in fn():
                out.append(c)
        except Exception:
            continue
    return out


def main() -> int:
    entries = _registry_entries()
    rows = []

    for cls in entries:
        name = str(getattr(cls, "name", "") or "")
        cls_name = str(getattr(cls, "class_name", "") or getattr(cls, "name", ""))
        hay = f"{name} {cls_name}".lower()
        if not any(w in hay for w in WANTED):
            continue

        pins = {}
        try:
            for pin in cls.get_matching_pins() if hasattr(cls, "get_matching_pins") else []:
                pins[str(pin)] = None
        except Exception:
            pass
        rows.append({"name": name, "class": cls_name, "pin_count": len(pins)})

    # Also dump the full class-name list: small, and it is the ground truth the
    # builder will be written against.
    all_names = sorted({str(getattr(c, "name", "")) for c in entries if getattr(c, "name", "")})

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_registered": len(all_names),
        "candidates": rows,
        "all_class_names": all_names,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"METASOUND_PROBE total={len(all_names)} candidates={len(rows)} report={REPORT}")
    print(f"METASOUND_PROBE total={len(all_names)} candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
