"""Jev lane-plan audit — isolated prototype (2026-09-24).

ISOLATION CONTRACT (per Prototypes/JevP0Triage precedent):
- Everything lives in Prototypes/JevLanePlanAudit/. Delete this folder to remove it.
- NO .uasset/.umap writes. NO editor mutations. NO ledger writes.
- Reads only the plan facts assembled by the researching agent and returns
  Jev's audit of the three-lane staging goal:
    H = hair Substance staging + UE integration
    S = Choral Sheep mesh (S4-S8 of the locked GN execution plan) + animations
    M = Sir Melodious rig + reusable animation set + retarget
- Jev selects ONLY among the authored option sets below. It never generates
  content, commands, or parameters beyond the closed sets.
- Provenance: source="jev-live" or "classical-fallback" plus reason. Fallback
  runs without TYPESAFE_API_KEY and is NOT Jev evidence.

Skill: system-one-conductor. All questions go in ONE system_one call over the
same state; code owns the log. Full distributions preserved per evaluation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

OUT = Path(__file__).parent / "audit_log.json"

# --- closed option sets -----------------------------------------------------

LANE_ORDER = {
    "HAIR_FIRST": (
        "Stage hair first: the owner handpaint window is the long pole and the "
        "Painter one-click + MI wiring are cheap to enable right now."
    ),
    "SHEEP_FIRST": (
        "Sheep first: S4 shape keys and the donor-retarget clips are fully "
        "agent-executable with no owner dependency."
    ),
    "SIR_FIRST": (
        "Sir Melodious first: the reusable animation set is the biggest asset "
        "gap (one retargeted flight clip today)."
    ),
    "PARALLEL_ALL": (
        "Run all three lanes in parallel (research/authoring lanes only; "
        "editor-mutating steps stay serialized)."
    ),
}

RISKIEST_ASSUMPTION = {
    "HAIR_UV_ATLAS": (
        "The shipped authored UV atlas is legal for Substance fill layers but "
        "handpaint across welded strand strips may read poorly."
    ),
    "SIR_CLIP_SOURCES": (
        "The reusable Sir animation set assumes authored clips that do not "
        "exist yet; retarget chains alone cannot invent them."
    ),
    "SHEEP_S4_PANEL": (
        "S4 assumes the shape-key panel retargets cleanly onto the "
        "armature-bound mesh; the plan itself flags it as needing retarget."
    ),
    "UE_WIRING_TRIVIAL": (
        "The plan assumes hair MI wiring is trivial; the tether audit found "
        "zero Copernicus refs, so the consumer path is unproven."
    ),
    "NONE_MATERIAL": "No assumption is materially risky; proceed as written.",
}

NEEDS_HUMAN_CRITERIA = {
    "true": (
        "An owner decision gates execution (e.g. Sir canonical mesh choice, "
        "S8 eye gate, handpaint start, or lane-order veto)."
    ),
    "false": "Agents can execute the plan as written without an owner decision.",
}

READINESS_LEVELS = [
    "Research only: no staged artifacts or receipts.",
    "Staged artifacts exist but gates unproven.",
    "Receipts exist for most steps; consumer wiring unproven.",
    "Live-proven end to end for at least one lane.",
    "All three lanes live-proven with owner eye gates passed.",
]


# --- state ------------------------------------------------------------------

@dataclass
class PlanState:
    """Compact plan facts. None = unknown (reads as missing, not zero)."""

    hair_spp_exists: bool = False
    hair_bakes_imported_ue: int = 24
    hair_runtime_mi_tethers: int = 0
    hair_staging_fbx_ok: bool = True
    sheep_stages_done: str = "S0,S1,S2,S3a,S3b,S3b3,S3c"
    sheep_next_stage: str = "S4_shapekeys"
    sheep_ue_anims: int = 6
    sheep_abp_proof_date: str = "2026-09-13"
    sheep_donor_rtg: bool = True
    sir_rigged_sks: int = 2          # Rigged vs Clothed_Production (wix FBX)
    sir_retargated_clips: int = 1    # FreeCameraTrackingframeupdate_Anim_RT
    sir_rtg_chains: int = 2          # UE4Mannequin, FlightSource
    sir_abp_exists: bool = True
    owner_present: bool = True
    time_budget_hours: float = 8.0

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "hair_spp_exists": self.hair_spp_exists,
            "hair_bakes_imported_ue": self.hair_bakes_imported_ue,
            "hair_runtime_mi_tethers": self.hair_runtime_mi_tethers,
            "hair_staging_fbx_ok": self.hair_staging_fbx_ok,
            "sheep_stages_done": self.sheep_stages_done,
            "sheep_next_stage": self.sheep_next_stage,
            "sheep_ue_anims": self.sheep_ue_anims,
            "sheep_abp_proof_date": self.sheep_abp_proof_date,
            "sheep_donor_rtg": self.sheep_donor_rtg,
            "sir_rigged_sks": self.sir_rigged_sks,
            "sir_retargated_clips": self.sir_retargated_clips,
            "sir_rtg_chains": self.sir_rtg_chains,
            "sir_abp_exists": self.sir_abp_exists,
            "owner_present": self.owner_present,
            "time_budget_hours": self.time_budget_hours,
        }
        return {k: v for k, v in raw.items() if v is not None}


# --- audit ------------------------------------------------------------------

@dataclass
class AuditDecision:
    order: str
    order_probs: dict[str, float]
    riskiest: str
    riskiest_probs: dict[str, float]
    needs_human: bool
    needs_human_prob: float
    readiness: int
    readiness_probs: list[float]
    source: str  # jev-live | classical-fallback
    reason: str
    confidence: float = 0.0


def classical_fallback(state: PlanState) -> AuditDecision:
    """Deterministic rules. Clearly labeled, never Jev evidence."""
    order_p = {k: 0.04 for k in LANE_ORDER}
    if not state.hair_spp_exists and state.owner_present:
        order, reason = "HAIR_FIRST", "owner present and the Painter gate is theirs to open"
        order_p["HAIR_FIRST"] = 0.7
    elif state.sheep_next_stage.startswith("S4"):
        order, reason = "SHEEP_FIRST", "S4 is fully agent-executable right now"
        order_p["SHEEP_FIRST"] = 0.7
    else:
        order, reason = "SIR_FIRST", "biggest asset gap"
        order_p["SIR_FIRST"] = 0.7
    risk_p = {k: 0.03 for k in RISKIEST_ASSUMPTION}
    risk = "SIR_CLIP_SOURCES" if state.sir_retargated_clips <= 1 else "HAIR_UV_ATLAS"
    risk_p[risk] = 0.7
    readiness = 2 if (state.hair_staging_fbx_ok and state.sheep_donor_rtg) else 1
    return AuditDecision(
        order=order,
        order_probs={k: round(v / sum(order_p.values()), 4) for k, v in order_p.items()},
        riskiest=risk,
        riskiest_probs={k: round(v / sum(risk_p.values()), 4) for k, v in risk_p.items()},
        needs_human=True,
        needs_human_prob=0.85,
        readiness=readiness,
        readiness_probs=[0.05, 0.1, 0.7, 0.1, 0.05],
        source="classical-fallback",
        reason=reason,
        confidence=0.7,
    )


def _try_jev_live(state: PlanState) -> Optional[AuditDecision]:
    """Live Jev via TypeSafe SDK. Returns None when unavailable (no key/sdk)."""
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
                            "Pick the single best lane to execute FIRST today "
                            "for the staging goal (hair / sheep / Sir Melodious)."
                        ),
                        "criteria": LANE_ORDER,
                    },
                    "riskiest": {
                        "type": "choice",
                        "instructions": (
                            "Which plan assumption is the riskiest — the one "
                            "most likely to invalidate the plan if wrong?"
                        ),
                        "criteria": RISKIEST_ASSUMPTION,
                    },
                    "human": {
                        "type": "noul",
                        "instructions": (
                            "Does an owner decision gate execution before "
                            "agents run the plan?"
                        ),
                        "criteria": NEEDS_HUMAN_CRITERIA,
                    },
                    "readiness": {
                        "type": "score",
                        "instructions": (
                            "How execution-ready is this three-lane plan as "
                            "evidenced by the state facts?"
                        ),
                        "criteria": READINESS_LEVELS,
                    },
                },
            )
            ans = resp.answers
            order = ans["order"]
            risk = ans["riskiest"]
            hum = ans["human"]
            red = ans["readiness"]
            order_pick = order.choice if order.choice in LANE_ORDER else "SHEEP_FIRST"
            risk_pick = risk.choice if risk.choice in RISKIEST_ASSUMPTION else "SIR_CLIP_SOURCES"
            return AuditDecision(
                order=order_pick,
                order_probs={k: float(v) for k, v in (order.probabilities or {}).items() if k in LANE_ORDER},
                riskiest=risk_pick,
                riskiest_probs={k: float(v) for k, v in (risk.probabilities or {}).items() if k in RISKIEST_ASSUMPTION},
                needs_human=bool(hum.noul is not None and hum.noul > 0.5),
                needs_human_prob=float(hum.noul or 0.0),
                readiness=int(red.score or 0),
                readiness_probs=[float(p) for p in (red.probabilities or [])],
                source="jev-live",
                reason="typesafe System One Choice+Choice+Noul+Score, one call",
                confidence=float(order.confidence or 0.0),
            )
    except Exception as exc:  # service failure is not a decision
        fb = classical_fallback(state)
        fb.reason = f"jev-live failed ({type(exc).__name__}), classical fallback"
        return fb


def main() -> None:
    state = PlanState()
    decision = _try_jev_live(state) or classical_fallback(state)
    log = {
        "schema": "melodia.jev_lane_plan_audit.v1",
        "date": datetime.now().isoformat(timespec="seconds"),
        "state": state.to_jev_state(),
        "decision": {
            "order": decision.order,
            "order_probs": decision.order_probs,
            "riskiest": decision.riskiest,
            "riskiest_probs": decision.riskiest_probs,
            "needs_human": decision.needs_human,
            "needs_human_prob": decision.needs_human_prob,
            "readiness": decision.readiness,
            "readiness_label": READINESS_LEVELS[decision.readiness],
            "readiness_probs": decision.readiness_probs,
            "source": decision.source,
            "reason": decision.reason,
            "confidence": decision.confidence,
        },
    }
    OUT.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log["decision"], indent=1))
    print("log:", OUT)


if __name__ == "__main__":
    main()
