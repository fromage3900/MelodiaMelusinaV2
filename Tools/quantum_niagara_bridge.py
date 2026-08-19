"""quantum_niagara_bridge.py — quantum/exotic draw → Niagara ecosystem.

The decision-service link for the Melusina VFX patterns. Draws the winner
from the authored reaction-pattern set through any provider in the quantum
service zoo (qsharp-simulator, qiskit-aer, pbit, entropy, cellular,
commit-reveal, chaos, swarm, oracle, classical-baseline) and publishes the
decision into MPC_Melodia_Palette as QuantumChoice / QuantumSeed /
QuantumBackend, which BP_MelodiaNiagaraDriver fans out project-wide.

Rules (AGENTS.md): presentation-only pattern selection before the session;
hit detection / grading stay classical in UE; classical fallback built in;
the solve runs here (Python), never in Blueprint tick.

Usage:
    python Tools/quantum_niagara_bridge.py [--backend entropy] [--seed 42]
        [--patterns Arc,Sigil] [--service http://127.0.0.1:8008] [--dry-run]

Backends: classical-baseline, qsharp-simulator (2 candidates only), qiskit-aer,
chaos, swarm, pbit, entropy, cellular, commit-reveal, oracle.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
PROJECT = TOOLS.parent
sys.path.insert(0, str(PROJECT / "Content" / "Python"))
sys.path.insert(0, str(TOOLS))

# The authored reaction-pattern set (difficulty = intensity, spacing = rarity).
# These are the patterns the draw picks BETWEEN before a session starts.
PATTERNS = {
    "Arc": {"difficulty": 0.70, "spacing": 0.50},
    "Splash": {"difficulty": 0.60, "spacing": 0.60},
    "Glint": {"difficulty": 0.85, "spacing": 0.35},
    "Sigil": {"difficulty": 0.50, "spacing": 0.80},
    "Dust": {"difficulty": 0.30, "spacing": 0.90},
    "Ripple": {"difficulty": 0.40, "spacing": 0.70},
    "EyeSparkle": {"difficulty": 0.90, "spacing": 0.30},
}

# backend -> normalized MPC value (0..1)
BACKEND_MAP = {
    "classical-baseline": 0.00,
    "qsharp-simulator": 0.15,
    "qiskit-aer": 0.25,
    "chaos": 0.40,
    "swarm": 0.50,
    "pbit": 0.60,
    "entropy": 0.70,
    "cellular": 0.80,
    "commit-reveal": 0.90,
    "oracle": 1.00,
}

# winner -> ReactionColor (Nikki-palette tints; the draw colors the world)
PATTERN_COLORS = {
    "Arc": (1.00, 0.78, 0.72),        # soft coral
    "Splash": (0.62, 0.90, 0.94),     # aqua
    "Glint": (1.00, 0.90, 0.66),      # champagne gold
    "Sigil": (0.80, 0.74, 0.96),      # lavender
    "Dust": (0.96, 0.94, 0.90),       # pearl
    "Ripple": (0.60, 0.84, 0.80),     # teal
    "EyeSparkle": (0.72, 0.82, 1.00), # starlight blue
}

MPC = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"
MONOLITH = "http://127.0.0.1:9316/mcp"


def mcp(tool: str, action: str, params: dict) -> dict:
    import urllib.request

    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": {"action": action, "params": params}},
    }).encode()
    req = urllib.request.Request(MONOLITH, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        envelope = json.loads(resp.read().decode())
    content = envelope.get("result", {}).get("content") or []
    return json.loads(content[0]["text"]) if content else envelope


def draw_local(seed: int, candidates: list[dict], backend: str) -> dict:
    """In-process draw through the quantum service package (the service boundary)."""
    from quantum.draw_providers import rank_and_draw, DEFAULT_BACKEND
    from quantum.draw_providers import PROVIDERS

    if backend not in PROVIDERS:
        backend = DEFAULT_BACKEND
    return rank_and_draw(seed, candidates, backend)


def draw_http(url: str, seed: int, candidates: list[dict], backend: str) -> dict:
    import urllib.request

    payload = json.dumps({"job_type": "rank_layouts", "seed": seed, "candidates": candidates,
                          "backend": backend}).encode()
    req = urllib.request.Request(f"{url}/rank_layouts", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def publish_mpc(choice: float, qseed: float, qbackend: float, color: tuple, pulse: float) -> None:
    """Write the decision into MPC_Melodia_Palette via Monolith."""
    script = (
        "import unreal\n"
        "w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()\n"
        "mpc = unreal.load_asset('%s')\n"
        "unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, 'QuantumChoice', %f)\n"
        "unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, 'QuantumSeed', %f)\n"
        "unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, 'QuantumBackend', %f)\n"
        "unreal.MaterialLibrary.set_vector_parameter_value(w, mpc, 'QuantumReactionColor', "
        "unreal.LinearColor(%f, %f, %f, 1.0))\n"
        "unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, 'QuantumPulse', %f)\n"
        "print('PUBLISHED')"
    ) % (MPC, choice, qseed, qbackend, color[0], color[1], color[2], pulse)
    r = mcp("editor_query", "run_python", {"command": script})
    print(r.get("output", [{}])[0].get("output", r)[:200] if r.get("output") else r)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="entropy", help="provider backend (default: entropy)")
    parser.add_argument("--seed", type=int, default=None, help="seed; None = derive from wall clock")
    parser.add_argument("--patterns", default="", help="comma subset of the 7 patterns")
    parser.add_argument("--service", default="", help="FastAPI service URL (optional; in-process otherwise)")
    parser.add_argument("--dry-run", action="store_true", help="print the draw without touching MPC")
    args = parser.parse_args()

    names = [p.strip() for p in args.patterns.split(",") if p.strip()] or list(PATTERNS)
    for n in names:
        if n not in PATTERNS:
            print(f"unknown pattern '{n}'; known: {', '.join(PATTERNS)}", file=sys.stderr)
            return 2
    candidates = [{"id": n, **PATTERNS[n]} for n in names]
    seed = args.seed if args.seed is not None else int(time.time() * 1000) % (2**31)

    try:
        if args.service:
            result = draw_http(args.service, seed, candidates, args.backend)
        else:
            result = draw_local(seed, candidates, args.backend)
    except Exception as e:
        print(f"[quantum_niagara_bridge] draw failed ({e}); classical fallback", file=sys.stderr)
        from quantum.draw_providers import rank_and_draw
        result = rank_and_draw(seed, candidates, "classical-baseline")

    backend = result.get("backend", "classical-baseline")
    winner = result.get("winner_id")
    n = len(candidates)
    choice = (names.index(winner) / (n - 1)) if n > 1 and winner in names else 0.0
    qseed = (seed % 1000) / 1000.0
    qbackend = BACKEND_MAP.get(backend, 0.0)
    color = PATTERN_COLORS.get(winner, (1.0, 1.0, 1.0))

    print(json.dumps(result, indent=2))
    print(f"[quantum_niagara_bridge] choice={choice:.3f} seed={qseed:.3f} backend={backend} "
          f"color={color}")

    if not args.dry_run:
        try:
            publish_mpc(choice, qseed, qbackend, color, 1.0)
        except Exception as e:
            print(f"[quantum_niagara_bridge] MPC publish failed: {e} "
                  "(systems keep neutral defaults)", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
