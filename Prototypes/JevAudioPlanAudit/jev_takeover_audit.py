"""
Jev takeover audit for the Melodia audio lane (2026-09-25 evening).

Third Jev conductor run in this lane, after Prototypes/JevAudioPlanAudit/.
State is rebuilt from LIVE disk + editor probes, including the facts that
changed since the first audit:

  * The editor was rebuilt around the audio component. UBT PASS. The C++ seam
    is NOT the open question any more.
  * The MetaSound authoring route is EXHAUSTED through the Python builder:
    60+ probe attempts resolved only ("UE","Wave Player","Mono") and
    ("UE","Envelope Follower",""). Every synth block FAILED across the
    UE / Synthesis / Modulation namespaces, with and without the
    (Monaural)/(Mono) variants, using the real `variant` field. The
    Metasound / Synthesis / AudioModulation / AudioSynesthesia plugins are all
    enabled (372 total), so this is the builder's resolution path -- not
    spelling, not a disabled plugin, not guessable.
  * A second session (Claude) owns the character/UI lanes and is mid-task; the
    owner has handed the whole repo to this session.

Plan-auditor shape: state = facts, questions = closed authored option sets,
one system_one call, deterministic classical fallback, provenance labelled.

Nothing here writes assets or mutates production.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

SCHEMA = "melodia.jev_audio_takeover_audit.v1"
OUT = Path("C:/EnvironmentPortfolio/BS_GodFile/Prototypes/JevAudioPlanAudit/takeover_audit_log.json")

# --------------------------------------------------------------------------
# Closed option sets. Keys are the only permitted model outputs.
# --------------------------------------------------------------------------

HIT_GRAPH_ROUTE: Dict[str, str] = {
    "GUI_HAND_AUTHOR": (
        "Author MS_Melodia_RhythmHit in the MetaSound editor GUI with the owner "
        "driving. Zero automation risk, unblocked tonight, but needs a human at "
        "the keyboard and does not scale past this one graph."
    ),
    "CPLUSPLUS_REGISTRY_DUMP": (
        "Add a small C++ commandlet/helper to enumerate the real MetaSound node "
        "class list, then script the graph. Highest confidence and reusable for "
        "every future graph, but a header change plus a full build, so it is "
        "blocked behind the same closed-editor window as the rebuild."
    ),
    "SAMPLE_VIA_PROVEN_BLOCKS": (
        "Playable tonight with zero unknowns: author one short hit sample, feed it "
        "through the two blocks that provably resolve (Wave Player + Envelope "
        "Follower), and let the component's grade/lane parameters drive pitch and "
        "envelope. Trades the pure-synth design for a sample dependency."
    ),
    "DEFER_P2_CONTENT": (
        "Keep the compiled C++ seam as P2's deliverable and move the whole audio "
        "lane's energy to P3 ambience, which needs no new authoring route."
    ),
}

FIRST_MOVE: Dict[str, str] = {
    "CLOSED_EDITOR_REBUILD": (
        "Take a closed-editor window now: rebuild the single-slot component plus "
        "the HandleVoiceFinished declaration, so P2's C++ is fully green."
    ),
    "P3_AMBIENCE_WIRING": (
        "Wire the two orphan ambience beds and the SCL_Ambience-safe zone crossfade, "
        "which needs no new authoring API and lands audible immersion immediately."
    ),
    "P1_REAL_SIGNAL": (
        "Add true envelope/FFT lanes beside the faked Bass/Mid/Treble, without "
        "overwriting the 89 bound assets."
    ),
    "OVERWORLD_HUD_FINISH": (
        "Finish the second session's overworld HUD: its widget is built and its 14 "
        "icons imported, but PIE verification is incomplete."
    ),
    "G7_REIMPORT_DEBUG": (
        "Solve the character reimport blocker: the reimported body gets no anim "
        "instance (T-pose). This unblocks her eyes, blinks and body fixes in UE."
    ),
}

RISKIEST: Dict[str, str] = {
    "METASOUND_AUTHORING_ROUTE": (
        "The synth-graph authoring route is unsolved. If it stays unsolved, the "
        "designed one-parameter hit layer cannot exist and P2 content is stuck."
    ),
    "SCL_AMBIENCE_TWO_WRITERS": (
        "The reactivity subsystem already ducks SCL_Ambience. Ambience zone "
        "crossfade that also writes SCL_Ambience volume would silently overwrite "
        "it -- two writers on one bus."
    ),
    "FAKE_SPECTRUM_LANES": (
        "Bass/Mid/Treble carry battle state, a decay and a sine, and 89 assets are "
        "bound to them. Changing their meaning moves 89 assets at once."
    ),
    "EDITOR_SINGLE_WRITER": (
        "Everything editor-bound serialises through one UnrealEditor on :9316. A "
        "second surface or a build while it is open corrupts work."
    ),
    "NONE_BLOCKING": "No assumption in the audio plan endangers more than one phase.",
}

NEEDS_HUMAN_CRITERIA: Dict[str, str] = {
    "GRAPH_GUI_SESSION": (
        "Someone must drive the MetaSound editor GUI if HIT_GRAPH_ROUTE resolves to "
        "GUI_HAND_AUTHOR."
    ),
    "MPC_OWNER_CALL": (
        "An owner must rule on whether Bass/Mid/Treble semantics may change; 89 "
        "assets are bound to those names."
    ),
    "NONE_BLOCKING": "An agent can safely start and reverse the first move alone.",
}

READINESS: List[str] = [
    "0 - no audio seams or assets",
    "1 - seams/assets exist, nothing wired or playable",
    "2 - a subsystem compiles and runs against a written contract",
    "3 - wired end to end and observed in PIE",
    "4 - player-verified with a committed receipt",
]


@dataclass
class TakeoverState:
    # editor / single-writer
    editor_running: bool = True
    editor_pid: int = 1228
    monolith_listeners: int = 1
    pie_level_open: str = "L_MelusinaMorning"
    dirty_content_packages: int = 0
    dirty_map_externals: int = 2

    # P2 C++ seam
    hit_component_compiles: bool = True
    hit_component_linked: bool = True
    first_build_result: str = "Succeeded (5 actions, 39.4s)"
    single_slot_revision_built: bool = False
    revision_blocked_by_livecoding: bool = True
    parameters_set_before_play: bool = True
    binds_on_lane_hit_judged: bool = True

    # MetaSound authoring route (exhausted)
    metasound_blocks_that_resolve: int = 2
    metasound_blocks_probed: int = 60
    synth_blocks_resolving: int = 0
    synthesis_plugin_enabled: bool = True
    enabled_plugins_total: int = 372
    graph_property_protected: bool = True

    # audio assets / lanes
    project_sfx_assets: int = 27
    project_sfx_gameplay: int = 0
    real_spectrum_analysis_hits: int = 0
    fake_spectrum_lane_count: int = 3
    assets_bound_to_fake_lanes: int = 89
    tension_duck_writes_scl_ambience: bool = True
    orphan_ambience_beds: int = 2

    # other lanes
    td_band_bridge_ue_receiver: bool = False
    fl_studio_state: str = "installed, zero projects/presets/plugins"
    g7_reimport_status: str = "BLOCKED twice, reverted, disk byte-identical to backup"
    overworld_hud_status: str = "widget built, 14 icons imported, PIE verify incomplete"

    def to_jev_state(self) -> Dict[str, object]:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != ""}


def classical_fallback(s: TakeoverState) -> dict:
    """Deterministic documented mapping. NOT model evidence."""
    return {
        "hit_graph_route": "GUI_HAND_AUTHOR",
        "hit_graph_probs": {
            "GUI_HAND_AUTHOR": 0.35,
            "CPLUSPLUS_REGISTRY_DUMP": 0.25,
            "SAMPLE_VIA_PROVEN_BLOCKS": 0.30,
            "DEFER_P2_CONTENT": 0.10,
        },
        "first_move": "CLOSED_EDITOR_REBUILD",
        "first_move_probs": {
            "CLOSED_EDITOR_REBUILD": 0.35,
            "P3_AMBIENCE_WIRING": 0.25,
            "P1_REAL_SIGNAL": 0.15,
            "OVERWORLD_HUD_FINISH": 0.15,
            "G7_REIMPORT_DEBUG": 0.10,
        },
        "riskiest": "METASOUND_AUTHORING_ROUTE",
        "riskiest_probs": {
            "METASOUND_AUTHORING_ROUTE": 0.45,
            "SCL_AMBIENCE_TWO_WRITERS": 0.20,
            "FAKE_SPECTRUM_LANES": 0.20,
            "EDITOR_SINGLE_WRITER": 0.13,
            "NONE_BLOCKING": 0.02,
        },
        "needs_human": True,
        "needs_human_prob": 0.7,
        "readiness": 2,
        "readiness_label": READINESS[2],
        "source": "classical-fallback",
        "reason": "no Jev backend used; documented mapping only",
    }


def try_jev_live(s: TakeoverState) -> Optional[dict]:
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
                state=s.to_jev_state(),
                questions={
                    "hit_graph": {
                        "type": "choice",
                        "instructions": (
                            "How should the rhythm-hit MetaSound graph be authored, given the "
                            "Python builder provably cannot resolve ANY synth node (60+ probes, "
                            "0 successes) while the C++ component that consumes it already "
                            "compiles? Optimise for a PLAYABLE, audible hit sound soonest without "
                            "faking evidence."
                        ),
                        "criteria": HIT_GRAPH_ROUTE,
                    },
                    "first_move": {
                        "type": "choice",
                        "instructions": (
                            "Which single move should this session make first, given it now has "
                            "sole authority over the editor and the repo? Weigh audible "
                            "player-facing immersion, blocking dependencies, and safety."
                        ),
                        "criteria": FIRST_MOVE,
                    },
                    "riskiest": {
                        "type": "choice",
                        "instructions": (
                            "Which remaining assumption most endangers the audio lane if false?"
                        ),
                        "criteria": RISKIEST,
                    },
                    "human": {
                        "type": "noul",
                        "instructions": (
                            "Does a human need to be present for the chosen first move to "
                            "proceed? Score high only if the route genuinely cannot be executed "
                            "by an agent alone."
                        ),
                        "criteria": NEEDS_HUMAN_CRITERIA,
                    },
                    "readiness": {
                        "type": "score",
                        "instructions": "How far proven is the AUDIO SYSTEM overall, on this ladder?",
                        "criteria": READINESS,
                    },
                },
            )
        a = resp.answers
        op = {k: float(v) for k, v in (a["hit_graph"].probabilities or {}).items() if k in HIT_GRAPH_ROUTE}
        fp = {k: float(v) for k, v in (a["first_move"].probabilities or {}).items() if k in FIRST_MOVE}
        rp = {k: float(v) for k, v in (a["riskiest"].probabilities or {}).items() if k in RISKIEST}
        if not op or not fp:
            return None
        hprob = float(a["human"].noul) if hasattr(a["human"], "noul") else 0.0
        ridx = int(a["readiness"].score) if hasattr(a["readiness"], "score") else 2
        ridx = max(0, min(len(READINESS) - 1, ridx))
        return {
            "hit_graph_route": max(op, key=op.get),
            "hit_graph_probs": op,
            "first_move": max(fp, key=fp.get),
            "first_move_probs": fp,
            "riskiest": max(rp, key=rp.get) if rp else "METASOUND_AUTHORING_ROUTE",
            "riskiest_probs": rp,
            "needs_human": hprob > 0.5,
            "needs_human_prob": hprob,
            "readiness": ridx,
            "readiness_label": READINESS[ridx],
            "source": "jev-live",
            "reason": "typesafe System One choice+choice+choice+noul+score, one call",
        }
    except Exception as exc:
        d = classical_fallback(s)
        d["reason"] = f"Jev call failed: {type(exc).__name__}"
        return d


def main() -> int:
    s = TakeoverState()
    d = try_jev_live(s) or classical_fallback(s)
    payload = {
        "schema": SCHEMA,
        "date": datetime.now().isoformat(timespec="seconds"),
        "state": s.to_jev_state(),
        "decision": d,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"SOURCE:    {d['source']}")
    print(f"HIT_GRAPH: {d['hit_graph_route']}  {json.dumps(d['hit_graph_probs'])}")
    print(f"FIRST_MOVE:{d['first_move']}  {json.dumps(d['first_move_probs'])}")
    print(f"RISKIEST:  {d['riskiest']}  {json.dumps(d['riskiest_probs'])}")
    print(f"HUMAN:     {d['needs_human']} p={d['needs_human_prob']:.2f}")
    print(f"READINESS: {d['readiness']} {d['readiness_label']}")
    print(f"WROTE:     {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
