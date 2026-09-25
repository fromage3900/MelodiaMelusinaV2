"""Jev Houdini-session plan audit — isolated prototype (2026-09-24).

ISOLATION CONTRACT (per Prototypes/JevLanePlanAudit precedent):
- Everything lives in Prototypes/JevHoudiniSessionPlan/. Delete this folder to remove it.
- NO .uasset/.umap writes. NO editor mutations. NO ledger writes.
- Reads only the plan facts assembled from tonight's docs:
    CURRENT_STATE.md          (Houdini live staging 2026-09-24, license-blocked)
    hda/README.md             (HDA lane quick start; license=blocking)
    Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md  (ArpeggioStair spec + gates)
    Docs/Handoffs/HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md  (B0 license verdict rule)
    Saved/Audit/cathedral/*   + p4_cathedral_houdini_mi_spec_confirm_2026-09-11.json
    Tonight's live probes: hserver -l (Used Licenses: None), smoke green, editor PID 55060.
- Question: the updated plan/order for the next LICENSED Houdini session
  (ArpeggioStair cook proof; college visit / student Education license path).
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

FIRST_BLOCK = {
    "LICENSE_AND_SMOKE_FIRST": (
        "Before any cook: verify the Engine license is actually leased (hserver / License "
        "Administrator shows a license line) and re-run smoke_houdini_engine_pcg.py, then proceed. "
        "Cheap insurance against a second blind failure on funded time."
    ),
    "ARPEGGIO_COOK_FIRST": (
        "Go straight to the blocked proof: trigger the existing ArpeggioStair actor, cook, bake, "
        "and walk the musical PIE gate. Treat licensing as a one-minute pre-check only."
    ),
    "EVIDENCE_HARNESS_FIRST": (
        "Build the cook-run capture harness first (structured log capture, actor state before/after, "
        "bake receipt, musical-gate JSON + frames) so the single funded cook attempt is fully "
        "evidenced in one pass."
    ),
    "CATHEDRAL_HDA_FIRST": (
        "Spend the licensed time on the cathedral: re-author the P4 cathedral generators as HDAs "
        "and cook them in UE. Bigger authoring lift; note the cathedral's own open item (MI "
        "materialization) is editor work, not Houdini work."
    ),
}

RISKIEST_ASSUMPTION = {
    "LICENSE_CLASS_COMPAT": (
        "The HDA was authored headlessly today and the license class is unverified. Engine tiers "
        "interact (Apprentice-authored assets need Engine Education; the free Unreal Engine "
        "license cooks FX/Core/Education-authored assets). 'No License Found' may persist until "
        "both the lease AND the class are right."
    ),
    "COLLEGE_ACCESS_ONLY": (
        "College Education licenses are floating and campus-bound; the project and editor are on "
        "this machine. Only a minimal smoke project can travel, so the main-project cook proof "
        "may still wait for home."
    ),
    "MUSICAL_GATE_MISMATCH": (
        "The musical chain gate (SetPressedForActor -> PlayMusicalNote -> ScoreState 64/1/1) "
        "assumes PCG-era level wiring; the HDA path has never produced a pad, so the expectation "
        "itself is unproven."
    ),
    "HDA_PARAM_DRIFT": (
        "The HDA was authored ad hoc today and may not match the smoke spec parameters "
        "(seed, stepCount 16, laneCount 4, spacing, baseMidiNote, scale, heightPerDegree), so a "
        "successful cook could still output the wrong field."
    ),
    "NONE_MATERIAL": "No assumption is materially risky; proceed as written.",
}

NEEDS_HUMAN_CRITERIA = {
    "true": (
        "An owner-only action gates execution (license acquisition/verification via SideFX "
        "account, or the college visit itself)."
    ),
    "false": "Agents can execute the plan as written without an owner decision.",
}

READINESS_LEVELS = [
    "Research only: no staged HDA assets.",
    "HDA + plugin staged; cook never attempted.",
    "All assets staged + offline smoke green; cook blocked by license with a named fix (lease + class check).",
    "Licensed cook proven in a smoke project; the main-project cook is next.",
    "Main-project cook + bake + musical gate proven; receipt exists.",
]


# --- state ------------------------------------------------------------------

@dataclass
class HoudiniState:
    """Compact plan facts from tonight's docs + live probes. None = unknown."""

    hda_asset_exists: bool = True           # hda/ArpeggioStair_1.0.hda + Content/HDA uasset imported
    hda_git_tracked: bool = False           # untracked work-tree files (hda/ and Content allowlist)
    placeholder_actor_present: bool = True  # L_MelusinaMorning (400,0,100), kept for diagnosis
    engine_license_leased: bool = False     # hserver -l: Used Licenses None; HARS: License failed
    license_server_reachable: bool = True   # localhost:1715 connected
    license_class_verified: bool = False    # Apprentice vs Education vs FX not confirmed
    smoke_offline_green: bool = True        # smoke_houdini_engine_pcg + plugin enabled (5.8/22.0.368)
    hython_built_hda_today: bool = True     # HDA written 2026-09-24 12:03
    cathedral_meshes_imported: int = 8      # SM_P4_Cathedral_* in Content/EnvSandbox/Meshes/Cathedral_Houdini
    cathedral_mi_pending: bool = True       # 0 MI_P4_Cathedral instances created
    editor_open_now: bool = True            # single UnrealEditor PID 55060
    owner_present: bool = True
    session_hours: float = 3.0

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "hda_asset_exists": self.hda_asset_exists,
            "hda_git_tracked": self.hda_git_tracked,
            "placeholder_actor_present": self.placeholder_actor_present,
            "engine_license_leased": self.engine_license_leased,
            "license_server_reachable": self.license_server_reachable,
            "license_class_verified": self.license_class_verified,
            "smoke_offline_green": self.smoke_offline_green,
            "hython_built_hda_today": self.hython_built_hda_today,
            "cathedral_meshes_imported": self.cathedral_meshes_imported,
            "cathedral_mi_pending": self.cathedral_mi_pending,
            "editor_open_now": self.editor_open_now,
            "owner_present": self.owner_present,
            "session_hours": self.session_hours,
        }
        return {k: v for k, v in raw.items() if v is not None}


