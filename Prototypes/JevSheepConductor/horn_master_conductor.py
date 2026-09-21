"""Horn Master Conductor — Jev selects the master horn setup for the Choral Sheep.
Doctrine: system-one-conductor skill. Jev ONLY selects among authored options;
closed sets; deterministic fallback labeled classical-fallback; live labeled jev-live.
One-shot decision (no cooldown needed): the master horn setup for the flock.
Run:  python Prototypes/JevSheepConductor/horn_master_conductor.py
Live: TYPESAFE_API_KEY=<hermeskey> python Prototypes/JevSheepConductor/horn_master_conductor.py
"""
import json
import math
import os
from typing import Any, Optional

HORN_OPTIONS = (
    "FILIGREE_HERITAGE",      # repo filigree_spiral gold openwork curl-crests (v1 heritage)
    "ANATOMICAL_KERATIN",     # solid ridged log-spiral keratin horns (v2 anatomy doctrine)
    "LISSAJOUS_CHORD",        # gold Lissajous coil = the sheep's chord signature (v3 baa-in-key)
    "FILIGREE_LISSAJOUS_HYBRID",  # filigree core + Lissajous overlay
)

INSTRUCTIONS = (
    "You are Jev, choosing the MASTER HORN SETUP for the Choral Sheep — a singing companion "
    "whose flock are the twelve pitch classes and whose baas are in key. Pick the ONE setup "
    "that best serves: (1) silhouette variants readable at 128px, (2) the baa-in-key mechanic "
    "(ornament = the note made visible), (3) the established gold filigree family and the "
    "approved material path (no new material masters), (4) UE export cleanliness."
)

CRITERIA: dict[str, Any] = {
    "FILIGREE_HERITAGE": (
        "Right when visual unity with the existing gold family (collar, tail scroll, star) "
        "matters most. Proven in-repo builder (melodia_gn filigree_spiral), lightest poly cost, "
        "cleanest export. Weakest tie to the baa-in-key audio mechanic."),
    "ANATOMICAL_KERATIN": (
        "Right when creature-credibility and realism outrank the musical identity. Heaviest "
        "geometry, and requires a new keratin material path — conflicts with the no-new-master "
        "guard on the approved coat family."),
    "LISSAJOUS_CHORD": (
        "Right when the baa-in-key mechanic is the star: each sheep's horn IS its chord "
        "signature (A:B:Delta ratios), animated by the wool_amp lane, rendered in the existing "
        "gold. Ties ornament to audio; needs the (already live) Lissajous math."),
    "FILIGREE_LISSAJOUS_HYBRID": (
        "Right when maximum adornment is wanted and poly budget is not a concern. Richest "
        "silhouette, heaviest build, two systems stacked on one head."),
}

HORN_STATE: dict[str, Any] = {
    "gold_family_present": True,     # collar + tail scroll + star already filigree gold
    "wool_amp_lane_live": True,      # pc_tint / wool_amp attributes authored (S5)
    "baa_wavs_present": True,        # 12 sheep_baa_PC*.wav in Content/Melodia/Companions/ChoralSheep/Audio
    "lissajous_driver_live": True,   # MEL_S5_lissajous + Align Curve to Surface wired
    "mp3_reactive_lane_live": True,  # SheepMusicBeads dancing to baked audio energy
    "ue_export_is_target": True,     # SK_ChoralSheep contract; use_armature_deform_only
    "poly_budget_conscious": True,   # companion, not hero gown
    "no_new_material_master": True,  # Board 06 guard
}

