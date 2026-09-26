"""
Jev orchestration auditor for the Melodia audio/world-field convergence.

Plan-auditor conductor per skill system-one-conductor: state = live project
facts assembled from disk probes, Jev supplies ONE judgment per question in a
single system_one call. Closed option sets only; classical fallback when no
key; fallback output is never presented as Jev evidence.

State supersedes Prototypes/JevAudioPlanAudit facts: that audit read the FROZEN
archive C:/EnvironmentPortfolio/_TouchDesigner. This one reads the canonical
C:/MelodiaTouchDesigner (PORTS.md SSOT) plus BS_GodFile probes, all 2026-09-25.

Deleting this folder is the rollback plan. No production mutation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = "melodia.jev_orchestration_audit.v1"
OUT = Path(__file__).with_name("orchestration_audit_log.json")

# ---------------------------------------------------------------------------
# Closed option sets — each maps 1:1 to a fact proven on disk 2026-09-25.
# ---------------------------------------------------------------------------

FIRST_MOVE: Dict[str, str] = {
    "O1_PORT_VOCAB_RECONCILE": (
        "Reconcile the live port drift and author ONE signal-vocabulary map: "
        "UE phrase bus moved :9000->:9002 on 09-25 (PIE-proven 7/7 fields), "
        "TD docs/PORTS.md still canonises :9000 for that direction, and "
        "osc_routing.json (09-02) predates the move. Three SSOTs disagree; "
        "UDP mis-binds drop packets silently. Docs + one small TD-side "
        "re-wire only; no UE C++, no editor needed. Everything later inherits "
        "a single honest routing table."
    ),
    "O2_BEAT_HITS": (
        "Bind per-note hitsounds to FMelodiaLaneHitJudged (the old P2). "
        "Highest player-facing immersion, but it is INSIDE UE only — it does "
        "not orchestrate TD/Foundry/Compiler at all."
    ),
    "O3_PHASE_F_RECEIVER": (
        "Close Universe Foundry Phase F: a NATIVE UE consumer for TD's live "
        "signals — the :9000 out_ue preset lane (12 schema'd signals) and the "
        "Spout TD_Faraway_WorldField 128x128 emotional field — with an "
        "alignment canary proof. TD already broadcasts (Phase E done "
        "09-23, 6-state replay PASS); UE has no ear. Needs a closed-editor "
        "C++ build and an editor window."
    ),
    "O4_CORE_AMBIENCE": (
        "Wire the two orphan ambience beds + zone crossfade on the music "
        "clock (old P3). MetaSound-side, UE-internal, no cross-repo coupling."
    ),
    "O5_FL_LIVE_RUN": (
        "Run the scripted FL/Voicemeeter live audio-in (wire_fl_audio_in.py, "
        "48kHz three-way lock) and commit the snapshot. Feeds TD's real FFT "
        "with actual music; prerequisite for TD analysis to mean anything in "
        "a show."
    ),
}

RISKIEST_ASSUMPTION: Dict[str, str] = {
    "A_9000_COLLISION_RESOLVED": (
        "Assumes the :9000 collision that forced the phrase bus to move is "
        "understood and that the out_ue preset lane can keep :9000 without "
        "re-colliding. CURRENT_STATE says :9000 'collided' but the second "
        "binder was never identified; a native UE listener could re-create "
        "the exact fault."
    ),
    "A_ZERO_BINDING_CENSUS_REAL": (
        "Assumes the 'no native UE listener on :9000' finding is real "
        "absence. It came from git grep over Source/ + Plugins/. AGENTS.md "
        "rule 20: text censuses confirm presence, never absence; Blueprint "
        "or plugin-side listeners were not reflected."
    ),
    "A_SPOUT_NATIVE_FEASIBLE": (
        "Assumes UE 5.8 can ingest TD_Faraway_WorldField zero-copy. The repo "
        "has no Spout plugin in Source/ or Plugins/ (only a python health-"
        "check stub in Content/Python/td_bridge.py); an OSC mirror of the "
        "field may be the simpler truth."
    ),
    "A_FAKE_LANES_TOLERATED": (
        "Assumes real TD bands can be ADDED as new named lanes without "
        "touching Bass/Mid/Treble (89 bound assets). If consumers actually "
        "need true spectral meaning under the old names, 89 assets move and "
        "every downstream phase changes shape."
    ),
    "A_FOUNDRY_EVIDENCE_SUFFICIENT": (
        "Assumes Phase F done via the alignment canary is accepted by the "
        "Foundry's own evidence rules (Echo ledger row, no self-"
        "certification). Cheap mis-scope here makes the phase fake-done "
        "like the 08-10 'runtime certified' incident."
    ),
}

NEEDS_HUMAN_CRITERIA: Dict[str, str] = {
    "EDITOR_WINDOW": (
        "O3 needs a closed-editor full build (AGENTS.md rules 15/21) — an "
        "owner schedules the editor down-time; agents cannot take it."
    ),
    "MPC_OWNER_CALL": (
        "Changing Bass/Mid/Treble semantics is an ownership ruling over 89 "
        "assets, not an audio call."
    ),
    "NONE_BLOCKING": (
        "O1/O2/O4/O5 can start agent-side now; editor work can be deferred "
        "to its own window."
    ),
}

READINESS_LEVELS: List[str] = [
    "0 - no signals or seams on disk",
    "1 - seams exist on one side only (TD broadcasts or UE authors, not both)",
    "2 - contracts written on BOTH sides with a known live port table",
    "3 - one live cross-repo signal observed end to end in PIE with receipt",
    "4 - orchestrated: compiler/field/beat all reading one vocabulary, player-verified",
]


@dataclass
class OrchestrationState:
    """Live facts, canonical repos, probed 2026-09-25. Unknowns are omitted."""

    # --- UE side ---
    music_clock_single_authority: bool = True
    fake_spectrum_lanes: int = 3
    assets_bound_to_fake_lanes: int = 89
    phrase_bus_ue_listener_port: int = 9002
    phrase_bus_ingest_proven_pie: bool = True          # 09-24, 7/7 fields
    native_ue_listener_on_9000_td_lane: bool = False   # git grep census only
    lane_hit_judged_bindings_found: int = 0
    ue_spout_plugin_present: bool = False              # none in Source//Plugins/

    # --- TD side (canonical C:/MelodiaTouchDesigner) ---
    td_real_band_chains: int = 5
    td_conductor_bus_channels: int = 22
    td_out_ue_port: int = 9000                         # oscoutCHOP, 12 preset signals
    td_out_blender_port: int = 9001
    td_phase_e_world_field_done: bool = True           # 09-23, 6-state replay PASS
    td_world_field_spout_sender: str = "TD_Faraway_WorldField 128x128"
    td_ports_md_forbids_8000: bool = True
    fl_live_routing: str = "Voicemeeter scripted, awaiting live run"

    # --- cross-repo truth drift ---
    ports_md_still_canonises_9000_for_phrase: bool = True
    osc_routing_json_dated: str = "2026-09-02"
    osc_routing_predates_port_move: bool = True

    # --- Foundry / compiler ---
    foundry_phase_F_open: bool = True                  # UE receiver/canary
    foundry_phases_A_to_E_done: bool = True
    world_compiler_signal_stage: str = "contract check only, no audio"
    world_compiler_live_proven_scope: bool = True      # L_MelusinaMorning 09-19

    jev_key_present: bool = False
    verified_by: str = "canonical-repo probes, studio, 2026-09-25"

    extra: Dict[str, Any] = field(default_factory=dict)

    def to_jev_state(self) -> Dict[str, Any]:
        d = dict(self.__dict__)
        d.pop("extra", None)
        return {k: v for k, v in d.items() if v is not None and v != ""}


@dataclass
class Decision:
    first: str
    first_probs: Dict[str, float]
    riskiest: str
    riskiest_probs: Dict[str, float]
    needs_human: bool
    needs_human_prob: float
    human_reason: str
    readiness: int
    readiness_label: str
    source: str
    reason: str


def classical_fallback(state: OrchestrationState) -> Decision:
    """Deterministic documented mapping. NOT model evidence."""
    return Decision(
        first="O1_PORT_VOCAB_RECONCILE",
        first_probs={
            "O1_PORT_VOCAB_RECONCILE": 0.42,
            "O3_PHASE_F_RECEIVER": 0.24,
            "O2_BEAT_HITS": 0.14,
            "O5_FL_LIVE_RUN": 0.12,
            "O4_CORE_AMBIENCE": 0.08,
        },
        riskiest="A_9000_COLLISION_RESOLVED",
        riskiest_probs={
            "A_9000_COLLISION_RESOLVED": 0.34,
            "A_ZERO_BINDING_CENSUS_REAL": 0.22,
            "A_SPOUT_NATIVE_FEASIBLE": 0.18,
            "A_FAKE_LANES_TOLERATED": 0.16,
            "A_FOUNDRY_EVIDENCE_SUFFICIENT": 0.10,
        },
        needs_human=False,
        needs_human_prob=0.30,
        human_reason="",
        readiness=1,
        readiness_label=READINESS_LEVELS[1],
        source="classical-fallback",
        reason="no Jev backend used; documented mapping only",
    )


def try_jev_live(state: OrchestrationState) -> Optional[Decision]:
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
                    "first": {
                        "type": "choice",
                        "instructions": (
                            "The owner wants the audio/TD/Universe-Foundry/"
                            "World-Compiler systems PROPERLY ORCHESTRATED — one "
                            "converged signal economy, no parallel authorities. "
                            "Pick the single first move that best unlocks "
                            "orchestration itself (not the largest isolated "
                            "immersion win). Weigh: what each later move depends "
                            "on, silent-failure risk while routing is disputed, "
                            "editor/build windows needed, and what is already "
                            "broadcast into the void today."
                        ),
                        "criteria": FIRST_MOVE,
                    },
                    "riskiest": {
                        "type": "choice",
                        "instructions": (
                            "Which assumption most endangers the convergence "
                            "plan if false — prefer a false that invalidates "
                            "several later moves at once."
                        ),
                        "criteria": RISKIEST_ASSUMPTION,
                    },
                    "human": {
                        "type": "noul",
                        "instructions": (
                            "Does an OWNER ruling gate STARTING the chosen "
                            "first move? Score high only if the first move "
                            "itself cannot proceed without a human; low if it "
                            "is docs/agent-side now with editor windows "
                            "deferrable."
                        ),
                        "criteria": NEEDS_HUMAN_CRITERIA,
                    },
                    "readiness": {
                        "type": "score",
                        "instructions": (
                            "How far proven is the CROSS-REPO ORCHESTRATION "
                            "(TD signals reaching UE consumers as one "
                            "vocabulary) on this ladder? Judge receipts, not "
                            "code."
                        ),
                        "criteria": READINESS_LEVELS,
                    },
                },
            )
        ans = resp.answers
        first = ans["first"]
        risk = ans["riskiest"]
        human = ans["human"]
        ready = ans["readiness"]
        fp = {k: float(v) for k, v in (first.probabilities or {}).items() if k in FIRST_MOVE}
        rp = {k: float(v) for k, v in (risk.probabilities or {}).items() if k in RISKIEST_ASSUMPTION}
        if not fp:
            return None
        top = max(fp, key=fp.get)
        rtop = max(rp, key=rp.get) if rp else "A_9000_COLLISION_RESOLVED"
        hprob = float(human.noul) if hasattr(human, "noul") else 0.0
        ridx = int(ready.score) if hasattr(ready, "score") else 1
        ridx = max(0, min(len(READINESS_LEVELS) - 1, ridx))
        hr = ""
        if hprob > 0.5:
            hr = NEEDS_HUMAN_CRITERIA["EDITOR_WINDOW"] if top == "O3_PHASE_F_RECEIVER" else NEEDS_HUMAN_CRITERIA["MPC_OWNER_CALL"]
        return Decision(
            first=top,
            first_probs=fp,
            riskiest=rtop,
            riskiest_probs=rp,
            needs_human=hprob > 0.5,
            needs_human_prob=hprob,
            human_reason=hr,
            readiness=ridx,
            readiness_label=READINESS_LEVELS[ridx],
            source="jev-live",
            reason="typesafe System One choice+choice+noul+score, one call",
        )
    except Exception as exc:  # fail closed, label it
        d = classical_fallback(state)
        return Decision(
            first=d.first, first_probs=d.first_probs, riskiest=d.riskiest,
            riskiest_probs=d.riskiest_probs, needs_human=d.needs_human,
            needs_human_prob=d.needs_human_prob,
            human_reason=f"Jev call failed: {exc!r}", readiness=d.readiness,
            readiness_label=d.readiness_label, source="classical-fallback",
            reason="Jev call failed; fallback mapping used",
        )


def main() -> int:
    state = OrchestrationState(jev_key_present=bool(os.environ.get("TYPESAFE_API_KEY")))
    decision = try_jev_live(state) or classical_fallback(state)
    log = {
        "schema": SCHEMA,
        "date": datetime.now().isoformat(timespec="seconds"),
        "state": state.to_jev_state(),
        "decision": decision.__dict__,
    }
    OUT.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps({"source": decision.source, "first": decision.first,
                      "first_probs": decision.first_probs,
                      "riskiest": decision.riskiest,
                      "riskiest_probs": decision.riskiest_probs,
                      "needs_human": decision.needs_human,
                      "needs_human_prob": decision.needs_human_prob,
                      "readiness": decision.readiness_label,
                      "reason": decision.reason}, indent=2))
    print(f"\nlog -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
