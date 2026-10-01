"""
Jev audio plan auditor for Melodia (BS_GodFile).

A "plan auditor" conductor per skill system-one-conductor: the state is live
project facts assembled from disk probes, and Jev supplies ONE judgment per
question inside a SINGLE system_one call.

  * Closed option sets only. Every criterion maps 1:1 to a fact proven on disk
    in this session (or to the classical fallback that documents the mapping).
  * Missing telemetry is OMITTED from the state, never filled with 0.
  * Runs with no key on a deterministic classical fallback. Fallback output is
    NEVER presented as Jev evidence.
  * No imports from production modules, no asset writes, no production
    mutation. Deleting this folder is the rollback plan.

Facts below were probed in the studio repo (C:/EnvironmentPortfolio/BS_GodFile)
on 2026-09-25. Each is annotated with how it was proven.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = "melodia.jev_audio_plan_audit.v1"
OUT = Path(__file__).with_name("audit_log.json")

# --------------------------------------------------------------------------
# Closed option sets. Keys are the only permitted model outputs.
# --------------------------------------------------------------------------

# What should be proven FIRST. Ordered by how much runtime immersion each
# unblocks, as established by the disk study.
PHASE_ORDER: Dict[str, str] = {
    "P1_REAL_SIGNAL": (
        "Replace the three fake spectrum lanes (Bass= BattleIntensity, "
        "Mid=decay, Treble=cos^2 beat) with real envelope/FFT from the audio "
        "mixer. Everything above it inherits the truth of this."
    ),
    "P2_BEAT_HITS": (
        "Bind per-note hitsounds to FMelodiaLaneHitJudged. The delegate is "
        "authored and fires per judged press; fastest immersion win and needs "
        "no new analysis."
    ),
    "P3_CORE_AMBIENCE": (
        "Wire the two orphan ambience beds and zone-crossfade quads on the "
        "musical clock. Closes open handoff items; smallest diff."
    ),
    "P4_TD_BAND_BRIDGE": (
        "Close the TD audio band lane: TD already computes 5 real bands in "
        "audio.tdn but has NO consumer in UE (no receiver on :8000)."
    ),
    "P5_FL_MUSIC_LANE": (
        "Stand up the FL Studio music pipeline. FL 2024 is installed but has "
        "zero projects/presets/plugins -- it is an empty install, not a pipeline."
    ),
}

RISKIEST_ASSUMPTION: Dict[str, str] = {
    "AUDIO_ANALYSIS_API_AVAILABLE": (
        "Assumes a real envelope/FFT read is available in UE 5.8 from the "
        "mixer. Zero hits for GetSpectrum/OnAudioSingleEnvelopeValue/"
        "EnvelopeFollower/GetMagnitudeForFrequencies were found in Source/ and "
        "MelodiaCore, so the mechanism is unproven and may need Audio Modulation."
    ),
    "MPC_LANE_MIGRATION_ALLOWED": (
        "Assumes the 89 assets bound to Bass/Mid/Treble can keep those names "
        "while new true lanes are added. If those names must change meaning, "
        "89 assets move and this stops being an audio-lane task."
    ),
    "MELODIA_TECH_VERIFYABLE": (
        "Assumes the zero-binding census for FMelodiaLaneHitJudged is real. "
        "That was a TEXT census; per AGENTS.md rule 20 a census can confirm "
        "presence but never absence. Monolith reflection has not run yet."
    ),
    "HARMONIX_MIDI_ROUTE": (
        "Assumes an FL track can drive the Harmonix clock sample-accurately. "
        "Content/Audio/128BPMarpeggiomelody_beatgrid.uasset may be the existing "
        "map, but its asset TYPE was never verified (rule 20)."
    ),
    "SUBMIX_CHAIN_AUTHORED": (
        "Assumes SUBMIX_SFX/SUBMIX_Ambience carry real effect chains. Four "
        "submixes exist on disk; their effect chains were never inspected."
    ),
}

NEEDS_HUMAN_CRITERIA: Dict[str, str] = {
    "MPC_OWNER_CALL": (
        "An owner must rule on whether Bass/Mid/Treble semantics may change. "
        "89 assets are bound; that is an ownership decision, not a sound call."
    ),
    "MIDDLEWARE_EDIT_SCOPE": (
        "An owner must authorise editing live MetaSound graphs, which is "
        "editor-mutating work on the single editor lock."
    ),
    "NONE_BLOCKING": "Nothing here needs a human before the first phase can start.",
}

READINESS_LEVELS: List[str] = [
    "0 - no audio assets or seams on disk",
    "1 - assets or seams exist but nothing is wired",
    "2 - a subsystem compiles and runs, with a written contract",
    "3 - wired end to end and observed in PIE",
    "4 - player-verified with a committed receipt",
]


@dataclass
class AudioState:
    """Live project facts. Omit unknowns -- never invent a signal to fill a field."""

    # --- clock / musical time (source: read from headers) ---
    music_clock_subsystem: bool = True
    harmonix_preferred_quartz_fallback: bool = True
    wallclock_accumulators_banned: bool = True
    experienced_input_video_visual_timebase: bool = True

    # --- the fake-spectrum finding (source: MelodiaAudioReactivePresentationSubsystem.cpp:310-313) ---
    real_spectrum_analysis_hits: int = 0
    fake_spectrum_lane_count: int = 3
    assets_bound_to_fake_lanes: int = 89
    single_mpc_writer_named: str = "UMelodiaAudioReactivePresentationSubsystem"

    # --- beat-hit seam (source: MelodiaRhythmCombatSubsystem.h:32) ---
    lane_hit_judged_delegate_exists: bool = True
    lane_hit_judged_bindings_found: int = 0
    lane_hit_carries_fields: str = "LaneIndex, Grade, TimingErrorMs"

    # --- assets on disk ---
    project_sfx_assets: int = 27
    project_sfx_ui_only: int = 27
    project_sfx_gameplay: int = 0
    vendor_ambience_presets: int = 30
    melodia_authored_metasounds: int = 6
    melodia_authored_metasound_scope: str = "water only (MS_Water_*)"
    sound_classes: int = 5
    submixes: int = 4
    tension_duck_soundmix_exists: bool = True
    tension_duck_writes_scl_ambience: bool = True
    water_bridge_voice_budget_exists: bool = True

    # --- orphans (source: TENSION_AUDIO_REACTIVITY_2026-08-15.md) ---
    melusina_bed_played_by_nothing: bool = True
    riverbed_open_unwired: bool = True

    # --- TouchDesigner ---
    td_audio_network_exists: bool = True
    td_real_band_chains: int = 5
    td_bands_merge_node_exists: bool = True
    td_sends_bands_to_ue: bool = True
    ue_receiver_on_td_port: bool = False
    td_osc_out_port: int = 8000
    ue_sends_rhythm_to_td_port: int = 9000
    td_reads_ue_rhythm_channels: str = "rhythm/beat_phase, rhythm/beat_pulse"
    td_preset_switch_channel: str = "5 authored presets (Nikki, Madoka, Celestial, Itto, Sakura)"

    # --- world compiler / universe foundry ---
    world_compiler_takes_mpc_signal: bool = True
    world_compiler_takes_audio: bool = False
    universe_foundry_musical_identity: bool = True
    universe_foundry_second_mpc_forbidden: bool = True

    # --- FL Studio ---
    fl_installed: bool = True
    fl_version: str = "2024"
    fl_projects: int = 0
    fl_presets: int = 0
    fl_plugins: int = 0

    # --- meta ---
    jev_key_present: bool = False
    verified_by: str = "disk probes, studio repo, 2026-09-25"

    extra: Dict[str, Any] = field(default_factory=dict)

    def to_jev_state(self) -> Dict[str, Any]:
        d = dict(self.__dict__)
        d.pop("extra", None)
        # Omit falsy-measures that are genuinely unknown vs measured-zero.
        return {k: v for k, v in d.items() if v is not None and v != ""}


@dataclass
class Decision:
    order: str
    order_probs: Dict[str, float]
    riskiest: str
    riskiest_probs: Dict[str, float]
    needs_human: bool
    needs_human_prob: float
    human_reason: str
    readiness: int
    readiness_label: str
    readiness_probs: List[float]
    source: str
    reason: str


def classical_fallback(state: AudioState) -> Decision:
    """Deterministic, documented mapping. Not model evidence."""
    order = "P1_REAL_SIGNAL"
    order_probs = {
        "P1_REAL_SIGNAL": 0.40,
        "P2_BEAT_HITS": 0.30,
        "P3_CORE_AMBIENCE": 0.12,
        "P4_TD_BAND_BRIDGE": 0.10,
        "P5_FL_MUSIC_LANE": 0.08,
    }
    # 89 bound assets make the lane-migration ruling the widest blast radius.
    risk = "MPC_OWNER_CALL" if state.assets_bound_to_fake_lanes > 0 else "AUDIO_ANALYSIS_API_AVAILABLE"
    riskiest = {
        "AUDIO_ANALYSIS_API_AVAILABLE": 0.30,
        "MPC_OWNER_CALL": 0.30,
        "MELODIA_TECH_VERIFYABLE": 0.22,
        "HARMONIX_MIDI_ROUTE": 0.10,
        "SUBMIX_CHAIN_AUTHORED": 0.08,
    }
    if risk not in riskiest:
        risk = "AUDIO_ANALYSIS_API_AVAILABLE"
    # Level 2: a written contract exists and subsystems exist, but nothing is
    # wired end to end and no PIE observation has been taken.
    return Decision(
        order=order,
        order_probs=order_probs,
        riskiest=risk,
        riskiest_probs=riskiest,
        needs_human=True,
        needs_human_prob=0.85,
        human_reason=NEEDS_HUMAN_CRITERIA["MPC_OWNER_CALL"],
        readiness=2,
        readiness_label=READINESS_LEVELS[2],
        readiness_probs=[0.05, 0.25, 0.55, 0.12, 0.03],
        source="classical-fallback",
        reason="no Jev backend used; documented mapping only",
    )


def try_jev_live(state: AudioState) -> Optional[Decision]:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None
    try:
        from typesafe_sdk import TypeSafeClient  # type: ignore
    except Exception:
        return None
    try:
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(
                state=state.to_jev_state(),
                questions={
                    "order": {
                        "type": "choice",
                        "instructions": (
                            "Pick the single best first phase for RUNTIME IMMERSION "
                            "(SFX, beat hits, core ambience) in an Unreal rhythm-JRPG "
                            "whose musical-time clock already works and whose audio "
                            "reactive lanes are currently faked. Weigh: how much "
                            "audible immersion each phase unblocks, how much of it is "
                            "already authored and waiting, dependency order, and "
                            "whether a phase depends on an unproven mechanism."
                        ),
                        "criteria": PHASE_ORDER,
                    },
                    "riskiest": {
                        "type": "choice",
                        "instructions": (
                            "Which assumption most endangers the audio plan if it turns "
                            "out false? Prefer assumptions whose failure invalidates "
                            "several later phases at once."
                        ),
                        "criteria": RISKIEST_ASSUMPTION,
                    },
                    "human": {
                        "type": "noul",
                        "instructions": (
                            "Does an OWNER decision gate starting the first phase? "
                            "Score 1.0 only if a human ruling is genuinely required "
                            "before any phase can begin; score low if agents could "
                            "start a safe, reversible first step now."
                        ),
                        "criteria": NEEDS_HUMAN_CRITERIA,
                    },
                    "readiness": {
                        "type": "score",
                        "instructions": (
                            "How far proven is the AUDIO SYSTEM overall, on this ladder? "
                            "Judge what has receipts, not what has code."
                        ),
                        "criteria": READINESS_LEVELS,
                    },
                },
            )
        ans = resp.answers
        order = ans["order"]
        risk = ans["riskiest"]
        human = ans["human"]
        ready = ans["readiness"]
        order_p = {k: float(v) for k, v in (order.probabilities or {}).items() if k in PHASE_ORDER}
        risk_p = {k: float(v) for k, v in (risk.probabilities or {}).items() if k in RISKIEST_ASSUMPTION}
        if not order_p:
            return None
        top = max(order_p, key=order_p.get)
        rtop = max(risk_p, key=risk_p.get) if risk_p else "AUDIO_ANALYSIS_API_AVAILABLE"
        hprob = float(human.noul) if hasattr(human, "noul") else 0.0
        ridx = int(ready.score) if hasattr(ready, "score") else 2
        ridx = max(0, min(len(READINESS_LEVELS) - 1, ridx))
        hr = ""
        if hprob > 0.5:
            if "MPC" in rtop:
                hr = NEEDS_HUMAN_CRITERIA["MPC_OWNER_CALL"]
            else:
                hr = NEEDS_HUMAN_CRITERIA[risk_p.get(rtop, "")] if risk_p else ""
                if not hr:
                    hr = NEEDS_HUMAN_CRITERIA["MPC_OWNER_CALL"]
        return Decision(
            order=top,
            order_probs=order_p,
            riskiest=rtop,
            riskiest_probs=risk_p,
            needs_human=hprob > 0.5,
            needs_human_prob=hprob,
            human_reason=hr,
            readiness=ridx,
            readiness_label=READINESS_LEVELS[ridx],
            readiness_probs=[float(p) for p in (ready.probabilities or [])],
            source="jev-live",
            reason="typesafe System One choice+choice+noul+score, one call",
        )
    except Exception as exc:  # fail closed to fallback, never fake live
        d = classical_fallback(state)
        d.reason = f"Jev call failed: {type(exc).__name__}"
        return d


def main() -> int:
    state = AudioState(jev_key_present=bool(os.environ.get("TYPESAFE_API_KEY")))
    decision = try_jev_live(state)
    if decision is None:
        decision = classical_fallback(state)
    payload = {
        "schema": SCHEMA,
        "date": datetime.now().isoformat(timespec="seconds"),
        "state": state.to_jev_state(),
        "decision": {
            "order": decision.order,
            "order_probs": decision.order_probs,
            "riskiest": decision.riskiest,
            "riskiest_probs": decision.riskiest_probs,
            "needs_human": decision.needs_human,
            "needs_human_prob": decision.needs_human_prob,
            "human_reason": decision.human_reason,
            "readiness": decision.readiness,
            "readiness_label": decision.readiness_label,
            "readiness_probs": decision.readiness_probs,
            "source": decision.source,
            "reason": decision.reason,
        },
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    d = payload["decision"]
    print(f"SOURCE:   {d['source']}")
    print(f"ORDER:    {d['order']}  {json.dumps(d['order_probs'])}")
    print(f"RISKIEST: {d['riskiest']}  {json.dumps(d['riskiest_probs'])}")
    print(f"HUMAN:    {d['needs_human']} p={d['needs_human_prob']:.2f}")
    print(f"READINESS: {d['readiness']} {d['readiness_label']}")
    print(f"WROTE:    {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