WEIGHTS: dict[str, dict[str, float]] = {
    "FILIGREE_HERITAGE": {
        "gold_family_present": 0.9, "poly_budget_conscious": 0.6,
        "ue_export_is_target": 0.4, "wool_amp_lane_live": -0.2},
    "ANATOMICAL_KERATIN": {
        "ue_export_is_target": 0.5, "gold_family_present": -0.8,
        "no_new_material_master": -0.9, "poly_budget_conscious": -0.5},
    "LISSAJOUS_CHORD": {
        "wool_amp_lane_live": 0.9, "baa_wavs_present": 0.9,
        "mp3_reactive_lane_live": 0.5, "lissajous_driver_live": 0.6,
        "ue_export_is_target": 0.4, "poly_budget_conscious": -0.3},
    "FILIGREE_LISSAJOUS_HYBRID": {
        "gold_family_present": 0.5, "wool_amp_lane_live": 0.4,
        "mp3_reactive_lane_live": 0.3, "poly_budget_conscious": -0.6},
}


def _softmax(scores: dict[str, float], temp: float = 0.4) -> dict[str, float]:
    mx = max(scores.values())
    exps = {k: math.exp((v - mx) / temp) for k, v in scores.items()}
    tot = sum(exps.values())
    return {k: v / tot for k, v in exps.items()}


def _fallback_scores() -> dict[str, float]:
    out = {}
    for opt in HORN_OPTIONS:
        s = 0.0
        for fact, present in HORN_STATE.items():
            if present and fact in WEIGHTS[opt]:
                s += WEIGHTS[opt][fact]
        out[opt] = s
    return out


def _horn_ask(timeout: float = 20.0) -> Optional[dict]:
    """One system_one Choice over HORN_OPTIONS. None when unavailable."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        return None
    try:
        from typesafe_sdk import Choice, TypeSafeClient
    except Exception:
        return None
    try:
        with TypeSafeClient() as client:
            resp = client.system_one(
                state=HORN_STATE,
                questions={"horn_master_setup": Choice(
                    instructions=INSTRUCTIONS, criteria=CRITERIA)},
            )
        a = resp.choices["horn_master_setup"]
        choice = str(a.choice)
        if choice not in HORN_OPTIONS:
            return None  # refuse unauthored output
        probs = dict(a.probabilities or {})
        probs = {k: float(probs.get(k, 0.0)) for k in HORN_OPTIONS}
        tot = sum(probs.values()) or 1.0
        probs = {k: v / tot for k, v in probs.items()}
        return {"choice": choice, "probabilities": probs,
                "confidence": float(a.confidence or 0.0), "source": "jev-live",
                "reason": "jev system_one Choice, full distribution preserved"}
    except Exception as exc:
        return {"choice": None, "source": "classical-fallback",
                "reason": f"jev transport failure ({type(exc).__name__}); fallback held",
                "probabilities": {}, "confidence": 0.0}


def decide() -> dict:
    live = _horn_ask()
    if live is not None:
        return {
            "marker": "HORN-MASTER-DECIDED",
            "source": live["source"],
            "reason": live["reason"],
            "choice": live["choice"],
            "confidence": live["confidence"],
            "probabilities": live["probabilities"],
            "options": list(HORN_OPTIONS),
            "state": HORN_STATE,
        }
    scores = _fallback_scores()
    dist = _softmax(scores)
    top = max(dist, key=dist.get)
    ranked = sorted(dist.items(), key=lambda kv: -kv[1])
    return {
        "marker": "HORN-MASTER-DECIDED",
        "source": "classical-fallback",
        "reason": ("no TYPESAFE_API_KEY in environment; deterministic criteria-weighted "
                   "fallback ranked the authored options. Set the hermeskey as "
                   "TYPESAFE_API_KEY and rerun for jev-live provenance."),
        "choice": top,
        "confidence": round(dist[top], 4),
        "probabilities": {k: round(v, 4) for k, v in dist.items()},
        "scores_raw": {k: round(v, 3) for k, v in scores.items()},
        "ranked": [k for k, _ in ranked],
        "options": list(HORN_OPTIONS),
        "state": HORN_STATE,
    }


if __name__ == "__main__":
    result = decide()
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "horn_master_report.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print("HORN-MASTER::" + json.dumps({
        "source": result["source"], "choice": result["choice"],
        "probabilities": result["probabilities"], "reason": result["reason"]})[:800])