# --- audit ------------------------------------------------------------------

@dataclass
class AuditDecision:
    first_block: str
    first_block_probs: dict[str, float]
    riskiest: str
    riskiest_probs: dict[str, float]
    needs_human: bool
    needs_human_prob: float
    readiness: int
    readiness_probs: list[float]
    source: str  # jev-live | classical-fallback
    reason: str
    confidence: float = 0.0


def classical_fallback(state: HoudiniState) -> AuditDecision:
    """Deterministic rules. Clearly labeled, never Jev evidence."""
    order_p = {k: 0.04 for k in FIRST_BLOCK}
    if not state.engine_license_leased:
        first, reason = "LICENSE_AND_SMOKE_FIRST", "license absent - every cook step is dead until the lease verifies"
        order_p["LICENSE_AND_SMOKE_FIRST"] = 0.72
    elif state.hda_asset_exists and state.smoke_offline_green:
        first, reason = "ARPEGGIO_COOK_FIRST", "HDA staged and smoke green; go to the blocked proof"
        order_p["ARPEGGIO_COOK_FIRST"] = 0.7
    else:
        first, reason = "EVIDENCE_HARNESS_FIRST", "capture harness must exist before the first funded cook"
        order_p["EVIDENCE_HARNESS_FIRST"] = 0.7
    risk_p = {k: 0.03 for k in RISKIEST_ASSUMPTION}
    risk = "LICENSE_CLASS_COMPAT" if not state.license_class_verified else "COLLEGE_ACCESS_ONLY"
    risk_p[risk] = 0.7
    readiness = 2 if state.smoke_offline_green else 1
    return AuditDecision(
        first_block=first,
        first_block_probs={k: round(v / sum(order_p.values()), 4) for k, v in order_p.items()},
        riskiest=risk,
        riskiest_probs={k: round(v / sum(risk_p.values()), 4) for k, v in risk_p.items()},
        needs_human=True,
        needs_human_prob=0.9,
        readiness=readiness,
        readiness_probs=[0.02, 0.08, 0.7, 0.15, 0.05],
        source="classical-fallback",
        reason=reason,
        confidence=0.7,
    )


def _try_jev_live(state: HoudiniState) -> Optional[AuditDecision]:
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
                    "first_block": {
                        "type": "choice",
                        "instructions": (
                            "Pick the single best FIRST block for the next licensed Houdini "
                            "session (the ArpeggioStair cook proof; college / student-Education "
                            "license path). The session is time-boxed to a few hours."
                        ),
                        "criteria": FIRST_BLOCK,
                    },
                    "riskiest": {
                        "type": "choice",
                        "instructions": (
                            "Which plan assumption is the riskiest - the one most likely to "
                            "invalidate the session if wrong?"
                        ),
                        "criteria": RISKIEST_ASSUMPTION,
                    },
                    "human": {
                        "type": "noul",
                        "instructions": (
                            "Does an owner-only action gate execution before agents can run "
                            "the plan to completion?"
                        ),
                        "criteria": NEEDS_HUMAN_CRITERIA,
                    },
                    "readiness": {
                        "type": "score",
                        "instructions": (
                            "How execution-ready is this licensed-session plan as evidenced "
                            "by the state facts?"
                        ),
                        "criteria": READINESS_LEVELS,
                    },
                },
            )
            ans = resp.answers
            order = ans["first_block"]
            risk = ans["riskiest"]
            hum = ans["human"]
            red = ans["readiness"]
            first_pick = order.choice if order.choice in FIRST_BLOCK else "LICENSE_AND_SMOKE_FIRST"
            risk_pick = risk.choice if risk.choice in RISKIEST_ASSUMPTION else "LICENSE_CLASS_COMPAT"
            return AuditDecision(
                first_block=first_pick,
                first_block_probs={k: float(v) for k, v in (order.probabilities or {}).items() if k in FIRST_BLOCK},
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
    state = HoudiniState()
    decision = _try_jev_live(state) or classical_fallback(state)
    log = {
        "schema": "melodia.jev_houdini_session_audit.v1",
        "date": datetime.now().isoformat(timespec="seconds"),
        "state": state.to_jev_state(),
        "decision": {
            "first_block": decision.first_block,
            "first_block_probs": decision.first_block_probs,
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